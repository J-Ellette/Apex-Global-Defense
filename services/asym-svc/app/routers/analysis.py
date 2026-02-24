from __future__ import annotations

import math
from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.auth import get_current_user, require_permission
from app.data.cell_types import CELL_FUNCTION_MAP
from app.models import (
    CellAnalysisNode,
    CellFunction,
    CellStatus,
    FundingLevel,
    InsurgentCell,
    NetworkAnalysis,
)
from app.routers.cells import _row_to_cell, _row_to_link

router = APIRouter(tags=["analysis"])


# ---------------------------------------------------------------------------
# Graph algorithm helpers (no external dependencies)
# ---------------------------------------------------------------------------

def _build_adjacency(cells: list[InsurgentCell], links: list) -> dict[UUID, set[UUID]]:
    """Build undirected adjacency list from cells and links."""
    adj: dict[UUID, set[UUID]] = {c.id: set() for c in cells}
    for link in links:
        src, tgt = link.source_cell_id, link.target_cell_id
        if src in adj and tgt in adj:
            adj[src].add(tgt)
            adj[tgt].add(src)
    return adj


def _degree_centrality(adj: dict[UUID, set[UUID]]) -> dict[UUID, float]:
    """Normalized degree centrality."""
    n = len(adj)
    if n <= 1:
        return {k: 0.0 for k in adj}
    return {k: len(v) / (n - 1) for k, v in adj.items()}


def _betweenness_centrality(cells: list[InsurgentCell], adj: dict[UUID, set[UUID]]) -> dict[UUID, float]:
    """
    Brandes-inspired betweenness centrality (exact, unweighted).
    Suitable for small/medium graphs (up to a few hundred nodes).
    """
    n = len(cells)
    node_ids = [c.id for c in cells]
    betweenness: dict[UUID, float] = {nid: 0.0 for nid in node_ids}

    for s in node_ids:
        # BFS from s
        stack: list[UUID] = []
        pred: dict[UUID, list[UUID]] = {nid: [] for nid in node_ids}
        sigma: dict[UUID, float] = {nid: 0.0 for nid in node_ids}
        dist: dict[UUID, int] = {nid: -1 for nid in node_ids}
        sigma[s] = 1.0
        dist[s] = 0
        queue: list[UUID] = [s]
        while queue:
            v = queue.pop(0)
            stack.append(v)
            for w in adj.get(v, set()):
                if dist[w] < 0:
                    queue.append(w)
                    dist[w] = dist[v] + 1
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        # Accumulate dependencies
        delta: dict[UUID, float] = {nid: 0.0 for nid in node_ids}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                betweenness[w] += delta[w]

    # Normalize
    if n > 2:
        scale = 1.0 / ((n - 1) * (n - 2))
        betweenness = {k: v * scale for k, v in betweenness.items()}
    return betweenness


def _hub_score(
    cell: InsurgentCell,
    degree: float,
    betweenness: float,
) -> float:
    """
    Composite hub score combining:
    - Degree centrality (connectivity)
    - Betweenness centrality (bridge importance)
    - Operational capability
    - Cell function priority weight
    """
    ct = CELL_FUNCTION_MAP.get(cell.function.value if isinstance(cell.function, CellFunction) else str(cell.function))
    prio_weight = (ct.interdiction_priority / 10.0) if ct else 0.5
    status_weight = 1.0 if cell.status in (CellStatus.ACTIVE, CellStatus.UNKNOWN) else 0.3
    raw = (
        0.35 * degree
        + 0.35 * betweenness
        + 0.20 * cell.operational_capability
        + 0.10 * prio_weight
    ) * status_weight
    return min(1.0, raw)


def _interdiction_value(cell: InsurgentCell, hub: float) -> int:
    ct = CELL_FUNCTION_MAP.get(cell.function.value if isinstance(cell.function, CellFunction) else str(cell.function))
    base = ct.interdiction_priority if ct else 5
    adjusted = base * (0.5 + 0.5 * hub)
    return max(1, min(10, round(adjusted)))


def _recommendation(cell: InsurgentCell, hub: float, degree: int) -> str:
    ct = CELL_FUNCTION_MAP.get(cell.function.value if isinstance(cell.function, CellFunction) else str(cell.function))
    func_label = ct.label if ct else cell.function.value
    if hub >= 0.7:
        return (
            f"HIGH PRIORITY — {func_label} is a critical network hub ({degree} connections). "
            "Recommend targeted interdiction via direct action or capture/exploitation."
        )
    if hub >= 0.4:
        return (
            f"MEDIUM PRIORITY — {func_label} provides bridging connectivity. "
            "Monitor and develop intelligence; consider disruption operations."
        )
    return (
        f"LOW PRIORITY — {func_label} is peripheral to the network. "
        "Continue intelligence collection; escalate if capability increases."
    )


# ---------------------------------------------------------------------------
# COIN recommendation generation
# ---------------------------------------------------------------------------

def _coin_recommendations(
    cells: list[InsurgentCell],
    top_nodes: list[CellAnalysisNode],
    total_links: int,
    density: float,
) -> list[str]:
    recs: list[str] = []

    active = [c for c in cells if c.status in (CellStatus.ACTIVE, CellStatus.UNKNOWN)]

    # Network structure recommendations
    if density > 0.4:
        recs.append(
            "Network density is HIGH (>{:.0f}%). The organization is tightly connected — "
            "single-node interdiction may not fragment the network. "
            "Prioritize simultaneous multi-cell operations.".format(density * 100)
        )
    elif density < 0.1 and len(cells) > 5:
        recs.append(
            "Network density is LOW (<10%). The organization operates with loose connections — "
            "likely chain or hub-and-spoke structure. Identify and sever key bridge links."
        )

    # Command cells
    cmd_cells = [c for c in active if c.function == CellFunction.COMMAND]
    if cmd_cells:
        recs.append(
            f"Identified {len(cmd_cells)} COMMAND cell(s). Decapitation strike or "
            "capture-exploitation will disrupt strategic coordination. "
            "Assess succession risk before action."
        )

    # Finance cells
    fin_cells = [c for c in active if c.function == CellFunction.FINANCE]
    if fin_cells:
        recs.append(
            f"Identified {len(fin_cells)} FINANCE cell(s). "
            "Coordinate with financial intelligence (FININT) for account freezing, "
            "hawala network disruption, and sanctions targeting."
        )

    # Technical/IED cells
    tech_cells = [c for c in active if c.function == CellFunction.TECHNICAL]
    if tech_cells:
        recs.append(
            f"Identified {len(tech_cells)} TECHNICAL/IED cell(s). "
            "Prioritize interdiction to reduce IED threat. "
            "Exploit bomb-maker capture for materials and network intelligence."
        )

    # Recruitment cells
    rec_cells = [c for c in active if c.function == CellFunction.RECRUITMENT]
    if rec_cells:
        recs.append(
            f"Identified {len(rec_cells)} RECRUITMENT cell(s). "
            "Counter-radicalization programs, community engagement, and monitoring "
            "of key venues are recommended alongside direct disruption."
        )

    # Highly funded cells
    high_funded = [c for c in active if c.funding_level == FundingLevel.HIGH]
    if high_funded:
        recs.append(
            f"{len(high_funded)} cell(s) assessed as HIGH-FUNDED. "
            "Financial disruption operations should be prioritized in parallel with kinetic action."
        )

    # Top hub target
    if top_nodes:
        top = top_nodes[0]
        recs.append(
            f"Top interdiction target: '{top.cell_name}' (hub score {top.hub_score:.2f}, "
            f"{top.degree} connections). Neutralizing this node has the highest projected "
            "network fragmentation effect."
        )

    if not recs:
        recs.append(
            "Insufficient cell data to generate specific COIN recommendations. "
            "Continue intelligence collection and network mapping."
        )

    return recs


# ---------------------------------------------------------------------------
# Analysis endpoint
# ---------------------------------------------------------------------------

@router.get("/asym/network/analysis", response_model=NetworkAnalysis)
async def analyze_network(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """
    Run cell network analysis for a scenario:
    - Hub detection (degree + betweenness centrality)
    - Composite interdiction scoring
    - COIN planning recommendations
    """
    require_permission(user, "scenario:read")
    db = request.app.state.db

    if scenario_id:
        cell_rows = await db.fetch(
            "SELECT * FROM asym_cells WHERE scenario_id = $1 ORDER BY created_at",
            scenario_id,
        )
        link_rows = await db.fetch(
            "SELECT * FROM asym_cell_links WHERE scenario_id = $1 ORDER BY created_at",
            scenario_id,
        )
    else:
        cell_rows = await db.fetch("SELECT * FROM asym_cells ORDER BY created_at LIMIT 500")
        link_rows = await db.fetch("SELECT * FROM asym_cell_links ORDER BY created_at LIMIT 2000")

    cells = [_row_to_cell(dict(r)) for r in cell_rows]
    links = [_row_to_link(dict(r)) for r in link_rows]

    n = len(cells)
    m = len(links)
    active_count = sum(1 for c in cells if c.status in (CellStatus.ACTIVE, CellStatus.UNKNOWN))

    # Network density
    max_possible_links = n * (n - 1) / 2 if n > 1 else 1
    density = m / max_possible_links if max_possible_links > 0 else 0.0

    if n == 0:
        return NetworkAnalysis(
            scenario_id=scenario_id,
            total_cells=0,
            total_links=0,
            active_cells=0,
            network_density=0.0,
            top_targets=[],
            coin_recommendations=["No cells found. Begin mapping the network."],
            analysis_summary="No insurgent cells have been mapped for this scenario.",
        )

    # Compute centrality
    adj = _build_adjacency(cells, links)
    degree_map = _degree_centrality(adj)
    betweenness_map = _betweenness_centrality(cells, adj)

    # Build analysis nodes
    analysis_nodes: list[CellAnalysisNode] = []
    for cell in cells:
        deg_score = degree_map.get(cell.id, 0.0)
        bet_score = betweenness_map.get(cell.id, 0.0)
        hub = _hub_score(cell, deg_score, bet_score)
        degree_count = len(adj.get(cell.id, set()))
        ival = _interdiction_value(cell, hub)
        rec = _recommendation(cell, hub, degree_count)
        analysis_nodes.append(CellAnalysisNode(
            cell_id=cell.id,
            cell_name=cell.name,
            function=cell.function,
            hub_score=round(hub, 4),
            degree=degree_count,
            betweenness=round(bet_score, 4),
            interdiction_value=ival,
            recommendation=rec,
        ))

    # Sort by interdiction value descending, then hub score
    analysis_nodes.sort(key=lambda x: (x.interdiction_value, x.hub_score), reverse=True)
    top_targets = analysis_nodes[:min(10, len(analysis_nodes))]

    coin_recs = _coin_recommendations(cells, top_targets, m, density)

    # Summary
    if n == 1:
        summary = (
            f"Single-cell network mapped. {active_count} active cell(s). "
            "Expand network mapping for meaningful analysis."
        )
    else:
        summary = (
            f"Analyzed {n} insurgent cells with {m} inter-cell links. "
            f"{active_count} cells are ACTIVE or UNKNOWN. "
            f"Network density: {density:.1%}. "
            f"Top interdiction target: {top_targets[0].cell_name} "
            f"(hub score {top_targets[0].hub_score:.2f})."
            if top_targets else
            f"Analyzed {n} insurgent cells with {m} inter-cell links. "
            f"Network density: {density:.1%}."
        )

    return NetworkAnalysis(
        scenario_id=scenario_id,
        total_cells=n,
        total_links=m,
        active_cells=active_count,
        network_density=round(density, 4),
        top_targets=top_targets,
        coin_recommendations=coin_recs,
        analysis_summary=summary,
        metadata={
            "algorithm": "degree+betweenness centrality",
            "max_possible_links": int(max_possible_links),
        },
    )

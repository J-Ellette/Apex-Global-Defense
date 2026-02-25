"""Infrastructure graph router — manage cyber infrastructure nodes and edges."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.models import (
    CreateInfraEdgeRequest,
    CreateInfraNodeRequest,
    Criticality,
    InfraEdge,
    InfraGraph,
    InfraNode,
    NodeType,
    UpdateInfraNodeRequest,
)

router = APIRouter(tags=["infrastructure"])

ClaimsDepend = Annotated[dict, Depends(get_current_user)]


def _db(request: Request):
    return request.app.state.db


def _row_to_node(row: dict) -> InfraNode:
    tags = row.get("tags") or []
    meta = row.get("metadata") or {}
    if isinstance(tags, str):
        tags = json.loads(tags)
    if isinstance(meta, str):
        meta = json.loads(meta)
    return InfraNode(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        label=row["label"],
        node_type=NodeType(row["node_type"]),
        network=row.get("network"),
        ip_address=row.get("ip_address"),
        criticality=Criticality(row["criticality"]),
        classification=row.get("classification", "UNCLASS"),
        tags=tags if isinstance(tags, list) else [],
        metadata=meta if isinstance(meta, dict) else {},
        created_at=row["created_at"],
    )


def _row_to_edge(row: dict) -> InfraEdge:
    return InfraEdge(
        id=row["id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        edge_type=row.get("edge_type", "NETWORK"),
        protocol=row.get("protocol"),
        port=row.get("port"),
        created_at=row["created_at"],
    )


@router.get("/cyber/infrastructure", response_model=InfraGraph)
async def get_graph(
    claims: ClaimsDepend,
    request: Request,
    scenario_id: str | None = None,
) -> InfraGraph:
    """Return the full infrastructure graph (nodes + edges), optionally scoped to a scenario."""
    require_permission(claims, "scenario:read")
    db = _db(request)

    # Application-level classification ceiling
    user_cls = get_user_classification(claims)
    allowed = classification_allowed_levels(user_cls)
    cls_placeholders = ", ".join(f"${i + 1}" for i in range(len(allowed)))

    if scenario_id:
        node_rows = await db.fetch(
            f"SELECT * FROM cyber_infra_nodes WHERE scenario_id = ${len(allowed) + 1} "
            f"AND classification::text IN ({cls_placeholders}) ORDER BY created_at",
            *allowed,
            uuid.UUID(scenario_id),
        )
    else:
        node_rows = await db.fetch(
            f"SELECT * FROM cyber_infra_nodes "
            f"WHERE classification::text IN ({cls_placeholders}) ORDER BY created_at",
            *allowed,
        )

    node_ids = [r["id"] for r in node_rows]
    edges: list[InfraEdge] = []
    if node_ids:
        edge_rows = await db.fetch(
            """
            SELECT * FROM cyber_infra_edges
            WHERE source_id = ANY($1::uuid[]) OR target_id = ANY($1::uuid[])
            ORDER BY created_at
            """,
            node_ids,
        )
        edges = [_row_to_edge(dict(r)) for r in edge_rows]

    return InfraGraph(
        nodes=[_row_to_node(dict(r)) for r in node_rows],
        edges=edges,
    )


@router.post("/cyber/infrastructure/nodes", response_model=InfraNode, status_code=201)
async def create_node(
    body: CreateInfraNodeRequest,
    claims: ClaimsDepend,
    request: Request,
) -> InfraNode:
    """Add an infrastructure node to the graph."""
    require_permission(claims, "scenario:write")
    enforce_classification_ceiling(claims, body.classification)
    db = _db(request)
    node_id = uuid.uuid4()
    now = datetime.utcnow()
    await db.execute(
        """
        INSERT INTO cyber_infra_nodes
            (id, scenario_id, label, node_type, network, ip_address, criticality,
             classification, tags, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11)
        """,
        node_id,
        body.scenario_id,
        body.label,
        body.node_type.value,
        body.network,
        body.ip_address,
        body.criticality.value,
        body.classification,
        body.tags,
        json.dumps(body.metadata),
        now,
    )
    return InfraNode(
        id=node_id,
        scenario_id=body.scenario_id,
        label=body.label,
        node_type=body.node_type,
        network=body.network,
        ip_address=body.ip_address,
        criticality=body.criticality,
        classification=body.classification,
        tags=body.tags,
        metadata=body.metadata,
        created_at=now,
    )


@router.put("/cyber/infrastructure/nodes/{node_id}", response_model=InfraNode)
async def update_node(
    node_id: uuid.UUID,
    body: UpdateInfraNodeRequest,
    claims: ClaimsDepend,
    request: Request,
) -> InfraNode:
    """Update an infrastructure node."""
    require_permission(claims, "scenario:write")
    db = _db(request)
    row = await db.fetchrow("SELECT * FROM cyber_infra_nodes WHERE id = $1", node_id)
    if not row:
        raise HTTPException(status_code=404, detail="Node not found")
    current = _row_to_node(dict(row))
    enforce_classification_ceiling(claims, current.classification)
    if body.classification is not None:
        enforce_classification_ceiling(claims, body.classification)

    updated = InfraNode(
        id=current.id,
        scenario_id=current.scenario_id,
        label=body.label if body.label is not None else current.label,
        node_type=body.node_type if body.node_type is not None else current.node_type,
        network=body.network if body.network is not None else current.network,
        ip_address=body.ip_address if body.ip_address is not None else current.ip_address,
        criticality=body.criticality if body.criticality is not None else current.criticality,
        classification=body.classification if body.classification is not None else current.classification,
        tags=body.tags if body.tags is not None else current.tags,
        metadata=body.metadata if body.metadata is not None else current.metadata,
        created_at=current.created_at,
    )

    await db.execute(
        """
        UPDATE cyber_infra_nodes
        SET label=$2, node_type=$3, network=$4, ip_address=$5, criticality=$6,
            classification=$7, tags=$8, metadata=$9::jsonb
        WHERE id=$1
        """,
        node_id,
        updated.label,
        updated.node_type.value,
        updated.network,
        updated.ip_address,
        updated.criticality.value,
        updated.classification,
        updated.tags,
        json.dumps(updated.metadata),
    )
    return updated


@router.delete("/cyber/infrastructure/nodes/{node_id}")
async def delete_node(
    node_id: uuid.UUID,
    claims: ClaimsDepend,
    request: Request,
) -> Response:
    """Delete an infrastructure node (and its edges via CASCADE)."""
    require_permission(claims, "scenario:write")
    db = _db(request)
    result = await db.execute("DELETE FROM cyber_infra_nodes WHERE id = $1", node_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Node not found")
    return Response(status_code=204)


@router.post("/cyber/infrastructure/edges", response_model=InfraEdge, status_code=201)
async def create_edge(
    body: CreateInfraEdgeRequest,
    claims: ClaimsDepend,
    request: Request,
) -> InfraEdge:
    """Add a connection between two infrastructure nodes."""
    require_permission(claims, "scenario:write")
    db = _db(request)

    # Verify both nodes exist
    for nid in (body.source_id, body.target_id):
        row = await db.fetchrow("SELECT id FROM cyber_infra_nodes WHERE id = $1", nid)
        if not row:
            raise HTTPException(status_code=404, detail=f"Node {nid} not found")

    edge_id = uuid.uuid4()
    now = datetime.utcnow()
    await db.execute(
        """
        INSERT INTO cyber_infra_edges (id, source_id, target_id, edge_type, protocol, port, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        edge_id,
        body.source_id,
        body.target_id,
        body.edge_type,
        body.protocol,
        body.port,
        now,
    )
    return InfraEdge(
        id=edge_id,
        source_id=body.source_id,
        target_id=body.target_id,
        edge_type=body.edge_type,
        protocol=body.protocol,
        port=body.port,
        created_at=now,
    )


@router.delete("/cyber/infrastructure/edges/{edge_id}")
async def delete_edge(
    edge_id: uuid.UUID,
    claims: ClaimsDepend,
    request: Request,
) -> Response:
    """Remove a connection between infrastructure nodes."""
    require_permission(claims, "scenario:write")
    db = _db(request)
    result = await db.execute("DELETE FROM cyber_infra_edges WHERE id = $1", edge_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Edge not found")
    return Response(status_code=204)

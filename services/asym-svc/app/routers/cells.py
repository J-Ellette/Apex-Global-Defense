from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status

from app.auth import get_current_user, require_permission
from app.models import (
    CellFunction,
    CellLink,
    CellNetwork,
    CellStatus,
    CellStructure,
    CreateCellLinkRequest,
    CreateCellRequest,
    FundingLevel,
    InsurgentCell,
    LinkStrength,
    LinkType,
    UpdateCellRequest,
)

router = APIRouter(tags=["cells"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_cell(row: dict) -> InsurgentCell:
    raw_groups = row.get("affiliated_groups") or "[]"
    if isinstance(raw_groups, str):
        groups = json.loads(raw_groups)
    else:
        groups = list(raw_groups)
    return InsurgentCell(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        name=row["name"],
        function=CellFunction(row["function"]),
        structure=CellStructure(row.get("structure", "NETWORK")),
        status=CellStatus(row.get("status", "UNKNOWN")),
        size_estimated=int(row.get("size_estimated", 5)),
        latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
        longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
        region=row.get("region"),
        country_code=row.get("country_code"),
        leadership_confidence=float(row.get("leadership_confidence", 0.5)),
        operational_capability=float(row.get("operational_capability", 0.5)),
        funding_level=FundingLevel(row.get("funding_level", "UNKNOWN")),
        affiliated_groups=groups,
        notes=row.get("notes"),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


def _row_to_link(row: dict) -> CellLink:
    return CellLink(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        source_cell_id=row["source_cell_id"],
        target_cell_id=row["target_cell_id"],
        link_type=LinkType(row.get("link_type", "UNKNOWN")),
        strength=LinkStrength(row.get("strength", "MODERATE")),
        confidence=float(row.get("confidence", 0.5)),
        notes=row.get("notes"),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


# ---------------------------------------------------------------------------
# Cell CRUD
# ---------------------------------------------------------------------------

@router.get("/asym/cells", response_model=list[InsurgentCell])
async def list_cells(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List insurgent cells, optionally filtered by scenario and/or status."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    if scenario_id and status:
        rows = await db.fetch(
            "SELECT * FROM asym_cells WHERE scenario_id = $1 AND status = $2 ORDER BY created_at DESC",
            scenario_id, status,
        )
    elif scenario_id:
        rows = await db.fetch(
            "SELECT * FROM asym_cells WHERE scenario_id = $1 ORDER BY created_at DESC",
            scenario_id,
        )
    elif status:
        rows = await db.fetch(
            "SELECT * FROM asym_cells WHERE status = $1 ORDER BY created_at DESC LIMIT 200",
            status,
        )
    else:
        rows = await db.fetch(
            "SELECT * FROM asym_cells ORDER BY created_at DESC LIMIT 200"
        )
    return [_row_to_cell(dict(r)) for r in rows]


@router.post("/asym/cells", response_model=InsurgentCell, status_code=http_status.HTTP_201_CREATED)
async def create_cell(
    request: Request,
    body: CreateCellRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new insurgent cell."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    cell_id = uuid4()
    now = datetime.now(timezone.utc)
    groups_json = json.dumps(body.affiliated_groups)
    await db.execute(
        """
        INSERT INTO asym_cells
          (id, scenario_id, name, function, structure, status, size_estimated,
           latitude, longitude, region, country_code, leadership_confidence,
           operational_capability, funding_level, affiliated_groups, notes,
           created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15::jsonb,$16,$17,$18)
        """,
        cell_id, body.scenario_id, body.name, body.function.value,
        body.structure.value, body.status.value, body.size_estimated,
        body.latitude, body.longitude, body.region, body.country_code,
        body.leadership_confidence, body.operational_capability,
        body.funding_level.value, groups_json, body.notes,
        user.get("sub") or user.get("uid"), now,
    )
    return InsurgentCell(
        id=cell_id,
        scenario_id=body.scenario_id,
        name=body.name,
        function=body.function,
        structure=body.structure,
        status=body.status,
        size_estimated=body.size_estimated,
        latitude=body.latitude,
        longitude=body.longitude,
        region=body.region,
        country_code=body.country_code,
        leadership_confidence=body.leadership_confidence,
        operational_capability=body.operational_capability,
        funding_level=body.funding_level,
        affiliated_groups=body.affiliated_groups,
        notes=body.notes,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.get("/asym/cells/{cell_id}", response_model=InsurgentCell)
async def get_cell(
    request: Request,
    cell_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get a single insurgent cell by ID."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM asym_cells WHERE id = $1", cell_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Cell not found")
    return _row_to_cell(dict(row))


@router.put("/asym/cells/{cell_id}", response_model=InsurgentCell)
async def update_cell(
    request: Request,
    cell_id: UUID,
    body: UpdateCellRequest,
    user: dict = Depends(get_current_user),
):
    """Update an insurgent cell's fields."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM asym_cells WHERE id = $1", cell_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Cell not found")
    current = _row_to_cell(dict(row))
    updated = current.model_copy(update={k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None})
    groups_json = json.dumps(updated.affiliated_groups)
    await db.execute(
        """
        UPDATE asym_cells SET
          name=$2, function=$3, structure=$4, status=$5, size_estimated=$6,
          latitude=$7, longitude=$8, region=$9, country_code=$10,
          leadership_confidence=$11, operational_capability=$12,
          funding_level=$13, affiliated_groups=$14::jsonb, notes=$15
        WHERE id=$1
        """,
        cell_id, updated.name, updated.function.value, updated.structure.value,
        updated.status.value, updated.size_estimated,
        updated.latitude, updated.longitude, updated.region, updated.country_code,
        updated.leadership_confidence, updated.operational_capability,
        updated.funding_level.value, groups_json, updated.notes,
    )
    return updated


@router.delete("/asym/cells/{cell_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_cell(
    request: Request,
    cell_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete an insurgent cell and all its links."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    await db.execute(
        "DELETE FROM asym_cell_links WHERE source_cell_id=$1 OR target_cell_id=$1",
        cell_id,
    )
    result = await db.execute("DELETE FROM asym_cells WHERE id = $1", cell_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Cell not found")


# ---------------------------------------------------------------------------
# Cell Link CRUD
# ---------------------------------------------------------------------------

@router.post("/asym/cell-links", response_model=CellLink, status_code=http_status.HTTP_201_CREATED)
async def create_cell_link(
    request: Request,
    body: CreateCellLinkRequest,
    user: dict = Depends(get_current_user),
):
    """Create a link between two cells."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    # Validate both cells exist
    src = await db.fetchrow("SELECT id FROM asym_cells WHERE id = $1", body.source_cell_id)
    tgt = await db.fetchrow("SELECT id FROM asym_cells WHERE id = $1", body.target_cell_id)
    if src is None:
        raise HTTPException(status_code=400, detail=f"Source cell {body.source_cell_id} not found")
    if tgt is None:
        raise HTTPException(status_code=400, detail=f"Target cell {body.target_cell_id} not found")

    link_id = uuid4()
    now = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO asym_cell_links
          (id, scenario_id, source_cell_id, target_cell_id, link_type,
           strength, confidence, notes, created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """,
        link_id, body.scenario_id, body.source_cell_id, body.target_cell_id,
        body.link_type.value, body.strength.value, body.confidence, body.notes,
        user.get("sub") or user.get("uid"), now,
    )
    return CellLink(
        id=link_id,
        scenario_id=body.scenario_id,
        source_cell_id=body.source_cell_id,
        target_cell_id=body.target_cell_id,
        link_type=body.link_type,
        strength=body.strength,
        confidence=body.confidence,
        notes=body.notes,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.delete("/asym/cell-links/{link_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_cell_link(
    request: Request,
    link_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a cell link."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute("DELETE FROM asym_cell_links WHERE id = $1", link_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Link not found")


# ---------------------------------------------------------------------------
# Cell Network (full graph)
# ---------------------------------------------------------------------------

@router.get("/asym/network", response_model=CellNetwork)
async def get_network(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """Return the full cell network (nodes + edges) for a scenario."""
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
    return CellNetwork(
        scenario_id=scenario_id,
        cells=[_row_to_cell(dict(r)) for r in cell_rows],
        links=[_row_to_link(dict(r)) for r in link_rows],
    )

from __future__ import annotations

"""Sanction target CRUD endpoints."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.models import (
    ClassificationLevel,
    CreateSanctionTargetRequest,
    SanctionStatus,
    SanctionTarget,
    SanctionType,
    UpdateSanctionTargetRequest,
)

router = APIRouter(tags=["sanctions"])


@router.get("/sanctions", response_model=list[SanctionTarget])
async def list_sanctions(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)
    cls_placeholders = ", ".join(f"${j + 1}" for j in range(len(allowed)))
    params: list = list(allowed)
    i = len(allowed) + 1
    params.extend([limit, offset])
    query = (
        f"SELECT * FROM econ_sanction_targets "
        f"WHERE classification IN ({cls_placeholders}) "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_sanction(r) for r in rows]


@router.post("/sanctions", response_model=SanctionTarget, status_code=status.HTTP_201_CREATED)
async def create_sanction(
    request: Request,
    body: CreateSanctionTargetRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO econ_sanction_targets (
            name, country_code, target_type, sanction_type, status,
            imposing_parties, effective_date, annual_gdp_impact_pct, notes, classification
        ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10)
        RETURNING *
        """,
        body.name,
        body.country_code,
        body.target_type,
        body.sanction_type.value,
        body.status.value,
        json.dumps(body.imposing_parties),
        body.effective_date,
        body.annual_gdp_impact_pct,
        body.notes,
        body.classification.value,
    )
    return _row_to_sanction(row)


@router.get("/sanctions/{sanction_id}", response_model=SanctionTarget)
async def get_sanction(
    sanction_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM econ_sanction_targets WHERE id = $1::uuid", sanction_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Sanction target not found")
    target = _row_to_sanction(row)
    enforce_classification_ceiling(user, target.classification.value)
    return target


@router.put("/sanctions/{sanction_id}", response_model=SanctionTarget)
async def update_sanction(
    sanction_id: str,
    request: Request,
    body: UpdateSanctionTargetRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM econ_sanction_targets WHERE id = $1::uuid", sanction_id
    )
    if existing:
        enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates = []
    params: list = []
    i = 1

    if body.name is not None:
        updates.append(f"name = ${i}")
        params.append(body.name)
        i += 1
    if body.status is not None:
        updates.append(f"status = ${i}")
        params.append(body.status.value)
        i += 1
    if body.sanction_type is not None:
        updates.append(f"sanction_type = ${i}")
        params.append(body.sanction_type.value)
        i += 1
    if body.imposing_parties is not None:
        updates.append(f"imposing_parties = ${i}::jsonb")
        params.append(json.dumps(body.imposing_parties))
        i += 1
    if body.annual_gdp_impact_pct is not None:
        updates.append(f"annual_gdp_impact_pct = ${i}")
        params.append(body.annual_gdp_impact_pct)
        i += 1
    if body.notes is not None:
        updates.append(f"notes = ${i}")
        params.append(body.notes)
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM econ_sanction_targets WHERE id = $1::uuid", sanction_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Sanction target not found")
        return _row_to_sanction(row)

    updates.append("updated_at = NOW()")
    params.append(sanction_id)
    query = (
        f"UPDATE econ_sanction_targets SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Sanction target not found")
    return _row_to_sanction(row)


@router.delete("/sanctions/{sanction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sanction(
    sanction_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM econ_sanction_targets WHERE id = $1::uuid", sanction_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Sanction target not found")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_sanction(row) -> SanctionTarget:
    imposing = row["imposing_parties"]
    if isinstance(imposing, str):
        imposing = json.loads(imposing)
    elif imposing is None:
        imposing = []

    return SanctionTarget(
        id=row["id"],
        name=row["name"],
        country_code=row["country_code"],
        target_type=row["target_type"],
        sanction_type=SanctionType(row["sanction_type"]),
        status=SanctionStatus(row["status"]),
        imposing_parties=imposing,
        effective_date=row["effective_date"],
        annual_gdp_impact_pct=row["annual_gdp_impact_pct"],
        notes=row["notes"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

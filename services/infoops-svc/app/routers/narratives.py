from __future__ import annotations

"""Narrative threat CRUD endpoints."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.engine.analysis import analyze_narrative
from app.models import (
    ClassificationLevel,
    CreateNarrativeThreatRequest,
    NarrativeAnalysis,
    NarrativeStatus,
    NarrativeThreat,
    NarrativeThreatLevel,
    PlatformType,
    UpdateNarrativeThreatRequest,
)

router = APIRouter(tags=["narratives"])


@router.get("/narratives", response_model=list[NarrativeThreat])
async def list_narratives(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    status: NarrativeStatus | None = None,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)
    cls_placeholders = ", ".join(f"${j + 1}" for j in range(len(allowed)))
    params: list = list(allowed)
    i = len(allowed) + 1

    conditions = [f"classification IN ({cls_placeholders})"]
    if status is not None:
        conditions.append(f"status = ${i}")
        params.append(status.value)
        i += 1

    params.extend([limit, offset])
    where = " AND ".join(conditions)
    query = (
        f"SELECT * FROM infoops_narrative_threats "
        f"WHERE {where} "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_narrative(r) for r in rows]


@router.post("/narratives", response_model=NarrativeThreat, status_code=status.HTTP_201_CREATED)
async def create_narrative(
    request: Request,
    body: CreateNarrativeThreatRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    now = datetime.now(tz=timezone.utc)
    row = await db.fetchrow(
        """
        INSERT INTO infoops_narrative_threats (
            title, description, origin_country, target_countries, platforms,
            status, threat_level, spread_velocity, reach_estimate,
            key_claims, counter_narratives, first_detected, last_updated, classification
        ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8, $9,
                  $10::jsonb, $11::jsonb, $12, $13, $14)
        RETURNING *
        """,
        body.title,
        body.description,
        body.origin_country,
        json.dumps(body.target_countries),
        json.dumps([p.value for p in body.platforms]),
        body.status.value,
        body.threat_level.value,
        body.spread_velocity,
        body.reach_estimate,
        json.dumps(body.key_claims),
        json.dumps(body.counter_narratives),
        now,
        now,
        body.classification.value,
    )
    return _row_to_narrative(row)


@router.get("/narratives/{narrative_id}", response_model=NarrativeThreat)
async def get_narrative(
    narrative_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM infoops_narrative_threats WHERE id = $1::uuid", narrative_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Narrative threat not found")
    narrative = _row_to_narrative(row)
    enforce_classification_ceiling(user, narrative.classification.value)
    return narrative


@router.put("/narratives/{narrative_id}", response_model=NarrativeThreat)
async def update_narrative(
    narrative_id: str,
    request: Request,
    body: UpdateNarrativeThreatRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM infoops_narrative_threats WHERE id = $1::uuid", narrative_id
    )
    if existing:
        enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates = []
    params: list = []
    i = 1

    if body.title is not None:
        updates.append(f"title = ${i}")
        params.append(body.title)
        i += 1
    if body.description is not None:
        updates.append(f"description = ${i}")
        params.append(body.description)
        i += 1
    if body.origin_country is not None:
        updates.append(f"origin_country = ${i}")
        params.append(body.origin_country)
        i += 1
    if body.target_countries is not None:
        updates.append(f"target_countries = ${i}::jsonb")
        params.append(json.dumps(body.target_countries))
        i += 1
    if body.platforms is not None:
        updates.append(f"platforms = ${i}::jsonb")
        params.append(json.dumps([p.value for p in body.platforms]))
        i += 1
    if body.status is not None:
        updates.append(f"status = ${i}")
        params.append(body.status.value)
        i += 1
    if body.threat_level is not None:
        updates.append(f"threat_level = ${i}")
        params.append(body.threat_level.value)
        i += 1
    if body.spread_velocity is not None:
        updates.append(f"spread_velocity = ${i}")
        params.append(body.spread_velocity)
        i += 1
    if body.reach_estimate is not None:
        updates.append(f"reach_estimate = ${i}")
        params.append(body.reach_estimate)
        i += 1
    if body.key_claims is not None:
        updates.append(f"key_claims = ${i}::jsonb")
        params.append(json.dumps(body.key_claims))
        i += 1
    if body.counter_narratives is not None:
        updates.append(f"counter_narratives = ${i}::jsonb")
        params.append(json.dumps(body.counter_narratives))
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM infoops_narrative_threats WHERE id = $1::uuid", narrative_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Narrative threat not found")
        return _row_to_narrative(row)

    updates.append("last_updated = NOW()")
    updates.append("updated_at = NOW()")
    params.append(narrative_id)
    query = (
        f"UPDATE infoops_narrative_threats SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Narrative threat not found")
    return _row_to_narrative(row)


@router.delete("/narratives/{narrative_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_narrative(
    narrative_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM infoops_narrative_threats WHERE id = $1::uuid", narrative_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Narrative threat not found")


@router.post("/narratives/{narrative_id}/analyze", response_model=NarrativeAnalysis)
async def analyze_narrative_endpoint(
    narrative_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM infoops_narrative_threats WHERE id = $1::uuid", narrative_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Narrative threat not found")
    enforce_classification_ceiling(user, row["classification"])

    narrative_dict = dict(row)
    for field in ("platforms", "counter_narratives", "key_claims", "target_countries"):
        val = narrative_dict.get(field)
        if isinstance(val, str):
            narrative_dict[field] = json.loads(val)
        elif val is None:
            narrative_dict[field] = []

    return analyze_narrative(narrative_dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_narrative(row) -> NarrativeThreat:
    def _load_json_list(val):
        if isinstance(val, str):
            return json.loads(val)
        return val if val is not None else []

    platforms_raw = _load_json_list(row["platforms"])
    platforms = [PlatformType(p) for p in platforms_raw]

    return NarrativeThreat(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        origin_country=row["origin_country"],
        target_countries=_load_json_list(row["target_countries"]),
        platforms=platforms,
        status=NarrativeStatus(row["status"]),
        threat_level=NarrativeThreatLevel(row["threat_level"]),
        spread_velocity=float(row["spread_velocity"]),
        reach_estimate=int(row["reach_estimate"]),
        key_claims=_load_json_list(row["key_claims"]),
        counter_narratives=_load_json_list(row["counter_narratives"]),
        first_detected=row["first_detected"],
        last_updated=row["last_updated"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

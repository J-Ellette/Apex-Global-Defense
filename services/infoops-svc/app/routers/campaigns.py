from __future__ import annotations

"""Influence campaign CRUD endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.models import (
    AttributionConfidence,
    CampaignStatus,
    ClassificationLevel,
    CreateInfluenceCampaignRequest,
    InfluenceCampaign,
    PlatformType,
    UpdateInfluenceCampaignRequest,
)

router = APIRouter(tags=["campaigns"])


@router.get("/campaigns", response_model=list[InfluenceCampaign])
async def list_campaigns(
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
        f"SELECT * FROM infoops_influence_campaigns "
        f"WHERE classification IN ({cls_placeholders}) "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_campaign(r) for r in rows]


@router.post("/campaigns", response_model=InfluenceCampaign, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: Request,
    body: CreateInfluenceCampaignRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO infoops_influence_campaigns (
            name, description, attributed_actor, attribution_confidence,
            sponsoring_state, target_countries, target_demographics, platforms,
            status, campaign_objectives, estimated_budget_usd,
            start_date, end_date, linked_narrative_ids, classification
        ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb,
                  $9, $10::jsonb, $11, $12, $13, $14::jsonb, $15)
        RETURNING *
        """,
        body.name,
        body.description,
        body.attributed_actor,
        body.attribution_confidence.value,
        body.sponsoring_state,
        json.dumps(body.target_countries),
        json.dumps(body.target_demographics),
        json.dumps([p.value for p in body.platforms]),
        body.status.value,
        json.dumps(body.campaign_objectives),
        body.estimated_budget_usd,
        body.start_date,
        body.end_date,
        json.dumps([str(nid) for nid in body.linked_narrative_ids]),
        body.classification.value,
    )
    return _row_to_campaign(row)


@router.get("/campaigns/{campaign_id}", response_model=InfluenceCampaign)
async def get_campaign(
    campaign_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM infoops_influence_campaigns WHERE id = $1::uuid", campaign_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Influence campaign not found")
    campaign = _row_to_campaign(row)
    enforce_classification_ceiling(user, campaign.classification.value)
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=InfluenceCampaign)
async def update_campaign(
    campaign_id: str,
    request: Request,
    body: UpdateInfluenceCampaignRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM infoops_influence_campaigns WHERE id = $1::uuid", campaign_id
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
    if body.description is not None:
        updates.append(f"description = ${i}")
        params.append(body.description)
        i += 1
    if body.attributed_actor is not None:
        updates.append(f"attributed_actor = ${i}")
        params.append(body.attributed_actor)
        i += 1
    if body.attribution_confidence is not None:
        updates.append(f"attribution_confidence = ${i}")
        params.append(body.attribution_confidence.value)
        i += 1
    if body.sponsoring_state is not None:
        updates.append(f"sponsoring_state = ${i}")
        params.append(body.sponsoring_state)
        i += 1
    if body.target_countries is not None:
        updates.append(f"target_countries = ${i}::jsonb")
        params.append(json.dumps(body.target_countries))
        i += 1
    if body.target_demographics is not None:
        updates.append(f"target_demographics = ${i}::jsonb")
        params.append(json.dumps(body.target_demographics))
        i += 1
    if body.platforms is not None:
        updates.append(f"platforms = ${i}::jsonb")
        params.append(json.dumps([p.value for p in body.platforms]))
        i += 1
    if body.status is not None:
        updates.append(f"status = ${i}")
        params.append(body.status.value)
        i += 1
    if body.campaign_objectives is not None:
        updates.append(f"campaign_objectives = ${i}::jsonb")
        params.append(json.dumps(body.campaign_objectives))
        i += 1
    if body.estimated_budget_usd is not None:
        updates.append(f"estimated_budget_usd = ${i}")
        params.append(body.estimated_budget_usd)
        i += 1
    if body.start_date is not None:
        updates.append(f"start_date = ${i}")
        params.append(body.start_date)
        i += 1
    if body.end_date is not None:
        updates.append(f"end_date = ${i}")
        params.append(body.end_date)
        i += 1
    if body.linked_narrative_ids is not None:
        updates.append(f"linked_narrative_ids = ${i}::jsonb")
        params.append(json.dumps([str(nid) for nid in body.linked_narrative_ids]))
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM infoops_influence_campaigns WHERE id = $1::uuid", campaign_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Influence campaign not found")
        return _row_to_campaign(row)

    updates.append("updated_at = NOW()")
    params.append(campaign_id)
    query = (
        f"UPDATE infoops_influence_campaigns SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Influence campaign not found")
    return _row_to_campaign(row)


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM infoops_influence_campaigns WHERE id = $1::uuid", campaign_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Influence campaign not found")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_campaign(row) -> InfluenceCampaign:
    def _load_json_list(val):
        if isinstance(val, str):
            import json as _json
            return _json.loads(val)
        return val if val is not None else []

    platforms_raw = _load_json_list(row["platforms"])
    platforms = [PlatformType(p) for p in platforms_raw]

    linked_ids_raw = _load_json_list(row["linked_narrative_ids"])
    from uuid import UUID
    linked_ids = [UUID(nid) for nid in linked_ids_raw]

    start_date = row.get("start_date")
    end_date = row.get("end_date")

    return InfluenceCampaign(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        attributed_actor=row["attributed_actor"],
        attribution_confidence=AttributionConfidence(row["attribution_confidence"]),
        sponsoring_state=row["sponsoring_state"],
        target_countries=_load_json_list(row["target_countries"]),
        target_demographics=_load_json_list(row["target_demographics"]),
        platforms=platforms,
        status=CampaignStatus(row["status"]),
        campaign_objectives=_load_json_list(row["campaign_objectives"]),
        estimated_budget_usd=row["estimated_budget_usd"],
        start_date=str(start_date) if start_date is not None else None,
        end_date=str(end_date) if end_date is not None else None,
        linked_narrative_ids=linked_ids,
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

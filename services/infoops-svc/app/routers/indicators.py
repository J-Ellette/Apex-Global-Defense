from __future__ import annotations

"""Disinformation indicator CRUD endpoints."""

import json
from datetime import datetime, timezone
from uuid import UUID

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
    CreateDisinformationIndicatorRequest,
    DisinformationIndicator,
    IndicatorType,
    PlatformType,
)

router = APIRouter(tags=["indicators"])


@router.get("/indicators", response_model=list[DisinformationIndicator])
async def list_indicators(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    campaign_id: str | None = None,
    indicator_type: IndicatorType | None = None,
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
    if campaign_id is not None:
        conditions.append(f"linked_campaign_id = ${i}::uuid")
        params.append(campaign_id)
        i += 1
    if indicator_type is not None:
        conditions.append(f"indicator_type = ${i}")
        params.append(indicator_type.value)
        i += 1

    params.extend([limit, offset])
    where = " AND ".join(conditions)
    query = (
        f"SELECT * FROM infoops_disinformation_indicators "
        f"WHERE {where} "
        f"ORDER BY detected_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_indicator(r) for r in rows]


@router.post("/indicators", response_model=DisinformationIndicator, status_code=status.HTTP_201_CREATED)
async def create_indicator(
    request: Request,
    body: CreateDisinformationIndicatorRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    detected_at = body.detected_at or datetime.now(tz=timezone.utc)
    row = await db.fetchrow(
        """
        INSERT INTO infoops_disinformation_indicators (
            indicator_type, title, description, source_url, platform,
            detected_at, confidence_score, linked_campaign_id, linked_narrative_id,
            is_verified, classification
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING *
        """,
        body.indicator_type.value,
        body.title,
        body.description,
        body.source_url,
        body.platform.value,
        detected_at,
        body.confidence_score,
        str(body.linked_campaign_id) if body.linked_campaign_id else None,
        str(body.linked_narrative_id) if body.linked_narrative_id else None,
        body.is_verified,
        body.classification.value,
    )
    return _row_to_indicator(row)


@router.get("/indicators/{indicator_id}", response_model=DisinformationIndicator)
async def get_indicator(
    indicator_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM infoops_disinformation_indicators WHERE id = $1::uuid", indicator_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Disinformation indicator not found")
    indicator = _row_to_indicator(row)
    enforce_classification_ceiling(user, indicator.classification.value)
    return indicator


@router.delete("/indicators/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indicator(
    indicator_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM infoops_disinformation_indicators WHERE id = $1::uuid", indicator_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Disinformation indicator not found")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_indicator(row) -> DisinformationIndicator:
    return DisinformationIndicator(
        id=row["id"],
        indicator_type=IndicatorType(row["indicator_type"]),
        title=row["title"],
        description=row["description"],
        source_url=row["source_url"],
        platform=PlatformType(row["platform"]),
        detected_at=row["detected_at"],
        confidence_score=float(row["confidence_score"]),
        linked_campaign_id=UUID(str(row["linked_campaign_id"])) if row["linked_campaign_id"] else None,
        linked_narrative_id=UUID(str(row["linked_narrative_id"])) if row["linked_narrative_id"] else None,
        is_verified=bool(row["is_verified"]),
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

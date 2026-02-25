from __future__ import annotations

"""Attribution assessment CRUD endpoints."""

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
    AttributionAssessment,
    AttributionConfidence,
    ClassificationLevel,
    CreateAttributionAssessmentRequest,
)

router = APIRouter(tags=["attribution"])


@router.get("/attribution", response_model=list[AttributionAssessment])
async def list_assessments(
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
        f"SELECT * FROM infoops_attribution_assessments "
        f"WHERE classification IN ({cls_placeholders}) "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_assessment(r) for r in rows]


@router.post("/attribution", response_model=AttributionAssessment, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: Request,
    body: CreateAttributionAssessmentRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO infoops_attribution_assessments (
            subject, attributed_to, confidence, evidence_summary,
            supporting_indicators, dissenting_evidence, analyst_id, classification
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8)
        RETURNING *
        """,
        body.subject,
        body.attributed_to,
        body.confidence.value,
        body.evidence_summary,
        json.dumps(body.supporting_indicators),
        json.dumps(body.dissenting_evidence),
        body.analyst_id,
        body.classification.value,
    )
    return _row_to_assessment(row)


@router.get("/attribution/{assessment_id}", response_model=AttributionAssessment)
async def get_assessment(
    assessment_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM infoops_attribution_assessments WHERE id = $1::uuid", assessment_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Attribution assessment not found")
    assessment = _row_to_assessment(row)
    enforce_classification_ceiling(user, assessment.classification.value)
    return assessment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_assessment(row) -> AttributionAssessment:
    def _load_json_list(val):
        if isinstance(val, str):
            return json.loads(val)
        return val if val is not None else []

    return AttributionAssessment(
        id=row["id"],
        subject=row["subject"],
        attributed_to=row["attributed_to"],
        confidence=AttributionConfidence(row["confidence"]),
        evidence_summary=row["evidence_summary"],
        supporting_indicators=_load_json_list(row["supporting_indicators"]),
        dissenting_evidence=_load_json_list(row["dissenting_evidence"]),
        analyst_id=row["analyst_id"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

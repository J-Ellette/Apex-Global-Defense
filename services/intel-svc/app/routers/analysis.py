from __future__ import annotations

"""Analysis endpoints: entity extraction and threat assessment."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user, require_permission
from app.engine.extractor import run_extraction
from app.engine.threat import assess_threat
from app.models import (
    ExtractionRequest,
    ExtractionResult,
    ThreatAssessmentRequest,
    ThreatAssessmentResult,
)

router = APIRouter(tags=["analysis"])


@router.post("/intel/extract", response_model=ExtractionResult)
async def extract_entities_endpoint(
    request: Request,
    body: ExtractionRequest,
    user: dict = Depends(get_current_user),
):
    """
    Run entity extraction on arbitrary text.

    Returns named entities (persons, organizations, locations, weapons, events,
    dates, facilities, vehicles) extracted via deterministic NLP patterns.

    If *item_id* is provided and the item exists, the extracted entities are
    also stored back to that intel item.
    """
    require_permission(user, "scenario:read")
    result = run_extraction(body.text)

    # Optionally persist entities to the intel item
    if body.item_id is not None:
        db = request.app.state.db
        row = await db.fetchrow("SELECT id FROM intel_items WHERE id = $1", body.item_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Intel item not found")

        entities_json = [
            {"type": e.type.value, "text": e.text, "confidence": e.confidence}
            for e in result.entities
        ]
        await db.execute(
            "UPDATE intel_items SET entities = $1::jsonb WHERE id = $2",
            json.dumps(entities_json),
            body.item_id,
        )

    return result


@router.post("/intel/threat-assess", response_model=ThreatAssessmentResult)
async def threat_assessment_endpoint(
    request: Request,
    body: ThreatAssessmentRequest,
    user: dict = Depends(get_current_user),
):
    """
    Assess the threat posed by a specified actor against a target.

    Uses a deterministic weighted-indicator matrix (PMESII-PT inspired).
    If *intel_item_ids* are provided, their content is appended to the
    analysis context to improve indicator coverage.

    Output includes: threat level (NEGLIGIBLE/LOW/MODERATE/HIGH/CRITICAL),
    numeric score (0–10), active threat vectors, indicator breakdown,
    confidence level, and protective action recommendations.
    """
    require_permission(user, "scenario:read")

    # Enrich context with referenced intel items
    enriched_context = body.context or ""
    if body.intel_item_ids:
        db = request.app.state.db
        for item_id in body.intel_item_ids[:5]:  # Cap at 5 to avoid huge prompts
            row = await db.fetchrow(
                "SELECT title, content FROM intel_items WHERE id = $1", item_id
            )
            if row:
                enriched_context += f"\n\nINTEL REPORT: {row['title']}\n{row['content']}"

    enriched_request = ThreatAssessmentRequest(
        actor=body.actor,
        target=body.target,
        context=enriched_context,
        intel_item_ids=body.intel_item_ids,
    )
    return assess_threat(enriched_request)

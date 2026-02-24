from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user, require_permission
from app.engine.impact import compute_impact
from app.models import AssessImpactRequest, ImpactAssessment

router = APIRouter()


@router.post("/civilian/impact/assess", response_model=ImpactAssessment)
async def assess_impact(
    request: Request,
    body: AssessImpactRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    # Fetch population zones for the scenario (or all if no scenario)
    if body.scenario_id is not None:
        rows = await db.fetch(
            "SELECT * FROM civilian_population_zones WHERE scenario_id = $1",
            body.scenario_id,
        )
    else:
        rows = await db.fetch("SELECT * FROM civilian_population_zones")

    zones = [dict(r) for r in rows]
    events = body.events or []

    assessment = compute_impact(
        run_id=body.run_id,
        scenario_id=body.scenario_id,
        zones=zones,
        events=events,
    )

    # Persist assessment
    await db.execute(
        """
        INSERT INTO civilian_impact_assessments
            (id, run_id, scenario_id, assessed_at,
             total_civilian_casualties, total_civilian_wounded,
             total_displaced_persons, zone_impacts, methodology, notes)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """,
        assessment.id,
        assessment.run_id,
        assessment.scenario_id,
        assessment.assessed_at,
        assessment.total_civilian_casualties,
        assessment.total_civilian_wounded,
        assessment.total_displaced_persons,
        json.dumps([zi.model_dump(mode="json") for zi in assessment.zone_impacts]),
        assessment.methodology,
        assessment.notes,
    )

    return assessment


@router.get("/civilian/impact/{run_id}", response_model=ImpactAssessment)
async def get_impact_for_run(
    run_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        """
        SELECT * FROM civilian_impact_assessments
        WHERE run_id = $1
        ORDER BY assessed_at DESC
        LIMIT 1
        """,
        run_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No impact assessment found for this run")

    r = dict(row)
    zone_impacts_raw = r.get("zone_impacts")
    if isinstance(zone_impacts_raw, str):
        zone_impacts_raw = json.loads(zone_impacts_raw)

    return ImpactAssessment(
        id=r["id"],
        run_id=r["run_id"],
        scenario_id=r.get("scenario_id"),
        assessed_at=r["assessed_at"],
        total_civilian_casualties=r["total_civilian_casualties"],
        total_civilian_wounded=r["total_civilian_wounded"],
        total_displaced_persons=r["total_displaced_persons"],
        zone_impacts=zone_impacts_raw or [],
        methodology=r.get("methodology", "deterministic"),
        notes=r.get("notes"),
    )

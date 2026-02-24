"""ATT&CK techniques router — browse the MITRE ATT&CK catalog."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user, require_permission
from app.data.attack_techniques import ATTACK_TECHNIQUES, TECHNIQUES_BY_ID
from app.models import ATTACKTactic, ATTACKTechnique

router = APIRouter(tags=["techniques"])

ClaimsDepend = Annotated[dict, Depends(get_current_user)]


@router.get("/cyber/techniques", response_model=list[ATTACKTechnique])
async def list_techniques(
    claims: ClaimsDepend,
    tactic: ATTACKTactic | None = Query(default=None, description="Filter by ATT&CK tactic"),
    platform: str | None = Query(default=None, description="Filter by platform (partial match)"),
    severity: str | None = Query(default=None, description="Filter by severity (LOW/MEDIUM/HIGH/CRITICAL)"),
    q: str | None = Query(default=None, description="Full-text search on name and description"),
) -> list[ATTACKTechnique]:
    """List MITRE ATT&CK techniques with optional filtering."""
    require_permission(claims, "scenario:read")
    results = ATTACK_TECHNIQUES

    if tactic:
        results = [t for t in results if t.tactic == tactic]
    if platform:
        pl = platform.lower()
        results = [t for t in results if any(pl in p.lower() for p in t.platforms)]
    if severity:
        results = [t for t in results if t.severity == severity.upper()]
    if q:
        ql = q.lower()
        results = [t for t in results if ql in t.name.lower() or ql in t.description.lower()]

    return results


@router.get("/cyber/techniques/{technique_id}", response_model=ATTACKTechnique)
async def get_technique(technique_id: str, claims: ClaimsDepend) -> ATTACKTechnique:
    """Get a single ATT&CK technique by ID (e.g. T1566)."""
    require_permission(claims, "scenario:read")
    tech = TECHNIQUES_BY_ID.get(technique_id.upper())
    if not tech:
        raise HTTPException(status_code=404, detail=f"Technique {technique_id} not found")
    return tech

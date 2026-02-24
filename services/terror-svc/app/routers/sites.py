from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status

from app.auth import get_current_user, require_permission
from app.models import (
    CreateSiteRequest,
    CrowdDensity,
    SiteStatus,
    SiteType,
    TerrorSite,
    UpdateSiteRequest,
)

router = APIRouter(tags=["sites"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_vulnerability_score(
    physical_security: float,
    access_control: float,
    surveillance: float,
    emergency_response: float,
    crowd_density: CrowdDensity,
) -> float:
    """
    Compute composite vulnerability score (1–10).
    - Base = 10 * (1 - mean of security dimensions)
    - Crowd density multiplier amplifies risk for dense sites
    """
    base_security = (physical_security + access_control + surveillance + emergency_response) / 4.0
    raw = 10.0 * (1.0 - base_security)
    density_mult = {
        CrowdDensity.LOW: 0.8,
        CrowdDensity.MEDIUM: 1.0,
        CrowdDensity.HIGH: 1.2,
        CrowdDensity.CRITICAL: 1.4,
    }.get(crowd_density, 1.0)
    return round(min(10.0, max(1.0, raw * density_mult)), 2)


def _row_to_site(row: dict) -> TerrorSite:
    raw_agencies = row.get("assigned_agencies") or "[]"
    if isinstance(raw_agencies, str):
        agencies = json.loads(raw_agencies)
    else:
        agencies = list(raw_agencies)
    return TerrorSite(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        name=row["name"],
        site_type=SiteType(row["site_type"]),
        address=row.get("address"),
        latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
        longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
        country_code=row.get("country_code"),
        population_capacity=int(row.get("population_capacity", 0)),
        physical_security=float(row.get("physical_security", 0.5)),
        access_control=float(row.get("access_control", 0.5)),
        surveillance=float(row.get("surveillance", 0.5)),
        emergency_response=float(row.get("emergency_response", 0.5)),
        crowd_density=CrowdDensity(row.get("crowd_density", "MEDIUM")),
        vulnerability_score=float(row.get("vulnerability_score", 5.0)),
        assigned_agencies=agencies,
        notes=row.get("notes"),
        status=SiteStatus(row.get("status", "ACTIVE")),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


# ---------------------------------------------------------------------------
# Site CRUD
# ---------------------------------------------------------------------------

@router.get("/terror/sites", response_model=list[TerrorSite])
async def list_sites(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    site_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List terror target sites, optionally filtered by scenario, status, or site type."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    filters: list[str] = []
    params: list = []

    if scenario_id:
        params.append(scenario_id)
        filters.append(f"scenario_id = ${len(params)}")
    if status:
        params.append(status)
        filters.append(f"status = ${len(params)}")
    if site_type:
        params.append(site_type)
        filters.append(f"site_type = ${len(params)}")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = await db.fetch(
        f"SELECT * FROM terror_sites {where} ORDER BY vulnerability_score DESC, created_at DESC LIMIT 200",
        *params,
    )
    return [_row_to_site(dict(r)) for r in rows]


@router.post("/terror/sites", response_model=TerrorSite, status_code=http_status.HTTP_201_CREATED)
async def create_site(
    request: Request,
    body: CreateSiteRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new terror target site with vulnerability assessment."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    site_id = uuid4()
    now = datetime.now(timezone.utc)
    agencies_json = json.dumps(body.assigned_agencies)
    vuln_score = _compute_vulnerability_score(
        body.physical_security,
        body.access_control,
        body.surveillance,
        body.emergency_response,
        body.crowd_density,
    )
    await db.execute(
        """
        INSERT INTO terror_sites
          (id, scenario_id, name, site_type, address, latitude, longitude,
           country_code, population_capacity, physical_security, access_control,
           surveillance, emergency_response, crowd_density, vulnerability_score,
           assigned_agencies, notes, status, created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16::jsonb,$17,$18,$19,$20)
        """,
        site_id, body.scenario_id, body.name, body.site_type.value,
        body.address, body.latitude, body.longitude, body.country_code,
        body.population_capacity, body.physical_security, body.access_control,
        body.surveillance, body.emergency_response, body.crowd_density.value,
        vuln_score, agencies_json, body.notes, body.status.value,
        user.get("sub") or user.get("uid"), now,
    )
    return TerrorSite(
        id=site_id,
        scenario_id=body.scenario_id,
        name=body.name,
        site_type=body.site_type,
        address=body.address,
        latitude=body.latitude,
        longitude=body.longitude,
        country_code=body.country_code,
        population_capacity=body.population_capacity,
        physical_security=body.physical_security,
        access_control=body.access_control,
        surveillance=body.surveillance,
        emergency_response=body.emergency_response,
        crowd_density=body.crowd_density,
        vulnerability_score=vuln_score,
        assigned_agencies=body.assigned_agencies,
        notes=body.notes,
        status=body.status,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.get("/terror/sites/{site_id}", response_model=TerrorSite)
async def get_site(
    request: Request,
    site_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get a single terror target site by ID."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM terror_sites WHERE id = $1", site_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return _row_to_site(dict(row))


@router.put("/terror/sites/{site_id}", response_model=TerrorSite)
async def update_site(
    request: Request,
    site_id: UUID,
    body: UpdateSiteRequest,
    user: dict = Depends(get_current_user),
):
    """Update a terror target site's vulnerability dimensions or metadata."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM terror_sites WHERE id = $1", site_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Site not found")
    current = _row_to_site(dict(row))
    updated = current.model_copy(update={k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None})
    vuln_score = _compute_vulnerability_score(
        updated.physical_security,
        updated.access_control,
        updated.surveillance,
        updated.emergency_response,
        updated.crowd_density,
    )
    updated = updated.model_copy(update={"vulnerability_score": vuln_score})
    agencies_json = json.dumps(updated.assigned_agencies)
    await db.execute(
        """
        UPDATE terror_sites SET
          name=$2, site_type=$3, address=$4, latitude=$5, longitude=$6,
          country_code=$7, population_capacity=$8, physical_security=$9,
          access_control=$10, surveillance=$11, emergency_response=$12,
          crowd_density=$13, vulnerability_score=$14,
          assigned_agencies=$15::jsonb, notes=$16, status=$17
        WHERE id=$1
        """,
        site_id, updated.name, updated.site_type.value, updated.address,
        updated.latitude, updated.longitude, updated.country_code,
        updated.population_capacity, updated.physical_security,
        updated.access_control, updated.surveillance, updated.emergency_response,
        updated.crowd_density.value, vuln_score, agencies_json,
        updated.notes, updated.status.value,
    )
    return updated


@router.delete("/terror/sites/{site_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_site(
    request: Request,
    site_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a terror target site and all linked threat scenarios and response plans."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    # Cascade handled by FK ON DELETE CASCADE in schema, but explicit for plans
    await db.execute(
        "DELETE FROM terror_response_plans WHERE site_id = $1",
        site_id,
    )
    await db.execute(
        "DELETE FROM terror_threat_scenarios WHERE site_id = $1",
        site_id,
    )
    result = await db.execute("DELETE FROM terror_sites WHERE id = $1", site_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Site not found")

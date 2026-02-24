from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status

from app.auth import get_current_user, require_permission
from app.data.ied_types import IED_TYPE_MAP
from app.models import (
    CreateIncidentRequest,
    DetonationType,
    IEDIncident,
    IncidentStatus,
    TargetType,
    UpdateIncidentRequest,
)

router = APIRouter(tags=["incidents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_incident(row: dict) -> IEDIncident:
    return IEDIncident(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        ied_type_id=row["ied_type_id"],
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        location_description=row.get("location_description"),
        status=IncidentStatus(row.get("status", "SUSPECTED")),
        detonation_type=DetonationType(row.get("detonation_type", "UNKNOWN")),
        target_type=TargetType(row.get("target_type", "UNKNOWN")),
        placement_date=row.get("placement_date"),
        detection_date=row.get("detection_date"),
        detonation_date=row.get("detonation_date"),
        estimated_yield_kg=float(row["estimated_yield_kg"]) if row.get("estimated_yield_kg") is not None else None,
        casualties_killed=int(row.get("casualties_killed", 0)),
        casualties_wounded=int(row.get("casualties_wounded", 0)),
        attributed_cell_id=row.get("attributed_cell_id"),
        notes=row.get("notes"),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


# ---------------------------------------------------------------------------
# IED Type catalog
# ---------------------------------------------------------------------------

@router.get("/asym/ied-types", response_model=list)
async def list_ied_types(
    category: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List IED type catalog with optional category filter."""
    require_permission(user, "scenario:read")
    from app.data.ied_types import IED_TYPE_CATALOG
    results = IED_TYPE_CATALOG
    if category:
        results = [t for t in results if t.category.value == category.upper()]
    return results


@router.get("/asym/ied-types/{type_id}")
async def get_ied_type(
    type_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a single IED type by ID."""
    require_permission(user, "scenario:read")
    entry = IED_TYPE_MAP.get(type_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"IED type '{type_id}' not found")
    return entry


# ---------------------------------------------------------------------------
# IED Incident CRUD
# ---------------------------------------------------------------------------

@router.get("/asym/incidents", response_model=list[IEDIncident])
async def list_incidents(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List IED incidents, optionally filtered by scenario and/or status."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    if scenario_id and status:
        rows = await db.fetch(
            "SELECT * FROM asym_ied_incidents WHERE scenario_id=$1 AND status=$2 ORDER BY created_at DESC",
            scenario_id, status,
        )
    elif scenario_id:
        rows = await db.fetch(
            "SELECT * FROM asym_ied_incidents WHERE scenario_id=$1 ORDER BY created_at DESC",
            scenario_id,
        )
    elif status:
        rows = await db.fetch(
            "SELECT * FROM asym_ied_incidents WHERE status=$1 ORDER BY created_at DESC LIMIT 500",
            status,
        )
    else:
        rows = await db.fetch("SELECT * FROM asym_ied_incidents ORDER BY created_at DESC LIMIT 500")
    return [_row_to_incident(dict(r)) for r in rows]


@router.post("/asym/incidents", response_model=IEDIncident, status_code=http_status.HTTP_201_CREATED)
async def create_incident(
    request: Request,
    body: CreateIncidentRequest,
    user: dict = Depends(get_current_user),
):
    """Log a new IED incident."""
    require_permission(user, "scenario:write")
    if body.ied_type_id not in IED_TYPE_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown IED type: {body.ied_type_id}")
    db = request.app.state.db
    incident_id = uuid4()
    now = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO asym_ied_incidents
          (id, scenario_id, ied_type_id, latitude, longitude, location_description,
           status, detonation_type, target_type, placement_date, detection_date,
           detonation_date, estimated_yield_kg, casualties_killed, casualties_wounded,
           attributed_cell_id, notes, created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
        """,
        incident_id, body.scenario_id, body.ied_type_id, body.latitude, body.longitude,
        body.location_description, body.status.value, body.detonation_type.value,
        body.target_type.value, body.placement_date, body.detection_date,
        body.detonation_date, body.estimated_yield_kg, body.casualties_killed,
        body.casualties_wounded, body.attributed_cell_id, body.notes,
        user.get("sub") or user.get("uid"), now,
    )
    return IEDIncident(
        id=incident_id,
        scenario_id=body.scenario_id,
        ied_type_id=body.ied_type_id,
        latitude=body.latitude,
        longitude=body.longitude,
        location_description=body.location_description,
        status=body.status,
        detonation_type=body.detonation_type,
        target_type=body.target_type,
        placement_date=body.placement_date,
        detection_date=body.detection_date,
        detonation_date=body.detonation_date,
        estimated_yield_kg=body.estimated_yield_kg,
        casualties_killed=body.casualties_killed,
        casualties_wounded=body.casualties_wounded,
        attributed_cell_id=body.attributed_cell_id,
        notes=body.notes,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.get("/asym/incidents/{incident_id}", response_model=IEDIncident)
async def get_incident(
    request: Request,
    incident_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get a single IED incident by ID."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM asym_ied_incidents WHERE id = $1", incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _row_to_incident(dict(row))


@router.put("/asym/incidents/{incident_id}", response_model=IEDIncident)
async def update_incident(
    request: Request,
    incident_id: UUID,
    body: UpdateIncidentRequest,
    user: dict = Depends(get_current_user),
):
    """Update an IED incident record."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM asym_ied_incidents WHERE id = $1", incident_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    current = _row_to_incident(dict(row))
    update_data = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    updated = current.model_copy(update=update_data)

    if body.ied_type_id and body.ied_type_id not in IED_TYPE_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown IED type: {body.ied_type_id}")

    await db.execute(
        """
        UPDATE asym_ied_incidents SET
          ied_type_id=$2, latitude=$3, longitude=$4, location_description=$5,
          status=$6, detonation_type=$7, target_type=$8, placement_date=$9,
          detection_date=$10, detonation_date=$11, estimated_yield_kg=$12,
          casualties_killed=$13, casualties_wounded=$14,
          attributed_cell_id=$15, notes=$16
        WHERE id=$1
        """,
        incident_id, updated.ied_type_id, updated.latitude, updated.longitude,
        updated.location_description, updated.status.value, updated.detonation_type.value,
        updated.target_type.value, updated.placement_date, updated.detection_date,
        updated.detonation_date, updated.estimated_yield_kg,
        updated.casualties_killed, updated.casualties_wounded,
        updated.attributed_cell_id, updated.notes,
    )
    return updated


@router.delete("/asym/incidents/{incident_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_incident(
    request: Request,
    incident_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete an IED incident."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute("DELETE FROM asym_ied_incidents WHERE id = $1", incident_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Incident not found")

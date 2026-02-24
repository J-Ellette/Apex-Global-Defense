from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status

from app.auth import get_current_user, require_permission
from app.models import (
    AgencyEntry,
    AgencyRole,
    AgencyType,
    CreateResponsePlanRequest,
    ResponsePlan,
    ResponsePlanStatus,
    ThreatLevel,
    UpdateResponsePlanRequest,
)

router = APIRouter(tags=["plans"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_agencies(raw) -> list[AgencyEntry]:
    if isinstance(raw, str):
        items = json.loads(raw)
    elif raw is None:
        return []
    else:
        items = list(raw)
    result = []
    for item in items:
        if isinstance(item, str):
            item = json.loads(item)
        result.append(AgencyEntry(
            agency_name=item.get("agency_name", ""),
            agency_type=AgencyType(item.get("agency_type", "LOCAL")),
            role=AgencyRole(item.get("role", "SUPPORTING")),
            contact=item.get("contact"),
            notes=item.get("notes"),
        ))
    return result


def _parse_routes(raw) -> list[str]:
    if isinstance(raw, str):
        return json.loads(raw)
    elif raw is None:
        return []
    return list(raw)


def _row_to_plan(row: dict) -> ResponsePlan:
    return ResponsePlan(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        site_id=row["site_id"],
        threat_scenario_id=row.get("threat_scenario_id"),
        title=row["title"],
        description=row.get("description"),
        agencies=_parse_agencies(row.get("agencies")),
        evacuation_routes=_parse_routes(row.get("evacuation_routes")),
        shelter_capacity=int(row.get("shelter_capacity", 0)),
        estimated_response_time_min=int(row.get("estimated_response_time_min", 10)),
        status=ResponsePlanStatus(row.get("status", "DRAFT")),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


# ---------------------------------------------------------------------------
# Response Plan CRUD
# ---------------------------------------------------------------------------

@router.get("/terror/response-plans", response_model=list[ResponsePlan])
async def list_response_plans(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    site_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List response plans, optionally filtered by scenario, site, or status."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    filters: list[str] = []
    params: list = []

    if scenario_id:
        params.append(scenario_id)
        filters.append(f"scenario_id = ${len(params)}")
    if site_id:
        params.append(site_id)
        filters.append(f"site_id = ${len(params)}")
    if status:
        params.append(status.upper())
        filters.append(f"status = ${len(params)}")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = await db.fetch(
        f"SELECT * FROM terror_response_plans {where} ORDER BY created_at DESC LIMIT 200",
        *params,
    )
    return [_row_to_plan(dict(r)) for r in rows]


@router.post(
    "/terror/response-plans",
    response_model=ResponsePlan,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_response_plan(
    request: Request,
    body: CreateResponsePlanRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new multi-agency response plan for a site."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    # Validate site exists
    site_row = await db.fetchrow("SELECT id FROM terror_sites WHERE id = $1", body.site_id)
    if site_row is None:
        raise HTTPException(status_code=400, detail=f"Site {body.site_id} not found")

    plan_id = uuid4()
    now = datetime.now(timezone.utc)
    agencies_json = json.dumps([a.model_dump() for a in body.agencies])
    routes_json = json.dumps(body.evacuation_routes)

    await db.execute(
        """
        INSERT INTO terror_response_plans
          (id, scenario_id, site_id, threat_scenario_id, title, description,
           agencies, evacuation_routes, shelter_capacity,
           estimated_response_time_min, status, created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9,$10,$11,$12,$13)
        """,
        plan_id, body.scenario_id, body.site_id, body.threat_scenario_id,
        body.title, body.description, agencies_json, routes_json,
        body.shelter_capacity, body.estimated_response_time_min, body.status.value,
        user.get("sub") or user.get("uid"), now,
    )
    return ResponsePlan(
        id=plan_id,
        scenario_id=body.scenario_id,
        site_id=body.site_id,
        threat_scenario_id=body.threat_scenario_id,
        title=body.title,
        description=body.description,
        agencies=body.agencies,
        evacuation_routes=body.evacuation_routes,
        shelter_capacity=body.shelter_capacity,
        estimated_response_time_min=body.estimated_response_time_min,
        status=body.status,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.get("/terror/response-plans/{plan_id}", response_model=ResponsePlan)
async def get_response_plan(
    request: Request,
    plan_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get a single response plan by ID."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM terror_response_plans WHERE id = $1", plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Response plan not found")
    return _row_to_plan(dict(row))


@router.put("/terror/response-plans/{plan_id}", response_model=ResponsePlan)
async def update_response_plan(
    request: Request,
    plan_id: UUID,
    body: UpdateResponsePlanRequest,
    user: dict = Depends(get_current_user),
):
    """Update a response plan."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM terror_response_plans WHERE id = $1", plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Response plan not found")
    current = _row_to_plan(dict(row))
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    updated = current.model_copy(update=updates)
    agencies_json = json.dumps([a.model_dump() for a in updated.agencies])
    routes_json = json.dumps(updated.evacuation_routes)
    await db.execute(
        """
        UPDATE terror_response_plans SET
          title=$2, description=$3, agencies=$4::jsonb, evacuation_routes=$5::jsonb,
          shelter_capacity=$6, estimated_response_time_min=$7, status=$8
        WHERE id=$1
        """,
        plan_id, updated.title, updated.description, agencies_json, routes_json,
        updated.shelter_capacity, updated.estimated_response_time_min, updated.status.value,
    )
    return updated


@router.delete("/terror/response-plans/{plan_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_response_plan(
    request: Request,
    plan_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a response plan."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute("DELETE FROM terror_response_plans WHERE id = $1", plan_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Response plan not found")

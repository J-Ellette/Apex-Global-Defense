from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user, require_permission
from app.models import (
    CreateRefugeeFlowRequest,
    DisplacementStatus,
    RefugeeFlow,
    UpdateRefugeeFlowRequest,
)

router = APIRouter()

_SEED_FLOWS: list[dict] = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000201"),
        "scenario_id": None,
        "origin_zone_id": None,
        "origin_name": "Eastern Ukraine",
        "destination_name": "Poland",
        "origin_lat": 48.3794,
        "origin_lon": 31.1656,
        "destination_lat": 51.9194,
        "destination_lon": 19.1451,
        "displaced_persons": 3500000,
        "status": "CONFIRMED",
        "started_at": datetime(2022, 2, 24, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000202"),
        "scenario_id": None,
        "origin_zone_id": None,
        "origin_name": "Northern Syria",
        "destination_name": "Turkey",
        "origin_lat": 36.2021,
        "origin_lon": 37.1343,
        "destination_lat": 38.9637,
        "destination_lon": 35.2433,
        "displaced_persons": 3600000,
        "status": "CONFIRMED",
        "started_at": datetime(2015, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000203"),
        "scenario_id": None,
        "origin_zone_id": None,
        "origin_name": "Afghanistan",
        "destination_name": "Pakistan",
        "origin_lat": 33.9391,
        "origin_lon": 67.7100,
        "destination_lat": 30.3753,
        "destination_lon": 69.3451,
        "displaced_persons": 1400000,
        "status": "CONFIRMED",
        "started_at": datetime(2021, 8, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000204"),
        "scenario_id": None,
        "origin_zone_id": None,
        "origin_name": "Southern Somalia",
        "destination_name": "Kenya",
        "origin_lat": 2.0469,
        "origin_lon": 45.3182,
        "destination_lat": -1.2921,
        "destination_lon": 36.8219,
        "displaced_persons": 280000,
        "status": "CONFIRMED",
        "started_at": datetime(2020, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000205"),
        "scenario_id": None,
        "origin_zone_id": None,
        "origin_name": "Darfur, Sudan",
        "destination_name": "Chad",
        "origin_lat": 13.5000,
        "origin_lon": 25.0000,
        "destination_lat": 15.4542,
        "destination_lon": 18.7322,
        "displaced_persons": 600000,
        "status": "CONFIRMED",
        "started_at": datetime(2023, 4, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
]


def _row_to_flow(row: dict) -> RefugeeFlow:
    return RefugeeFlow(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        origin_zone_id=row.get("origin_zone_id"),
        origin_name=row["origin_name"],
        destination_name=row["destination_name"],
        origin_lat=row["origin_lat"],
        origin_lon=row["origin_lon"],
        destination_lat=row["destination_lat"],
        destination_lon=row["destination_lon"],
        displaced_persons=row["displaced_persons"],
        status=DisplacementStatus(row["status"]),
        started_at=row["started_at"],
        updated_at=row["updated_at"],
    )


@router.get("/civilian/flows", response_model=list[RefugeeFlow])
async def list_refugee_flows(
    request: Request,
    scenario_id: Optional[UUID] = Query(default=None),
    status: Optional[DisplacementStatus] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    conditions = []
    params: list = []

    if scenario_id is not None:
        params.append(scenario_id)
        conditions.append(f"scenario_id = ${len(params)}")
    if status is not None:
        params.append(status.value)
        conditions.append(f"status = ${len(params)}")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)
    rows = await db.fetch(
        f"SELECT * FROM civilian_refugee_flows {where} ORDER BY started_at DESC LIMIT ${len(params)}",
        *params,
    )

    if not rows:
        seeds = _SEED_FLOWS
        if scenario_id is not None:
            seeds = [f for f in seeds if f["scenario_id"] == scenario_id]
        if status is not None:
            seeds = [f for f in seeds if f["status"] == status.value]
        return [_row_to_flow(f) for f in seeds[:limit]]

    return [_row_to_flow(dict(r)) for r in rows]


@router.post("/civilian/flows", response_model=RefugeeFlow, status_code=201)
async def create_refugee_flow(
    request: Request,
    body: CreateRefugeeFlowRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    flow_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO civilian_refugee_flows
            (id, scenario_id, origin_zone_id, origin_name, destination_name,
             origin_lat, origin_lon, destination_lat, destination_lon,
             displaced_persons, status, started_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        """,
        flow_id,
        body.scenario_id,
        body.origin_zone_id,
        body.origin_name,
        body.destination_name,
        body.origin_lat,
        body.origin_lon,
        body.destination_lat,
        body.destination_lon,
        body.displaced_persons,
        body.status.value,
        now,
        now,
    )
    return RefugeeFlow(
        id=flow_id,
        scenario_id=body.scenario_id,
        origin_zone_id=body.origin_zone_id,
        origin_name=body.origin_name,
        destination_name=body.destination_name,
        origin_lat=body.origin_lat,
        origin_lon=body.origin_lon,
        destination_lat=body.destination_lat,
        destination_lon=body.destination_lon,
        displaced_persons=body.displaced_persons,
        status=body.status,
        started_at=now,
        updated_at=now,
    )


@router.get("/civilian/flows/{flow_id}", response_model=RefugeeFlow)
async def get_refugee_flow(
    flow_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM civilian_refugee_flows WHERE id = $1", flow_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Refugee flow not found")
    return _row_to_flow(dict(row))


@router.put("/civilian/flows/{flow_id}", response_model=RefugeeFlow)
async def update_refugee_flow(
    flow_id: UUID,
    request: Request,
    body: UpdateRefugeeFlowRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM civilian_refugee_flows WHERE id = $1", flow_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Refugee flow not found")

    current = dict(row)
    now = datetime.now(timezone.utc)

    new_persons = body.displaced_persons if body.displaced_persons is not None else current["displaced_persons"]
    new_status = body.status.value if body.status is not None else current["status"]
    new_dest = body.destination_name if body.destination_name is not None else current["destination_name"]

    await db.execute(
        """
        UPDATE civilian_refugee_flows
        SET displaced_persons=$1, status=$2, destination_name=$3, updated_at=$4
        WHERE id=$5
        """,
        new_persons,
        new_status,
        new_dest,
        now,
        flow_id,
    )
    current.update(
        displaced_persons=new_persons,
        status=new_status,
        destination_name=new_dest,
        updated_at=now,
    )
    return _row_to_flow(current)


@router.delete("/civilian/flows/{flow_id}", status_code=204)
async def delete_refugee_flow(
    flow_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM civilian_refugee_flows WHERE id = $1", flow_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Refugee flow not found")

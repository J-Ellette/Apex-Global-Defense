from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user, require_permission
from app.models import (
    CorridorStatus,
    CreateCorridorRequest,
    HumanitarianCorridor,
    UpdateCorridorRequest,
)

router = APIRouter()

_SEED_CORRIDORS: list[dict] = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000301"),
        "scenario_id": None,
        "name": "Mariupol Evacuation Corridor",
        "waypoints": [
            {"lat": 47.0970, "lon": 37.5426},
            {"lat": 47.3000, "lon": 36.8000},
            {"lat": 47.5500, "lon": 35.5000},
        ],
        "status": "CLOSED",
        "notes": "Previously negotiated corridor; closed due to active shelling.",
        "created_at": datetime(2022, 3, 5, tzinfo=timezone.utc),
        "updated_at": datetime(2022, 5, 17, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000302"),
        "scenario_id": None,
        "name": "Aleppo Aid Corridor",
        "waypoints": [
            {"lat": 36.2021, "lon": 37.1343},
            {"lat": 36.5000, "lon": 36.7000},
            {"lat": 36.8000, "lon": 36.1500},
        ],
        "status": "RESTRICTED",
        "notes": "UN-monitored aid delivery route; convoys require 48h advance notice.",
        "created_at": datetime(2016, 10, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000303"),
        "scenario_id": None,
        "name": "Kabul-Kandahar Humanitarian Route",
        "waypoints": [
            {"lat": 34.5553, "lon": 69.2075},
            {"lat": 32.9295, "lon": 65.3633},
            {"lat": 31.6129, "lon": 65.7372},
        ],
        "status": "OPEN",
        "notes": "Active corridor for food and medical supplies.",
        "created_at": datetime(2021, 9, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
]


def _row_to_corridor(row: dict) -> HumanitarianCorridor:
    waypoints = row.get("waypoints")
    if isinstance(waypoints, str):
        waypoints = json.loads(waypoints)
    return HumanitarianCorridor(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        name=row["name"],
        waypoints=waypoints or [],
        status=CorridorStatus(row["status"]),
        notes=row.get("notes"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/civilian/corridors", response_model=list[HumanitarianCorridor])
async def list_corridors(
    request: Request,
    scenario_id: Optional[UUID] = Query(default=None),
    status: Optional[CorridorStatus] = Query(default=None),
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
    rows = await db.fetch(
        f"SELECT * FROM civilian_humanitarian_corridors {where} ORDER BY created_at DESC",
        *params,
    )

    if not rows:
        seeds = _SEED_CORRIDORS
        if scenario_id is not None:
            seeds = [c for c in seeds if c["scenario_id"] == scenario_id]
        if status is not None:
            seeds = [c for c in seeds if c["status"] == status.value]
        return [_row_to_corridor(c) for c in seeds]

    return [_row_to_corridor(dict(r)) for r in rows]


@router.post("/civilian/corridors", response_model=HumanitarianCorridor, status_code=201)
async def create_corridor(
    request: Request,
    body: CreateCorridorRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    corridor_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO civilian_humanitarian_corridors
            (id, scenario_id, name, waypoints, status, notes, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        """,
        corridor_id,
        body.scenario_id,
        body.name,
        json.dumps(body.waypoints),
        body.status.value,
        body.notes,
        now,
        now,
    )
    return HumanitarianCorridor(
        id=corridor_id,
        scenario_id=body.scenario_id,
        name=body.name,
        waypoints=body.waypoints,
        status=body.status,
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )


@router.get("/civilian/corridors/{corridor_id}", response_model=HumanitarianCorridor)
async def get_corridor(
    corridor_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM civilian_humanitarian_corridors WHERE id = $1", corridor_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Humanitarian corridor not found")
    return _row_to_corridor(dict(row))


@router.put("/civilian/corridors/{corridor_id}", response_model=HumanitarianCorridor)
async def update_corridor(
    corridor_id: UUID,
    request: Request,
    body: UpdateCorridorRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM civilian_humanitarian_corridors WHERE id = $1", corridor_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Humanitarian corridor not found")

    current = dict(row)
    now = datetime.now(timezone.utc)

    new_status = body.status.value if body.status is not None else current["status"]
    new_notes = body.notes if body.notes is not None else current.get("notes")

    await db.execute(
        "UPDATE civilian_humanitarian_corridors SET status=$1, notes=$2, updated_at=$3 WHERE id=$4",
        new_status,
        new_notes,
        now,
        corridor_id,
    )
    current.update(status=new_status, notes=new_notes, updated_at=now)
    return _row_to_corridor(current)


@router.delete("/civilian/corridors/{corridor_id}", status_code=204)
async def delete_corridor(
    corridor_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM civilian_humanitarian_corridors WHERE id = $1", corridor_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Humanitarian corridor not found")

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user, require_permission
from app.models import CreatePopulationZoneRequest, DensityClass, PopulationZone

router = APIRouter()

# Synthetic seed zones returned when DB is empty
_SEED_ZONES: list[dict] = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000101"),
        "scenario_id": None,
        "name": "Baghdad",
        "country_code": "IRQ",
        "latitude": 33.3152,
        "longitude": 44.3661,
        "radius_km": 30.0,
        "population": 7000000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000102"),
        "scenario_id": None,
        "name": "Kabul",
        "country_code": "AFG",
        "latitude": 34.5553,
        "longitude": 69.2075,
        "radius_km": 25.0,
        "population": 4500000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000103"),
        "scenario_id": None,
        "name": "Kyiv",
        "country_code": "UKR",
        "latitude": 50.4501,
        "longitude": 30.5234,
        "radius_km": 28.0,
        "population": 2900000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000104"),
        "scenario_id": None,
        "name": "Mariupol",
        "country_code": "UKR",
        "latitude": 47.0970,
        "longitude": 37.5426,
        "radius_km": 15.0,
        "population": 430000,
        "density_class": "SUBURBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000105"),
        "scenario_id": None,
        "name": "Aleppo",
        "country_code": "SYR",
        "latitude": 36.2021,
        "longitude": 37.1343,
        "radius_km": 20.0,
        "population": 2000000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000106"),
        "scenario_id": None,
        "name": "Mogadishu",
        "country_code": "SOM",
        "latitude": 2.0469,
        "longitude": 45.3182,
        "radius_km": 18.0,
        "population": 2400000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000107"),
        "scenario_id": None,
        "name": "Khartoum",
        "country_code": "SDN",
        "latitude": 15.5007,
        "longitude": 32.5599,
        "radius_km": 22.0,
        "population": 6200000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000108"),
        "scenario_id": None,
        "name": "Bamako",
        "country_code": "MLI",
        "latitude": 12.6392,
        "longitude": -8.0029,
        "radius_km": 20.0,
        "population": 2700000,
        "density_class": "SUBURBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
]


def _row_to_zone(row: dict) -> PopulationZone:
    return PopulationZone(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        name=row["name"],
        country_code=row["country_code"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        radius_km=row["radius_km"],
        population=row["population"],
        density_class=DensityClass(row["density_class"]),
        created_at=row["created_at"],
    )


@router.get("/civilian/population", response_model=list[PopulationZone])
async def list_population_zones(
    request: Request,
    scenario_id: Optional[UUID] = Query(default=None),
    country_code: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    conditions = []
    params: list = []

    if scenario_id is not None:
        params.append(scenario_id)
        conditions.append(f"scenario_id = ${len(params)}")
    if country_code is not None:
        params.append(country_code.upper())
        conditions.append(f"country_code = ${len(params)}")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)
    rows = await db.fetch(
        f"SELECT * FROM civilian_population_zones {where} ORDER BY created_at DESC LIMIT ${len(params)}",
        *params,
    )

    if not rows:
        seeds = _SEED_ZONES
        if scenario_id is not None:
            seeds = [z for z in seeds if z["scenario_id"] == scenario_id]
        if country_code is not None:
            seeds = [z for z in seeds if z["country_code"] == country_code.upper()]
        return [_row_to_zone(z) for z in seeds[:limit]]

    return [_row_to_zone(dict(r)) for r in rows]


@router.post("/civilian/population", response_model=PopulationZone, status_code=201)
async def create_population_zone(
    request: Request,
    body: CreatePopulationZoneRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    zone_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO civilian_population_zones
            (id, scenario_id, name, country_code, latitude, longitude,
             radius_km, population, density_class, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """,
        zone_id,
        body.scenario_id,
        body.name,
        body.country_code.upper(),
        body.latitude,
        body.longitude,
        body.radius_km,
        body.population,
        body.density_class.value,
        now,
    )
    return PopulationZone(
        id=zone_id,
        scenario_id=body.scenario_id,
        name=body.name,
        country_code=body.country_code.upper(),
        latitude=body.latitude,
        longitude=body.longitude,
        radius_km=body.radius_km,
        population=body.population,
        density_class=body.density_class,
        created_at=now,
    )


@router.get("/civilian/population/{zone_id}", response_model=PopulationZone)
async def get_population_zone(
    zone_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM civilian_population_zones WHERE id = $1", zone_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Population zone not found")
    return _row_to_zone(dict(row))


@router.delete("/civilian/population/{zone_id}", status_code=204)
async def delete_population_zone(
    zone_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM civilian_population_zones WHERE id = $1", zone_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Population zone not found")

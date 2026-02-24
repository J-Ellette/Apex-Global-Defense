from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status

from app.auth import get_current_user, require_permission
from app.data.agents import AGENT_MAP
from app.engine.plume import run_dispersion
from app.models import (
    CBRNRelease,
    CreateReleaseRequest,
    DispersionSimulation,
    MetConditions,
    StabilityClass,
)

router = APIRouter(tags=["releases"])


def _row_to_met(row: dict) -> MetConditions:
    met_raw = row.get("met") or {}
    if isinstance(met_raw, str):
        met_raw = json.loads(met_raw)
    return MetConditions(
        wind_speed_ms=met_raw.get("wind_speed_ms", 3.0),
        wind_direction_deg=met_raw.get("wind_direction_deg", 270.0),
        stability_class=StabilityClass(met_raw.get("stability_class", "D")),
        mixing_height_m=met_raw.get("mixing_height_m", 800.0),
        temperature_c=met_raw.get("temperature_c", 15.0),
        relative_humidity_pct=met_raw.get("relative_humidity_pct", 60.0),
    )


def _row_to_release(row: dict) -> CBRNRelease:
    return CBRNRelease(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        agent_id=row["agent_id"],
        release_type=row.get("release_type", "POINT"),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        quantity_kg=float(row["quantity_kg"]),
        release_height_m=float(row.get("release_height_m", 1.0)),
        duration_min=float(row.get("duration_min", 10.0)),
        met=_row_to_met(row),
        population_density_per_km2=float(row.get("population_density_per_km2", 500.0)),
        label=row.get("label", ""),
        notes=row.get("notes"),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


@router.get("/cbrn/releases", response_model=list[CBRNRelease])
async def list_releases(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List CBRN release events, optionally filtered by scenario."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    if scenario_id:
        rows = await db.fetch(
            "SELECT * FROM cbrn_releases WHERE scenario_id = $1 ORDER BY created_at DESC",
            scenario_id,
        )
    else:
        rows = await db.fetch(
            "SELECT * FROM cbrn_releases ORDER BY created_at DESC LIMIT 200"
        )
    return [_row_to_release(dict(r)) for r in rows]


@router.post("/cbrn/releases", response_model=CBRNRelease, status_code=http_status.HTTP_201_CREATED)
async def create_release(
    request: Request,
    body: CreateReleaseRequest,
    user: dict = Depends(get_current_user),
):
    """Create a CBRN release event."""
    require_permission(user, "scenario:write")

    if body.agent_id not in AGENT_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {body.agent_id}")

    db = request.app.state.db
    release_id = uuid4()
    now = datetime.now(timezone.utc)
    met_json = json.dumps(body.met.model_dump())

    await db.execute(
        """
        INSERT INTO cbrn_releases
          (id, scenario_id, agent_id, release_type, latitude, longitude,
           quantity_kg, release_height_m, duration_min, met,
           population_density_per_km2, label, notes, created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13,$14,$15)
        """,
        release_id,
        body.scenario_id,
        body.agent_id,
        body.release_type.value,
        body.latitude,
        body.longitude,
        body.quantity_kg,
        body.release_height_m,
        body.duration_min,
        met_json,
        body.population_density_per_km2,
        body.label,
        body.notes,
        user.get("sub") or user.get("uid"),
        now,
    )

    return CBRNRelease(
        id=release_id,
        scenario_id=body.scenario_id,
        agent_id=body.agent_id,
        release_type=body.release_type,
        latitude=body.latitude,
        longitude=body.longitude,
        quantity_kg=body.quantity_kg,
        release_height_m=body.release_height_m,
        duration_min=body.duration_min,
        met=body.met,
        population_density_per_km2=body.population_density_per_km2,
        label=body.label,
        notes=body.notes,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.get("/cbrn/releases/{release_id}", response_model=CBRNRelease)
async def get_release(
    request: Request,
    release_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get a single CBRN release event."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM cbrn_releases WHERE id = $1", release_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return _row_to_release(dict(row))


@router.delete("/cbrn/releases/{release_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_release(
    request: Request,
    release_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a CBRN release event and its associated simulations."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    await db.execute("DELETE FROM cbrn_simulations WHERE release_id = $1", release_id)
    result = await db.execute("DELETE FROM cbrn_releases WHERE id = $1", release_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Release not found")


@router.post("/cbrn/releases/{release_id}/simulate", response_model=DispersionSimulation)
async def simulate_release(
    request: Request,
    release_id: UUID,
    user: dict = Depends(get_current_user),
):
    """
    Run Gaussian plume dispersion simulation for a release event.
    Returns plume contours, hazard zones, and casualty estimates.
    """
    require_permission(user, "simulation:run")
    db = request.app.state.db

    row = await db.fetchrow("SELECT * FROM cbrn_releases WHERE id = $1", release_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Release not found")

    release = _row_to_release(dict(row))
    agent = AGENT_MAP.get(release.agent_id)
    if agent is None:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {release.agent_id}")

    simulation = run_dispersion(release, agent)

    # Persist result
    result_json = simulation.model_dump_json()
    await db.execute(
        """
        INSERT INTO cbrn_simulations (id, release_id, result, simulated_at)
        VALUES ($1, $2, $3::jsonb, $4)
        ON CONFLICT (release_id) DO UPDATE
          SET result = EXCLUDED.result, simulated_at = EXCLUDED.simulated_at
        """,
        simulation.id,
        release_id,
        result_json,
        simulation.simulated_at,
    )

    return simulation


@router.get("/cbrn/releases/{release_id}/simulation", response_model=DispersionSimulation)
async def get_simulation(
    request: Request,
    release_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get the latest dispersion simulation result for a release."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT result FROM cbrn_simulations WHERE release_id = $1", release_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="No simulation found for this release")
    result_raw = row["result"]
    if isinstance(result_raw, str):
        data = json.loads(result_raw)
    else:
        data = dict(result_raw)
    return DispersionSimulation.model_validate(data)

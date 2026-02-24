"""Runs router — control, inspect, and report on simulation runs."""

from __future__ import annotations

import json
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user, require_permission
from app.engine.stub import build_after_action_report, generate_run_events, run_monte_carlo
from app.models import (
    AfterActionReport,
    MCResult,
    ScenarioConfig,
    SimEvent,
    SimMode,
    SimState,
    SimStatus,
    SimulationRun,
)

router = APIRouter(tags=["runs"])

ClaimsDepend = Annotated[dict, Depends(get_current_user)]


def _db(request: Request):
    return request.app.state.db


def _redis(request: Request):
    return request.app.state.redis


async def _get_run_or_404(db, run_id: uuid.UUID) -> dict:
    row = await db.fetchrow(
        """
        SELECT id, scenario_id, mode, status, progress, config,
               created_by, created_at, started_at, completed_at, error_message
        FROM simulation_runs WHERE id = $1
        """,
        run_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    return dict(row)


@router.get("/runs/{run_id}", response_model=SimulationRun)
async def get_run(run_id: uuid.UUID, claims: ClaimsDepend, request: Request):
    """Get status and metadata for a simulation run."""
    require_permission(claims, "scenario:read")
    row = await _get_run_or_404(_db(request), run_id)
    cfg = row["config"] if isinstance(row["config"], dict) else {}
    return SimulationRun(
        id=row["id"],
        scenario_id=row["scenario_id"],
        mode=SimMode(row["mode"]),
        status=SimStatus(row["status"]),
        progress=float(row["progress"]),
        config=cfg,
        created_by=row["created_by"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        error_message=row["error_message"],
    )


@router.post("/runs/{run_id}/pause", response_model=SimulationRun)
async def pause_run(run_id: uuid.UUID, claims: ClaimsDepend, request: Request):
    """Pause a running simulation."""
    require_permission(claims, "simulation:control")
    db = _db(request)
    redis = _redis(request)
    row = await _get_run_or_404(db, run_id)
    if row["status"] != SimStatus.RUNNING:
        raise HTTPException(status_code=400, detail=f"Run is not running (status={row['status']})")
    await db.execute(
        "UPDATE simulation_runs SET status='paused' WHERE id=$1", run_id
    )
    await redis.publish(f"sim:{run_id}", json.dumps({"type": "status", "status": "paused"}))
    row["status"] = SimStatus.PAUSED
    cfg = row["config"] if isinstance(row["config"], dict) else {}
    return SimulationRun(
        id=row["id"],
        scenario_id=row["scenario_id"],
        mode=SimMode(row["mode"]),
        status=SimStatus.PAUSED,
        progress=float(row["progress"]),
        config=cfg,
        created_by=row["created_by"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        error_message=row["error_message"],
    )


@router.post("/runs/{run_id}/resume", response_model=SimulationRun)
async def resume_run(run_id: uuid.UUID, claims: ClaimsDepend, request: Request):
    """Resume a paused simulation."""
    require_permission(claims, "simulation:control")
    db = _db(request)
    redis = _redis(request)
    row = await _get_run_or_404(db, run_id)
    if row["status"] != SimStatus.PAUSED:
        raise HTTPException(status_code=400, detail=f"Run is not paused (status={row['status']})")
    await db.execute(
        "UPDATE simulation_runs SET status='running' WHERE id=$1", run_id
    )
    await redis.publish(f"sim:{run_id}", json.dumps({"type": "status", "status": "running"}))
    cfg = row["config"] if isinstance(row["config"], dict) else {}
    return SimulationRun(
        id=row["id"],
        scenario_id=row["scenario_id"],
        mode=SimMode(row["mode"]),
        status=SimStatus.RUNNING,
        progress=float(row["progress"]),
        config=cfg,
        created_by=row["created_by"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        error_message=row["error_message"],
    )


@router.post("/runs/{run_id}/step", response_model=SimEvent)
async def step_run(run_id: uuid.UUID, claims: ClaimsDepend, request: Request):
    """Advance a turn-based simulation by one turn."""
    require_permission(claims, "simulation:control")
    db = _db(request)
    redis = _redis(request)
    row = await _get_run_or_404(db, run_id)
    if row["mode"] != SimMode.TURN_BASED:
        raise HTTPException(status_code=400, detail="Step is only available in turn_based mode")
    if row["status"] not in (SimStatus.RUNNING, SimStatus.PAUSED):
        raise HTTPException(status_code=400, detail=f"Cannot step run in status={row['status']}")

    # Get the current highest turn number
    last = await db.fetchval(
        "SELECT COALESCE(MAX(turn_number), 0) FROM sim_events WHERE run_id=$1", run_id
    )
    next_turn = (last or 0) + 1

    cfg_raw = row["config"]
    if isinstance(cfg_raw, str):
        cfg_raw = json.loads(cfg_raw)
    config = ScenarioConfig(**cfg_raw)

    events = generate_run_events(run_id, config, seed=next_turn)
    # Return the first event of the new turn
    turn_events = [e for e in events if e.turn_number == ((next_turn - 1) % max(1, len(events) // 5) + 1)]
    event = turn_events[0] if turn_events else events[0]
    # Adjust event turn number
    event = event.model_copy(update={"turn_number": next_turn})

    await db.execute(
        """
        INSERT INTO sim_events (time, run_id, event_type, entity_id, payload, turn_number)
        VALUES (NOW(), $1, $2, $3, $4::jsonb, $5)
        """,
        run_id,
        event.event_type.value,
        event.entity_id,
        json.dumps(event.payload),
        next_turn,
    )

    progress = min(1.0, next_turn / max(1, config.duration_hours // 4))
    status = SimStatus.COMPLETE if progress >= 1.0 else SimStatus.RUNNING
    await db.execute(
        "UPDATE simulation_runs SET progress=$1, status=$2 WHERE id=$3",
        round(progress, 3),
        status.value,
        run_id,
    )

    await redis.publish(
        f"sim:{run_id}",
        json.dumps({"type": "sim:event", "payload": event.model_dump(mode="json")}),
    )
    return event


@router.get("/runs/{run_id}/state", response_model=SimState)
async def get_state(run_id: uuid.UUID, claims: ClaimsDepend, request: Request):
    """Get the current state snapshot of a simulation run."""
    require_permission(claims, "scenario:read")
    db = _db(request)
    row = await _get_run_or_404(db, run_id)

    last_turn = await db.fetchval(
        "SELECT COALESCE(MAX(turn_number), 0) FROM sim_events WHERE run_id=$1", run_id
    )

    cfg_raw = row["config"]
    if isinstance(cfg_raw, str):
        cfg_raw = json.loads(cfg_raw)
    config = ScenarioConfig(**cfg_raw)

    return SimState(
        run_id=run_id,
        status=SimStatus(row["status"]),
        progress=float(row["progress"]),
        turn_number=last_turn or 0,
        sim_time=config.start_time + timedelta(hours=(last_turn or 0) * 4),
        blue_unit_count=max(0, len(config.blue_force_ids) - (last_turn or 0)),
        red_unit_count=max(0, len(config.red_force_ids) - (last_turn or 0)),
        objectives_status={"OBJ-1": "CONTESTED", "OBJ-2": "BLUE", "OBJ-3": "RED"},
    )


@router.get("/runs/{run_id}/events", response_model=list[SimEvent])
async def get_events(
    run_id: uuid.UUID,
    claims: ClaimsDepend,
    request: Request,
    since: str | None = None,
    limit: int = 100,
):
    """List simulation events for a run, optionally filtered by time."""
    require_permission(claims, "scenario:read")
    db = _db(request)
    await _get_run_or_404(db, run_id)

    if since:
        rows = await db.fetch(
            """
            SELECT time, run_id, event_type, entity_id, payload, turn_number
            FROM sim_events
            WHERE run_id=$1 AND time > $2
            ORDER BY time ASC
            LIMIT $3
            """,
            run_id,
            since,
            limit,
        )
    else:
        rows = await db.fetch(
            """
            SELECT time, run_id, event_type, entity_id, payload, turn_number
            FROM sim_events
            WHERE run_id=$1
            ORDER BY time ASC
            LIMIT $2
            """,
            run_id,
            limit,
        )

    return [
        SimEvent(
            time=row["time"],
            run_id=row["run_id"],
            event_type=row["event_type"],
            entity_id=row["entity_id"],
            payload=row["payload"] if isinstance(row["payload"], dict) else {},
            turn_number=row["turn_number"],
        )
        for row in rows
    ]


@router.get("/runs/{run_id}/report", response_model=AfterActionReport)
async def get_report(run_id: uuid.UUID, claims: ClaimsDepend, request: Request):
    """Generate an after-action report for a completed simulation run."""
    require_permission(claims, "scenario:read")
    db = _db(request)
    row = await _get_run_or_404(db, run_id)

    if row["status"] not in (SimStatus.COMPLETE, SimStatus.ERROR):
        raise HTTPException(
            status_code=400,
            detail=f"Report only available for completed runs (status={row['status']})",
        )

    cfg_raw = row["config"]
    if isinstance(cfg_raw, str):
        cfg_raw = json.loads(cfg_raw)
    config = ScenarioConfig(**cfg_raw)

    event_rows = await db.fetch(
        """
        SELECT time, run_id, event_type, entity_id, payload, turn_number
        FROM sim_events WHERE run_id=$1 ORDER BY time ASC
        """,
        run_id,
    )
    events = [
        SimEvent(
            time=r["time"],
            run_id=r["run_id"],
            event_type=r["event_type"],
            entity_id=r["entity_id"],
            payload=r["payload"] if isinstance(r["payload"], dict) else {},
            turn_number=r["turn_number"],
        )
        for r in event_rows
    ]

    mc_result = None
    if config.mode == SimMode.MONTE_CARLO:
        mc_cfg = cfg_raw.get("mc_result")
        if mc_cfg:
            mc_result = MCResult(**mc_cfg)

    return build_after_action_report(run_id, row["scenario_id"], config, events, mc_result)

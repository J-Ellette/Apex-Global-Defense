"""Scenario router — list runs for a scenario and start new runs."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.auth import get_current_user, require_permission
from app.engine.stub import (
    build_after_action_report,
    generate_run_events,
    run_monte_carlo,
)
from app.models import (
    AfterActionReport,
    ScenarioConfig,
    SimMode,
    SimStatus,
    SimulationRun,
    StartRunRequest,
)

router = APIRouter(tags=["scenarios"])


def _db(request: Request):
    return request.app.state.db


def _redis(request: Request):
    return request.app.state.redis


ClaimsDepend = Annotated[dict, Depends(get_current_user)]


@router.get("/scenarios/{scenario_id}/runs", response_model=list[SimulationRun])
async def list_runs(
    scenario_id: uuid.UUID,
    claims: ClaimsDepend,
    request: Request,
):
    """List all simulation runs for a scenario."""
    require_permission(claims, "scenario:read")
    db = _db(request)
    rows = await db.fetch(
        """
        SELECT id, scenario_id, mode, status, progress, config,
               created_by, created_at, started_at, completed_at, error_message
        FROM simulation_runs
        WHERE scenario_id = $1
        ORDER BY created_at DESC
        """,
        scenario_id,
    )
    return [
        SimulationRun(
            id=row["id"],
            scenario_id=row["scenario_id"],
            mode=SimMode(row["mode"]),
            status=SimStatus(row["status"]),
            progress=float(row["progress"]),
            config=row["config"] if isinstance(row["config"], dict) else {},
            created_by=row["created_by"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"],
        )
        for row in rows
    ]


@router.post(
    "/scenarios/{scenario_id}/runs",
    response_model=SimulationRun,
    status_code=201,
)
async def start_run(
    scenario_id: uuid.UUID,
    body: StartRunRequest,
    background_tasks: BackgroundTasks,
    claims: ClaimsDepend,
    request: Request,
):
    """Create and queue a new simulation run for a scenario."""
    require_permission(claims, "simulation:run")

    db = _db(request)
    redis = _redis(request)

    # Verify scenario exists
    scenario = await db.fetchrow(
        "SELECT id FROM scenarios WHERE id = $1", scenario_id
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    user_id = uuid.UUID(claims["uid"])
    run_id = uuid.uuid4()

    config_json = body.config.model_dump_json()

    await db.execute(
        """
        INSERT INTO simulation_runs
            (id, scenario_id, mode, status, progress, config, created_by)
        VALUES ($1, $2, $3, 'queued', 0, $4::jsonb, $5)
        """,
        run_id,
        scenario_id,
        body.config.mode.value,
        config_json,
        user_id,
    )

    run = SimulationRun(
        id=run_id,
        scenario_id=scenario_id,
        mode=body.config.mode,
        status=SimStatus.QUEUED,
        progress=0.0,
        config=body.config.model_dump(mode="json"),
        created_by=user_id,
        created_at=__import__("datetime").datetime.utcnow(),
    )

    # Dispatch to stub engine in background
    background_tasks.add_task(_execute_run, db, redis, run_id, scenario_id, body.config)

    return run


async def _execute_run(db, redis, run_id: uuid.UUID, scenario_id: uuid.UUID, config: ScenarioConfig):
    """Background task: run the stub engine and persist events."""

    try:
        await db.execute(
            "UPDATE simulation_runs SET status='running', started_at=NOW() WHERE id=$1",
            run_id,
        )
        await redis.publish(f"sim:{run_id}", json.dumps({"type": "status", "status": "running"}))

        if config.mode == SimMode.MONTE_CARLO:
            mc = run_monte_carlo(run_id, config)

            await db.execute(
                "UPDATE simulation_runs SET status='complete', progress=1, completed_at=NOW(), config=config || $1::jsonb WHERE id=$2",
                _json.dumps({"mc_result": mc.model_dump(mode="json")}),
                run_id,
            )
        else:
            events = generate_run_events(run_id, config)
            total = len(events)
            for i, event in enumerate(events, 1):
                await db.execute(
                    """
                    INSERT INTO sim_events (time, run_id, event_type, entity_id, payload, turn_number)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                    """,
                    event.time,
                    run_id,
                    event.event_type.value,
                    event.entity_id,
                    json.dumps(event.payload),
                    event.turn_number,
                )
                progress = round(i / total, 3)
                await db.execute(
                    "UPDATE simulation_runs SET progress=$1 WHERE id=$2",
                    progress,
                    run_id,
                )
                # Publish event to Redis for collab-svc fan-out
                await redis.publish(
                    f"sim:{run_id}",
                    json.dumps({
                        "type": "sim:event",
                        "payload": event.model_dump(mode="json"),
                    }),
                )

            await db.execute(
                "UPDATE simulation_runs SET status='complete', progress=1, completed_at=NOW() WHERE id=$1",
                run_id,
            )

        await redis.publish(f"sim:{run_id}", json.dumps({"type": "status", "status": "complete"}))

    except Exception as exc:  # noqa: BLE001
        await db.execute(
            "UPDATE simulation_runs SET status='error', error_message=$1 WHERE id=$2",
            str(exc),
            run_id,
        )
        await redis.publish(f"sim:{run_id}", json.dumps({"type": "status", "status": "error", "error": str(exc)}))

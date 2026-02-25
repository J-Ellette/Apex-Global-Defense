from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import grpc

from app.models import EventType, ScenarioConfig, SimEvent

from . import sim_engine_pb2, sim_engine_pb2_grpc

EventTypeEnum = getattr(sim_engine_pb2, "EventType")
ScenarioConfigMessage = getattr(sim_engine_pb2, "ScenarioConfig")
SimRequestMessage = getattr(sim_engine_pb2, "SimRequest")
RunRefMessage = getattr(sim_engine_pb2, "RunRef")


def _to_datetime(timestamp_ms: int) -> datetime:
    if timestamp_ms <= 0:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)


def _to_event_type(value: int) -> EventType:
    name = EventTypeEnum.Name(value)
    try:
        return EventType(name)
    except ValueError:
        return EventType.PHASE_CHANGE


def _to_sim_event(message: Any) -> SimEvent:
    payload: dict = {}
    if message.payload:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except Exception:  # noqa: BLE001
            payload = {}

    entity_id = None
    if message.entity_id:
        try:
            entity_id = uuid.UUID(message.entity_id)
        except ValueError:
            entity_id = None

    location = None
    if message.HasField("location"):
        location = {"lat": message.location.lat, "lng": message.location.lng}

    run_id = uuid.UUID(message.run_id)

    return SimEvent(
        time=_to_datetime(message.timestamp_ms),
        run_id=run_id,
        event_type=_to_event_type(message.type),
        entity_id=entity_id,
        location=location,
        payload=payload,
        turn_number=message.turn_number,
    )


def _to_scenario_config_message(config: ScenarioConfig) -> Any:
    return ScenarioConfigMessage(
        mode=config.mode.value,
        blue_force_ids=[str(force_id) for force_id in config.blue_force_ids],
        red_force_ids=[str(force_id) for force_id in config.red_force_ids],
        theater_bounds_json=json.dumps(config.theater_bounds or {}),
        start_time_iso=config.start_time.isoformat(),
        duration_hours=config.duration_hours,
        monte_carlo_runs=config.monte_carlo_runs,
        weather_preset=config.weather_preset,
        fog_of_war=config.fog_of_war,
        terrain_effects=config.terrain_effects,
    )


async def stream_run_events(run_id: uuid.UUID, config: ScenarioConfig, grpc_addr: str):
    request = SimRequestMessage(
        run_id=str(run_id),
        config=_to_scenario_config_message(config),
        initial_state=b"",
    )

    async with grpc.aio.insecure_channel(grpc_addr) as channel:
        stub = sim_engine_pb2_grpc.SimEngineStub(channel)
        stream = stub.RunScenario(request)
        async for event in stream:
            yield _to_sim_event(event)


async def pause_run(run_id: uuid.UUID, grpc_addr: str) -> Any:
    async with grpc.aio.insecure_channel(grpc_addr) as channel:
        stub = sim_engine_pb2_grpc.SimEngineStub(channel)
        return await stub.PauseRun(RunRefMessage(run_id=str(run_id)))


async def resume_run(run_id: uuid.UUID, grpc_addr: str) -> Any:
    async with grpc.aio.insecure_channel(grpc_addr) as channel:
        stub = sim_engine_pb2_grpc.SimEngineStub(channel)
        return await stub.ResumeRun(RunRefMessage(run_id=str(run_id)))


async def step_turn(run_id: uuid.UUID, grpc_addr: str) -> SimEvent:
    async with grpc.aio.insecure_channel(grpc_addr) as channel:
        stub = sim_engine_pb2_grpc.SimEngineStub(channel)
        event = await stub.StepTurn(RunRefMessage(run_id=str(run_id)))
        return _to_sim_event(event)


async def get_state(run_id: uuid.UUID, grpc_addr: str) -> Any:
    async with grpc.aio.insecure_channel(grpc_addr) as channel:
        stub = sim_engine_pb2_grpc.SimEngineStub(channel)
        return await stub.GetState(RunRefMessage(run_id=str(run_id)))

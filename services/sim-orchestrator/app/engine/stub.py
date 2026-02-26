"""Stub simulation engine.

This module provides a deterministic-ish simulation that generates realistic
events without a real C++/Rust engine.  When the gRPC sim-engine service is
available it will replace these stubs.
"""

from __future__ import annotations

import math
import os
import random
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

from app.models import (
    AfterActionReport,
    CasualtyDistribution,
    EventType,
    ForceSummary,
    LogisticsState,
    LogisticsSummary,
    MCResult,
    OutcomeDistribution,
    ScenarioConfig,
    SimEvent,
    SimMode,
    SimState,
    SimStatus,
    SupplyLevels,
)


# ---------------------------------------------------------------------------
# Combat resolution constants
# ---------------------------------------------------------------------------

_WEATHER_MODIFIERS = {
    "clear": 1.0,
    "overcast": 0.95,
    "rain": 0.85,
    "fog": 0.70,
    "storm": 0.55,
    "snow": 0.60,
}

_EVENT_TEMPLATES = [
    (EventType.UNIT_MOVE, "Unit repositioned"),
    (EventType.ENGAGEMENT, "Fire exchange"),
    (EventType.CASUALTY, "Casualties sustained"),
    (EventType.SUPPLY_CONSUMED, "Resupply consumed"),
    (EventType.AIRSTRIKE, "Airstrike executed"),
    (EventType.OBJECTIVE_CAPTURED, "Objective captured"),
    (EventType.RESUPPLY, "Resupply convoy arrived"),
]


def _atk_score(rng: random.Random, weather: str) -> float:
    base = rng.uniform(0.6, 1.4)
    return base * _WEATHER_MODIFIERS.get(weather, 1.0)


def _def_score(rng: random.Random) -> float:
    return rng.uniform(0.5, 1.2)


def resolve_engagement(rng: random.Random, config: ScenarioConfig) -> dict:
    atk = _atk_score(rng, config.weather_preset)
    dfn = _def_score(rng)
    ratio = atk / dfn
    if ratio > 3.0:
        outcome = "decisive_attacker_victory"
    elif ratio > 1.5:
        outcome = "attacker_victory"
    elif ratio > 0.8:
        outcome = "contested"
    elif ratio > 0.4:
        outcome = "defender_victory"
    else:
        outcome = "decisive_defender_victory"
    return {
        "atk_score": round(atk, 3),
        "def_score": round(dfn, 3),
        "ratio": round(ratio, 3),
        "outcome": outcome,
        "blue_casualties": int(rng.uniform(0, 50) * (1.0 / max(ratio, 0.1))),
        "red_casualties": int(rng.uniform(0, 50) * ratio),
    }


# ---------------------------------------------------------------------------
# Single-run event generator
# ---------------------------------------------------------------------------

def generate_run_events(
    run_id: uuid.UUID,
    config: ScenarioConfig,
    seed: int | None = None,
) -> list[SimEvent]:
    """Generate a synthetic list of sim events for one run."""
    rng = random.Random(seed)
    events: list[SimEvent] = []
    turns = max(1, config.duration_hours // 4)  # ~4h per turn
    sim_time = config.start_time

    for turn in range(1, turns + 1):
        sim_time += timedelta(hours=4)

        # 2–5 events per turn
        n_events = rng.randint(2, 5)
        for _ in range(n_events):
            etype, _label = rng.choice(_EVENT_TEMPLATES)
            lat = rng.uniform(-10.0, 10.0)
            lng = rng.uniform(30.0, 60.0)

            payload: dict = {"turn": turn}
            if etype == EventType.ENGAGEMENT:
                payload.update(resolve_engagement(rng, config))
            elif etype == EventType.CASUALTY:
                payload["blue_casualties"] = rng.randint(0, 20)
                payload["red_casualties"] = rng.randint(0, 20)
            elif etype == EventType.OBJECTIVE_CAPTURED:
                payload["objective"] = f"OBJ-{rng.randint(1, 6)}"
                payload["side"] = rng.choice(["BLUE", "RED"])
            elif etype == EventType.RESUPPLY:
                payload["side"] = rng.choice(["BLUE", "RED"])
                payload["ammo_restored"] = round(rng.uniform(0.10, 0.25), 3)
                payload["fuel_restored"] = round(rng.uniform(0.10, 0.20), 3)
                payload["rations_restored"] = round(rng.uniform(0.05, 0.15), 3)

            events.append(
                SimEvent(
                    time=sim_time,
                    run_id=run_id,
                    event_type=etype,
                    entity_id=uuid.uuid4(),
                    location={"lat": lat, "lng": lng},
                    payload=payload,
                    turn_number=turn,
                )
            )

    return events


# ---------------------------------------------------------------------------
# Logistics & Attrition model
# ---------------------------------------------------------------------------

# Base supply drain per turn (fraction of total supply consumed)
_BASE_DRAIN_PER_TURN = 0.06


def _compute_force_summary(
    side: str,
    rng: random.Random,
    events: list[SimEvent],
    config: ScenarioConfig,
    n_force_units: int,
) -> ForceSummary:
    """Derive force supply and attrition from accumulated sim events."""
    weather_penalty = 1.0 - _WEATHER_MODIFIERS.get(config.weather_preset, 1.0)
    turns_elapsed = max((e.turn_number or 0) for e in events) if events else 0

    # Tally events that affect this force's supply
    supply_drain = 0.0
    resupply_ammo = 0.0
    resupply_fuel = 0.0
    resupply_rations = 0.0
    kia = 0
    n_engagements = 0
    n_airstrikes = 0

    kia_key = f"{side.lower()}_casualties"

    for e in events:
        if e.event_type == EventType.SUPPLY_CONSUMED:
            supply_drain += 0.03 + weather_penalty * 0.01
        elif e.event_type == EventType.RESUPPLY and e.payload.get("side") == side:
            resupply_ammo += e.payload.get("ammo_restored", 0.0)
            resupply_fuel += e.payload.get("fuel_restored", 0.0)
            resupply_rations += e.payload.get("rations_restored", 0.0)
        elif e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT):
            kia += e.payload.get(kia_key, 0)
        if e.event_type == EventType.ENGAGEMENT:
            n_engagements += 1
        elif e.event_type == EventType.AIRSTRIKE:
            n_airstrikes += 1

    # Baseline drain from time elapsed + weather
    base_drain = turns_elapsed * (_BASE_DRAIN_PER_TURN + weather_penalty * 0.02)
    total_ammo_drain = min(1.0, base_drain + n_engagements * 0.025 + supply_drain)
    total_fuel_drain = min(1.0, base_drain * 0.85 + supply_drain)
    total_rations_drain = min(1.0, base_drain * 0.4 + supply_drain * 0.3)

    ammo = max(0.0, round(1.0 - total_ammo_drain + resupply_ammo, 3))
    fuel = max(0.0, round(1.0 - total_fuel_drain + resupply_fuel, 3))
    rations = max(0.0, round(1.0 - total_rations_drain + resupply_rations, 3))

    # Attrition
    initial_strength = max(200, n_force_units * 150)
    wia = int(kia * 2.3)
    strength_pct = max(0.05, round(1.0 - kia / max(1, initial_strength), 3))

    # Equipment losses driven by engagements + airstrikes + some RNG
    equipment_rng = random.Random(rng.random())
    armor_losses = equipment_rng.randint(0, max(0, n_engagements * 2))
    arty_losses = equipment_rng.randint(0, max(0, n_engagements))
    air_losses = equipment_rng.randint(0, max(0, n_airstrikes))

    return ForceSummary(
        strength_pct=min(1.0, strength_pct),
        kia=kia,
        wia=wia,
        supply=SupplyLevels(ammo=min(1.0, ammo), fuel=min(1.0, fuel), rations=min(1.0, rations)),
        equipment_losses={"armor": armor_losses, "artillery": arty_losses, "aircraft": air_losses},
    )


def generate_logistics_state(
    run_id: uuid.UUID,
    config: ScenarioConfig,
    events: list[SimEvent],
    turn_number: int,
) -> LogisticsState:
    """Compute logistics state up to the given turn from accumulated events."""
    turn_events = [e for e in events if (e.turn_number or 0) <= turn_number]

    rng = random.Random(hash(str(run_id)) % (2 ** 31))

    blue = _compute_force_summary(
        "BLUE", rng, turn_events, config, len(config.blue_force_ids)
    )
    red = _compute_force_summary(
        "RED", rng, turn_events, config, len(config.red_force_ids)
    )

    sim_time = config.start_time + timedelta(hours=turn_number * 4)

    return LogisticsState(
        run_id=run_id,
        turn_number=turn_number,
        sim_time=sim_time,
        blue=blue,
        red=red,
    )


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

# Minimum trials before we spin up a process pool (avoid overhead for tiny n).
# Must be >= the ScenarioConfig.monte_carlo_runs minimum (10).
_MC_PARALLEL_THRESHOLD = 10
# Maximum worker processes (cap at CPU count to avoid oversubscription)
_MC_MAX_WORKERS = max(1, min(4, os.cpu_count() or 1))


def _wilson_ci_95(wins: int, n: int) -> tuple[float, float]:
    """Compute the 95% Wilson score confidence interval for a proportion.

    Returns (lower_pct, upper_pct) as percentages.
    """
    if n == 0:
        return (0.0, 0.0)
    z = 1.96  # z* for 95% two-sided interval
    p = wins / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    lo = max(0.0, round((center - margin) * 100, 1))
    hi = min(100.0, round((center + margin) * 100, 1))
    return (lo, hi)


def _mc_trial(args: tuple[uuid.UUID, object, int]) -> dict:
    """Single Monte Carlo trial — runs in a worker process.

    Returns a plain dict so it crosses the process boundary via pickle
    without importing Pydantic models in every worker.
    """
    run_id, config_dict, trial_index = args
    # Re-hydrate config inside the worker to avoid Pydantic cross-process issues
    from app.models import ScenarioConfig  # noqa: PLC0415 (local import for worker)
    config = ScenarioConfig(**config_dict)

    rng = random.Random(trial_index)
    events = generate_run_events(run_id, config, seed=trial_index)
    duration = config.duration_hours * rng.uniform(0.5, 1.2)

    from app.models import EventType  # noqa: PLC0415
    blue_cas = sum(
        e.payload.get("blue_casualties", 0)
        for e in events
        if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
    )
    red_cas = sum(
        e.payload.get("red_casualties", 0)
        for e in events
        if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
    )
    obj_events = [e for e in events if e.event_type == EventType.OBJECTIVE_CAPTURED]
    blue_obj = sum(1 for e in obj_events if e.payload.get("side") == "BLUE")
    red_obj = sum(1 for e in obj_events if e.payload.get("side") == "RED")
    return {
        "duration": duration,
        "blue_cas": blue_cas,
        "red_cas": red_cas,
        "blue_obj": blue_obj,
        "red_obj": red_obj,
    }


def run_monte_carlo(
    run_id: uuid.UUID,
    config: ScenarioConfig,
) -> MCResult:
    """Run N independent simulations and return aggregate statistics.

    Each trial uses a deterministic seed (trial index) so results are
    reproducible.  Confidence intervals are computed via the Wilson score method.

    Trials are executed in parallel using ProcessPoolExecutor when N ≥
    _MC_PARALLEL_THRESHOLD, falling back to a serial loop for small runs
    (avoids process-spawn overhead that exceeds computation cost).
    """
    n = config.monte_carlo_runs
    t0 = time.monotonic()

    # Serialize config for worker-process pickle boundary
    config_dict = config.model_dump(mode="json")
    trial_args = [(run_id, config_dict, i) for i in range(n)]

    if n >= _MC_PARALLEL_THRESHOLD:
        workers = min(_MC_MAX_WORKERS, n)
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_mc_trial, trial_args))
    else:
        results = [_mc_trial(a) for a in trial_args]

    elapsed_ms = round((time.monotonic() - t0) * 1000, 1)

    blue_wins = 0
    red_wins = 0
    durations: list[float] = []
    blue_cas_list: list[int] = []
    red_cas_list: list[int] = []

    for r in results:
        durations.append(r["duration"])
        blue_cas_list.append(r["blue_cas"])
        red_cas_list.append(r["red_cas"])
        if r["blue_obj"] > r["red_obj"]:
            blue_wins += 1
        elif r["red_obj"] > r["blue_obj"]:
            red_wins += 1

    contested = n - blue_wins - red_wins

    import logging  # noqa: PLC0415
    logging.getLogger("sim-orchestrator.mc").info(
        "MC run complete: n=%d, workers=%d, elapsed_ms=%.1f, blue_wins=%d, red_wins=%d",
        n,
        min(_MC_MAX_WORKERS, n) if n >= _MC_PARALLEL_THRESHOLD else 1,
        elapsed_ms,
        blue_wins,
        red_wins,
    )

    def _pct(x: int) -> float:
        return round(x / n * 100, 1)

    def _cas_dist(lst: list[int]) -> CasualtyDistribution:
        sorted_lst = sorted(lst)
        mean = sum(lst) / len(lst)
        return CasualtyDistribution(
            mean=int(mean),
            std=int(math.sqrt(sum((x - mean) ** 2 for x in lst) / len(lst))),
            p10=sorted_lst[int(len(sorted_lst) * 0.10)],
            p50=sorted_lst[int(len(sorted_lst) * 0.50)],
            p90=sorted_lst[int(len(sorted_lst) * 0.90)],
        )

    dur_mean = sum(durations) / len(durations)
    return MCResult(
        runs_completed=n,
        objective_outcomes={
            "primary": OutcomeDistribution(
                blue_win_pct=_pct(blue_wins),
                red_win_pct=_pct(red_wins),
                contested_pct=_pct(contested),
                mean_duration_hours=round(dur_mean, 1),
                std_duration_hours=round(
                    math.sqrt(sum((d - dur_mean) ** 2 for d in durations) / len(durations)), 1
                ),
                blue_win_ci_95=_wilson_ci_95(blue_wins, n),
                red_win_ci_95=_wilson_ci_95(red_wins, n),
            )
        },
        blue_casualties=_cas_dist(blue_cas_list),
        red_casualties=_cas_dist(red_cas_list),
        duration_distribution=sorted(durations)[:100],  # sample for UI
    )


# ---------------------------------------------------------------------------
# After-action report builder
# ---------------------------------------------------------------------------

def build_after_action_report(
    run_id: uuid.UUID,
    scenario_id: uuid.UUID,
    config: ScenarioConfig,
    events: list[SimEvent],
    mc_result: MCResult | None,
) -> AfterActionReport:
    blue_cas = sum(
        e.payload.get("blue_casualties", 0)
        for e in events
        if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
    )
    red_cas = sum(
        e.payload.get("red_casualties", 0)
        for e in events
        if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
    )
    obj_events = [e for e in events if e.event_type == EventType.OBJECTIVE_CAPTURED]
    blue_obj = sum(1 for e in obj_events if e.payload.get("side") == "BLUE")
    red_obj = sum(1 for e in obj_events if e.payload.get("side") == "RED")

    turns = max((e.turn_number or 0) for e in events) if events else 0
    winner = "Blue Force" if blue_obj > red_obj else ("Red Force" if red_obj > blue_obj else "Neither side")

    summary = (
        f"Simulation complete. {winner} achieved superiority over {config.duration_hours} hours "
        f"across {turns} turns. Blue captured {blue_obj} objectives with {blue_cas} casualties; "
        f"Red captured {red_obj} objectives with {red_cas} casualties."
    )

    key_events = [
        e for e in events
        if e.event_type in (
            EventType.OBJECTIVE_CAPTURED,
            EventType.PHASE_CHANGE,
            EventType.AIRSTRIKE,
        )
    ][:10]

    # Build logistics summary from final turn
    logistics = generate_logistics_state(run_id, config, events, turns)
    logistics_summary = LogisticsSummary(
        blue_final_strength_pct=logistics.blue.strength_pct,
        red_final_strength_pct=logistics.red.strength_pct,
        blue_total_kia=logistics.blue.kia,
        red_total_kia=logistics.red.kia,
        blue_supply=logistics.blue.supply,
        red_supply=logistics.red.supply,
        blue_equipment_losses=logistics.blue.equipment_losses,
        red_equipment_losses=logistics.red.equipment_losses,
    )

    return AfterActionReport(
        run_id=run_id,
        scenario_id=scenario_id,
        generated_at=datetime.utcnow(),
        executive_summary=summary,
        duration_hours=float(config.duration_hours),
        total_turns=turns,
        blue_objectives_captured=blue_obj,
        red_objectives_captured=red_obj,
        blue_casualties=blue_cas,
        red_casualties=red_cas,
        key_events=key_events,
        mc_result=mc_result,
        logistics_summary=logistics_summary,
    )

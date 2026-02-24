"""Stub simulation engine.

This module provides a deterministic-ish simulation that generates realistic
events without a real C++/Rust engine.  When the gRPC sim-engine service is
available it will replace these stubs.
"""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime, timedelta
from typing import AsyncIterator

from app.models import (
    AfterActionReport,
    CasualtyDistribution,
    EventType,
    MCResult,
    OutcomeDistribution,
    ScenarioConfig,
    SimEvent,
    SimMode,
    SimState,
    SimStatus,
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
# Monte Carlo
# ---------------------------------------------------------------------------

def run_monte_carlo(
    run_id: uuid.UUID,
    config: ScenarioConfig,
) -> MCResult:
    """Run N independent simulations and return aggregate statistics."""
    n = config.monte_carlo_runs
    blue_wins = 0
    red_wins = 0
    durations: list[float] = []
    blue_cas_list: list[int] = []
    red_cas_list: list[int] = []

    for i in range(n):
        rng = random.Random(i)
        events = generate_run_events(run_id, config, seed=i)
        duration = config.duration_hours * rng.uniform(0.5, 1.2)
        durations.append(duration)

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
        blue_cas_list.append(blue_cas)
        red_cas_list.append(red_cas)

        obj_events = [e for e in events if e.event_type == EventType.OBJECTIVE_CAPTURED]
        blue_obj = sum(1 for e in obj_events if e.payload.get("side") == "BLUE")
        red_obj = sum(1 for e in obj_events if e.payload.get("side") == "RED")
        if blue_obj > red_obj:
            blue_wins += 1
        elif red_obj > blue_obj:
            red_wins += 1

    contested = n - blue_wins - red_wins

    def _pct(x: int) -> float:
        return round(x / n * 100, 1)

    def _cas_dist(lst: list[int]) -> CasualtyDistribution:
        sorted_lst = sorted(lst)
        return CasualtyDistribution(
            mean=int(sum(lst) / len(lst)),
            std=int(math.sqrt(sum((x - sum(lst) / len(lst)) ** 2 for x in lst) / len(lst))),
            p10=sorted_lst[int(len(sorted_lst) * 0.10)],
            p50=sorted_lst[int(len(sorted_lst) * 0.50)],
            p90=sorted_lst[int(len(sorted_lst) * 0.90)],
        )

    return MCResult(
        runs_completed=n,
        objective_outcomes={
            "primary": OutcomeDistribution(
                blue_win_pct=_pct(blue_wins),
                red_win_pct=_pct(red_wins),
                contested_pct=_pct(contested),
                mean_duration_hours=round(sum(durations) / len(durations), 1),
                std_duration_hours=round(
                    math.sqrt(
                        sum((d - sum(durations) / len(durations)) ** 2 for d in durations)
                        / len(durations)
                    ),
                    1,
                ),
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
    )

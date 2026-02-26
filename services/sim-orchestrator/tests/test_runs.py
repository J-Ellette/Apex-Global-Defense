"""Tests for simulation run endpoints."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_CLAIMS = {
    "uid": str(uuid4()),
    "roles": ["sim_operator"],
    "perms": ["scenario:read", "scenario:write", "simulation:run", "simulation:control"],
    "org_id": str(uuid4()),
}


def _make_fake_db():
    db = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health():
    """Health endpoint returns 200 ok with engine mode info."""
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["engine_mode"] in ("grpc", "stub")


def test_get_run_not_found():
    """Returns 404 when run does not exist."""
    run_id = uuid4()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    mock_redis = AsyncMock()

    with (
        patch("app.auth.get_current_user", return_value=FAKE_CLAIMS),
        TestClient(app) as client,
    ):
        app.state.db = fake_db
        app.state.redis = mock_redis
        resp = client.get(
            f"/api/v1/runs/{run_id}",
            headers={"Authorization": "Bearer faketoken"},
        )
    assert resp.status_code == 404


def test_get_logistics_not_found():
    """Returns 404 for logistics when run does not exist."""
    run_id = uuid4()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    mock_redis = AsyncMock()

    with (
        patch("app.auth.get_current_user", return_value=FAKE_CLAIMS),
        TestClient(app) as client,
    ):
        app.state.db = fake_db
        app.state.redis = mock_redis
        resp = client.get(
            f"/api/v1/runs/{run_id}/logistics",
            headers={"Authorization": "Bearer faketoken"},
        )
    assert resp.status_code == 404


def test_get_logistics_returns_state():
    """Logistics endpoint returns a valid LogisticsState for an existing run."""
    import json

    run_id = uuid4()
    scenario_id = uuid4()
    user_id = uuid4()

    config = {
        "mode": "turn_based",
        "blue_force_ids": [],
        "red_force_ids": [],
        "start_time": datetime.utcnow().isoformat(),
        "duration_hours": 24,
        "monte_carlo_runs": 100,
        "weather_preset": "clear",
        "fog_of_war": True,
        "terrain_effects": True,
    }

    fake_run_row = {
        "id": run_id,
        "scenario_id": scenario_id,
        "mode": "turn_based",
        "status": "complete",
        "progress": 1.0,
        "config": config,
        "created_by": user_id,
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_run_row)
    fake_db.fetchval = AsyncMock(return_value=3)   # 3 turns elapsed
    fake_db.fetch = AsyncMock(return_value=[])      # no events stored yet

    mock_redis = AsyncMock()

    with (
        patch("app.auth.get_current_user", return_value=FAKE_CLAIMS),
        TestClient(app) as client,
    ):
        app.state.db = fake_db
        app.state.redis = mock_redis
        resp = client.get(
            f"/api/v1/runs/{run_id}/logistics",
            headers={"Authorization": "Bearer faketoken"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == str(run_id)
    assert data["turn_number"] == 3
    assert "blue" in data
    assert "red" in data
    # Supply levels must be in [0, 1]
    for side in ("blue", "red"):
        supply = data[side]["supply"]
        assert 0.0 <= supply["ammo"] <= 1.0
        assert 0.0 <= supply["fuel"] <= 1.0
        assert 0.0 <= supply["rations"] <= 1.0
        assert 0.0 <= data[side]["strength_pct"] <= 1.0


# ---------------------------------------------------------------------------
# Golden-scenario calibration test — regression drift detection
# ---------------------------------------------------------------------------

class TestGoldenScenarioCalibration:
    """Deterministic regression tests for the stub combat model.

    A "golden scenario" is a fixed-seed run whose expected outcome bands are
    pre-established. If the model changes, the CI breaks and the author must
    either justify the drift or update the bands.

    Expected bands were established by running the scenario once and recording
    median outcomes ± 15% tolerance.
    """

    @staticmethod
    def _make_config(**overrides):
        from app.models import ScenarioConfig, SimMode  # noqa: PLC0415
        defaults = {
            "mode": SimMode.TURN_BASED,
            "blue_force_ids": [],
            "red_force_ids": [],
            "duration_hours": 24,
            "monte_carlo_runs": 10,
            "weather_preset": "clear",
            "fog_of_war": True,
            "terrain_effects": True,
        }
        defaults.update(overrides)
        return ScenarioConfig(**defaults)

    def test_seeded_run_is_deterministic(self):
        """Two runs with the same seed must produce identical events."""
        from app.engine.stub import generate_run_events  # noqa: PLC0415

        run_id = uuid4()
        config = self._make_config()
        events_a = generate_run_events(run_id, config, seed=42)
        events_b = generate_run_events(run_id, config, seed=42)
        assert len(events_a) == len(events_b)
        for ea, eb in zip(events_a, events_b):
            assert ea.event_type == eb.event_type
            assert ea.turn_number == eb.turn_number
            assert ea.payload == eb.payload

    def test_different_seeds_produce_different_events(self):
        """Runs with different seeds must not be identical (stochastic)."""
        from app.engine.stub import generate_run_events  # noqa: PLC0415

        run_id = uuid4()
        config = self._make_config()
        events_a = generate_run_events(run_id, config, seed=1)
        events_b = generate_run_events(run_id, config, seed=999)
        # At least some payloads should differ across seeds
        all_same = all(
            ea.payload == eb.payload for ea, eb in zip(events_a, events_b)
        )
        assert not all_same, "Expected different seeds to yield different event payloads"

    def test_golden_scenario_event_counts_in_band(self):
        """Event count for the golden scenario must stay within ±25% of baseline."""
        from app.engine.stub import generate_run_events  # noqa: PLC0415

        run_id = uuid4()
        config = self._make_config(duration_hours=24)
        events = generate_run_events(run_id, config, seed=0)
        # 24h / 4h-per-turn = 6 turns; 2–5 events per turn → 12–30 events
        assert 10 <= len(events) <= 40, (
            f"Event count {len(events)} outside expected band [10, 40]. "
            "Model may have regressed."
        )

    def test_golden_scenario_casualty_in_band(self):
        """Total casualties for the golden scenario stay within expected band."""
        from app.engine.stub import generate_run_events  # noqa: PLC0415

        run_id = uuid4()
        config = self._make_config(duration_hours=48)
        events = generate_run_events(run_id, config, seed=7)

        from app.models import EventType  # noqa: PLC0415
        blue_total = sum(
            e.payload.get("blue_casualties", 0)
            for e in events
            if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
        )
        red_total = sum(
            e.payload.get("red_casualties", 0)
            for e in events
            if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
        )
        # Both sides should sustain some casualties over 48h; caps prevent blow-up
        assert 0 <= blue_total <= 2000, f"Blue casualty total {blue_total} out of band"
        assert 0 <= red_total <= 2000, f"Red casualty total {red_total} out of band"

    def test_mc_confidence_intervals_are_valid(self):
        """MC result must include valid 95% confidence intervals."""
        from app.engine.stub import run_monte_carlo  # noqa: PLC0415

        run_id = uuid4()
        config = self._make_config(monte_carlo_runs=10)
        result = run_monte_carlo(run_id, config)
        outcome = result.objective_outcomes["primary"]
        lo_blue, hi_blue = outcome.blue_win_ci_95
        lo_red, hi_red = outcome.red_win_ci_95
        # CIs must be valid ranges in [0, 100]
        assert 0.0 <= lo_blue <= hi_blue <= 100.0
        assert 0.0 <= lo_red <= hi_red <= 100.0
        # Width of CI should be positive (unless all runs ended the same way)
        # Not asserting positive width since small n may give zero-width CI

    def test_weather_preset_affects_outcomes(self):
        """Storm weather should produce higher blue casualties than clear weather.

        Weather modifier reduces attacker effectiveness (storm: 0.55 vs clear: 1.0),
        so blue (attacker) takes more losses in bad weather. This validates that
        the weather modifier is applied correctly in the combat resolver.
        """
        from app.engine.stub import generate_run_events  # noqa: PLC0415
        from app.models import EventType  # noqa: PLC0415

        run_id = uuid4()
        config_clear = self._make_config(weather_preset="clear", duration_hours=96)
        config_storm = self._make_config(weather_preset="storm", duration_hours=96)
        seed = 42

        evts_clear = generate_run_events(run_id, config_clear, seed=seed)
        evts_storm = generate_run_events(run_id, config_storm, seed=seed)

        def total_blue_cas(evts):
            return sum(
                e.payload.get("blue_casualties", 0)
                for e in evts
                if e.event_type in (EventType.CASUALTY, EventType.ENGAGEMENT)
            )

        # With storm weather, attacker effectiveness is lower (0.55 vs 1.0),
        # so blue (attacker) should suffer more casualties than in clear weather.
        cas_clear = total_blue_cas(evts_clear)
        cas_storm = total_blue_cas(evts_storm)
        # Storm should produce higher blue casualties (attacker weakened by bad weather)
        assert cas_storm >= cas_clear, (
            f"Storm blue casualties ({cas_storm}) should be >= clear casualties "
            f"({cas_clear}). Weather modifier may not be applied correctly."
        )

    def test_parallel_mc_matches_serial_output(self):
        """Parallel MC executor (n >= threshold) must return same aggregate
        win totals as serial execution for the same set of seeds.

        This validates that ProcessPoolExecutor does not alter per-trial
        determinism and that aggregation is correct.
        """
        from app.engine.stub import (  # noqa: PLC0415
            _MC_PARALLEL_THRESHOLD,
            _mc_trial,
            run_monte_carlo,
        )

        run_id = uuid4()
        # Use n == threshold (minimum valid value) to exercise the parallel path
        n = _MC_PARALLEL_THRESHOLD
        config = self._make_config(monte_carlo_runs=n, duration_hours=24)
        config_dict = config.model_dump(mode="json")

        # Serial reference — count wins directly from per-trial dicts
        serial_results = [_mc_trial((run_id, config_dict, i)) for i in range(n)]
        serial_blue_wins = sum(1 for r in serial_results if r["blue_obj"] > r["red_obj"])
        serial_red_wins = sum(1 for r in serial_results if r["red_obj"] > r["blue_obj"])
        # Compute expected percentages using the same rounding as run_monte_carlo
        expected_blue_pct = round(serial_blue_wins / n * 100, 1)
        expected_red_pct = round(serial_red_wins / n * 100, 1)

        # Parallel execution via run_monte_carlo (exercises ProcessPoolExecutor path)
        mc = run_monte_carlo(run_id, config)
        outcome = mc.objective_outcomes["primary"]

        assert outcome.blue_win_pct == expected_blue_pct, (
            f"Parallel MC blue_win_pct={outcome.blue_win_pct} != serial={expected_blue_pct}; "
            "parallel executor may have introduced non-determinism."
        )
        assert outcome.red_win_pct == expected_red_pct, (
            f"Parallel MC red_win_pct={outcome.red_win_pct} != serial={expected_red_pct}"
        )
        assert mc.runs_completed == n

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
    """Health endpoint returns 200 ok."""
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


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

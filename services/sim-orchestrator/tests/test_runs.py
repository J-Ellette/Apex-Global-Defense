"""Tests for simulation run endpoints."""

from __future__ import annotations

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

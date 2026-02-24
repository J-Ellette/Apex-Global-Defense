"""Tests for cbrn-svc endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_user
from main import app

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FAKE_CLAIMS = {
    "uid": str(uuid4()),
    "roles": ["analyst"],
    "perms": ["scenario:read", "scenario:write", "simulation:run"],
    "org_id": str(uuid4()),
}


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass JWT validation for all tests."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Agent catalog
# ---------------------------------------------------------------------------

def test_list_agents_all():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cbrn/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    ids = {a["id"] for a in data}
    assert "VX" in ids
    assert "GB" in ids
    assert "BA" in ids
    assert "CS137" in ids
    assert "IND-10KT" in ids


def test_list_agents_filter_category():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cbrn/agents?category=CHEMICAL")
    assert resp.status_code == 200
    data = resp.json()
    assert all(a["category"] == "CHEMICAL" for a in data)
    assert len(data) >= 3


def test_list_agents_search():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cbrn/agents?q=nerve")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any("nerve" in a["description"].lower() or "nerve" in a["sub_category"].lower() for a in data)


def test_get_agent_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cbrn/agents/VX")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "VX"
    assert data["category"] == "CHEMICAL"


def test_get_agent_not_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cbrn/agents/UNKNOWN99")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Release CRUD
# ---------------------------------------------------------------------------

def test_list_releases_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/cbrn/releases")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_release_invalid_agent():
    fake_db = AsyncMock()
    payload = {
        "agent_id": "UNKNOWN",
        "latitude": 48.85,
        "longitude": 2.35,
        "quantity_kg": 1.0,
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/cbrn/releases", json=payload)
    assert resp.status_code == 400


def test_create_release_valid():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    payload = {
        "agent_id": "GB",
        "latitude": 48.85,
        "longitude": 2.35,
        "quantity_kg": 5.0,
        "duration_min": 15.0,
        "release_height_m": 2.0,
        "label": "Test Release",
        "met": {
            "wind_speed_ms": 4.0,
            "wind_direction_deg": 270.0,
            "stability_class": "D",
            "mixing_height_m": 800.0,
            "temperature_c": 20.0,
            "relative_humidity_pct": 65.0,
        },
        "population_density_per_km2": 1000.0,
    }

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/cbrn/releases", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_id"] == "GB"
    assert data["latitude"] == 48.85
    assert data["quantity_kg"] == 5.0
    assert "id" in data


def test_get_release_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/cbrn/releases/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Dispersion simulation
# ---------------------------------------------------------------------------

def test_simulate_release_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/cbrn/releases/{uuid4()}/simulate")
    assert resp.status_code == 404


def test_simulate_release_sarin():
    """Run a full dispersion simulation for sarin and verify plume output."""
    import json

    release_id = uuid4()
    now = datetime.now(timezone.utc)
    met_json = json.dumps({
        "wind_speed_ms": 4.0,
        "wind_direction_deg": 270.0,
        "stability_class": "D",
        "mixing_height_m": 800.0,
        "temperature_c": 20.0,
        "relative_humidity_pct": 60.0,
    })
    release_row = {
        "id": release_id,
        "scenario_id": None,
        "agent_id": "GB",
        "release_type": "POINT",
        "latitude": 48.85,
        "longitude": 2.35,
        "quantity_kg": 10.0,
        "release_height_m": 1.5,
        "duration_min": 10.0,
        "met": met_json,
        "population_density_per_km2": 500.0,
        "label": "Sarin sim",
        "notes": None,
        "created_at": now,
        "created_by": "test",
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=release_row)
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/cbrn/releases/{release_id}/simulate")

    assert resp.status_code == 200
    data = resp.json()
    assert "contours" in data
    assert "max_downwind_km" in data
    assert data["max_downwind_km"] >= 0
    assert "total_estimated_casualties" in data
    assert isinstance(data["total_estimated_casualties"], int)
    assert "wind_direction_deg" in data
    assert "summary" in data
    # Plume should extend some downwind distance for a 10kg sarin release
    assert data["max_downwind_km"] > 0


def test_simulate_release_vx():
    """Run dispersion for VX (persistent nerve agent)."""
    import json

    release_id = uuid4()
    now = datetime.now(timezone.utc)
    met_json = json.dumps({
        "wind_speed_ms": 2.0,
        "wind_direction_deg": 90.0,
        "stability_class": "F",
        "mixing_height_m": 300.0,
        "temperature_c": 10.0,
        "relative_humidity_pct": 80.0,
    })
    release_row = {
        "id": release_id,
        "scenario_id": None,
        "agent_id": "VX",
        "release_type": "POINT",
        "latitude": 51.5,
        "longitude": -0.1,
        "quantity_kg": 0.5,
        "release_height_m": 1.0,
        "duration_min": 5.0,
        "met": met_json,
        "population_density_per_km2": 2000.0,
        "label": "VX test",
        "notes": None,
        "created_at": now,
        "created_by": "test",
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=release_row)
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/cbrn/releases/{release_id}/simulate")

    assert resp.status_code == 200
    data = resp.json()
    assert data["stability_class"] == "F"
    assert data["wind_direction_deg"] == 90.0
    assert data["max_downwind_km"] >= 0


def test_simulate_release_anthrax():
    """Run dispersion for anthrax (bio agent, no Ct threshold → fallback zone)."""
    import json

    release_id = uuid4()
    now = datetime.now(timezone.utc)
    met_json = json.dumps({
        "wind_speed_ms": 5.0,
        "wind_direction_deg": 180.0,
        "stability_class": "C",
        "mixing_height_m": 1200.0,
        "temperature_c": 25.0,
        "relative_humidity_pct": 50.0,
    })
    release_row = {
        "id": release_id,
        "scenario_id": None,
        "agent_id": "BA",
        "release_type": "POINT",
        "latitude": 40.7,
        "longitude": -74.0,
        "quantity_kg": 1.0,
        "release_height_m": 100.0,
        "duration_min": 2.0,
        "met": met_json,
        "population_density_per_km2": 3000.0,
        "label": "Anthrax dispersion",
        "notes": None,
        "created_at": now,
        "created_by": "test",
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=release_row)
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/cbrn/releases/{release_id}/simulate")

    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "protective_actions" in data


# ---------------------------------------------------------------------------
# Plume engine unit tests (no HTTP)
# ---------------------------------------------------------------------------

def test_plume_engine_direct():
    """Test the plume engine directly with a known input."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from app.data.agents import AGENT_MAP
    from app.engine.plume import run_dispersion
    from app.models import CBRNRelease, MetConditions, StabilityClass

    release = CBRNRelease(
        id=uuid4(),
        agent_id="GB",
        latitude=48.85,
        longitude=2.35,
        quantity_kg=5.0,
        release_height_m=1.0,
        duration_min=10.0,
        met=MetConditions(
            wind_speed_ms=3.0,
            wind_direction_deg=270.0,
            stability_class=StabilityClass.D,
            mixing_height_m=800.0,
            temperature_c=15.0,
            relative_humidity_pct=60.0,
        ),
        population_density_per_km2=500.0,
        created_at=datetime.now(timezone.utc),
    )

    agent = AGENT_MAP["GB"]
    result = run_dispersion(release, agent)

    # The plume should have at least some extent
    assert result.max_downwind_km >= 0
    # Contours should be generated for a real chemical agent
    assert isinstance(result.contours, list)
    # Summary should be non-empty
    assert len(result.summary) > 0
    # Metadata should include emission rate
    assert "emission_rate_g_s" in result.metadata
    assert result.metadata["emission_rate_g_s"] > 0

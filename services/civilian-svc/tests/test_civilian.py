"""Tests for civilian-svc endpoints and engine logic."""
from __future__ import annotations

import json
import math
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
    "perms": ["scenario:read", "scenario:write"],
    "org_id": str(uuid4()),
}


@pytest.fixture(autouse=True)
def override_auth():
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
# Engine: compute_impact unit tests (no DB)
# ---------------------------------------------------------------------------

def test_compute_impact_empty_zones_zero_totals():
    from app.engine.impact import compute_impact
    run_id = uuid4()
    result = compute_impact(run_id=run_id, scenario_id=None, zones=[], events=[])
    assert result.total_civilian_casualties == 0
    assert result.total_civilian_wounded == 0
    assert result.total_displaced_persons == 0
    assert result.zone_impacts == []
    assert result.run_id == run_id


def test_compute_impact_engagement_near_urban_zone_causes_casualties():
    from app.engine.impact import compute_impact
    zone = {
        "id": str(uuid4()),
        "name": "TestCity",
        "latitude": 33.0,
        "longitude": 44.0,
        "radius_km": 10.0,
        "population": 1000000,
        "density_class": "URBAN",
    }
    event = {
        "event_type": "ENGAGEMENT",
        "location": {"lat": 33.0, "lng": 44.0},
    }
    result = compute_impact(run_id=uuid4(), scenario_id=None, zones=[zone], events=[event])
    assert result.total_civilian_casualties > 0
    assert result.total_civilian_wounded > 0
    assert result.total_displaced_persons > 0


def test_compute_impact_airstrike_higher_than_engagement():
    from app.engine.impact import compute_impact
    zone = {
        "id": str(uuid4()),
        "name": "TestCity",
        "latitude": 33.0,
        "longitude": 44.0,
        "radius_km": 10.0,
        "population": 1000000,
        "density_class": "URBAN",
    }
    engagement_event = {"event_type": "ENGAGEMENT", "location": {"lat": 33.0, "lng": 44.0}}
    airstrike_event = {"event_type": "AIRSTRIKE", "location": {"lat": 33.0, "lng": 44.0}}

    r_eng = compute_impact(run_id=uuid4(), scenario_id=None, zones=[zone], events=[engagement_event])
    r_air = compute_impact(run_id=uuid4(), scenario_id=None, zones=[zone], events=[airstrike_event])

    assert r_air.total_civilian_casualties > r_eng.total_civilian_casualties


def test_compute_impact_cbrn_causes_most_casualties():
    from app.engine.impact import compute_impact
    zone = {
        "id": str(uuid4()),
        "name": "TestCity",
        "latitude": 33.0,
        "longitude": 44.0,
        "radius_km": 10.0,
        "population": 1000000,
        "density_class": "URBAN",
    }
    airstrike_event = {"event_type": "AIRSTRIKE", "location": {"lat": 33.0, "lng": 44.0}}
    cbrn_event = {"event_type": "CBRN_RELEASE", "location": {"lat": 33.0, "lng": 44.0}}

    r_air = compute_impact(run_id=uuid4(), scenario_id=None, zones=[zone], events=[airstrike_event])
    r_cbrn = compute_impact(run_id=uuid4(), scenario_id=None, zones=[zone], events=[cbrn_event])

    assert r_cbrn.total_civilian_casualties > r_air.total_civilian_casualties


def test_compute_impact_far_event_has_no_effect():
    from app.engine.impact import compute_impact
    zone = {
        "id": str(uuid4()),
        "name": "TestCity",
        "latitude": 33.0,
        "longitude": 44.0,
        "radius_km": 10.0,
        "population": 1000000,
        "density_class": "URBAN",
    }
    # Place event ~500km away (well beyond 3× radius = 30km)
    far_event = {"event_type": "AIRSTRIKE", "location": {"lat": 38.0, "lng": 44.0}}
    result = compute_impact(run_id=uuid4(), scenario_id=None, zones=[zone], events=[far_event])
    assert result.total_civilian_casualties == 0
    assert result.total_displaced_persons == 0


def test_haversine_distance():
    from app.engine.impact import _haversine_km
    # Baghdad to Kabul ~2290 km
    dist = _haversine_km(33.3152, 44.3661, 34.5553, 69.2075)
    assert 2200 < dist < 2400

    # Same point: distance should be ~0
    dist_zero = _haversine_km(33.0, 44.0, 33.0, 44.0)
    assert dist_zero < 0.001


# ---------------------------------------------------------------------------
# Population CRUD endpoints (mocked DB)
# ---------------------------------------------------------------------------

def test_list_population_zones_empty_returns_seeds():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/civilian/population")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 8  # 8 seed zones
    names = {z["name"] for z in data}
    assert "Baghdad" in names
    assert "Kyiv" in names


def test_create_population_zone():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/civilian/population",
            json={
                "name": "TestZone",
                "country_code": "TST",
                "latitude": 10.0,
                "longitude": 20.0,
                "radius_km": 15.0,
                "population": 500000,
                "density_class": "URBAN",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TestZone"
    assert data["country_code"] == "TST"
    assert data["population"] == 500000


def test_get_population_zone_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/civilian/population/{uuid4()}")
    assert resp.status_code == 404


def test_get_population_zone_found():
    zone_id = uuid4()
    fake_row = {
        "id": zone_id,
        "scenario_id": None,
        "name": "Baghdad",
        "country_code": "IRQ",
        "latitude": 33.3152,
        "longitude": 44.3661,
        "radius_km": 30.0,
        "population": 7000000,
        "density_class": "URBAN",
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_row)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/civilian/population/{zone_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Baghdad"


def test_delete_population_zone_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 0")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/civilian/population/{uuid4()}")
    assert resp.status_code == 404


def test_delete_population_zone_success():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/civilian/population/{uuid4()}")
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Refugee Flows endpoints (mocked DB)
# ---------------------------------------------------------------------------

def test_list_flows_empty_returns_seeds():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/civilian/flows")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    origins = {f["origin_name"] for f in data}
    assert "Eastern Ukraine" in origins
    assert "Darfur, Sudan" in origins


def test_create_refugee_flow():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/civilian/flows",
            json={
                "origin_name": "East Region",
                "destination_name": "Safe Zone",
                "origin_lat": 10.0,
                "origin_lon": 20.0,
                "destination_lat": 15.0,
                "destination_lon": 25.0,
                "displaced_persons": 10000,
                "status": "PROJECTED",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["origin_name"] == "East Region"
    assert data["displaced_persons"] == 10000


def test_update_refugee_flow():
    flow_id = uuid4()
    fake_row = {
        "id": flow_id,
        "scenario_id": None,
        "origin_zone_id": None,
        "origin_name": "East Region",
        "destination_name": "Safe Zone",
        "origin_lat": 10.0,
        "origin_lon": 20.0,
        "destination_lat": 15.0,
        "destination_lon": 25.0,
        "displaced_persons": 10000,
        "status": "PROJECTED",
        "started_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_row)
    fake_db.execute = AsyncMock(return_value="UPDATE 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.put(
            f"/api/v1/civilian/flows/{flow_id}",
            json={"status": "CONFIRMED", "displaced_persons": 15000},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "CONFIRMED"
    assert data["displaced_persons"] == 15000


def test_delete_refugee_flow_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 0")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/civilian/flows/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Corridors endpoints (mocked DB)
# ---------------------------------------------------------------------------

def test_list_corridors_empty_returns_seeds():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/civilian/corridors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    names = {c["name"] for c in data}
    assert "Mariupol Evacuation Corridor" in names


def test_create_corridor():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/civilian/corridors",
            json={
                "name": "Test Corridor",
                "waypoints": [
                    {"lat": 33.0, "lon": 44.0},
                    {"lat": 34.0, "lon": 45.0},
                ],
                "status": "OPEN",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Corridor"
    assert data["status"] == "OPEN"
    assert len(data["waypoints"]) == 2


def test_update_corridor():
    corridor_id = uuid4()
    fake_row = {
        "id": corridor_id,
        "scenario_id": None,
        "name": "Test Corridor",
        "waypoints": json.dumps([{"lat": 33.0, "lon": 44.0}, {"lat": 34.0, "lon": 45.0}]),
        "status": "OPEN",
        "notes": None,
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
    }
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_row)
    fake_db.execute = AsyncMock(return_value="UPDATE 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.put(
            f"/api/v1/civilian/corridors/{corridor_id}",
            json={"status": "RESTRICTED", "notes": "Under review"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "RESTRICTED"
    assert data["notes"] == "Under review"


def test_delete_corridor_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 0")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/civilian/corridors/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Impact assessment endpoint (mocked DB)
# ---------------------------------------------------------------------------

def test_assess_impact_empty_zones():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    run_id = uuid4()
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/civilian/impact/assess",
            json={"run_id": str(run_id)},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == str(run_id)
    assert data["total_civilian_casualties"] == 0
    assert data["methodology"] == "deterministic"
    assert data["zone_impacts"] == []


def test_get_impact_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/civilian/impact/{uuid4()}")
    assert resp.status_code == 404

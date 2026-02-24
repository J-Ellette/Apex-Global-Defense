"""Tests for terror-svc endpoints."""

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
# Attack Type Catalog
# ---------------------------------------------------------------------------

def test_list_attack_types_all():
    with TestClient(app) as client:
        resp = client.get("/api/v1/terror/attack-types")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 8
    ids = {t["id"] for t in data}
    assert "VRAM" in ids
    assert "ASHT" in ids
    assert "SBOM" in ids
    assert "CHEM" in ids
    assert "CYBR" in ids


def test_list_attack_types_filter_category():
    with TestClient(app) as client:
        resp = client.get("/api/v1/terror/attack-types?category=KINETIC")
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["category"] == "KINETIC" for t in data)
    assert len(data) >= 3


def test_get_attack_type_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/terror/attack-types/VRAM")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "VRAM"
    assert data["category"] == "KINETIC"
    assert len(data["countermeasures"]) > 0


def test_get_attack_type_not_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/terror/attack-types/UNKNOWN999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Site CRUD
# ---------------------------------------------------------------------------

def test_list_sites_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/terror/sites")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_site_valid():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "name": "Central Train Station",
        "site_type": "TRANSPORT_HUB",
        "address": "1 Station Plaza",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "country_code": "FR",
        "population_capacity": 50000,
        "physical_security": 0.6,
        "access_control": 0.5,
        "surveillance": 0.7,
        "emergency_response": 0.5,
        "crowd_density": "HIGH",
        "assigned_agencies": ["Police Nationale", "DGSI"],
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/sites", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Central Train Station"
    assert data["site_type"] == "TRANSPORT_HUB"
    assert "id" in data
    assert "vulnerability_score" in data
    # base = 10 * (1 - mean(0.6, 0.5, 0.7, 0.5)) = 10 * 0.425 = 4.25
    # HIGH crowd multiplier = 1.2 → score = 5.1 > 3.0
    assert data["vulnerability_score"] > 3.0


def test_create_site_vulnerability_score_computed():
    """Verify vulnerability score formula: low security + critical density = high score."""
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "name": "Unprotected Market",
        "site_type": "MARKET",
        "physical_security": 0.1,
        "access_control": 0.1,
        "surveillance": 0.1,
        "emergency_response": 0.1,
        "crowd_density": "CRITICAL",
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/sites", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["vulnerability_score"] >= 9.0  # Very high due to low security + CRITICAL density


def test_create_site_hardened_low_score():
    """Verify well-secured site has low vulnerability score."""
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "name": "Hardened Military Base",
        "site_type": "MILITARY_BASE",
        "physical_security": 0.95,
        "access_control": 0.95,
        "surveillance": 0.95,
        "emergency_response": 0.95,
        "crowd_density": "LOW",
        "status": "HARDENED",
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/sites", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["vulnerability_score"] <= 2.0


def test_get_site_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/terror/sites/{uuid4()}")
    assert resp.status_code == 404


def test_delete_site_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(side_effect=["DELETE 0", "DELETE 0", "DELETE 0"])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/terror/sites/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Threat Scenario CRUD
# ---------------------------------------------------------------------------

def test_list_threat_scenarios_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/terror/threat-scenarios")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_threat_scenario_invalid_type():
    fake_db = AsyncMock()
    site_id = uuid4()
    fake_db.fetchrow = AsyncMock(return_value={"id": site_id})
    payload = {
        "site_id": str(site_id),
        "attack_type_id": "UNKNOWN_ATTACK",
        "threat_level": "HIGH",
        "probability": 0.3,
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/threat-scenarios", json=payload)
    assert resp.status_code == 400


def test_create_threat_scenario_site_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    payload = {
        "site_id": str(uuid4()),
        "attack_type_id": "VRAM",
        "threat_level": "HIGH",
        "probability": 0.4,
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/threat-scenarios", json=payload)
    assert resp.status_code == 400


def test_create_threat_scenario_valid():
    fake_db = AsyncMock()
    site_id = uuid4()
    fake_db.fetchrow = AsyncMock(return_value={"id": site_id})
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "site_id": str(site_id),
        "attack_type_id": "ASHT",
        "threat_level": "CRITICAL",
        "probability": 0.35,
        "estimated_killed_low": 3,
        "estimated_killed_high": 15,
        "estimated_wounded_low": 10,
        "estimated_wounded_high": 40,
        "notes": "Intelligence indicates pre-attack surveillance activity",
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/threat-scenarios", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["attack_type_id"] == "ASHT"
    assert data["threat_level"] == "CRITICAL"
    assert data["probability"] == 0.35
    assert "id" in data


def test_get_threat_scenario_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/terror/threat-scenarios/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Response Plan CRUD
# ---------------------------------------------------------------------------

def test_list_response_plans_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/terror/response-plans")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_response_plan_site_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    payload = {
        "site_id": str(uuid4()),
        "title": "Emergency Response Plan Alpha",
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/response-plans", json=payload)
    assert resp.status_code == 400


def test_create_response_plan_valid():
    fake_db = AsyncMock()
    site_id = uuid4()
    fake_db.fetchrow = AsyncMock(return_value={"id": site_id})
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "site_id": str(site_id),
        "title": "Station Alpha Response Plan",
        "description": "Coordinated response for active threat scenarios at Central Station",
        "agencies": [
            {
                "agency_name": "Metropolitan Police",
                "agency_type": "POLICE",
                "role": "PRIMARY",
                "contact": "+44-20-7230-1212",
            },
            {
                "agency_name": "London Ambulance Service",
                "agency_type": "MEDICAL",
                "role": "SUPPORTING",
            },
            {
                "agency_name": "MI5",
                "agency_type": "INTELLIGENCE",
                "role": "NOTIFIED",
            },
        ],
        "evacuation_routes": ["North exit to King's Cross", "South exit to Strand"],
        "shelter_capacity": 500,
        "estimated_response_time_min": 8,
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/terror/response-plans", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Station Alpha Response Plan"
    assert len(data["agencies"]) == 3
    assert len(data["evacuation_routes"]) == 2
    assert data["shelter_capacity"] == 500
    assert data["status"] == "DRAFT"
    assert "id" in data


def test_get_response_plan_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/terror/response-plans/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Vulnerability Analysis
# ---------------------------------------------------------------------------

def test_analyze_site_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/terror/sites/{uuid4()}/analysis")
    assert resp.status_code == 404


def test_analyze_site_high_vulnerability():
    """A poorly-secured transport hub with critical crowd density should return high vulnerability."""
    now = datetime.now(timezone.utc)
    site_id = uuid4()
    site_row = {
        "id": site_id,
        "scenario_id": None,
        "name": "Vulnerable Airport",
        "site_type": "TRANSPORT_HUB",
        "address": None,
        "latitude": 51.5,
        "longitude": -0.1,
        "country_code": "GB",
        "population_capacity": 100000,
        "physical_security": 0.2,
        "access_control": 0.2,
        "surveillance": 0.3,
        "emergency_response": 0.2,
        "crowd_density": "CRITICAL",
        "vulnerability_score": 9.0,
        "assigned_agencies": "[]",
        "notes": None,
        "status": "ACTIVE",
        "created_at": now,
        "created_by": "test",
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=site_row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/terror/sites/{site_id}/analysis")

    assert resp.status_code == 200
    data = resp.json()
    assert data["vulnerability_score"] >= 8.0
    assert len(data["top_attack_risks"]) == 5
    assert len(data["recommendations"]) >= 3
    assert len(data["analysis_summary"]) > 0
    # VRAM and EXPL should be in top risks for a transport hub
    top_ids = {r["attack_type_id"] for r in data["top_attack_risks"]}
    assert len(top_ids & {"VRAM", "EXPL", "SBOM", "CHEM", "INFR"}) >= 2


def test_analyze_site_low_vulnerability():
    """A well-secured military base with low crowd density should return low vulnerability."""
    now = datetime.now(timezone.utc)
    site_id = uuid4()
    site_row = {
        "id": site_id,
        "scenario_id": None,
        "name": "Secure Military Installation",
        "site_type": "MILITARY_BASE",
        "address": None,
        "latitude": 38.9,
        "longitude": -77.0,
        "country_code": "US",
        "population_capacity": 500,
        "physical_security": 0.95,
        "access_control": 0.95,
        "surveillance": 0.95,
        "emergency_response": 0.95,
        "crowd_density": "LOW",
        "vulnerability_score": 1.2,
        "assigned_agencies": "[]",
        "notes": None,
        "status": "HARDENED",
        "created_at": now,
        "created_by": "test",
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=site_row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/terror/sites/{site_id}/analysis")

    assert resp.status_code == 200
    data = resp.json()
    assert data["vulnerability_score"] <= 3.0
    assert len(data["top_attack_risks"]) == 5


# ---------------------------------------------------------------------------
# Direct vulnerability score unit tests (no HTTP)
# ---------------------------------------------------------------------------

def test_vulnerability_score_extremes():
    from app.models import CrowdDensity
    from app.routers.sites import _compute_vulnerability_score

    # Minimum security, critical density → max score
    score_max = _compute_vulnerability_score(0.0, 0.0, 0.0, 0.0, CrowdDensity.CRITICAL)
    assert score_max == 10.0

    # Maximum security, low density → min score
    score_min = _compute_vulnerability_score(1.0, 1.0, 1.0, 1.0, CrowdDensity.LOW)
    assert score_min == 1.0


def test_vulnerability_score_medium():
    from app.models import CrowdDensity
    from app.routers.sites import _compute_vulnerability_score

    # Equal moderate security + medium density → should be around 5
    score = _compute_vulnerability_score(0.5, 0.5, 0.5, 0.5, CrowdDensity.MEDIUM)
    assert 4.5 <= score <= 5.5


def test_attack_type_catalog_completeness():
    from app.data.attack_types import ATTACK_TYPE_CATALOG, ATTACK_TYPE_MAP

    assert len(ATTACK_TYPE_CATALOG) >= 8
    ids = {e.id for e in ATTACK_TYPE_CATALOG}
    assert "VRAM" in ids
    assert "ASHT" in ids
    assert "SBOM" in ids
    assert "CHEM" in ids
    assert "CYBR" in ids
    assert "INFR" in ids
    assert len(ATTACK_TYPE_MAP) == len(ATTACK_TYPE_CATALOG)

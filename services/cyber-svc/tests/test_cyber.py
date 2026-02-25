"""Tests for cyber-svc endpoints."""

from __future__ import annotations

from datetime import datetime
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
# ATT&CK Techniques
# ---------------------------------------------------------------------------

def test_list_techniques_all():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cyber/techniques")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    ids = {t["id"] for t in data}
    assert "T1566" in ids
    assert "T1486" in ids


def test_list_techniques_filter_tactic():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cyber/techniques?tactic=impact")
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["tactic"] == "impact" for t in data)
    assert len(data) >= 2


def test_list_techniques_filter_severity():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cyber/techniques?severity=CRITICAL")
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["severity"] == "CRITICAL" for t in data)


def test_list_techniques_search():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cyber/techniques?q=phishing")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any("phishing" in t["name"].lower() or "phishing" in t["description"].lower() for t in data)


def test_get_technique_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cyber/techniques/T1566")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "T1566"
    assert data["name"] == "Phishing"


def test_get_technique_not_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/cyber/techniques/T9999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Infrastructure graph
# ---------------------------------------------------------------------------

def test_get_graph_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/cyber/infrastructure")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"nodes": [], "edges": []}


def test_create_node():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    payload = {
        "label": "Web Server 01",
        "node_type": "SERVER",
        "network": "DMZ",
        "ip_address": "10.0.1.5",
        "criticality": "HIGH",
    }

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/cyber/infrastructure/nodes", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["label"] == "Web Server 01"
    assert data["node_type"] == "SERVER"
    assert data["criticality"] == "HIGH"
    assert "id" in data


# ---------------------------------------------------------------------------
# Cyber attacks
# ---------------------------------------------------------------------------

def test_create_attack_unknown_technique():
    fake_db = AsyncMock()

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/cyber/attacks",
            json={"technique_id": "T9999", "attacker": "APT-X", "impact": "HIGH"},
        )
    assert resp.status_code == 400


def test_create_attack_valid():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/cyber/attacks",
            json={
                "technique_id": "T1566",
                "attacker": "APT-28",
                "impact": "HIGH",
                "notes": "Spear-phishing campaign",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["technique_id"] == "T1566"
    assert data["attacker"] == "APT-28"
    assert data["status"] == "PLANNED"
    assert 0.0 <= data["success_probability"] <= 1.0


def test_get_attack_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/cyber/attacks/{uuid4()}")
    assert resp.status_code == 404


def test_simulate_attack():
    attack_id = uuid4()
    target_node_id = uuid4()

    attack_row = {
        "id": attack_id,
        "scenario_id": None,
        "technique_id": "T1486",
        "target_node_id": target_node_id,
        "attacker": "APT-X",
        "status": "PLANNED",
        "success_probability": 0.45,
        "impact": "CRITICAL",
        "notes": None,
        "created_at": datetime.utcnow(),
        "executed_at": None,
        "result": None,
    }
    node_row = {"label": "Domain Controller"}

    fake_db = AsyncMock()

    async def fake_fetchrow(query, *args):
        if "cyber_attacks" in query:
            return attack_row
        if "cyber_infra_nodes" in query:
            return node_row
        return None

    async def fake_fetch(query, *args):
        return []

    fake_db.fetchrow = fake_fetchrow
    fake_db.fetch = fake_fetch
    fake_db.execute = AsyncMock(return_value="UPDATE 1")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            f"/api/v1/cyber/attacks/{attack_id}/simulate",
            json={"defender_skill": 0.4, "network_hardening": 0.3},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    assert "detected" in data
    assert "damage_level" in data
    assert "narrative" in data
    assert isinstance(data["persistence_achieved"], bool)
    assert data["damage_level"] in ("NONE", "MINIMAL", "MODERATE", "SEVERE", "CATASTROPHIC")


# ---------------------------------------------------------------------------
# STIX/TAXII endpoints
# ---------------------------------------------------------------------------

def test_list_stix_indicators_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/cyber/stix/indicators")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_stix_indicator_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/cyber/stix/indicators/{uuid4()}")
    assert resp.status_code == 404


def test_delete_stix_indicator_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 0")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/cyber/stix/indicators/{uuid4()}")
    assert resp.status_code == 404


def test_taxii_ingest_dry_run():
    """TAXII ingest with dry_run=True should return synthetic data without hitting DB."""
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/cyber/taxii/ingest",
            json={
                "server_url": "https://taxii.example.com",
                "collection_id": "test-collection",
                "max_items": 10,
                "dry_run": True,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["dry_run"] is True
    assert data["items_fetched"] >= 1
    assert data["items_saved"] >= 1
    # No DB inserts in dry_run mode
    fake_db.execute.assert_not_called()


"""Tests for asym-svc endpoints."""

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
# Cell function catalog (via cell-types embedded in data module)
# ---------------------------------------------------------------------------

def test_cell_function_catalog_completeness():
    from app.data.cell_types import CELL_FUNCTION_CATALOG, CELL_FUNCTION_MAP
    assert len(CELL_FUNCTION_CATALOG) >= 8
    ids = {e.id for e in CELL_FUNCTION_CATALOG}
    assert "CMD" in ids
    assert "OPS" in ids
    assert "TECH" in ids
    assert len(CELL_FUNCTION_MAP) == len(CELL_FUNCTION_CATALOG)


# ---------------------------------------------------------------------------
# IED Type catalog
# ---------------------------------------------------------------------------

def test_list_ied_types_all():
    with TestClient(app) as client:
        resp = client.get("/api/v1/asym/ied-types")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    ids = {t["id"] for t in data}
    assert "VBIED" in ids
    assert "PBIED" in ids
    assert "EFP" in ids
    assert "PLACED_IED" in ids


def test_list_ied_types_filter_category():
    with TestClient(app) as client:
        resp = client.get("/api/v1/asym/ied-types?category=VEHICLE")
    assert resp.status_code == 200
    data = resp.json()
    assert all(t["category"] == "VEHICLE" for t in data)
    assert len(data) >= 2


def test_get_ied_type_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/asym/ied-types/EFP")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "EFP"
    assert data["category"] == "EXPLOSIVELY_FORMED"
    assert len(data["countermeasures"]) > 0


def test_get_ied_type_not_found():
    with TestClient(app) as client:
        resp = client.get("/api/v1/asym/ied-types/UNKNOWN999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Cell CRUD
# ---------------------------------------------------------------------------

def test_list_cells_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/asym/cells")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_cell_valid():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "name": "Alpha Command",
        "function": "COMMAND",
        "structure": "HIERARCHICAL",
        "status": "ACTIVE",
        "size_estimated": 4,
        "latitude": 33.5,
        "longitude": 44.4,
        "region": "Baghdad",
        "country_code": "IQ",
        "leadership_confidence": 0.8,
        "operational_capability": 0.7,
        "funding_level": "HIGH",
        "affiliated_groups": ["ISF", "PMF"],
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/asym/cells", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alpha Command"
    assert data["function"] == "COMMAND"
    assert data["status"] == "ACTIVE"
    assert "id" in data


def test_get_cell_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/asym/cells/{uuid4()}")
    assert resp.status_code == 404


def test_delete_cell_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(side_effect=["DELETE 0", "DELETE 0"])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/asym/cells/{uuid4()}")
    assert resp.status_code == 404


def test_get_network_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/asym/network")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cells"] == []
    assert data["links"] == []


# ---------------------------------------------------------------------------
# Cell link CRUD
# ---------------------------------------------------------------------------

def test_create_cell_link_valid():
    import json as json_mod

    now = datetime.now(timezone.utc)
    cell_a_id = uuid4()
    cell_b_id = uuid4()

    async def fake_fetchrow(query, arg):
        return {"id": arg}

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(side_effect=fake_fetchrow)
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")

    payload = {
        "source_cell_id": str(cell_a_id),
        "target_cell_id": str(cell_b_id),
        "link_type": "COMMAND",
        "strength": "STRONG",
        "confidence": 0.9,
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/asym/cell-links", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["link_type"] == "COMMAND"
    assert data["strength"] == "STRONG"
    assert "id" in data


def test_create_cell_link_missing_source():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    payload = {
        "source_cell_id": str(uuid4()),
        "target_cell_id": str(uuid4()),
        "link_type": "LOGISTICS",
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/asym/cell-links", json=payload)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# IED Incident CRUD
# ---------------------------------------------------------------------------

def test_list_incidents_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/asym/incidents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_incident_invalid_type():
    fake_db = AsyncMock()
    payload = {
        "ied_type_id": "UNKNOWN_TYPE",
        "latitude": 33.5,
        "longitude": 44.4,
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/asym/incidents", json=payload)
    assert resp.status_code == 400


def test_create_incident_valid():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="INSERT 0 1")
    payload = {
        "ied_type_id": "VBIED",
        "latitude": 33.5,
        "longitude": 44.4,
        "status": "CONFIRMED",
        "detonation_type": "REMOTE",
        "target_type": "CONVOY",
        "casualties_killed": 2,
        "casualties_wounded": 8,
        "notes": "Route 6 ambush",
    }
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post("/api/v1/asym/incidents", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["ied_type_id"] == "VBIED"
    assert data["status"] == "CONFIRMED"
    assert data["casualties_killed"] == 2
    assert "id" in data


def test_get_incident_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/asym/incidents/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Network analysis
# ---------------------------------------------------------------------------

def test_network_analysis_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/asym/network/analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cells"] == 0
    assert data["total_links"] == 0
    assert data["top_targets"] == []
    assert len(data["coin_recommendations"]) >= 1


def test_network_analysis_with_cells():
    """Stub 3 cells + 2 links and verify analysis scores are computed."""
    import json as json_mod

    now = datetime.now(timezone.utc)
    cell_a = uuid4()
    cell_b = uuid4()
    cell_c = uuid4()

    cell_rows = [
        {
            "id": cell_a, "scenario_id": None, "name": "Command Alpha", "function": "COMMAND",
            "structure": "HIERARCHICAL", "status": "ACTIVE", "size_estimated": 4,
            "latitude": 33.5, "longitude": 44.4, "region": "Baghdad", "country_code": "IQ",
            "leadership_confidence": 0.9, "operational_capability": 0.85,
            "funding_level": "HIGH", "affiliated_groups": "[]", "notes": None,
            "created_at": now, "created_by": "test",
        },
        {
            "id": cell_b, "scenario_id": None, "name": "Ops Bravo", "function": "OPERATIONS",
            "structure": "NETWORK", "status": "ACTIVE", "size_estimated": 8,
            "latitude": 33.6, "longitude": 44.5, "region": "Baghdad", "country_code": "IQ",
            "leadership_confidence": 0.6, "operational_capability": 0.75,
            "funding_level": "MEDIUM", "affiliated_groups": "[]", "notes": None,
            "created_at": now, "created_by": "test",
        },
        {
            "id": cell_c, "scenario_id": None, "name": "Tech Charlie", "function": "TECHNICAL",
            "structure": "NETWORK", "status": "ACTIVE", "size_estimated": 2,
            "latitude": 33.4, "longitude": 44.3, "region": "Baghdad", "country_code": "IQ",
            "leadership_confidence": 0.5, "operational_capability": 0.6,
            "funding_level": "LOW", "affiliated_groups": "[]", "notes": None,
            "created_at": now, "created_by": "test",
        },
    ]

    link_rows = [
        {
            "id": uuid4(), "scenario_id": None, "source_cell_id": cell_a, "target_cell_id": cell_b,
            "link_type": "COMMAND", "strength": "STRONG", "confidence": 0.9,
            "notes": None, "created_at": now, "created_by": "test",
        },
        {
            "id": uuid4(), "scenario_id": None, "source_cell_id": cell_a, "target_cell_id": cell_c,
            "link_type": "LOGISTICS", "strength": "MODERATE", "confidence": 0.7,
            "notes": None, "created_at": now, "created_by": "test",
        },
    ]

    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(side_effect=[cell_rows, link_rows])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/asym/network/analysis")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cells"] == 3
    assert data["total_links"] == 2
    assert data["active_cells"] == 3
    assert len(data["top_targets"]) == 3
    assert len(data["coin_recommendations"]) >= 1
    assert len(data["analysis_summary"]) > 0

    # Command Alpha should have highest hub score (2 connections)
    top = data["top_targets"][0]
    assert top["cell_name"] == "Command Alpha"
    assert top["degree"] == 2
    assert top["hub_score"] > 0


# ---------------------------------------------------------------------------
# Direct analysis algorithm tests (no HTTP)
# ---------------------------------------------------------------------------

def test_betweenness_centrality_line_graph():
    """Middle node in a 3-node line should have highest betweenness."""
    from uuid import uuid4
    from app.models import CellFunction, CellStatus, CellStructure, FundingLevel, InsurgentCell
    from app.routers.analysis import _betweenness_centrality, _build_adjacency

    now = datetime.now(timezone.utc)
    ids = [uuid4() for _ in range(3)]
    cells = [
        InsurgentCell(
            id=ids[i], name=f"Cell {i}", function=CellFunction.OPERATIONS,
            status=CellStatus.ACTIVE, size_estimated=5,
            leadership_confidence=0.5, operational_capability=0.5,
            affiliated_groups=[], created_at=now,
        )
        for i in range(3)
    ]

    class FakeLink:
        def __init__(self, s, t):
            self.source_cell_id = s
            self.target_cell_id = t

    links = [FakeLink(ids[0], ids[1]), FakeLink(ids[1], ids[2])]
    adj = _build_adjacency(cells, links)
    bet = _betweenness_centrality(cells, adj)

    # Middle node (ids[1]) should have the highest betweenness
    assert bet[ids[1]] >= bet[ids[0]]
    assert bet[ids[1]] >= bet[ids[2]]

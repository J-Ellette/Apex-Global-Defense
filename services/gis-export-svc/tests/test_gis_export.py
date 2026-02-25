"""Tests for gis-export-svc endpoints and formatters."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.formatters.geojson import (
    format_cbrn_releases_geojson,
    format_civilian_zones_geojson,
    format_intel_items_geojson,
    format_units_geojson,
    COUNTRY_CENTROIDS,
)
from app.formatters.kml import format_geojson_to_kml
from main import app

# ---------------------------------------------------------------------------
# Auth stub
# ---------------------------------------------------------------------------

FAKE_CLAIMS = {
    "uid": str(uuid4()),
    "roles": ["analyst"],
    "perms": ["scenario:read"],
    "org_id": str(uuid4()),
    "cls": 4,  # TS_SCI ceiling
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# DB mock helpers
# ---------------------------------------------------------------------------

def _make_db(fetch_rows=None, fetchrow=None, execute_result="DELETE 1"):
    """Create a mock db that matches the direct-call pattern used by the routers."""
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=fetch_rows or [])
    fake_db.fetchrow = AsyncMock(return_value=fetchrow)
    fake_db.execute = AsyncMock(return_value=execute_result)
    return fake_db


def _fake_integration_row():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "name": "Test ArcGIS",
        "integration_type": "ARCGIS",
        "config": json.dumps({"service_url": "https://example.com", "api_key": "secret123"}),
        "is_active": True,
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# Test: health endpoint
# ---------------------------------------------------------------------------

def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Test: GET /export/formats
# ---------------------------------------------------------------------------

def test_list_formats():
    with TestClient(app) as client:
        resp = client.get("/api/v1/export/formats")
    assert resp.status_code == 200
    data = resp.json()
    values = [f["value"] for f in data["formats"]]
    assert "GEOJSON" in values
    assert "KML" in values


# ---------------------------------------------------------------------------
# Test: GET /export/layers
# ---------------------------------------------------------------------------

def test_list_layers():
    with TestClient(app) as client:
        resp = client.get("/api/v1/export/layers")
    assert resp.status_code == 200
    data = resp.json()
    layer_values = [l["value"] for l in data["layers"]]
    assert "UNITS" in layer_values
    assert "TERROR_SITES" in layer_values
    assert "CBRN_RELEASES" in layer_values


# ---------------------------------------------------------------------------
# Test: POST /export/generate — GeoJSON
# ---------------------------------------------------------------------------

def test_export_units_geojson(mock_db_pool):
    fake_unit = {
        "id": uuid4(),
        "name": "1st Armored Division",
        "country_code": "USA",
        "unit_type": "ARMORED",
        "strength": 15000,
        "status": "ACTIVE",
        "classification": "UNCLASS",
    }

    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[fake_unit])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/export/generate",
            json={"layer_type": "UNITS", "format": "GEOJSON", "classification": "UNCLASS"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    feat = data["features"][0]
    assert feat["geometry"]["type"] == "Point"
    assert feat["properties"]["name"] == "1st Armored Division"
    lon, lat = feat["geometry"]["coordinates"]
    assert abs(lon - COUNTRY_CENTROIDS["USA"][0]) < 0.01


# ---------------------------------------------------------------------------
# Test: POST /export/generate — KML
# ---------------------------------------------------------------------------

def test_export_terror_sites_kml(mock_db_pool):
    fake_site = {
        "id": uuid4(),
        "name": "Compound Alpha",
        "site_type": "TRAINING",
        "country_code": "AFG",
        "latitude": 33.9,
        "longitude": 67.7,
        "threat_level": "HIGH",
        "classification": "UNCLASS",
    }

    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[fake_site])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/export/generate",
            json={"layer_type": "TERROR_SITES", "format": "KML", "classification": "UNCLASS"},
        )

    assert resp.status_code == 200
    assert "kml" in resp.headers["content-type"]
    body = resp.text
    assert "<?xml" in body
    assert "<kml" in body
    assert "Compound Alpha" in body


# ---------------------------------------------------------------------------
# Test: export unsupported format returns 422
# ---------------------------------------------------------------------------

def test_export_unsupported_format(mock_db_pool):
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/export/generate",
            json={"layer_type": "UNITS", "format": "CSV", "classification": "UNCLASS"},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test: integrations CRUD
# ---------------------------------------------------------------------------

def test_list_integrations_empty(mock_db_pool):
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/integrations")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_integration_not_found(mock_db_pool):
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/integrations/{uuid4()}")

    assert resp.status_code == 404


def test_create_integration(mock_db_pool):
    row = _fake_integration_row()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Test ArcGIS",
                "integration_type": "ARCGIS",
                "config": {"service_url": "https://example.com", "api_key": "secret"},
                "is_active": True,
                "classification": "UNCLASS",
            },
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test ArcGIS"
    # api_key should be masked
    assert data["config"].get("api_key") == "***"


def test_test_integration_endpoint(mock_db_pool):
    row = {"id": uuid4()}
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/integrations/{uuid4()}/test")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["latency_ms"] == 42


# ---------------------------------------------------------------------------
# Test: KML formatter (unit test)
# ---------------------------------------------------------------------------

def test_kml_formatter_basic():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [34.85, 31.05, 0]},
                "properties": {"name": "Site Alpha", "threat": "HIGH"},
            }
        ],
    }
    kml = format_geojson_to_kml(geojson, "Test Export")
    assert '<?xml version="1.0"' in kml
    assert "<kml" in kml
    assert "<Document>" in kml
    assert "Test Export" in kml
    assert "Site Alpha" in kml
    assert "34.85,31.05,0" in kml


def test_kml_formatter_xml_escaping():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"name": "A&B <test>"},
            }
        ],
    }
    kml = format_geojson_to_kml(geojson)
    assert "&amp;" in kml
    assert "&lt;" in kml
    assert "&gt;" in kml


# ---------------------------------------------------------------------------
# Test: GeoJSON formatter (unit test)
# ---------------------------------------------------------------------------

def test_geojson_formatter_units():
    rows = [
        {"name": "Alpha Brigade", "country_code": "RUS", "unit_type": "INFANTRY",
         "strength": 5000, "status": "ACTIVE", "classification": "UNCLASS"},
    ]
    result = format_units_geojson(rows)
    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1
    feat = result["features"][0]
    assert feat["geometry"]["type"] == "Point"
    lon, lat = feat["geometry"]["coordinates"]
    assert abs(lon - COUNTRY_CENTROIDS["RUS"][0]) < 0.01
    assert feat["properties"]["name"] == "Alpha Brigade"


def test_geojson_formatter_intel_no_coords():
    rows = [{"title": "Signal Intel", "source": "SIGINT", "classification": "SECRET"}]
    result = format_intel_items_geojson(rows)
    assert result["features"][0]["geometry"]["coordinates"] == [0.0, 0.0]


def test_geojson_formatter_cbrn():
    rows = [
        {"agent_type": "NERVE_AGENT", "latitude": 48.0, "longitude": 37.5,
         "severity": "CRITICAL", "classification": "SECRET"},
    ]
    result = format_cbrn_releases_geojson(rows)
    feat = result["features"][0]
    assert feat["geometry"]["coordinates"] == [37.5, 48.0]
    assert feat["properties"]["agent_type"] == "NERVE_AGENT"

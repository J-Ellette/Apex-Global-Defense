"""Tests for econ-svc endpoints."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
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
    "cls": 4,  # TS_SCI ceiling for most tests
}


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass JWT validation for all tests."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS
    yield
    app.dependency_overrides.clear()


def _fake_sanction(sanction_type: str = "ASSET_FREEZE", status: str = "ACTIVE"):
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "name": "Test Target",
        "country_code": "RUS",
        "target_type": "COUNTRY",
        "sanction_type": sanction_type,
        "status": status,
        "imposing_parties": json.dumps(["USA", "EU"]),
        "effective_date": date(2022, 2, 24),
        "annual_gdp_impact_pct": 3.5,
        "notes": None,
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


def _fake_trade_route():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "origin_country": "CHN",
        "destination_country": "USA",
        "commodity": "semiconductors",
        "annual_value_usd": 500_000_000_000,
        "dependency_level": "CRITICAL",
        "is_disrupted": False,
        "disruption_cause": None,
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


def _fake_indicator():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "country_code": "RUS",
        "indicator_name": "GDP_GROWTH_RATE",
        "value": -2.1,
        "unit": "percent",
        "year": 2023,
        "source": "IMF",
        "classification": "UNCLASS",
        "created_at": now,
    }


def _fake_assessment():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "scenario_id": None,
        "target_country": "RUS",
        "gdp_impact_pct": 4.0,
        "inflation_rate_change": 2.6,
        "unemployment_change": 1.8,
        "currency_devaluation_pct": 4.0,
        "trade_volume_reduction_pct": 6.0,
        "affected_sectors": json.dumps(["banking", "manufacturing"]),
        "severity": "MODERATE",
        "timeline_months": 18,
        "confidence_score": 0.6,
        "notes": None,
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Sanctions — list
# ---------------------------------------------------------------------------

def test_list_sanctions_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/sanctions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_sanctions_returns_items():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[_fake_sanction()])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/sanctions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sanction_type"] == "ASSET_FREEZE"


# ---------------------------------------------------------------------------
# Sanctions — create
# ---------------------------------------------------------------------------

def test_create_sanction():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_sanction("TRADE_EMBARGO"))

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/sanctions",
            json={
                "name": "Russia",
                "country_code": "RUS",
                "sanction_type": "TRADE_EMBARGO",
                "status": "ACTIVE",
                "imposing_parties": ["USA"],
            },
        )
    assert resp.status_code == 201
    assert resp.json()["sanction_type"] == "TRADE_EMBARGO"


# ---------------------------------------------------------------------------
# Sanctions — get by id
# ---------------------------------------------------------------------------

def test_get_sanction_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/sanctions/{uuid4()}")
    assert resp.status_code == 404


def test_get_sanction_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_sanction())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/sanctions/{uuid4()}")
    assert resp.status_code == 200
    assert resp.json()["country_code"] == "RUS"


# ---------------------------------------------------------------------------
# Trade Routes — list and create
# ---------------------------------------------------------------------------

def test_list_trade_routes_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/trade-routes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_trade_route():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_trade_route())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/trade-routes",
            json={
                "origin_country": "CHN",
                "destination_country": "USA",
                "commodity": "semiconductors",
                "annual_value_usd": 500_000_000_000,
                "dependency_level": "CRITICAL",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["commodity"] == "semiconductors"
    assert data["dependency_level"] == "CRITICAL"


def test_get_trade_route_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/trade-routes/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Economic Indicators
# ---------------------------------------------------------------------------

def test_list_indicators_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/economic-indicators")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_indicator():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_indicator())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/economic-indicators",
            json={
                "country_code": "RUS",
                "indicator_name": "GDP_GROWTH_RATE",
                "value": -2.1,
                "unit": "percent",
                "year": 2023,
                "source": "IMF",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["country_code"] == "RUS"


# ---------------------------------------------------------------------------
# Impact Assessment
# ---------------------------------------------------------------------------

def test_run_impact_assessment():
    sanction_id = uuid4()
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(
        side_effect=[
            # sanctions fetch
            [{"sanction_type": "TRADE_EMBARGO", "status": "ACTIVE"}],
            # indicators fetch
            [{"country_code": "RUS", "indicator_name": "GDP_GROWTH_RATE", "value": -2.1}],
        ]
    )
    fake_db.fetchrow = AsyncMock(return_value=_fake_assessment())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/impact/assess",
            json={
                "target_country": "RUS",
                "sanction_ids": [str(sanction_id)],
                "classification": "UNCLASS",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_country"] == "RUS"
    assert data["severity"] == "MODERATE"


def test_list_assessments_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/impact/assessments")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_assessment_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/impact/assessments/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Classification ceiling enforcement
# ---------------------------------------------------------------------------

def test_classification_ceiling_blocks_write():
    """FOUO user (cls=1) cannot create a SECRET sanction."""
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": str(uuid4()),
        "roles": ["analyst"],
        "perms": ["scenario:read", "scenario:write"],
        "cls": 1,  # FOUO ceiling
    }
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/sanctions",
                json={
                    "name": "Test",
                    "country_code": "RUS",
                    "sanction_type": "ASSET_FREEZE",
                    "classification": "SECRET",
                },
            )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS


# ---------------------------------------------------------------------------
# Engine unit tests
# ---------------------------------------------------------------------------

def test_impact_engine_no_sanctions():
    from app.engine.impact import calculate_economic_impact

    result = calculate_economic_impact("RUS", [], [])
    assert result["gdp_impact_pct"] == 0.0
    assert result["severity"] == "NEGLIGIBLE"
    assert result["confidence_score"] == 0.0


def test_impact_engine_trade_embargo():
    from app.engine.impact import calculate_economic_impact

    sanctions = [{"sanction_type": "TRADE_EMBARGO"}]
    result = calculate_economic_impact("IRN", sanctions, [])
    assert result["gdp_impact_pct"] == 2.5
    assert "manufacturing" in result["affected_sectors"]
    # Single TRADE_EMBARGO (2.5%) falls in the LIMITED band (1.0–4.0)
    assert result["severity"] == "LIMITED"


def test_impact_engine_multiple_sanctions_catastrophic():
    from app.engine.impact import calculate_economic_impact

    # Enough sanctions to exceed the 15% CATASTROPHIC threshold
    sanctions = [
        {"sanction_type": "TRADE_EMBARGO"},    # 2.5
        {"sanction_type": "TRADE_EMBARGO"},    # 2.5
        {"sanction_type": "FINANCIAL_CUTOFF"}, # 2.0
        {"sanction_type": "FINANCIAL_CUTOFF"}, # 2.0
        {"sanction_type": "ASSET_FREEZE"},     # 1.5
        {"sanction_type": "SECTORAL"},         # 1.8
        {"sanction_type": "SECTORAL"},         # 1.8
        {"sanction_type": "TRADE_EMBARGO"},    # 2.5 → total ≥ 16.6
    ]
    result = calculate_economic_impact("PRK", sanctions, [])
    assert result["gdp_impact_pct"] >= 15.0
    assert result["severity"] == "CATASTROPHIC"


def test_impact_engine_confidence_increases_with_indicators():
    from app.engine.impact import calculate_economic_impact

    sanctions = [{"sanction_type": "ASSET_FREEZE"}]
    indicators = [
        {"country_code": "RUS", "indicator_name": "GDP_GROWTH_RATE", "value": -2.1},
        {"country_code": "RUS", "indicator_name": "INFLATION", "value": 8.5},
        {"country_code": "RUS", "indicator_name": "UNEMPLOYMENT", "value": 4.2},
    ]
    result = calculate_economic_impact("RUS", sanctions, indicators)
    assert result["confidence_score"] > 0.5

"""Tests for infoops-svc endpoints."""

from __future__ import annotations

import json
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
    "cls": 4,  # TS_SCI ceiling for most tests
}


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass JWT validation for all tests."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS
    yield
    app.dependency_overrides.clear()


def _fake_narrative(threat_level: str = "HIGH", status: str = "ACTIVE"):
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "title": "Test Narrative",
        "description": "A test disinformation narrative",
        "origin_country": "RUS",
        "target_countries": json.dumps(["USA", "DEU"]),
        "platforms": json.dumps(["SOCIAL_MEDIA", "STATE_MEDIA"]),
        "status": status,
        "threat_level": threat_level,
        "spread_velocity": 0.75,
        "reach_estimate": 5_000_000,
        "key_claims": json.dumps(["Claim A", "Claim B"]),
        "counter_narratives": json.dumps(["Counter A"]),
        "first_detected": now,
        "last_updated": now,
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


def _fake_campaign():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "name": "Secondary Infektion",
        "description": "Russian influence operation",
        "attributed_actor": "GRU",
        "attribution_confidence": "HIGH",
        "sponsoring_state": "RUS",
        "target_countries": json.dumps(["DEU", "FRA"]),
        "target_demographics": json.dumps(["young voters"]),
        "platforms": json.dumps(["SOCIAL_MEDIA"]),
        "status": "ACTIVE",
        "campaign_objectives": json.dumps(["Sow discord"]),
        "estimated_budget_usd": 5_000_000,
        "start_date": None,
        "end_date": None,
        "linked_narrative_ids": json.dumps([]),
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


def _fake_indicator():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "indicator_type": "BOT_NETWORK",
        "title": "Bot network amplifying energy FUD",
        "description": "Coordinated bot accounts",
        "source_url": None,
        "platform": "SOCIAL_MEDIA",
        "detected_at": now,
        "confidence_score": 0.85,
        "linked_campaign_id": None,
        "linked_narrative_id": None,
        "is_verified": False,
        "classification": "UNCLASS",
        "created_at": now,
        "updated_at": now,
    }


def _fake_assessment():
    now = datetime.now(tz=timezone.utc)
    return {
        "id": uuid4(),
        "subject": "GRU Unit 29155",
        "attributed_to": "Russian Federation",
        "confidence": "HIGH",
        "evidence_summary": "SIGINT corroborated by HUMINT",
        "supporting_indicators": json.dumps(["indicator-A"]),
        "dissenting_evidence": json.dumps([]),
        "analyst_id": "analyst-001",
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
# Narratives — list
# ---------------------------------------------------------------------------

def test_list_narratives_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/narratives")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_narratives_returns_items():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[_fake_narrative()])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/narratives")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["threat_level"] == "HIGH"
    assert data[0]["origin_country"] == "RUS"


# ---------------------------------------------------------------------------
# Narratives — create
# ---------------------------------------------------------------------------

def test_create_narrative():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_narrative("CRITICAL"))

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/narratives",
            json={
                "title": "Energy FUD",
                "threat_level": "CRITICAL",
                "platforms": ["SOCIAL_MEDIA"],
                "spread_velocity": 0.9,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["threat_level"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Narratives — get by id
# ---------------------------------------------------------------------------

def test_get_narrative_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/narratives/{uuid4()}")
    assert resp.status_code == 404


def test_get_narrative_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_narrative())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/narratives/{uuid4()}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Narrative"


# ---------------------------------------------------------------------------
# Narratives — analyze
# ---------------------------------------------------------------------------

def test_analyze_narrative():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_narrative("HIGH"))

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/narratives/{uuid4()}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert "spread_score" in data
    assert "virality_index" in data
    assert "recommended_actions" in data
    assert data["risk_level"] == "HIGH"


# ---------------------------------------------------------------------------
# Campaigns — list and create
# ---------------------------------------------------------------------------

def test_list_campaigns_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/campaigns")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_campaign():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_campaign())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/campaigns",
            json={
                "name": "Secondary Infektion",
                "attributed_actor": "GRU",
                "attribution_confidence": "HIGH",
                "sponsoring_state": "RUS",
                "status": "ACTIVE",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Secondary Infektion"
    assert resp.json()["attribution_confidence"] == "HIGH"


def test_get_campaign_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/campaigns/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Indicators — list and create
# ---------------------------------------------------------------------------

def test_list_indicators_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/indicators")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_indicator():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_indicator())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/indicators",
            json={
                "indicator_type": "BOT_NETWORK",
                "title": "Bot network amplifying energy FUD",
                "platform": "SOCIAL_MEDIA",
                "confidence_score": 0.85,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["indicator_type"] == "BOT_NETWORK"


def test_get_indicator_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/indicators/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Attribution — list and create
# ---------------------------------------------------------------------------

def test_list_attribution_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/attribution")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_attribution():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_assessment())

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/attribution",
            json={
                "subject": "GRU Unit 29155",
                "attributed_to": "Russian Federation",
                "confidence": "HIGH",
                "evidence_summary": "SIGINT corroborated by HUMINT",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["attributed_to"] == "Russian Federation"
    assert resp.json()["confidence"] == "HIGH"


def test_get_attribution_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/attribution/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Classification ceiling enforcement
# ---------------------------------------------------------------------------

def test_classification_ceiling_blocks_narrative_write():
    """FOUO user (cls=1) cannot create a SECRET narrative."""
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": str(uuid4()),
        "roles": ["analyst"],
        "perms": ["scenario:read", "scenario:write"],
        "cls": 1,  # FOUO ceiling
    }
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/narratives",
                json={
                    "title": "Secret Narrative",
                    "classification": "SECRET",
                    "platforms": [],
                },
            )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS


# ---------------------------------------------------------------------------
# Engine unit tests
# ---------------------------------------------------------------------------

def test_engine_spread_score_zero_velocity():
    from app.engine.analysis import analyze_narrative as _analyze

    narrative = {
        "id": str(uuid4()),
        "threat_level": "LOW",
        "spread_velocity": 0.0,
        "reach_estimate": 0,
        "platforms": [],
        "counter_narratives": [],
    }
    result = _analyze(narrative)
    assert result.spread_score == 0.0
    assert result.virality_index == 0.0
    assert result.risk_level == "LOW"


def test_engine_critical_narrative_recommendations():
    from app.engine.analysis import analyze_narrative as _analyze

    narrative = {
        "id": str(uuid4()),
        "threat_level": "CRITICAL",
        "spread_velocity": 0.9,
        "reach_estimate": 50_000_000,
        "platforms": ["SOCIAL_MEDIA", "STATE_MEDIA", "NEWS_OUTLET", "VIDEO_PLATFORM"],
        "counter_narratives": [],
    }
    result = _analyze(narrative)
    assert result.risk_level == "CRITICAL"
    assert result.spread_score > 0.5
    assert result.virality_index > 0.0
    # No counter narratives → should recommend developing them
    assert any("counter" in a.lower() for a in result.recommended_actions)
    # High velocity → rapid response team
    assert any("rapid" in a.lower() for a in result.recommended_actions)


def test_engine_counter_effectiveness_full():
    from app.engine.analysis import analyze_narrative as _analyze

    narrative = {
        "id": str(uuid4()),
        "threat_level": "MEDIUM",
        "spread_velocity": 0.3,
        "reach_estimate": 1000,
        "platforms": [],
        "counter_narratives": ["c1", "c2", "c3", "c4", "c5"],
    }
    result = _analyze(narrative)
    assert result.counter_effectiveness == 1.0

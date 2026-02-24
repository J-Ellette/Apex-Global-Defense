"""Tests for intel-svc endpoints and engine logic."""
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
# Entity Extractor — unit tests (no DB)
# ---------------------------------------------------------------------------

def test_extractor_weapon_detection():
    from app.engine.extractor import extract_entities
    text = "The insurgents used an IED device and RPG-7 to attack the convoy."
    entities = extract_entities(text)
    types = {e.type.value for e in entities}
    texts = {e.text.upper() for e in entities}
    assert "WEAPON" in types
    assert any("IED" in t or "RPG" in t for t in texts)


def test_extractor_organization_detection():
    from app.engine.extractor import extract_entities
    text = "ISIS claimed responsibility for the suicide bombing in Mosul."
    entities = extract_entities(text)
    org_entities = [e for e in entities if e.type.value == "ORGANIZATION"]
    assert len(org_entities) > 0
    assert any("ISIS" in e.text.upper() for e in org_entities)


def test_extractor_date_detection():
    from app.engine.extractor import extract_entities
    text = "The attack occurred on January 15, 2024 near the checkpoint."
    entities = extract_entities(text)
    date_entities = [e for e in entities if e.type.value == "DATE"]
    assert len(date_entities) > 0
    assert any("January" in e.text for e in date_entities)


def test_extractor_event_detection():
    from app.engine.extractor import extract_entities
    text = "A bombing and ambush were reported near the forward operating base."
    entities = extract_entities(text)
    event_entities = [e for e in entities if e.type.value == "EVENT"]
    assert len(event_entities) > 0


def test_extractor_dedup():
    from app.engine.extractor import extract_entities
    # Same weapon mentioned twice should be deduplicated
    text = "The IED was constructed with TNT. Another IED was found nearby."
    entities = extract_entities(text)
    weapon_texts = [e.text.upper() for e in entities if e.type.value == "WEAPON"]
    assert weapon_texts.count("IED") == 1


def test_extractor_run_extraction_returns_result():
    from app.engine.extractor import run_extraction
    result = run_extraction("Taliban forces attacked a NATO convoy with RPG-7 weapons.")
    assert result.method == "deterministic"
    assert result.entity_count == len(result.entities)
    assert result.duration_ms >= 0


def test_extractor_empty_text():
    from app.engine.extractor import extract_entities
    entities = extract_entities("")
    assert entities == []


def test_extractor_confidence_bounds():
    from app.engine.extractor import extract_entities
    text = (
        "Al-Qaeda operatives planted IEDs on January 1, 2024 near the embassy "
        "in northern Syria. General Ahmad al-Hassan ordered the operation."
    )
    for entity in extract_entities(text):
        assert 0.0 <= entity.confidence <= 1.0


# ---------------------------------------------------------------------------
# Threat Assessment — unit tests (no DB)
# ---------------------------------------------------------------------------

def test_threat_assess_basic():
    from app.engine.threat import assess_threat
    from app.models import ThreatAssessmentRequest
    req = ThreatAssessmentRequest(
        actor="ISIS",
        target="Baghdad International Airport",
        context="Recent IED attacks and VBIED threats reported near the perimeter.",
    )
    result = assess_threat(req)
    assert result.threat_score >= 0.0
    assert result.threat_score <= 10.0
    assert result.threat_level.value in {"NEGLIGIBLE", "LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert len(result.indicators) > 0
    assert len(result.recommendations) > 0
    assert result.ai_assisted is False


def test_threat_assess_state_actor_baseline():
    from app.engine.threat import assess_threat
    from app.models import ThreatAssessmentRequest
    req = ThreatAssessmentRequest(
        actor="Russia",
        target="NATO eastern flank",
        context="",
    )
    result = assess_threat(req)
    # State actor modifier should push score above 0 even with empty context
    assert result.threat_score > 0.0


def test_threat_assess_terrorist_actor_baseline():
    from app.engine.threat import assess_threat
    from app.models import ThreatAssessmentRequest
    req = ThreatAssessmentRequest(
        actor="Taliban",
        target="Kabul",
        context="",
    )
    result = assess_threat(req)
    assert result.threat_score > 0.0


def test_threat_assess_with_cbrn_context():
    from app.engine.threat import assess_threat
    from app.models import ThreatAssessmentRequest, ThreatVector
    req = ThreatAssessmentRequest(
        actor="Unknown",
        target="City water supply",
        context="CBRN threat detected. Chemical agent suspected in water treatment facility.",
    )
    result = assess_threat(req)
    assert ThreatVector.CBRN in result.threat_vectors


def test_threat_assess_cyber_context():
    from app.engine.threat import assess_threat
    from app.models import ThreatAssessmentRequest, ThreatVector
    req = ThreatAssessmentRequest(
        actor="APT28",
        target="Power grid",
        context="Cyber intrusion detected. Malware found on industrial control systems.",
    )
    result = assess_threat(req)
    assert ThreatVector.CYBER in result.threat_vectors


def test_threat_assess_summary_populated():
    from app.engine.threat import assess_threat
    from app.models import ThreatAssessmentRequest
    req = ThreatAssessmentRequest(
        actor="Hezbollah",
        target="Israeli border region",
        context="Rocket attack reported. Mobilization of forces observed.",
    )
    result = assess_threat(req)
    assert len(result.summary) > 20
    assert req.actor in result.summary
    assert req.target in result.summary


# ---------------------------------------------------------------------------
# OSINT Adapters — unit tests (no network / no DB)
# ---------------------------------------------------------------------------

def test_osint_adapter_registry_populated():
    from app.engine.osint_adapters import _init_registry, list_adapters
    _init_registry()
    adapters = list_adapters()
    assert len(adapters) >= 3
    ids = {a.source_id for a in adapters}
    assert "acled" in ids
    assert "ucdp" in ids
    assert "rss" in ids


@pytest.mark.asyncio
async def test_acled_adapter_synthetic():
    from app.engine.osint_adapters import ACLEDAdapter
    adapter = ACLEDAdapter()  # No API key → synthetic
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    items = []
    async for item in adapter.fetch(since=since, max_items=5):
        items.append(item)
    assert len(items) > 0
    assert all("title" in i for i in items)
    assert all("content" in i for i in items)


@pytest.mark.asyncio
async def test_ucdp_adapter_synthetic():
    """UCDP adapter should return synthetic data when network is unavailable."""
    from app.engine.osint_adapters import UCDPAdapter
    adapter = UCDPAdapter()
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    items = []
    async for item in adapter.fetch(since=since, max_items=5):
        items.append(item)
    # Either live or synthetic; either way must have required fields
    for item in items:
        assert "title" in item
        assert "source_type" in item


@pytest.mark.asyncio
async def test_rss_adapter_synthetic():
    """RSS adapter should return synthetic data when feedparser is unavailable."""
    from app.engine.osint_adapters import RSSAdapter
    adapter = RSSAdapter()
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    items = []
    async for item in adapter.fetch(since=since, max_items=5):
        items.append(item)
    for item in items:
        assert "title" in item
        assert "content" in item


# ---------------------------------------------------------------------------
# Intel CRUD endpoints (mocked DB)
# ---------------------------------------------------------------------------

def test_list_intel_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/intel")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_intel_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/intel/{uuid4()}")
    assert resp.status_code == 404


def test_delete_intel_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 0")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/intel/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Analysis endpoints (mocked DB)
# ---------------------------------------------------------------------------

def test_extract_endpoint_no_item_id():
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/intel/extract",
            json={"text": "ISIS used an IED near the Baghdad checkpoint on January 1, 2024."},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "entities" in data
    assert data["method"] == "deterministic"
    assert data["entity_count"] == len(data["entities"])


def test_extract_endpoint_item_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/intel/extract",
            json={"text": "test", "item_id": str(uuid4())},
        )
    assert resp.status_code == 404


def test_threat_assess_endpoint():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/intel/threat-assess",
            json={
                "actor": "ISIS",
                "target": "Mosul",
                "context": "IED attack and suicide bombing reported.",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "threat_level" in data
    assert "threat_score" in data
    assert data["threat_score"] >= 0
    assert data["ai_assisted"] is False


# ---------------------------------------------------------------------------
# OSINT endpoints (mocked DB)
# ---------------------------------------------------------------------------

def test_list_osint_sources():
    from app.engine.osint_adapters import _init_registry
    _init_registry()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value={"last_run": None, "total_items": 0})
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/intel/osint/sources")
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 3
    source_ids = {s["id"] for s in sources}
    assert "acled" in source_ids
    assert "ucdp" in source_ids


def test_trigger_ingestion_unknown_source():
    fake_db = AsyncMock()
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/intel/osint/ingest",
            json={"source_id": "nonexistent_source", "since_days": 7, "dry_run": True},
        )
    assert resp.status_code == 404

"""Tests for reporting-svc endpoints."""

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
# Template generators (unit tests)
# ---------------------------------------------------------------------------

def test_sitrep_template_generates_content():
    from app.engine.templates import generate_sitrep

    result = generate_sitrep(scenario_name="EXERCISE ALPHA")
    assert "content" in result
    assert "summary" in result
    assert "situation_summary" in result["content"]
    assert "EXERCISE ALPHA" in result["summary"]


def test_intsum_template_generates_content():
    from app.engine.templates import generate_intsum

    result = generate_intsum(scenario_name="EXERCISE BRAVO")
    assert "content" in result
    assert "summary" in result
    content = result["content"]
    assert "threat_level" in content
    assert content["threat_level"] in ("NEGLIGIBLE", "LOW", "MODERATE", "HIGH", "CRITICAL")


def test_conops_template_generates_content():
    from app.engine.templates import generate_conops

    result = generate_conops(scenario_name="EXERCISE CHARLIE")
    assert "content" in result
    assert "summary" in result
    content = result["content"]
    assert "mission_statement" in content
    assert "execution_phases" in content
    assert len(content["execution_phases"]) == 3


def test_intsum_with_assessments_sets_threat_level():
    from app.engine.templates import generate_intsum

    assessments = [{"threat_level": "CRITICAL"}, {"threat_level": "HIGH"}]
    result = generate_intsum(threat_assessments=assessments)
    assert result["content"]["threat_level"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Report list
# ---------------------------------------------------------------------------

def test_list_reports_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/reports")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Get report not found
# ---------------------------------------------------------------------------

def test_get_report_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/reports/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete report not found
# ---------------------------------------------------------------------------

def test_delete_report_not_found():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 0")

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/reports/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Generate report - SITREP
# ---------------------------------------------------------------------------

def test_generate_sitrep():
    report_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    fake_row = {
        "id": report_id,
        "scenario_id": None,
        "run_id": None,
        "report_type": "SITREP",
        "title": "SITREP — TEST — 2026-02-24 1200Z",
        "classification": "UNCLASS",
        "author_id": FAKE_CLAIMS["uid"],
        "status": "DRAFT",
        "content": {"situation_summary": "Test", "significant_events": []},
        "summary": "SITREP for TEST SCENARIO",
        "created_at": now,
        "updated_at": now,
        "approved_by": None,
        "approved_at": None,
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "SITREP"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["report_type"] == "SITREP"
    assert data["status"] == "DRAFT"


def test_generate_intsum():
    report_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    fake_row = {
        "id": report_id,
        "scenario_id": None,
        "run_id": None,
        "report_type": "INTSUM",
        "title": "INTSUM — TEST — 2026-02-24 1200Z",
        "classification": "UNCLASS",
        "author_id": FAKE_CLAIMS["uid"],
        "status": "DRAFT",
        "content": {"threat_level": "MODERATE", "key_developments": []},
        "summary": "INTSUM for TEST SCENARIO",
        "created_at": now,
        "updated_at": now,
        "approved_by": None,
        "approved_at": None,
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "INTSUM"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["report_type"] == "INTSUM"


def test_generate_conops():
    report_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    fake_row = {
        "id": report_id,
        "scenario_id": None,
        "run_id": None,
        "report_type": "CONOPS",
        "title": "CONOPS — TEST — 2026-02-24 1200Z",
        "classification": "UNCLASS",
        "author_id": FAKE_CLAIMS["uid"],
        "status": "DRAFT",
        "content": {"mission_statement": "Test mission", "execution_phases": []},
        "summary": "CONOPS for TEST SCENARIO",
        "created_at": now,
        "updated_at": now,
        "approved_by": None,
        "approved_at": None,
    }

    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=fake_row)

    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/reports/generate",
            json={"report_type": "CONOPS"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["report_type"] == "CONOPS"


# ---------------------------------------------------------------------------
# Classification helpers unit tests
# ---------------------------------------------------------------------------


def test_get_user_classification_default():
    from app.auth import get_user_classification

    user = {"uid": "x", "perms": []}
    assert get_user_classification(user) == "UNCLASS"


def test_get_user_classification_from_int():
    from app.auth import get_user_classification

    assert get_user_classification({"cls": 0}) == "UNCLASS"
    assert get_user_classification({"cls": 1}) == "FOUO"
    assert get_user_classification({"cls": 2}) == "SECRET"
    assert get_user_classification({"cls": 3}) == "TOP_SECRET"
    assert get_user_classification({"cls": 4}) == "TS_SCI"


def test_classification_allowed_levels():
    from app.auth import classification_allowed_levels

    assert classification_allowed_levels("UNCLASS") == ["UNCLASS"]
    assert classification_allowed_levels("SECRET") == ["UNCLASS", "FOUO", "SECRET"]
    assert "TS_SCI" in classification_allowed_levels("TS_SCI")


def test_enforce_classification_ceiling_allows_lower():
    from app.auth import enforce_classification_ceiling

    user = {"cls": 2}  # SECRET
    # Should not raise — SECRET user can see SECRET and below
    enforce_classification_ceiling(user, "UNCLASS")
    enforce_classification_ceiling(user, "FOUO")
    enforce_classification_ceiling(user, "SECRET")


def test_enforce_classification_ceiling_blocks_higher():
    from app.auth import enforce_classification_ceiling
    from fastapi import HTTPException

    user = {"cls": 1}  # FOUO
    import pytest
    with pytest.raises(HTTPException) as exc_info:
        enforce_classification_ceiling(user, "SECRET")
    assert exc_info.value.status_code == 403


def test_generate_report_blocked_by_classification():
    """FOUO user (cls=1) cannot generate a SECRET report."""
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": str(uuid4()),
        "roles": ["analyst"],
        "perms": ["scenario:read", "scenario:write"],
        "org_id": str(uuid4()),
        "cls": 1,  # FOUO ceiling
    }
    try:
        from fastapi.testclient import TestClient
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/reports/generate",
                json={"report_type": "SITREP", "classification": "SECRET"},
            )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS

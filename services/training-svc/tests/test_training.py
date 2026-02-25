"""Tests for training-svc endpoints and scoring engine."""

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
    "roles": ["instructor"],
    "perms": ["scenario:read", "scenario:write"],
    "org_id": str(uuid4()),
    "cls": 4,  # TS_SCI ceiling
}


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass JWT validation for all tests."""
    app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS
    yield
    app.dependency_overrides.clear()


def _now():
    return datetime.now(tz=timezone.utc)


def _fake_exercise(**kwargs):
    now = _now()
    base = {
        "id": uuid4(),
        "name": "Test Exercise",
        "description": "A test exercise",
        "scenario_id": None,
        "instructor_id": "user-1",
        "trainee_ids": json.dumps(["trainee-1", "trainee-2"]),
        "status": "DRAFT",
        "classification": "UNCLASS",
        "planned_start": None,
        "actual_start": None,
        "actual_end": None,
        "learning_objectives": json.dumps(["Objective A", "Objective B"]),
        "created_at": now,
        "updated_at": now,
    }
    base.update(kwargs)
    return base


def _fake_inject(**kwargs):
    now = _now()
    base = {
        "id": uuid4(),
        "exercise_id": uuid4(),
        "inject_type": "UNIT_MOVEMENT",
        "trigger_type": "MANUAL",
        "title": "Move Alpha to Grid 123",
        "description": "Unit movement inject",
        "payload": json.dumps({"grid": "123456", "unit": "Alpha"}),
        "trigger_time_offset_minutes": None,
        "trigger_event": None,
        "trigger_condition": None,
        "status": "PENDING",
        "injected_at": None,
        "acknowledged_by": None,
        "acknowledged_at": None,
        "classification": "UNCLASS",
        "created_at": now,
    }
    base.update(kwargs)
    return base


def _fake_objective(**kwargs):
    now = _now()
    base = {
        "id": uuid4(),
        "exercise_id": uuid4(),
        "objective_type": "DECISION",
        "description": "Make the correct tactical decision",
        "expected_response": "Move forces to high ground",
        "weight": 1.0,
        "status": "PENDING",
        "actual_response": None,
        "score": None,
        "scorer_id": None,
        "scored_at": None,
        "feedback": None,
        "classification": "UNCLASS",
        "created_at": now,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Exercise — list and create
# ---------------------------------------------------------------------------

def test_list_exercises_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/exercises")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_exercises_returns_items():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[_fake_exercise()])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/exercises")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Exercise"
    assert data[0]["status"] == "DRAFT"


def test_create_exercise():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_exercise(status="DRAFT"))
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/exercises",
            json={
                "name": "Operation Dawn - Entry Exercise",
                "instructor_id": "instructor-1",
                "classification": "UNCLASS",
                "trainee_ids": ["t1", "t2"],
                "learning_objectives": ["Complete situational awareness report"],
            },
        )
    assert resp.status_code == 201
    assert resp.json()["status"] == "DRAFT"


def test_get_exercise_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/exercises/{uuid4()}")
    assert resp.status_code == 404


def test_get_exercise_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_exercise())
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/exercises/{uuid4()}")
    assert resp.status_code == 200
    assert resp.json()["instructor_id"] == "user-1"


# ---------------------------------------------------------------------------
# Exercise — status transitions
# ---------------------------------------------------------------------------

def test_start_exercise():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_exercise(status="ACTIVE"))
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/exercises/{uuid4()}/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"


def test_pause_exercise():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_exercise(status="PAUSED"))
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/exercises/{uuid4()}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAUSED"


def test_complete_exercise():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_exercise(status="COMPLETED"))
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/exercises/{uuid4()}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"


def test_start_exercise_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/exercises/{uuid4()}/start")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Injects — CRUD + fire + acknowledge
# ---------------------------------------------------------------------------

def test_list_injects_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/injects")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_inject():
    ex_id = uuid4()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_inject(exercise_id=ex_id))
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/injects",
            json={
                "exercise_id": str(ex_id),
                "inject_type": "UNIT_MOVEMENT",
                "trigger_type": "MANUAL",
                "title": "Move Alpha to Grid 123",
                "classification": "UNCLASS",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["inject_type"] == "UNIT_MOVEMENT"


def test_get_inject_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/injects/{uuid4()}")
    assert resp.status_code == 404


def test_fire_inject():
    now = _now()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(
        return_value=_fake_inject(status="INJECTED", injected_at=now)
    )
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(f"/api/v1/injects/{uuid4()}/fire")
    assert resp.status_code == 200
    assert resp.json()["status"] == "INJECTED"
    assert resp.json()["injected_at"] is not None


def test_acknowledge_inject():
    now = _now()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(
        return_value=_fake_inject(
            status="ACKNOWLEDGED",
            acknowledged_by="trainee-1",
            acknowledged_at=now,
        )
    )
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            f"/api/v1/injects/{uuid4()}/acknowledge",
            params={"acknowledged_by": "trainee-1"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACKNOWLEDGED"
    assert resp.json()["acknowledged_by"] == "trainee-1"


def test_delete_inject():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(return_value="DELETE 1")
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.delete(f"/api/v1/injects/{uuid4()}")
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Objectives — CRUD + scoring
# ---------------------------------------------------------------------------

def test_list_objectives_empty():
    fake_db = AsyncMock()
    fake_db.fetch = AsyncMock(return_value=[])
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get("/api/v1/objectives")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_objective():
    ex_id = uuid4()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=_fake_objective(exercise_id=ex_id))
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            "/api/v1/objectives",
            json={
                "exercise_id": str(ex_id),
                "objective_type": "DECISION",
                "description": "Make the correct tactical decision",
                "weight": 1.0,
            },
        )
    assert resp.status_code == 201
    assert resp.json()["objective_type"] == "DECISION"


def test_score_objective():
    now = _now()
    fake_db = AsyncMock()
    # fetchrow called twice: once to check existing, once after update
    fake_db.fetchrow = AsyncMock(
        side_effect=[
            {"classification": "UNCLASS"},
            _fake_objective(
                status="MET",
                score=95.0,
                scorer_id="instructor-1",
                scored_at=now,
                feedback="Excellent decision under pressure",
            ),
        ]
    )
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.post(
            f"/api/v1/objectives/{uuid4()}/score",
            json={
                "status": "MET",
                "score": 95.0,
                "actual_response": "Moved forces to high ground",
                "feedback": "Excellent decision under pressure",
                "scorer_id": "instructor-1",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "MET"
    assert data["score"] == 95.0
    assert data["scorer_id"] == "instructor-1"


def test_get_objective_not_found():
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(return_value=None)
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/objectives/{uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Exercise score endpoint
# ---------------------------------------------------------------------------

def test_get_exercise_score():
    ex_id = uuid4()
    fake_db = AsyncMock()
    fake_db.fetchrow = AsyncMock(
        return_value={"id": ex_id, "classification": "UNCLASS"}
    )
    fake_db.fetch = AsyncMock(
        side_effect=[
            # objectives
            [
                {"objective_type": "DECISION", "status": "MET", "score": 90.0, "weight": 1.0},
                {"objective_type": "COMMUNICATION", "status": "PARTIALLY_MET", "score": 60.0, "weight": 0.5},
            ],
            # injects
            [],
        ]
    )
    with TestClient(app) as client:
        app.state.db = fake_db
        resp = client.get(f"/api/v1/exercises/{ex_id}/score")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_score" in data
    assert "grade" in data
    assert data["objectives_total"] == 2


# ---------------------------------------------------------------------------
# Classification ceiling enforcement
# ---------------------------------------------------------------------------

def test_classification_ceiling_blocks_write():
    """FOUO user (cls=1) cannot create a SECRET exercise."""
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": str(uuid4()),
        "roles": ["instructor"],
        "perms": ["scenario:read", "scenario:write"],
        "cls": 1,  # FOUO ceiling
    }
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/exercises",
                json={
                    "name": "Secret Exercise",
                    "instructor_id": "user-1",
                    "classification": "SECRET",
                },
            )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: FAKE_CLAIMS


# ---------------------------------------------------------------------------
# Scoring engine unit tests
# ---------------------------------------------------------------------------

def test_scoring_engine_no_objectives():
    from app.engine.scoring import calculate_exercise_score

    result = calculate_exercise_score(exercise_id=uuid4(), objectives=[], injects=[])
    assert result.total_score == 0.0
    assert result.grade == "F"
    assert result.objectives_total == 0


def test_scoring_engine_all_met():
    from app.engine.scoring import calculate_exercise_score

    objectives = [
        {"objective_type": "DECISION", "status": "MET", "score": 100.0, "weight": 1.0},
        {"objective_type": "ACTION", "status": "MET", "score": 90.0, "weight": 1.0},
    ]
    result = calculate_exercise_score(exercise_id=uuid4(), objectives=objectives)
    assert result.total_score == 95.0
    assert result.grade == "A"
    assert result.objectives_met == 2
    assert result.objectives_partial == 0


def test_scoring_engine_mixed_results():
    from app.engine.scoring import calculate_exercise_score

    objectives = [
        {"objective_type": "DECISION", "status": "MET", "score": 100.0, "weight": 1.0},
        {"objective_type": "REPORT", "status": "PARTIALLY_MET", "score": 50.0, "weight": 1.0},
        {"objective_type": "ACTION", "status": "NOT_MET", "score": 0.0, "weight": 1.0},
    ]
    result = calculate_exercise_score(exercise_id=uuid4(), objectives=objectives)
    assert result.objectives_met == 1
    assert result.objectives_partial == 1
    assert result.objectives_not_met == 1
    assert result.total_score == pytest.approx(50.0)
    assert result.grade == "F"


def test_scoring_engine_grade_thresholds():
    from app.engine.scoring import calculate_exercise_score

    for score, expected_grade in [(95.0, "A"), (85.0, "B"), (75.0, "C"), (65.0, "D"), (55.0, "F")]:
        objectives = [
            {"objective_type": "DECISION", "status": "MET", "score": score, "weight": 1.0}
        ]
        result = calculate_exercise_score(exercise_id=uuid4(), objectives=objectives)
        assert result.grade == expected_grade, f"Expected {expected_grade} for score {score}"


def test_scoring_engine_timeliness():
    from app.engine.scoring import calculate_exercise_score
    from datetime import timedelta

    now = _now()
    injects = [
        {
            "trigger_type": "TIME_BASED",
            "injected_at": now,
            "acknowledged_at": now + timedelta(minutes=3),  # within 5 min
        },
        {
            "trigger_type": "TIME_BASED",
            "injected_at": now,
            "acknowledged_at": now + timedelta(minutes=8),  # beyond 5 min
        },
    ]
    result = calculate_exercise_score(exercise_id=uuid4(), objectives=[], injects=injects)
    assert result.timeliness_score == 50.0


def test_scoring_engine_communication_objectives():
    from app.engine.scoring import calculate_exercise_score

    objectives = [
        {"objective_type": "COMMUNICATION", "status": "MET", "score": 100.0, "weight": 1.0},
        {"objective_type": "COMMUNICATION", "status": "PARTIALLY_MET", "score": 40.0, "weight": 1.0},
    ]
    result = calculate_exercise_score(exercise_id=uuid4(), objectives=objectives)
    assert result.communication_score == pytest.approx(70.0)


def test_scoring_engine_weighted_objectives():
    from app.engine.scoring import calculate_exercise_score

    objectives = [
        {"objective_type": "DECISION", "status": "MET", "score": 100.0, "weight": 2.0},
        {"objective_type": "ACTION", "status": "NOT_MET", "score": 0.0, "weight": 1.0},
    ]
    result = calculate_exercise_score(exercise_id=uuid4(), objectives=objectives)
    # weighted: (100*2 + 0*1) / 3 = 66.67
    assert result.total_score == pytest.approx(66.67, abs=0.1)

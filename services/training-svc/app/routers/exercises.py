from __future__ import annotations

"""Exercise CRUD endpoints."""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.engine.scoring import calculate_exercise_score
from app.models import (
    ClassificationLevel,
    CreateExerciseRequest,
    Exercise,
    ExerciseScore,
    ExerciseStatus,
    UpdateExerciseRequest,
)

router = APIRouter(tags=["exercises"])


@router.get("/exercises", response_model=list[Exercise])
async def list_exercises(
    request: Request,
    status_filter: str | None = None,
    instructor_id: str | None = None,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)
    cls_placeholders = ", ".join(f"${j + 1}" for j in range(len(allowed)))
    params: list = list(allowed)
    i = len(allowed) + 1

    conditions = [f"classification IN ({cls_placeholders})"]
    if status_filter:
        conditions.append(f"status = ${i}")
        params.append(status_filter)
        i += 1
    if instructor_id:
        conditions.append(f"instructor_id = ${i}")
        params.append(instructor_id)
        i += 1

    where = " AND ".join(conditions)
    query = f"SELECT * FROM training_exercises WHERE {where} ORDER BY created_at DESC LIMIT 500"
    rows = await db.fetch(query, *params)
    return [_row_to_exercise(r) for r in rows]


@router.post("/exercises", response_model=Exercise, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    request: Request,
    body: CreateExerciseRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO training_exercises (
            name, description, scenario_id, instructor_id, trainee_ids,
            classification, planned_start, learning_objectives
        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8::jsonb)
        RETURNING *
        """,
        body.name,
        body.description,
        body.scenario_id,
        body.instructor_id,
        json.dumps(body.trainee_ids),
        body.classification.value,
        body.planned_start,
        json.dumps(body.learning_objectives),
    )
    return _row_to_exercise(row)


@router.get("/exercises/{exercise_id}", response_model=Exercise)
async def get_exercise(
    exercise_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM training_exercises WHERE id = $1::uuid", exercise_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    ex = _row_to_exercise(row)
    enforce_classification_ceiling(user, ex.classification.value)
    return ex


@router.put("/exercises/{exercise_id}", response_model=Exercise)
async def update_exercise(
    exercise_id: str,
    request: Request,
    body: UpdateExerciseRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM training_exercises WHERE id = $1::uuid", exercise_id
    )
    if existing:
        enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates: list[str] = []
    params: list = []
    i = 1

    if body.name is not None:
        updates.append(f"name = ${i}")
        params.append(body.name)
        i += 1
    if body.description is not None:
        updates.append(f"description = ${i}")
        params.append(body.description)
        i += 1
    if body.scenario_id is not None:
        updates.append(f"scenario_id = ${i}")
        params.append(body.scenario_id)
        i += 1
    if body.trainee_ids is not None:
        updates.append(f"trainee_ids = ${i}::jsonb")
        params.append(json.dumps(body.trainee_ids))
        i += 1
    if body.status is not None:
        updates.append(f"status = ${i}")
        params.append(body.status.value)
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1
    if body.planned_start is not None:
        updates.append(f"planned_start = ${i}")
        params.append(body.planned_start)
        i += 1
    if body.learning_objectives is not None:
        updates.append(f"learning_objectives = ${i}::jsonb")
        params.append(json.dumps(body.learning_objectives))
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM training_exercises WHERE id = $1::uuid", exercise_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return _row_to_exercise(row)

    updates.append("updated_at = NOW()")
    params.append(exercise_id)
    query = (
        f"UPDATE training_exercises SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _row_to_exercise(row)


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM training_exercises WHERE id = $1::uuid", exercise_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Exercise not found")


@router.post("/exercises/{exercise_id}/start", response_model=Exercise)
async def start_exercise(
    exercise_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        """
        UPDATE training_exercises
        SET status = 'ACTIVE', actual_start = NOW(), updated_at = NOW()
        WHERE id = $1::uuid
        RETURNING *
        """,
        exercise_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _row_to_exercise(row)


@router.post("/exercises/{exercise_id}/pause", response_model=Exercise)
async def pause_exercise(
    exercise_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        """
        UPDATE training_exercises
        SET status = 'PAUSED', updated_at = NOW()
        WHERE id = $1::uuid
        RETURNING *
        """,
        exercise_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _row_to_exercise(row)


@router.post("/exercises/{exercise_id}/complete", response_model=Exercise)
async def complete_exercise(
    exercise_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        """
        UPDATE training_exercises
        SET status = 'COMPLETED', actual_end = NOW(), updated_at = NOW()
        WHERE id = $1::uuid
        RETURNING *
        """,
        exercise_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return _row_to_exercise(row)


@router.get("/exercises/{exercise_id}/score", response_model=ExerciseScore)
async def get_exercise_score(
    exercise_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    ex_row = await db.fetchrow(
        "SELECT id, classification FROM training_exercises WHERE id = $1::uuid", exercise_id
    )
    if not ex_row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    enforce_classification_ceiling(user, ex_row["classification"])

    obj_rows = await db.fetch(
        "SELECT objective_type, status, score, weight FROM training_objectives WHERE exercise_id = $1::uuid",
        exercise_id,
    )
    inject_rows = await db.fetch(
        "SELECT trigger_type, injected_at, acknowledged_at FROM training_injects WHERE exercise_id = $1::uuid",
        exercise_id,
    )

    objectives = [dict(r) for r in obj_rows]
    injects = [dict(r) for r in inject_rows]

    return calculate_exercise_score(
        exercise_id=UUID(exercise_id),
        objectives=objectives,
        injects=injects,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_exercise(row) -> Exercise:
    def _parse_json_list(val) -> list:
        if val is None:
            return []
        if isinstance(val, str):
            return json.loads(val)
        return list(val)

    return Exercise(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        scenario_id=row["scenario_id"],
        instructor_id=row["instructor_id"],
        trainee_ids=_parse_json_list(row["trainee_ids"]),
        status=ExerciseStatus(row["status"]),
        classification=ClassificationLevel(row["classification"]),
        planned_start=row["planned_start"],
        actual_start=row["actual_start"],
        actual_end=row["actual_end"],
        learning_objectives=_parse_json_list(row["learning_objectives"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )

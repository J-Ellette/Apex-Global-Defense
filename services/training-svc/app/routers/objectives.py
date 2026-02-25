from __future__ import annotations

"""Objective CRUD and scoring endpoints."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.models import (
    ClassificationLevel,
    CreateObjectiveRequest,
    ExerciseObjective,
    ObjectiveStatus,
    ObjectiveType,
    ScoreObjectiveRequest,
    UpdateObjectiveRequest,
)

router = APIRouter(tags=["objectives"])


@router.get("/objectives", response_model=list[ExerciseObjective])
async def list_objectives(
    request: Request,
    exercise_id: str | None = None,
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
    if exercise_id:
        conditions.append(f"exercise_id = ${i}::uuid")
        params.append(exercise_id)
        i += 1

    where = " AND ".join(conditions)
    query = f"SELECT * FROM training_objectives WHERE {where} ORDER BY created_at ASC LIMIT 1000"
    rows = await db.fetch(query, *params)
    return [_row_to_objective(r) for r in rows]


@router.post("/objectives", response_model=ExerciseObjective, status_code=status.HTTP_201_CREATED)
async def create_objective(
    request: Request,
    body: CreateObjectiveRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO training_objectives (
            exercise_id, objective_type, description, expected_response,
            weight, classification
        ) VALUES ($1::uuid, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        str(body.exercise_id),
        body.objective_type.value,
        body.description,
        body.expected_response,
        body.weight,
        body.classification.value,
    )
    return _row_to_objective(row)


@router.get("/objectives/{objective_id}", response_model=ExerciseObjective)
async def get_objective(
    objective_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM training_objectives WHERE id = $1::uuid", objective_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Objective not found")
    obj = _row_to_objective(row)
    enforce_classification_ceiling(user, obj.classification.value)
    return obj


@router.put("/objectives/{objective_id}", response_model=ExerciseObjective)
async def update_objective(
    objective_id: str,
    request: Request,
    body: UpdateObjectiveRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM training_objectives WHERE id = $1::uuid", objective_id
    )
    if existing:
        enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates: list[str] = []
    params: list = []
    i = 1

    if body.objective_type is not None:
        updates.append(f"objective_type = ${i}")
        params.append(body.objective_type.value)
        i += 1
    if body.description is not None:
        updates.append(f"description = ${i}")
        params.append(body.description)
        i += 1
    if body.expected_response is not None:
        updates.append(f"expected_response = ${i}")
        params.append(body.expected_response)
        i += 1
    if body.weight is not None:
        updates.append(f"weight = ${i}")
        params.append(body.weight)
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM training_objectives WHERE id = $1::uuid", objective_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Objective not found")
        return _row_to_objective(row)

    params.append(objective_id)
    query = (
        f"UPDATE training_objectives SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Objective not found")
    return _row_to_objective(row)


@router.delete("/objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_objective(
    objective_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM training_objectives WHERE id = $1::uuid", objective_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Objective not found")


@router.post("/objectives/{objective_id}/score", response_model=ExerciseObjective)
async def score_objective(
    objective_id: str,
    request: Request,
    body: ScoreObjectiveRequest,
    user: dict = Depends(get_current_user),
):
    """Score an objective: record status, score, response, and scorer."""
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM training_objectives WHERE id = $1::uuid", objective_id
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Objective not found")
    enforce_classification_ceiling(user, existing["classification"])

    row = await db.fetchrow(
        """
        UPDATE training_objectives
        SET status = $2, actual_response = $3, score = $4,
            scorer_id = $5, scored_at = NOW(), feedback = $6
        WHERE id = $1::uuid
        RETURNING *
        """,
        objective_id,
        body.status.value,
        body.actual_response,
        body.score,
        body.scorer_id,
        body.feedback,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Objective not found")
    return _row_to_objective(row)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_objective(row) -> ExerciseObjective:
    score_val = row["score"]
    if score_val is not None:
        score_val = float(score_val)

    return ExerciseObjective(
        id=row["id"],
        exercise_id=row["exercise_id"],
        objective_type=ObjectiveType(row["objective_type"]),
        description=row["description"],
        expected_response=row["expected_response"],
        weight=float(row["weight"]),
        status=ObjectiveStatus(row["status"]),
        actual_response=row["actual_response"],
        score=score_val,
        scorer_id=row["scorer_id"],
        scored_at=row["scored_at"],
        feedback=row["feedback"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
    )

from __future__ import annotations

"""Inject CRUD endpoints."""

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
    CreateInjectRequest,
    ExerciseInject,
    InjectStatus,
    InjectTrigger,
    InjectType,
    UpdateInjectRequest,
)

router = APIRouter(tags=["injects"])


@router.get("/injects", response_model=list[ExerciseInject])
async def list_injects(
    request: Request,
    exercise_id: str | None = None,
    status_filter: str | None = None,
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
    if status_filter:
        conditions.append(f"status = ${i}")
        params.append(status_filter)
        i += 1

    where = " AND ".join(conditions)
    query = f"SELECT * FROM training_injects WHERE {where} ORDER BY created_at ASC LIMIT 1000"
    rows = await db.fetch(query, *params)
    return [_row_to_inject(r) for r in rows]


@router.post("/injects", response_model=ExerciseInject, status_code=status.HTTP_201_CREATED)
async def create_inject(
    request: Request,
    body: CreateInjectRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO training_injects (
            exercise_id, inject_type, trigger_type, title, description,
            payload, trigger_time_offset_minutes, trigger_event,
            trigger_condition, classification
        ) VALUES (
            $1::uuid, $2, $3, $4, $5,
            $6::jsonb, $7, $8, $9, $10
        )
        RETURNING *
        """,
        str(body.exercise_id),
        body.inject_type.value,
        body.trigger_type.value,
        body.title,
        body.description,
        json.dumps(body.payload),
        body.trigger_time_offset_minutes,
        body.trigger_event,
        body.trigger_condition,
        body.classification.value,
    )
    return _row_to_inject(row)


@router.get("/injects/{inject_id}", response_model=ExerciseInject)
async def get_inject(
    inject_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM training_injects WHERE id = $1::uuid", inject_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inject not found")
    inj = _row_to_inject(row)
    enforce_classification_ceiling(user, inj.classification.value)
    return inj


@router.put("/injects/{inject_id}", response_model=ExerciseInject)
async def update_inject(
    inject_id: str,
    request: Request,
    body: UpdateInjectRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM training_injects WHERE id = $1::uuid", inject_id
    )
    if existing:
        enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates: list[str] = []
    params: list = []
    i = 1

    if body.inject_type is not None:
        updates.append(f"inject_type = ${i}")
        params.append(body.inject_type.value)
        i += 1
    if body.trigger_type is not None:
        updates.append(f"trigger_type = ${i}")
        params.append(body.trigger_type.value)
        i += 1
    if body.title is not None:
        updates.append(f"title = ${i}")
        params.append(body.title)
        i += 1
    if body.description is not None:
        updates.append(f"description = ${i}")
        params.append(body.description)
        i += 1
    if body.payload is not None:
        updates.append(f"payload = ${i}::jsonb")
        params.append(json.dumps(body.payload))
        i += 1
    if body.trigger_time_offset_minutes is not None:
        updates.append(f"trigger_time_offset_minutes = ${i}")
        params.append(body.trigger_time_offset_minutes)
        i += 1
    if body.trigger_event is not None:
        updates.append(f"trigger_event = ${i}")
        params.append(body.trigger_event)
        i += 1
    if body.trigger_condition is not None:
        updates.append(f"trigger_condition = ${i}")
        params.append(body.trigger_condition)
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM training_injects WHERE id = $1::uuid", inject_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Inject not found")
        return _row_to_inject(row)

    params.append(inject_id)
    query = (
        f"UPDATE training_injects SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Inject not found")
    return _row_to_inject(row)


@router.delete("/injects/{inject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inject(
    inject_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM training_injects WHERE id = $1::uuid", inject_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Inject not found")


@router.post("/injects/{inject_id}/fire", response_model=ExerciseInject)
async def fire_inject(
    inject_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Manually fire an inject: set status=INJECTED and injected_at=now."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        """
        UPDATE training_injects
        SET status = 'INJECTED', injected_at = NOW()
        WHERE id = $1::uuid
        RETURNING *
        """,
        inject_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inject not found")
    return _row_to_inject(row)


@router.post("/injects/{inject_id}/acknowledge", response_model=ExerciseInject)
async def acknowledge_inject(
    inject_id: str,
    request: Request,
    acknowledged_by: str,
    user: dict = Depends(get_current_user),
):
    """Acknowledge an inject: record who acknowledged and when."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow(
        """
        UPDATE training_injects
        SET status = 'ACKNOWLEDGED', acknowledged_by = $2, acknowledged_at = NOW()
        WHERE id = $1::uuid
        RETURNING *
        """,
        inject_id,
        acknowledged_by,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Inject not found")
    return _row_to_inject(row)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_inject(row) -> ExerciseInject:
    payload = row["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    elif payload is None:
        payload = {}

    return ExerciseInject(
        id=row["id"],
        exercise_id=row["exercise_id"],
        inject_type=InjectType(row["inject_type"]),
        trigger_type=InjectTrigger(row["trigger_type"]),
        title=row["title"],
        description=row["description"],
        payload=payload,
        trigger_time_offset_minutes=row["trigger_time_offset_minutes"],
        trigger_event=row["trigger_event"],
        trigger_condition=row["trigger_condition"],
        status=InjectStatus(row["status"]),
        injected_at=row["injected_at"],
        acknowledged_by=row["acknowledged_by"],
        acknowledged_at=row["acknowledged_at"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
    )

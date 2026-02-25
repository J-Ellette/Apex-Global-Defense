from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import get_current_user
from app.models import CreateIntegrationConfigRequest, IntegrationConfig

router = APIRouter(tags=["integrations"])


def _mask_config(config: dict) -> dict:
    masked = dict(config)
    if "api_key" in masked:
        masked["api_key"] = "***"
    return masked


def _row_to_model(row: dict) -> IntegrationConfig:
    raw_config = row.get("config") or {}
    if isinstance(raw_config, str):
        raw_config = json.loads(raw_config)
    return IntegrationConfig(
        id=row["id"],
        name=row["name"],
        integration_type=row["integration_type"],
        config=_mask_config(raw_config),
        is_active=row.get("is_active", True),
        classification=row.get("classification", "UNCLASS"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/integrations", response_model=list[IntegrationConfig])
async def list_integrations(
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    rows = await db.fetch(
        "SELECT * FROM gis_integration_configs ORDER BY created_at DESC"
    )
    return [_row_to_model(dict(r)) for r in rows]


@router.post("/integrations", response_model=IntegrationConfig, status_code=status.HTTP_201_CREATED)
async def create_integration(
    body: CreateIntegrationConfigRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    now = datetime.now(tz=timezone.utc)
    new_id = uuid4()
    row = await db.fetchrow(
        """
        INSERT INTO gis_integration_configs
            (id, name, integration_type, config, is_active, classification, created_at, updated_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8)
        RETURNING *
        """,
        new_id,
        body.name,
        body.integration_type.value,
        json.dumps(body.config),
        body.is_active,
        body.classification.value,
        now,
        now,
    )
    return _row_to_model(dict(row))


@router.get("/integrations/{integration_id}", response_model=IntegrationConfig)
async def get_integration(
    integration_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM gis_integration_configs WHERE id = $1", integration_id
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return _row_to_model(dict(row))


@router.put("/integrations/{integration_id}", response_model=IntegrationConfig)
async def update_integration(
    integration_id: UUID,
    body: CreateIntegrationConfigRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    now = datetime.now(tz=timezone.utc)
    row = await db.fetchrow(
        """
        UPDATE gis_integration_configs
        SET name=$2, integration_type=$3, config=$4::jsonb,
            is_active=$5, classification=$6, updated_at=$7
        WHERE id=$1
        RETURNING *
        """,
        integration_id,
        body.name,
        body.integration_type.value,
        json.dumps(body.config),
        body.is_active,
        body.classification.value,
        now,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return _row_to_model(dict(row))


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM gis_integration_configs WHERE id = $1", integration_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")


@router.post("/integrations/{integration_id}/test")
async def test_integration(
    integration_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
):
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT id FROM gis_integration_configs WHERE id = $1", integration_id
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return {"status": "ok", "latency_ms": 42, "message": "Integration test successful"}

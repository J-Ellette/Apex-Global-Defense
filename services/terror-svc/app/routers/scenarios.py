from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status

from app.auth import get_current_user, require_permission
from app.data.attack_types import ATTACK_TYPE_CATALOG, ATTACK_TYPE_MAP
from app.models import (
    AttackTypeEntry,
    CreateThreatScenarioRequest,
    ThreatLevel,
    ThreatScenario,
    UpdateThreatScenarioRequest,
)

router = APIRouter(tags=["scenarios"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_scenario(row: dict) -> ThreatScenario:
    return ThreatScenario(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        site_id=row["site_id"],
        attack_type_id=row["attack_type_id"],
        threat_level=ThreatLevel(row.get("threat_level", "LOW")),
        probability=float(row.get("probability", 0.1)),
        estimated_killed_low=int(row.get("estimated_killed_low", 0)),
        estimated_killed_high=int(row.get("estimated_killed_high", 0)),
        estimated_wounded_low=int(row.get("estimated_wounded_low", 0)),
        estimated_wounded_high=int(row.get("estimated_wounded_high", 0)),
        notes=row.get("notes"),
        created_at=row["created_at"],
        created_by=row.get("created_by"),
    )


# ---------------------------------------------------------------------------
# Attack Type Catalog (static)
# ---------------------------------------------------------------------------

@router.get("/terror/attack-types", response_model=list[AttackTypeEntry])
async def list_attack_types(
    category: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List all terror attack types, optionally filtered by category."""
    catalog = ATTACK_TYPE_CATALOG
    if category:
        catalog = [e for e in catalog if e.category.value == category.upper()]
    return catalog


@router.get("/terror/attack-types/{type_id}", response_model=AttackTypeEntry)
async def get_attack_type(
    type_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a specific attack type by ID."""
    entry = ATTACK_TYPE_MAP.get(type_id.upper())
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Attack type '{type_id}' not found")
    return entry


# ---------------------------------------------------------------------------
# Threat Scenario CRUD
# ---------------------------------------------------------------------------

@router.get("/terror/threat-scenarios", response_model=list[ThreatScenario])
async def list_threat_scenarios(
    request: Request,
    scenario_id: UUID | None = Query(default=None),
    site_id: UUID | None = Query(default=None),
    threat_level: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """List threat scenarios, optionally filtered by scenario, site, or threat level."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    filters: list[str] = []
    params: list = []

    if scenario_id:
        params.append(scenario_id)
        filters.append(f"scenario_id = ${len(params)}")
    if site_id:
        params.append(site_id)
        filters.append(f"site_id = ${len(params)}")
    if threat_level:
        params.append(threat_level.upper())
        filters.append(f"threat_level = ${len(params)}")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = await db.fetch(
        f"SELECT * FROM terror_threat_scenarios {where} ORDER BY probability DESC, created_at DESC LIMIT 200",
        *params,
    )
    return [_row_to_scenario(dict(r)) for r in rows]


@router.post(
    "/terror/threat-scenarios",
    response_model=ThreatScenario,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_threat_scenario(
    request: Request,
    body: CreateThreatScenarioRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new threat scenario for a site."""
    require_permission(user, "scenario:write")
    # Validate attack type
    if body.attack_type_id.upper() not in ATTACK_TYPE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown attack type: '{body.attack_type_id}'. "
                   f"Valid IDs: {list(ATTACK_TYPE_MAP.keys())}",
        )
    db = request.app.state.db
    # Validate site exists
    site_row = await db.fetchrow("SELECT id FROM terror_sites WHERE id = $1", body.site_id)
    if site_row is None:
        raise HTTPException(status_code=400, detail=f"Site {body.site_id} not found")

    ts_id = uuid4()
    now = datetime.now(timezone.utc)
    await db.execute(
        """
        INSERT INTO terror_threat_scenarios
          (id, scenario_id, site_id, attack_type_id, threat_level, probability,
           estimated_killed_low, estimated_killed_high, estimated_wounded_low,
           estimated_wounded_high, notes, created_by, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        """,
        ts_id, body.scenario_id, body.site_id, body.attack_type_id.upper(),
        body.threat_level.value, body.probability,
        body.estimated_killed_low, body.estimated_killed_high,
        body.estimated_wounded_low, body.estimated_wounded_high,
        body.notes, user.get("sub") or user.get("uid"), now,
    )
    return ThreatScenario(
        id=ts_id,
        scenario_id=body.scenario_id,
        site_id=body.site_id,
        attack_type_id=body.attack_type_id.upper(),
        threat_level=body.threat_level,
        probability=body.probability,
        estimated_killed_low=body.estimated_killed_low,
        estimated_killed_high=body.estimated_killed_high,
        estimated_wounded_low=body.estimated_wounded_low,
        estimated_wounded_high=body.estimated_wounded_high,
        notes=body.notes,
        created_at=now,
        created_by=user.get("sub") or user.get("uid"),
    )


@router.get("/terror/threat-scenarios/{ts_id}", response_model=ThreatScenario)
async def get_threat_scenario(
    request: Request,
    ts_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Get a single threat scenario by ID."""
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM terror_threat_scenarios WHERE id = $1", ts_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Threat scenario not found")
    return _row_to_scenario(dict(row))


@router.put("/terror/threat-scenarios/{ts_id}", response_model=ThreatScenario)
async def update_threat_scenario(
    request: Request,
    ts_id: UUID,
    body: UpdateThreatScenarioRequest,
    user: dict = Depends(get_current_user),
):
    """Update a threat scenario."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM terror_threat_scenarios WHERE id = $1", ts_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Threat scenario not found")
    current = _row_to_scenario(dict(row))
    updated = current.model_copy(update={k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None})
    if updated.attack_type_id.upper() not in ATTACK_TYPE_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown attack type: '{updated.attack_type_id}'")
    await db.execute(
        """
        UPDATE terror_threat_scenarios SET
          attack_type_id=$2, threat_level=$3, probability=$4,
          estimated_killed_low=$5, estimated_killed_high=$6,
          estimated_wounded_low=$7, estimated_wounded_high=$8, notes=$9
        WHERE id=$1
        """,
        ts_id, updated.attack_type_id.upper(), updated.threat_level.value,
        updated.probability, updated.estimated_killed_low, updated.estimated_killed_high,
        updated.estimated_wounded_low, updated.estimated_wounded_high, updated.notes,
    )
    return updated


@router.delete("/terror/threat-scenarios/{ts_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_threat_scenario(
    request: Request,
    ts_id: UUID,
    user: dict = Depends(get_current_user),
):
    """Delete a threat scenario."""
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute("DELETE FROM terror_threat_scenarios WHERE id = $1", ts_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Threat scenario not found")

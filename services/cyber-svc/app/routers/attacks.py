"""Cyber attacks router — plan, inspect, and simulate cyber operations."""

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import get_current_user, require_permission
from app.data.attack_techniques import TECHNIQUES_BY_ID
from app.models import (
    AttackStatus,
    CreateAttackRequest,
    CyberAttack,
    SimulateAttackRequest,
    SimulateAttackResult,
)

router = APIRouter(tags=["attacks"])

ClaimsDepend = Annotated[dict, Depends(get_current_user)]


def _db(request: Request):
    return request.app.state.db


def _row_to_attack(row: dict) -> CyberAttack:
    result = row.get("result")
    if isinstance(result, str):
        result = json.loads(result)
    return CyberAttack(
        id=row["id"],
        scenario_id=row.get("scenario_id"),
        technique_id=row["technique_id"],
        target_node_id=row.get("target_node_id"),
        attacker=row["attacker"],
        status=AttackStatus(row["status"]),
        success_probability=float(row.get("success_probability", 0.5)),
        impact=row.get("impact", "MEDIUM"),
        notes=row.get("notes"),
        created_at=row["created_at"],
        executed_at=row.get("executed_at"),
        result=result if isinstance(result, dict) else None,
    )


def _compute_success_probability(technique_id: str, target_criticality: str | None) -> float:
    """Estimate base success probability from technique severity and target criticality."""
    technique = TECHNIQUES_BY_ID.get(technique_id)
    severity_base = {
        "LOW": 0.75,
        "MEDIUM": 0.60,
        "HIGH": 0.45,
        "CRITICAL": 0.35,
    }
    base = severity_base.get(technique.severity if technique else "MEDIUM", 0.55)
    # Higher criticality targets often have better defenses
    crit_penalty = {
        "LOW": 0.0,
        "MEDIUM": -0.05,
        "HIGH": -0.10,
        "CRITICAL": -0.20,
    }
    return round(base + crit_penalty.get(target_criticality or "MEDIUM", 0.0), 3)


@router.get("/cyber/attacks", response_model=list[CyberAttack])
async def list_attacks(
    claims: ClaimsDepend,
    request: Request,
    scenario_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
) -> list[CyberAttack]:
    """List cyber attacks, optionally filtered by scenario or status."""
    require_permission(claims, "scenario:read")
    db = _db(request)

    conditions = []
    params: list = []
    if scenario_id:
        params.append(uuid.UUID(scenario_id))
        conditions.append(f"scenario_id = ${len(params)}")
    if status:
        params.append(status.upper())
        conditions.append(f"status = ${len(params)}")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    rows = await db.fetch(
        f"SELECT * FROM cyber_attacks {where} ORDER BY created_at DESC LIMIT ${len(params)}",
        *params,
    )
    return [_row_to_attack(dict(r)) for r in rows]


@router.post("/cyber/attacks", response_model=CyberAttack, status_code=201)
async def create_attack(
    body: CreateAttackRequest,
    claims: ClaimsDepend,
    request: Request,
) -> CyberAttack:
    """Plan a cyber attack against an infrastructure node using an ATT&CK technique."""
    require_permission(claims, "scenario:write")
    db = _db(request)

    # Validate technique exists
    if body.technique_id not in TECHNIQUES_BY_ID:
        raise HTTPException(status_code=400, detail=f"Unknown technique: {body.technique_id}")

    # Optionally validate target node
    target_criticality = None
    if body.target_node_id:
        node_row = await db.fetchrow(
            "SELECT criticality FROM cyber_infra_nodes WHERE id = $1", body.target_node_id
        )
        if not node_row:
            raise HTTPException(status_code=404, detail=f"Target node {body.target_node_id} not found")
        target_criticality = node_row["criticality"]

    attack_id = uuid.uuid4()
    now = datetime.utcnow()
    success_prob = _compute_success_probability(body.technique_id, target_criticality)

    await db.execute(
        """
        INSERT INTO cyber_attacks
            (id, scenario_id, technique_id, target_node_id, attacker, status,
             success_probability, impact, notes, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        attack_id,
        body.scenario_id,
        body.technique_id,
        body.target_node_id,
        body.attacker,
        AttackStatus.PLANNED.value,
        success_prob,
        body.impact,
        body.notes,
        now,
    )
    return CyberAttack(
        id=attack_id,
        scenario_id=body.scenario_id,
        technique_id=body.technique_id,
        target_node_id=body.target_node_id,
        attacker=body.attacker,
        status=AttackStatus.PLANNED,
        success_probability=success_prob,
        impact=body.impact,
        notes=body.notes,
        created_at=now,
    )


@router.get("/cyber/attacks/{attack_id}", response_model=CyberAttack)
async def get_attack(
    attack_id: uuid.UUID,
    claims: ClaimsDepend,
    request: Request,
) -> CyberAttack:
    """Get details of a single cyber attack."""
    require_permission(claims, "scenario:read")
    db = _db(request)
    row = await db.fetchrow("SELECT * FROM cyber_attacks WHERE id = $1", attack_id)
    if not row:
        raise HTTPException(status_code=404, detail="Attack not found")
    return _row_to_attack(dict(row))


@router.post("/cyber/attacks/{attack_id}/simulate", response_model=SimulateAttackResult)
async def simulate_attack(
    attack_id: uuid.UUID,
    body: SimulateAttackRequest,
    claims: ClaimsDepend,
    request: Request,
) -> SimulateAttackResult:
    """Simulate the outcome of a planned cyber attack.

    Applies defender skill and network hardening modifiers to the base
    success probability.  Result is persisted on the attack record.
    """
    require_permission(claims, "simulation:run")
    db = _db(request)
    row = await db.fetchrow("SELECT * FROM cyber_attacks WHERE id = $1", attack_id)
    if not row:
        raise HTTPException(status_code=404, detail="Attack not found")

    attack = _row_to_attack(dict(row))
    if attack.status not in (AttackStatus.PLANNED, AttackStatus.FAILED):
        raise HTTPException(
            status_code=400,
            detail=f"Can only simulate attacks in PLANNED or FAILED status (current: {attack.status})",
        )

    technique = TECHNIQUES_BY_ID.get(attack.technique_id)
    rng = random.Random(attack_id.int % (2 ** 31))

    # Adjusted probability accounts for defender posture
    defense_factor = (body.defender_skill * 0.4 + body.network_hardening * 0.6)
    adjusted_prob = max(0.05, min(0.95, attack.success_probability - defense_factor * 0.4))

    success = rng.random() < adjusted_prob
    # Detection is more likely if the attack fails or technique is high-severity
    detect_base = 0.3 if success else 0.65
    if technique and technique.severity in ("HIGH", "CRITICAL"):
        detect_base += 0.15
    detected = rng.random() < min(0.95, detect_base + body.defender_skill * 0.2)

    # Time-to-detect (only meaningful if detected)
    ttd = int(rng.uniform(5, 480)) if detected else None

    # Damage level
    if not success:
        damage = "NONE"
    elif technique and technique.severity == "CRITICAL":
        damage = "CATASTROPHIC" if rng.random() < 0.4 else "SEVERE"
    elif technique and technique.severity == "HIGH":
        damage = "SEVERE" if rng.random() < 0.5 else "MODERATE"
    else:
        damage = "MODERATE" if rng.random() < 0.5 else "MINIMAL"

    # Possibly spread to adjacent nodes
    affected: list[uuid.UUID] = []
    if success and attack.target_node_id:
        affected.append(attack.target_node_id)
        if rng.random() < 0.35:
            edge_rows = await db.fetch(
                """
                SELECT target_id AS node_id FROM cyber_infra_edges WHERE source_id = $1
                UNION
                SELECT source_id AS node_id FROM cyber_infra_edges WHERE target_id = $1
                LIMIT 5
                """,
                attack.target_node_id,
            )
            affected += [r["node_id"] for r in edge_rows if rng.random() < 0.4]

    persistence = success and technique is not None and technique.tactic.value in (
        "persistence", "privilege_escalation", "lateral_movement"
    ) and rng.random() < 0.6

    # Build narrative
    tech_name = technique.name if technique else attack.technique_id
    target_label = "(unknown target)"
    if attack.target_node_id:
        node_row = await db.fetchrow(
            "SELECT label FROM cyber_infra_nodes WHERE id = $1", attack.target_node_id
        )
        if node_row:
            target_label = node_row["label"]

    if success:
        narrative = (
            f"Attack using {tech_name} against {target_label} SUCCEEDED. "
            f"Damage assessed as {damage}. "
            f"{'Threat actor established persistence. ' if persistence else ''}"
            f"{'Attack was detected after ' + str(ttd) + ' minutes.' if detected else 'Attack went undetected.'}"
        )
    else:
        narrative = (
            f"Attack using {tech_name} against {target_label} FAILED. "
            f"{'Defender detected the attempt after ' + str(ttd) + ' minutes.' if detected else 'Attempt was not detected.'}"
        )

    new_status = AttackStatus.DETECTED if detected else (AttackStatus.COMPLETE if success else AttackStatus.FAILED)
    result_payload = {
        "success": success,
        "detected": detected,
        "damage_level": damage,
        "affected_nodes": [str(n) for n in affected],
        "narrative": narrative,
        "ttd_minutes": ttd,
        "persistence_achieved": persistence,
        "adjusted_probability": round(adjusted_prob, 3),
    }

    await db.execute(
        """
        UPDATE cyber_attacks
        SET status=$2, executed_at=$3, result=$4::jsonb
        WHERE id=$1
        """,
        attack_id,
        new_status.value,
        datetime.utcnow(),
        json.dumps(result_payload),
    )

    return SimulateAttackResult(
        attack_id=attack_id,
        success=success,
        detected=detected,
        damage_level=damage,
        affected_nodes=affected,
        narrative=narrative,
        ttd_minutes=ttd,
        persistence_achieved=persistence,
    )

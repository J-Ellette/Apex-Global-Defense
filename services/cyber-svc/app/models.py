from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# MITRE ATT&CK
# ---------------------------------------------------------------------------

class ATTACKTactic(str, Enum):
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class ATTACKTechnique(BaseModel):
    id: str            # e.g. "T1566"
    name: str
    tactic: ATTACKTactic
    description: str
    platforms: list[str]
    severity: str      # LOW / MEDIUM / HIGH / CRITICAL
    mitigations: list[str]
    url: str


# ---------------------------------------------------------------------------
# Infrastructure Graph
# ---------------------------------------------------------------------------

class NodeType(str, Enum):
    HOST = "HOST"
    SERVER = "SERVER"
    ROUTER = "ROUTER"
    FIREWALL = "FIREWALL"
    ICS = "ICS"
    CLOUD = "CLOUD"
    SATELLITE = "SATELLITE"
    IOT = "IOT"
    DATABASE = "DATABASE"


class Criticality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InfraNode(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    label: str
    node_type: NodeType
    network: str | None = None
    ip_address: str | None = None
    criticality: Criticality = Criticality.MEDIUM
    classification: str = "UNCLASS"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CreateInfraNodeRequest(BaseModel):
    scenario_id: UUID | None = None
    label: str
    node_type: NodeType
    network: str | None = None
    ip_address: str | None = None
    criticality: Criticality = Criticality.MEDIUM
    classification: str = "UNCLASS"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateInfraNodeRequest(BaseModel):
    label: str | None = None
    node_type: NodeType | None = None
    network: str | None = None
    ip_address: str | None = None
    criticality: Criticality | None = None
    classification: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class InfraEdge(BaseModel):
    id: UUID
    source_id: UUID
    target_id: UUID
    edge_type: str = "NETWORK"
    protocol: str | None = None
    port: int | None = None
    created_at: datetime


class CreateInfraEdgeRequest(BaseModel):
    source_id: UUID
    target_id: UUID
    edge_type: str = "NETWORK"
    protocol: str | None = None
    port: int | None = None


class InfraGraph(BaseModel):
    nodes: list[InfraNode]
    edges: list[InfraEdge]


# ---------------------------------------------------------------------------
# Cyber Attacks
# ---------------------------------------------------------------------------

class AttackStatus(str, Enum):
    PLANNED = "PLANNED"
    EXECUTING = "EXECUTING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    DETECTED = "DETECTED"


class CyberAttack(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    technique_id: str
    target_node_id: UUID | None = None
    attacker: str
    status: AttackStatus = AttackStatus.PLANNED
    success_probability: float = Field(ge=0.0, le=1.0)
    impact: str = "MEDIUM"
    notes: str | None = None
    created_at: datetime
    executed_at: datetime | None = None
    result: dict[str, Any] | None = None


class CreateAttackRequest(BaseModel):
    scenario_id: UUID | None = None
    technique_id: str
    target_node_id: UUID | None = None
    attacker: str
    impact: str = "MEDIUM"
    notes: str | None = None


class SimulateAttackRequest(BaseModel):
    defender_skill: float = Field(default=0.5, ge=0.0, le=1.0)
    network_hardening: float = Field(default=0.5, ge=0.0, le=1.0)


class SimulateAttackResult(BaseModel):
    attack_id: UUID
    success: bool
    detected: bool
    damage_level: str          # NONE / MINIMAL / MODERATE / SEVERE / CATASTROPHIC
    affected_nodes: list[UUID]
    narrative: str
    ttd_minutes: int | None    # time-to-detect (None if undetected)
    persistence_achieved: bool

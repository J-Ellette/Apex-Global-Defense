from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ReportType(str, Enum):
    SITREP = "SITREP"
    INTSUM = "INTSUM"
    CONOPS = "CONOPS"


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"
    APPROVED = "APPROVED"


class ClassificationLevel(str, Enum):
    UNCLASS = "UNCLASS"
    FOUO = "FOUO"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
    TS_SCI = "TS_SCI"


# ---------------------------------------------------------------------------
# Report models
# ---------------------------------------------------------------------------

class Report(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    run_id: UUID | None = None
    report_type: ReportType
    title: str
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    author_id: str | None = None
    status: ReportStatus = ReportStatus.DRAFT
    content: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None


class GenerateReportRequest(BaseModel):
    report_type: ReportType
    title: str | None = None
    scenario_id: UUID | None = None
    run_id: UUID | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    # Optional free-text context for AI or template fill
    context: str | None = None


class UpdateReportRequest(BaseModel):
    title: str | None = None
    status: ReportStatus | None = None
    classification: ClassificationLevel | None = None
    content: dict[str, Any] | None = None
    summary: str | None = None


class ApproveReportRequest(BaseModel):
    approved_by: str


# ---------------------------------------------------------------------------
# Structured report content schemas
# ---------------------------------------------------------------------------

class SITREPContent(BaseModel):
    """SITREP — Situation Report content structure (NATO format)."""
    period_from: str = ""
    period_to: str = ""
    situation_summary: str = ""
    friendly_forces: str = ""
    enemy_forces: str = ""
    civilian_situation: str = ""
    significant_events: list[str] = Field(default_factory=list)
    current_operations: str = ""
    planned_operations: str = ""
    logistics_status: str = ""
    weather: str = ""
    commander_assessment: str = ""
    next_report_due: str = ""


class INTSUMContent(BaseModel):
    """INTSUM — Intelligence Summary content structure."""
    period_from: str = ""
    period_to: str = ""
    enemy_disposition: str = ""
    enemy_strength: str = ""
    enemy_capabilities: str = ""
    enemy_intentions: str = ""
    threat_level: str = "MODERATE"
    key_developments: list[str] = Field(default_factory=list)
    isr_gaps: list[str] = Field(default_factory=list)
    cyber_threats: str = ""
    cbrn_threats: str = ""
    threat_indicators: list[dict[str, str]] = Field(default_factory=list)
    analyst_assessment: str = ""
    confidence_level: str = "MEDIUM"


class CONOPSContent(BaseModel):
    """CONOPS — Concept of Operations content structure."""
    mission_statement: str = ""
    commander_intent: str = ""
    end_state: str = ""
    scheme_of_maneuver: str = ""
    tasks_to_subordinate_units: list[dict[str, str]] = Field(default_factory=list)
    tasks_to_supporting_elements: list[dict[str, str]] = Field(default_factory=list)
    coordinating_instructions: list[str] = Field(default_factory=list)
    sustainment_concept: str = ""
    command_and_signal: str = ""
    risk_assessment: str = ""
    execution_phases: list[dict[str, str]] = Field(default_factory=list)

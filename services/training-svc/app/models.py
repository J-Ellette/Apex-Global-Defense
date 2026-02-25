from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ClassificationLevel(str, Enum):
    UNCLASS = "UNCLASS"
    FOUO = "FOUO"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
    TS_SCI = "TS_SCI"


class ExerciseStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InjectType(str, Enum):
    UNIT_MOVEMENT = "UNIT_MOVEMENT"
    INTEL_REPORT = "INTEL_REPORT"
    COMMS_DEGRADATION = "COMMS_DEGRADATION"
    ENEMY_ATTACK = "ENEMY_ATTACK"
    FRIENDLY_CASUALTIES = "FRIENDLY_CASUALTIES"
    CBRN_ALERT = "CBRN_ALERT"
    CYBER_ATTACK = "CYBER_ATTACK"
    CIVILIAN_INCIDENT = "CIVILIAN_INCIDENT"
    LOGISTICS_FAILURE = "LOGISTICS_FAILURE"
    WEATHER_CHANGE = "WEATHER_CHANGE"
    COMMAND_MESSAGE = "COMMAND_MESSAGE"
    CUSTOM = "CUSTOM"


class InjectTrigger(str, Enum):
    TIME_BASED = "TIME_BASED"
    EVENT_BASED = "EVENT_BASED"
    MANUAL = "MANUAL"
    CONDITION_BASED = "CONDITION_BASED"


class InjectStatus(str, Enum):
    PENDING = "PENDING"
    INJECTED = "INJECTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    EXPIRED = "EXPIRED"


class ObjectiveType(str, Enum):
    DECISION = "DECISION"
    REPORT = "REPORT"
    ACTION = "ACTION"
    COMMUNICATION = "COMMUNICATION"
    ASSESSMENT = "ASSESSMENT"


class ObjectiveStatus(str, Enum):
    PENDING = "PENDING"
    MET = "MET"
    PARTIALLY_MET = "PARTIALLY_MET"
    NOT_MET = "NOT_MET"
    SKIPPED = "SKIPPED"


# ---------------------------------------------------------------------------
# Exercise models
# ---------------------------------------------------------------------------

class Exercise(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    scenario_id: UUID | None = None
    instructor_id: str
    trainee_ids: list[str] = Field(default_factory=list)
    status: ExerciseStatus
    classification: ClassificationLevel
    planned_start: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CreateExerciseRequest(BaseModel):
    name: str
    description: str | None = None
    scenario_id: UUID | None = None
    instructor_id: str
    trainee_ids: list[str] = Field(default_factory=list)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    planned_start: datetime | None = None
    learning_objectives: list[str] = Field(default_factory=list)


class UpdateExerciseRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    scenario_id: UUID | None = None
    trainee_ids: list[str] | None = None
    status: ExerciseStatus | None = None
    classification: ClassificationLevel | None = None
    planned_start: datetime | None = None
    learning_objectives: list[str] | None = None


# ---------------------------------------------------------------------------
# Inject models
# ---------------------------------------------------------------------------

class ExerciseInject(BaseModel):
    id: UUID
    exercise_id: UUID
    inject_type: InjectType
    trigger_type: InjectTrigger
    title: str
    description: str | None = None
    payload: dict = Field(default_factory=dict)
    trigger_time_offset_minutes: int | None = None
    trigger_event: str | None = None
    trigger_condition: str | None = None
    status: InjectStatus
    injected_at: datetime | None = None
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    classification: ClassificationLevel
    created_at: datetime


class CreateInjectRequest(BaseModel):
    exercise_id: UUID
    inject_type: InjectType
    trigger_type: InjectTrigger
    title: str
    description: str | None = None
    payload: dict = Field(default_factory=dict)
    trigger_time_offset_minutes: int | None = None
    trigger_event: str | None = None
    trigger_condition: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class UpdateInjectRequest(BaseModel):
    inject_type: InjectType | None = None
    trigger_type: InjectTrigger | None = None
    title: str | None = None
    description: str | None = None
    payload: dict | None = None
    trigger_time_offset_minutes: int | None = None
    trigger_event: str | None = None
    trigger_condition: str | None = None
    classification: ClassificationLevel | None = None


# ---------------------------------------------------------------------------
# Objective models
# ---------------------------------------------------------------------------

class ExerciseObjective(BaseModel):
    id: UUID
    exercise_id: UUID
    objective_type: ObjectiveType
    description: str
    expected_response: str | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="scoring weight")
    status: ObjectiveStatus
    actual_response: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    scorer_id: str | None = None
    scored_at: datetime | None = None
    feedback: str | None = None
    classification: ClassificationLevel
    created_at: datetime


class CreateObjectiveRequest(BaseModel):
    exercise_id: UUID
    objective_type: ObjectiveType
    description: str
    expected_response: str | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class UpdateObjectiveRequest(BaseModel):
    objective_type: ObjectiveType | None = None
    description: str | None = None
    expected_response: str | None = None
    weight: float | None = Field(default=None, ge=0.0, le=1.0)
    classification: ClassificationLevel | None = None


class ScoreObjectiveRequest(BaseModel):
    status: ObjectiveStatus
    actual_response: str | None = None
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    feedback: str | None = None
    scorer_id: str


# ---------------------------------------------------------------------------
# Exercise Score model
# ---------------------------------------------------------------------------

class ExerciseScore(BaseModel):
    exercise_id: UUID
    total_score: float = Field(ge=0.0, le=100.0)
    objectives_met: int
    objectives_partial: int
    objectives_not_met: int
    objectives_total: int
    completion_pct: float
    timeliness_score: float
    accuracy_score: float
    communication_score: float
    grade: str  # A / B / C / D / F
    instructor_notes: str | None = None
    scored_at: datetime | None = None

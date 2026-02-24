from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SimMode(str, Enum):
    REAL_TIME = "real_time"
    TURN_BASED = "turn_based"
    MONTE_CARLO = "monte_carlo"


class SimStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    ERROR = "error"


class ScenarioConfig(BaseModel):
    mode: SimMode
    blue_force_ids: list[UUID] = Field(default_factory=list)
    red_force_ids: list[UUID] = Field(default_factory=list)
    theater_bounds: dict[str, Any] | None = None  # GeoJSON polygon
    start_time: datetime = Field(default_factory=datetime.utcnow)
    duration_hours: int = Field(default=24, ge=1, le=8760)
    monte_carlo_runs: int = Field(default=1000, ge=10, le=10000)
    weather_preset: str = "clear"
    fog_of_war: bool = True
    terrain_effects: bool = True


class StartRunRequest(BaseModel):
    config: ScenarioConfig


class SimulationRun(BaseModel):
    id: UUID
    scenario_id: UUID
    mode: SimMode
    status: SimStatus
    progress: float = Field(ge=0.0, le=1.0)
    config: dict[str, Any]
    created_by: UUID
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class EventType(str, Enum):
    UNIT_MOVE = "UNIT_MOVE"
    ENGAGEMENT = "ENGAGEMENT"
    CASUALTY = "CASUALTY"
    SUPPLY_CONSUMED = "SUPPLY_CONSUMED"
    RESUPPLY = "RESUPPLY"
    OBJECTIVE_CAPTURED = "OBJECTIVE_CAPTURED"
    AIRSTRIKE = "AIRSTRIKE"
    NAVAL_ACTION = "NAVAL_ACTION"
    CYBER_ATTACK = "CYBER_ATTACK"
    CBRN_RELEASE = "CBRN_RELEASE"
    PHASE_CHANGE = "PHASE_CHANGE"


class SimEvent(BaseModel):
    time: datetime
    run_id: UUID
    event_type: EventType
    entity_id: UUID | None = None
    location: dict[str, float] | None = None  # {lat, lng}
    payload: dict[str, Any] = Field(default_factory=dict)
    turn_number: int | None = None


class OutcomeDistribution(BaseModel):
    blue_win_pct: float
    red_win_pct: float
    contested_pct: float
    mean_duration_hours: float
    std_duration_hours: float


class CasualtyDistribution(BaseModel):
    mean: int
    std: int
    p10: int
    p50: int
    p90: int


class MCResult(BaseModel):
    runs_completed: int
    objective_outcomes: dict[str, OutcomeDistribution]
    blue_casualties: CasualtyDistribution
    red_casualties: CasualtyDistribution
    duration_distribution: list[float]


class AfterActionReport(BaseModel):
    run_id: UUID
    scenario_id: UUID
    generated_at: datetime
    executive_summary: str
    duration_hours: float
    total_turns: int | None
    blue_objectives_captured: int
    red_objectives_captured: int
    blue_casualties: int
    red_casualties: int
    key_events: list[SimEvent]
    mc_result: MCResult | None = None
    logistics_summary: "LogisticsSummary | None" = None


class SimState(BaseModel):
    run_id: UUID
    status: SimStatus
    progress: float
    turn_number: int
    sim_time: datetime
    blue_unit_count: int
    red_unit_count: int
    objectives_status: dict[str, str]  # objective_id → BLUE/RED/CONTESTED


# ---------------------------------------------------------------------------
# Logistics & Attrition models
# ---------------------------------------------------------------------------

class SupplyLevels(BaseModel):
    ammo: float = Field(ge=0.0, le=1.0)     # fraction remaining (0=empty, 1=full)
    fuel: float = Field(ge=0.0, le=1.0)
    rations: float = Field(ge=0.0, le=1.0)


class ForceSummary(BaseModel):
    strength_pct: float = Field(ge=0.0, le=1.0)   # current / initial strength
    kia: int
    wia: int
    supply: SupplyLevels
    equipment_losses: dict[str, int]   # category → count (armor, artillery, aircraft)


class LogisticsState(BaseModel):
    run_id: UUID
    turn_number: int
    sim_time: datetime
    blue: ForceSummary
    red: ForceSummary


class LogisticsSummary(BaseModel):
    blue_final_strength_pct: float
    red_final_strength_pct: float
    blue_total_kia: int
    red_total_kia: int
    blue_supply: SupplyLevels
    red_supply: SupplyLevels
    blue_equipment_losses: dict[str, int]
    red_equipment_losses: dict[str, int]

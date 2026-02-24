from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DensityClass(str, Enum):
    URBAN = "URBAN"
    SUBURBAN = "SUBURBAN"
    RURAL = "RURAL"
    SPARSE = "SPARSE"


class CorridorStatus(str, Enum):
    OPEN = "OPEN"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"


class DisplacementStatus(str, Enum):
    PROJECTED = "PROJECTED"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"


# Population Zone
class PopulationZone(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    name: str
    country_code: str
    latitude: float
    longitude: float
    radius_km: float
    population: int
    density_class: DensityClass
    created_at: datetime


class CreatePopulationZoneRequest(BaseModel):
    scenario_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    country_code: str = Field(min_length=2, max_length=3)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    radius_km: float = Field(gt=0.0, le=500.0)
    population: int = Field(gt=0)
    density_class: DensityClass = DensityClass.URBAN


# Civilian Impact Assessment
class ZoneImpact(BaseModel):
    zone_id: UUID
    zone_name: str
    civilian_casualties: int
    civilian_wounded: int
    displaced_persons: int
    infrastructure_damage_pct: float = Field(ge=0.0, le=1.0)
    impact_score: float = Field(ge=0.0, le=10.0)


class ImpactAssessment(BaseModel):
    id: UUID
    run_id: UUID
    scenario_id: UUID | None = None
    assessed_at: datetime
    total_civilian_casualties: int
    total_civilian_wounded: int
    total_displaced_persons: int
    zone_impacts: list[ZoneImpact]
    methodology: str = "deterministic"
    notes: str | None = None


class AssessImpactRequest(BaseModel):
    run_id: UUID
    scenario_id: UUID | None = None
    # Optional: caller can pass sim events directly; else service fetches from DB
    events: list[dict[str, Any]] | None = None


# Refugee Flow
class RefugeeFlow(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    origin_zone_id: UUID | None = None
    origin_name: str
    destination_name: str
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    displaced_persons: int
    status: DisplacementStatus
    started_at: datetime
    updated_at: datetime


class CreateRefugeeFlowRequest(BaseModel):
    scenario_id: UUID | None = None
    origin_zone_id: UUID | None = None
    origin_name: str = Field(min_length=1, max_length=200)
    destination_name: str = Field(min_length=1, max_length=200)
    origin_lat: float = Field(ge=-90.0, le=90.0)
    origin_lon: float = Field(ge=-180.0, le=180.0)
    destination_lat: float = Field(ge=-90.0, le=90.0)
    destination_lon: float = Field(ge=-180.0, le=180.0)
    displaced_persons: int = Field(gt=0)
    status: DisplacementStatus = DisplacementStatus.PROJECTED


class UpdateRefugeeFlowRequest(BaseModel):
    displaced_persons: int | None = Field(default=None, gt=0)
    status: DisplacementStatus | None = None
    destination_name: str | None = Field(default=None, min_length=1, max_length=200)


# Humanitarian Corridor
class HumanitarianCorridor(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    name: str
    waypoints: list[dict[str, float]]  # list of {lat, lon}
    status: CorridorStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateCorridorRequest(BaseModel):
    scenario_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    waypoints: list[dict[str, float]] = Field(min_length=2)
    status: CorridorStatus = CorridorStatus.OPEN
    notes: str | None = None


class UpdateCorridorRequest(BaseModel):
    status: CorridorStatus | None = None
    notes: str | None = None

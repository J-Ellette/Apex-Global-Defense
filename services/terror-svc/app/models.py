from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Attack Type Catalog
# ---------------------------------------------------------------------------

class AttackCategory(str, Enum):
    KINETIC = "KINETIC"
    EXPLOSIVE = "EXPLOSIVE"
    CHEMICAL_BIO = "CHEMICAL_BIO"
    CYBER = "CYBER"
    HYBRID = "HYBRID"


class AttackTypeEntry(BaseModel):
    id: str
    category: AttackCategory
    label: str
    description: str
    typical_perpetrators: list[str]
    typical_targets: list[str]
    avg_killed_low: int
    avg_killed_high: int
    avg_wounded_low: int
    avg_wounded_high: int
    detection_window: str            # pre-attack detection timeframe description
    countermeasures: list[str]
    threat_indicator: str
    color_hex: str = "#DC2626"


# ---------------------------------------------------------------------------
# Terror Site (vulnerability assessment target)
# ---------------------------------------------------------------------------

class SiteType(str, Enum):
    TRANSPORT_HUB = "TRANSPORT_HUB"
    STADIUM = "STADIUM"
    GOVERNMENT_BUILDING = "GOVERNMENT_BUILDING"
    HOTEL = "HOTEL"
    MARKET = "MARKET"
    HOUSE_OF_WORSHIP = "HOUSE_OF_WORSHIP"
    SCHOOL = "SCHOOL"
    HOSPITAL = "HOSPITAL"
    EMBASSY = "EMBASSY"
    CRITICAL_INFRASTRUCTURE = "CRITICAL_INFRASTRUCTURE"
    FINANCIAL_CENTER = "FINANCIAL_CENTER"
    MILITARY_BASE = "MILITARY_BASE"
    ENTERTAINMENT_VENUE = "ENTERTAINMENT_VENUE"
    SHOPPING_CENTER = "SHOPPING_CENTER"


class CrowdDensity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SiteStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    HARDENED = "HARDENED"
    CLOSED = "CLOSED"


class TerrorSite(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    name: str
    site_type: SiteType
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    country_code: str | None = None
    population_capacity: int = 0
    # Vulnerability dimensions (0.0–1.0, where 1.0 = excellent security)
    physical_security: float = Field(default=0.5, ge=0.0, le=1.0)
    access_control: float = Field(default=0.5, ge=0.0, le=1.0)
    surveillance: float = Field(default=0.5, ge=0.0, le=1.0)
    emergency_response: float = Field(default=0.5, ge=0.0, le=1.0)
    crowd_density: CrowdDensity = CrowdDensity.MEDIUM
    # Computed (stored for query performance)
    vulnerability_score: float = Field(default=5.0, description="Composite vulnerability score (1–10). Higher = more vulnerable.")
    assigned_agencies: list[str] = Field(default_factory=list)
    notes: str | None = None
    status: SiteStatus = SiteStatus.ACTIVE
    created_at: datetime
    created_by: str | None = None


class CreateSiteRequest(BaseModel):
    scenario_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    site_type: SiteType
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    country_code: str | None = None
    population_capacity: int = Field(default=0, ge=0)
    physical_security: float = Field(default=0.5, ge=0.0, le=1.0)
    access_control: float = Field(default=0.5, ge=0.0, le=1.0)
    surveillance: float = Field(default=0.5, ge=0.0, le=1.0)
    emergency_response: float = Field(default=0.5, ge=0.0, le=1.0)
    crowd_density: CrowdDensity = CrowdDensity.MEDIUM
    assigned_agencies: list[str] = Field(default_factory=list)
    notes: str | None = None
    status: SiteStatus = SiteStatus.ACTIVE


class UpdateSiteRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    site_type: SiteType | None = None
    address: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    country_code: str | None = None
    population_capacity: int | None = Field(default=None, ge=0)
    physical_security: float | None = Field(default=None, ge=0.0, le=1.0)
    access_control: float | None = Field(default=None, ge=0.0, le=1.0)
    surveillance: float | None = Field(default=None, ge=0.0, le=1.0)
    emergency_response: float | None = Field(default=None, ge=0.0, le=1.0)
    crowd_density: CrowdDensity | None = None
    assigned_agencies: list[str] | None = None
    notes: str | None = None
    status: SiteStatus | None = None


# ---------------------------------------------------------------------------
# Threat Scenario
# ---------------------------------------------------------------------------

class ThreatLevel(str, Enum):
    LOW = "LOW"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    IMMINENT = "IMMINENT"


class ThreatScenario(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    site_id: UUID
    attack_type_id: str
    threat_level: ThreatLevel = ThreatLevel.LOW
    probability: float = Field(default=0.1, ge=0.0, le=1.0)
    estimated_killed_low: int = Field(default=0, ge=0)
    estimated_killed_high: int = Field(default=0, ge=0)
    estimated_wounded_low: int = Field(default=0, ge=0)
    estimated_wounded_high: int = Field(default=0, ge=0)
    notes: str | None = None
    created_at: datetime
    created_by: str | None = None


class CreateThreatScenarioRequest(BaseModel):
    scenario_id: UUID | None = None
    site_id: UUID
    attack_type_id: str
    threat_level: ThreatLevel = ThreatLevel.LOW
    probability: float = Field(default=0.1, ge=0.0, le=1.0)
    estimated_killed_low: int = Field(default=0, ge=0)
    estimated_killed_high: int = Field(default=0, ge=0)
    estimated_wounded_low: int = Field(default=0, ge=0)
    estimated_wounded_high: int = Field(default=0, ge=0)
    notes: str | None = None


class UpdateThreatScenarioRequest(BaseModel):
    attack_type_id: str | None = None
    threat_level: ThreatLevel | None = None
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    estimated_killed_low: int | None = Field(default=None, ge=0)
    estimated_killed_high: int | None = Field(default=None, ge=0)
    estimated_wounded_low: int | None = Field(default=None, ge=0)
    estimated_wounded_high: int | None = Field(default=None, ge=0)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Response Plan (multi-agency coordination)
# ---------------------------------------------------------------------------

class AgencyType(str, Enum):
    POLICE = "POLICE"
    FIRE = "FIRE"
    MEDICAL = "MEDICAL"
    MILITARY = "MILITARY"
    INTELLIGENCE = "INTELLIGENCE"
    FEDERAL = "FEDERAL"
    STATE = "STATE"
    LOCAL = "LOCAL"
    INTERNATIONAL = "INTERNATIONAL"
    PRIVATE = "PRIVATE"


class AgencyRole(str, Enum):
    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    NOTIFIED = "NOTIFIED"


class AgencyEntry(BaseModel):
    agency_name: str
    agency_type: AgencyType
    role: AgencyRole
    contact: str | None = None
    notes: str | None = None


class ResponsePlanStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class ResponsePlan(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    site_id: UUID
    threat_scenario_id: UUID | None = None
    title: str
    description: str | None = None
    agencies: list[AgencyEntry] = Field(default_factory=list)
    evacuation_routes: list[str] = Field(default_factory=list)
    shelter_capacity: int = 0
    estimated_response_time_min: int = 10
    status: ResponsePlanStatus = ResponsePlanStatus.DRAFT
    created_at: datetime
    created_by: str | None = None


class CreateResponsePlanRequest(BaseModel):
    scenario_id: UUID | None = None
    site_id: UUID
    threat_scenario_id: UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    agencies: list[AgencyEntry] = Field(default_factory=list)
    evacuation_routes: list[str] = Field(default_factory=list)
    shelter_capacity: int = Field(default=0, ge=0)
    estimated_response_time_min: int = Field(default=10, ge=1)
    status: ResponsePlanStatus = ResponsePlanStatus.DRAFT


class UpdateResponsePlanRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    agencies: list[AgencyEntry] | None = None
    evacuation_routes: list[str] | None = None
    shelter_capacity: int | None = Field(default=None, ge=0)
    estimated_response_time_min: int | None = Field(default=None, ge=1)
    status: ResponsePlanStatus | None = None


# ---------------------------------------------------------------------------
# Vulnerability Analysis
# ---------------------------------------------------------------------------

class AttackRisk(BaseModel):
    attack_type_id: str
    attack_type_label: str
    risk_score: float = Field(description="Composite risk score (0–10). Higher = greater risk at this site.")
    rationale: str


class SiteVulnerabilityAnalysis(BaseModel):
    site_id: UUID
    site_name: str
    vulnerability_score: float
    dimension_scores: dict[str, float]
    top_attack_risks: list[AttackRisk]
    recommendations: list[str]
    analysis_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

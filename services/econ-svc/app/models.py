from __future__ import annotations

from datetime import date, datetime
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


class SanctionType(str, Enum):
    ASSET_FREEZE = "ASSET_FREEZE"
    TRADE_EMBARGO = "TRADE_EMBARGO"
    TRAVEL_BAN = "TRAVEL_BAN"
    FINANCIAL_CUTOFF = "FINANCIAL_CUTOFF"
    TECH_TRANSFER = "TECH_TRANSFER"
    SECTORAL = "SECTORAL"
    INDIVIDUAL = "INDIVIDUAL"
    ARMS_EMBARGO = "ARMS_EMBARGO"


class SanctionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    LIFTED = "LIFTED"
    PROPOSED = "PROPOSED"


class TradeDependency(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class ImpactSeverity(str, Enum):
    CATASTROPHIC = "CATASTROPHIC"
    SEVERE = "SEVERE"
    MODERATE = "MODERATE"
    LIMITED = "LIMITED"
    NEGLIGIBLE = "NEGLIGIBLE"


# ---------------------------------------------------------------------------
# Sanction Target models
# ---------------------------------------------------------------------------

class SanctionTarget(BaseModel):
    id: UUID
    name: str
    country_code: str
    target_type: str  # COUNTRY / ENTITY / INDIVIDUAL
    sanction_type: SanctionType
    status: SanctionStatus
    imposing_parties: list[str] = Field(default_factory=list)
    effective_date: date | None = None
    annual_gdp_impact_pct: float | None = None
    notes: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateSanctionTargetRequest(BaseModel):
    name: str
    country_code: str
    target_type: str = "COUNTRY"
    sanction_type: SanctionType
    status: SanctionStatus = SanctionStatus.ACTIVE
    imposing_parties: list[str] = Field(default_factory=list)
    effective_date: date | None = None
    annual_gdp_impact_pct: float | None = None
    notes: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class UpdateSanctionTargetRequest(BaseModel):
    name: str | None = None
    status: SanctionStatus | None = None
    sanction_type: SanctionType | None = None
    imposing_parties: list[str] | None = None
    annual_gdp_impact_pct: float | None = None
    notes: str | None = None
    classification: ClassificationLevel | None = None


# ---------------------------------------------------------------------------
# Trade Route models
# ---------------------------------------------------------------------------

class TradeRoute(BaseModel):
    id: UUID
    origin_country: str
    destination_country: str
    commodity: str
    annual_value_usd: int
    dependency_level: TradeDependency
    is_disrupted: bool = False
    disruption_cause: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateTradeRouteRequest(BaseModel):
    origin_country: str
    destination_country: str
    commodity: str
    annual_value_usd: int
    dependency_level: TradeDependency = TradeDependency.MEDIUM
    is_disrupted: bool = False
    disruption_cause: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class UpdateTradeRouteRequest(BaseModel):
    commodity: str | None = None
    annual_value_usd: int | None = None
    dependency_level: TradeDependency | None = None
    is_disrupted: bool | None = None
    disruption_cause: str | None = None
    classification: ClassificationLevel | None = None


# ---------------------------------------------------------------------------
# Economic Impact Assessment models
# ---------------------------------------------------------------------------

class EconomicImpactAssessment(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    target_country: str
    gdp_impact_pct: float
    inflation_rate_change: float
    unemployment_change: float
    currency_devaluation_pct: float
    trade_volume_reduction_pct: float
    affected_sectors: list[str] = Field(default_factory=list)
    severity: ImpactSeverity
    timeline_months: int
    confidence_score: float = Field(ge=0.0, le=1.0)
    notes: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class RunImpactAssessmentRequest(BaseModel):
    target_country: str
    sanction_ids: list[UUID] = Field(default_factory=list)
    scenario_id: UUID | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


# ---------------------------------------------------------------------------
# Economic Indicator models
# ---------------------------------------------------------------------------

class EconomicIndicator(BaseModel):
    id: UUID
    country_code: str
    indicator_name: str
    value: float
    unit: str
    year: int
    source: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime


class CreateEconomicIndicatorRequest(BaseModel):
    country_code: str
    indicator_name: str
    value: float
    unit: str
    year: int
    source: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS

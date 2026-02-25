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


class NarrativeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    COUNTERED = "COUNTERED"
    NEUTRALIZED = "NEUTRALIZED"


class NarrativeThreatLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PlatformType(str, Enum):
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    NEWS_OUTLET = "NEWS_OUTLET"
    MESSAGING_APP = "MESSAGING_APP"
    FORUM = "FORUM"
    VIDEO_PLATFORM = "VIDEO_PLATFORM"
    BLOG = "BLOG"
    STATE_MEDIA = "STATE_MEDIA"
    UNKNOWN = "UNKNOWN"


class CampaignStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPECTED = "SUSPECTED"
    HISTORICAL = "HISTORICAL"
    UNCONFIRMED = "UNCONFIRMED"


class AttributionConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNATTRIBUTED = "UNATTRIBUTED"


class IndicatorType(str, Enum):
    COORDINATED_INAUTHENTIC_BEHAVIOR = "COORDINATED_INAUTHENTIC_BEHAVIOR"
    FAKE_ACCOUNT_NETWORK = "FAKE_ACCOUNT_NETWORK"
    DEEPFAKE_CONTENT = "DEEPFAKE_CONTENT"
    ASTROTURFING = "ASTROTURFING"
    HASHTAG_HIJACKING = "HASHTAG_HIJACKING"
    CONTENT_FARM = "CONTENT_FARM"
    BOT_NETWORK = "BOT_NETWORK"
    NARRATIVE_AMPLIFICATION = "NARRATIVE_AMPLIFICATION"


# ---------------------------------------------------------------------------
# Narrative Threat models
# ---------------------------------------------------------------------------

class NarrativeThreat(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    origin_country: str | None = None
    target_countries: list[str] = Field(default_factory=list)
    platforms: list[PlatformType] = Field(default_factory=list)
    status: NarrativeStatus = NarrativeStatus.ACTIVE
    threat_level: NarrativeThreatLevel = NarrativeThreatLevel.MEDIUM
    spread_velocity: float = Field(default=0.5, ge=0.0, le=1.0, description="How fast spreading 0-1")
    reach_estimate: int = Field(default=0, description="Estimated audience")
    key_claims: list[str] = Field(default_factory=list)
    counter_narratives: list[str] = Field(default_factory=list)
    first_detected: datetime
    last_updated: datetime
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateNarrativeThreatRequest(BaseModel):
    title: str
    description: str | None = None
    origin_country: str | None = None
    target_countries: list[str] = Field(default_factory=list)
    platforms: list[PlatformType] = Field(default_factory=list)
    status: NarrativeStatus = NarrativeStatus.ACTIVE
    threat_level: NarrativeThreatLevel = NarrativeThreatLevel.MEDIUM
    spread_velocity: float = Field(default=0.5, ge=0.0, le=1.0)
    reach_estimate: int = 0
    key_claims: list[str] = Field(default_factory=list)
    counter_narratives: list[str] = Field(default_factory=list)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class UpdateNarrativeThreatRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    origin_country: str | None = None
    target_countries: list[str] | None = None
    platforms: list[PlatformType] | None = None
    status: NarrativeStatus | None = None
    threat_level: NarrativeThreatLevel | None = None
    spread_velocity: float | None = None
    reach_estimate: int | None = None
    key_claims: list[str] | None = None
    counter_narratives: list[str] | None = None
    classification: ClassificationLevel | None = None


# ---------------------------------------------------------------------------
# Influence Campaign models
# ---------------------------------------------------------------------------

class InfluenceCampaign(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    attributed_actor: str | None = None
    attribution_confidence: AttributionConfidence = AttributionConfidence.UNATTRIBUTED
    sponsoring_state: str | None = None
    target_countries: list[str] = Field(default_factory=list)
    target_demographics: list[str] = Field(default_factory=list)
    platforms: list[PlatformType] = Field(default_factory=list)
    status: CampaignStatus = CampaignStatus.UNCONFIRMED
    campaign_objectives: list[str] = Field(default_factory=list)
    estimated_budget_usd: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    linked_narrative_ids: list[UUID] = Field(default_factory=list)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateInfluenceCampaignRequest(BaseModel):
    name: str
    description: str | None = None
    attributed_actor: str | None = None
    attribution_confidence: AttributionConfidence = AttributionConfidence.UNATTRIBUTED
    sponsoring_state: str | None = None
    target_countries: list[str] = Field(default_factory=list)
    target_demographics: list[str] = Field(default_factory=list)
    platforms: list[PlatformType] = Field(default_factory=list)
    status: CampaignStatus = CampaignStatus.UNCONFIRMED
    campaign_objectives: list[str] = Field(default_factory=list)
    estimated_budget_usd: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    linked_narrative_ids: list[UUID] = Field(default_factory=list)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class UpdateInfluenceCampaignRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    attributed_actor: str | None = None
    attribution_confidence: AttributionConfidence | None = None
    sponsoring_state: str | None = None
    target_countries: list[str] | None = None
    target_demographics: list[str] | None = None
    platforms: list[PlatformType] | None = None
    status: CampaignStatus | None = None
    campaign_objectives: list[str] | None = None
    estimated_budget_usd: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    linked_narrative_ids: list[UUID] | None = None
    classification: ClassificationLevel | None = None


# ---------------------------------------------------------------------------
# Disinformation Indicator models
# ---------------------------------------------------------------------------

class DisinformationIndicator(BaseModel):
    id: UUID
    indicator_type: IndicatorType
    title: str
    description: str | None = None
    source_url: str | None = None
    platform: PlatformType
    detected_at: datetime
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    linked_campaign_id: UUID | None = None
    linked_narrative_id: UUID | None = None
    is_verified: bool = False
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateDisinformationIndicatorRequest(BaseModel):
    indicator_type: IndicatorType
    title: str
    description: str | None = None
    source_url: str | None = None
    platform: PlatformType
    detected_at: datetime | None = None
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    linked_campaign_id: UUID | None = None
    linked_narrative_id: UUID | None = None
    is_verified: bool = False
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


# ---------------------------------------------------------------------------
# Attribution Assessment models
# ---------------------------------------------------------------------------

class AttributionAssessment(BaseModel):
    id: UUID
    subject: str
    attributed_to: str
    confidence: AttributionConfidence
    evidence_summary: str | None = None
    supporting_indicators: list[str] = Field(default_factory=list)
    dissenting_evidence: list[str] = Field(default_factory=list)
    analyst_id: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateAttributionAssessmentRequest(BaseModel):
    subject: str
    attributed_to: str
    confidence: AttributionConfidence = AttributionConfidence.LOW
    evidence_summary: str | None = None
    supporting_indicators: list[str] = Field(default_factory=list)
    dissenting_evidence: list[str] = Field(default_factory=list)
    analyst_id: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


# ---------------------------------------------------------------------------
# Narrative Analysis (engine output)
# ---------------------------------------------------------------------------

class NarrativeAnalysis(BaseModel):
    narrative_id: UUID
    spread_score: float = Field(ge=0.0, le=1.0)
    virality_index: float = Field(ge=0.0, le=1.0)
    counter_effectiveness: float = Field(ge=0.0, le=1.0)
    recommended_actions: list[str]
    risk_level: str

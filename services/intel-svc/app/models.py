from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SourceType(str, Enum):
    OSINT = "OSINT"
    SIGINT = "SIGINT"
    HUMINT = "HUMINT"
    IMINT = "IMINT"
    TECHINT = "TECHINT"
    FININT = "FININT"


class ClassificationLevel(str, Enum):
    UNCLASS = "UNCLASS"
    FOUO = "FOUO"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
    TS_SCI = "TS_SCI"


class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    WEAPON = "WEAPON"
    DATE = "DATE"
    EVENT = "EVENT"
    VEHICLE = "VEHICLE"
    FACILITY = "FACILITY"


class ThreatVector(str, Enum):
    MILITARY = "MILITARY"
    TERRORIST = "TERRORIST"
    CYBER = "CYBER"
    CBRN = "CBRN"
    ECONOMIC = "ECONOMIC"
    HYBRID = "HYBRID"


class ThreatLevel(str, Enum):
    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OSINTSourceType(str, Enum):
    ACLED = "ACLED"
    UCDP = "UCDP"
    RSS = "RSS"
    MANUAL = "MANUAL"


class OSINTSourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


# ---------------------------------------------------------------------------
# Intel Item
# ---------------------------------------------------------------------------

class ExtractedEntity(BaseModel):
    type: EntityType
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_char: int | None = None
    end_char: int | None = None


class IntelItem(BaseModel):
    id: UUID
    source_type: SourceType
    source_url: str | None = None
    title: str
    content: str
    language: str = "eng"
    latitude: float | None = None
    longitude: float | None = None
    entities: list[ExtractedEntity] = Field(default_factory=list)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    # NATO admiralty reliability scale: A=completely reliable … F=cannot be judged
    reliability: str = "F"
    # NATO admiralty credibility scale: 1=confirmed … 6=truth cannot be judged
    credibility: str = "6"
    published_at: datetime | None = None
    ingested_at: datetime
    has_embedding: bool = False


class CreateIntelItemRequest(BaseModel):
    source_type: SourceType
    source_url: str | None = None
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    language: str = "eng"
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    reliability: str = Field(default="F", pattern=r"^[A-F]$")
    credibility: str = Field(default="6", pattern=r"^[1-6]$")
    published_at: datetime | None = None
    auto_extract: bool = True


class UpdateIntelItemRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = None
    classification: ClassificationLevel | None = None
    reliability: str | None = Field(default=None, pattern=r"^[A-F]$")
    credibility: str | None = Field(default=None, pattern=r"^[1-6]$")


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    q: str | None = None
    source_types: list[SourceType] | None = None
    classification: ClassificationLevel | None = None
    entity_types: list[EntityType] | None = None
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    radius_km: float | None = Field(default=None, gt=0.0)
    from_date: datetime | None = None
    to_date: datetime | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    source_types: list[SourceType] | None = None
    classification: ClassificationLevel | None = None


class SearchResult(BaseModel):
    items: list[IntelItem]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Entity Extraction
# ---------------------------------------------------------------------------

class ExtractionRequest(BaseModel):
    text: str = Field(min_length=1)
    item_id: UUID | None = None


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity]
    entity_count: int
    method: str  # "deterministic" or "ai"
    duration_ms: float


# ---------------------------------------------------------------------------
# Threat Assessment
# ---------------------------------------------------------------------------

class ThreatIndicator(BaseModel):
    indicator: str
    weight: float
    present: bool
    source: str | None = None


class ThreatAssessmentRequest(BaseModel):
    actor: str = Field(min_length=1)
    target: str = Field(min_length=1)
    context: str | None = None
    intel_item_ids: list[UUID] | None = None


class ThreatAssessmentResult(BaseModel):
    actor: str
    target: str
    threat_level: ThreatLevel
    threat_score: float = Field(description="Composite threat score 0–10")
    threat_vectors: list[ThreatVector]
    indicators: list[ThreatIndicator]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    recommendations: list[str]
    assessed_at: datetime
    ai_assisted: bool = False


# ---------------------------------------------------------------------------
# OSINT Pipeline
# ---------------------------------------------------------------------------

class OSINTSource(BaseModel):
    id: str
    name: str
    source_type: OSINTSourceType
    status: OSINTSourceStatus
    last_ingested_at: datetime | None = None
    items_ingested: int = 0
    error_message: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class IngestRequest(BaseModel):
    source_id: str
    since_days: int = Field(default=7, ge=1, le=365)
    max_items: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = False


class IngestResult(BaseModel):
    source_id: str
    source_type: OSINTSourceType
    items_fetched: int
    items_saved: int
    errors: list[str] = Field(default_factory=list)
    dry_run: bool = False
    duration_seconds: float

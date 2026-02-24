from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Cell Type Catalog
# ---------------------------------------------------------------------------

class CellFunction(str, Enum):
    COMMAND = "COMMAND"
    OPERATIONS = "OPERATIONS"
    LOGISTICS = "LOGISTICS"
    INTELLIGENCE = "INTELLIGENCE"
    FINANCE = "FINANCE"
    RECRUITMENT = "RECRUITMENT"
    PROPAGANDA = "PROPAGANDA"
    SAFE_HOUSE = "SAFE_HOUSE"
    MEDICAL = "MEDICAL"
    TECHNICAL = "TECHNICAL"


class CellStructure(str, Enum):
    HIERARCHICAL = "HIERARCHICAL"
    NETWORK = "NETWORK"
    HUB_AND_SPOKE = "HUB_AND_SPOKE"
    CHAIN = "CHAIN"
    HYBRID = "HYBRID"


class CellTypeEntry(BaseModel):
    id: str
    function: CellFunction
    label: str
    description: str
    typical_size_min: int
    typical_size_max: int
    detection_difficulty: str         # LOW / MEDIUM / HIGH
    interdiction_priority: int        # 1-10
    icon: str
    color_hex: str = "#6B7280"


# ---------------------------------------------------------------------------
# IED Type Catalog
# ---------------------------------------------------------------------------

class IEDCategory(str, Enum):
    VEHICLE = "VEHICLE"
    PERSON_BORNE = "PERSON_BORNE"
    PLACED = "PLACED"
    EXPLOSIVELY_FORMED = "EXPLOSIVELY_FORMED"
    REMOTE_CONTROLLED = "REMOTE_CONTROLLED"
    VICTIM_OPERATED = "VICTIM_OPERATED"
    AERIAL = "AERIAL"


class IEDTypeEntry(BaseModel):
    id: str
    category: IEDCategory
    label: str
    description: str
    typical_yield_kg_tnt_equiv: float
    lethal_radius_m: float
    injury_radius_m: float
    blast_radius_m: float
    avg_killed: int
    avg_wounded: int
    detection_difficulty: str          # LOW / MEDIUM / HIGH
    primary_effect: str                # BLAST / BLAST_FRAGMENTATION / ARMOR_PENETRATION
    countermeasures: list[str]
    construction_complexity: str       # LOW / MEDIUM / HIGH
    color_hex: str = "#F97316"


# ---------------------------------------------------------------------------
# Insurgent Cell
# ---------------------------------------------------------------------------

class CellStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    DISRUPTED = "DISRUPTED"
    NEUTRALIZED = "NEUTRALIZED"
    UNKNOWN = "UNKNOWN"


class FundingLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class InsurgentCell(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    name: str
    function: CellFunction
    structure: CellStructure = CellStructure.NETWORK
    status: CellStatus = CellStatus.UNKNOWN
    # Personnel
    size_estimated: int = Field(ge=1, description="Estimated number of members")
    # Location
    latitude: float | None = None
    longitude: float | None = None
    region: str | None = None
    country_code: str | None = None
    # Capability assessments (0.0–1.0)
    leadership_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    operational_capability: float = Field(default=0.5, ge=0.0, le=1.0)
    funding_level: FundingLevel = FundingLevel.UNKNOWN
    # Affiliations
    affiliated_groups: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime
    created_by: str | None = None


class CreateCellRequest(BaseModel):
    scenario_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    function: CellFunction
    structure: CellStructure = CellStructure.NETWORK
    status: CellStatus = CellStatus.UNKNOWN
    size_estimated: int = Field(default=5, ge=1)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    region: str | None = None
    country_code: str | None = None
    leadership_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    operational_capability: float = Field(default=0.5, ge=0.0, le=1.0)
    funding_level: FundingLevel = FundingLevel.UNKNOWN
    affiliated_groups: list[str] = Field(default_factory=list)
    notes: str | None = None


class UpdateCellRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    function: CellFunction | None = None
    structure: CellStructure | None = None
    status: CellStatus | None = None
    size_estimated: int | None = Field(default=None, ge=1)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    region: str | None = None
    country_code: str | None = None
    leadership_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    operational_capability: float | None = Field(default=None, ge=0.0, le=1.0)
    funding_level: FundingLevel | None = None
    affiliated_groups: list[str] | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Cell Links (network edges)
# ---------------------------------------------------------------------------

class LinkType(str, Enum):
    COMMAND = "COMMAND"
    LOGISTICS = "LOGISTICS"
    FINANCE = "FINANCE"
    COMMS = "COMMS"
    IDEOLOGY = "IDEOLOGY"
    FAMILY = "FAMILY"
    UNKNOWN = "UNKNOWN"


class LinkStrength(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class CellLink(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    source_cell_id: UUID
    target_cell_id: UUID
    link_type: LinkType = LinkType.UNKNOWN
    strength: LinkStrength = LinkStrength.MODERATE
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: str | None = None
    created_at: datetime
    created_by: str | None = None


class CreateCellLinkRequest(BaseModel):
    scenario_id: UUID | None = None
    source_cell_id: UUID
    target_cell_id: UUID
    link_type: LinkType = LinkType.UNKNOWN
    strength: LinkStrength = LinkStrength.MODERATE
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: str | None = None


# ---------------------------------------------------------------------------
# Cell Network (full graph)
# ---------------------------------------------------------------------------

class CellNetwork(BaseModel):
    scenario_id: UUID | None = None
    cells: list[InsurgentCell]
    links: list[CellLink]


# ---------------------------------------------------------------------------
# IED Incidents
# ---------------------------------------------------------------------------

class IncidentStatus(str, Enum):
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"
    NEUTRALIZED = "NEUTRALIZED"
    DETONATED = "DETONATED"


class DetonationType(str, Enum):
    COMMAND_WIRE = "COMMAND_WIRE"
    REMOTE = "REMOTE"
    PRESSURE = "PRESSURE"
    TIMER = "TIMER"
    VICTIM_OPERATED = "VICTIM_OPERATED"
    UNKNOWN = "UNKNOWN"


class TargetType(str, Enum):
    CONVOY = "CONVOY"
    PATROL = "PATROL"
    CHECKPOINT = "CHECKPOINT"
    CIVILIAN = "CIVILIAN"
    VIP = "VIP"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    MARKET = "MARKET"
    GOVERNMENT = "GOVERNMENT"
    UNKNOWN = "UNKNOWN"


class IEDIncident(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    ied_type_id: str
    # Location
    latitude: float
    longitude: float
    location_description: str | None = None
    # Incident details
    status: IncidentStatus = IncidentStatus.SUSPECTED
    detonation_type: DetonationType = DetonationType.UNKNOWN
    target_type: TargetType = TargetType.UNKNOWN
    placement_date: datetime | None = None
    detection_date: datetime | None = None
    detonation_date: datetime | None = None
    # Effects
    estimated_yield_kg: float | None = None
    casualties_killed: int = 0
    casualties_wounded: int = 0
    # Attribution
    attributed_cell_id: UUID | None = None
    notes: str | None = None
    created_at: datetime
    created_by: str | None = None


class CreateIncidentRequest(BaseModel):
    scenario_id: UUID | None = None
    ied_type_id: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    location_description: str | None = None
    status: IncidentStatus = IncidentStatus.SUSPECTED
    detonation_type: DetonationType = DetonationType.UNKNOWN
    target_type: TargetType = TargetType.UNKNOWN
    placement_date: datetime | None = None
    detection_date: datetime | None = None
    detonation_date: datetime | None = None
    estimated_yield_kg: float | None = None
    casualties_killed: int = Field(default=0, ge=0)
    casualties_wounded: int = Field(default=0, ge=0)
    attributed_cell_id: UUID | None = None
    notes: str | None = None


class UpdateIncidentRequest(BaseModel):
    ied_type_id: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    location_description: str | None = None
    status: IncidentStatus | None = None
    detonation_type: DetonationType | None = None
    target_type: TargetType | None = None
    placement_date: datetime | None = None
    detection_date: datetime | None = None
    detonation_date: datetime | None = None
    estimated_yield_kg: float | None = None
    casualties_killed: int | None = Field(default=None, ge=0)
    casualties_wounded: int | None = Field(default=None, ge=0)
    attributed_cell_id: UUID | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Network Analysis
# ---------------------------------------------------------------------------

class CellAnalysisNode(BaseModel):
    cell_id: UUID
    cell_name: str
    function: CellFunction
    hub_score: float = Field(description="Normalized centrality score (0–1). Higher = more critical to network.")
    degree: int = Field(description="Number of direct connections to other cells.")
    betweenness: float = Field(description="Fraction of shortest paths that pass through this cell.")
    interdiction_value: int = Field(description="Composite interdiction priority (1–10).")
    recommendation: str


class NetworkAnalysis(BaseModel):
    scenario_id: UUID | None = None
    total_cells: int
    total_links: int
    active_cells: int
    network_density: float = Field(description="Ratio of actual to possible links (0–1).")
    top_targets: list[CellAnalysisNode]
    coin_recommendations: list[str]
    analysis_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

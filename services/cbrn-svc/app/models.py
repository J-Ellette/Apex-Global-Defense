from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Agent Catalog
# ---------------------------------------------------------------------------

class CBRNCategory(str, Enum):
    CHEMICAL = "CHEMICAL"
    BIOLOGICAL = "BIOLOGICAL"
    RADIOLOGICAL = "RADIOLOGICAL"
    NUCLEAR = "NUCLEAR"


class AgentState(str, Enum):
    GAS = "GAS"
    VAPOR = "VAPOR"
    LIQUID = "LIQUID"
    AEROSOL = "AEROSOL"
    PARTICULATE = "PARTICULATE"
    EXPLOSION = "EXPLOSION"


class Persistency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class CBRNAgent(BaseModel):
    id: str
    name: str
    category: CBRNCategory
    sub_category: str
    description: str
    state: AgentState
    persistency: Persistency
    # Physical properties (None for bio/nuclear/rad where not applicable)
    vapor_pressure_pa: float | None = None
    density_kg_m3: float | None = None
    molecular_weight: float | None = None
    # Casualty thresholds
    lct50_mg_min_m3: float | None = None       # inhalation lethal Ct50
    ict50_mg_min_m3: float | None = None       # incapacitating Ct50
    idlh_mg_m3: float | None = None            # immediately dangerous to life/health
    id50_particles: float | None = None        # bio: infectious dose (particles)
    lethal_dose_gy: float | None = None        # rad/nuc: lethal absorbed dose
    incapacitating_dose_gy: float | None = None
    yield_kt: float | None = None              # nuclear yield (kilotons)
    half_life_min: float | None = None         # environmental half-life (minutes)
    # Response guidance
    protective_action: str
    nato_code: str
    color_hex: str = "#FF0000"


# ---------------------------------------------------------------------------
# Meteorological Conditions
# ---------------------------------------------------------------------------

class StabilityClass(str, Enum):
    """Pasquill-Gifford atmospheric stability classes."""
    A = "A"   # Very unstable
    B = "B"   # Unstable
    C = "C"   # Slightly unstable
    D = "D"   # Neutral
    E = "E"   # Slightly stable
    F = "F"   # Stable


class MetConditions(BaseModel):
    wind_speed_ms: float = Field(default=3.0, ge=0.1, le=50.0, description="Wind speed (m/s)")
    wind_direction_deg: float = Field(default=270.0, ge=0.0, lt=360.0, description="Wind direction FROM (degrees, meteorological)")
    stability_class: StabilityClass = StabilityClass.D
    mixing_height_m: float = Field(default=800.0, ge=50.0, le=5000.0, description="Atmospheric mixing height (m)")
    temperature_c: float = Field(default=15.0, description="Ambient temperature (°C)")
    relative_humidity_pct: float = Field(default=60.0, ge=0.0, le=100.0)


# ---------------------------------------------------------------------------
# Release Events
# ---------------------------------------------------------------------------

class ReleaseType(str, Enum):
    POINT = "POINT"        # Fixed-point release (e.g., munition, IED)
    LINE = "LINE"          # Line release (e.g., aircraft spray)
    AREA = "AREA"          # Area release (e.g., artillery barrage)


class CBRNRelease(BaseModel):
    id: UUID
    scenario_id: UUID | None = None
    agent_id: str
    release_type: ReleaseType = ReleaseType.POINT
    # Location (WGS-84)
    latitude: float
    longitude: float
    # Release parameters
    quantity_kg: float = Field(ge=0.001, description="Mass of agent released (kg)")
    release_height_m: float = Field(default=1.0, ge=0.0, description="Release height above ground (m)")
    duration_min: float = Field(default=10.0, ge=0.1, description="Release duration (minutes)")
    # Met conditions at release
    met: MetConditions = Field(default_factory=MetConditions)
    # Population density for casualty estimation
    population_density_per_km2: float = Field(default=500.0, ge=0.0)
    label: str = ""
    notes: str | None = None
    created_at: datetime
    created_by: str | None = None


class CreateReleaseRequest(BaseModel):
    scenario_id: UUID | None = None
    agent_id: str
    release_type: ReleaseType = ReleaseType.POINT
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    quantity_kg: float = Field(ge=0.001)
    release_height_m: float = Field(default=1.0, ge=0.0)
    duration_min: float = Field(default=10.0, ge=0.1)
    met: MetConditions = Field(default_factory=MetConditions)
    population_density_per_km2: float = Field(default=500.0, ge=0.0)
    label: str = ""
    notes: str | None = None


# ---------------------------------------------------------------------------
# Dispersion Simulation
# ---------------------------------------------------------------------------

class ConcentrationPoint(BaseModel):
    """A point in the concentration grid."""
    lat: float
    lon: float
    concentration_mg_m3: float
    dose_mg_min_m3: float


class PlumeContour(BaseModel):
    """A closed polygon representing a concentration isoline."""
    level_mg_m3: float
    label: str                             # e.g. "IDLH", "ICt50/min", "LCt50/min"
    coordinates: list[list[float]]         # [[lon, lat], ...]  — GeoJSON ring


class CasualtyZone(BaseModel):
    label: str                             # e.g. "Lethal Zone", "Injury Zone"
    estimated_casualties: int
    area_km2: float
    max_downwind_km: float
    max_crosswind_km: float
    contour: PlumeContour | None = None


class DispersionSimulation(BaseModel):
    id: UUID
    release_id: UUID
    simulated_at: datetime
    # Plume geometry
    max_downwind_km: float
    max_crosswind_km: float
    plume_area_km2: float
    # Contour polygons for map overlay
    contours: list[PlumeContour]
    # Casualty estimates
    lethal_zone: CasualtyZone | None = None
    injury_zone: CasualtyZone | None = None
    idlh_zone: CasualtyZone | None = None
    total_estimated_casualties: int
    # Wind vector for map display
    wind_direction_deg: float
    wind_speed_ms: float
    stability_class: str
    # Narrative
    summary: str
    protective_actions: str
    metadata: dict[str, Any] = Field(default_factory=dict)

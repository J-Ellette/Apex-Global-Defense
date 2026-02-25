from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    GEOJSON = "GEOJSON"
    KML = "KML"
    SHAPEFILE_ZIP = "SHAPEFILE_ZIP"
    CSV = "CSV"
    GPX = "GPX"


class LayerType(str, Enum):
    UNITS = "UNITS"
    INTEL_ITEMS = "INTEL_ITEMS"
    CBRN_RELEASES = "CBRN_RELEASES"
    CIVILIAN_ZONES = "CIVILIAN_ZONES"
    SANCTION_TARGETS = "SANCTION_TARGETS"
    TRADE_ROUTES = "TRADE_ROUTES"
    NARRATIVE_THREATS = "NARRATIVE_THREATS"
    TERROR_SITES = "TERROR_SITES"
    ASYM_CELLS = "ASYM_CELLS"


class ClassificationLevel(str, Enum):
    UNCLASS = "UNCLASS"
    FOUO = "FOUO"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"
    TS_SCI = "TS_SCI"


class ExportJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class IntegrationType(str, Enum):
    ARCGIS = "ARCGIS"
    GOOGLE_EARTH = "GOOGLE_EARTH"
    WMS = "WMS"
    WFS = "WFS"
    GENERIC_REST = "GENERIC_REST"


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    layer_type: LayerType
    format: ExportFormat
    scenario_id: UUID | None = None
    filters: dict[str, str] = Field(default_factory=dict)
    include_classification: bool = False
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class ExportJob(BaseModel):
    id: UUID
    layer_type: LayerType
    format: ExportFormat
    status: ExportJobStatus
    created_at: datetime
    completed_at: datetime | None = None
    download_url: str | None = None
    error: str | None = None
    classification: ClassificationLevel = ClassificationLevel.UNCLASS


class ArcGISLayerConfig(BaseModel):
    service_url: str
    layer_name: str
    username: str
    api_key: str = Field(default="", description="masked in responses")
    agol_item_id: str | None = None


class GoogleEarthConfig(BaseModel):
    kml_network_link_url: str
    refresh_interval_seconds: int = 300
    balloon_style: str = ""


class IntegrationConfig(BaseModel):
    id: UUID
    name: str
    integration_type: IntegrationType
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    classification: ClassificationLevel = ClassificationLevel.UNCLASS
    created_at: datetime
    updated_at: datetime


class CreateIntegrationConfigRequest(BaseModel):
    name: str
    integration_type: IntegrationType
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    classification: ClassificationLevel = ClassificationLevel.UNCLASS

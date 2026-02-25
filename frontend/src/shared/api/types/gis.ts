export type ExportFormat = 'GEOJSON' | 'KML' | 'SHAPEFILE_ZIP' | 'CSV' | 'GPX'

export type LayerType =
  | 'UNITS'
  | 'INTEL_ITEMS'
  | 'CBRN_RELEASES'
  | 'CIVILIAN_ZONES'
  | 'SANCTION_TARGETS'
  | 'TRADE_ROUTES'
  | 'NARRATIVE_THREATS'
  | 'TERROR_SITES'
  | 'ASYM_CELLS'

export type IntegrationType = 'ARCGIS' | 'GOOGLE_EARTH' | 'WMS' | 'WFS' | 'GENERIC_REST'

export type ClassificationLevel = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'

export interface ExportRequest {
  layer_type: LayerType
  format: ExportFormat
  scenario_id?: string
  filters?: Record<string, string>
  include_classification?: boolean
  classification?: ClassificationLevel
}

export interface IntegrationConfig {
  id: string
  name: string
  integration_type: IntegrationType
  config: Record<string, unknown>
  is_active: boolean
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateIntegrationConfigRequest {
  name: string
  integration_type: IntegrationType
  config: Record<string, unknown>
  is_active?: boolean
  classification?: ClassificationLevel
}

export interface IntegrationTestResult {
  status: string
  latency_ms: number
  message: string
}

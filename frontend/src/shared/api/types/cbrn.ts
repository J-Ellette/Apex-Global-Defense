// CBRN module types

export type CBRNCategory = 'CHEMICAL' | 'BIOLOGICAL' | 'RADIOLOGICAL' | 'NUCLEAR'

export type AgentState = 'GAS' | 'VAPOR' | 'LIQUID' | 'AEROSOL' | 'PARTICULATE' | 'EXPLOSION'

export type Persistency = 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH'

export interface CBRNAgent {
  id: string
  name: string
  category: CBRNCategory
  sub_category: string
  description: string
  state: AgentState
  persistency: Persistency
  vapor_pressure_pa: number | null
  density_kg_m3: number | null
  molecular_weight: number | null
  lct50_mg_min_m3: number | null
  ict50_mg_min_m3: number | null
  idlh_mg_m3: number | null
  id50_particles: number | null
  lethal_dose_gy: number | null
  incapacitating_dose_gy: number | null
  yield_kt: number | null
  half_life_min: number | null
  protective_action: string
  nato_code: string
  color_hex: string
}

export type StabilityClass = 'A' | 'B' | 'C' | 'D' | 'E' | 'F'

export interface MetConditions {
  wind_speed_ms: number
  wind_direction_deg: number
  stability_class: StabilityClass
  mixing_height_m: number
  temperature_c: number
  relative_humidity_pct: number
}

export type ReleaseType = 'POINT' | 'LINE' | 'AREA'

export interface CBRNRelease {
  id: string
  scenario_id: string | null
  agent_id: string
  release_type: ReleaseType
  latitude: number
  longitude: number
  quantity_kg: number
  release_height_m: number
  duration_min: number
  met: MetConditions
  population_density_per_km2: number
  label: string
  notes: string | null
  created_at: string
  created_by: string | null
}

export interface CreateReleaseRequest {
  scenario_id?: string
  agent_id: string
  release_type?: ReleaseType
  latitude: number
  longitude: number
  quantity_kg: number
  release_height_m?: number
  duration_min?: number
  met?: Partial<MetConditions>
  population_density_per_km2?: number
  label?: string
  notes?: string
}

export interface PlumeContour {
  level_mg_m3: number
  label: string
  coordinates: number[][]
}

export interface CasualtyZone {
  label: string
  estimated_casualties: number
  area_km2: number
  max_downwind_km: number
  max_crosswind_km: number
  contour: PlumeContour | null
}

export interface DispersionSimulation {
  id: string
  release_id: string
  simulated_at: string
  max_downwind_km: number
  max_crosswind_km: number
  plume_area_km2: number
  contours: PlumeContour[]
  lethal_zone: CasualtyZone | null
  injury_zone: CasualtyZone | null
  idlh_zone: CasualtyZone | null
  total_estimated_casualties: number
  wind_direction_deg: number
  wind_speed_ms: number
  stability_class: string
  summary: string
  protective_actions: string
  metadata: Record<string, unknown>
}

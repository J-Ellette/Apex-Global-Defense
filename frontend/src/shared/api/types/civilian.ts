// Civilian Impact Module — TypeScript types

export type DensityClass = 'URBAN' | 'SUBURBAN' | 'RURAL' | 'SPARSE'
export type CorridorStatus = 'OPEN' | 'RESTRICTED' | 'CLOSED'
export type DisplacementStatus = 'PROJECTED' | 'CONFIRMED' | 'RESOLVED'

// ── Population Zone ────────────────────────────────────────────────────────────

export interface PopulationZone {
  id: string
  scenario_id: string | null
  name: string
  country_code: string
  latitude: number
  longitude: number
  radius_km: number
  population: number
  density_class: DensityClass
  created_at: string
}

export interface CreatePopulationZoneRequest {
  scenario_id?: string | null
  name: string
  country_code: string
  latitude: number
  longitude: number
  radius_km: number
  population: number
  density_class: DensityClass
}

// ── Impact Assessment ──────────────────────────────────────────────────────────

export interface ZoneImpact {
  zone_id: string
  zone_name: string
  civilian_casualties: number
  civilian_wounded: number
  displaced_persons: number
  infrastructure_damage_pct: number
  impact_score: number
}

export interface ImpactAssessment {
  id: string
  run_id: string
  scenario_id: string | null
  assessed_at: string
  total_civilian_casualties: number
  total_civilian_wounded: number
  total_displaced_persons: number
  zone_impacts: ZoneImpact[]
  methodology: string
  notes: string | null
}

export interface AssessImpactRequest {
  run_id: string
  scenario_id?: string | null
  events?: Record<string, unknown>[] | null
}

// ── Refugee Flow ───────────────────────────────────────────────────────────────

export interface RefugeeFlow {
  id: string
  scenario_id: string | null
  origin_zone_id: string | null
  origin_name: string
  destination_name: string
  origin_lat: number
  origin_lon: number
  destination_lat: number
  destination_lon: number
  displaced_persons: number
  status: DisplacementStatus
  started_at: string
  updated_at: string
}

export interface CreateRefugeeFlowRequest {
  scenario_id?: string | null
  origin_zone_id?: string | null
  origin_name: string
  destination_name: string
  origin_lat: number
  origin_lon: number
  destination_lat: number
  destination_lon: number
  displaced_persons: number
  status?: DisplacementStatus
}

export interface UpdateRefugeeFlowRequest {
  displaced_persons?: number | null
  status?: DisplacementStatus | null
  destination_name?: string | null
}

// ── Humanitarian Corridor ──────────────────────────────────────────────────────

export interface CorridorWaypoint {
  lat: number
  lon: number
}

export interface HumanitarianCorridor {
  id: string
  scenario_id: string | null
  name: string
  waypoints: CorridorWaypoint[]
  status: CorridorStatus
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CreateCorridorRequest {
  scenario_id?: string | null
  name: string
  waypoints: CorridorWaypoint[]
  status?: CorridorStatus
  notes?: string | null
}

export interface UpdateCorridorRequest {
  status?: CorridorStatus | null
  notes?: string | null
}

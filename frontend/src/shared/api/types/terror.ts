// ---------------------------------------------------------------------------
// Terror Response Planning types
// ---------------------------------------------------------------------------

export type AttackCategory = 'KINETIC' | 'EXPLOSIVE' | 'CHEMICAL_BIO' | 'CYBER' | 'HYBRID'

export interface AttackTypeEntry {
  id: string
  category: AttackCategory
  label: string
  description: string
  typical_perpetrators: string[]
  typical_targets: string[]
  avg_killed_low: number
  avg_killed_high: number
  avg_wounded_low: number
  avg_wounded_high: number
  detection_window: string
  countermeasures: string[]
  threat_indicator: string
  color_hex: string
}

export type SiteType =
  | 'TRANSPORT_HUB'
  | 'STADIUM'
  | 'GOVERNMENT_BUILDING'
  | 'HOTEL'
  | 'MARKET'
  | 'HOUSE_OF_WORSHIP'
  | 'SCHOOL'
  | 'HOSPITAL'
  | 'EMBASSY'
  | 'CRITICAL_INFRASTRUCTURE'
  | 'FINANCIAL_CENTER'
  | 'MILITARY_BASE'
  | 'ENTERTAINMENT_VENUE'
  | 'SHOPPING_CENTER'

export type CrowdDensity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type SiteStatus = 'ACTIVE' | 'UNDER_REVIEW' | 'HARDENED' | 'CLOSED'

export interface TerrorSite {
  id: string
  scenario_id?: string
  name: string
  site_type: SiteType
  address?: string
  latitude?: number
  longitude?: number
  country_code?: string
  population_capacity: number
  physical_security: number
  access_control: number
  surveillance: number
  emergency_response: number
  crowd_density: CrowdDensity
  vulnerability_score: number
  assigned_agencies: string[]
  notes?: string
  status: SiteStatus
  created_at: string
  created_by?: string
}

export interface CreateSiteRequest {
  scenario_id?: string
  name: string
  site_type: SiteType
  address?: string
  latitude?: number
  longitude?: number
  country_code?: string
  population_capacity?: number
  physical_security?: number
  access_control?: number
  surveillance?: number
  emergency_response?: number
  crowd_density?: CrowdDensity
  assigned_agencies?: string[]
  notes?: string
  status?: SiteStatus
}

export interface UpdateSiteRequest {
  name?: string
  site_type?: SiteType
  address?: string
  latitude?: number
  longitude?: number
  country_code?: string
  population_capacity?: number
  physical_security?: number
  access_control?: number
  surveillance?: number
  emergency_response?: number
  crowd_density?: CrowdDensity
  assigned_agencies?: string[]
  notes?: string
  status?: SiteStatus
}

export type ThreatLevel = 'LOW' | 'ELEVATED' | 'HIGH' | 'CRITICAL' | 'IMMINENT'

export interface ThreatScenario {
  id: string
  scenario_id?: string
  site_id: string
  attack_type_id: string
  threat_level: ThreatLevel
  probability: number
  estimated_killed_low: number
  estimated_killed_high: number
  estimated_wounded_low: number
  estimated_wounded_high: number
  notes?: string
  created_at: string
  created_by?: string
}

export interface CreateThreatScenarioRequest {
  scenario_id?: string
  site_id: string
  attack_type_id: string
  threat_level?: ThreatLevel
  probability?: number
  estimated_killed_low?: number
  estimated_killed_high?: number
  estimated_wounded_low?: number
  estimated_wounded_high?: number
  notes?: string
}

export type AgencyType =
  | 'POLICE'
  | 'FIRE'
  | 'MEDICAL'
  | 'MILITARY'
  | 'INTELLIGENCE'
  | 'FEDERAL'
  | 'STATE'
  | 'LOCAL'
  | 'INTERNATIONAL'
  | 'PRIVATE'

export type AgencyRole = 'PRIMARY' | 'SUPPORTING' | 'NOTIFIED'

export interface AgencyEntry {
  agency_name: string
  agency_type: AgencyType
  role: AgencyRole
  contact?: string
  notes?: string
}

export type ResponsePlanStatus = 'DRAFT' | 'ACTIVE' | 'SUPERSEDED'

export interface ResponsePlan {
  id: string
  scenario_id?: string
  site_id: string
  threat_scenario_id?: string
  title: string
  description?: string
  agencies: AgencyEntry[]
  evacuation_routes: string[]
  shelter_capacity: number
  estimated_response_time_min: number
  status: ResponsePlanStatus
  created_at: string
  created_by?: string
}

export interface CreateResponsePlanRequest {
  scenario_id?: string
  site_id: string
  threat_scenario_id?: string
  title: string
  description?: string
  agencies?: AgencyEntry[]
  evacuation_routes?: string[]
  shelter_capacity?: number
  estimated_response_time_min?: number
}

export interface AttackRisk {
  attack_type_id: string
  attack_type_label: string
  risk_score: number
  rationale: string
}

export interface SiteVulnerabilityAnalysis {
  site_id: string
  site_name: string
  vulnerability_score: number
  dimension_scores: {
    physical_security: number
    access_control: number
    surveillance: number
    emergency_response: number
  }
  top_attack_risks: AttackRisk[]
  recommendations: string[]
  analysis_summary: string
  metadata: Record<string, unknown>
}

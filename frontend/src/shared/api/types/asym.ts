// ---------------------------------------------------------------------------
// Asymmetric / Insurgency module types
// ---------------------------------------------------------------------------

export type CellFunction =
  | 'COMMAND'
  | 'OPERATIONS'
  | 'LOGISTICS'
  | 'INTELLIGENCE'
  | 'FINANCE'
  | 'RECRUITMENT'
  | 'PROPAGANDA'
  | 'SAFE_HOUSE'
  | 'MEDICAL'
  | 'TECHNICAL'

export type CellStructure =
  | 'HIERARCHICAL'
  | 'NETWORK'
  | 'HUB_AND_SPOKE'
  | 'CHAIN'
  | 'HYBRID'

export type CellStatus = 'ACTIVE' | 'DORMANT' | 'DISRUPTED' | 'NEUTRALIZED' | 'UNKNOWN'

export type FundingLevel = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN'

export type LinkType = 'COMMAND' | 'LOGISTICS' | 'FINANCE' | 'COMMS' | 'IDEOLOGY' | 'FAMILY' | 'UNKNOWN'

export type LinkStrength = 'WEAK' | 'MODERATE' | 'STRONG'

export type IEDCategory =
  | 'VEHICLE'
  | 'PERSON_BORNE'
  | 'PLACED'
  | 'EXPLOSIVELY_FORMED'
  | 'REMOTE_CONTROLLED'
  | 'VICTIM_OPERATED'
  | 'AERIAL'

export type IncidentStatus = 'SUSPECTED' | 'CONFIRMED' | 'NEUTRALIZED' | 'DETONATED'

export type DetonationType =
  | 'COMMAND_WIRE'
  | 'REMOTE'
  | 'PRESSURE'
  | 'TIMER'
  | 'VICTIM_OPERATED'
  | 'UNKNOWN'

export type TargetType =
  | 'CONVOY'
  | 'PATROL'
  | 'CHECKPOINT'
  | 'CIVILIAN'
  | 'VIP'
  | 'INFRASTRUCTURE'
  | 'MARKET'
  | 'GOVERNMENT'
  | 'UNKNOWN'

// Static catalog
export interface CellTypeEntry {
  id: string
  function: CellFunction
  label: string
  description: string
  typical_size_min: number
  typical_size_max: number
  detection_difficulty: string
  interdiction_priority: number
  icon: string
  color_hex: string
}

export interface IEDTypeEntry {
  id: string
  category: IEDCategory
  label: string
  description: string
  typical_yield_kg_tnt_equiv: number
  lethal_radius_m: number
  injury_radius_m: number
  blast_radius_m: number
  avg_killed: number
  avg_wounded: number
  detection_difficulty: string
  primary_effect: string
  countermeasures: string[]
  construction_complexity: string
  color_hex: string
}

// DB entities
export interface InsurgentCell {
  id: string
  scenario_id?: string
  name: string
  function: CellFunction
  structure: CellStructure
  status: CellStatus
  size_estimated: number
  latitude?: number
  longitude?: number
  region?: string
  country_code?: string
  leadership_confidence: number
  operational_capability: number
  funding_level: FundingLevel
  affiliated_groups: string[]
  notes?: string
  created_at: string
  created_by?: string
}

export interface CreateCellRequest {
  scenario_id?: string
  name: string
  function: CellFunction
  structure?: CellStructure
  status?: CellStatus
  size_estimated?: number
  latitude?: number
  longitude?: number
  region?: string
  country_code?: string
  leadership_confidence?: number
  operational_capability?: number
  funding_level?: FundingLevel
  affiliated_groups?: string[]
  notes?: string
}

export interface UpdateCellRequest {
  name?: string
  function?: CellFunction
  structure?: CellStructure
  status?: CellStatus
  size_estimated?: number
  latitude?: number
  longitude?: number
  region?: string
  country_code?: string
  leadership_confidence?: number
  operational_capability?: number
  funding_level?: FundingLevel
  affiliated_groups?: string[]
  notes?: string
}

export interface CellLink {
  id: string
  scenario_id?: string
  source_cell_id: string
  target_cell_id: string
  link_type: LinkType
  strength: LinkStrength
  confidence: number
  notes?: string
  created_at: string
  created_by?: string
}

export interface CreateCellLinkRequest {
  scenario_id?: string
  source_cell_id: string
  target_cell_id: string
  link_type?: LinkType
  strength?: LinkStrength
  confidence?: number
  notes?: string
}

export interface CellNetwork {
  scenario_id?: string
  cells: InsurgentCell[]
  links: CellLink[]
}

export interface IEDIncident {
  id: string
  scenario_id?: string
  ied_type_id: string
  latitude: number
  longitude: number
  location_description?: string
  status: IncidentStatus
  detonation_type: DetonationType
  target_type: TargetType
  placement_date?: string
  detection_date?: string
  detonation_date?: string
  estimated_yield_kg?: number
  casualties_killed: number
  casualties_wounded: number
  attributed_cell_id?: string
  notes?: string
  created_at: string
  created_by?: string
}

export interface CreateIncidentRequest {
  scenario_id?: string
  ied_type_id: string
  latitude: number
  longitude: number
  location_description?: string
  status?: IncidentStatus
  detonation_type?: DetonationType
  target_type?: TargetType
  placement_date?: string
  detection_date?: string
  detonation_date?: string
  estimated_yield_kg?: number
  casualties_killed?: number
  casualties_wounded?: number
  attributed_cell_id?: string
  notes?: string
}

export interface UpdateIncidentRequest {
  ied_type_id?: string
  latitude?: number
  longitude?: number
  location_description?: string
  status?: IncidentStatus
  detonation_type?: DetonationType
  target_type?: TargetType
  placement_date?: string
  detection_date?: string
  detonation_date?: string
  estimated_yield_kg?: number
  casualties_killed?: number
  casualties_wounded?: number
  attributed_cell_id?: string
  notes?: string
}

// Network Analysis
export interface CellAnalysisNode {
  cell_id: string
  cell_name: string
  function: CellFunction
  hub_score: number
  degree: number
  betweenness: number
  interdiction_value: number
  recommendation: string
}

export interface NetworkAnalysis {
  scenario_id?: string
  total_cells: number
  total_links: number
  active_cells: number
  network_density: number
  top_targets: CellAnalysisNode[]
  coin_recommendations: string[]
  analysis_summary: string
  metadata: Record<string, unknown>
}

export type SimMode = 'real_time' | 'turn_based' | 'monte_carlo'

export type SimStatus = 'queued' | 'running' | 'paused' | 'complete' | 'error'

export type SimEventType =
  | 'UNIT_MOVE'
  | 'ENGAGEMENT'
  | 'CASUALTY'
  | 'SUPPLY_CONSUMED'
  | 'RESUPPLY'
  | 'OBJECTIVE_CAPTURED'
  | 'AIRSTRIKE'
  | 'NAVAL_ACTION'
  | 'CYBER_ATTACK'
  | 'CBRN_RELEASE'
  | 'PHASE_CHANGE'

export interface ScenarioRunConfig {
  mode: SimMode
  blue_force_ids: string[]
  red_force_ids: string[]
  theater_bounds?: Record<string, unknown>
  start_time: string
  duration_hours: number
  monte_carlo_runs: number
  weather_preset: string
  fog_of_war: boolean
  terrain_effects: boolean
}

export interface SimulationRun {
  id: string
  scenario_id: string
  mode: SimMode
  status: SimStatus
  progress: number
  config: Record<string, unknown>
  created_by: string
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
}

export interface SimEvent {
  time: string
  run_id: string
  event_type: SimEventType
  entity_id?: string
  location?: { lat: number; lng: number }
  payload: Record<string, unknown>
  turn_number?: number
}

export interface OutcomeDistribution {
  blue_win_pct: number
  red_win_pct: number
  contested_pct: number
  mean_duration_hours: number
  std_duration_hours: number
}

export interface CasualtyDistribution {
  mean: number
  std: number
  p10: number
  p50: number
  p90: number
}

export interface MCResult {
  runs_completed: number
  objective_outcomes: Record<string, OutcomeDistribution>
  blue_casualties: CasualtyDistribution
  red_casualties: CasualtyDistribution
  duration_distribution: number[]
}

// Logistics & Attrition types
export interface SupplyLevels {
  ammo: number    // 0.0 – 1.0 fraction remaining
  fuel: number
  rations: number
}

export interface ForceSummary {
  strength_pct: number   // 0.0 – 1.0
  kia: number
  wia: number
  supply: SupplyLevels
  equipment_losses: Record<string, number>  // armor / artillery / aircraft → count
}

export interface LogisticsState {
  run_id: string
  turn_number: number
  sim_time: string
  blue: ForceSummary
  red: ForceSummary
}

export interface LogisticsSummary {
  blue_final_strength_pct: number
  red_final_strength_pct: number
  blue_total_kia: number
  red_total_kia: number
  blue_supply: SupplyLevels
  red_supply: SupplyLevels
  blue_equipment_losses: Record<string, number>
  red_equipment_losses: Record<string, number>
}

export interface AfterActionReport {
  run_id: string
  scenario_id: string
  generated_at: string
  executive_summary: string
  duration_hours: number
  total_turns: number | null
  blue_objectives_captured: number
  red_objectives_captured: number
  blue_casualties: number
  red_casualties: number
  key_events: SimEvent[]
  mc_result?: MCResult
  logistics_summary?: LogisticsSummary
}

export interface StartRunRequest {
  config: ScenarioRunConfig
}

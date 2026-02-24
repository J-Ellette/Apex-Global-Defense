export type SimMode = 'real_time' | 'turn_based' | 'monte_carlo'

export type SimStatus = 'queued' | 'running' | 'paused' | 'complete' | 'error'

export type SimEventType =
  | 'UNIT_MOVE'
  | 'ENGAGEMENT'
  | 'CASUALTY'
  | 'SUPPLY_CONSUMED'
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
}

export interface StartRunRequest {
  config: ScenarioRunConfig
}

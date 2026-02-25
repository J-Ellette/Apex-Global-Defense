// Training Mode — TypeScript types

export type ClassificationLevel = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'

export type ExerciseStatus =
  | 'DRAFT'
  | 'SCHEDULED'
  | 'ACTIVE'
  | 'PAUSED'
  | 'COMPLETED'
  | 'CANCELLED'

export type InjectType =
  | 'UNIT_MOVEMENT'
  | 'INTEL_REPORT'
  | 'COMMS_DEGRADATION'
  | 'ENEMY_ATTACK'
  | 'FRIENDLY_CASUALTIES'
  | 'CBRN_ALERT'
  | 'CYBER_ATTACK'
  | 'CIVILIAN_INCIDENT'
  | 'LOGISTICS_FAILURE'
  | 'WEATHER_CHANGE'
  | 'COMMAND_MESSAGE'
  | 'CUSTOM'

export type InjectTrigger = 'TIME_BASED' | 'EVENT_BASED' | 'MANUAL' | 'CONDITION_BASED'

export type InjectStatus = 'PENDING' | 'INJECTED' | 'ACKNOWLEDGED' | 'EXPIRED'

export type ObjectiveType = 'DECISION' | 'REPORT' | 'ACTION' | 'COMMUNICATION' | 'ASSESSMENT'

export type ObjectiveStatus = 'PENDING' | 'MET' | 'PARTIALLY_MET' | 'NOT_MET' | 'SKIPPED'

// ── Exercise ──────────────────────────────────────────────────────────────────

export interface Exercise {
  id: string
  name: string
  description: string | null
  scenario_id: string | null
  instructor_id: string
  trainee_ids: string[]
  status: ExerciseStatus
  classification: ClassificationLevel
  planned_start: string | null
  actual_start: string | null
  actual_end: string | null
  learning_objectives: string[]
  created_at: string
  updated_at: string
}

export interface CreateExerciseRequest {
  name: string
  description?: string | null
  scenario_id?: string | null
  instructor_id: string
  trainee_ids?: string[]
  classification?: ClassificationLevel
  planned_start?: string | null
  learning_objectives?: string[]
}

export interface UpdateExerciseRequest {
  name?: string | null
  description?: string | null
  scenario_id?: string | null
  trainee_ids?: string[] | null
  status?: ExerciseStatus | null
  classification?: ClassificationLevel | null
  planned_start?: string | null
  learning_objectives?: string[] | null
}

// ── Inject ────────────────────────────────────────────────────────────────────

export interface ExerciseInject {
  id: string
  exercise_id: string
  inject_type: InjectType
  trigger_type: InjectTrigger
  title: string
  description: string | null
  payload: Record<string, unknown>
  trigger_time_offset_minutes: number | null
  trigger_event: string | null
  trigger_condition: string | null
  status: InjectStatus
  injected_at: string | null
  acknowledged_by: string | null
  acknowledged_at: string | null
  classification: ClassificationLevel
  created_at: string
}

export interface CreateInjectRequest {
  exercise_id: string
  inject_type: InjectType
  trigger_type: InjectTrigger
  title: string
  description?: string | null
  payload?: Record<string, unknown>
  trigger_time_offset_minutes?: number | null
  trigger_event?: string | null
  trigger_condition?: string | null
  classification?: ClassificationLevel
}

// ── Objective ─────────────────────────────────────────────────────────────────

export interface ExerciseObjective {
  id: string
  exercise_id: string
  objective_type: ObjectiveType
  description: string
  expected_response: string | null
  weight: number
  status: ObjectiveStatus
  actual_response: string | null
  score: number | null
  scorer_id: string | null
  scored_at: string | null
  feedback: string | null
  classification: ClassificationLevel
  created_at: string
}

export interface CreateObjectiveRequest {
  exercise_id: string
  objective_type: ObjectiveType
  description: string
  expected_response?: string | null
  weight?: number
  classification?: ClassificationLevel
}

export interface ScoreObjectiveRequest {
  status: ObjectiveStatus
  actual_response?: string | null
  score?: number | null
  feedback?: string | null
  scorer_id: string
}

// ── Exercise Score ────────────────────────────────────────────────────────────

export interface ExerciseScore {
  exercise_id: string
  total_score: number
  objectives_met: number
  objectives_partial: number
  objectives_not_met: number
  objectives_total: number
  completion_pct: number
  timeliness_score: number
  accuracy_score: number
  communication_score: number
  grade: string
  instructor_notes: string | null
  scored_at: string | null
}

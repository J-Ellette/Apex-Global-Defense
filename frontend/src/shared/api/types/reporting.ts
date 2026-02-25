export type ReportType = 'SITREP' | 'INTSUM' | 'CONOPS'
export type ReportStatus = 'DRAFT' | 'FINAL' | 'APPROVED'
export type ClassificationLevel = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'

export interface Report {
  id: string
  scenario_id: string | null
  run_id: string | null
  report_type: ReportType
  title: string
  classification: ClassificationLevel
  author_id: string | null
  status: ReportStatus
  content: Record<string, unknown>
  summary: string | null
  created_at: string
  updated_at: string
  approved_by: string | null
  approved_at: string | null
}

export interface GenerateReportRequest {
  report_type: ReportType
  title?: string
  scenario_id?: string
  run_id?: string
  classification?: ClassificationLevel
  context?: string
}

export interface UpdateReportRequest {
  title?: string
  status?: ReportStatus
  classification?: ClassificationLevel
  content?: Record<string, unknown>
  summary?: string
}

export interface ApproveReportRequest {
  approved_by: string
}

// Structured content types

export interface SITREPContent {
  period_from: string
  period_to: string
  situation_summary: string
  friendly_forces: string
  enemy_forces: string
  civilian_situation: string
  significant_events: string[]
  current_operations: string
  planned_operations: string
  logistics_status: string
  weather: string
  commander_assessment: string
  next_report_due: string
}

export interface INTSUMContent {
  period_from: string
  period_to: string
  enemy_disposition: string
  enemy_strength: string
  enemy_capabilities: string
  enemy_intentions: string
  threat_level: string
  key_developments: string[]
  isr_gaps: string[]
  cyber_threats: string
  cbrn_threats: string
  threat_indicators: Array<{ indicator: string; pattern_type: string; confidence: string }>
  analyst_assessment: string
  confidence_level: string
}

export interface CONOPSContent {
  mission_statement: string
  commander_intent: string
  end_state: string
  scheme_of_maneuver: string
  tasks_to_subordinate_units: Array<{ unit: string; task: string }>
  tasks_to_supporting_elements: Array<{ element: string; task: string }>
  coordinating_instructions: string[]
  sustainment_concept: string
  command_and_signal: string
  risk_assessment: string
  execution_phases: Array<{ phase: string; duration: string; description: string }>
}

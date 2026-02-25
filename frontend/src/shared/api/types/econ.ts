// Economic Warfare Module — TypeScript types

export type ClassificationLevel = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'
export type SanctionType =
  | 'ASSET_FREEZE'
  | 'TRADE_EMBARGO'
  | 'TRAVEL_BAN'
  | 'FINANCIAL_CUTOFF'
  | 'TECH_TRANSFER'
  | 'SECTORAL'
  | 'INDIVIDUAL'
  | 'ARMS_EMBARGO'
export type SanctionStatus = 'ACTIVE' | 'SUSPENDED' | 'LIFTED' | 'PROPOSED'
export type TradeDependency = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE'
export type ImpactSeverity = 'CATASTROPHIC' | 'SEVERE' | 'MODERATE' | 'LIMITED' | 'NEGLIGIBLE'

// ── Sanction Target ────────────────────────────────────────────────────────────

export interface SanctionTarget {
  id: string
  name: string
  country_code: string
  target_type: string
  sanction_type: SanctionType
  status: SanctionStatus
  imposing_parties: string[]
  effective_date: string | null
  annual_gdp_impact_pct: number | null
  notes: string | null
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateSanctionTargetRequest {
  name: string
  country_code: string
  target_type?: string
  sanction_type: SanctionType
  status?: SanctionStatus
  imposing_parties?: string[]
  effective_date?: string | null
  annual_gdp_impact_pct?: number | null
  notes?: string | null
  classification?: ClassificationLevel
}

export interface UpdateSanctionTargetRequest {
  name?: string | null
  status?: SanctionStatus | null
  sanction_type?: SanctionType | null
  imposing_parties?: string[] | null
  annual_gdp_impact_pct?: number | null
  notes?: string | null
  classification?: ClassificationLevel | null
}

// ── Trade Route ────────────────────────────────────────────────────────────────

export interface TradeRoute {
  id: string
  origin_country: string
  destination_country: string
  commodity: string
  annual_value_usd: number
  dependency_level: TradeDependency
  is_disrupted: boolean
  disruption_cause: string | null
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateTradeRouteRequest {
  origin_country: string
  destination_country: string
  commodity: string
  annual_value_usd: number
  dependency_level?: TradeDependency
  is_disrupted?: boolean
  disruption_cause?: string | null
  classification?: ClassificationLevel
}

export interface UpdateTradeRouteRequest {
  commodity?: string | null
  annual_value_usd?: number | null
  dependency_level?: TradeDependency | null
  is_disrupted?: boolean | null
  disruption_cause?: string | null
  classification?: ClassificationLevel | null
}

// ── Economic Impact Assessment ─────────────────────────────────────────────────

export interface EconomicImpactAssessment {
  id: string
  scenario_id: string | null
  target_country: string
  gdp_impact_pct: number
  inflation_rate_change: number
  unemployment_change: number
  currency_devaluation_pct: number
  trade_volume_reduction_pct: number
  affected_sectors: string[]
  severity: ImpactSeverity
  timeline_months: number
  confidence_score: number
  notes: string | null
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface RunImpactAssessmentRequest {
  target_country: string
  sanction_ids?: string[]
  scenario_id?: string | null
  classification?: ClassificationLevel
}

// ── Economic Indicator ─────────────────────────────────────────────────────────

export interface EconomicIndicator {
  id: string
  country_code: string
  indicator_name: string
  value: number
  unit: string
  year: number
  source: string | null
  classification: ClassificationLevel
  created_at: string
}

export interface CreateEconomicIndicatorRequest {
  country_code: string
  indicator_name: string
  value: number
  unit: string
  year: number
  source?: string | null
  classification?: ClassificationLevel
}

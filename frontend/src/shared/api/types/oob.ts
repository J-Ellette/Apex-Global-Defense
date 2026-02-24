import type { ClassificationLevel } from './auth'

export type MilitaryBranch =
  | 'ARMY'
  | 'NAVY'
  | 'AIR'
  | 'SPACE'
  | 'CYBER'
  | 'INTEL'
  | 'SPECIAL_OPS'
  | 'COAST_GUARD'

export type Echelon =
  | 'FIRETEAM'
  | 'SQUAD'
  | 'SECTION'
  | 'PLATOON'
  | 'COMPANY'
  | 'BATTALION'
  | 'REGIMENT'
  | 'BRIGADE'
  | 'DIVISION'
  | 'CORPS'
  | 'FIELD_ARMY'
  | 'ARMY_GROUP'
  | 'CARRIER_STRIKE_GROUP'
  | 'FLEET'
  | 'WING'
  | 'GROUP'
  | 'SQUADRON'

export interface Country {
  code: string
  name: string
  region?: string
  alliance_codes: string[]
  gdp_usd?: number
  defense_budget_usd?: number
  population?: number
  area_km2?: number
  iso2?: string
  flag_emoji?: string
  updated_at: string
}

export interface MilitaryUnit {
  id: string
  country_code: string
  branch: MilitaryBranch
  echelon?: Echelon
  name: string
  short_name?: string
  nato_symbol?: string
  parent_id?: string
  lat?: number
  lng?: number
  classification: ClassificationLevel
  confidence?: number
  data_sources: string[]
  as_of: string
  created_at: string
  updated_at: string
}

export interface CreateUnitRequest {
  country_code: string
  branch: MilitaryBranch
  echelon?: Echelon
  name: string
  short_name?: string
  nato_symbol?: string
  parent_id?: string
  lat?: number
  lng?: number
  classification?: ClassificationLevel
  confidence?: number
  data_sources?: string[]
  as_of: string
}

export interface UpdateUnitRequest {
  branch?: MilitaryBranch
  echelon?: Echelon
  name?: string
  short_name?: string
  nato_symbol?: string
  parent_id?: string
  lat?: number
  lng?: number
  classification?: ClassificationLevel
  confidence?: number
  data_sources?: string[]
  as_of?: string
}

export interface PersonnelSummary {
  total?: number
  active_duty?: number
  reserve?: number
  paramilitary?: number
}

export interface CountryStrength {
  country: Country
  total_units: number
  by_branch: Record<string, number>
  personnel?: PersonnelSummary
}

export interface CompareRequest {
  country_a: string
  country_b: string
  as_of?: string
}

export interface CompareResponse {
  country_a: CountryStrength
  country_b: CountryStrength
}

export interface EquipmentCatalogItem {
  type_code: string
  category: string
  name: string
  origin_country?: string
  specs?: Record<string, unknown>
  threat_score?: number
  in_service_year?: number
  updated_at: string
}

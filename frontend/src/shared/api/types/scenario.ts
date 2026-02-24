import type { ClassificationLevel } from './auth'

export interface Scenario {
  id: string
  name: string
  description?: string
  classification: ClassificationLevel
  created_by: string
  org_id: string
  parent_id?: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface CreateScenarioRequest {
  name: string
  description?: string
  classification?: ClassificationLevel
  tags?: string[]
}

export interface UpdateScenarioRequest {
  name?: string
  description?: string
  classification?: ClassificationLevel
  tags?: string[]
}

export interface BranchScenarioRequest {
  name: string
}

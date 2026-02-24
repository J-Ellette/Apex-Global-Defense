// Classification levels — mirror of backend models
export type ClassificationLevel = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'

export type Role =
  | 'viewer'
  | 'analyst'
  | 'planner'
  | 'commander'
  | 'sim_operator'
  | 'admin'
  | 'classification_officer'

export type Permission =
  | 'scenario:read'
  | 'scenario:write'
  | 'oob:read'
  | 'oob:write'
  | 'intel:read'
  | 'intel:write'
  | 'simulation:run'
  | 'simulation:control'
  | 'users:manage'
  | 'classification:manage'

export interface User {
  id: string
  email: string
  display_name: string
  roles: Role[]
  classification: ClassificationLevel
  org_id: string
  active: boolean
  created_at: string
  last_login_at?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RefreshRequest {
  refresh_token: string
}

export interface APIError {
  error: string
  message?: string
  status?: number
}

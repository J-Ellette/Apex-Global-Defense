// MITRE ATT&CK types
export type ATTACKTactic =
  | 'reconnaissance'
  | 'resource_development'
  | 'initial_access'
  | 'execution'
  | 'persistence'
  | 'privilege_escalation'
  | 'defense_evasion'
  | 'credential_access'
  | 'discovery'
  | 'lateral_movement'
  | 'collection'
  | 'command_and_control'
  | 'exfiltration'
  | 'impact'

export interface ATTACKTechnique {
  id: string
  name: string
  tactic: ATTACKTactic
  description: string
  platforms: string[]
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  mitigations: string[]
  url: string
}

// Infrastructure graph
export type NodeType =
  | 'HOST'
  | 'SERVER'
  | 'ROUTER'
  | 'FIREWALL'
  | 'ICS'
  | 'CLOUD'
  | 'SATELLITE'
  | 'IOT'
  | 'DATABASE'

export type Criticality = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface InfraNode {
  id: string
  scenario_id: string | null
  label: string
  node_type: NodeType
  network: string | null
  ip_address: string | null
  criticality: Criticality
  classification: string
  tags: string[]
  metadata: Record<string, unknown>
  created_at: string
}

export interface InfraEdge {
  id: string
  source_id: string
  target_id: string
  edge_type: string
  protocol: string | null
  port: number | null
  created_at: string
}

export interface InfraGraph {
  nodes: InfraNode[]
  edges: InfraEdge[]
}

export interface CreateInfraNodeRequest {
  scenario_id?: string
  label: string
  node_type: NodeType
  network?: string
  ip_address?: string
  criticality?: Criticality
  classification?: string
  tags?: string[]
  metadata?: Record<string, unknown>
}

export interface CreateInfraEdgeRequest {
  source_id: string
  target_id: string
  edge_type?: string
  protocol?: string
  port?: number
}

// Cyber attacks
export type AttackStatus = 'PLANNED' | 'EXECUTING' | 'COMPLETE' | 'FAILED' | 'DETECTED'

export interface CyberAttack {
  id: string
  scenario_id: string | null
  technique_id: string
  target_node_id: string | null
  attacker: string
  status: AttackStatus
  success_probability: number
  impact: string
  notes: string | null
  created_at: string
  executed_at: string | null
  result: Record<string, unknown> | null
}

export interface CreateAttackRequest {
  scenario_id?: string
  technique_id: string
  target_node_id?: string
  attacker: string
  impact?: string
  notes?: string
}

export interface SimulateAttackRequest {
  defender_skill: number
  network_hardening: number
}

export interface SimulateAttackResult {
  attack_id: string
  success: boolean
  detected: boolean
  damage_level: 'NONE' | 'MINIMAL' | 'MODERATE' | 'SEVERE' | 'CATASTROPHIC'
  affected_nodes: string[]
  narrative: string
  ttd_minutes: number | null
  persistence_achieved: boolean
}

// STIX/TAXII threat intelligence

export type PatternType = 'stix' | 'pcre' | 'yara' | 'sigma'

export interface KillChainPhase {
  kill_chain_name: string
  phase_name: string
}

export interface ExternalReference {
  source_name: string
  url?: string
  external_id?: string
  description?: string
}

export interface STIXIndicator {
  id: string
  stix_id: string
  stix_type: string
  spec_version: string
  name: string
  description: string | null
  pattern: string
  pattern_type: PatternType
  indicator_types: string[]
  kill_chain_phases: KillChainPhase[]
  confidence: number
  labels: string[]
  valid_from: string
  valid_until: string | null
  created: string
  modified: string
  created_by_ref: string | null
  external_references: ExternalReference[]
  taxii_collection: string | null
  taxii_server: string | null
  classification: string
  scenario_id: string | null
  ingested_at: string
}

export interface CreateSTIXIndicatorRequest {
  stix_id?: string
  name: string
  description?: string
  pattern: string
  pattern_type?: PatternType
  indicator_types?: string[]
  kill_chain_phases?: KillChainPhase[]
  confidence?: number
  labels?: string[]
  valid_from: string
  valid_until?: string
  external_references?: ExternalReference[]
  taxii_collection?: string
  taxii_server?: string
  classification?: string
  scenario_id?: string
}

export interface TAXIIIngestRequest {
  server_url: string
  collection_id: string
  api_key?: string
  max_items?: number
  dry_run?: boolean
}

export interface TAXIIIngestResult {
  server_url: string
  collection_id: string
  items_fetched: number
  items_saved: number
  errors: string[]
  dry_run: boolean
  duration_seconds: number
}

// ---------------------------------------------------------------------------
// Intelligence Service types
// ---------------------------------------------------------------------------

export type SourceType = 'OSINT' | 'SIGINT' | 'HUMINT' | 'IMINT' | 'TECHINT' | 'FININT'

export type IntelClassification = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'

export type EntityType =
  | 'PERSON'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'WEAPON'
  | 'DATE'
  | 'EVENT'
  | 'VEHICLE'
  | 'FACILITY'

export type ThreatLevel = 'NEGLIGIBLE' | 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'

export type ThreatVector = 'MILITARY' | 'TERRORIST' | 'CYBER' | 'CBRN' | 'ECONOMIC' | 'HYBRID'

export type OSINTSourceType = 'ACLED' | 'UCDP' | 'RSS' | 'MANUAL'

export type OSINTSourceStatus = 'ACTIVE' | 'ERROR' | 'DISABLED'

// ---------------------------------------------------------------------------
// Intel Item
// ---------------------------------------------------------------------------

export interface ExtractedEntity {
  type: EntityType
  text: string
  confidence: number
  start_char?: number
  end_char?: number
}

export interface IntelItem {
  id: string
  source_type: SourceType
  source_url?: string
  title: string
  content: string
  language: string
  latitude?: number
  longitude?: number
  entities: ExtractedEntity[]
  classification: IntelClassification
  reliability: string
  credibility: string
  published_at?: string
  ingested_at: string
  has_embedding: boolean
}

export interface CreateIntelItemRequest {
  source_type: SourceType
  source_url?: string
  title: string
  content: string
  language?: string
  latitude?: number
  longitude?: number
  classification?: IntelClassification
  reliability?: string
  credibility?: string
  published_at?: string
  auto_extract?: boolean
}

export interface UpdateIntelItemRequest {
  title?: string
  content?: string
  classification?: IntelClassification
  reliability?: string
  credibility?: string
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export interface SearchRequest {
  q?: string
  source_types?: SourceType[]
  classification?: IntelClassification
  entity_types?: EntityType[]
  lat?: number
  lon?: number
  radius_km?: number
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}

export interface SemanticSearchRequest {
  query: string
  limit?: number
  source_types?: SourceType[]
  classification?: IntelClassification
}

export interface SearchResult {
  items: IntelItem[]
  total: number
  limit: number
  offset: number
}

// ---------------------------------------------------------------------------
// Entity Extraction
// ---------------------------------------------------------------------------

export interface ExtractionRequest {
  text: string
  item_id?: string
}

export interface ExtractionResult {
  entities: ExtractedEntity[]
  entity_count: number
  method: string
  duration_ms: number
}

// ---------------------------------------------------------------------------
// Threat Assessment
// ---------------------------------------------------------------------------

export interface ThreatIndicator {
  indicator: string
  weight: number
  present: boolean
  source?: string
}

export interface ThreatAssessmentRequest {
  actor: string
  target: string
  context?: string
  intel_item_ids?: string[]
}

export interface ThreatAssessmentResult {
  actor: string
  target: string
  threat_level: ThreatLevel
  threat_score: number
  threat_vectors: ThreatVector[]
  indicators: ThreatIndicator[]
  confidence: number
  summary: string
  recommendations: string[]
  assessed_at: string
  ai_assisted: boolean
}

// ---------------------------------------------------------------------------
// OSINT Pipeline
// ---------------------------------------------------------------------------

export interface OSINTSource {
  id: string
  name: string
  source_type: OSINTSourceType
  status: OSINTSourceStatus
  last_ingested_at?: string
  items_ingested: number
  error_message?: string
}

export interface IngestRequest {
  source_id: string
  since_days?: number
  max_items?: number
  dry_run?: boolean
}

export interface IngestResult {
  source_id: string
  source_type: OSINTSourceType
  items_fetched: number
  items_saved: number
  errors: string[]
  dry_run: boolean
  duration_seconds: number
}

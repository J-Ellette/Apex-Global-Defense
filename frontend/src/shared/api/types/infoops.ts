// TypeScript types for the Information Operations service

export type ClassificationLevel = 'UNCLASS' | 'FOUO' | 'SECRET' | 'TOP_SECRET' | 'TS_SCI'

export type NarrativeStatus = 'ACTIVE' | 'DORMANT' | 'COUNTERED' | 'NEUTRALIZED'

export type NarrativeThreatLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export type PlatformType =
  | 'SOCIAL_MEDIA'
  | 'NEWS_OUTLET'
  | 'MESSAGING_APP'
  | 'FORUM'
  | 'VIDEO_PLATFORM'
  | 'BLOG'
  | 'STATE_MEDIA'
  | 'UNKNOWN'

export type CampaignStatus = 'ACTIVE' | 'SUSPECTED' | 'HISTORICAL' | 'UNCONFIRMED'

export type AttributionConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNATTRIBUTED'

export type IndicatorType =
  | 'COORDINATED_INAUTHENTIC_BEHAVIOR'
  | 'FAKE_ACCOUNT_NETWORK'
  | 'DEEPFAKE_CONTENT'
  | 'ASTROTURFING'
  | 'HASHTAG_HIJACKING'
  | 'CONTENT_FARM'
  | 'BOT_NETWORK'
  | 'NARRATIVE_AMPLIFICATION'

// ---------------------------------------------------------------------------
// Narrative Threats
// ---------------------------------------------------------------------------

export interface NarrativeThreat {
  id: string
  title: string
  description: string | null
  origin_country: string | null
  target_countries: string[]
  platforms: PlatformType[]
  status: NarrativeStatus
  threat_level: NarrativeThreatLevel
  spread_velocity: number
  reach_estimate: number
  key_claims: string[]
  counter_narratives: string[]
  first_detected: string
  last_updated: string
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateNarrativeThreatRequest {
  title: string
  description?: string | null
  origin_country?: string | null
  target_countries?: string[]
  platforms?: PlatformType[]
  status?: NarrativeStatus
  threat_level?: NarrativeThreatLevel
  spread_velocity?: number
  reach_estimate?: number
  key_claims?: string[]
  counter_narratives?: string[]
  classification?: ClassificationLevel
}

// ---------------------------------------------------------------------------
// Influence Campaigns
// ---------------------------------------------------------------------------

export interface InfluenceCampaign {
  id: string
  name: string
  description: string | null
  attributed_actor: string | null
  attribution_confidence: AttributionConfidence
  sponsoring_state: string | null
  target_countries: string[]
  target_demographics: string[]
  platforms: PlatformType[]
  status: CampaignStatus
  campaign_objectives: string[]
  estimated_budget_usd: number | null
  start_date: string | null
  end_date: string | null
  linked_narrative_ids: string[]
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateInfluenceCampaignRequest {
  name: string
  description?: string | null
  attributed_actor?: string | null
  attribution_confidence?: AttributionConfidence
  sponsoring_state?: string | null
  target_countries?: string[]
  target_demographics?: string[]
  platforms?: PlatformType[]
  status?: CampaignStatus
  campaign_objectives?: string[]
  estimated_budget_usd?: number | null
  start_date?: string | null
  end_date?: string | null
  linked_narrative_ids?: string[]
  classification?: ClassificationLevel
}

// ---------------------------------------------------------------------------
// Disinformation Indicators
// ---------------------------------------------------------------------------

export interface DisinformationIndicator {
  id: string
  indicator_type: IndicatorType
  title: string
  description: string | null
  source_url: string | null
  platform: PlatformType
  detected_at: string
  confidence_score: number
  linked_campaign_id: string | null
  linked_narrative_id: string | null
  is_verified: boolean
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateDisinformationIndicatorRequest {
  indicator_type: IndicatorType
  title: string
  description?: string | null
  source_url?: string | null
  platform: PlatformType
  detected_at?: string | null
  confidence_score?: number
  linked_campaign_id?: string | null
  linked_narrative_id?: string | null
  is_verified?: boolean
  classification?: ClassificationLevel
}

// ---------------------------------------------------------------------------
// Attribution Assessments
// ---------------------------------------------------------------------------

export interface AttributionAssessment {
  id: string
  subject: string
  attributed_to: string
  confidence: AttributionConfidence
  evidence_summary: string | null
  supporting_indicators: string[]
  dissenting_evidence: string[]
  analyst_id: string | null
  classification: ClassificationLevel
  created_at: string
  updated_at: string
}

export interface CreateAttributionAssessmentRequest {
  subject: string
  attributed_to: string
  confidence?: AttributionConfidence
  evidence_summary?: string | null
  supporting_indicators?: string[]
  dissenting_evidence?: string[]
  analyst_id?: string | null
  classification?: ClassificationLevel
}

// ---------------------------------------------------------------------------
// Narrative Analysis (engine output)
// ---------------------------------------------------------------------------

export interface NarrativeAnalysis {
  narrative_id: string
  spread_score: number
  virality_index: number
  counter_effectiveness: number
  recommended_actions: string[]
  risk_level: string
}

import { useEffect, useState, useCallback } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { infoopsClient } from '../../shared/api/infoopsClient'
import type {
  NarrativeThreat,
  NarrativeThreatLevel,
  NarrativeStatus,
  InfluenceCampaign,
  AttributionConfidence,
  CampaignStatus,
  DisinformationIndicator,
  IndicatorType,
  AttributionAssessment,
  NarrativeAnalysis,
  CreateNarrativeThreatRequest,
  CreateInfluenceCampaignRequest,
  CreateDisinformationIndicatorRequest,
  CreateAttributionAssessmentRequest,
  PlatformType,
} from '../../shared/api/types/infoops'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type Tab = 'narratives' | 'campaigns' | 'indicators' | 'attribution'

const THREAT_LEVEL_COLORS: Record<NarrativeThreatLevel, string> = {
  CRITICAL: 'bg-red-900 text-red-200',
  HIGH: 'bg-orange-900 text-orange-200',
  MEDIUM: 'bg-yellow-900 text-yellow-200',
  LOW: 'bg-green-900 text-green-200',
}

const NARRATIVE_STATUS_COLORS: Record<NarrativeStatus, string> = {
  ACTIVE: 'bg-red-900 text-red-200',
  DORMANT: 'bg-gray-700 text-gray-300',
  COUNTERED: 'bg-blue-900 text-blue-200',
  NEUTRALIZED: 'bg-green-900 text-green-200',
}

const CONFIDENCE_COLORS: Record<AttributionConfidence, string> = {
  HIGH: 'bg-red-900 text-red-200',
  MEDIUM: 'bg-yellow-900 text-yellow-200',
  LOW: 'bg-gray-700 text-gray-300',
  UNATTRIBUTED: 'bg-gray-800 text-gray-400',
}

const CAMPAIGN_STATUS_COLORS: Record<CampaignStatus, string> = {
  ACTIVE: 'bg-red-900 text-red-200',
  SUSPECTED: 'bg-orange-900 text-orange-200',
  HISTORICAL: 'bg-gray-700 text-gray-300',
  UNCONFIRMED: 'bg-blue-900 text-blue-200',
}

const PLATFORM_ICONS: Partial<Record<PlatformType, string>> = {
  SOCIAL_MEDIA: '📱',
  NEWS_OUTLET: '📰',
  MESSAGING_APP: '💬',
  FORUM: '🗣️',
  VIDEO_PLATFORM: '🎬',
  BLOG: '📝',
  STATE_MEDIA: '📡',
  UNKNOWN: '❓',
}

// ---------------------------------------------------------------------------
// Analysis Modal
// ---------------------------------------------------------------------------

interface AnalysisModalProps {
  narrative: NarrativeThreat
  analysis: NarrativeAnalysis
  onClose: () => void
}

function AnalysisModal({ narrative, analysis, onClose }: AnalysisModalProps) {
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg p-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-base font-semibold text-white">Narrative Analysis</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">✕</button>
        </div>
        <p className="text-sm text-gray-400 mb-4">{narrative.title}</p>

        <div className="grid grid-cols-3 gap-3 mb-4">
          {[
            { label: 'Spread Score', value: (analysis.spread_score * 100).toFixed(0) + '%' },
            { label: 'Virality Index', value: (analysis.virality_index * 100).toFixed(0) + '%' },
            { label: 'Counter Effectiveness', value: (analysis.counter_effectiveness * 100).toFixed(0) + '%' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-gray-800 rounded p-3 text-center">
              <p className="text-lg font-bold text-sky-400">{value}</p>
              <p className="text-xs text-gray-400 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        <div className="mb-4">
          <p className="text-xs text-gray-400 mb-1">Risk Level</p>
          <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${THREAT_LEVEL_COLORS[analysis.risk_level as NarrativeThreatLevel] ?? 'bg-gray-700 text-gray-300'}`}>
            {analysis.risk_level}
          </span>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-2">Recommended Actions</p>
          <ul className="space-y-1">
            {analysis.recommended_actions.map((action, idx) => (
              <li key={idx} className="text-sm text-gray-300 flex gap-2">
                <span className="text-sky-500 flex-shrink-0">›</span>
                {action}
              </li>
            ))}
          </ul>
        </div>

        <button
          onClick={onClose}
          className="mt-5 w-full bg-sky-700 hover:bg-sky-600 text-white text-sm py-2 rounded"
        >
          Close
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Add Narrative Modal
// ---------------------------------------------------------------------------

interface AddNarrativeModalProps {
  onClose: () => void
  onCreated: (n: NarrativeThreat) => void
}

function AddNarrativeModal({ onClose, onCreated }: AddNarrativeModalProps) {
  const [title, setTitle] = useState('')
  const [originCountry, setOriginCountry] = useState('')
  const [threatLevel, setThreatLevel] = useState<NarrativeThreatLevel>('MEDIUM')
  const [spreadVelocity, setSpreadVelocity] = useState('0.5')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!title.trim()) { setError('Title is required'); return }
    setLoading(true)
    setError(null)
    try {
      const body: CreateNarrativeThreatRequest = {
        title: title.trim(),
        origin_country: originCountry.trim() || null,
        threat_level: threatLevel,
        spread_velocity: parseFloat(spreadVelocity) || 0.5,
      }
      const resp = await infoopsClient.post<NarrativeThreat>('/narratives', body)
      onCreated(resp.data)
      onClose()
    } catch {
      setError('Failed to create narrative threat')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-semibold text-white">Add Narrative Threat</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">✕</button>
        </div>
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Title *</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Narrative title"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Origin Country (ISO-3)</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={originCountry}
              onChange={(e) => setOriginCountry(e.target.value)}
              placeholder="e.g. RUS"
              maxLength={3}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Threat Level</label>
            <select
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={threatLevel}
              onChange={(e) => setThreatLevel(e.target.value as NarrativeThreatLevel)}
            >
              {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as NarrativeThreatLevel[]).map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Spread Velocity (0–1)</label>
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={spreadVelocity}
              onChange={(e) => setSpreadVelocity(e.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-3 mt-5">
          <button onClick={onClose} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-sm py-2 rounded">
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="flex-1 bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-sm py-2 rounded"
          >
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Narratives Tab
// ---------------------------------------------------------------------------

function NarrativesTab() {
  const [narratives, setNarratives] = useState<NarrativeThreat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [analysisState, setAnalysisState] = useState<{
    narrative: NarrativeThreat
    result: NarrativeAnalysis
  } | null>(null)
  const [analyzing, setAnalyzing] = useState<string | null>(null)

  const fetchNarratives = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await infoopsClient.get<NarrativeThreat[]>('/narratives')
      setNarratives(resp.data)
    } catch {
      setError('Failed to load narrative threats')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchNarratives() }, [fetchNarratives])

  const handleAnalyze = async (narrative: NarrativeThreat) => {
    setAnalyzing(narrative.id)
    try {
      const resp = await infoopsClient.post<NarrativeAnalysis>(`/narratives/${narrative.id}/analyze`)
      setAnalysisState({ narrative, result: resp.data })
    } catch {
      // silently ignore in demo
    } finally {
      setAnalyzing(null)
    }
  }

  if (loading) return <p className="text-gray-400 text-sm">Loading…</p>
  if (error) return <p className="text-red-400 text-sm">{error}</p>

  return (
    <>
      {showAdd && (
        <AddNarrativeModal
          onClose={() => setShowAdd(false)}
          onCreated={(n) => setNarratives((prev) => [n, ...prev])}
        />
      )}
      {analysisState && (
        <AnalysisModal
          narrative={analysisState.narrative}
          analysis={analysisState.result}
          onClose={() => setAnalysisState(null)}
        />
      )}

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold text-gray-300">Narrative Threats ({narratives.length})</h2>
        <button
          onClick={() => setShowAdd(true)}
          className="bg-sky-700 hover:bg-sky-600 text-white text-xs px-3 py-1.5 rounded"
        >
          + Add Narrative
        </button>
      </div>

      {narratives.length === 0 && (
        <p className="text-gray-500 text-sm">No narrative threats found.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {narratives.map((n) => {
          const isExpanded = expanded === n.id
          return (
            <div
              key={n.id}
              className="bg-gray-900 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
            >
              {/* Header */}
              <div
                className="cursor-pointer"
                onClick={() => setExpanded(isExpanded ? null : n.id)}
              >
                <div className="flex justify-between items-start gap-2 mb-2">
                  <h3 className="text-sm font-semibold text-white leading-tight">{n.title}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded font-semibold flex-shrink-0 ${THREAT_LEVEL_COLORS[n.threat_level]}`}>
                    {n.threat_level}
                  </span>
                </div>

                <div className="flex items-center gap-2 mb-2">
                  {n.origin_country && (
                    <span className="text-xs text-gray-400 font-mono">{n.origin_country}</span>
                  )}
                  <span className={`text-xs px-1.5 py-0.5 rounded ${NARRATIVE_STATUS_COLORS[n.status]}`}>
                    {n.status}
                  </span>
                </div>

                {/* Spread velocity bar */}
                <div className="mb-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-0.5">
                    <span>Spread Velocity</span>
                    <span>{(n.spread_velocity * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-sky-500 rounded-full"
                      style={{ width: `${n.spread_velocity * 100}%` }}
                    />
                  </div>
                </div>

                <p className="text-xs text-gray-400 mb-2">
                  Reach: {n.reach_estimate.toLocaleString()}
                </p>

                {/* Platform tags */}
                <div className="flex flex-wrap gap-1">
                  {n.platforms.map((p) => (
                    <span key={p} className="text-xs bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded" title={p}>
                      {PLATFORM_ICONS[p] ?? '❓'} {p.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>

              {/* Expanded details */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  {n.key_claims.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1 font-semibold uppercase tracking-wide">Key Claims</p>
                      <ul className="space-y-0.5">
                        {n.key_claims.map((c, i) => (
                          <li key={i} className="text-xs text-gray-300 flex gap-1.5">
                            <span className="text-red-500">•</span>{c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {n.counter_narratives.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1 font-semibold uppercase tracking-wide">Counter Narratives</p>
                      <ul className="space-y-0.5">
                        {n.counter_narratives.map((c, i) => (
                          <li key={i} className="text-xs text-gray-300 flex gap-1.5">
                            <span className="text-green-500">✓</span>{c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <button
                    onClick={() => handleAnalyze(n)}
                    disabled={analyzing === n.id}
                    className="w-full bg-indigo-800 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs py-1.5 rounded mt-1"
                  >
                    {analyzing === n.id ? 'Analyzing…' : '🔬 Analyze'}
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Add Campaign Modal
// ---------------------------------------------------------------------------

interface AddCampaignModalProps {
  onClose: () => void
  onCreated: (c: InfluenceCampaign) => void
}

function AddCampaignModal({ onClose, onCreated }: AddCampaignModalProps) {
  const [name, setName] = useState('')
  const [actor, setActor] = useState('')
  const [sponsoringState, setSponsoringState] = useState('')
  const [confidence, setConfidence] = useState<AttributionConfidence>('UNATTRIBUTED')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!name.trim()) { setError('Name is required'); return }
    setLoading(true)
    setError(null)
    try {
      const body: CreateInfluenceCampaignRequest = {
        name: name.trim(),
        attributed_actor: actor.trim() || null,
        sponsoring_state: sponsoringState.trim() || null,
        attribution_confidence: confidence,
      }
      const resp = await infoopsClient.post<InfluenceCampaign>('/campaigns', body)
      onCreated(resp.data)
      onClose()
    } catch {
      setError('Failed to create campaign')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-semibold text-white">Add Influence Campaign</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">✕</button>
        </div>
        {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Name *</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Campaign name"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Attributed Actor</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={actor}
              onChange={(e) => setActor(e.target.value)}
              placeholder="e.g. GRU"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sponsoring State (ISO-3)</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={sponsoringState}
              onChange={(e) => setSponsoringState(e.target.value)}
              placeholder="e.g. RUS"
              maxLength={3}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Attribution Confidence</label>
            <select
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
              value={confidence}
              onChange={(e) => setConfidence(e.target.value as AttributionConfidence)}
            >
              {(['HIGH', 'MEDIUM', 'LOW', 'UNATTRIBUTED'] as AttributionConfidence[]).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex gap-3 mt-5">
          <button onClick={onClose} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white text-sm py-2 rounded">Cancel</button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="flex-1 bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-sm py-2 rounded"
          >
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Campaigns Tab
// ---------------------------------------------------------------------------

function CampaignsTab() {
  const [campaigns, setCampaigns] = useState<InfluenceCampaign[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAdd, setShowAdd] = useState(false)

  useEffect(() => {
    infoopsClient.get<InfluenceCampaign[]>('/campaigns')
      .then((r) => setCampaigns(r.data))
      .catch(() => setError('Failed to load campaigns'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-gray-400 text-sm">Loading…</p>
  if (error) return <p className="text-red-400 text-sm">{error}</p>

  return (
    <>
      {showAdd && (
        <AddCampaignModal
          onClose={() => setShowAdd(false)}
          onCreated={(c) => setCampaigns((prev) => [c, ...prev])}
        />
      )}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold text-gray-300">Influence Campaigns ({campaigns.length})</h2>
        <button
          onClick={() => setShowAdd(true)}
          className="bg-sky-700 hover:bg-sky-600 text-white text-xs px-3 py-1.5 rounded"
        >
          + Add Campaign
        </button>
      </div>
      {campaigns.length === 0 && <p className="text-gray-500 text-sm">No campaigns found.</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-700">
              <th className="pb-2 pr-4">Name</th>
              <th className="pb-2 pr-4">Actor</th>
              <th className="pb-2 pr-4">Sponsoring State</th>
              <th className="pb-2 pr-4">Confidence</th>
              <th className="pb-2 pr-4">Platforms</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {campaigns.map((c) => (
              <tr key={c.id} className="hover:bg-gray-900">
                <td className="py-2 pr-4 text-white font-medium">{c.name}</td>
                <td className="py-2 pr-4 text-gray-300">{c.attributed_actor ?? '—'}</td>
                <td className="py-2 pr-4 font-mono text-gray-300">{c.sponsoring_state ?? '—'}</td>
                <td className="py-2 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded font-semibold ${CONFIDENCE_COLORS[c.attribution_confidence]}`}>
                    {c.attribution_confidence}
                  </span>
                </td>
                <td className="py-2 pr-4">
                  <div className="flex flex-wrap gap-1">
                    {c.platforms.slice(0, 3).map((p) => (
                      <span key={p} className="text-xs" title={p}>{PLATFORM_ICONS[p] ?? '❓'}</span>
                    ))}
                    {c.platforms.length > 3 && (
                      <span className="text-xs text-gray-500">+{c.platforms.length - 3}</span>
                    )}
                  </div>
                </td>
                <td className="py-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${CAMPAIGN_STATUS_COLORS[c.status]}`}>
                    {c.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Indicators Tab
// ---------------------------------------------------------------------------

const INDICATOR_TYPE_COLORS: Partial<Record<IndicatorType, string>> = {
  BOT_NETWORK: 'bg-red-900 text-red-200',
  DEEPFAKE_CONTENT: 'bg-purple-900 text-purple-200',
  COORDINATED_INAUTHENTIC_BEHAVIOR: 'bg-orange-900 text-orange-200',
  FAKE_ACCOUNT_NETWORK: 'bg-yellow-900 text-yellow-200',
  ASTROTURFING: 'bg-pink-900 text-pink-200',
  HASHTAG_HIJACKING: 'bg-blue-900 text-blue-200',
  CONTENT_FARM: 'bg-gray-700 text-gray-300',
  NARRATIVE_AMPLIFICATION: 'bg-indigo-900 text-indigo-200',
}

function IndicatorsTab() {
  const [indicators, setIndicators] = useState<DisinformationIndicator[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    infoopsClient.get<DisinformationIndicator[]>('/indicators')
      .then((r) => setIndicators(r.data))
      .catch(() => setError('Failed to load indicators'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-gray-400 text-sm">Loading…</p>
  if (error) return <p className="text-red-400 text-sm">{error}</p>

  return (
    <>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold text-gray-300">Disinformation Indicators ({indicators.length})</h2>
      </div>
      {indicators.length === 0 && <p className="text-gray-500 text-sm">No indicators found.</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-700">
              <th className="pb-2 pr-4">Type</th>
              <th className="pb-2 pr-4">Title</th>
              <th className="pb-2 pr-4">Platform</th>
              <th className="pb-2 pr-4">Detected</th>
              <th className="pb-2 pr-4">Confidence</th>
              <th className="pb-2">Verified</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {indicators.map((ind) => (
              <tr key={ind.id} className="hover:bg-gray-900">
                <td className="py-2 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded font-semibold ${INDICATOR_TYPE_COLORS[ind.indicator_type] ?? 'bg-gray-700 text-gray-300'}`}>
                    {ind.indicator_type.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="py-2 pr-4 text-white">{ind.title}</td>
                <td className="py-2 pr-4 text-gray-300">{PLATFORM_ICONS[ind.platform]} {ind.platform.replace(/_/g, ' ')}</td>
                <td className="py-2 pr-4 text-gray-400 text-xs">{new Date(ind.detected_at).toLocaleDateString()}</td>
                <td className="py-2 pr-4">
                  <div className="flex items-center gap-1.5">
                    <div className="h-1.5 w-16 bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-sky-500 rounded-full" style={{ width: `${ind.confidence_score * 100}%` }} />
                    </div>
                    <span className="text-xs text-gray-400">{(ind.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="py-2">
                  <span className={`text-xs ${ind.is_verified ? 'text-green-400' : 'text-gray-600'}`}>
                    {ind.is_verified ? '✓ Yes' : '✗ No'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Attribution Tab
// ---------------------------------------------------------------------------

function AttributionTab() {
  const [assessments, setAssessments] = useState<AttributionAssessment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAdd, setShowAdd] = useState(false)
  const [subject, setSubject] = useState('')
  const [attributedTo, setAttributedTo] = useState('')
  const [confidence, setConfidence] = useState<AttributionConfidence>('LOW')
  const [evidenceSummary, setEvidenceSummary] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [addLoading, setAddLoading] = useState(false)

  useEffect(() => {
    infoopsClient.get<AttributionAssessment[]>('/attribution')
      .then((r) => setAssessments(r.data))
      .catch(() => setError('Failed to load attribution assessments'))
      .finally(() => setLoading(false))
  }, [])

  const handleCreate = async () => {
    if (!subject.trim() || !attributedTo.trim()) { setAddError('Subject and Attributed To are required'); return }
    setAddLoading(true)
    setAddError(null)
    try {
      const body: CreateAttributionAssessmentRequest = {
        subject: subject.trim(),
        attributed_to: attributedTo.trim(),
        confidence,
        evidence_summary: evidenceSummary.trim() || null,
      }
      const resp = await infoopsClient.post<AttributionAssessment>('/attribution', body)
      setAssessments((prev) => [resp.data, ...prev])
      setShowAdd(false)
      setSubject('')
      setAttributedTo('')
      setEvidenceSummary('')
    } catch {
      setAddError('Failed to create assessment')
    } finally {
      setAddLoading(false)
    }
  }

  if (loading) return <p className="text-gray-400 text-sm">Loading…</p>
  if (error) return <p className="text-red-400 text-sm">{error}</p>

  return (
    <>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold text-gray-300">Attribution Assessments ({assessments.length})</h2>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="bg-sky-700 hover:bg-sky-600 text-white text-xs px-3 py-1.5 rounded"
        >
          {showAdd ? 'Cancel' : '+ Add Assessment'}
        </button>
      </div>

      {showAdd && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 mb-4">
          {addError && <p className="text-red-400 text-sm mb-2">{addError}</p>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Subject *</label>
              <input
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Actor being attributed"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Attributed To *</label>
              <input
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
                value={attributedTo}
                onChange={(e) => setAttributedTo(e.target.value)}
                placeholder="State / organization"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Confidence</label>
              <select
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
                value={confidence}
                onChange={(e) => setConfidence(e.target.value as AttributionConfidence)}
              >
                {(['HIGH', 'MEDIUM', 'LOW', 'UNATTRIBUTED'] as AttributionConfidence[]).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Evidence Summary</label>
              <input
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
                value={evidenceSummary}
                onChange={(e) => setEvidenceSummary(e.target.value)}
                placeholder="Brief evidence summary"
              />
            </div>
          </div>
          <button
            onClick={handleCreate}
            disabled={addLoading}
            className="bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-xs px-4 py-1.5 rounded"
          >
            {addLoading ? 'Saving…' : 'Save Assessment'}
          </button>
        </div>
      )}

      {assessments.length === 0 && <p className="text-gray-500 text-sm">No attribution assessments found.</p>}
      <div className="space-y-3">
        {assessments.map((a) => (
          <div key={a.id} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-start gap-2 mb-1">
              <div>
                <span className="text-sm font-semibold text-white">{a.subject}</span>
                <span className="text-sm text-gray-500 mx-2">→</span>
                <span className="text-sm text-sky-400">{a.attributed_to}</span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded font-semibold flex-shrink-0 ${CONFIDENCE_COLORS[a.confidence]}`}>
                {a.confidence}
              </span>
            </div>
            {a.evidence_summary && (
              <p className="text-xs text-gray-400 mt-1">{a.evidence_summary}</p>
            )}
            <p className="text-xs text-gray-600 mt-1">{new Date(a.created_at).toLocaleDateString()}</p>
          </div>
        ))}
      </div>
    </>
  )
}

// ---------------------------------------------------------------------------
// Main InfoOpsPage
// ---------------------------------------------------------------------------

export default function InfoOpsPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [activeTab, setActiveTab] = useState<Tab>('narratives')

  const tabs: { id: Tab; label: string }[] = [
    { id: 'narratives', label: 'Narrative Threats' },
    { id: 'campaigns', label: 'Influence Campaigns' },
    { id: 'indicators', label: 'Indicators' },
    { id: 'attribution', label: 'Attribution' },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <div className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-xl font-bold text-white">📡 Information Operations</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Track influence campaigns, disinformation indicators, and narrative threats
          </p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="bg-gray-900 border-b border-gray-700 px-6">
        <div className="max-w-7xl mx-auto flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 px-6 py-6 max-w-7xl mx-auto w-full">
        {activeTab === 'narratives' && <NarrativesTab />}
        {activeTab === 'campaigns' && <CampaignsTab />}
        {activeTab === 'indicators' && <IndicatorsTab />}
        {activeTab === 'attribution' && <AttributionTab />}
      </div>

      <ClassificationBanner level={classification} />
    </div>
  )
}

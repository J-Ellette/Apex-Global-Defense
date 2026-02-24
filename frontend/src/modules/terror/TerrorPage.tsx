import { useEffect, useState } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { terrorApi } from '../../shared/api/endpoints'
import type {
  AgencyEntry,
  AgencyRole,
  AgencyType,
  AttackTypeEntry,
  CreateResponsePlanRequest,
  CreateSiteRequest,
  CreateThreatScenarioRequest,
  CrowdDensity,
  ResponsePlan,
  SiteType,
  SiteVulnerabilityAnalysis,
  TerrorSite,
  ThreatLevel,
  ThreatScenario,
} from '../../shared/api/types'

// ---------------------------------------------------------------------------
// Constants & helpers
// ---------------------------------------------------------------------------

const SITE_TYPE_LABELS: Record<SiteType, string> = {
  TRANSPORT_HUB: 'Transport Hub',
  STADIUM: 'Stadium / Arena',
  GOVERNMENT_BUILDING: 'Government Building',
  HOTEL: 'Hotel',
  MARKET: 'Market',
  HOUSE_OF_WORSHIP: 'House of Worship',
  SCHOOL: 'School',
  HOSPITAL: 'Hospital',
  EMBASSY: 'Embassy',
  CRITICAL_INFRASTRUCTURE: 'Critical Infrastructure',
  FINANCIAL_CENTER: 'Financial Center',
  MILITARY_BASE: 'Military Base',
  ENTERTAINMENT_VENUE: 'Entertainment Venue',
  SHOPPING_CENTER: 'Shopping Center',
}

const SITE_TYPE_ICONS: Record<SiteType, string> = {
  TRANSPORT_HUB: '🚉',
  STADIUM: '🏟️',
  GOVERNMENT_BUILDING: '🏛️',
  HOTEL: '🏨',
  MARKET: '🏪',
  HOUSE_OF_WORSHIP: '⛪',
  SCHOOL: '🏫',
  HOSPITAL: '🏥',
  EMBASSY: '🏢',
  CRITICAL_INFRASTRUCTURE: '⚡',
  FINANCIAL_CENTER: '🏦',
  MILITARY_BASE: '🪖',
  ENTERTAINMENT_VENUE: '🎭',
  SHOPPING_CENTER: '🛍️',
}

const THREAT_LEVEL_COLORS: Record<ThreatLevel, string> = {
  LOW: 'bg-green-900 text-green-200',
  ELEVATED: 'bg-yellow-900 text-yellow-200',
  HIGH: 'bg-orange-900 text-orange-200',
  CRITICAL: 'bg-red-900 text-red-200',
  IMMINENT: 'bg-red-700 text-white font-bold',
}

const AGENCY_TYPE_ICONS: Record<AgencyType, string> = {
  POLICE: '👮',
  FIRE: '🚒',
  MEDICAL: '🚑',
  MILITARY: '🪖',
  INTELLIGENCE: '🔍',
  FEDERAL: '🏛️',
  STATE: '🏴',
  LOCAL: '🏙️',
  INTERNATIONAL: '🌐',
  PRIVATE: '🔒',
}

function vulnScoreColor(score: number): string {
  if (score >= 7) return 'text-red-400'
  if (score >= 4) return 'text-yellow-400'
  return 'text-green-400'
}

function vulnBarColor(score: number): string {
  if (score >= 7) return 'bg-red-500'
  if (score >= 4) return 'bg-yellow-500'
  return 'bg-green-500'
}

function securityBar(value: number, label: string) {
  const pct = Math.round(value * 100)
  const color = value >= 0.7 ? 'bg-green-500' : value >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-36 text-gray-400 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-gray-300 w-8 text-right">{pct}%</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sites Tab
// ---------------------------------------------------------------------------

function SitesTab() {
  const [sites, setSites] = useState<TerrorSite[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedSite, setSelectedSite] = useState<TerrorSite | null>(null)

  const loadSites = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await terrorApi.listSites()
      setSites(data)
    } catch {
      setError('Failed to load sites. Ensure terror-svc is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadSites() }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Target Site Vulnerability Assessment</h2>
          <p className="text-sm text-gray-400">
            Map and assess terror target sites. Vulnerability score (1–10) is computed from security dimensions.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg"
        >
          + Add Site
        </button>
      </div>

      {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-3">{error}</div>}
      {loading && <div className="text-gray-400 text-sm">Loading sites…</div>}

      {!loading && sites.length === 0 && !error && (
        <div className="text-gray-500 text-sm text-center py-12 border border-dashed border-gray-700 rounded-lg">
          No sites mapped. Click <strong>+ Add Site</strong> to begin vulnerability assessment.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sites.map((site) => (
          <div
            key={site.id}
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 cursor-pointer hover:border-red-700 transition-colors"
            onClick={() => setSelectedSite(site)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{SITE_TYPE_ICONS[site.site_type]}</span>
                <div>
                  <h3 className="text-white font-semibold text-sm">{site.name}</h3>
                  <p className="text-xs text-gray-400">{SITE_TYPE_LABELS[site.site_type]}</p>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-2xl font-bold ${vulnScoreColor(site.vulnerability_score)}`}>
                  {site.vulnerability_score.toFixed(1)}
                </div>
                <div className="text-xs text-gray-500">vuln score</div>
              </div>
            </div>

            <div className="mb-3">
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div
                    className={`${vulnBarColor(site.vulnerability_score)} h-2 rounded-full`}
                    style={{ width: `${site.vulnerability_score * 10}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-1">
              {securityBar(site.physical_security, 'Physical security')}
              {securityBar(site.access_control, 'Access control')}
              {securityBar(site.surveillance, 'Surveillance')}
              {securityBar(site.emergency_response, 'Emergency response')}
            </div>

            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300">
                Crowd: {site.crowd_density}
              </span>
              {site.country_code && (
                <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300">
                  {site.country_code}
                </span>
              )}
              {site.population_capacity > 0 && (
                <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300">
                  Cap: {site.population_capacity.toLocaleString()}
                </span>
              )}
              <span className={`text-xs px-2 py-0.5 rounded ${
                site.status === 'HARDENED' ? 'bg-green-900 text-green-200' :
                site.status === 'UNDER_REVIEW' ? 'bg-yellow-900 text-yellow-200' :
                site.status === 'CLOSED' ? 'bg-gray-700 text-gray-400' :
                'bg-blue-900 text-blue-200'
              }`}>
                {site.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {showCreateModal && (
        <CreateSiteModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); loadSites() }}
        />
      )}

      {selectedSite && (
        <SiteDetailModal
          site={selectedSite}
          onClose={() => setSelectedSite(null)}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Create Site Modal
// ---------------------------------------------------------------------------

function CreateSiteModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState<CreateSiteRequest>({
    name: '',
    site_type: 'TRANSPORT_HUB',
    crowd_density: 'MEDIUM',
    physical_security: 0.5,
    access_control: 0.5,
    surveillance: 0.5,
    emergency_response: 0.5,
    population_capacity: 0,
    status: 'ACTIVE',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!form.name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError(null)
    try {
      await terrorApi.createSite(form)
      onCreated()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Failed to create site')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-xl max-h-[90vh] overflow-y-auto p-6 space-y-4">
        <h2 className="text-white font-bold text-lg">Add Target Site</h2>

        {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-2">{error}</div>}

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Site Name *</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Central Station Main Hall"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Site Type</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.site_type}
              onChange={(e) => setForm({ ...form, site_type: e.target.value as SiteType })}
            >
              {(Object.entries(SITE_TYPE_LABELS) as [SiteType, string][]).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Crowd Density</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.crowd_density}
              onChange={(e) => setForm({ ...form, crowd_density: e.target.value as CrowdDensity })}
            >
              {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as CrowdDensity[]).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Country Code</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.country_code ?? ''}
              onChange={(e) => setForm({ ...form, country_code: e.target.value || undefined })}
              placeholder="e.g. FR"
              maxLength={2}
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Population Capacity</label>
            <input
              type="number"
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.population_capacity ?? 0}
              onChange={(e) => setForm({ ...form, population_capacity: parseInt(e.target.value) || 0 })}
              min={0}
            />
          </div>
        </div>

        <div>
          <h3 className="text-sm text-gray-300 font-medium mb-2">Security Dimensions (0 = none, 1 = excellent)</h3>
          <div className="space-y-3">
            {([
              ['physical_security', 'Physical Security'],
              ['access_control', 'Access Control'],
              ['surveillance', 'Surveillance'],
              ['emergency_response', 'Emergency Response'],
            ] as [keyof CreateSiteRequest, string][]).map(([field, label]) => (
              <div key={field} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-36 shrink-0">{label}</span>
                <input
                  type="range"
                  min={0} max={1} step={0.05}
                  className="flex-1"
                  value={(form[field] as number) ?? 0.5}
                  onChange={(e) => setForm({ ...form, [field]: parseFloat(e.target.value) })}
                />
                <span className="text-xs text-gray-300 w-8 text-right">
                  {Math.round(((form[field] as number) ?? 0.5) * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Create Site'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Site Detail Modal (vulnerability analysis)
// ---------------------------------------------------------------------------

function SiteDetailModal({ site, onClose }: { site: TerrorSite; onClose: () => void }) {
  const [analysis, setAnalysis] = useState<SiteVulnerabilityAnalysis | null>(null)
  const [loading, setLoading] = useState(false)

  const loadAnalysis = async () => {
    setLoading(true)
    try {
      const data = await terrorApi.analyzeSite(site.id)
      setAnalysis(data)
    } catch {
      // Analysis load failure is non-critical
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // loadAnalysis is stable for the lifetime of this site.id; no additional deps needed
    loadAnalysis()
  }, [site.id]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{SITE_TYPE_ICONS[site.site_type]}</span>
            <div>
              <h2 className="text-white font-bold text-lg">{site.name}</h2>
              <p className="text-sm text-gray-400">{SITE_TYPE_LABELS[site.site_type]}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl">✕</button>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-800 rounded-lg p-3">
            <div className={`text-3xl font-bold ${vulnScoreColor(site.vulnerability_score)}`}>
              {site.vulnerability_score.toFixed(1)}<span className="text-base text-gray-400">/10</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">Vulnerability Score</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 space-y-1">
            {securityBar(site.physical_security, 'Physical security')}
            {securityBar(site.access_control, 'Access control')}
            {securityBar(site.surveillance, 'Surveillance')}
            {securityBar(site.emergency_response, 'Emerg. response')}
          </div>
        </div>

        {loading && <div className="text-gray-400 text-sm">Running vulnerability analysis…</div>}

        {analysis && (
          <>
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-2">Top Attack Risks</h3>
              <div className="space-y-2">
                {analysis.top_attack_risks.map((risk) => (
                  <div key={risk.attack_type_id} className="bg-gray-800 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white text-sm font-medium">{risk.attack_type_label}</span>
                      <span className={`text-sm font-bold ${vulnScoreColor(risk.risk_score)}`}>
                        {risk.risk_score.toFixed(1)}/10
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">{risk.rationale}</p>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-2">Security Recommendations</h3>
              <div className="space-y-2">
                {analysis.recommendations.map((rec, i) => (
                  <div key={i} className="flex gap-2 text-sm">
                    <span className="text-red-400 mt-0.5 shrink-0">•</span>
                    <p className="text-gray-300">{rec}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-3">
              <p className="text-sm text-gray-300">{analysis.analysis_summary}</p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Threat Scenarios Tab
// ---------------------------------------------------------------------------

function ThreatScenariosTab() {
  const [attackTypes, setAttackTypes] = useState<AttackTypeEntry[]>([])
  const [scenarios, setScenarios] = useState<ThreatScenario[]>([])
  const [sites, setSites] = useState<TerrorSite[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [expandedType, setExpandedType] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [typesData, scenariosData, sitesData] = await Promise.all([
        terrorApi.listAttackTypes(),
        terrorApi.listThreatScenarios(),
        terrorApi.listSites(),
      ])
      setAttackTypes(typesData)
      setScenarios(scenariosData)
      setSites(sitesData)
    } catch {
      setError('Failed to load data. Ensure terror-svc is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const siteMap = Object.fromEntries(sites.map((s) => [s.id, s]))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Threat Scenarios & Attack Type Catalog</h2>
          <p className="text-sm text-gray-400">Log threat scenarios for sites and reference the attack type catalog.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={sites.length === 0}
          className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg disabled:opacity-50"
          title={sites.length === 0 ? 'Add a site first' : undefined}
        >
          + Log Threat Scenario
        </button>
      </div>

      {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-3">{error}</div>}
      {loading && <div className="text-gray-400 text-sm">Loading…</div>}

      {/* Active threat scenarios */}
      {scenarios.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Active Threat Scenarios</h3>
          <div className="space-y-2">
            {scenarios.map((ts) => {
              const site = siteMap[ts.site_id]
              const attackType = attackTypes.find((a) => a.id === ts.attack_type_id)
              return (
                <div key={ts.id} className="bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded ${THREAT_LEVEL_COLORS[ts.threat_level]}`}>
                        {ts.threat_level}
                      </span>
                      <span className="text-white text-sm font-medium">
                        {attackType?.label ?? ts.attack_type_id}
                      </span>
                      <span className="text-gray-400 text-xs">at</span>
                      <span className="text-gray-300 text-sm">{site?.name ?? ts.site_id}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Probability: {Math.round(ts.probability * 100)}% ·
                      Casualties: {ts.estimated_killed_low}–{ts.estimated_killed_high} KIA /
                      {ts.estimated_wounded_low}–{ts.estimated_wounded_high} WIA
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Attack type catalog */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Attack Type Catalog</h3>
        <div className="space-y-3">
          {attackTypes.map((at) => (
            <div
              key={at.id}
              className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden"
            >
              <button
                className="w-full text-left p-4 flex items-center justify-between hover:bg-gray-800 transition-colors"
                onClick={() => setExpandedType(expandedType === at.id ? null : at.id)}
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: at.color_hex }}
                  />
                  <div>
                    <div className="text-white font-medium text-sm">{at.label}</div>
                    <div className="text-xs text-gray-500">{at.category} · {at.id}</div>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-right text-xs text-gray-400">
                  <div>
                    <div className="text-red-400 font-semibold">
                      {at.avg_killed_low}–{at.avg_killed_high} KIA
                    </div>
                    <div>{at.avg_wounded_low}–{at.avg_wounded_high} WIA</div>
                  </div>
                  <span>{expandedType === at.id ? '▲' : '▼'}</span>
                </div>
              </button>

              {expandedType === at.id && (
                <div className="px-4 pb-4 border-t border-gray-800 pt-3 space-y-3">
                  <p className="text-sm text-gray-300">{at.description}</p>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <h4 className="text-gray-400 font-medium mb-1">Typical Perpetrators</h4>
                      <ul className="space-y-0.5">
                        {at.typical_perpetrators.map((p) => (
                          <li key={p} className="text-gray-300">• {p}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="text-gray-400 font-medium mb-1">Typical Targets</h4>
                      <ul className="space-y-0.5">
                        {at.typical_targets.map((t) => (
                          <li key={t} className="text-gray-300">• {t}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs text-gray-400 font-medium mb-1">Detection Window</h4>
                    <p className="text-xs text-gray-300">{at.detection_window}</p>
                  </div>

                  <div>
                    <h4 className="text-xs text-gray-400 font-medium mb-1">Threat Indicators</h4>
                    <p className="text-xs text-orange-300">{at.threat_indicator}</p>
                  </div>

                  <div>
                    <h4 className="text-xs text-gray-400 font-medium mb-1">Countermeasures</h4>
                    <ul className="space-y-0.5">
                      {at.countermeasures.map((c) => (
                        <li key={c} className="text-xs text-green-300">✓ {c}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {showCreateModal && (
        <CreateThreatScenarioModal
          sites={sites}
          attackTypes={attackTypes}
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); loadData() }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Create Threat Scenario Modal
// ---------------------------------------------------------------------------

function CreateThreatScenarioModal({
  sites,
  attackTypes,
  onClose,
  onCreated,
}: {
  sites: TerrorSite[]
  attackTypes: AttackTypeEntry[]
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState<CreateThreatScenarioRequest>({
    site_id: sites[0]?.id ?? '',
    attack_type_id: attackTypes[0]?.id ?? 'VRAM',
    threat_level: 'LOW',
    probability: 0.1,
    estimated_killed_low: 0,
    estimated_killed_high: 5,
    estimated_wounded_low: 0,
    estimated_wounded_high: 20,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    setSaving(true)
    setError(null)
    try {
      await terrorApi.createThreatScenario(form)
      onCreated()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Failed to create threat scenario')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6 space-y-4">
        <h2 className="text-white font-bold text-lg">Log Threat Scenario</h2>

        {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-2">{error}</div>}

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Target Site *</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.site_id}
              onChange={(e) => setForm({ ...form, site_id: e.target.value })}
            >
              {sites.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Attack Type *</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.attack_type_id}
              onChange={(e) => setForm({ ...form, attack_type_id: e.target.value })}
            >
              {attackTypes.map((a) => (
                <option key={a.id} value={a.id}>{a.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Threat Level</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.threat_level}
              onChange={(e) => setForm({ ...form, threat_level: e.target.value as ThreatLevel })}
            >
              {(['LOW', 'ELEVATED', 'HIGH', 'CRITICAL', 'IMMINENT'] as ThreatLevel[]).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Probability: {Math.round((form.probability ?? 0.1) * 100)}%
            </label>
            <input
              type="range"
              min={0} max={1} step={0.05}
              className="w-full"
              value={form.probability ?? 0.1}
              onChange={(e) => setForm({ ...form, probability: parseFloat(e.target.value) })}
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Killed Range</label>
            <div className="flex gap-2">
              <input
                type="number"
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                value={form.estimated_killed_low}
                onChange={(e) => setForm({ ...form, estimated_killed_low: parseInt(e.target.value) || 0 })}
                placeholder="min"
                min={0}
              />
              <input
                type="number"
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                value={form.estimated_killed_high}
                onChange={(e) => setForm({ ...form, estimated_killed_high: parseInt(e.target.value) || 0 })}
                placeholder="max"
                min={0}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Wounded Range</label>
            <div className="flex gap-2">
              <input
                type="number"
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                value={form.estimated_wounded_low}
                onChange={(e) => setForm({ ...form, estimated_wounded_low: parseInt(e.target.value) || 0 })}
                placeholder="min"
                min={0}
              />
              <input
                type="number"
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                value={form.estimated_wounded_high}
                onChange={(e) => setForm({ ...form, estimated_wounded_high: parseInt(e.target.value) || 0 })}
                placeholder="max"
                min={0}
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Log Scenario'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Response Planning Tab
// ---------------------------------------------------------------------------

function ResponsePlanningTab() {
  const [plans, setPlans] = useState<ResponsePlan[]>([])
  const [sites, setSites] = useState<TerrorSite[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [expandedPlan, setExpandedPlan] = useState<string | null>(null)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [plansData, sitesData] = await Promise.all([
        terrorApi.listResponsePlans(),
        terrorApi.listSites(),
      ])
      setPlans(plansData)
      setSites(sitesData)
    } catch {
      setError('Failed to load response plans. Ensure terror-svc is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const siteMap = Object.fromEntries(sites.map((s) => [s.id, s]))

  const agencyRoleColor: Record<AgencyRole, string> = {
    PRIMARY: 'bg-red-900 text-red-200',
    SUPPORTING: 'bg-blue-900 text-blue-200',
    NOTIFIED: 'bg-gray-700 text-gray-300',
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Multi-Agency Response Planning</h2>
          <p className="text-sm text-gray-400">
            Define coordinated response plans with agency assignments, evacuation routes, and operational phases.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={sites.length === 0}
          className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg disabled:opacity-50"
          title={sites.length === 0 ? 'Add a site first' : undefined}
        >
          + New Response Plan
        </button>
      </div>

      {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-3">{error}</div>}
      {loading && <div className="text-gray-400 text-sm">Loading…</div>}

      {!loading && plans.length === 0 && !error && (
        <div className="text-gray-500 text-sm text-center py-12 border border-dashed border-gray-700 rounded-lg">
          No response plans created. Click <strong>+ New Response Plan</strong> to start coordination planning.
        </div>
      )}

      <div className="space-y-3">
        {plans.map((plan) => {
          const site = siteMap[plan.site_id]
          const primaryAgencies = plan.agencies.filter((a) => a.role === 'PRIMARY')
          return (
            <div
              key={plan.id}
              className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden"
            >
              <button
                className="w-full text-left p-4 flex items-center justify-between hover:bg-gray-800"
                onClick={() => setExpandedPlan(expandedPlan === plan.id ? null : plan.id)}
              >
                <div className="flex items-center gap-3">
                  <div>
                    <div className="text-white font-semibold text-sm">{plan.title}</div>
                    <div className="text-xs text-gray-400">
                      {site ? `${SITE_TYPE_ICONS[site.site_type]} ${site.name}` : plan.site_id}
                      {' · '}
                      {plan.agencies.length} agencies · ETA {plan.estimated_response_time_min} min
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    plan.status === 'ACTIVE' ? 'bg-green-900 text-green-200' :
                    plan.status === 'SUPERSEDED' ? 'bg-gray-700 text-gray-400' :
                    'bg-yellow-900 text-yellow-200'
                  }`}>
                    {plan.status}
                  </span>
                  <span className="text-gray-500">{expandedPlan === plan.id ? '▲' : '▼'}</span>
                </div>
              </button>

              {expandedPlan === plan.id && (
                <div className="px-4 pb-4 border-t border-gray-800 pt-3 space-y-3">
                  {plan.description && (
                    <p className="text-sm text-gray-300">{plan.description}</p>
                  )}

                  <div>
                    <h4 className="text-xs font-semibold text-gray-400 mb-2">Agency Assignments</h4>
                    <div className="space-y-1.5">
                      {plan.agencies.map((agency, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span>{AGENCY_TYPE_ICONS[agency.agency_type]}</span>
                          <span className="text-sm text-white">{agency.agency_name}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded ${agencyRoleColor[agency.role]}`}>
                            {agency.role}
                          </span>
                          {agency.contact && (
                            <span className="text-xs text-gray-400">{agency.contact}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {plan.evacuation_routes.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-gray-400 mb-1">Evacuation Routes</h4>
                      <ul className="space-y-0.5">
                        {plan.evacuation_routes.map((route, i) => (
                          <li key={i} className="text-xs text-gray-300">→ {route}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex gap-4 text-xs text-gray-400">
                    <div>Shelter capacity: <span className="text-white">{plan.shelter_capacity.toLocaleString()}</span></div>
                    <div>Response ETA: <span className="text-white">{plan.estimated_response_time_min} min</span></div>
                    <div>Lead agencies: <span className="text-white">{primaryAgencies.map((a) => a.agency_name).join(', ') || '—'}</span></div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {showCreateModal && (
        <CreateResponsePlanModal
          sites={sites}
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); loadData() }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Create Response Plan Modal
// ---------------------------------------------------------------------------

function CreateResponsePlanModal({
  sites,
  onClose,
  onCreated,
}: {
  sites: TerrorSite[]
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState<CreateResponsePlanRequest>({
    site_id: sites[0]?.id ?? '',
    title: '',
    agencies: [],
    evacuation_routes: [],
    shelter_capacity: 0,
    estimated_response_time_min: 10,
  })
  const [agencyName, setAgencyName] = useState('')
  const [agencyType, setAgencyType] = useState<AgencyType>('POLICE')
  const [agencyRole, setAgencyRole] = useState<AgencyRole>('PRIMARY')
  const [agencyContact, setAgencyContact] = useState('')
  const [routeInput, setRouteInput] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addAgency = () => {
    if (!agencyName.trim()) return
    setForm({
      ...form,
      agencies: [...(form.agencies ?? []), {
        agency_name: agencyName.trim(),
        agency_type: agencyType,
        role: agencyRole,
        contact: agencyContact.trim() || undefined,
      }],
    })
    setAgencyName('')
    setAgencyContact('')
  }

  const removeAgency = (i: number) => {
    setForm({ ...form, agencies: form.agencies?.filter((_, idx) => idx !== i) })
  }

  const addRoute = () => {
    if (!routeInput.trim()) return
    setForm({ ...form, evacuation_routes: [...(form.evacuation_routes ?? []), routeInput.trim()] })
    setRouteInput('')
  }

  const handleSubmit = async () => {
    if (!form.title.trim()) { setError('Title is required'); return }
    setSaving(true)
    setError(null)
    try {
      await terrorApi.createResponsePlan(form)
      onCreated()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Failed to create response plan')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-4">
        <h2 className="text-white font-bold text-lg">New Response Plan</h2>

        {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-2">{error}</div>}

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Plan Title *</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Station Alpha Active Threat Response"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Target Site *</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.site_id}
              onChange={(e) => setForm({ ...form, site_id: e.target.value })}
            >
              {sites.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Response ETA (min)</label>
            <input
              type="number"
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.estimated_response_time_min}
              onChange={(e) => setForm({ ...form, estimated_response_time_min: parseInt(e.target.value) || 10 })}
              min={1}
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Shelter Capacity</label>
            <input
              type="number"
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
              value={form.shelter_capacity}
              onChange={(e) => setForm({ ...form, shelter_capacity: parseInt(e.target.value) || 0 })}
              min={0}
            />
          </div>
        </div>

        {/* Agency assignment */}
        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-2">Agency Assignments</h3>
          <div className="flex gap-2 mb-2 flex-wrap">
            <input
              className="flex-1 min-w-32 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              value={agencyName}
              onChange={(e) => setAgencyName(e.target.value)}
              placeholder="Agency name"
              onKeyDown={(e) => e.key === 'Enter' && addAgency()}
            />
            <select
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              value={agencyType}
              onChange={(e) => setAgencyType(e.target.value as AgencyType)}
            >
              {(['POLICE','FIRE','MEDICAL','MILITARY','INTELLIGENCE','FEDERAL','STATE','LOCAL','INTERNATIONAL','PRIVATE'] as AgencyType[]).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
            <select
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              value={agencyRole}
              onChange={(e) => setAgencyRole(e.target.value as AgencyRole)}
            >
              {(['PRIMARY','SUPPORTING','NOTIFIED'] as AgencyRole[]).map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
            <input
              className="flex-1 min-w-24 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              value={agencyContact}
              onChange={(e) => setAgencyContact(e.target.value)}
              placeholder="Contact (optional)"
            />
            <button
              onClick={addAgency}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
            >
              Add
            </button>
          </div>
          {(form.agencies?.length ?? 0) > 0 && (
            <div className="space-y-1">
              {form.agencies?.map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-sm bg-gray-800 rounded px-2 py-1">
                  <span>{AGENCY_TYPE_ICONS[a.agency_type]}</span>
                  <span className="text-white">{a.agency_name}</span>
                  <span className="text-xs text-gray-400">{a.role}</span>
                  <button
                    onClick={() => removeAgency(i)}
                    className="ml-auto text-gray-500 hover:text-red-400 text-xs"
                  >✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Evacuation routes */}
        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-2">Evacuation Routes</h3>
          <div className="flex gap-2 mb-2">
            <input
              className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              value={routeInput}
              onChange={(e) => setRouteInput(e.target.value)}
              placeholder="e.g. North exit to King's Cross"
              onKeyDown={(e) => e.key === 'Enter' && addRoute()}
            />
            <button
              onClick={addRoute}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
            >
              Add
            </button>
          </div>
          {(form.evacuation_routes?.length ?? 0) > 0 && (
            <ul className="space-y-1">
              {form.evacuation_routes?.map((r, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                  <span>→ {r}</span>
                  <button
                    onClick={() => setForm({ ...form, evacuation_routes: form.evacuation_routes?.filter((_, idx) => idx !== i) })}
                    className="ml-auto text-gray-500 hover:text-red-400 text-xs"
                  >✕</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Create Plan'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main TerrorPage
// ---------------------------------------------------------------------------

type Tab = 'sites' | 'threats' | 'response'

export default function TerrorPage() {
  const user = useAuthStore((s) => s.user)
  const classification = user?.classification ?? 'UNCLASS'
  const [tab, setTab] = useState<Tab>('sites')

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'sites', label: 'Site Vulnerability', icon: '🎯' },
    { id: 'threats', label: 'Threat Scenarios', icon: '⚠️' },
    { id: 'response', label: 'Response Planning', icon: '🚨' },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 px-6 py-8 max-w-7xl mx-auto w-full">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Terror Response Planning</h1>
          <p className="text-sm text-gray-400 mt-1">
            Vulnerability assessment, threat scenario analysis, and multi-agency response coordination.
          </p>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-1 mb-6 border-b border-gray-800">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                tab === t.id
                  ? 'bg-gray-800 text-white border border-b-0 border-gray-700'
                  : 'text-gray-400 hover:text-white hover:bg-gray-900'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {tab === 'sites' && <SitesTab />}
        {tab === 'threats' && <ThreatScenariosTab />}
        {tab === 'response' && <ResponsePlanningTab />}
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

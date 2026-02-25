import { useEffect, useState, useCallback } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { econClient } from '../../shared/api/econClient'
import type {
  SanctionTarget,
  SanctionType,
  SanctionStatus,
  TradeRoute,
  TradeDependency,
  EconomicIndicator,
  EconomicImpactAssessment,
  ImpactSeverity,
  CreateSanctionTargetRequest,
  CreateTradeRouteRequest,
  RunImpactAssessmentRequest,
} from '../../shared/api/types/econ'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type Tab = 'sanctions' | 'trade' | 'indicators' | 'impact'

const SANCTION_TYPE_LABELS: Record<SanctionType, string> = {
  ASSET_FREEZE: 'Asset Freeze',
  TRADE_EMBARGO: 'Trade Embargo',
  TRAVEL_BAN: 'Travel Ban',
  FINANCIAL_CUTOFF: 'Financial Cutoff',
  TECH_TRANSFER: 'Tech Transfer Ban',
  SECTORAL: 'Sectoral',
  INDIVIDUAL: 'Individual',
  ARMS_EMBARGO: 'Arms Embargo',
}

const SANCTION_STATUS_COLORS: Record<SanctionStatus, string> = {
  ACTIVE: 'bg-red-900 text-red-200',
  SUSPENDED: 'bg-yellow-900 text-yellow-200',
  LIFTED: 'bg-gray-700 text-gray-300',
  PROPOSED: 'bg-blue-900 text-blue-200',
}

const DEPENDENCY_COLORS: Record<TradeDependency, string> = {
  CRITICAL: 'bg-red-900 text-red-200',
  HIGH: 'bg-orange-900 text-orange-200',
  MEDIUM: 'bg-yellow-900 text-yellow-200',
  LOW: 'bg-green-900 text-green-200',
  NONE: 'bg-gray-700 text-gray-300',
}

const SEVERITY_COLORS: Record<ImpactSeverity, string> = {
  CATASTROPHIC: 'text-red-400',
  SEVERE: 'text-orange-400',
  MODERATE: 'text-yellow-400',
  LIMITED: 'text-blue-400',
  NEGLIGIBLE: 'text-green-400',
}

// ---------------------------------------------------------------------------
// Add Sanction Modal
// ---------------------------------------------------------------------------

interface AddSanctionModalProps {
  onClose: () => void
  onCreated: (target: SanctionTarget) => void
}

function AddSanctionModal({ onClose, onCreated }: AddSanctionModalProps) {
  const [name, setName] = useState('')
  const [countryCode, setCountryCode] = useState('')
  const [targetType, setTargetType] = useState('COUNTRY')
  const [sanctionType, setSanctionType] = useState<SanctionType>('ASSET_FREEZE')
  const [status, setStatus] = useState<SanctionStatus>('ACTIVE')
  const [imposingParties, setImposingParties] = useState('')
  const [gdpImpact, setGdpImpact] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    setLoading(true)
    setError(null)
    try {
      const body: CreateSanctionTargetRequest = {
        name,
        country_code: countryCode.toUpperCase().slice(0, 3),
        target_type: targetType,
        sanction_type: sanctionType,
        status,
        imposing_parties: imposingParties.split(',').map((p) => p.trim()).filter(Boolean),
        annual_gdp_impact_pct: gdpImpact ? parseFloat(gdpImpact) : null,
        notes: notes || null,
      }
      const resp = await econClient.post<SanctionTarget>('/sanctions', body)
      onCreated(resp.data)
      onClose()
    } catch {
      setError('Failed to create sanction target')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-lg font-semibold text-white mb-4">Add Sanction Target</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              placeholder="e.g. Russia — Energy Sector"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Country Code *</label>
              <input
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value)}
                maxLength={3}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm font-mono uppercase"
                placeholder="RUS"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Target Type</label>
              <select
                value={targetType}
                onChange={(e) => setTargetType(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                <option value="COUNTRY">Country</option>
                <option value="ENTITY">Entity</option>
                <option value="INDIVIDUAL">Individual</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Sanction Type</label>
              <select
                value={sanctionType}
                onChange={(e) => setSanctionType(e.target.value as SanctionType)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                {Object.entries(SANCTION_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as SanctionStatus)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                <option value="ACTIVE">Active</option>
                <option value="PROPOSED">Proposed</option>
                <option value="SUSPENDED">Suspended</option>
                <option value="LIFTED">Lifted</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Imposing Parties (comma-separated)</label>
            <input
              value={imposingParties}
              onChange={(e) => setImposingParties(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              placeholder="USA, EU, UK"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Est. Annual GDP Impact (%)</label>
            <input
              value={gdpImpact}
              onChange={(e) => setGdpImpact(e.target.value)}
              type="number"
              step="0.1"
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              placeholder="2.5"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
            />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>
        <div className="flex justify-end gap-3 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={loading || !name || !countryCode}
            className="px-4 py-2 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded disabled:opacity-50 transition-colors"
          >
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sanctions Tab
// ---------------------------------------------------------------------------

function SanctionsTab() {
  const [sanctions, setSanctions] = useState<SanctionTarget[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await econClient.get<SanctionTarget[]>('/sanctions')
      setSanctions(resp.data)
    } catch {
      setError('Failed to load sanctions')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-400">{sanctions.length} sanction target{sanctions.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-3 py-1.5 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded transition-colors"
        >
          + Add Target
        </button>
      </div>

      {loading && <p className="text-gray-400 text-sm">Loading…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sanctions.map((s) => (
          <div key={s.id} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div>
                <h3 className="text-sm font-semibold text-white">{s.name}</h3>
                <span className="text-xs font-mono text-gray-400">{s.country_code}</span>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${SANCTION_STATUS_COLORS[s.status]}`}>
                  {s.status}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
                  {SANCTION_TYPE_LABELS[s.sanction_type]}
                </span>
              </div>
            </div>
            {s.annual_gdp_impact_pct != null && (
              <p className="text-xs text-orange-300 mb-1">
                GDP Impact: <strong>−{s.annual_gdp_impact_pct}%</strong>
              </p>
            )}
            {s.imposing_parties.length > 0 && (
              <p className="text-xs text-gray-400">
                Parties: {s.imposing_parties.join(', ')}
              </p>
            )}
            {s.notes && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{s.notes}</p>}
          </div>
        ))}
        {!loading && sanctions.length === 0 && (
          <p className="text-gray-500 text-sm col-span-2 py-8 text-center">
            No sanction targets. Click "Add Target" to create one.
          </p>
        )}
      </div>

      {showAddModal && (
        <AddSanctionModal
          onClose={() => setShowAddModal(false)}
          onCreated={(t) => { setSanctions((prev) => [t, ...prev]); setShowAddModal(false) }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Trade Routes Tab
// ---------------------------------------------------------------------------

function TradeRoutesTab() {
  const [routes, setRoutes] = useState<TradeRoute[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await econClient.get<TradeRoute[]>('/trade-routes')
      setRoutes(resp.data)
    } catch {
      setError('Failed to load trade routes')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div>
      {loading && <p className="text-gray-400 text-sm mb-4">Loading…</p>}
      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Route</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Commodity</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Annual Value</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Dependency</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {routes.map((r) => (
              <tr key={r.id} className="hover:bg-gray-800/50">
                <td className="py-3 pr-4">
                  <span className="font-mono text-sky-400">{r.origin_country}</span>
                  <span className="text-gray-500 mx-1">→</span>
                  <span className="font-mono text-sky-300">{r.destination_country}</span>
                </td>
                <td className="py-3 pr-4 text-gray-200">{r.commodity.replace(/_/g, ' ')}</td>
                <td className="py-3 pr-4 text-gray-300">
                  ${(r.annual_value_usd / 1e9).toFixed(0)}B
                </td>
                <td className="py-3 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${DEPENDENCY_COLORS[r.dependency_level]}`}>
                    {r.dependency_level}
                  </span>
                </td>
                <td className="py-3">
                  {r.is_disrupted ? (
                    <span className="text-xs text-red-400 font-medium">⚠ DISRUPTED</span>
                  ) : (
                    <span className="text-xs text-green-400">ACTIVE</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && routes.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-8">No trade routes found.</p>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Economic Indicators Tab
// ---------------------------------------------------------------------------

function IndicatorsTab() {
  const [indicators, setIndicators] = useState<EconomicIndicator[]>([])
  const [countryFilter, setCountryFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {}
      if (countryFilter) params.country_code = countryFilter.toUpperCase()
      const resp = await econClient.get<EconomicIndicator[]>('/economic-indicators', { params })
      setIndicators(resp.data)
    } catch {
      setError('Failed to load indicators')
    } finally {
      setLoading(false)
    }
  }, [countryFilter])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <div className="flex gap-3 mb-4">
        <input
          value={countryFilter}
          onChange={(e) => setCountryFilter(e.target.value)}
          maxLength={3}
          className="w-32 bg-gray-800 border border-gray-600 text-white rounded px-3 py-1.5 text-sm font-mono uppercase"
          placeholder="Country"
        />
        <button
          onClick={load}
          className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
        >
          Filter
        </button>
      </div>

      {loading && <p className="text-gray-400 text-sm mb-4">Loading…</p>}
      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Country</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Indicator</th>
              <th className="text-right text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Value</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Unit</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2 pr-4">Year</th>
              <th className="text-left text-xs font-semibold text-gray-400 uppercase pb-2">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {indicators.map((ind) => (
              <tr key={ind.id} className="hover:bg-gray-800/50">
                <td className="py-2.5 pr-4 font-mono text-sky-400">{ind.country_code}</td>
                <td className="py-2.5 pr-4 text-gray-200">{ind.indicator_name.replace(/_/g, ' ')}</td>
                <td className={`py-2.5 pr-4 text-right font-mono font-medium ${ind.value < 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {ind.value > 0 ? '+' : ''}{ind.value.toFixed(2)}
                </td>
                <td className="py-2.5 pr-4 text-gray-400 text-xs">{ind.unit}</td>
                <td className="py-2.5 pr-4 text-gray-400">{ind.year}</td>
                <td className="py-2.5 text-gray-500 text-xs">{ind.source ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && indicators.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-8">No indicators found.</p>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Impact Assessment Tab
// ---------------------------------------------------------------------------

function ImpactTab() {
  const [targetCountry, setTargetCountry] = useState('')
  const [sanctions, setSanctions] = useState<SanctionTarget[]>([])
  const [selectedSanctionIds, setSelectedSanctionIds] = useState<string[]>([])
  const [result, setResult] = useState<EconomicImpactAssessment | null>(null)
  const [pastAssessments, setPastAssessments] = useState<EconomicImpactAssessment[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    econClient.get<SanctionTarget[]>('/sanctions').then((r) => setSanctions(r.data)).catch(() => {})
    econClient.get<EconomicImpactAssessment[]>('/impact/assessments').then((r) => setPastAssessments(r.data)).catch(() => {})
  }, [])

  const toggleSanction = (id: string) => {
    setSelectedSanctionIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const runAssessment = async () => {
    setRunning(true)
    setError(null)
    try {
      const body: RunImpactAssessmentRequest = {
        target_country: targetCountry.toUpperCase().slice(0, 3),
        sanction_ids: selectedSanctionIds,
      }
      const resp = await econClient.post<EconomicImpactAssessment>('/impact/assess', body)
      setResult(resp.data)
      setPastAssessments((prev) => [resp.data, ...prev])
    } catch {
      setError('Failed to run assessment')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      {/* Left: form */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Target Country Code *</label>
          <input
            value={targetCountry}
            onChange={(e) => setTargetCountry(e.target.value)}
            maxLength={3}
            className="w-32 bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm font-mono uppercase"
            placeholder="RUS"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">Select Active Sanctions</label>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {sanctions.length === 0 && (
              <p className="text-xs text-gray-500">No sanctions loaded.</p>
            )}
            {sanctions.map((s) => (
              <label key={s.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-800 rounded px-2 py-1">
                <input
                  type="checkbox"
                  checked={selectedSanctionIds.includes(s.id)}
                  onChange={() => toggleSanction(s.id)}
                  className="accent-sky-500"
                />
                <span className="text-sm text-gray-200">{s.name}</span>
                <span className="text-xs text-gray-500">({SANCTION_TYPE_LABELS[s.sanction_type]})</span>
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          onClick={runAssessment}
          disabled={running || !targetCountry}
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-sm rounded disabled:opacity-50 transition-colors"
        >
          {running ? 'Running…' : 'Run Assessment'}
        </button>

        {/* Result card */}
        {result && (
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">
                Assessment — <span className="font-mono text-sky-400">{result.target_country}</span>
              </h3>
              <span className={`text-lg font-bold ${SEVERITY_COLORS[result.severity]}`}>
                {result.severity}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-gray-400">GDP Impact</p>
                <p className="font-mono text-red-400 font-medium">−{result.gdp_impact_pct.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Inflation Change</p>
                <p className="font-mono text-orange-400 font-medium">+{result.inflation_rate_change.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Unemployment Change</p>
                <p className="font-mono text-yellow-400 font-medium">+{result.unemployment_change.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Currency Devaluation</p>
                <p className="font-mono text-red-300 font-medium">−{result.currency_devaluation_pct.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Trade Volume Reduction</p>
                <p className="font-mono text-orange-300 font-medium">−{result.trade_volume_reduction_pct.toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Timeline</p>
                <p className="font-mono text-gray-200">{result.timeline_months} months</p>
              </div>
            </div>
            {result.affected_sectors.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-gray-400 mb-1">Affected Sectors</p>
                <div className="flex flex-wrap gap-1">
                  {result.affected_sectors.map((s) => (
                    <span key={s} className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                      {s.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <p className="text-xs text-gray-500 mt-3">
              Confidence: {(result.confidence_score * 100).toFixed(0)}%
            </p>
          </div>
        )}
      </div>

      {/* Right: past assessments */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Past Assessments</h3>
        <div className="space-y-2 max-h-[560px] overflow-y-auto">
          {pastAssessments.length === 0 && (
            <p className="text-gray-500 text-sm">No past assessments.</p>
          )}
          {pastAssessments.map((a) => (
            <div
              key={a.id}
              className="bg-gray-900 border border-gray-700 rounded p-3 cursor-pointer hover:border-gray-600"
              onClick={() => setResult(a)}
            >
              <div className="flex justify-between items-center">
                <span className="font-mono text-sm text-sky-400">{a.target_country}</span>
                <span className={`text-sm font-semibold ${SEVERITY_COLORS[a.severity]}`}>{a.severity}</span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                GDP: −{a.gdp_impact_pct.toFixed(2)}% · {new Date(a.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main EconPage
// ---------------------------------------------------------------------------

export default function EconPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [activeTab, setActiveTab] = useState<Tab>('sanctions')

  const tabs: { id: Tab; label: string }[] = [
    { id: 'sanctions', label: 'Sanction Targets' },
    { id: 'trade', label: 'Trade Routes' },
    { id: 'indicators', label: 'Economic Indicators' },
    { id: 'impact', label: 'Impact Assessment' },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <div className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-xl font-bold text-white">💰 Economic Warfare</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Sanction mapping, trade disruption modeling, and economic impact assessment
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
        {activeTab === 'sanctions' && <SanctionsTab />}
        {activeTab === 'trade' && <TradeRoutesTab />}
        {activeTab === 'indicators' && <IndicatorsTab />}
        {activeTab === 'impact' && <ImpactTab />}
      </div>

      <ClassificationBanner level={classification} />
    </div>
  )
}

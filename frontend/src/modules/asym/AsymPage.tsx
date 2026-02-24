import { useEffect, useState } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { asymApi } from '../../shared/api/endpoints'
import type {
  CellFunction,
  CellStatus,
  CellStructure,
  CreateCellRequest,
  CreateCellLinkRequest,
  CreateIncidentRequest,
  FundingLevel,
  IEDIncident,
  IEDTypeEntry,
  IncidentStatus,
  InsurgentCell,
  NetworkAnalysis,
} from '../../shared/api/types'

// ---------------------------------------------------------------------------
// Constants & helpers
// ---------------------------------------------------------------------------

const CELL_FUNCTION_LABELS: Record<CellFunction, string> = {
  COMMAND: 'Command',
  OPERATIONS: 'Operations',
  LOGISTICS: 'Logistics',
  INTELLIGENCE: 'Intelligence',
  FINANCE: 'Finance',
  RECRUITMENT: 'Recruitment',
  PROPAGANDA: 'Propaganda',
  SAFE_HOUSE: 'Safe House',
  MEDICAL: 'Medical',
  TECHNICAL: 'Technical / IED',
}

const CELL_FUNCTION_ICONS: Record<CellFunction, string> = {
  COMMAND: '⭐',
  OPERATIONS: '⚔️',
  LOGISTICS: '📦',
  INTELLIGENCE: '🔍',
  FINANCE: '💰',
  RECRUITMENT: '🎯',
  PROPAGANDA: '📢',
  SAFE_HOUSE: '🏠',
  MEDICAL: '🏥',
  TECHNICAL: '🔧',
}

const STATUS_COLORS: Record<CellStatus, string> = {
  ACTIVE: 'bg-red-900 text-red-200',
  DORMANT: 'bg-yellow-900 text-yellow-200',
  DISRUPTED: 'bg-orange-900 text-orange-200',
  NEUTRALIZED: 'bg-gray-700 text-gray-400',
  UNKNOWN: 'bg-gray-800 text-gray-300',
}

const INCIDENT_STATUS_COLORS: Record<IncidentStatus, string> = {
  SUSPECTED: 'bg-yellow-900 text-yellow-200',
  CONFIRMED: 'bg-red-900 text-red-200',
  NEUTRALIZED: 'bg-green-900 text-green-200',
  DETONATED: 'bg-purple-900 text-purple-200',
}

function hubScoreBar(score: number) {
  const pct = Math.round(score * 100)
  const color = score >= 0.7 ? 'bg-red-500' : score >= 0.4 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-300 w-8 text-right">{pct}%</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-panels
// ---------------------------------------------------------------------------

function CellNetworkTab() {
  const [cells, setCells] = useState<InsurgentCell[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedCell, setSelectedCell] = useState<InsurgentCell | null>(null)

  const loadCells = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await asymApi.listCells()
      setCells(data)
    } catch {
      setError('Failed to load cell network. Ensure asym-svc is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadCells() }, [])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this cell and all its links?')) return
    try {
      await asymApi.deleteCell(id)
      setCells((prev) => prev.filter((c) => c.id !== id))
      if (selectedCell?.id === id) setSelectedCell(null)
    } catch {
      alert('Failed to delete cell.')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Cell Network</h2>
          <p className="text-sm text-gray-400">Map insurgent cell structures, roles, and inter-cell connections.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-sky-700 hover:bg-sky-600 text-white text-sm rounded-lg"
        >
          + Add Cell
        </button>
      </div>

      {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-3">{error}</div>}

      {loading ? (
        <div className="text-gray-400 text-sm">Loading cell network…</div>
      ) : cells.length === 0 ? (
        <div className="text-gray-500 text-sm bg-gray-900 border border-gray-800 rounded p-6 text-center">
          No cells mapped yet. Add cells to build the network.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {cells.map((cell) => (
            <div
              key={cell.id}
              className={`rounded-lg border bg-gray-900 p-4 cursor-pointer transition-colors ${
                selectedCell?.id === cell.id ? 'border-sky-600' : 'border-gray-800 hover:border-gray-600'
              }`}
              onClick={() => setSelectedCell(selectedCell?.id === cell.id ? null : cell)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{CELL_FUNCTION_ICONS[cell.function]}</span>
                  <div>
                    <div className="text-white font-medium text-sm">{cell.name}</div>
                    <div className="text-gray-400 text-xs">{CELL_FUNCTION_LABELS[cell.function]}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[cell.status]}`}>
                    {cell.status}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(cell.id) }}
                    className="text-gray-600 hover:text-red-400 text-xs"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Size</div>
                  <div className="text-white font-medium">{cell.size_estimated} mbrs</div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Capability</div>
                  <div className="text-white font-medium">{Math.round(cell.operational_capability * 100)}%</div>
                </div>
                <div className="bg-gray-800 rounded p-2">
                  <div className="text-gray-500">Funding</div>
                  <div className="text-white font-medium">{cell.funding_level}</div>
                </div>
              </div>

              {selectedCell?.id === cell.id && (
                <div className="mt-3 space-y-2 text-xs text-gray-400 border-t border-gray-800 pt-3">
                  {cell.region && <div>Region: <span className="text-gray-200">{cell.region}{cell.country_code ? ` (${cell.country_code})` : ''}</span></div>}
                  {cell.latitude != null && <div>Location: <span className="text-gray-200">{cell.latitude.toFixed(4)}°, {cell.longitude!.toFixed(4)}°</span></div>}
                  <div>Structure: <span className="text-gray-200">{cell.structure}</span></div>
                  <div>Leadership confidence: <span className="text-gray-200">{Math.round(cell.leadership_confidence * 100)}%</span></div>
                  {cell.affiliated_groups.length > 0 && (
                    <div>Affiliations: <span className="text-gray-200">{cell.affiliated_groups.join(', ')}</span></div>
                  )}
                  {cell.notes && <div className="text-gray-500 italic">{cell.notes}</div>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreateCellModal
          onClose={() => setShowCreateModal(false)}
          onCreated={(cell) => { setCells((prev) => [cell, ...prev]); setShowCreateModal(false) }}
        />
      )}
    </div>
  )
}


function CreateCellModal({ onClose, onCreated }: { onClose: () => void; onCreated: (c: InsurgentCell) => void }) {
  const [form, setForm] = useState<CreateCellRequest>({
    name: '',
    function: 'OPERATIONS',
    structure: 'NETWORK',
    status: 'UNKNOWN',
    size_estimated: 5,
    leadership_confidence: 0.5,
    operational_capability: 0.5,
    funding_level: 'UNKNOWN',
    affiliated_groups: [],
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const cell = await asymApi.createCell(form)
      onCreated(cell)
    } catch {
      setError('Failed to create cell.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold">Add Insurgent Cell</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Cell Name *</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
                placeholder="e.g. Alpha Command"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Function</label>
              <select
                value={form.function}
                onChange={(e) => setForm({ ...form, function: e.target.value as CellFunction })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {(Object.keys(CELL_FUNCTION_LABELS) as CellFunction[]).map((f) => (
                  <option key={f} value={f}>{CELL_FUNCTION_LABELS[f]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as CellStatus })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {(['ACTIVE', 'DORMANT', 'DISRUPTED', 'NEUTRALIZED', 'UNKNOWN'] as CellStatus[]).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Structure</label>
              <select
                value={form.structure}
                onChange={(e) => setForm({ ...form, structure: e.target.value as CellStructure })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {(['HIERARCHICAL', 'NETWORK', 'HUB_AND_SPOKE', 'CHAIN', 'HYBRID'] as CellStructure[]).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Est. Size (members)</label>
              <input
                type="number"
                min={1}
                value={form.size_estimated}
                onChange={(e) => setForm({ ...form, size_estimated: Number(e.target.value) })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Funding Level</label>
              <select
                value={form.funding_level}
                onChange={(e) => setForm({ ...form, funding_level: e.target.value as FundingLevel })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {(['NONE', 'LOW', 'MEDIUM', 'HIGH', 'UNKNOWN'] as FundingLevel[]).map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Op. Capability (0–1)</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={form.operational_capability}
                onChange={(e) => setForm({ ...form, operational_capability: Number(e.target.value) })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Region</label>
              <input
                value={form.region ?? ''}
                onChange={(e) => setForm({ ...form, region: e.target.value || undefined })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
                placeholder="e.g. Baghdad"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Notes</label>
              <textarea
                value={form.notes ?? ''}
                onChange={(e) => setForm({ ...form, notes: e.target.value || undefined })}
                rows={2}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm resize-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-sky-700 hover:bg-sky-600 text-white text-sm rounded-lg disabled:opacity-50"
            >
              {loading ? 'Creating…' : 'Create Cell'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}


function IEDThreatTab() {
  const [iedTypes, setIEDTypes] = useState<IEDTypeEntry[]>([])
  const [incidents, setIncidents] = useState<IEDIncident[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedType, setSelectedType] = useState<IEDTypeEntry | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([asymApi.listIEDTypes(), asymApi.listIncidents()])
      .then(([types, incs]) => { setIEDTypes(types); setIncidents(incs) })
      .catch(() => setError('Failed to load IED data. Ensure asym-svc is running.'))
      .finally(() => setLoading(false))
  }, [])

  const handleDeleteIncident = async (id: string) => {
    if (!confirm('Delete this incident record?')) return
    try {
      await asymApi.deleteIncident(id)
      setIncidents((prev) => prev.filter((i) => i.id !== id))
    } catch {
      alert('Failed to delete incident.')
    }
  }

  const totalKilled = incidents.reduce((s, i) => s + i.casualties_killed, 0)
  const totalWounded = incidents.reduce((s, i) => s + i.casualties_wounded, 0)

  return (
    <div className="space-y-6">
      {/* IED Type Catalog */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">IED Type Catalog</h2>
        <p className="text-sm text-gray-400 mb-3">Reference catalog of IED types with threat parameters and countermeasures.</p>

        {loading ? (
          <div className="text-gray-400 text-sm">Loading…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {iedTypes.map((type) => (
              <div
                key={type.id}
                onClick={() => setSelectedType(selectedType?.id === type.id ? null : type)}
                className={`rounded-lg border bg-gray-900 p-4 cursor-pointer transition-colors ${
                  selectedType?.id === type.id ? 'border-orange-600' : 'border-gray-800 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium text-sm">{type.label}</span>
                  <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{type.category}</span>
                </div>
                <div className="grid grid-cols-2 gap-1 text-xs text-gray-400 mb-2">
                  <div>Yield: <span className="text-white">{type.typical_yield_kg_tnt_equiv} kg TNT</span></div>
                  <div>Lethal r.: <span className="text-white">{type.lethal_radius_m} m</span></div>
                  <div>Avg KIA: <span className="text-red-400">{type.avg_killed}</span></div>
                  <div>Avg WIA: <span className="text-orange-400">{type.avg_wounded}</span></div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Detection: </span>
                  <span className={
                    type.detection_difficulty === 'HIGH' ? 'text-red-400' :
                    type.detection_difficulty === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'
                  }>{type.detection_difficulty}</span>
                </div>
                {selectedType?.id === type.id && (
                  <div className="mt-3 space-y-2 border-t border-gray-800 pt-3">
                    <p className="text-xs text-gray-400">{type.description}</p>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Countermeasures:</div>
                      <ul className="text-xs text-gray-300 space-y-0.5">
                        {type.countermeasures.map((cm, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="text-sky-500">›</span>{cm}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Incident Log */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-white">IED Incident Log</h2>
            {incidents.length > 0 && (
              <p className="text-xs text-gray-400 mt-0.5">
                {incidents.length} incident(s) — Total: <span className="text-red-400">{totalKilled} KIA</span>, <span className="text-orange-400">{totalWounded} WIA</span>
              </p>
            )}
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-orange-800 hover:bg-orange-700 text-white text-sm rounded-lg"
          >
            + Log Incident
          </button>
        </div>

        {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-3 mb-3">{error}</div>}

        {incidents.length === 0 ? (
          <div className="text-gray-500 text-sm bg-gray-900 border border-gray-800 rounded p-6 text-center">
            No incidents logged. Use "Log Incident" to record IED events.
          </div>
        ) : (
          <div className="space-y-2">
            {incidents.map((inc) => (
              <div key={inc.id} className="flex items-start gap-4 bg-gray-900 border border-gray-800 rounded-lg p-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white text-sm font-medium">{inc.ied_type_id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${INCIDENT_STATUS_COLORS[inc.status]}`}>
                      {inc.status}
                    </span>
                    <span className="text-xs text-gray-500">{inc.target_type}</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    📍 {inc.latitude.toFixed(4)}°, {inc.longitude.toFixed(4)}°
                    {inc.location_description && ` — ${inc.location_description}`}
                  </div>
                  {(inc.casualties_killed > 0 || inc.casualties_wounded > 0) && (
                    <div className="text-xs mt-1">
                      <span className="text-red-400">{inc.casualties_killed} KIA</span>
                      {' · '}
                      <span className="text-orange-400">{inc.casualties_wounded} WIA</span>
                    </div>
                  )}
                  {inc.notes && <div className="text-xs text-gray-500 mt-1 italic">{inc.notes}</div>}
                </div>
                <button
                  onClick={() => handleDeleteIncident(inc.id)}
                  className="text-gray-600 hover:text-red-400 text-xs flex-shrink-0"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
        <CreateIncidentModal
          iedTypes={iedTypes}
          onClose={() => setShowCreateModal(false)}
          onCreated={(inc) => { setIncidents((prev) => [inc, ...prev]); setShowCreateModal(false) }}
        />
      )}
    </div>
  )
}


function CreateIncidentModal({
  iedTypes,
  onClose,
  onCreated,
}: {
  iedTypes: IEDTypeEntry[]
  onClose: () => void
  onCreated: (i: IEDIncident) => void
}) {
  const [form, setForm] = useState<CreateIncidentRequest>({
    ied_type_id: iedTypes[0]?.id ?? 'PLACED_IED',
    latitude: 33.5,
    longitude: 44.4,
    status: 'SUSPECTED',
    detonation_type: 'UNKNOWN',
    target_type: 'UNKNOWN',
    casualties_killed: 0,
    casualties_wounded: 0,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const inc = await asymApi.createIncident(form)
      onCreated(inc)
    } catch {
      setError('Failed to log incident.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold">Log IED Incident</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-gray-400 block mb-1">IED Type *</label>
              <select
                value={form.ied_type_id}
                onChange={(e) => setForm({ ...form, ied_type_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {iedTypes.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Latitude</label>
              <input
                type="number"
                step={0.0001}
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: Number(e.target.value) })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Longitude</label>
              <input
                type="number"
                step={0.0001}
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: Number(e.target.value) })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as IncidentStatus })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {(['SUSPECTED', 'CONFIRMED', 'NEUTRALIZED', 'DETONATED'] as IncidentStatus[]).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Target Type</label>
              <select
                value={form.target_type}
                onChange={(e) => setForm({ ...form, target_type: e.target.value as CreateIncidentRequest['target_type'] })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              >
                {['CONVOY', 'PATROL', 'CHECKPOINT', 'CIVILIAN', 'VIP', 'INFRASTRUCTURE', 'MARKET', 'GOVERNMENT', 'UNKNOWN'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Casualties KIA</label>
              <input
                type="number"
                min={0}
                value={form.casualties_killed}
                onChange={(e) => setForm({ ...form, casualties_killed: Number(e.target.value) })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Casualties WIA</label>
              <input
                type="number"
                min={0}
                value={form.casualties_wounded}
                onChange={(e) => setForm({ ...form, casualties_wounded: Number(e.target.value) })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Location Description</label>
              <input
                value={form.location_description ?? ''}
                onChange={(e) => setForm({ ...form, location_description: e.target.value || undefined })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm"
                placeholder="e.g. Route 6 north of Baghdad"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Notes</label>
              <textarea
                value={form.notes ?? ''}
                onChange={(e) => setForm({ ...form, notes: e.target.value || undefined })}
                rows={2}
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm resize-none"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-orange-800 hover:bg-orange-700 text-white text-sm rounded-lg disabled:opacity-50"
            >
              {loading ? 'Logging…' : 'Log Incident'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}


function COINPlanningTab() {
  const [analysis, setAnalysis] = useState<NetworkAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runAnalysis = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await asymApi.analyzeNetwork()
      setAnalysis(data)
    } catch {
      setError('Failed to run analysis. Ensure asym-svc is running and cells have been mapped.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { runAnalysis() }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">COIN Planning</h2>
          <p className="text-sm text-gray-400">Counter-insurgency analysis: hub detection, network vulnerability, and interdiction priorities.</p>
        </div>
        <button
          onClick={runAnalysis}
          disabled={loading}
          className="px-4 py-2 bg-purple-800 hover:bg-purple-700 text-white text-sm rounded-lg disabled:opacity-50"
        >
          {loading ? 'Analyzing…' : '🔄 Re-analyze'}
        </button>
      </div>

      {error && <div className="text-red-400 text-sm bg-red-950 border border-red-800 rounded p-3">{error}</div>}

      {!analysis && !loading && !error && (
        <div className="text-gray-500 text-sm bg-gray-900 border border-gray-800 rounded p-6 text-center">
          No analysis yet.
        </div>
      )}

      {analysis && (
        <div className="space-y-4">
          {/* Summary stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Total Cells', value: analysis.total_cells },
              { label: 'Active', value: analysis.active_cells, cls: 'text-red-400' },
              { label: 'Links', value: analysis.total_links },
              { label: 'Network Density', value: `${(analysis.network_density * 100).toFixed(1)}%` },
            ].map(({ label, value, cls }) => (
              <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
                <div className={`text-2xl font-bold ${cls ?? 'text-white'}`}>{value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          {/* Analysis summary */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-1">Analysis Summary</h3>
            <p className="text-sm text-gray-400">{analysis.analysis_summary}</p>
          </div>

          {/* COIN recommendations */}
          {analysis.coin_recommendations.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">COIN Recommendations</h3>
              <ul className="space-y-2">
                {analysis.coin_recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="text-purple-400 flex-shrink-0 mt-0.5">▸</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Top interdiction targets */}
          {analysis.top_targets.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                Interdiction Priority Ranking
              </h3>
              <div className="space-y-2">
                {analysis.top_targets.map((node, rank) => (
                  <div key={node.cell_id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-5">#{rank + 1}</span>
                        <span className="text-white text-sm font-medium">{node.cell_name}</span>
                        <span className="text-xs text-gray-500">{CELL_FUNCTION_LABELS[node.function]}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span>{node.degree} links</span>
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          node.interdiction_value >= 8 ? 'bg-red-900 text-red-200' :
                          node.interdiction_value >= 5 ? 'bg-yellow-900 text-yellow-200' :
                          'bg-gray-700 text-gray-300'
                        }`}>
                          P{node.interdiction_value}
                        </span>
                      </div>
                    </div>
                    <div className="mb-2">
                      <div className="text-xs text-gray-500 mb-1">Hub Score</div>
                      {hubScoreBar(node.hub_score)}
                    </div>
                    <p className="text-xs text-gray-400">{node.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}


// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type Tab = 'network' | 'ied' | 'coin'

export default function AsymPage() {
  const user = useAuthStore((s) => s.user)
  const classification = user?.classification ?? 'UNCLASS'
  const [activeTab, setActiveTab] = useState<Tab>('network')

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'network', label: 'Cell Network', icon: '🕸️' },
    { id: 'ied', label: 'IED Threats', icon: '💣' },
    { id: 'coin', label: 'COIN Planning', icon: '🎯' },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 px-6 py-6 max-w-7xl mx-auto w-full">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Asymmetric / Insurgency</h1>
          <p className="text-sm text-gray-400 mt-1">
            Insurgent cell structure modeling, IED threat tracking, and COIN planning.
          </p>
        </div>

        {/* Tab nav */}
        <div className="flex gap-1 mb-6 bg-gray-900 border border-gray-800 rounded-lg p-1 w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm rounded-md transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-700 text-white font-medium'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'network' && <CellNetworkTab />}
        {activeTab === 'ied' && <IEDThreatTab />}
        {activeTab === 'coin' && <COINPlanningTab />}
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

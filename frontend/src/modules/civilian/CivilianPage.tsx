import { useEffect, useState } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { civilianApi } from '../../shared/api/endpoints'
import type {
  PopulationZone,
  CreatePopulationZoneRequest,
  DensityClass,
  ImpactAssessment,
  ZoneImpact,
  RefugeeFlow,
  CreateRefugeeFlowRequest,
  DisplacementStatus,
  HumanitarianCorridor,
  CreateCorridorRequest,
  CorridorStatus,
} from '../../shared/api/types'

// ---------------------------------------------------------------------------
// Constants & helpers
// ---------------------------------------------------------------------------

const DENSITY_COLORS: Record<DensityClass, string> = {
  URBAN: 'bg-sky-900 text-sky-200',
  SUBURBAN: 'bg-yellow-900 text-yellow-200',
  RURAL: 'bg-green-900 text-green-200',
  SPARSE: 'bg-gray-700 text-gray-300',
}

const DISPLACEMENT_COLORS: Record<DisplacementStatus, string> = {
  PROJECTED: 'bg-gray-700 text-gray-300',
  CONFIRMED: 'bg-yellow-900 text-yellow-200',
  RESOLVED: 'bg-green-900 text-green-200',
}

const CORRIDOR_COLORS: Record<CorridorStatus, string> = {
  OPEN: 'bg-green-900 text-green-200',
  RESTRICTED: 'bg-yellow-900 text-yellow-200',
  CLOSED: 'bg-red-900 text-red-200',
}

function impactBarColor(score: number): string {
  if (score <= 3) return 'bg-green-500'
  if (score <= 6) return 'bg-yellow-500'
  return 'bg-red-500'
}

// ---------------------------------------------------------------------------
// CivilianPage
// ---------------------------------------------------------------------------

export default function CivilianPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [activeTab, setActiveTab] = useState<'zones' | 'impact' | 'flows' | 'corridors'>('zones')

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <div className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Civilian Impact</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Population zones · Impact assessment · Refugee flows · Humanitarian corridors
            </p>
          </div>
        </div>

        <div className="flex gap-1 mt-4">
          {(
            [
              { id: 'zones', label: '🏙️ Population Zones' },
              { id: 'impact', label: '📊 Impact Assessment' },
              { id: 'flows', label: '🚶 Refugee Flows' },
              { id: 'corridors', label: '🛤️ Humanitarian Corridors' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 overflow-auto p-6">
        {activeTab === 'zones' && <PopulationZonesTab />}
        {activeTab === 'impact' && <ImpactAssessmentTab />}
        {activeTab === 'flows' && <RefugeeFlowsTab />}
        {activeTab === 'corridors' && <HumanitarianCorridorsTab />}
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 1: Population Zones
// ---------------------------------------------------------------------------

function PopulationZonesTab() {
  const [zones, setZones] = useState<PopulationZone[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)

  const fetchZones = () => {
    setLoading(true)
    setError(null)
    civilianApi
      .listZones()
      .then(setZones)
      .catch(() => setError('Failed to load population zones.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchZones()
  }, [])

  const handleDelete = (id: string) => {
    civilianApi
      .deleteZone(id)
      .then(fetchZones)
      .catch(() => setError('Failed to delete zone.'))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold">Population Zones</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
        >
          + Add Zone
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : zones.length === 0 ? (
        <div className="text-gray-500 text-sm rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
          No population zones configured. Add a zone to get started.
        </div>
      ) : (
        <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Country</th>
                <th className="px-4 py-3 text-right">Population</th>
                <th className="px-4 py-3 text-left">Density</th>
                <th className="px-4 py-3 text-right">Radius (km)</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {zones.map((zone) => (
                <tr key={zone.id} className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
                  <td className="px-4 py-3 text-white font-medium">{zone.name}</td>
                  <td className="px-4 py-3 text-gray-300 font-mono">{zone.country_code}</td>
                  <td className="px-4 py-3 text-gray-300 text-right">{zone.population.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${DENSITY_COLORS[zone.density_class]}`}>
                      {zone.density_class}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-right">{zone.radius_km}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(zone.id)}
                      className="text-xs text-red-400 hover:text-red-300 transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAddModal && (
        <AddZoneModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => {
            setShowAddModal(false)
            fetchZones()
          }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// AddZoneModal
// ---------------------------------------------------------------------------

function AddZoneModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState('')
  const [countryCode, setCountryCode] = useState('')
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [radiusKm, setRadiusKm] = useState('')
  const [population, setPopulation] = useState('')
  const [densityClass, setDensityClass] = useState<DensityClass>('URBAN')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = () => {
    setError(null)

    if (!name.trim()) { setError('Name is required.'); return }
    if (countryCode.length < 2 || countryCode.length > 3) { setError('Country code must be 2–3 characters.'); return }
    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)
    if (isNaN(lat) || isNaN(lon)) { setError('Latitude and Longitude must be valid numbers.'); return }
    const radius = parseFloat(radiusKm)
    if (isNaN(radius) || radius <= 0) { setError('Radius must be greater than 0.'); return }
    const pop = parseInt(population, 10)
    if (isNaN(pop) || pop <= 0) { setError('Population must be greater than 0.'); return }

    const payload: CreatePopulationZoneRequest = {
      name: name.trim(),
      country_code: countryCode.toUpperCase(),
      latitude: lat,
      longitude: lon,
      radius_km: radius,
      population: pop,
      density_class: densityClass,
    }

    setSubmitting(true)
    civilianApi
      .createZone(payload)
      .then(() => onCreated())
      .catch(() => setError('Failed to create zone.'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Modal title="Add Population Zone" onClose={onClose}>
      <div className="space-y-3">
        <ModalField label="Name">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
            placeholder="e.g. Kabul City Centre"
          />
        </ModalField>
        <ModalField label="Country Code (2–3 chars)">
          <input
            value={countryCode}
            onChange={(e) => setCountryCode(e.target.value)}
            maxLength={3}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500 font-mono uppercase"
            placeholder="e.g. AF"
          />
        </ModalField>
        <div className="grid grid-cols-2 gap-3">
          <ModalField label="Latitude">
            <input
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="34.5553"
            />
          </ModalField>
          <ModalField label="Longitude">
            <input
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="69.2075"
            />
          </ModalField>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <ModalField label="Radius (km)">
            <input
              value={radiusKm}
              onChange={(e) => setRadiusKm(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="15"
            />
          </ModalField>
          <ModalField label="Population">
            <input
              value={population}
              onChange={(e) => setPopulation(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="500000"
            />
          </ModalField>
        </div>
        <ModalField label="Density Class">
          <select
            value={densityClass}
            onChange={(e) => setDensityClass(e.target.value as DensityClass)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
          >
            <option value="URBAN">URBAN</option>
            <option value="SUBURBAN">SUBURBAN</option>
            <option value="RURAL">RURAL</option>
            <option value="SPARSE">SPARSE</option>
          </select>
        </ModalField>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="rounded px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
          >
            {submitting ? 'Creating…' : 'Create Zone'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ---------------------------------------------------------------------------
// Tab 2: Impact Assessment
// ---------------------------------------------------------------------------

function ImpactAssessmentTab() {
  const [zones, setZones] = useState<PopulationZone[]>([])
  const [zonesLoaded, setZonesLoaded] = useState(false)
  const [runId, setRunId] = useState('')
  const [assessment, setAssessment] = useState<ImpactAssessment | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    civilianApi
      .listZones()
      .then((z) => { setZones(z); setZonesLoaded(true) })
      .catch(() => setZonesLoaded(true))
  }, [])

  const handleAssess = () => {
    if (!runId.trim()) { setError('Run ID is required.'); return }
    setError(null)
    setLoading(true)
    civilianApi
      .assessImpact({ run_id: runId.trim() })
      .then(setAssessment)
      .catch(() => setError('Failed to assess impact. Ensure the run ID is valid.'))
      .finally(() => setLoading(false))
  }

  return (
    <div className="space-y-4">
      <h2 className="text-white font-semibold">Impact Assessment</h2>

      {zonesLoaded && zones.length === 0 ? (
        <div className="text-gray-500 text-sm rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
          No zones configured — add population zones first.
        </div>
      ) : (
        <>
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4 flex gap-3 flex-wrap items-end">
            <div className="flex-1 min-w-48">
              <label className="block text-xs text-gray-400 mb-1">Run ID</label>
              <input
                value={runId}
                onChange={(e) => setRunId(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAssess()}
                placeholder="Enter simulation run ID…"
                className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              />
            </div>
            <button
              onClick={handleAssess}
              disabled={loading}
              className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
            >
              {loading ? 'Assessing…' : 'Assess Impact'}
            </button>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          {assessment && <ImpactResultPanel assessment={assessment} />}
        </>
      )}
    </div>
  )
}

function ImpactResultPanel({ assessment }: { assessment: ImpactAssessment }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <SummaryCard label="Total Casualties" value={assessment.total_civilian_casualties.toLocaleString()} color="text-red-400" />
        <SummaryCard label="Total Wounded" value={assessment.total_civilian_wounded.toLocaleString()} color="text-orange-400" />
        <SummaryCard label="Total Displaced" value={assessment.total_displaced_persons.toLocaleString()} color="text-yellow-400" />
      </div>

      {assessment.zone_impacts.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 text-left">Zone</th>
                <th className="px-4 py-3 text-right">Casualties</th>
                <th className="px-4 py-3 text-right">Wounded</th>
                <th className="px-4 py-3 text-right">Displaced</th>
                <th className="px-4 py-3 text-right">Infra Damage %</th>
                <th className="px-4 py-3 text-left">Impact Score</th>
              </tr>
            </thead>
            <tbody>
              {assessment.zone_impacts.map((zi: ZoneImpact) => (
                <tr key={zi.zone_id} className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
                  <td className="px-4 py-3 text-white">{zi.zone_name}</td>
                  <td className="px-4 py-3 text-red-400 text-right">{zi.civilian_casualties.toLocaleString()}</td>
                  <td className="px-4 py-3 text-orange-400 text-right">{zi.civilian_wounded.toLocaleString()}</td>
                  <td className="px-4 py-3 text-yellow-400 text-right">{zi.displaced_persons.toLocaleString()}</td>
                  <td className="px-4 py-3 text-gray-300 text-right">{(zi.infrastructure_damage_pct * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-700 rounded-full h-2 min-w-20">
                        <div
                          className={`h-2 rounded-full ${impactBarColor(zi.impact_score)}`}
                          style={{ width: `${Math.min((zi.impact_score / 10) * 100, 100)}%` }}
                        />
                      </div>
                      <span className="text-gray-300 text-xs w-6 text-right">{zi.impact_score.toFixed(1)}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 3: Refugee Flows
// ---------------------------------------------------------------------------

function RefugeeFlowsTab() {
  const [flows, setFlows] = useState<RefugeeFlow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [pendingStatus, setPendingStatus] = useState<Record<string, DisplacementStatus>>({})

  const fetchFlows = () => {
    setLoading(true)
    setError(null)
    civilianApi
      .listFlows()
      .then((f) => {
        setFlows(f)
        const initial: Record<string, DisplacementStatus> = {}
        f.forEach((flow) => { initial[flow.id] = flow.status })
        setPendingStatus(initial)
      })
      .catch(() => setError('Failed to load refugee flows.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchFlows()
  }, [])

  const handleSaveStatus = (flowId: string) => {
    const status = pendingStatus[flowId]
    if (!status) return
    civilianApi
      .updateFlow(flowId, { status })
      .then(fetchFlows)
      .catch(() => setError('Failed to update flow status.'))
  }

  const handleDelete = (id: string) => {
    civilianApi
      .deleteFlow(id)
      .then(fetchFlows)
      .catch(() => setError('Failed to delete flow.'))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold">Refugee Flows</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
        >
          + Add Flow
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : flows.length === 0 ? (
        <div className="text-gray-500 text-sm rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
          No refugee flows recorded.
        </div>
      ) : (
        <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 text-left">Origin → Destination</th>
                <th className="px-4 py-3 text-right">Displaced Persons</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Started At</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {flows.map((flow) => (
                <tr key={flow.id} className="border-b border-gray-800 hover:bg-gray-800/40 transition-colors">
                  <td className="px-4 py-3 text-white">
                    <span className="text-gray-300">{flow.origin_name}</span>
                    <span className="text-gray-500 mx-1">→</span>
                    <span className="text-gray-300">{flow.destination_name}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-200 text-right">{flow.displaced_persons.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${DISPLACEMENT_COLORS[flow.status]}`}>
                      {flow.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {new Date(flow.started_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <select
                        value={pendingStatus[flow.id] ?? flow.status}
                        onChange={(e) =>
                          setPendingStatus((prev) => ({ ...prev, [flow.id]: e.target.value as DisplacementStatus }))
                        }
                        className="bg-gray-800 text-white rounded px-2 py-1 text-xs border border-gray-700 focus:outline-none"
                      >
                        <option value="PROJECTED">PROJECTED</option>
                        <option value="CONFIRMED">CONFIRMED</option>
                        <option value="RESOLVED">RESOLVED</option>
                      </select>
                      <button
                        onClick={() => handleSaveStatus(flow.id)}
                        className="text-xs text-sky-400 hover:text-sky-300 transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => handleDelete(flow.id)}
                        className="text-xs text-red-400 hover:text-red-300 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAddModal && (
        <AddFlowModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => {
            setShowAddModal(false)
            fetchFlows()
          }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// AddFlowModal
// ---------------------------------------------------------------------------

function AddFlowModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [originName, setOriginName] = useState('')
  const [originLat, setOriginLat] = useState('')
  const [originLon, setOriginLon] = useState('')
  const [destName, setDestName] = useState('')
  const [destLat, setDestLat] = useState('')
  const [destLon, setDestLon] = useState('')
  const [displacedPersons, setDisplacedPersons] = useState('')
  const [status, setStatus] = useState<DisplacementStatus>('PROJECTED')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = () => {
    setError(null)
    if (!originName.trim()) { setError('Origin name is required.'); return }
    if (!destName.trim()) { setError('Destination name is required.'); return }
    const oLat = parseFloat(originLat)
    const oLon = parseFloat(originLon)
    const dLat = parseFloat(destLat)
    const dLon = parseFloat(destLon)
    if (isNaN(oLat) || isNaN(oLon)) { setError('Origin coordinates must be valid numbers.'); return }
    if (isNaN(dLat) || isNaN(dLon)) { setError('Destination coordinates must be valid numbers.'); return }
    const persons = parseInt(displacedPersons, 10)
    if (isNaN(persons) || persons <= 0) { setError('Displaced persons must be greater than 0.'); return }

    const payload: CreateRefugeeFlowRequest = {
      origin_name: originName.trim(),
      destination_name: destName.trim(),
      origin_lat: oLat,
      origin_lon: oLon,
      destination_lat: dLat,
      destination_lon: dLon,
      displaced_persons: persons,
      status,
    }

    setSubmitting(true)
    civilianApi
      .createFlow(payload)
      .then(() => onCreated())
      .catch(() => setError('Failed to create flow.'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Modal title="Add Refugee Flow" onClose={onClose}>
      <div className="space-y-3">
        <ModalField label="Origin Name">
          <input
            value={originName}
            onChange={(e) => setOriginName(e.target.value)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
            placeholder="e.g. Aleppo"
          />
        </ModalField>
        <div className="grid grid-cols-2 gap-3">
          <ModalField label="Origin Latitude">
            <input
              value={originLat}
              onChange={(e) => setOriginLat(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="36.2021"
            />
          </ModalField>
          <ModalField label="Origin Longitude">
            <input
              value={originLon}
              onChange={(e) => setOriginLon(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="37.1343"
            />
          </ModalField>
        </div>
        <ModalField label="Destination Name">
          <input
            value={destName}
            onChange={(e) => setDestName(e.target.value)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
            placeholder="e.g. Ankara"
          />
        </ModalField>
        <div className="grid grid-cols-2 gap-3">
          <ModalField label="Destination Latitude">
            <input
              value={destLat}
              onChange={(e) => setDestLat(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="39.9334"
            />
          </ModalField>
          <ModalField label="Destination Longitude">
            <input
              value={destLon}
              onChange={(e) => setDestLon(e.target.value)}
              className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
              placeholder="32.8597"
            />
          </ModalField>
        </div>
        <ModalField label="Displaced Persons">
          <input
            value={displacedPersons}
            onChange={(e) => setDisplacedPersons(e.target.value)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
            placeholder="50000"
          />
        </ModalField>
        <ModalField label="Status">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as DisplacementStatus)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
          >
            <option value="PROJECTED">PROJECTED</option>
            <option value="CONFIRMED">CONFIRMED</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>
        </ModalField>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="rounded px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
          >
            {submitting ? 'Creating…' : 'Create Flow'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ---------------------------------------------------------------------------
// Tab 4: Humanitarian Corridors
// ---------------------------------------------------------------------------

function HumanitarianCorridorsTab() {
  const [corridors, setCorridors] = useState<HumanitarianCorridor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [pendingStatus, setPendingStatus] = useState<Record<string, CorridorStatus>>({})

  const fetchCorridors = () => {
    setLoading(true)
    setError(null)
    civilianApi
      .listCorridors()
      .then((c) => {
        setCorridors(c)
        const initial: Record<string, CorridorStatus> = {}
        c.forEach((corridor) => { initial[corridor.id] = corridor.status })
        setPendingStatus(initial)
      })
      .catch(() => setError('Failed to load humanitarian corridors.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchCorridors()
  }, [])

  const handleSaveStatus = (corridorId: string) => {
    const status = pendingStatus[corridorId]
    if (!status) return
    civilianApi
      .updateCorridor(corridorId, { status })
      .then(fetchCorridors)
      .catch(() => setError('Failed to update corridor status.'))
  }

  const handleDelete = (id: string) => {
    civilianApi
      .deleteCorridor(id)
      .then(fetchCorridors)
      .catch(() => setError('Failed to delete corridor.'))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-white font-semibold">Humanitarian Corridors</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
        >
          + Add Corridor
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : corridors.length === 0 ? (
        <div className="text-gray-500 text-sm rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
          No humanitarian corridors configured.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {corridors.map((corridor) => (
            <div key={corridor.id} className="rounded-lg border border-gray-800 bg-gray-900 p-4 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-white font-medium text-sm">{corridor.name}</h3>
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium whitespace-nowrap ${CORRIDOR_COLORS[corridor.status]}`}>
                  {corridor.status}
                </span>
              </div>
              <div className="text-xs text-gray-400">
                {corridor.waypoints.length} waypoint{corridor.waypoints.length !== 1 ? 's' : ''}
              </div>
              {corridor.notes && (
                <p className="text-xs text-gray-300 border-t border-gray-800 pt-2">{corridor.notes}</p>
              )}
              <div className="flex items-center gap-2 pt-1">
                <select
                  value={pendingStatus[corridor.id] ?? corridor.status}
                  onChange={(e) =>
                    setPendingStatus((prev) => ({ ...prev, [corridor.id]: e.target.value as CorridorStatus }))
                  }
                  className="flex-1 bg-gray-800 text-white rounded px-2 py-1 text-xs border border-gray-700 focus:outline-none"
                >
                  <option value="OPEN">OPEN</option>
                  <option value="RESTRICTED">RESTRICTED</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
                <button
                  onClick={() => handleSaveStatus(corridor.id)}
                  className="text-xs text-sky-400 hover:text-sky-300 transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={() => handleDelete(corridor.id)}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <AddCorridorModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => {
            setShowAddModal(false)
            fetchCorridors()
          }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// AddCorridorModal
// ---------------------------------------------------------------------------

function AddCorridorModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState('')
  const [waypointsText, setWaypointsText] = useState('')
  const [status, setStatus] = useState<CorridorStatus>('OPEN')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = () => {
    setError(null)
    if (!name.trim()) { setError('Name is required.'); return }

    const lines = waypointsText
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0)

    if (lines.length < 2) { setError('At least 2 waypoints are required.'); return }

    const waypoints: { lat: number; lon: number }[] = []
    for (const line of lines) {
      const parts = line.split(',')
      if (parts.length !== 2) { setError(`Invalid waypoint format: "${line}". Use "lat,lon".`); return }
      const lat = parseFloat(parts[0].trim())
      const lon = parseFloat(parts[1].trim())
      if (isNaN(lat) || isNaN(lon)) { setError(`Invalid coordinates in line: "${line}".`); return }
      waypoints.push({ lat, lon })
    }

    const payload: CreateCorridorRequest = {
      name: name.trim(),
      waypoints,
      status,
      notes: notes.trim() || null,
    }

    setSubmitting(true)
    civilianApi
      .createCorridor(payload)
      .then(() => onCreated())
      .catch(() => setError('Failed to create corridor.'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Modal title="Add Humanitarian Corridor" onClose={onClose}>
      <div className="space-y-3">
        <ModalField label="Name">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
            placeholder="e.g. Northern Aid Route"
          />
        </ModalField>
        <ModalField label='Waypoints (one per line, "lat,lon")'>
          <textarea
            value={waypointsText}
            onChange={(e) => setWaypointsText(e.target.value)}
            rows={4}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500 font-mono resize-none"
            placeholder={'36.20,37.13\n37.06,36.78\n38.46,34.16'}
          />
        </ModalField>
        <ModalField label="Status">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as CorridorStatus)}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500"
          >
            <option value="OPEN">OPEN</option>
            <option value="RESTRICTED">RESTRICTED</option>
            <option value="CLOSED">CLOSED</option>
          </select>
        </ModalField>
        <ModalField label="Notes (optional)">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-sky-500 resize-none"
            placeholder="Additional notes…"
          />
        </ModalField>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="rounded px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
          >
            {submitting ? 'Creating…' : 'Create Corridor'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

// ---------------------------------------------------------------------------
// Shared UI primitives
// ---------------------------------------------------------------------------

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-lg border border-gray-700 bg-gray-900 shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-800 px-5 py-4">
          <h2 className="text-sm font-semibold text-white">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-lg leading-none transition-colors">
            ×
          </button>
        </div>
        <div className="px-5 py-4 max-h-[70vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  )
}

function ModalField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  )
}

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { LoadingSpinner } from '../../shared/components/LoadingSpinner'
import { cbrnApi } from '../../shared/api/endpoints'
import type {
  CBRNAgent,
  CBRNCategory,
  CBRNRelease,
  CreateReleaseRequest,
  DispersionSimulation,
  StabilityClass,
} from '../../shared/api/types'

// ── Display helpers ──────────────────────────────────────────────────────────

const CATEGORY_COLOR: Record<CBRNCategory, string> = {
  CHEMICAL:    'bg-orange-900 text-orange-200',
  BIOLOGICAL:  'bg-green-900  text-green-200',
  RADIOLOGICAL:'bg-yellow-900 text-yellow-200',
  NUCLEAR:     'bg-red-900    text-red-200',
}

const CATEGORY_ICON: Record<CBRNCategory, string> = {
  CHEMICAL:    '☣️',
  BIOLOGICAL:  '🦠',
  RADIOLOGICAL:'☢️',
  NUCLEAR:     '💥',
}

const PERSISTENCY_COLOR: Record<string, string> = {
  LOW:       'text-green-400',
  MEDIUM:    'text-yellow-400',
  HIGH:      'text-orange-400',
  VERY_HIGH: 'text-red-400',
}

const STABILITY_LABELS: Record<StabilityClass, string> = {
  A: 'A — Very Unstable',
  B: 'B — Unstable',
  C: 'C — Slightly Unstable',
  D: 'D — Neutral',
  E: 'E — Slightly Stable',
  F: 'F — Stable',
}

type Tab = 'agents' | 'releases' | 'dispersion'

// ── Main page ────────────────────────────────────────────────────────────────

export default function CBRNPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const canWrite = useAuthStore((s) => s.hasPermission('scenario:write'))
  const canRun = useAuthStore((s) => s.hasPermission('simulation:run'))
  const [activeTab, setActiveTab] = useState<Tab>('agents')

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Page header */}
        <div className="px-6 py-4 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white">CBRN Operations</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Agent catalog · Release planning · Gaussian plume dispersion modeling
          </p>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 px-6 pt-3 border-b border-gray-800">
          {([
            ['agents',    '☣️',  'Agent Catalog'],
            ['releases',  '📍',  'Release Planner'],
            ['dispersion','🌬️', 'Dispersion Results'],
          ] as const).map(([id, icon, label]) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`px-4 py-2 text-sm font-medium rounded-t border-b-2 transition-colors ${
                activeTab === id
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              {icon} {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'agents'    && <AgentCatalogTab />}
          {activeTab === 'releases'  && <ReleasePlannerTab canWrite={canWrite} canRun={canRun} />}
          {activeTab === 'dispersion'&& <DispersionTab canRun={canRun} />}
        </div>
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

// ── Agent Catalog Tab ────────────────────────────────────────────────────────

function AgentCatalogTab() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<CBRNCategory | ''>('')
  const [selected, setSelected] = useState<CBRNAgent | null>(null)

  const { data: agents = [], isLoading } = useQuery({
    queryKey: ['cbrn-agents', category, search],
    queryFn: () =>
      cbrnApi.listAgents({
        category: category || undefined,
        q: search || undefined,
      }),
  })

  return (
    <div className="flex gap-6 h-full">
      {/* Left: list */}
      <div className="flex-1 min-w-0">
        {/* Search + filter */}
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            placeholder="Search agents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700 focus:outline-none focus:border-sky-500"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as CBRNCategory | '')}
            className="bg-gray-800 text-white text-sm rounded px-3 py-2 border border-gray-700 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Categories</option>
            <option value="CHEMICAL">Chemical</option>
            <option value="BIOLOGICAL">Biological</option>
            <option value="RADIOLOGICAL">Radiological</option>
            <option value="NUCLEAR">Nuclear</option>
          </select>
        </div>

        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-2">
            {agents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => setSelected(agent)}
                className={`w-full text-left rounded-lg border p-4 transition-colors ${
                  selected?.id === agent.id
                    ? 'border-sky-600 bg-gray-800'
                    : 'border-gray-800 bg-gray-900 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{CATEGORY_ICON[agent.category]}</span>
                    <div>
                      <span className="text-white text-sm font-semibold">{agent.name}</span>
                      <span className="ml-2 text-xs text-gray-400">{agent.sub_category}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded ${CATEGORY_COLOR[agent.category]}`}
                    >
                      {agent.category}
                    </span>
                    <span
                      className={`text-xs font-medium ${PERSISTENCY_COLOR[agent.persistency]}`}
                    >
                      {agent.persistency.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <p className="mt-1 text-xs text-gray-400 line-clamp-2">{agent.description}</p>
              </button>
            ))}
            {agents.length === 0 && (
              <p className="text-center text-gray-500 py-8">No agents match the current filter.</p>
            )}
          </div>
        )}
      </div>

      {/* Right: detail panel */}
      {selected && (
        <div className="w-80 shrink-0 bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-2xl">{CATEGORY_ICON[selected.category]}</span>
            <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-gray-300 text-lg">✕</button>
          </div>
          <div>
            <h2 className="text-white font-bold text-base">{selected.name}</h2>
            <div className="flex gap-2 mt-1 flex-wrap">
              <span className={`text-xs px-2 py-0.5 rounded font-medium ${CATEGORY_COLOR[selected.category]}`}>
                {selected.category}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-200">
                {selected.sub_category}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-200">
                {selected.state}
              </span>
            </div>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed">{selected.description}</p>

          <div className="space-y-1 text-xs">
            <div className="text-gray-400 font-semibold uppercase tracking-wide mb-1">NATO Code</div>
            <div className="font-mono text-sky-400">{selected.nato_code}</div>
          </div>

          {/* Casualty thresholds */}
          <div className="space-y-1 text-xs">
            <div className="text-gray-400 font-semibold uppercase tracking-wide mb-1">Hazard Thresholds</div>
            {selected.lct50_mg_min_m3 != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">LCt50 (inhal.)</span>
                <span className="text-red-300 font-mono">{selected.lct50_mg_min_m3} mg·min/m³</span>
              </div>
            )}
            {selected.ict50_mg_min_m3 != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">ICt50</span>
                <span className="text-orange-300 font-mono">{selected.ict50_mg_min_m3} mg·min/m³</span>
              </div>
            )}
            {selected.idlh_mg_m3 != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">IDLH</span>
                <span className="text-yellow-300 font-mono">{selected.idlh_mg_m3} mg/m³</span>
              </div>
            )}
            {selected.lethal_dose_gy != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">LD50 (absorbed)</span>
                <span className="text-red-300 font-mono">{selected.lethal_dose_gy} Gy</span>
              </div>
            )}
            {selected.yield_kt != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">Yield</span>
                <span className="text-red-300 font-mono">{selected.yield_kt} kT</span>
              </div>
            )}
            {selected.id50_particles != null && (
              <div className="flex justify-between">
                <span className="text-gray-400">ID50 (particles)</span>
                <span className="text-orange-300 font-mono">{selected.id50_particles.toLocaleString()}</span>
              </div>
            )}
          </div>

          <div className="space-y-1 text-xs">
            <div className="text-gray-400 font-semibold uppercase tracking-wide mb-1">Protective Action</div>
            <p className="text-green-300 leading-relaxed">{selected.protective_action}</p>
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span
              className="inline-block w-3 h-3 rounded-full"
              style={{ backgroundColor: selected.color_hex }}
            />
            <span>Map color: {selected.color_hex}</span>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Release Planner Tab ──────────────────────────────────────────────────────

const DEFAULT_MET = {
  wind_speed_ms: 3.0,
  wind_direction_deg: 270.0,
  stability_class: 'D' as StabilityClass,
  mixing_height_m: 800.0,
  temperature_c: 15.0,
  relative_humidity_pct: 60.0,
}

function ReleasePlannerTab({ canWrite, canRun }: { canWrite: boolean; canRun: boolean }) {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CreateReleaseRequest>({
    agent_id: 'GB',
    latitude: 48.85,
    longitude: 2.35,
    quantity_kg: 1.0,
    release_height_m: 1.0,
    duration_min: 10.0,
    met: { ...DEFAULT_MET },
    population_density_per_km2: 500.0,
    label: '',
  })

  const { data: agents = [] } = useQuery({
    queryKey: ['cbrn-agents'],
    queryFn: () => cbrnApi.listAgents(),
  })

  const { data: releases = [], isLoading } = useQuery({
    queryKey: ['cbrn-releases'],
    queryFn: () => cbrnApi.listReleases(),
  })

  const createMut = useMutation({
    mutationFn: (data: CreateReleaseRequest) => cbrnApi.createRelease(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cbrn-releases'] })
      setShowForm(false)
    },
  })

  const deleteMut = useMutation({
    mutationFn: (releaseId: string) => cbrnApi.deleteRelease(releaseId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cbrn-releases'] }),
  })

  const simulateMut = useMutation({
    mutationFn: (releaseId: string) => cbrnApi.simulate(releaseId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cbrn-simulations'] }),
  })

  return (
    <div className="space-y-4">
      {canWrite && (
        <button
          onClick={() => setShowForm((v) => !v)}
          className="px-4 py-2 bg-sky-700 hover:bg-sky-600 text-white text-sm rounded font-medium"
        >
          {showForm ? 'Cancel' : '+ New Release Event'}
        </button>
      )}

      {/* Create Release Form */}
      {showForm && (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-5 space-y-4">
          <h3 className="text-white font-semibold">New CBRN Release Event</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {/* Agent */}
            <div>
              <label className="block text-gray-400 mb-1">Agent</label>
              <select
                value={form.agent_id}
                onChange={(e) => setForm({ ...form, agent_id: e.target.value })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              >
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>

            {/* Label */}
            <div>
              <label className="block text-gray-400 mb-1">Label</label>
              <input
                type="text"
                value={form.label ?? ''}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
                placeholder="e.g. Scenario Alpha Release 1"
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>

            {/* Latitude */}
            <div>
              <label className="block text-gray-400 mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>

            {/* Longitude */}
            <div>
              <label className="block text-gray-400 mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>

            {/* Quantity */}
            <div>
              <label className="block text-gray-400 mb-1">Quantity (kg)</label>
              <input
                type="number"
                min="0.001"
                step="0.1"
                value={form.quantity_kg}
                onChange={(e) => setForm({ ...form, quantity_kg: parseFloat(e.target.value) })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>

            {/* Duration */}
            <div>
              <label className="block text-gray-400 mb-1">Duration (min)</label>
              <input
                type="number"
                min="0.1"
                step="1"
                value={form.duration_min}
                onChange={(e) => setForm({ ...form, duration_min: parseFloat(e.target.value) })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>

            {/* Release height */}
            <div>
              <label className="block text-gray-400 mb-1">Release Height (m)</label>
              <input
                type="number"
                min="0"
                step="1"
                value={form.release_height_m}
                onChange={(e) => setForm({ ...form, release_height_m: parseFloat(e.target.value) })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>

            {/* Population density */}
            <div>
              <label className="block text-gray-400 mb-1">Pop. Density (/km²)</label>
              <input
                type="number"
                min="0"
                step="100"
                value={form.population_density_per_km2}
                onChange={(e) => setForm({ ...form, population_density_per_km2: parseFloat(e.target.value) })}
                className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
              />
            </div>
          </div>

          {/* Met conditions */}
          <div>
            <h4 className="text-gray-300 text-sm font-semibold mb-2">Meteorological Conditions</h4>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div>
                <label className="block text-gray-400 mb-1">Wind Speed (m/s)</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.5"
                  value={form.met?.wind_speed_ms ?? 3}
                  onChange={(e) => setForm({ ...form, met: { ...form.met, wind_speed_ms: parseFloat(e.target.value) } })}
                  className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Wind Direction (°)</label>
                <input
                  type="number"
                  min="0"
                  max="359"
                  step="5"
                  value={form.met?.wind_direction_deg ?? 270}
                  onChange={(e) => setForm({ ...form, met: { ...form.met, wind_direction_deg: parseFloat(e.target.value) } })}
                  className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Stability Class</label>
                <select
                  value={form.met?.stability_class ?? 'D'}
                  onChange={(e) => setForm({ ...form, met: { ...form.met, stability_class: e.target.value as StabilityClass } })}
                  className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
                >
                  {(Object.entries(STABILITY_LABELS) as [StabilityClass, string][]).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Mixing Height (m)</label>
                <input
                  type="number"
                  min="50"
                  step="50"
                  value={form.met?.mixing_height_m ?? 800}
                  onChange={(e) => setForm({ ...form, met: { ...form.met, mixing_height_m: parseFloat(e.target.value) } })}
                  className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Temperature (°C)</label>
                <input
                  type="number"
                  step="1"
                  value={form.met?.temperature_c ?? 15}
                  onChange={(e) => setForm({ ...form, met: { ...form.met, temperature_c: parseFloat(e.target.value) } })}
                  className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
                />
              </div>
              <div>
                <label className="block text-gray-400 mb-1">Rel. Humidity (%)</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="5"
                  value={form.met?.relative_humidity_pct ?? 60}
                  onChange={(e) => setForm({ ...form, met: { ...form.met, relative_humidity_pct: parseFloat(e.target.value) } })}
                  className="w-full bg-gray-800 text-white rounded px-3 py-2 border border-gray-700"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => createMut.mutate(form)}
              disabled={createMut.isPending}
              className="px-4 py-2 bg-sky-700 hover:bg-sky-600 text-white text-sm rounded disabled:opacity-50"
            >
              {createMut.isPending ? 'Creating…' : 'Create Release'}
            </button>
            {createMut.isError && (
              <span className="text-red-400 text-sm self-center">Error creating release.</span>
            )}
          </div>
        </div>
      )}

      {/* Release list */}
      {isLoading ? (
        <LoadingSpinner />
      ) : releases.length === 0 ? (
        <p className="text-center text-gray-500 py-10">No release events. Create one above.</p>
      ) : (
        <div className="space-y-3">
          {releases.map((rel) => (
            <ReleaseCard
              key={rel.id}
              release={rel}
              agents={agents}
              canWrite={canWrite}
              canRun={canRun}
              onDelete={() => deleteMut.mutate(rel.id)}
              onSimulate={() => simulateMut.mutate(rel.id)}
              isSimulating={simulateMut.isPending}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ReleaseCard({
  release,
  agents,
  canWrite,
  canRun,
  onDelete,
  onSimulate,
  isSimulating,
}: {
  release: CBRNRelease
  agents: CBRNAgent[]
  canWrite: boolean
  canRun: boolean
  onDelete: () => void
  onSimulate: () => void
  isSimulating: boolean
}) {
  const agent = agents.find((a) => a.id === release.agent_id)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{agent ? CATEGORY_ICON[agent.category] : '❓'}</span>
          <div>
            <div className="text-white text-sm font-semibold">
              {release.label || `Release — ${release.agent_id}`}
            </div>
            <div className="text-xs text-gray-400">
              {agent?.name ?? release.agent_id} · {release.quantity_kg} kg ·{' '}
              {release.duration_min} min ·{' '}
              {release.latitude.toFixed(4)}°, {release.longitude.toFixed(4)}°
            </div>
          </div>
        </div>
        <div className="flex gap-2 items-center">
          {canRun && (
            <button
              onClick={onSimulate}
              disabled={isSimulating}
              className="px-3 py-1 text-xs bg-indigo-700 hover:bg-indigo-600 text-white rounded disabled:opacity-50"
            >
              {isSimulating ? '⏳ Running…' : '🌬️ Simulate'}
            </button>
          )}
          {canWrite && (
            <button
              onClick={onDelete}
              className="px-3 py-1 text-xs bg-red-900 hover:bg-red-800 text-red-200 rounded"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <div className="mt-3 flex gap-4 text-xs text-gray-400 flex-wrap">
        <span>💨 {release.met.wind_speed_ms} m/s from {release.met.wind_direction_deg}°</span>
        <span>🌡 {release.met.temperature_c}°C</span>
        <span>📊 Stability: {release.met.stability_class}</span>
        <span>🏙 Pop: {release.population_density_per_km2.toLocaleString()}/km²</span>
        <span>📅 {new Date(release.created_at).toLocaleString()}</span>
      </div>
    </div>
  )
}

// ── Dispersion Results Tab ───────────────────────────────────────────────────

function DispersionTab({ canRun }: { canRun: boolean }) {
  const { data: releases = [] } = useQuery({
    queryKey: ['cbrn-releases'],
    queryFn: () => cbrnApi.listReleases(),
  })
  const [selectedReleaseId, setSelectedReleaseId] = useState<string | null>(null)
  const [simResult, setSimResult] = useState<DispersionSimulation | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSimulate(releaseId: string) {
    setIsRunning(true)
    setError(null)
    setSelectedReleaseId(releaseId)
    try {
      const result = await cbrnApi.simulate(releaseId)
      setSimResult(result)
    } catch {
      setError('Simulation failed. Check service logs.')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="flex gap-6">
      {/* Left: release selector */}
      <div className="w-72 shrink-0">
        <h3 className="text-white text-sm font-semibold mb-3">Select Release to Simulate</h3>
        {releases.length === 0 ? (
          <p className="text-gray-500 text-sm">No releases found. Create one in the Release Planner tab.</p>
        ) : (
          <div className="space-y-2">
            {releases.map((rel) => (
              <div
                key={rel.id}
                className={`rounded-lg border p-3 cursor-pointer transition-colors ${
                  selectedReleaseId === rel.id
                    ? 'border-sky-600 bg-gray-800'
                    : 'border-gray-800 bg-gray-900 hover:border-gray-600'
                }`}
                onClick={() => setSelectedReleaseId(rel.id)}
              >
                <div className="text-white text-xs font-medium">{rel.label || rel.agent_id}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {rel.quantity_kg} kg · {rel.latitude.toFixed(3)}°, {rel.longitude.toFixed(3)}°
                </div>
              </div>
            ))}
          </div>
        )}

        {canRun && selectedReleaseId && (
          <button
            onClick={() => handleSimulate(selectedReleaseId)}
            disabled={isRunning}
            className="mt-4 w-full px-4 py-2 bg-indigo-700 hover:bg-indigo-600 text-white text-sm rounded disabled:opacity-50"
          >
            {isRunning ? '⏳ Running simulation…' : '🌬️ Run Dispersion Model'}
          </button>
        )}
        {error && <p className="mt-2 text-red-400 text-xs">{error}</p>}
      </div>

      {/* Right: simulation result */}
      <div className="flex-1 min-w-0">
        {!simResult ? (
          <div className="flex items-center justify-center h-48 text-gray-500 text-sm">
            Select a release and run the dispersion model to see results.
          </div>
        ) : (
          <DispersionResultPanel result={simResult} />
        )}
      </div>
    </div>
  )
}

function DispersionResultPanel({ result }: { result: DispersionSimulation }) {
  const totalCasualties = result.total_estimated_casualties

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-white font-bold text-base">Dispersion Simulation Result</h3>
          <span className="text-xs text-gray-400">
            {new Date(result.simulated_at).toLocaleString()}
          </span>
        </div>
        <p className="text-sm text-gray-300 leading-relaxed">{result.summary}</p>
      </div>

      {/* Plume metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Max Downwind', value: `${result.max_downwind_km.toFixed(2)} km`, color: 'text-orange-300' },
          { label: 'Max Crosswind', value: `${result.max_crosswind_km.toFixed(2)} km`, color: 'text-yellow-300' },
          { label: 'Plume Area', value: `${result.plume_area_km2.toFixed(2)} km²`, color: 'text-sky-300' },
          { label: 'Est. Affected', value: totalCasualties.toLocaleString(), color: totalCasualties > 1000 ? 'text-red-400' : 'text-orange-300' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded p-3">
            <div className="text-xs text-gray-400 mb-1">{label}</div>
            <div className={`text-lg font-bold ${color}`}>{value}</div>
          </div>
        ))}
      </div>

      {/* Met summary */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h4 className="text-gray-300 text-sm font-semibold mb-2">Meteorological Conditions</h4>
        <div className="flex gap-6 text-xs text-gray-400 flex-wrap">
          <span>💨 Wind: {result.wind_speed_ms} m/s from {result.wind_direction_deg}°</span>
          <span>📊 Stability: Class {result.stability_class}</span>
          <span>🌡 Temp: {result.metadata.temperature_c as number}°C</span>
          <span>💧 RH: {result.metadata.rh_pct as number}%</span>
          <span>⬆ Mixing height: {result.metadata.mixing_height_m as number} m</span>
        </div>
      </div>

      {/* Hazard zones */}
      {(result.lethal_zone || result.injury_zone || result.idlh_zone) && (
        <div className="space-y-3">
          <h4 className="text-white text-sm font-semibold">Hazard Zones</h4>
          {[result.lethal_zone, result.injury_zone, result.idlh_zone]
            .filter(Boolean)
            .map((zone) => {
              const z = zone!
              const colors: Record<string, { border: string; badge: string }> = {
                'Lethal Zone':  { border: 'border-red-700',    badge: 'bg-red-900 text-red-200' },
                'Injury Zone':  { border: 'border-orange-700', badge: 'bg-orange-900 text-orange-200' },
                'IDLH Zone':    { border: 'border-yellow-700', badge: 'bg-yellow-900 text-yellow-200' },
                'Hazard Zone':  { border: 'border-orange-700', badge: 'bg-orange-900 text-orange-200' },
              }
              const c = colors[z.label] ?? { border: 'border-gray-700', badge: 'bg-gray-700 text-gray-200' }
              return (
                <div key={z.label} className={`bg-gray-900 border ${c.border} rounded-lg p-4`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${c.badge}`}>{z.label}</span>
                    <span className="text-sm font-bold text-white">
                      {z.estimated_casualties.toLocaleString()} est. casualties
                    </span>
                  </div>
                  <div className="flex gap-6 text-xs text-gray-400">
                    <span>Downwind: {z.max_downwind_km.toFixed(2)} km</span>
                    <span>Crosswind: {z.max_crosswind_km.toFixed(2)} km</span>
                    <span>Area: {z.area_km2.toFixed(2)} km²</span>
                    {z.contour && (
                      <span>Threshold: {z.contour.level_mg_m3.toExponential(2)} mg/m³</span>
                    )}
                  </div>
                </div>
              )
            })}
        </div>
      )}

      {/* Plume contours summary */}
      {result.contours.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h4 className="text-gray-300 text-sm font-semibold mb-2">
            Plume Contours ({result.contours.length} polygons)
          </h4>
          <div className="space-y-1">
            {result.contours.map((c, i) => (
              <div key={i} className="flex justify-between text-xs text-gray-400">
                <span>{c.label}</span>
                <span className="font-mono">{c.level_mg_m3.toExponential(2)} mg/m³ · {c.coordinates.length} vertices</span>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500">
            GeoJSON polygon coordinates available for map overlay integration (MapLibre GL).
          </p>
        </div>
      )}

      {/* Protective actions */}
      <div className="bg-gray-900 border border-green-800 rounded-lg p-4">
        <h4 className="text-green-400 text-sm font-semibold mb-1">Recommended Protective Actions</h4>
        <p className="text-sm text-green-200">{result.protective_actions}</p>
      </div>
    </div>
  )
}

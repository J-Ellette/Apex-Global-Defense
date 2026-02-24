import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { LoadingSpinner } from '../../shared/components/LoadingSpinner'
import { scenarioApi, simApi } from '../../shared/api/endpoints'
import type {
  Scenario,
  CreateScenarioRequest,
  ClassificationLevel,
  SimulationRun,
  SimMode,
  SimEvent,
  AfterActionReport,
  ScenarioRunConfig,
} from '../../shared/api/types'

export default function SimulationPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const canWrite = useAuthStore((s) => s.hasPermission('scenario:write'))
  const canRun = useAuthStore((s) => s.hasPermission('simulation:run'))
  const queryClient = useQueryClient()

  const [showCreate, setShowCreate] = useState(false)
  const [branchSource, setBranchSource] = useState<Scenario | null>(null)
  const [runTarget, setRunTarget] = useState<Scenario | null>(null)
  const [activeRun, setActiveRun] = useState<SimulationRun | null>(null)

  const { data: scenarios, isLoading, error } = useQuery({
    queryKey: ['scenarios'],
    queryFn: () => scenarioApi.listScenarios(),
    staleTime: 2 * 60 * 1000,
  })

  const createMutation = useMutation({
    mutationFn: (req: CreateScenarioRequest) => scenarioApi.createScenario(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
      setShowCreate(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => scenarioApi.deleteScenario(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scenarios'] }),
  })

  const branchMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      scenarioApi.branchScenario(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios'] })
      setBranchSource(null)
    },
  })

  const startRunMutation = useMutation({
    mutationFn: ({ scenarioId, config }: { scenarioId: string; config: ScenarioRunConfig }) =>
      simApi.startRun(scenarioId, { config }),
    onSuccess: (run) => {
      setActiveRun(run)
      setRunTarget(null)
      queryClient.invalidateQueries({ queryKey: ['sim-runs', run.scenario_id] })
    },
  })

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Scenario Management</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Create, manage, and run planning scenarios
            </p>
          </div>
          {canWrite && (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 rounded bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition-colors"
            >
              <span aria-hidden>＋</span> New Scenario
            </button>
          )}
        </div>

        {/* Active run panel */}
        {activeRun && (
          <div className="border-b border-gray-800 bg-gray-900/60">
            <SimRunPanel
              run={activeRun}
              onRunUpdate={setActiveRun}
              onClose={() => setActiveRun(null)}
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && (
            <div className="flex justify-center py-16">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-400 text-center py-16">Failed to load scenarios.</p>
          )}

          {scenarios && scenarios.length === 0 && !isLoading && (
            <div className="text-center py-16 text-gray-500">
              <p className="text-4xl mb-3">⚔️</p>
              <p className="text-sm">No scenarios yet. Create one to get started.</p>
            </div>
          )}

          {scenarios && scenarios.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {scenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  canWrite={canWrite}
                  canRun={canRun}
                  onDelete={(id) => deleteMutation.mutate(id)}
                  onBranch={(s) => setBranchSource(s)}
                  onRun={(s) => setRunTarget(s)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      <ClassificationBanner level={classification} />

      {showCreate && (
        <ScenarioFormModal
          title="New Scenario"
          submitLabel="Create"
          isLoading={createMutation.isPending}
          error={createMutation.error?.message}
          onSubmit={(data) => createMutation.mutate(data)}
          onClose={() => setShowCreate(false)}
        />
      )}

      {branchSource && (
        <BranchModal
          source={branchSource}
          isLoading={branchMutation.isPending}
          error={branchMutation.error?.message}
          onSubmit={(name) => branchMutation.mutate({ id: branchSource.id, name })}
          onClose={() => setBranchSource(null)}
        />
      )}

      {runTarget && (
        <SimRunModal
          scenario={runTarget}
          isLoading={startRunMutation.isPending}
          error={startRunMutation.error?.message}
          onSubmit={(config) =>
            startRunMutation.mutate({ scenarioId: runTarget.id, config })
          }
          onClose={() => setRunTarget(null)}
        />
      )}
    </div>
  )
}

// ── SimRunPanel ───────────────────────────────────────────────────────────────

function SimRunPanel({
  run,
  onRunUpdate,
  onClose,
}: {
  run: SimulationRun
  onRunUpdate: (run: SimulationRun) => void
  onClose: () => void
}) {
  const [showReport, setShowReport] = useState(false)

  const pauseMutation = useMutation({
    mutationFn: () => simApi.pauseRun(run.id),
    onSuccess: onRunUpdate,
  })

  const resumeMutation = useMutation({
    mutationFn: () => simApi.resumeRun(run.id),
    onSuccess: onRunUpdate,
  })

  const stepMutation = useMutation({
    mutationFn: () => simApi.stepRun(run.id),
  })

  const { data: events } = useQuery({
    queryKey: ['sim-events', run.id],
    queryFn: () => simApi.getEvents(run.id),
    refetchInterval: run.status === 'running' ? 3000 : false,
    enabled: run.status !== 'queued',
  })

  const { data: report } = useQuery({
    queryKey: ['sim-report', run.id],
    queryFn: () => simApi.getReport(run.id),
    enabled: showReport && run.status === 'complete',
  })

  const statusColor: Record<string, string> = {
    queued: 'text-yellow-400',
    running: 'text-sky-400',
    paused: 'text-orange-400',
    complete: 'text-green-400',
    error: 'text-red-400',
  }

  return (
    <div className="px-6 py-4 space-y-4">
      {/* Run header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Active Run</p>
            <p className="text-sm font-mono text-gray-300">{run.id.slice(0, 8)}…</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Mode</p>
            <p className="text-sm font-semibold text-white uppercase">{run.mode.replaceAll('_', ' ')}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Status</p>
            <p className={`text-sm font-semibold uppercase ${statusColor[run.status] ?? 'text-gray-400'}`}>
              {run.status}
            </p>
          </div>
          <div className="flex-1 min-w-[120px]">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Progress</p>
            <div className="h-2 rounded-full bg-gray-700 overflow-hidden">
              <div
                className="h-full bg-sky-500 transition-all duration-500"
                style={{ width: `${Math.round(run.progress * 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{Math.round(run.progress * 100)}%</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {run.mode === 'turn_based' && run.status !== 'complete' && (
            <button
              onClick={() => stepMutation.mutate()}
              disabled={stepMutation.isPending}
              className="flex items-center gap-1 rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              {stepMutation.isPending ? <LoadingSpinner size="sm" /> : '▶'}
              Step Turn
            </button>
          )}
          {run.status === 'running' && (
            <button
              onClick={() => pauseMutation.mutate()}
              disabled={pauseMutation.isPending}
              className="flex items-center gap-1 rounded bg-orange-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-orange-500 disabled:opacity-50 transition-colors"
            >
              ⏸ Pause
            </button>
          )}
          {run.status === 'paused' && (
            <button
              onClick={() => resumeMutation.mutate()}
              disabled={resumeMutation.isPending}
              className="flex items-center gap-1 rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-50 transition-colors"
            >
              ▶ Resume
            </button>
          )}
          {run.status === 'complete' && (
            <button
              onClick={() => setShowReport((v) => !v)}
              className="flex items-center gap-1 rounded bg-green-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-600 transition-colors"
            >
              📋 {showReport ? 'Hide' : 'After-Action Report'}
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded border border-gray-700 px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
          >
            ✕ Close
          </button>
        </div>
      </div>

      {/* After-action report */}
      {showReport && report && <AfterActionReportPanel report={report} />}

      {/* Event feed */}
      {events && events.length > 0 && !showReport && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Recent Events</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
            {[...events].reverse().slice(0, 9).map((event, i) => (
              <EventChip key={i} event={event} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── AfterActionReportPanel ────────────────────────────────────────────────────

function AfterActionReportPanel({ report }: { report: AfterActionReport }) {
  return (
    <div className="rounded-lg border border-green-900/50 bg-green-950/20 p-4 space-y-4">
      <h3 className="text-sm font-semibold text-green-300">After-Action Report</h3>
      <p className="text-sm text-gray-300">{report.executive_summary}</p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Duration" value={`${report.duration_hours}h`} />
        <StatCard label="Total Turns" value={report.total_turns?.toString() ?? '—'} />
        <StatCard label="Blue Objectives" value={report.blue_objectives_captured.toString()} />
        <StatCard label="Red Objectives" value={report.red_objectives_captured.toString()} />
        <StatCard label="Blue Casualties" value={report.blue_casualties.toString()} color="text-sky-400" />
        <StatCard label="Red Casualties" value={report.red_casualties.toString()} color="text-red-400" />
      </div>

      {report.mc_result && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
            Monte Carlo — {report.mc_result.runs_completed} runs
          </p>
          {Object.entries(report.mc_result.objective_outcomes).map(([obj, outcome]) => (
            <div key={obj} className="mb-2">
              <p className="text-xs text-gray-400 mb-1 capitalize">{obj} objective</p>
              <div className="flex h-3 rounded-full overflow-hidden">
                <div
                  className="bg-sky-600"
                  style={{ width: `${outcome.blue_win_pct}%` }}
                  title={`Blue ${outcome.blue_win_pct}%`}
                />
                <div
                  className="bg-gray-600"
                  style={{ width: `${outcome.contested_pct}%` }}
                  title={`Contested ${outcome.contested_pct}%`}
                />
                <div
                  className="bg-red-600"
                  style={{ width: `${outcome.red_win_pct}%` }}
                  title={`Red ${outcome.red_win_pct}%`}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-0.5">
                <span>Blue {outcome.blue_win_pct}%</span>
                <span>Contested {outcome.contested_pct}%</span>
                <span>Red {outcome.red_win_pct}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color = 'text-white' }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded border border-gray-800 bg-gray-900/60 px-3 py-2">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className={`text-sm font-semibold ${color}`}>{value}</p>
    </div>
  )
}

function EventChip({ event }: { event: SimEvent }) {
  const typeColors: Record<string, string> = {
    ENGAGEMENT: 'border-red-800 text-red-300',
    CASUALTY: 'border-orange-800 text-orange-300',
    OBJECTIVE_CAPTURED: 'border-green-800 text-green-300',
    AIRSTRIKE: 'border-purple-800 text-purple-300',
    UNIT_MOVE: 'border-gray-700 text-gray-400',
    PHASE_CHANGE: 'border-sky-800 text-sky-300',
  }
  const cls = typeColors[event.event_type] ?? 'border-gray-700 text-gray-400'
  return (
    <div className={`rounded border px-2 py-1 text-xs ${cls}`}>
      <span className="font-medium">{event.event_type.replaceAll('_', ' ')}</span>
      {event.turn_number != null && (
        <span className="ml-1 text-gray-500">T{event.turn_number}</span>
      )}
      {event.payload?.outcome && (
        <p className="text-gray-500 truncate">{event.payload.outcome as string}</p>
      )}
    </div>
  )
}

// ── ScenarioCard ──────────────────────────────────────────────────────────────

function ScenarioCard({
  scenario,
  canWrite,
  canRun,
  onDelete,
  onBranch,
  onRun,
}: {
  scenario: Scenario
  canWrite: boolean
  canRun: boolean
  onDelete: (id: string) => void
  onBranch: (scenario: Scenario) => void
  onRun: (scenario: Scenario) => void
}) {
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate">{scenario.name}</h3>
          {scenario.parent_id && (
            <p className="text-xs text-sky-400 mt-0.5">Branched scenario</p>
          )}
          {scenario.description && (
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{scenario.description}</p>
          )}
        </div>
        <ClassificationPill level={scenario.classification as ClassificationLevel} />
      </div>

      {scenario.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {scenario.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center rounded bg-gray-800 px-1.5 py-0.5 text-xs text-gray-400"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between mt-auto pt-2 border-t border-gray-800">
        <span className="text-xs text-gray-600">
          {new Date(scenario.updated_at).toLocaleDateString()}
        </span>
        <div className="flex gap-2 items-center">
          {canRun && (
            <button
              onClick={() => onRun(scenario)}
              title="Run this scenario"
              className="text-xs text-green-400 hover:text-green-300 transition-colors font-semibold"
            >
              ▶ Run
            </button>
          )}
          {canWrite && (
            <>
              <button
                onClick={() => onBranch(scenario)}
                title="Branch this scenario"
                className="text-xs text-sky-400 hover:text-sky-300 transition-colors"
              >
                Branch
              </button>
              <button
                onClick={() => onDelete(scenario.id)}
                title="Delete scenario"
                className="text-xs text-red-400 hover:text-red-300 transition-colors"
              >
                Delete
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ── SimRunModal ───────────────────────────────────────────────────────────────

function SimRunModal({
  scenario,
  isLoading,
  error,
  onSubmit,
  onClose,
}: {
  scenario: Scenario
  isLoading: boolean
  error?: string
  onSubmit: (config: ScenarioRunConfig) => void
  onClose: () => void
}) {
  const [mode, setMode] = useState<SimMode>('turn_based')
  const [durationHours, setDurationHours] = useState(48)
  const [mcRuns, setMcRuns] = useState(500)
  const [weather, setWeather] = useState('clear')
  const [fogOfWar, setFogOfWar] = useState(true)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      mode,
      blue_force_ids: [],
      red_force_ids: [],
      start_time: new Date().toISOString(),
      duration_hours: durationHours,
      monte_carlo_runs: mcRuns,
      weather_preset: weather,
      fog_of_war: fogOfWar,
      terrain_effects: true,
    })
  }

  return (
    <ModalOverlay onClose={onClose}>
      <h2 className="text-lg font-bold text-white mb-1">Run Scenario</h2>
      <p className="text-sm text-gray-400 mb-4">
        Configure and launch a simulation run for{' '}
        <span className="text-white font-medium">{scenario.name}</span>
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p className="rounded border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}

        <FormField label="Simulation Mode">
          <div className="grid grid-cols-3 gap-2">
            {SIM_MODES.map((m) => (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className={[
                  'rounded border px-3 py-2.5 text-left text-xs transition-colors',
                  mode === m.value
                    ? 'border-sky-500 bg-sky-900/30 text-sky-300'
                    : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-600',
                ].join(' ')}
              >
                <div className="text-lg mb-0.5">{m.icon}</div>
                <div className="font-semibold">{m.label}</div>
                <div className="text-gray-500 mt-0.5">{m.desc}</div>
              </button>
            ))}
          </div>
        </FormField>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Duration (hours)">
            <input
              type="number"
              min={1}
              max={720}
              value={durationHours}
              onChange={(e) => setDurationHours(Number(e.target.value))}
              className={INPUT_CLS}
            />
          </FormField>
          {mode === 'monte_carlo' && (
            <FormField label="MC Runs">
              <input
                type="number"
                min={10}
                max={10000}
                step={10}
                value={mcRuns}
                onChange={(e) => setMcRuns(Number(e.target.value))}
                className={INPUT_CLS}
              />
            </FormField>
          )}
          <FormField label="Weather">
            <select
              value={weather}
              onChange={(e) => setWeather(e.target.value)}
              className={INPUT_CLS}
            >
              <option value="clear">Clear</option>
              <option value="overcast">Overcast</option>
              <option value="rain">Rain</option>
              <option value="fog">Fog</option>
              <option value="storm">Storm</option>
              <option value="snow">Snow</option>
            </select>
          </FormField>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="fog-of-war"
            checked={fogOfWar}
            onChange={(e) => setFogOfWar(e.target.checked)}
            className="rounded border-gray-600 bg-gray-800 text-sky-500"
          />
          <label htmlFor="fog-of-war" className="text-sm text-gray-300">
            Enable fog of war
          </label>
        </div>

        <div className="flex gap-3 pt-2 justify-end">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center gap-2 rounded bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-50 transition-colors"
          >
            {isLoading ? <LoadingSpinner size="sm" /> : '▶'}
            Launch Run
          </button>
        </div>
      </form>
    </ModalOverlay>
  )
}

// ── ScenarioFormModal ─────────────────────────────────────────────────────────

interface ScenarioFormModalProps {
  title: string
  submitLabel: string
  isLoading: boolean
  error?: string
  onSubmit: (data: CreateScenarioRequest) => void
  onClose: () => void
}

function ScenarioFormModal({ title, submitLabel, isLoading, error, onSubmit, onClose }: ScenarioFormModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [classification, setClassification] = useState<ClassificationLevel>('UNCLASS')
  const [tags, setTags] = useState('')
  const [showAIBuilder, setShowAIBuilder] = useState(false)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      name,
      description: description || undefined,
      classification,
      tags: tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
    })
  }

  if (showAIBuilder) {
    return (
      <AIScenarioBuilderModal
        onApply={(generated) => {
          setName(generated.name)
          setDescription(generated.description ?? '')
          setTags(generated.tags?.join(', ') ?? '')
          setShowAIBuilder(false)
        }}
        onClose={() => setShowAIBuilder(false)}
      />
    )
  }

  return (
    <ModalOverlay onClose={onClose}>
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-lg font-bold text-white">{title}</h2>
        <button
          type="button"
          onClick={() => setShowAIBuilder(true)}
          className="flex items-center gap-1.5 rounded border border-sky-700 bg-sky-900/20 px-3 py-1.5 text-xs text-sky-300 hover:bg-sky-900/40 transition-colors"
        >
          🤖 Generate with AI
        </button>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <p className="rounded border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
        <FormField label="Name" required>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={INPUT_CLS}
            placeholder="Operation Thunder"
          />
        </FormField>
        <FormField label="Description">
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className={INPUT_CLS}
            placeholder="Brief scenario description…"
          />
        </FormField>
        <FormField label="Classification">
          <select
            value={classification}
            onChange={(e) => setClassification(e.target.value as ClassificationLevel)}
            className={INPUT_CLS}
          >
            <option value="UNCLASS">UNCLASSIFIED</option>
            <option value="FOUO">FOUO</option>
            <option value="SECRET">SECRET</option>
            <option value="TOP_SECRET">TOP SECRET</option>
            <option value="TS_SCI">TS/SCI</option>
          </select>
        </FormField>
        <FormField label="Tags (comma-separated)">
          <input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className={INPUT_CLS}
            placeholder="exercise, nato, 2026"
          />
        </FormField>
        <div className="flex gap-3 pt-2 justify-end">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center gap-2 rounded bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-50 transition-colors"
          >
            {isLoading && <LoadingSpinner size="sm" />}
            {submitLabel}
          </button>
        </div>
      </form>
    </ModalOverlay>
  )
}

// ── AIScenarioBuilderModal ────────────────────────────────────────────────────

function AIScenarioBuilderModal({
  onApply,
  onClose,
}: {
  onApply: (scenario: Partial<CreateScenarioRequest>) => void
  onClose: () => void
}) {
  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<Partial<CreateScenarioRequest> | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    if (!prompt.trim()) return
    setIsGenerating(true)
    setAiError(null)
    try {
      // In production this calls POST /ai/scenario/generate via the ai-svc.
      // For now we use a deterministic stub that parses keywords from the prompt.
      const generated = generateScenarioFromPrompt(prompt)
      setResult(generated)
    } catch {
      setAiError('AI service unavailable. Check your AI provider configuration in Administration.')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <ModalOverlay onClose={onClose}>
      <h2 className="text-lg font-bold text-white mb-1">AI Scenario Builder</h2>
      <p className="text-sm text-gray-400 mb-4">
        Describe the scenario in plain language and AI will generate the configuration.
        Requires an AI provider configured in Administration.
      </p>
      <form onSubmit={handleGenerate} className="space-y-4">
        <FormField label="Describe the scenario">
          <textarea
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className={INPUT_CLS}
            placeholder="A NATO-Russia conventional conflict in Eastern Europe, beginning with a Russian incursion into the Baltic states. Duration 72 hours. Blue forces defend, Red forces attack."
          />
        </FormField>

        {aiError && (
          <p className="rounded border border-yellow-700 bg-yellow-900/20 px-3 py-2 text-sm text-yellow-300">
            {aiError}
          </p>
        )}

        {result && (
          <div className="rounded border border-sky-800 bg-sky-900/20 p-3 space-y-1">
            <p className="text-xs text-sky-400 font-semibold uppercase tracking-wider">Generated</p>
            <p className="text-sm text-white font-medium">{result.name}</p>
            {result.description && (
              <p className="text-xs text-gray-400">{result.description}</p>
            )}
            {result.tags && result.tags.length > 0 && (
              <p className="text-xs text-gray-500">Tags: {result.tags.join(', ')}</p>
            )}
          </div>
        )}

        <div className="flex gap-3 pt-2 justify-end">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
            Cancel
          </button>
          {result ? (
            <button
              type="button"
              onClick={() => onApply(result)}
              className="rounded bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition-colors"
            >
              Apply
            </button>
          ) : (
            <button
              type="submit"
              disabled={isGenerating || !prompt.trim()}
              className="flex items-center gap-2 rounded bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-50 transition-colors"
            >
              {isGenerating ? <LoadingSpinner size="sm" /> : '🤖'}
              Generate
            </button>
          )}
        </div>
      </form>
    </ModalOverlay>
  )
}

/** Deterministic stub for AI scenario generation (used until ai-svc is wired up). */
function generateScenarioFromPrompt(prompt: string): Partial<CreateScenarioRequest> {
  const lower = prompt.toLowerCase()
  const tags: string[] = []
  if (lower.includes('nato')) tags.push('nato')
  if (lower.includes('russia') || lower.includes('russian')) tags.push('russia')
  if (lower.includes('china') || lower.includes('chinese')) tags.push('china')
  if (lower.includes('conventional')) tags.push('conventional')
  if (lower.includes('cyber')) tags.push('cyber')
  if (lower.includes('cbrn')) tags.push('cbrn')
  if (lower.includes('exercise')) tags.push('exercise')
  if (lower.includes('baltic')) tags.push('baltics', 'eastern-europe')
  const firstSentence = prompt.split(/[.!?]/)[0].trim()
  return {
    name: firstSentence.slice(0, 80) || 'AI-Generated Scenario',
    description: prompt.slice(0, 500),
    tags,
    classification: 'UNCLASS',
  }
}

// ── BranchModal ───────────────────────────────────────────────────────────────

function BranchModal({
  source,
  isLoading,
  error,
  onSubmit,
  onClose,
}: {
  source: Scenario
  isLoading: boolean
  error?: string
  onSubmit: (name: string) => void
  onClose: () => void
}) {
  const [name, setName] = useState(`${source.name} (branch)`)

  return (
    <ModalOverlay onClose={onClose}>
      <h2 className="text-lg font-bold text-white mb-1">Branch Scenario</h2>
      <p className="text-sm text-gray-400 mb-4">
        Creates a copy of <span className="text-white font-medium">{source.name}</span> with a new name.
      </p>
      <form
        onSubmit={(e) => { e.preventDefault(); onSubmit(name) }}
        className="space-y-4"
      >
        {error && (
          <p className="rounded border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-300">
            {error}
          </p>
        )}
        <FormField label="Branch Name" required>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={INPUT_CLS}
          />
        </FormField>
        <div className="flex gap-3 pt-2 justify-end">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center gap-2 rounded bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-50 transition-colors"
          >
            {isLoading && <LoadingSpinner size="sm" />}
            Create Branch
          </button>
        </div>
      </form>
    </ModalOverlay>
  )
}

// ── Shared primitives ─────────────────────────────────────────────────────────

function ModalOverlay({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="w-full max-w-md rounded-lg border border-gray-700 bg-gray-900 p-6 shadow-xl max-h-[90vh] overflow-y-auto">
        {children}
      </div>
    </div>
  )
}

function FormField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}

const CLASSIFICATION_PILL: Record<ClassificationLevel, string> = {
  UNCLASS:    'bg-green-900/40 text-green-300 ring-green-800',
  FOUO:       'bg-yellow-900/40 text-yellow-300 ring-yellow-800',
  SECRET:     'bg-red-900/40 text-red-300 ring-red-800',
  TOP_SECRET: 'bg-orange-900/40 text-orange-300 ring-orange-800',
  TS_SCI:     'bg-purple-900/40 text-purple-300 ring-purple-800',
}

function ClassificationPill({ level }: { level: ClassificationLevel }) {
  return (
    <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ring-1 shrink-0 ${CLASSIFICATION_PILL[level] ?? CLASSIFICATION_PILL.UNCLASS}`}>
      {level}
    </span>
  )
}

const SIM_MODES: { value: SimMode; label: string; icon: string; desc: string }[] = [
  { value: 'turn_based', label: 'Turn-Based', icon: '♟️', desc: 'Step through each turn manually' },
  { value: 'real_time', label: 'Real-Time', icon: '⏱️', desc: 'Continuous time simulation' },
  { value: 'monte_carlo', label: 'Monte Carlo', icon: '🎲', desc: 'Probabilistic multi-run analysis' },
]

const INPUT_CLS = 'w-full rounded bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500'

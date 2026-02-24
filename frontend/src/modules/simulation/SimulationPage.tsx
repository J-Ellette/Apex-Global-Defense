import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { LoadingSpinner } from '../../shared/components/LoadingSpinner'
import { scenarioApi } from '../../shared/api/endpoints'
import type { Scenario, CreateScenarioRequest, ClassificationLevel } from '../../shared/api/types'

export default function SimulationPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const canWrite = useAuthStore((s) => s.hasPermission('scenario:write'))
  const queryClient = useQueryClient()

  const [showCreate, setShowCreate] = useState(false)
  const [branchSource, setBranchSource] = useState<Scenario | null>(null)

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

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Scenario Management</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Create, manage, and branch planning scenarios
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
                  onDelete={(id) => deleteMutation.mutate(id)}
                  onBranch={(s) => setBranchSource(s)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      <ClassificationBanner level={classification} />

      {/* Create scenario modal */}
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

      {/* Branch scenario modal */}
      {branchSource && (
        <BranchModal
          source={branchSource}
          isLoading={branchMutation.isPending}
          error={branchMutation.error?.message}
          onSubmit={(name) => branchMutation.mutate({ id: branchSource.id, name })}
          onClose={() => setBranchSource(null)}
        />
      )}
    </div>
  )
}

// ── ScenarioCard ──────────────────────────────────────────────────────────────

function ScenarioCard({
  scenario,
  canWrite,
  onDelete,
  onBranch,
}: {
  scenario: Scenario
  canWrite: boolean
  onDelete: (id: string) => void
  onBranch: (scenario: Scenario) => void
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
        {canWrite && (
          <div className="flex gap-2">
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
          </div>
        )}
      </div>
    </div>
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

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      name,
      description: description || undefined,
      classification,
      tags: tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
    })
  }

  return (
    <ModalOverlay onClose={onClose}>
      <h2 className="text-lg font-bold text-white mb-4">{title}</h2>
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

// ── Shared sub-components ─────────────────────────────────────────────────────

function ModalOverlay({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="w-full max-w-md rounded-lg border border-gray-700 bg-gray-900 p-6 shadow-xl">
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

const INPUT_CLS = 'w-full rounded bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500'

import { useEffect, useState } from 'react'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { gisClient } from '../../shared/api/gisClient'
import type {
  CreateIntegrationConfigRequest,
  IntegrationConfig,
  IntegrationType,
  LayerType,
} from '../../shared/api/types/gis'
import { useAIConfigStore } from './hooks/useAIConfigStore'

type Tab = 'ai-config' | 'gis-integrations'

const ALL_LAYERS: LayerType[] = [
  'UNITS', 'INTEL_ITEMS', 'CBRN_RELEASES', 'CIVILIAN_ZONES',
  'SANCTION_TARGETS', 'TRADE_ROUTES', 'NARRATIVE_THREATS', 'TERROR_SITES', 'ASYM_CELLS',
]

export default function AdminPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const isAdmin = useAuthStore((s) => s.hasRole('admin'))
  const [activeTab, setActiveTab] = useState<Tab>('ai-config')

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-950">
        <ClassificationBanner level={classification} />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-red-400 text-sm">Access denied — admin role required.</p>
        </main>
        <ClassificationBanner level={classification} />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white">Administration</h1>
          <p className="text-sm text-gray-400 mt-0.5">System configuration and management</p>
          <div className="flex gap-2 mt-3">
            {([['ai-config', 'AI Configuration'], ['gis-integrations', 'GIS Integrations']] as [Tab, string][]).map(([tab, label]) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={[
                  'px-3 py-1.5 rounded text-sm font-medium transition-colors',
                  activeTab === tab
                    ? 'bg-sky-700 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700',
                ].join(' ')}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 max-w-4xl">
          {activeTab === 'ai-config' && <AIConfigPanel />}
          {activeTab === 'gis-integrations' && <GISIntegrationsPanel />}
        </div>
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

// ── AI Config Panel ───────────────────────────────────────────────────────────

type AIProvider = 'ollama' | 'openai' | 'anthropic' | 'azure_openai'

function AIConfigPanel() {
  const { config, setConfig } = useAIConfigStore()
  const [saved, setSaved] = useState(false)

  function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setConfig(config)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <section>
      <h2 className="text-base font-semibold text-white mb-1">AI Provider Configuration</h2>
      <p className="text-sm text-gray-400 mb-6">
        Configure the AI provider used for scenario generation, threat assessment, and intel
        summarization. All API keys are stored locally in this browser session only.
      </p>

      <form onSubmit={handleSave} className="space-y-5">
        {/* Provider selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Provider</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {PROVIDER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setConfig({ ...config, provider: opt.value })}
                className={[
                  'rounded border px-3 py-3 text-sm text-left transition-colors',
                  config.provider === opt.value
                    ? 'border-sky-500 bg-sky-900/30 text-sky-300'
                    : 'border-gray-700 bg-gray-900 text-gray-300 hover:border-gray-500',
                ].join(' ')}
              >
                <div className="text-xl mb-1">{opt.icon}</div>
                <div className="font-medium">{opt.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{opt.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Provider-specific fields */}
        {config.provider === 'ollama' && (
          <OllamaFields config={config} onChange={(c) => setConfig({ ...config, ...c })} />
        )}
        {(config.provider === 'openai' || config.provider === 'anthropic') && (
          <APIKeyFields
            config={config}
            onChange={(c) => setConfig({ ...config, ...c })}
            keyLabel={config.provider === 'openai' ? 'OpenAI API Key' : 'Anthropic API Key'}
            keyPlaceholder={config.provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
          />
        )}
        {config.provider === 'azure_openai' && (
          <AzureOpenAIFields config={config} onChange={(c) => setConfig({ ...config, ...c })} />
        )}

        {/* Non-AI fallback toggle */}
        <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-200">Non-AI fallback mode</p>
              <p className="text-xs text-gray-500 mt-0.5">
                When enabled, AI features degrade gracefully to deterministic alternatives.
                AI outputs are never shown without a fallback available.
              </p>
            </div>
            <Toggle
              checked={config.fallbackEnabled}
              onChange={(v) => setConfig({ ...config, fallbackEnabled: v })}
              label="Enable fallback"
            />
          </div>

          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-200">Show AI confidence scores</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Displays confidence/uncertainty markers on all AI-generated content.
              </p>
            </div>
            <Toggle
              checked={config.showConfidenceScores}
              onChange={(v) => setConfig({ ...config, showConfidenceScores: v })}
              label="Show confidence scores"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="rounded bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition-colors"
          >
            Save configuration
          </button>
          {saved && (
            <span className="text-sm text-green-400">✓ Configuration saved</span>
          )}
        </div>
      </form>
    </section>
  )
}

// ── Provider field sub-forms ──────────────────────────────────────────────────

interface AIConfig {
  provider: AIProvider
  ollamaUrl: string
  ollamaModel: string
  apiKey: string
  azureEndpoint: string
  azureDeployment: string
  azureApiKey: string
  fallbackEnabled: boolean
  showConfidenceScores: boolean
}

function OllamaFields({ config, onChange }: { config: AIConfig; onChange: (c: Partial<AIConfig>) => void }) {
  return (
    <div className="space-y-3">
      <p className="text-xs text-sky-400 bg-sky-900/20 border border-sky-900 rounded px-3 py-2">
        Ollama runs locally — no API key required. Supports air-gap deployment with local models.
      </p>
      <Field label="Ollama Server URL">
        <input
          value={config.ollamaUrl}
          onChange={(e) => onChange({ ollamaUrl: e.target.value })}
          placeholder="http://localhost:11434"
          className={INPUT}
        />
      </Field>
      <Field label="Model">
        <input
          value={config.ollamaModel}
          onChange={(e) => onChange({ ollamaModel: e.target.value })}
          placeholder="llama3.1:8b"
          className={INPUT}
        />
        <p className="text-xs text-gray-500 mt-1">
          Recommended: <code className="text-gray-400">llama3.1:8b</code> or{' '}
          <code className="text-gray-400">mistral:7b</code>
        </p>
      </Field>
    </div>
  )
}

function APIKeyFields({
  config,
  onChange,
  keyLabel,
  keyPlaceholder,
}: {
  config: AIConfig
  onChange: (c: Partial<AIConfig>) => void
  keyLabel: string
  keyPlaceholder: string
}) {
  return (
    <Field label={keyLabel}>
      <input
        type="password"
        value={config.apiKey}
        onChange={(e) => onChange({ apiKey: e.target.value })}
        placeholder={keyPlaceholder}
        autoComplete="off"
        className={INPUT}
      />
      <p className="text-xs text-gray-500 mt-1">Stored in browser session memory only — not persisted to localStorage and never sent to AGD backend servers. Keys are forwarded directly to the configured AI provider.</p>
    </Field>
  )
}

function AzureOpenAIFields({ config, onChange }: { config: AIConfig; onChange: (c: Partial<AIConfig>) => void }) {
  return (
    <div className="space-y-3">
      <Field label="Azure Endpoint">
        <input
          value={config.azureEndpoint}
          onChange={(e) => onChange({ azureEndpoint: e.target.value })}
          placeholder="https://my-resource.openai.azure.com/"
          className={INPUT}
        />
      </Field>
      <Field label="Deployment Name">
        <input
          value={config.azureDeployment}
          onChange={(e) => onChange({ azureDeployment: e.target.value })}
          placeholder="gpt-4o"
          className={INPUT}
        />
      </Field>
      <Field label="API Key">
        <input
          type="password"
          value={config.azureApiKey}
          onChange={(e) => onChange({ azureApiKey: e.target.value })}
          placeholder="••••••••••••••••"
          autoComplete="off"
          className={INPUT}
        />
      </Field>
    </div>
  )
}

// ── Primitives ────────────────────────────────────────────────────────────────

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">{label}</label>
      {children}
    </div>
  )
}

function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={[
        'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors',
        checked ? 'bg-sky-600' : 'bg-gray-600',
      ].join(' ')}
    >
      <span
        className={[
          'pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow transform transition-transform',
          checked ? 'translate-x-4' : 'translate-x-0',
        ].join(' ')}
      />
    </button>
  )
}

// ── GIS Integrations Panel ───────────────────────────────────────────────────

const INTEGRATION_TYPES: IntegrationType[] = ['ARCGIS', 'GOOGLE_EARTH', 'WMS', 'WFS', 'GENERIC_REST']

function GISIntegrationsPanel() {
  const [integrations, setIntegrations] = useState<IntegrationConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, string>>({})

  const [form, setForm] = useState<CreateIntegrationConfigRequest>({
    name: '',
    integration_type: 'ARCGIS',
    config: {},
    is_active: true,
    classification: 'UNCLASS',
  })
  const [configJson, setConfigJson] = useState('{}')
  const [jsonError, setJsonError] = useState('')

  useEffect(() => {
    gisClient.get<IntegrationConfig[]>('/integrations')
      .then((r) => setIntegrations(r.data))
      .catch(() => setIntegrations([]))
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    let parsed: Record<string, unknown> = {}
    try {
      parsed = JSON.parse(configJson)
      setJsonError('')
    } catch {
      setJsonError('Invalid JSON in config field')
      return
    }
    try {
      const res = await gisClient.post<IntegrationConfig>('/integrations', { ...form, config: parsed })
      setIntegrations((prev) => [res.data, ...prev])
      setShowModal(false)
      setForm({ name: '', integration_type: 'ARCGIS', config: {}, is_active: true, classification: 'UNCLASS' })
      setConfigJson('{}')
    } catch {
      // silently fail – real impl would show error
    }
  }

  async function handleDelete(id: string) {
    try {
      await gisClient.delete(`/integrations/${id}`)
      setIntegrations((prev) => prev.filter((i) => i.id !== id))
    } catch {
      // silently fail
    }
  }

  async function handleTest(id: string) {
    setTestResults((prev) => ({ ...prev, [id]: 'testing…' }))
    try {
      const res = await gisClient.post<{ status: string; message: string }>(`/integrations/${id}/test`)
      setTestResults((prev) => ({ ...prev, [id]: res.data.message }))
    } catch {
      setTestResults((prev) => ({ ...prev, [id]: 'Test failed' }))
    }
  }

  function downloadExport(layer: LayerType, format: 'GEOJSON' | 'KML') {
    gisClient.post(
      '/export/generate',
      { layer_type: layer, format, classification: 'UNCLASS' },
      { responseType: 'blob' },
    ).then((res) => {
      const ext = format === 'KML' ? 'kml' : 'geojson'
      const url = URL.createObjectURL(res.data as Blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${layer.toLowerCase()}.${ext}`
      a.click()
      URL.revokeObjectURL(url)
    }).catch(() => {})
  }

  return (
    <section className="space-y-8">
      {/* Integrations table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white">Configured Integrations</h2>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            className="rounded bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-500 transition-colors"
          >
            + Add Integration
          </button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : integrations.length === 0 ? (
          <p className="text-sm text-gray-500">No integrations configured.</p>
        ) : (
          <div className="rounded border border-gray-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-800 text-gray-300">
                  <th className="text-left px-3 py-2">Name</th>
                  <th className="text-left px-3 py-2">Type</th>
                  <th className="text-left px-3 py-2">Status</th>
                  <th className="text-left px-3 py-2">Classification</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {integrations.map((intg) => (
                  <tr key={intg.id} className="border-t border-gray-700 hover:bg-gray-800/50">
                    <td className="px-3 py-2 text-white">{intg.name}</td>
                    <td className="px-3 py-2 text-gray-300">{intg.integration_type}</td>
                    <td className="px-3 py-2">
                      <span className={intg.is_active ? 'text-green-400' : 'text-gray-500'}>
                        {intg.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-400">{intg.classification}</td>
                    <td className="px-3 py-2 flex gap-2 justify-end">
                      {testResults[intg.id] && (
                        <span className="text-xs text-sky-400 mr-2">{testResults[intg.id]}</span>
                      )}
                      <button
                        type="button"
                        onClick={() => handleTest(intg.id)}
                        className="rounded border border-sky-700 px-2 py-0.5 text-xs text-sky-400 hover:bg-sky-900/30"
                      >
                        Test
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(intg.id)}
                        className="rounded border border-red-800 px-2 py-0.5 text-xs text-red-400 hover:bg-red-900/30"
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
      </div>

      {/* Export quick-links */}
      <div>
        <h2 className="text-base font-semibold text-white mb-3">Export Quick-Links</h2>
        <p className="text-sm text-gray-400 mb-4">Download any layer as GeoJSON or KML for use in ArcGIS or Google Earth.</p>
        <div className="space-y-2">
          {ALL_LAYERS.map((layer) => (
            <div key={layer} className="flex items-center gap-3">
              <span className="text-sm text-gray-300 w-40">{layer.replace(/_/g, ' ')}</span>
              <button
                type="button"
                onClick={() => downloadExport(layer, 'GEOJSON')}
                className="rounded border border-gray-600 px-2 py-0.5 text-xs text-gray-300 hover:bg-gray-700"
              >
                GeoJSON
              </button>
              <button
                type="button"
                onClick={() => downloadExport(layer, 'KML')}
                className="rounded border border-gray-600 px-2 py-0.5 text-xs text-gray-300 hover:bg-gray-700"
              >
                KML
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Add integration modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-gray-900 rounded-lg border border-gray-700 p-6 w-full max-w-md shadow-xl">
            <h3 className="text-base font-semibold text-white mb-4">Add Integration</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <Field label="Name">
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="My ArcGIS Layer"
                  className={INPUT}
                />
              </Field>
              <Field label="Type">
                <select
                  value={form.integration_type}
                  onChange={(e) => setForm({ ...form, integration_type: e.target.value as IntegrationType })}
                  className={INPUT}
                >
                  {INTEGRATION_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </Field>
              <Field label="Config (JSON)">
                <textarea
                  rows={5}
                  value={configJson}
                  onChange={(e) => setConfigJson(e.target.value)}
                  className={INPUT + ' font-mono resize-none'}
                  spellCheck={false}
                />
                {jsonError && <p className="text-xs text-red-400 mt-1">{jsonError}</p>}
              </Field>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded border border-gray-600 px-4 py-1.5 text-sm text-gray-300 hover:bg-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded bg-sky-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-sky-500"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PROVIDER_OPTIONS: { value: AIProvider; label: string; icon: string; description: string }[] = [
  { value: 'ollama',       label: 'Ollama',       icon: '🦙', description: 'Local / air-gap' },
  { value: 'openai',       label: 'OpenAI',       icon: '🤖', description: 'GPT-4o, GPT-4' },
  { value: 'anthropic',    label: 'Anthropic',    icon: '🧠', description: 'Claude 3.5' },
  { value: 'azure_openai', label: 'Azure OpenAI', icon: '☁️',  description: 'GovCloud / IL4' },
]

const INPUT = 'w-full rounded bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500'

import { useState } from 'react'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAIConfigStore } from './hooks/useAIConfigStore'

type Tab = 'ai-config'

export default function AdminPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const isAdmin = useAuthStore((s) => s.hasRole('admin'))
  const [activeTab] = useState<Tab>('ai-config')

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
        </div>

        <div className="flex-1 overflow-y-auto p-6 max-w-3xl">
          {activeTab === 'ai-config' && <AIConfigPanel />}
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

// ── Constants ─────────────────────────────────────────────────────────────────

const PROVIDER_OPTIONS: { value: AIProvider; label: string; icon: string; description: string }[] = [
  { value: 'ollama',       label: 'Ollama',       icon: '🦙', description: 'Local / air-gap' },
  { value: 'openai',       label: 'OpenAI',       icon: '🤖', description: 'GPT-4o, GPT-4' },
  { value: 'anthropic',    label: 'Anthropic',    icon: '🧠', description: 'Claude 3.5' },
  { value: 'azure_openai', label: 'Azure OpenAI', icon: '☁️',  description: 'GovCloud / IL4' },
]

const INPUT = 'w-full rounded bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500'

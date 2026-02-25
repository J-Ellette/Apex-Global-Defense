import { useEffect, useState } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { ClassificationBadge } from '../../shared/components/ClassificationBadge'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { intelApi } from '../../shared/api/endpoints'
import type {
  CreateIntelItemRequest,
  EntityType,
  ExtractionResult,
  IngestResult,
  IntelItem,
  OSINTSource,
  SearchResult,
  SourceType,
  ThreatAssessmentResult,
  ThreatLevel,
  ThreatVector,
} from '../../shared/api/types'

// ---------------------------------------------------------------------------
// Constants & helpers
// ---------------------------------------------------------------------------

const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  OSINT: 'OSINT',
  SIGINT: 'SIGINT',
  HUMINT: 'HUMINT',
  IMINT: 'IMINT',
  TECHINT: 'TECHINT',
  FININT: 'FININT',
}

const SOURCE_TYPE_COLORS: Record<SourceType, string> = {
  OSINT: 'bg-blue-900 text-blue-200',
  SIGINT: 'bg-purple-900 text-purple-200',
  HUMINT: 'bg-green-900 text-green-200',
  IMINT: 'bg-cyan-900 text-cyan-200',
  TECHINT: 'bg-orange-900 text-orange-200',
  FININT: 'bg-yellow-900 text-yellow-200',
}

const ENTITY_TYPE_ICONS: Record<EntityType, string> = {
  PERSON: '👤',
  ORGANIZATION: '🏛️',
  LOCATION: '📍',
  WEAPON: '🔫',
  DATE: '📅',
  EVENT: '\u26A1',
  VEHICLE: '🚗',
  FACILITY: '🏢',
}

const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  PERSON: 'bg-blue-800 text-blue-200',
  ORGANIZATION: 'bg-red-800 text-red-200',
  LOCATION: 'bg-green-800 text-green-200',
  WEAPON: 'bg-orange-800 text-orange-200',
  DATE: 'bg-gray-700 text-gray-200',
  EVENT: 'bg-yellow-800 text-yellow-200',
  VEHICLE: 'bg-cyan-800 text-cyan-200',
  FACILITY: 'bg-purple-800 text-purple-200',
}

const THREAT_LEVEL_COLORS: Record<ThreatLevel, string> = {
  NEGLIGIBLE: 'bg-gray-700 text-gray-300',
  LOW: 'bg-green-900 text-green-200',
  MODERATE: 'bg-yellow-900 text-yellow-200',
  HIGH: 'bg-orange-900 text-orange-200',
  CRITICAL: 'bg-red-700 text-white font-bold',
}

const THREAT_VECTOR_ICONS: Record<ThreatVector, string> = {
  MILITARY: '🪖',
  TERRORIST: '💣',
  CYBER: '💻',
  CBRN: '☢️',
  ECONOMIC: '💰',
  HYBRID: '🌐',
}

const RELIABILITY_LABELS: Record<string, string> = {
  A: 'A — Completely Reliable',
  B: 'B — Usually Reliable',
  C: 'C — Fairly Reliable',
  D: 'D — Not Usually Reliable',
  E: 'E — Unreliable',
  F: 'F — Cannot Be Judged',
}

const CREDIBILITY_LABELS: Record<string, string> = {
  '1': '1 — Confirmed',
  '2': '2 — Probably True',
  '3': '3 — Possibly True',
  '4': '4 — Doubtful',
  '5': '5 — Improbable',
  '6': '6 — Cannot Be Judged',
}

// ---------------------------------------------------------------------------
// IntelPage
// ---------------------------------------------------------------------------

export default function IntelPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [activeTab, setActiveTab] = useState<'feed' | 'analysis' | 'osint'>('feed')

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <div className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Intelligence</h1>
            <p className="text-sm text-gray-400 mt-0.5">
              OSINT ingestion · Entity extraction · Threat assessment · Semantic search
            </p>
          </div>
        </div>

        <div className="flex gap-1 mt-4">
          {(
            [
              { id: 'feed', label: '📰 Intel Feed' },
              { id: 'analysis', label: '🔬 Analysis' },
              { id: 'osint', label: '📡 OSINT Sources' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 overflow-auto p-6">
        {activeTab === 'feed' && <IntelFeedTab />}
        {activeTab === 'analysis' && <AnalysisTab />}
        {activeTab === 'osint' && <OSINTSourcesTab />}
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Intel Feed Tab
// ---------------------------------------------------------------------------

function IntelFeedTab() {
  const [items, setItems] = useState<IntelItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterSource, setFilterSource] = useState<SourceType | ''>('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState<IntelItem | null>(null)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)

  const fetchItems = () => {
    setLoading(true)
    intelApi
      .listItems({ limit: 50 })
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchItems()
  }, [])

  const handleSearch = () => {
    if (!searchQuery.trim() && !filterSource) {
      fetchItems()
      setSearchResult(null)
      return
    }
    setLoading(true)
    intelApi
      .search({
        q: searchQuery || undefined,
        source_types: filterSource ? [filterSource] : undefined,
        limit: 50,
      })
      .then((r) => {
        setSearchResult(r)
        setItems(r.items)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const handleSemanticSearch = () => {
    if (!searchQuery.trim()) return
    setLoading(true)
    intelApi
      .semanticSearch({ query: searchQuery, limit: 20 })
      .then((r) => {
        setSearchResult(r)
        setItems(r.items)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-lg p-4 flex gap-3 flex-wrap">
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search intelligence items…"
          className="flex-1 min-w-48 bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none focus:border-blue-500"
        />
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value as SourceType | '')}
          className="bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 focus:outline-none"
        >
          <option value="">All Sources</option>
          {Object.entries(SOURCE_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <button
          onClick={handleSearch}
          className="bg-blue-700 hover:bg-blue-600 text-white rounded px-4 py-2 text-sm"
        >
          Search
        </button>
        <button
          onClick={handleSemanticSearch}
          title="AI-powered semantic search using pgvector"
          className="bg-purple-800 hover:bg-purple-700 text-white rounded px-4 py-2 text-sm"
        >
          🧠 Semantic
        </button>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-green-700 hover:bg-green-600 text-white rounded px-4 py-2 text-sm"
        >
          + Add Item
        </button>
      </div>

      {searchResult && (
        <p className="text-sm text-gray-400">
          {searchResult.total} result{searchResult.total !== 1 ? 's' : ''} found
        </p>
      )}

      {loading ? (
        <div className="text-gray-400 text-sm">Loading…</div>
      ) : items.length === 0 ? (
        <div className="text-gray-500 text-sm bg-gray-900 rounded-lg p-8 text-center">
          No intelligence items. Use the OSINT Sources tab to ingest data, or add items manually.
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <IntelItemCard key={item.id} item={item} onSelect={() => setSelectedItem(item)} />
          ))}
        </div>
      )}

      {showAddModal && (
        <AddItemModal onClose={() => setShowAddModal(false)} onCreated={() => { setShowAddModal(false); fetchItems() }} />
      )}
      {selectedItem && <ItemDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />}
    </div>
  )
}

function IntelItemCard({ item, onSelect }: { item: IntelItem; onSelect: () => void }) {
  const date = item.published_at
    ? new Date(item.published_at).toLocaleDateString()
    : new Date(item.ingested_at).toLocaleDateString()

  return (
    <div
      className="bg-gray-900 border border-gray-700 rounded-lg p-4 cursor-pointer hover:border-gray-500 transition-colors"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${SOURCE_TYPE_COLORS[item.source_type] ?? 'bg-gray-700 text-gray-300'}`}>
              {item.source_type}
            </span>
            <ClassificationBadge level={item.classification} />
            <span className="text-xs text-gray-500">R:{item.reliability} C:{item.credibility}</span>
          </div>
          <h3 className="text-white font-medium text-sm leading-snug">{item.title}</h3>
          <p className="text-gray-400 text-xs mt-1 line-clamp-2">{item.content}</p>
          {item.entities.length > 0 && (
            <div className="flex gap-1 flex-wrap mt-2">
              {item.entities.slice(0, 6).map((e, i) => (
                <span key={i} className={`text-xs px-1.5 py-0.5 rounded flex items-center gap-1 ${ENTITY_TYPE_COLORS[e.type] ?? 'bg-gray-700 text-gray-300'}`}>
                  <span>{ENTITY_TYPE_ICONS[e.type]}</span>
                  <span className="font-mono">{e.text}</span>
                </span>
              ))}
              {item.entities.length > 6 && <span className="text-xs text-gray-500">+{item.entities.length - 6} more</span>}
            </div>
          )}
        </div>
        <div className="text-right shrink-0">
          <div className="text-xs text-gray-500">{date}</div>
          {item.latitude != null && item.longitude != null && (
            <div className="text-xs text-gray-600 mt-1">📍 {item.latitude.toFixed(2)}, {item.longitude.toFixed(2)}</div>
          )}
          {item.has_embedding && <div className="text-xs text-purple-500 mt-1" title="Has semantic embedding">🧠</div>}
        </div>
      </div>
    </div>
  )
}

function ItemDetailModal({ item, onClose }: { item: IntelItem; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-5 border-b border-gray-700 flex items-start justify-between">
          <div>
            <div className="flex gap-2 mb-1">
              <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${SOURCE_TYPE_COLORS[item.source_type] ?? 'bg-gray-700 text-gray-300'}`}>{item.source_type}</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-600 font-mono">{item.classification}</span>
            </div>
            <h2 className="text-white font-semibold">{item.title}</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl ml-4">×</button>
        </div>
        <div className="p-5 space-y-5">
          <div>
            <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Content</h3>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">{item.content}</p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-800 rounded p-3">
              <div className="text-xs text-gray-500 mb-1">Reliability</div>
              <div className="text-white">{RELIABILITY_LABELS[item.reliability] ?? item.reliability}</div>
            </div>
            <div className="bg-gray-800 rounded p-3">
              <div className="text-xs text-gray-500 mb-1">Credibility</div>
              <div className="text-white">{CREDIBILITY_LABELS[item.credibility] ?? item.credibility}</div>
            </div>
          </div>
          {item.source_url && (
            <div>
              <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-1">Source</h3>
              <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 text-sm break-all">{item.source_url}</a>
            </div>
          )}
          {item.entities.length > 0 && (
            <div>
              <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Extracted Entities ({item.entities.length})</h3>
              <div className="flex flex-wrap gap-1.5">
                {item.entities.map((e, i) => (
                  <span key={i} className={`text-xs px-2 py-1 rounded flex items-center gap-1.5 ${ENTITY_TYPE_COLORS[e.type] ?? 'bg-gray-700 text-gray-300'}`} title={`${e.type} · confidence ${Math.round(e.confidence * 100)}%`}>
                    <span>{ENTITY_TYPE_ICONS[e.type]}</span>
                    <span className="font-medium">{e.text}</span>
                    <span className="opacity-60 text-xs">{Math.round(e.confidence * 100)}%</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AddItemModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState<Partial<CreateIntelItemRequest>>({
    source_type: 'HUMINT',
    classification: 'UNCLASS',
    reliability: 'F',
    credibility: '6',
    language: 'eng',
    auto_extract: true,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = () => {
    if (!form.title || !form.content) { setError('Title and content are required.'); return }
    setSaving(true)
    intelApi.createItem(form as CreateIntelItemRequest)
      .then(() => onCreated())
      .catch(() => setError('Failed to create item. Please try again.'))
      .finally(() => setSaving(false))
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="p-5 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-white font-semibold">Add Intelligence Item</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Source Type</label>
              <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value as SourceType })} className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700">
                {Object.entries(SOURCE_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Classification</label>
              <select value={form.classification} onChange={(e) => setForm({ ...form, classification: e.target.value as CreateIntelItemRequest['classification'] })} className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700">
                <option value="UNCLASS">UNCLASSIFIED</option>
                <option value="FOUO">FOUO</option>
                <option value="SECRET">SECRET</option>
                <option value="TOP_SECRET">TOP SECRET</option>
                <option value="TS_SCI">TS/SCI</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Title *</label>
            <input value={form.title ?? ''} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g., Armed clash reported — Donetsk Oblast" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Content *</label>
            <textarea value={form.content ?? ''} onChange={(e) => setForm({ ...form, content: e.target.value })} rows={5} placeholder="Detailed intelligence report…" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Reliability (NATO)</label>
              <select value={form.reliability} onChange={(e) => setForm({ ...form, reliability: e.target.value })} className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700">
                {Object.entries(RELIABILITY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Credibility (NATO)</label>
              <select value={form.credibility} onChange={(e) => setForm({ ...form, credibility: e.target.value })} className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700">
                {Object.entries(CREDIBILITY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Source URL (optional)</label>
            <input value={form.source_url ?? ''} onChange={(e) => setForm({ ...form, source_url: e.target.value || undefined })} placeholder="https://…" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700" />
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={form.auto_extract ?? true} onChange={(e) => setForm({ ...form, auto_extract: e.target.checked })} className="rounded" />
            <span className="text-sm text-gray-300">Auto-extract entities (NLP)</span>
          </label>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={onClose} className="text-gray-400 hover:text-white px-4 py-2 text-sm">Cancel</button>
            <button onClick={handleSubmit} disabled={saving} className="bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white rounded px-5 py-2 text-sm">{saving ? 'Saving…' : 'Add Item'}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Analysis Tab
// ---------------------------------------------------------------------------

function AnalysisTab() {
  const [activePanel, setActivePanel] = useState<'extract' | 'threat'>('extract')
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button onClick={() => setActivePanel('extract')} className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activePanel === 'extract' ? 'bg-blue-700 text-white' : 'text-gray-400 hover:text-white bg-gray-800'}`}>
          🔬 Entity Extraction
        </button>
        <button onClick={() => setActivePanel('threat')} className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activePanel === 'threat' ? 'bg-red-800 text-white' : 'text-gray-400 hover:text-white bg-gray-800'}`}>
          🎯 Threat Assessment
        </button>
      </div>
      {activePanel === 'extract' ? <EntityExtractionPanel /> : <ThreatAssessmentPanel />}
    </div>
  )
}

function EntityExtractionPanel() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleExtract = () => {
    if (!text.trim()) return
    setLoading(true)
    intelApi.extractEntities({ text }).then(setResult).catch(() => {}).finally(() => setLoading(false))
  }

  const entityGroups = result
    ? result.entities.reduce<Record<string, typeof result.entities>>((acc, e) => {
        if (!acc[e.type]) acc[e.type] = []
        acc[e.type].push(e)
        return acc
      }, {})
    : {}

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-lg p-5">
        <h2 className="text-white font-semibold mb-3">Named Entity Recognition</h2>
        <p className="text-sm text-gray-400 mb-4">Paste intelligence text below. The deterministic NLP engine will identify persons, organizations, locations, weapons, events, dates, vehicles, and facilities.</p>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} placeholder="Paste intelligence text here…" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 resize-none focus:outline-none focus:border-blue-500" />
        <div className="flex justify-end mt-3">
          <button onClick={handleExtract} disabled={loading || !text.trim()} className="bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white rounded px-5 py-2 text-sm">
            {loading ? 'Extracting…' : 'Extract Entities'}
          </button>
        </div>
      </div>
      {result && (
        <div className="bg-gray-900 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-semibold">{result.entity_count} Entities Found</h3>
            <div className="flex items-center gap-3 text-sm">
              <span className="text-gray-400">Method: <span className="text-blue-400">{result.method}</span></span>
              <span className="text-gray-400">{result.duration_ms.toFixed(1)}ms</span>
            </div>
          </div>
          {Object.entries(entityGroups).map(([type, entities]) => (
            <div key={type}>
              <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-2">
                <span>{ENTITY_TYPE_ICONS[type as EntityType]}</span>
                <span>{type}</span>
                <span className="text-gray-600">({entities.length})</span>
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {entities.map((e, i) => (
                  <span key={i} className={`text-sm px-2 py-1 rounded flex items-center gap-1.5 ${ENTITY_TYPE_COLORS[e.type] ?? 'bg-gray-700 text-gray-300'}`} title={`Confidence: ${Math.round(e.confidence * 100)}%`}>
                    <span className="font-medium">{e.text}</span>
                    <span className="text-xs opacity-60">{Math.round(e.confidence * 100)}%</span>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ThreatAssessmentPanel() {
  const [actor, setActor] = useState('')
  const [target, setTarget] = useState('')
  const [context, setContext] = useState('')
  const [result, setResult] = useState<ThreatAssessmentResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleAssess = () => {
    if (!actor.trim() || !target.trim()) return
    setLoading(true)
    intelApi.assessThreat({ actor, target, context: context || undefined }).then(setResult).catch(() => {}).finally(() => setLoading(false))
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-lg p-5">
        <h2 className="text-white font-semibold mb-3">Threat Assessment</h2>
        <p className="text-sm text-gray-400 mb-4">Assess the threat level posed by an actor against a target. The PMESII-PT inspired weighted indicator matrix produces a structured threat estimate with recommendations.</p>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Threat Actor *</label>
            <input value={actor} onChange={(e) => setActor(e.target.value)} placeholder="e.g., ISIS, Russia, APT28" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Target *</label>
            <input value={target} onChange={(e) => setTarget(e.target.value)} placeholder="e.g., NATO eastern flank" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700" />
          </div>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Context / Intel Summary (optional)</label>
          <textarea value={context} onChange={(e) => setContext(e.target.value)} rows={5} placeholder="Paste relevant intelligence text…" className="w-full bg-gray-800 text-white rounded px-3 py-2 text-sm border border-gray-700 resize-none" />
        </div>
        <div className="flex justify-end mt-3">
          <button onClick={handleAssess} disabled={loading || !actor.trim() || !target.trim()} className="bg-red-800 hover:bg-red-700 disabled:opacity-50 text-white rounded px-5 py-2 text-sm">
            {loading ? 'Assessing…' : 'Assess Threat'}
          </button>
        </div>
      </div>
      {result && <ThreatAssessmentResultCard result={result} />}
    </div>
  )
}

function ThreatAssessmentResultCard({ result }: { result: ThreatAssessmentResult }) {
  const activeIndicators = result.indicators.filter((i) => i.present)
  const inactiveIndicators = result.indicators.filter((i) => !i.present)

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
      <div className="p-5 border-b border-gray-700">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <span className={`px-3 py-1 rounded text-sm font-bold ${THREAT_LEVEL_COLORS[result.threat_level]}`}>{result.threat_level}</span>
              <span className="text-2xl font-bold text-white">{result.threat_score.toFixed(1)}<span className="text-base text-gray-400">/10</span></span>
            </div>
            <p className="text-sm text-gray-300">
              <span className="text-white font-medium">{result.actor}</span>
              <span className="text-gray-500 mx-2">→</span>
              <span className="text-white font-medium">{result.target}</span>
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500 mb-1">Confidence</div>
            <div className="text-white font-semibold">{Math.round(result.confidence * 100)}%</div>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap mt-3">
          {result.threat_vectors.map((v) => (
            <span key={v} className="flex items-center gap-1.5 text-xs bg-gray-800 px-2 py-1 rounded border border-gray-600 text-gray-200">
              <span>{THREAT_VECTOR_ICONS[v]}</span><span>{v}</span>
            </span>
          ))}
        </div>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Assessment Summary</h3>
          <p className="text-sm text-gray-300">{result.summary}</p>
        </div>
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1"><span>Threat Score</span><span>{result.threat_score.toFixed(1)} / 10</span></div>
          <div className="bg-gray-700 rounded-full h-2">
            <div className={`h-2 rounded-full transition-all ${result.threat_score >= 8 ? 'bg-red-500' : result.threat_score >= 6 ? 'bg-orange-500' : result.threat_score >= 4 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${(result.threat_score / 10) * 100}%` }} />
          </div>
        </div>
        {activeIndicators.length > 0 && (
          <div>
            <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Active Indicators ({activeIndicators.length})</h3>
            <ul className="space-y-1">
              {activeIndicators.map((ind, i) => (
                <li key={i} className="text-sm text-red-300 flex items-center gap-2">
                  <span className="text-red-500">⚠</span>
                  <span>{ind.indicator}</span>
                  <span className="text-gray-500 text-xs">(weight: {ind.weight})</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {inactiveIndicators.length > 0 && (
          <details>
            <summary className="cursor-pointer text-xs text-gray-500 uppercase tracking-wide hover:text-gray-300">Not Detected ({inactiveIndicators.length} indicators)</summary>
            <ul className="mt-2 space-y-1">
              {inactiveIndicators.map((ind, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="text-gray-700">–</span><span>{ind.indicator}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
        {result.recommendations.length > 0 && (
          <div>
            <h3 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Protective Actions</h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="text-sm text-yellow-200 flex gap-2">
                  <span className="text-yellow-500 shrink-0">→</span><span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-xs text-gray-600">Assessed: {new Date(result.assessed_at).toLocaleString()} · {result.ai_assisted ? 'AI-assisted' : 'Deterministic matrix (non-AI fallback)'}</p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// OSINT Sources Tab
// ---------------------------------------------------------------------------

function OSINTSourcesTab() {
  const [sources, setSources] = useState<OSINTSource[]>([])
  const [loading, setLoading] = useState(true)
  const [ingesting, setIngesting] = useState<string | null>(null)
  const [ingestResult, setIngestResult] = useState<{ id: string; result: IngestResult } | null>(null)

  useEffect(() => {
    intelApi.listOSINTSources().then(setSources).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleIngest = (sourceId: string, sinceDays = 7, dryRun = false) => {
    setIngesting(sourceId)
    setIngestResult(null)
    intelApi.triggerIngestion({ source_id: sourceId, since_days: sinceDays, max_items: 50, dry_run: dryRun })
      .then((r) => setIngestResult({ id: sourceId, result: r }))
      .catch(() => {})
      .finally(() => setIngesting(null))
  }

  const SOURCE_INFO: Record<string, { icon: string; description: string }> = {
    ACLED: { icon: '⚔️', description: 'Armed Conflict Location & Event Data Project. Disaggregated conflict data covering Africa, Middle East, Asia, and Latin America.' },
    UCDP: { icon: '📊', description: 'Uppsala Conflict Data Program. Academic conflict event database from Uppsala University. High-quality, peer-reviewed data.' },
    RSS: { icon: '📡', description: 'Public RSS feeds from Reuters, BBC World News, and ReliefWeb. Near real-time news monitoring.' },
  }

  return (
    <div className="space-y-4">
      <div className="bg-gray-900 rounded-lg p-5 border border-gray-700">
        <h2 className="text-white font-semibold mb-1">OSINT Ingestion Pipeline</h2>
        <p className="text-sm text-gray-400">Trigger ingestion from configured open-source intelligence adapters. Items are automatically saved to the intel database with entity extraction applied.</p>
      </div>
      {loading ? (
        <div className="text-gray-400 text-sm">Loading sources…</div>
      ) : (
        <div className="grid gap-4">
          {sources.map((source) => {
            const info = SOURCE_INFO[source.source_type]
            const isIngesting = ingesting === source.id
            const myResult = ingestResult?.id === source.id ? ingestResult.result : null
            return (
              <div key={source.id} className="bg-gray-900 border border-gray-700 rounded-lg p-5 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{info?.icon ?? '🔌'}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-white font-semibold">{source.name}</h3>
                        <span className={`text-xs px-1.5 py-0.5 rounded font-mono ${source.status === 'ACTIVE' ? 'bg-green-900 text-green-300' : source.status === 'ERROR' ? 'bg-red-900 text-red-300' : 'bg-gray-700 text-gray-400'}`}>{source.status}</span>
                        <span className="text-xs bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">{source.source_type}</span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">{info?.description}</p>
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-4">
                    <div className="text-sm text-gray-300">{source.items_ingested} items</div>
                    {source.last_ingested_at && <div className="text-xs text-gray-500">Last: {new Date(source.last_ingested_at).toLocaleDateString()}</div>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleIngest(source.id, 7, false)} disabled={isIngesting} className="bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white rounded px-4 py-2 text-sm">
                    {isIngesting ? '⏳ Ingesting…' : '▶ Ingest (7 days)'}
                  </button>
                  <button onClick={() => handleIngest(source.id, 7, true)} disabled={isIngesting} className="bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded px-4 py-2 text-sm">
                    🔍 Dry Run
                  </button>
                </div>
                {myResult && (
                  <div className="bg-gray-800 rounded p-3 text-sm space-y-1">
                    <div className="flex gap-4 text-gray-300">
                      <span>Fetched: <span className="text-white font-medium">{myResult.items_fetched}</span></span>
                      <span>Saved: <span className="text-white font-medium">{myResult.items_saved}</span></span>
                      <span>Duration: <span className="text-white font-medium">{myResult.duration_seconds.toFixed(2)}s</span></span>
                      {myResult.dry_run && <span className="text-yellow-400 font-medium">DRY RUN</span>}
                    </div>
                    {myResult.errors.length > 0 && (
                      <div className="text-red-400 text-xs">{myResult.errors.slice(0, 3).map((e, i) => <div key={i}>{e}</div>)}</div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

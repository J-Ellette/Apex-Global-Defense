import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { LoadingSpinner } from '../../shared/components/LoadingSpinner'
import { cyberApi } from '../../shared/api/endpoints'
import type {
  ATTACKTactic,
  ATTACKTechnique,
  CyberAttack,
  SimulateAttackResult,
  NodeType,
  Criticality,
} from '../../shared/api/types'

// ── Tactic display names ────────────────────────────────────────────────────
const TACTIC_LABELS: Record<ATTACKTactic, string> = {
  reconnaissance: 'Reconnaissance',
  resource_development: 'Resource Development',
  initial_access: 'Initial Access',
  execution: 'Execution',
  persistence: 'Persistence',
  privilege_escalation: 'Privilege Escalation',
  defense_evasion: 'Defense Evasion',
  credential_access: 'Credential Access',
  discovery: 'Discovery',
  lateral_movement: 'Lateral Movement',
  collection: 'Collection',
  command_and_control: 'Command & Control',
  exfiltration: 'Exfiltration',
  impact: 'Impact',
}

const SEVERITY_COLOR: Record<string, string> = {
  LOW: 'bg-green-900 text-green-200',
  MEDIUM: 'bg-yellow-900 text-yellow-200',
  HIGH: 'bg-orange-900 text-orange-200',
  CRITICAL: 'bg-red-900 text-red-200',
}

const CRITICALITY_COLOR: Record<Criticality, string> = {
  LOW: 'text-green-400',
  MEDIUM: 'text-yellow-400',
  HIGH: 'text-orange-400',
  CRITICAL: 'text-red-400',
}

const STATUS_COLOR: Record<string, string> = {
  PLANNED: 'bg-gray-700 text-gray-200',
  EXECUTING: 'bg-blue-900 text-blue-200',
  COMPLETE: 'bg-green-900 text-green-200',
  FAILED: 'bg-red-900 text-red-200',
  DETECTED: 'bg-orange-900 text-orange-200',
}

const NODE_ICONS: Record<NodeType, string> = {
  HOST: '💻',
  SERVER: '🖥️',
  ROUTER: '📡',
  FIREWALL: '🛡️',
  ICS: '⚙️',
  CLOUD: '☁️',
  SATELLITE: '🛰️',
  IOT: '📱',
  DATABASE: '🗄️',
}

type Tab = 'techniques' | 'infrastructure' | 'attacks'

// ── Main page ────────────────────────────────────────────────────────────────

export default function CyberPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const canWrite = useAuthStore((s) => s.hasPermission('scenario:write'))
  const canRun = useAuthStore((s) => s.hasPermission('simulation:run'))
  const [activeTab, setActiveTab] = useState<Tab>('techniques')

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Page header */}
        <div className="px-6 py-4 border-b border-gray-800">
          <h1 className="text-xl font-bold text-white">Cyber Operations</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            MITRE ATT&amp;CK catalog · Infrastructure mapping · Attack simulation
          </p>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 px-6 pt-3 border-b border-gray-800">
          {([
            ['techniques', '🎯', 'ATT&CK Techniques'],
            ['infrastructure', '🗺️', 'Infrastructure Graph'],
            ['attacks', '⚔️', 'Attack Planner'],
          ] as const).map(([id, icon, label]) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
                activeTab === id
                  ? 'bg-gray-900 text-sky-400 border border-b-0 border-gray-700'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {icon} {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'techniques' && <TechniquesPanel />}
          {activeTab === 'infrastructure' && <InfrastructurePanel canWrite={canWrite} />}
          {activeTab === 'attacks' && <AttacksPanel canWrite={canWrite} canRun={canRun} />}
        </div>
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

// ── ATT&CK Techniques Panel ──────────────────────────────────────────────────

function TechniquesPanel() {
  const [tactic, setTactic] = useState<ATTACKTactic | ''>('')
  const [severity, setSeverity] = useState('')
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<ATTACKTechnique | null>(null)

  const { data: techniques, isLoading } = useQuery({
    queryKey: ['cyber-techniques', tactic, severity, query],
    queryFn: () =>
      cyberApi.listTechniques({
        tactic: tactic || undefined,
        severity: severity || undefined,
        q: query || undefined,
      }),
    staleTime: 10 * 60 * 1000,
  })

  return (
    <div className="flex gap-4 h-full">
      {/* Left: filters + list */}
      <div className="flex-1 min-w-0">
        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search techniques…"
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white placeholder-gray-500 w-56 focus:outline-none focus:border-sky-600"
          />
          <select
            value={tactic}
            onChange={(e) => setTactic(e.target.value as ATTACKTactic | '')}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
          >
            <option value="">All Tactics</option>
            {(Object.keys(TACTIC_LABELS) as ATTACKTactic[]).map((t) => (
              <option key={t} value={t}>{TACTIC_LABELS[t]}</option>
            ))}
          </select>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
          >
            <option value="">All Severities</option>
            {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          {(tactic || severity || query) && (
            <button
              onClick={() => { setTactic(''); setSeverity(''); setQuery('') }}
              className="text-xs text-gray-400 hover:text-white px-2"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Table */}
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="overflow-auto rounded border border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
                <tr>
                  <th className="px-4 py-2 text-left">ID</th>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Tactic</th>
                  <th className="px-4 py-2 text-left">Severity</th>
                  <th className="px-4 py-2 text-left">Platforms</th>
                </tr>
              </thead>
              <tbody>
                {(techniques ?? []).map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => setSelected(selected?.id === t.id ? null : t)}
                    className={`border-t border-gray-800 cursor-pointer transition-colors ${
                      selected?.id === t.id ? 'bg-sky-900/30' : 'hover:bg-gray-900'
                    }`}
                  >
                    <td className="px-4 py-2 font-mono text-sky-400">{t.id}</td>
                    <td className="px-4 py-2 text-white font-medium">{t.name}</td>
                    <td className="px-4 py-2 text-gray-300">{TACTIC_LABELS[t.tactic]}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${SEVERITY_COLOR[t.severity]}`}>
                        {t.severity}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-400 text-xs">{t.platforms.slice(0, 3).join(', ')}</td>
                  </tr>
                ))}
                {!isLoading && (techniques?.length ?? 0) === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-500">
                      No techniques match the current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
        <p className="mt-2 text-xs text-gray-600">
          {techniques?.length ?? 0} technique{(techniques?.length ?? 0) !== 1 ? 's' : ''} • Source: MITRE ATT&amp;CK Enterprise Matrix
        </p>
      </div>

      {/* Right: detail panel */}
      {selected && (
        <div className="w-80 flex-shrink-0 rounded border border-gray-700 bg-gray-900 p-4 self-start">
          <div className="flex items-start justify-between mb-3">
            <div>
              <span className="font-mono text-sky-400 text-sm">{selected.id}</span>
              <h3 className="text-base font-bold text-white mt-0.5">{selected.name}</h3>
            </div>
            <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white text-lg">✕</button>
          </div>
          <div className="flex gap-2 mb-3">
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${SEVERITY_COLOR[selected.severity]}`}>
              {selected.severity}
            </span>
            <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
              {TACTIC_LABELS[selected.tactic]}
            </span>
          </div>
          <p className="text-sm text-gray-300 mb-3 leading-relaxed">{selected.description}</p>
          <div className="mb-3">
            <p className="text-xs text-gray-500 font-semibold uppercase mb-1">Platforms</p>
            <p className="text-xs text-gray-300">{selected.platforms.join(', ')}</p>
          </div>
          <div className="mb-3">
            <p className="text-xs text-gray-500 font-semibold uppercase mb-1">Mitigations</p>
            <ul className="space-y-1">
              {selected.mitigations.map((m) => (
                <li key={m} className="text-xs text-gray-300">• {m}</li>
              ))}
            </ul>
          </div>
          <a
            href={selected.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-sky-400 hover:underline"
          >
            View on attack.mitre.org ↗
          </a>
        </div>
      )}
    </div>
  )
}

// ── Infrastructure Panel ─────────────────────────────────────────────────────

function InfrastructurePanel({ canWrite }: { canWrite: boolean }) {
  const queryClient = useQueryClient()
  const [showAddNode, setShowAddNode] = useState(false)
  const [showAddEdge, setShowAddEdge] = useState(false)
  const [newNode, setNewNode] = useState<{
    label: string; node_type: NodeType; network: string; ip_address: string; criticality: Criticality
  }>({ label: '', node_type: 'SERVER', network: '', ip_address: '', criticality: 'MEDIUM' })
  const [newEdge, setNewEdge] = useState({ source_id: '', target_id: '', edge_type: 'NETWORK', protocol: '', port: '' })

  const { data: graph, isLoading } = useQuery({
    queryKey: ['cyber-graph'],
    queryFn: () => cyberApi.getGraph(),
    staleTime: 30_000,
  })

  const createNodeMutation = useMutation({
    mutationFn: () => cyberApi.createNode({
      label: newNode.label,
      node_type: newNode.node_type,
      network: newNode.network || undefined,
      ip_address: newNode.ip_address || undefined,
      criticality: newNode.criticality,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cyber-graph'] })
      setShowAddNode(false)
      setNewNode({ label: '', node_type: 'SERVER', network: '', ip_address: '', criticality: 'MEDIUM' })
    },
  })

  const deleteNodeMutation = useMutation({
    mutationFn: (id: string) => cyberApi.deleteNode(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cyber-graph'] }),
  })

  const createEdgeMutation = useMutation({
    mutationFn: () => cyberApi.createEdge({
      source_id: newEdge.source_id,
      target_id: newEdge.target_id,
      edge_type: newEdge.edge_type,
      protocol: newEdge.protocol || undefined,
      port: newEdge.port ? parseInt(newEdge.port) : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cyber-graph'] })
      setShowAddEdge(false)
      setNewEdge({ source_id: '', target_id: '', edge_type: 'NETWORK', protocol: '', port: '' })
    },
  })

  const deleteEdgeMutation = useMutation({
    mutationFn: (id: string) => cyberApi.deleteEdge(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cyber-graph'] }),
  })

  if (isLoading) return <LoadingSpinner />

  const nodes = graph?.nodes ?? []
  const edges = graph?.edges ?? []
  const nodeMap = useMemo(
    () => Object.fromEntries(nodes.map((n) => [n.id, n])),
    [nodes],
  )

  return (
    <div className="space-y-6">
      {/* Nodes */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white">Infrastructure Nodes ({nodes.length})</h2>
          {canWrite && (
            <button
              onClick={() => setShowAddNode(!showAddNode)}
              className="text-sm bg-sky-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition-colors"
            >
              + Add Node
            </button>
          )}
        </div>

        {/* Add node form */}
        {showAddNode && (
          <div className="mb-4 p-4 rounded border border-gray-700 bg-gray-900 space-y-3">
            <h3 className="text-sm font-semibold text-white">New Infrastructure Node</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Label *</label>
                <input
                  value={newNode.label}
                  onChange={(e) => setNewNode({ ...newNode, label: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                  placeholder="e.g. Domain Controller"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Type *</label>
                <select
                  value={newNode.node_type}
                  onChange={(e) => setNewNode({ ...newNode, node_type: e.target.value as NodeType })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                >
                  {(['HOST','SERVER','ROUTER','FIREWALL','ICS','CLOUD','SATELLITE','IOT','DATABASE'] as NodeType[]).map((t) => (
                    <option key={t} value={t}>{NODE_ICONS[t]} {t}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Network</label>
                <input
                  value={newNode.network}
                  onChange={(e) => setNewNode({ ...newNode, network: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                  placeholder="e.g. DMZ"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">IP Address</label>
                <input
                  value={newNode.ip_address}
                  onChange={(e) => setNewNode({ ...newNode, ip_address: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                  placeholder="e.g. 10.0.1.5"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Criticality</label>
                <select
                  value={newNode.criticality}
                  onChange={(e) => setNewNode({ ...newNode, criticality: e.target.value as Criticality })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                >
                  {(['LOW','MEDIUM','HIGH','CRITICAL'] as Criticality[]).map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                disabled={!newNode.label || createNodeMutation.isPending}
                onClick={() => createNodeMutation.mutate()}
                className="bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded transition-colors"
              >
                {createNodeMutation.isPending ? 'Saving…' : 'Save Node'}
              </button>
              <button
                onClick={() => setShowAddNode(false)}
                className="text-gray-400 hover:text-white text-sm px-3 py-1.5"
              >
                Cancel
              </button>
            </div>
            {createNodeMutation.isError && (
              <p className="text-red-400 text-xs">Failed to create node.</p>
            )}
          </div>
        )}

        {/* Node list */}
        {nodes.length === 0 ? (
          <p className="text-gray-500 text-sm">No infrastructure nodes defined. Add nodes to start mapping.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {nodes.map((node) => (
              <div key={node.id} className="rounded border border-gray-800 bg-gray-900 p-3 flex items-start gap-3">
                <span className="text-2xl">{NODE_ICONS[node.node_type]}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{node.label}</p>
                  <p className="text-xs text-gray-400">{node.node_type}{node.network ? ` · ${node.network}` : ''}</p>
                  {node.ip_address && <p className="text-xs font-mono text-gray-500">{node.ip_address}</p>}
                  <span className={`text-xs font-semibold ${CRITICALITY_COLOR[node.criticality]}`}>
                    {node.criticality}
                  </span>
                </div>
                {canWrite && (
                  <button
                    onClick={() => {
                      if (window.confirm(`Delete node "${node.label}"?`)) {
                        deleteNodeMutation.mutate(node.id)
                      }
                    }}
                    className="text-gray-600 hover:text-red-400 text-sm flex-shrink-0"
                    title="Delete node"
                  >
                    🗑
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edges */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white">Connections ({edges.length})</h2>
          {canWrite && nodes.length >= 2 && (
            <button
              onClick={() => setShowAddEdge(!showAddEdge)}
              className="text-sm bg-sky-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition-colors"
            >
              + Add Connection
            </button>
          )}
        </div>

        {/* Add edge form */}
        {showAddEdge && (
          <div className="mb-4 p-4 rounded border border-gray-700 bg-gray-900 space-y-3">
            <h3 className="text-sm font-semibold text-white">New Connection</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Source Node *</label>
                <select
                  value={newEdge.source_id}
                  onChange={(e) => setNewEdge({ ...newEdge, source_id: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                >
                  <option value="">Select node…</option>
                  {nodes.map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Target Node *</label>
                <select
                  value={newEdge.target_id}
                  onChange={(e) => setNewEdge({ ...newEdge, target_id: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                >
                  <option value="">Select node…</option>
                  {nodes.filter(n => n.id !== newEdge.source_id).map((n) => <option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Edge Type</label>
                <select
                  value={newEdge.edge_type}
                  onChange={(e) => setNewEdge({ ...newEdge, edge_type: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                >
                  {['NETWORK','DEPENDENCY','CONTROL'].map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">Protocol</label>
                <input
                  value={newEdge.protocol}
                  onChange={(e) => setNewEdge({ ...newEdge, protocol: e.target.value })}
                  placeholder="e.g. TCP"
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                disabled={!newEdge.source_id || !newEdge.target_id || createEdgeMutation.isPending}
                onClick={() => createEdgeMutation.mutate()}
                className="bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded transition-colors"
              >
                {createEdgeMutation.isPending ? 'Saving…' : 'Save Connection'}
              </button>
              <button onClick={() => setShowAddEdge(false)} className="text-gray-400 hover:text-white text-sm px-3 py-1.5">
                Cancel
              </button>
            </div>
          </div>
        )}

        {edges.length === 0 ? (
          <p className="text-gray-500 text-sm">No connections defined.</p>
        ) : (
          <div className="overflow-auto rounded border border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
                <tr>
                  <th className="px-4 py-2 text-left">Source</th>
                  <th className="px-4 py-2 text-left">→</th>
                  <th className="px-4 py-2 text-left">Target</th>
                  <th className="px-4 py-2 text-left">Type</th>
                  <th className="px-4 py-2 text-left">Protocol</th>
                  {canWrite && <th className="px-4 py-2 text-left"></th>}
                </tr>
              </thead>
              <tbody>
                {edges.map((edge) => (
                  <tr key={edge.id} className="border-t border-gray-800 hover:bg-gray-900/50">
                    <td className="px-4 py-2 text-white">{nodeMap[edge.source_id]?.label ?? edge.source_id.slice(0, 8)}</td>
                    <td className="px-4 py-2 text-gray-500">→</td>
                    <td className="px-4 py-2 text-white">{nodeMap[edge.target_id]?.label ?? edge.target_id.slice(0, 8)}</td>
                    <td className="px-4 py-2 text-gray-300">{edge.edge_type}</td>
                    <td className="px-4 py-2 text-gray-400">{edge.protocol ?? '—'}{edge.port ? `:${edge.port}` : ''}</td>
                    {canWrite && (
                      <td className="px-4 py-2">
                        <button
                          onClick={() => deleteEdgeMutation.mutate(edge.id)}
                          className="text-gray-600 hover:text-red-400 text-sm"
                        >
                          🗑
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Attack Planner Panel ─────────────────────────────────────────────────────

function AttacksPanel({ canWrite, canRun }: { canWrite: boolean; canRun: boolean }) {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [simTarget, setSimTarget] = useState<CyberAttack | null>(null)
  const [simResult, setSimResult] = useState<SimulateAttackResult | null>(null)
  const [defenderSkill, setDefenderSkill] = useState(0.5)
  const [networkHardening, setNetworkHardening] = useState(0.5)

  // Form state
  const [form, setForm] = useState({
    technique_id: '',
    attacker: '',
    target_node_id: '',
    impact: 'MEDIUM',
    notes: '',
  })

  const { data: attacks, isLoading } = useQuery({
    queryKey: ['cyber-attacks'],
    queryFn: () => cyberApi.listAttacks(),
    staleTime: 30_000,
  })

  const { data: techniques } = useQuery({
    queryKey: ['cyber-techniques'],
    queryFn: () => cyberApi.listTechniques(),
    staleTime: 10 * 60 * 1000,
  })

  const { data: graph } = useQuery({
    queryKey: ['cyber-graph'],
    queryFn: () => cyberApi.getGraph(),
    staleTime: 30_000,
  })

  const createMutation = useMutation({
    mutationFn: () => cyberApi.createAttack({
      technique_id: form.technique_id,
      attacker: form.attacker,
      target_node_id: form.target_node_id || undefined,
      impact: form.impact,
      notes: form.notes || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cyber-attacks'] })
      setShowCreate(false)
      setForm({ technique_id: '', attacker: '', target_node_id: '', impact: 'MEDIUM', notes: '' })
    },
  })

  const simulateMutation = useMutation({
    mutationFn: (attack: CyberAttack) =>
      cyberApi.simulateAttack(attack.id, { defender_skill: defenderSkill, network_hardening: networkHardening }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['cyber-attacks'] })
      setSimResult(result)
    },
  })

  const damageColor: Record<string, string> = {
    NONE: 'text-green-400',
    MINIMAL: 'text-yellow-400',
    MODERATE: 'text-orange-400',
    SEVERE: 'text-red-400',
    CATASTROPHIC: 'text-red-300 font-bold',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-white">Planned & Executed Attacks ({attacks?.length ?? 0})</h2>
        {canWrite && (
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="text-sm bg-sky-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition-colors"
          >
            + Plan Attack
          </button>
        )}
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="p-4 rounded border border-gray-700 bg-gray-900 space-y-3">
          <h3 className="text-sm font-semibold text-white">Plan Cyber Attack</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">ATT&CK Technique *</label>
              <select
                value={form.technique_id}
                onChange={(e) => setForm({ ...form, technique_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
              >
                <option value="">Select technique…</option>
                {(techniques ?? []).map((t) => (
                  <option key={t.id} value={t.id}>{t.id} – {t.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Threat Actor *</label>
              <input
                value={form.attacker}
                onChange={(e) => setForm({ ...form, attacker: e.target.value })}
                placeholder="e.g. APT-28, Lazarus Group"
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Target Node</label>
              <select
                value={form.target_node_id}
                onChange={(e) => setForm({ ...form, target_node_id: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
              >
                <option value="">No specific target</option>
                {(graph?.nodes ?? []).map((n) => (
                  <option key={n.id} value={n.id}>{NODE_ICONS[n.node_type]} {n.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Intended Impact</label>
              <select
                value={form.impact}
                onChange={(e) => setForm({ ...form, impact: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600"
              >
                {['LOW','MEDIUM','HIGH','CRITICAL'].map((i) => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-400 mb-1">Notes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                rows={2}
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-sky-600 resize-none"
                placeholder="Optional planning notes…"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              disabled={!form.technique_id || !form.attacker || createMutation.isPending}
              onClick={() => createMutation.mutate()}
              className="bg-sky-700 hover:bg-sky-600 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded transition-colors"
            >
              {createMutation.isPending ? 'Planning…' : 'Plan Attack'}
            </button>
            <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-white text-sm px-3 py-1.5">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Simulation result */}
      {simResult && simTarget && (
        <div className={`p-4 rounded border ${simResult.success ? 'border-red-700 bg-red-950/40' : 'border-gray-700 bg-gray-900'}`}>
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm font-bold text-white">
              Simulation Result — {simResult.success ? '🔴 Attack Succeeded' : '🟢 Attack Repelled'}
            </h3>
            <button onClick={() => { setSimResult(null); setSimTarget(null) }} className="text-gray-500 hover:text-white">✕</button>
          </div>
          <p className={`text-sm mb-2 ${damageColor[simResult.damage_level]}`}>
            Damage Level: {simResult.damage_level}
          </p>
          <p className="text-sm text-gray-300 mb-2">{simResult.narrative}</p>
          <div className="flex gap-4 text-xs text-gray-400">
            <span>Detected: {simResult.detected ? `Yes (${simResult.ttd_minutes} min)` : 'No'}</span>
            <span>Persistence: {simResult.persistence_achieved ? 'Established' : 'Not established'}</span>
            <span>Affected nodes: {simResult.affected_nodes.length}</span>
          </div>
        </div>
      )}

      {/* Simulation controls */}
      {simTarget && !simResult && (
        <div className="p-4 rounded border border-yellow-700 bg-yellow-950/30 space-y-3">
          <h3 className="text-sm font-bold text-white">Simulate: {simTarget.technique_id} by {simTarget.attacker}</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Defender Skill: {Math.round(defenderSkill * 100)}%</label>
              <input
                type="range" min={0} max={1} step={0.05} value={defenderSkill}
                onChange={(e) => setDefenderSkill(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Network Hardening: {Math.round(networkHardening * 100)}%</label>
              <input
                type="range" min={0} max={1} step={0.05} value={networkHardening}
                onChange={(e) => setNetworkHardening(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              disabled={simulateMutation.isPending}
              onClick={() => simulateMutation.mutate(simTarget)}
              className="bg-yellow-700 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded transition-colors"
            >
              {simulateMutation.isPending ? 'Simulating…' : '▶ Run Simulation'}
            </button>
            <button onClick={() => setSimTarget(null)} className="text-gray-400 hover:text-white text-sm px-3 py-1.5">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Attacks table */}
      {isLoading ? (
        <LoadingSpinner />
      ) : attacks?.length === 0 ? (
        <p className="text-gray-500 text-sm">No attacks planned yet.</p>
      ) : (
        <div className="overflow-auto rounded border border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
              <tr>
                <th className="px-4 py-2 text-left">Technique</th>
                <th className="px-4 py-2 text-left">Actor</th>
                <th className="px-4 py-2 text-left">Status</th>
                <th className="px-4 py-2 text-left">Probability</th>
                <th className="px-4 py-2 text-left">Impact</th>
                {canRun && <th className="px-4 py-2 text-left"></th>}
              </tr>
            </thead>
            <tbody>
              {(attacks ?? []).map((attack) => (
                <tr key={attack.id} className="border-t border-gray-800 hover:bg-gray-900/50">
                  <td className="px-4 py-2 font-mono text-sky-400">{attack.technique_id}</td>
                  <td className="px-4 py-2 text-white">{attack.attacker}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${STATUS_COLOR[attack.status]}`}>
                      {attack.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-300">{Math.round(attack.success_probability * 100)}%</td>
                  <td className="px-4 py-2 text-gray-300">{attack.impact}</td>
                  {canRun && (
                    <td className="px-4 py-2">
                      {(attack.status === 'PLANNED' || attack.status === 'FAILED') && (
                        <button
                          onClick={() => { setSimTarget(attack); setSimResult(null) }}
                          className="text-xs bg-yellow-900 hover:bg-yellow-800 text-yellow-200 px-2 py-1 rounded transition-colors"
                        >
                          Simulate
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

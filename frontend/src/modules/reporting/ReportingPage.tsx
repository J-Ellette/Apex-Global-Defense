import { useEffect, useState, useCallback } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { ClassificationBadge } from '../../shared/components/ClassificationBadge'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { reportingApi } from '../../shared/api/endpoints'
import type {
  Report,
  ReportType,
  ReportStatus,
  GenerateReportRequest,
  SITREPContent,
  INTSUMContent,
  CONOPSContent,
} from '../../shared/api/types'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  SITREP: 'Situation Report',
  INTSUM: 'Intelligence Summary',
  CONOPS: 'Concept of Operations',
}

const STATUS_COLORS: Record<ReportStatus, string> = {
  DRAFT: 'bg-gray-700 text-gray-200',
  FINAL: 'bg-blue-900 text-blue-200',
  APPROVED: 'bg-green-900 text-green-200',
}

// ---------------------------------------------------------------------------
// Generate Report Modal
// ---------------------------------------------------------------------------

interface GenerateModalProps {
  onClose: () => void
  onGenerated: (report: Report) => void
}

function GenerateModal({ onClose, onGenerated }: GenerateModalProps) {
  const [reportType, setReportType] = useState<ReportType>('SITREP')
  const [title, setTitle] = useState('')
  const [scenarioId, setScenarioId] = useState('')
  const [runId, setRunId] = useState('')
  const [context, setContext] = useState('')
  const [classification, setClassification] = useState<'UNCLASS' | 'FOUO' | 'SECRET'>('UNCLASS')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const req: GenerateReportRequest = {
        report_type: reportType,
        classification,
        context: context || undefined,
      }
      if (title) req.title = title
      if (scenarioId) req.scenario_id = scenarioId
      if (runId) req.run_id = runId

      const report = await reportingApi.generateReport(req)
      onGenerated(report)
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-lg font-semibold text-white mb-4">Generate Report</h2>

        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Report Type *</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as ReportType)}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
            >
              <option value="SITREP">SITREP — Situation Report</option>
              <option value="INTSUM">INTSUM — Intelligence Summary</option>
              <option value="CONOPS">CONOPS — Concept of Operations</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Title (optional)</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Auto-generated if blank"
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Scenario ID (optional)</label>
            <input
              value={scenarioId}
              onChange={(e) => setScenarioId(e.target.value)}
              placeholder="UUID of scenario"
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm font-mono"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Run ID (optional)</label>
            <input
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
              placeholder="UUID of simulation run"
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm font-mono"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Classification</label>
            <select
              value={classification}
              onChange={(e) => setClassification(e.target.value as 'UNCLASS' | 'FOUO' | 'SECRET')}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
            >
              <option value="UNCLASS">UNCLASSIFIED</option>
              <option value="FOUO">FOUO</option>
              <option value="SECRET">SECRET</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Context / Additional Details (optional)</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={3}
              placeholder="Provide context to customize the generated report..."
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="px-4 py-2 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded disabled:opacity-50 transition-colors"
          >
            {loading ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Report viewer component
// ---------------------------------------------------------------------------

function SITREPView({ content }: { content: SITREPContent }) {
  const sections: [string, string | string[]][] = [
    ['Reporting Period', `${content.period_from} → ${content.period_to}`],
    ['Situation Summary', content.situation_summary],
    ['Friendly Forces (BLUE)', content.friendly_forces],
    ['Enemy Forces (RED)', content.enemy_forces],
    ['Civilian Situation', content.civilian_situation],
    ['Current Operations', content.current_operations],
    ['Planned Operations', content.planned_operations],
    ['Logistics Status', content.logistics_status],
    ['Weather', content.weather],
    ['Commander\'s Assessment', content.commander_assessment],
    ['Next Report Due', content.next_report_due],
  ]
  return (
    <div className="space-y-4">
      {content.significant_events?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Significant Events</h3>
          <ul className="space-y-1">
            {content.significant_events.map((ev, i) => (
              <li key={i} className="text-sm text-gray-300 flex gap-2">
                <span className="text-sky-400 flex-shrink-0">•</span>
                {ev}
              </li>
            ))}
          </ul>
        </div>
      )}
      {sections.map(([label, val]) => (
        <div key={label}>
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</h3>
          <p className="text-sm text-gray-200">{String(val)}</p>
        </div>
      ))}
    </div>
  )
}

function INTSUMView({ content }: { content: INTSUMContent }) {
  const threatColor = content.threat_level === 'CRITICAL' ? 'text-red-400' :
    content.threat_level === 'HIGH' ? 'text-orange-400' :
    content.threat_level === 'MODERATE' ? 'text-yellow-400' : 'text-green-400'

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="flex-1">
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Threat Level</h3>
          <p className={`text-xl font-bold ${threatColor}`}>{content.threat_level}</p>
        </div>
        <div className="flex-1">
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Confidence</h3>
          <p className="text-sm text-gray-200">{content.confidence_level}</p>
        </div>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Enemy Disposition</h3>
        <p className="text-sm text-gray-200">{content.enemy_disposition}</p>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Enemy Intentions</h3>
        <p className="text-sm text-gray-200">{content.enemy_intentions}</p>
      </div>
      {content.key_developments?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Key Developments</h3>
          <ul className="space-y-1">
            {content.key_developments.map((dev, i) => (
              <li key={i} className="text-sm text-gray-300 flex gap-2">
                <span className="text-orange-400 flex-shrink-0">•</span>
                {dev}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Cyber Threats</h3>
        <p className="text-sm text-gray-200">{content.cyber_threats}</p>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">CBRN Threats</h3>
        <p className="text-sm text-gray-200">{content.cbrn_threats}</p>
      </div>
      {content.isr_gaps?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">ISR Gaps</h3>
          <ul className="space-y-1">
            {content.isr_gaps.map((gap, i) => (
              <li key={i} className="text-sm text-yellow-300 flex gap-2">
                <span className="flex-shrink-0">⚠</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Analyst Assessment</h3>
        <p className="text-sm text-gray-200">{content.analyst_assessment}</p>
      </div>
    </div>
  )
}

function CONOPSView({ content }: { content: CONOPSContent }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Mission Statement</h3>
        <p className="text-sm text-gray-200">{content.mission_statement}</p>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Commander's Intent</h3>
        <p className="text-sm text-gray-200">{content.commander_intent}</p>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">End State</h3>
        <p className="text-sm text-gray-200">{content.end_state}</p>
      </div>
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Scheme of Maneuver</h3>
        <p className="text-sm text-gray-200">{content.scheme_of_maneuver}</p>
      </div>
      {content.execution_phases?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Execution Phases</h3>
          <div className="space-y-2">
            {content.execution_phases.map((phase, i) => (
              <div key={i} className="bg-gray-800 rounded p-3">
                <div className="flex justify-between items-start">
                  <span className="text-sm font-medium text-sky-300">{phase.phase}</span>
                  <span className="text-xs text-gray-400">{phase.duration}</span>
                </div>
                <p className="text-sm text-gray-300 mt-1">{phase.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {content.tasks_to_subordinate_units?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">Tasks to Subordinate Units</h3>
          <div className="space-y-2">
            {content.tasks_to_subordinate_units.map((t, i) => (
              <div key={i} className="text-sm">
                <span className="text-sky-400 font-medium">{t.unit}</span>
                <span className="text-gray-400"> — </span>
                <span className="text-gray-300">{t.task}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-1">Risk Assessment</h3>
        <p className="text-sm text-gray-200">{content.risk_assessment}</p>
      </div>
    </div>
  )
}

function ReportContentView({ report }: { report: Report }) {
  const c = report.content
  if (report.report_type === 'SITREP') return <SITREPView content={c as unknown as SITREPContent} />
  if (report.report_type === 'INTSUM') return <INTSUMView content={c as unknown as INTSUMContent} />
  return <CONOPSView content={c as unknown as CONOPSContent} />
}

// ---------------------------------------------------------------------------
// Main ReportingPage
// ---------------------------------------------------------------------------

export default function ReportingPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [reports, setReports] = useState<Report[]>([])
  const [selected, setSelected] = useState<Report | null>(null)
  const [filterType, setFilterType] = useState<ReportType | ''>('')
  const [filterStatus, setFilterStatus] = useState<ReportStatus | ''>('')
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchReports = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {}
      if (filterType) params.report_type = filterType
      if (filterStatus) params.status = filterStatus
      const data = await reportingApi.listReports(params)
      setReports(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load reports')
    } finally {
      setLoading(false)
    }
  }, [filterType, filterStatus])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this report?')) return
    try {
      await reportingApi.deleteReport(id)
      setReports((prev) => prev.filter((r) => r.id !== id))
      if (selected?.id === id) setSelected(null)
    } catch {
      alert('Failed to delete report')
    }
  }

  const handleFinalize = async (id: string) => {
    try {
      const updated = await reportingApi.updateReport(id, { status: 'FINAL' })
      setReports((prev) => prev.map((r) => (r.id === id ? updated : r)))
      if (selected?.id === id) setSelected(updated)
    } catch {
      alert('Failed to finalize report')
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <div className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div>
            <h1 className="text-xl font-bold text-white">📋 Reports</h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Auto-generated SITREP, INTSUM, and CONOPS briefs
            </p>
          </div>
          <button
            onClick={() => setShowGenerateModal(true)}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-sm rounded transition-colors"
          >
            + Generate Report
          </button>
        </div>
      </div>

      <div className="flex-1 flex max-w-7xl mx-auto w-full px-6 py-6 gap-6">
        {/* Left panel: report list */}
        <div className="w-96 flex-shrink-0 flex flex-col gap-4">
          {/* Filters */}
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as ReportType | '')}
              className="flex-1 bg-gray-800 border border-gray-600 text-white rounded px-2 py-1.5 text-sm"
            >
              <option value="">All types</option>
              <option value="SITREP">SITREP</option>
              <option value="INTSUM">INTSUM</option>
              <option value="CONOPS">CONOPS</option>
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as ReportStatus | '')}
              className="flex-1 bg-gray-800 border border-gray-600 text-white rounded px-2 py-1.5 text-sm"
            >
              <option value="">All statuses</option>
              <option value="DRAFT">DRAFT</option>
              <option value="FINAL">FINAL</option>
              <option value="APPROVED">APPROVED</option>
            </select>
          </div>

          {loading && <p className="text-gray-400 text-sm">Loading…</p>}
          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="space-y-2 overflow-y-auto">
            {reports.length === 0 && !loading && (
              <p className="text-gray-500 text-sm text-center py-8">
                No reports yet. Click "Generate Report" to create one.
              </p>
            )}
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => setSelected(r)}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  selected?.id === r.id
                    ? 'border-sky-600 bg-gray-800'
                    : 'border-gray-700 bg-gray-900 hover:border-gray-600 hover:bg-gray-800'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-sky-400">{r.report_type}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[r.status]}`}>
                        {r.status}
                      </span>
                      <ClassificationBadge level={r.classification} />
                    </div>
                    <p className="text-sm text-white truncate">{r.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {new Date(r.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                {r.summary && (
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">{r.summary}</p>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Right panel: report content */}
        <div className="flex-1 min-w-0">
          {selected ? (
            <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-700">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-sky-400">{selected.report_type}</span>
                      <span className="text-xs text-gray-400">—</span>
                      <span className="text-xs text-gray-400">{REPORT_TYPE_LABELS[selected.report_type]}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${STATUS_COLORS[selected.status]}`}>
                        {selected.status}
                      </span>
                      <ClassificationBadge level={selected.classification} />
                    </div>
                    <h2 className="text-lg font-semibold text-white">{selected.title}</h2>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Generated: {new Date(selected.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    {selected.status === 'DRAFT' && (
                      <button
                        onClick={() => handleFinalize(selected.id)}
                        className="px-3 py-1.5 text-xs bg-blue-700 hover:bg-blue-600 text-white rounded transition-colors"
                      >
                        Finalize
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(selected.id)}
                      className="px-3 py-1.5 text-xs bg-red-800 hover:bg-red-700 text-white rounded transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {selected.summary && (
                  <p className="text-sm text-gray-300 mt-2 italic">{selected.summary}</p>
                )}
              </div>

              {/* Content */}
              <div className="px-6 py-5 overflow-y-auto max-h-[calc(100vh-380px)]">
                <ReportContentView report={selected} />
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-sm">
              Select a report to view its content
            </div>
          )}
        </div>
      </div>

      {showGenerateModal && (
        <GenerateModal
          onClose={() => setShowGenerateModal(false)}
          onGenerated={(report) => {
            setReports((prev) => [report, ...prev])
            setSelected(report)
          }}
        />
      )}

      <ClassificationBanner level={classification} />
    </div>
  )
}

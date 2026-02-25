import { useEffect, useState, useCallback } from 'react'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { trainingClient } from '../../shared/api/trainingClient'
import type {
  Exercise,
  ExerciseInject,
  ExerciseObjective,
  ExerciseScore,
  ExerciseStatus,
  InjectType,
  InjectTrigger,
  ObjectiveType,
  ObjectiveStatus,
  CreateInjectRequest,
  CreateObjectiveRequest,
  ScoreObjectiveRequest,
} from '../../shared/api/types/training'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type Tab = 'exercises' | 'injects' | 'objectives'

const STATUS_BADGE: Record<ExerciseStatus, string> = {
  DRAFT: 'bg-gray-700 text-gray-300',
  SCHEDULED: 'bg-blue-900 text-blue-200',
  ACTIVE: 'bg-green-900 text-green-200 animate-pulse',
  PAUSED: 'bg-yellow-900 text-yellow-200',
  COMPLETED: 'bg-teal-900 text-teal-200',
  CANCELLED: 'bg-red-900 text-red-200',
}

const INJECT_TYPE_LABELS: Record<InjectType, string> = {
  UNIT_MOVEMENT: 'Unit Movement',
  INTEL_REPORT: 'Intel Report',
  COMMS_DEGRADATION: 'Comms Degradation',
  ENEMY_ATTACK: 'Enemy Attack',
  FRIENDLY_CASUALTIES: 'Friendly Casualties',
  CBRN_ALERT: 'CBRN Alert',
  CYBER_ATTACK: 'Cyber Attack',
  CIVILIAN_INCIDENT: 'Civilian Incident',
  LOGISTICS_FAILURE: 'Logistics Failure',
  WEATHER_CHANGE: 'Weather Change',
  COMMAND_MESSAGE: 'Command Message',
  CUSTOM: 'Custom',
}

const INJECT_TRIGGER_LABELS: Record<InjectTrigger, string> = {
  TIME_BASED: 'Time-Based',
  EVENT_BASED: 'Event-Based',
  MANUAL: 'Manual',
  CONDITION_BASED: 'Condition-Based',
}

const INJECT_TYPE_COLORS: Record<string, string> = {
  ENEMY_ATTACK: 'bg-red-900 text-red-200',
  CBRN_ALERT: 'bg-orange-900 text-orange-200',
  CYBER_ATTACK: 'bg-purple-900 text-purple-200',
  FRIENDLY_CASUALTIES: 'bg-orange-900 text-orange-200',
  COMMS_DEGRADATION: 'bg-yellow-900 text-yellow-200',
  UNIT_MOVEMENT: 'bg-blue-900 text-blue-200',
  INTEL_REPORT: 'bg-sky-900 text-sky-200',
  COMMAND_MESSAGE: 'bg-indigo-900 text-indigo-200',
  CIVILIAN_INCIDENT: 'bg-pink-900 text-pink-200',
  LOGISTICS_FAILURE: 'bg-amber-900 text-amber-200',
  WEATHER_CHANGE: 'bg-teal-900 text-teal-200',
  CUSTOM: 'bg-gray-700 text-gray-300',
}

const OBJ_TYPE_COLORS: Record<ObjectiveType, string> = {
  DECISION: 'bg-blue-900 text-blue-200',
  REPORT: 'bg-sky-900 text-sky-200',
  ACTION: 'bg-orange-900 text-orange-200',
  COMMUNICATION: 'bg-purple-900 text-purple-200',
  ASSESSMENT: 'bg-teal-900 text-teal-200',
}

const OBJ_STATUS_COLORS: Record<ObjectiveStatus, string> = {
  PENDING: 'bg-gray-700 text-gray-300',
  MET: 'bg-green-900 text-green-200',
  PARTIALLY_MET: 'bg-yellow-900 text-yellow-200',
  NOT_MET: 'bg-red-900 text-red-200',
  SKIPPED: 'bg-gray-600 text-gray-400',
}

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-400',
  B: 'text-teal-400',
  C: 'text-yellow-400',
  D: 'text-orange-400',
  F: 'text-red-400',
}

// ---------------------------------------------------------------------------
// Add Inject Modal
// ---------------------------------------------------------------------------

interface AddInjectModalProps {
  exerciseId: string
  onClose: () => void
  onCreated: (inject: ExerciseInject) => void
}

function AddInjectModal({ exerciseId, onClose, onCreated }: AddInjectModalProps) {
  const [injectType, setInjectType] = useState<InjectType>('UNIT_MOVEMENT')
  const [triggerType, setTriggerType] = useState<InjectTrigger>('MANUAL')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [offsetMinutes, setOffsetMinutes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    setLoading(true)
    setError(null)
    try {
      const body: CreateInjectRequest = {
        exercise_id: exerciseId,
        inject_type: injectType,
        trigger_type: triggerType,
        title,
        description: description || null,
        trigger_time_offset_minutes: offsetMinutes ? parseInt(offsetMinutes, 10) : null,
      }
      const resp = await trainingClient.post<ExerciseInject>('/injects', body)
      onCreated(resp.data)
      onClose()
    } catch {
      setError('Failed to create inject')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-lg font-semibold text-white mb-4">Add Inject</h2>
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Inject Type</label>
              <select
                value={injectType}
                onChange={(e) => setInjectType(e.target.value as InjectType)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                {Object.entries(INJECT_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Trigger</label>
              <select
                value={triggerType}
                onChange={(e) => setTriggerType(e.target.value as InjectTrigger)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                {Object.entries(INJECT_TRIGGER_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Title *</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              placeholder="e.g. OPFOR contact at Grid 445621"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
            />
          </div>
          {triggerType === 'TIME_BASED' && (
            <div>
              <label className="block text-sm text-gray-400 mb-1">Trigger Offset (minutes)</label>
              <input
                value={offsetMinutes}
                onChange={(e) => setOffsetMinutes(e.target.value)}
                type="number"
                min={0}
                className="w-32 bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
                placeholder="15"
              />
            </div>
          )}
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>
        <div className="flex justify-end gap-3 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={loading || !title}
            className="px-4 py-2 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded disabled:opacity-50 transition-colors"
          >
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Add Objective Modal
// ---------------------------------------------------------------------------

interface AddObjectiveModalProps {
  exerciseId: string
  onClose: () => void
  onCreated: (obj: ExerciseObjective) => void
}

function AddObjectiveModal({ exerciseId, onClose, onCreated }: AddObjectiveModalProps) {
  const [objType, setObjType] = useState<ObjectiveType>('DECISION')
  const [description, setDescription] = useState('')
  const [expectedResponse, setExpectedResponse] = useState('')
  const [weight, setWeight] = useState('1.0')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    setLoading(true)
    setError(null)
    try {
      const body: CreateObjectiveRequest = {
        exercise_id: exerciseId,
        objective_type: objType,
        description,
        expected_response: expectedResponse || null,
        weight: parseFloat(weight) || 1.0,
      }
      const resp = await trainingClient.post<ExerciseObjective>('/objectives', body)
      onCreated(resp.data)
      onClose()
    } catch {
      setError('Failed to create objective')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-lg font-semibold text-white mb-4">Add Objective</h2>
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Type</label>
              <select
                value={objType}
                onChange={(e) => setObjType(e.target.value as ObjectiveType)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                <option value="DECISION">Decision</option>
                <option value="REPORT">Report</option>
                <option value="ACTION">Action</option>
                <option value="COMMUNICATION">Communication</option>
                <option value="ASSESSMENT">Assessment</option>
              </select>
            </div>
            <div className="w-28">
              <label className="block text-sm text-gray-400 mb-1">Weight (0–1)</label>
              <input
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                type="number"
                step="0.1"
                min={0}
                max={1}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Description *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
              placeholder="Describe what the trainee must do"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Expected Response (optional)</label>
            <textarea
              value={expectedResponse}
              onChange={(e) => setExpectedResponse(e.target.value)}
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
              placeholder="Ideal trainee response"
            />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>
        <div className="flex justify-end gap-3 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={loading || !description}
            className="px-4 py-2 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded disabled:opacity-50 transition-colors"
          >
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Score Objective Modal
// ---------------------------------------------------------------------------

interface ScoreObjectiveModalProps {
  objective: ExerciseObjective
  onClose: () => void
  onScored: (obj: ExerciseObjective) => void
}

function ScoreObjectiveModal({ objective, onClose, onScored }: ScoreObjectiveModalProps) {
  const [objStatus, setObjStatus] = useState<ObjectiveStatus>(objective.status === 'PENDING' ? 'MET' : objective.status)
  const [score, setScore] = useState(objective.score?.toString() ?? '80')
  const [actualResponse, setActualResponse] = useState(objective.actual_response ?? '')
  const [feedback, setFeedback] = useState(objective.feedback ?? '')
  const [scorerId, setScorerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleScore = async () => {
    setLoading(true)
    setError(null)
    try {
      const body: ScoreObjectiveRequest = {
        status: objStatus,
        actual_response: actualResponse || null,
        score: score ? parseFloat(score) : null,
        feedback: feedback || null,
        scorer_id: scorerId || 'instructor',
      }
      const resp = await trainingClient.post<ExerciseObjective>(
        `/objectives/${objective.id}/score`,
        body
      )
      onScored(resp.data)
      onClose()
    } catch {
      setError('Failed to score objective')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 w-full max-w-lg">
        <h2 className="text-lg font-semibold text-white mb-1">Score Objective</h2>
        <p className="text-sm text-gray-400 mb-4 line-clamp-2">{objective.description}</p>
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Outcome</label>
              <select
                value={objStatus}
                onChange={(e) => setObjStatus(e.target.value as ObjectiveStatus)}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              >
                <option value="MET">Met</option>
                <option value="PARTIALLY_MET">Partially Met</option>
                <option value="NOT_MET">Not Met</option>
                <option value="SKIPPED">Skipped</option>
              </select>
            </div>
            <div className="w-28">
              <label className="block text-sm text-gray-400 mb-1">Score (0–100)</label>
              <input
                value={score}
                onChange={(e) => setScore(e.target.value)}
                type="number"
                min={0}
                max={100}
                className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Actual Response</label>
            <textarea
              value={actualResponse}
              onChange={(e) => setActualResponse(e.target.value)}
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Feedback</label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={2}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm resize-none"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Scorer ID</label>
            <input
              value={scorerId}
              onChange={(e) => setScorerId(e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
              placeholder="instructor"
            />
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
        </div>
        <div className="flex justify-end gap-3 mt-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleScore}
            disabled={loading}
            className="px-4 py-2 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded disabled:opacity-50 transition-colors"
          >
            {loading ? 'Saving…' : 'Save Score'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Exercises Tab
// ---------------------------------------------------------------------------

function ExercisesTab() {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [scores, setScores] = useState<Record<string, ExerciseScore>>({})

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await trainingClient.get<Exercise[]>('/exercises')
      setExercises(resp.data)
    } catch {
      setError('Failed to load exercises')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const transition = async (id: string, action: 'start' | 'pause' | 'complete') => {
    try {
      const resp = await trainingClient.post<Exercise>(`/exercises/${id}/${action}`)
      setExercises((prev) => prev.map((e) => e.id === id ? resp.data : e))
    } catch {
      setError(`Failed to ${action} exercise`)
    }
  }

  const loadScore = async (id: string) => {
    try {
      const resp = await trainingClient.get<ExerciseScore>(`/exercises/${id}/score`)
      setScores((prev) => ({ ...prev, [id]: resp.data }))
    } catch {
      // score may not be available yet
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => prev === id ? null : id)
    if (!scores[id]) loadScore(id)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-gray-400">{exercises.length} exercise{exercises.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => {/* TODO: Add exercise modal */}}
          className="px-3 py-1.5 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded transition-colors"
        >
          + Create Exercise
        </button>
      </div>

      {loading && <p className="text-gray-400 text-sm">Loading…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="space-y-3">
        {exercises.map((ex) => (
          <div key={ex.id} className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
            {/* Header row */}
            <div
              className="p-4 cursor-pointer hover:bg-gray-800/50 transition-colors"
              onClick={() => toggleExpand(ex.id)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-white truncate">{ex.name}</h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Instructor: <span className="text-gray-300">{ex.instructor_id}</span>
                    {' · '}
                    {ex.trainee_ids.length} trainee{ex.trainee_ids.length !== 1 ? 's' : ''}
                    {ex.planned_start && (
                      <>{' · '}Planned: {new Date(ex.planned_start).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 ${STATUS_BADGE[ex.status]}`}>
                  {ex.status}
                </span>
              </div>
            </div>

            {/* Expanded detail */}
            {expandedId === ex.id && (
              <div className="border-t border-gray-700 p-4 bg-gray-800/30">
                {/* Learning objectives */}
                {ex.learning_objectives.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Learning Objectives</p>
                    <ul className="space-y-1">
                      {ex.learning_objectives.map((lo, idx) => (
                        <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                          <span className="text-sky-500 mt-0.5">›</span>
                          {lo}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex gap-2 mb-4">
                  {(ex.status === 'DRAFT' || ex.status === 'SCHEDULED' || ex.status === 'PAUSED') && (
                    <button
                      onClick={() => transition(ex.id, 'start')}
                      className="px-3 py-1.5 text-xs bg-green-700 hover:bg-green-600 text-white rounded transition-colors"
                    >
                      ▶ Start
                    </button>
                  )}
                  {ex.status === 'ACTIVE' && (
                    <>
                      <button
                        onClick={() => transition(ex.id, 'pause')}
                        className="px-3 py-1.5 text-xs bg-yellow-700 hover:bg-yellow-600 text-white rounded transition-colors"
                      >
                        ⏸ Pause
                      </button>
                      <button
                        onClick={() => transition(ex.id, 'complete')}
                        className="px-3 py-1.5 text-xs bg-teal-700 hover:bg-teal-600 text-white rounded transition-colors"
                      >
                        ✓ Complete
                      </button>
                    </>
                  )}
                </div>

                {/* Score section */}
                {ex.status === 'COMPLETED' && (
                  <div>
                    <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Exercise Score</p>
                    {scores[ex.id] ? (
                      <ScoreCard score={scores[ex.id]} />
                    ) : (
                      <button
                        onClick={() => loadScore(ex.id)}
                        className="text-xs text-sky-400 hover:text-sky-300 transition-colors"
                      >
                        Load score…
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {!loading && exercises.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-10">
            No exercises found. Click "Create Exercise" to get started.
          </p>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Score Card
// ---------------------------------------------------------------------------

function ScoreCard({ score }: { score: ExerciseScore }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center gap-4 mb-3">
        <div className="text-center">
          <p className={`text-4xl font-bold ${GRADE_COLORS[score.grade] ?? 'text-white'}`}>
            {score.grade}
          </p>
          <p className="text-xs text-gray-400">Grade</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{score.total_score.toFixed(1)}</p>
          <p className="text-xs text-gray-400">Total Score</p>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
        <ScoreStat label="Objectives Met" value={`${score.objectives_met}/${score.objectives_total}`} />
        <ScoreStat label="Partial" value={String(score.objectives_partial)} />
        <ScoreStat label="Not Met" value={String(score.objectives_not_met)} />
        <ScoreStat label="Completion" value={`${score.completion_pct.toFixed(0)}%`} />
        <ScoreStat label="Timeliness" value={`${score.timeliness_score.toFixed(0)}%`} />
        <ScoreStat label="Accuracy" value={`${score.accuracy_score.toFixed(0)}%`} />
      </div>
    </div>
  )
}

function ScoreStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="font-mono font-medium text-gray-200">{value}</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Injects Tab
// ---------------------------------------------------------------------------

function InjectsTab({ exercises }: { exercises: Exercise[] }) {
  const [selectedExercise, setSelectedExercise] = useState('')
  const [injects, setInjects] = useState<ExerciseInject[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)

  const load = useCallback(async () => {
    if (!selectedExercise) return
    setLoading(true)
    setError(null)
    try {
      const resp = await trainingClient.get<ExerciseInject[]>('/injects', {
        params: { exercise_id: selectedExercise },
      })
      setInjects(resp.data)
    } catch {
      setError('Failed to load injects')
    } finally {
      setLoading(false)
    }
  }, [selectedExercise])

  useEffect(() => { load() }, [load])

  const fireInject = async (id: string) => {
    try {
      const resp = await trainingClient.post<ExerciseInject>(`/injects/${id}/fire`)
      setInjects((prev) => prev.map((inj) => inj.id === id ? resp.data : inj))
    } catch {
      setError('Failed to fire inject')
    }
  }

  const acknowledgeInject = async (id: string) => {
    try {
      const resp = await trainingClient.post<ExerciseInject>(`/injects/${id}/acknowledge`, null, {
        params: { acknowledged_by: 'trainee' },
      })
      setInjects((prev) => prev.map((inj) => inj.id === id ? resp.data : inj))
    } catch {
      setError('Failed to acknowledge inject')
    }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <select
          value={selectedExercise}
          onChange={(e) => setSelectedExercise(e.target.value)}
          className="flex-1 max-w-sm bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
        >
          <option value="">— Select Exercise —</option>
          {exercises.map((ex) => (
            <option key={ex.id} value={ex.id}>{ex.name}</option>
          ))}
        </select>
        {selectedExercise && (
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded transition-colors"
          >
            + Add Inject
          </button>
        )}
      </div>

      {!selectedExercise && (
        <p className="text-gray-500 text-sm text-center py-10">Select an exercise to view injects.</p>
      )}

      {selectedExercise && (
        <>
          {loading && <p className="text-gray-400 text-sm">Loading…</p>}
          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="space-y-2">
            {injects.map((inj) => (
              <div key={inj.id} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${INJECT_TYPE_COLORS[inj.inject_type] ?? 'bg-gray-700 text-gray-300'}`}>
                        {INJECT_TYPE_LABELS[inj.inject_type]}
                      </span>
                      <span className="text-xs text-gray-500">
                        {INJECT_TRIGGER_LABELS[inj.trigger_type]}
                        {inj.trigger_time_offset_minutes != null && ` (+${inj.trigger_time_offset_minutes}m)`}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-white">{inj.title}</p>
                    {inj.description && (
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{inj.description}</p>
                    )}
                    {inj.acknowledged_by && (
                      <p className="text-xs text-teal-400 mt-1">
                        ✓ Acknowledged by {inj.acknowledged_by}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col gap-1.5 shrink-0">
                    {inj.status === 'PENDING' && (
                      <button
                        onClick={() => fireInject(inj.id)}
                        className="px-2 py-1 text-xs bg-orange-700 hover:bg-orange-600 text-white rounded transition-colors"
                      >
                        Fire
                      </button>
                    )}
                    {inj.status === 'INJECTED' && (
                      <button
                        onClick={() => acknowledgeInject(inj.id)}
                        className="px-2 py-1 text-xs bg-teal-700 hover:bg-teal-600 text-white rounded transition-colors"
                      >
                        Ack
                      </button>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded text-center ${
                      inj.status === 'PENDING' ? 'bg-gray-700 text-gray-300'
                      : inj.status === 'INJECTED' ? 'bg-orange-900 text-orange-200'
                      : inj.status === 'ACKNOWLEDGED' ? 'bg-teal-900 text-teal-200'
                      : 'bg-gray-600 text-gray-400'
                    }`}>
                      {inj.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}

            {!loading && injects.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-8">
                No injects for this exercise. Click "Add Inject" to create one.
              </p>
            )}
          </div>
        </>
      )}

      {showAddModal && selectedExercise && (
        <AddInjectModal
          exerciseId={selectedExercise}
          onClose={() => setShowAddModal(false)}
          onCreated={(inj) => { setInjects((prev) => [...prev, inj]); setShowAddModal(false) }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Objectives Tab
// ---------------------------------------------------------------------------

function ObjectivesTab({ exercises }: { exercises: Exercise[] }) {
  const [selectedExercise, setSelectedExercise] = useState('')
  const [objectives, setObjectives] = useState<ExerciseObjective[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [scoringObj, setScoringObj] = useState<ExerciseObjective | null>(null)

  const load = useCallback(async () => {
    if (!selectedExercise) return
    setLoading(true)
    setError(null)
    try {
      const resp = await trainingClient.get<ExerciseObjective[]>('/objectives', {
        params: { exercise_id: selectedExercise },
      })
      setObjectives(resp.data)
    } catch {
      setError('Failed to load objectives')
    } finally {
      setLoading(false)
    }
  }, [selectedExercise])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <select
          value={selectedExercise}
          onChange={(e) => setSelectedExercise(e.target.value)}
          className="flex-1 max-w-sm bg-gray-800 border border-gray-600 text-white rounded px-3 py-2 text-sm"
        >
          <option value="">— Select Exercise —</option>
          {exercises.map((ex) => (
            <option key={ex.id} value={ex.id}>{ex.name}</option>
          ))}
        </select>
        {selectedExercise && (
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 text-sm bg-sky-600 hover:bg-sky-500 text-white rounded transition-colors"
          >
            + Add Objective
          </button>
        )}
      </div>

      {!selectedExercise && (
        <p className="text-gray-500 text-sm text-center py-10">Select an exercise to view objectives.</p>
      )}

      {selectedExercise && (
        <>
          {loading && <p className="text-gray-400 text-sm">Loading…</p>}
          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="space-y-2">
            {objectives.map((obj) => (
              <div key={obj.id} className="bg-gray-900 border border-gray-700 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${OBJ_TYPE_COLORS[obj.objective_type]}`}>
                        {obj.objective_type}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${OBJ_STATUS_COLORS[obj.status]}`}>
                        {obj.status.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500">
                        weight: {obj.weight.toFixed(1)}
                      </span>
                      {obj.score != null && (
                        <span className="text-xs font-mono font-medium text-yellow-300">
                          {obj.score.toFixed(0)}/100
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-200">{obj.description}</p>
                    {obj.feedback && (
                      <p className="text-xs text-gray-400 mt-1 italic">{obj.feedback}</p>
                    )}
                  </div>
                  <button
                    onClick={() => setScoringObj(obj)}
                    className="px-2 py-1 text-xs bg-sky-700 hover:bg-sky-600 text-white rounded transition-colors shrink-0"
                  >
                    Score
                  </button>
                </div>
              </div>
            ))}

            {!loading && objectives.length === 0 && (
              <p className="text-gray-500 text-sm text-center py-8">
                No objectives for this exercise. Click "Add Objective" to create one.
              </p>
            )}
          </div>
        </>
      )}

      {showAddModal && selectedExercise && (
        <AddObjectiveModal
          exerciseId={selectedExercise}
          onClose={() => setShowAddModal(false)}
          onCreated={(obj) => { setObjectives((prev) => [...prev, obj]); setShowAddModal(false) }}
        />
      )}

      {scoringObj && (
        <ScoreObjectiveModal
          objective={scoringObj}
          onClose={() => setScoringObj(null)}
          onScored={(updated) => {
            setObjectives((prev) => prev.map((o) => o.id === updated.id ? updated : o))
            setScoringObj(null)
          }}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main TrainingPage
// ---------------------------------------------------------------------------

export default function TrainingPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const [activeTab, setActiveTab] = useState<Tab>('exercises')
  const [exercises, setExercises] = useState<Exercise[]>([])

  // Load exercises once for the exercise selector in Injects/Objectives tabs
  useEffect(() => {
    trainingClient.get<Exercise[]>('/exercises').then((r) => setExercises(r.data)).catch(() => {})
  }, [])

  const tabs: { id: Tab; label: string }[] = [
    { id: 'exercises', label: 'Exercises' },
    { id: 'injects', label: 'Injects' },
    { id: 'objectives', label: 'Objectives' },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <div className="bg-gray-900 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-xl font-bold text-white">🎓 Training Mode</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Exercise management, scripted inject system, and trainee performance scoring
          </p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="bg-gray-900 border-b border-gray-700 px-6">
        <div className="max-w-7xl mx-auto flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === tab.id
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 px-6 py-6 max-w-7xl mx-auto w-full">
        {activeTab === 'exercises' && <ExercisesTab />}
        {activeTab === 'injects' && <InjectsTab exercises={exercises} />}
        {activeTab === 'objectives' && <ObjectivesTab exercises={exercises} />}
      </div>

      <ClassificationBanner level={classification} />
    </div>
  )
}

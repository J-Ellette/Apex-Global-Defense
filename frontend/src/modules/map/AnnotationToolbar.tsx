import { clsx } from 'clsx'

export type DrawMode = 'none' | 'marker' | 'line' | 'polygon' | 'text'

interface AnnotationToolbarProps {
  mode: DrawMode
  onModeChange: (mode: DrawMode) => void
  onClearAnnotations: () => void
  annotationCount: number
}

interface Tool {
  mode: DrawMode
  icon: string
  label: string
}

const TOOLS: Tool[] = [
  { mode: 'marker',  icon: '📍', label: 'Place marker' },
  { mode: 'line',    icon: '📏', label: 'Draw line' },
  { mode: 'polygon', icon: '⬡',  label: 'Draw polygon' },
  { mode: 'text',    icon: '🔤', label: 'Add label' },
]

export function AnnotationToolbar({
  mode,
  onModeChange,
  onClearAnnotations,
  annotationCount,
}: AnnotationToolbarProps) {
  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-1 rounded-lg border border-gray-700 bg-gray-900/90 backdrop-blur-sm px-2 py-1.5 shadow-lg">
      {TOOLS.map((tool) => (
        <button
          key={tool.mode}
          title={tool.label}
          aria-label={tool.label}
          aria-pressed={mode === tool.mode}
          onClick={() => onModeChange(mode === tool.mode ? 'none' : tool.mode)}
          className={clsx(
            'flex items-center justify-center w-8 h-8 rounded text-base transition-colors',
            mode === tool.mode
              ? 'bg-sky-600 text-white'
              : 'text-gray-300 hover:bg-gray-700',
          )}
        >
          {tool.icon}
        </button>
      ))}

      <div className="w-px h-5 bg-gray-700 mx-1" aria-hidden />

      <button
        title="Clear all annotations"
        aria-label="Clear all annotations"
        disabled={annotationCount === 0}
        onClick={onClearAnnotations}
        className="flex items-center justify-center w-8 h-8 rounded text-base text-gray-400 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        🗑️
      </button>

      {annotationCount > 0 && (
        <span className="ml-1 text-xs text-gray-400">
          {annotationCount} {annotationCount === 1 ? 'annotation' : 'annotations'}
        </span>
      )}

      {mode !== 'none' && (
        <span className="ml-1 text-xs text-sky-400 animate-pulse">
          {mode === 'marker'  && 'Click to place marker'}
          {mode === 'line'    && 'Click to add points • double-click to finish'}
          {mode === 'polygon' && 'Click to add points • double-click to close'}
          {mode === 'text'    && 'Click to place label'}
        </span>
      )}
    </div>
  )
}

import { clsx } from 'clsx'
import type { MapLayer, LayerId } from './hooks/useMapLayers'

interface LayerPanelProps {
  layers: MapLayer[]
  onToggle: (id: LayerId) => void
  onOpacityChange: (id: LayerId, opacity: number) => void
}

export function LayerPanel({ layers, onToggle, onOpacityChange }: LayerPanelProps) {
  return (
    <aside className="absolute top-4 right-4 z-10 w-56 rounded-lg border border-gray-700 bg-gray-900/90 backdrop-blur-sm shadow-lg overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-700">
        <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Layers</p>
      </div>

      <ul className="divide-y divide-gray-800/60">
        {layers.map((layer) => (
          <li key={layer.id} className="px-3 py-2">
            <div className="flex items-center gap-2">
              <button
                role="switch"
                aria-checked={layer.visible}
                aria-label={`Toggle ${layer.label}`}
                onClick={() => onToggle(layer.id)}
                className={clsx(
                  'relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-1 focus:ring-offset-gray-900',
                  layer.visible ? 'bg-sky-600' : 'bg-gray-600',
                )}
              >
                <span
                  className={clsx(
                    'pointer-events-none inline-block h-3 w-3 rounded-full bg-white shadow-sm transform transition-transform',
                    layer.visible ? 'translate-x-3' : 'translate-x-0',
                  )}
                />
              </button>
              <span className={clsx('text-xs truncate', layer.visible ? 'text-gray-200' : 'text-gray-500')}>
                {layer.label}
              </span>
            </div>

            {layer.visible && layer.id !== 'osm-base' && (
              <div className="mt-1.5 pl-9 flex items-center gap-2">
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={layer.opacity}
                  aria-label={`${layer.label} opacity`}
                  onChange={(e) => onOpacityChange(layer.id, parseFloat(e.target.value))}
                  className="w-full h-1 appearance-none rounded bg-gray-600 accent-sky-500"
                />
                <span className="text-xs text-gray-500 shrink-0 w-8 text-right">
                  {Math.round(layer.opacity * 100)}%
                </span>
              </div>
            )}
          </li>
        ))}
      </ul>
    </aside>
  )
}

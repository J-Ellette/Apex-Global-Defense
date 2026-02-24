import { useState, useCallback, useMemo } from 'react'
import { useAuthStore } from '../../app/providers/AuthProvider'
import { ClassificationBanner } from '../../shared/components/ClassificationBanner'
import { MapCanvas } from './MapCanvas'
import { LayerPanel } from './LayerPanel'
import { AnnotationToolbar, type DrawMode } from './AnnotationToolbar'
import { useMapLayers } from './hooks/useMapLayers'

// Annotation shape stored in local state (persisted to scenario on save).
export interface Annotation {
  id: string
  type: 'marker' | 'line' | 'polygon' | 'text'
  coordinates: [number, number] | [number, number][]
  label: string
  color: string
}

export default function MapPage() {
  const classification = useAuthStore((s) => s.user?.classification ?? 'UNCLASS')
  const { layers, toggleLayer, setOpacity, isVisible } = useMapLayers()

  const [drawMode, setDrawMode]     = useState<DrawMode>('none')
  const [annotations, setAnnotations] = useState<Annotation[]>([])

  const handleAnnotationAdd = useCallback((annotation: Annotation) => {
    setAnnotations((prev) => [...prev, annotation])
  }, [])

  const handleClearAnnotations = useCallback(() => {
    setAnnotations([])
  }, [])

  // Derived maps for MapCanvas
  const layerVisibility = useMemo(
    () => Object.fromEntries(layers.map((l) => [l.id, l.visible])),
    [layers],
  )
  const layerOpacity = useMemo(
    () => Object.fromEntries(layers.map((l) => [l.id, l.opacity])),
    [layers],
  )

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      <ClassificationBanner level={classification} />

      <main className="flex-1 relative overflow-hidden">
        {/* Full-bleed map canvas */}
        <MapCanvas
          drawMode={drawMode}
          annotations={annotations}
          onAnnotationAdd={handleAnnotationAdd}
          layerVisibility={layerVisibility}
          layerOpacity={layerOpacity}
        />

        {/* Floating annotation toolbar */}
        <AnnotationToolbar
          mode={drawMode}
          onModeChange={setDrawMode}
          onClearAnnotations={handleClearAnnotations}
          annotationCount={annotations.length}
        />

        {/* Floating layer panel */}
        <LayerPanel
          layers={layers}
          onToggle={toggleLayer}
          onOpacityChange={setOpacity}
        />

        {/* Deactivate draw mode on ESC */}
        <div
          className="sr-only"
          onKeyDown={(e) => { if (e.key === 'Escape') setDrawMode('none') }}
          tabIndex={-1}
        />
      </main>

      <ClassificationBanner level={classification} />
    </div>
  )
}

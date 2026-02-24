import { useState, useCallback } from 'react'

export type LayerId = 'osm-base' | 'unit-markers' | 'aor-polygons' | 'intel-points' | 'annotations' | 'population-density' | 'refugee-flows' | 'humanitarian-corridors'

export interface MapLayer {
  id: LayerId
  label: string
  visible: boolean
  opacity: number
}

const DEFAULT_LAYERS: MapLayer[] = [
  { id: 'osm-base',      label: 'Base Map',          visible: true,  opacity: 1 },
  { id: 'unit-markers',  label: 'Military Units',     visible: true,  opacity: 1 },
  { id: 'aor-polygons',  label: 'Areas of Responsibility', visible: false, opacity: 0.4 },
  { id: 'intel-points',  label: 'Intel Items',        visible: false, opacity: 1 },
  { id: 'annotations',              label: 'Annotations',              visible: true,  opacity: 1 },
  { id: 'population-density',        label: 'Population Density',        visible: false, opacity: 0.6 },
  { id: 'refugee-flows',             label: 'Refugee Flows',             visible: false, opacity: 0.8 },
  { id: 'humanitarian-corridors',    label: 'Humanitarian Corridors',    visible: false, opacity: 0.9 },
]

export function useMapLayers() {
  const [layers, setLayers] = useState<MapLayer[]>(DEFAULT_LAYERS)

  const toggleLayer = useCallback((id: LayerId) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, visible: !l.visible } : l)),
    )
  }, [])

  const setOpacity = useCallback((id: LayerId, opacity: number) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === id ? { ...l, opacity } : l)),
    )
  }, [])

  const isVisible = useCallback(
    (id: LayerId) => layers.find((l) => l.id === id)?.visible ?? false,
    [layers],
  )

  return { layers, toggleLayer, setOpacity, isVisible }
}

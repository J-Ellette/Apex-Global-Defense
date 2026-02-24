import { useEffect, useRef, useCallback, useState } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { DrawMode } from './AnnotationToolbar'
import type { Annotation } from './MapPage'

const TILE_SERVER = import.meta.env.VITE_TILE_SERVER ?? 'https://tile.openstreetmap.org'
const AIRGAP      = import.meta.env.VITE_AIRGAP === 'true'

// Tile URL: air-gap uses local MBTileserver, otherwise falls back to OSM CDN.
function tileUrl(): string {
  if (AIRGAP) return `${TILE_SERVER}/osm/{z}/{x}/{y}.png`
  return 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
}

interface MapCanvasProps {
  drawMode: DrawMode
  annotations: Annotation[]
  onAnnotationAdd: (annotation: Annotation) => void
  layerVisibility: Record<string, boolean>
  layerOpacity: Record<string, number>
}

export function MapCanvas({
  drawMode,
  annotations,
  onAnnotationAdd,
  layerVisibility,
  layerOpacity,
}: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef       = useRef<maplibregl.Map | null>(null)
  const linePointsRef = useRef<[number, number][]>([])
  const tempMarkerRef = useRef<maplibregl.Marker[]>([])

  // Pending text annotation — coordinates waiting for a label
  const [pendingText, setPendingText] = useState<{ coords: [number, number]; label: string } | null>(null)

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: [tileUrl()],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
            maxzoom: 19,
          },
        },
        layers: [
          {
            id: 'osm-base',
            type: 'raster',
            source: 'osm-tiles',
            paint: { 'raster-opacity': 1 },
          },
        ],
      },
      center: [0, 20],
      zoom: 2,
    })

    map.addControl(new maplibregl.NavigationControl(), 'bottom-right')
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left')
    map.addControl(new maplibregl.FullscreenControl(), 'bottom-right')

    // Add GeoJSON sources for annotations
    map.on('load', () => {
      map.addSource('annotation-points', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addSource('annotation-lines', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addSource('annotation-polygons', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      map.addLayer({
        id: 'annotation-polygons-fill',
        type: 'fill',
        source: 'annotation-polygons',
        paint: { 'fill-color': ['get', 'color'], 'fill-opacity': 0.25 },
      })
      map.addLayer({
        id: 'annotation-polygons-outline',
        type: 'line',
        source: 'annotation-polygons',
        paint: { 'line-color': ['get', 'color'], 'line-width': 2 },
      })
      map.addLayer({
        id: 'annotation-lines',
        type: 'line',
        source: 'annotation-lines',
        paint: { 'line-color': ['get', 'color'], 'line-width': 2, 'line-dasharray': [2, 1] },
      })
      map.addLayer({
        id: 'annotation-labels',
        type: 'symbol',
        source: 'annotation-points',
        layout: {
          'text-field': ['get', 'label'],
          'text-offset': [0, 1.5],
          'text-size': 12,
        },
        paint: { 'text-color': '#ffffff', 'text-halo-color': '#000000', 'text-halo-width': 1 },
      })
    })

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Handle map clicks for annotation drawing
  const handleClick = useCallback(
    (e: maplibregl.MapMouseEvent) => {
      const { lng, lat } = e.lngLat

      if (drawMode === 'marker') {
        onAnnotationAdd({
          id: crypto.randomUUID(),
          type: 'marker',
          coordinates: [lng, lat],
          label: '',
          color: '#FF4444',
        })
        return
      }

      if (drawMode === 'text') {
        setPendingText({ coords: [lng, lat], label: '' })
        return
      }

      if (drawMode === 'line' || drawMode === 'polygon') {
        linePointsRef.current.push([lng, lat])

        // Add temporary vertex marker
        const el = document.createElement('div')
        el.className = 'w-2 h-2 rounded-full bg-sky-400 border border-white'
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([lng, lat])
          .addTo(mapRef.current!)
        tempMarkerRef.current.push(marker)
      }
    },
    [drawMode, onAnnotationAdd],
  )

  // Handle double-click to finish line/polygon
  const handleDblClick = useCallback(
    (e: maplibregl.MapMouseEvent) => {
      e.preventDefault()
      if (drawMode !== 'line' && drawMode !== 'polygon') return
      const pts = linePointsRef.current
      if (pts.length < 2) {
        linePointsRef.current = []
        tempMarkerRef.current.forEach((m) => m.remove())
        tempMarkerRef.current = []
        return
      }

      onAnnotationAdd({
        id: crypto.randomUUID(),
        type: drawMode,
        coordinates: drawMode === 'polygon' ? [...pts, pts[0]] : pts,
        label: '',
        color: '#FF4444',
      })

      linePointsRef.current = []
      tempMarkerRef.current.forEach((m) => m.remove())
      tempMarkerRef.current = []
    },
    [drawMode, onAnnotationAdd],
  )

  // Wire up / tear down click handlers when draw mode changes
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    map.getCanvas().style.cursor = drawMode !== 'none' ? 'crosshair' : ''
    map.on('click', handleClick)
    map.on('dblclick', handleDblClick)
    return () => {
      map.off('click', handleClick)
      map.off('dblclick', handleDblClick)
    }
  }, [drawMode, handleClick, handleDblClick])

  // Sync annotation GeoJSON sources
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    const pointFeatures = annotations
      .filter((a) => a.type === 'marker' || a.type === 'text')
      .map((a) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: a.coordinates as [number, number] },
        properties: { label: a.label, color: a.color },
      }))

    const lineFeatures = annotations
      .filter((a) => a.type === 'line')
      .map((a) => ({
        type: 'Feature' as const,
        geometry: {
          type: 'LineString' as const,
          coordinates: a.coordinates as [number, number][],
        },
        properties: { color: a.color },
      }))

    const polygonFeatures = annotations
      .filter((a) => a.type === 'polygon')
      .map((a) => ({
        type: 'Feature' as const,
        geometry: {
          type: 'Polygon' as const,
          coordinates: [a.coordinates as [number, number][]],
        },
        properties: { color: a.color },
      }))

    ;(map.getSource('annotation-points') as maplibregl.GeoJSONSource | undefined)?.setData({
      type: 'FeatureCollection',
      features: pointFeatures,
    })
    ;(map.getSource('annotation-lines') as maplibregl.GeoJSONSource | undefined)?.setData({
      type: 'FeatureCollection',
      features: lineFeatures,
    })
    ;(map.getSource('annotation-polygons') as maplibregl.GeoJSONSource | undefined)?.setData({
      type: 'FeatureCollection',
      features: polygonFeatures,
    })

    // Add/remove DOM markers for point annotations
    // (Handled via GeoJSON symbol layer above)
  }, [annotations])

  // Layer visibility + opacity sync
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    const layerMap: Record<string, string[]> = {
      'osm-base':     ['osm-base'],
      'annotations':  ['annotation-polygons-fill', 'annotation-polygons-outline', 'annotation-lines', 'annotation-labels'],
    }

    Object.entries(layerVisibility).forEach(([layerId, visible]) => {
      const glLayers = layerMap[layerId]
      if (!glLayers) return
      glLayers.forEach((glId) => {
        if (map.getLayer(glId)) {
          map.setLayoutProperty(glId, 'visibility', visible ? 'visible' : 'none')
        }
      })
    })
    Object.entries(layerOpacity).forEach(([layerId, opacity]) => {
      if (layerId === 'osm-base' && map.getLayer('osm-base')) {
        map.setPaintProperty('osm-base', 'raster-opacity', opacity)
      }
    })
  }, [layerVisibility, layerOpacity])

  function commitPendingText() {
    if (!pendingText) return
    if (pendingText.label.trim()) {
      onAnnotationAdd({
        id: crypto.randomUUID(),
        type: 'text',
        coordinates: pendingText.coords,
        label: pendingText.label.trim(),
        color: '#FF4444',
      })
    }
    setPendingText(null)
  }

  return (
    <div className="relative w-full h-full">
      <div
        ref={containerRef}
        className="w-full h-full"
        aria-label="Geospatial map"
        data-testid="map-canvas"
      />

      {/* Inline label input for text annotations */}
      {pendingText && (
        <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Add map label"
            className="pointer-events-auto rounded-lg border border-gray-700 bg-gray-900/95 backdrop-blur-sm shadow-xl p-4 w-72 space-y-3"
          >
            <p className="text-sm font-medium text-white">Add label</p>
            <input
              autoFocus
              value={pendingText.label}
              onChange={(e) => setPendingText({ ...pendingText, label: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commitPendingText()
                if (e.key === 'Escape') setPendingText(null)
              }}
              placeholder="Enter label text…"
              className="w-full rounded bg-gray-800 border border-gray-700 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setPendingText(null)}
                className="px-3 py-1.5 text-xs text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={commitPendingText}
                disabled={!pendingText.label.trim()}
                className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-40 transition-colors"
              >
                Add label
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

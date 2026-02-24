# Tile Sets

This directory is mounted into the `mbtiles-server` container at `/tilesets`.

Place `.mbtiles` files here to serve them locally (air-gap / offline mode).

## Getting the OSM base map

Download a pre-built MBTiles file from one of these sources:

| Source | Description | URL |
|--------|-------------|-----|
| OpenMapTiles | Planet or regional extracts | https://data.maptiler.com/downloads/planet/ |
| BBBike.org | Custom region export | https://extract.bbbike.org/ |
| Geofabrik | OSM regional extracts (convert via `tippecanoe`) | https://download.geofabrik.de/ |

## Expected file layout

```
tiles/
  osm.mbtiles          ← world or regional OSM base layer
  terrain.mbtiles      ← optional: Mapbox Terrain-RGB elevation tiles
```

## Tile server URL

The `mbtiles-server` service (port **8081**) serves tiles at:

```
http://localhost:8081/services/{tileset_name}/tiles/{z}/{x}/{y}.png
```

The frontend reads `VITE_TILE_SERVER` (default: `http://localhost:8081`) and when
`VITE_AIRGAP=true` constructs the tile URL:

```
{VITE_TILE_SERVER}/osm/{z}/{x}/{y}.png
```

For standard (non-air-gap) development the map falls back to the public OSM CDN.

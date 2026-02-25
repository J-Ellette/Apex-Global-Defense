from __future__ import annotations

from typing import Any

# ISO3 country code → [longitude, latitude] centroids
COUNTRY_CENTROIDS: dict[str, list[float]] = {
    "USA": [-98.5795, 39.8283],
    "RUS": [105.3188, 61.5240],
    "CHN": [104.1954, 35.8617],
    "GBR": [-3.4360, 55.3781],
    "FRA": [2.2137, 46.2276],
    "DEU": [10.4515, 51.1657],
    "IRN": [53.6880, 32.4279],
    "PRK": [127.5101, 40.3399],
    "SYR": [38.9968, 34.8021],
    "IRQ": [43.6793, 33.2232],
    "AFG": [67.7100, 33.9391],
    "UKR": [31.1656, 48.3794],
    "BLR": [27.9534, 53.7098],
    "PAK": [69.3451, 30.3753],
    "IND": [78.9629, 20.5937],
    "SAU": [45.0792, 23.8859],
    "ISR": [34.8516, 31.0461],
    "TUR": [35.2433, 38.9637],
    "BRA": [-51.9253, -14.2350],
    "NGA": [8.6753, 9.0820],
    "ETH": [40.4897, 9.1450],
    "ZAF": [25.0830, -29.0000],
    "MEX": [-102.5528, 23.6345],
    "VNM": [108.2772, 14.0583],
    "IDN": [113.9213, -0.7893],
}


def _make_feature(geometry: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": geometry, "properties": properties}


def _point(lon: float, lat: float) -> dict[str, Any]:
    return {"type": "Point", "coordinates": [lon, lat]}


def _centroid_for(country: str) -> list[float]:
    return COUNTRY_CENTROIDS.get(str(country).upper(), [0.0, 0.0])


def format_units_geojson(rows: list[dict]) -> dict:
    features = []
    for r in rows:
        lon, lat = _centroid_for(r.get("country_code", ""))
        props = {
            "name": r.get("name", "Unknown Unit"),
            "country": r.get("country_code"),
            "unit_type": r.get("unit_type"),
            "strength": r.get("strength"),
            "status": r.get("status"),
            "classification": r.get("classification", "UNCLASS"),
        }
        features.append(_make_feature(_point(lon, lat), props))
    return {"type": "FeatureCollection", "features": features}


def format_civilian_zones_geojson(rows: list[dict]) -> dict:
    features = []
    for r in rows:
        lon = float(r.get("longitude") or r.get("lon") or 0.0)
        lat = float(r.get("latitude") or r.get("lat") or 0.0)
        props = {
            "name": r.get("name", "Unknown Zone"),
            "zone_type": r.get("zone_type"),
            "population": r.get("population"),
            "country_code": r.get("country_code"),
            "classification": r.get("classification", "UNCLASS"),
        }
        features.append(_make_feature(_point(lon, lat), props))
    return {"type": "FeatureCollection", "features": features}


def format_intel_items_geojson(rows: list[dict]) -> dict:
    features = []
    for r in rows:
        lat = r.get("latitude") or r.get("lat")
        lon = r.get("longitude") or r.get("lon")
        coords = [float(lon), float(lat)] if (lat is not None and lon is not None) else [0.0, 0.0]
        props = {
            "name": r.get("title") or r.get("name", "Unknown Intel"),
            "source": r.get("source"),
            "intel_type": r.get("intel_type"),
            "confidence": r.get("confidence"),
            "classification": r.get("classification", "UNCLASS"),
        }
        features.append(_make_feature({"type": "Point", "coordinates": coords}, props))
    return {"type": "FeatureCollection", "features": features}


def format_cbrn_releases_geojson(rows: list[dict]) -> dict:
    features = []
    for r in rows:
        lat = float(r.get("latitude") or r.get("lat") or 0.0)
        lon = float(r.get("longitude") or r.get("lon") or 0.0)
        props = {
            "name": r.get("name") or r.get("agent_type", "CBRN Release"),
            "agent_type": r.get("agent_type"),
            "release_date": str(r.get("release_date", "")),
            "severity": r.get("severity"),
            "classification": r.get("classification", "UNCLASS"),
        }
        features.append(_make_feature(_point(lon, lat), props))
    return {"type": "FeatureCollection", "features": features}


def format_terror_sites_geojson(rows: list[dict]) -> dict:
    features = []
    for r in rows:
        lat = float(r.get("latitude") or r.get("lat") or 0.0)
        lon = float(r.get("longitude") or r.get("lon") or 0.0)
        props = {
            "name": r.get("name", "Terror Site"),
            "site_type": r.get("site_type"),
            "country_code": r.get("country_code"),
            "threat_level": r.get("threat_level"),
            "classification": r.get("classification", "UNCLASS"),
        }
        features.append(_make_feature(_point(lon, lat), props))
    return {"type": "FeatureCollection", "features": features}


def format_generic_geojson(
    rows: list[dict],
    lat_field: str = "latitude",
    lon_field: str = "longitude",
) -> dict:
    features = []
    for r in rows:
        lat = float(r.get(lat_field) or 0.0)
        lon = float(r.get(lon_field) or 0.0)
        props = {k: v for k, v in r.items() if k not in (lat_field, lon_field)}
        features.append(_make_feature(_point(lon, lat), props))
    return {"type": "FeatureCollection", "features": features}

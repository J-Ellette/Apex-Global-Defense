from __future__ import annotations

from typing import Any


def _xml_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _props_to_description(props: dict[str, Any]) -> str:
    lines = []
    for k, v in props.items():
        if v is not None:
            lines.append(f"  <tr><td>{_xml_escape(k)}</td><td>{_xml_escape(str(v))}</td></tr>")
    if not lines:
        return ""
    return "<![CDATA[<table>" + "".join(lines) + "</table>]]>"


def _feature_to_placemark(feature: dict[str, Any]) -> str:
    props = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    name = _xml_escape(str(props.get("name", "Unnamed")))
    description = _props_to_description(props)

    geo_xml = ""
    if geometry.get("type") == "Point":
        coords = geometry.get("coordinates", [0, 0])
        lon = coords[0] if len(coords) > 0 else 0
        lat = coords[1] if len(coords) > 1 else 0
        alt = coords[2] if len(coords) > 2 else 0
        geo_xml = f"    <Point><coordinates>{lon},{lat},{alt}</coordinates></Point>"

    return (
        f"  <Placemark>\n"
        f"    <name>{name}</name>\n"
        f"    <description>{description}</description>\n"
        f"{geo_xml}\n"
        f"  </Placemark>"
    )


def format_geojson_to_kml(geojson: dict, document_name: str = "AGD Export") -> str:
    features = geojson.get("features", [])
    placemarks = "\n".join(_feature_to_placemark(f) for f in features)
    doc_name_escaped = _xml_escape(document_name)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        f"<Document>\n"
        f"  <name>{doc_name_escaped}</name>\n"
        f"  <description>Exported from AGD GIS Export Service</description>\n"
        f"{placemarks}\n"
        f"</Document>\n"
        f"</kml>"
    )

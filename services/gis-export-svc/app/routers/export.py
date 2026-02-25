from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
)
from app.formatters.geojson import (
    format_cbrn_releases_geojson,
    format_civilian_zones_geojson,
    format_intel_items_geojson,
    format_terror_sites_geojson,
    format_units_geojson,
    format_generic_geojson,
)
from app.formatters.kml import format_geojson_to_kml
from app.models import ExportFormat, ExportRequest, LayerType

router = APIRouter(tags=["export"])

# ---------------------------------------------------------------------------
# Layer → (table, formatter) mapping
# ---------------------------------------------------------------------------

_LAYER_META: dict[LayerType, dict] = {
    LayerType.UNITS: {
        "table": "units",
        "description": "Order of battle units with country centroids as geometry",
        "formatter": format_units_geojson,
    },
    LayerType.INTEL_ITEMS: {
        "table": "intel_items",
        "description": "Intelligence items with lat/lon coordinates",
        "formatter": format_intel_items_geojson,
    },
    LayerType.CBRN_RELEASES: {
        "table": "cbrn_releases",
        "description": "CBRN release events with geographic coordinates",
        "formatter": format_cbrn_releases_geojson,
    },
    LayerType.CIVILIAN_ZONES: {
        "table": "civilian_zones",
        "description": "Civilian population zones",
        "formatter": format_civilian_zones_geojson,
    },
    LayerType.SANCTION_TARGETS: {
        "table": "sanction_targets",
        "description": "Economic sanction targets by country",
        "formatter": lambda rows: format_generic_geojson(rows),
    },
    LayerType.TRADE_ROUTES: {
        "table": "trade_routes",
        "description": "Trade routes and disrupted corridors",
        "formatter": lambda rows: format_generic_geojson(rows),
    },
    LayerType.NARRATIVE_THREATS: {
        "table": "narrative_threats",
        "description": "Information operations narrative threats",
        "formatter": lambda rows: format_generic_geojson(rows),
    },
    LayerType.TERROR_SITES: {
        "table": "terror_sites",
        "description": "Known terror organization sites and facilities",
        "formatter": format_terror_sites_geojson,
    },
    LayerType.ASYM_CELLS: {
        "table": "asym_cells",
        "description": "Asymmetric warfare cells and networks",
        "formatter": lambda rows: format_generic_geojson(rows),
    },
}


@router.get("/export/formats")
async def list_formats(user: dict = Depends(get_current_user)):
    return {
        "formats": [
            {"value": ExportFormat.GEOJSON, "label": "GeoJSON", "mime": "application/geo+json"},
            {"value": ExportFormat.KML, "label": "KML (Google Earth)", "mime": "application/vnd.google-earth.kml+xml"},
            {"value": ExportFormat.SHAPEFILE_ZIP, "label": "Shapefile (ZIP)", "mime": "application/zip"},
            {"value": ExportFormat.CSV, "label": "CSV", "mime": "text/csv"},
            {"value": ExportFormat.GPX, "label": "GPX", "mime": "application/gpx+xml"},
        ]
    }


@router.get("/export/layers")
async def list_layers(user: dict = Depends(get_current_user)):
    return {
        "layers": [
            {"value": lt.value, "description": meta["description"]}
            for lt, meta in _LAYER_META.items()
        ]
    }


@router.post("/export/generate")
async def generate_export(
    req: ExportRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    # Enforce classification ceiling
    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)
    if req.classification.value not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient clearance for {req.classification.value} data",
        )

    if req.format not in (ExportFormat.GEOJSON, ExportFormat.KML):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Synchronous export only supports GEOJSON and KML; {req.format.value} requires async job.",
        )

    meta = _LAYER_META.get(req.layer_type)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown layer type")

    db = request.app.state.db
    table = meta["table"]

    try:
        if req.scenario_id:
            db_rows = await db.fetch(
                f"SELECT * FROM {table} WHERE classification = ANY($1::text[]) AND scenario_id = $2",  # noqa: S608
                allowed,
                str(req.scenario_id),
            )
        else:
            db_rows = await db.fetch(
                f"SELECT * FROM {table} WHERE classification = ANY($1::text[])",  # noqa: S608
                allowed,
            )
    except Exception:
        # Table may not exist for this layer — return empty collection
        db_rows = []

    rows = [dict(r) for r in db_rows]
    formatter = meta["formatter"]
    geojson = formatter(rows)

    if req.format == ExportFormat.KML:
        kml_str = format_geojson_to_kml(geojson, document_name=f"AGD {req.layer_type.value}")
        return Response(
            content=kml_str,
            media_type="application/vnd.google-earth.kml+xml",
            headers={"Content-Disposition": f'attachment; filename="{req.layer_type.value.lower()}.kml"'},
        )

    return JSONResponse(
        content=geojson,
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="{req.layer_type.value.lower()}.geojson"'},
    )

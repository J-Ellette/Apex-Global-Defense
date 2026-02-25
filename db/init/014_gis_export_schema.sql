-- GIS Export Service schema
-- Integration configuration for ArcGIS, Google Earth, WMS/WFS, and generic REST endpoints

CREATE TABLE IF NOT EXISTS gis_integration_configs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL,
    integration_type text NOT NULL,
    config          jsonb NOT NULL DEFAULT '{}',
    is_active       boolean NOT NULL DEFAULT true,
    classification  text NOT NULL DEFAULT 'UNCLASS',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gis_integration_configs_type
    ON gis_integration_configs (integration_type);
CREATE INDEX IF NOT EXISTS idx_gis_integration_configs_active
    ON gis_integration_configs (is_active);

-- Seed: ArcGIS Online example integration
INSERT INTO gis_integration_configs (name, integration_type, config, is_active, classification)
VALUES (
    'ArcGIS Online – AGD Layers',
    'ARCGIS',
    '{
        "service_url": "https://services.arcgis.com/example/arcgis/rest/services/AGD_Layers/FeatureServer",
        "layer_name": "AGD_Operational_Layers",
        "username": "agd_publisher",
        "api_key": "REPLACE_WITH_REAL_KEY",
        "agol_item_id": "abc123def456ghi789"
    }'::jsonb,
    true,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

-- Seed: Google Earth Network Link example
INSERT INTO gis_integration_configs (name, integration_type, config, is_active, classification)
VALUES (
    'Google Earth – Live Feed',
    'GOOGLE_EARTH',
    '{
        "kml_network_link_url": "http://gis-export-svc:8000/api/v1/export/generate?layer_type=UNITS&format=KML",
        "refresh_interval_seconds": 300,
        "balloon_style": ""
    }'::jsonb,
    true,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

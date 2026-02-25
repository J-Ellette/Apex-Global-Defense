-- STIX/TAXII Indicator Schema
-- Stores STIX 2.1 threat intelligence indicators ingested via TAXII 2.1 feeds.

CREATE TABLE IF NOT EXISTS stix_indicators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stix_id         TEXT NOT NULL UNIQUE,          -- STIX 2.1 object ID (e.g. indicator--<uuid>)
    stix_type       TEXT NOT NULL DEFAULT 'indicator',
    spec_version    TEXT NOT NULL DEFAULT '2.1',
    name            TEXT NOT NULL,
    description     TEXT,
    pattern         TEXT NOT NULL,                 -- STIX pattern expression
    pattern_type    TEXT NOT NULL DEFAULT 'stix',  -- stix / pcre / yara / sigma
    indicator_types TEXT[] DEFAULT '{}',           -- malicious-activity, anomalous-activity, etc.
    kill_chain_phases JSONB DEFAULT '[]',           -- [{kill_chain_name, phase_name}]
    confidence      INTEGER DEFAULT 50,            -- 0-100
    labels          TEXT[] DEFAULT '{}',
    valid_from      TIMESTAMPTZ NOT NULL,
    valid_until     TIMESTAMPTZ,
    created         TIMESTAMPTZ NOT NULL,
    modified        TIMESTAMPTZ NOT NULL,
    created_by_ref  TEXT,
    object_marking_refs TEXT[] DEFAULT '{}',
    external_references JSONB DEFAULT '[]',
    taxii_collection TEXT,                         -- source TAXII collection ID
    taxii_server     TEXT,                         -- source TAXII server URL
    classification   classification_level NOT NULL DEFAULT 'UNCLASS',
    scenario_id      UUID,                         -- optional scenario association
    ingested_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stix_indicators_stix_type    ON stix_indicators (stix_type);
CREATE INDEX IF NOT EXISTS idx_stix_indicators_taxii_server ON stix_indicators (taxii_server);
CREATE INDEX IF NOT EXISTS idx_stix_indicators_valid_from   ON stix_indicators (valid_from);
CREATE INDEX IF NOT EXISTS idx_stix_indicators_scenario_id  ON stix_indicators (scenario_id);
CREATE INDEX IF NOT EXISTS idx_stix_indicators_ingested_at  ON stix_indicators (ingested_at DESC);

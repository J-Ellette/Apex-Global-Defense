-- ============================================================
-- 005_asym_schema.sql
-- Asymmetric / Insurgency module schema
-- AGD — Phase 3 Domain Expansion
-- ============================================================

-- Insurgent cell nodes
CREATE TABLE IF NOT EXISTS asym_cells (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id             UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    name                    TEXT NOT NULL,
    function                TEXT NOT NULL,          -- CellFunction enum value
    structure               TEXT NOT NULL DEFAULT 'NETWORK',
    status                  TEXT NOT NULL DEFAULT 'UNKNOWN',
    size_estimated          INTEGER NOT NULL DEFAULT 5 CHECK (size_estimated >= 1),
    latitude                DOUBLE PRECISION,
    longitude               DOUBLE PRECISION,
    region                  TEXT,
    country_code            CHAR(2),
    leadership_confidence   DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (leadership_confidence BETWEEN 0 AND 1),
    operational_capability  DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (operational_capability BETWEEN 0 AND 1),
    funding_level           TEXT NOT NULL DEFAULT 'UNKNOWN',
    affiliated_groups       JSONB NOT NULL DEFAULT '[]',
    notes                   TEXT,
    created_by              TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asym_cells_scenario    ON asym_cells(scenario_id);
CREATE INDEX IF NOT EXISTS idx_asym_cells_status      ON asym_cells(status);
CREATE INDEX IF NOT EXISTS idx_asym_cells_function    ON asym_cells(function);

-- Cell network edges (links between cells)
CREATE TABLE IF NOT EXISTS asym_cell_links (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id     UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    source_cell_id  UUID NOT NULL REFERENCES asym_cells(id) ON DELETE CASCADE,
    target_cell_id  UUID NOT NULL REFERENCES asym_cells(id) ON DELETE CASCADE,
    link_type       TEXT NOT NULL DEFAULT 'UNKNOWN',
    strength        TEXT NOT NULL DEFAULT 'MODERATE',
    confidence      DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
    notes           TEXT,
    created_by      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT no_self_link CHECK (source_cell_id <> target_cell_id)
);

CREATE INDEX IF NOT EXISTS idx_asym_links_scenario ON asym_cell_links(scenario_id);
CREATE INDEX IF NOT EXISTS idx_asym_links_source   ON asym_cell_links(source_cell_id);
CREATE INDEX IF NOT EXISTS idx_asym_links_target   ON asym_cell_links(target_cell_id);

-- IED incidents
CREATE TABLE IF NOT EXISTS asym_ied_incidents (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id             UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    ied_type_id             TEXT NOT NULL,          -- IEDTypeEntry.id
    latitude                DOUBLE PRECISION NOT NULL,
    longitude               DOUBLE PRECISION NOT NULL,
    location_description    TEXT,
    status                  TEXT NOT NULL DEFAULT 'SUSPECTED',
    detonation_type         TEXT NOT NULL DEFAULT 'UNKNOWN',
    target_type             TEXT NOT NULL DEFAULT 'UNKNOWN',
    placement_date          TIMESTAMPTZ,
    detection_date          TIMESTAMPTZ,
    detonation_date         TIMESTAMPTZ,
    estimated_yield_kg      DOUBLE PRECISION,
    casualties_killed       INTEGER NOT NULL DEFAULT 0 CHECK (casualties_killed >= 0),
    casualties_wounded      INTEGER NOT NULL DEFAULT 0 CHECK (casualties_wounded >= 0),
    attributed_cell_id      UUID REFERENCES asym_cells(id) ON DELETE SET NULL,
    notes                   TEXT,
    created_by              TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asym_incidents_scenario  ON asym_ied_incidents(scenario_id);
CREATE INDEX IF NOT EXISTS idx_asym_incidents_status    ON asym_ied_incidents(status);
CREATE INDEX IF NOT EXISTS idx_asym_incidents_cell      ON asym_ied_incidents(attributed_cell_id);

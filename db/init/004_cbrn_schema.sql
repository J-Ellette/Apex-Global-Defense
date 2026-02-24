-- ============================================================
-- AGD CBRN Schema (004)
-- Chemical, Biological, Radiological, Nuclear module
-- ============================================================

-- CBRN Release Events
CREATE TABLE IF NOT EXISTS cbrn_releases (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id                 UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    agent_id                    VARCHAR(64) NOT NULL,
    release_type                VARCHAR(16) NOT NULL DEFAULT 'POINT',
    latitude                    DOUBLE PRECISION NOT NULL,
    longitude                   DOUBLE PRECISION NOT NULL,
    quantity_kg                 DOUBLE PRECISION NOT NULL,
    release_height_m            DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    duration_min                DOUBLE PRECISION NOT NULL DEFAULT 10.0,
    met                         JSONB NOT NULL DEFAULT '{}',
    population_density_per_km2  DOUBLE PRECISION NOT NULL DEFAULT 500.0,
    label                       VARCHAR(255) NOT NULL DEFAULT '',
    notes                       TEXT,
    created_by                  VARCHAR(255),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cbrn_releases_scenario ON cbrn_releases(scenario_id);
CREATE INDEX IF NOT EXISTS idx_cbrn_releases_agent    ON cbrn_releases(agent_id);
CREATE INDEX IF NOT EXISTS idx_cbrn_releases_created  ON cbrn_releases(created_at DESC);

-- CBRN Dispersion Simulation Results
CREATE TABLE IF NOT EXISTS cbrn_simulations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    release_id   UUID NOT NULL UNIQUE REFERENCES cbrn_releases(id) ON DELETE CASCADE,
    result       JSONB NOT NULL,
    simulated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cbrn_simulations_release ON cbrn_simulations(release_id);

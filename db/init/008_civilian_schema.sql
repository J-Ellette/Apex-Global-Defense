-- AGD Civilian Impact Schema
-- Population zones, conflict impact assessments, refugee flows,
-- and humanitarian corridors.

-- ── Population zones ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS civilian_population_zones (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id     UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    country_code    VARCHAR(3) NOT NULL,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    radius_km       DOUBLE PRECISION NOT NULL CHECK (radius_km > 0),
    population      INTEGER NOT NULL CHECK (population > 0),
    density_class   TEXT NOT NULL CHECK (density_class IN ('URBAN','SUBURBAN','RURAL','SPARSE')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cpz_scenario ON civilian_population_zones (scenario_id);
CREATE INDEX IF NOT EXISTS idx_cpz_country  ON civilian_population_zones (country_code);

-- ── Impact assessments ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS civilian_impact_assessments (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id                      UUID NOT NULL,
    scenario_id                 UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    assessed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_civilian_casualties   INTEGER NOT NULL DEFAULT 0,
    total_civilian_wounded      INTEGER NOT NULL DEFAULT 0,
    total_displaced_persons     INTEGER NOT NULL DEFAULT 0,
    zone_impacts                JSONB NOT NULL DEFAULT '[]',
    methodology                 TEXT NOT NULL DEFAULT 'deterministic',
    notes                       TEXT
);

CREATE INDEX IF NOT EXISTS idx_cia_run_id ON civilian_impact_assessments (run_id);

-- ── Refugee flows ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS civilian_refugee_flows (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id         UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    origin_zone_id      UUID REFERENCES civilian_population_zones(id) ON DELETE SET NULL,
    origin_name         TEXT NOT NULL,
    destination_name    TEXT NOT NULL,
    origin_lat          DOUBLE PRECISION NOT NULL,
    origin_lon          DOUBLE PRECISION NOT NULL,
    destination_lat     DOUBLE PRECISION NOT NULL,
    destination_lon     DOUBLE PRECISION NOT NULL,
    displaced_persons   INTEGER NOT NULL CHECK (displaced_persons > 0),
    status              TEXT NOT NULL DEFAULT 'PROJECTED'
                            CHECK (status IN ('PROJECTED','CONFIRMED','RESOLVED')),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crf_scenario ON civilian_refugee_flows (scenario_id);
CREATE INDEX IF NOT EXISTS idx_crf_status   ON civilian_refugee_flows (status);

-- ── Humanitarian corridors ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS civilian_humanitarian_corridors (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    waypoints   JSONB NOT NULL DEFAULT '[]',
    status      TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK (status IN ('OPEN','RESTRICTED','CLOSED')),
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chc_scenario ON civilian_humanitarian_corridors (scenario_id);
CREATE INDEX IF NOT EXISTS idx_chc_status   ON civilian_humanitarian_corridors (status);

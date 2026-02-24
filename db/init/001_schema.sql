-- =============================================================================
-- Apex Global Defense (AGD) — PostgreSQL / PostGIS Initialization Schema
-- Version 1.0
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector for semantic search

-- =============================================================================
-- Enums
-- =============================================================================

CREATE TYPE classification_level AS ENUM (
    'UNCLASS', 'FOUO', 'SECRET', 'TOP_SECRET', 'TS_SCI'
);

CREATE TYPE branch AS ENUM (
    'ARMY', 'NAVY', 'AIR', 'SPACE', 'CYBER', 'INTEL', 'SPECIAL_OPS', 'COAST_GUARD'
);

CREATE TYPE echelon AS ENUM (
    'FIRETEAM', 'SQUAD', 'SECTION', 'PLATOON', 'COMPANY', 'BATTALION',
    'REGIMENT', 'BRIGADE', 'DIVISION', 'CORPS', 'FIELD_ARMY', 'ARMY_GROUP',
    'CARRIER_STRIKE_GROUP', 'FLEET', 'WING', 'GROUP', 'SQUADRON'
);

CREATE TYPE source_type AS ENUM (
    'OSINT', 'SIGINT', 'HUMINT', 'IMINT', 'MASINT', 'GEOINT', 'TECHINT', 'FININT'
);

-- =============================================================================
-- Users & Auth (managed by Keycloak; mirror table for local enrichment)
-- =============================================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    description     TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keycloak_id     TEXT UNIQUE,            -- Keycloak sub claim
    email           TEXT NOT NULL UNIQUE,
    display_name    TEXT NOT NULL,
    roles           JSONB NOT NULL DEFAULT '[]',   -- []Role
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    org_id          UUID NOT NULL REFERENCES organizations(id),
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);
CREATE INDEX idx_users_email     ON users(email);
CREATE INDEX idx_users_org       ON users(org_id);
CREATE INDEX idx_users_keycloak  ON users(keycloak_id);

-- =============================================================================
-- Countries & Military Units (Order of Battle)
-- =============================================================================

CREATE TABLE countries (
    code                CHAR(3) PRIMARY KEY,   -- ISO 3166-1 alpha-3
    name                TEXT NOT NULL,
    region              TEXT,
    alliance_codes      TEXT[],                -- e.g. {'NATO', 'QUAD', 'SCO'}
    gdp_usd             BIGINT,
    defense_budget_usd  BIGINT,
    population          BIGINT,
    area_km2            BIGINT,
    iso2                CHAR(2),
    flag_emoji          TEXT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Military units — hierarchical via parent_id (self-referential)
CREATE TABLE military_units (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code    CHAR(3) NOT NULL REFERENCES countries(code),
    branch          branch NOT NULL,
    echelon         echelon,
    name            TEXT NOT NULL,
    short_name      TEXT,
    nato_symbol     TEXT,                           -- APP-6D symbol code
    parent_id       UUID REFERENCES military_units(id) ON DELETE SET NULL,
    location        GEOGRAPHY(POINT, 4326),
    aor             GEOGRAPHY(POLYGON, 4326),        -- Area of Responsibility
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    confidence      NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    data_sources    TEXT[],
    as_of           TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_units_country   ON military_units(country_code);
CREATE INDEX idx_units_parent    ON military_units(parent_id);
CREATE INDEX idx_units_branch    ON military_units(branch);
CREATE INDEX idx_units_location  ON military_units USING GIST(location);
CREATE INDEX idx_units_aor       ON military_units USING GIST(aor);

-- Equipment catalog (reference table)
CREATE TABLE equipment_catalog (
    type_code       TEXT PRIMARY KEY,
    category        TEXT NOT NULL,   -- ARMOR, AIRCRAFT, NAVAL, ARTILLERY, MISSILE, SMALL_ARMS, C2
    name            TEXT NOT NULL,
    origin_country  CHAR(3) REFERENCES countries(code),
    specs           JSONB,           -- range_km, speed_kph, payload_kg, crew, etc.
    threat_score    NUMERIC(3,2) CHECK (threat_score BETWEEN 0 AND 1),
    in_service_year INTEGER,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Equipment inventory per unit
CREATE TABLE equipment (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_id         UUID NOT NULL REFERENCES military_units(id) ON DELETE CASCADE,
    type_code       TEXT NOT NULL REFERENCES equipment_catalog(type_code),
    quantity        INTEGER NOT NULL CHECK (quantity >= 0),
    operational_pct NUMERIC(3,2) CHECK (operational_pct BETWEEN 0 AND 1),
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    as_of           TIMESTAMPTZ NOT NULL,
    notes           TEXT
);
CREATE INDEX idx_equipment_unit ON equipment(unit_id);
CREATE INDEX idx_equipment_type ON equipment(type_code);

-- Personnel counts embedded as JSONB to keep schema flexible
-- Schema: {total, active_duty, reserve, paramilitary}
-- Stored as a separate table for queryability
CREATE TABLE personnel_counts (
    unit_id         UUID PRIMARY KEY REFERENCES military_units(id) ON DELETE CASCADE,
    total           INTEGER,
    active_duty     INTEGER,
    reserve         INTEGER,
    paramilitary    INTEGER,
    as_of           TIMESTAMPTZ NOT NULL
);

-- =============================================================================
-- Scenarios
-- =============================================================================

CREATE TABLE scenarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    description     TEXT,
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    theater_bounds  GEOGRAPHY(POLYGON, 4326),
    created_by      UUID NOT NULL REFERENCES users(id),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    parent_id       UUID REFERENCES scenarios(id),   -- branching / version tree
    tags            TEXT[],
    metadata        JSONB DEFAULT '{}',
    archived        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_scenarios_org       ON scenarios(org_id);
CREATE INDEX idx_scenarios_created   ON scenarios(created_by);
CREATE INDEX idx_scenarios_parent    ON scenarios(parent_id);
CREATE INDEX idx_scenarios_tags      ON scenarios USING GIN(tags);

-- =============================================================================
-- Simulation Runs & Events
-- =============================================================================

CREATE TABLE simulation_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id     UUID NOT NULL REFERENCES scenarios(id),
    mode            TEXT NOT NULL,   -- real_time, turn_based, monte_carlo
    status          TEXT NOT NULL DEFAULT 'queued',
    progress        NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 1),
    config          JSONB NOT NULL DEFAULT '{}',
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT
);
CREATE INDEX idx_sim_runs_scenario ON simulation_runs(scenario_id);

-- TimescaleDB hypertable for simulation events (time-series data)
CREATE TABLE sim_events (
    time            TIMESTAMPTZ NOT NULL,
    run_id          UUID NOT NULL REFERENCES simulation_runs(id),
    event_type      TEXT NOT NULL,
    entity_id       UUID,
    location        GEOGRAPHY(POINT, 4326),
    payload         JSONB,
    turn_number     INTEGER
);
SELECT create_hypertable('sim_events', 'time');
CREATE INDEX idx_sim_events_run ON sim_events(run_id, time DESC);

-- =============================================================================
-- Intelligence Items
-- =============================================================================

CREATE TABLE intel_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type     source_type,
    source_url      TEXT,
    title           TEXT NOT NULL,
    content         TEXT,
    language        CHAR(3),
    location        GEOGRAPHY(POINT, 4326),
    bounding_box    GEOGRAPHY(POLYGON, 4326),
    entities        JSONB DEFAULT '[]',   -- extracted NLP entities
    tags            TEXT[],
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    reliability     CHAR(1) CHECK (reliability IN ('A','B','C','D','E','F')),  -- NATO admiralty
    credibility     CHAR(1) CHECK (credibility IN ('1','2','3','4','5','6')),  -- NATO admiralty
    published_at    TIMESTAMPTZ,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingested_by     UUID REFERENCES users(id),
    embedding       VECTOR(1536)   -- pgvector for semantic search
);
CREATE INDEX idx_intel_location  ON intel_items USING GIST(location);
CREATE INDEX idx_intel_source    ON intel_items(source_type);
CREATE INDEX idx_intel_tags      ON intel_items USING GIN(tags);
CREATE INDEX idx_intel_published ON intel_items(published_at DESC);
CREATE INDEX idx_intel_embedding ON intel_items USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

-- =============================================================================
-- Map Annotations
-- =============================================================================

CREATE TABLE annotations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id     UUID NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    created_by      UUID NOT NULL REFERENCES users(id),
    annotation_type TEXT NOT NULL,   -- POINT, LINE, POLYGON, ARROW, TEXT, SYMBOL
    geometry        GEOGRAPHY NOT NULL,
    properties      JSONB DEFAULT '{}',
    label           TEXT,
    color           TEXT DEFAULT '#FF0000',
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_annotations_scenario  ON annotations(scenario_id);
CREATE INDEX idx_annotations_geom      ON annotations USING GIST(geometry);

-- =============================================================================
-- AI / Prompt Templates
-- =============================================================================

CREATE TABLE prompt_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key             TEXT NOT NULL UNIQUE,
    version         TEXT NOT NULL,
    system_prompt   TEXT NOT NULL,
    user_template   TEXT NOT NULL,
    description     TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Audit Log (append-only, partitioned by month)
-- =============================================================================

CREATE TABLE audit_log (
    id              BIGSERIAL,
    time            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id         UUID NOT NULL REFERENCES users(id),
    session_id      UUID,
    action          TEXT NOT NULL,
    resource_type   TEXT,
    resource_id     UUID,
    classification  classification_level,
    ip_address      INET,
    user_agent      TEXT,
    payload         JSONB,
    PRIMARY KEY (id, time)
) PARTITION BY RANGE (time);

-- Create initial monthly partitions (current and next 2 months)
CREATE TABLE audit_log_y2026m02 PARTITION OF audit_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE audit_log_y2026m03 PARTITION OF audit_log
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE audit_log_y2026m04 PARTITION OF audit_log
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE INDEX idx_audit_user   ON audit_log(user_id, time DESC);
CREATE INDEX idx_audit_action ON audit_log(action, time DESC);

-- =============================================================================
-- Row-Level Security (classification enforcement)
-- =============================================================================

ALTER TABLE intel_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY intel_classification_policy ON intel_items
    FOR SELECT
    USING (
        classification::text = ANY(
            CASE current_setting('agd.user_classification', TRUE)
                WHEN 'UNCLASS'    THEN ARRAY['UNCLASS']
                WHEN 'FOUO'       THEN ARRAY['UNCLASS','FOUO']
                WHEN 'SECRET'     THEN ARRAY['UNCLASS','FOUO','SECRET']
                WHEN 'TOP_SECRET' THEN ARRAY['UNCLASS','FOUO','SECRET','TOP_SECRET']
                WHEN 'TS_SCI'     THEN ARRAY['UNCLASS','FOUO','SECRET','TOP_SECRET','TS_SCI']
                ELSE ARRAY['UNCLASS']
            END
        )
    );

ALTER TABLE military_units ENABLE ROW LEVEL SECURITY;
CREATE POLICY units_classification_policy ON military_units
    FOR SELECT
    USING (
        classification::text = ANY(
            CASE current_setting('agd.user_classification', TRUE)
                WHEN 'UNCLASS'    THEN ARRAY['UNCLASS']
                WHEN 'FOUO'       THEN ARRAY['UNCLASS','FOUO']
                WHEN 'SECRET'     THEN ARRAY['UNCLASS','FOUO','SECRET']
                WHEN 'TOP_SECRET' THEN ARRAY['UNCLASS','FOUO','SECRET','TOP_SECRET']
                WHEN 'TS_SCI'     THEN ARRAY['UNCLASS','FOUO','SECRET','TOP_SECRET','TS_SCI']
                ELSE ARRAY['UNCLASS']
            END
        )
    );

-- =============================================================================
-- Seed: Default organization and prompt templates
-- =============================================================================

INSERT INTO organizations (id, name, slug, description) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Apex Global Defense', 'agd', 'Default organization');

INSERT INTO prompt_templates (key, version, system_prompt, user_template, description) VALUES
(
    'scenario_builder',
    '1.2',
    'You are a military scenario planning assistant for professional defense analysts. Generate structured conflict scenarios based on provided parameters. Output ONLY valid JSON matching the ScenarioConfig schema. Do not include any narrative text outside JSON.',
    'Generate a {mode} scenario with the following parameters:
Theater: {theater_description}
Blue Forces: {blue_force_summary}
Red Forces: {red_force_summary}
Trigger event: {trigger}
Duration: {duration_hours} hours
Objectives: {objectives}

Return a JSON ScenarioConfig object.',
    'AI-assisted scenario generation from natural language parameters'
),
(
    'threat_assess',
    '1.0',
    'You are a senior defense intelligence analyst. Assess threat levels using established frameworks (PMESII-PT, ASCOPE). Be precise. Cite data. Express uncertainty clearly.',
    'Assess the threat posed by {actor} to {target} given the following Order of Battle data:
{oob_json}

Current intel items (last 30 days):
{intel_summary}

Provide: threat level (1-5), primary vectors, confidence level, and key uncertainties.',
    'AI-assisted threat assessment using OOB and intel data'
),
(
    'intel_summary',
    '1.0',
    'You are an intelligence analyst. Summarize the following intelligence items concisely and accurately. Preserve uncertainty qualifiers. Do not fabricate details not present in the source material.',
    'Summarize the following {count} intelligence items collected between {date_from} and {date_to} regarding {subject}:

{items_json}

Provide: key findings, trend analysis, confidence level, and recommended follow-up.',
    'AI-assisted summarization of multiple intel items'
),
(
    'report_draft',
    '1.0',
    'You are a military staff officer drafting an intelligence report. Use standard BLUF (Bottom Line Up Front) format. Be concise and factual.',
    'Draft a {report_type} report for the period {period_start} to {period_end} covering {subject}.

Key data points:
{data_json}

Required sections: BLUF, Situation, Analysis, Recommendations.',
    'AI-assisted report drafting in standard military format'
);

-- =============================================================================
-- 006_terror_schema.sql — Terror Response Planning
-- Tables: terror_sites, terror_threat_scenarios, terror_response_plans
-- =============================================================================

CREATE TABLE IF NOT EXISTS terror_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    site_type VARCHAR(50) NOT NULL,
    address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    country_code CHAR(2),
    population_capacity INTEGER DEFAULT 0,
    -- Vulnerability dimensions (0.0–1.0; 1.0 = excellent security)
    physical_security DOUBLE PRECISION DEFAULT 0.5
        CHECK (physical_security >= 0 AND physical_security <= 1),
    access_control DOUBLE PRECISION DEFAULT 0.5
        CHECK (access_control >= 0 AND access_control <= 1),
    surveillance DOUBLE PRECISION DEFAULT 0.5
        CHECK (surveillance >= 0 AND surveillance <= 1),
    emergency_response DOUBLE PRECISION DEFAULT 0.5
        CHECK (emergency_response >= 0 AND emergency_response <= 1),
    crowd_density VARCHAR(20) DEFAULT 'MEDIUM',
    vulnerability_score DOUBLE PRECISION DEFAULT 5.0
        CHECK (vulnerability_score >= 1 AND vulnerability_score <= 10),
    assigned_agencies JSONB DEFAULT '[]',
    notes TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_by VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_terror_sites_scenario
    ON terror_sites(scenario_id);
CREATE INDEX IF NOT EXISTS idx_terror_sites_type
    ON terror_sites(site_type);
CREATE INDEX IF NOT EXISTS idx_terror_sites_vuln
    ON terror_sites(vulnerability_score DESC);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS terror_threat_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    site_id UUID NOT NULL REFERENCES terror_sites(id) ON DELETE CASCADE,
    attack_type_id VARCHAR(20) NOT NULL,
    threat_level VARCHAR(20) DEFAULT 'LOW',
    probability DOUBLE PRECISION DEFAULT 0.1
        CHECK (probability >= 0 AND probability <= 1),
    estimated_killed_low INTEGER DEFAULT 0 CHECK (estimated_killed_low >= 0),
    estimated_killed_high INTEGER DEFAULT 0 CHECK (estimated_killed_high >= 0),
    estimated_wounded_low INTEGER DEFAULT 0 CHECK (estimated_wounded_low >= 0),
    estimated_wounded_high INTEGER DEFAULT 0 CHECK (estimated_wounded_high >= 0),
    notes TEXT,
    created_by VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_terror_threat_scenarios_site
    ON terror_threat_scenarios(site_id);
CREATE INDEX IF NOT EXISTS idx_terror_threat_scenarios_scenario
    ON terror_threat_scenarios(scenario_id);

-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS terror_response_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    site_id UUID NOT NULL REFERENCES terror_sites(id) ON DELETE CASCADE,
    threat_scenario_id UUID REFERENCES terror_threat_scenarios(id) ON DELETE SET NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    agencies JSONB DEFAULT '[]',
    evacuation_routes JSONB DEFAULT '[]',
    shelter_capacity INTEGER DEFAULT 0 CHECK (shelter_capacity >= 0),
    estimated_response_time_min INTEGER DEFAULT 10 CHECK (estimated_response_time_min >= 1),
    status VARCHAR(20) DEFAULT 'DRAFT',
    created_by VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_terror_response_plans_site
    ON terror_response_plans(site_id);
CREATE INDEX IF NOT EXISTS idx_terror_response_plans_scenario
    ON terror_response_plans(scenario_id);

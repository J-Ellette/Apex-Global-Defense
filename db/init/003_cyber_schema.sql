-- =============================================================================
-- Apex Global Defense (AGD) — Cyber Operations Schema
-- Migration 003
-- =============================================================================

-- Infrastructure graph nodes
CREATE TABLE cyber_infra_nodes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id     UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    label           TEXT NOT NULL,
    node_type       TEXT NOT NULL,     -- HOST, SERVER, ROUTER, FIREWALL, ICS, CLOUD, SATELLITE, IOT, DATABASE
    network         TEXT,
    ip_address      TEXT,
    criticality     TEXT NOT NULL DEFAULT 'MEDIUM',  -- LOW, MEDIUM, HIGH, CRITICAL
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    tags            TEXT[] DEFAULT '{}',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cyber_nodes_scenario ON cyber_infra_nodes(scenario_id);
CREATE INDEX idx_cyber_nodes_type     ON cyber_infra_nodes(node_type);

-- Infrastructure graph edges (connections between nodes)
CREATE TABLE cyber_infra_edges (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL REFERENCES cyber_infra_nodes(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES cyber_infra_nodes(id) ON DELETE CASCADE,
    edge_type       TEXT NOT NULL DEFAULT 'NETWORK',  -- NETWORK, DEPENDENCY, CONTROL
    protocol        TEXT,
    port            INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cyber_edges_source ON cyber_infra_edges(source_id);
CREATE INDEX idx_cyber_edges_target ON cyber_infra_edges(target_id);

-- Planned and executed cyber attacks
CREATE TABLE cyber_attacks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id         UUID REFERENCES scenarios(id) ON DELETE SET NULL,
    technique_id        TEXT NOT NULL,         -- MITRE ATT&CK ID (e.g. T1566)
    target_node_id      UUID REFERENCES cyber_infra_nodes(id) ON DELETE SET NULL,
    attacker            TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'PLANNED',  -- PLANNED, EXECUTING, COMPLETE, FAILED, DETECTED
    success_probability NUMERIC(4,3) CHECK (success_probability BETWEEN 0 AND 1),
    impact              TEXT NOT NULL DEFAULT 'MEDIUM',
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    executed_at         TIMESTAMPTZ,
    result              JSONB
);

CREATE INDEX idx_cyber_attacks_scenario   ON cyber_attacks(scenario_id);
CREATE INDEX idx_cyber_attacks_technique  ON cyber_attacks(technique_id);
CREATE INDEX idx_cyber_attacks_status     ON cyber_attacks(status);

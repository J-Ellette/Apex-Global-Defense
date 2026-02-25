-- Economic Warfare Schema
-- Models sanctions, trade disruption, and economic impact for strategic warfare operations.

CREATE TABLE IF NOT EXISTS econ_sanction_targets (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    TEXT NOT NULL,
    country_code            CHAR(3) NOT NULL,
    target_type             TEXT NOT NULL DEFAULT 'COUNTRY',  -- COUNTRY / ENTITY / INDIVIDUAL
    sanction_type           TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'ACTIVE',
    imposing_parties        JSONB NOT NULL DEFAULT '[]',
    effective_date          DATE,
    annual_gdp_impact_pct   NUMERIC(6, 2),
    notes                   TEXT,
    classification          TEXT NOT NULL DEFAULT 'UNCLASS',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_econ_sanctions_country     ON econ_sanction_targets (country_code);
CREATE INDEX IF NOT EXISTS idx_econ_sanctions_status      ON econ_sanction_targets (status);
CREATE INDEX IF NOT EXISTS idx_econ_sanctions_type        ON econ_sanction_targets (sanction_type);
CREATE INDEX IF NOT EXISTS idx_econ_sanctions_created     ON econ_sanction_targets (created_at DESC);

CREATE TABLE IF NOT EXISTS econ_trade_routes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_country      CHAR(3) NOT NULL,
    destination_country CHAR(3) NOT NULL,
    commodity           TEXT NOT NULL,
    annual_value_usd    BIGINT NOT NULL DEFAULT 0,
    dependency_level    TEXT NOT NULL DEFAULT 'MEDIUM',
    is_disrupted        BOOLEAN NOT NULL DEFAULT FALSE,
    disruption_cause    TEXT,
    classification      TEXT NOT NULL DEFAULT 'UNCLASS',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_econ_trade_origin      ON econ_trade_routes (origin_country);
CREATE INDEX IF NOT EXISTS idx_econ_trade_destination ON econ_trade_routes (destination_country);
CREATE INDEX IF NOT EXISTS idx_econ_trade_disrupted   ON econ_trade_routes (is_disrupted);
CREATE INDEX IF NOT EXISTS idx_econ_trade_created     ON econ_trade_routes (created_at DESC);

CREATE TABLE IF NOT EXISTS econ_impact_assessments (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id                 UUID,
    target_country              CHAR(3) NOT NULL,
    gdp_impact_pct              NUMERIC(8, 2) NOT NULL DEFAULT 0,
    inflation_rate_change       NUMERIC(8, 2) NOT NULL DEFAULT 0,
    unemployment_change         NUMERIC(8, 2) NOT NULL DEFAULT 0,
    currency_devaluation_pct    NUMERIC(8, 2) NOT NULL DEFAULT 0,
    trade_volume_reduction_pct  NUMERIC(8, 2) NOT NULL DEFAULT 0,
    affected_sectors            JSONB NOT NULL DEFAULT '[]',
    severity                    TEXT NOT NULL DEFAULT 'NEGLIGIBLE',
    timeline_months             INT NOT NULL DEFAULT 1,
    confidence_score            NUMERIC(4, 2) NOT NULL DEFAULT 0,
    notes                       TEXT,
    classification              TEXT NOT NULL DEFAULT 'UNCLASS',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_econ_impact_country    ON econ_impact_assessments (target_country);
CREATE INDEX IF NOT EXISTS idx_econ_impact_scenario   ON econ_impact_assessments (scenario_id);
CREATE INDEX IF NOT EXISTS idx_econ_impact_severity   ON econ_impact_assessments (severity);
CREATE INDEX IF NOT EXISTS idx_econ_impact_created    ON econ_impact_assessments (created_at DESC);

CREATE TABLE IF NOT EXISTS econ_indicators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code    CHAR(3) NOT NULL,
    indicator_name  TEXT NOT NULL,
    value           NUMERIC(14, 4) NOT NULL,
    unit            TEXT NOT NULL DEFAULT 'percent',
    year            INT NOT NULL,
    source          TEXT,
    classification  TEXT NOT NULL DEFAULT 'UNCLASS',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_econ_indicators_country   ON econ_indicators (country_code);
CREATE INDEX IF NOT EXISTS idx_econ_indicators_name      ON econ_indicators (indicator_name);
CREATE INDEX IF NOT EXISTS idx_econ_indicators_year      ON econ_indicators (year);

-- ---------------------------------------------------------------------------
-- Seed data
-- ---------------------------------------------------------------------------

INSERT INTO econ_sanction_targets (
    id, name, country_code, target_type, sanction_type, status,
    imposing_parties, effective_date, annual_gdp_impact_pct, notes, classification
) VALUES
    (
        gen_random_uuid(), 'Russia — Comprehensive Sanctions', 'RUS', 'COUNTRY',
        'ASSET_FREEZE', 'ACTIVE',
        '["USA","EU","UK","Canada","Australia","Japan"]',
        '2022-02-24', 3.5,
        'Comprehensive sanctions imposed following invasion of Ukraine.',
        'UNCLASS'
    ),
    (
        gen_random_uuid(), 'Iran — Trade Embargo', 'IRN', 'COUNTRY',
        'TRADE_EMBARGO', 'ACTIVE',
        '["USA","EU"]',
        '2012-07-01', 4.2,
        'Broad trade embargo targeting oil exports and financial sector.',
        'UNCLASS'
    ),
    (
        gen_random_uuid(), 'North Korea — Financial Cutoff', 'PRK', 'COUNTRY',
        'FINANCIAL_CUTOFF', 'ACTIVE',
        '["USA","EU","UN"]',
        '2006-10-14', 6.8,
        'Comprehensive financial isolation following nuclear weapons tests.',
        'UNCLASS'
    ),
    (
        gen_random_uuid(), 'Belarus — Sectoral Sanctions', 'BLR', 'COUNTRY',
        'SECTORAL', 'ACTIVE',
        '["EU","USA","UK"]',
        '2021-06-21', 2.1,
        'Sectoral sanctions targeting energy, potash, and financial sectors.',
        'UNCLASS'
    ),
    (
        gen_random_uuid(), 'Venezuela — Arms Embargo', 'VEN', 'COUNTRY',
        'ARMS_EMBARGO', 'ACTIVE',
        '["USA","EU"]',
        '2019-01-28', 1.2,
        'Arms embargo and targeted financial sanctions against Maduro regime.',
        'UNCLASS'
    )
ON CONFLICT DO NOTHING;

INSERT INTO econ_trade_routes (
    id, origin_country, destination_country, commodity,
    annual_value_usd, dependency_level, is_disrupted, disruption_cause, classification
) VALUES
    (
        gen_random_uuid(), 'CHN', 'USA', 'semiconductors',
        500000000000, 'CRITICAL', FALSE, NULL, 'UNCLASS'
    ),
    (
        gen_random_uuid(), 'RUS', 'EUR', 'natural_gas',
        85000000000, 'CRITICAL', TRUE,
        'Russia-Ukraine conflict; Nord Stream pipeline sabotage; EU energy diversification.',
        'UNCLASS'
    ),
    (
        gen_random_uuid(), 'SAU', 'USA', 'crude_oil',
        140000000000, 'HIGH', FALSE, NULL, 'UNCLASS'
    ),
    (
        gen_random_uuid(), 'CHN', 'EUR', 'manufactured_goods',
        380000000000, 'HIGH', FALSE, NULL, 'UNCLASS'
    ),
    (
        gen_random_uuid(), 'USA', 'CHN', 'agricultural_products',
        26000000000, 'MEDIUM', FALSE, NULL, 'UNCLASS'
    )
ON CONFLICT DO NOTHING;

INSERT INTO econ_indicators (
    id, country_code, indicator_name, value, unit, year, source, classification
) VALUES
    (gen_random_uuid(), 'RUS', 'GDP_GROWTH_RATE',  -2.10, 'percent',      2023, 'IMF',        'UNCLASS'),
    (gen_random_uuid(), 'RUS', 'INFLATION',         7.40, 'percent',      2023, 'IMF',        'UNCLASS'),
    (gen_random_uuid(), 'RUS', 'UNEMPLOYMENT',      3.90, 'percent',      2023, 'Rosstat',    'UNCLASS'),
    (gen_random_uuid(), 'IRN', 'GDP_GROWTH_RATE',   1.40, 'percent',      2023, 'IMF',        'UNCLASS'),
    (gen_random_uuid(), 'IRN', 'INFLATION',        44.60, 'percent',      2023, 'IMF',        'UNCLASS'),
    (gen_random_uuid(), 'PRK', 'GDP_GROWTH_RATE',  -4.50, 'percent',      2022, 'Bank of Korea', 'UNCLASS'),
    (gen_random_uuid(), 'CHN', 'GDP_GROWTH_RATE',   5.20, 'percent',      2023, 'NBS China',  'UNCLASS'),
    (gen_random_uuid(), 'CHN', 'INFLATION',         0.20, 'percent',      2023, 'NBS China',  'UNCLASS'),
    (gen_random_uuid(), 'USA', 'GDP_GROWTH_RATE',   2.50, 'percent',      2023, 'BEA',        'UNCLASS'),
    (gen_random_uuid(), 'USA', 'INFLATION',         3.40, 'percent',      2023, 'BLS',        'UNCLASS')
ON CONFLICT DO NOTHING;

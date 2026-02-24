-- =============================================================================
-- 007_intel_schema.sql — Intelligence Service supplemental tables
-- Extends the intel_items table defined in 001_schema.sql with:
--   * intel_threat_assessments — stored threat assessment results
--   * osint_ingestion_jobs     — ingestion job history / audit trail
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Threat Assessments
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intel_threat_assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor               TEXT NOT NULL,
    target              TEXT NOT NULL,
    context             TEXT,
    threat_level        TEXT NOT NULL CHECK (threat_level IN ('NEGLIGIBLE','LOW','MODERATE','HIGH','CRITICAL')),
    threat_score        DOUBLE PRECISION NOT NULL CHECK (threat_score >= 0 AND threat_score <= 10),
    threat_vectors      TEXT[] DEFAULT '{}',
    indicators          JSONB DEFAULT '[]',
    confidence          DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    summary             TEXT,
    recommendations     JSONB DEFAULT '[]',
    ai_assisted         BOOLEAN DEFAULT FALSE,
    intel_item_ids      UUID[] DEFAULT '{}',   -- referenced intel items
    classification      classification_level DEFAULT 'UNCLASS',
    created_by          TEXT,
    assessed_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threat_assessments_actor  ON intel_threat_assessments(actor);
CREATE INDEX IF NOT EXISTS idx_threat_assessments_target ON intel_threat_assessments(target);
CREATE INDEX IF NOT EXISTS idx_threat_assessments_level  ON intel_threat_assessments(threat_level);
CREATE INDEX IF NOT EXISTS idx_threat_assessments_time   ON intel_threat_assessments(assessed_at DESC);

-- ---------------------------------------------------------------------------
-- OSINT Ingestion Jobs
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS osint_ingestion_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       TEXT NOT NULL,            -- 'acled', 'ucdp', 'rss'
    source_type     TEXT NOT NULL,
    since_date      TIMESTAMPTZ NOT NULL,
    items_fetched   INTEGER DEFAULT 0,
    items_saved     INTEGER DEFAULT 0,
    errors          JSONB DEFAULT '[]',
    dry_run         BOOLEAN DEFAULT FALSE,
    duration_sec    DOUBLE PRECISION DEFAULT 0,
    status          TEXT DEFAULT 'COMPLETED' CHECK (status IN ('RUNNING','COMPLETED','FAILED')),
    triggered_by    TEXT,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_osint_jobs_source ON osint_ingestion_jobs(source_id);
CREATE INDEX IF NOT EXISTS idx_osint_jobs_time   ON osint_ingestion_jobs(started_at DESC);

-- ---------------------------------------------------------------------------
-- Full-text search index on intel_items (not created in 001_schema.sql)
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_intel_fts ON intel_items
    USING GIN(to_tsvector('english', title || ' ' || COALESCE(content, '')));

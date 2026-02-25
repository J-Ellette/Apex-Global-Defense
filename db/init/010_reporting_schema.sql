-- Reporting Schema
-- Stores generated intelligence and operational reports: SITREP, INTSUM, CONOPS.

CREATE TABLE IF NOT EXISTS reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id     UUID,
    run_id          UUID,
    report_type     TEXT NOT NULL,          -- SITREP / INTSUM / CONOPS
    title           TEXT NOT NULL,
    classification  classification_level NOT NULL DEFAULT 'UNCLASS',
    author_id       TEXT,
    status          TEXT NOT NULL DEFAULT 'DRAFT',  -- DRAFT / FINAL / APPROVED
    content         JSONB NOT NULL DEFAULT '{}',    -- structured report content
    summary         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by     TEXT,
    approved_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_reports_scenario_id  ON reports (scenario_id);
CREATE INDEX IF NOT EXISTS idx_reports_run_id       ON reports (run_id);
CREATE INDEX IF NOT EXISTS idx_reports_report_type  ON reports (report_type);
CREATE INDEX IF NOT EXISTS idx_reports_status       ON reports (status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at   ON reports (created_at DESC);

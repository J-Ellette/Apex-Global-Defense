-- 016_event_archival.sql
-- Retention and archival policy for high-volume tables.
--
-- Priority C (improvements.md): "Add retention/partitioning + archival policy
-- for sim_events and audit_log."
--
-- Strategy:
--   • sim_events   — archive rows older than 90 days into sim_events_archive
--   • audit_log    — archive rows older than 180 days into audit_log_archive
--   • Both archive tables are identical to their source tables plus an
--     archived_at timestamp so operators know when the row was moved.
--   • Helper functions archive_old_sim_events() and archive_old_audit_log()
--     are designed to be called from a cron job (e.g. pg_cron or an external
--     scheduler).  They are idempotent and safe to run at any frequency.
--
-- NOTE: Full declarative partitioning (PARTITION BY RANGE) would require
-- converting the existing tables, which is a breaking DDL change.  This
-- archive-table approach provides equivalent retention control with no
-- downtime risk and is safe to apply incrementally.

-- ── sim_events archive ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sim_events_archive (
    LIKE sim_events INCLUDING ALL,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_sim_events_archive_run_id
    ON sim_events_archive (run_id);

CREATE INDEX IF NOT EXISTS ix_sim_events_archive_archived_at
    ON sim_events_archive (archived_at);

-- archive_old_sim_events: moves sim_events rows older than p_retain_days days
-- into sim_events_archive and deletes them from the live table.
-- Returns the number of rows archived.
CREATE OR REPLACE FUNCTION archive_old_sim_events(
    p_retain_days INT DEFAULT 90
) RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_cutoff  TIMESTAMPTZ := NOW() - (p_retain_days || ' days')::INTERVAL;
    v_count   INT;
BEGIN
    -- Insert into archive (exclude the computed archived_at; it defaults to NOW())
    INSERT INTO sim_events_archive
        SELECT *, NOW() AS archived_at
        FROM   sim_events
        WHERE  time < v_cutoff;

    GET DIAGNOSTICS v_count = ROW_COUNT;

    -- Remove archived rows from the live table
    DELETE FROM sim_events WHERE time < v_cutoff;

    RETURN v_count;
END;
$$;

COMMENT ON FUNCTION archive_old_sim_events(INT) IS
    'Moves sim_events rows older than p_retain_days days to sim_events_archive. '
    'Idempotent. Intended to be called from a scheduled job (default: 90-day retention).';

-- ── audit_log archive ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log_archive (
    LIKE audit_log INCLUDING ALL,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_log_archive_actor_id
    ON audit_log_archive (actor_id);

CREATE INDEX IF NOT EXISTS ix_audit_log_archive_archived_at
    ON audit_log_archive (archived_at);

-- archive_old_audit_log: moves audit_log rows older than p_retain_days days
-- into audit_log_archive. Returns the number of rows archived.
CREATE OR REPLACE FUNCTION archive_old_audit_log(
    p_retain_days INT DEFAULT 180
) RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_cutoff  TIMESTAMPTZ := NOW() - (p_retain_days || ' days')::INTERVAL;
    v_count   INT;
BEGIN
    INSERT INTO audit_log_archive
        SELECT *, NOW() AS archived_at
        FROM   audit_log
        WHERE  occurred_at < v_cutoff;

    GET DIAGNOSTICS v_count = ROW_COUNT;

    DELETE FROM audit_log WHERE occurred_at < v_cutoff;

    RETURN v_count;
END;
$$;

COMMENT ON FUNCTION archive_old_audit_log(INT) IS
    'Moves audit_log rows older than p_retain_days days to audit_log_archive. '
    'Idempotent. Intended to be called from a scheduled job (default: 180-day retention).';

-- ── Helpful views ────────────────────────────────────────────────────────────

-- v_sim_events_all: union of live + archived events for forensic queries.
CREATE OR REPLACE VIEW v_sim_events_all AS
    SELECT *, FALSE AS is_archived FROM sim_events
    UNION ALL
    SELECT time, run_id, event_type, entity_id, location, payload,
           turn_number, TRUE AS is_archived
    FROM   sim_events_archive;

-- v_audit_log_all: union of live + archived audit entries.
CREATE OR REPLACE VIEW v_audit_log_all AS
    SELECT *, FALSE AS is_archived FROM audit_log
    UNION ALL
    SELECT id, actor_id, actor_role, action, resource_type, resource_id,
           classification_level, detail, occurred_at, TRUE AS is_archived
    FROM   audit_log_archive;

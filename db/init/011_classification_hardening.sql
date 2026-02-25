-- =============================================================================
-- Apex Global Defense (AGD) — Classification Hardening Migration
-- Migration 011 — Phase 4 Enterprise: Row-Level Security for all classified tables
-- =============================================================================
--
-- Extends RLS to every table that carries a classification_level column.
-- Relies on the session setting agd.user_classification being set by the
-- application before issuing queries (SET LOCAL agd.user_classification = '...').
--
-- Pattern: cumulative clearance — a user cleared at level X can see all records
-- classified at X and below.
--
-- Write restriction: INSERT / UPDATE of records at a higher classification
-- than the caller's clearance ceiling is rejected by a WITH CHECK expression.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Helper function: returns the ordered list of levels visible to the current
-- session's classification setting.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION agd_visible_classifications()
RETURNS TEXT[] LANGUAGE sql STABLE AS $$
    SELECT CASE current_setting('agd.user_classification', TRUE)
        WHEN 'UNCLASS'    THEN ARRAY['UNCLASS']
        WHEN 'FOUO'       THEN ARRAY['UNCLASS','FOUO']
        WHEN 'SECRET'     THEN ARRAY['UNCLASS','FOUO','SECRET']
        WHEN 'TOP_SECRET' THEN ARRAY['UNCLASS','FOUO','SECRET','TOP_SECRET']
        WHEN 'TS_SCI'     THEN ARRAY['UNCLASS','FOUO','SECRET','TOP_SECRET','TS_SCI']
        ELSE ARRAY['UNCLASS']
    END
$$;

-- ---------------------------------------------------------------------------
-- scenarios
-- ---------------------------------------------------------------------------

ALTER TABLE scenarios ENABLE ROW LEVEL SECURITY;

CREATE POLICY scenarios_select ON scenarios
    FOR SELECT
    USING (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY scenarios_insert ON scenarios
    FOR INSERT
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY scenarios_update ON scenarios
    FOR UPDATE
    USING (classification::text = ANY(agd_visible_classifications()))
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY scenarios_delete ON scenarios
    FOR DELETE
    USING (classification::text = ANY(agd_visible_classifications()));

-- ---------------------------------------------------------------------------
-- equipment
-- ---------------------------------------------------------------------------

ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;

CREATE POLICY equipment_select ON equipment
    FOR SELECT
    USING (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY equipment_insert ON equipment
    FOR INSERT
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY equipment_update ON equipment
    FOR UPDATE
    USING (classification::text = ANY(agd_visible_classifications()))
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

-- ---------------------------------------------------------------------------
-- annotations
-- ---------------------------------------------------------------------------

ALTER TABLE annotations ENABLE ROW LEVEL SECURITY;

CREATE POLICY annotations_select ON annotations
    FOR SELECT
    USING (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY annotations_insert ON annotations
    FOR INSERT
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY annotations_update ON annotations
    FOR UPDATE
    USING (classification::text = ANY(agd_visible_classifications()))
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

-- ---------------------------------------------------------------------------
-- cyber_infra_nodes
-- ---------------------------------------------------------------------------

ALTER TABLE cyber_infra_nodes ENABLE ROW LEVEL SECURITY;

CREATE POLICY cyber_nodes_select ON cyber_infra_nodes
    FOR SELECT
    USING (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY cyber_nodes_insert ON cyber_infra_nodes
    FOR INSERT
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY cyber_nodes_update ON cyber_infra_nodes
    FOR UPDATE
    USING (classification::text = ANY(agd_visible_classifications()))
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

-- ---------------------------------------------------------------------------
-- intel_threat_assessments
-- ---------------------------------------------------------------------------

ALTER TABLE intel_threat_assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY threat_assessments_select ON intel_threat_assessments
    FOR SELECT
    USING (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY threat_assessments_insert ON intel_threat_assessments
    FOR INSERT
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY threat_assessments_update ON intel_threat_assessments
    FOR UPDATE
    USING (classification::text = ANY(agd_visible_classifications()))
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

-- ---------------------------------------------------------------------------
-- reports
-- ---------------------------------------------------------------------------

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY reports_select ON reports
    FOR SELECT
    USING (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY reports_insert ON reports
    FOR INSERT
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

CREATE POLICY reports_update ON reports
    FOR UPDATE
    USING (classification::text = ANY(agd_visible_classifications()))
    WITH CHECK (classification::text = ANY(agd_visible_classifications()));

-- ---------------------------------------------------------------------------
-- Superuser bypass: PostgreSQL superusers and table owners bypass RLS by
-- default.  For production, the application DB role (agd_app) must NOT be a
-- superuser so that these policies are enforced.
-- Grant the application role BYPASSRLS=false (the default) to enforce policies.
-- ---------------------------------------------------------------------------

-- Create application role if it doesn't exist (no-op if already exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'agd_app') THEN
        CREATE ROLE agd_app NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
END
$$;

-- =============================================================================
-- 020_seed_users.sql
-- Dev seed users for local development. No passwords stored — auth-svc
-- trusts email lookup in dev mode (see handlers/auth.go).
-- =============================================================================

INSERT INTO users (
    id, keycloak_id, email, display_name, roles, classification, org_id, active
) VALUES
    (
        '00000000-0000-0000-0000-000000000100',
        'dev-admin',
        'admin@agd.local',
        'Dev Admin',
        '["admin"]'::jsonb,
        'TS_SCI',
        '00000000-0000-0000-0000-000000000001',
        true
    ),
    (
        '00000000-0000-0000-0000-000000000101',
        'dev-analyst',
        'analyst@agd.local',
        'Dev Analyst',
        '["analyst"]'::jsonb,
        'SECRET',
        '00000000-0000-0000-0000-000000000001',
        true
    )
ON CONFLICT (email) DO NOTHING;

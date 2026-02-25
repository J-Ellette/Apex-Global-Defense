# Runbook: DB Init / Migration Failure

**Failure Class:** Database initialization or migration failure — partial schema drift  
**Severity:** High  
**Services Affected:** All backend services (PostgreSQL dependency)

---

## Symptoms

- One or more services fail to start with `relation does not exist` or `column does not exist` errors
- `docker compose up` exits with non-zero code from a service that queries a missing table
- A migration SQL script partially applies and leaves the DB in an inconsistent state
- Services connect but return 500 errors on endpoints that hit newly-added columns

---

## Immediate Triage

```bash
# 1. Check Postgres health
docker compose -f docker-compose.dev.yml exec postgres pg_isready -U agd -d agd_dev

# 2. List tables that exist
docker compose -f docker-compose.dev.yml exec postgres psql -U agd -d agd_dev \
  -c "\dt"

# 3. Check which init scripts ran
docker compose -f docker-compose.dev.yml exec postgres psql -U agd -d agd_dev \
  -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1;"

# 4. Check service logs for the specific error
docker compose -f docker-compose.dev.yml logs <service-name> | tail -50
```

---

## Common Causes and Fixes

### Init script did not run (fresh volume, script ordering issue)

**Cause:** `db/init/` scripts run in alphabetical order; a new script may have been skipped if volume was created before it was added.

**Fix:**
```bash
# Destroy volume and restart to re-run all init scripts
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up --build
```

### Partial schema application (script failed mid-way)

**Cause:** A script in `db/init/` raised an error (e.g., duplicate object) partway through, leaving schema partially applied.

**Fix:**
```bash
# Connect and inspect the error
docker compose -f docker-compose.dev.yml exec postgres psql -U agd -d agd_dev

# Check for partial table creation
\d <table_name>

# Re-run the specific failed script (idempotent scripts use IF NOT EXISTS)
docker compose -f docker-compose.dev.yml exec postgres psql -U agd -d agd_dev \
  -f /docker-entrypoint-initdb.d/<script_name>.sql
```

### Missing extension (timescaledb / pgvector not available)

**Cause:** Base Postgres image does not include `timescaledb` or `pgvector`. AGD gracefully handles this at startup via `DO $$ BEGIN ... EXCEPTION WHEN ... END $$` blocks.

**Symptom:** `sim_events` runs without time-series partitioning; `intel_items` uses JSONB instead of vector type.

**Fix (dev):** This is expected behavior in plain Postgres. No action needed; functionality degrades gracefully.

**Fix (production):** Use `timescale/timescaledb-ha:pg16-latest` or `ankane/pgvector` image and ensure extension loads before init scripts.

### RLS policy blocks service user

**Cause:** Row-level security is enabled on classified tables and `agd.user_classification` session variable is not set before the query.

**Symptom:** Queries return empty results or `ERROR: row security is active` for the `agd` user.

**Fix:** Ensure the service sets `SET LOCAL agd.user_classification = '<level>';` at the start of each transaction when querying classified tables. See `db/init/011_classification_hardening.sql`.

---

## Validation After Fix

```bash
# Run schema migration smoke check
make db-migrate

# Run full health sweep
make smoke-test

# Run service unit tests
make svc-test SVC=<service-name>
```

---

## Escalation

If the DB volume is corrupt or the issue cannot be resolved by re-initializing with `down -v`, escalate to the database administrator. Do **not** manually edit production schema without a reviewed migration script.

---

*Apex Global Defense | Operations | UNCLASSIFIED*

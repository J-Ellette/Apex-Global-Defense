# AGD — Database Dev-Fallback Behavior

## Overview

AGD uses two optional PostgreSQL extensions that enhance performance and
intelligence features in production but are **not required for local
development**:

| Extension | Purpose | Required for |
|-----------|---------|-------------|
| [TimescaleDB](https://docs.timescale.com/) | Time-series compression and continuous aggregates for `sim_events` and `audit_log` | Production retention/compaction SLOs |
| [pgvector](https://github.com/pgvector/pgvector) | High-dimensional similarity search (cosine/L2) | `intel-svc` semantic search (`/intel/search`) |

The dev compose stack uses `postgis/postgis:16-3.4` which does **not** include
TimescaleDB or pgvector.  All init scripts (`db/init/`) detect extension
availability at startup and degrade gracefully:

- If `timescaledb` is missing, hypertable creation is skipped.
- If `vector` (pgvector) is missing, the `embedding` column and vector index
  on `intel_items` are skipped; the service falls back to full-text search.

---

## Dev Environment (default)

```
postgis/postgis:16-3.4
├─ PostGIS (geometry/geography types, spatial indexes)       ✅ available
├─ TimescaleDB hypertables (sim_events, audit_log)           ⚠️  degraded — plain table
└─ pgvector semantic search (intel_items.embedding)          ⚠️  degraded — full-text fallback
```

No action required.  `make dev` works out of the box.

---

## Enabling Extensions in Dev (optional)

If you want to test TimescaleDB or pgvector locally, switch to an image that
ships both:

```yaml
# docker-compose.dev.yml — postgres service
image: timescale/timescaledb-ha:pg16-latest   # ships timescaledb + pgvector
```

Then restart:

```bash
make dev-down
docker compose -f docker-compose.dev.yml up --build postgres
```

---

## Production Expectations

| Feature | Requirement |
|---------|------------|
| `sim_events` / `audit_log` time-series compression | TimescaleDB ≥ 2.14 |
| `sim_events` / `audit_log` retention policy | TimescaleDB `add_retention_policy()` |
| `intel_items` vector similarity search | pgvector ≥ 0.7.0 |
| PostGIS spatial queries | PostGIS ≥ 3.4 (bundled in most images) |

In production (Kubernetes via the Helm chart), the `postgres` container uses
`timescale/timescaledb-ha:pg16-latest` by default, which bundles all three
extensions.  See `helm/agd/values.yaml` for the image override.

---

## Schema Init Guard Pattern

All `db/init/` scripts that use optional extensions follow this pattern to
avoid hard failures on plain PostgreSQL images:

```sql
-- Create vector extension if available; skip silently otherwise.
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'pgvector not available — semantic search disabled';
END
$$;
```

This ensures `make dev` and CI (`docker-compose.test.yml`) complete without
requiring the full production extension set.

---

## Related Files

| File | Notes |
|------|-------|
| `db/init/001_schema.sql` | pgvector guard for `intel_items.embedding` |
| `db/init/016_event_archival.sql` | TimescaleDB hypertable guards for `sim_events` / `audit_log` |
| `docs/fedramp/README.md` | Production DB security controls |
| `scripts/db-migrate-smoke.sh` | Migration smoke validation (no extension checks) |

---

*Last updated: Session 17 — 2026-02-26 | UNCLASSIFIED*

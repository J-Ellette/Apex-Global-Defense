# AGD Unified Improvement Suggestions

_Last updated: 2026-02-26_

This document synthesizes and prioritizes improvement opportunities from ChatGPT, Claude, and Copilot reviews. It merges overlapping recommendations, resolves conflicts by selecting the most actionable or detailed option, and organizes them by priority and impact.

---

## Priority A — Correctness & Data Integrity

### 1. Enforce Data Constraints and Foreign Keys
- Add unique/natural-key constraints to all major seed tables (e.g., `econ_indicators`, `econ_trade_routes`, `econ_sanction_targets`, `infoops_narrative_threats`, `infoops_influence_campaigns`).
- Add explicit FK constraints for all `country_code`, `origin_country`, and similar fields in expansion tables. Use deferrable constraints if migration ordering requires.
- Add a migration to retroactively check and clean up any orphaned rows.

### 2. Seed Data Validation Automation
- Expand `db-seed-sanity.sql` to cover econ/infoops tables, checking for duplicate natural keys, invalid/missing country references, out-of-range values, and invalid enum/text domains.
- Integrate these checks into CI/CD so every PR and nightly build validates seed data integrity.
- Add a pre-commit or CI lint step to flag non-ISO country codes.

### 3. Standardize and Document Data Formats
- Define category-specific JSON schema contracts for `equipment_catalog.specs` and normalize units/types.
- Replace symbolic placeholders (e.g., '—') with `null` or explicit metadata fields.
- Document and enforce ISO 3166-1 alpha-3 codes for all country references.

---

## Priority B — Architecture & Technical Debt

### 4. Shared Auth Middleware Adoption
- Migrate all Python services to use `agd-shared` for JWT auth middleware. Remove local `app/auth.py` copies and update imports.

### 5. API Gateway and Service Exposure
- Add Kong/Nginx API gateway to `docker-compose.dev.yml` and Helm chart, or update documentation to reflect the current direct-exposure approach and future plans.

### 6. Keycloak Realm Auto-Provisioning
- Add a Keycloak realm export and mount it for auto-provisioning in dev. Document this in the Quick Start.

---

## Priority C — Documentation & Roadmap Accuracy

### 7. Documentation Sync
- Align `buildsheet.md` and `README.md` status, service inventory, and stack descriptions with the actual codebase and deployment.
- Update validation checklists and implementation order in `SeedDataExpansion.md` to reflect completed work.
- Add missing deliverables to `docs/status-matrix.md`.
- Update frontend stack documentation to match actual libraries (MapLibre GL, native WebSocket, etc.).

### 8. Provenance and Source Attribution
- For each major seed block, add a comment or metadata field referencing the primary data source. Consider a `source` column for traceability.

---

## Priority D — Data Expansion & Quality

### 9. Expand and Normalize Seed Data
- Continue expanding `equipment_catalog` toward the 270–450 entry target, prioritizing underrepresented categories.
- Normalize multi-origin platforms (e.g., FRA/ITA) to arrays or canonical representations.
- Add missing economic indicators for all planned countries.
- Review and update sanction targets and trade routes for real-world accuracy.

### 10. Performance and Scalability
- Add scripts to generate synthetic large-scale data for stress-testing backend and frontend.
- Add benchmark tests for primary endpoints and track query latency in CI.
- Monitor and optimize frontend performance as data grows (pagination, server-side filtering).

---

## Priority E — Operations, Observability, and Planning

### 11. Archival and Data Lifecycle
- Ensure archival functions are scheduled/invoked (via `pg_cron` or external job) for event/audit tables.
- Define retention/versioning strategy for analytical tables as data grows.

### 12. Observability
- Expand Grafana dashboards to cover new services and seed data ingestion/validation metrics.
- Update observability stack documentation to match actual deployments (Prometheus, Grafana, Jaeger).

### 13. Phase 5 and Future Planning
- Create a Phase 5 planning document for future services (map-svc, ai-svc, notify-svc, audit-svc, mobile app), including endpoint specs and MVP definitions.
- For every new AI-powered feature, ensure deterministic fallbacks are implemented and tested.

---

## Priority F — Minor / Housekeeping

- Update misleading Makefile targets and comments (e.g., `db-migrate`).
- Check off completed items in validation checklists and update session numbers where needed.
- Add missing URLs and notes for observability stack in README Quick Start.
- Sync schema documentation with actual DB columns and categories.

---

_Review and prioritize these suggestions for upcoming sprints. This unified list is intended to maximize data integrity, maintainability, and developer onboarding for AGD._

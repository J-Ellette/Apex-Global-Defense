# AGD Copilot Improvement Suggestions

_Last updated: 2026-02-26_

## 1. Data Quality & Consistency

- **Strict Foreign Key Enforcement:**
  - Add explicit FK constraints for all `country_code`, `origin_country`, and similar fields in expansion tables (e.g., `econ_trade_routes.destination_country`). This will prevent silent data loss and ensure referential integrity.
  - Add a migration to retroactively check and clean up any orphaned rows.

- **Seed Data Validation Automation:**
  - Integrate the reusable SQL sanity checks (e.g., `db-seed-sanity.sql`) into CI/CD so every PR and nightly build validates seed data integrity.
  - Expand the script to check for other common issues: missing required fields, invalid enum values, and duplicate names.

- **Country Code Normalization:**
  - Document and enforce ISO 3166-1 alpha-3 codes for all country references in seed and runtime data.
  - Add a pre-commit or CI lint step to flag non-ISO codes (like 'EUR').

## 2. Schema & Seed Expansion

- **Equipment Catalog Coverage:**
  - Continue expanding `019_equipment_catalog_seed.sql` toward the 270–450 entry target. Prioritize underrepresented categories (e.g., support vehicles, UAVs, logistics, EW, C4ISR).
  - Normalize multi-origin platforms (e.g., FRA/ITA) to arrays or a canonical representation for better downstream filtering.

- **Economic & InfoOps Data:**
  - Review all new sanction targets and trade routes for real-world plausibility and up-to-date status (e.g., check for lifted or suspended sanctions).
  - Add more granular disruption causes and dependency levels to trade routes for richer scenario modeling.

## 3. Documentation & Developer Experience

- **Seed Data Source Attribution:**
  - For each major seed block, add a comment or metadata field referencing the primary data source (e.g., SIPRI, Jane's, ODIN).
  - Consider a `source` column in catalog tables for traceability.

- **Validation Checklist Automation:**
  - Convert the checklist in `SeedDataExpansion.md` into a scriptable test (e.g., Python or Bash) that runs as part of `make test`.

- **Frontend Data Volume Handling:**
  - Monitor and optimize frontend filter/search performance as seed data grows. Consider paginated endpoints or server-side filtering for large tables.

## 4. Roadmap & Risk Management

- **Mobile App Roadmap:**
  - Define a concrete MVP for the deferred mobile app (read-only, offline maps). Identify blockers and required backend changes.

- **Classification & Security:**
  - Periodically review RLS and classification enforcement with new data and features. Add regression tests for classification leaks.

- **AI/ML Fallbacks:**
  - For every new AI-powered feature, ensure a deterministic fallback is implemented and tested (especially for air-gap deployments).

## 5. Miscellaneous

- **Test Data Volume:**
  - Add a script to generate synthetic large-scale data for stress-testing both backend and frontend (simulate 10x–100x current seed volume).

- **Observability:**
  - Expand Grafana dashboards to cover new services and seed data ingestion/validation metrics.

---

_These suggestions are based on the current state of the buildsheet, README, copilot log, and SeedDataExpansion plan. Review and prioritize as appropriate for upcoming sprints._

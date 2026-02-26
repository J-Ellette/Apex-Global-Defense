# AGD Improvement Suggestions (ChatGPT)

Based on review of:
- `buildsheet.md`
- `README.md`
- `copilot.md`
- `SeedDataExpansion.md`

## Top Improvement Opportunities

## 1) Add Seed Data Constraints (Highest Impact)
Current seed expansions (`017`/`018`/`019`) are idempotent by `id`, but core domain tables still lack natural-key constraints.

Why this matters:
- Prevents silent duplicate semantics when new rows use new UUIDs for the same conceptual entity.
- Makes future seed updates safer than relying on manual UUID discipline.

Suggested changes:
- `econ_indicators`: unique on `(country_code, indicator_name, year)`.
- `econ_trade_routes`: unique on `(origin_country, destination_country, commodity)`.
- `econ_sanction_targets`: unique on `(country_code, sanction_type, effective_date, name)` (or another agreed business key).
- `infoops_narrative_threats`: unique on `(title, origin_country)`.
- `infoops_influence_campaigns`: unique on `(name, sponsoring_state)`.

## 2) Add Foreign Keys for Country Codes
Econ and InfoOps tables store `country_code`/`origin_country`/`destination_country` but don’t enforce FK linkage to `countries(code)`.

Why this matters:
- Prevents drift and typos in future migrations.
- Removes need for manual "country backfill" rescue patterns later.

Suggested changes:
- Add FK constraints where country code columns exist.
- Keep deferrable constraints if migration ordering needs flexibility.

## 3) Standardize `specs` JSON Shape in `equipment_catalog`
`019_equipment_catalog_seed.sql` mixes numeric and string representations for similar attributes (e.g., numeric ranges vs string ranges; nullable fields encoded with symbols like `—`).

Why this matters:
- Frontend filters and simulation logic become harder and more brittle.
- Analytics and indexing on JSONB become inconsistent.

Suggested changes:
- Define category-specific JSON schema contracts in `docs/`.
- Normalize units and scalar types (`number` vs `string`) by key.
- Replace symbolic placeholders (`—`) with `null` and explicit metadata fields.

## 4) Expand Seed Sanity Checks Beyond Equipment
Current `scripts/db-seed-sanity.sql` validates only equipment quality.

Why this matters:
- The biggest expansion risk now is in econ/infoops consistency, not only equipment.

Suggested changes:
- Add checks for:
  - duplicate natural keys in econ/infoops
  - invalid/missing country references
  - out-of-range confidence/threat/severity values
  - invalid enum-like text domains (status/type fields)
- Run this script in CI after migration smoke.

## 5) Close Buildsheet vs README Status Drift
`README.md` reports Phase 4 complete; `buildsheet.md` still has legacy/older status framing in places.

Why this matters:
- New contributors use both docs; drift causes planning confusion.

Suggested changes:
- Declare a single source of truth for status (recommend `README.md`).
- Add a short "Buildsheet lagging sections" note or update buildsheet phase tables to match current state.

## 6) Convert Text Domain Fields to Enums/Checks
In `012_econ_schema.sql` and `013_infoops_schema.sql`, many domain values are free-text (`status`, `threat_level`, `indicator_type`, `classification`).

Why this matters:
- Easy to introduce spelling variants and unqueryable taxonomies.

Suggested changes:
- Add `CHECK` constraints or PostgreSQL enums for key domain fields.
- Align with existing classification model conventions used elsewhere.

## 7) Add Provenance Metadata for Seed Rows
`SeedDataExpansion.md` includes strong source references, but rows inserted into DB do not carry structured provenance links per record.

Why this matters:
- Auditing and trust in analytical output are stronger when each row can be traced.

Suggested changes:
- Add optional metadata fields (or sidecar table) for `source_url`, `source_org`, `source_date`, `confidence_note` on econ/infoops seedable entities.

## 8) Add Performance Tests for Seed Scale Claims
`SeedDataExpansion.md` targets larger data volume, but CI currently emphasizes correctness, not query latency under expanded seeds.

Why this matters:
- UI and API behavior can degrade after additional seed growth.

Suggested changes:
- Add benchmark tests for primary list/filter/search endpoints in econ/infoops/equipment modules.
- Track p50/p95 for representative queries in CI artifacts.

## 9) Introduce Seed Generation Pipeline (Instead of Hand-Written SQL Only)
Current seed expansions are large hand-authored SQL files.

Why this matters:
- Harder to maintain, diff, and validate at scale.

Suggested changes:
- Define structured source files (`.csv`/`.json`) plus a deterministic generator that emits SQL.
- Keep generated SQL committed, but validate source→SQL determinism in CI.

## 10) Add Data Lifecycle Policy for Large Seed Tables
You already added archival for events/audit (`016`), but seeded analytical tables can also bloat as yearly indicators/campaign history grows.

Why this matters:
- Long-term operational cost and query performance.

Suggested changes:
- Define retention/versioning strategy for indicators and historical narrative assessments.
- Separate canonical current snapshot views from full historical tables.

---

## Suggested 2-Week Execution Order

1. Add constraints/FKs (items 1 and 2).
2. Normalize equipment `specs` schema and add JSON checks (item 3).
3. Expand `db-seed-sanity.sql` + CI hook (item 4).
4. Align docs status and buildsheet references (item 5).
5. Add provenance fields and seed generation workflow (items 7 and 9).

These changes will materially improve data integrity, maintainability, and trustworthiness of AGD’s expanded seed foundation.

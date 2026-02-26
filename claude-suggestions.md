# AGD Improvement Suggestions

**Reviewed:** 2026-02-26 | **Sessions covered:** 1–22 + SeedDataExpansion
**Scope:** buildsheet.md, README.md, copilot.md, SeedDataExpansion.md, CI, Makefile, DB init scripts

---

## Priority A — Correctness / Operations-Blocking

These are bugs or gaps that will cause silent failures or incorrect behavior in a running system.

### A1 — `make db-migrate` only runs `001_schema.sql`

**File:** [Makefile:103](Makefile)
**Issue:** The `db-migrate` target runs only `001_schema.sql` — it ignores all 18 subsequent init scripts. Running `make db-migrate` after initial setup will not apply `002`–`019`.
**Fix:** Either remove the `db-migrate` target (Docker auto-runs all `db/init/*.sql` files on first boot, making it redundant) or rewrite it to loop through all files in sequence. The `migrate-smoke` target is the right tool for validation; `db-migrate` as written is misleading.

### A2 — CI Go test matrix is stale: `auth-svc, oob-svc, collab-svc` only

**File:** [.github/workflows/ci.yml:42](.github/workflows/ci.yml)
**Issue:** The `test-go` CI job matrix is `service: [auth-svc, oob-svc, collab-svc]`. This excludes `sim-engine` (Rust) from automated testing entirely — the Rust simulation engine has no CI test coverage at all. Additionally, Python services are tested in a separate matrix, but coverage results are not uploaded to Codecov (unlike Go services which upload per-service flags).
**Fix:** Add a `cargo test` CI job for `sim-engine`. Upload Python service coverage to Codecov alongside Go.

### A3 — Archival functions are defined but never invoked

**File:** [db/init/016_event_archival.sql](db/init/016_event_archival.sql)
**Issue:** `archive_old_sim_events(retain_days := 90)` and `archive_old_audit_log(retain_days := 180)` are created but nothing calls them. Data will accumulate in `sim_events` and `audit_log` indefinitely. For FedRAMP AU-11 (audit record retention), a scheduled invocation is required.
**Fix:** Add a `pg_cron` schedule inside `016_event_archival.sql` (requires `pg_cron` extension), or document an external cron/Kubernetes CronJob that calls these functions and add it to the Helm chart.

### ~~A4 — `ETH` missing from country backfill in `017_econ_seed_expansion.sql`~~ ✅ Resolved

**File:** [db/init/017_econ_seed_expansion.sql:9-31](db/init/017_econ_seed_expansion.sql)
**Resolution:** `ETH` (Ethiopia) is present in `002_seed_countries.sql` (line 59) with full data (GDP, population, area, ISO2, flag). The 017 backfill correctly omits it. The `ON CONFLICT (code) DO NOTHING` would have been a no-op. The `econ_sanction_targets` FK for ETH resolves correctly.

### A5 — Kafka has no consumers; topic table in buildsheet is fictitious

**File:** [buildsheet.md:654-659](buildsheet.md)
**Issue:** The buildsheet documents a full Kafka topic table (`sim.events`, `intel.processed`, `oob.changes`, `alerts`, `audit`), and Kafka appears in `docker-compose.dev.yml`. However, no AGD service implements a Kafka producer or consumer. All async communication is Redis pub/sub (`collab-svc`). Kafka does not start cleanly because the ZooKeeper service it depends on is not in `docker-compose.dev.yml`.
**Fix (short-term):** Remove Kafka from `docker-compose.dev.yml` or add ZooKeeper. Document that Kafka is planned but not implemented.
**Fix (long-term):** If Kafka is intended for Phase 5, add it to the Phase 5 plan document with actual producer/consumer specs.

---

## Priority B — Architecture / Technical Debt

### B1 — `agd-shared` auth middleware not migrated to the 13 Python services

**File:** [services/agd-shared/README.md](services/agd-shared/README.md)
**Issue:** `agd-shared` was created in Session 16 to consolidate the duplicated JWT auth middleware copied across 13 services. The copilot log explicitly states "Services continue using their local `app/auth.py` for now." The shared package exists but isn't actually used — and likely isn't included in each service's `requirements.txt`.
**Consequence:** Any security fix to auth logic must be made in 13 separate places.
**Fix:** For each Python service, (1) add `agd-shared` to `requirements.txt`, (2) replace `from app.auth import ...` imports with `from agd_shared.auth import ...`, (3) delete the local `app/auth.py` copy.

### B2 — No API gateway in the actual deployment

**File:** [buildsheet.md:299-333](buildsheet.md)
**Issue:** Buildsheet §4.1 documents a Kong Gateway config with rate limiting and JWT plugin. The actual `docker-compose.dev.yml` and Helm chart have no API gateway. All 16 services are exposed directly on host ports, with no rate limiting, TLS termination, or unified routing layer.
**Consequence:** Production deployments lack rate limiting, centralized auth, and a single ingress point.
**Fix:** Either add Kong/Nginx to `docker-compose.dev.yml` and the Helm chart, or update the buildsheet to reflect the current "no gateway" approach and document the plan for adding one.

### B3 — Keycloak realm not auto-provisioned

**File:** [README.md:222-263](README.md)
**Issue:** `make dev` starts Keycloak, but the AGD realm, clients, roles, and test users are not auto-created. A new developer must manually configure Keycloak through the admin console before any service will accept JWTs. The README Quick Start doesn't mention this.
**Fix:** Add a Keycloak realm export file (`keycloak/realm-export.json`) and mount it as `KEYCLOAK_IMPORT` in `docker-compose.dev.yml` to auto-provision the realm on first boot. Document the step in Quick Start §1.

---

## Priority C — Documentation Accuracy

Stale or incorrect information in the primary reference documents.

### C1 — Buildsheet §2.2 Service Inventory is missing 7 services

**File:** [buildsheet.md:111-127](buildsheet.md)
**Issue:** The service table lists 13 entries. The actual codebase has 16 implemented services plus sim-engine. Missing entirely: `asym-svc`, `cbrn-svc`, `terror-svc`, `econ-svc`, `infoops-svc`, `gis-export-svc`, `training-svc`. Also lists `notify-svc` and `audit-svc` (not built, not planned imminently) without a status flag.
**Fix:** Add the 7 missing services with ports and status. Add a "Not yet built" flag to `notify-svc` and `audit-svc`.

### C2 — Buildsheet Phase 2 checklist: sim-engine marked incomplete

**File:** [buildsheet.md:1595](buildsheet.md)
**Issue:** `- [ ] C++/Rust sim engine with gRPC interface` is still unchecked. The Rust sim-engine prototype scaffold exists at `services/sim-engine/` with a complete gRPC contract and stateful turn resolver (Sessions 12, 13, 17). It should be marked `[x]` (as prototype scaffold) or annotated clearly.

### C3 — Buildsheet §3.1 Frontend stack lists wrong libraries

**File:** [buildsheet.md:141-149](buildsheet.md)
**Issue:** The frontend stack lists Cesium.js, Deck.gl, and socket.io-client. The actual implementation uses MapLibre GL (not Cesium), does not use Deck.gl, and uses native browser WebSocket (not socket.io) to connect to `collab-svc`. This also means the Cesium initialization code in §3.4 is speculative, not actual.
**Fix:** Update to reflect the actual stack: MapLibre GL, native WebSocket. Remove or annotate the Cesium/socket.io code blocks as "future/aspirational."

### C4 — README Table of Contents and section headers are stale

**File:** [README.md:20](README.md), [README.md:50](README.md), [README.md:118](README.md), [README.md:407](README.md)

**Issues:**

- ToC item 10: "Phase 4 Roadmap" — Phase 4 is complete; heading should be "Future Plans" or removed
- Section header line 50: "Phases 1–3 + Phase 4 Start" — Phase 4 is fully complete
- Line 118: "Phase 4 — Enterprise (In Progress)" — should be ✅
- Line 407: "Phase 4 Roadmap" + text "Phase 4 (Enterprise) is **complete**" — the header contradicts the content

### C5 — SeedDataExpansion.md validation checklist not updated

**File:** [SeedDataExpansion.md:486-492](SeedDataExpansion.md)

**Issue:** All six validation checklist items are still `[ ]` (unchecked), but most have been completed across Sessions 19–22:

- ON CONFLICT DO NOTHING: present in all three files ✅
- JSONB arrays properly escaped: confirmed ✅
- `db-migrate-smoke.sh` passes: SMOKE_EXIT_CODE=0 ✅
- Equipment `type_code` uniqueness: 0 duplicate rows confirmed ✅
- Country code references: equipment_catalog passes; econ/infoops not verified by script
- Frontend performance: not yet verified

**Fix:** Check off the four confirmed items and add a note on remaining two.

### C6 — copilot.md Session 18 note has wrong session number

**File:** [copilot.md:1320](copilot.md)
**Issue:** "docs/status-matrix.md: All rows updated, session date bumped to Session 17" — this is Session 18 updating the matrix. Should say "Session 18."

### C7 — `docs/status-matrix.md` missing Sessions 19–22 deliverables

**File:** [docs/status-matrix.md](docs/status-matrix.md)
**Issue:** The status matrix was last updated in Session 18. It doesn't include:

- `017_econ_seed_expansion.sql`
- `018_infoops_seed_expansion.sql`
- `019_equipment_catalog_seed.sql`
- `016_event_archival.sql` schema-alignment fix (Session 22)
- `scripts/db-seed-sanity.sql`

---

## Priority D — Data Quality

### ~~D0 — `'EUR'` used as `destination_country` in three trade route rows~~ ✅ Resolved

**File:** [db/init/017_econ_seed_expansion.sql:68-77](db/init/017_econ_seed_expansion.sql)
**Resolution:** The three rows (CUB→EUR, UKR→EUR, LBY→EUR) were corrected to real ISO 3166-1 alpha-3 codes: `CUB→ESP`, `UKR→POL`, `LBY→ITA`. All three destination countries are present in `002_seed_countries.sql`. The query `WHERE destination_country = 'EUR'` returns zero rows on the current file.

### D1 — Economic indicator coverage: 15 of 25 planned countries have no indicators

**File:** [db/init/017_econ_seed_expansion.sql:88-116](db/init/017_econ_seed_expansion.sql)
**Issue:** The SeedDataExpansion.md indicator table includes 25 countries. `017` seeds indicators for only 10 (RUS, IRN, PRK, CHN, USA, CUB, SYR, MMR, SDN, VEN). The following 15 sanctioned/high-risk states have sanctions and country backfills but no indicator rows: AFG, LBY, YEM, ZWE, COD, ETH, NIC, MLI, LBN, BLR, SOM, SSD, ERI, CAF, IRQ.
**Fix:** Add a second indicator INSERT block in `017` (or a `020_econ_indicator_expansion.sql`) covering the 15 missing countries. Data is already tabulated in SeedDataExpansion.md §1.

### D2 — Multi-origin platforms attributed to a single country in `019`

**File:** [db/init/019_equipment_catalog_seed.sql](db/init/019_equipment_catalog_seed.sql)
**Issue:** Several joint-development platforms are attributed to only one partner nation, which will cause incorrect results when filtering equipment by `origin_country`:

- `SAM-NASAMS` → `'NOR'` (joint Kongsberg + Raytheon, should be NOR/USA)
- `DDG-FREMM` → `'FRA'` (also Italian Navy; FRA/ITA)
- `HEL-AW149` → `'ITA'` (AgustaWestland joint UK/ITA)

**Fix:** Either add a second `origin_country` column (e.g., `origin_countries TEXT[]`) or document that `origin_country` reflects the lead design nation, not co-production partners, and add a `specs` note.

### D3 — `db-seed-sanity.sql` doesn't cover econ or infoops tables

**File:** [scripts/db-seed-sanity.sql](scripts/db-seed-sanity.sql)
**Issue:** The three sanity checks only query `equipment_catalog`. With 017 and 018 adding ~70+ rows across econ/infoops tables, there are no automated checks for:

- Dangling `country_code` references in `econ_sanction_targets`, `econ_trade_routes`, `econ_indicators`
- Orphaned `linked_campaign_id` or `linked_narrative_id` values in `infoops_disinformation_indicators`
- Duplicate `id` values across the seed files

**Fix:** Add a second section to `db-seed-sanity.sql` with econ/infoops integrity checks. Minimal additions:

```sql
\echo '=== econ: missing country_code references ==='
SELECT id, country_code FROM econ_sanction_targets e
LEFT JOIN countries c ON c.code = e.country_code
WHERE c.code IS NULL;

\echo '=== infoops: orphaned campaign links in indicators ==='
SELECT id, linked_campaign_id FROM infoops_disinformation_indicators i
LEFT JOIN infoops_influence_campaigns c ON c.id = i.linked_campaign_id
WHERE i.linked_campaign_id IS NOT NULL AND c.id IS NULL;
```

---

## Priority E — Phase 5 Planning

### E1 — No Phase 5 planning document exists

**Issue:** Four services are listed as "Future" in the README (`map-svc`, `ai-svc`, `notify-svc`, `audit-svc`) and the mobile app is deferred. There is no Phase 5 planning document analogous to `SeedDataExpansion.md`.
**Recommended document structure:**

- `map-svc` — annotation persistence, tile auth proxy, WMS/WFS bridge
- `ai-svc` — Claude/OpenAI/Ollama routing; stub endpoint spec for `POST /ai/scenario/generate` (already stubbed in frontend)
- `notify-svc` — alert webhook delivery, Slack/Teams integration, user notification preferences
- `audit-svc` — separate immutable audit store (currently audit_log is in the main DB; dedicated service enables forwarding to SIEM)
- Mobile app — React Native scope, offline map requirements, authentication flow

### E2 — `ai-svc` stub endpoint not documented anywhere

**File:** [copilot.md:57-60](copilot.md) (Session 1)
**Issue:** The frontend's "Generate with AI" button calls `POST /ai/scenario/generate`. The expected request/response schema is not documented. When `ai-svc` is eventually built, the endpoint must match what the frontend already expects.
**Fix:** Add `ai-svc` endpoint spec to the Phase 5 planning doc (or `buildsheet.md §4`) before implementation begins.

---

## Priority F — Minor / Housekeeping

### F1 — `make db-migrate` description is misleading

**File:** [Makefile:100-103](Makefile) (`## db-migrate: Run database migrations` comment)
Since it only runs a single file, rename the comment or add a `## NOTE: runs 001_schema.sql only` warning so developers don't rely on it for applying incremental migrations.

### F2 — `SeedDataExpansion.md` implementation order was reversed from plan

**File:** [SeedDataExpansion.md:480-483](SeedDataExpansion.md)
The plan specified Equipment first (019), then Econ (017), then InfoOps (018). Actual implementation order was 017 → 018 → 019. Update §"Implementation Order" to reflect what was done, so the document remains accurate as a historical record.

### F3 — README Quick Start missing Grafana/Prometheus/Jaeger URLs

**File:** [README.md:238-248](README.md)
The "Open the app" table lists 4 URLs (frontend, Keycloak, Elasticsearch, Grafana, Prometheus, Jaeger). Grafana, Prometheus, and Jaeger were added in Session 18 and are in the table. However, the `make dev` description (§1) doesn't mention that it also starts the observability stack. Add one line noting that Prometheus/Grafana/Jaeger are included.

### F4 — Buildsheet §11.4 observability stack incomplete

**File:** [buildsheet.md:1303-1311](buildsheet.md)
Logs section says "Fluentd → Elasticsearch → Kibana" but no Fluentd or Kibana is deployed. The actual observability stack is Prometheus + Grafana + Jaeger (added Session 18). Update to reflect reality.

### F5 — Buildsheet §5.1 `equipment_catalog` schema missing `in_service_year`

**File:** [buildsheet.md:537-544](buildsheet.md)
The buildsheet schema for `equipment_catalog` shows no `in_service_year` column, but `019_equipment_catalog_seed.sql` inserts `in_service_year` values into every row. The actual schema (in `001_schema.sql`) either has this column or the inserts have been failing silently. Verify and sync.

### F6 — Buildsheet lists `SMALL_ARMS` as an equipment category; `IFV` and `HELICOPTER` are missing

**File:** [buildsheet.md:539](buildsheet.md)
The `equipment_catalog.category` comment says `-- ARMOR, AIRCRAFT, NAVAL, ARTILLERY, MISSILE, SMALL_ARMS`. Actual categories in 019 are `ARMOR, IFV, AIRCRAFT, HELICOPTER, NAVAL, MISSILE, ARTILLERY`. `SMALL_ARMS` is in the buildsheet but not seeded; `IFV` and `HELICOPTER` are seeded but not in the buildsheet.

---

## Summary Table

| ID | Priority | Area | Effort |
| -- | -------- | ---- | ------ |
| A1 | 🔴 High | Makefile `db-migrate` only runs one script | Small |
| A2 | 🔴 High | CI matrix missing 13 services | Medium |
| A3 | 🔴 High | Archival functions never called | Medium |
| ~~A4~~ | ~~🟠 Med-High~~ | ~~ETH FK gap in 017 seed~~ | ✅ ETH already in 002 |
| A5 | 🟠 Med-High | Kafka unusable (no ZooKeeper, no consumers) | Medium |
| B1 | 🟠 Medium | `agd-shared` not actually adopted by services | Large |
| B2 | 🟠 Medium | No API gateway in actual deployment | Large |
| B3 | 🟠 Medium | Keycloak realm not auto-provisioned | Medium |
| C1 | 🟡 Low-Med | Buildsheet service inventory 7 services short | Small |
| C2 | 🟡 Low | Buildsheet sim-engine still marked `[ ]` | Tiny |
| C3 | 🟡 Low | Buildsheet frontend stack (Cesium/socket.io wrong) | Small |
| C4 | 🟡 Low | README headers stale (Phase 4 In Progress) | Tiny |
| C5 | 🟡 Low | SeedDataExpansion.md checklist not updated | Tiny |
| C6 | 🟡 Low | copilot.md Session 18 wrong session number | Tiny |
| C7 | 🟡 Low | status-matrix.md missing Sessions 19–22 | Small |
| D1 | 🟠 Medium | 15 countries missing economic indicators | Medium |
| D2 | 🟡 Low | Multi-origin platforms single-country attributed | Small |
| D3 | 🟡 Low | db-seed-sanity.sql only checks equipment_catalog | Small |
| E1 | 🟠 Medium | No Phase 5 planning document | Medium |
| E2 | 🟡 Low | ai-svc stub endpoint spec not documented | Small |
| F1–F6 | 🟢 Low | Minor housekeeping / schema sync | Tiny each |

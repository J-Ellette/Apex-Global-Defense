# AGD Implementation Status Matrix

Maps every buildsheet deliverable to its implementation files and test evidence.
Status tags: `complete` | `prototype` | `deferred` | `future`

---

## Phase 1 — MVP

| Deliverable | Status | Implementation Files | Tests |
|------------|--------|---------------------|-------|
| Auth service (Go/JWT + RBAC + classification) | `complete` | `services/auth-svc/main.go`, `internal/` | `services/auth-svc/internal/**/*_test.go` |
| Order of Battle CRUD (50-nation seed) | `complete` | `services/oob-svc/main.go`, `internal/` | `services/oob-svc/internal/**/*_test.go` |
| Interactive globe (MapLibre GL) | `complete` | `frontend/src/modules/map/` | — |
| Self-hosted tile server | `complete` | `docker-compose.dev.yml` (mbtiles-server) | — |
| Scenario management | `complete` | `services/oob-svc/internal/` | — |
| AI config UI | `complete` | `frontend/src/modules/admin/AdminPage.tsx` | — |
| Audit logging | `complete` | `services/oob-svc/`, `services/auth-svc/` | — |
| Keycloak OIDC integration | `complete` | `keycloak/`, `services/auth-svc/` | — |

---

## Phase 2 — Simulation Core

| Deliverable | Status | Implementation Files | Tests |
|------------|--------|---------------------|-------|
| Sim orchestrator (FastAPI, turn/real-time/MC) | `complete` | `services/sim-orchestrator/main.py`, `app/` | `services/sim-orchestrator/tests/` |
| Sim engine gRPC scaffold (Rust/tonic) | `prototype` | `services/sim-engine/src/` | — |
| gRPC integration path + fallback | `complete` | `services/sim-orchestrator/app/routers/scenarios.py` | `services/sim-orchestrator/tests/test_runs.py` |
| Logistics & attrition model | `complete` | `services/sim-orchestrator/app/engine/stub.py` | `services/sim-orchestrator/tests/` |
| WebSocket collaboration hub | `complete` | `services/collab-svc/main.go` | — |
| Monte Carlo result panel (frontend) | `complete` | `frontend/src/modules/simulation/SimulationPage.tsx` | — |
| After-action report | `complete` | `services/sim-orchestrator/app/engine/stub.py` | — |
| AI-assisted scenario builder | `prototype` | `frontend/src/modules/simulation/` (modal stub) | — |

---

## Phase 3 — Domain Expansion

| Deliverable | Status | Implementation Files | Tests |
|------------|--------|---------------------|-------|
| Cyber ops (ATT&CK, infra graph, attack planner) | `complete` | `services/cyber-svc/` | `services/cyber-svc/tests/` |
| STIX/TAXII consumer | `complete` | `services/cyber-svc/app/routers/taxii.py` | `services/cyber-svc/tests/` |
| CBRN dispersion (Gaussian plume) | `complete` | `services/cbrn-svc/app/engine/plume.py` | `services/cbrn-svc/tests/` |
| Asymmetric / IED / COIN module | `complete` | `services/asym-svc/` | `services/asym-svc/tests/` |
| Terror response planning | `complete` | `services/terror-svc/` | `services/terror-svc/tests/` |
| Intel NER + PMESII threat assessment | `complete` | `services/intel-svc/app/engine/` | `services/intel-svc/tests/` |
| OSINT ingestion (ACLED, UCDP, RSS) | `complete` | `services/intel-svc/app/routers/osint.py` | `services/intel-svc/tests/` |
| pgvector semantic search | `complete` | `services/intel-svc/app/routers/search.py` | — |
| Civilian impact (haversine) | `complete` | `services/civilian-svc/app/engine/impact.py` | `services/civilian-svc/tests/` |
| Classification hardening (RLS) | `complete` | `db/init/011_classification_hardening.sql` | — |

---

## Phase 4 — Enterprise

| Deliverable | Status | Implementation Files | Tests |
|------------|--------|---------------------|-------|
| Auto-report generation (SITREP/INTSUM/CONOPS) | `complete` | `services/reporting-svc/` | `services/reporting-svc/tests/` |
| Economic warfare module | `complete` | `services/econ-svc/` | `services/econ-svc/tests/` |
| Information operations / disinfo tracking | `complete` | `services/infoops-svc/` | `services/infoops-svc/tests/` |
| GIS export (GeoJSON/KML, ArcGIS, Google Earth) | `complete` | `services/gis-export-svc/` | `services/gis-export-svc/tests/` |
| Training mode (exercises, injects, scoring) | `complete` | `services/training-svc/` | `services/training-svc/tests/` |
| Air-gap deployment (Helm chart, scripts) | `complete` | `helm/agd/`, `scripts/airgap-*.sh` | — |
| FedRAMP controls documentation | `complete` | `docs/fedramp/` | — |

---

## Improvements Roadmap

| Priority | Deliverable | Status | Implementation Files |
|---------|------------|--------|---------------------|
| A | Sim engine fidelity (combat model, deterministic resolver, MC, logistics, checkpointing) | `complete` | `services/sim-orchestrator/app/engine/stub.py`, `services/sim-engine/` |
| A | Performance hardening + parallel MC executor (ProcessPoolExecutor) | `complete` | `services/sim-orchestrator/app/engine/stub.py` (run_monte_carlo, _mc_trial) |
| B | CI/CD — stale service matrix fix | `complete` | `.github/workflows/ci.yml`, `Makefile` |
| B | CI/CD — docker-compose.test.yml integration harness | `complete` | `docker-compose.test.yml` |
| B | CI/CD — matrix multi-service image publishing | `complete` | `.github/workflows/ci.yml` (build-images job) |
| B | CI/CD — repo guard check | `complete` | `Makefile` (guard-services), `ci.yml` |
| C | Health endpoint surfaces engine mode | `complete` | `services/sim-orchestrator/main.py` |
| C | Explicit fallback policy (dev: stub, prod: fail-closed) | `complete` | `services/sim-orchestrator/app/routers/scenarios.py` |
| C | Migration smoke validation | `complete` | `scripts/db-migrate-smoke.sh`, `.github/workflows/ci.yml` (migrate-smoke job) |
| C | DB dev-fallback documentation (TimescaleDB/pgvector) | `complete` | `docs/db-dev-fallback.md` |
| D | `.env.example` templates (root + frontend) | `complete` | `.env.example`, `frontend/.env.example` |
| D | Env-var-driven secrets in docker-compose.dev.yml | `complete` | `docker-compose.dev.yml` |
| D | CI secret scanning (gitleaks) | `complete` | `.github/workflows/ci.yml` (secret-scan job) |
| D | Artifact provenance/signing (build attestation) | `complete` | `.github/workflows/ci.yml` (build-images job, attest-build-provenance step) |
| D | RLS classification tier testing (all clearance levels) | `complete` | `services/agd-shared/tests/test_classification_tiers.py` |
| E | Shared Python package (auth/classification/errors) | `complete` | `services/agd-shared/` |
| E | SemVer contract governance, protobuf compat checks | `complete` | `docs/contract-governance.md`, `buf.yaml` |
| F | OpenTelemetry SDK + FastAPI auto-instrumentation | `complete` | `services/sim-orchestrator/main.py` |
| F | Prometheus + Grafana + Jaeger observability stack | `complete` | `docker-compose.dev.yml`, `monitoring/` |
| F | Grafana dashboard (sim latency, error rate, event throughput) | `complete` | `monitoring/grafana/dashboards/sim-orchestrator.json` |
| F | Incident runbooks | `complete` | `docs/runbooks/` |
| G | Service-scoped make targets (svc-test, svc-lint) | `complete` | `Makefile` |
| G | One-command smoke script | `complete` | `scripts/smoke-test.sh` |
| G | Docs-status matrix | `complete` | `docs/status-matrix.md` (this file) |

---

## Database Schema Inventory

| File | Tables | Status |
|------|--------|--------|
| `db/init/001_schema.sql` | countries, military_units, equipment, scenarios, simulation_runs, sim_events, audit_log, intel_items | `complete` |
| `db/init/002_seed_countries.sql` | (seed data) | `complete` |
| `db/init/003_cyber_schema.sql` | cyber_infra_nodes, cyber_infra_edges, cyber_attacks | `complete` |
| `db/init/004_cbrn_schema.sql` | cbrn_releases, cbrn_simulations | `complete` |
| `db/init/005_asym_schema.sql` | asym_cells, asym_cell_links, asym_ied_incidents | `complete` |
| `db/init/006_terror_schema.sql` | terror_sites, terror_threat_scenarios, terror_response_plans | `complete` |
| `db/init/007_intel_schema.sql` | intel_threat_assessments, osint_ingestion_jobs | `complete` |
| `db/init/008_civilian_schema.sql` | civilian_population_zones, civilian_impact_assessments, civilian_refugee_flows, civilian_humanitarian_corridors | `complete` |
| `db/init/009_stix_schema.sql` | stix_indicators | `complete` |
| `db/init/010_reporting_schema.sql` | reports | `complete` |
| `db/init/011_classification_hardening.sql` | (RLS policies, agd_visible_classifications helper) | `complete` |
| `db/init/012_econ_schema.sql` | econ_sanction_targets, econ_trade_routes, econ_impact_assessments, econ_indicators | `complete` |
| `db/init/013_infoops_schema.sql` | infoops_narrative_threats, infoops_influence_campaigns, infoops_disinfo_indicators, infoops_attribution_assessments | `complete` |
| `db/init/014_gis_export_schema.sql` | gis_integrations | `complete` |
| `db/init/015_training_schema.sql` | training_exercises, training_injects, training_objectives | `complete` |

---

*Last updated: Session 17 — 2026-02-26 | UNCLASSIFIED*

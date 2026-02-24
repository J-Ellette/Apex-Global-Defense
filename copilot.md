# AGD Copilot Progress Log

**Agent:** GitHub Copilot Coding Agent  
**Repository:** Apex Global Defense (AGD)  
**Reference:** [buildsheet.md](./buildsheet.md)

---

## What Was Already Done (Phase 1 — MVP)

All Phase 1 checklist items were complete when this agent session started:

- [x] Project scaffold: monorepo, CI/CD, dev Docker Compose
- [x] Auth service (`services/auth-svc`) — Go, JWT + RBAC + classification, Keycloak integration
- [x] PostgreSQL + PostGIS schema (`db/init/001_schema.sql`) — countries, units, equipment, scenarios, simulation_runs, audit_log, intel_items
- [x] OOB service (`services/oob-svc`) — Go, full CRUD API, 50-nation seed data
- [x] Map frontend (`frontend/src/modules/map/`) — MapLibre GL globe, LayerPanel, AnnotationToolbar
- [x] Self-hosted tile server — mbtiles-server in docker-compose, `tiles/` directory
- [x] Scenario management — create, save, branch (oob-svc CRUD + SimulationPage UI)
- [x] AI config UI — AdminPage with provider selection, API key entry, fallback toggle
- [x] Basic audit logging — oob-svc write middleware + auth-svc login/logout

---

## Session 1 — Phase 2 Start (2026-02-24)

### Goal
Begin Phase 2: Functional conventional warfare simulation engine. Work from the top of the buildsheet Phase 2 checklist to the bottom.

### What I Did This Session

- [x] Created `services/sim-orchestrator/` — Python/FastAPI simulation lifecycle service
  - Full REST API: start runs, pause/resume, step (turn-based), events, after-action report
  - PostgreSQL-backed: reads `scenarios`, writes `simulation_runs` + `sim_events`
  - Stub engine generates realistic sim events (UNIT_MOVE, ENGAGEMENT, CASUALTY, OBJECTIVE_CAPTURED)
  - Monte Carlo stub: runs N simulations and returns probability distributions
  - JWT auth middleware (validates same JWTs as auth-svc)
  - `/health` endpoint for k8s readiness probe
  - `Dockerfile` + `requirements.txt`

- [x] Created `services/collab-svc/` — Go WebSocket collaboration relay
  - WebSocket hub: scenario-scoped rooms, fan-out relay
  - JWT validation on WS upgrade
  - Message types: `cursor:move`, `annotation:add`, `annotation:sync`, `sim:event`, `alert`
  - Redis pub/sub bridge: subscribes to `sim:{run_id}` and fans out to connected clients
  - Graceful shutdown, structured zap logging
  - `Dockerfile` + `go.mod`

- [x] Enhanced `frontend/src/modules/simulation/SimulationPage.tsx`
  - Added **Turn-based / Real-time / Monte Carlo** sim run launcher
  - `SimRunModal` — configure mode, duration, fog-of-war, weather, number of MC runs
  - `SimRunPanel` — live status display, step/pause/resume controls, event feed
  - Monte Carlo results panel — probability outcomes, casualty distributions
  - After-action report section

- [x] Added AI-assisted scenario builder
  - "Generate with AI" button in New Scenario modal
  - `AIScenarioBuilderModal` — natural language → ScenarioConfig
  - Calls `POST /ai/scenario/generate` (stub pending `ai-svc` implementation)

- [x] Added sim run API types to `frontend/src/shared/api/types/`
- [x] Added sim run API endpoints to `frontend/src/shared/api/endpoints.ts`
- [x] Updated `docker-compose.dev.yml` — added `sim-orchestrator` and `collab-svc` services
- [x] Updated `buildsheet.md` Phase 2 checklist to mark in-progress items

---

## Session 2 — Phase 2 Completion (2026-02-24)

### Goal
Complete the remaining Phase 2 item: Logistics and attrition model.

### What I Did This Session

- [x] **Logistics & attrition model — backend** (`services/sim-orchestrator/`)
  - Added `SupplyLevels`, `ForceSummary`, `LogisticsState`, `LogisticsSummary` Pydantic models to `app/models.py`
  - Added `RESUPPLY` event type to `EventType` enum
  - Added `generate_logistics_state()` to `app/engine/stub.py`
    - Derives per-force supply levels (ammo/fuel/rations) from accumulated events + weather + elapsed turns
    - Tracks RESUPPLY event restorations separately for BLUE vs RED forces
    - Computes personnel attrition (KIA/WIA) and equipment losses (armor, artillery, aircraft)
  - Updated `build_after_action_report()` to compute and embed `LogisticsSummary` in AAR
  - Added `RESUPPLY` payload generation in `generate_run_events()`
  - Added `GET /runs/{run_id}/logistics` → `LogisticsState` endpoint

- [x] **Logistics & attrition model — frontend** (`frontend/`)
  - Added `SupplyLevels`, `ForceSummary`, `LogisticsState`, `LogisticsSummary` types to `shared/api/types/simulation.ts`
  - Added `RESUPPLY` to `SimEventType`
  - Added `logistics_summary?: LogisticsSummary` field to `AfterActionReport`
  - Added `simApi.getLogistics()` to `shared/api/endpoints.ts`
  - Added `LogisticsPanel` component to `SimulationPage.tsx`
    - Per-force supply bars (ammo/fuel/rations) with color-coded depletion indicators
    - Strength percentage with conditional coloring (green/yellow/red)
    - KIA/WIA counts
    - Equipment loss badges (armor, artillery, aircraft)
  - Added **📦 Logistics** toggle button to `SimRunPanel` (auto-refreshes during live runs)
  - Added `logistics_summary` final state section to `AfterActionReportPanel`
  - Added RESUPPLY event color to `EventChip`

- [x] Added `test_get_logistics_not_found` and `test_get_logistics_returns_state` tests

### Stopping Point

Phase 2 is now **complete**. All checklist items marked done in `buildsheet.md`.

### What's Next (Session 3 — Phase 3)

- [ ] Cyber module (ATT&CK mapping, infrastructure graph)
- [ ] CBRN dispersion modeling (HYSPLIT integration)
- [ ] Insurgent/asymmetric module (cell structure, IED threat)
- [ ] Terror response planning module
- [ ] AI-assisted intel analysis (entity extraction, threat assessment)
- [ ] OSINT ingestion pipeline (ACLED, UCDP, RSS feeds)

---

## Session 3 — Phase 3 Start (2026-02-24)

### Goal
Begin Phase 3: Domain Expansion. First item: Cyber module.

### What I Did This Session

- [x] **Cyber module — backend** (`services/cyber-svc/`)
  - Python/FastAPI service with JWT auth (same pattern as sim-orchestrator)
  - **ATT&CK Techniques catalog** (`app/data/attack_techniques.py`) — 30 representative techniques across all 14 enterprise tactics (Reconnaissance → Impact)
  - `GET /cyber/techniques` — list with filtering by tactic, platform, severity, full-text search
  - `GET /cyber/techniques/{id}` — single technique detail
  - **Infrastructure Graph** (`app/routers/infrastructure.py`) — DB-backed node/edge CRUD
    - `GET /cyber/infrastructure` — full graph (nodes + edges), optionally scoped to scenario
    - `POST /cyber/infrastructure/nodes` — add node (HOST, SERVER, ROUTER, FIREWALL, ICS, CLOUD, SATELLITE, IOT, DATABASE)
    - `PUT /cyber/infrastructure/nodes/{id}` — update node
    - `DELETE /cyber/infrastructure/nodes/{id}` — remove node (cascades edges)
    - `POST /cyber/infrastructure/edges` — add connection
    - `DELETE /cyber/infrastructure/edges/{id}` — remove connection
  - **Cyber Attacks** (`app/routers/attacks.py`) — ATT&CK-mapped attack planning + simulation
    - `GET /cyber/attacks` — list attacks with status/scenario filters
    - `POST /cyber/attacks` — plan an attack (validates technique, estimates success probability from severity + target criticality)
    - `GET /cyber/attacks/{id}` — get attack detail
    - `POST /cyber/attacks/{id}/simulate` — Monte Carlo-style outcome simulation (defender skill + network hardening modifiers → success/detection/damage/spread)
  - `Dockerfile` + `requirements.txt`
  - 13 unit tests (conftest mocks asyncpg pool, dependency_overrides for JWT)

- [x] **DB schema** (`db/init/003_cyber_schema.sql`)
  - `cyber_infra_nodes` — infrastructure graph nodes with criticality, tags, metadata
  - `cyber_infra_edges` — connections with type, protocol, port
  - `cyber_attacks` — planned/executed attacks with technique_id, target node, result JSONB

- [x] **Cyber module — frontend** (`frontend/src/modules/cyber/CyberPage.tsx`)
  - **ATT&CK Techniques tab** — searchable/filterable table with detail side panel (description, mitigations, link to attack.mitre.org)
  - **Infrastructure Graph tab** — node cards (typed icons, criticality colors) + edge connection table; Add Node / Add Connection forms with validation
  - **Attack Planner tab** — plan attacks by selecting technique + threat actor + target node; per-attack simulate button with defender skill / network hardening sliders; result card (success/failure, damage level, detection narrative)

- [x] Added `cyberClient.ts` — Axios client for cyber-svc (port 8086, bearer token auth)
- [x] Added `frontend/src/shared/api/types/cyber.ts` — full TypeScript type definitions
- [x] Added `cyberApi` to `endpoints.ts` — all cyber operations
- [x] Updated `frontend/src/app/router.tsx` — added `/cyber` route
- [x] Updated `frontend/src/modules/dashboard/DashboardPage.tsx` — added Cyber Operations module card
- [x] Updated `docker-compose.dev.yml` — added `cyber-svc` (port 8086) + `VITE_CYBER_API_URL`
- [x] Updated `buildsheet.md` Phase 3 checklist — Cyber module marked done

### Stopping Point

Cyber module (Phase 3, item 1) is **complete**. Moving to CBRN next.

### What's Next (Session 4 — Phase 3 continued)

- [ ] CBRN dispersion modeling (HYSPLIT integration)
- [ ] Insurgent/asymmetric module (cell structure, IED threat)
- [ ] Terror response planning module
- [ ] AI-assisted intel analysis (entity extraction, threat assessment)
- [ ] OSINT ingestion pipeline (ACLED, UCDP, RSS feeds)

---

## Session 4 — Phase 3 Continued: CBRN Module (2026-02-24)

### Goal
Implement CBRN dispersion modeling (Phase 3, item 2): agent catalog, release planning, Gaussian plume dispersion simulation, casualty estimation, and frontend UI.

### What I Did This Session

- [x] **CBRN module — backend** (`services/cbrn-svc/`)
  - Python/FastAPI service on port 8087 (same JWT auth pattern as cyber-svc)
  - **Agent Catalog** (`app/data/agents.py`) — 11 representative agents across all 4 CBRN categories:
    - **Chemical**: VX (nerve), GB/Sarin (nerve), HD/Mustard Gas (blister), Chlorine (choking), HCN (blood)
    - **Biological**: Anthrax spores, Botulinum toxin type A, Plague (Y. pestis)
    - **Radiological**: Cesium-137 (dirty bomb), Cobalt-60
    - **Nuclear**: IND 10 kT, IND 100 kT
    - Each agent includes: casualty thresholds (LCt50, ICt50, IDLH), physical properties, half-life, NATO code, protective action guidance
  - **Gaussian Plume Engine** (`app/engine/plume.py`) — HYSPLIT-inspired dispersion model:
    - Pasquill-Gifford stability classes A–F with proper σy/σz dispersion coefficients
    - Steady-state Gaussian plume equation with ground reflection and mixing layer
    - Atmospheric mixing layer reflection model
    - Plume contour polygon generation (isoline at lethal/incapacitating/IDLH thresholds)
    - `_latlon_offset()` — converts (x_m, y_m) plume coordinates to WGS-84 lat/lon
    - Casualty estimation: area × population density × affected fraction
    - Fallback hazard zone for bio/nuclear agents without Ct thresholds
  - **Release CRUD** (`app/routers/releases.py`) — DB-backed release event management
    - `GET /cbrn/releases` — list with optional scenario_id filter
    - `POST /cbrn/releases` — create release (validates agent, stores met conditions as JSONB)
    - `GET /cbrn/releases/{id}` — get release
    - `DELETE /cbrn/releases/{id}` — delete release + cascade simulations
    - `POST /cbrn/releases/{id}/simulate` — run plume model, persist result, return DispersionSimulation
    - `GET /cbrn/releases/{id}/simulation` — retrieve cached simulation result
  - **Agent endpoints** (`app/routers/agents.py`)
    - `GET /cbrn/agents` — list with category + full-text search filters
    - `GET /cbrn/agents/{id}` — get single agent
  - `Dockerfile` + `requirements.txt` (fastapi, asyncpg, python-jose, pydantic, numpy)
  - 15 unit tests — all passing

- [x] **DB schema** (`db/init/004_cbrn_schema.sql`)
  - `cbrn_releases` — release events with agent_id, met JSONB, population density
  - `cbrn_simulations` — simulation results (JSONB) with unique constraint on release_id (upsert on re-simulate)

- [x] **CBRN module — frontend** (`frontend/src/modules/cbrn/CBRNPage.tsx`)
  - **Agent Catalog tab** — searchable/filterable card list; detail side panel with casualty thresholds (LCt50/ICt50/IDLH/LD50), NATO code, protective action, map color
  - **Release Planner tab** — create release form with full met conditions input (wind speed/direction, stability class A–F, mixing height, temperature, humidity); release card list with 🌬️ Simulate button
  - **Dispersion Results tab** — run dispersion model; display plume metrics (max downwind/crosswind km, area km², estimated casualties); hazard zone cards (Lethal/Injury/IDLH) with estimated casualties; met summary; plume contour polygon summary; protective actions panel

- [x] Added `cbrnClient.ts` — Axios client for cbrn-svc (port 8087, bearer token auth)
- [x] Added `frontend/src/shared/api/types/cbrn.ts` — full TypeScript type definitions
- [x] Added `cbrnApi` to `endpoints.ts` — all CBRN operations
- [x] Updated `frontend/src/shared/api/types/index.ts` — re-exports cbrn types
- [x] Updated `frontend/src/app/router.tsx` — added `/cbrn` route
- [x] Updated `frontend/src/modules/dashboard/DashboardPage.tsx` — added CBRN Operations module card
- [x] Updated `docker-compose.dev.yml` — added `cbrn-svc` (port 8087) + `VITE_CBRN_API_URL`
- [x] Updated `buildsheet.md` Phase 3 checklist — CBRN dispersion + frontend marked done

### Stopping Point

CBRN module (Phase 3, items 2 + frontend) is **complete**. Next: Insurgent/asymmetric module.

### What's Next (Session 5 — Phase 3 continued)

- [ ] Insurgent/asymmetric module (cell structure, IED threat)
- [ ] Terror response planning module
- [ ] AI-assisted intel analysis (entity extraction, threat assessment)
- [ ] OSINT ingestion pipeline (ACLED, UCDP, RSS feeds)
- [ ] Elasticsearch + semantic search (pgvector)
- [ ] Civilian impact overlays (population, refugee modeling)

---

## Architecture Notes (for future sessions)

| Service | Port (dev) | Language | Status |
|---------|-----------|----------|--------|
| auth-svc | 8082 | Go | ✅ Complete |
| oob-svc | 8083 | Go | ✅ Complete |
| sim-orchestrator | 8085 | Python/FastAPI | ✅ Session 1–2 |
| collab-svc | 8084 | Go | ✅ Session 1 |
| cyber-svc | 8086 | Python/FastAPI | ✅ Session 3 |
| cbrn-svc | 8087 | Python/FastAPI | ✅ Session 4 |
| map-svc | — | Go | ⏳ Future |
| intel-svc | — | Python | ⏳ Future |
| ai-svc | — | Python | ⏳ Future |
| reporting-svc | — | Python | ⏳ Future |
| sim-engine | — | C++/Rust | ⏳ Future |

### Key Integration Points

- **JWT secret**: `dev-secret-change-in-prod` — shared across all services
- **Database**: `postgres://agd:devpass@postgres:5432/agd_dev`
- **Redis**: `redis://redis:6379`
- **Collab WS URL**: `ws://localhost:8084` (consumed by frontend `VITE_WS_URL`)
- **Sim orchestrator**: `http://localhost:8085/api/v1` (consumed by frontend `VITE_SIM_API_URL`)
- **Cyber svc**: `http://localhost:8086/api/v1` (consumed by frontend `VITE_CYBER_API_URL`)
- **CBRN svc**: `http://localhost:8087/api/v1` (consumed by frontend `VITE_CBRN_API_URL`)

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

## Architecture Notes (for future sessions)

| Service | Port (dev) | Language | Status |
|---------|-----------|----------|--------|
| auth-svc | 8082 | Go | ✅ Complete |
| oob-svc | 8083 | Go | ✅ Complete |
| sim-orchestrator | 8085 | Python/FastAPI | ✅ Session 1–2 |
| collab-svc | 8084 | Go | ✅ Session 1 |
| cyber-svc | 8086 | Python/FastAPI | ✅ Session 3 |
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
- **Sim orchestrator**: `http://localhost:8085/api/v1` (to be added to frontend env)

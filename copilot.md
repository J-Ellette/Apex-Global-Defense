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

## Session 5 — Phase 3 Asymmetric Module (2026-02-24)

### Goal
Implement the insurgent/asymmetric module: cell structure modeling, IED threat tracking, and COIN planning.

### What I Did This Session

- [x] **Asymmetric module — backend** (`services/asym-svc/`)
  - Python/FastAPI service on port 8088 (same JWT auth pattern as cbrn-svc)
  - **Cell Function Catalog** (`app/data/cell_types.py`) — 10 cell type entries across all operational roles:
    - CMD (Command), OPS (Operations), LOG (Logistics), INT (Intelligence), FIN (Finance)
    - REC (Recruitment), PROP (Propaganda), SFH (Safe House), MED (Medical), TECH (Technical/IED)
    - Each entry includes: detection difficulty, interdiction priority, typical size range, icon, color
  - **IED Type Catalog** (`app/data/ied_types.py`) — 9 IED types across all threat categories:
    - VBIED, SVBIED (vehicle-borne), PBIED (person-borne/suicide vest)
    - PLACED_IED, COMMAND_WIRE, RCIED, PRESSURE_PLATE (placed/triggered variants)
    - EFP (explosively formed penetrator, armor-defeating)
    - DRONE_IED (emerging aerial IED threat)
    - Each entry includes: yield, lethal/injury/blast radius, avg casualties, countermeasures
  - **Cell CRUD** (`app/routers/cells.py`)
    - `GET /asym/cells` — list with scenario_id / status filters
    - `POST /asym/cells` — create cell
    - `GET /asym/cells/{id}` — get cell
    - `PUT /asym/cells/{id}` — update cell
    - `DELETE /asym/cells/{id}` — cascade-deletes links
    - `POST /asym/cell-links` — create inter-cell link
    - `DELETE /asym/cell-links/{id}` — delete link
    - `GET /asym/network` — return full cell graph (nodes + edges)
  - **IED Incident CRUD** (`app/routers/incidents.py`)
    - `GET /asym/ied-types` — list IED type catalog
    - `GET /asym/ied-types/{id}` — get single IED type
    - `GET /asym/incidents` — list with scenario_id / status filters
    - `POST /asym/incidents` — log new IED incident
    - `GET /asym/incidents/{id}` — get incident
    - `PUT /asym/incidents/{id}` — update incident (status, casualties, attribution)
    - `DELETE /asym/incidents/{id}` — delete incident
  - **Network Analysis** (`app/routers/analysis.py`)
    - `GET /asym/network/analysis` — full cell network analysis:
      - Degree centrality (normalized connectivity per node)
      - Betweenness centrality (Brandes algorithm, exact, no external dependencies)
      - Composite hub score (degree + betweenness + operational capability + function priority)
      - Per-cell interdiction value (1–10), interdiction recommendation text
      - Network density computation
      - COIN planning recommendations (decapitation, finance disruption, FININT, counter-radicalization)
  - `Dockerfile` + `requirements.txt`
  - 20 unit tests — all passing

- [x] **DB schema** (`db/init/005_asym_schema.sql`)
  - `asym_cells` — insurgent cell nodes with function, structure, status, location, capability assessments
  - `asym_cell_links` — cell network edges with link_type, strength, confidence
  - `asym_ied_incidents` — IED incidents with type, location, status, casualties, attribution

- [x] **Asymmetric module — frontend** (`frontend/src/modules/asym/AsymPage.tsx`)
  - **Cell Network tab** — cell list with function icons, status badges, capability metrics; add-cell modal with full field set
  - **IED Threats tab** — IED type catalog cards with detailed specs + countermeasures; incident log with casualties summary; log-incident modal
  - **COIN Planning tab** — on-demand network analysis; summary stats panel; prioritized COIN recommendations; interdiction priority ranking with hub score bars (red/yellow/green by score)

- [x] Added `asymClient.ts` — Axios client for asym-svc (port 8088, bearer token auth)
- [x] Added `frontend/src/shared/api/types/asym.ts` — full TypeScript type definitions
- [x] Added `asymApi` to `endpoints.ts` — all asymmetric operations
- [x] Updated `frontend/src/shared/api/types/index.ts` — re-exports asym types
- [x] Updated `frontend/src/app/router.tsx` — added `/asym` route
- [x] Updated `frontend/src/modules/dashboard/DashboardPage.tsx` — added Asymmetric/Insurgency module card
- [x] Updated `docker-compose.dev.yml` — added `asym-svc` (port 8088) + `VITE_ASYM_API_URL`
- [x] Updated `buildsheet.md` Phase 3 checklist — insurgent/asymmetric module marked done

### Stopping Point

Insurgent/asymmetric module (Phase 3, item 3) is **complete**. Next: Terror response planning module.

### What's Next (Session 6 — Phase 3 continued)

- [ ] Terror response planning module
- [ ] AI-assisted intel analysis (entity extraction, threat assessment)
- [ ] OSINT ingestion pipeline (ACLED, UCDP, RSS feeds)
- [ ] Elasticsearch + semantic search (pgvector)
- [ ] Civilian impact overlays (population, refugee modeling)

---

## Session 6 — Phase 3 Continued (2026-02-24)

### Goal
Implement the Terror Response Planning module (Phase 3, item 4).

### What I Did This Session

- [x] **Terror response planning module — backend** (`services/terror-svc/`)
  - **Attack type catalog** (`app/data/attack_types.py`) — 10 attack types with full metadata:
    - VRAM (Vehicle Ramming), ASHT (Active Shooter), SBOM (Suicide Bombing), HSTG (Hostage/Siege)
    - EXPL (Planted Explosive), CHEM (Chemical Attack), BIOL (Biological Attack)
    - CYBR (Cyber/Infrastructure), ASSN (Assassination), INFR (Infrastructure Attack)
    - Each: category, lethality range, typical perpetrators/targets, detection window, countermeasures, threat indicators
  - **Site CRUD** (`app/routers/sites.py`)
    - `GET /terror/sites` — list with scenario/status/site_type filters
    - `POST /terror/sites` — create site with auto-computed vulnerability score (1–10)
    - `GET /terror/sites/{id}` — get site
    - `PUT /terror/sites/{id}` — update site + recompute vulnerability score
    - `DELETE /terror/sites/{id}` — cascade-deletes scenarios and plans
    - Vulnerability score formula: 10 × (1 − mean security dimensions) × crowd density multiplier
    - 14 site types: TRANSPORT_HUB, STADIUM, GOVERNMENT_BUILDING, HOTEL, MARKET, HOUSE_OF_WORSHIP, SCHOOL, HOSPITAL, EMBASSY, CRITICAL_INFRASTRUCTURE, FINANCIAL_CENTER, MILITARY_BASE, ENTERTAINMENT_VENUE, SHOPPING_CENTER
  - **Threat Scenario CRUD** (`app/routers/scenarios.py`)
    - `GET /terror/attack-types` — list attack type catalog with optional category filter
    - `GET /terror/attack-types/{id}` — get single attack type
    - `GET /terror/threat-scenarios` — list with scenario/site/threat_level filters
    - `POST /terror/threat-scenarios` — log threat scenario for a site
    - `GET /terror/threat-scenarios/{id}` — get scenario
    - `PUT /terror/threat-scenarios/{id}` — update scenario
    - `DELETE /terror/threat-scenarios/{id}` — delete scenario
  - **Response Plan CRUD** (`app/routers/plans.py`)
    - `GET /terror/response-plans` — list with filters
    - `POST /terror/response-plans` — create multi-agency response plan
    - `GET /terror/response-plans/{id}` — get plan
    - `PUT /terror/response-plans/{id}` — update plan
    - `DELETE /terror/response-plans/{id}` — delete plan
    - Plans include: agency assignments (role: PRIMARY/SUPPORTING/NOTIFIED), evacuation routes, shelter capacity, ETA
  - **Vulnerability Analysis** (`app/routers/analysis.py`)
    - `GET /terror/sites/{id}/analysis` — full vulnerability analysis
    - Scores all 10 attack types against site using: lethality × vulnerability × site-type affinity × crowd factor
    - Site-type affinity map: each site type has specific high-risk attack vectors
    - Dimension-specific recommendations (physical_security, access_control, surveillance, emergency_response)
    - Attack-specific recommendations (VRAM → bollards, EXPL/SBOM → explosive detection, CHEM/BIOL → CBRN sensors)
  - `Dockerfile` + `requirements.txt`
  - 26 unit tests — all passing

- [x] **DB schema** (`db/init/006_terror_schema.sql`)
  - `terror_sites` — target sites with 4 security dimensions + computed vulnerability_score
  - `terror_threat_scenarios` — threat scenarios linking sites to attack types
  - `terror_response_plans` — multi-agency response plans with JSONB agencies/routes

- [x] **Terror module — frontend** (`frontend/src/modules/terror/TerrorPage.tsx`)
  - **Site Vulnerability tab** — site cards with vulnerability bars and dimension breakdowns; add site modal with slider-based security dimension scoring; site detail modal with vulnerability analysis and attack risk ranking
  - **Threat Scenarios tab** — attack type catalog cards (expandable: description, perpetrators, targets, indicators, countermeasures); active threat scenario log with threat level badges
  - **Response Planning tab** — response plan list with agency assignments and evacuation routes; multi-agency plan builder with agency role selection (PRIMARY/SUPPORTING/NOTIFIED)

- [x] Added `terrorClient.ts` — Axios client for terror-svc (port 8089, bearer token auth)
- [x] Added `frontend/src/shared/api/types/terror.ts` — full TypeScript type definitions
- [x] Added `terrorApi` to `endpoints.ts` — all terror response operations
- [x] Updated `frontend/src/shared/api/types/index.ts` — re-exports terror types
- [x] Updated `frontend/src/app/router.tsx` — added `/terror` route
- [x] Updated `frontend/src/modules/dashboard/DashboardPage.tsx` — added Terror Response module card
- [x] Updated `docker-compose.dev.yml` — added `terror-svc` (port 8089) + `VITE_TERROR_API_URL`
- [x] Updated `buildsheet.md` Phase 3 checklist — terror response planning module marked done

### Stopping Point

Terror response planning module (Phase 3, item 4) is **complete**. Next: AI-assisted intel analysis.

### What's Next (Session 7 — Phase 3 continued)

- [x] AI-assisted intel analysis (entity extraction, threat assessment)
- [x] OSINT ingestion pipeline (ACLED, UCDP, RSS feeds)
- [x] Elasticsearch + semantic search (pgvector)
- [ ] Civilian impact overlays (population, refugee modeling)

---

## Session 7 — Phase 3 Intel Items (2026-02-24)

### Goal
Complete Phase 3 intelligence items: AI-assisted intel analysis, OSINT ingestion pipeline, pgvector semantic search.

### What I Did This Session

- [x] **`services/intel-svc/`** — Python/FastAPI intelligence service (port 8090)
  - **Entity extraction engine** (`app/engine/extractor.py`)
    - Fully deterministic NLP using regex patterns and curated military keyword lists
    - Extracts: PERSON, ORGANIZATION, LOCATION, WEAPON, DATE, EVENT, VEHICLE, FACILITY
    - Supports: 35+ weapon keywords, 12 org patterns, military ranks/titles, Arabic names, patronymics
    - 12 location patterns including military map references (Hill 937, MGRS grids)
    - 14 event keywords (attack, airstrike, ambush, IED attack, VBIED, etc.)
    - Deduplication by (type, text) key; all confidences clamped 0–1
    - Air-gap first: zero ML model dependencies
  - **Threat assessment engine** (`app/engine/threat.py`)
    - Deterministic PMESII-PT/ASCOPE inspired weighted indicator matrix
    - 14 threat indicators (kinetic, intelligence, cyber, CBRN, destabilization, actor-specific)
    - Actor classification: state actors, terrorist organizations, cyber actors
    - Score modifiers: state actor +1.0, terrorist +1.5
    - Outputs: ThreatLevel enum (NEGLIGIBLE/LOW/MODERATE/HIGH/CRITICAL), score 0–10
    - Derives active ThreatVectors (MILITARY, TERRORIST, CYBER, CBRN, ECONOMIC, HYBRID)
    - Confidence score based on proportion of indicators with evidence
    - Protective action recommendations tailored to level and vectors
  - **OSINT ingestion adapters** (`app/engine/osint_adapters.py`)
    - `ACLEDAdapter`: ACLED API with fallback to 5 deterministic synthetic conflict events (Ukraine, Afghanistan, Syria, Mali, Iraq)
    - `UCDPAdapter`: UCDP GED API with synthetic fallback (Ethiopia Tigray, Mozambique Cabo Delgado)
    - `RSSAdapter`: feedparser-based generic adapter for Reuters/BBC/ReliefWeb with synthetic fallback
    - `run_ingestion()`: fetch → entity extract → DB INSERT with `ON CONFLICT DO NOTHING`
    - Adapter registry: `_init_registry()` initialized from service config
  - **Intel CRUD + search** (`app/routers/intel.py`)
    - `GET /intel` — list with source_type / classification filters
    - `POST /intel` — ingest item with optional auto entity extraction
    - `GET /intel/{id}` — get single item
    - `PUT /intel/{id}` — update title/content/classification/reliability/credibility
    - `DELETE /intel/{id}` — delete
    - `POST /intel/search` — full-text (PostgreSQL `to_tsvector`), geo (PostGIS `ST_DWithin`), date range
    - `POST /intel/semantic-search` — pgvector `<=>` cosine similarity (falls back to full-text when embedding model not available; production: swap in `embedding = await embed(query)`)
  - **Analysis endpoints** (`app/routers/analysis.py`)
    - `POST /intel/extract` — entity extraction on arbitrary text; optionally persists to item
    - `POST /intel/threat-assess` — threat assessment; optionally enriches context with referenced intel items
  - **OSINT pipeline endpoints** (`app/routers/osint.py`)
    - `GET /intel/osint/sources` — list adapters with DB-backed item counts
    - `POST /intel/osint/ingest` — trigger ingestion run (dry_run supported)
  - `Dockerfile` + `requirements.txt` (same stack as other Python services)
  - 27 unit tests — all passing

- [x] **DB schema** (`db/init/007_intel_schema.sql`)
  - `intel_threat_assessments` — stored threat assessment results with full indicator JSONB
  - `osint_ingestion_jobs` — ingestion job history / audit trail
  - `idx_intel_fts` — PostgreSQL GIN full-text search index on intel_items (supplements pgvector)

- [x] **Frontend** (`frontend/src/modules/intel/IntelPage.tsx`) — replaced stub with full module
  - **Intel Feed tab** — item cards with source type badge, classification, entity chips (color-coded by type), date, location, semantic embedding indicator; add item modal (all fields including NATO reliability/credibility); item detail modal with full entity breakdown
  - **Analysis tab** — Entity Extraction panel (paste text → NLP → grouped entity results by type with confidence %) and Threat Assessment panel (actor + target + context → indicator breakdown + score bar + vector tags + protective actions)
  - **OSINT Sources tab** — ACLED/UCDP/RSS source cards with item counts, last ingestion date, ingest trigger button, dry-run button, result summary
  - Search: full-text + source type filter; 🧠 Semantic button (calls semantic-search endpoint)

- [x] Added `intelClient.ts` — Axios client for intel-svc (port 8090, bearer token auth)
- [x] Added `frontend/src/shared/api/types/intel.ts` — full TypeScript type definitions
- [x] Added `intelApi` to `endpoints.ts` — all intel operations
- [x] Updated `frontend/src/shared/api/types/index.ts` — re-exports intel types
- [x] Updated `docker-compose.dev.yml` — added `intel-svc` (port 8090) + `VITE_INTEL_API_URL`
- [x] Updated `buildsheet.md` Phase 3 checklist — AI-assisted intel, OSINT pipeline, pgvector marked done

### Stopping Point

Three Phase 3 intel items are **complete**: AI-assisted intel analysis, OSINT ingestion pipeline (ACLED/UCDP/RSS), and pgvector semantic search.

### What's Next (Session 8 — Phase 3 final item)

- [ ] Civilian impact overlays (population, refugee modeling)
- [ ] Then Phase 4 items (multi-user collaboration, STIX/TAXII, auto-report generation, etc.)

---

## Session 8 — Phase 3 Completion (2026-02-24)

### Goal
Complete the final Phase 3 item: Civilian impact overlays (population, refugee modeling).

### What I Did This Session

- [x] **Civilian Impact Service — backend** (`services/civilian-svc/`)
  - Python/FastAPI service on port 8091
  - **Population zone CRUD** (`app/routers/population.py`)
    - `GET /civilian/population`, `POST /civilian/population`, `GET /civilian/population/{id}`, `DELETE /civilian/population/{id}`
    - 8 built-in seed zones when DB is empty: Baghdad, Kabul, Kyiv, Mariupol, Aleppo, Mogadishu, Khartoum, Bamako
  - **Civilian impact assessment** (`app/routers/impact.py`)
    - `POST /civilian/impact/assess` — runs deterministic model, stores result
    - `GET /civilian/impact/{run_id}` — retrieve stored assessment
  - **Refugee flows** (`app/routers/flows.py`)
    - Full CRUD; 5 seed flows (Ukraine→Poland, Syria→Turkey, Afghanistan→Pakistan, Somalia→Kenya, Sudan→Chad)
  - **Humanitarian corridors** (`app/routers/corridors.py`)
    - Full CRUD; 3 seed corridors; status: OPEN/RESTRICTED/CLOSED
  - **Deterministic impact engine** (`app/engine/impact.py`)
    - Haversine proximity model — only events within 3× zone radius affect zone
    - Per-event-type severity: CBRN_RELEASE (8.0) > AIRSTRIKE (2.5) > ENGAGEMENT (0.8)
    - Per-density-class multipliers: URBAN (1.0) > SUBURBAN (0.4) > RURAL (0.1) > SPARSE (0.02)
    - Wounded ≈ 2.5× casualties; impact_score 0–10; infrastructure_damage_pct 0–1
  - 23 unit tests — all passing
  - `Dockerfile` + `requirements.txt`

- [x] **DB schema** (`db/init/008_civilian_schema.sql`)
  - `civilian_population_zones` — zone data (id, scenario_id, name, country_code, lat/lon, radius_km, population, density_class)
  - `civilian_impact_assessments` — stored assessments with JSONB zone_impacts array
  - `civilian_refugee_flows` — displacement flows (origin/destination, status: PROJECTED/CONFIRMED/RESOLVED)
  - `civilian_humanitarian_corridors` — safe passage corridors (waypoints JSONB, status: OPEN/RESTRICTED/CLOSED)
  - Indexes on scenario_id, status, run_id

- [x] **Frontend** (`frontend/src/modules/civilian/CivilianPage.tsx`) — full 4-tab module
  - **Population Zones tab** — table with colored density badges (URBAN=sky, SUBURBAN=yellow, RURAL=green, SPARSE=gray), delete per row, AddZoneModal with full validation
  - **Impact Assessment tab** — run ID input → assess → summary cards (casualties/wounded/displaced) + per-zone table with color-coded impact score progress bars (green ≤3, yellow ≤6, red >6)
  - **Refugee Flows tab** — table with inline status dropdowns + Save + Delete per row; AddFlowModal
  - **Humanitarian Corridors tab** — card grid with inline status select + Save + Delete; AddCorridorModal (lat,lon textarea parsing)

- [x] Added `civilianClient.ts` — Axios client for civilian-svc (port 8091, bearer token auth)
- [x] Added `frontend/src/shared/api/types/civilian.ts` — full TypeScript type definitions
- [x] Added `civilianApi` to `endpoints.ts` — all civilian operations
- [x] Updated `frontend/src/shared/api/types/index.ts` — re-exports civilian types
- [x] Updated `frontend/src/app/router.tsx` — added `/civilian` route
- [x] Updated `frontend/src/modules/dashboard/DashboardPage.tsx` — added 👥 Civilian Impact card
- [x] Updated `frontend/src/modules/map/hooks/useMapLayers.ts` — added 3 new overlay layers: Population Density, Refugee Flows, Humanitarian Corridors
- [x] Updated `frontend/src/modules/map/MapCanvas.tsx` — renders population zones as circles, refugee flows as dashed amber lines, corridors as colored status lines; lazy-fetches data when layer is toggled on
- [x] Updated `docker-compose.dev.yml` — added `civilian-svc` (port 8091) + `VITE_CIVILIAN_API_URL`
- [x] Updated `buildsheet.md` Phase 3 checklist — Civilian impact overlays marked done
- [x] Updated `copilot.md` — added Session 8 entry

### Stopping Point

Phase 3 is now **100% complete**. All Phase 3 items are done.

### What's Next (Session 9 — Phase 4 start)

Phase 4 — Enterprise items, starting from the top:
- [ ] Multi-user collaboration with role-based map control
- [ ] Commercial intel feed integration (Recorded Future, Maxar, Jane's)
- [ ] STIX/TAXII cyber threat feed consumer
- [ ] Auto-report generation (SITREP, INTSUM, CONOPS briefs)
- [ ] Classification handling hardening (row-level security, labels)
- [ ] FedRAMP documentation and controls
- [ ] Air-gap deployment package (Helm chart, offline tile pack, Ollama models)
- [ ] Mobile app (React Native, read-only, offline maps)
- [ ] Economic warfare module
- [ ] Information operations / disinformation tracking
- [ ] API for external system integration (ArcGIS, Google Earth)
- [ ] Training mode (exercise inject system, scoring)

---

## Session 9 — Phase 4 Start (2026-02-24)

### Goal
Begin Phase 4 (Enterprise): implement the first four items from the top of the Phase 4 buildsheet checklist.

### What I Did This Session

#### Item 1: Multi-user collaboration with role-based map control ✅

- [x] **`auth-svc/internal/models/models.go`** — added `PermMapControl Permission = "map:control"` permission
  - Added to RolePermissions for `planner`, `commander`, `sim_operator`, and `admin` roles
- [x] **`services/collab-svc/internal/hub/hub.go`** — full rewrite with map controller tracking
  - `controllers map[string]string` field: scenarioID → userID holding map control
  - `RequestMapControl(scenarioID, userID string) bool` — grants control or returns false if busy
  - `ReleaseMapControl(scenarioID, userID string)` — releases control by owner
  - `RevokeMapControl(scenarioID string)` — admin force-revoke
  - `Presence(scenarioID string) []string` — list of connected user IDs
  - `hasMapControlRole(roles []string) bool` — checks planner/commander/sim_operator/admin
  - Client struct updated: added `Roles []string` field
  - `ServeWS()` updated: accepts roles from JWT claims, passes to Client
  - `readPump()` updated: handles `map:control:request` and `map:control:release` messages
  - Auto-releases control when a controlling client disconnects; broadcasts `map:control:released`
- [x] **`services/collab-svc/internal/handlers/ws.go`** — updated to extract roles from JWT
  - `extractRoles(claims jwt.MapClaims) []string` — parses roles array from JWT
  - `PresenceHandler` updated: returns both users list and controller
  - New `GetMapControlHandler` — `GET /rooms/:scenario_id/control`
  - New `RequestMapControlHandler` — `POST /rooms/:scenario_id/control/request`
  - New `ReleaseMapControlHandler` — `DELETE /rooms/:scenario_id/control`
  - `authFromRequest()` helper for REST auth
- [x] **`services/collab-svc/main.go`** — registered new REST routes
- [x] **`frontend/src/modules/map/CollabPanel.tsx`** — new floating collaboration panel
  - WebSocket connection with JWT from Zustand store
  - Real-time presence list (user:join / user:leave messages)
  - Map controller display (who holds control)
  - "Request Control" / "Release Control" button (role-gated by server)
  - Status messages for granted / busy / denied
- [x] **`frontend/src/modules/map/MapPage.tsx`** — integrated CollabPanel (top-right overlay)

#### Item 2: Commercial intel feed integration ✅

- [x] **`services/intel-svc/app/models.py`** — added `OSINTSourceType` enum values:
  - `RECORDED_FUTURE = "RECORDED_FUTURE"`
  - `MAXAR = "MAXAR"`
  - `JANES = "JANES"`
- [x] **`services/intel-svc/app/config.py`** — added settings:
  - `recorded_future_api_key: str = ""`
  - `maxar_api_key: str = ""`
  - `janes_api_key: str = ""`
- [x] **`services/intel-svc/app/engine/osint_adapters.py`** — added three new adapters:
  - `RecordedFutureAdapter`: Recorded Future Connect API; synthetic fallback with 4 APT/ransomware/dark-web threat alerts
  - `MaxarAdapter`: Maxar Streaming API (WorldView/GeoEye imagery); synthetic fallback with 3 IMINT reports (Crimea troop buildup, DPRK Sohae launch site, South China Sea construction)
  - `JanesAdapter`: Jane's Defence Intelligence API; synthetic fallback with 4 TECHINT reports (T-14 Armata, J-20 fighter, Shahed-136 drone, Hwasong-18 ICBM)
  - `_init_registry()` updated to accept and register all three new adapters
- [x] **`services/intel-svc/main.py`** — passes new API key settings to `_init_registry()`
- All 27 existing intel-svc tests still passing

#### Item 3: STIX/TAXII cyber threat feed consumer ✅

- [x] **`db/init/009_stix_schema.sql`** — new `stix_indicators` table
  - STIX 2.1 object model: stix_id, name, description, pattern, pattern_type (stix/pcre/yara/sigma)
  - kill_chain_phases (JSONB), confidence (0–100), labels, valid_from/until
  - taxii_collection + taxii_server provenance fields
  - classification_level, scenario_id foreign key
  - Indexes on stix_type, taxii_server, valid_from, scenario_id, ingested_at
- [x] **`services/cyber-svc/app/models.py`** — new STIX/TAXII models:
  - `PatternType`, `KillChainPhase`, `ExternalReference`, `STIXIndicator`
  - `CreateSTIXIndicatorRequest`, `TAXIIIngestRequest`, `TAXIIIngestResult`
- [x] **`services/cyber-svc/app/routers/taxii.py`** — new router:
  - `GET /cyber/stix/indicators` — list with scenario/server/type filters
  - `POST /cyber/stix/indicators` — manual create
  - `GET /cyber/stix/indicators/{id}` — get
  - `DELETE /cyber/stix/indicators/{id}` — delete
  - `POST /cyber/taxii/ingest` — TAXII 2.1 collection poll; synthetic 5-indicator bundle fallback:
    - APT29 Cobalt Strike C2 IPv4 (confidence 85)
    - SUNBURST SHA-256 hash (confidence 99)
    - Industroyer2 ICS domain (confidence 92)
    - Lazarus Group SWIFT phishing URL (confidence 78)
    - BlackEnergy3 PowerShell dropper YARA rule (confidence 88)
- [x] **`services/cyber-svc/main.py`** — registered taxii router
- [x] **`frontend/src/shared/api/types/cyber.ts`** — added full STIX type definitions
- [x] **`frontend/src/shared/api/endpoints.ts`** — added STIX/TAXII methods to `cyberApi`
- [x] 4 new STIX/TAXII tests added to `tests/test_cyber.py` — all 17 tests passing

#### Item 4: Auto-report generation (SITREP, INTSUM, CONOPS briefs) ✅

- [x] **`db/init/010_reporting_schema.sql`** — new `reports` table
  - report_type (SITREP/INTSUM/CONOPS), status (DRAFT/FINAL/APPROVED)
  - JSONB content, approval fields, scenario_id/run_id
- [x] **`services/reporting-svc/`** — new Python/FastAPI service (port 8092)
  - `app/engine/templates.py` — deterministic NATO-format report generators:
    - `generate_sitrep()`: period, situation summary, friendly/enemy forces, significant events, logistics, commander assessment; aggregates simulation run events and logistics data
    - `generate_intsum()`: threat level from assessments, enemy disposition/intentions, key developments from intel items, STIX indicator count, ISR gaps, cyber/CBRN threats, analyst assessment
    - `generate_conops()`: mission statement, commander's intent, end state, scheme of maneuver, 3 execution phases, tasks to subordinate units, sustainment concept, risk assessment
  - `app/routers/reports.py` — REST API:
    - `POST /reports/generate` — generate from template + DB data
    - `GET /reports` — list with report_type/status/scenario_id filters
    - `GET /reports/{id}` — get report
    - `PUT /reports/{id}` — update title/status/classification/content/summary
    - `POST /reports/{id}/approve` — mark APPROVED + record approver
    - `DELETE /reports/{id}` — delete
  - 11 unit tests — all passing
- [x] **`docker-compose.dev.yml`** — added `reporting-svc` (port 8092) + `VITE_REPORTING_API_URL`
- [x] **`frontend/src/shared/api/reportingClient.ts`** — Axios client
- [x] **`frontend/src/shared/api/types/reporting.ts`** — full TypeScript types (Report, content types for SITREP/INTSUM/CONOPS)
- [x] **`frontend/src/shared/api/types/index.ts`** — re-exports reporting types
- [x] **`frontend/src/shared/api/endpoints.ts`** — added `reportingApi` (generate, list, get, update, approve, delete)
- [x] **`frontend/src/modules/reporting/ReportingPage.tsx`** — full two-panel reporting UI
  - Left panel: report list with type/status filters + status color badges
  - Right panel: formatted content viewer tailored by report type (SITREPView, INTSUMView, CONOPSView)
  - GenerateModal: report type selector, optional title/scenario/run binding, classification, context textarea
  - Finalize (DRAFT → FINAL) and Delete actions
- [x] Updated `frontend/src/app/router.tsx` — added `/reporting` route
- [x] Updated `frontend/src/modules/dashboard/DashboardPage.tsx` — added 📋 Reports card
- [x] Updated `buildsheet.md` — Phase 4 items 1–4 marked ✅
- [x] Updated `README.md` — Phase 4 section, service table, frontend modules table, DB schema table
- [x] TypeScript compilation passes with no errors

### Stopping Point

Phase 4 items 1–4 are **complete**:
- ✅ Multi-user collaboration with role-based map control
- ✅ Commercial intel feed integration (Recorded Future, Maxar, Jane's)
- ✅ STIX/TAXII cyber threat feed consumer
- ✅ Auto-report generation (SITREP, INTSUM, CONOPS briefs)

### What's Next (Session 10 — Phase 4 continued)

- [ ] Classification handling hardening (row-level security, labels)
- [ ] FedRAMP documentation and controls
- [ ] Air-gap deployment package (Helm chart, offline tile pack, Ollama models)
- [ ] Mobile app (React Native, read-only, offline maps)
- [ ] Economic warfare module
- [ ] Information operations / disinformation tracking
- [ ] API for external system integration (ArcGIS, Google Earth)
- [ ] Training mode (exercise inject system, scoring)

---

## Session 10 — Phase 4 Classification Hardening + FedRAMP (2026-02-25)

### Goal
Phase 4 items 5–6: Classification handling hardening (row-level security, labels) and FedRAMP documentation.

### What I Did This Session

#### Item 5: Classification handling hardening (row-level security, labels) ✅

- [x] **`db/init/011_classification_hardening.sql`** — new migration:
  - `agd_visible_classifications()` SQL helper function for DRY policy expressions
  - RLS SELECT + INSERT + UPDATE + DELETE policies for: `scenarios`, `equipment`, `annotations`, `cyber_infra_nodes`, `intel_threat_assessments`, `reports`
  - `agd_app` role created with `NOBYPASSRLS` to ensure policies fire for the application DB user

- [x] **All 8 Python service `app/auth.py` files updated** with new classification helpers:
  - `get_user_classification(user: dict) -> str` — extracts clearance level from JWT `cls` claim (supports int 0–4 or string)
  - `classification_allowed_levels(user_cls: str) -> list[str]` — returns cumulative list of allowed levels for a clearance ceiling
  - `enforce_classification_ceiling(user: dict, record_cls: str) -> None` — raises HTTP 403 if record classification exceeds user's clearance

- [x] **`services/intel-svc/app/routers/intel.py`** — classification enforcement:
  - `list_intel_items`: always filters by user's clearance ceiling (WHERE classification IN (...))
  - `search_intel`: same classification ceiling filter applied
  - `create_intel_item`: `enforce_classification_ceiling` before insert
  - `get_intel_item`: `enforce_classification_ceiling` after fetch
  - `update_intel_item`: ceiling checked on both current and requested classification

- [x] **`services/reporting-svc/app/routers/reports.py`** — classification enforcement:
  - `generate_report`: ceiling check on requested classification
  - `list_reports`: classification ceiling WHERE filter
  - `get_report`: ceiling check after fetch
  - `update_report`: ceiling check on current + requested classification

- [x] **`services/cyber-svc/app/routers/infrastructure.py`** — classification enforcement:
  - `get_graph`: classification ceiling filter in node queries (WHERE classification::text IN (...))
  - `create_node`: `enforce_classification_ceiling` before insert
  - `update_node`: ceiling check on current + requested classification

- [x] **`frontend/src/shared/components/ClassificationBadge.tsx`** — new inline badge component:
  - Color-coded: UNCLASS=green, FOUO=blue, SECRET=red, TOP SECRET=orange, TS/SCI=yellow
  - Used in place of raw text classification indicators

- [x] **`frontend/src/modules/intel/IntelPage.tsx`** — added `ClassificationBadge` to each intel item card

- [x] **`frontend/src/modules/reporting/ReportingPage.tsx`** — added `ClassificationBadge` to report list items and report detail header

- [x] **Tests** — 6 new classification unit tests in `services/reporting-svc/tests/test_reporting.py`:
  - `test_get_user_classification_default`
  - `test_get_user_classification_from_int`
  - `test_classification_allowed_levels`
  - `test_enforce_classification_ceiling_allows_lower`
  - `test_enforce_classification_ceiling_blocks_higher`
  - `test_generate_report_blocked_by_classification`
  - All 17 reporting-svc tests pass; all 27 intel-svc tests pass; all 17 cyber-svc tests pass

#### Item 6: FedRAMP documentation and controls ✅

- [x] **`docs/fedramp/README.md`** — FedRAMP overview:
  - Authorization scope table (system name, impact level, deployment model)
  - Architecture summary from security perspective
  - System boundary diagram (in/out of boundary)
  - Key security controls already implemented table
  - Continuous monitoring plan
  - Contact roles (System Owner, ISSO, AO, 3PAO)

- [x] **`docs/fedramp/controls-matrix.md`** — NIST SP 800-53 Rev 5 control inventory:
  - FedRAMP Moderate baseline coverage
  - Control families: AC, AU, CM, IA, IR, MP, PL, RA, SA, SC, SI
  - Status: ✅ Implemented / 🔄 In Progress / ⏳ Planned / N/A
  - AGD implementation notes for each control
  - POA&M summary (8 items requiring remediation before ATO)

- [x] Updated `buildsheet.md` — Phase 4 items 5–6 marked ✅
- [x] Updated `README.md` — Phase 4 checklist, classification enforcement description, DB schema table
- [x] Updated `copilot.md` — Session 10 progress

### Stopping Point

Phase 4 items 5–6 are **complete**:
- ✅ Classification handling hardening (row-level security, labels)
- ✅ FedRAMP documentation and controls

---

## Session 11 — Phase 4 Completion (2026-02-25)

### Goal
Complete all remaining Phase 4 items (except Mobile app, which is explicitly deferred).

### What I Did This Session

#### Item 7: Air-gap deployment package ✅

- [x] **`helm/agd/`** — Full Helm chart for Kubernetes deployment:
  - `Chart.yaml`, `values.yaml` covering all 16 services + infra
  - `templates/_helpers.tpl` with image, labels, namespace, DB URL helpers
  - Per-service Deployment + Service templates for all 15 application services
  - StatefulSets for postgres and ollama (with PVCs)
  - `ingress.yaml` — nginx path-based routing + WebSocket support
  - `configmap.yaml`, `secret.yaml` — shared config + JWT/DB credentials
  - `NOTES.txt` — post-install instructions

- [x] **`scripts/airgap-pack.sh`** — Builds/pulls all Docker images, saves as .tar, packages Helm chart, creates `agd-airgap-bundle.tar.gz`
- [x] **`scripts/airgap-load.sh`** — Loads image bundle; optional `--push <registry>` for multi-node clusters
- [x] **`scripts/ollama-pull.sh`** — Three modes: pull (live), `--save` (archive), `--load` (restore)
- [x] **`docs/airgap/README.md`** — 9-section air-gap deployment guide

#### Item 8: Economic warfare module ✅

- [x] **`services/econ-svc/`** — Python/FastAPI service on port 8093:
  - Sanction target CRUD (8 sanction types, 4 status values)
  - Trade route CRUD (dependency levels, disruption tracking)
  - Economic indicators (per-country, per-year)
  - Deterministic impact engine: GDP/inflation/unemployment/currency/trade impact by sanction type
  - Classification ceiling enforcement throughout
  - 19 passing tests

- [x] **`db/init/012_econ_schema.sql`** — 4 tables + seed (Russia/Iran/DPRK/Belarus/Venezuela sanctions, 5 trade routes)
- [x] **Frontend**: `econClient.ts`, `types/econ.ts`, `EconPage.tsx` (4-tab UI), `/econ` route, dashboard card, docker-compose wiring

#### Item 9: Information operations / disinformation tracking ✅

- [x] **`services/infoops-svc/`** — Python/FastAPI service on port 8094:
  - Narrative threat CRUD + `/analyze` endpoint (spread score, virality, counter-effectiveness)
  - Influence campaign CRUD
  - Disinformation indicator CRUD (8 indicator types)
  - Attribution assessment CRUD
  - 20 passing tests

- [x] **`db/init/013_infoops_schema.sql`** — 4 tables + seed (Russian energy FUD, Taiwan justification narratives, Secondary Infektion campaign)
- [x] **Frontend**: `infoopsClient.ts`, `types/infoops.ts`, `InfoOpsPage.tsx` (4-tab UI with analyze modal), `/infoops` route, dashboard card

#### Item 10: API for external system integration (ArcGIS, Google Earth) ✅

- [x] **`services/gis-export-svc/`** — Python/FastAPI service on port 8095:
  - GeoJSON export for 9 layer types with COUNTRY_CENTROIDS lookup
  - Pure-Python KML formatter with proper XML escaping
  - External integration config CRUD (ArcGIS/Google Earth/WMS/WFS)
  - `POST /integrations/{id}/test` stub
  - 15 passing tests

- [x] **`db/init/014_gis_export_schema.sql`** — integration config table + ArcGIS/Google Earth seed records
- [x] **Frontend**: `gisClient.ts`, `types/gis.ts`, GIS Integrations tab added to AdminPage
- [x] **docker-compose**: `gis-export-svc` at port 8095

#### Item 11: Training mode ✅

- [x] **`services/training-svc/`** — Python/FastAPI service on port 8096:
  - Exercise CRUD with lifecycle (DRAFT→SCHEDULED→ACTIVE→PAUSED→COMPLETED)
  - Inject CRUD: 12 inject types, 3 trigger modes, fire + acknowledge endpoints
  - Objective CRUD + scoring endpoint
  - Deterministic scoring engine: weighted objectives → grade A–F, timeliness/accuracy/communication sub-scores
  - 29 passing tests

- [x] **`db/init/015_training_schema.sql`** — 3 tables (exercises, injects, objectives) with CASCADE FKs + seed data
- [x] **Frontend**: `trainingClient.ts`, `types/training.ts`, `TrainingPage.tsx` (3-tab UI with score modal), `/training` route, dashboard card

### Stopping Point

Phase 4 is now **complete** (except Mobile app, deferred per instructions):
- ✅ Multi-user collaboration with role-based map control
- ✅ Commercial intel feed integration
- ✅ STIX/TAXII cyber threat feed consumer
- ✅ Auto-report generation
- ✅ Classification handling hardening
- ✅ FedRAMP documentation and controls
- ✅ Air-gap deployment package
- ⏭️ Mobile app (deferred)
- ✅ Economic warfare module
- ✅ Information operations / disinformation tracking
- ✅ API for external system integration (ArcGIS, Google Earth)
- ✅ Training mode

### What's Next (Session 12 — Future phases)

- Mobile app (React Native, read-only, offline maps) — when undeferred
- map-svc (Go, self-hosted tile management API)
- ai-svc (Python, LLM integration + fallback routing)
- sim-engine (C++/Rust, high-fidelity physics engine)

---

## Architecture Notes (for future sessions)

| Service | Port (dev) | Language | Status |
|---------|-----------|----------|--------|
| auth-svc | 8082 | Go | ✅ Complete |
| oob-svc | 8083 | Go | ✅ Complete |
| sim-orchestrator | 8085 | Python/FastAPI | ✅ Session 1–2 |
| collab-svc | 8084 | Go | ✅ Session 1 + map control (Session 9) |
| cyber-svc | 8086 | Python/FastAPI | ✅ Session 3 + STIX/TAXII (Session 9) |
| cbrn-svc | 8087 | Python/FastAPI | ✅ Session 4 |
| asym-svc | 8088 | Python/FastAPI | ✅ Session 5 |
| terror-svc | 8089 | Python/FastAPI | ✅ Session 6 |
| intel-svc | 8090 | Python/FastAPI | ✅ Session 7 + commercial feeds (Session 9) |
| civilian-svc | 8091 | Python/FastAPI | ✅ Session 8 |
| reporting-svc | 8092 | Python/FastAPI | ✅ Session 9 |
| econ-svc | 8093 | Python/FastAPI | ✅ Session 11 |
| infoops-svc | 8094 | Python/FastAPI | ✅ Session 11 |
| gis-export-svc | 8095 | Python/FastAPI | ✅ Session 11 |
| training-svc | 8096 | Python/FastAPI | ✅ Session 11 |
| map-svc | — | Go | ⏳ Future |
| ai-svc | — | Python | ⏳ Future |
| sim-engine | — | C++/Rust | ⏳ Future |

### Key Integration Points

- **JWT secret**: `dev-secret-change-in-prod` — shared across all services
- **Database**: `postgres://agd:devpass@postgres:5432/agd_dev`
- **Redis**: `redis://redis:6379`
- **Collab WS URL**: `ws://localhost:8084` (consumed by frontend `VITE_WS_URL`)
- **Sim orchestrator**: `http://localhost:8085/api/v1` (consumed by frontend `VITE_SIM_API_URL`)
- **Cyber svc**: `http://localhost:8086/api/v1` (consumed by frontend `VITE_CYBER_API_URL`)
- **CBRN svc**: `http://localhost:8087/api/v1` (consumed by frontend `VITE_CBRN_API_URL`)
- **Asym svc**: `http://localhost:8088/api/v1` (consumed by frontend `VITE_ASYM_API_URL`)
- **Terror svc**: `http://localhost:8089/api/v1` (consumed by frontend `VITE_TERROR_API_URL`)
- **Intel svc**: `http://localhost:8090/api/v1` (consumed by frontend `VITE_INTEL_API_URL`)
- **Civilian svc**: `http://localhost:8091/api/v1` (consumed by frontend `VITE_CIVILIAN_API_URL`)
- **Reporting svc**: `http://localhost:8092/api/v1` (consumed by frontend `VITE_REPORTING_API_URL`)
- **Econ svc**: `http://localhost:8093/api/v1` (consumed by frontend `VITE_ECON_API_URL`)
- **InfoOps svc**: `http://localhost:8094/api/v1` (consumed by frontend `VITE_INFOOPS_API_URL`)
- **GIS Export svc**: `http://localhost:8095/api/v1` (consumed by frontend `VITE_GIS_API_URL`)
- **Training svc**: `http://localhost:8096/api/v1` (consumed by frontend `VITE_TRAINING_API_URL`)

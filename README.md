# Apex Global Defense (AGD)

**Enterprise-grade defense simulation and strategic planning platform** — multi-domain wargaming, threat analysis, CBRN/Cyber/Asymmetric/Terror response modeling, AI-assisted intelligence, and civilian impact assessment.

> ⚠️ **UNCLASSIFIED // FOR OFFICIAL USE ONLY** — Development build. Not for operational use.

---

## Table of Contents

1. [What Is AGD?](#what-is-agd)
2. [Implemented Features (Phases 1–3)](#implemented-features-phases-13)
3. [Architecture Overview](#architecture-overview)
4. [Prerequisites](#prerequisites)
5. [Quick Start — Local Dev](#quick-start--local-dev)
6. [Service Endpoints](#service-endpoints)
7. [Frontend](#frontend)
8. [RBAC Roles & Classification](#rbac-roles--classification)
9. [Running Tests](#running-tests)
10. [Phase 4 Roadmap](#phase-4-roadmap)

---

## What Is AGD?

Apex Global Defense is a simulation and strategic planning platform designed for military strategists, defense analysts, intelligence professionals, and security planners. It models and simulates armed conflict, assesses worldwide military capabilities, and supports coordinated response planning across all warfare domains.

### Core Design Principles

| Principle | Description |
|-----------|-------------|
| **Air-gap first** | Every component supports fully disconnected deployment |
| **Classification-aware** | Data compartmentalization baked in at the schema level (UNCLASS → TS/SCI) |
| **Non-AI fallback** | Every AI feature degrades gracefully to a deterministic alternative |
| **Modularity** | Domains are independently deployable feature modules |
| **Auditability** | Every action, query, and state change is logged immutably |

### Warfare Domains

| Domain | Description |
|--------|-------------|
| Conventional | Land/Air/Sea combined-arms operations |
| CBRN | Chemical, Biological, Radiological, Nuclear dispersion modeling |
| Cyber | Infrastructure attack/defense, MITRE ATT&CK mapping |
| Asymmetric | Insurgent cell modeling, IED analysis, COIN planning |
| Terror Response | Site vulnerability assessment, multi-agency coordination |

---

## Implemented Features (Phases 1–3 + Phase 4 Start)

### Phase 1 — MVP ✅

- **Auth service** — Go/JWT + RBAC + classification-level enforcement, Keycloak OIDC integration
- **Order of Battle (OOB)** — Full CRUD API for military units/equipment; 50-nation seed data
- **Interactive Globe** — MapLibre GL world map with layer panel and annotation toolbar
- **Self-hosted tile server** — MBTiles-based, air-gap compatible (mbtiles-server)
- **Scenario management** — Create, save, and branch named scenarios
- **AI config UI** — Provider selection (OpenAI / Anthropic / Ollama / None), API key management, fallback toggle
- **Audit logging** — Immutable append-only event log for all write operations and auth events

### Phase 2 — Simulation Core ✅

- **Sim Orchestrator** (`sim-orchestrator`, port 8085) — Python/FastAPI service managing simulation lifecycle
  - Turn-based, real-time, and Monte Carlo simulation modes
  - Start / pause / resume / step controls with live event feed
  - Monte Carlo result panel: probability outcomes, casualty distributions
  - After-action report generation
- **Logistics & Attrition Model** — Per-force supply levels (ammo/fuel/rations), strength %, KIA/WIA, equipment losses; RESUPPLY events; logistics summary in after-action reports
- **WebSocket Collaboration** (`collab-svc`, port 8084) — Go hub for scenario-scoped real-time relay; cursor sharing, annotation sync, sim event fan-out; Redis pub/sub bridge
- **AI-assisted scenario builder** — Natural language → ScenarioConfig via `ai-svc` hook

### Phase 3 — Domain Expansion ✅

#### Cyber Operations (`cyber-svc`, port 8086)
- MITRE ATT&CK technique catalog (30 techniques across all 14 enterprise tactics)
- Infrastructure graph — node/edge CRUD (HOST, SERVER, ROUTER, FIREWALL, ICS, CLOUD, etc.)
- Attack planner — plan attacks by technique + threat actor + target node
- Monte Carlo attack simulation with defender skill and network-hardening modifiers

#### CBRN (`cbrn-svc`, port 8087)
- 11-agent catalog: Chemical (VX, Sarin, Mustard, Chlorine, HCN), Biological (Anthrax, Botulinum, Plague), Radiological (Cs-137, Co-60), Nuclear (IND 10kT/100kT)
- Gaussian plume dispersion engine (HYSPLIT-inspired, Pasquill-Gifford stability classes A–F)
- Plume contour polygon generation with lethal/incapacitating/IDLH hazard zones
- Casualty estimation: area × population density × affected fraction

#### Asymmetric/Insurgency (`asym-svc`, port 8088)
- Insurgent cell network CRUD (10 cell function types: CMD, OPS, LOG, INT, FIN, REC, PROP, SFH, MED, TECH)
- IED threat catalog (9 IED types: VBIED, PBIED, EFP, RCIED, Drone-IED, etc.)
- COIN planning engine — degree + betweenness centrality, hub scoring, interdiction recommendations

#### Terror Response (`terror-svc`, port 8089)
- 14 site types (transport hubs, stadiums, embassies, critical infrastructure, etc.)
- 10 attack-type catalog (VRAM, ASHT, SBOM, HSTG, EXPL, CHEM, BIOL, CYBR, ASSN, INFR)
- Vulnerability scoring (security dimensions: physical, access control, surveillance, emergency response)
- Multi-agency response plan builder with agency role assignments (PRIMARY/SUPPORTING/NOTIFIED)

#### Intelligence (`intel-svc`, port 8090)
- Deterministic NER entity extraction: PERSON, ORG, LOCATION, WEAPON, DATE, EVENT, VEHICLE, FACILITY
- PMESII-PT threat assessment engine (14 indicators → ThreatLevel, ThreatVectors, confidence score)
- OSINT ingestion adapters: ACLED, UCDP, RSS feeds (with deterministic synthetic fallback)
- Full-text search (PostgreSQL `tsvector`) + pgvector semantic similarity search
- NATO admiralty reliability/credibility scoring on all intel items

#### Civilian Impact (`civilian-svc`, port 8091)
- Population zone management (8 built-in seed zones: Baghdad, Kabul, Kyiv, Mariupol, Aleppo, etc.)
- Deterministic impact assessment engine (haversine proximity, CBRN/airstrike/engagement severity)
- Refugee flow tracking (5 seed flows: Ukraine→Poland, Syria→Turkey, Afghanistan→Pakistan, etc.)
- Humanitarian corridor management (status: OPEN/RESTRICTED/CLOSED)
- Map overlays: population density circles, refugee flow lines, corridor status lines

### Phase 4 — Enterprise (In Progress)

#### Multi-user collaboration with role-based map control ✅
- `collab-svc` extended with per-room map controller tracking
- Role-based access: only planners, commanders, sim_operators, and admins may request map control
- New REST endpoints: `GET/POST/DELETE /rooms/{scenario_id}/control`
- WS message types: `map:control:request`, `map:control:granted`, `map:control:released`, `map:control:busy`, `map:control:denied`
- `CollabPanel` floating UI on map page — presence list + request/release map control button
- `map:control` permission added to `auth-svc` RBAC model

#### Commercial intel feed integration ✅
- `RecordedFutureAdapter` — Recorded Future Connect API (stub/synthetic for dev/air-gap)
- `MaxarAdapter` — Maxar WorldView/GeoEye satellite imagery IMINT (stub/synthetic)
- `JanesAdapter` — Jane's Defence Intelligence TECHINT (stub/synthetic)
- All three adapters registered in `intel-svc` and accessible via the OSINT pipeline UI

#### STIX/TAXII cyber threat feed consumer ✅
- New DB schema: `stix_indicators` table (STIX 2.1 object model)
- `cyber-svc` extended with STIX/TAXII router:
  - `GET/POST /cyber/stix/indicators` — list and manually create STIX indicators
  - `GET /cyber/stix/indicators/{id}` — get indicator
  - `DELETE /cyber/stix/indicators/{id}` — delete indicator
  - `POST /cyber/taxii/ingest` — poll a TAXII 2.1 server collection; falls back to 5-indicator synthetic bundle (APT29 Cobalt Strike, SUNBURST, Industroyer2, Lazarus Group, BlackEnergy3 YARA)
- Pattern types: stix / pcre / yara / sigma
- Frontend STIX types and `taxiiApi` methods in `cyberApi`

#### Auto-report generation (SITREP, INTSUM, CONOPS briefs) ✅
- New service: `reporting-svc` (Python/FastAPI, port 8092)
- `POST /reports/generate` — generate a SITREP, INTSUM, or CONOPS from simulation + intel data
- Deterministic NATO-format template generators:
  - **SITREP**: period, situation summary, friendly/enemy forces, significant events, logistics, commander assessment
  - **INTSUM**: threat level, enemy disposition/intentions, key developments, cyber/CBRN threats, ISR gaps, analyst assessment
  - **CONOPS**: mission statement, commander's intent, end state, scheme of maneuver, execution phases, tasks to subordinates, risk assessment
- Full CRUD: list, get, update (title, status, content), approve, delete
- Report statuses: DRAFT → FINAL → APPROVED
- Frontend `ReportingPage` at `/reporting` — two-panel view (report list + formatted content viewer); Generate Report modal with report type, classification, context, scenario/run binding

---

## Architecture Overview

```
React 18 + TypeScript (Vite)  ──►  API services (Go + Python/FastAPI)  ──►  PostgreSQL + PostGIS
                                                                          ──►  Redis (cache/pub-sub)
                                                                          ──►  Elasticsearch (OSINT search)
                                                                          ──►  Kafka (event bus)
```

### Service Inventory

| Service | Port | Language | Status |
|---------|------|----------|--------|
| `auth-svc` | 8082 | Go | ✅ Complete |
| `oob-svc` | 8083 | Go | ✅ Complete |
| `collab-svc` | 8084 | Go | ✅ Complete + map control |
| `sim-orchestrator` | 8085 | Python/FastAPI | ✅ Complete |
| `cyber-svc` | 8086 | Python/FastAPI | ✅ Complete + STIX/TAXII |
| `cbrn-svc` | 8087 | Python/FastAPI | ✅ Complete |
| `asym-svc` | 8088 | Python/FastAPI | ✅ Complete |
| `terror-svc` | 8089 | Python/FastAPI | ✅ Complete |
| `intel-svc` | 8090 | Python/FastAPI | ✅ Complete + commercial feeds |
| `civilian-svc` | 8091 | Python/FastAPI | ✅ Complete |
| `reporting-svc` | 8092 | Python/FastAPI | ✅ Complete (Phase 4) |
| `map-svc` | — | Go | ⏳ Phase 4 |
| `ai-svc` | — | Python | ⏳ Phase 4 |
| `sim-engine` | — | C++/Rust | ⏳ Phase 4 |

### Infrastructure Services (dev)

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL + PostGIS | 5432 | Primary database |
| Redis | 6379 | Cache + pub/sub |
| Elasticsearch | 9200 | Full-text search |
| Kafka | 9092 | Event bus |
| Keycloak | 8180 | OIDC identity provider |
| mbtiles-server | 8081 | Self-hosted map tiles |
| Ollama | 11434 | Local LLM (air-gap AI) |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24 with [Compose](https://docs.docker.com/compose/) v2
- [Node.js](https://nodejs.org/) ≥ 20 (for frontend development only)
- [Go](https://go.dev/) ≥ 1.22 (for Go service development only)
- [Python](https://python.org/) ≥ 3.11 (for Python service development only)

> **Minimum resources (local dev):** 8 GB RAM, 4 CPU cores, 20 GB free disk.
> The largest consumers are Elasticsearch (~5 GB image + index data), Ollama model storage (~4–8 GB per model), PostgreSQL data volumes, and Docker image layers for all services. If disk space is tight, you can comment out `ollama` and `elasticsearch` in `docker-compose.dev.yml` for a lighter start.

---

## Quick Start — Local Dev

### 1. Clone and start all services

```bash
git clone https://github.com/J-Ellette/Apex-Global-Defense.git
cd Apex-Global-Defense
make dev
```

This runs `docker compose -f docker-compose.dev.yml up --build`, which:
- Starts PostgreSQL, Redis, Elasticsearch, Kafka, Keycloak, mbtiles-server, and Ollama
- Runs all DB init scripts in `db/init/` (schema + seed data)
- Builds and starts all backend microservices
- Starts the React frontend dev server

### 2. Open the app

| URL | Service |
|-----|---------|
| `http://localhost:5173` | Frontend (React dev server) |
| `http://localhost:8180` | Keycloak admin console |
| `http://localhost:9200` | Elasticsearch |

### 3. Default credentials

| Account | Username | Password |
|---------|----------|----------|
| App (dev) | `admin` | `adminpass` |
| Keycloak admin | `admin` | `adminpass` |
| PostgreSQL | `agd` | `devpass` |

> **Note:** The dev JWT secret is defined in `docker-compose.dev.yml`. All services share this secret. **Never use dev credentials in production.**

### 4. Stopping the environment

```bash
make dev-down   # stops all containers and removes volumes
```

---

## Service Endpoints

All REST APIs accept `Authorization: Bearer <jwt>` and return `application/json`.

| Service | Base URL | Key Endpoints |
|---------|----------|---------------|
| Auth | `http://localhost:8082/api/v1/auth` | `POST /login`, `POST /refresh`, `GET /me` |
| OOB | `http://localhost:8083/api/v1/oob` | `GET /countries`, `GET /countries/{code}/forces`, `POST /units` |
| Collab WS | `ws://localhost:8084` | WebSocket: cursor, annotation, sim events |
| Simulation | `http://localhost:8085/api/v1` | `POST /scenarios/{id}/runs`, `GET /runs/{id}`, `GET /runs/{id}/report` |
| Cyber | `http://localhost:8086/api/v1/cyber` | `GET /techniques`, `GET /infrastructure`, `POST /attacks` |
| CBRN | `http://localhost:8087/api/v1/cbrn` | `GET /agents`, `POST /releases`, `POST /releases/{id}/simulate` |
| Asymmetric | `http://localhost:8088/api/v1/asym` | `GET /cells`, `GET /incidents`, `GET /network/analysis` |
| Terror | `http://localhost:8089/api/v1/terror` | `GET /sites`, `GET /attack-types`, `GET /response-plans` |
| Intel | `http://localhost:8090/api/v1/intel` | `GET /intel`, `POST /intel/search`, `POST /extract`, `POST /threat-assess` |
| Civilian | `http://localhost:8091/api/v1/civilian` | `GET /population`, `POST /impact/assess`, `GET /flows`, `GET /corridors` |
| Reporting | `http://localhost:8092/api/v1` | `POST /reports/generate`, `GET /reports`, `GET /reports/{id}`, `POST /reports/{id}/approve` |

All services expose a `GET /health` endpoint for readiness checks.

---

## Frontend

The React frontend (`frontend/`) is a single-page application built with Vite + TypeScript.

### Frontend Modules

| Route | Module | Description |
|-------|--------|-------------|
| `/` | Dashboard | Module overview and quick-launch cards |
| `/map` | Map | Interactive globe with layer panel, annotation toolbar, and collaboration panel |
| `/oob` | Order of Battle | Browse and manage military units by country |
| `/simulation` | Simulation | Run turn-based / real-time / Monte Carlo scenarios |
| `/cyber` | Cyber Operations | ATT&CK techniques, infrastructure graph, attack planner, STIX/TAXII indicators |
| `/cbrn` | CBRN | Agent catalog, release planner, dispersion results |
| `/asym` | Asymmetric/Insurgency | Cell network, IED threats, COIN planning |
| `/terror` | Terror Response | Site vulnerability, threat scenarios, response plans |
| `/intel` | Intelligence | Intel feed, entity extraction, threat assessment, OSINT (incl. Recorded Future, Maxar, Jane's) |
| `/civilian` | Civilian Impact | Population zones, impact assessment, refugee flows, corridors |
| `/reporting` | Reports | Generate and manage SITREP, INTSUM, and CONOPS briefs |
| `/admin` | Admin | AI provider config, user management |

### Frontend Dev Server (standalone)

```bash
cd frontend
npm ci
npm run dev
```

Set environment variables (or copy `.env.example`):

```
VITE_AUTH_API_URL=http://localhost:8082
VITE_OOB_API_URL=http://localhost:8083
VITE_WS_URL=ws://localhost:8084
VITE_SIM_API_URL=http://localhost:8085/api/v1
VITE_CYBER_API_URL=http://localhost:8086/api/v1
VITE_CBRN_API_URL=http://localhost:8087/api/v1
VITE_ASYM_API_URL=http://localhost:8088/api/v1
VITE_TERROR_API_URL=http://localhost:8089/api/v1
VITE_INTEL_API_URL=http://localhost:8090/api/v1
VITE_CIVILIAN_API_URL=http://localhost:8091/api/v1
VITE_REPORTING_API_URL=http://localhost:8092/api/v1
VITE_TILE_SERVER=http://localhost:8081
```

---

## RBAC Roles & Classification

### Roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only, UNCLASS data only |
| `analyst` | Create/edit intel items, annotate maps, run assessments |
| `planner` | Create/edit scenarios, configure simulations, **request map control** |
| `commander` | Approve scenario publication, access all FOUO data, **request map control** |
| `sim_operator` | Launch and control simulation runs, **request map control** |
| `admin` | User management, system configuration, **request map control** |
| `classification_officer` | Manage classification labels on records |

### Classification Levels

| Level | Integer | Description |
|-------|---------|-------------|
| `UNCLASS` | 0 | Unclassified |
| `FOUO` | 1 | For Official Use Only |
| `SECRET` | 2 | Secret |
| `TOP_SECRET` | 3 | Top Secret |
| `TS_SCI` | 4 | Top Secret / Sensitive Compartmented Information |

Classification is enforced at the JWT level (claims), at the application layer (ceiling checks on every read/write endpoint), and at the PostgreSQL row-level security layer (RLS policies on all classified tables via `agd.user_classification` session setting).

---

## Running Tests

```bash
# All tests
make test

# Go services only
make test-go

# Python services only
make test-python

# Frontend only
make test-frontend
```

### Linting & Formatting

```bash
make lint    # lint all (Go: golangci-lint, Python: ruff, Frontend: eslint)
make fmt     # format all (Go: gofmt, Python: ruff format, Frontend: prettier)
```

### Security Scan

```bash
make security-scan   # Trivy scan (fails on HIGH/CRITICAL CVEs)
make sbom            # Generate SBOM (Syft → sbom.json)
```

---

## Phase 4 Roadmap

Phase 4 (Enterprise) is **in progress**:

- [x] Multi-user collaboration with role-based map control
- [x] Commercial intel feed integration (Recorded Future, Maxar, Jane's)
- [x] STIX/TAXII cyber threat feed consumer
- [x] Auto-report generation (SITREP, INTSUM, CONOPS briefs)
- [x] Classification handling hardening (row-level security, labels)
- [x] FedRAMP documentation and controls
- [ ] Air-gap deployment package (Helm chart, offline tile pack, Ollama models)
- [ ] Mobile app (React Native, read-only, offline maps)
- [ ] Economic warfare module
- [ ] Information operations / disinformation tracking
- [ ] API for external system integration (ArcGIS, Google Earth)
- [ ] Training mode (exercise inject system, scoring)

---

## Database

All schema initialization scripts are in `db/init/` and run automatically on first `make dev`:

| File | Description |
|------|-------------|
| `001_schema.sql` | Core tables: countries, military units, equipment, scenarios, intel items, audit log |
| `002_oob_seed.sql` | 50-nation OOB seed data |
| `003_cyber_schema.sql` | Cyber infrastructure nodes, edges, attacks |
| `004_cbrn_schema.sql` | CBRN releases, dispersion simulations |
| `005_asym_schema.sql` | Insurgent cells, cell links, IED incidents |
| `006_terror_schema.sql` | Terror sites, threat scenarios, response plans |
| `007_intel_schema.sql` | Intel threat assessments, OSINT ingestion jobs |
| `008_civilian_schema.sql` | Population zones, impact assessments, refugee flows, corridors |
| `009_stix_schema.sql` | STIX 2.1 indicator table for TAXII feed ingestion |
| `010_reporting_schema.sql` | SITREP / INTSUM / CONOPS report storage |
| `011_classification_hardening.sql` | RLS SELECT/INSERT/UPDATE policies for all classified tables; `agd_visible_classifications()` helper function |

---

*Apex Global Defense — Engineering Build Sheet v2.0 | UNCLASSIFIED*
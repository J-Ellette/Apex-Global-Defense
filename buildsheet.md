# Apex Global Defense (AGD)
## Comprehensive Engineering Build Sheet — Version 2.0

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Services](#4-backend-services)
5. [Database Layer](#5-database-layer)
6. [Simulation Engine](#6-simulation-engine)
7. [AI/ML Integration Layer](#7-aiml-integration-layer)
8. [Mapping & Geospatial Stack](#8-mapping--geospatial-stack)
9. [Intelligence Integration Layer](#9-intelligence-integration-layer)
10. [Security & Auth](#10-security--auth)
11. [Infrastructure & DevOps](#11-infrastructure--devops)
12. [API Reference](#12-api-reference)
13. [Data Sources](#13-data-sources)
14. [Feature Modules](#14-feature-modules)
15. [Development Phases](#15-development-phases)
16. [Competitive Landscape](#16-competitive-landscape)
17. [Strategic Considerations](#17-strategic-considerations)

---

## 1. Project Overview

**Apex Global Defense (AGD)** is an enterprise-grade defense simulation and strategic planning platform designed for military strategists, defense analysts, intelligence professionals, and security planners. It enables conflict modeling, threat assessment, and coordinated response planning across all warfare domains.

### 1.1 Core Mission

- Model and simulate armed conflicts across multiple domains
- Assess and project worldwide military capabilities
- Plan coordinated responses to diverse threat scenarios
- Provide enterprise-grade tools for defense planning and analysis

### 1.2 Warfare Domains

| Domain | Description |
|--------|-------------|
| Conventional | Land, Air, Sea combined arms operations |
| CBRN | Chemical, Biological, Radiological, Nuclear modeling |
| Cyber | Infrastructure attack/defense, attribution |
| Asymmetric | Insurgent cell modeling, IED analysis, COIN planning |
| Terror Response | Vulnerability assessment, multi-agency coordination |

### 1.3 Design Principles

- **Air-gap first**: Every component must support fully disconnected deployment
- **Classification-aware**: Data compartmentalization baked in at the schema level
- **Non-AI fallback**: Every AI feature must degrade gracefully to a deterministic alternative
- **Modularity**: Domains are independently deployable feature modules
- **Auditability**: Every action, query, and state change is logged immutably

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT TIER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Web App     │  │  Mobile App  │  │  Desktop (Electron/Tauri)│  │
│  │ React + TS   │  │ React Native │  │  Optional Air-Gap UI     │  │
│  └──────┬───────┘  └──────┬───────┘  └─────────────┬────────────┘  │
└─────────┼─────────────────┼───────────────────────┼───────────────┘
          │                 │                         │
          └─────────────────┴─────────────────────────┘
                            │  HTTPS / WSS
┌───────────────────────────▼─────────────────────────────────────────┐
│                       API GATEWAY TIER                               │
│  ┌────────────────────┐   ┌──────────────────────────────────────┐  │
│  │  Kong / Nginx      │   │  WebSocket Hub (scenario streaming)  │  │
│  │  Rate Limit / TLS  │   │  (Go or Node.js)                     │  │
│  └────────────────────┘   └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│                       SERVICE TIER (Kubernetes)                     │
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │  Auth Svc    │ │  Map Svc     │ │  Intel Svc   │ │  AI Svc   │ │
│  │  (Go)        │ │  (Go/Python) │ │  (Python)    │ │  (Python) │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └───────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │  Order of    │ │  Simulation  │ │  Reporting   │ │  Collab   │ │
│  │  Battle Svc  │ │  Engine Svc  │ │  Svc         │ │  Svc      │ │
│  │  (Go)        │ │  (C++/Rust)  │ │  (Python)    │ │  (Go)     │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └───────────┘ │
└────────────────────────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│                       DATA TIER                                     │
│  ┌────────────────┐ ┌───────────────┐ ┌──────────────┐ ┌────────┐ │
│  │  PostgreSQL    │ │  TimescaleDB  │ │  Redis       │ │ Minio  │ │
│  │  + PostGIS     │ │  (time-series)│ │  (cache/pub) │ │ (blobs)│ │
│  └────────────────┘ └───────────────┘ └──────────────┘ └────────┘ │
│  ┌────────────────┐ ┌───────────────┐                              │
│  │  Elasticsearch │ │  Kafka        │                              │
│  │  (search/OSINT)│ │  (event bus)  │                              │
│  └────────────────┘ └───────────────┘                              │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 Service Inventory

| Service | Language | Purpose | Scales |
|---------|----------|---------|--------|
| `auth-svc` | Go | JWT/RBAC/OIDC | Horizontally |
| `map-svc` | Go | Tile serving, annotation management | Horizontally |
| `oob-svc` | Go | Order of Battle database CRUD | Horizontally |
| `sim-engine` | C++/Rust | Core simulation compute | Vertically (GPU optional) |
| `sim-orchestrator` | Python | Scenario lifecycle management | Horizontally |
| `intel-svc` | Python | OSINT ingestion, entity extraction | Horizontally |
| `ai-svc` | Python | LLM routing, prompt management | Horizontally |
| `reporting-svc` | Python | Brief/report generation | Horizontally |
| `collab-svc` | Go | WebSocket relay, presence, cursors | Horizontally |
| `cbrn-svc` | Python/C++ | Dispersion modeling | Vertically |
| `cyber-svc` | Python | Infrastructure graph, ATT&CK mapping | Horizontally |
| `notify-svc` | Go | Alerts, webhooks | Horizontally |
| `audit-svc` | Go | Immutable event log | Append-only |

### 2.3 Inter-Service Communication

- **Synchronous**: REST + gRPC (internal)
- **Asynchronous**: Kafka topics for simulation events, intel ingestion, notifications
- **Real-time**: WebSocket via `collab-svc` relay; Redis pub/sub for ephemeral state
- **Service mesh**: Istio (mTLS between all pods, traffic policies, observability)

---

## 3. Frontend Architecture

### 3.1 Stack

```
React 18 + TypeScript 5
Vite (build)
TanStack Query (server state)
Zustand (client state)
React Router v6
Cesium.js / Mapbox GL JS (geo rendering)
Deck.gl (overlay layers)
Recharts + D3 (charts/graphs)
Socket.io client (real-time collab)
Tailwind CSS + shadcn/ui
```

### 3.2 Project Structure

```
src/
├── app/                    # App shell, routing, providers
│   ├── App.tsx
│   ├── router.tsx
│   └── providers/
│       ├── AuthProvider.tsx
│       ├── ThemeProvider.tsx
│       └── RealtimeProvider.tsx
├── modules/                # Feature modules (lazy-loaded)
│   ├── map/
│   │   ├── MapCanvas.tsx
│   │   ├── LayerPanel.tsx
│   │   ├── AnnotationToolbar.tsx
│   │   └── hooks/
│   │       ├── useCesium.ts
│   │       └── useMapLayers.ts
│   ├── oob/                # Order of Battle
│   ├── simulation/
│   │   ├── ScenarioBuilder.tsx
│   │   ├── WargameBoard.tsx
│   │   ├── ProbabilityHeatmap.tsx
│   │   └── AfterActionReport.tsx
│   ├── intel/
│   ├── cbrn/
│   ├── cyber/
│   ├── reporting/
│   └── admin/
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── api/               # API client layer
│   │   ├── client.ts      # Axios instance + interceptors
│   │   ├── endpoints.ts
│   │   └── types/         # Generated from OpenAPI spec
│   └── utils/
└── assets/
```

### 3.3 State Management Strategy

```typescript
// Global auth/session state — Zustand
interface AuthStore {
  user: User | null;
  token: string | null;
  classification: ClassificationLevel;
  permissions: Permission[];
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

// Server state — TanStack Query
// Example: Order of Battle query
const { data: forces } = useQuery({
  queryKey: ['oob', countryCode, branch],
  queryFn: () => api.oob.getForces({ countryCode, branch }),
  staleTime: 5 * 60 * 1000,
});

// Simulation state — Zustand + WebSocket sync
interface SimulationStore {
  scenarioId: string | null;
  phase: SimPhase;
  turnNumber: number;
  blueForces: Force[];
  redForces: Force[];
  events: SimEvent[];
  tick: (event: SimEvent) => void;
}
```

### 3.4 Map Integration

```typescript
// Cesium viewer initialization
import { Viewer, Ion, Terrain, ImageryLayer } from 'cesium';

export function initCesiumViewer(containerId: string): Viewer {
  Ion.defaultAccessToken = process.env.VITE_CESIUM_TOKEN!;

  const viewer = new Viewer(containerId, {
    terrain: Terrain.fromWorldTerrain(),
    animation: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: true,
    navigationHelpButton: false,
    timeline: true,                // For replay mode
  });

  // Custom imagery: self-hosted tile server in air-gap mode
  if (import.meta.env.VITE_AIRGAP === 'true') {
    viewer.imageryLayers.removeAll();
    viewer.imageryLayers.addImageryProvider(
      new UrlTemplateImageryProvider({
        url: `${process.env.VITE_TILE_SERVER}/{z}/{x}/{y}.png`,
      })
    );
  }

  return viewer;
}
```

### 3.5 Real-time Collaboration (WebSocket)

```typescript
// collab socket — handles map cursors, scenario events, annotations
import { io, Socket } from 'socket.io-client';

class CollabSocket {
  private socket: Socket;

  constructor(scenarioId: string, token: string) {
    this.socket = io('/collab', {
      auth: { token },
      query: { scenarioId },
      transports: ['websocket'],
    });

    this.socket.on('scenario:tick', this.handleTick);
    this.socket.on('annotation:add', this.handleAnnotation);
    this.socket.on('cursor:move', this.handleCursor);
  }

  emitMove(lat: number, lng: number) {
    this.socket.emit('cursor:move', { lat, lng });
  }

  emitAnnotation(annotation: Annotation) {
    this.socket.emit('annotation:add', annotation);
  }
}
```

---

## 4. Backend Services

### 4.1 API Gateway

**Kong Gateway** is the preferred choice for enterprise/government deployments.

```yaml
# kong.yml (declarative config excerpt)
services:
  - name: auth-svc
    url: http://auth-svc:8080
    routes:
      - paths: [/api/v1/auth]
    plugins:
      - name: rate-limiting
        config:
          minute: 60
          policy: local

  - name: oob-svc
    url: http://oob-svc:8080
    routes:
      - paths: [/api/v1/oob]
    plugins:
      - name: jwt
      - name: request-size-limiting
        config:
          allowed_payload_size: 10

  - name: sim-orchestrator
    url: http://sim-orchestrator:8000
    routes:
      - paths: [/api/v1/simulation]
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 20
```

### 4.2 Auth Service (Go)

```go
// auth-svc: JWT + RBAC + classification label enforcement

type Claims struct {
    UserID           string              `json:"uid"`
    Roles            []Role              `json:"roles"`
    Permissions      []Permission        `json:"perms"`
    Classification   ClassificationLevel `json:"cls"` // UNCLASS, SECRET, TS, TS_SCI
    jwt.RegisteredClaims
}

// Classification levels
type ClassificationLevel int
const (
    UNCLASS    ClassificationLevel = 0
    FOUO       ClassificationLevel = 1
    SECRET     ClassificationLevel = 2
    TOP_SECRET ClassificationLevel = 3
    TS_SCI     ClassificationLevel = 4
)

// Middleware: enforce classification ceiling on every request
func ClassificationMiddleware(required ClassificationLevel) gin.HandlerFunc {
    return func(c *gin.Context) {
        claims := c.MustGet("claims").(*Claims)
        if claims.Classification < required {
            c.AbortWithStatusJSON(403, gin.H{
                "error": "classification_insufficient",
                "required": required,
                "provided": claims.Classification,
            })
            return
        }
        c.Next()
    }
}
```

### 4.3 Order of Battle Service (Go)

```go
// Core OOB data model
type MilitaryUnit struct {
    ID              uuid.UUID         `json:"id" db:"id"`
    CountryCode     string            `json:"country_code" db:"country_code"`
    Branch          Branch            `json:"branch" db:"branch"`       // ARMY, NAVY, AIR, SPACE, CYBER
    Name            string            `json:"name" db:"name"`
    ParentID        *uuid.UUID        `json:"parent_id" db:"parent_id"`
    Location        *pgtype.Point     `json:"location" db:"location"`   // PostGIS point
    Personnel       PersonnelCounts   `json:"personnel" db:"personnel"`
    Equipment       []Equipment       `json:"equipment"`
    Capabilities    []Capability      `json:"capabilities"`
    ConfidenceScore float64           `json:"confidence" db:"confidence_score"` // 0.0-1.0
    DataSources     []string          `json:"sources" db:"data_sources"`
    AsOf            time.Time         `json:"as_of" db:"as_of"`
    ClassLevel      ClassificationLevel `json:"classification"`
}

// REST endpoints
// GET    /api/v1/oob/countries
// GET    /api/v1/oob/countries/{code}/forces
// GET    /api/v1/oob/units/{id}
// POST   /api/v1/oob/units
// PUT    /api/v1/oob/units/{id}
// GET    /api/v1/oob/units/{id}/history      // temporal tracking
// POST   /api/v1/oob/compare                 // compare two countries' OOB
// GET    /api/v1/oob/equipment/types         // equipment catalog
```

### 4.4 Simulation Orchestrator (Python / FastAPI)

```python
# sim-orchestrator: manages scenario lifecycle, dispatches to C++ engine

from fastapi import FastAPI, BackgroundTasks, WebSocket
from pydantic import BaseModel
from uuid import UUID, uuid4
from enum import Enum
import asyncio

app = FastAPI(title="AGD Simulation Orchestrator", version="1.0.0")

class SimMode(str, Enum):
    REAL_TIME = "real_time"
    TURN_BASED = "turn_based"
    MONTE_CARLO = "monte_carlo"

class ScenarioConfig(BaseModel):
    name: str
    mode: SimMode
    blue_force_ids: list[UUID]
    red_force_ids: list[UUID]
    theater_bounds: dict           # GeoJSON polygon
    start_time: datetime
    duration_hours: int
    monte_carlo_runs: int = 1000   # for MC mode
    weather_preset: str = "clear"
    fog_of_war: bool = True

class SimulationRun(BaseModel):
    id: UUID
    scenario_id: UUID
    config: ScenarioConfig
    status: str                    # queued, running, paused, complete, error
    progress: float                # 0.0 - 1.0
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

@app.post("/scenarios/{scenario_id}/run", response_model=SimulationRun)
async def start_run(
    scenario_id: UUID,
    config: ScenarioConfig,
    background_tasks: BackgroundTasks,
):
    run = SimulationRun(
        id=uuid4(),
        scenario_id=scenario_id,
        config=config,
        status="queued",
        progress=0.0,
        created_at=datetime.utcnow(),
    )
    await db.save_run(run)
    background_tasks.add_task(dispatch_to_engine, run)
    return run

async def dispatch_to_engine(run: SimulationRun):
    """Sends scenario to C++ sim engine via gRPC, streams events back."""
    async with grpc.aio.insecure_channel('sim-engine:50051') as channel:
        stub = SimEngineStub(channel)
        request = SimRequest(run_id=str(run.id), config=run.config.model_dump())
        async for event in stub.RunScenario(request):
            await kafka_producer.send('sim.events', event.SerializeToString())
            await redis.publish(f'sim:{run.id}', event.SerializeToString())
```

---

## 5. Database Layer

### 5.1 PostgreSQL + PostGIS Schema

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Classification enum
CREATE TYPE classification_level AS ENUM (
    'UNCLASS', 'FOUO', 'SECRET', 'TOP_SECRET', 'TS_SCI'
);

-- Countries table
CREATE TABLE countries (
    code            CHAR(3) PRIMARY KEY,   -- ISO 3166-1 alpha-3
    name            TEXT NOT NULL,
    region          TEXT,
    alliance_codes  TEXT[],                -- e.g. {'NATO', 'QUAD'}
    gdp_usd         BIGINT,
    defense_budget_usd BIGINT,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Military units (hierarchical via parent_id)
CREATE TABLE military_units (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code    CHAR(3) REFERENCES countries(code),
    branch          TEXT NOT NULL,         -- ARMY, NAVY, AIR, SPACE, CYBER, INTEL
    echelon         TEXT,                  -- SQUAD, PLATOON, COMPANY, ... ARMY_GROUP
    name            TEXT NOT NULL,
    short_name      TEXT,
    parent_id       UUID REFERENCES military_units(id),
    location        GEOGRAPHY(POINT, 4326),
    aor             GEOGRAPHY(POLYGON, 4326), -- Area of Responsibility
    classification  classification_level DEFAULT 'UNCLASS',
    confidence      NUMERIC(3,2) CHECK (confidence BETWEEN 0 AND 1),
    data_sources    TEXT[],
    as_of           TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_units_country ON military_units(country_code);
CREATE INDEX idx_units_location ON military_units USING GIST(location);
CREATE INDEX idx_units_parent ON military_units(parent_id);

-- Equipment inventory
CREATE TABLE equipment (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_id         UUID REFERENCES military_units(id) ON DELETE CASCADE,
    type_code       TEXT NOT NULL,         -- from equipment_catalog
    name            TEXT,
    quantity        INTEGER NOT NULL,
    operational_pct NUMERIC(3,2),          -- % combat-ready
    classification  classification_level DEFAULT 'UNCLASS',
    as_of           TIMESTAMPTZ NOT NULL
);

-- Equipment catalog (reference table)
CREATE TABLE equipment_catalog (
    type_code       TEXT PRIMARY KEY,
    category        TEXT,   -- ARMOR, AIRCRAFT, NAVAL, ARTILLERY, MISSILE, SMALL_ARMS
    name            TEXT,
    origin_country  CHAR(3),
    specs           JSONB,                 -- range_km, speed_kph, payload_kg, etc.
    threat_score    NUMERIC(3,2)
);

-- Scenarios
CREATE TABLE scenarios (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    description     TEXT,
    classification  classification_level DEFAULT 'UNCLASS',
    theater_bounds  GEOGRAPHY(POLYGON, 4326),
    created_by      UUID NOT NULL,
    org_id          UUID NOT NULL,
    parent_id       UUID REFERENCES scenarios(id),  -- branching
    tags            TEXT[],
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Simulation runs (TimescaleDB hypertable for event storage)
CREATE TABLE sim_events (
    time            TIMESTAMPTZ NOT NULL,
    run_id          UUID NOT NULL,
    event_type      TEXT NOT NULL,
    entity_id       UUID,
    location        GEOGRAPHY(POINT, 4326),
    payload         JSONB,
    turn_number     INTEGER
);
SELECT create_hypertable('sim_events', 'time');
CREATE INDEX idx_sim_events_run ON sim_events(run_id, time DESC);

-- Intelligence items
CREATE TABLE intel_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type     TEXT,                  -- OSINT, SIGINT, HUMINT, IMINT
    source_url      TEXT,
    title           TEXT,
    content         TEXT,
    language        CHAR(3),
    location        GEOGRAPHY(POINT, 4326),
    entities        JSONB,                 -- extracted entities
    classification  classification_level DEFAULT 'UNCLASS',
    reliability     CHAR(1),               -- NATO admiralty: A-F
    credibility     CHAR(1),               -- 1-6
    published_at    TIMESTAMPTZ,
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    embedding       VECTOR(1536)           -- pgvector for semantic search
);
CREATE INDEX idx_intel_location ON intel_items USING GIST(location);
CREATE INDEX idx_intel_embedding ON intel_items USING ivfflat(embedding vector_cosine_ops);

-- Audit log (append-only, partitioned by month)
CREATE TABLE audit_log (
    id              BIGSERIAL,
    time            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id         UUID NOT NULL,
    session_id      UUID,
    action          TEXT NOT NULL,
    resource_type   TEXT,
    resource_id     UUID,
    classification  classification_level,
    ip_address      INET,
    payload         JSONB,
    PRIMARY KEY (id, time)
) PARTITION BY RANGE (time);
```

### 5.2 Redis Usage

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `session:{token}` | Session cache | 8h |
| `oob:{country}:{branch}` | OOB data cache | 15min |
| `sim:cursor:{scenario}:{user}` | Map cursor positions | 5s |
| `sim:state:{run_id}` | Live sim state snapshot | run lifetime |
| `pub:sim:{run_id}` | Sim event pub/sub channel | n/a |
| `rate:{ip}:{endpoint}` | Rate limit counters | 1min |

### 5.3 Elasticsearch Index Schema

```json
// intel-items index mapping
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "title": { "type": "text", "analyzer": "multilingual" },
      "content": { "type": "text", "analyzer": "multilingual" },
      "entities": {
        "type": "nested",
        "properties": {
          "type": { "type": "keyword" },
          "text": { "type": "keyword" },
          "confidence": { "type": "float" }
        }
      },
      "location": { "type": "geo_point" },
      "published_at": { "type": "date" },
      "source_type": { "type": "keyword" },
      "reliability": { "type": "keyword" },
      "tags": { "type": "keyword" }
    }
  }
}
```

### 5.4 Kafka Topics

| Topic | Producer | Consumers | Schema |
|-------|----------|-----------|--------|
| `sim.events` | sim-engine | collab-svc, reporting-svc, audit-svc | Protobuf SimEvent |
| `intel.raw` | intel-svc ingestion workers | intel-svc NLP pipeline | Protobuf RawIntel |
| `intel.processed` | intel-svc NLP pipeline | ai-svc, elasticsearch sink | Protobuf IntelItem |
| `oob.changes` | oob-svc | sim-orchestrator, notify-svc | Protobuf OOBChange |
| `alerts` | ai-svc, sim-engine | notify-svc | Protobuf Alert |
| `audit` | all services | audit-svc | Protobuf AuditEntry |

---

## 6. Simulation Engine

### 6.1 Architecture

The simulation engine is a standalone C++ (or Rust) binary exposing a gRPC interface. It runs as a stateful process per active simulation run.

```protobuf
// sim_engine.proto
syntax = "proto3";
package agd.sim;

service SimEngine {
  rpc RunScenario(SimRequest) returns (stream SimEvent);
  rpc PauseRun(RunRef) returns (RunStatus);
  rpc ResumeRun(RunRef) returns (RunStatus);
  rpc StepTurn(RunRef) returns (SimEvent);       // turn-based mode
  rpc GetState(RunRef) returns (SimState);
  rpc InjectEvent(EventInjection) returns (Ack); // for training exercises
}

message SimRequest {
  string run_id = 1;
  ScenarioConfig config = 2;
  bytes initial_state = 3;   // serialized OOB snapshot
}

message SimEvent {
  string run_id = 1;
  int64  timestamp_ms = 2;
  int32  turn_number = 3;
  EventType type = 4;
  string entity_id = 5;
  GeoPoint location = 6;
  bytes payload = 7;         // type-specific data
}

enum EventType {
  UNIT_MOVE = 0;
  ENGAGEMENT = 1;
  CASUALTY = 2;
  SUPPLY_CONSUMED = 3;
  OBJECTIVE_CAPTURED = 4;
  AIRSTRIKE = 5;
  NAVAL_ACTION = 6;
  CYBER_ATTACK = 7;
  CBRN_RELEASE = 8;
  PHASE_CHANGE = 9;
}
```

### 6.2 Simulation Modes

#### Turn-Based
- Discrete turns, each player (Red/Blue/Green) submits orders
- Engine resolves combat, movement, logistics per turn
- State is saved after each turn for replay/branch

#### Real-Time
- Continuous time with configurable time acceleration (1x–100x)
- Agent-based units follow AI-driven decision trees
- Events streamed to collab-svc in real-time

#### Monte Carlo
- N runs (default 1000) with randomized outcomes within confidence intervals
- Outputs: probability distributions, outcome histograms, expected casualty ranges
- Parallelized across available CPU cores

```cpp
// Monte Carlo runner (C++ pseudocode)
struct MCResult {
    int runs_completed;
    std::map<std::string, OutcomeDistribution> objective_outcomes;
    CasualtyDistribution blue_casualties;
    CasualtyDistribution red_casualties;
    std::vector<double> duration_distribution;
};

MCResult run_monte_carlo(
    const ScenarioConfig& config,
    const OOBSnapshot& oob,
    int n_runs,
    int n_threads
) {
    std::vector<SimRun> runs(n_runs);
    std::mt19937 rng(config.seed);

    #pragma omp parallel for num_threads(n_threads)
    for (int i = 0; i < n_runs; i++) {
        auto local_rng = rng; // per-thread RNG seeded from master
        std::advance(local_rng, i * 1000);
        runs[i] = run_single(config, oob, local_rng);
    }

    return aggregate_results(runs);
}
```

### 6.3 Combat Resolution Model

```
ATK_SCORE = (firepower_rating × readiness_pct × terrain_modifier × weather_modifier)
           + RNG_NOISE(μ=0, σ=0.15)

DEF_SCORE = (defense_rating × entrenchment × ECM_factor)
           + RNG_NOISE(μ=0, σ=0.10)

OUTCOME_RATIO = ATK_SCORE / DEF_SCORE

if OUTCOME_RATIO > 3.0:   decisive_attacker_victory
elif OUTCOME_RATIO > 1.5: attacker_victory
elif OUTCOME_RATIO > 0.8: contested
elif OUTCOME_RATIO > 0.4: defender_victory
else:                     decisive_defender_victory
```

### 6.4 Logistics Model

- Each unit has supply consumption rates (fuel L/hr, ammo rounds/day, rations/person/day)
- Supply lines are modeled as graph edges with capacity and vulnerability
- Interdiction events reduce edge capacity
- Units below threshold go into degraded readiness states

---

## 7. AI/ML Integration Layer

### 7.1 Architecture

```
ai-svc is a Python/FastAPI service acting as a router and prompt manager.
It sits between application services and LLM providers.
```

```python
# ai-svc: provider abstraction layer
from abc import ABC, abstractmethod
from enum import Enum

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_OLLAMA = "ollama"
    NONE = "none"

class LLMBackend(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str, max_tokens: int) -> str: ...

class AnthropicBackend(LLMBackend):
    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, prompt: str, system: str, max_tokens: int) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class OllamaBackend(LLMBackend):
    """Air-gapped local model via Ollama (e.g., Mixtral, LLaMA 3)"""
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "mixtral"):
        self.base_url = base_url
        self.model = model

    async def complete(self, prompt: str, system: str, max_tokens: int) -> str:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/api/generate", json={
                "model": self.model,
                "prompt": f"{system}\n\n{prompt}",
                "stream": False,
                "options": {"num_predict": max_tokens}
            })
            return r.json()["response"]
```

### 7.2 AI Feature Catalog

| Feature | Prompt Template Key | Fallback Mode |
|---------|--------------------|--------------| 
| Scenario generation | `scenario_builder` | Wizard UI with dropdown fields |
| Intel summarization | `intel_summary` | Manual tagging + keyword extraction |
| Threat assessment | `threat_assess` | Weighted scoring matrix |
| Report drafting | `report_draft` | Template library (JIRA-style) |
| OSINT translation | `translate_osint` | LibreTranslate API → manual |
| Anomaly flagging | `anomaly_detect` | Rule-based threshold alerts |
| Red team suggestion | `red_team` | Historical playbook lookup |
| COA generation | `coa_generate` | Doctrinal COA templates |

### 7.3 Prompt Templates

```python
# Stored in DB, versioned, auditable
PROMPT_TEMPLATES = {
    "scenario_builder": {
        "version": "1.2",
        "system": """You are a military scenario planning assistant for 
        professional defense analysts. Generate structured conflict scenarios 
        based on provided parameters. Output ONLY valid JSON matching the 
        ScenarioConfig schema. Do not include any narrative text outside JSON.""",
        "user_template": """Generate a {mode} scenario with the following parameters:
Theater: {theater_description}
Blue Forces: {blue_force_summary}
Red Forces: {red_force_summary}
Trigger event: {trigger}
Duration: {duration_hours} hours
Objectives: {objectives}

Return a JSON ScenarioConfig object."""
    },
    "threat_assess": {
        "version": "1.0",
        "system": """You are a senior defense intelligence analyst. 
        Assess threat levels using established frameworks (PMESII-PT, ASCOPE).
        Be precise. Cite data. Express uncertainty clearly.""",
        "user_template": """Assess the threat posed by {actor} to {target} 
        given the following Order of Battle data:
{oob_json}

Current intel items (last 30 days):
{intel_summary}

Provide: threat level (1-5), primary vectors, confidence level, and key uncertainties."""
    }
}
```

### 7.4 Non-AI Fallbacks

```python
# Weighted threat matrix (fallback when AI is disabled)
def calculate_threat_score_deterministic(
    actor: Country,
    target: Country,
    weights: ThreatWeights
) -> ThreatScore:
    factors = {
        "military_power_ratio":   actor.military_power / target.military_power,
        "proximity_score":        proximity_score(actor, target),
        "historical_conflict":    actor.conflict_history.get(target.code, 0),
        "alliance_threat":        compute_alliance_threat(actor, target),
        "economic_tension":       compute_economic_tension(actor, target),
        "political_hostility":    actor.political_relations.get(target.code, 0.5),
    }

    weighted_sum = sum(
        v * getattr(weights, k) for k, v in factors.items()
    )
    return ThreatScore(
        overall=min(5.0, weighted_sum),
        factors=factors,
        method="deterministic_matrix",
        confidence=0.6  # always flag as lower confidence than AI
    )
```

---

## 8. Mapping & Geospatial Stack

### 8.1 Tile Server (Air-Gap Support)

```dockerfile
# Self-hosted tile server using Martin (Rust-based, PostGIS-backed)
# docker-compose.yml excerpt
services:
  martin:
    image: ghcr.io/maplibre/martin:latest
    environment:
      DATABASE_URL: postgresql://agd:${DB_PASS}@postgres:5432/agd
    ports:
      - "3000:3000"
    command: --config /config/martin.yaml

  # For air-gap: pre-downloaded MBTiles files
  mbtiles-server:
    image: ghcr.io/consbio/mbtileserver:latest
    volumes:
      - ./tiles:/tilesets
    ports:
      - "8080:8080"
```

### 8.2 Layer Architecture

```typescript
// Layers are registered in a central registry and toggled from LayerPanel
interface MapLayer {
  id: string;
  name: string;
  category: LayerCategory;  // BASE, POLITICAL, MILITARY, INTEL, CBRN, INFRASTRUCTURE
  source: LayerSource;
  defaultVisible: boolean;
  classificationRequired: ClassificationLevel;
  renderer: LayerRenderer;  // CESIUM_PRIMITIVE, DECK_GL, MAPBOX_LAYER
}

const LAYER_REGISTRY: MapLayer[] = [
  {
    id: 'terrain-3d',
    name: '3D Terrain',
    category: 'BASE',
    source: { type: 'cesium-terrain', url: process.env.TERRAIN_URL },
    defaultVisible: true,
    classificationRequired: 'UNCLASS',
    renderer: 'CESIUM_PRIMITIVE',
  },
  {
    id: 'military-units',
    name: 'Military Units (OOB)',
    category: 'MILITARY',
    source: { type: 'api', endpoint: '/api/v1/oob/geojson' },
    defaultVisible: true,
    classificationRequired: 'FOUO',
    renderer: 'DECK_GL',
  },
  {
    id: 'cbrn-plume',
    name: 'CBRN Dispersion Plume',
    category: 'CBRN',
    source: { type: 'simulation', runId: null },
    defaultVisible: false,
    classificationRequired: 'SECRET',
    renderer: 'DECK_GL',
  },
  // ... infrastructure, population, intel overlays
];
```

### 8.3 Geospatial Analysis Operations

```python
# map-svc: common geospatial operations (PostGIS-backed)
from shapely.geometry import Point, Polygon
import geopandas as gpd

async def get_units_in_radius(
    center_lat: float,
    center_lng: float,
    radius_km: float,
    country_codes: list[str] | None = None
) -> list[MilitaryUnit]:
    query = """
        SELECT *, ST_Distance(location::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography) AS dist_m
        FROM military_units
        WHERE ST_DWithin(
            location::geography,
            ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
            $3
        )
        AND ($4::text[] IS NULL OR country_code = ANY($4))
        ORDER BY dist_m;
    """
    return await db.fetch(query, center_lng, center_lat, radius_km * 1000, country_codes)

async def compute_line_of_sight(
    observer: tuple[float, float, float],  # lat, lng, alt_m
    target: tuple[float, float, float]
) -> LosResult:
    """Uses SRTM terrain data via GDAL."""
    ...
```

---

## 9. Intelligence Integration Layer

### 9.1 OSINT Ingestion Pipeline

```
[Source Adapters] → Kafka:intel.raw → [NLP Pipeline] → Kafka:intel.processed → [ES + Postgres + pgvector]
```

```python
# intel-svc: source adapter base class
class OSINTAdapter(ABC):
    source_type: str

    @abstractmethod
    async def fetch(self, since: datetime) -> AsyncIterator[RawIntelItem]: ...

    async def run(self):
        async for item in self.fetch(self.last_run):
            await kafka.send('intel.raw', item.serialize())


class ACLEDAdapter(OSINTAdapter):
    source_type = "ACLED"

    async def fetch(self, since: datetime) -> AsyncIterator[RawIntelItem]:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.acleddata.com/acled/read", params={
                "key": self.api_key,
                "email": self.email,
                "event_date": since.strftime("%Y-%m-%d"),
                "event_date_where": ">=",
                "limit": 1000,
            })
            for row in r.json()["data"]:
                yield RawIntelItem(
                    source_type="OSINT",
                    source_url=f"https://acleddata.com/data/{row['data_id']}",
                    title=f"{row['event_type']} in {row['location']}",
                    content=row["notes"],
                    location={"lat": float(row["latitude"]), "lng": float(row["longitude"])},
                    published_at=datetime.strptime(row["event_date"], "%Y-%m-%d"),
                )

# NLP pipeline step
class IntelNLPPipeline:
    def __init__(self):
        self.ner = spacy.load("en_core_web_trf")  # or custom military NER model
        self.embedder = SentenceTransformer("all-mpnet-base-v2")

    async def process(self, raw: RawIntelItem) -> IntelItem:
        doc = self.ner(raw.content)
        entities = [
            {"type": ent.label_, "text": ent.text, "confidence": 0.85}
            for ent in doc.ents
        ]
        embedding = self.embedder.encode(raw.title + " " + raw.content).tolist()

        return IntelItem(
            **raw.dict(),
            entities=entities,
            embedding=embedding,
            language=detect(raw.content),
        )
```

### 9.2 STIX/TAXII Integration (Cyber Threats)

```python
# Consume STIX bundles from TAXII servers (e.g., MITRE ATT&CK, FS-ISAC)
from taxii2client.v21 import Server, as_pages

class TAXIIAdapter:
    def __init__(self, url: str, username: str, password: str):
        self.server = Server(url, user=username, password=password)

    async def fetch_indicators(self, collection_id: str) -> list[STIXIndicator]:
        collection = self.server.collections[collection_id]
        indicators = []
        for bundle in as_pages(collection.get_objects):
            for obj in bundle.get("objects", []):
                if obj["type"] == "indicator":
                    indicators.append(STIXIndicator.from_dict(obj))
        return indicators
```

---

## 10. Security & Auth

### 10.1 Authentication Flow

```
1. User submits credentials to /api/v1/auth/login
2. auth-svc validates against Keycloak (OIDC)
3. auth-svc issues short-lived JWT (15min) + refresh token (8hr)
4. JWT contains: uid, roles, permissions, classification ceiling
5. All API calls include JWT in Authorization: Bearer header
6. Kong validates JWT signature on every request
7. Individual services check classification level via middleware
```

### 10.2 RBAC Roles

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only access to scenarios and OOB (UNCLASS only) |
| `analyst` | Create/edit intel items, annotate maps, run assessments |
| `planner` | Create/edit scenarios, configure simulations |
| `commander` | Approve scenario publication, access all FOUO data |
| `sim_operator` | Launch and control simulation runs |
| `admin` | User management, system configuration |
| `classification_officer` | Manage classification labels on records |

### 10.3 Data Compartmentalization

```sql
-- Row-level security: users only see records at or below their classification
ALTER TABLE intel_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY intel_classification_policy ON intel_items
    FOR SELECT
    USING (
        classification::text <= current_setting('agd.user_classification')::text
    );

-- Set per-session at connection time
SET agd.user_classification = 'SECRET';
```

### 10.4 Key Security Controls

- **TLS 1.3** everywhere, mTLS between internal services (Istio)
- **Air-gap support**: All external dependencies optionally replaced with local equivalents
- **Audit log**: Immutable, append-only, signed entries with user + session + IP + resource
- **Secrets management**: HashiCorp Vault (or AWS Secrets Manager in cloud deployments)
- **Container scanning**: Trivy in CI pipeline, no HIGH/CRITICAL CVEs in prod images
- **SBOM**: Generated on every release (Syft)
- **Network policies**: Kubernetes NetworkPolicy — deny all, allow-list per service
- **FedRAMP path**: IL4 target for unclassified cloud, IL5/IL6 for on-prem/air-gap

---

## 11. Infrastructure & DevOps

### 11.1 Kubernetes Deployment

```yaml
# Example: sim-orchestrator deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sim-orchestrator
  namespace: agd
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sim-orchestrator
  template:
    spec:
      containers:
        - name: sim-orchestrator
          image: agd/sim-orchestrator:1.0.0
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2"
              memory: "2Gi"
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: agd-secrets
                  key: database-url
            - name: KAFKA_BROKERS
              value: kafka:9092
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
```

### 11.2 Deployment Profiles

| Profile | Description | Key Differences |
|---------|-------------|----------------|
| `cloud` | AWS GovCloud / Azure Government | External tile/imagery SaaS, managed DB |
| `on-prem` | Customer data center | Self-hosted everything |
| `air-gap` | No internet connectivity | All data pre-loaded, local LLM (Ollama), local tiles |
| `dev` | Local developer machine | Docker Compose, mock data, no auth |

```yaml
# docker-compose.dev.yml — single command local dev
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: agd_dev
      POSTGRES_PASSWORD: devpass
    ports: ["5432:5432"]
    volumes:
      - ./db/init:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  elasticsearch:
    image: elasticsearch:8.12.0
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
    ports: ["9200:9200"]

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"

  mbtiles-server:
    image: ghcr.io/consbio/mbtileserver:latest
    volumes:
      - ./tiles:/tilesets        # pre-downloaded OSM tiles
    ports: ["8080:8080"]

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
    ports: ["11434:11434"]       # local LLM for air-gap AI features
```

### 11.3 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml (abbreviated)
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: make test
      - name: Run integration tests
        run: docker-compose -f docker-compose.test.yml up --abort-on-container-exit
      - name: Security scan
        run: trivy fs --exit-code 1 --severity HIGH,CRITICAL .
      - name: SAST
        uses: github/codeql-action/analyze@v3
      - name: Generate SBOM
        run: syft . -o spdx-json > sbom.json

  build:
    needs: test
    steps:
      - name: Build and push images
        run: |
          docker buildx bake --push
      - name: Deploy to staging
        run: kubectl apply -k k8s/overlays/staging
```

### 11.4 Observability Stack

```
Metrics:   Prometheus + Grafana
Logs:      Fluentd → Elasticsearch → Kibana
Traces:    OpenTelemetry → Jaeger
Alerts:    Alertmanager → PagerDuty / email
Dashboards: Grafana (pre-built: API latency, sim throughput, AI cost, error rates)
```

---

## 12. API Reference

### 12.1 REST API Conventions

```
Base URL: https://api.agd.yourdomain.mil/api/v1
Auth:     Authorization: Bearer <jwt>
Format:   application/json
Errors:   RFC 7807 Problem Details
Pagination: ?page=1&per_page=50 (cursor-based for large datasets)
```

### 12.2 Core Endpoint Groups

```
/auth
  POST   /login
  POST   /refresh
  POST   /logout
  GET    /me

/oob
  GET    /countries
  GET    /countries/{code}
  GET    /countries/{code}/forces
  GET    /units/{id}
  POST   /units
  PUT    /units/{id}
  DELETE /units/{id}
  GET    /units/{id}/history
  POST   /compare                 # body: {country_a, country_b, as_of}
  GET    /equipment/catalog

/scenarios
  GET    /scenarios
  POST   /scenarios
  GET    /scenarios/{id}
  PUT    /scenarios/{id}
  DELETE /scenarios/{id}
  POST   /scenarios/{id}/branch   # create variant
  GET    /scenarios/{id}/runs

/simulation
  POST   /scenarios/{id}/runs               # start run
  GET    /runs/{run_id}
  POST   /runs/{run_id}/pause
  POST   /runs/{run_id}/resume
  POST   /runs/{run_id}/step                # turn-based step
  GET    /runs/{run_id}/state
  GET    /runs/{run_id}/events?since=...
  GET    /runs/{run_id}/report              # after-action report

/intel
  GET    /intel
  POST   /intel
  GET    /intel/{id}
  POST   /intel/search                      # full-text + geo + date filter
  POST   /intel/semantic-search             # embedding-based search

/map
  GET    /layers                            # available layers + classification reqs
  GET    /tiles/{z}/{x}/{y}                 # tile proxy (auth-gated)
  GET    /annotations?scenario_id=...
  POST   /annotations
  DELETE /annotations/{id}

/ai
  POST   /ai/scenario/generate
  POST   /ai/intel/summarize
  POST   /ai/threat/assess
  POST   /ai/coa/generate
  POST   /ai/report/draft
  GET    /ai/config                         # current provider config

/reporting
  POST   /reports
  GET    /reports/{id}
  GET    /reports/{id}/download?format=pdf|docx|pptx
```

### 12.3 WebSocket Events

```
Connection: wss://api.agd.yourdomain.mil/ws/collab/{scenario_id}
Auth: ?token={jwt}

// Client → Server
{ "type": "cursor:move", "payload": { "lat": 48.5, "lng": 2.3 } }
{ "type": "annotation:add", "payload": { ...Annotation } }
{ "type": "sim:step", "payload": {} }

// Server → Client
{ "type": "cursor:move", "userId": "abc", "payload": { "lat": 48.5, "lng": 2.3 } }
{ "type": "sim:event", "payload": { ...SimEvent } }
{ "type": "sim:state", "payload": { ...SimState } }
{ "type": "alert", "payload": { "level": "WARNING", "message": "..." } }
{ "type": "annotation:sync", "payload": [...Annotation] }
```

### 12.4 Export Formats

| Format | Endpoint | Notes |
|--------|----------|-------|
| KML/KMZ | `/export/kml/{scenario_id}` | Google Earth compatible |
| GeoJSON | `/export/geojson/{scenario_id}` | All layers |
| NATO APP-6 | `/export/nato/{scenario_id}` | MilSymbol compliant |
| SITREP PDF | `/reports/{id}/download?format=pdf` | Auto-generated brief |
| SITREP DOCX | `/reports/{id}/download?format=docx` | Editable Word doc |
| Raw JSON | `/scenarios/{id}/export` | Full scenario data dump |

---

## 13. Data Sources

### 13.1 Commercial / Subscription

| Provider | Data Type | Update Frequency | API |
|----------|-----------|-----------------|-----|
| Maxar | Satellite imagery | Daily (30cm) | REST |
| Planet Labs | Satellite imagery | Daily (3m) | REST |
| IISS Military Balance | OOB/military data | Annual | Licensed data |
| Jane's Defence | OOB/equipment | Continuous | REST |
| Recorded Future | Threat intel | Real-time | REST/STIX |
| Mandiant | Cyber threat intel | Continuous | REST/STIX |

### 13.2 Open Geospatial

| Source | Use | Format |
|--------|-----|--------|
| Sentinel Hub (ESA) | Satellite imagery | COG/WMS |
| NASA EOSDIS | Multi-spectral imagery | HDF5/GeoTIFF |
| USGS Earth Explorer | Historical imagery | GeoTIFF |
| OpenStreetMap | Base map, infrastructure | PBF/GeoJSON |
| SRTM / ASTER GDEM | Terrain elevation | GeoTIFF |
| Natural Earth | Political boundaries | Shapefile/GeoJSON |
| HDX (OCHA) | Humanitarian datasets | CSV/GeoJSON |

### 13.3 Open Military/Defense

| Source | Data | Update |
|--------|------|--------|
| SIPRI | Arms transfers, defense budgets | Annual |
| ACLED | Conflict events (geocoded) | Continuous |
| UCDP | Armed conflict data | Annual |
| START GTD | Terror incidents | Annual |
| CIA World Factbook | Country profiles | Periodic |
| GlobalFirepower | Military power rankings | Annual |

### 13.4 CBRN / Hazard

| Source | Use |
|--------|-----|
| NOAA HYSPLIT | Atmospheric dispersion modeling |
| EPA ALOHA | Chemical hazard modeling |
| IAEA INES | Nuclear incident scale/data |
| ProMED-mail | Infectious disease outbreak tracking |
| WHO DO News | Disease outbreak news |

---

## 14. Feature Modules

### 14.1 CBRN Module

```python
# cbrn-svc: atmospheric dispersion using HYSPLIT wrapper
class HYSPLITDispersionModel:
    def run(
        self,
        release_point: GeoPoint,
        agent_type: CBRNAgent,           # chem class, bio pathogen, rad isotope
        release_quantity_kg: float,
        met_data: MeteorologicalData,    # wind speed/dir, stability class, temp
        duration_hours: float,
    ) -> DispersionResult:
        """
        Returns a GeoJSON FeatureCollection of concentration contours.
        Contour levels: IDLH, ERPG-2, ERPG-3 (chemical)
                        PAD (radiation)
                        Infectious dose (biological)
        """
        ...

class DispersionResult(BaseModel):
    agent: str
    plume_geojson: dict          # GeoJSON concentration contours
    max_downwind_km: float
    affected_area_km2: float
    casualty_estimate: CasualtyEstimate
    decontamination_zones: list[GeoPolygon]
    evacuation_routes: list[GeoLineString]
    confidence: float
    generated_at: datetime
```

### 14.2 Cyber Module

```python
# cyber-svc: infrastructure dependency graph + ATT&CK mapping
class CyberInfraGraph:
    """
    Nodes: power plants, substations, data centers, financial nodes, 
           comms towers, water treatment, transport hubs
    Edges: dependency relationships (power feeds X, comms connects Y)
    """

    def compute_attack_impact(
        self,
        target_nodes: list[str],
        attack_type: ATTACKTechnique,   # MITRE ATT&CK ICS technique
    ) -> AttackImpactResult:
        """
        BFS/Dijkstra through dependency graph to find cascade effects.
        Returns: affected nodes, estimated civilian impact, recovery time.
        """
        ...

    def generate_attack_path(
        self,
        attacker_capability: ThreatActorProfile,
        target: InfraNode,
    ) -> list[AttackPath]:
        """
        Returns ranked list of paths from initial access to target,
        scored by attacker capability vs defender controls.
        """
        ...
```

### 14.3 Training Mode

```python
# Exercise inject system
class ExerciseInject(BaseModel):
    id: UUID
    exercise_id: UUID
    trigger: InjectTrigger          # TIME, EVENT, MANUAL
    trigger_time: datetime | None
    trigger_event: str | None
    inject_type: str                # INTEL_REPORT, INCIDENT, MESSAGE, MAP_OVERLAY
    content: dict
    target_roles: list[str]         # which players see this inject
    expected_actions: list[str]     # for scoring
    score_weight: float

class ExerciseScorer:
    def score_action(
        self,
        exercise_id: UUID,
        player_action: PlayerAction,
        inject: ExerciseInject,
    ) -> ActionScore:
        """Compares player action to expected_actions, assigns score."""
        ...
```

---

## 15. Development Phases

### Phase 1 — MVP (Months 1–6)
**Goal**: Working geospatial platform with OOB data and basic user management.

- [ ] Project scaffold: monorepo, CI/CD, dev Docker Compose
- [ ] Auth service (Keycloak + JWT + RBAC)
- [ ] PostgreSQL + PostGIS schema (countries, units, equipment)
- [ ] OOB service: CRUD API + top 50 nations seeded
- [ ] Map frontend: Cesium globe, layer panel, basic annotations
- [ ] Self-hosted tile server (MBTiles OSM base map)
- [ ] Scenario management: create, save, branch
- [ ] AI config UI (provider selection, API key entry, fallback toggle)
- [ ] Basic audit logging

**Deliverable**: Web app where analysts can explore a global military OOB on an interactive map, create named scenarios, and configure AI providers.

### Phase 2 — Simulation Core (Months 7–12)
**Goal**: Functional conventional warfare simulation engine.

- [ ] C++/Rust sim engine with gRPC interface
- [ ] Sim orchestrator (Python/FastAPI)
- [ ] Turn-based wargame mode UI
- [ ] Real-time simulation mode
- [ ] Monte Carlo probability modeling
- [ ] Scenario branching + version control
- [ ] After-action report generation
- [ ] AI-assisted scenario builder (natural language → ScenarioConfig)
- [ ] WebSocket collaboration layer (cursors, annotations sync)
- [ ] Logistics and attrition model

**Deliverable**: Analysts can construct conventional conflict scenarios, run turn-based or real-time simulations, view probabilistic outcomes, and replay events.

### Phase 3 — Domain Expansion (Months 13–20)
**Goal**: Multi-domain simulation capability.

- [ ] Cyber module (ATT&CK mapping, infrastructure graph)
- [ ] CBRN dispersion modeling (HYSPLIT integration)
- [ ] Insurgent/asymmetric module (cell structure, IED threat)
- [ ] Terror response planning module
- [ ] AI-assisted intel analysis (entity extraction, threat assessment)
- [ ] OSINT ingestion pipeline (ACLED, UCDP, RSS feeds)
- [ ] Elasticsearch + semantic search (pgvector)
- [ ] CBRN frontend: plume visualization, casualty overlays
- [ ] Civilian impact overlays (population, refugee modeling)

**Deliverable**: Full multi-domain simulation with AI-assisted intelligence analysis.

### Phase 4 — Enterprise (Months 21–28)
**Goal**: Enterprise-grade collaboration, integrations, and deployment hardening.

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

## 16. Competitive Landscape

| Competitor | Core Strength | AGD Differentiator |
|------------|--------------|-------------------|
| Palantir Gotham | Data integration & link analysis | Simulation-first; multi-domain wargaming native |
| CMANO / Command | Air & naval wargaming depth | Enterprise collaboration + domain breadth + AI layer |
| Jane's Intara | Intelligence analysis | Integrated simulation; not just an intel viewer |
| Esri Defense | GIS / spatial analysis | Deeper military modeling; simulation engine; air-gap AI |
| AFSIM (AFRL) | High-fidelity air sim | Multi-domain; accessible UI; built for enterprise not R&D |
| Syniti / OneSim | Logistics modeling | Broader threat domains; visual simulation |

---

## 17. Strategic Considerations

### 17.1 Target Customers

| Segment | Examples | Buying Process |
|---------|----------|----------------|
| Government defense agencies | DoD, DIA, NGA, allied MoDs | FedRAMP/IL procurement, contract vehicles (GSA, CIO-SP4) |
| Defense primes | Raytheon, L3Harris, Northrop | B2B licensing, integration partnerships |
| Think tanks | RAND, CSIS, IISS | Academic licensing, grant-funded |
| War colleges | NDU, NWC, CGSC | Educational licensing, training contracts |

### 17.2 Classification Strategy

| Build | Hosting | Data | Staffing |
|-------|---------|------|----------|
| Unclassified | AWS GovCloud / Azure Gov (IL4) | Open + commercial sources | No clearance required for most roles |
| Secret | IL5 accredited environment | Classified feeds | Clearances required |
| TS/SCI | IL6 / on-prem air-gap | Full classified | Full clearances + program access |

**Recommendation**: Ship unclassified first to maximize addressable market and validate product. Design classification-aware from day one so upgrade path is architectural, not a rewrite.

### 17.3 Licensing Model

| Tier | Target | Pricing Model |
|------|--------|--------------|
| Analyst | Individual analysts | Per-seat SaaS subscription |
| Team | Small teams (≤20 users) | Flat monthly, per-team |
| Enterprise | Agencies, primes | Unlimited seats, annual contract + support |
| Air-Gap | Classified environments | Perpetual license + annual maintenance |
| Academic | War colleges | Discounted annual, data-limited |

### 17.4 Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Export control (ITAR/EAR) | Legal review; limit access by geography; no offensive capability features |
| Data classification mishandling | Row-level security; classification labels on all records; mandatory training |
| AI hallucination in threat assessments | Non-AI fallback always shown; AI outputs clearly marked; confidence scores required |
| Simulation over-reliance | Documentation and training: simulations are decision support, not ground truth |
| Vendor lock-in (LLM) | Provider abstraction layer; local LLM (Ollama) always a supported option |

---

**_End of Build Sheet — Version 2.0_**  
**Apex Global Defense | Engineering Document | UNCLASSIFIED**

# AGD Contract Governance

> **Status:** ACTIVE | **Reference:** improvements.md Priority E  
> **Last updated:** 2026-02-26

This document defines the SemVer policy, compatibility windows, and event schema
governance for all AGD REST and gRPC contracts.

---

## 1. SemVer Policy

All AGD service contracts (REST API paths, gRPC service definitions, and event
schemas) follow [Semantic Versioning 2.0](https://semver.org/):

| Change type | Version bump | Example |
|-------------|-------------|---------|
| Breaking (remove field, change type, rename RPC) | **Major** (X.0.0) | Remove a required request field |
| Additive (new optional field, new RPC, new event type) | **Minor** (x.Y.0) | Add `ForceStatus` to `SimState` |
| Bugfix / doc only | **Patch** (x.y.Z) | Fix typo in field description |

### Current contract versions

| Contract | Version | Location |
|----------|---------|----------|
| `agd.sim` gRPC (sim-engine) | **1.3.0** | `services/sim-engine/proto/sim_engine.proto` |
| REST API v1 (all HTTP services) | **1.0.0** | per-service `main.py` + OpenAPI at `/docs` |
| `sim.events` schema (sim event payloads) | **1.2.0** | `docs/contract-governance.md` §3 |

### Versioning conventions

* The gRPC package version is embedded as a comment in `sim_engine.proto`.
* REST APIs are versioned by URL prefix (`/api/v1/`). A new major version
  introduces `/api/v2/` while `/api/v1/` remains available for one migration
  window (90 days in production, negotiable in dev).
* gRPC services use proto field numbers as the compatibility wire. Old clients
  ignore unknown fields; new clients treat missing fields as proto3 defaults.

---

## 2. Compatibility Windows

| Scenario | Policy |
|----------|--------|
| Proto additive change (new field, new RPC) | **No window needed** — backward compatible |
| Proto breaking change (field removal, type change) | **90-day migration window** in production; update all consumers before removing |
| REST endpoint removed | **90-day deprecation** notice via `Deprecation` response header |
| REST endpoint renamed / URL change | Redirect (HTTP 301) for 90 days, then remove |
| Event payload field removed | **60-day migration window** + update all consumers |

### Breaking change procedure

1. Open a GitHub issue labelled `breaking-change` with the proposed change.
2. Update the major version in the proto or API.
3. Publish migration guide in `docs/migrations/`.
4. Deploy with old + new side-by-side until all consumers are migrated.
5. Remove old version after migration window expires.

---

## 3. Canonical Event Schema Governance

All sim events produced by `sim-engine` and consumed by `sim-orchestrator`,
`collab-svc`, and frontend clients must conform to the following schema.

### 3.1 Envelope (all event types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | `string (UUID)` | ✅ | Simulation run identifier |
| `timestamp_ms` | `int64` | ✅ | Wall-clock timestamp (milliseconds since Unix epoch) |
| `turn_number` | `int32` | ✅ | Sim turn this event belongs to (1-indexed) |
| `type` | `EventType` (enum) | ✅ | Event category (see §3.2) |
| `entity_id` | `string (UUID)` | ✅ | Unit / actor that generated the event |
| `location` | `{lat, lng}` | optional | Geographic location of the event |
| `payload` | `bytes (JSON)` | ✅ | Type-specific payload (see §3.3) |

### 3.2 EventType enum values (v1.2.0)

| Value | Int | Introduced |
|-------|-----|-----------|
| `UNIT_MOVE` | 0 | v1.0.0 |
| `ENGAGEMENT` | 1 | v1.0.0 |
| `CASUALTY` | 2 | v1.0.0 |
| `SUPPLY_CONSUMED` | 3 | v1.0.0 |
| `OBJECTIVE_CAPTURED` | 4 | v1.0.0 |
| `AIRSTRIKE` | 5 | v1.0.0 |
| `NAVAL_ACTION` | 6 | v1.0.0 |
| `CYBER_ATTACK` | 7 | v1.0.0 |
| `CBRN_RELEASE` | 8 | v1.0.0 |
| `PHASE_CHANGE` | 9 | v1.0.0 |
| `RESUPPLY` | 10 | v1.1.0 |

### 3.3 Typed payload schemas

#### ENGAGEMENT
```json
{
  "turn":             1,
  "blue_casualties":  12,
  "red_casualties":   25,
  "atk_score":        0.92,
  "def_score":        0.75,
  "ratio":            1.227,
  "outcome":          "attacker_victory"
}
```

#### CASUALTY
```json
{
  "turn":             1,
  "blue_casualties":  8,
  "red_casualties":   14
}
```

#### OBJECTIVE_CAPTURED
```json
{
  "turn":      2,
  "objective": "OBJ-3",
  "side":      "BLUE"
}
```

#### RESUPPLY
```json
{
  "turn":              3,
  "side":              "RED",
  "ammo_restored":     0.18,
  "fuel_restored":     0.14,
  "rations_restored":  0.07
}
```

#### UNIT_MOVE
```json
{
  "turn": 1,
  "side": "BLUE"
}
```

#### SUPPLY_CONSUMED
```json
{
  "turn": 1,
  "side": "BLUE"
}
```

#### AIRSTRIKE
```json
{
  "turn": 2,
  "side": "BLUE"
}
```

### 3.4 Producer / consumer validation

| Producer | Consumer | Validation mechanism |
|----------|----------|---------------------|
| `sim-engine` (gRPC stream) | `sim-orchestrator` | Proto wire format + `grpc_client.py` deserialization |
| `sim-orchestrator` (Redis publish) | `collab-svc` | JSON schema; consumers log unknown fields |
| `sim-orchestrator` (DB store) | Reporting, AAR | Column type constraints in `sim_events` table |
| `sim-orchestrator` (REST API) | Frontend | OpenAPI spec at `/docs` |

### 3.5 Governance process for new event types

1. Open a GitHub issue labelled `event-schema` with the proposed `EventType`
   and payload schema.
2. Increment the `sim.events` schema **minor** version in this document.
3. Add the new value to `EventType` in `sim_engine.proto` (use the next
   available integer; **never reuse** a deleted value).
4. Update `EventType` enum in `services/sim-orchestrator/app/models.py`.
5. Add a payload example to §3.3 in this document.
6. Update any consumers that must handle the new type.

---

## 4. Protobuf Compatibility Checks (CI)

The CI pipeline runs `buf lint` on every push to validate that proto files
conform to the style guide and that no breaking changes are introduced without
an explicit approval.

See `.github/workflows/ci.yml` job `proto-lint` for configuration.

To run locally:
```bash
cd services/sim-engine
buf lint proto/
buf breaking --against '.git#branch=main' proto/
```

---

## 5. REST API Versioning Conventions

* All REST routes are prefixed with `/api/v1/`.
* New resources are added under `/api/v1/` (minor bump).
* Breaking changes (renamed path, removed parameter) introduce `/api/v2/`
  and the old path is deprecated with a `Deprecation` header.
* OpenAPI specs are served at `GET /docs` (Swagger UI) and `GET /openapi.json`.

---

*AGD Engineering — Contract Governance v1.0 | UNCLASSIFIED*

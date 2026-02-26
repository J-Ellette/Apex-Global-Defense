# AGD Consolidated Improvements

## Merge Policy

This document combines:
- `copilot-suggestions.md` (primary source of truth when overlap/conflict exists)
- `openai-suggestions.md`
- `claude-suggestions.md`

When suggestions were redundant or contrary, `copilot-suggestions.md` was favored.

## Executive Summary

AGD has broad feature coverage and a working integration baseline. The highest-value next step is simulation fidelity: move `sim-engine` from prototype integration behavior to calibrated, deterministic, persistent simulation capability, while hardening CI, contracts, and operational reliability.

## Priority A — Simulation Engine Fidelity Program (Primary)

The current engine is integration-ready but still a prototype. To be high-fidelity, it needs real simulation logic, not synthetic in-memory events.

### Remaining Work

- ✅ Replace deterministic stub event generation with a real stateful combat model (force state, terrain/weather effects, doctrine-driven decisions) defined in `buildsheet.md`.
- ✅ Implement full turn resolver and real-time tick loop with deterministic replay (seeded RNG, snapshotting, rewind/branch support).
- ✅ Build proper Monte Carlo execution (statistical aggregation, confidence intervals) instead of placeholder outcomes.
- ✅ Implement logistics graph modeling (supply drain per turn, interdiction effects, resupply restoration, readiness degradation) per the logistics spec in `buildsheet.md`.
- ✅ Add persistent engine state/checkpointing (turn snapshots, `GetCheckpoint` gRPC RPC for replay/branch-on-turn).
- ✅ Expand gRPC contracts/payload schema for richer unit state (ForceStatus), casualties, objectives, and typed event payloads; backward compatible with orchestrator.
- ✅ Add validation and calibration harnesses (golden scenarios, expected outcome bands, regression drift checks) so model changes are measurable.
- Add performance hardening (profiling, CPU/GPU path where needed, bounded latency/throughput SLAs) plus observability and integration tests for gRPC-first/fallback paths. ⏳ Future
- Parallel MC execution (ProcessPoolExecutor) — deferred pending multiprocessing-safe execution context. ⏳ Future

## Priority B — CI/CD and Build Hygiene (Merged from OpenAI + Claude)

- ✅ Fix stale service matrices in `.github/workflows/ci.yml` and `Makefile` so only real services are tested/linted/formatted, and all implemented services are included.
- ✅ Add `docker-compose.test.yml` (or equivalent integration test harness) so integration jobs run reliably.
- ✅ Expand image publishing from single-service to matrix-based multi-service builds.
- ✅ Add a repo guard check that fails CI when service lists in CI/Makefile drift from `services/` directory reality.
- ✅ Ensure Python test matrix excludes non-existent `ai-svc` until implemented.

## Priority C — Runtime Reliability and Data Controls

- ✅ Make orchestrator fallback policy explicit by environment (dev: allow stub fallback, production: fail closed).
- ✅ Add health reporting that surfaces engine mode (`grpc` vs `fallback`) and degraded state.
- ✅ Add migration smoke validation for all schema init/migration paths (`scripts/db-migrate-smoke.sh` + CI job).
- Keep DB dev-fallback behavior explicit and separate from production expectations (TimescaleDB/pgvector availability).
- ✅ Add retention/partitioning + archival policy for `sim_events` and `audit_log`.

## Priority D — Security and Compliance Hardening

- ✅ Replace inline secrets in dev compose with environment-variable driven placeholders and committed `.env.example` templates (root and frontend).
- ✅ Add CI secret scanning and policy checks (gitleaks).
- ✅ Add artifact provenance/signing and release attestation for deployable images (`actions/attest-build-provenance`).
- Standardize request-scoped classification context setting and test RLS visibility behavior by classification tier.

## Priority E — Architecture and Contract Governance

- ✅ Create shared internal Python package for duplicated auth/classification/error logic across services (`services/agd-shared/`).
- ✅ Establish SemVer policy for REST/gRPC contracts and compatibility windows (`docs/contract-governance.md`).
- ✅ Add protobuf/schema compatibility checks in CI (`buf lint` job, `buf.yaml`).
- ✅ Define canonical event schema governance for `sim.events` (producer/consumer validation) in `docs/contract-governance.md`.

## Priority F — Observability and Operational Readiness

- ✅ Add incident runbooks for top failure classes (`docs/runbooks/`).
- Standardize OpenTelemetry traces and correlation IDs across services.
- Add dashboards for simulation latency, event throughput, queue lag, error rate, and run success/failure.

## Priority G — Developer Experience and Documentation

- ✅ Add a root docs-status matrix that maps buildsheet checklist items to implementation files and test evidence (`docs/status-matrix.md`).
- ✅ Add one-command smoke script under `scripts/` for JWT + run + state/events verification (`scripts/smoke-test.sh`).
- ✅ Add service-scoped make targets for faster local iteration (`svc-test`, `svc-lint`).
- ✅ Keep buildsheet/README/progress docs synchronized with explicit status tags: `complete`, `prototype`, `deferred`, `future`.

## Suggested 4-Milestone Delivery Sequence

### Milestone 1 — Determinism Foundation
- combat state model
- deterministic turn resolver + tick loop
- replay/snapshot format v1
- orchestrator↔engine integration assertions

### Milestone 2 — Logistics + Monte Carlo Fidelity
- parallel MC executor
- logistics network model
- calibration baseline and confidence outputs
- load/perf baseline

### Milestone 3 — Persistence + Recovery + Scale
- checkpointing and crash-safe resume
- long-run memory controls
- event archival/compaction

### Milestone 4 — Production Readiness Gates
- golden scenario validation harness
- drift detection in CI
- SLO dashboards + incident runbooks
- release checklist and attestation

## Notes on Redundancies/Conflicts Resolved

- Simulation roadmap conflicts were resolved in favor of `copilot-suggestions.md` wording and ordering.
- CI/Makefile drift, missing test-compose, and env-template recommendations were merged from OpenAI/Claude because they complement the Copilot plan.
- RLS concern from earlier Claude notes is treated as implementation-verification work (test and document runtime classification context), not as a presumed schema bug.

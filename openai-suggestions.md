# OpenAI Improvement Suggestions for AGD

## Scope
Based on current repository state and docs review:
- `buildsheet.md`
- `README.md`
- key implementation files (`Makefile`, `.github/workflows/ci.yml`, `docker-compose.dev.yml`, `db/init/*.sql`)

## Priority 0 (Fix Immediately)

### 1. Tooling and CI service lists are out of sync with the repo
- `Makefile` still references non-existent services (`map-svc`, `notify-svc`, `audit-svc`, `ai-svc`) and misses multiple implemented Python services.
- `.github/workflows/ci.yml` has the same stale matrix entries.
- Impact: CI and local `make test/lint/fmt` are failing for wrong reasons and skipping real services.
- Suggestion:
  1. Generate service matrices dynamically from `services/` directories by language.
  2. Or keep explicit lists, but make a CI check that fails if list != actual directories.

### 2. Missing `docker-compose.test.yml` breaks integration test job
- CI calls `docker compose -f docker-compose.test.yml ...`, but file does not exist.
- Impact: integration job is dead-on-arrival.
- Suggestion:
  1. Add `docker-compose.test.yml` with minimal dependencies and tested services.
  2. Use `--exit-code-from` to propagate failures correctly.

### 3. Missing `.env.example` files despite README instructions
- README says to copy `.env.example`, but both root and `frontend/.env.example` are absent.
- Impact: onboarding friction and inconsistent local setup.
- Suggestion:
  1. Add `/.env.example` for backend/dev compose variables.
  2. Add `/frontend/.env.example` for all `VITE_*` variables.

## Priority 1 (Security and Data Controls)

### 4. RLS session classification setting appears undocumented in runtime code path
- DB policies rely on `current_setting('agd.user_classification', TRUE)`.
- Search found this setting in SQL migrations only, not set from service code.
- Impact: RLS may default to the fallback path and not reflect caller clearance as intended.
- Suggestion:
  1. Set `SET LOCAL agd.user_classification = ...` on each request transaction (or per connection with reset discipline).
  2. Add integration tests proving visibility behavior for UNCLASS/FOUO/SECRET users.

### 5. Dev secrets are hardcoded in compose and repeated in docs
- `docker-compose.dev.yml` includes static passwords and JWT secret.
- Impact: bad secret hygiene and accidental reuse risk.
- Suggestion:
  1. Replace inline values with `${VAR}` sourced from local `.env`.
  2. Keep only non-sensitive placeholders in docs and examples.

## Priority 2 (Reliability and Maintainability)

### 6. `db-migrate` target is incomplete for current schema model
- `make db-migrate` only runs `001_schema.sql` while repo has `001`–`015` init scripts.
- Impact: partial schema state and drift between environments.
- Suggestion:
  1. Move to ordered migration tool (Flyway/golang-migrate/Alembic-style approach).
  2. Add migration smoke test in CI that initializes a blank DB and verifies all migrations apply.

### 7. Docs drift between buildsheet and implementation reality
- Buildsheet still treats some services as active architecture components while they are not in `services/` (`map-svc`, `ai-svc`, `notify-svc`, `audit-svc`).
- README marks `sim-engine` prototype present; buildsheet Phase 2 checklist still marks C++/Rust sim engine unchecked.
- Impact: confusion for contributors and misleading planning status.
- Suggestion:
  1. Define one source-of-truth status table (recommended in `README.md`).
  2. Add lightweight doc-consistency check script for service inventory and status fields.

### 8. Python auth/classification logic is duplicated across services
- `services/*/app/auth.py` exists in 12 Python services.
- Impact: security fixes are expensive and likely to drift.
- Suggestion:
  1. Create shared internal package (`services/_shared/py/agd_common`).
  2. Centralize JWT validation, role checks, classification helpers, and common HTTP error models.

### 9. Local dev startup is heavy and all-or-nothing
- `docker-compose.dev.yml` starts many heavyweight dependencies by default.
- Impact: slower contributor feedback loop.
- Suggestion:
  1. Add Compose profiles (e.g., `core`, `intel`, `full`).
  2. Default `make dev` to a lighter profile and keep `make dev-full` for full stack.

## Quick 1-Week Action Plan

1. Fix Makefile and CI service matrices.
2. Add `docker-compose.test.yml`.
3. Add root and frontend `.env.example` files.
4. Implement `agd.user_classification` session setting and tests.
5. Replace hardcoded compose secrets with env vars.

## Expected Outcome
If you execute the 1-week plan, you’ll eliminate the main false negatives in CI, improve security posture, and reduce onboarding friction without changing core product behavior.

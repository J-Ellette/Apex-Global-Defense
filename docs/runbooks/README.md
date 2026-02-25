# AGD Incident Runbooks

**Classification:** UNCLASSIFIED  
**Status:** Active

This directory contains incident response runbooks for the Apex Global Defense (AGD) platform. Each runbook covers a specific failure class with triage steps, mitigation actions, and escalation paths.

---

## Runbooks

| File | Failure Class | Severity |
|------|--------------|---------|
| [db-init-migration.md](./db-init-migration.md) | DB init/migration failure or partial schema drift | High |
| [sim-engine-grpc-outage.md](./sim-engine-grpc-outage.md) | sim-engine gRPC unavailable or degraded | High |
| [kafka-backpressure.md](./kafka-backpressure.md) | Kafka backpressure or consumer lag | Medium |
| [auth-jwt-misconfiguration.md](./auth-jwt-misconfiguration.md) | Auth/JWT misconfiguration causing 401/403 errors | High |

---

## Severity Definitions

| Severity | Definition |
|----------|-----------|
| **Critical** | Total platform outage or data loss risk — page on-call immediately |
| **High** | Core workflow unavailable or security control degraded — address within 1 hour |
| **Medium** | Degraded capability with workaround available — address within 4 hours |
| **Low** | Minor issue or cosmetic defect — address in next sprint |

---

## General Response Principles

1. **Triage first** — confirm the failure before taking action
2. **Check health endpoints** — all services expose `GET /health`; use `make smoke-test` for a full sweep
3. **Check logs** — structured JSON logs from all services; filter by `run_id` or `scenario_id` for correlation
4. **Do not restart without evidence** — a restart may mask the root cause; capture logs first
5. **Escalate if unsure** — contact the on-call engineer if the issue is not covered by a runbook

---

*Apex Global Defense | Operations | UNCLASSIFIED*

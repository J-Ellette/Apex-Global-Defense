# Runbook: sim-engine gRPC Outage

**Failure Class:** sim-engine gRPC service unavailable or degraded  
**Severity:** High  
**Services Affected:** `sim-orchestrator` (port 8085), downstream simulation UI

---

## Symptoms

- Simulation runs transition to `error` status immediately after starting
- `sim-orchestrator` logs contain: `gRPC sim-engine failed for run <id>`
- `GET /runs/{id}` returns `status: "error"` with `error_message` referencing gRPC connection failure
- Health endpoint reports `engine_mode: "grpc"` but runs fail
- In dev/test: runs may silently fall back to stub engine (check logs)
- In production: runs fail closed immediately (expected behavior — do not treat as a bug)

---

## Immediate Triage

```bash
# 1. Check sim-engine container health
docker compose -f docker-compose.dev.yml ps sim-engine
docker compose -f docker-compose.dev.yml logs sim-engine | tail -50

# 2. Test gRPC port reachability
docker compose -f docker-compose.dev.yml exec sim-orchestrator \
  nc -zv sim-engine 50051

# 3. Check orchestrator health endpoint for engine mode
curl -sf http://localhost:8085/health | jq .
# Expected: {"status":"ok","engine_mode":"grpc","engine_addr":"sim-engine:50051"}

# 4. Check orchestrator logs for gRPC errors
docker compose -f docker-compose.dev.yml logs sim-orchestrator | grep -i grpc | tail -20
```

---

## Common Causes and Fixes

### sim-engine container crashed or not started

**Fix:**
```bash
docker compose -f docker-compose.dev.yml up -d sim-engine
docker compose -f docker-compose.dev.yml logs sim-engine --follow
```

### sim-engine failed to compile (Rust build error in dev)

**Fix:**
```bash
cd services/sim-engine
cargo build --release
# Fix any compilation errors, then rebuild the Docker image
docker compose -f docker-compose.dev.yml build sim-engine
docker compose -f docker-compose.dev.yml up -d sim-engine
```

### gRPC address misconfiguration

**Cause:** `SIM_ENGINE_GRPC_ADDR` env var is wrong or DNS resolution fails.

**Fix:**
```bash
# Verify the address in compose config
grep SIM_ENGINE_GRPC_ADDR docker-compose.dev.yml

# Within the orchestrator container, resolve the hostname
docker compose -f docker-compose.dev.yml exec sim-orchestrator getent hosts sim-engine
```

### gRPC proto version mismatch

**Cause:** `sim_engine_pb2.py` stubs in `sim-orchestrator` do not match the `.proto` served by `sim-engine`.

**Fix:** Regenerate Python stubs from the `.proto` file:
```bash
cd services/sim-engine
# Copy the proto to orchestrator and regenerate
cp proto/sim_engine.proto ../sim-orchestrator/
cd ../sim-orchestrator
python -m grpc_tools.protoc -I. --python_out=app/engine --grpc_python_out=app/engine sim_engine.proto
```

### Temporary network partition (Kubernetes)

**Fix:**
1. Verify the `sim-engine` Pod is Running: `kubectl get pods -n agd | grep sim-engine`
2. Check Pod logs: `kubectl logs deployment/sim-engine -n agd --tail=50`
3. Restart if unhealthy: `kubectl rollout restart deployment/sim-engine -n agd`

---

## Degraded Mode Operation

| Environment | Behavior when gRPC fails |
|-------------|--------------------------|
| `development` / `test` | Automatically falls back to stub engine; run completes with synthetic events |
| `production` | Fails closed — run transitions to `error`; no silent fallback |

To temporarily re-enable stub fallback in production (only with explicit approval):
```bash
# Override in compose or k8s deployment env:
USE_GRPC_SIM_ENGINE=false
# Then restart sim-orchestrator
```

---

## Validation After Fix

```bash
# Health check
curl -sf http://localhost:8085/health | jq .

# Start a test run (requires valid JWT)
make smoke-test
```

---

## Escalation

If the Rust `sim-engine` binary panics with an unrecoverable error, capture the full logs and escalate to the sim-engine team. Do not attempt to patch the Rust binary in production without a full build + integration test cycle.

---

*Apex Global Defense | Operations | UNCLASSIFIED*

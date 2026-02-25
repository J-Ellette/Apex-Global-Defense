# Runbook: Kafka Backpressure / Unavailable

**Failure Class:** Kafka consumer lag, backpressure, or Kafka broker unavailable  
**Severity:** Medium  
**Services Affected:** Event bus consumers (currently bridged via Redis pub/sub in dev; Kafka used in production event pipeline)

---

## Symptoms

- `sim-orchestrator` or `collab-svc` logs show Kafka connection errors or timeouts
- Simulation event fan-out to connected WebSocket clients is delayed or stopped
- Redis pub/sub messages published but Kafka consumers are not processing
- Consumer lag visible in Kafka UI / monitoring dashboards
- `GET /runs/{id}/events` returns fewer events than expected (events not yet consumed/persisted)

---

## Immediate Triage

```bash
# 1. Check Kafka broker health (dev)
docker compose -f docker-compose.dev.yml ps kafka
docker compose -f docker-compose.dev.yml logs kafka | tail -30

# 2. Check consumer lag (if kafka-topics tool is available)
docker compose -f docker-compose.dev.yml exec kafka \
  kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --all-groups

# 3. Check collab-svc logs for Kafka errors
docker compose -f docker-compose.dev.yml logs collab-svc | grep -i kafka | tail -20

# 4. Check Redis pub/sub (the collab-svc bridge uses Redis in dev)
docker compose -f docker-compose.dev.yml exec redis redis-cli MONITOR
```

---

## Common Causes and Fixes

### Kafka broker not started or crashed

**Fix:**
```bash
docker compose -f docker-compose.dev.yml up -d kafka
docker compose -f docker-compose.dev.yml logs kafka --follow
```

### Consumer group lag accumulation

**Cause:** A slow consumer (e.g., `collab-svc` processing backlog) is falling behind the producer.

**Fix:**
1. Check consumer group lag (see triage step 2 above)
2. Scale the consumer horizontally if needed (Kubernetes: increase replica count)
3. If the lag is non-critical, allow it to drain organically
4. If the topic is backed up beyond retention window, reset the consumer offset:
```bash
docker compose -f docker-compose.dev.yml exec kafka \
  kafka-consumer-groups.sh --bootstrap-server kafka:9092 \
  --group <group-id> --topic sim.events --reset-offsets --to-latest --execute
```
> **Warning:** Resetting to latest will skip unprocessed messages. Only do this when old events are confirmed non-essential.

### Kafka disk full (retention exceeded)

**Fix:**
1. Check Kafka log directory disk usage
2. Reduce retention period for `sim.events`: `retention.ms=86400000` (24h default)
3. Add disk or clean up old log segments

### Kafka port conflict or network issue

**Fix:**
```bash
# Verify port 9092 is reachable from service containers
docker compose -f docker-compose.dev.yml exec sim-orchestrator \
  nc -zv kafka 9092
```

---

## Dev vs Production Behavior

In the dev stack, `collab-svc` uses **Redis pub/sub** (not Kafka) to relay `sim:{run_id}` events to WebSocket clients. Kafka is present in `docker-compose.dev.yml` for infrastructure completeness, but the critical fan-out path is Redis.

If Redis is the actual issue, see [auth-jwt-misconfiguration.md](./auth-jwt-misconfiguration.md) for Redis connectivity triage, or restart Redis:
```bash
docker compose -f docker-compose.dev.yml restart redis
```

---

## Validation After Fix

```bash
# Verify Kafka broker is healthy
docker compose -f docker-compose.dev.yml exec kafka \
  kafka-broker-api-versions.sh --bootstrap-server kafka:9092

# Check consumer lag is draining
docker compose -f docker-compose.dev.yml exec kafka \
  kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --all-groups

# Run smoke test to verify event flow end-to-end
make smoke-test
```

---

## Escalation

If consumer lag exceeds 1 million messages or the broker is in an unrecoverable state (corrupted log segments), escalate to the platform engineering team. Do not attempt to manually delete Kafka log segments without team review.

---

*Apex Global Defense | Operations | UNCLASSIFIED*

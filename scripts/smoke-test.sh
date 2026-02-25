#!/usr/bin/env bash
# scripts/smoke-test.sh — One-command smoke test for a running AGD dev environment.
#
# Usage:
#   ./scripts/smoke-test.sh [--base-url <url>]
#
# Prerequisites:
#   - A running AGD dev stack (make dev) or custom base URL
#   - curl, jq (optional but recommended)
#
# What it tests:
#   1. Health endpoints on all services
#   2. Auth login → JWT acquisition
#   3. OOB countries list (authenticated)
#   4. Simulation run creation (stub mode)
#   5. Simulation state/events retrieval

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
AUTH_URL="${AUTH_URL:-http://localhost:8082}"
OOB_URL="${OOB_URL:-http://localhost:8083}"
SIM_URL="${SIM_URL:-http://localhost:8085/api/v1}"
CYBER_URL="${CYBER_URL:-http://localhost:8086/api/v1}"
CBRN_URL="${CBRN_URL:-http://localhost:8087/api/v1}"
ASYM_URL="${ASYM_URL:-http://localhost:8088/api/v1}"
TERROR_URL="${TERROR_URL:-http://localhost:8089/api/v1}"
INTEL_URL="${INTEL_URL:-http://localhost:8090/api/v1}"
CIVILIAN_URL="${CIVILIAN_URL:-http://localhost:8091/api/v1}"
REPORTING_URL="${REPORTING_URL:-http://localhost:8092/api/v1}"
ECON_URL="${ECON_URL:-http://localhost:8093/api/v1}"
INFOOPS_URL="${INFOOPS_URL:-http://localhost:8094/api/v1}"
GIS_URL="${GIS_URL:-http://localhost:8095/api/v1}"
TRAINING_URL="${TRAINING_URL:-http://localhost:8096/api/v1}"
COLLAB_URL="${COLLAB_URL:-http://localhost:8084}"

AGD_USER="${AGD_USER:-admin}"
AGD_PASS="${AGD_PASS:-adminpass}"

PASS=0
FAIL=0

# ── Helpers ───────────────────────────────────────────────────────────────────
green() { printf "\033[0;32m%s\033[0m\n" "$*"; }
red()   { printf "\033[0;31m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n" "$*"; }

check() {
  local label="$1"
  local cmd="$2"
  printf "  %-55s" "$label"
  if eval "$cmd" >/dev/null 2>&1; then
    green "PASS"
    PASS=$((PASS + 1))
  else
    red "FAIL"
    FAIL=$((FAIL + 1))
  fi
}

# ── Phase 1: Health checks ────────────────────────────────────────────────────
bold "Phase 1 — Health Checks"
check "auth-svc"         "curl -sf ${AUTH_URL}/health"
check "oob-svc"          "curl -sf ${OOB_URL}/health"
check "collab-svc"       "curl -sf ${COLLAB_URL}/health"
check "sim-orchestrator" "curl -sf ${SIM_URL%/api/v1}/health"
check "cyber-svc"        "curl -sf ${CYBER_URL%/api/v1}/health"
check "cbrn-svc"         "curl -sf ${CBRN_URL%/api/v1}/health"
check "asym-svc"         "curl -sf ${ASYM_URL%/api/v1}/health"
check "terror-svc"       "curl -sf ${TERROR_URL%/api/v1}/health"
check "intel-svc"        "curl -sf ${INTEL_URL%/api/v1}/health"
check "civilian-svc"     "curl -sf ${CIVILIAN_URL%/api/v1}/health"
check "reporting-svc"    "curl -sf ${REPORTING_URL%/api/v1}/health"
check "econ-svc"         "curl -sf ${ECON_URL%/api/v1}/health"
check "infoops-svc"      "curl -sf ${INFOOPS_URL%/api/v1}/health"
check "gis-export-svc"   "curl -sf ${GIS_URL%/api/v1}/health"
check "training-svc"     "curl -sf ${TRAINING_URL%/api/v1}/health"

# ── Phase 2: Auth — obtain JWT ───────────────────────────────────────────────
bold "Phase 2 — Authentication"
TOKEN=""
TOKEN=$(curl -sf -X POST "${AUTH_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${AGD_USER}\",\"password\":\"${AGD_PASS}\"}" \
  | (command -v jq >/dev/null 2>&1 && jq -r '.token' || grep -o '"token":"[^"]*"' | cut -d'"' -f4)) || true

if [ -n "${TOKEN}" ] && [ "${TOKEN}" != "null" ]; then
  green "  JWT acquired"
  PASS=$((PASS + 1))
else
  red "  JWT acquisition FAILED — remaining checks may fail"
  FAIL=$((FAIL + 1))
fi

# ── Phase 3: Authenticated API calls ─────────────────────────────────────────
bold "Phase 3 — Authenticated Endpoints"
AUTH_HDR="Authorization: Bearer ${TOKEN}"

check "OOB countries list"         "curl -sf -H '${AUTH_HDR}' '${OOB_URL}/api/v1/oob/countries'"
check "Cyber techniques list"      "curl -sf -H '${AUTH_HDR}' '${CYBER_URL}/cyber/techniques'"
check "CBRN agents list"           "curl -sf -H '${AUTH_HDR}' '${CBRN_URL}/cbrn/agents'"
check "Asym cells list"            "curl -sf -H '${AUTH_HDR}' '${ASYM_URL}/asym/cells'"
check "Terror sites list"          "curl -sf -H '${AUTH_HDR}' '${TERROR_URL}/terror/sites'"
check "Intel items list"           "curl -sf -H '${AUTH_HDR}' '${INTEL_URL}/intel'"
check "Civilian population list"   "curl -sf -H '${AUTH_HDR}' '${CIVILIAN_URL}/civilian/population'"
check "Reports list"               "curl -sf -H '${AUTH_HDR}' '${REPORTING_URL}/reports'"
check "Econ sanctions list"        "curl -sf -H '${AUTH_HDR}' '${ECON_URL}/sanctions'"
check "InfoOps narratives list"    "curl -sf -H '${AUTH_HDR}' '${INFOOPS_URL}/narratives'"
check "GIS export layers"          "curl -sf -H '${AUTH_HDR}' '${GIS_URL}/export/layers'"
check "Training exercises list"    "curl -sf -H '${AUTH_HDR}' '${TRAINING_URL}/exercises'"

# ── Phase 4: Simulation run lifecycle ────────────────────────────────────────
bold "Phase 4 — Simulation Run Lifecycle"
SCENARIO_ID="smoke-test-scenario"

RUN_ID=""
RUN_ID=$(curl -sf -X POST "${SIM_URL}/scenarios/${SCENARIO_ID}/runs" \
  -H "Content-Type: application/json" \
  -H "${AUTH_HDR}" \
  -d '{"mode":"turn_based","max_turns":2,"config":{}}' \
  | (command -v jq >/dev/null 2>&1 && jq -r '.run_id // .id' || grep -o '"run_id":"[^"]*"' | cut -d'"' -f4)) || true

if [ -n "${RUN_ID}" ] && [ "${RUN_ID}" != "null" ]; then
  green "  Run created: ${RUN_ID}"
  PASS=$((PASS + 1))

  check "Get run state"   "curl -sf -H '${AUTH_HDR}' '${SIM_URL}/runs/${RUN_ID}'"
  check "Get run events"  "curl -sf -H '${AUTH_HDR}' '${SIM_URL}/runs/${RUN_ID}/events'"
  check "Get run report"  "curl -sf -H '${AUTH_HDR}' '${SIM_URL}/runs/${RUN_ID}/report'"
else
  red "  Run creation FAILED — skipping lifecycle checks"
  FAIL=$((FAIL + 3))
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  Results: "
green "${PASS} passed"
printf "  "
if [ "${FAIL}" -gt 0 ]; then
  red "${FAIL} failed"
else
  echo "0 failed"
fi
bold "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "${FAIL}" -eq 0 ] || exit 1

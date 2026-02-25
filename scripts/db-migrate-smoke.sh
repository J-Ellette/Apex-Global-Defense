#!/usr/bin/env bash
# scripts/db-migrate-smoke.sh — Migration smoke validation.
#
# Validates all DB init/migration scripts in db/init/:
#   1. Checks files exist and are sequentially numbered (no gaps).
#   2. Optionally runs them against a temporary PostgreSQL container
#      (requires Docker; set SKIP_DOCKER=1 to skip the live run).
#
# Usage:
#   ./scripts/db-migrate-smoke.sh
#   SKIP_DOCKER=1 ./scripts/db-migrate-smoke.sh   # lint/sequence check only
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed

set -euo pipefail

INIT_DIR="${INIT_DIR:-db/init}"
SKIP_DOCKER="${SKIP_DOCKER:-0}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgis/postgis:16-3.4}"

PASS=0
FAIL=0
CONTAINER_NAME="agd-migrate-smoke-$$"

green() { printf "\033[0;32m%s\033[0m\n" "$*"; }
red()   { printf "\033[0;31m%s\033[0m\n" "$*"; }
bold()  { printf "\033[1m%s\033[0m\n" "$*"; }

check_pass() { green "  PASS: $1"; PASS=$((PASS + 1)); }
check_fail() { red   "  FAIL: $1"; FAIL=$((FAIL + 1)); }

cleanup() {
  if docker ps -q --filter "name=${CONTAINER_NAME}" 2>/dev/null | grep -q .; then
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# ── Step 1: Directory existence ───────────────────────────────────────────────
bold "Step 1 — Init directory check"
if [ -d "${INIT_DIR}" ]; then
  check_pass "db/init/ directory exists"
else
  check_fail "db/init/ directory missing (expected: ${INIT_DIR})"
  exit 1
fi

# ── Step 2: File discovery ────────────────────────────────────────────────────
bold "Step 2 — File discovery"
mapfile -t SQL_FILES < <(find "${INIT_DIR}" -maxdepth 1 -name "*.sql" | sort)

if [ "${#SQL_FILES[@]}" -eq 0 ]; then
  check_fail "No .sql files found in ${INIT_DIR}"
  exit 1
fi

check_pass "Found ${#SQL_FILES[@]} SQL migration file(s)"

# ── Step 3: Sequential numbering check ───────────────────────────────────────
bold "Step 3 — Sequential numbering"
EXPECTED=1
SEQ_OK=1
for f in "${SQL_FILES[@]}"; do
  base=$(basename "$f")
  # Extract leading number (e.g., 001 from 001_schema.sql)
  num_str=$(echo "$base" | grep -oE '^[0-9]+')
  if [ -z "$num_str" ] || ! echo "$num_str" | grep -qE '^[0-9]+$'; then
    check_fail "File does not start with a number: ${base}"
    SEQ_OK=0
    continue
  fi
  num=$((10#${num_str}))  # strip leading zeros for arithmetic
  if [ "$num" -ne "$EXPECTED" ]; then
    check_fail "Gap in sequence: expected $(printf '%03d' $EXPECTED), got ${num_str} (${base})"
    SEQ_OK=0
  fi
  EXPECTED=$((EXPECTED + 1))
done
[ "$SEQ_OK" -eq 1 ] && check_pass "All files are sequentially numbered (001–$(printf '%03d' $((EXPECTED - 1))))"

# Print file list
echo ""
echo "  Migration files:"
for f in "${SQL_FILES[@]}"; do
  echo "    $(basename "$f")"
done
echo ""

# ── Step 4: Non-empty file check ─────────────────────────────────────────────
bold "Step 4 — Non-empty file check"
EMPTY_OK=1
for f in "${SQL_FILES[@]}"; do
  if [ ! -s "$f" ]; then
    check_fail "Empty file: $(basename "$f")"
    EMPTY_OK=0
  fi
done
[ "$EMPTY_OK" -eq 1 ] && check_pass "All migration files are non-empty"

# ── Step 5: Docker live run ───────────────────────────────────────────────────
if [ "${SKIP_DOCKER}" = "1" ]; then
  bold "Step 5 — Docker live run (SKIPPED: SKIP_DOCKER=1)"
else
  bold "Step 5 — Docker live run"
  if ! command -v docker >/dev/null 2>&1; then
    check_fail "docker not found; set SKIP_DOCKER=1 to skip this step"
  else
    echo "  Starting temporary PostgreSQL container..."
    docker run -d \
      --name "${CONTAINER_NAME}" \
      -e POSTGRES_DB=agd_smoke \
      -e POSTGRES_USER=agd \
      -e POSTGRES_PASSWORD=smokepass \
      -v "$(pwd)/${INIT_DIR}:/docker-entrypoint-initdb.d:ro" \
      "${POSTGRES_IMAGE}" >/dev/null

    echo "  Waiting for PostgreSQL to be ready..."
    MAX_WAIT=60
    WAITED=0
    until docker exec "${CONTAINER_NAME}" pg_isready -U agd -d agd_smoke >/dev/null 2>&1; do
      sleep 2
      WAITED=$((WAITED + 2))
      if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        check_fail "PostgreSQL did not become ready within ${MAX_WAIT}s"
        break
      fi
    done

    if docker exec "${CONTAINER_NAME}" pg_isready -U agd -d agd_smoke >/dev/null 2>&1; then
      check_pass "PostgreSQL started and all init scripts applied without error"

      # Verify key tables exist
      TABLES=$(docker exec "${CONTAINER_NAME}" psql -U agd -d agd_smoke -tAc \
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")
      if [ "${TABLES:-0}" -gt 0 ]; then
        check_pass "Schema applied: ${TABLES} public tables found"
      else
        check_fail "Schema may be empty: 0 public tables found"
      fi
    fi
  fi
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

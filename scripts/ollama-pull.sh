#!/usr/bin/env bash
# ollama-pull.sh — Pull Ollama models and optionally save/load them for air-gap use.
#
# Usage:
#   ollama-pull.sh                          # pull models into running Ollama instance
#   ollama-pull.sh --save <output-dir>      # pull and save model blobs to directory
#   ollama-pull.sh --load <model-dir>       # load previously saved blobs (air-gap)
set -euo pipefail

MODELS=(llama3 mistral)
MODE="pull"
DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --save)
      MODE="save"
      DIR="${2:-}"
      [ -z "${DIR}" ] && { echo "ERROR: --save requires a directory argument" >&2; exit 1; }
      shift 2
      ;;
    --load)
      MODE="load"
      DIR="${2:-}"
      [ -z "${DIR}" ] && { echo "ERROR: --load requires a directory argument" >&2; exit 1; }
      shift 2
      ;;
    --models)
      IFS=',' read -ra MODELS <<< "${2:-}"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $(basename "$0") [--save <dir>] [--load <dir>] [--models model1,model2]"
      echo "Default models: ${MODELS[*]}"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

log() { echo "[ollama-pull] $*"; }
die() { echo "[ollama-pull] ERROR: $*" >&2; exit 1; }

wait_for_ollama() {
  log "Waiting for Ollama at ${OLLAMA_HOST} ..."
  local retries=30
  while ! curl -sf "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
    retries=$((retries - 1))
    [ "${retries}" -le 0 ] && die "Ollama not reachable at ${OLLAMA_HOST}"
    sleep 2
  done
  log "Ollama is ready."
}

case "${MODE}" in
  pull)
    command -v curl >/dev/null 2>&1 || die "curl is required"
    wait_for_ollama
    for model in "${MODELS[@]}"; do
      log "Pulling model: ${model}"
      curl -sf -X POST "${OLLAMA_HOST}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${model}\"}" | tail -1
      log "  Done: ${model}"
    done
    log "All models pulled successfully."
    ;;

  save)
    command -v curl   >/dev/null 2>&1 || die "curl is required"
    command -v ollama >/dev/null 2>&1 || die "ollama CLI is required for --save"
    mkdir -p "${DIR}"
    wait_for_ollama
    for model in "${MODELS[@]}"; do
      log "Pulling and saving model: ${model}"
      curl -sf -X POST "${OLLAMA_HOST}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"${model}\"}" | tail -1
      safe_name="${model//\//_}"
      log "  Copying model blobs for ${model} → ${DIR}/${safe_name}"
      # Export via Ollama's model directory (default ~/.ollama/models)
      OLLAMA_MODELS="${HOME}/.ollama/models"
      if [ -d "${OLLAMA_MODELS}" ]; then
        tar -czf "${DIR}/${safe_name}.tar.gz" -C "${OLLAMA_MODELS}" .
        log "  Saved: ${DIR}/${safe_name}.tar.gz"
      else
        log "  WARNING: Ollama models directory not found at ${OLLAMA_MODELS}"
      fi
    done
    log "Models saved to ${DIR}."
    log "Transfer this directory to the air-gapped host."
    ;;

  load)
    command -v curl >/dev/null 2>&1 || die "curl is required"
    [ -d "${DIR}" ] || die "Model directory not found: ${DIR}"
    OLLAMA_MODELS="${HOME}/.ollama/models"
    mkdir -p "${OLLAMA_MODELS}"
    for model in "${MODELS[@]}"; do
      safe_name="${model//\//_}"
      tarball="${DIR}/${safe_name}.tar.gz"
      if [ ! -f "${tarball}" ]; then
        log "WARNING: Model archive not found, skipping: ${tarball}"
        continue
      fi
      log "Loading model blobs: ${model}"
      tar -xzf "${tarball}" -C "${OLLAMA_MODELS}"
      log "  Loaded: ${model}"
    done
    log "All available models loaded into ${OLLAMA_MODELS}."
    log "Restart Ollama to pick up the models."
    ;;
esac

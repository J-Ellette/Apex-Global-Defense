#!/usr/bin/env bash
# airgap-load.sh — Load AGD Docker images on an air-gapped system.
#
# Usage:
#   airgap-load.sh <bundle-dir> [--push <registry>]
#
# Examples:
#   airgap-load.sh ./airgap-bundle
#   airgap-load.sh ./airgap-bundle --push registry.local:5000
set -euo pipefail

BUNDLE_DIR="${1:-}"
PUSH_REGISTRY=""

if [ -z "${BUNDLE_DIR}" ]; then
  echo "Usage: $(basename "$0") <bundle-dir> [--push <registry>]" >&2
  exit 1
fi

shift
while [ $# -gt 0 ]; do
  case "$1" in
    --push)
      PUSH_REGISTRY="${2:-}"
      [ -z "${PUSH_REGISTRY}" ] && { echo "ERROR: --push requires a registry argument" >&2; exit 1; }
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

IMAGES_DIR="${BUNDLE_DIR}/images"
MANIFEST="${IMAGES_DIR}/manifest.txt"

log()  { echo "[airgap-load] $*"; }
die()  { echo "[airgap-load] ERROR: $*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "docker is required"

[ -d "${IMAGES_DIR}" ] || die "images directory not found: ${IMAGES_DIR}"
[ -f "${MANIFEST}"   ] || die "manifest not found: ${MANIFEST}"

log "Loading images from ${IMAGES_DIR}"

while IFS='|' read -r image tarfile; do
  tarpath="${IMAGES_DIR}/${tarfile}"
  if [ ! -f "${tarpath}" ]; then
    log "  WARNING: tar file not found, skipping: ${tarpath}"
    continue
  fi
  log "  Loading ${image} from ${tarfile}"
  docker load -i "${tarpath}"

  if [ -n "${PUSH_REGISTRY}" ]; then
    new_tag="${PUSH_REGISTRY}/${image}"
    log "  Tagging ${image} → ${new_tag}"
    docker tag "${image}" "${new_tag}"
    log "  Pushing ${new_tag}"
    docker push "${new_tag}"
  fi
done < "${MANIFEST}"

log "All images loaded successfully."

if [ -n "${PUSH_REGISTRY}" ]; then
  log "All images pushed to ${PUSH_REGISTRY}."
  log ""
  log "Deploy with:"
  log "  helm upgrade --install agd <chart.tgz> \\"
  log "    --set global.imageRegistry=${PUSH_REGISTRY} \\"
  log "    --set airgap=true \\"
  log "    ..."
fi

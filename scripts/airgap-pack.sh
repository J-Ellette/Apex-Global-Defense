#!/usr/bin/env bash
# airgap-pack.sh — Bundle all AGD Docker images and Helm chart for air-gap deployment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUNDLE_DIR="${REPO_ROOT}/airgap-bundle"
IMAGES_DIR="${BUNDLE_DIR}/images"
CHART_DIR="${REPO_ROOT}/helm/agd"

AGD_TAG="${AGD_TAG:-1.0.0}"

# ---------------------------------------------------------------------------
# Image list (registry image → local tar filename)
# ---------------------------------------------------------------------------
declare -A IMAGES=(
  ["postgis/postgis:16-3.4"]="postgis-16-3.4.tar"
  ["redis:7-alpine"]="redis-7-alpine.tar"
  ["elasticsearch:8.12.0"]="elasticsearch-8.12.0.tar"
  ["ghcr.io/consbio/mbtileserver:latest"]="mbtileserver-latest.tar"
  ["ollama/ollama:latest"]="ollama-latest.tar"
  ["quay.io/keycloak/keycloak:24.0.1"]="keycloak-24.0.1.tar"
  ["confluentinc/cp-zookeeper:7.6.0"]="cp-zookeeper-7.6.0.tar"
  ["confluentinc/cp-kafka:7.6.0"]="cp-kafka-7.6.0.tar"
  ["agd/auth-svc:${AGD_TAG}"]="auth-svc-${AGD_TAG}.tar"
  ["agd/oob-svc:${AGD_TAG}"]="oob-svc-${AGD_TAG}.tar"
  ["agd/sim-orchestrator:${AGD_TAG}"]="sim-orchestrator-${AGD_TAG}.tar"
  ["agd/collab-svc:${AGD_TAG}"]="collab-svc-${AGD_TAG}.tar"
  ["agd/cyber-svc:${AGD_TAG}"]="cyber-svc-${AGD_TAG}.tar"
  ["agd/cbrn-svc:${AGD_TAG}"]="cbrn-svc-${AGD_TAG}.tar"
  ["agd/asym-svc:${AGD_TAG}"]="asym-svc-${AGD_TAG}.tar"
  ["agd/terror-svc:${AGD_TAG}"]="terror-svc-${AGD_TAG}.tar"
  ["agd/intel-svc:${AGD_TAG}"]="intel-svc-${AGD_TAG}.tar"
  ["agd/civilian-svc:${AGD_TAG}"]="civilian-svc-${AGD_TAG}.tar"
  ["agd/reporting-svc:${AGD_TAG}"]="reporting-svc-${AGD_TAG}.tar"
  ["agd/frontend:${AGD_TAG}"]="frontend-${AGD_TAG}.tar"
)

log()  { echo "[airgap-pack] $*"; }
die()  { echo "[airgap-pack] ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
command -v docker >/dev/null 2>&1 || die "docker is required"
command -v helm   >/dev/null 2>&1 || die "helm is required"

# ---------------------------------------------------------------------------
# Build AGD service images if not already present
# ---------------------------------------------------------------------------
log "Building AGD application images (tag: ${AGD_TAG})"
docker compose -f "${REPO_ROOT}/docker-compose.dev.yml" build \
  auth-svc oob-svc sim-orchestrator collab-svc \
  cyber-svc cbrn-svc asym-svc terror-svc intel-svc civilian-svc reporting-svc frontend

# Re-tag with AGD_TAG
for svc in auth-svc oob-svc sim-orchestrator collab-svc \
           cyber-svc cbrn-svc asym-svc terror-svc intel-svc civilian-svc reporting-svc frontend; do
  docker tag "${svc}" "agd/${svc}:${AGD_TAG}" 2>/dev/null || true
done

# ---------------------------------------------------------------------------
# Pull infrastructure images
# ---------------------------------------------------------------------------
log "Pulling infrastructure images"
for img in \
  "postgis/postgis:16-3.4" \
  "redis:7-alpine" \
  "elasticsearch:8.12.0" \
  "ghcr.io/consbio/mbtileserver:latest" \
  "ollama/ollama:latest" \
  "quay.io/keycloak/keycloak:24.0.1" \
  "confluentinc/cp-zookeeper:7.6.0" \
  "confluentinc/cp-kafka:7.6.0"; do
  log "  Pulling ${img}"
  docker pull "${img}"
done

# ---------------------------------------------------------------------------
# Save images to tar files
# ---------------------------------------------------------------------------
mkdir -p "${IMAGES_DIR}"
log "Saving images to ${IMAGES_DIR}"

for img in "${!IMAGES[@]}"; do
  tarfile="${IMAGES_DIR}/${IMAGES[$img]}"
  if [ -f "${tarfile}" ]; then
    log "  Skipping ${img} (already exists)"
  else
    log "  Saving ${img} → ${IMAGES[$img]}"
    docker save "${img}" -o "${tarfile}"
  fi
done

# ---------------------------------------------------------------------------
# Package the Helm chart
# ---------------------------------------------------------------------------
log "Packaging Helm chart"
helm package "${CHART_DIR}" --destination "${BUNDLE_DIR}"

# ---------------------------------------------------------------------------
# Create manifest of image → tar mappings (used by airgap-load.sh)
# ---------------------------------------------------------------------------
MANIFEST="${BUNDLE_DIR}/images/manifest.txt"
log "Writing image manifest to ${MANIFEST}"
: > "${MANIFEST}"
for img in "${!IMAGES[@]}"; do
  echo "${img}|${IMAGES[$img]}" >> "${MANIFEST}"
done

# ---------------------------------------------------------------------------
# Write README
# ---------------------------------------------------------------------------
cat > "${BUNDLE_DIR}/README.md" <<'AIRGAP_README'
# AGD Air-Gap Deployment Bundle

This bundle contains everything required to deploy Apex Global Defense
on an isolated (air-gapped) Kubernetes cluster.

## Contents

```
airgap-bundle/
├── images/
│   ├── manifest.txt          # image → tar mapping
│   └── *.tar                 # Docker image archives
├── agd-*.tgz                 # Helm chart package
└── README.md                 # This file
```

## Deployment Steps

1. **Transfer the bundle** to the air-gapped host (USB, secure transfer, etc.)

2. **Load Docker images** (on each Kubernetes node):
   ```bash
   bash scripts/airgap-load.sh /path/to/airgap-bundle
   ```

3. **Configure a local registry** (recommended):
   ```bash
   # Start a local registry (if not already running)
   docker run -d -p 5000:5000 --name registry registry:2

   # Push images to local registry
   bash scripts/airgap-load.sh /path/to/airgap-bundle --push registry.local:5000
   ```

4. **Load Ollama models** (on Ollama host/node):
   ```bash
   bash scripts/ollama-pull.sh --load /path/to/airgap-bundle/ollama-models
   ```

5. **Deploy with Helm**:
   ```bash
   helm upgrade --install agd /path/to/airgap-bundle/agd-1.0.0.tgz \
     --namespace agd \
     --create-namespace \
     --set global.imageRegistry=registry.local:5000 \
     --set airgap=true \
     --set jwt.secret=<strong-random-value> \
     --set postgres.password=<strong-password> \
     --set keycloak.adminPassword=<strong-password>
   ```

6. **Verify the deployment**:
   ```bash
   kubectl get pods -n agd
   kubectl get svc -n agd
   ```

## Post-Deployment

- Access the application at: http://<ingress-host>
- Default Keycloak admin: admin / <keycloak.adminPassword>
- Import the AGD realm: `keycloak/realms/agd-realm.json`

## Troubleshooting

- If pods fail with `ImagePullBackOff`, verify images are loaded and
  `global.imageRegistry` is set correctly.
- If Ollama models are missing, re-run `airgap-load.sh` with `--push` or
  use `ollama-pull.sh --load`.
- Check logs: `kubectl logs -n agd <pod-name>`
AIRGAP_README

# ---------------------------------------------------------------------------
# Create archive of the full bundle
# ---------------------------------------------------------------------------
ARCHIVE="${REPO_ROOT}/agd-airgap-bundle.tar.gz"
log "Creating archive: ${ARCHIVE}"
tar -czf "${ARCHIVE}" -C "${REPO_ROOT}" airgap-bundle
log "Done! Bundle: ${ARCHIVE}"
log "Transfer this file to the air-gapped environment."

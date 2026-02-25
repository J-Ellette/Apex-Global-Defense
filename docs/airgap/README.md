# Air-Gap Deployment Guide — Apex Global Defense

This guide covers building the air-gap bundle on a connected host and deploying
AGD on an isolated (air-gapped) Kubernetes cluster with no external internet
access.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Bundle Creation (connected host)](#2-bundle-creation-connected-host)
3. [Transferring the Bundle](#3-transferring-the-bundle)
4. [Loading Images on Air-Gap Nodes](#4-loading-images-on-air-gap-nodes)
5. [Kubernetes Deployment with Helm](#5-kubernetes-deployment-with-helm)
6. [Offline Tile Server Setup](#6-offline-tile-server-setup)
7. [Ollama Model Deployment](#7-ollama-model-deployment)
8. [Post-Deployment Verification](#8-post-deployment-verification)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

### Connected (build) host

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Docker | 24.x | Required to pull/build/save images |
| Docker Compose | v2 | Used by `airgap-pack.sh` |
| Helm | 3.12+ | Chart packaging |
| curl | any | Health checks |

### Air-gap (target) host

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Docker | 24.x | For loading image archives |
| Kubernetes | 1.27+ | k3s, RKE2, or vanilla k8s |
| Helm | 3.12+ | Chart deployment |
| kubectl | matching k8s | Cluster management |

A local container registry (e.g., `registry:2`) is **strongly recommended**
so image archives are loaded once and all nodes pull from the registry.

---

## 2. Bundle Creation (connected host)

### 2.1 Build application images and pull infrastructure images

```bash
# Clone the repository (if not already done)
git clone https://github.com/Apex-Global-Defense/Apex-Global-Defense.git
cd Apex-Global-Defense

# Set the image tag (defaults to 1.0.0)
export AGD_TAG=1.0.0

# Run the pack script
bash scripts/airgap-pack.sh
```

This script will:
- Build all AGD service images from source
- Pull all third-party infrastructure images
- Save every image to `airgap-bundle/images/*.tar`
- Package the Helm chart to `airgap-bundle/agd-1.0.0.tgz`
- Write `airgap-bundle/images/manifest.txt`
- Create the final archive `agd-airgap-bundle.tar.gz`

### 2.2 Save Ollama models (optional — large download)

```bash
# Pull and save llama3 and mistral model blobs
bash scripts/ollama-pull.sh --save airgap-bundle/ollama-models
```

> **Note:** Llama3 is ~4 GB and Mistral is ~4.1 GB. Ensure sufficient disk
> space before running.

---

## 3. Transferring the Bundle

Transfer `agd-airgap-bundle.tar.gz` to the air-gapped host using an approved
secure method (encrypted USB drive, secure file transfer, etc.).

```bash
# Example: using scp to a jump host
scp agd-airgap-bundle.tar.gz operator@jump-host:/transfer/

# On the air-gap host
tar -xzf agd-airgap-bundle.tar.gz
```

---

## 4. Loading Images on Air-Gap Nodes

### 4.1 Start a local registry (recommended)

Run this once on a node reachable by all Kubernetes nodes:

```bash
docker run -d \
  --restart=always \
  --name registry \
  -p 5000:5000 \
  -v /opt/registry:/var/lib/registry \
  registry:2
```

> The `registry:2` image tar is **not** included in the AGD bundle.
> Pre-load it separately or include it in your base node image.

### 4.2 Load and push all images

```bash
cd Apex-Global-Defense

# Load images into Docker and push to local registry
bash scripts/airgap-load.sh ./airgap-bundle --push registry.local:5000
```

To load images without pushing (e.g., single-node):

```bash
bash scripts/airgap-load.sh ./airgap-bundle
```

### 4.3 Configure containerd to use the local registry

For k3s, add to `/etc/rancher/k3s/registries.yaml` on every node:

```yaml
mirrors:
  "registry.local:5000":
    endpoint:
      - "http://registry.local:5000"
```

Restart k3s: `systemctl restart k3s`

---

## 5. Kubernetes Deployment with Helm

### 5.1 Create the namespace

```bash
kubectl create namespace agd
```

### 5.2 Copy tile data (optional, see Section 6)

```bash
kubectl create configmap agd-tiles \
  --from-file=./tiles/ \
  -n agd
```

### 5.3 Deploy with Helm

```bash
helm upgrade --install agd ./airgap-bundle/agd-1.0.0.tgz \
  --namespace agd \
  --create-namespace \
  --set global.imageRegistry=registry.local:5000 \
  --set airgap=true \
  --set classificationLevel=SECRET \
  --set jwt.secret="$(openssl rand -hex 32)" \
  --set postgres.password="$(openssl rand -hex 16)" \
  --set keycloak.adminPassword="$(openssl rand -hex 16)" \
  --set ingress.host=agd.internal \
  --wait \
  --timeout 10m
```

For a custom `values.yaml` override file:

```yaml
# values-airgap.yaml
global:
  imageRegistry: registry.local:5000

airgap: true
classificationLevel: SECRET
ingress:
  enabled: true
  host: agd.internal
  className: nginx

jwt:
  secret: "<strong-random>"
postgres:
  password: "<strong-password>"
keycloak:
  adminPassword: "<strong-password>"
```

```bash
helm upgrade --install agd ./airgap-bundle/agd-1.0.0.tgz \
  -n agd -f values-airgap.yaml --wait --timeout 10m
```

---

## 6. Offline Tile Server Setup

The mbtiles-server pod mounts tile files from a Kubernetes volume.

### 6.1 Obtain MBTiles files

Download `.mbtiles` files **before** air-gapping from a source such as
[OpenMapTiles](https://openmaptiles.org/) or the Natural Earth dataset.

### 6.2 Load tiles into the cluster

**Option A — PersistentVolume (production):**

1. Place `.mbtiles` files on a node at `/opt/agd/tiles/`.
2. Create a PV and PVC pointing to that path, then update the
   `mbtiles-server` deployment's volume mount.

**Option B — ConfigMap (small datasets only):**

```bash
kubectl create configmap agd-tiles -n agd \
  --from-file=world.mbtiles=/path/to/world.mbtiles
```

### 6.3 Verify tiles are served

```bash
kubectl port-forward -n agd svc/mbtiles-server 8080:8080
curl http://localhost:8080/services
```

---

## 7. Ollama Model Deployment

### 7.1 Load model blobs (air-gap)

```bash
bash scripts/ollama-pull.sh \
  --load ./airgap-bundle/ollama-models \
  --models llama3,mistral
```

### 7.2 Verify models are available

```bash
kubectl port-forward -n agd svc/ollama 11434:11434
curl http://localhost:11434/api/tags
```

Expected output lists `llama3` and `mistral` in the `models` array.

---

## 8. Post-Deployment Verification

```bash
# All pods should be Running
kubectl get pods -n agd

# Services
kubectl get svc -n agd

# Ingress
kubectl get ingress -n agd

# Smoke-test auth service
kubectl port-forward -n agd svc/auth-svc 8082:8082
curl -s http://localhost:8082/healthz

# Check frontend
kubectl port-forward -n agd svc/frontend 8080:80
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
# Expected: 200
```

### Import Keycloak realm

```bash
kubectl port-forward -n agd svc/keycloak 8180:8080

# In a browser: http://localhost:8180/admin
# Login: admin / <keycloak.adminPassword>
# Import: keycloak/realms/agd-realm.json
```

---

## 9. Troubleshooting

### ImagePullBackOff

```bash
kubectl describe pod -n agd <pod-name> | grep -A5 Events
```

- Verify the image is loaded: `docker images | grep <name>`
- Verify `global.imageRegistry` matches the registry hostname/port.
- Check containerd/CRI registry mirrors are configured correctly.

### Pod stuck in Init state

- Ollama `pull-models` init container runs only when `airgap=false`.
  When air-gapped, models must be pre-loaded (Section 7).

### Database connection errors

```bash
kubectl logs -n agd deployment/auth-svc | grep -i "database\|connect"
```

- Confirm `postgres.password` matches the secret value.
- Check postgres pod is healthy: `kubectl get pod -n agd -l app.kubernetes.io/name=postgres`

### Elasticsearch not green

```bash
kubectl port-forward -n agd svc/elasticsearch 9200:9200
curl http://localhost:9200/_cluster/health?pretty
```

- Increase memory limit if OOMKilled: `--set elasticsearch.resources.limits.memory=4Gi`

### Logs

```bash
# Tail all logs for a service
kubectl logs -n agd -l app.kubernetes.io/name=auth-svc --follow

# Previous container logs (after crash)
kubectl logs -n agd <pod> --previous
```

---

*Set `classificationLevel` in `values.yaml` to reflect your deployment classification.*

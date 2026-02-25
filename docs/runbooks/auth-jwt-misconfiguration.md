# Runbook: Auth / JWT Misconfiguration

**Failure Class:** Authentication or JWT misconfiguration causing 401/403 errors across services  
**Severity:** High  
**Services Affected:** All backend services (shared JWT secret)

---

## Symptoms

- All or most API calls return `HTTP 401 Unauthorized` with `"Invalid or expired token"`
- Login succeeds (`POST /api/v1/auth/login` returns a token) but subsequent calls fail with 401
- Services return `HTTP 403 Forbidden` with `"Missing permission: <perm>"` unexpectedly
- Frontend shows "Session expired" or "Unauthorized" after a recent deployment
- `make smoke-test` fails at Phase 3 (authenticated endpoints)

---

## Immediate Triage

```bash
# 1. Verify the auth-svc is healthy
curl -sf http://localhost:8082/health | jq .

# 2. Attempt a login and inspect the token
TOKEN=$(curl -sf -X POST http://localhost:8082/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpass"}' | jq -r '.token')
echo "Token: ${TOKEN}"

# 3. Decode the JWT header and payload (no verification)
echo "${TOKEN}" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .

# 4. Test the token against a protected endpoint
curl -sf -H "Authorization: Bearer ${TOKEN}" http://localhost:8083/api/v1/oob/countries | jq .

# 5. Check that JWT_SECRET is consistent across services
grep JWT_SECRET docker-compose.dev.yml | sort -u
```

---

## Common Causes and Fixes

### JWT secret mismatch between auth-svc and other services

**Cause:** `auth-svc` signs tokens with one secret; other services validate with a different secret. This typically happens after a deployment where only some services received an updated `JWT_SECRET`.

**Fix:**
1. Ensure all services in `docker-compose.dev.yml` share the same `JWT_SECRET` value
2. Rebuild and restart all affected services:
```bash
docker compose -f docker-compose.dev.yml up -d --build
```

### Expired token not being refreshed

**Cause:** The frontend is not calling `POST /api/v1/auth/refresh` when the access token expires, or the refresh token itself has expired.

**Fix (user-facing):** Log out and log back in.

**Fix (developer):** Verify the frontend Axios interceptor is calling refresh on 401 responses and retrying. See `frontend/src/shared/api/client.ts`.

### Token issued with wrong algorithm

**Cause:** `auth-svc` was configured with a different algorithm (e.g., RS256) while services expect HS256.

**Check:**
```bash
# Inspect JWT header
echo "${TOKEN}" | cut -d'.' -f1 | base64 -d 2>/dev/null | jq .
# Expected: {"alg":"HS256","typ":"JWT"}
```

**Fix:** Ensure `JWT_ALGORITHM=HS256` is set consistently. All Python services default to HS256 via `settings.jwt_algorithm`.

### Missing permission in token claims

**Cause:** A role was updated in `auth-svc` RBAC model but existing tokens (issued before the change) don't have the new permission.

**Symptom:** 403 with `"Missing permission: <new-permission>"`

**Fix:** Log out and log back in to obtain a new token with updated claims.

### Keycloak OIDC integration issue

**Cause:** Keycloak is down or misconfigured, breaking SSO login flows.

**Check:**
```bash
curl -sf http://localhost:8180/health/live | jq .
docker compose -f docker-compose.dev.yml logs keycloak | tail -30
```

**Fix:**
```bash
docker compose -f docker-compose.dev.yml restart keycloak
```

---

## Secrets Hygiene Reminder

The dev JWT secret is intentionally weak (`dev-secret-change-in-prod`). In production:
- Rotate `JWT_SECRET` using a cryptographically random 32+ character value
- Store the secret in a secrets manager (AWS Secrets Manager, HashiCorp Vault, or Kubernetes Secrets)
- Never commit a real secret to source control — CI secret scanning (gitleaks) will flag it

---

## Validation After Fix

```bash
# Full auth + authenticated endpoint smoke
make smoke-test

# Verify token claims
TOKEN=$(curl -sf -X POST http://localhost:8082/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpass"}' | jq -r '.token')
echo "${TOKEN}" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq '{uid, roles, perms, cls}'
```

---

## Escalation

If tokens cannot be issued (auth-svc is down and users cannot log in), this is a **Critical** incident. Escalate immediately to the on-call engineer to restore `auth-svc`. Until resolved, all services requiring authentication are unavailable.

---

*Apex Global Defense | Operations | UNCLASSIFIED*

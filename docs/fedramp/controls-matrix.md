# NIST SP 800-53 Rev 5 Controls Matrix
## Apex Global Defense (AGD) — FedRAMP Moderate Baseline

**Classification:** UNCLASSIFIED  
**Baseline:** FedRAMP Moderate (325 controls)  
**Last Updated:** 2026-02-25

---

## Legend

| Status | Meaning |
|--------|---------|
| ✅ Implemented | Control is fully implemented |
| 🔄 In Progress | Partially implemented; POA&M item |
| ⏳ Planned | Not yet implemented; on roadmap |
| N/A | Not applicable to AGD |

---

## AC — Access Control

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| AC-1 | Access Control Policy | ✅ | Policy documented in this SSP; enforced via RBAC |
| AC-2 | Account Management | ✅ | Keycloak manages user lifecycle; `users` table mirrors with `active` flag |
| AC-3 | Access Enforcement | ✅ | JWT RBAC middleware; `RequirePermission` + `ClassificationGate` middleware |
| AC-4 | Information Flow Enforcement | ✅ | Classification RLS policies; service-level ceiling checks |
| AC-5 | Separation of Duties | ✅ | Distinct roles: viewer, analyst, planner, commander, sim_operator, admin, classification_officer |
| AC-6 | Least Privilege | ✅ | Per-role permission sets; principle of least privilege enforced in `RolePermissions` map |
| AC-7 | Unsuccessful Logon Attempts | 🔄 | Auth-svc logs failed logins; lockout policy TBD in Keycloak config |
| AC-8 | System Use Notification | ⏳ | Login banner not yet implemented in frontend |
| AC-11 | Session Lock | ⏳ | JWT TTL (1h); refresh token rotation; auto-logout on inactivity TBD |
| AC-14 | Permitted Actions Without Identification | ✅ | All data endpoints require JWT; only `/health` is unauthenticated |
| AC-17 | Remote Access | ✅ | All remote access via HTTPS/TLS; no unencrypted channels |
| AC-18 | Wireless Access | N/A | Government-managed network controls |
| AC-19 | Access Control for Mobile Devices | ⏳ | Mobile app planned; device management TBD |
| AC-20 | Use of External Systems | 🔄 | OSINT/intel feed connections documented; MOU/ISA required for production |
| AC-22 | Publicly Accessible Content | N/A | AGD is not a public-facing system |

---

## AU — Audit and Accountability

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| AU-1 | Audit and Accountability Policy | ✅ | Policy documented; `audit_log` table is system of record |
| AU-2 | Event Logging | ✅ | Logged: login, logout, all write operations (POST/PUT/DELETE), classification access |
| AU-3 | Content of Audit Records | ✅ | `audit_log`: user_id, session_id, action, resource_type, resource_id, classification, ip_address, user_agent, payload, timestamp |
| AU-4 | Audit Log Storage Capacity | ✅ | TimescaleDB partitioned hypertable; automated monthly partitions; retention policy configurable |
| AU-5 | Response to Audit Log Failures | 🔄 | Alert on DB write failure; dead-letter queue TBD |
| AU-6 | Audit Record Review | 🔄 | Manual review process; automated anomaly detection TBD |
| AU-7 | Audit Record Reduction and Report Generation | ⏳ | Export of audit logs TBD; SIEM integration TBD |
| AU-8 | Time Stamps | ✅ | All timestamps are `TIMESTAMPTZ` (UTC); PostgreSQL `NOW()` |
| AU-9 | Protection of Audit Information | ✅ | `audit_log` is append-only; no DELETE or UPDATE operations permitted by application role |
| AU-11 | Audit Record Retention | 🔄 | Partition retention policy TBD; recommend 3 years for Moderate |
| AU-12 | Audit Record Generation | ✅ | `AuditWrites` middleware on all write routes; auth-svc logs login/logout/token refresh |

---

## CM — Configuration Management

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| CM-1 | Configuration Management Policy | 🔄 | Policy TBD; process documented in Makefile and docker-compose |
| CM-2 | Baseline Configuration | ✅ | Docker Compose dev; Helm chart production (in progress); pinned image versions |
| CM-3 | Configuration Change Control | 🔄 | GitHub PR reviews; CI/CD pipeline; change board process TBD |
| CM-4 | Impact Analyses | 🔄 | Architecture review required for boundary changes; formal process TBD |
| CM-5 | Access Restrictions for Change | ✅ | Branch protection on `main`; code owners; required reviews |
| CM-6 | Configuration Settings | ✅ | Environment-specific config via env vars; secrets via K8s secrets / AWS Secrets Manager |
| CM-7 | Least Functionality | ✅ | Each service exposes only required ports; `/health` is the only unauthenticated endpoint |
| CM-8 | Information System Component Inventory | 🔄 | Container image SBOMs TBD; SBOM generation in CI pipeline planned |
| CM-10 | Software Usage Restrictions | ✅ | Open source dependencies reviewed; no commercial restrictions violated |
| CM-11 | User-Installed Software | N/A | SaaS deployment; user cannot install software |

---

## IA — Identification and Authentication

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| IA-1 | Identification and Authentication Policy | ✅ | Policy enforced via Keycloak + JWT; documented here |
| IA-2 | Identification and Authentication (Organizational Users) | ✅ | Keycloak OIDC; all users authenticate before accessing any endpoint |
| IA-2(1) | MFA for Privileged Accounts | 🔄 | Keycloak MFA capable; not enforced by default — MUST enable for admin roles |
| IA-2(2) | MFA for Non-Privileged Accounts | ⏳ | Planned for production Keycloak config |
| IA-3 | Device Identification and Authentication | N/A | Browser SaaS; device auth not applicable at this level |
| IA-4 | Identifier Management | ✅ | UUID-based user IDs; Keycloak manages identity lifecycle |
| IA-5 | Authenticator Management | ✅ | Keycloak manages password policy; JWT secret rotatable via env var |
| IA-5(1) | Password Complexity | ✅ | Keycloak enforces min 8 chars, complexity; login binding requires `min=8` |
| IA-6 | Authentication Feedback | ✅ | Generic error messages on login failure; no username enumeration |
| IA-7 | Cryptographic Module Authentication | ✅ | JWT signed with HMAC-SHA256; TLS for all connections |
| IA-8 | Identification and Authentication (Non-Org Users) | 🔄 | External partner access TBD; Keycloak federation configurable |
| IA-11 | Re-Authentication | ✅ | Access token TTL 1h; refresh token required for continuation |

---

## IR — Incident Response

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| IR-1 | Incident Response Policy | ⏳ | Policy document TBD |
| IR-2 | Incident Response Training | ⏳ | Training program TBD |
| IR-3 | Incident Response Testing | ⏳ | Tabletop exercise TBD |
| IR-4 | Incident Handling | 🔄 | Runbook TBD; logging infrastructure supports incident analysis |
| IR-5 | Incident Monitoring | 🔄 | Structured logging in place; SIEM integration TBD |
| IR-6 | Incident Reporting | ⏳ | US-CERT reporting procedures TBD |
| IR-8 | Incident Response Plan | ⏳ | IRP document TBD |

---

## MP — Media Protection

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| MP-1 | Media Protection Policy | ⏳ | Policy TBD |
| MP-2 | Media Access | N/A | Cloud SaaS; no physical media |
| MP-6 | Media Sanitization | N/A | Cloud SaaS; data deletion via DB procedures |
| MP-7 | Media Use | N/A | Cloud SaaS |

---

## PL — Planning

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| PL-1 | Security Planning Policy | 🔄 | This SSP fulfills PL-1 partially; formal policy TBD |
| PL-2 | System Security Plan | 🔄 | This document (in progress) |
| PL-4 | Rules of Behavior | ⏳ | User agreement / acceptable use policy TBD |
| PL-8 | Information Security Architecture | ✅ | Architecture documented in buildsheet.md; boundary diagram in README |
| PL-10 | Baseline Selection | ✅ | FedRAMP Moderate selected as baseline |

---

## RA — Risk Assessment

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| RA-1 | Risk Assessment Policy | ⏳ | Policy document TBD |
| RA-2 | Security Categorization | ✅ | FIPS 199 categorization: Confidentiality=Moderate, Integrity=Moderate, Availability=Low |
| RA-3 | Risk Assessment | 🔄 | Initial risk assessment documented in buildsheet.md §17.4; formal RA TBD |
| RA-5 | Vulnerability Monitoring and Scanning | 🔄 | Dependabot enabled; container scanning TBD |
| RA-7 | Risk Response | 🔄 | Engineering addresses critical CVEs within 30 days; POA&M for others |

---

## SA — System and Services Acquisition

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| SA-1 | System and Services Acquisition Policy | ⏳ | Policy TBD |
| SA-3 | System Development Life Cycle | ✅ | Agile SDLC with security integrated; buildsheet.md tracks phases |
| SA-4 | Acquisition Process | 🔄 | OSS license review required; commercial dependency review in progress |
| SA-5 | System Documentation | ✅ | buildsheet.md, copilot.md, README.md, this FedRAMP package |
| SA-8 | Security and Privacy Engineering Principles | ✅ | Air-gap first, classification-aware, non-AI fallback, auditability baked in |
| SA-9 | External System Services | 🔄 | OSINT/intel feed ISAs TBD |
| SA-10 | Developer Configuration Management | ✅ | Git, GitHub Actions CI/CD, container builds |
| SA-11 | Developer Testing and Evaluation | ✅ | Unit tests per service; TypeScript strict mode |

---

## SC — System and Communications Protection

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| SC-1 | System and Communications Protection Policy | ⏳ | Policy TBD |
| SC-2 | Application Partitioning | ✅ | Microservices architecture; each domain isolated |
| SC-3 | Security Function Isolation | ✅ | Auth-svc handles all authentication; separate from domain services |
| SC-4 | Information in Shared Resources | ✅ | asyncpg connection pool; no shared memory between requests |
| SC-5 | Denial of Service Protection | 🔄 | Rate limiting at API gateway; DDoS protection via cloud WAF planned |
| SC-7 | Boundary Protection | ✅ | API gateway is single ingress; no direct DB access from outside |
| SC-8 | Transmission Confidentiality and Integrity | ✅ | TLS 1.3 required; HSTS headers |
| SC-12 | Cryptographic Key Management | 🔄 | JWT secret via env var; rotation procedure TBD; KMS integration planned |
| SC-13 | Cryptographic Protection | ✅ | TLS 1.3, HMAC-SHA256 JWT signing, bcrypt/PBKDF2 passwords |
| SC-15 | Collaborative Computing Devices | N/A | No audio/video devices |
| SC-17 | Public Key Infrastructure Certificates | 🔄 | TLS certs via Let's Encrypt / ACM; PKI policy TBD |
| SC-18 | Mobile Code | ✅ | React/TypeScript frontend; no arbitrary code execution |
| SC-20 | Secure Name/Address Resolution | N/A | Managed by cloud provider DNS |
| SC-28 | Protection of Information at Rest | 🔄 | DB encryption at rest via RDS/EBS encryption planned; PostgreSQL pgcrypto for field-level TBD |
| SC-39 | Process Isolation | ✅ | Each service in separate container; no shared process space |

---

## SI — System and Information Integrity

| Control | Title | Status | AGD Implementation |
|---------|-------|--------|--------------------|
| SI-1 | System and Information Integrity Policy | ⏳ | Policy TBD |
| SI-2 | Flaw Remediation | 🔄 | Dependabot for dependency updates; patch SLA TBD |
| SI-3 | Malicious Code Protection | 🔄 | Container image scanning; antivirus for uploaded files TBD |
| SI-4 | System Monitoring | 🔄 | Structured logging; health endpoints; centralized log aggregation TBD |
| SI-5 | Security Alerts, Advisories, and Directives | 🔄 | GitHub Security Advisories monitored; process TBD |
| SI-6 | Security Function Verification | 🔄 | Health check endpoints per service; integrity monitoring TBD |
| SI-7 | Software, Firmware, and Information Integrity | 🔄 | Container image digests; SBOM TBD |
| SI-10 | Information Input Validation | ✅ | Pydantic v2 models on all Python endpoints; Zod/TypeScript on frontend |
| SI-11 | Error Handling | ✅ | Generic error messages to clients; detailed errors in logs only |
| SI-12 | Information Management and Retention | 🔄 | Retention policy for audit logs and sim data TBD |
| SI-16 | Memory Protection | N/A | Managed by container runtime |

---

## POA&M Summary (Plan of Action & Milestones)

Items requiring remediation before production ATO:

| ID | Control | Gap | Priority | Target Date |
|----|---------|-----|----------|-------------|
| 1 | AC-7 | Account lockout policy not configured | High | Q3 2026 |
| 2 | AC-8 | System use notification banner missing | Medium | Q2 2026 |
| 3 | IA-2(1) | MFA not enforced for privileged accounts | High | Q3 2026 |
| 4 | SC-28 | DB encryption at rest not verified | High | Q3 2026 |
| 5 | AU-11 | Audit log retention policy not configured | Medium | Q2 2026 |
| 6 | IR-1/IR-8 | Incident response policy/plan not drafted | Medium | Q3 2026 |
| 7 | SC-12 | JWT secret rotation procedure not documented | Medium | Q2 2026 |
| 8 | CM-8 | SBOM generation not automated | Low | Q4 2026 |

---

*Controls matrix based on NIST SP 800-53 Rev 5 FedRAMP Moderate baseline. Not all 325 baseline controls are listed — only those most directly relevant to AGD's architecture are included here. The full control set must be addressed in the final SSP.*

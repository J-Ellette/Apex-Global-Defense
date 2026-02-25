# FedRAMP Authorization Documentation
## Apex Global Defense (AGD) — Version 1.0

**Classification:** UNCLASSIFIED  
**Impact Level Target:** FedRAMP Moderate (IL4-ready)  
**Document Status:** Initial Draft

---

## Overview

This directory contains documentation artifacts required for or relevant to a FedRAMP Moderate Authorization to Operate (ATO) for the Apex Global Defense (AGD) platform.

AGD is architected to support FedRAMP Moderate from day one. Classification-aware data handling, immutable audit logging, role-based access control, and air-gap deployment capability are built-in design constraints, not afterthoughts.

---

## Authorization Scope

| Attribute | Value |
|-----------|-------|
| System Name | Apex Global Defense (AGD) |
| System Abbreviation | AGD |
| Responsible Organization | Apex Global Defense |
| Impact Level | FedRAMP Moderate (NIST SP 800-53 Rev 5) |
| Deployment Model | Government Community Cloud (GCC) / AWS GovCloud |
| Service Model | SaaS |
| Authorization Type | Agency ATO via FedRAMP |

---

## Document Index

| Document | Description | Status |
|----------|-------------|--------|
| [controls-matrix.md](./controls-matrix.md) | NIST SP 800-53 Rev 5 control inventory with AGD implementation notes | Draft |
| [ssp-skeleton.md](./ssp-skeleton.md) | System Security Plan skeleton | Draft |

---

## Architecture Summary (Security Perspective)

### Data Flow

```
Browser (TLS 1.3)
  │
  ▼
Load Balancer / API Gateway (rate limiting, WAF)
  │
  ▼
Auth Service (JWT issuance, RBAC, classification ceiling enforcement)
  │
  ├── Microservices (classification-aware, permission-checked endpoints)
  │     └── Row-Level Security enforced in PostgreSQL
  │
  └── Audit Log (append-only, partitioned, tamper-evident)
```

### Key Security Controls Already Implemented

| Control Family | AGD Implementation |
|---------------|-------------------|
| Access Control (AC) | JWT RBAC, classification ceiling in JWT claims, ClassificationGate middleware, RLS policies |
| Audit & Accountability (AU) | Immutable `audit_log` table (TimescaleDB partitioned), async writes on every write operation |
| Identification & Authentication (IA) | JWT + Keycloak OIDC integration, refresh token rotation, PBKDF2 password hashing |
| System & Communications Protection (SC) | TLS 1.3 enforced at gateway, CORS policy, no plaintext credentials |
| Configuration Management (CM) | Docker Compose dev / Helm chart production, version-pinned images, migration-versioned DB schema |
| Incident Response (IR) | Structured zap logging, audit trail, health endpoints for monitoring |
| Risk Assessment (RA) | Classification-aware threat assessment engine, PMESII-PT framework integration |
| Data Classification | `classification_level` enum on all sensitive tables, RLS policies (migration 001 + 011) |

---

## Boundary Diagram

### System Boundary (FedRAMP Authorization Boundary)

The AGD authorization boundary includes:

- **Frontend**: React/TypeScript SPA (served from CDN within GovCloud)
- **API Gateway**: Kong or Nginx (TLS termination, rate limiting)
- **Microservices**: All services in `services/` directory (containerized, Kubernetes)
- **Database Tier**: PostgreSQL + PostGIS + TimescaleDB + pgvector (RDS or self-managed)
- **Cache**: Redis (ElastiCache)
- **Object Storage**: MinIO or S3 GovCloud (for attachments, tile packs)
- **Auth**: Keycloak (or AWS Cognito GovCloud)

### Outside the Boundary

- External OSINT feeds (ACLED, UCDP, RSS) — data is ingested; no PII transmitted outbound
- Commercial intel feeds (Recorded Future, Maxar, Jane's) — API keys stored as secrets

---

## Continuous Monitoring Plan

| Activity | Frequency | Responsible Party |
|----------|-----------|------------------|
| Vulnerability scans (container images) | Weekly | DevSecOps |
| SAST/DAST scans | Per release | Engineering |
| Penetration testing | Annual | Third-party |
| Security control reviews | Quarterly | ISSO |
| Audit log review | Daily (automated) | ISSO |
| Incident review | Per incident | IR Team |
| POA&M updates | Monthly | ISSO |

---

## Contacts

| Role | Responsibility |
|------|---------------|
| System Owner | Executive accountability for AGD |
| ISSO (Information System Security Officer) | Day-to-day security oversight |
| AO (Authorizing Official) | Signs ATO; government agency representative |
| 3PAO (Third-Party Assessment Organization) | Independent FedRAMP assessment |

---

*This document is a living artifact. Update it with each significant system change, security incident, or authorization event.*

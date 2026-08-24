# High Level Design (HLD) — tvsm-auth (Auth Ninja)

| Attribute | Value |
|-----------|-------|
| Service Name | tvsm-auth (Auth Ninja) |
| Version | 1.0.0 |
| Owner | TVS Motor - Connected Services |
| Last Updated | June 2026 |
| Status | Production |

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Major Components / Services](#2-major-components--services)
3. [Deployment Architecture](#3-deployment-architecture)
4. [Database Interactions](#4-database-interactions)
5. [API Integrations](#5-api-integrations)
6. [Authentication & Authorization Flow](#6-authentication--authorization-flow)
7. [External Systems](#7-external-systems)
8. [Infrastructure Dependencies](#8-infrastructure-dependencies)
9. [High-Level Sequence Flows](#9-high-level-sequence-flows)
10. [Scalability & Resiliency Considerations](#10-scalability--resiliency-considerations)

---

## 1. System Architecture

### Architecture Diagram Description

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   DMS    │  │ Super App│  │  Admin   │  │  Norton  │  │ 3rd Party│     │
│  │  Portal  │  │ (Mobile) │  │  Portal  │  │   App    │  │   Apps   │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼──────────────┼──────────────┼──────────────┼──────────────┼─────────┘
        │              │              │              │              │
        └──────────────┴──────────────┴──────┬───────┴──────────────┘
                                             │ HTTPS
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AZURE API MANAGEMENT (APIM)                              │
│                  Rate Limiting · Throttling · Routing                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AZURE KUBERNETES SERVICE (AKS)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    tvsm-auth (Auth Ninja)                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │  Security   │  │ Application │  │    User     │  │  Scheduler │  │  │
│  │  │   Layer     │  │   Module    │  │   Module    │  │   Module   │  │  │
│  │  │ (JWT/AOP)   │  │ (OAuth/B2C) │  │(Profile/eKYC│  │  (Cron)    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────┐
│   Azure MySQL    │    │  Azure Services  │    │   External APIs          │
│   (Persistent)   │    │  B2C · Blob ·    │    │   Karza · MDP ·          │
│                  │    │  Face · Bus      │    │   Notification           │
└──────────────────┘    └──────────────────┘    └──────────────────────────┘
```

### Design Principles

- **Stateless**: No server-side sessions; all authentication via JWT tokens
- **Environment-agnostic**: All secrets/config injected via environment variables
- **Event-driven**: User lifecycle events published to Azure Service Bus for downstream consumers
- **Defense-in-depth**: APIM gateway + JWT filter + AOP-based token validation + role-based access

---

## 2. Major Components / Services

### Service Interaction

| Component | Responsibility | Interactions |
|-----------|---------------|--------------|
| **Security Layer** | JWT parsing, request authentication, role extraction | Intercepts all authenticated requests |
| **Application Module** | OAuth 2.0 flows, B2C token exchange, app registry | Azure B2C, Client Apps |
| **User Profile Module** | User CRUD, status lifecycle, face enrollment | MySQL, Azure B2C, Face API, Service Bus |
| **eKYC Module** | Identity verification (PAN/DL/Bank) | Karza API, MySQL |
| **Face Recognition Module** | Biometric detection, identification, liveness | Azure Face API |
| **Dealer Module** | Dealership management, branch data | MDP API, MySQL |
| **RBAC Module** | Roles, groups, departments, permissions | MySQL |
| **Dynamic Forms Module** | Configurable registration forms per app | MySQL |
| **Notification Gateway** | SMS delivery for consent and reminders | Notification Service |
| **Event Publisher** | Async event publishing | Azure Service Bus |
| **Scheduler Module** | Cron-based lifecycle jobs (reminders, deactivation) | MySQL, Notification Service |

### Internal Service Communication Pattern

```
Controller → Service → Repository (DB)
                    → Gateway (External API)
                    → Event Publisher (Service Bus)
```

All internal communication is synchronous (request-response). External event publishing is fire-and-forget via Service Bus.

---

## 3. Deployment Architecture

### Infra Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Cloud (India Region)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Azure Kubernetes Service (AKS)                 │ │
│  │                                                             │ │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐   │ │
│  │  │  Namespace: dev  │    │  Namespace: dev-cp (Norton) │   │ │
│  │  │  auth-ninja pod  │    │  norton-auth-ninja pod       │   │ │
│  │  └─────────────────┘    └─────────────────────────────┘   │ │
│  │                                                             │ │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐   │ │
│  │  │  Namespace: uat  │    │  Namespace: prod             │   │ │
│  │  │  auth-ninja pod  │    │  auth-ninja pod              │   │ │
│  │  └─────────────────┘    └─────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Azure MySQL  │  │ Azure Blob   │  │ Azure Service Bus    │  │
│  │ (per env)    │  │ Storage      │  │ (Topic: user_apps)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Azure AD B2C │  │ Azure Face   │  │ Azure APIM           │  │
│  │ (Identity)   │  │ API          │  │ (Gateway)            │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Flow

```
Developer → GitHub (Push to develop)
                │
                ▼
┌──────────────────────────────────┐
│  Azure DevOps CI Pipeline        │
│  1. Sonar Scan (quality gate)    │
│  2. Maven Build + Test           │
│  3. Docker Image Build           │
│  4. AST Image Security Scan      │
│  5. Push to Container Registry   │
└──────────────────┬───────────────┘
                   │ (trigger)
                   ▼
┌──────────────────────────────────┐
│  Azure DevOps CD Pipeline        │
│  1. Deploy to DEV (auto)         │
│  2. Manual Approval → UAT        │
│  3. Manual Approval → PROD       │
│  (Helm chart based deployment)   │
└──────────────────────────────────┘
```

### Container Specification

| Attribute | Value |
|-----------|-------|
| Base Image | `amazoncorretto:17.0.17-alpine3.19` |
| JVM Heap | `-Xms512m -XX:MaxRAMPercentage=75.0` |
| Port | 8080 |
| Timezone | Asia/Kolkata (IST) |
| Build Tool | Maven 3.9.12 (multi-stage Docker build) |

### Environments

| Environment | Namespace | Approval | Deployment |
|-------------|-----------|----------|------------|
| DEV | `dev` | Automatic | On CI completion |
| DEV-CP (Norton) | `dev-cp` | Automatic | On CI completion |
| UAT | `uat` | Manual (24h timeout) | Post-DEV |
| PROD | `prod` | Manual (24h timeout) | Post-UAT |

---

## 4. Database Interactions

### Database Technology

- **Engine**: Azure Database for MySQL
- **ORM**: Spring Data JPA (Hibernate)
- **Connection Pool**: HikariCP (max 50 connections, min idle 10)
- **Driver**: MySQL Connector/J 9.6.0

### Core Entity Model

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Application    │       │   UserDetails     │       │   Dealership     │
│──────────────────│       │──────────────────│       │──────────────────│
│ id               │       │ id               │       │ id               │
│ name             │       │ firstName        │       │ name             │
│ clientId         │◄──────│ dealerId         │──────▶│ dealerCode       │
│ clientSecret     │       │ b2cUserId        │       │ dealershipType   │
│ appCallbackUri   │       │ primaryPhone     │       │ mdpStatus        │
│ loginPolicies[]  │       │ status           │       └──────────────────┘
│ authMethods[]    │       │ userType         │
└──────────────────┘       │ bankDetails      │       ┌──────────────────┐
                           │ professionalDtls │       │  Role / Group    │
┌──────────────────┐       └────────┬─────────┘       │──────────────────│
│  UserEkycDetails │                │                  │ id               │
│──────────────────│                │                  │ name             │
│ id               │◄───────────────┤                  │                  │
│ type (PAN/DL/BNK)│                │                  └──────────────────┘
│ value            │                │
│ verified         │                ▼
│ comments         │       ┌──────────────────┐
└──────────────────┘       │ UserLoginAudit   │
                           │──────────────────│
                           │ id               │
                           │ userId           │
                           │ lastLogin        │
                           │ applicationId    │
                           │ authMethod       │
                           └──────────────────┘
```

### Key Database Operations

| Operation | Tables Involved | Frequency |
|-----------|----------------|-----------|
| User Registration | UserDetails, BankDetails, UserApplicationMapping | Medium |
| Login Audit | UserLoginAudit | High (every login) |
| eKYC Verification | UserEkycDetails, UserDetails, ConflictedUsers | Medium |
| Status Transitions | UserDetails | Medium |
| Role/Group CRUD | Role, Group, Department, Permission | Low |
| Scheduled Lifecycle | UserDetails, UserLoginAudit | Daily (cron) |

---

## 5. API Integrations

### External Integrations

| Integration | Protocol | Auth Method | Purpose |
|-------------|----------|-------------|---------|
| **Azure AD B2C** (Graph API) | HTTPS/REST | Client Credentials (OAuth 2.0) | User identity CRUD, JWKS key retrieval |
| **Azure Face API** | HTTPS/REST | Subscription Key (Header) | Face detect, identify, liveness verification |
| **Azure Blob Storage** | Azure SDK | Connection String | Profile photos, consent docs, pre-signed URLs |
| **Azure Service Bus** | AMQP (Azure SDK) | Managed Identity | Event publishing (user lifecycle) |
| **Karza** | HTTPS/REST | API Key (Header: x-karza-key) | PAN, DL, Bank Account verification |
| **MDP** | HTTPS/REST | Bearer Token (B2C client credentials) | Dealer/branch master data |
| **Notification Service** | HTTPS/REST | Bearer Token (B2C client credentials) | SMS delivery |
| **Site24x7** | HTTPS | API Key | Application performance monitoring, error tracking |

### Internal API Surface

| Base Path | Module | Auth Required |
|-----------|--------|---------------|
| `/auth/v1/app/**` | Application (OAuth) | No (public) |
| `/v1/app/**` | Application (OAuth) | No (public) |
| `/api/v1/user/**` | User Profile | Yes (JWT) |
| `/api/v1/user/ekyc/**` | eKYC | Yes (JWT) |
| `/api/v1/admin/**` | Admin | Yes (JWT) |
| `/api/v1/dealer/**` | Dealer | Yes (JWT) |
| `/api/v1/role/**` | Role | Yes (JWT) |
| `/api/v1/group/**` | Group | Yes (JWT) |
| `/api/v1/department/**` | Department | Yes (JWT) |
| `/api/v1/application/**` | User-Application Mapping | Yes (JWT) |
| `/api/v1/dynamic-forms/**` | Dynamic Forms | Yes (JWT) |

---

## 6. Authentication & Authorization Flow

### Authentication Architecture

```
┌──────────┐         ┌──────────┐         ┌──────────────┐         ┌──────────┐
│  Client  │──(1)──▶ │   APIM   │──(2)──▶ │JwtTokenFilter│──(3)──▶ │Controller│
│   App    │         │ Gateway  │         │              │         │          │
└──────────┘         └──────────┘         └──────────────┘         └──────────┘
                                                 │
                                          (Parse JWT Token)
                                          (Extract B2C ID)
                                          (Load User + Roles)
                                          (Set SecurityContext)
```

### Token Validation Layers

1. **APIM Layer**: Subscription key validation, rate limiting
2. **JwtTokenFilter**: Parses `Authorization` header, extracts B2C user ID, loads user details from DB, sets Spring SecurityContext
3. **@Authenticate AOP**: Additional token validation for specific endpoints (validates against B2C JWKS keys + client ID matching)
4. **Spring Security**: Role-based access control via `hasAnyAuthority()`

### OAuth 2.0 Authorization Code Flow

```
Client App                    Auth Ninja                    Azure B2C
    │                              │                            │
    │──(1) GET /token?app_id=X───▶│                            │
    │                              │──(2) Resolve policy───────▶│
    │◀──(3) 302 Redirect──────────│                            │
    │──────────────────────────────────(4) User Login──────────▶│
    │                              │◀──(5) Auth Code────────────│
    │                              │──(6) Exchange Code─────────▶│
    │                              │◀──(7) ID Token─────────────│
    │◀──(8) 302 Redirect + Token──│                            │
    │                              │                            │
```

### Role Hierarchy

```
Authority Set (from JWT claims)
    └── User Onboard Authorities (configurable)
         └── Functional Roles (per user)
              └── Permissions (per role)
```

---

## 7. External Systems

| System | Direction | Data Flow | SLA Dependency |
|--------|-----------|-----------|----------------|
| **Azure AD B2C** | Bidirectional | User creation, deletion, token validation, JWKS keys | Critical (login blocked if down) |
| **Azure Face API** | Outbound | Face images → detection/identification results | Critical for face-login |
| **Azure Service Bus** | Outbound | User lifecycle events (JSON messages to topic) | Non-blocking (fire-and-forget) |
| **Azure Blob Storage** | Bidirectional | Profile photos, consent PDFs, logo images | Medium (degraded UX if down) |
| **Karza** | Outbound | PAN/DL/Bank details → verification results | Medium (eKYC blocked if down) |
| **MDP (Master Data Platform)** | Inbound | Dealer/branch master data | Medium (onboarding blocked) |
| **Notification Service** | Outbound | SMS requests (consent, reminders) | Low (async, non-blocking) |
| **Site24x7** | Outbound | APM metrics, error reports, performance traces | Non-critical |
| **Azure DevOps** | CI/CD | Build artifacts, deployment triggers | Deployment only |

### Downstream Consumers (via Service Bus)

| Event | Topic | Consumers |
|-------|-------|-----------|
| `UmsUserActivatedEvent` | `{env}.ums.user_apps` | DMS, downstream services |
| `UmsUserUpdatedEvent` | `{env}.ums.user_apps` | DMS, downstream services |
| `UmsUserDeactivatedEvent` | `{env}.ums.user_apps` | DMS, downstream services |

---

## 8. Infrastructure Dependencies

| Resource | Service | Purpose |
|----------|---------|---------|
| Azure Kubernetes Service (AKS) | Compute | Container orchestration |
| Azure Database for MySQL | Storage | Persistent data store |
| Azure AD B2C Tenant | Identity | User identity provider |
| Azure Blob Storage | Storage | File/document storage |
| Azure Face API (Cognitive Services) | AI | Biometric verification |
| Azure Service Bus | Messaging | Async event distribution |
| Azure API Management (APIM) | Networking | API gateway, rate limiting |
| Azure Container Registry | CI/CD | Docker image storage |
| Azure Managed Identity | Security | Service Bus authentication |
| Site24x7 (SaaS) | Observability | APM, error tracking |
| Helm Charts | Deployment | K8s deployment configuration |

### Environment Variables (Categories)

| Category | Examples | Injection |
|----------|----------|-----------|
| Database | `DB_URI`, `DB_USERNAME`, `DB_PASSWORD` | K8s Secrets |
| Azure B2C | `B2C_TENANT_NAME`, `UMS_CLIENT_ID`, `B2C_ISSUER` | K8s ConfigMap/Secrets |
| Azure Services | `AZURE_FACE_URL`, `AZURE_BLOB_CONNECTION`, `AZURE_CLIENT_ID` | K8s Secrets |
| External APIs | `KARZA_API_BASE_URL`, `MDP_BASE_URL`, `NOTIFICATION_BASE_URL` | K8s ConfigMap |
| Business Config | `MAX_PENDING_DAYS`, `FACE_CONFIDENCE_THRESHOLD`, `EKYC_NAME_MATCH_THRESHOLD` | K8s ConfigMap |

---

## 9. High-Level Sequence Flows

### 9.1 User Registration Flow

```
Dealer Portal          Auth Ninja              Azure B2C         Face API        MySQL
     │                      │                      │                │              │
     │──POST /register-user─▶                      │                │              │
     │  (face + user data)  │                      │                │              │
     │                      │──validateFaceImage──────────────────▶│              │
     │                      │◀──validation result─────────────────│              │
     │                      │                      │                │              │
     │                      │──registerUserInB2C──▶│                │              │
     │                      │◀──B2C User Object────│                │              │
     │                      │                      │                │              │
     │                      │──addPersonToGroup────────────────────▶│              │
     │                      │──addFaceToPerson─────────────────────▶│              │
     │                      │──train───────────────────────────────▶│              │
     │                      │                      │                │              │
     │                      │──save UserDetails────────────────────────────────────▶│
     │                      │──publish UmsUserActivatedEvent──▶ Service Bus        │
     │                      │                      │                │              │
     │◀──201 Created────────│                      │                │              │
```

### 9.2 Face Login Flow

```
Mobile App             Auth Ninja              Face API            MySQL
     │                      │                      │                 │
     │──POST /face-login────▶                      │                 │
     │  (face image)        │                      │                 │
     │                      │──detectFace──────────▶│                 │
     │                      │◀──faceId─────────────│                 │
     │                      │                      │                 │
     │                      │──identifyFace────────▶│                 │
     │                      │◀──personId + conf────│                 │
     │                      │                      │                 │
     │                      │──lookup user by personId───────────────▶│
     │                      │◀──UserDetails──────────────────────────│
     │                      │                      │                 │
     │◀──200 OK (users)─────│                      │                 │
```

### 9.3 eKYC Verification Flow

```
Client App             Auth Ninja              Karza API           MySQL
     │                      │                      │                 │
     │──POST /ekyc/verify───▶                      │                 │
     │  (PAN/DL/Bank data)  │                      │                 │
     │                      │──check consent status────────────────▶│
     │                      │◀──consent OK──────────────────────────│
     │                      │                      │                 │
     │                      │──validatePan/DL/Bank─▶│                 │
     │                      │◀──name match score───│                 │
     │                      │                      │                 │
     │                      │──check conflicts─────────────────────▶│
     │                      │──save eKYC result────────────────────▶│
     │                      │                      │                 │
     │◀──200 OK (result)────│                      │                 │
```

### 9.4 Token Generation (Inter-Service)

```
Downstream Service     Auth Ninja              Azure B2C
     │                      │                      │
     │──POST /token/generate▶                      │
     │  (appId, secret)     │                      │
     │                      │──client_credentials──▶│
     │                      │◀──access_token────────│
     │                      │                      │
     │◀──200 (token)────────│                      │
```

---

## 10. Scalability & Resiliency Considerations

### Current Design

| Aspect | Implementation |
|--------|---------------|
| **Horizontal Scaling** | Stateless pods on AKS; scale via HPA (Horizontal Pod Autoscaler) |
| **Connection Pooling** | HikariCP with max 50 connections, min idle 10 |
| **Retry Logic** | Spring Retry (`@Retryable`) for transient failures on external calls |
| **Async Processing** | `AsyncJobService` for non-blocking operations (user activation post-eKYC) |
| **Caching** | `AppCacheManager` for JWKS keys (avoids repeated B2C calls per request) |
| **Event Decoupling** | Service Bus for downstream communication (no synchronous coupling) |
| **JVM Tuning** | `-XX:MaxRAMPercentage=75.0` for container-aware memory management |
| **Graceful Degradation** | Face login and eKYC are independent; one failing doesn't block the other |

### Resiliency Patterns

| Pattern | Where Applied |
|---------|---------------|
| **Circuit Breaker** | Not currently implemented (recommended for Karza/MDP) |
| **Timeout** | OkHttp client defaults; configurable per integration |
| **Retry with Backoff** | Spring Retry on user profile operations |
| **Idempotency** | eKYC checks if already verified before calling Karza |
| **Managed Identity** | Service Bus auth via Azure Managed Identity (no secret rotation needed) |
| **Multi-stage Docker** | Smaller attack surface, reduced image size |

### Recommendations for Scale

| Area | Recommendation |
|------|----------------|
| Database | Read replicas for high-read endpoints (login profile lookup) |
| Caching | Redis/Azure Cache for user profile and token validation results |
| Face API | Batch processing for bulk onboarding scenarios |
| Rate Limiting | Per-app rate limits at APIM level |
| Observability | Distributed tracing (OpenTelemetry) for cross-service debugging |
| Circuit Breaker | Resilience4j for Karza, MDP, and Notification integrations |

---

## Appendix: Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Language | Java 17 |
| Framework | Spring Boot 3.5.7 |
| Security | Spring Security + JWT + Azure B2C |
| ORM | Spring Data JPA (Hibernate) |
| Database | MySQL (Azure) |
| HTTP Client | OkHttp + WebClient (WebFlux) |
| Messaging | Azure Service Bus (AMQP) |
| Storage | Azure Blob Storage |
| AI/ML | Azure Face API (Cognitive Services) |
| Build | Maven 3.9.12 |
| Container | Docker (Alpine + Amazon Corretto 17) |
| Orchestration | Kubernetes (AKS) + Helm |
| CI/CD | Azure DevOps Pipelines |
| Code Quality | SonarQube + JaCoCo (40% min coverage) |
| Monitoring | Site24x7 |
| API Docs | SpringDoc OpenAPI (Swagger) |

---

*This document is intended for external engineering partners. Confidential business logic, credentials, and internal URLs have been omitted.*

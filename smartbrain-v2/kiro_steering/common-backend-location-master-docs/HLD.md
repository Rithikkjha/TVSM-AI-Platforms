# High Level Design (HLD) — Location Master Service

**Service Name:** `tvsmbe-location` (location-master)  
**Version:** 1.0.0  
**Document Version:** 1.0  
**Last Updated:** 2026-05-29  
**Author:** Engineering Team  

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Diagram Description](#2-architecture-diagram-description)
3. [System Architecture](#3-system-architecture)
4. [Major Components & Services](#4-major-components--services)
5. [Service Interactions](#5-service-interactions)
6. [Infrastructure Topology](#6-infrastructure-topology)
7. [Deployment Architecture & Flow](#7-deployment-architecture--flow)
8. [Database Interactions](#8-database-interactions)
9. [API Integrations](#9-api-integrations)
10. [Authentication & Authorization Flow](#10-authentication--authorization-flow)
11. [External Systems & Integrations](#11-external-systems--integrations)
12. [High-Level Sequence Flows](#12-high-level-sequence-flows)
13. [Scalability & Resiliency Considerations](#13-scalability--resiliency-considerations)
14. [Non-Functional Requirements](#14-non-functional-requirements)

---

## 1. Overview

The **Location Master Service** is a Spring Boot microservice that serves as the centralized platform for managing dealer location data across the TVS Motor dealer network. It handles dealer location submissions, verification workflows, proximity-based dealer search, geocoding, and location master data management.

**Key Capabilities:**
- Dealer location submission and photo capture (mobile flow)
- Admin verification/rejection workflow for submitted locations
- Proximity-based dealer finder (geospatial queries)
- Geocoding and reverse geocoding via Google Maps API
- SMS notifications to dealers for location updates
- Location master data management (Country, State, District, City, Pincode hierarchy)
- International Business (IB) dealer management
- Integration with Master Data Platform (MDP) for dealer metadata

**Technology Stack:**

| Layer | Technology |
|-------|-----------|
| Language | Java 17 |
| Framework | Spring Boot 3.5.x |
| Database | MongoDB |
| Object Storage | Azure Blob Storage |
| Authentication | Azure AD B2C (OAuth2 Client Credentials) |
| HTTP Client | OkHttp3 |
| Build Tool | Apache Maven 3.9 |
| Container Runtime | Docker (Amazon Corretto 17 Alpine) |
| CI/CD | Azure DevOps Pipelines |
| Monitoring | Sentry, OpenTelemetry, Spring Boot Actuator |
| API Documentation | SpringDoc OpenAPI (Swagger UI) |

---

## 2. Architecture Diagram Description

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS / CONSUMERS                                 │
├──────────────┬──────────────────┬───────────────────┬───────────────────────────┤
│  Admin Portal│  Dealer Mobile   │  Consumer App     │  Internal Services        │
│  (Web)       │  App             │  (Dealer Finder)  │                           │
└──────┬───────┴────────┬─────────┴─────────┬─────────┴────────────┬──────────────┘
       │                │                   │                      │
       ▼                ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AZURE API MANAGEMENT (APIM)                              │
│                    (JWT Validation, Rate Limiting, Routing)                       │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        LOCATION MASTER SERVICE                                   │
│                     (Spring Boot 3.5 / Java 17)                                  │
│                                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Admin Flow  │  │ Mobile Flow  │  │ Dealer Flow  │  │ Proximity/Search    │  │
│  │ Controller  │  │ Controller   │  │ Controller   │  │ Controllers         │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────────┬──────────┘  │
│         │                │                  │                     │              │
│         ▼                ▼                  ▼                     ▼              │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        SERVICE LAYER                                     │    │
│  │  AdminFlowService | MobileFlowService | DealerService | ProximityService │    │
│  │  GeocodingService | NotificationService | MDPDealerService | UMSService  │    │
│  └──────────────────────────────────┬──────────────────────────────────────┘    │
│                                     │                                            │
│  ┌──────────────────────────────────┴──────────────────────────────────────┐    │
│  │                      REPOSITORY LAYER (19 Repositories)                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          ▼                            ▼                            ▼
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────────────┐
│    MongoDB       │    │  Azure Blob Storage  │    │   External Services      │
│  (location_master│    │  (Dealer Photos)     │    │  ┌────────────────────┐  │
│   database)      │    │                      │    │  │ MDP Service        │  │
│                  │    │                      │    │  │ UMS Service        │  │
│                  │    │                      │    │  │ Notification Svc   │  │
│                  │    │                      │    │  │ Google Maps API    │  │
└──────────────────┘    └──────────────────────┘    │  └────────────────────┘  │
                                                    └──────────────────────────┘
```

---

## 3. System Architecture

### 3.1 Architecture Style

The Location Master Service follows a **layered monolithic architecture** deployed as a containerized microservice:

- **Presentation Layer** — REST Controllers exposing HTTP APIs
- **Business Logic Layer** — Service classes with domain logic, orchestration, and external integrations
- **Data Access Layer** — Spring Data MongoDB repositories
- **Cross-Cutting Concerns** — Security filters, caching, retry, audit logging, scheduling

### 3.2 Design Principles

| Principle | Implementation |
|-----------|---------------|
| Stateless | JWT-based auth, no server-side sessions |
| Resilient | Spring Retry (3-5 attempts) on all external API calls |
| Auditable | All external API calls and key operations logged to MongoDB |
| Secure | Role-based access control, Azure B2C token management |
| Observable | Sentry error tracking, OpenTelemetry tracing, Actuator health checks |

### 3.3 Runtime Configuration

Configuration is externalized via environment variables, supporting multi-environment deployment (local, dev, uat, prod) through Spring profiles (`spring.profiles.active`).

---

## 4. Major Components & Services

### 4.1 Controller Layer (API Endpoints)

| Controller | Base Path | Access Level | Purpose |
|-----------|-----------|-------------|---------|
| `AdminFlowController` | `/api/v1/admin-flow` | Admin (TM, HR Manager) | Dealer verification, summary, SMS dispatch |
| `DealerFlowController` | `/api/v1/dealer-flow` | Dealer (Owner, Branch Mgr) | Dealer self-service location management |
| `MobileFlowController` | `/v1/dealer-location` | Open | Mobile location submission with photo |
| `DealerProximityController` | `/api/v1/finder` | Open | Proximity-based dealer search |
| `DealershipLocationController` | `/api/v1/dealer-search` | Open | Dealer search by criteria |
| `LocationMasterController` | `/api/v1/location` | Open | Location master data (states) |
| `GeoCodeController` | `/api/v1/geo` | Open | Geocoding operations |
| `IBDealerController` | `/api/v1/dealer` | Admin | International Business dealer CRUD |
| `CountryController` | `/api/v1/country` | Open | Country data |
| `MigrationController` | `/api/v1/admin/migrate` | Admin | Data migration utilities |

### 4.2 Service Layer

| Service | Responsibility |
|---------|---------------|
| `AdminFlowService` | Admin workflow orchestration — summary, list, verify/reject dealers |
| `DealerService` | Dealer data retrieval, branch details, location details |
| `MobileFlowOperationalService` | Mobile submission processing, photo upload, secret key validation |
| `DealerProximityService` | Proximity-based dealer search using MDP and geospatial queries |
| `DealershipLocationService` | Dealer search with filtering and pagination |
| `MDPDealerService` | Integration with Master Data Platform for dealer metadata |
| `UMSService` | User Management Service integration — token validation, contacts |
| `NotificationSmsDispatcherService` | SMS dispatch via Notification Service |
| `GeocodingService` | Geocoding orchestration (forward and reverse) |
| `GoogleMapsApiCallerService` | Direct Google Maps Geocoding API integration |
| `AzureB2CTokenGenerationService` | OAuth2 client credentials token generation |
| `AzureB2CTokenManager` | Token lifecycle management with caching |
| `AzureBlobOperationService` | Photo upload/download, SAS URL generation |
| `CronService` | Scheduled JVM metrics and executor pool logging |
| `AsyncJobService` | Async task execution with thread pool management |
| `AuditLogService` | Audit trail persistence |
| `IBDealerManagementService` | International Business dealer operations |

### 4.3 Repository Layer (Data Access)

| Repository | Collection | Purpose |
|-----------|-----------|---------|
| `DealerInfoDetailsRepository` | `dealer_data` | Dealer location submissions and status |
| `DealershipLocationRepository` | `dealership_location` | Dealer store locations (GeoJSON indexed) |
| `VerifiedDealerLocationRepository` | `verified_dealer_locations` | Approved dealer locations |
| `DealerSecretKeyRepository` | — | Mobile flow secret key management |
| `AuditLogRepository` | — | Audit trail |
| `RejectionCommentsRepository` | — | Configurable rejection reasons |
| `CountryRepository` | — | Country master data |
| `StateRepository` / `StateDetailsRepo` | — | State master data |
| `DistrictRepository` / `SubDistrictRepository` | — | District hierarchy |
| `CityRepository` | — | City master data |
| `AreaRepository` | — | Area master data |
| `PincodeRepository` / `PincodeCentroidRepo` | — | Pincode and centroid data |
| `DivisionRepository` | — | Division data |
| `LocationRepo` / `LocaleRepo` | — | Location and locale data |

---

## 5. Service Interactions

```
┌────────────────────────────────────────────────────────────────────────┐
│                    LOCATION MASTER SERVICE                              │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    INTERNAL SERVICE MESH                          │  │
│  │                                                                  │  │
│  │  AdminFlowService ──────► MDPDealerService                       │  │
│  │       │                        │                                 │  │
│  │       ├──────► UMSService      ├──► AzureB2CTokenManager         │  │
│  │       │                        │         │                       │  │
│  │       ├──────► NotificationSmsDispatcherService                  │  │
│  │       │                                                          │  │
│  │       └──────► AzureBlobOperationService                         │  │
│  │                                                                  │  │
│  │  MobileFlowService ──► AzureBlobOperationService                 │  │
│  │       │                                                          │  │
│  │       └──────► GeocodingService ──► GoogleMapsApiCallerService   │  │
│  │                                                                  │  │
│  │  DealerProximityService ──► MDPDealerService                     │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌─────────┐   ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │   MDP   │   │   UMS    │  │Notif Svc │  │ Google Maps  │
    │ Service │   │ Service  │  │          │  │     API      │
    └─────────┘   └──────────┘  └──────────┘  └──────────────┘
```

### 5.1 Inter-Service Communication Pattern

All external service communication uses:
- **Protocol:** HTTPS (REST)
- **Client:** OkHttp3 (synchronous)
- **Authentication:** Azure B2C OAuth2 tokens (client credentials grant)
- **Resilience:** Spring `@Retryable` with 3-5 max attempts
- **Audit:** All API calls logged to MongoDB audit collection

### 5.2 Token Flow for External Services

```
Service Call → TokenCacheManager.getToken()
                    │
            ┌───────┴────────┐
            │ Token in cache  │
            │ & not expired?  │
            └───────┬────────┘
              Yes ↙     ↘ No
         Use cached    AzureB2CTokenGenerationService
          token              .generateToken()
                                   │
                              Cache new token
                                   │
                              Return token
```

---

## 6. Infrastructure Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AZURE CLOUD                                   │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              AZURE API MANAGEMENT (APIM)                       │  │
│  │         (Gateway, JWT Validation, Rate Limiting)               │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│  ┌───────────────────────────▼───────────────────────────────────┐  │
│  │              AZURE APP SERVICE                                  │  │
│  │         (Container Hosting - Linux)                             │  │
│  │                                                                │  │
│  │    ┌─────────────────────────────────────────────────────┐    │  │
│  │    │  Docker Container                                    │    │  │
│  │    │  (Amazon Corretto 17 Alpine + location-master.jar)   │    │  │
│  │    │  Port: 8080                                          │    │  │
│  │    │  JVM: -XX:MaxRAMPercentage=75                        │    │  │
│  │    │  TZ: Asia/Kolkata                                    │    │  │
│  │    └─────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  MongoDB      │  │ Azure Blob       │  │ Azure Container       │  │
│  │  (CosmosDB /  │  │ Storage          │  │ Registry (ACR)        │  │
│  │   Atlas)      │  │ (dealer photos)  │  │                       │  │
│  └──────────────┘  └──────────────────┘  └───────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    AZURE AD B2C                                │   │
│  │         (Identity Provider - Token Issuance)                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.1 Environment Topology

| Environment | Purpose | Approval Gate |
|-------------|---------|---------------|
| **Dev** | Development and integration testing | Automatic (post-CI) |
| **UAT** | User acceptance testing | Manual approval required |
| **Prod** | Production | Manual approval required |

---

## 7. Deployment Architecture & Flow

### 7.1 CI/CD Pipeline

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Code    │    │  SonarQube   │    │   CI Build   │    │ Docker Image │
│  Commit  │───►│  PR Analysis │───►│  (Maven +    │───►│ Security     │
│  (main)  │    │              │    │   Docker)    │    │ Scan (AST)   │
└──────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                               │
                                                               ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Deploy     │◄───│   Deploy     │◄───│   Deploy     │◄───│  Push to     │
│   PROD       │    │   UAT        │    │   DEV        │    │  ACR         │
│ (Manual Gate)│    │ (Manual Gate)│    │ (Automatic)  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### 7.2 Build Process

1. **Source:** GitHub repository (`TVSM-DMS/tvsmbe-location`)
2. **SonarQube Analysis:** Triggered on PR creation for code quality gates
3. **CI Pipeline:** Triggered after SonarQube passes on `main` branch
   - Maven build (`mvn clean install`)
   - Docker multi-stage build (build + runtime stages)
   - JaCoCo code coverage report generation
4. **Image Security Scan:** AST (Application Security Testing) pipeline scans Docker image
5. **CD Pipeline:** Multi-stage deployment with manual approval gates

### 7.3 Docker Build Strategy

```dockerfile
# Stage 1: Maven Build
FROM maven:3.9.14-amazoncorretto-17-alpine AS build
# Compiles source and produces location-master.jar

# Stage 2: Runtime
FROM amazoncorretto:17.0.18-alpine3.23
# Minimal runtime image with JVM tuning
# -XX:MaxRAMPercentage=75 for container-aware memory management
```

### 7.4 Container Registry

- **Registry:** Azure Container Registry (ACR)
- **Image naming:** `tvsmazcmnsvcacrdev01location.azurecr.io/location-master:<tag>`
- **Deployment target:** Azure App Service (Linux container)

---

## 8. Database Interactions

### 8.1 Database Technology

- **Engine:** MongoDB
- **Connection:** Via `MONGODB_URI` environment variable (connection string with auth)
- **Features Used:** MongoAuditing, Transactions, GeoJSON indexes, Text indexes

### 8.2 Data Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MongoDB: location_master                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  CORE COLLECTIONS                                            │    │
│  │                                                              │    │
│  │  dealer_data                 ← Location submissions          │    │
│  │    - sapDealerCode (indexed)                                 │    │
│  │    - dealerLocationStatus                                    │    │
│  │    - submittedLocationDetails (lat, lng, address, accuracy)  │    │
│  │    - imageCapturedLocationDetails                            │    │
│  │    - locationType (SALES/SERVICE)                            │    │
│  │    - photoUrl                                                │    │
│  │                                                              │    │
│  │  dealership_location         ← Dealer store locations        │    │
│  │    - dealerCode (indexed)                                    │    │
│  │    - location.geocode (GeoJSON 2dsphere index)               │    │
│  │    - location.countryCode (indexed)                          │    │
│  │    - status, flags                                           │    │
│  │                                                              │    │
│  │  verified_dealer_locations   ← Approved locations            │    │
│  │    - sapDealerCode (unique index)                            │    │
│  │    - verifiedLocationDetails[]                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  LOCATION HIERARCHY COLLECTIONS                              │    │
│  │                                                              │    │
│  │  Country → State → District → SubDistrict → City → Area     │    │
│  │  Pincode, PincodeCentroid, Division                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  OPERATIONAL COLLECTIONS                                     │    │
│  │                                                              │    │
│  │  AuditLog          ← API call audit trail                    │    │
│  │  DealerSecretKey   ← Mobile flow authentication keys         │    │
│  │  RejectionComment  ← Configurable rejection reasons          │    │
│  │  UserX             ← User data                               │    │
│  │  Locale            ← Localization data                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Base Entity Pattern

All entities extend `MongoBaseEntity` providing:
- `id` — MongoDB ObjectId (auto-generated)
- `createdAt` — Auto-populated via `@CreatedDate`
- `updatedAt` — Auto-populated via `@LastModifiedDate`

### 8.4 Geospatial Queries

The `dealership_location` collection uses MongoDB's `GeoJsonPoint` type with `2dsphere` index for proximity-based dealer search operations.

---

## 9. API Integrations

### 9.1 External API Summary

| External Service | Protocol | Auth Method | Purpose |
|-----------------|----------|-------------|---------|
| MDP (Master Data Platform) | REST/HTTPS | Azure B2C Token | Dealer metadata, active dealer codes, branches, proximity |
| UMS (User Management Service) | REST/HTTPS | Azure B2C Token | Token validation, dealer/branch manager contacts |
| Notification Service | REST/HTTPS | Azure B2C Token + APIM Key | SMS dispatch, SMS status check |
| Google Maps Geocoding API | REST/HTTPS | API Key | Forward/reverse geocoding |
| Azure Blob Storage | Azure SDK | Connection String | Photo upload, SAS URL generation |
| Azure AD B2C | OAuth2 | Client Credentials | Token generation for service-to-service auth |

### 9.2 MDP Integration Details

| API Endpoint | Method | Purpose |
|-------------|--------|---------|
| `/v1/dealer/{code}` | GET | Get single dealer data |
| `/v1/dealers/data?fetchMdpActiveDealersOnly=true` | POST | Get bulk dealer data |
| `/v1/dealers/listOfSapDealerCode/basedOnFilters` | POST | List dealer codes with filters |
| `/v1/dealer/{code}/branches` | GET | Get dealer branches |
| `/v1/dealers/listOfDealerDetails/basedOnProximity` | POST | Proximity-based dealer search |

### 9.3 UMS Integration Details

| API Endpoint | Method | Purpose |
|-------------|--------|---------|
| `/api/v1/dealer/get-contacts?dealerId={id}` | GET | Get dealer and branch manager contacts |
| `/auth/v1/app/token/validate` | POST | Validate JWT token |

### 9.4 Notification Service Integration

| API Endpoint | Method | Purpose |
|-------------|--------|---------|
| `/api/v1/notification/sms` | POST | Send SMS notification |
| `/api/v1/notification/{id}` | GET | Check SMS delivery status |

### 9.5 Google Maps Geocoding API

| API Endpoint | Method | Purpose |
|-------------|--------|---------|
| `/maps/api/geocode/json?address={addr}&key={key}` | GET | Address to coordinates |
| `/maps/api/geocode/json?latlng={lat,lng}&key={key}` | GET | Coordinates to address |

---

## 10. Authentication & Authorization Flow

### 10.1 Authentication Architecture

```
┌──────────┐         ┌──────────┐         ┌─────────────────────┐
│  Client  │──JWT───►│  APIM    │──JWT───►│  Location Master    │
│          │         │(validates│         │                     │
│          │         │  token)  │         │  RequestFilter      │
└──────────┘         └──────────┘         │    │                │
                                          │    ▼                │
                                          │  Extract JWT payload│
                                          │  (no re-validation) │
                                          │    │                │
                                          │    ▼                │
                                          │  Set SecurityContext│
                                          │  with roles         │
                                          │    │                │
                                          │    ▼                │
                                          │  Spring Security    │
                                          │  Role-based access  │
                                          └─────────────────────┘
```

### 10.2 Security Configuration

- **Session Management:** Stateless (no server-side sessions)
- **CSRF:** Disabled (stateless JWT-based API)
- **Token Validation:** Delegated to Azure APIM gateway; service extracts payload only
- **Filter:** `RequestFilter` extends `OncePerRequestFilter`, runs before `UsernamePasswordAuthenticationFilter`

### 10.3 Role-Based Access Control (RBAC)

| API Category | Required Roles |
|-------------|---------------|
| Open APIs | No authentication required |
| Admin APIs | `Territory Manager`, `HR Manager` |
| Dealer APIs | `Dealer Owner/Partner`, `Branch Manager` |

### 10.4 JWT Token Payload Structure

The JWT token (issued by Azure AD B2C via UMS) contains:
- `sub` — User ID
- `name` — User name
- `dealerId` — SAP Dealer Code
- `primaryPhoneNumber` — User phone
- `baseRoles` — Array of role objects (department, group, role)
- `branches` — Array of branch assignments

### 10.5 Service-to-Service Authentication

For outbound calls to MDP, UMS, and Notification Service:
- **Grant Type:** OAuth2 Client Credentials
- **Identity Provider:** Azure AD B2C
- **Token Caching:** In-memory with TTL-based expiry (buffer of 60 seconds before actual expiry)
- **Token Refresh:** Automatic on 401 response (cache eviction + retry)

---

## 11. External Systems & Integrations

### 11.1 Infrastructure Dependencies

| Dependency | Type | Purpose | Criticality |
|-----------|------|---------|-------------|
| MongoDB | Database | Primary data store | Critical |
| Azure Blob Storage | Object Store | Dealer location photos | High |
| Azure AD B2C | Identity | Token issuance for service auth | Critical |
| Azure APIM | Gateway | Request routing, JWT validation, rate limiting | Critical |
| Azure App Service | Compute | Container hosting | Critical |
| Azure Container Registry | Registry | Docker image storage | High |
| Azure DevOps | CI/CD | Build and deployment pipelines | High |

### 11.2 External Service Dependencies

| Service | Owner | Purpose | Failure Impact |
|---------|-------|---------|---------------|
| MDP (Master Data Platform) | Internal | Dealer master data | Degraded — cannot validate dealers or fetch metadata |
| UMS (User Management Service) | Internal | User auth, contacts | Degraded — admin/dealer flows impacted |
| Notification Service | Internal | SMS dispatch | Degraded — SMS notifications fail (non-blocking) |
| Google Maps Geocoding API | Google | Address/coordinate conversion | Degraded — geocoding features unavailable |
| Sentry | External | Error monitoring | Non-critical — monitoring only |

### 11.3 Azure Blob Storage

- **Container:** `dealer-location-photo`
- **Operations:** Upload photos, generate SAS presigned URLs
- **URL Expiry:** Configurable (default 2 hours)
- **Public Domain:** Configurable for CDN/custom domain access

---

## 12. High-Level Sequence Flows

### 12.1 Dealer Location Submission (Mobile Flow)

```
Dealer Mobile App          Location Master              Azure Blob       MongoDB
      │                         │                          │               │
      │  POST /v1/dealer-       │                          │               │
      │  location/submit        │                          │               │
      │  (data + photo file)    │                          │               │
      │────────────────────────►│                          │               │
      │                         │  Validate secret key     │               │
      │                         │─────────────────────────────────────────►│
      │                         │◄─────────────────────────────────────────│
      │                         │                          │               │
      │                         │  Upload photo            │               │
      │                         │─────────────────────────►│               │
      │                         │◄─────────────────────────│               │
      │                         │                          │               │
      │                         │  Save dealer_data        │               │
      │                         │─────────────────────────────────────────►│
      │                         │◄─────────────────────────────────────────│
      │                         │                          │               │
      │◄────────────────────────│                          │               │
      │   200 OK (DealerResponse)                          │               │
```

### 12.2 Admin Verification Flow

```
Admin Portal        APIM        Location Master         MDP          MongoDB
     │               │               │                   │              │
     │  GET /admin-  │               │                   │              │
     │  flow/summary │               │                   │              │
     │──────────────►│──────────────►│                   │              │
     │               │               │  Query dealer_data│              │
     │               │               │─────────────────────────────────►│
     │               │               │◄─────────────────────────────────│
     │◄──────────────│◄──────────────│                   │              │
     │               │               │                   │              │
     │  POST /admin- │               │                   │              │
     │  flow/verify  │               │                   │              │
     │──────────────►│──────────────►│                   │              │
     │               │               │  Get dealer from  │              │
     │               │               │  MDP              │              │
     │               │               │──────────────────►│              │
     │               │               │◄──────────────────│              │
     │               │               │                   │              │
     │               │               │  Update status +  │              │
     │               │               │  save to verified │              │
     │               │               │─────────────────────────────────►│
     │               │               │◄─────────────────────────────────│
     │◄──────────────│◄──────────────│                   │              │
```

### 12.3 Proximity-Based Dealer Search

```
Consumer App        APIM        Location Master              MDP
     │               │               │                        │
     │  POST /finder │               │                        │
     │  /dealers     │               │                        │
     │  {lat, lng,   │               │                        │
     │   radius}     │               │                        │
     │──────────────►│──────────────►│                        │
     │               │               │  POST proximity API    │
     │               │               │───────────────────────►│
     │               │               │◄───────────────────────│
     │               │               │  (sorted by distance)  │
     │               │               │                        │
     │◄──────────────│◄──────────────│                        │
     │  200 OK       │               │                        │
     │  [dealers]    │               │                        │
```

### 12.4 SMS Notification Flow

```
Admin Portal     Location Master     AzureB2C     Notification Svc     Dealer
     │                │                  │               │                │
     │  POST /send-   │                  │               │                │
     │  location-     │                  │               │                │
     │  update-sms    │                  │               │                │
     │───────────────►│                  │               │                │
     │                │  Get B2C token   │               │                │
     │                │─────────────────►│               │                │
     │                │◄─────────────────│               │                │
     │                │                  │               │                │
     │                │  POST /sms       │               │                │
     │                │─────────────────────────────────►│                │
     │                │◄─────────────────────────────────│                │
     │                │                  │               │  SMS delivered  │
     │                │                  │               │───────────────►│
     │◄───────────────│                  │               │                │
     │  200 OK        │                  │               │                │
```

---

## 13. Scalability & Resiliency Considerations

### 13.1 Current Scalability Characteristics

| Aspect | Current State | Notes |
|--------|--------------|-------|
| Horizontal Scaling | Supported | Stateless design allows multiple instances |
| Caching | In-memory (per-instance) | Not shared across instances |
| Database | MongoDB | Supports sharding and replica sets |
| File Storage | Azure Blob | Inherently scalable |
| Async Processing | Thread pool (`AsyncJobService`) | Configurable pool size |

### 13.2 Resiliency Patterns Implemented

| Pattern | Implementation | Details |
|---------|---------------|---------|
| **Retry** | Spring `@Retryable` | 3-5 attempts on external API failures |
| **Token Refresh** | Auto-evict on 401 | Removes cached token and retries |
| **Circuit Breaker** | Not implemented | Recommended for future |
| **Timeout** | OkHttp client timeouts | Prevents indefinite blocking |
| **Graceful Degradation** | Partial | SMS failures don't block core flows |
| **Health Checks** | Spring Actuator | `/actuator/health` endpoint |
| **Error Tracking** | Sentry | Real-time error alerting in production |

### 13.3 Monitoring & Observability

| Tool | Purpose | Environment |
|------|---------|-------------|
| Sentry | Error tracking, performance monitoring | Production |
| OpenTelemetry Agent | Distributed tracing | All environments |
| Spring Boot Actuator | Health, metrics, info endpoints | All environments |
| CronService | JVM memory + thread pool metrics (every 60s) | All environments |
| Logback | Structured logging with rolling files | All environments |
| Audit Log (MongoDB) | Business operation audit trail | All environments |

### 13.4 Scalability Recommendations

1. **Distributed Caching:** Consider Redis for shared token cache across instances
2. **Circuit Breaker:** Add Resilience4j for MDP/UMS/Notification service calls
3. **Rate Limiting:** Implement per-client rate limiting at service level
4. **Database Indexing:** Ensure compound indexes on frequently queried fields
5. **Connection Pooling:** Configure MongoDB connection pool for high concurrency
6. **Async Processing:** Consider message queue (Azure Service Bus) for SMS dispatch

### 13.5 Single Points of Failure

| Component | Risk | Mitigation |
|-----------|------|-----------|
| MongoDB | Database unavailability | Replica set / CosmosDB with multi-region |
| MDP Service | Dealer data unavailable | Retry + local cache of dealer data |
| Azure B2C | Token generation failure | Token caching with TTL buffer |
| Google Maps API | Geocoding unavailable | Graceful degradation, fallback |

---

## 14. Non-Functional Requirements

### 14.1 Performance

- **Response Time Target:** < 500ms for read APIs, < 2s for write APIs with external calls
- **File Upload:** Supports up to 100MB per file, 200MB per request
- **Export Limit:** Maximum 2000 records per export operation

### 14.2 Security

- All APIs behind Azure APIM gateway
- JWT-based stateless authentication
- Role-based authorization (RBAC)
- No secrets in code — all via environment variables
- HTTPS enforced for all external communications
- SAS tokens with configurable expiry for blob access

### 14.3 Availability

- Container-based deployment on Azure App Service
- Multi-environment setup with promotion gates
- Health check endpoints via Spring Actuator
- Automatic restart on container failure (Azure App Service)

### 14.4 Maintainability

- OpenAPI/Swagger documentation auto-generated
- Structured logging with correlation
- Comprehensive audit trail in MongoDB
- Code coverage enforcement via JaCoCo
- SonarQube quality gates on PRs

---

*Document generated from source code analysis. For architecture decisions and rationale, refer to internal ADR documents.*

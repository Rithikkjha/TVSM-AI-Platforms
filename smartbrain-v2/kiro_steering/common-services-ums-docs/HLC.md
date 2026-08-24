# High Level Code Document — tvsm-auth (Auth Ninja)

## 1. Application Overview

**tvsm-auth** (internally known as "Auth Ninja") is a Spring Boot 3.5.7 microservice built with Java 17 that serves as the centralized **Authentication & Authorization** platform for TVS Motor's digital ecosystem. It manages user identity lifecycle, application-level access control, eKYC verification, and face-based biometric authentication for dealer employees, distributors, and internal users.

| Attribute | Value |
|-----------|-------|
| Framework | Spring Boot 3.5.7 |
| Language | Java 17 |
| Build Tool | Maven |
| Database | MySQL (via HikariCP connection pool) |
| Artifact | `com.tvsmotor:tvsm-auth:1.0.0` |

---

## 2. Major Modules / Components

| Module | Package | Responsibility |
|--------|---------|----------------|
| **Applications** | `applications/` | Application registry, B2C OAuth flows, token validation/generation |
| **User Profile** | `user/profile/` | User registration, status management, dealer-employee lifecycle |
| **eKYC** | `user/profile/ekyc/` | Identity verification via PAN, Driving License, Bank Account (Karza) |
| **Face Recognition** | `user/gateway/FaceRecognitionService` | Biometric face detection, identification, liveness verification |
| **Dealership** | `user/dealership/` | Dealer entity management, MDP integration |
| **RBAC** | `user/role/`, `user/group/`, `user/department/`, `user/permission/` | Role-based access control hierarchy |
| **Dynamic Forms** | `user/dynamicforms/` | Configurable registration forms per application |
| **Gateways** | `user/gateway/` | External service clients (Azure B2C, MDP, Notifications, Service Bus) |
| **Security** | `config/` | JWT filter, Spring Security, AOP-based token validation |
| **Schedulers** | `user/profile/scheduler/` | Cron-based user lifecycle and notification jobs |

---

## 3. Folder Structure

```
src/main/java/com/tvsmotor/tvsmauth/
├── AuthApplication.java                 # Spring Boot entry point
├── aop/                                 # @Authenticate aspect for token validation
├── applications/                        # Application entity, OAuth flows, token APIs
│   ├── controller/                      # ApplicationController, exception handlers
│   ├── dto/                             # Request/response DTOs
│   ├── entity/                          # Application, LoginPolicies, AuthenticationMethod
│   ├── exception/                       # Custom exceptions
│   ├── gateway/                         # AzureB2CGateway (token validation, JWKS)
│   └── repository/                      # JPA repositories
├── config/                              # Security, JWT filter, Azure configs, caching
├── support/                             # Utilities (constants, blob, encryption, JSON, validation)
└── user/
    ├── dealership/                      # Dealership entity and service
    ├── department/                      # Department CRUD
    ├── designation/                     # Designation entity
    ├── dynamicforms/                    # Dynamic form registration
    ├── gateway/                         # External service clients
    │   ├── AzureGatewayB2C.java        # MS Graph API for B2C user management
    │   ├── AzureServiceBusPublisher.java # Event publishing
    │   ├── FaceRecognitionService.java  # Azure Face API integration
    │   ├── MDPServiceClient.java        # Master Data Platform client
    │   ├── NotificationGateway.java     # SMS notification client
    │   └── UMSServiceClient.java        # Inter-service token generation
    ├── group/                           # Group CRUD with role mappings
    ├── permission/                      # Permission entity
    ├── profile/                         # Core user profile domain
    │   ├── api/                         # REST controllers
    │   ├── dto/                         # 60+ DTOs
    │   ├── ekyc/                        # eKYC verification sub-module
    │   ├── entity/                      # 26 JPA entities
    │   ├── enums/                       # Status, UserType, Gender
    │   ├── repository/                  # 22 JPA repositories
    │   ├── scheduler/                   # Cron jobs
    │   └── service/                     # Business logic services
    ├── role/                            # Role CRUD
    ├── specialization/                  # Specialization entity
    └── type/                            # Type entity
```

---

## 4. Core Business Workflows

### 4.1 User Registration (Dealer Employee)
1. Dealer submits employee details + face image via `/api/v1/user/register-user`
2. Face image validated (quality, liveness, uniqueness) via Azure Face API
3. User created in local DB with `PENDING_ACTIVE` status
4. User registered in Azure B2C (Graph API) with phone-based identity
5. Face enrolled in Azure Large Person Group for future identification
6. Consent SMS sent to user for eKYC
7. User activated after eKYC completion

### 4.2 OAuth Login Flow
1. Client app requests auth URL via `/auth/v1/app/token?app_id=...`
2. Service resolves login policy by country code and auth method
3. User redirected to Azure B2C login page
4. B2C returns auth code to `/auth/v1/app/callback/{appName}`
5. Service exchanges code for token, validates user, checks employee confirmation
6. User redirected to application callback with token

### 4.3 Face-Based Login
1. User submits face image via `/auth/v1/app/face-login`
2. Face detected and identified against enrolled person groups
3. Matching users returned with confidence scores
4. Optional liveness verification via `/auth/v1/app/face/verification` with session-based check

### 4.4 eKYC Verification
1. User consent collected via SMS link
2. Verification triggered via `/api/v1/user/ekyc/verify`
3. Karza API validates PAN / Driving License / Bank Account
4. Name matching performed with configurable threshold
5. Conflict detection if same document already verified for another user
6. User status updated on successful verification

### 4.5 User Lifecycle Management
- **Status transitions**: Pending Active → Active → Passive → Inactive
- **Scheduled jobs**: Deactivation of unused accounts, face login reminders
- **Bulk operations**: CSV-based onboarding, bulk deactivation

---

## 5. Key Services / Classes

| Service | Responsibility |
|---------|----------------|
| `ApplicationServiceImpl` | Application registry, B2C OAuth flow orchestration, token generation |
| `UserProfileService` | User CRUD, status management, face verification, application assignment |
| `EkycService` | eKYC orchestration (PAN, DL, Bank), conflict detection |
| `EkycValidationKarzaService` | Karza API integration for document verification |
| `FaceRecognitionService` | Azure Face API operations (detect, identify, validate, liveness) |
| `AdminService` | Admin user onboarding, dealership management |
| `DealerProfileService` | Dealer-specific operations, branch management |
| `UserOnboardFlxService` | Bulk user/dealer onboarding via CSV |
| `ConsentService` | User consent management, SMS-based consent collection |
| `AzureGatewayB2C` | MS Graph API for B2C user CRUD operations |
| `MDPServiceClient` | Master Data Platform integration for dealer/branch data |
| `AzureServiceBusPublisher` | Event publishing to Azure Service Bus topics |
| `JwtTokenFilter` | Request authentication, token parsing, SecurityContext setup |
| `AuthenticateAspect` | AOP-based token validation for annotated endpoints |

---

## 6. External Integrations

| Integration | Purpose | Protocol |
|-------------|---------|----------|
| **Azure AD B2C** | User identity management, OAuth 2.0 flows, JWKS token validation | MS Graph API (REST) |
| **Azure Face API** | Face detection, identification, liveness verification, person group management | REST (OkHttp) |
| **Azure Service Bus** | Asynchronous event publishing (user activated/updated/deactivated) | Azure SDK (AMQP) |
| **Azure Blob Storage** | Profile photos, consent documents, logo images, pre-signed URLs | Azure SDK |
| **Karza** | eKYC verification — PAN, Driving License, Bank Account validation | REST (OkHttp) |
| **MDP (Master Data Platform)** | Dealer and branch master data retrieval | REST (OkHttp) |
| **Notification Service** | SMS delivery for consent links and face login reminders | REST (OkHttp) |
| **Site24x7** | Application performance monitoring, error tracking | SDK |

---

## 7. Major Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Spring Boot Starter Web | 3.5.11 | REST API framework |
| Spring Boot Starter Security | 3.5.7 | Authentication/authorization |
| Spring Boot Starter Data JPA | 3.5.7 | Database access (Hibernate) |
| Spring Boot Starter WebFlux | 3.5.7 | Reactive WebClient for external calls |
| MySQL Connector/J | 9.6.0 | Database driver |
| Microsoft Graph SDK | 5.79.0 | Azure B2C Graph API |
| MSAL4J | 1.20.1 | Microsoft Authentication Library |
| Azure Identity | 1.18.1 | Azure credential management |
| Azure Messaging Service Bus | 7.17.4 | Service Bus event publishing |
| Azure Storage Blob | 12.25.2 | Blob storage operations |
| Azure AI Vision Face | 1.0.0-beta.2 | Face liveness verification |
| Auth0 Java JWT | 4.4.0 | JWT token parsing and validation |
| Spring Retry | — | Retry logic for transient failures |
| OpenCSV | 5.12.0 | CSV parsing for bulk operations |
| SpringDoc OpenAPI | 2.8.13 | API documentation (Swagger) |
| Lombok | — | Boilerplate reduction |
| JaCoCo | 0.8.11 | Code coverage (min 40% line coverage) |

---

## 8. Runtime Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Applications                          │
│              (DMS, Super App, Admin Portal, etc.)                    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Azure API Management (APIM)                      │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      tvsm-auth (Auth Ninja)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Security     │  │ Controllers  │  │ Scheduled Jobs            │  │
│  │ (JWT Filter) │→ │ (REST APIs)  │  │ (Notification, Lifecycle) │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────────┘  │
│                            │                                         │
│                    ┌───────▼────────┐                                │
│                    │  Service Layer │                                │
│                    └───────┬────────┘                                │
│           ┌────────────────┼────────────────┐                       │
│           ▼                ▼                ▼                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Repository  │  │   Gateways   │  │ Event Pub    │               │
│  │ (JPA/MySQL) │  │ (External)   │  │ (Service Bus)│               │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘               │
└─────────┼────────────────┼──────────────────┼───────────────────────┘
          │                │                  │
          ▼                ▼                  ▼
┌──────────────┐  ┌────────────────┐  ┌────────────────────┐
│   MySQL DB   │  │ Azure B2C      │  │ Azure Service Bus  │
│              │  │ Azure Face API │  │ (Topic: user_apps) │
│              │  │ Karza (eKYC)   │  │                    │
│              │  │ MDP            │  │                    │
│              │  │ Notification   │  │                    │
│              │  │ Azure Blob     │  │                    │
└──────────────┘  └────────────────┘  └────────────────────┘
```

**Runtime characteristics:**
- Stateless (session: STATELESS) — all auth via JWT tokens
- Connection pool: HikariCP (max 50, min idle 10)
- Async operations via `AsyncJobService` for non-blocking tasks
- Spring Retry for transient failure handling
- Managed Identity for Azure Service Bus authentication

---

## 9. Important Entry Points

| Entry Point | Path | Description |
|-------------|------|-------------|
| `AuthApplication.java` | — | Spring Boot main class |
| `ApplicationController` | `/auth/v1/app/**` | OAuth flows, token operations, face login (public) |
| `UserProfileController` | `/api/v1/user/**` | User management (authenticated) |
| `AdminController` | `/api/v1/admin/**` | Admin operations (authenticated) |
| `EkycController` | `/api/v1/user/ekyc/**` | eKYC verification (authenticated) |
| `DealerController` | `/api/v1/dealer/**` | Dealer operations (authenticated) |
| `DynamicFormController` | `/api/v1/dynamic-forms/**` | Dynamic registration (authenticated) |
| `JwtTokenFilter` | — | Security filter — authenticates all non-open requests |
| `SecurityConfig` | — | Defines open URLs vs authenticated endpoints |

**Open (unauthenticated) endpoints:**
- `/auth/v1/app/**` and `/v1/app/**` — OAuth flows
- `/api/v1/user/b2c-login-profile` — B2C login profile lookup
- `/v1/user/ekyc/get-consent-content` and `/v1/user/ekyc/submit-consent` — Consent flow
- `/api/v1/dealer/get-contacts` — Dealer contacts
- `/api/v1/admin/onboard-tvsm-user` — TVSM user onboarding

---

## 10. High-Level Data Flow

```
┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│  Client  │────▶│  JWT Filter  │────▶│  Controller │────▶│  Service │
│  App     │     │  (Auth)      │     │  (REST)     │     │  Layer   │
└──────────┘     └──────────────┘     └─────────────┘     └────┬─────┘
                                                                │
                        ┌───────────────────────────────────────┤
                        │                                       │
                        ▼                                       ▼
               ┌─────────────────┐                    ┌─────────────────┐
               │  JPA Repository │                    │    Gateways     │
               │  (MySQL)        │                    │  (External APIs)│
               └────────┬────────┘                    └────────┬────────┘
                        │                                      │
                        ▼                                      ▼
               ┌─────────────────┐                    ┌─────────────────┐
               │  MySQL Database │                    │  Azure B2C      │
               │  - UserDetails  │                    │  Azure Face API │
               │  - Applications │                    │  Karza          │
               │  - Roles/Groups │                    │  MDP            │
               │  - eKYC Records │                    │  Service Bus    │
               │  - Audit Logs   │                    │  Blob Storage   │
               └─────────────────┘                    └─────────────────┘
```

**Key data entities:**
- `UserDetails` — Core user record (personal info, status, B2C ID, dealer mapping)
- `Application` — Registered client applications with login policies
- `Role` / `Group` / `Department` — RBAC hierarchy
- `UserEkycDetails` — eKYC verification records
- `UserLoginAudit` — Login history for lifecycle management
- `Dealership` / `UserDealershipMapping` — Dealer-branch associations
- `BankDetails` / `ProfessionalDetails` — Extended user profile data

---

## Integration Summary

| System | Direction | Data Exchanged |
|--------|-----------|----------------|
| Azure B2C | Bidirectional | User creation/deletion, token validation, OAuth flows |
| Azure Face API | Outbound | Face images for detection, identification, liveness |
| Azure Service Bus | Outbound | User lifecycle events (activated, updated, deactivated) |
| Azure Blob Storage | Bidirectional | Profile photos, consent PDFs, logo images |
| Karza | Outbound | PAN/DL/Bank details for verification |
| MDP | Inbound | Dealer master data, branch information |
| Notification Service | Outbound | SMS messages (consent links, reminders) |
| Client Applications | Inbound | API requests for auth, user management |

---

*Document generated for vendor onboarding purposes. Sensitive credentials and business logic details have been omitted.*

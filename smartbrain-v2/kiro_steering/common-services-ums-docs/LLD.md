# Low Level Design (LLD) — tvsm-auth (Auth Ninja)

| Attribute | Value |
|-----------|-------|
| Service Name | tvsm-auth (Auth Ninja) |
| Version | 1.0.0 |
| Framework | Spring Boot 3.5.7 / Java 17 |
| Last Updated | June 2026 |

---

## Table of Contents

1. [Detailed Module Breakdown](#1-detailed-module-breakdown)
2. [Class/Service Responsibilities](#2-classservice-responsibilities)
3. [API Flow Details](#3-api-flow-details)
4. [Internal Component Interactions](#4-internal-component-interactions)
5. [Database Schema Usage](#5-database-schema-usage)
6. [Request/Response Lifecycle](#6-requestresponse-lifecycle)
7. [Validation Logic](#7-validation-logic)
8. [Error Handling](#8-error-handling)
9. [Key Algorithms & Business Rules](#9-key-algorithms--business-rules)
10. [Configuration Handling](#10-configuration-handling)

---

## API Endpoints Summary

| Controller | Base Path | Total APIs | Auth Required |
|-----------|-----------|-----------|---------------|
| `ApplicationController` | `/auth/v1/app` | 10 | No (Public) |
| `UserProfileController` | `/api/v1/user` | 28 | Yes (JWT) |
| `AdminController` | `/api/v1/admin` | 3 | Yes (JWT) |
| `EkycController` | `/api/v1/user/ekyc` | 1 | Yes (JWT) |
| `ConsentController` | `/v1/user` | 2 | No (Public) |
| `DealerController` | `/api/v1/dealer` | 6 | Yes (JWT) |
| `RoleController` | `/api/v1/role` | 6 | Yes (JWT) |
| `GroupController` | `/api/v1/group` | 3 | Yes (JWT) |
| `DepartmentController` | `/api/v1/department` | 2 | Yes (JWT) |
| `UserApplicationController` | `/api/v1/application` | 4 | Yes (JWT) |
| `DynamicFormController` | `/api/v1/dynamic-forms` | 5 | Yes (JWT) |
| **Total** | | **70** | |

---

## 1. Detailed Module Breakdown

### 1.1 Applications Module (`applications/`)

| Class | Type | Purpose |
|-------|------|---------|
| `ApplicationController` | Controller | OAuth token flow, B2C callback, face login, session creation |
| `ApplicationExceptionHandler` | Advice | Global exception handling for `CustomException`, `LoginRedirectException` |
| `ValidationHandler` | Advice | Bean validation error formatting |
| `ApplicationService` | Interface | Application business operations contract |
| `ApplicationServiceImpl` | Service | OAuth flow orchestration, token exchange, app registry |
| `AzureB2CGateway` | Gateway | B2C JWKS key retrieval, token validation, token generation |
| `Application` | Entity | Application registry (clientId, policies, auth methods) |
| `LoginPolicies` | Entity | Country-specific B2C user flow policies |
| `ApplicationRepository` | Repository | JPA CRUD for Application entity |

### 1.2 User Profile Module (`user/profile/`)

| Class | Type | Purpose |
|-------|------|---------|
| `UserProfileController` | Controller | User CRUD, registration, status changes, face operations |
| `AdminController` | Controller | Admin user onboarding, dealership listing |
| `DealerController` | Controller | Dealer branches, contacts, onboarding |
| `ConsentController` | Controller | eKYC consent content and submission |
| `UserApplicationController` | Controller | Application-user assignment/removal |
| `UserProfileService` | Service | Core user lifecycle, face verification, status transitions |
| `AdminService` | Service | Admin-specific onboarding logic |
| `DealerProfileService` | Service | Dealer branch listing, contacts |
| `DealerEmployeeProfileService` | Service | Dealer employee listing with pagination |
| `UserOnboardFlxService` | Service | Bulk CSV onboarding for users and dealers |
| `EmployeeIdGeneratorService` | Service | Sequential employee ID generation |
| `UserDetails` | Entity | Core user entity (abstract, single-table inheritance) |
| `DealerEmployees` | Entity | Dealer employee subclass of UserDetails |
| `HOUser` | Entity | Head Office user subclass |
| `TvsmUser` | Entity | TVSM internal user subclass |
| `Distributor` | Entity | Distributor user subclass |
| `SupportUser` | Entity | Support user subclass |

### 1.3 eKYC Module (`user/profile/ekyc/`)

| Class | Type | Purpose |
|-------|------|---------|
| `EkycController` | Controller | Single endpoint `/verify` for all eKYC types |
| `EkycService` | Service | Orchestrates PAN/DL/Bank verification, conflict detection |
| `EkycValidationKarzaService` | Service | Karza API integration (PAN, DL, Bank, Name Match) |
| `EkycValidationService` | Interface | Strategy interface for eKYC providers |
| `EkycValidationServiceFactory` | Factory | Returns correct validation service by vendor |
| `ConsentService` | Service | Consent SMS sending, content retrieval, submission |
| `AsyncService` | Service | Async consent notification after registration |
| `UserEkycDetails` | Entity | Stores verification results per user |
| `UserConsentDetails` | Entity | Stores consent acceptance records |

### 1.4 Gateway Module (`user/gateway/`)

| Class | Type | Purpose |
|-------|------|---------|
| `AzureGatewayB2C` | Gateway | MS Graph API: create/delete/update users in B2C |
| `FaceRecognitionService` | Gateway | Azure Face API: detect, identify, validate, liveness |
| `MDPServiceClient` | Gateway | MDP API: fetch dealer/branch master data |
| `NotificationGateway` | Gateway | Notification service: send SMS |
| `UMSServiceClient` | Gateway | Inter-service token generation |
| `AzureServiceBusPublisher` | Gateway | Publish user lifecycle events to Service Bus topic |

### 1.5 RBAC Module (`user/role/`, `user/group/`, `user/department/`)

| Class | Type | Purpose |
|-------|------|---------|
| `RoleController` | Controller | Role CRUD, types/specializations, designations |
| `GroupController` | Controller | Group CRUD, role assignments |
| `DepartmentController` | Controller | Department listing, groups by department |
| `RoleService` | Service | Role business logic, reporting role mapping |
| `GroupService` | Service | Group business logic |
| `DepartmentService` | Service | Department business logic |

### 1.6 Dynamic Forms Module (`user/dynamicforms/`)

| Class | Type | Purpose |
|-------|------|---------|
| `DynamicFormController` | Controller | Form retrieval, validation, registration, update |
| `FormService` | Service | Dynamic form logic, user registration via form |
| `FormValidatorUtil` | Utility | Runtime form field validation |

### 1.7 Configuration Module (`config/`)

| Class | Type | Purpose |
|-------|------|---------|
| `SecurityConfig` | Config | Spring Security filter chain, URL authorization |
| `JwtTokenFilter` | Filter | JWT parsing, user loading, SecurityContext setup |
| `AccessDeniedHandler` | Handler | Custom 403 response |
| `GraphServiceClientConfig` | Config | MS Graph SDK client bean |
| `AzureServiceBusConfig` | Config | Service Bus sender client bean |
| `AzureBlobStorageConfig` | Config | Blob storage client bean |
| `OkHttpClientConfig` | Config | Shared OkHttp client bean |
| `WebClientConfiguration` | Config | WebClient bean for B2C calls |
| `CacheConfig` | Config | In-memory cache configuration |
| `AsyncConfig` | Config | Async thread pool configuration |
| `SwaggerConfig` | Config | OpenAPI/Swagger documentation |

### 1.8 Support Module (`support/`)

| Class | Type | Purpose |
|-------|------|---------|
| `AppConstants` | Constants | URL patterns, regex, API paths, role names |
| `AppUtils` | Utility | Token parsing, B2C URL building, phone formatting |
| `BlobStorageUtil` | Utility | Blob upload/download, pre-signed URL generation |
| `EncryptUtil` | Utility | AES-GCM encryption/decryption for passwords |
| `PasswordUtil` | Utility | Password generation for B2C users |
| `JsonUtil` | Utility | Jackson serialization/deserialization helpers |
| `SanitizeUtil` | Utility | Input sanitization against XSS |
| `ValidationUtil` | Utility | Multipart file validation (type, size) |
| `MessageUtil` | Utility | i18n message resolution |
| `OkHttpService` | Utility | Generic HTTP POST/GET helper |
| `AsyncJobService` | Utility | Async job submission with delay support |

---

## 2. Class/Service Responsibilities

### 2.1 UserProfileService (Core Service)

**Dependencies**: 30+ injected beans (repositories, gateways, other services)

| Method Category | Key Methods | Description |
|----------------|-------------|-------------|
| Registration | `registerUser()` | Full registration: face validate → B2C create → face enroll → DB save → event publish |
| Status Management | `changeUserStatus()`, `deactivateUser()`, `bulkDeactivation()` | Status transitions with B2C sync |
| Query | `getUserWithApplicationDetails()`, `getUserDetailsByB2CUserId()` | User lookup with related data |
| Face Operations | `verifyFaceExists()`, `verifyFaceExistsAndFetchUsers()`, `UpdateAndVerifyFaceExists()` | Face detection + identification |
| Lifecycle | `updatePendingActiveUsersToInactive()`, `changeUnUsedUsersToPassive()` | Scheduled status transitions |
| Validation | `validateDealerUserUpdate()`, `verifyPrimaryPhoneNumber()` | Business rule enforcement |
| Application | `assignApplicationToUser()`, `unassignApplicationToUser()` | App-user mapping |

### 2.2 ApplicationServiceImpl

| Method | Description |
|--------|-------------|
| `getB2CAuthUri()` | Resolves login policy by country/auth-type, builds B2C authorize URL |
| `getB2CTokenWithCallbackUri()` | Exchanges auth code for token, validates user, returns callback URL |
| `validateToken()` | Validates JWT against B2C JWKS keys via `AzureB2CGateway` |
| `generateB2CToken()` | Client credentials flow for inter-service tokens |
| `getEndSessionEndpoint()` | Builds B2C logout URL with redirect |
| `getLoginFormResponseByClientId()` | Returns app metadata (title, logo, auth methods) for login UI |

### 2.3 EkycService

| Method | Description |
|--------|-------------|
| `verifyUserEkyc()` | Main orchestrator: checks consent → checks if already verified → calls Karza → detects conflicts → saves result |
| `validatePanNumber()` | External PAN-only validation (no user context) |
| `checkIfEkycAlreadyDoneForTheUser()` | Idempotency check before calling external API |
| `checkForConflict()` | Detects if same document verified for another user |
| `saveUserEkycDetails()` | Persists verification result |

### 2.4 FaceRecognitionService

| Method | Description |
|--------|-------------|
| `validateFaceImage()` | Quality checks: position, blur, noise, exposure, accessories, head pose, eye openness |
| `detectFace()` | Calls Azure Face Detect API, returns faceId |
| `identifyFace()` | Matches faceId against enrolled person group |
| `addPersonToGroup()` | Enrolls new person in large person group |
| `addFaceToPerson()` | Adds face image to enrolled person |
| `train()` | Triggers model training after enrollment changes |
| `verifyFaceLoginWithLiveliness()` | Session-based liveness + verification check |
| `sessionCreation()` | Creates liveness session with reference image |
| `removePersonByPersonId()` | Removes person from group (on deactivation) |

### 2.5 AzureGatewayB2C (Graph API)

| Method | Description |
|--------|-------------|
| `registerUserInB2C()` | Creates user with phone-based identity in B2C |
| `registerUserInB2CWithEmployeeId()` | Creates user with phone + employeeId identities |
| `getUserByPhoneNumber()` | Looks up B2C user by phone identity |
| `deleteUserInB2C()` | Removes user from B2C directory |
| `updateAccountEnabledInB2C()` | Enables/disables B2C account |

---

## 3. API Flow Details

### 3.1 User Registration (`POST /api/v1/user/register-user`)

```
Request: multipart/form-data
  - face: MultipartFile (JPEG/PNG, max 5MB)
  - data: JSON (DealerEmployeeCreateRequest)

Flow:
1. ValidationUtil.validateAndSanitizeMultipart(face) → checks file type, size
2. UserProfileService.registerUser():
   a. Validate phone number uniqueness
   b. FaceRecognitionService.validateFaceImage(face) → quality checks
   c. Generate employee ID (EmployeeIdGeneratorService)
   d. Generate password (PasswordUtil)
   e. Encrypt password (EncryptUtil.encrypt)
   f. AzureGatewayB2C.registerUserInB2CWithEmployeeId() → create in B2C
   g. Save UserDetails to MySQL
   h. FaceRecognitionService.addPersonToGroup() → enroll face
   i. FaceRecognitionService.addFaceToPerson() → add face image
   j. FaceRecognitionService.train() → retrain model
   k. AzureServiceBusPublisher.publishEvent(UmsUserActivatedEvent)
3. AsyncService.sendConsentNotification() → async SMS

Response: 201 Created
  - ApplicationUserDetailsDto (user details + assigned applications)
```

### 3.2 OAuth Token Flow (`GET /auth/v1/app/token`)

```
Request: Query params (app_id, callback_uri, country, aut, lhi, scp)

Flow:
1. ApplicationServiceImpl.getB2CAuthUri():
   a. Find Application by clientId
   b. Resolve LoginPolicy by countryCode + authType
   c. Build B2C authorize URL with PKCE challenge
2. Return 302 redirect to B2C login page

Response: 302 Found (Location: B2C authorize URL)
```

### 3.3 B2C Callback (`GET /auth/v1/app/callback/{appName}`)

```
Request: Query params (code, state/policyName, error)

Flow:
1. If error → redirect to UMS login with error message
2. ApplicationServiceImpl.getB2CTokenWithCallbackUri():
   a. Find Application by name
   b. Exchange auth code for ID token (WebClient POST to B2C token endpoint)
   c. Extract B2C user ID from token
   d. Load UserDetails from DB
   e. Check employee confirmation (if enabled for app)
   f. Build callback URL with token
3. Return 302 redirect to app callback

Response: 302 Found (Location: app_callback_uri?token=...)
```

### 3.4 Face Login (`POST /auth/v1/app/face-login`)

```
Request: multipart/form-data (face: MultipartFile)

Flow:
1. UserProfileService.verifyFaceExistsAndFetchUsers():
   a. FaceRecognitionService.detectFace(face) → get faceId
   b. FaceRecognitionService.identifyFace(faceId, personGroupId) → candidates
   c. Filter by confidence threshold
   d. Lookup users by personId from PersonGroupDetails
   e. Build response with user details + confidence scores

Response: 200 OK (FaceDetailsWithUsersResponse)
```

### 3.5 eKYC Verification (`POST /api/v1/user/ekyc/verify`)

```
Request: JSON (ValidationRequest: userId, ekycType, panNumber/dlNumber/accountNumber/ifscCode/dob)

Flow:
1. ValidationRequest.validateAndSanitize() → input sanitization
2. EkycService.verifyUserEkyc():
   a. Check if eKYC enabled for user's application
   b. Load UserDetails (throw if inactive)
   c. Check consent status
   d. Check if already verified (idempotency)
   e. Call Karza API (PAN/DL/Bank based on type)
   f. Compare name match score against threshold
   g. Check for conflicts with existing users
   h. Save UserEkycDetails record
   i. (Disabled) Auto-activate user post-verification

Response: 200 OK (ValidationResponse: verified, comments, userNameFromEKyc)
```

### 3.6 Token Validation (`POST /auth/v1/app/token/validate`)

```
Request: Header (Authorization: Bearer <token>), Body (TokenVerificationRequest: appId, countryCode)

Flow:
1. ApplicationServiceImpl.validateToken():
   a. Find Application by clientId
   b. AzureB2CGateway.validateToken():
      - Decode JWT header → extract kid
      - Check cache for JWKS key
      - If miss: fetch OpenID config → fetch JWKS keys → cache
      - Verify signature using RSA public key
      - Validate audience matches clientId

Response: 200 OK (TokenVerificationResponse: isValid)
```

---

## 4. Internal Component Interactions

### 4.1 Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROLLERS                                  │
│  ApplicationController  UserProfileController  EkycController  ...  │
└──────────────┬──────────────────┬──────────────────┬────────────────┘
               │                  │                  │
               ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          SERVICES                                    │
│  ApplicationServiceImpl  UserProfileService  EkycService            │
│  AdminService  DealerProfileService  UserOnboardFlxService          │
└──────┬──────────────┬──────────────┬──────────────┬─────────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐
│ Repositories│ │  Gateways  │ │  Utilities │ │  Event Publisher   │
│ (JPA/MySQL) │ │ (External) │ │ (Support)  │ │ (Service Bus)      │
└────────────┘ └────────────┘ └────────────┘ └────────────────────┘
```

### 4.2 Cross-Service Dependencies

| Service | Depends On |
|---------|-----------|
| `UserProfileService` | `AzureGatewayB2C`, `FaceRecognitionService`, `MDPServiceClient`, `AzureServiceBusPublisher`, `BlobStorageUtil`, `EmployeeIdGeneratorService`, `RoleService`, `GroupService`, `DepartmentService`, `DealershipService` |
| `ApplicationServiceImpl` | `AzureB2CGateway`, `UserProfileService`, `BlobStorageUtil`, `WebClient` |
| `EkycService` | `UserProfileService`, `EkycValidationServiceFactory`, `AsyncJobService` |
| `EkycValidationKarzaService` | `OkHttpService` |
| `JwtTokenFilter` | `UserProfileService` |
| `AuthenticateAspect` | `ApplicationService` |

### 4.3 Event Flow

```
UserProfileService
    │
    ├── registerUser() ──────▶ AzureServiceBusPublisher.publishEvent(UmsUserActivatedEvent)
    ├── changeUserStatus() ──▶ AzureServiceBusPublisher.publishEvent(UmsUserUpdatedEvent)
    └── deactivateUser() ────▶ AzureServiceBusPublisher.publishEvent(UmsUserDeactivatedEvent)
                                        │
                                        ▼
                              Azure Service Bus Topic
                              ({env}.ums.user_apps)
                                        │
                                        ▼
                              Downstream Subscribers (DMS, etc.)
```

### 4.4 Caching Strategy

| Cache | Key | Value | TTL | Purpose |
|-------|-----|-------|-----|---------|
| JWKS Keys | `kid` (Key ID) | `KeyBean` (RSA public key) | Until eviction | Avoid repeated B2C JWKS calls |
| Scheduled Clear | — | — | Periodic | `CacheClearScheduler` clears stale entries |

---

## 5. Database Schema Usage

### 5.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          user_details (Single Table Inheritance)          │
│─────────────────────────────────────────────────────────────────────────│
│ id (PK, AUTO_INCREMENT)    │ b2c_user_id          │ first_name          │
│ last_name                  │ date_of_birth        │ email               │
│ primary_phone_number       │ secondary_phone      │ gender (ENUM)       │
│ status (ENUM)              │ user_type (ENUM)     │ dealer_id           │
│ login_id                   │ comments             │ maritial_status     │
│ multiple_branch_allowed    │ branches (JSON)      │ self_onboarding     │
│ db_user_type (DISCRIMINATOR)│ created_at          │ updated_at          │
│ created_by                 │ updated_by           │                     │
└─────────────┬───────────────────────────┬───────────────────────────────┘
              │ 1:1                        │ 1:N
              ▼                            ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│   address            │    │   user_base_role_mapping     │
│──────────────────────│    │──────────────────────────────│
│ id (PK)              │    │ id (PK)                      │
│ line1, line2, line3  │    │ user_id (FK)                 │
│ city, state, country │    │ role_id (FK)                 │
│ zip_code             │    │ created_at, updated_at       │
└──────────────────────┘    └──────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────┐
│   bank_details       │    │   professional_details       │
│──────────────────────│    │──────────────────────────────│
│ id (PK)              │    │ id (PK)                      │
│ account_number       │    │ employee_id                  │
│ ifsc_code            │    │ driving_licence_number       │
│ pan_number           │    │ date_of_joining              │
│ bank_name            │    │ designation_id               │
└──────────────────────┘    └──────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────┐
│   user_ekyc_details  │    │   user_consent_details       │
│──────────────────────│    │──────────────────────────────│
│ id (PK)              │    │ id (PK)                      │
│ user_id (FK)         │    │ user_id (FK)                 │
│ type (ENUM: PAN/DL/  │    │ consent_accepted             │
│        BANK)         │    │ consent_date                 │
│ value (JSON)         │    │ signed_consent_url           │
│ verified (boolean)   │    │ created_at                   │
│ comments             │    └──────────────────────────────┘
│ created_at           │
└──────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────┐
│   user_face_details  │    │   person_group_details       │
│──────────────────────│    │──────────────────────────────│
│ user_id (PK, FK)     │    │ id (PK)                      │
│ face_id              │    │ person_id                    │
│ person_id            │    │ large_person_group_id        │
│ large_person_group_id│    │ user_id (FK)                 │
└──────────────────────┘    └──────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────┐
│   user_login_audit   │    │   conflicted_users           │
│──────────────────────│    │──────────────────────────────│
│ id (PK)              │    │ id (PK)                      │
│ user_id (FK)         │    │ existing_user_id             │
│ last_login           │    │ existing_dealer_id           │
│ application_id       │    │ new_user_id                  │
│ auth_method          │    │ new_dealer_id                │
└──────────────────────┘    └──────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────────────┐
│   application        │    │   login_policies             │
│──────────────────────│    │──────────────────────────────│
│ id (PK)              │    │ id (PK)                      │
│ name (UNIQUE)        │    │ application_id (FK)          │
│ client_id (UNIQUE)   │    │ name (policy name)           │
│ client_secret        │    │ country_code                 │
│ redirect_uri         │    │ is_default                   │
│ app_callback_uri     │    └──────────────────────────────┘
│ app_logout_uri       │
│ is_ekyc_enabled      │    ┌──────────────────────────────┐
│ is_emp_confirmation  │    │   user_application_mapping   │
│ auth_methods         │    │──────────────────────────────│
│ title, logo_image    │    │ id (PK)                      │
└──────────────────────┘    │ user_id (FK)                 │
                            │ application_id (FK)          │
                            └──────────────────────────────┘
```

### 5.2 Inheritance Strategy

`UserDetails` uses **Single Table Inheritance** with discriminator column `db_user_type`:

| Discriminator Value | Subclass | Description |
|--------------------|----------|-------------|
| `DEALER_EMPLOYEE` | `DealerEmployees` | Dealer staff |
| `HO` | `HOUser` | Head Office users |
| `TVSM` | `TvsmUser` | TVSM internal users |
| `DISTRIBUTOR` | `Distributor` | Distributor users |
| `SUPPORT` | `SupportUser` | Support team |

### 5.3 Key Repository Methods

| Repository | Custom Methods |
|-----------|----------------|
| `UserDetailsRepository` | `findByB2cUserId()`, `findByPrimaryPhoneNumber()`, `findByStatus()`, `findByDealerId()` |
| `DealerEmployeeRepository` | `findByDealerIdAndStatus()`, pagination queries |
| `UserLoginAuditRepository` | `findLatestLoginAuditByUser()` |
| `PersonGroupDetailsRepository` | `findByPersonId()`, `findByUserId()` |
| `ConflictedUsersRepository` | `findByExistingUserIdOrNewUserId()` |
| `UserApplicationMappingRepository` | `findCountOfUserByApplicationId()` |
| `ApplicationRepository` | `findByClientId()`, `findByName()` |

---

## 6. Request/Response Lifecycle

### 6.1 Authenticated Request Pipeline

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ 1. Spring Security Filter Chain                      │
│    └─ JwtTokenFilter.doFilterInternal()             │
│       a. Check if URL is in OPEN_URLS → skip auth   │
│       b. Extract "Authorization" header             │
│       c. Parse JWT → extract B2C user ID            │
│       d. Check for "ums.api" role → use admin ID    │
│       e. Load UserDetails from DB by B2C ID         │
│       f. Build AuthenticationDto (user + roles)     │
│       g. Set SecurityContextHolder                  │
│       h. Continue filter chain                      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ 2. Controller Method                                 │
│    - @Valid annotation triggers bean validation      │
│    - @RequestBody / @RequestPart deserialization     │
│    - Calls service layer                            │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ 3. Service Layer                                     │
│    - Business logic execution                       │
│    - Repository calls (DB)                          │
│    - Gateway calls (external APIs)                  │
│    - Event publishing                               │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ 4. Response                                          │
│    - ResponseEntity with DTO                        │
│    - Jackson serialization to JSON                  │
│    - HTTP status code                               │
└─────────────────────────────────────────────────────┘
```

### 6.2 @Authenticate AOP Flow (Application Module)

```
Request to @Authenticate annotated method
    │
    ▼
AuthenticateAspect.validateAuthHeader()
    │
    ├── Extract "Authorization" header
    ├── Extract "x-client-id" header
    ├── If either empty → throw TokenException
    ├── ApplicationService.validateToken(clientId, token)
    │       └── AzureB2CGateway.validateToken()
    │              ├── Decode JWT header → get kid
    │              ├── Fetch/cache JWKS keys
    │              ├── Verify RSA signature
    │              └── Validate aud == clientId
    ├── If invalid → throw TokenException
    └── Proceed to controller method
```

### 6.3 Open URL Request (No Auth)

URLs matching `OPEN_URLS` set bypass `JwtTokenFilter` via `shouldNotFilter()`:
- `/auth/v1/app/**` — OAuth flows
- `/v1/app/**` — OAuth flows (alternate path)
- `/api/v1/user/b2c-login-profile` — Login profile lookup
- `/v1/user/ekyc/get-consent-content` — Consent content
- `/v1/user/ekyc/submit-consent` — Consent submission
- `/api/v1/dealer/get-contacts` — Dealer contacts
- `/api/v1/admin/onboard-tvsm-user` — TVSM onboarding

---

## 7. Validation Logic

### 7.1 Bean Validation (Jakarta Validation)

| DTO Field | Annotation | Rule |
|-----------|-----------|------|
| `firstName` | `@NotBlank` | Cannot be empty |
| `email` | `@Email` | Must be valid email format |
| `primaryPhoneNumber` | `@Pattern(PHONE_NUMBER)` | Numeric with optional `+` prefix |
| `userId` | `@NotNull` | Required for operations |
| `userIds` (bulk) | `@NotEmpty` | At least one ID required |

### 7.2 Multipart File Validation (`ValidationUtil.validateAndSanitizeMultipart`)

```java
Checks performed:
1. File not null (if required=true)
2. Content type in allowed list:
   - Images: image/jpeg, image/jpg, image/png
   - Documents: text/csv, application/json, application/vnd.ms-excel
3. File size within Spring limits (5MB max)
4. Content sanitization
```

### 7.3 Face Image Validation (`FaceRecognitionService.validateFaceImage`)

| Check | Threshold | Error Message |
|-------|-----------|---------------|
| No face detected | 0 faces | "No face detected in the image" |
| Multiple faces | >1 faces | "Multiple faces detected" |
| Edge proximity | 10% margin | "Face is too close to the edge" |
| Center deviation | 20% tolerance | "Face is not centered" |
| Too far (area ratio) | <3% of image | "Face is too far from the camera" |
| Too close (area ratio) | >60% of image | "Face is too close to the camera" |
| Too far (pixel width) | <90px on large images | "Face is too far from the camera" |
| Noise | "high" level | "Image is too noisy" |
| Under-exposure | "underexposure" | "Image is too dark" |
| Over-exposure | "overexposure" | "Image is too bright" |
| Blur | "high" or value ≥0.45 | "Image is too blurry" |
| Mouth occluded | true | "Please remove any mask" |
| Forehead occluded | true | "Please remove any hat" |
| Eye occluded | true | "Eyes are not clearly visible" |
| Sunglasses | "sunglasses" | "Please remove sunglasses" |
| Headwear accessory | confidence >0.8 | "Please remove any headwear" |
| Head pose (yaw) | >25° | "Please look straight at the camera" |
| Head pose (pitch) | >20° | "Please look straight at the camera" |
| Head pose (roll) | >20° | "Please look straight at the camera" |
| Eyes closed (EAR) | height/width <0.20 | "Eyes appear to be closed" |
| Pupils not detected | null | "Pupils are not visible" |

### 7.4 eKYC Input Validation (`ValidationRequest.validateAndSanitize`)

- PAN: Not null/empty when type=PAN
- DL: Not null/empty + DOB required when type=DL
- Bank: Account number + IFSC required when type=BANK
- Input sanitization applied to all string fields

### 7.5 Phone Number Validation

- Regex: `^(\+?[0-9]*)$`
- Uniqueness check against existing users in DB
- Country code normalization (ensures `+91` prefix for India)

---

## 8. Error Handling

### 8.1 Exception Hierarchy

```
Exception
├── CustomException (400 Bad Request) — general business rule violations
├── ApplicationNotFoundException (400/404) — app not found by clientId
├── TokenException (401 Unauthorized) — invalid/expired JWT
├── LoginRedirectException (302 Found) — redirect to login with error
├── EKycVerificationException — Karza API failures
├── UserFaceNotLiveException — face liveness check failed
└── MethodArgumentNotValidException (400) — bean validation failures
```

### 8.2 Global Exception Handlers

| Handler | Exception | Response |
|---------|-----------|----------|
| `ApplicationExceptionHandler` | `CustomException` | 400 + `ErrorResponse(status, timestamp, message)` |
| `ApplicationExceptionHandler` | `LoginRedirectException` | 302 redirect to error URL |
| `ValidationHandler` | `MethodArgumentNotValidException` | 400 + `Map<fieldName, errorMessage>` |
| `JwtTokenFilter` | `CustomException` (auth) | 401 + plain text message |
| `AccessDeniedHandler` | Access denied | 403 + custom response |

### 8.3 Error Response Format

```json
{
  "status": "BAD_REQUEST",
  "timestamp": "Mon Jun 01 10:30:00 IST 2026",
  "message": "User not found with the given ID"
}
```

### 8.4 Validation Error Response Format

```json
{
  "firstName": "First name should not be empty.",
  "primaryPhoneNumber": "Field should contain only numeric and +"
}
```

### 8.5 Error Handling Patterns

| Pattern | Implementation |
|---------|---------------|
| Fail-fast | Throw `CustomException` immediately on business rule violation |
| Null-safe | Extensive use of `Objects.isNull()`, `Optional`, null checks before external calls |
| Retry | `@Retryable` with backoff on transient failures |
| Graceful degradation | MDP returns "NA" if dealer data unavailable |
| Logging | All exceptions logged with `@Slf4j` before throwing |

---

## 9. Key Algorithms & Business Rules

### 9.1 User Status State Machine

```
                    ┌──────────────┐
                    │   CREATED    │ (initial, pre-B2C)
                    └──────┬───────┘
                           │ (B2C registration complete)
                           ▼
                    ┌──────────────┐
         ┌─────────│PENDING_ACTIVE│◀─────────┐
         │         └──────┬───────┘          │
         │                │ (eKYC verified    │ (re-onboard)
         │                │  OR admin approve)│
         │                ▼                   │
         │         ┌──────────────┐           │
         │    ┌────│    ACTIVE    │────┐      │
         │    │    └──────────────┘    │      │
         │    │ (no login for          │      │
         │    │  MAX_UNUSED_DAYS)      │      │
         │    ▼                        │      │
         │  ┌──────────────┐           │      │
         │  │   PASSIVE    │           │      │
         │  └──────┬───────┘           │      │
         │         │ (exceeds          │      │
         │         │  MAX_PASSIVE_DAYS)│      │
         │         ▼                   ▼      │
         │  ┌──────────────────────────────┐  │
         └──│          INACTIVE            │──┘
            └──────────────────────────────┘
```

### 9.2 eKYC Name Match Algorithm

```
Input: userName (from DB), nameFromDocument (from Karza)
Threshold: configurable via ekyc.namematch-threshold

For PAN:
  - Karza returns profileMatch[].matchScore for "name" parameter
  - If matchScore >= threshold → VERIFIED

For DL:
  - Karza returns name in response
  - Call Karza Name Match API: name1=userName, name2=karzaName
  - If score >= threshold → VERIFIED

For Bank:
  - Karza returns flags.accountHolderName.score
  - If score >= threshold → VERIFIED

Post-verification:
  - Check if same document exists for another ACTIVE user
  - If yes → mark as CONFLICT (both users flagged)
```

### 9.3 Face Identification Confidence

```
1. Detect face → get faceId (Azure Face Detect API)
2. Identify face against large person group → candidates with confidence
3. Filter candidates where confidence >= FACE_CONFIDENCE_THRESHOLD (env var)
4. Lookup PersonGroupDetails by personId → get userId
5. Return matching users with confidence scores
```

### 9.4 Employee ID Generation

```
Format: {PREFIX}{SEQUENCE_NUMBER}
  - Dealer employees: {dealerCode}{5-digit sequence} (e.g., "ABC0000001")
  - TVSM users: "TVSM{phone}{sequence}"

Sequence: Auto-incremented per dealer via EmployeeId entity
Thread-safe: @Transactional ensures atomicity
```

### 9.5 Password Generation & Encryption

```
Generation: PasswordUtil.generatePassword()
  - Format: "{prefix}@{suffix}#66" or "{phone}@TVSM#{random}"

Encryption: EncryptUtil.encrypt()
  - Algorithm: AES/GCM/NoPadding
  - Key derivation: PBKDF2WithHmacSHA256
  - Stored encrypted, decrypted only when sending to B2C
```

### 9.6 B2C Login Policy Resolution

```
Input: Application, countryCode, authType

1. Find LoginPolicy matching countryCode
2. If not found → use default policy (isDefault=true)
3. If authType provided:
   - Split policy name by "_"
   - Insert authType value before last segment
   - Example: "B2C_1A_signup_signin_v2" + "FID" → "B2C_1A_signup_signin_FID_v2"
```

### 9.7 Scheduled User Lifecycle Rules

| Rule | Condition | Action |
|------|-----------|--------|
| Pending → Inactive | `PENDING_ACTIVE` for > `MAX_PENDING_DAYS` | Set status=INACTIVE, disable in B2C |
| Active → Passive | No login for > `MAX_UNUSED_DAYS` | Set status=PASSIVE |
| Passive → Inactive | `PASSIVE` for > `MAX_PASSIVE_DAYS` | Set status=INACTIVE, disable in B2C |
| Face Login Reminder | Passive user, 1st reminder day | Send SMS notification |
| Face Login Reminder | Passive user, 2nd reminder day | Send SMS notification |

### 9.8 Conflict Detection

```
After successful eKYC verification:
1. Search for existing user with same verified document:
   - PAN: findExistingUserByPAN(panNumber)
   - DL: findExistingUserByDL(dlNumber)
   - Bank: findExistingUserByBankAcc(accountNumber, ifscCode)
2. If found AND their eKYC for same type is verified:
   - Save ConflictedUsers record (existing vs new)
   - Add comment to new user explaining conflict
   - Flag user for manual review
```

---

## 10. Configuration Handling

### 10.1 Profile-Based Configuration

| Profile | File | Usage |
|---------|------|-------|
| (default) | `application.properties` | All env-variable placeholders |
| `local` | `application-local.properties` | Local dev with hardcoded values |
| Activated by | `spring.profiles.active=${ACTIVE_ENVIRONMENT}` | Set per environment |

### 10.2 Configuration Categories

#### Database Configuration
| Property | Source | Description |
|----------|--------|-------------|
| `spring.datasource.url` | `${DB_URI}` | MySQL connection URL |
| `spring.datasource.username` | `${DB_USERNAME}` | DB username |
| `spring.datasource.password` | `${DB_PASSWORD}` | DB password |
| `spring.datasource.hikari.maximum-pool-size` | Hardcoded: 50 | Max DB connections |
| `spring.datasource.hikari.minimum-idle` | Hardcoded: 10 | Min idle connections |

#### Azure B2C Configuration
| Property | Source | Description |
|----------|--------|-------------|
| `application.b2c.baseUri` | `${B2C_TENANT_NAME}` | B2C tenant login URL |
| `application.b2c.tenantId` | `${B2C_TENANT_ID}` | Azure AD tenant ID |
| `application.b2c.clientId` | `${UMS_CLIENT_ID}` | UMS app registration client ID |
| `application.b2c.clientSecret` | `${UMS_CLIENT_SECRET}` | UMS app registration secret |
| `application.b2c.issuer` | `${B2C_ISSUER}` | Token issuer domain |
| `application.b2c.graphApiScope` | Hardcoded | `https://graph.microsoft.com/.default` |

#### Azure Face API Configuration
| Property | Source | Description |
|----------|--------|-------------|
| `azure.faceApi.url` | `${AZURE_FACE_URL}` | Face API endpoint |
| `azure.faceApi.subscriptionKey` | `${AZURE_FACE_SUBSCRIPTION}` | Cognitive Services key |
| `face-confidence-threshold` | `${FACE_CONFIDENCE_THRESHOLD}` | Min confidence for face match |

#### eKYC Configuration
| Property | Source | Description |
|----------|--------|-------------|
| `karza.baseUrl` | `${KARZA_API_BASE_URL}` | Karza API base URL |
| `karza.key` | `${KARZA_API_KEY}` | Karza API key |
| `ekyc.namematch-threshold` | `${EKYC_NAME_MATCH_THRESHOLD}` | Min name match score (0-1) |
| `ekyc.consent-link` | `${EKYC_CONSENT_LINK}` | Consent page URL |
| `ekyc.consent-expiry` | `${EKYC_CONSENT_EXPIRY}` | Consent link TTL |

#### User Lifecycle Configuration
| Property | Source | Description |
|----------|--------|-------------|
| `application.user.max-pending-active-days` | `${MAX_PENDING_DAYS}` | Days before pending→inactive |
| `application.user.max-passive-days` | `${MAX_PASSIVE_DAYS}` | Days before passive→inactive |
| `application.user.max-unused-days` | `${MAX_UNUSED_DAYS}` | Days before active→passive |
| `application.user.max-face-login-days` | `${MAX_FACE_LOGIN_DAYS}` | Face login reminder threshold |

#### Cron Schedules
| Property | Value | Description |
|----------|-------|-------------|
| `passive-and-pending-active-to-inactive-cron` | `0 0 0 * * ?` | Midnight daily |
| `face-api-login-reminder-cron` | `0 0 18 * * ?` | 6 PM daily |

#### Service Bus Configuration
| Property | Source | Description |
|----------|--------|-------------|
| `azure.servicebus.namespace` | `${AZURE_SERVICE_BUS_NAMESPACE}` | Service Bus FQDN |
| `azure.servicebus.topic-name` | `${AZURE_SERVICE_BUS_TOPIC_NAME}` | Topic name |
| `azure.servicebus.client-id` | `${AZURE_CLIENT_ID}` | Managed Identity client ID |

### 10.3 Configuration Beans

| Config Class | Beans Created | Purpose |
|-------------|---------------|---------|
| `GraphServiceClientConfig` | `GraphServiceClient` | MS Graph SDK with client credentials |
| `AzureServiceBusConfig` | `ServiceBusSenderClient` | Service Bus sender with managed identity |
| `AzureBlobStorageConfig` | Blob client | Blob storage operations |
| `OkHttpClientConfig` | `OkHttpClient` | Shared HTTP client for external calls |
| `WebClientConfiguration` | `WebClient` | Reactive client for B2C token calls |
| `SecurityConfig` | `SecurityFilterChain` | URL authorization rules |
| `AsyncConfig` | Thread pool | Async task execution |
| `CacheConfig` | Cache manager | In-memory JWKS key cache |

### 10.4 Security Configuration Details

```java
SecurityFilterChain:
  - CORS: disabled
  - CSRF: disabled (stateless API)
  - Session: STATELESS
  - Open URLs: OPEN_URLS set → permitAll()
  - Onboard APIs: USER_ONBOARD_APIS → hasAnyAuthority(userOnboardAuthorities)
  - All other: authenticated()
  - Filter: JwtTokenFilter before UsernamePasswordAuthenticationFilter
  - Exception: custom AccessDeniedHandler
```

---

## Appendix: Key Constants Reference

| Constant | Value | Usage |
|----------|-------|-------|
| `SIGNIN_TYPE_USER_NAME` | `"userName"` | B2C identity sign-in type |
| `SIGNIN_TYPE_EMAIL` | `"emailAddress"` | B2C email identity |
| `KARZA_INTERNAL_STATUS_SUCCESS` | `101` | Karza success response code |
| `BEARER` | `"Bearer "` | Auth header prefix |
| `ALLOWED_FILE_TYPES_IMAGE` | `[image/jpeg, image/jpg, image/png]` | Upload validation |
| `ALLOWED_FILE_TYPES_DOCUMENT` | `[text/csv, application/json, ...]` | CSV upload validation |
| `MAX_EMAIL_LENGTH` | `320` | Email field max length |
| `EMPLOYEE_ID_FORMAT` | `"%s%05d"` | Employee ID pattern |

---

*This document is intended for engineering vendor onboarding. No secrets, credentials, or sensitive business logic are exposed.*

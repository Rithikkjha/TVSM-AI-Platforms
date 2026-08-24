# Low Level Design (LLD) — Location Master Service

**Service Name:** `tvsmbe-location` (location-master)  
**Version:** 1.0.0  
**Document Version:** 1.0  
**Last Updated:** 2026-05-29  
**Author:** Engineering Team  

---

## Table of Contents

1. [Overview & Scope](#1-overview--scope)
2. [Module Breakdown](#2-module-breakdown)
3. [Class & Service Responsibilities](#3-class--service-responsibilities)
4. [API Flow Details](#4-api-flow-details)
5. [Internal Component Interactions](#5-internal-component-interactions)
6. [Database Schema & Usage](#6-database-schema--usage)
7. [Request/Response Lifecycle](#7-requestresponse-lifecycle)
8. [Validation Logic](#8-validation-logic)
9. [Error Handling](#9-error-handling)
10. [Key Algorithms & Business Rules](#10-key-algorithms--business-rules)
11. [Configuration Handling](#11-configuration-handling)
12. [Security Implementation](#12-security-implementation)
13. [Caching Strategy](#13-caching-strategy)
14. [Retry & Resilience](#14-retry--resilience)

---

## 1. Overview & Scope

This LLD covers the implementation-level details of the Location Master Service.

**Technology Stack:**

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.13 |
| Database | MongoDB (Spring Data) | — |
| Object Storage | Azure Blob Storage SDK | 12.32.0 |
| HTTP Client | OkHttp3 | 4.12.0 |
| Build Tool | Apache Maven | 3.9.14 |
| Caching | Spring Cache (ConcurrentMapCache) | — |
| Retry | Spring Retry + AOP | — |
| Security | Spring Security 6 | — |
| Monitoring | Sentry (7.16.0), OpenTelemetry | — |
| API Docs | SpringDoc OpenAPI | 1.8.0 |
| File Parsing | Apache POI (5.5.0), OpenCSV (5.12.0) | — |
| Serialization | Gson (2.11.0), Jackson | — |

---

## 2. Module Breakdown

### 2.1 Package Structure

```
com.tvsmotor.location_master/
├── config/                  # Spring configuration beans
├── controller/              # REST API controllers (13 controllers)
├── entity/                  # MongoDB document entities
├── ENUM/                    # Application enumerations (16 enums)
├── exception/               # Global exception handling
├── model/
│   ├── request/             # Request DTOs with self-validation
│   ├── response/            # Response DTOs
│   ├── mongo_projections/   # MongoDB aggregation projections
│   └── mongo_repo_supporter/# Repository helper models
├── repository/              # Spring Data MongoDB repositories (19)
├── security/                # Security filters, RBAC utilities
├── service/                 # Business logic services (35+)
│   ├── external_api_caller/ # External API integration services
│   └── interfaces/          # Service interfaces
└── utils/                   # Utility classes, constants, helpers
```

### 2.2 Controller Layer (13 Controllers)

| Controller | Base Path | Auth | Purpose |
|-----------|-----------|------|---------|
| `AdminFlowController` | `/api/v1/admin-flow` | Admin (TM, HR Manager) | Dealer verification workflow, SMS dispatch, summary |
| `DealerFlowController` | `/api/v1/dealer-flow` | Dealer (Owner, Branch Mgr) | Dealer self-service, branch details |
| `MobileFlowController` | `/v1/dealer-location` | Open (secret key) | Mobile location + photo submission |
| `DealerProximityController` | `/api/v1/finder` | Open | Proximity-based dealer search |
| `DealershipLocationController` | `/api/v1/dealer-search` | Open | IB dealer search by criteria |
| `LocationMasterController` | `api/v1/location` | Open | State master data |
| `LocationController` | `/api/v1/location` | Open | Location hierarchy queries |
| `GeoCodeController` | `/api/v1/geo` | Open | Forward/reverse geocoding |
| `IBDealerController` | `/api/v1/dealer` | Admin | IB dealer CRUD, export |
| `CountryController` | `/api/v1/country` | Open | Country filter config, provinces |
| `MigrationController` | `/api/v1/admin/migrate` | Admin | CSV/XLSX data import |
| `UserXController` | `/api/v1/user-x` | Admin | Internal user management |
| `TestController` | `/api/v1/test` | Open | Health check, cache clear, diagnostics |

### 2.3 Service Layer (Key Services)

| Service | Responsibility |
|---------|---------------|
| `AdminFlowService` | Admin verification orchestration — summary, list, verify/reject, SMS, distance matrix |
| `MobileFlowOperationalService` | Mobile submission processing — secret key validation, photo upload, status transition |
| `DealerProximityService` | Proximity search via MDP API, photo URL generation |
| `DealershipLocationService` | IB dealer search with geospatial queries, XLSX import |
| `IBDealerManagementService` | IB dealer CRUD, summary, list with filters, Excel export |
| `DealerService` | Dealer data retrieval, branch details for dealer flow |
| `DealerInfoDetailsService` | Core CRUD for `dealer_data` collection, status queries |
| `MDPDealerService` | MDP API integration — dealer data, branches, proximity, filters |
| `NotificationSmsDispatcherService` | SMS dispatch via Notification Service |
| `GeocodingService` | Google Maps geocoding orchestration |
| `AzureBlobOperationService` | Photo upload, SAS URL generation, file download |
| `AzureB2CTokenManager` | OAuth2 token lifecycle with in-memory caching |
| `CoordinateDistanceCalculatorUtilService` | Distance calculation (Haversine, Vincenty, Equirectangular) |
| `LocationService` | Location hierarchy queries, CSV import, pincode details |
| `VerifiedDealerLocationsService` | Persist verified dealer locations |
| `SecretKeyManager` | Secret key generation, validation, lifecycle |
| `UserXService` | Internal user CRUD, owned entity management |
| `CountryService` | Country master data, filter config |
| `AuditLogService` | Audit trail persistence |
| `DealerLocationStatusManager` | State machine for dealer location status transitions |

---

## 3. Class & Service Responsibilities

### 3.1 Base Entity Pattern

All MongoDB entities extend `MongoBaseEntity`:

```java
public abstract class MongoBaseEntity {
    @Id
    private String id;           // MongoDB ObjectId (auto-generated)
    @CreatedDate
    private LocalDateTime createdAt;  // Auto-populated via MongoAuditing
    @LastModifiedDate
    private LocalDateTime updatedAt;  // Auto-populated via MongoAuditing
}
```

### 3.2 Request DTO Pattern (Self-Validating)

All request DTOs implement `ApiRequest<E>` which extends both `Sanitizeable<E>` and `Validateable<E>`:

```java
public interface ApiRequest<E> extends Sanitizeable<E>, Validateable<E> {}

// Usage in controller/service:
request.validate(request);
request.sanitizeIncomingData(request);
```

Each request DTO contains its own validation and sanitization logic, keeping business rules co-located with the data structure.

### 3.3 Response DTO Pattern

Standard response wrapper:

```java
public class GeneralResponse {
    private Object data;
    private String errorMessage;
    private String time;          // Auto-set to current timestamp
    private Long timeTakenInMs;
    private String serverId;      // Instance identifier
}
```

### 3.4 Authentication DTO

Custom `Authentication` implementation for Spring Security:

```java
public class AuthenticationDto implements Authentication {
    private String name;
    private String sapDealerCode;
    private boolean authenticated;
    private Collection<GrantedAuthority> authorities;
    private String primaryPhoneNumber;
    private String userId;
}
```

### 3.5 DealerLocationStatusManager (State Machine)

Static utility class managing dealer location status transitions. No DB operations — only in-memory state changes:

| Current Status | Action | New Status |
|---------------|--------|------------|
| `VERIFICATION_TO_BE_INITIATED` | SMS Sent | `VERIFICATION_INITIATED` |
| `VERIFICATION_INITIATED` | SMS Sent | `VERIFICATION_INITIATED` |
| `VERIFIED` | SMS Sent | `VERIFICATION_INITIATED` |
| `REJECTED` | SMS Sent | `RE_VERIFICATION_INITIATED` |
| `RE_VERIFICATION_INITIATED` | SMS Sent | `RE_VERIFICATION_INITIATED` |
| `VERIFICATION_INITIATED` | Location Submit | `VERIFICATION_PENDING` |
| `RE_VERIFICATION_INITIATED` | Location Submit | `RE_VERIFICATION_PENDING` |
| `VERIFICATION_PENDING` | Admin Verify | `VERIFIED` |
| `VERIFICATION_PENDING` | Admin Reject | `REJECTED` |
| `RE_VERIFICATION_PENDING` | Admin Verify | `VERIFIED` |
| `RE_VERIFICATION_PENDING` | Admin Reject | `REJECTED` |

---

## 4. API Flow Details

### 4.1 Admin Flow — Send Location Update SMS

```
POST /api/v1/admin-flow/send-location-update-sms

Request Body:
{
  "sapDealerCode": "11016",
  "phoneNumber": "+919876543210",
  "locationType": "SALES"
}

Flow:
1. Validate & sanitize request (phone max 13 chars, dealer code max 20)
2. Check user access (isUserAllowedAccessToOrElseThrow)
3. Validate dealer is active in MDP for given locationType
4. Find or generate DealerInfoDetails record
5. Generate unique 5-char secret key (UUID-based, max 1000 attempts)
6. Send SMS via Notification Service (with retry)
7. Save secret key to DB (delete old keys for same dealer+locationType)
8. Update status via DealerLocationStatusManager
9. Save DealerInfoDetails with SMS details
10. Audit log the operation
```

### 4.2 Mobile Flow — Submit Dealer Location

```
POST /v1/dealer-location/submit (multipart)

Parts:
- "data": MobileFlowSubmitDealerLocationData (JSON)
- "file": MultipartFile (photo)

Flow:
1. Validate & sanitize incoming data (secret key, coordinates, accuracy thresholds)
2. Resolve DealerSecretKey from secret key (with expiry check)
3. Validate dealer is active in MDP for resolved locationType
4. Find existing DealerInfoDetails by sapDealerCode + locationType
5. Update status via DealerLocationStatusManager.updateStatusForLocationSubmit()
6. Set submittedLocationDetails (lat, lng, address lines, accuracy)
7. Set imageCapturedLocationDetails (lat, lng, reverse geocoded address, accuracy, timestamp)
8. Upload photo to Azure Blob Storage (filename: SAPCODE_TIMESTAMP_DEALERSHIP_PHOTO.ext)
9. Save DealerInfoDetails
10. Delete used secret key
11. Audit log the submission
```

### 4.3 Admin Flow — Verify/Reject Dealer

```
POST /api/v1/admin-flow/verification

Request Body:
{
  "sapDealerCode": "11016",
  "status": "VERIFIED",        // or "REJECTED"
  "locationType": "SALES",
  "adminComments": "Location verified"  // Required for REJECTED
}

Flow:
1. Check user access (territory/dealer ownership validation)
2. Validate request (status must be VERIFIED or REJECTED)
3. Find DealerInfoDetails with valid status (VERIFICATION_PENDING or RE_VERIFICATION_PENDING)
4. Update status and admin comments
5. Save DealerInfoDetails
6. If VERIFIED → save to verified_dealer_locations collection
7. Audit log the verification
```

### 4.4 Proximity Search (India — via MDP)

```
POST /api/v1/finder/dealers

Request Body:
{
  "latitude": 12.9716,
  "longitude": 77.5946,
  "limit": 10,
  "filterType": "TWO_WHEELER_SALES"
}

Flow:
1. Validate coordinates (-90/90 lat, -180/180 lng), limit (1-20)
2. Extract MDP flags from DealerFilterType enum
3. Call MDP proximity API with lat/lng/flags/limit/dealerType
4. For each result: fetch MDP dealer data for metadata
5. Determine DealerLocationType from filter flags
6. Get formatted address from MDP location data
7. Generate pre-signed photo URL (if verified photo exists)
8. Get main contact from MDP contacts
9. Return enriched proximity response with distance
```

### 4.5 IB Dealer Search (International — via MongoDB GeoNear)

```
POST /api/v1/dealer-search

Request Body:
{
  "countryCode": "IT",
  "geoCode": { "latitude": 41.89, "longitude": 12.51, "radiusInKM": 50 },
  "dealerFilterType": "TWO_WHEELER_SALES",
  "pagination": { "page": 1, "size": 20 }
}

Flow:
1. Validate & sanitize (countryCode max 2 chars, coordinates, pagination)
2. Determine search strategy:
   a. If geoCode present → MongoDB $geoNear query with 2dsphere index
   b. If location (province/city) present → filter by province+city
   c. If only countryCode → paginated list by country
3. Convert results to DealerSearchResponse with distance (meters → km)
4. Return paginated response
```

---

## 5. Internal Component Interactions

### 5.1 Admin Verification Flow — Component Interaction

```
AdminFlowController
    │
    ▼
AdminFlowService
    ├──► UserXService (access control check)
    ├──► MDPDealerService (validate dealer active + locationType)
    ├──► DealerInfoDetailsService (find/save dealer data)
    ├──► SecretKeyManager → DealerSecretKeyService (generate/save/delete keys)
    ├──► NotificationSmsDispatcherService → AzureB2CTokenManager → OkHttpUtil
    ├──► AzureBlobOperationService (pre-signed URL generation)
    ├──► GeocodingService → GoogleMapsApiCallerService (address → lat/lng)
    ├──► CoordinateDistanceCalculatorUtilService (distance matrix)
    ├──► VerifiedDealerLocationsService (save verified locations)
    ├──► UMSService (dealer contacts)
    └──► AuditLogService (audit trail)
```

### 5.2 Token Management Flow

```
Any External API Call
    │
    ▼
AzureB2CTokenManager.getAzureB2CToken(ServiceType)
    │
    ├── Cache HIT + token valid? → Return cached token
    │
    └── Cache MISS or expired?
            │
            ▼
        AzureB2CTokenGenerationService.generateToken()
            │
            ▼
        POST to Azure AD B2C token endpoint
        (client_credentials grant)
            │
            ▼
        Cache token with calculated expiry
        (actual_expiry - 60 seconds buffer)
            │
            ▼
        Return token

On 401 Response from External API:
    → Remove token from cache
    → Throw RetryableException
    → Spring Retry re-invokes method (fetches new token)
```

### 5.3 Secret Key Lifecycle

```
Admin sends SMS
    │
    ▼
SecretKeyManager.generateSecretKey(sapDealerCode, locationType)
    │ (UUID-based, 5 chars, uniqueness check up to 1000 attempts)
    ▼
DealerSecretKeyService.save(secretKey, sapDealerCode, locationType)
    │ (deletes old keys for same dealer+locationType first)
    ▼
SMS sent to dealer with secret key
    │
    ▼
Dealer opens mobile app with secret key
    │
    ▼
SecretKeyManager.getDealerSecretDataFromSecretKeyOrElseThrow(secretKey)
    │ (validates key exists AND createdAt >= now - expiryDays)
    ▼
Dealer submits location data
    │
    ▼
SecretKeyManager.deleteSecret(secretKey)  // one-time use
```

---

## 6. Database Schema & Usage

### 6.1 Collection: `dealer_data`

| Field | Type | Index | Description |
|-------|------|-------|-------------|
| `_id` | ObjectId | Primary | Auto-generated |
| `sapDealerCode` | String | Indexed (non-unique) | SAP dealer identifier |
| `locationType` | Enum | — | SALES / SERVICE |
| `dealerLocationStatus` | Enum | — | 7 possible states |
| `photoUrl` | String | — | Azure Blob URL |
| `adminComments` | String | — | Admin verification comments |
| `submittedLocationDetails` | Embedded | — | lat, lng, addressLines, accuracy, googlePlaceId |
| `imageCapturedLocationDetails` | Embedded | — | lat, lng, reverseGeocodedAddress, accuracy, submittedAt |
| `locationUpdateSmsDetails` | Embedded | — | notificationId, phoneNumber, smsSentAt |
| `createdAt` | DateTime | — | Auto (MongoAuditing) |
| `updatedAt` | DateTime | — | Auto (MongoAuditing) |

**Key Queries:**
- `findBy(sapDealerCode, locationType)` — Primary lookup
- `findBySapDealerCodeAndValidStatuses(code, type, statuses)` — Verification flow
- `findAllSapDealerCodeAndLocationsMap()` — Aggregation for admin list
- `findAllSapDealerCodeAndLocationsMapBy(status)` — Status-filtered aggregation

### 6.2 Collection: `dealership_location`

| Field | Type | Index | Description |
|-------|------|-------|-------------|
| `_id` | ObjectId | Primary | Auto-generated |
| `dealerCode` | String | Indexed | Dealer identifier |
| `dealershipName` | String | — | Display name |
| `status` | Enum | — | ACTIVE / DELETED / PRE_ACTIVE / INACTIVE |
| `flags` | List\<DealerFilterType\> | — | TWO_WHEELER_SALES, ELECTRIC_IQUBE, etc. |
| `location.countryCode` | String | Indexed | ISO country code |
| `location.address` | String | — | Full address |
| `location.zipcode` | String | — | Postal code |
| `location.city` | String | — | City name |
| `location.province` | String | — | Province/state |
| `location.geocode` | GeoJsonPoint | **2dsphere** | Geospatial index for proximity queries |
| `contacts` | Embedded | — | Phone numbers, email addresses |

**Key Queries:**
- `findNearestDealers(lat, lng, radius, country, flags, limit)` — `$geoNear` aggregation
- `findByCountryCodeFlagsProvinceCityPagination(...)` — Filtered pagination
- `findDealersWithAllFilters(...)` — Full-text regex + filters + pagination
- `countDealersByStatus(countryCode)` — Summary aggregation
- `findProvincesAndCitiesByCountryForActiveDealers(country)` — Province/city dropdown

### 6.3 Collection: `verified_dealer_locations`

| Field | Type | Index | Description |
|-------|------|-------|-------------|
| `sapDealerCode` | String | **Unique** | One record per dealer |
| `verifiedLocationDetails` | List | — | Array of verified submissions |
| `verifiedLocationDetails[].locationType` | Enum | — | SALES / SERVICE |
| `verifiedLocationDetails[].verifiedAt` | DateTime | — | Verification timestamp |
| `verifiedLocationDetails[].submittedLocationDetails` | Embedded | — | Submitted coordinates |
| `verifiedLocationDetails[].photoUrl` | String | — | Photo blob URL |

### 6.4 Collection: `location_data`

| Field | Type | Index | Description |
|-------|------|-------|-------------|
| `pincode` | Integer | Indexed | 6-digit pincode |
| `stateName` | String | Indexed | State name (uppercase) |
| `country` | String | — | Country code |
| `division` | String | — | Division name |
| `district` | String | — | District name |
| `area` | String | — | Area/locality name |
| `latitude` | BigDecimal | — | Area centroid lat |
| `longitude` | BigDecimal | — | Area centroid lng |

**Compound Unique Index:** `{stateName, district, pincode, area}` — prevents duplicates

### 6.5 Collection: `dealer_secret_key`

| Field | Type | Description |
|-------|------|-------------|
| `sapDealerCode` | String | Dealer identifier |
| `locationType` | Enum | SALES / SERVICE |
| `secretKey` | String | 5-char unique key |
| `createdAt` | DateTime | Used for expiry calculation |

**Key Query:** `findBySecretKeyAndThreshold(key, threshold)` — validates key not expired

### 6.6 Other Collections

| Collection | Entity | Purpose |
|-----------|--------|---------|
| `country` | Country | Country config, filter options, proximity limits |
| `state_details` | StateDetails | State code ↔ state name mapping |
| `locale` | Locale | Language/locale master data |
| `user_x` | UserX | Internal user roles and owned entities |
| `audit_log` | AuditLog | API call audit trail |
| `rejection_comments` | RejectionComment | Configurable rejection reasons |
| `pincode_centroid_data` | PincodeCentroidEntity | Pincode centroid coordinates |

---

## 7. Request/Response Lifecycle

### 7.1 Incoming Request Pipeline

```
HTTP Request
    │
    ▼
Spring Security FilterChain
    │
    ├── shouldNotFilter? (OPEN_APIS pattern match)
    │       │
    │       YES → Skip filter → Controller
    │       │
    │       NO ↓
    │
    ▼
RequestFilter (OncePerRequestFilter)
    │
    ├── Extract "Authorization" header
    ├── Decode JWT payload (Base64, NO signature verification)
    │   (Token validation delegated to Azure APIM gateway)
    ├── Extract: name, sapDealerCode, primaryPhoneNumber, userId, baseRoles
    ├── Map baseRoles → List<SimpleGrantedAuthority>
    ├── Build AuthenticationDto
    └── Set SecurityContextHolder
    │
    ▼
Spring Security Authorization
    │
    ├── OPEN_APIS → permitAll()
    ├── ADMIN_APIS → hasAnyAuthority("Territory Manager", "HR Manager")
    ├── DEALER_APIS → hasAnyAuthority("Dealer Owner/Partner", "Branch Manager")
    └── anyRequest() → authenticated()
    │
    ▼
Controller → Service → Repository → Response
```

### 7.2 Response Structure

**Success Response (200):**
```json
{
  "data": { ... },
  "errorMessage": null,
  "time": "Thu May 29 10:30:00 IST 2026",
  "timeTakenInMs": null,
  "serverId": "abc123"
}
```

**Validation Error (400):**
```json
{
  "data": null,
  "errorMessage": "sapDealerCode is NULL",
  "time": "Thu May 29 10:30:00 IST 2026"
}
```

**Unauthorized (401):**
```json
{
  "errorMessage": "Authorization is NULL",
  "timeTakenInMs": 5,
  "serverId": "abc123"
}
```

**Forbidden (403):**
```json
{
  "errorMessage": "Access Denied"
}
```

**Internal Error (500):**
```json
{
  "data": {                          // Only if show.http_500_error_details=true
    "ex.getClass": "java.lang.NullPointerException",
    "ex.getMessage": "...",
    "ex.getStackTrace": [...]
  },
  "errorMessage": "Internal Error occurred"
}
```

---

## 8. Validation Logic

### 8.1 Validation Utility Methods (`GeneralUtils`)

| Method | Purpose |
|--------|---------|
| `notNullOrElseThrow(obj, name)` | Null check |
| `notNullAndNotEmptyOrElseThrow(str, name)` | Null + empty string check |
| `notNullAndNotEmptyAndMaxLengthCheckOrElseThrow(str, max, name)` | Null + empty + max length |
| `neitherNullNorEmptyThenMaxLengthCheckOrElseThrow(str, max, name)` | Optional field max length |
| `validateLatitudeOrElseThrow(lat, name)` | Range: -90 to 90 |
| `validateLongitudeOrElseThrow(lng, name)` | Range: -180 to 180 |
| `validatePositiveOrElseThrow(int, name)` | Must be > 0 |
| `validatePincodeOrElseThrow(pincode, name)` | 6-digit numeric, positive |
| `validateNoSpecialCharactersOrElseThrow(str, name)` | Only alphanumeric + spaces |
| `validateBothOrNoneOrElseThrow(a, aName, b, bName)` | Both present or both null |
| `validateFileType(file, expectedType, name)` | MIME type check |
| `notNullThenValidatePositiveAndLimitOrElseThrow(int, max, name)` | Optional positive with upper bound |

### 8.2 Request-Level Validation Examples

**DealerVerificationRequest:**
- `sapDealerCode`: not null, not empty, max 100 chars
- `status`: not null, must be VERIFIED or REJECTED
- `locationType`: not null
- `adminComments`: max 200 chars; **required** if status is REJECTED

**ProximitySearchRequest:**
- `latitude`: valid range (-90 to 90)
- `longitude`: valid range (-180 to 180)
- `limit`: not null, positive, max 20
- `filterType`: not null

**MobileFlowSubmitDealerLocationData:**
- `secretKey`: not null, not empty, max 10 chars
- `submittedLocationDetails.addressLine1-4`: not null, not empty, max 200 chars each
- `submittedLocationDetails.accuracy`: between 0 and configurable threshold
- `imageCapturedLocationDetails.accuracy`: between 0 and configurable threshold
- All lat/lng fields: valid coordinate ranges

**DealerSearchFilterRequest:**
- `countryCode`: not null, not empty, max 3 chars
- `search`: if present, min 3 chars, max 100 chars
- `pagination.page`: positive, max 10000
- `pagination.size`: positive, max 100

### 8.3 Sanitization Pattern

All incoming string data is:
1. **Trimmed** — leading/trailing whitespace removed
2. **Uppercased** — country codes, state names, district names
3. **Null-safe** — `trimNullable()` returns null for null/empty inputs
4. **Phone numbers** — hyphens, spaces, leading zeros removed via `removeLeadingZerosAndWhitespaceAndHyphens()`

---

## 9. Error Handling

### 9.1 Global Exception Handler (`RestExceptionHandler`)

```java
@ControllerAdvice
public class RestExceptionHandler {

    @ExceptionHandler(ValidationException.class)
    → HTTP 400 BAD_REQUEST + error message

    @ExceptionHandler(HttpMessageNotReadableException.class)
    → HTTP 400 + "Invalid value 'X' for field 'Y'. Allowed values: [...]"
    (Handles invalid enum values in request body)

    @ExceptionHandler(Exception.class)
    → HTTP 500 INTERNAL_SERVER_ERROR
    → Conditionally includes stack trace (controlled by show.http_500_error_details env var)
}
```

### 9.2 Security Exception Handling

| Exception | Handler | HTTP Status | Response |
|-----------|---------|-------------|----------|
| Missing/invalid JWT | `RequestFilter` | 401 | `{ errorMessage: "Authorization is NULL" }` |
| Insufficient role | `AccessDeniedHandler` | 403 | `{ errorMessage: "Access Denied" }` |

### 9.3 Custom Exception Classes

| Exception | Usage | Behavior |
|-----------|-------|----------|
| `ValidationException` | Business rule violations, invalid input | Returns 400 with message |
| `RetryableException` | External API failures (401, 5xx) | Triggers Spring Retry |

### 9.4 External API Error Handling Pattern

```java
// Common pattern in MDPDealerService, NotificationSmsDispatcherService, UMSService:

if (response.isSuccessful()) {
    return deserialize(response.body());
} else if (response.code() == 401) {
    // Token expired — evict from cache, throw RetryableException
    azureB2CTokenManager.removeAzureB2CTokenFromCache(serviceType);
    throw new RetryableException("Unauthorized");
} else if (response.code() >= 500) {
    // Server error — throw RetryableException for retry
    throw new RetryableException("API failed");
} else {
    // Client error (4xx) — log, audit, throw ValidationException (no retry)
    auditLogService.saveLog(API_FAILED, details);
    throw new ValidationException("Failed to get response");
}
```

---

## 10. Key Algorithms & Business Rules

### 10.1 Distance Calculation Algorithms

The service supports three geodesic distance formulas via `CoordinateDistanceCalculatorUtilService`:

**Haversine Formula** (default for distance matrix):
- Uses Earth radius = 6371 km
- Suitable for most use cases
- O(1) computation

**Vincenty's Formula** (most accurate):
- Uses WGS-84 ellipsoid parameters (semi-major: 6378137m, semi-minor: 6356752.314245m)
- Iterative calculation with error tolerance 1e-12
- Best for long distances

**Equirectangular Distance Approximation** (fastest):
- Simple trigonometric approximation
- Best for short distances where speed matters

### 10.2 Secret Key Generation Algorithm

```
Input: sapDealerCode, dealerLocationType
1. source = sapDealerCode + "_" + locationType + "_" + LocalDateTime.now()
2. uuid = UUID.nameUUIDFromBytes(source.getBytes(UTF_8))
3. secretKey = uuid.replaceAll("-", "").substring(0, 5)
4. Check uniqueness in DB (up to 1000 attempts)
5. If collision → regenerate (timestamp changes ensure different UUID)
6. Retry annotation: @Retryable(maxAttempts = 3) on outer method
```

### 10.3 Token Expiry Calculation

```
calculateExpiryEpoch(expiresInInSec):
    return currentEpochInSec + expiresInInSec - 60 (buffer)

isTokenValid(validTillEpochInSec):
    return validTillEpochInSec > currentEpochInSec
```

Buffer of 60 seconds ensures token is refreshed before actual expiry.

### 10.4 Admin List Pagination Algorithm

The admin dealer list combines data from MDP (external) and local DB:

```
Step 1.1: Get active dealer codes from MDP (filtered by user's territory/dealers)
Step 1.2: Apply beta release filter (if enabled, intersect with beta dealer codes)
Step 1.3: Cross-reference with MDP locationType flags → build [sapDealerCode + locationType] pairs
Step 2:   Filter by status:
          - VERIFICATION_TO_BE_INITIATED → dealers NOT in local DB
          - Other statuses → dealers in local DB with matching status
Step 3:   Apply pagination (page, size) on filtered list
Step 4:   Fetch MDP bulk data for paginated dealer codes
Step 5:   Build response with MDP metadata + local DB status
```

### 10.5 IB Dealer XLSX Import Logic

```
1. Parse XLSX file → List<DealershipLocation>
2. Validate & sanitize each record
3. Build unique key: dealerCode|countryCode|province|city|address
4. Fetch existing records from DB for same countryCode
5. For each existing record:
   a. If matching key in import → UPDATE existing record
   b. If no matching key → mark as DELETED
6. Remaining import records (no match in DB) → INSERT
7. Return counts: { inserted, updated, deleted }
```

### 10.6 Dealer Authorization (DealerValidatorUtil)

```
1. Get logged-in user's AuthenticationDto from SecurityContext
2. Check if user has "Dealer Owner/Partner" authority:
   a. If accessing own dealer data (sapDealerCode matches) → AUTHORIZED
   b. If accessing branch data → verify branch's parentAmdSapDealerCode matches user's dealer
3. Check if user has "Branch Manager" authority:
   a. Only authorized for own sapDealerCode
4. If not authorized → audit log + throw ValidationException
```

### 10.7 Admin User Access Control (UserX-based)

```
1. Get UserX record by userId from JWT
2. If role == ADMIN → full access
3. If role == TERRITORY_MANAGER:
   a. Extract owned territories from UserX.owningMatrix
   b. If territories empty → check owned dealers list
   c. Validate dealer's territory (from MDP) is in user's territories
   d. Validate locationType is in user's owned DEALER_LOCATION_TYPE
4. If neither → throw "Invalid user role"
```

---

## 11. Configuration Handling

### 11.1 Configuration Strategy

- **Externalized via environment variables** — all sensitive and environment-specific values
- **Spring Profiles** — `spring.profiles.active=${ACTIVE_ENVIRONMENT}` (local, dev, uat, prod)
- **No hardcoded secrets** — all credentials injected at runtime

### 11.2 Key Configuration Properties

| Property | Env Variable | Purpose |
|----------|-------------|---------|
| `spring.data.mongodb.uri` | `MONGODB_URI` | MongoDB connection string |
| `azureBlob.connection-string` | `LOCATION_MASTER_AZUREBLOB_CONNECTION_STRING` | Blob storage auth |
| `azureBlob.presigned-url.expiry-hours` | `AZUREBLOB_SAS_PRESIGNED_URL_EXPIRY_HOURS` | SAS URL TTL |
| `azureBlob.publicDomain` | `AZUREBLOB_PUBLIC_DOMAIN` | CDN/public domain for photos |
| `mdp.base.url` | `MDP_BASE_URL` | MDP service base URL |
| `notification.base.url` | `NOTIFICATION_BASE_URL` | Notification service URL |
| `b2c.notification.token.url` | `NOTIFICATION_TOKEN_URL` | B2C token endpoint |
| `b2c.notification.client.id` | `NOTIFICATION_CLIENT_ID` | OAuth2 client ID |
| `b2c.notification.client.secret` | `NOTIFICATION_CLIENT_SECRET` | OAuth2 client secret |
| `b2c.notification.scope` | `NOTIFICATION_SCOPE` | OAuth2 scope |
| `b2c.notification.apim-subscription-key` | `NOTIFICATION_APIM_SUBSCRIPTION_KEY` | APIM key |
| `ums.base.url` | `UMS_BASE_URL` | UMS service URL |
| `google-maps.geocode.api-key` | `GOOGLE_MAPS_GEOCODE_API_KEY` | Google Maps API key |
| `location-update-secret-expiry-days` | `LOCATION_UPDATE_SECRET_EXPIRY_DAYS` | Secret key TTL |
| `show.http_500_error_details` | `SHOW_HTTP_500_DETAILS` | Toggle stack trace in 500 |
| `beta-release-enabled` | `BETA_RELEASE_ENABLED` | Feature flag for beta |
| `beta-release-sapDealerCodes` | `BETA_RELEASE_SAP_DEALER_CODES` | Beta dealer whitelist |
| `submitted.location.accuracy.threshold.in.meters` | `SUBMITTED_LOCATION_ACCURACY_THRESHOLD_IN_METERS` | GPS accuracy limit |
| `image.captured.location.accuracy.threshold.in.meters` | `IMAGE_CAPTURED_LOCATION_ACCURACY_THRESHOLD_IN_METERS` | Photo GPS accuracy limit |

### 11.3 Configuration Beans

| Config Class | Bean(s) Created | Purpose |
|-------------|----------------|---------|
| `OkHttpClientConfig` | `OkHttpClient` (singleton) | HTTP client with 30s read timeout |
| `AzureBlobConfig` | `BlobContainerClient` | Azure Blob container access |
| `CacheConfig` | `CacheManager` (SimpleCacheManager) | In-memory caches from CacheType enum |
| `TransactionManagerConfig` | `MongoTransactionManager` | MongoDB transaction support |
| `SecurityConfig` | `SecurityFilterChain` | Security rules, filter chain |

### 11.4 Server Configuration

```properties
server.port=8080
server.servlet.context-path=/location-master
spring.servlet.multipart.max-file-size=100MB
spring.servlet.multipart.max-request-size=200MB
```

### 11.5 Docker/JVM Configuration

```dockerfile
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/usr/local/lib/location-master.jar"]
ENV TZ=Asia/Kolkata
EXPOSE 8080
```

---

## 12. Security Implementation

### 12.1 Authentication Flow

1. **APIM Gateway** validates JWT signature and expiry (upstream)
2. **RequestFilter** extracts JWT payload (no re-validation)
3. JWT payload decoded via Base64 (no signature check — trusted from APIM)
4. Roles extracted from `baseRoles` array in JWT → mapped to Spring Security authorities

### 12.2 Role-Based Access Control

| API Category | Required Authorities |
|-------------|---------------------|
| Open APIs | None (permitAll) |
| Admin APIs | `Territory Manager` OR `HR Manager` |
| Dealer APIs | `Dealer Owner/Partner` OR `Branch Manager` |

**Open API Patterns:**
- `/v1/dealer-location/**` (mobile flow)
- `/api/v1/dealer-flow/dealerInfo` (secret key based)
- `/api/v1/test/**`
- `/api/v1/dealership-locations/**`
- `/api/v1/finder/**`
- `/api/v1/location/**`
- `/api/v1/country/**`
- `/api/v1/dealer-search`

### 12.3 Additional Authorization Layers

Beyond Spring Security role checks, the service implements:

1. **DealerValidatorUtil** — Ensures dealers can only access their own data or their branches
2. **UserX-based access control** — Territory Managers restricted to their assigned territories/dealers/locationTypes
3. **Secret Key validation** — Mobile flow uses time-limited secret keys instead of JWT

### 12.4 Security Configuration Details

```java
// SecurityConfig.java
http
    .csrf(csrf -> csrf.disable())           // Stateless API, no CSRF needed
    .sessionManagement(STATELESS)           // No server-side sessions
    .addFilterBefore(requestFilter, UsernamePasswordAuthenticationFilter.class)
    .exceptionHandling(accessDeniedHandler)
```

---

## 13. Caching Strategy

### 13.1 Cache Types (CacheType Enum)

| Cache Name | Purpose | TTL |
|-----------|---------|-----|
| `AZURE_B2C_TOKEN` | OAuth2 tokens for MDP, UMS, Notification | Token expiry - 60s buffer |
| `COUNTRY_PROVINCES` | Province/city data per country | 7200 seconds (2 hours) |

### 13.2 Implementation

- **Technology:** Spring Cache with `SimpleCacheManager` + `ConcurrentMapCache`
- **Eviction:** Manual eviction on 401 responses (tokens), TTL-based for province data
- **Cache clear endpoint:** `DELETE /api/v1/test/cache/{cacheName}/{key}`

### 13.3 Token Cache Flow

```
getAzureB2CToken(ServiceType):
    1. Check cache for ServiceType key
    2. If present AND isTokenValid(expiryEpoch) → return cached token
    3. Else → generate new token, calculate expiry, cache it, return
```

---

## 14. Retry & Resilience

### 14.1 Spring Retry Configuration

All external API calls use `@Retryable`:

| Service | Max Attempts | Retry On |
|---------|-------------|----------|
| `MDPDealerService` | 3 | `RetryableException` |
| `NotificationSmsDispatcherService` | 3 | `RetryableException` |
| `UMSService` | 3 | `RetryableException` |
| `SecretKeyManager.generateSecretKey()` | 3 | `ValidationException` |

### 14.2 Retry Trigger Conditions

- HTTP 401 from external service → evict token cache → retry with new token
- HTTP 5xx from MDP → retry
- Secret key collision → retry generation

### 14.3 OkHttp Client Configuration

```java
new OkHttpClient.Builder()
    .readTimeout(30, TimeUnit.SECONDS)
    .build();
```

Single shared instance (thread-safe singleton) for all external API calls.

### 14.4 Transaction Management

- MongoDB transactions enabled via `MongoTransactionManager`
- `@Transactional` used on:
  - `submitDealerDetails()` — ensures atomic photo upload + DB save
  - `sendLocationUpdateSms()` — ensures atomic SMS + status update
  - `updateIBDealer()` — ensures atomic dealer update
  - `saveAllWithValidateAndSanitize()` — batch location import

---

## Appendix A: Enum Reference

| Enum | Values |
|------|--------|
| `DealerLocationStatus` | VERIFICATION_TO_BE_INITIATED, VERIFICATION_INITIATED, VERIFICATION_PENDING, VERIFIED, REJECTED, RE_VERIFICATION_INITIATED, RE_VERIFICATION_PENDING |
| `DealerLocationType` | SALES, SERVICE, PARTS |
| `DealerFilterType` | TWO_WHEELER_SALES, TWO_WHEELER_SERVICE, TWO_WHEELER_APS, THREE_WHEELER_SALES, SUPER_PREMIUM_APACHE_RR310, SUPER_PREMIUM_APACHE_RTR310, SUPER_PREMIUM_TVS_RONIN, ELECTRIC_IQUBE, ELECTRIC_TVSX |
| `DealershipStatus` | ACTIVE, DELETED, PRE_ACTIVE, INACTIVE |
| `DealerType` | AMD, APS, BRANCH, AD |
| `UserRole` | ADMIN, DEALER, TERRITORY_MANAGER |
| `ServiceType` | MDP, NOTIFICATION, UMS |
| `CacheType` | AZURE_B2C_TOKEN, COUNTRY_PROVINCES |
| `CoordinateDistanceCalculatorFormula` | HAVERSINE, VINCENTY, EQUIRECTANGULAR_DISTANCE_APPROXIMATION, SIMPLE_MATHS |
| `ContactType` | (used for phone/email type classification) |
| `AuditLogType` | MDP_API_FAILED, NOTIFICATION_API_FAILED, DEALER_SUBMITS_LOCATION_DATA, DEALER_LOCATION_VERIFICATION_API, UNAUTHORIZED_ACCESS_TO_DEALER_DATA, COORDINATE_DISTANCE_CALCULATION, UNEXPECTED_EXCEPTION_OCCURRED, MDP_GET_DEALER_DATA_API |

---

## Appendix B: External API Contracts

### B.1 MDP APIs

| Endpoint | Method | Auth | Request | Response |
|----------|--------|------|---------|----------|
| `/v1/dealer/{code}` | GET | B2C Token | — | `MDPResponse<MDPDealerData>` |
| `/v1/dealers/data?fetchMdpActiveDealersOnly=true` | POST | B2C Token | `List<String>` (dealer codes) | `MDPResponse<List<MDPDealerData>>` |
| `/v1/dealers/listOfSapDealerCode/basedOnFilters` | POST | B2C Token | `MdpDealerFilterApiRequest` | `MDPResponse<List<String>>` |
| `/v1/dealer/{code}/branches` | GET | B2C Token | — | `MDPResponse<MDPBranchesData>` |
| `/v1/dealers/listOfDealerDetails/basedOnProximity` | POST | B2C Token | `MdpProximityRequest` | `MDPResponse<List<MdpProximityApiResponse>>` |

### B.2 Notification Service APIs

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/notification/sms` | POST | B2C Token + APIM Key | Send SMS |
| `/api/v1/notification/{id}` | GET | B2C Token + APIM Key | Check SMS status |

### B.3 UMS APIs

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/dealer/get-contacts?dealerId={id}` | GET | B2C Token | Get dealer contacts |
| `/auth/v1/app/token/validate` | POST | B2C Token | Validate JWT token |

### B.4 Google Maps Geocoding API

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/maps/api/geocode/json?address={addr}&key={key}` | GET | API Key | Forward geocoding |
| `/maps/api/geocode/json?latlng={lat,lng}&key={key}` | GET | API Key | Reverse geocoding |

---

*End of Document*

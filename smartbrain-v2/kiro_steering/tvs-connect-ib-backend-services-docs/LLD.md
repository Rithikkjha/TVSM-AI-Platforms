# Low Level Design (LLD) — TVS Connect Web API

## 1. Document Overview

| Field | Details |
|-------|---------|
| Project | TVS Connect Web API |
| Version | 1.0 |
| Last Updated | June 2026 |
| Audience | Engineering vendors, new developers |

---

## 2. Detailed Module Breakdown

### 2.1 TVS.ApiService.Api (API Layer)

| Component | Files/Folders | Responsibility |
|-----------|---------------|----------------|
| Controllers | `Controllers/` (75+ subdirectories) | HTTP endpoint handlers |
| Auth Filters | `JWTAuthenticationFilter.cs`, `RefreshTokenValidationFilter.cs` | Token validation |
| Custom Handlers | `CustomHandler/` | Rate limiting, logging, ride data formatting |
| Custom Attributes | `CustomFilterAttributes/` | Action filters, localization |
| OAuth Provider | `Providers/` | Token generation, credential validation |
| Azure AD Auth | `AzureADAuthentication/` | Azure AD token validation |
| DI Configuration | `App_Start/UnityConfig.cs` | Unity IoC container setup |
| Route Configuration | `App_Start/WebApiConfig.cs` | API routing and middleware pipeline |
| Models | `Models/` | API-specific request/response models |
| Response Wrapper | `Responsecls.cs`, `ApiResponse.cs` | Standardized API response format |

### 2.2 TVS.ApiService.Service (Business Layer)

| Module | Key Services | Responsibility |
|--------|-------------|----------------|
| Ride | `RideService` | Ride data processing, stats calculation |
| User | `UserProfileService`, `ICEUserService` | User management, profile ops |
| Vehicle | `VehicleService`, `UserVehicleService` | Vehicle CRUD, type management |
| Notification | `NotificationService`, `HibNotificationService` | Push, SMS, in-app notifications |
| Telemetry | `P360Service`, `CodpService`, `TrakNTellService` | Connected vehicle data |
| Maps | `HereMapService`, `MMIDownloadService` | Route images, geocoding |
| Weather | `WeatherP360Service`, `AQIP360Service` | Weather and air quality |
| DMS | `DmsService`, `CSIFeedbackService` | Dealer management integration |
| Caching | `SmartCacheService` | In-memory cache management |
| External | `ExternalApiService`, `ThirdPartyAPIConfigurationService` | Third-party API calls |
| Encryption | `EncryptionDecryption/` | AES-256 encryption for GDPR |
| Storage | `StorageUploadService` | Azure Blob operations |

### 2.3 TVS.ApiService.Repository (Data Layer)

Each repository follows the pattern:
```
Repository/{Module}/
├── I{Module}Repository.cs    (Interface)
└── {Module}Repository.cs     (Implementation)
```

Key repositories: `RideRepository`, `UserVehicleRepository`, `UserProfileRepository`, `NotificationRepository`, `MasterDataRepository`, `VehicleRepository`, `TourRepository`, `ModeRepository`, `GearRepository`, `LapRepository`

### 2.4 TVS.ApiService.DAL (Entity Framework)

| Component | Purpose |
|-----------|---------|
| `TVSModel.edmx` | Primary EF6 model (Database-First) |
| `TVSDAModel.edmx` | Secondary EF model (Data Access specific) |
| `TVSModel.Context.cs` | DbContext for LINQ queries |
| `*.cs` (150+ entity files) | POCO entity classes auto-generated from EDMX |

### 2.5 TVS.ApiService.Common (Shared Utilities)

| Component | Purpose |
|-----------|---------|
| `Constant/` | Application-wide constants |
| `Enum/` | Enumerations (Vehicle types, statuses) |
| `Security/` | Encryption/decryption utilities |
| `Logging/` | log4net wrapper |
| `Notification/` | Notification helpers |
| `InternationalSMS/` | International SMS formatting |
| `Utility/` | General utility methods |
| `Resources/` | Localized resource strings |

### 2.6 TVS.SMSService

```
TVS.SMSService/
├── Services/
│   └── SMSNotificationService.cs       # Main service interface
├── SMSProviderFactory/
│   └── SMSProviderFactory.cs           # Factory pattern for providers
└── SMSProviders/
    ├── TataCommunicationProvider.cs    # Tata Comm SMS implementation
    ├── AirtelProvider.cs               # Airtel SMS implementation
    └── PlivoProvider.cs                # Plivo SMS implementation
```

---

## 3. Class/Service Responsibilities

### 3.1 Controller Layer Pattern

```csharp
[RoutePrefix("api/{version}/{module}")]
public class {Module}Controller : ApiController
{
    private readonly I{Module}Service _service;
    
    // Constructor injection via Unity
    public {Module}Controller(I{Module}Service service)
    {
        _service = service;
    }
    
    [HttpPost]
    [Route("{action}")]
    public async Task<HttpResponseMessage> Action(RequestModel model)
    {
        // Validation → Service call → Response wrapping
    }
}
```

### 3.2 Service Layer Pattern

```csharp
public interface I{Module}Service
{
    Task<ResultModel> OperationAsync(InputModel input);
}

public class {Module}Service : I{Module}Service
{
    private readonly I{Module}Repository _repository;
    private readonly ICacheService _cacheService;
    
    public async Task<ResultModel> OperationAsync(InputModel input)
    {
        // Business logic
        // Cache check
        // Repository call
        // Transform and return
    }
}
```

### 3.3 Repository Layer Pattern

```csharp
public interface I{Module}Repository
{
    Task<Entity> GetByIdAsync(long id);
    Task<bool> InsertOrUpdateAsync(Entity entity);
}

public class {Module}Repository : I{Module}Repository
{
    // Uses EF6 DbContext or ADO.NET SqlParameter collections
    public async Task<Entity> GetByIdAsync(long id)
    {
        using (var context = new TVSModel())
        {
            return await context.Entities.FindAsync(id);
        }
    }
}
```

### 3.4 Key Service Class Details

#### RideService
- Processes ride telemetry data from connected vehicles
- Vehicle-type-specific calculation strategies (`IOtherRideCalculations`)
  - `U408RideCalculations` — NTorq/N360 scooters
  - `U399CRideCalculations` — Apache RTR motorcycles
  - `U467RideCalculations` — iQube EV scooters
  - `U347UGRideCalculations` — Jupiter series
  - `U368RideCalculations` — Raider series
  - `U449RideCalculations` — Other ICE variants
- Reads CSV telemetry files from Azure Blob Storage
- Calculates: distance, speed, eco score, fuel efficiency, riding patterns

#### SmartCacheService
- In-memory caching with configurable TTL
- Cache key composition using country code + language + entity identifiers
- Thread-safe lazy initialization pattern
- Factory delegate pattern for cache population

#### NotificationService
- Manages Azure Notification Hub registrations
- Supports iOS (APNS) and Android (FCM) push notifications
- Tag-based notification routing
- MQTT notification fallback

#### P360Service / TrakNTellService
- Factory pattern (`P360AndTntFactory`) to select provider based on vehicle type
- mTLS client certificate authentication for TrakNTell
- Configurable timeout (5 seconds for TNT)
- Max concurrent request throttling

---

## 4. API Flow Details

### 4.1 Request Processing Pipeline

```
HTTP Request
    │
    ▼
┌────────────────────────┐
│ IIS / OWIN Host        │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ RateLimitingHandler    │  ← DelegatingHandler (checks request rate)
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ LogActionFilterAttribute│  ← MessageHandler (logs request/response)
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ CORS Middleware        │  ← EnableCors attribute
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ OAuth Bearer Auth      │  ← HostAuthenticationFilter
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ LocalizationAttribute  │  ← Sets language/country from headers
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ UserDeviceLogFilter    │  ← Logs device info
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ Controller Action      │  ← Business logic execution
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│ GlobalExceptionHandler │  ← Catches unhandled exceptions
└───────────┬────────────┘
            ▼
HTTP Response (Responsecls wrapper)
```

### 4.2 Standard Response Format

```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "",
    "Data": { /* payload */ }
}
```

### 4.3 Authentication Flow (Detailed)

1. **Login Request**: `POST /api/UserLogin/Login` with mobile/email/social credentials
2. **OTP Generation**: Random N-digit code stored in DB via stored procedure
3. **OTP Delivery**: 
   - Domestic (India): SMS via Tata/Airtel
   - International: Email (SendGrid) + SMS (Plivo/Tata International)
4. **OTP Verification**: `POST /api/UserLogin/VerifyLoginOtp`
5. **Token Issuance**: OAuth Bearer token via OWIN `/token` endpoint
6. **Subsequent Calls**: `Authorization: Bearer <token>` header

---

## 5. Database Schema Usage

### 5.1 Core Entity Relationships

```
UserProfile (1) ──────── (N) UserVehicle
     │                          │
     │                          │ (1)
     │                          ▼
     │                    VehicleDetail ──── VehicleType
     │                          │
     │                          │ (N)
     │                          ▼
     │                    Ride / TravelTransection
     │                          │
     │                          │ (1)
     │                          ▼
     │                    RideCumulative
     │
     ├──── (N) UserDevice
     ├──── (N) UserConsent
     ├──── (N) EmergencyContact
     ├──── (N) UserBadge
     ├──── (N) UserSetting
     └──── (N) FavouriteNavigationLocation
```

### 5.2 Key Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `UserProfile` | User master data (GDPR encrypted) | UserId, MobileNumber, Email, FullName |
| `UserVehicle` | User-vehicle mapping | UserId, VehicleId, FrameNumber, IsActive |
| `VehicleDetail` | Vehicle master catalog | VehicleId, VehicleTypeId, ModelName |
| `VehicleType` | Vehicle type configuration | VehicleTypeId, TypeName, Series |
| `Ride` | Individual ride records | RideId, UserId, VehicleId, StartTime, EndTime |
| `RideCumulative` | Aggregated ride statistics | UserId, TotalDistance, TotalRides |
| `TravelTransection` | Raw telemetry data (per vehicle type) | Multiple tables per vehicle series |
| `MobileNotification` | Push notification queue | NotificationId, UserId, Message |
| `AppVersion` | Mobile app version control | Platform, Version, ForceUpdate |
| `MasterData` | Configuration key-values | Key, Value, CountryCode |
| `CountryMaster` | Country configuration | CountryId, CountryCode, Settings |

### 5.3 Vehicle-Specific Tables

Each vehicle type has dedicated telemetry tables:
- `U399CTravelTransection` / `U399CTravelTransection_Archived` (Apache)
- `N251BLETravelTransection` / `N251BLETravelTransection_Archived` (NTorq BLE)
- `U347TravelTransection` (iQube)
- `ApacheTravelTransection` / `ApacheNONIOTTravelTransection`
- `N109TravelTransection` (Jupiter)

### 5.4 Data Access Patterns

**Entity Framework (LINQ):**
```csharp
using (var context = new TVSModel())
{
    var vehicle = await context.UserVehicles
        .Where(v => v.UserId == userId && v.IsActive)
        .FirstOrDefaultAsync();
}
```

**Stored Procedures (ADO.NET):**
```csharp
var parameters = new Collection<SqlParameter>
{
    new SqlParameter("@UserId", userId),
    new SqlParameter("@ReturnCode", 0) { Direction = ParameterDirection.InputOutput }
};
var result = UserProfileDa.InsertUpdateUserProfile("ProcedureName", parameters);
```

---

## 6. Request/Response Lifecycle

### 6.1 Typical API Request Flow

```
1. Client sends HTTP request with:
   - Authorization: Bearer <token>
   - Headers: languagecode, countrycode, devicetype
   - Body: JSON payload

2. Pipeline Processing:
   a. Rate limiter checks request frequency
   b. Log handler records request metadata
   c. OAuth filter validates bearer token
   d. Localization attribute sets GlobalSetting (language, country)
   e. Controller receives validated request

3. Controller Processing:
   a. Input validation (null checks, format validation)
   b. GDPR encryption of PII fields
   c. Service method invocation
   d. Response wrapping in Responsecls

4. Service Processing:
   a. Cache lookup (if applicable)
   b. Business logic execution
   c. Repository/DA layer call
   d. External API calls (if needed)
   e. Result transformation

5. Response:
   - HTTP 200 with Responsecls JSON body
   - StatusCode field indicates actual result status
   - All errors returned as HTTP 200 with appropriate StatusCode
```

### 6.2 Error Response Pattern

```json
{
    "StatusCode": 417,
    "Message": "Failure",
    "Description": "Exception occurred. Please try again.",
    "Data": null
}
```

---

## 7. Validation Logic

### 7.1 Controller-Level Validation

```csharp
// Null/empty field checks
if (string.IsNullOrWhiteSpace(request.MobileNumber) &&
    string.IsNullOrWhiteSpace(request.Email))
{
    return Responsecls(HttpStatusCode.BadRequest, "Failure", "Empty fields found");
}
```

### 7.2 Common Validation Patterns
- Mobile number format validation (per country)
- OTP attempt limiting (configurable max attempts + timeout)
- Frame number/VIN validation against master data
- Token expiry and refresh token validation
- IMEI restriction checking (blocked device list)
- Country-code based feature gating
- App version force-update checks

### 7.3 OTP Validation Rules
- Maximum failed attempts: configurable (default: 5)
- Lockout duration: configurable (default: 1 hour)
- OTP length: configurable per request
- Static OTP bypass for test numbers (non-production)

---

## 8. Error Handling

### 8.1 Global Exception Handler

```csharp
public class GlobalExceptionHandler : ExceptionHandler
{
    // Catches all unhandled exceptions
    // Logs to database via LogExceptionDa
    // Returns standardized error response
    // Does not expose stack traces in production
}

public class GlobalExceptionLogger : ExceptionLogger
{
    // Logs exception details to Application Insights + log4net
}
```

### 8.2 Error Handling Strategy

| Level | Mechanism | Action |
|-------|-----------|--------|
| Controller | try-catch per action | Log + return structured error |
| Service | Exception propagation | Let exceptions bubble up |
| Repository | Handled at data access | Log + throw specific exceptions |
| Global | GlobalExceptionHandler | Catch-all, log, sanitized response |
| External API | Per-call try-catch | Log + graceful degradation |

### 8.3 Logging

```csharp
// Database logging
LogExceptionDa.InsertLogException(
    ex.Message, ex.StackTrace, 
    className, methodName, 
    customMessage, userId, additionalInfo
);

// log4net
Logger.Error(ex);

// Application Insights (automatic via SDK)
```

---

## 9. Key Algorithms/Business Rules

### 9.1 Ride Calculation Strategy Pattern

```csharp
// Vehicle-type-specific ride calculations
public interface IOtherRideCalculations
{
    RideResult CalculateRideStats(RideData data);
}

// Resolved at runtime via Unity DI with named registrations
container.RegisterType<IOtherRideCalculations, U408RideCalculations>(VEHICLETYPE_ID_N360);
container.RegisterType<IOtherRideCalculations, U467RideCalculations>(VEHICLETYPE_ID_U467);
```

### 9.2 SMS Provider Failover

```
1. Try Primary Provider (TataCommunication)
2. If fails N times (configurable: FailedAttemptForProviderSwitch)
3. Switch to Secondary Provider (Airtel)
4. Periodically test primary (PrimaryProviderTestFrequency)
5. Auto-switch back when primary recovers
```

### 9.3 GDPR Data Encryption

```csharp
// PII fields encrypted before storage
public class ProfileGdprData
{
    public string Email { get; set; }
    public string MobileNumber { get; set; }
    public string FullName { get; set; }
    
    public Dictionary<string, string> EncryptedProfileData { get; }  // AES-256
    public Dictionary<string, string> DecryptedProfileData { get; }
}
```

### 9.4 SAS Token Generation
- Per-vehicle-type Event Hub SAS tokens
- Configurable expiry (default: ~6 months)
- Resource URI, key name, and key per vehicle series

### 9.5 Cache Strategy

```csharp
var cachedData = await _cacheService.GetOrAddAsync<T>(
    key: $"{prefix}_{GlobalSetting.GetCountryCode()}",
    cacheType: CacheType.Memory,
    factory: async () => { /* DB query */ },
    successValidator: result => result != null
);
```

### 9.6 Vehicle Type Resolution
- Vehicle type ID determines: telemetry table, calculation strategy, CSV container, SAS token config
- Named Unity registrations map vehicle type constants to specific implementations
- Supports 20+ vehicle variants (NTorq, Apache RTR, iQube, Jupiter, Raider, etc.)

---

## 10. Configuration Handling

### 10.1 Configuration Sources

| Source | Purpose | Example |
|--------|---------|---------|
| `Web.config` (appSettings) | Application settings | API URLs, feature flags |
| `Web.{env}.config` | Environment transforms | Per-environment overrides |
| Connection Strings | Database connections | SQL Server, CosmosDB |
| Azure Key Vault | Secrets | API keys, certificates |
| `Country_Specific_Configuration_Files/` | Country configs | Per-region XML overrides |
| Database (`MasterData` table) | Dynamic settings | Runtime-changeable config |

### 10.2 Environment Configurations

| Config File | Environment |
|-------------|-------------|
| `Web.Debug.config` | Local development |
| `Web.Dev.config` | Development |
| `Web.Staging.config` | Staging/UAT |
| `Web.Prod.config` | Production |
| `Web.Release.config` | Generic release |

### 10.3 Global Settings Pattern

```csharp
public static class GlobalSetting
{
    // Thread-local settings populated by LocalizationAttribute
    public static string GetCountryCode();
    public static string GetLanguageCode();
    public static int CountryId;
    public static string GetMobileCountryCode();
    public static string GetIsSMSEnabled();
}
```

### 10.4 Country-Specific Configuration

```
Country_Specific_Configuration_Files/
├── Africa/
│   ├── Production/     # Production XML configs
│   └── Staging/        # Staging XML configs
├── Bangladesh/
├── Egypt/
├── Europe/
├── Latam/
├── MiddleEast/
├── Nepal/
├── SEA/
└── Sri-Lanka/
```

### 10.5 Key Configuration Categories

| Category | Key Examples | Purpose |
|----------|-------------|---------|
| SMS | PrimarySMSProvider, FailedAttemptForProviderSwitch | SMS delivery config |
| Maps | heremap_api_key, mmi-macid-activation-url | Map service config |
| Storage | AzureHostName, mmicontainer | Blob storage config |
| Vehicle | tov-part-*, EVSeries | Vehicle identification |
| Features | enable-third-party-API, swagger-enable | Feature flags |
| Auth | accessTokenLifeTimeInMinutes, TokenExpireTimeSpan | Token config |
| Notification | NotificationURL, NotificationAppName | Push notification config |

---

## 11. Dependency Injection Details

### 11.1 Unity Container Setup

All services registered in `UnityConfig.RegisterTypes()`:

```csharp
// Standard pattern
container.RegisterType<IService, ServiceImpl>();
container.RegisterType<IRepository, RepositoryImpl>();

// Named registrations (vehicle-type strategy)
container.RegisterType<IOtherRideCalculations, U408RideCalculations>("vehicleTypeId");

// Singleton services
container.RegisterType<ICacheService, SmartCacheService>(new SingletonLifetimeManager());

// Factory registrations
container.RegisterFactory<HttpClient>("TntHttpClient", c => { /* mTLS client */ });
```

### 11.2 Lifetime Management
- **Transient** (default): New instance per resolution (controllers, services)
- **Singleton** (`SingletonLifetimeManager`): Cache service, HTTP clients
- **Container Controlled** (`ContainerControlledLifetimeManager`): Certificate providers

---

## 12. Key Design Patterns Used

| Pattern | Usage |
|---------|-------|
| Repository | Data access abstraction |
| Strategy | Vehicle-type ride calculations |
| Factory | SMS provider selection, TNT/P360 selection |
| Dependency Injection | Unity IoC throughout |
| Decorator | Message handlers (rate limiting, logging) |
| Template Method | Base controller patterns |
| Observer | Notification dispatch |
| Singleton | Cache service, HTTP clients |

---

*This document is intended for new engineering vendors to understand implementation details. Secrets, credentials, and connection strings have been excluded.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner (iOS)** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |
| **Owner (Android)** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
| **DevOps** | Raju Nimse | raju.nimse@tvsmotor.com |
| **Contact Person (Backend)** | Raju Nimse | raju.nimse@tvsmotor.com |

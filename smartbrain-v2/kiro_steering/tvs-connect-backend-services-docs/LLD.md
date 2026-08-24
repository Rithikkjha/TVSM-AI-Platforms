# Low Level Design (LLD) — TVS Connect Web API

| Attribute       | Value                                    |
|-----------------|------------------------------------------|
| Service Name    | TVS Connect Web API                      |
| Framework       | .NET Framework 4.8 / ASP.NET Web API 2   |
| ORM             | Entity Framework 6 (Database-First)      |
| DI Container    | Unity 5.x                                |
| Last Updated    | June 2026                                |

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


## 1. Detailed Module Breakdown

### TVS.ApiService.Api (Presentation Layer)

```
TVS.ApiService.Api/
├── App_Start/
│   ├── UnityConfig.cs          # 100+ DI registrations (all services, repos, DALs)
│   ├── WebApiConfig.cs         # Route table, formatters, message handlers
│   ├── SwaggerConfig.cs        # Swagger/Swashbuckle configuration
│   ├── FilterConfig.cs         # Global filter registration
│   ├── Startup.Auth.cs         # OWIN auth middleware
│   └── UnityActionFilterProvider.cs  # DI for action filters
├── Controllers/                # 79 controllers in feature folders
│   ├── Registration/           # RegisterUserController (OTP, user creation)
│   ├── Vehicle/                # VehicleController, VehicleControllerV3
│   ├── Ride/                   # RideController (CRUD + CSV upload)
│   ├── Home/                   # HomeController (dashboard telemetry)
│   ├── Notification/           # NotificationController
│   ├── Geofence/               # GeofenceController (CRUD + alerts)
│   ├── Cricket/Football/AQI/   # Third-party content controllers
│   ├── CSIFeedback/NPSFeedback/# Survey controllers
│   ├── Admin/                  # AdminController
│   └── HealthCheck/            # HealthCheckController
├── CustomFilterAttributes/     # Custom validation + exception filters
├── CustomHandler/              # AiHandleErrorAttribute (App Insights)
├── JWTAuthenticationFilter.cs  # Primary auth filter (per-request)
├── RefreshTokenValidationFilter.cs  # Refresh token auth
├── UserDeviceLogFilter.cs      # Device activity logging
├── Startup.cs                  # OWIN pipeline entry
└── Web.config                  # All configuration (conn strings, keys, flags)
```

### TVS.ApiService.Service (Business Logic Layer)

```
TVS.ApiService.Service/
├── Home/HomeService.cs                    # Dashboard: latest device data, cumulative
├── Ride/RideService.cs                    # Ride save, CSV upload, stats calculation
├── Vehicle/VehicleService.cs              # Onboarding, DMS lookup, P360 register
├── P360/P360Service.cs                    # P360 telematics API wrapper
├── ExternalApi/ExternalApiService.cs      # Generic HTTP client (circuit breaker)
├── MMIDownload/MMIDownloadService.cs      # MapMyIndia route image generation
├── Geofence/GeofenceService.cs            # Geofence CRUD + alert logic
├── CSIFeedback/CSIFeedbackService.cs      # Customer satisfaction surveys
├── NPSFeedback/NPSFeedbackService.cs     # NPS surveys
├── InAppFeedback/InAppFeedbackService.cs  # In-app feedback
├── Referral/ReferralService.cs            # Referral program
├── Widget/WidgetService.cs                # Home screen widgets
├── P360TntProviderFactory/                # Factory pattern: P360 vs TnT provider
├── EncryptionDecryptionService.cs         # RSA encryption (public key exchange)
├── CodpService.cs                         # Connected Data Provider integration
├── DmsService.cs                          # DMS API wrapper
├── CricketP360Service.cs                  # Cricket via P360
├── FootballP360Service.cs                 # Football via P360
├── EVUserService.cs                       # EV-specific user operations
├── ICEUserService.cs                      # ICE-specific user operations
└── BaseRideCalculations.cs                # Ride math (distance, speed, duration)
```

### TVS.ApiService.Repository (Data Access Abstraction)

```
TVS.ApiService.Repository/
├── HomeRepository.cs / IHomeRepository.cs
├── RideRepository.cs / IRideRepository.cs
├── VehicleRepository.cs / IVehicleRepository.cs
├── NotificationRepository.cs / INotificationRepository.cs
├── ManageProfileRepository.cs / IManageProfileRepository.cs
├── FeedBackRepository.cs / IFeedBackRepository.cs
├── GeofenceRepository.cs / IGeofenceRepository.cs
├── CSIFeedbackRepository.cs / ICSIFeedbackRepository.cs
├── EVUserRepository.cs / IEVUserRepository.cs
├── ICEUserRepository.cs / IICEUserRepository.cs
├── ClientSecretRepository.cs / IClientSecretRepository.cs
└── ... (103 files total, interface + implementation pairs)
```

### TVS.ApiService.DAL / TVS.ApiService.EV.DAL

```
TVS.ApiService.DAL/
├── TVSModel.edmx              # EF6 EDMX: ICE entities (Users, Vehicles, Rides, etc.)
├── TVSModel.Context.tt        # T4-generated DbContext
├── TVSDAModel.edmx            # Secondary EDMX: Stored procedure mappings
└── Entities/                  # Auto-generated entity classes

TVS.ApiService.EV.DAL/
├── EVModel.edmx               # EF6 EDMX: EV entities (EV Users, Telemetry, MQTT)
└── Entities/                  # Auto-generated EV entity classes
```


---

## 2. Class/Service Responsibilities

### Service Layer (Interface → Implementation Pattern)

| Interface | Implementation | Responsibility |
|-----------|---------------|----------------|
| `IHomeService` | `HomeService` | Get latest device data from P360, ride cumulative stats |
| `IRideService` | `RideService` | Save ride (CSV to Blob), calculate cumulative, generate route image |
| `IVehicleService` | `VehicleService` | Vehicle onboarding, DMS lookup, mark active vehicle |
| `IP360Service` | `P360Service` | All P360 telematics API calls (auth token, ride stats, device data) |
| `IExternalApiService` | `ExternalApiService` | Generic HTTP GET/POST with resilience wrapping |
| `IMMIDownloadService` | `MMIDownloadService` | MapMyIndia static map URL generation and download |
| `IGeofenceService` | `GeofenceService` | Geofence CRUD, vehicle-to-geofence mapping, alerts |
| `IDmsService` | `DmsService` | DMS Digi API calls (vehicle lookup, service history) |
| `ICodpService` | `CodpService` | Connected Data Provider API (add/remove user, sync) |
| `ISMSService` | `SMSServiceFactory` | Factory: selects Airtel or Tata based on queue/failover |
| `ICacheService` | `CacheService` | In-memory cache wrapper (MemoryCache) |
| `IEncryptionDecryptionService` | `EncryptionDecryptionService` | RSA encrypt/decrypt for secure key exchange |
| `ICSIFeedbackService` | `CSIFeedbackService` | CSI survey fetch + submission to DMS |
| `INPSFeedbackService` | `NPSFeedbackService` | NPS survey management |
| `IReferralService` | `ReferralService` | Referral code generation and validation |
| `IEVUserService` | `EVUserService` | EV database user CRUD |
| `IICEUserService` | `ICEUserService` | ICE database user CRUD |
| `IP360AndTntFactory` | `P360AndTntFactory` | Factory: selects P360 or TrakNTell provider by vehicle type |

### Repository Layer Pattern

Each repository follows:
```csharp
public interface IHomeRepository
{
    DataTable GetLatestDeviceData(long userId, long userVehicleId);
    DataTable GetRideCumulative(long userId, long userVehicleId);
}

public class HomeRepository : IHomeRepository
{
    private readonly TVSModelEntities _context;
    
    public HomeRepository(TVSModelEntities context)
    {
        _context = context;
    }
    
    public DataTable GetLatestDeviceData(long userId, long userVehicleId)
    {
        // Calls stored procedure via SqlHelper/ADO.NET
        return SqlHelper.ExecuteDataset(connectionString, "SP_GetLatestDeviceData", params).Tables[0];
    }
}
```

### Filter/Attribute Responsibilities

| Class | Type | Responsibility |
|-------|------|----------------|
| `JwtAuthenticationFilter` | AuthorizationFilter | Validates JWT + DB token on every protected request |
| `JwtAuthenticationAttribute` | AuthorizationFilter | Attribute-based JWT (alternate usage) |
| `JWTDeleteProfileAuthenticationFilter` | AuthorizationFilter | Special auth for delete profile flow |
| `RefreshTokenValidationFilter` | AuthorizationFilter | Validates refresh token for token renewal |
| `UserDeviceLogFilter` | ActionFilter | Logs device details (OS, version, model) per request |
| `ValidateModelAttribute` | ActionFilter | ModelState validation for profile updates |
| `ArgumentExceptionFilterAttribute` | ExceptionFilter | Catches ArgumentException → 400 response |
| `ItemNotFoundExceptionFilter` | ExceptionFilter | Catches not-found → 404 response |
| `MultiPartRequstValidatorAttribute` | ActionFilter | Validates multipart/form-data requests |
| `LogActionFilterAttribute` | ActionFilter | Request/response logging for debugging |
| `AiHandleErrorAttribute` | ExceptionFilter | Sends unhandled exceptions to Application Insights |


---

## 3. API Flow Details

### Login Flow (V3) — Detailed Sequence

```
UserLoginControllerV3.LoginV3(LoginDto)
│
├── 1. Validate input (MobileNumber not empty)
├── 2. Check rate limit (IP + endpoint key)
├── 3. Lookup user in ICE DB: ICEUserService.GetUserByMobile()
├── 4. Lookup user in EV DB: EVUserService.GetUserByMobile()
├── 5. Generate 6-digit OTP (Random or fixed for test numbers)
├── 6. Store OTP in DB with expiry timestamp
├── 7. Send OTP via SMS:
│       SMSServiceFactory.SendSMS()
│       ├── Try AirtelDigimateProvider.Send()
│       └── Failover: TataCommunicationProvider.Send()
├── 8. (Optional) Send via WhatsApp if requested
└── 9. Return { ICEUserId, EVUserId, IsNewUser }
```

### Ride Save Flow — Detailed Sequence

```
RideController.Post(multipart/form-data)
│
├── 1. UserVehicleAuthorization filter validates ownership
├── 2. Parse multipart: RideDetails JSON + CSV file
├── 3. RideService.AddRide():
│       ├── a. Upload CSV to Azure Blob Storage
│       ├── b. Parse ride metadata (distance, speed, time)
│       ├── c. Insert ride record to DB (RideRepository)
│       ├── d. Calculate cumulative stats:
│       │       BaseRideCalculations.CalculateCumulative()
│       │       Update RideCumulative table
│       ├── e. Generate route image:
│       │       MMIDownloadService.GetRouteImage(lat/long points)
│       │       Upload image to Blob Storage
│       └── f. Return ride summary with Blob download URLs
└── 4. Return 200 + RideResponse DTO
```

### Vehicle Onboarding Flow

```
VehicleControllerV3.AddVehicle(AddVehicleDto)
│
├── 1. JWT auth validated
├── 2. Check if vehicle already onboarded (FrameNumber + UserId)
├── 3. Determine vehicle type (ICE/EV/3W) from SERIES/PART_ID
├── 4. Create UserVehicle mapping in DB
├── 5. If connected vehicle:
│       ├── CodpService.AddUser() — register with P360
│       └── Store TrakNTell/P360 registration ID
├── 6. Register for push notifications (vehicle-specific topics)
└── 7. Return VehicleDetail response
```

---

## 4. Internal Component Interactions

### Controller → Service → Repository → DAL

```
┌─────────────────────────────────────────────────────────────────────┐
│ Controller (HomeController)                                          │
│   - Receives HTTP request                                            │
│   - Extracts userid from header                                      │
│   - Calls service method                                             │
│   - Wraps result in Responsecls/ResponceDto                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ (Unity DI injection)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Service (HomeService)                                                │
│   - Business logic and orchestration                                 │
│   - Calls repository for DB data                                     │
│   - Calls external APIs (P360, DMS) via ProviderService              │
│   - Maps entities to DTOs (Mapster)                                  │
└──────────┬───────────────────────────────┬──────────────────────────┘
           │                               │
           ▼                               ▼
┌──────────────────────┐    ┌──────────────────────────────────────────┐
│ Repository           │    │ ProviderService / ExternalApiService      │
│ (HomeRepository)     │    │   - HTTP calls with circuit breaker       │
│   - EF6 DbContext    │    │   - Retry policy (Polly)                  │
│   - Stored Procedures│    │   - Per-host timeout config               │
│   - SqlHelper (ADO)  │    │   - JSON deserialization                  │
└──────────┬───────────┘    └──────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│ DAL (TVSModel)       │
│   - EF6 EDMX context │
│   - Entity classes    │
│   - Connection String │
│   - Azure SQL DB      │
└──────────────────────┘
```

### SMS Service Factory Pattern

```
ISMSService (interface)
    │
    ├── SMSServiceFactory (selects provider based on PersistentService.ProviderQueue)
    │       │
    │       ├── AirtelDigimateProvider (primary)
    │       │       └── POST to Airtel Digimate BULK_API
    │       │
    │       └── TataCommunicationProvider (failover)
    │               └── POST to Tata campaignService API
    │
    └── Failover Logic:
            - If primary fails → increment ProviderQueue counter
            - If counter > threshold → switch to secondary
            - Auto-reset after cooldown period
```

### P360/TnT Factory Pattern

```
IP360AndTntFactory
    │
    ├── Determines provider by VehicleType/Series:
    │       - NTorq, Jupiter 125, Raider → P360 Provider
    │       - Older connected models → TrakNTell Provider
    │
    ├── P360 Provider:
    │       - Auth: JWT Bearer (generated per-request from clientId/secret)
    │       - Endpoints: /gapi/device/data, /gapi/trip/list
    │
    └── TrakNTell Provider:
            - Auth: API Key
            - Endpoints: /tnt/vehicle/status
```


---

## 5. Database Schema Usage

### Entity Framework Models

| EF Context | Database | Key Entities |
|------------|----------|--------------|
| `TVSModelEntities` | ICE DB | UserProfile, UserVehicle, VehicleType, Ride, RideCumulative, PushNotification, UserDevice, UserConsent, Geofence |
| `TVSDAModelEntities` | ICE DB (SPs) | Stored procedure mappings for token validation, user lookup, reporting |
| `EVModelEntities` | EV DB | EVUser, EVVehicle, EVTelemetry, EVNotification |

### Key Stored Procedures

| Stored Procedure | Called By | Purpose |
|------------------|-----------|---------|
| `ValidateAccessToken` | JwtAuthenticationFilter | Verify token is active in DB (every request) |
| `ValidateToken` | JwtAuthenticationFilter (legacy) | Legacy token validation |
| `SP_GetLatestDeviceData` | HomeRepository | Latest vehicle telemetry snapshot |
| `SP_GetRideCumulative` | HomeRepository | Cumulative ride statistics |
| `SP_GetUserByMobile` | ICEUserRepository | User lookup by mobile number |
| `SP_GenerateOTP` | RegisterUserRepository | OTP generation and storage |
| `SP_ValidateOTP` | RegisterUserRepository | OTP verification with lockout |
| `SP_GetVehicleList` | VehicleRepository | User's registered vehicles |
| `SP_SaveNotification` | NotificationRepository | Persist notification to queue |
| `SP_GetPendingNotifications` | WebJob | Fetch undelivered notifications |

### Data Access Patterns

**Pattern 1: Entity Framework (LINQ)**
```csharp
// Used for simple CRUD operations
var vehicle = _context.UserVehicles
    .Where(v => v.UserId == userId && v.IsActive == true)
    .FirstOrDefault();
```

**Pattern 2: SqlHelper + Stored Procedures**
```csharp
// Used for complex queries and reporting
DataTable dt = SqlHelper.ExecuteDataset(
    _connectionString,
    "SP_GetLatestDeviceData",
    new SqlParameter("@UserId", userId),
    new SqlParameter("@UserVehicleId", userVehicleId)
).Tables[0];
```

**Pattern 3: Raw ADO.NET (CommonDA)**
```csharp
// Used in background jobs (Console apps)
DataSet ds = CommonDA.GetDataSet(connectionString, CommandType.StoredProcedure, spName, parameters);
```

---

## 6. Request/Response Lifecycle

### Full Request Pipeline

```
1. HTTP Request arrives at IIS (Azure App Service)
       │
2. OWIN Middleware Pipeline (Startup.cs)
       │
3. ASP.NET Web API Routing (WebApiConfig.cs)
       │   Route: "api/{controller}/{action}/{id}"
       │
4. Message Handlers (if configured)
       │
5. Authorization Filters:
       │   ├── RateLimitFilter (IP check, login endpoints only)
       │   ├── JwtAuthenticationFilter:
       │   │       ├── Extract headers: accesstoken, userid
       │   │       ├── Validate JWT (HMAC-SHA256, check expiry)
       │   │       ├── Match NameIdentifier claim ↔ userid header
       │   │       ├── DB call: ValidateAccessToken SP
       │   │       └── Set Thread.CurrentPrincipal
       │   └── UserVehicleAuthorization (ride endpoints)
       │
6. Action Filters:
       │   ├── ValidateModelAttribute (ModelState check)
       │   ├── UserDeviceLogFilter (log device info)
       │   └── LogActionFilterAttribute (request logging)
       │
7. Model Binding (JSON → DTO deserialization)
       │
8. Controller Action Execution
       │   ├── Call Service Layer
       │   ├── Build Response (Responsecls / ResponceDto)
       │   └── Return IHttpActionResult
       │
9. Result Execution (JSON serialization)
       │
10. Exception Filters (if error):
       │   ├── ArgumentExceptionFilterAttribute → 400
       │   ├── ItemNotFoundExceptionFilter → 404
       │   └── AiHandleErrorAttribute → App Insights + 500
       │
11. HTTP Response sent to client
```

### Response Envelope Classes

```csharp
// Legacy response (most endpoints)
public class Responsecls
{
    public int StatusCode { get; set; }      // 200, 400, 401, 404, 417, 500
    public string Result { get; set; }       // "success" or "failure"
    public string Message { get; set; }      // Human-readable message
    public object Data { get; set; }         // Payload (any object)
    public List<ErrorMessage> ErrorMessages { get; set; }
}

// Newer response (v2/v3 endpoints)
public class ResponceDto
{
    public int statusCode { get; set; }
    public string result { get; set; }
    public string message { get; set; }
    public object data { get; set; }
    public List<string> errorMessages { get; set; }
}
```


---

## 7. Validation Logic

### Authentication Validation (JwtAuthenticationFilter)

```
Step 1: Header presence check
    - "accesstoken" header required
    - "userid" header required
    - Missing → 401 (Code 1: "Missing UserId or Token")

Step 2: JWT signature validation
    - Algorithm: HMAC-SHA256
    - Key: ConfigurationManager.AppSettings["CommunicationKey"]
    - Validates: signature, expiry (exp claim)
    - Fail → 401 (Code 4: "Invalid access token")

Step 3: Claim-to-header consistency
    - Token's NameIdentifier claim must equal header "userid"
    - Mismatch → 401 (Code 4)

Step 4: Query string/body UserId consistency
    - If UserId in querystring → must match header userid
    - If UserId in JSON body → must match header userid
    - Mismatch → 401 (Code 2 or 3)

Step 5: Database validation
    - SP: ValidateAccessToken(userId, accessToken)
    - Confirms token is active and not revoked
    - Fail → 401 (Code 5: "Access token does not match")
```

### Input Validation

| Validation | Location | Rule |
|------------|----------|------|
| Mobile number | Registration | 10 digits, numeric only |
| OTP | Login verification | Exactly 6 digits |
| Email | Profile update | Standard email regex |
| Platform | Multiple endpoints | Must be IOS/ANDROID/WEB (PlatformEnum) |
| LatLong | Geofence | Custom attribute: both Lat and Long non-null |
| Profile image | Upload | Max 5 MB file size |
| Vehicle frame | AddVehicle | 17-character alphanumeric |
| Ride TravelIds | Bulk delete | No duplicates in array |

### OTP Lockout Logic

```
On OTP verification failure:
    1. Increment failedAttemptCount for userId
    2. If failedAttemptCount >= MaxAttempts (5):
        - Set lockout timestamp = now + 60 minutes
        - Return: "Too many failed attempts. Try again after 1 hour."
    3. On successful OTP verification:
        - Reset failedAttemptCount to 0
        - Clear lockout timestamp
```

---

## 8. Error Handling

### Exception Handling Strategy

```
Layer 1: Controller-level try/catch
    └── Catches specific exceptions → maps to Responsecls with StatusCode 400/417

Layer 2: Custom Exception Filters
    ├── ArgumentExceptionFilterAttribute → 400 Bad Request
    ├── ItemNotFoundExceptionFilter → 404 Not Found
    └── AiHandleErrorAttribute → logs to App Insights, returns 500

Layer 3: Global Exception Handler (if configured)
    └── Catches unhandled → 500 Internal Server Error

Layer 4: OWIN error middleware
    └── Final safety net for pipeline errors
```

### Error Response Patterns

```csharp
// Pattern 1: Validation failure (returned as 200 with inner StatusCode)
return Ok(new Responsecls {
    StatusCode = 400,
    Result = "failure",
    Message = "Empty Fields Found.",
    Data = null
});

// Pattern 2: Exception caught
catch (Exception ex)
{
    Logger.Error("Error in method", ex);
    return Ok(new Responsecls {
        StatusCode = 417,
        Result = "failure",
        Message = "Exception Occured",
        Data = null
    });
}

// Pattern 3: Not found
return Ok(new Responsecls {
    StatusCode = 404,
    Result = "failure",
    Message = "Record Not Found",
    Data = null
});
```

### Logging (log4net)

```
Appenders:
    - FileAppender (rolling, daily rotation)
    - MongoDB Appender (structured logs)
    - Application Insights (via AiHandleErrorAttribute)

Log Levels Used:
    - ERROR: Exception details with stack trace
    - INFO: API call start/end, external API responses
    - DEBUG: Detailed data (request bodies, config values)
```

---

## 9. Key Algorithms & Business Rules

### JWT Token Generation

```csharp
Algorithm: HMAC-SHA256
Key: AppSettings["CommunicationKey"] (symmetric)
Claims:
    - ClaimTypes.Name = MobileNumber
    - ClaimTypes.NameIdentifier = UserId (string)
Lifetime:
    - AccessToken: AppSettings["accessTokenLifeTimeInMinutes"]
    - RefreshToken: AppSettings["refreshTokenLifeTimeInMinutes"]
Output: Base64-encoded JWT (header.payload.signature)
```

### Ride Cumulative Calculation

```
On each ride save:
    1. Fetch existing RideCumulative for (UserId, UserVehicleId)
    2. Update:
        - TotalDistance += newRide.TotalTravelledDistance
        - TotalDuration += newRide.TotalTime
        - TotalRideCount += 1
        - TopSpeed = MAX(existing.TopSpeed, newRide.TopSpeed)
        - AvgSpeed = TotalDistance / TotalDuration
        - FuelSaved = calculated based on vehicle type efficiency
    3. Save updated cumulative record
```

### SMS Provider Failover

```
ProviderQueue (static counter):
    - value = 0 → use Airtel (primary)
    - value > threshold → use Tata (secondary)

On send failure:
    1. Increment ProviderQueue
    2. Log failure with provider name
    3. Retry with alternate provider
    4. If both fail → log critical, return failure to caller

Auto-reset: ProviderQueue resets to 0 after cooldown period
```

### SAS Token Generation (Event Hub)

```
For each vehicle type (NTorq, Jupiter, Raider, etc.):
    1. Lookup Event Hub config by vehicle series
    2. Generate SAS token:
        - Resource URI: Event Hub namespace + entity path
        - Expiry: current time + configured lifetime
        - Signature: HMAC-SHA256(resource + expiry, SharedAccessKey)
    3. Return token to mobile app for direct Event Hub publish
```

### Rate Limiting Algorithm

```
Key: SHA256(ClientIP + EndpointPath)
Storage: MemoryCache (in-process)
Window: Fixed (configurable, default 1800s)

On request:
    1. Generate cache key from IP + path
    2. Get current counter from cache
    3. If counter >= MaxRequests (5):
        - Check block list in DB
        - Save block record if not exists
        - Return 429 with Retry-After header
    4. Else:
        - Increment counter
        - Set/extend cache expiry to window duration
        - Allow request
```

---

## 10. Configuration Handling

### Configuration Sources

| Source | File | Purpose |
|--------|------|---------|
| App Settings | Web.config `<appSettings>` | Feature flags, API keys, timeouts, limits |
| Connection Strings | Web.config `<connectionStrings>` | Azure SQL (ICE, EV), MongoDB (logging) |
| Entity Framework | Web.config `<entityFramework>` | EF provider, context config |
| log4net | Web.config `<log4net>` | Logging appender config |
| OWIN | Startup.cs | Auth middleware, pipeline config |

### Key Configuration Categories

**Authentication & Tokens:**
```xml
<add key="CommunicationKey" value="..." />           <!-- JWT signing key -->
<add key="accessTokenLifeTimeInMinutes" value="131400" />
<add key="refreshTokenLifeTimeInMinutes" value="..." />
<add key="OTPFailedAttemptCount" value="5" />
<add key="OTPFailedAttemptTimeout" value="60" />
<add key="FixedOTPLength" value="6" />
```

**External API Configuration:**
```xml
<add key="P360BaseUrl" value="https://p360uat.tvsmotor.com/gapi" />
<add key="DMSDigiApiUrl" value="https://dmsdigiapi.tvsmotor.com" />
<add key="MapMyIndiaApiKey" value="..." />
<add key="OpenWeatherApiKey" value="..." />
<add key="RapidApiKey" value="..." />
<add key="AirtelSMSUrl" value="https://digimate.airtel.in:15443/BULK_API/" />
<add key="TataSMSUrl" value="https://smsgw.tatatel.co.in:9095/" />
```

**Feature Flags:**
```xml
<add key="IsSendOTP" value="true" />                 <!-- Toggle OTP sending -->
<add key="swagger-enable" value="TRUE" />            <!-- Swagger UI toggle -->
<add key="DefaultFrameDMSData" value="1" />          <!-- Test data bypass -->
<add key="TestMobileNumber" value="..." />           <!-- Test numbers -->
```

**Azure Services:**
```xml
<add key="BlobStorageConnectionString" value="..." />
<add key="NotificationHubConnectionString" value="..." />
<add key="EventHubNamespace" value="..." />
```

**Rate Limiting:**
```xml
<add key="MaxLoginAttemptCount" value="5" />
<add key="LoginAttemptCacheDurationSeconds" value="1800" />
<add key="LoginIpBlockDurationInHours" value="2" />
```

### Environment-Specific Configuration

Configuration varies by environment via Web.config transforms:

| Setting | DEV | UAT | PROD |
|---------|-----|-----|------|
| `debug` | true | false | false |
| `customErrors` | Off | RemoteOnly | On |
| Connection Strings | Dev DB | UAT DB | Prod DB |
| API Base URLs | Dev endpoints | UAT endpoints | Prod endpoints |
| `swagger-enable` | TRUE | TRUE | FALSE (should be) |
| `IsSendOTP` | false (test) | true | true |

### Configuration Access Pattern

```csharp
// Used throughout codebase (100+ locations):
string value = ConfigurationManager.AppSettings["KeyName"];
int timeout = Convert.ToInt32(ConfigurationManager.AppSettings["TimeoutSeconds"]);
string connStr = ConfigurationManager.ConnectionStrings["TVSModel"].ConnectionString;
```

---

*This document is intended for engineering vendors to understand implementation details.*
*Do not expose secrets or credentials in shared copies of this document.*


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

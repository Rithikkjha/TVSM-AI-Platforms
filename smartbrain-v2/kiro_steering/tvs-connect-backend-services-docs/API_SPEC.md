# TVS Connect Web API — API Specification Document

| Attribute       | Value                                      |
|-----------------|--------------------------------------------|
| Service         | TVS Connect Web API                        |
| Base URL (UAT)  | `https://uat-tvsconnectapi.tvsmotor.net`   |
| Base URL (PROD) | `https://tvsconnectapi.tvsmotor.net`       |
| API Version     | v1 / v2 / v3 (URL path-based)             |
| Swagger UI      | `/swagger` (enabled via config flag)       |
| Format          | JSON (application/json)                    |
| Last Updated    | June 2026                                  |

---

## Table of Contents

1. [Authentication & Security](#1-authentication--security)
2. [Rate Limiting](#2-rate-limiting)
3. [Standard Response Envelope](#3-standard-response-envelope)
4. [Error Codes & Responses](#4-error-codes--responses)
5. [API Endpoint Catalog](#5-api-endpoint-catalog)
   - 5.1 [Inbound APIs](#51-inbound-apis-client-facing--exposed-by-tvs-connect-web-api)
   - 5.2 [Outbound APIs](#52-outbound-apis-external-systems-called-by-tvs-connect-web-api)
6. [Detailed Endpoint Specifications](#6-detailed-endpoint-specifications)
7. [External API Dependencies](#7-external-api-dependencies)
8. [Validation Rules](#8-validation-rules)
9. [Sample Requests & Responses](#9-sample-requests--responses)

---

## 1. Authentication & Security

### Authentication Mechanisms

| Mechanism | Header | Description |
|-----------|--------|-------------|
| **Legacy Token (v1)** | `token` + `userid` | Long-lived JWT token validated against DB via stored procedure `ValidateToken` |
| **Access Token (v2/v3)** | `accesstoken` + `userid` | Short-lived JWT with HMAC-SHA256 signature + DB validation via `ValidateAccessToken` |
| **Refresh Token** | `refreshtoken` | Used to obtain new access + refresh tokens without re-login |
| **Bearer Token** | `Authorization: Bearer <token>` | Service-to-service authentication (HIB notifications) |
| **Version Header** | `version: 2` | When present, triggers access+refresh token generation (v2 flow) |

### Token Generation

- **Algorithm**: HMAC-SHA256 (symmetric key from config `CommunicationKey`)
- **Claims**: `Name` (mobile number), `NameIdentifier` (userId)
- **Access Token Lifetime**: Configurable via `accessTokenLifeTimeInMinutes`
- **Refresh Token Lifetime**: Configurable via `refreshTokenLifeTimeInMinutes`
- **Legacy Token Lifetime**: 1 year

### Per-Request Validation Pipeline

```
1. Extract accesstoken + userid from headers
2. Validate JWT signature + expiry (HMAC-SHA256)
3. Verify NameIdentifier claim matches header userid
4. Verify userid in query string matches header (if present)
5. Verify UserId in JSON body matches header (if present)
6. Call SP ValidateAccessToken to confirm token is active in DB
7. Set Thread.CurrentPrincipal with authenticated identity
```

### Auth Error Codes (401 Unauthorized)

| Code | Condition | Message |
|------|-----------|---------|
| 1 | Missing userid or accesstoken header | "Missing UserId or Token" |
| 2 | UserId in querystring doesn't match header | "Invalid UserId in query string" |
| 3 | UserId in JSON body doesn't match header | "Different UserId" |
| 4 | Token expired or userId claim mismatch | "Invalid access token" |
| 5 | Token not found in DB for user | "Access token does not match" |

### Additional Headers (v3 Endpoints)

| Header | Type | Description |
|--------|------|-------------|
| `ICEUserId` | long | ICE platform user ID |
| `EVUserId` | long | EV platform user ID |
| `AppName` | string | Application identifier |
| `OS` | string | Operating system (ios/android) |
| `DeviceUUID` | string | Unique device identifier |
| `AppVersionName` | string | App version string |
| `DeviceModel` | string | Device model name |

---

## 2. Rate Limiting

### Configuration

| Parameter | Default | Config Key |
|-----------|---------|------------|
| Max requests per window | 5 | `MaxLoginAttemptCount` |
| Window duration | 1800 seconds (30 min) | `LoginAttemptCacheDurationSeconds` |
| Block duration | 2 hours | `LoginIpBlockDurationInHours` |

### Rate-Limited Endpoints

```
/api/v3/userlogin/loginv3
/api/RegisterUser/GenerateOTP
/api/v3/userlogin/verifyloginotp
```

### Behavior

- **Key**: Client IP (from `X-Forwarded-For` or `UserHostAddress`) + endpoint path
- **Algorithm**: Fixed-window counter with in-memory cache
- **On Block**: Returns `429 Too Many Requests` with `Retry-After` header
- **Persistence**: Blocked IPs are saved to database for analysis
- **Unblock**: Automatic after block duration expires

### 429 Response

```json
{
  "StatusCode": 429,
  "Result": "failure",
  "Message": "Too many requests. Please try again later.",
  "Data": null,
  "ErrorMessages": null
}
```

**Response Headers:**
```
Retry-After: <seconds-until-unblock>
```

---

## 3. Standard Response Envelope

### Primary Response Schema (Responsecls)

```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "Description of operation result",
  "Data": { /* payload object or array */ },
  "ErrorMessages": [
    { "Code": "ERR001", "Message": "Field-level error description" }
  ]
}
```

### Newer Response Schema (ResponceDto — v2/v3 endpoints)

```json
{
  "statusCode": 200,
  "result": "success",
  "message": "Operation successful",
  "data": { /* payload */ },
  "errorMessages": ["Error message 1", "Error message 2"]
}
```

### Common StatusCode Values

| StatusCode | Meaning |
|------------|---------|
| 200 | Success |
| 400 | Bad Request (validation failure) |
| 401 | Unauthorized (auth failure) |
| 404 | Not Found |
| 417 | Expectation Failed (exception) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

### Result Field Values

| Value | Meaning |
|-------|---------|
| `"success"` | Operation completed successfully |
| `"failure"` | Operation failed |

---

## 4. Error Codes & Responses

### Standard Error Responses

| HTTP Status | Result | Message | Condition |
|-------------|--------|---------|-----------|
| 200 + StatusCode 400 | failure | "Empty Fields Found." | Required fields missing |
| 200 + StatusCode 400 | failure | "User is already registered." | Duplicate registration |
| 200 + StatusCode 400 | failure | "Email is already registered." | Duplicate email |
| 200 + StatusCode 400 | failure | "Mobile is already registered." | Duplicate mobile |
| 200 + StatusCode 400 | failure | "Entered OTP is incorrect." | Wrong OTP |
| 200 + StatusCode 400 | failure | "Entered OTP is Expired." | OTP timeout |
| 200 + StatusCode 400 | failure | "Too many failed attempts. Try again after 1 hour." | OTP lockout |
| 200 + StatusCode 400 | failure | "Vehicle is already onboarded" | Duplicate vehicle |
| 200 + StatusCode 404 | success | "NewUser" | User not found (proceed to register) |
| 200 + StatusCode 404 | failure | "Record Not Found" | Entity not found |
| 401 | failure | "Session Expired" | Token invalid/expired |
| 429 | failure | "Too many requests..." | Rate limited |
| 200 + StatusCode 500 | failure | "InternalServerError" | Unhandled error |
| 200 + StatusCode 417 | failure | "Exception Occured" | Caught exception |

### Validation Error Pattern

```json
{
  "statusCode": 400,
  "result": "failure",
  "message": "failure",
  "data": null,
  "errorMessages": [
    "The MobileNumber field is required.",
    "Invalid platform value."
  ]
}
```

---

## 5. API Endpoint Catalog

APIs are categorized by traffic direction:
- **Inbound APIs** — endpoints exposed *by* TVS Connect Web API, consumed by the mobile app, admin portal, and Alexa/voice integration.
- **Outbound APIs** — external/third-party systems that TVS Connect Web API calls *out* to, in order to fulfill inbound requests.

---

### 5.1 Inbound APIs (Client-Facing — Exposed by TVS Connect Web API)

#### Authentication & User Management

| Method | Endpoint | Auth | Rate Limited | Description |
|--------|----------|------|--------------|-------------|
| POST | `/api/v3/userlogin/loginv3` | No | Yes | Initiate login (generate + send OTP) |
| POST | `/api/v3/userlogin/verifyloginotp` | No | Yes | Verify OTP and get tokens |
| POST | `/api/UserLogin/Login` | No | No | Legacy login (v1) |
| POST | `/api/UserLogin/Loginv1` | No | No | Login v1 with social auth |
| POST | `/api/UserLogin/VerifyLoginOtp` | No | No | Legacy OTP verification |
| POST | `/api/RegisterUser/CreateUser` | No | No | New user registration |
| POST | `/api/RegisterUser/VerifyOTP` | No | No | Verify registration OTP |
| POST | `/api/RegisterUser/GenerateOTP` | No | Yes | Resend OTP (SMS/WhatsApp) |
| POST | `/api/RegisterUser/RefreshJWTToken` | RefreshToken | No | Refresh access + refresh tokens |
| POST | `/api/RegisterUser/RefreshToken` | No | No | Legacy token refresh |
| POST | `/api/UpgradeToken` | JWT | No | Upgrade legacy token to v2 |
| POST | `/api/v3/userlogin/getnewevuserdetails` | JWT | No | Create EV user for ICE user |
| POST | `/api/v3/userlogin/getnewiceuserdetails` | No | No | Create ICE user for EV user |
| GET | `/api/v3/userlogin/migrateevuser` | No | No | Set migration flag for EV user |
| GET | `/api/v3/userlogin/migrateiceuser` | JWT | No | Set migration flag for ICE user |
| POST | `/api/v3/userlogin/replaceICEnumber` | No | No | Replace mobile number |

#### Vehicle Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v3/vehicle/vehiclelist` | JWT | Get DMS vehicle list by mobile |
| GET | `/api/vehicle/vehiclelist` | JWT | Get DMS vehicle list (alias) |
| POST | `/api/v3/vehicle/vehiclelistbyframeinvoice` | JWT | Get vehicle by frame + invoice date |
| POST | `/api/v3/vehicle/vehiclelistbyframeengineno` | JWT | Get vehicle by frame + engine number |
| GET | `/api/v3/vehicle/vehiclelistdetails` | JWT | Get ICE + EV vehicle list combined |
| GET | `/api/v2/vehicle/vehiclelistdetails` | JWT | Get ICE + EV vehicle list (v2 alias) |
| POST | `/api/Vehicle/AddVehicle` | JWT | Add/onboard vehicle (legacy) |
| POST | `/api/v3/Vehicle/AddVehicle` | JWT | Add/onboard vehicle (v3) |
| POST | `/api/v3/Vehicle/markactivevehicle` | JWT | Set active vehicle |
| GET | `/api/v3/Vehicle/GetOnBoarding` | JWT | Auto-onboard from DMS data |
| GET | `/api/vehicle/nonconnecteddashboard` | JWT | Non-connected vehicle dashboard |
| GET | `/api/vehicle/vehicledetails` | JWT | Get vehicle details |
| PUT | `/api/vehicle/vehiclenickname` | JWT | Update vehicle nickname |
| GET | `/api/vehicle/overspeedalert` | JWT | Get overspeed alert settings |
| POST | `/api/vehicle/overspeedalert` | JWT | Set overspeed alert settings |

#### Ride Management

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/ride` | JWT + VehicleAuth | Save ride data (with CSV upload) |
| GET | `/api/ride` | JWT + VehicleAuth | Get rides by user vehicle |
| PUT | `/api/ride` | JWT | Update ride name |
| DELETE | `/api/ride` | JWT | Delete a ride |
| POST | `/api/v2/ride` | JWT | Get filtered rides with pagination |
| DELETE | `/api/v2/ride` | JWT | Bulk delete rides |
| POST | `/api/v3/ride` | JWT | Get filtered rides v3 |
| GET | `/api/ride/rideStats` | JWT | Get ride statistics from P360 |
| GET | `/api/ride/rideanalytics` | JWT | Get ride analytics |
| POST | `/api/ride/favouriterides` | JWT | Set favourite rides |
| GET | `/api/ride/trackingpoints` | JWT | Get ride tracking points |

#### Notifications

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/Notification/SendNotification` | JWT | Trigger pending notifications |
| GET | `/api/Notification/GetNotificationByUser` | JWT | Get user notifications |
| POST | `/api/Notification/ClearNotification` | JWT | Clear notifications |
| POST | `/api/Notification/MakeSeen` | JWT | Mark notifications as read |
| GET | `/api/Notification/Getadminnotificationbyuser` | JWT | Get admin notifications (paginated) |
| POST | `/api/notification/sendnotification` | Bearer | Send custom push notification |
| GET | `/api/Notification/Unread` | JWT | Get unread notification count |
| GET | `/api/Notification/NotificationList` | JWT | Get combined notification list |
| POST | `/api/Notification/registerfcmtoken` | JWT | Register FCM token |
| POST | `/api/Notification/deregisterfcmtoken` | JWT | Deregister FCM token |

#### Geofence

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/geofence/getgeofencelist` | JWT | Get geofence list |
| POST | `/api/geofence/updategeofence` | JWT | Update geofence |
| GET | `/api/geofence/getallgeofencealerts` | JWT | Get all geofence alerts |
| GET | `/api/geofence/getgeofencedetails` | JWT | Get geofence details |
| POST | `/api/geofence/deletegeofence` | JWT | Delete geofence |
| POST | `/api/geofence/addgeofence` | JWT | Create new geofence |
| POST | `/api/geofence/addvehicletogeofence` | JWT | Add vehicle to geofence |

#### User Profile

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/UserProfile/GetProfile` | JWT | Get user profile |
| PUT | `/api/UserProfile/UpdateProfile` | JWT | Update user profile |
| POST | `/api/UserProfile/UploadProfileImage` | JWT | Upload profile image |
| POST | `/api/UserProfile/DeleteUser` | JWT | Request account deletion |
| GET | `/api/UserProfile/GetUserConsent` | JWT | Get consent status |
| POST | `/api/UserProfile/UpdateUserConsent` | JWT | Update consent |

#### Connected Vehicle (Home Dashboard)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/Home/GetLatestDeviceData` | JWT | Get latest vehicle telemetry |
| GET | `/api/Home/GetRideCumulative` | JWT | Get cumulative ride stats |

#### OTA Updates

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/OTA/CheckForUpdate` | JWT | Check firmware update availability |
| POST | `/api/OTA/GetSASToken` | JWT | Get SAS token for OTA download |

#### Third-Party Content

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/Weather/GetWeather` | JWT | Get weather forecast |
| GET | `/api/Weather/GetAQI` | JWT | Get air quality index |
| GET | `/api/Cricket/GetLiveMatches` | JWT | Get live cricket scores |
| GET | `/api/Football/GetLiveMatches` | JWT | Get live football scores |
| GET | `/api/News/GetNews` | JWT | Get news feed |

#### Service & Feedback

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/Service/BookService` | JWT | Book dealer service |
| GET | `/api/Service/GetServiceHistory` | JWT | Get service history |
| POST | `/api/Feedback/SubmitFeedback` | JWT | Submit feedback |
| GET | `/api/CSIFeedback/GetCSIFeedback` | JWT | Get CSI feedback form |
| POST | `/api/CSIFeedback/SubmitCSIFeedback` | JWT | Submit CSI feedback |
| GET | `/api/NPSFeedback/GetNPSFeedback` | JWT | Get NPS feedback form |

#### Miscellaneous

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/Health/CheckHealth` | No | Health check |
| GET | `/api/SasToken/GetSASToken` | JWT | Get Event Hub SAS token |
| GET | `/api/MasterData/GetStates` | JWT | Get states list |
| GET | `/api/MasterData/GetCities` | JWT | Get cities by state |

---

### 5.2 Outbound APIs (External Systems Called by TVS Connect Web API)

These are third-party/external APIs that TVS Connect Web API calls out to when fulfilling inbound requests. Full auth, timeout, and circuit-breaker details are in [Section 7 — External API Dependencies](#7-external-api-dependencies).

#### Vehicle & Telematics

| System | Called From (Inbound Trigger) | Direction | Purpose |
|--------|-------------------------------|-----------|---------|
| P360 Telematics | Home, Ride, Vehicle, Geofence endpoints | Outbound | Vehicle telemetry, connected data, SAS tokens |
| DMS Digi API | Vehicle Management endpoints | Outbound | Vehicle lookup, job cards, service history |
| DMS Online Sales | Vehicle Management endpoints | Outbound | Sales/ownership data lookup |
| MapMyIndia (Mappls) | Ride Management (route images) | Outbound | Static route map image generation |

#### Content & Master Data

| System | Called From (Inbound Trigger) | Direction | Purpose |
|--------|-------------------------------|-----------|---------|
| Sitecore CMS | Preownership endpoints | Outbound | Vehicle content, pre-ownership data |
| OpenWeatherMap | Third-Party Content (`/api/Weather/*`) | Outbound | Weather forecast + AQI |
| Bing News | Third-Party Content (`/api/News/*`) | Outbound | News aggregation |
| RapidAPI Cricket | Third-Party Content (`/api/Cricket/*`) | Outbound | Live cricket scores |
| RapidAPI Football | Third-Party Content (`/api/Football/*`) | Outbound | Live football scores |

#### Communication & Notification

| System | Called From (Inbound Trigger) | Direction | Purpose |
|--------|-------------------------------|-----------|---------|
| Airtel Digimate SMS | Login/Register OTP endpoints | Outbound | Primary OTP/SMS delivery |
| Tata Communication SMS | Login/Register OTP endpoints | Outbound | Failover OTP/SMS delivery |
| WhatsApp Notification Service | Register (`GenerateOTP` WhatsApp flag) | Outbound | WhatsApp-based OTP delivery |
| Azure Notification Hub | Notification endpoints, Login | Outbound | Push notification delivery |

#### Storage, Streaming & Infra

| System | Called From (Inbound Trigger) | Direction | Purpose |
|--------|-------------------------------|-----------|---------|
| Azure Blob Storage | Ride, OTA, Profile endpoints | Outbound | File storage (CSV, images, firmware) |
| Azure Event Hub | SasToken endpoints | Outbound | Vehicle telemetry streaming (per SAS token) |

#### Service & Booking

| System | Called From (Inbound Trigger) | Direction | Purpose |
|--------|-------------------------------|-----------|---------|
| RSA Policy | Service endpoints | Outbound | Roadside assistance policy lookup |
| TVS Service History (CRC Portal) | Service endpoints | Outbound | Dealer service history |
| Shopify Booking | Service endpoints | Outbound | Service/booking management |

> **Note:** All inbound endpoints are synchronous request/response over HTTPS. Outbound calls are wrapped in a Polly-based circuit breaker (see [Circuit Breaker Protection](#circuit-breaker-protection)) — retries on 5xx/429/timeout, opens after 5 consecutive failures, auto-closes after 30s.

---

## 6. Detailed Endpoint Specifications

### 6.1 POST /api/v3/userlogin/loginv3

**Purpose:** Initiate login — checks user existence across ICE + EV, generates OTP, sends SMS.

**Auth:** None (public) | **Rate Limited:** Yes

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "MobileNumber": "9876543210",
  "iosToken": "apns-device-token-string",
  "androidToken": "fcm-device-token-string",
  "publicKey": "RSA-public-key-base64",
  "PlatformType": "MOBILE",
  "Application": "TVSConnect"
}
```

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "",
  "Data": {
    "MobileNumber": "9876543210",
    "ICEUserId": "12345",
    "EVUserId": "67890",
    "IsNewUser": "0"
  }
}
```

**Error Responses:**

| Condition | StatusCode | Message |
|-----------|------------|---------|
| Empty mobile | 400 | "Empty Fields Found." |
| Rate limited | 429 | "Too many requests..." |
| Server error | 417 | "Something went wrong" |

---

### 6.2 POST /api/v3/userlogin/verifyloginotp

**Purpose:** Verify OTP, generate JWT tokens, register device for push notifications.

**Auth:** None (public) | **Rate Limited:** Yes

**Request Headers:**
```
Content-Type: application/json
ICEUserId: 12345
EVUserId: 67890
version: 2
```

**Request Body:**
```json
{
  "Mobilenumber": "9876543210",
  "Otp": 123456,
  "IosToken": "apns-token",
  "AndroidToken": "fcm-token",
  "publicKey": "RSA-public-key-base64",
  "deviceType": "android"
}
```

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "successfully logged In",
  "Data": {
    "iceUser": {
      "UserId": 12345,
      "MobileNumber": "9876543210",
      "FullName": "User Name",
      "Email": "user@email.com",
      "Token": "jwt-legacy-token",
      "AccessToken": "jwt-access-token",
      "RefreshToken": "jwt-refresh-token",
      "ProfileImagePath": "https://..."
    },
    "evUser": {
      "UserId": 67890,
      "Token": "ev-jwt-token",
      "AccessToken": "ev-access-token",
      "RefreshToken": "ev-refresh-token"
    }
  }
}
```

**Response Headers (on success):**
```
Token: <jwt-token>
userid: <user-id>
```

---

### 6.3 POST /api/RegisterUser/GenerateOTP

**Purpose:** Generate and send OTP for existing user (resend OTP). Supports SMS and WhatsApp channels.

**Auth:** None (public) | **Rate Limited:** Yes

**Request Body:**
```json
{
  "Mobilenumber": "9876543210",
  "IsWhatsAppOTPRequested": false,
  "Application": "TVSConnect"
}
```

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "",
  "Data": ""
}
```

**Error Responses:**

| Condition | StatusCode | Message |
|-----------|------------|---------|
| User not found | 400 | "User not found" |
| Internal error | 400 | "Internal Error" |

---

### 6.4 POST /api/RegisterUser/RefreshJWTToken

**Purpose:** Exchange valid refresh token for new access + refresh token pair.

**Auth:** Refresh Token (validated via `RefreshTokenValidationFilter`)

**Request Headers:**
```
refreshtoken: <current-refresh-token>
```

**Request Body:** Empty

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "Access and Refresh tokens are generated successfully",
  "Data": {
    "AccessToken": "new-jwt-access-token",
    "RefreshToken": "new-jwt-refresh-token"
  }
}
```

---

### 6.5 POST /api/ride

**Purpose:** Save ride telemetry data with CSV file upload, trigger cumulative calculation and route image generation.

**Auth:** JWT + UserVehicleAuthorization

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UserId | long | Yes (from header) | User identifier |
| UserVehicleId | long | Yes | User-vehicle mapping ID |
| VehicleTypeId | int | Yes | Vehicle type identifier |
| RideDetails | JSON | Yes | Ride metadata |
| Files[0] | File (CSV) | Yes | Telemetry CSV data |

**RideDetails Schema:**
```json
{
  "travelId": 0,
  "vehicleTypeId": 22,
  "userId": 12345,
  "userVehicleId": 456,
  "totalTime": 3600,
  "rideTime": 3200,
  "travelStartTime": 1719648000,
  "travelEndTime": 1719651600,
  "totalTravelledDistance": 45.5,
  "topSpeed": 85.3,
  "avgSpeed": 42.1,
  "Type": 1,
  "Tour": null
}
```

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Result": "Success",
  "Message": "Record saved successfully",
  "Data": {
    "travelId": 789,
    "totalTravelledDistance": 45.5,
    "topSpeed": 85.3,
    "avgSpeed": 42.1,
    "travelStartTime": 1719648000,
    "travelEndTime": 1719651600,
    "rideStatsDownloadLink": "https://blob.../ride.csv",
    "travelMMIDownloadLink": "https://blob.../route.png"
  }
}
```

---

### 6.6 POST /api/v3/Vehicle/AddVehicle

**Purpose:** Onboard a vehicle — integrates with CODP/TrakNTell for connected vehicles.

**Auth:** JWT

**Request Headers:**
```
userid: 12345
ICEUserId: 12345
EVUserId: 67890
```

**Request Body:**
```json
{
  "UserId": "12345",
  "FRAME_NO": "MD2A43AZ5RCA12345",
  "ENGINE_NO": "A43ARCA12345",
  "REG_NO": "KA01AB1234",
  "SERIES": "ntorq",
  "SALE_DATE": "2024-01-15",
  "TOV_PART_ID": "K21901408F",
  "MAC_ID": "AA:BB:CC:DD:EE:FF",
  "TelematicsSerialNo": "TEL-12345",
  "DEALER_ID": "DLR001",
  "VehicleName": "My NTorq",
  "NickName": "Rocket"
}
```

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "Vehicle successfully onboarded",
  "Data": { /* VehicleDetail object */ }
}
```

---

### 6.7 GET /api/geofence/getgeofencelist

**Purpose:** Get list of geofences for a user vehicle.

**Auth:** JWT

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| userVehicleId | long | Yes | User vehicle mapping ID |

**Success Response (200):**
```json
{
  "statusCode": 200,
  "result": "success",
  "message": "Geofences fetched successfully",
  "data": {
    "geofences": [
      {
        "geofenceId": "gf-001",
        "name": "Home",
        "radius": 500,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "isActive": true
      }
    ]
  }
}
```

---

## 7. External API Dependencies

| External System | Base URL | Auth | Called By | Timeout |
|-----------------|----------|------|-----------|---------|
| **P360 Telematics** | `https://p360uat.tvsmotor.com/gapi` | JWT Bearer (generated per-request) | HomeController, RideController, VehicleController, GeofenceController | 5s |
| **DMS Digi API** | `https://dmsdigiapi.tvsmotor.com/login/` | Basic Auth (Base64) | VehicleController, FeedbackController | 15s |
| **DMS Online Sales** | `https://www.advantagetvs.in/OnlineSalesWebAPI/` | Basic Auth (Username/Password) | VehicleController | 15s |
| **Sitecore CMS** | `https://www.tvsmotor.com/sitecore/api/layout/` | API Key | PreownershipController | 15s |
| **MapMyIndia (Mappls)** | `https://apis.mappls.com/advancedmaps/v1/` | API Key (URL param) | RideController (route images) | 15s |
| **OpenWeatherMap** | `https://api.openweathermap.org/data/2.5/` | API Key (URL param) | WeatherController | 15s |
| **Bing News** | `https://api.bing.microsoft.com/v7.0/news` | Subscription Key (Header) | NewsController | 15s |
| **RapidAPI Cricket** | `https://cricket-live-data.p.rapidapi.com/` | API Key (Header) | CricketController | 15s |
| **RapidAPI Football** | `https://api-football-v1.p.rapidapi.com/v3/` | API Key (Header) | FootballController | 15s |
| **Airtel Digimate SMS** | `https://digimate.airtel.in:15443/BULK_API/` | Username + Encoded Key | SMSService | 15s |
| **Tata Communication SMS** | `https://smsgw.tatatel.co.in:9095/campaignService/` | Username + Password | SMSService | 15s |
| **WhatsApp Notification** | `https://uat-api.tvsmotor.net/notification-service/` | OAuth 2.0 (Azure AD Client Credentials) | WhatsAppService | 15s |
| **Azure Notification Hub** | Azure SDK (Connection String) | SAS Connection String | NotificationController, Login | 30s |
| **Azure Blob Storage** | Azure SDK (Account Key) | Storage Account Key | RideService, OTAService, ProfileService | 30s |
| **Azure Event Hub** | AMQP (SAS Token) | SAS Token (per vehicle type) | SASTokenController | N/A |
| **RSA Policy** | `https://myhrmsnow.com/rsa/` | Direct URL | ServiceController | 15s |
| **TVS Service History** | `https://tvsmapp.com/CRC_PORTAL/` | Direct URL | ServiceController | 15s |
| **Shopify Booking** | `https://uat-api.tvsmotor.net` | OAuth 2.0 (Client Credentials) | ShopifyBookingController | 15s |

### Circuit Breaker Protection

All external HTTP calls are wrapped in the Polly-based circuit breaker (per-host config):
- **Retry** on 5xx, 429, timeout, HttpRequestException
- **Circuit opens** after 5 consecutive failures
- **Auto-close** after 30 seconds (half-open probe)
- **Email alert** sent to engineering team on break/reset

---

## 8. Validation Rules

### Request-Level Validation

| Rule | Applied To | Description |
|------|-----------|-------------|
| Required fields check | All endpoints | Controller-level null/empty checks |
| UserId consistency | All JWT endpoints | Header userid must match body/querystring userid |
| UserVehicle authorization | Ride POST/GET | Validates user owns the vehicle (UserVehicleAuthorization filter) |
| OTP length | Login/Register | Fixed 6-digit OTP (configurable via `FixedOTPLength`) |
| OTP lockout | Login/Register | Max 5 attempts, then 60-min lockout |
| Mobile number format | Registration | 10-digit numeric validation |
| Email validation | Registration | Standard email format check |
| Blood group validation | Registration | Must exist in master data |
| Platform validation | Multiple endpoints | Must be valid PlatformEnum (IOS/ANDROID/WEB) |
| LatLong validation | Geofence | Custom attribute: Lat and Long must be non-null |
| Vehicle duplicate check | AddVehicle | Prevents re-onboarding same vehicle |
| Profile image size | UploadProfileImage | Max 5 MB allowed |
| Travel IDs uniqueness | Bulk delete rides | No duplicate IDs in array |

### Custom Validation Attributes

| Attribute | Applied To | Logic |
|-----------|-----------|-------|
| `[PlatformValidation]` | Platform field | Validates against `PlatformEnum` (IOS, ANDROID, WEB) |
| `[LatLongValidator]` | LatLong objects | Ensures Lat and Long are non-null |
| `[ValidateModel]` | Profile update | Custom ModelState validation (FirstName, MobileNumber required) |
| `[JwtAuthenticationFilter]` | Protected endpoints | Full JWT + DB token validation |
| `[UserVehicleAuthorization]` | Ride endpoints | Verifies vehicle ownership |
| `[ArgumentExceptionFilter]` | Ride endpoints | Catches validation exceptions, returns 400 |
| `[RefreshTokenValidationFilter]` | Token refresh | Validates refresh token format and signature |

### OTP Security Rules

| Rule | Value | Config Key |
|------|-------|------------|
| OTP Length | 6 digits | `FixedOTPLength` |
| Max Failed Attempts | 5 | `OTPFailedAttemptCount` |
| Lockout Duration | 60 minutes | `OTPFailedAttemptTimeout` |
| Lockout Message | "Too many failed attempts. Try again after 1 hour." | `OTPFailedAttemptMessage` |

---

## 9. Sample Requests & Responses

### 9.1 Login Flow (Complete)

**Step 1: Initiate Login**

```http
POST /api/v3/userlogin/loginv3 HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
Content-Type: application/json

{
  "MobileNumber": "9876543210",
  "androidToken": "fLp4kHs...FCM_TOKEN",
  "publicKey": "MIIBIjANBg...RSA_KEY",
  "PlatformType": "MOBILE"
}
```

**Response:**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "",
  "Data": {
    "MobileNumber": "9876543210",
    "ICEUserId": "10523",
    "EVUserId": "8901",
    "IsNewUser": "0"
  }
}
```

**Step 2: Verify OTP**

```http
POST /api/v3/userlogin/verifyloginotp HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
Content-Type: application/json
ICEUserId: 10523
EVUserId: 8901
version: 2

{
  "Mobilenumber": "9876543210",
  "Otp": 654321,
  "AndroidToken": "fLp4kHs...FCM_TOKEN",
  "publicKey": "MIIBIjANBg...RSA_KEY",
  "deviceType": "android"
}
```

**Response:**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "successfully logged In",
  "Data": {
    "iceUser": {
      "UserId": 10523,
      "FullName": "Raj Kumar",
      "MobileNumber": "9876543210",
      "Email": "raj@email.com",
      "ProfileImagePath": "https://uat-tvsconnectapi.tvsmotor.net/domestic-assets/...",
      "Token": "eyJhbGciOi...",
      "AccessToken": "eyJhbGciOi...",
      "RefreshToken": "eyJhbGciOi..."
    },
    "evUser": {
      "UserId": 8901,
      "Token": "eyJhbGciOi...",
      "AccessToken": "eyJhbGciOi...",
      "RefreshToken": "eyJhbGciOi..."
    }
  }
}
```

---

### 9.2 Get Vehicle List

```http
GET /api/v3/vehicle/vehiclelist?mobileNumber=9876543210 HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
accesstoken: eyJhbGciOi...
userid: 10523
```

**Response:**
```json
{
  "StatusCode": 200,
  "Result": "success",
  "Message": "DMS data",
  "Data": [
    {
      "FRAME_NO": "MD2A43AZ5RCA12345",
      "ENGINE_NO": "A43ARCA12345",
      "SERIES": "ntorq",
      "PART_ID": "K21901408F",
      "SALE_DATE": "2024-01-15",
      "REG_NO": "KA01AB1234",
      "IsEV": 0,
      "Is3W": 0,
      "ImageUrl": "https://..."
    }
  ]
}
```

---

### 9.3 Save Ride

```http
POST /api/ride HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
Content-Type: multipart/form-data
accesstoken: eyJhbGciOi...
userid: 10523

--boundary
Content-Disposition: form-data; name="UserVehicleId"
456
--boundary
Content-Disposition: form-data; name="VehicleTypeId"
22
--boundary
Content-Disposition: form-data; name="RideDetails"
{"totalTime":3600,"rideTime":3200,...,"Type":1,"Tour":null}
--boundary
Content-Disposition: form-data; name="Files"; filename="ride_data.csv"
Content-Type: text/csv
<CSV telemetry data>
--boundary--
```

**Response:**
```json
{
  "StatusCode": 200,
  "Result": "Success",
  "Message": "Record saved successfully",
  "Data": {
    "travelId": 78901,
    "totalTravelledDistance": 23.4,
    "topSpeed": 72.5,
    "avgSpeed": 38.2,
    "travelStartTime": 1719648000,
    "travelEndTime": 1719651600,
    "rideStatsDownloadLink": "https://tvsmaztcmstauat02cin.blob.core.windows.net/...",
    "travelMMIDownloadLink": "https://tvsmaztcmstauat02cin.blob.core.windows.net/..."
  }
}
```

---

### 9.4 Add Geofence

```http
POST /api/geofence/addgeofence HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
Content-Type: application/json
accesstoken: eyJhbGciOi...
userid: 10523

{
  "userVehicleId": 456,
  "name": "Office",
  "radius": 300,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "isActive": true
}
```

**Response:**
```json
{
  "statusCode": 200,
  "result": "success",
  "message": "Geofence created successfully",
  "data": {
    "geofenceId": "gf-002",
    "name": "Office",
    "radius": 300,
    "latitude": 12.9716,
    "longitude": 77.5946
  }
}
```

---

### 9.5 401 Unauthorized Response

```http
GET /api/ride?UserVehicleId=456&VehicleTypeId=22&Type=1 HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
accesstoken: expired-token-here
userid: 10523
```

**Response (401):**
```json
{
  "StatusCode": 401,
  "Result": "failure",
  "Message": "Invalid access token",
  "Data": null,
  "ErrorMessages": null
}
```

---

### 9.6 Rate Limited Response (429)

```http
POST /api/v3/userlogin/loginv3 HTTP/1.1
Host: uat-tvsconnectapi.tvsmotor.net
Content-Type: application/json

{"MobileNumber": "9876543210"}
```

**Response (429):**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 7200

{
  "StatusCode": 429,
  "Result": "failure",
  "Message": "Too many requests. Please try again later.",
  "Data": null,
  "ErrorMessages": null
}
```

---

## Appendix: OpenAPI Info Block

```yaml
openapi: 3.0.3
info:
  title: TVS Connect Web API
  description: Backend API for TVS Connect mobile app - connected vehicle platform
  version: 3.0.0
  contact:
    name: TVS Motor - Connected Vehicle Services
    email: ConnectedServices@tvsmotor.com
servers:
  - url: https://uat-tvsconnectapi.tvsmotor.net
    description: UAT Environment
  - url: https://tvsconnectapi.tvsmotor.net
    description: Production Environment
  - url: https://dev-tvsconnectapi.tvsmotor.net
    description: Development Environment
tags:
  - name: Authentication
    description: Login, OTP, token management
  - name: Vehicle
    description: Vehicle onboarding and management
  - name: Ride
    description: Ride recording and analytics
  - name: Geofence
    description: Geofence CRUD and alerts
  - name: Notification
    description: Push notification management
  - name: UserProfile
    description: User profile management
  - name: OTA
    description: Over-the-air firmware updates
  - name: Content
    description: Weather, news, sports content
  - name: Service
    description: Dealer service booking
components:
  securitySchemes:
    JwtTokenAuth:
      type: apiKey
      in: header
      name: accesstoken
      description: JWT access token (HMAC-SHA256 signed)
    UserIdHeader:
      type: apiKey
      in: header
      name: userid
      description: Numeric user ID (must match token claims)
    LegacyTokenAuth:
      type: apiKey
      in: header
      name: token
      description: Legacy long-lived JWT token
    RefreshTokenAuth:
      type: apiKey
      in: header
      name: refreshtoken
      description: JWT refresh token for token renewal
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: Service-to-service bearer token
```

---

*Document Type: API Specification for External Engineering Partners*
*Swagger UI: Available at `/swagger` (configurable via AppSettings `swagger-enable`)*
*Confidentiality: Internal-shareable. No credentials or proprietary logic included.*


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

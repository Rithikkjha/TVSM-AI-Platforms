# TVS Connect - API Specification Document

> **Purpose**: API reference for engineering vendors working on the TVS Connect mobile application.
> **Last Updated**: June 2026
> **Format**: OpenAPI/Swagger-friendly structure

---

## 1. Authentication Requirements

All API requests (except login/signup) require the following headers:

| Header | Description | Required |
|--------|-------------|----------|
| `accessToken` | JWT access token | Yes |
| `UserId` | Numeric user identifier | Yes |
| `countryId` | Country code (e.g., "1" for India) | Yes |
| `Region` | Region identifier (e.g., "nepal", "srilanka") | Conditional |
| `lang` | Language code (e.g., "en-US") | Yes |

**P360/EV endpoints** use a different header pattern:

| Header | Description |
|--------|-------------|
| `AccessToken` | EV access token |
| `RefreshToken` | EV refresh token |
| `userid` | User ID (lowercase) |

---

## 2. API Endpoint List

### 2.1 Authentication & User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/UserLogin/Loginv1` | Login with OTP request |
| POST | `/UserLogin/VerifyLoginOtp` | Verify login OTP |
| POST | `/RegisterUser/CreateUser` | New user registration |
| POST | `/RegisterUser/VerifyOTP` | Verify registration OTP |
| POST | `/RegisterUser/GenerateOTP` | Resend OTP |
| POST | `/UpgradeToken` | Upgrade legacy token |
| POST | `/RefreshToken` | Refresh access token |
| GET | `/secret` | Get secured API keys |
| GET | `/RegisterUser/GetCountryList` | Get supported countries |
| GET | `/state` | Get state-wise city list |

### 2.2 Vehicle Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/Vehicle/AddVehicle` | Add new vehicle |
| POST | `/Vehicle/AddVehicleWithoutVINDetails` | Add vehicle (no VIN) |
| POST | `/Vehicle/SendOTPtoBikeOwner` | OTP for ownership verification |
| POST | `/Vehicle/VerifyOTPforBikeOwner` | Verify bike owner OTP |
| GET | `/Vehicle/GetVahicleList` | Get user's vehicles |

### 2.3 Dashboard & Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/UserDashboard/GetDashboardDetail` | Get dashboard data |
| GET | `/vehicle/overview` | Get vehicle cumulative data |
| GET | `/Travel/GetVehicleCumulativeData` | Legacy cumulative data |

### 2.4 Ride Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ride` | Save ride data (multipart) |
| POST | `/Travel/inserttraveldataForApache` | Save Apache ride (legacy) |
| POST | `/N109/inserttraveldataForN109` | Save N109 ride |
| POST | `/N251/inserttraveldataForN251BLE` | Save N251 ride |
| POST | `/widget` | Save dashboard widgets |

### 2.5 Navigation & Location

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/location/favourite` | Add favourite location |
| GET | `/location/favourite` | Get all favourite locations |
| PUT | `/location/favourite` | Edit favourite location |
| DELETE | `/location/favourite` | Delete favourite location |
| POST | `/location/recent` | Add recent location |
| GET | `/location/recent` | Get all recent locations |
| POST | `/location/sharelivelocation` | Share live location |
| POST | `/location/stoplivelocation` | Stop live location sharing |
| GET | `/home/getallfavoritelocations` | P360 favourites |
| GET | `/home/getallrecentlocations` | P360 recents |
| GET | `/home/getallshareddestinations` | Get shared destinations |

### 2.6 Service & Support

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/Tips/GetTips` | Get maintenance tips |
| GET | `/Maintainance/GetMaintainance` | DIY maintenance guides |
| GET | `/Support/getHelp` | Get help content |
| GET | `/Support/getCrashAlertFeatures` | Crash alert config |
| POST | `/Service/BookService` | Book service appointment |
| GET | `/v2/Faq/GetFaq` | Get FAQ list |
| POST | `/V2/Feedback/AddFeedback` | Submit feedback |
| GET | `/Feedback/Feedbacktype` | Get feedback types |

### 2.7 Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | Get notification list |
| POST | `/notifications/clear` | Clear notifications |
| POST | `/notifications/counter` | Update notification counter |

### 2.8 Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mobilesetting` | Get optimized settings |
| GET | `/mobilesettinginfo` | Get settings info |
| POST | `/UserLogin/CrashAlertDate` | Set crash alert date |
| POST | `/AddDeviceDetails` | Sync device details |

### 2.9 Community

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/discussions` | Get discussions list |
| POST | `/discussions` | Create discussion |
| GET | `/events` | Get events list |
| POST | `/events` | Create event |
| POST | `/comments` | Create comment |
| POST | `/likes` | Toggle like |

### 2.10 Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ManageProfile/EditProfile` | Edit profile (multipart) |
| POST | `/EmergencyContact/AddEmergencyContact` | Add emergency contact (multipart) |

---

## 3. Request/Response Payloads

### 3.1 Login Request

```json
POST /UserLogin/Loginv1
Content-Type: application/json

{
  "mobileNumber": "9876543210",
  "countryCode": "+91",
  "loginType": "otp",
  "deviceId": "unique-device-id",
  "fcmToken": "firebase-cloud-messaging-token"
}
```

### 3.2 Verify OTP Request

```json
POST /UserLogin/VerifyLoginOtp
Content-Type: application/json
Header: Version: "8.8.0"

{
  "mobileNumber": "9876543210",
  "otp": "1234",
  "publicKey": "base64-encoded-rsa-public-key"
}
```

### 3.3 Verify OTP Response

```json
{
  "statusCode": 200,
  "message": "Success",
  "data": {
    "userId": "12345",
    "accessToken": "jwt-access-token",
    "refreshToken": "jwt-refresh-token",
    "fullName": "User Name",
    "mobileNumber": "9876543210",
    "email": "user@example.com",
    "vehicles": [...]
  }
}
```

### 3.4 Add Favourite Location

```json
POST /location/favourite
Headers: userid, AccessToken, RefreshToken, countryId, region, lang

{
  "vin": "vehicle-vin-number",
  "locationName": "Office",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "address": "Full address string"
}
```

### 3.5 Add Favourite Location Response

```json
{
  "statusCode": 200,
  "message": "Favourite location added successfully",
  "data": {
    "id": "fav-123",
    "locationName": "Office",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "address": "Full address string"
  }
}
```

### 3.6 Save Ride (Multipart)

```
POST /ride
Content-Type: multipart/form-data

Parts:
- UserVehicleId: "vehicle-id"
- UserId: "user-id"
- VehicleTypeId: "vehicle-type"
- StartDate: "2026-06-09T10:00:00"
- EndDate: "2026-06-09T11:30:00"
- Distance: "45.2"
- Duration: "5400"
- AvgSpeed: "30.1"
- MaxSpeed: "85.0"
- file: route-data.json (MultipartBody.Part)
```

### 3.7 Refresh Token Request

```json
POST /RefreshToken
Headers: accessToken, refreshToken

{
  "requestType": "refreshToken"
}
```

### 3.8 Refresh Token Response

```json
{
  "statusCode": 200,
  "data": {
    "accessToken": "new-jwt-access-token",
    "refreshToken": "new-jwt-refresh-token"
  }
}
```

---

## 4. Error Responses

### 4.1 Standard Error Format

```json
{
  "statusCode": 400,
  "message": "Human-readable error message",
  "result": "Additional error context"
}
```

### 4.2 HTTP Status Code Handling

| Code | Meaning | App Behavior |
|------|---------|------|
| 200 | Success | Process response |
| 400 | Bad Request | Show error dialog |
| 401 | Unauthorized | Force logout, broadcast session expired |
| 500 | Server Error | Error callback to caller |
| Timeout | Connection timeout | Show timeout message |
| No network | No connectivity | Show "No connection" dialog |

---

## 5. Validation Rules

| Field | Rule |
|-------|------|
| Mobile Number | Non-empty, valid format per country |
| OTP | 4-6 digits, non-empty |
| Access Token | Non-empty string in header |
| User ID | Non-empty numeric string |
| VIN | Alphanumeric, model-specific length |
| Latitude/Longitude | Valid GPS coordinates |
| File upload | Max size per endpoint configuration |

---

## 6. Rate Limits

Rate limiting is managed server-side. Client-side mitigations:

| Mechanism | Implementation |
|-----------|---------------|
| Request queuing | `PriorityQueue<NetworkRequestObject>` |
| Connection pooling | `ConnectionPool(3, 10000ms)` |
| Timeout | 160 seconds (session timeout interval) |
| Retry | `RetryInterceptor` with configurable retry count |

---

## 7. External API Dependencies

| Service | Base URL Pattern | Auth Method |
|---------|-----------------|-------------|
| TrakNTell (TNT) | `api.trakntell.com/tnt/servlet/` | Mutual TLS (client certificate) |
| Kazam | `platform.kazam.in/` | Bearer token |
| Google Elevation | `maps.googleapis.com/maps/api/` | API key |
| P360 GraphQL | `p360.tvsmotor.com/gapi` | Bearer token |
| P360 WebSocket | `wss://p360.tvsmotor.com/subscriptions` | Connection payload token |
| Dealer Locator | `api.latlong.in/v2/` | OAuth2 access token |

---

## 8. GraphQL Schema (P360)

### 8.1 Connection

```
Server URL: {P360_URL}/gapi
WebSocket URL: {P360_WSS_URL}/subscriptions
Auth: Bearer token via Authorization header
Cache: SQLite normalized cache (apollo_.db)
```

### 8.2 Subscription Pattern

```graphql
subscription LiveTracking($vehicleId: String!) {
  vehicleLocation(vehicleId: $vehicleId) {
    latitude
    longitude
    speed
    heading
    timestamp
  }
}
```

---

## 9. Sample Requests / Responses

### 9.1 Get Vehicle List

```
GET /Vehicle/GetVahicleList?userid=12345
Headers:
  accessToken: <token>
  UserId: 12345
  countryId: 1
  Region: ""
  lang: en-US

Response:
{
  "statusCode": 200,
  "data": [
    {
      "userVehicleId": "v-001",
      "vehicleName": "Apache RTR 200",
      "vehicleTypeId": "U399",
      "vin": "MD2ABCDE1234567",
      "nickName": "My Apache"
    }
  ]
}
```

### 9.2 Get Cumulative Data

```
GET /vehicle/overview?UserVehicleId=v-001&UserId=12345&VehicleTypeId=U408
Headers:
  countryId: 1
  Region: ""
  lang: en-US

Response:
{
  "statusCode": 200,
  "data": {
    "totalRides": 156,
    "totalDistance": 4520.5,
    "totalDuration": 345600,
    "avgSpeed": 32.1,
    "maxSpeed": 98.5,
    "avgMileage": 42.3
  }
}
```

---

*This document is generated for engineering vendor reference. Actual API keys, tokens, and sensitive data are excluded.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |

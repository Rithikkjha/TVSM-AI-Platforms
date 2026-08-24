# API Specification Document — TVS Connect Web API

## 1. Overview

| Field | Value |
|-------|-------|
| Base URL | `https://{region-host}/api/` |
| Protocol | HTTPS (TLS 1.2+) |
| Format | JSON |
| Authentication | OAuth 2.0 Bearer Token |
| Rate Limiting | Yes (per-client throttling) |

---

## 2. Authentication

### 2.1 JWT Token Endpoint

```
POST /api/RegisterUser/RefreshJWTToken
Content-Type: application/x-www-form-urlencoded

--header 'Content-Type: application/json' \
  --header 'countryId: 203' \
  --header 'refreshToken: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbmFtZSI6Ijk4NTY0NTg3MDIiLCJuYW1laWQiOiIyNSIsImlzcyI6InNlbGYiLCJhdWQiOiJodHRwOi8vd3d3LmV4YW1wbGUuY29tIiwiZXhwIjoxNzk4MDYxMjcwLCJuYmYiOjE3ODIyOTMyNzB9.li17wxTG_5h8MQ1RHCQQWmiFJO3BzcKlKIP09Cvj18k' \
  --header 'accesstoken: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbmFtZSI6Ijk4NTY0NTg3MDIiLCJuYW1laWQiOiIyNSIsImlzcyI6InNlbGYiLCJhdWQiOiJodHRwOi8vd3d3LmV4YW1wbGUuY29tIiwiZXhwIjoxNzkwMTc3MjcwLCJuYmYiOjE3ODIyOTMyNzB9.8X2UiOJNhiN6gqBaCzMm2Iuszq47GB9m56jJ_XLLHtQ' \
  --header 'region: europe' \
```

**Request Body:**
``json
{
    "MobileNumber": "0000000000",
    "Email": "abc@gmail.com",
    "CountryCode": {{countryid}}
}
```

**Response:**
```json
{
	"UserId": 25,
	"FullName": "ABC",
	"MobileNumber": "9856325600",
	"Email": "abc@yopmail.com",
	"CityId": 11,
	"CityName": "Italy",
	"BloodGroup": "",
	"AllergicContent": "",
	"ProfileImagePath": "https://tvsconnectapi.tvsmotor.com/europe-assets/italy/profileimages/25092024034718_cropped8565901677251874990.jpg",
	"Token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbmFtZSI6ImFiQHlvcG1haWwuY29tIiwibmFtZWlkIjoiODQyNjkxIiwiaXNzIjoic2VsZiIsImF1ZCI6Imh0dHA6Ly93d3cuZXhhbXBsZS5jb20iLCJleHAiOjE4MTM4MjkyNjksIm5iZiI6MTc4MjI5MzI2OX0.1509xKKga24wrd1JuV8EW6tq1lT-uQ9toBPRGEw_rBg",
	"FacebookId": "",
	"GooglePlusId": "",
	"CrashAlertDate": "1900-01-01T00:00:00",
	"Addedvehiclecount": 0,
	"AccessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbmFtZSI6Ijk4NTY0NTg3MDIiLCJuYW1laWQiOiIyNSIsImlzcyI6InNlbGYiLCJhdWQiOiJodHRwOi8vd3d3LmV4YW1wbGUuY29tIiwiZXhwIjoxNzkwMTc3MjcwLCJuYmYiOjE3ODIyOTMyNzB9.8X2UiOJNhiN6gqBaCzMm2Iuszq47GB9m56jJ_XLLHtQ",
	"RefreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1bmlxdWVfbmFtZSI6Ijk4NTY0NTg3MDIiLCJuYW1laWQiOiIyNSIsImlzcyI6InNlbGYiLCJhdWQiOiJodHRwOi8vd3d3LmV4YW1wbGUuY29tIiwiZXhwIjoxNzk4MDYxMjcwLCJuYmYiOjE3ODIyOTMyNzB9.li17wxTG_5h8MQ1RHCQQWmiFJO3BzcKlKIP09Cvj18k"
   }
```

### 2.2 Authenticated Requests

All API calls (except login/register) require:
```
Authorization: Bearer {access_token}
```

### 2.3 Common Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `token` | Yes (post-login) | JWT token |
| `Content-Type` | Yes | `application/json` |
| `languagecode` | Optional | Language code (e.g., `en`, `fr`) |
| `countrycode` | Optional | Numeric country code |
| `devicetype` | Optional | `android` or `ios` |

---

## 3. Standard Response Format

All API responses follow this structure:

```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "Optional description",
    "Data": { }
}
```

### 3.1 Status Codes (in response body)

| StatusCode | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized |
| 404 | Not Found |
| 417 | Expectation Failed (caught exception) |
| 500 | Internal Server Error |

> Note: HTTP response status is always 200 OK. The actual status is in the response body `StatusCode` field.

---

## 4. API Endpoint List

### 4.1 Authentication & User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/UserLogin/Login` | Initiate login (sends OTP) |
| POST | `/api/UserLogin/Loginv1` | Login v1 (check user first) |
| POST | `/api/v3/userlogin/loginv3` | Login v3 (with ICE integration) |
| POST | `/api/UserLogin/VerifyLoginOtp` | Verify OTP and get token |
| POST | `/api/v3/userlogin/verifyloginotp` | Verify OTP v3 |
| GET | `/api/UserLogin/Logout` | Logout user |
| GET | `/api/UserLogin/deleteUser` | Delete user account |
| GET | `/api/UserLogin/getAppVersion` | Get latest app version info |

### 4.2 User Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/Profile/{action}` | Get user profile |
| POST | `/api/Profile/{action}` | Update user profile |
| POST | `/api/UserAddress/{action}` | Manage user addresses |
| POST | `/api/UserConsent/{action}` | Manage user consents (GDPR) |
| POST | `/api/UserSetting/{action}` | User app settings |

### 4.3 Vehicle Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Vehicle/{action}` | Vehicle operations |
| POST | `/api/VehicleAccess/{action}` | Vehicle access/sharing |
| GET | `/api/Vin/{action}` | VIN validation |
| POST | `/api/Registration/{action}` | Vehicle registration |
| POST | `/api/AlexaEnableVehicles/{action}` | Alexa-enabled vehicle config |

### 4.4 Ride & Telemetry

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Ride/{action}` | Ride data management |
| GET | `/api/RideCumulative/{action}` | Cumulative ride statistics |
| POST | `/api/Travel/{action}` | Travel/telemetry data |
| GET | `/api/RidingPattern/{action}` | Riding pattern analysis |
| GET | `/api/RidingTip/{action}` | Riding tips |
| POST | `/api/FavouriteRide/{action}` | Favourite rides |
| GET | `/api/MileageForVehicle/{action}` | Mileage tracking |

### 4.5 Location & Maps

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Location/{action}` | Location services |
| GET | `/api/LastLocationParked/{action}` | Last parked location |
| POST | `/api/Heremap/{action}` | HERE Maps integration |
| POST | `/api/Geofence/{action}` | Geofencing management |

### 4.6 Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Notification/{action}` | Push notifications |
| POST | `/api/HIBNotification/{action}` | HIB notifications |
| POST | `/api/SMSNotification/{action}` | SMS notification callbacks |

### 4.7 Dealer & Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/DealersNearYou/{action}` | Nearby dealer search |
| POST | `/api/Service/{action}` | Service booking |
| POST | `/api/TestRide/{action}` | Test ride booking |
| POST | `/api/BikeService/{action}` | Bike service management |
| POST | `/api/BreakDownAssistance/{action}` | Breakdown assistance |

### 4.8 Feedback & Surveys

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/FeedBack/{action}` | General feedback |
| POST | `/api/InAppFeedback/{action}` | In-app feedback |
| POST | `/api/CSIFeedback/{action}` | Customer Satisfaction Index |
| POST | `/api/NPSFeedback/{action}` | Net Promoter Score |
| POST | `/api/EVRating/{action}` | EV rating/nudge |
| POST | `/api/Survey/{action}` | Surveys |

### 4.9 Content & Information

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/FAQ/{action}` | FAQ content |
| GET | `/api/Home/{action}` | Home screen data |
| GET | `/api/News/{action}` | News feed |
| GET | `/api/Weather/{action}` | Weather data |
| GET | `/api/AQI/{action}` | Air Quality Index |
| GET | `/api/Cricket/{action}` | Cricket scores |
| GET | `/api/Football/{action}` | Football scores |
| GET | `/api/Tips/{action}` | Tips and guides |
| GET | `/api/UserGuide/{action}` | User guides |

### 4.10 Vehicle Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Tpms/{action}` | Tire Pressure Monitoring |
| POST | `/api/OTA/{action}` | Over-the-Air updates |
| POST | `/api/VoiceAssistant/{action}` | Voice assistant config |
| POST | `/api/UserVoiceCommand/{action}` | Voice commands |
| POST | `/api/Charging/{action}` | EV charging |
| POST | `/api/CustomizeScreen/{action}` | Dashboard customization |
| POST | `/api/Widget/{action}` | Widget configuration |

### 4.11 Enquiry & Lead Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Enquiry/{action}` | Product enquiries |
| POST | `/api/HLXEnquiry/{action}` | HLX enquiries |
| POST | `/api/WebEnquiry/{action}` | Web enquiries |
| POST | `/api/ContactUs/{action}` | Contact us submissions |
| POST | `/api/LeadStatus/{action}` | Lead status tracking |
| POST | `/api/LeadStatistics/{action}` | Lead analytics |
| POST | `/api/LaunchNotifyMe/{action}` | Launch notifications |

### 4.12 Administrative

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/Health/CheckHealth` | Health check endpoint |
| POST | `/api/MobileSetting/{action}` | Mobile app settings |
| POST | `/api/Admin/{action}` | Admin operations |
| GET | `/api/SasToken/{action}` | SAS token generation |
| POST | `/api/TPToken/{action}` | Third-party tokens |
| POST | `/api/Secret/{action}` | Client secret management |
| POST | `/api/IMEI/{action}` | IMEI management |
| POST | `/api/DeviceDetails/{action}` | Device details logging |

### 4.13 Finance & Commerce

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/Finance/{action}` | Finance/EMI info |
| POST | `/api/EMI/{action}` | EMI calculator |
| POST | `/api/Accessory/{action}` | Vehicle accessories |
| POST | `/api/BrandGetInTouch/{action}` | Brand contact |

### 4.14 Tracking Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/TrakNTell/{action}` | TrakNTell device ops |
| POST | `/api/CrashEmailAlert/{action}` | Crash detection alerts |

---

## 5. Detailed API Examples

### 5.1 Login (Send OTP)

```http
POST /api/UserLogin/Login
Content-Type: application/json
```

**Request:**
```json
{
    "MobileNumber": "9876543210",
    "Email": "",
    "FacebookId": "",
    "GoogleplusId": "",
    "AppleId": "",
    "CountryCode": 1,
    "otpLength": 4,
    "iosToken": "",
    "androidToken": "fcm_token_here"
}
```

**Success Response:**
```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "",
    "Data": {
        "MobileNumber": "9876543210"
    }
}
```

**Error Response (New User):**
```json
{
    "StatusCode": 404,
    "Message": "Success",
    "Description": "New User"
}
```

### 5.2 Verify OTP

```http
POST /api/UserLogin/VerifyLoginOtp
Content-Type: application/json
```

**Request:**
```json
{
    "MobileNumber": "9876543210",
    "OTP": "1234",
    "DeviceId": "device_uuid",
    "PublicKey": "rsa_public_key_base64"
}
```

**Success Response:**
```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "",
    "Data": {
        "UserId": 12345,
        "FullName": "John Doe",
        "MobileNumber": "9876543210",
        "Email": "john@example.com",
        "IsNewUser": false,
        "Token": "bearer_token_here",
        "RefreshToken": "refresh_token_here"
    }
}
```

**Error Response (Too Many Attempts):**
```json
{
    "StatusCode": 400,
    "Message": "Failure",
    "Description": "Too many failed attempts. Try again after 1 hour."
}
```

### 5.3 Get App Version

```http
GET /api/UserLogin/getAppVersion
Authorization: Bearer {token}
languagecode: en
countrycode: 1
```

**Response:**
```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "",
    "Data": {
        "Appversion": [
            {
                "Platform": "Android",
                "LatestVersion": "3.2.0",
                "MinimumVersion": "2.8.0",
                "ForceUpdate": true,
                "UpdateMessage": "Please update to continue"
            }
        ]
    }
}
```

### 5.4 Health Check

```http
GET /api/Health/CheckHealth
```

**Response:**
```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "Service is healthy"
}
```

### 5.5 Logout

```http
GET /api/UserLogin/Logout?userId=12345
Authorization: Bearer {token}
```

**Response:**
```json
{
    "StatusCode": 200,
    "Message": "Success",
    "Description": "Logout successfully."
}
```

---

## 6. Error Responses

### 6.1 Common Error Codes

| StatusCode | Message | Description | Cause |
|-----------|---------|-------------|-------|
| 400 | Failure | Empty fields found | Missing required fields |
| 400 | Failure | User already registered | Duplicate registration |
| 401 | Unauthorized | Token expired | Invalid/expired bearer token |
| 404 | Success | New User | User not found (registration needed) |
| 404 | Failure | Record not found | No data for request |
| 417 | Failure | Exception occurred | Server-side error |
| 500 | Failure | Internal server error | Unhandled exception |

### 6.2 Validation Errors

```json
{
    "StatusCode": 400,
    "Message": "Failure",
    "Description": "Invalid mobile number format"
}
```

### 6.3 Authentication Errors

```json
{
    "StatusCode": 401,
    "Message": "Failure",
    "Description": "Invalid or expired token"
}
```

---

## 7. Validation Rules

| Field | Rules |
|-------|-------|
| MobileNumber | Required for domestic login, numeric, country-specific format |
| Email | Required for international login, valid email format |
| OTP | Numeric, length as specified in otpLength parameter |
| CountryCode | Numeric, must exist in CountryMaster |
| FrameNumber | Alphanumeric, must exist in VehicleDetail master |
| UserId | Numeric, must be valid user |
| Token | Valid OAuth bearer token, not expired |
| DeviceId | Required for push notification registration |

---

## 8. Rate Limiting

| Configuration | Value |
|--------------|-------|
| Implementation | Custom `RateLimitingHandler` (DelegatingHandler) |
| Scope | Per-client (based on request identity) |
| Response on Limit | HTTP 429 Too Many Requests |
| OTP Attempts | Max 5 failed attempts, 1-hour lockout |

---

## 9. External API Dependencies

| External API | Used By | Purpose |
|-------------|---------|---------|
| HERE Maps Router API | `/api/Heremap/` | Route calculation |
| HERE Maps Image API | Ride service | Static route images |
| MapMyIndia Static Image | Ride service | Route images (India) |
| OpenWeatherMap OneCall | `/api/Weather/` | Weather data |
| OpenWeatherMap AQI | `/api/AQI/` | Air quality |
| TrakNTell Device API | `/api/TrakNTell/` | GPS tracking |
| P360 Platform API | Multiple | Connected vehicle data |
| TVS DMS API | `/api/Service/`, `/api/DealersNearYou/` | Dealer operations |
| TechPerspect API | `/api/Charging/` | EV charging stations |
| Bing News API | `/api/News/` | News content |
| Cricket Live Data API | `/api/Cricket/` | Cricket scores |
| Football API | `/api/Football/` | Football scores |
| Azure Notification Hubs | `/api/Notification/` | Push delivery |
| SMS APIs (Tata/Airtel/Plivo) | Login/OTP flows | OTP delivery |

---

## 10. Swagger Documentation

Swagger UI is available when enabled:
- **Configuration**: `swagger-enable` = `TRUE` in appSettings
- **URL**: `https://{host}/swagger`
- **Setup**: `App_Start/SwaggerConfig.cs`

---

## 11. API Versioning

The API uses URL-based versioning for newer endpoints:

| Version | Pattern | Example |
|---------|---------|---------|
| v1 (default) | `/api/{Controller}/{Action}` | `/api/UserLogin/Login` |
| v1 explicit | `/api/{Controller}/{Action}v1` | `/api/UserLogin/Loginv1` |
| v3 | `/api/v3/{controller}/{action}` | `/api/v3/userlogin/loginv3` |

---

## 12. CORS Configuration

| Setting | Value |
|---------|-------|
| Enabled | Yes (global) |
| Implementation | `config.EnableCors()` in WebApiConfig |
| Allowed Origins | Configured per environment |
| Allowed Methods | GET, POST, PUT, DELETE |
| Allowed Headers | Authorization, Content-Type, custom headers |

---

*This document provides API specifications suitable for client developers. Actual API keys, tokens, and credentials are not included.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |

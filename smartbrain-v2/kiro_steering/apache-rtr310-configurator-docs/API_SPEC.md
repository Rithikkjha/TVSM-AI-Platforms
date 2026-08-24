# API Specification Document - TVS Apache RTR 310 3D Configurator

## Overview

This document describes all API endpoints consumed by the TVS Apache RTR 310 3D Configurator frontend application. The application communicates with two primary backend services:

1. **TVS Connect API** — Authentication service (OTP-based login/registration)
2. **TVS Motor Web API** — Business operations (pricing, orders, content, asset URLs)

---

## Base URLs

| Environment | TVS Connect API (`LOGIN_URL`) | TVS Motor Web API (`API_BASE_URL`) |
|-------------|-------------------------------|-------------------------------------|
| Development | `https://dev-tvsconnectapi.tvsmotor.net/api` | `https://dev-www.tvsmotor.net/api` |
| UAT | `https://uat-tvsconnectapi.tvsmotor.net/api` | `https://uat-www.tvsmotor.net/api` |
| Production | `https://tvsconnectapi.tvsmotor.com/api` | `https://www.tvsmotor.com/api` |

---

## Authentication Requirements

- **Login/Registration endpoints**: No authentication required (public)
- **Business endpoints** (pricing, orders): Bearer token authentication via `Authorization` header
- **Token source**: Received from `/UserLogin/VerifyLoginOtp` response
- **Token transport**: `Authorization: Bearer {token}` header (added by Axios interceptor)

---

## API Endpoints

---

### 1. Request OTP (Login)

**Endpoint:** `POST {LOGIN_URL}/UserLogin/Loginv1`

**Description:** Sends an OTP to the registered mobile number for login.

**Authentication:** None

**Request Payload:**
```json
{
  "mobileNumber": "9876543210"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| mobileNumber | string | Yes | 10-digit numeric (`/^[0-9]{10}$/`) |

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Message": "OTP sent successfully"
}
```

**Error Response (404 - User not found):**
```json
{
  "StatusCode": 404,
  "Message": "User not registered"
}
```

**Client Handling:**
- 200: Start 90-second OTP timer, show OTP input
- 404: Show "New user, please register first" message

---

### 2. Verify Login OTP

**Endpoint:** `POST {LOGIN_URL}/UserLogin/VerifyLoginOtp`

**Description:** Verifies the OTP and returns authentication token + user data.

**Authentication:** None

**Request Payload:**
```json
{
  "mobileNumber": "9876543210",
  "otp": "123456"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| mobileNumber | string | Yes | 10-digit numeric |
| otp | string | Yes | Non-empty |

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Data": [
    {
      "Email": "user@example.com",
      "FullName": "John Doe",
      "Token": "eyJhbGciOiJIUz...",
      "UserId": 12345
    }
  ]
}
```

**Error Response:**
```json
{
  "StatusCode": 400,
  "Message": "Invalid OTP"
}
```

**Client Handling:**
- Success: Store user data in auth store, navigate to home
- Error: Show "Invalid OTP entered" message

---

### 3. Register User

**Endpoint:** `POST {LOGIN_URL}/RegisterUser/CreateUser`

**Description:** Registers a new user and sends verification OTP.

**Authentication:** None

**Request Payload:**
```json
{
  "fullName": "John Doe",
  "email": "john@example.com",
  "mobileNumber": "9876543210"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| fullName | string | Yes | Non-empty |
| email | string | Yes | Valid email format |
| mobileNumber | string | Yes | 10-digit numeric |

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Message": "OTP sent to mobile number"
}
```

**Error Response:**
```json
{
  "StatusCode": 400,
  "Message": "User already exists"
}
```

---

### 4. Verify Registration OTP

**Endpoint:** `POST {LOGIN_URL}/RegisterUser/VerifyOTP`

**Description:** Verifies the OTP sent during registration.

**Authentication:** None

**Request Payload:**
```json
{
  "mobileNumber": "9876543210",
  "otp": "123456"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| mobileNumber | string | Yes | 10-digit numeric |
| otp | string | Yes | Non-empty |

**Success Response (200):**
```json
{
  "StatusCode": 200,
  "Message": "Registration successful"
}
```

**Client Handling:**
- Success: Navigate to home page
- Error: Show "OTP verification failed" message

---

### 5. Get Vehicle Prices

**Endpoint:** `GET {API_BASE_URL}/Booking/LastestVehiclePricesDetails?vehicleCode=1161`

**Description:** Returns current vehicle prices for all color/kit combinations, grouped by state.

**Authentication:** Bearer token (via Axios interceptor)

**Query Parameters:**

| Parameter | Type | Required | Value |
|-----------|------|----------|-------|
| vehicleCode | string | Yes | `1161` (RTR 310) |

**Success Response (200):**
```json
{
  "data": [
    {
      "State": "Delhi",
      "PartId": "N71903402D",
      "Price": "236890",
      "VehicleName": "RTR-310",
      "ColorName": "Arsenal Black",
      "VariantName": "Base"
    },
    {
      "State": "Delhi",
      "PartId": "N71903502D",
      "Price": "254890",
      "VehicleName": "RTR-310",
      "ColorName": "Arsenal Black",
      "VariantName": "Dynamic"
    }
  ]
}
```

**Client Handling:**
- Filter by `State === "Delhi"`
- Cache in `useVehicleConfigStore.products[]`
- Look up price by matching `PartId`

---

### 6. Place Order

**Endpoint:** `POST {API_BASE_URL}/placeorder`

**Description:** Submits vehicle order and returns payment gateway redirect URL.

**Authentication:** Token included in payload body

**Request Payload:**
```json
{
  "OrderVehicle": 1,
  "OrderAccessories": 1,
  "Token": "eyJhbGciOiJIUz...",
  "SessionId": "session120210614123",
  "UserId": 12345,
  "Name": "John Doe",
  "Phone": "9876543210",
  "Email": "john@example.com",
  "CustomVehicleName": "NA",
  "VehicleCode": "NA",
  "VehicleName": "RTR-310",
  "VariantCode": 1161,
  "VariantName": "NA",
  "ColorCode": "NA",
  "ColorName": "NA",
  "PartId": "N71903502D",
  "City": "NA",
  "State": "NA",
  "TotalPrice": "NA",
  "VehiclePrice": "NA",
  "BTO": {
    "Status": false
  },
  "PreBooking": {
    "PaymentStatus": "False",
    "Phone": "9876543210",
    "IsBTOComplete": false,
    "DealerName": "",
    "DealerCode": "",
    "DealerContact": "",
    "DealerEmail": "",
    "DealerAddress": "",
    "Pincode": "",
    "City": "",
    "State": ""
  },
  "Price": {
    "ExShowroom": 236890,
    "AdditonalColorPrice": 0,
    "DynamicPackage": 18000,
    "DynamicProPackage": 28000
  },
  "AccessoriesData": [],
  "MerchandiseData": [],
  "AppProvider": ""
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| OrderVehicle | number | Yes | Always 1 |
| Token | string | Yes | User auth token |
| UserId | number | Yes | User ID from auth |
| Name | string | Yes | User's full name |
| Phone | string | Yes | User's mobile number |
| Email | string | Yes | User's email |
| VehicleName | string | Yes | Fixed: "RTR-310" |
| VariantCode | number | Yes | Fixed: 1161 |
| PartId | string | Yes | Resolved from color×kit matrix |
| Price | object | Yes | Pricing breakdown |
| Price.ExShowroom | number | Yes | Base vehicle price |
| Price.AdditonalColorPrice | number | Yes | Premium color surcharge (0 or 10000) |
| Price.DynamicPackage | number | Conditional | If Dynamic kit selected |
| Price.DynamicProPackage | number | Conditional | If Dynamic Pro kit selected |

**Success Response (200):**
```json
{
  "RedirectUrl": "https://payment-gateway.example.com/pay?orderId=abc123",
  "OrderId": "ORD-2025-001",
  "Status": "Pending"
}
```

**Client Handling:**
- Extract `RedirectUrl` from response
- Open in new tab: `window.open(RedirectUrl, "_blank")`

**Error Response:**
```json
{
  "StatusCode": 500,
  "Message": "Order placement failed"
}
```

---

### 7. Get Policy Content

**Endpoint:** `GET {API_BASE_URL}/Booking/PageContent`

**Description:** Fetches Terms & Conditions or Privacy Policy HTML content.

**Authentication:** None (public)

**Query Parameters:**

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| PageType | string | Yes | `tnc` or `privacy` |
| VehicleCode | string | Yes | `1161` |

**Sample Request:**
```
GET /Booking/PageContent?PageType=tnc&VehicleCode=1161
```

**Success Response (200):**
```json
{
  "Content": "<h1>Terms and Conditions</h1><p>By placing an order...</p>",
  "PageType": "tnc"
}
```

**Client Handling:**
- Render HTML content in PolicyPopup modal
- Error fallback: Show "Failed to load content" message

---

### 8. Get Model Chunk URLs (Headless)

**Endpoint:** `GET {API_BASE_URL}/Headless/Get`

**Description:** Returns signed Azure Blob Storage URLs for downloading 3D model chunks.

**Authentication:** None (the SAS tokens in the URLs provide access)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| api | string | Yes | `/api/BlobSas/GetRes?t=rtr310` |
| _t | number | No | Cache-busting timestamp |

**Request Headers:**
```
Accept: */*
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
```

**Success Response (200):**
```json
{
  "Message": "[\"https://storage.blob.core.windows.net/container/chunk-0?sv=...&sig=...\", \"https://storage.blob.core.windows.net/container/chunk-1?sv=...&sig=...\"]",
  "Success": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| Message | string (JSON) | JSON-encoded array of SAS-token signed URLs |
| Success | boolean | Operation success indicator |

**Client Handling:**
- Parse `Message` as JSON to get URL array
- Download each URL as ArrayBuffer (binary)
- Combine in order to reconstruct GLB file

---

## Error Responses (Global)

### HTTP Status Codes

| Code | Meaning | Client Behavior |
|------|---------|-----------------|
| 200 | Success | Process response |
| 201 | Created | Process response |
| 400 | Bad Request | Show validation error |
| 401 | Unauthorized | Log warning (token expired) |
| 404 | Not Found | Context-specific message |
| 500 | Server Error | Show generic error |

### Axios Error Shape

```typescript
// Interceptor-rejected error
{
  message: "API call failed with statusCode: 400",
  statusCode: 400,
  data: { /* API response body */ }
}
```

---

## Validation Rules Summary

| Endpoint | Field | Rule |
|----------|-------|------|
| Login/Register | mobileNumber | `/^[0-9]{10}$/` (exactly 10 digits) |
| Login/Register | otp | Non-empty string |
| Register | email | `/^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/` |
| Register | fullName | Non-empty string |
| Place Order | T&C Checkbox | Must be checked |
| Place Order | PartId | Must resolve from color×kit matrix |

---

## Rate Limits

No explicit rate limiting is documented in the frontend code. Rate limiting, if any, is managed server-side by the TVS Motor API gateway.

---

## External API Dependencies

| Dependency | Protocol | Purpose |
|------------|----------|---------|
| Azure Blob Storage | HTTPS (SAS-gated) | 3D model chunk download |
| Payment Gateway | HTTPS (Redirect) | Payment processing |
| TVS Connect API | HTTPS REST | Authentication |
| TVS Motor Web API | HTTPS REST | Business operations |

---

## CORS Configuration

### Development (Localhost)
- Vite proxy configuration handles CORS:
  - `/api/*` → proxied to TVS backend
  - `/blob-proxy/*` → proxied to Azure Blob Storage

### Production
- CORS headers configured server-side on TVS APIs
- Azure Blob Storage accessed directly (SAS tokens bypass CORS for authorized requests)

---

## Timeout Configuration

| Service | Timeout | Retry |
|---------|---------|-------|
| Auth API (axiosInstance) | 10,000ms | No |
| Product API (placeOrderAxios) | 10,000ms | No |
| Model chunks (fetch) | Browser default | 3 retries, 500ms×attempt backoff |

---

*This document is generated for API integration reference. No secrets, credentials, or SAS tokens are exposed.*

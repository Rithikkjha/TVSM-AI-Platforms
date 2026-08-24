# API Specification Document

## TVS Apache RR310 BTO Configurator — API Reference

---

## Overview

This document defines all API endpoints consumed by the RR310 3D Configurator application. The configurator is a client-side application that communicates with TVS Motor backend services, Azure Blob Storage, and Firebase Cloud Functions.

All APIs are called from the browser (client-side JavaScript) using the `fetch()` API.

---

## Base URLs

| Environment | Base URL | Purpose |
|-------------|----------|---------|
| Production | `https://www.tvsmotor.com` | Primary API gateway |
| UAT / Pre-prod | `https://uat-www.tvsmotor.net` | Testing/staging |
| Firebase (Legacy) | `https://us-central1-tvs-configurator.cloudfunctions.net` | User config persistence (partially deprecated) |
| Azure Blob | Dynamic (returned by API) | 3D model chunk storage |

---

## Authentication Requirements

| Method | Details |
|--------|---------|
| Type | Token-based (passed via URL parameter from parent website) |
| Token Source | TVS Motor website login → `authToken` URL param passed to iframe |
| User Identification | `userId` URL parameter + `configuredUserId` variable |
| Session | No persistent session; each API call includes `userid` in body |
| Guest Access | `userid = "AvataarGuest"`, limited API access (no save/order) |

**Authentication Flow:**
```
TVS Website Login → authToken generated → passed to iframe URL params
→ Configurator extracts authToken, userId → includes userId in API request bodies
```

> Note: There is no OAuth token refresh. If the token expires, the user must re-authenticate on the parent TVS website.

---

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: TVS RR310 BTO Configurator API
  description: APIs consumed by the RR310 3D motorcycle configurator
  version: 1.0.16
  contact:
    name: TVS D2C Engineering
servers:
  - url: https://www.tvsmotor.com
    description: Production
  - url: https://uat-www.tvsmotor.net
    description: UAT / Pre-production

paths:
  /api/Headless/Post:
    post:
      summary: Generic API Gateway (Proxy)
      description: |
        All internal microservice calls are routed through this single gateway endpoint.
        The `api` field in the request body specifies the actual internal endpoint.
      operationId: headlessPost
      tags:
        - Gateway
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - api
                - jsonRequest
              properties:
                api:
                  type: string
                  description: Internal API path with timestamp cache buster
                  example: "/api/WebSiteUserConfiguration/WebSiteUserConfigurations?t=1718400000000"
                jsonRequest:
                  type: string
                  description: JSON-encoded string of the actual request payload
                  example: '{"userid":"USER123","modelName":"RR310"}'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  Success:
                    type: boolean
                  Message:
                    type: string
                    description: JSON-encoded response data (must be parsed)
        '400':
          description: Bad request - invalid payload
        '401':
          description: Unauthorized - invalid or expired session
        '500':
          description: Internal server error

  /api/Headless/Get:
    get:
      summary: Generic API Gateway (GET Proxy)
      description: Routes GET requests to internal services. Used for 3D model chunk URL retrieval.
      operationId: headlessGet
      tags:
        - Gateway
        - 3D Assets
      parameters:
        - name: api
          in: query
          required: true
          schema:
            type: string
          example: "/api/BlobSas/GetRes?t=rr310"
      responses:
        '200':
          description: Successful response with signed URLs
          content:
            application/json:
              schema:
                type: object
                properties:
                  Message:
                    type: string
                    description: JSON array of signed blob URLs (as string)
                    example: '["https://blob.core.windows.net/chunk1.bin","https://blob.core.windows.net/chunk2.bin"]'
        '500':
          description: Internal server error

  /api/placeorderforavataar:
    post:
      summary: Place BTO Order
      description: |
        Submits the configured motorcycle order to the TVS booking system.
        Returns a redirect URL for the payment flow.
      operationId: placeOrder
      tags:
        - Orders
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PlaceOrderRequest'
      responses:
        '200':
          description: Order placed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PlaceOrderResponse'
        '400':
          description: Invalid order data
        '401':
          description: User not authenticated
        '409':
          description: Booking limit reached
        '500':
          description: Server error during order placement

  /api/Booking/GetVehicleOrderCountFromVehicleCode:
    get:
      summary: Get Booking Availability
      description: Returns total allowed bookings and current successful bookings for a vehicle code.
      operationId: getVehicleOrderCount
      tags:
        - Booking
      parameters:
        - name: vehicleCode
          in: query
          required: true
          schema:
            type: integer
          example: 101
      responses:
        '200':
          description: Booking count data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VehicleOrderCountResponse'

components:
  schemas:
    SaveConfigurationRequest:
      type: object
      required:
        - userid
        - modelName
        - currentConfigNo
      properties:
        userid:
          type: string
          description: TVS user identifier
          example: "USER123"
        config:
          type: string
          description: JSON-encoded configuration object (or empty string for delete)
          example: '{"ConfigurationName":"My RR310","FavouriteNumber":"24","PartId":"N71904208F","configurationNumber":"0"}'
        isBuyNowClicked:
          type: boolean
          default: false
        isSaveClicked:
          type: boolean
          default: true
        currentConfigNo:
          type: integer
          description: Save slot index (0-4)
          minimum: 0
          maximum: 4
          example: 0
        modelName:
          type: string
          enum: ["RR310"]
          example: "RR310"

    GetConfigurationsRequest:
      type: object
      required:
        - userid
        - modelName
      properties:
        userid:
          type: string
          example: "USER123"
        modelName:
          type: string
          enum: ["RR310"]

    GetConfigurationsResponse:
      type: object
      properties:
        Success:
          type: boolean
          example: true
        Message:
          type: string
          description: JSON array of configuration entries
          example: '[{"Config":"{...}","CurrentConfigNo":0,"IsBuyNowClicked":false,"IsSaveClicked":true,"ModelName":"RR310"}]'

    PlaceOrderRequest:
      type: object
      required:
        - SessionId
        - UserId
        - CustomVehicleName
        - PartId
        - Price
        - TotalPrice
      properties:
        SessionId:
          type: string
          description: Client session identifier
          example: "session1"
        UserId:
          type: string
          description: Authenticated user ID
          example: "USER123"
        CustomVehicleName:
          type: string
          description: User-given name for configuration
          example: "Apache RR310"
        PartId:
          type: string
          description: TVS part identifier for the variant
          example: "N71904208F"
        Price:
          $ref: '#/components/schemas/PriceBreakdown'
        TotalPrice:
          type: string
          description: Total price as string (no formatting)
          example: "293290"
        Name:
          type: string
          example: "John Doe"
        Phone:
          type: string
          pattern: '^\d{10}$'
          example: "9876543210"
        Email:
          type: string
          format: email
          example: "user@example.com"
        VehicleCode:
          type: string
          example: "0"
        VehicleName:
          type: string
          example: "NA"
        VariantCode:
          type: string
          example: "NA"
        VariantName:
          type: string
          example: "NA"
        ColorCode:
          type: string
          example: "NA"
        ColorName:
          type: string
          example: "NA"
        City:
          type: string
          example: "NA"

    PlaceOrderResponse:
      type: object
      properties:
        RedirectUrl:
          type: string
          format: uri
          description: Payment gateway URL for order completion
          example: "https://www.tvsmotor.com/payment/checkout?orderId=12345"

    PriceBreakdown:
      type: object
      properties:
        RacePackage:
          type: string
          example: "0"
        total:
          type: string
          example: "293290"
        Base:
          type: string
          example: "276690"
        ExShowroom:
          type: string
          example: "276690"
        DynamicPackage:
          type: string
          example: "16600"
        DynamicProPackage:
          type: string
          example: "0"
        AlloyWheelColor:
          type: string
          example: "0"
        SpecialEditionColor:
          type: string
          example: "0"
        FavouriteNumber:
          type: string
          description: User's selected race number (2 digits)
          example: "24"

    VehicleOrderCountResponse:
      type: object
      properties:
        MaxBooking:
          type: string
          description: Total allowed bookings
          example: "500"
        SuccessRecord:
          type: string
          description: Currently successful bookings
          example: "450"

    ConfigurationEntry:
      type: object
      properties:
        ConfigurationName:
          type: string
          maxLength: 10
          example: "My RR310"
        PartId:
          type: string
          example: "N71904208F"
        FavouriteNumber:
          type: string
          pattern: '^\d{2}$'
          example: "24"
        configurationNumber:
          type: string
          example: "0"
        currentConfigNo:
          type: integer
          example: 0
        isLastConfig:
          type: boolean
          example: true
        modelName:
          type: string
          example: "RR310"
```

---

## Detailed API Endpoint Reference

---

### API 1: Save User Configuration

Persists the user's motorcycle configuration to the TVS backend.

| Property | Value |
|----------|-------|
| **URL** | `POST https://www.tvsmotor.com/api/Headless/Post` |
| **Internal Route** | `/api/WebSiteUserConfiguration/WebSiteUserConfigurations` |
| **Auth Required** | Yes (userId in body) |
| **Idempotent** | Yes (upsert by userId + currentConfigNo) |

#### Request

```json
{
  "api": "/api/WebSiteUserConfiguration/WebSiteUserConfigurations?t=1718400000000",
  "jsonRequest": "{\"userid\":\"USER123\",\"config\":\"{\\\"ConfigurationName\\\":\\\"My RR310\\\",\\\"FavouriteNumber\\\":\\\"24\\\",\\\"PartId\\\":\\\"N71904208F\\\",\\\"configurationNumber\\\":\\\"0\\\",\\\"currentConfigNo\\\":0,\\\"isLastConfig\\\":true,\\\"modelName\\\":\\\"RR310\\\"}\",\"isBuyNowClicked\":false,\"isSaveClicked\":true,\"currentConfigNo\":0,\"modelName\":\"RR310\"}"
}
```

#### Headers

```
Content-Type: application/json; charset=UTF-8
```

#### Response (200 OK)

```json
{
  "Success": true,
  "Message": "Configuration saved"
}
```

#### Validation Rules
- `userid` must be non-empty string
- `currentConfigNo` must be integer 0-4 (max 5 save slots)
- `config` must be valid JSON string or empty string (for deletion)
- `modelName` must be "RR310"
- `ConfigurationName` max 10 characters (enforced client-side)

#### Error Responses

| Status | Scenario |
|--------|----------|
| 400 | Invalid JSON in `jsonRequest` |
| 401 | User session expired |
| 500 | Database write failure |

---

### API 2: Get User Configurations

Retrieves all saved configurations for a user.

| Property | Value |
|----------|-------|
| **URL** | `POST https://www.tvsmotor.com/api/Headless/Post` |
| **Internal Route** | `/api/WebSiteUserConfiguration/GetWebSiteUserConfigurations` |
| **Auth Required** | Yes (userId in body) |

#### Request

```json
{
  "api": "/api/WebSiteUserConfiguration/GetWebSiteUserConfigurations?t=1718400000000",
  "jsonRequest": "{\"userid\":\"USER123\",\"modelName\":\"RR310\"}"
}
```

#### Response (200 OK)

```json
{
  "Success": true,
  "Message": "[{\"Config\":\"{\\\"ConfigurationName\\\":\\\"My RR310\\\",\\\"FavouriteNumber\\\":\\\"24\\\",\\\"PartId\\\":\\\"N71904208F\\\",\\\"configurationNumber\\\":\\\"0\\\"}\",\"CurrentConfigNo\":0,\"IsBuyNowClicked\":false,\"IsSaveClicked\":true,\"ModelName\":\"RR310\"}]"
}
```

#### Response Parsing Logic

```javascript
const result = await response.json();
const parsedConfigs = JSON.parse(result.Message); // Array of entries

for (const entry of parsedConfigs) {
    let configObj = JSON.parse(entry.Config);
    // Handle wrapped format: {"0": {...}} → extract inner object
    if (Object.keys(configObj).length === 1 && Object.keys(configObj)[0] === "0") {
        configObj = configObj["0"];
    }
    configObj.currentConfigNo = entry.CurrentConfigNo;
    configObj.isLastConfig = entry.IsBuyNowClicked || entry.IsSaveClicked;
    configObj.modelName = entry.ModelName;
}
```

#### Error Responses

| Status | Scenario |
|--------|----------|
| 200 + `Success: false` | No configurations found |
| 200 + `Message: null` | Empty result |
| 401 | Unauthorized |
| 500 | Server error |

---

### API 3: Place BTO Order

Submits the finalized motorcycle order to the TVS booking system.

| Property | Value |
|----------|-------|
| **URL** | `POST https://uat-www.tvsmotor.net/api/placeorderforavataar` |
| **Production URL** | `POST https://www.tvsmotor.com/api/placeorderforavataar` |
| **Auth Required** | Yes (UserId in body) |
| **Idempotent** | No (creates new order each call) |

#### Request

```json
{
  "SessionId": "session1",
  "UserId": "USER123",
  "CustomVehicleName": "Apache RR310",
  "PartId": "N71904208F",
  "Price": {
    "RacePackage": "0",
    "total": "293290",
    "Base": "276690",
    "ExShowroom": "276690",
    "DynamicPackage": "16600",
    "DynamicProPackage": "0",
    "AlloyWheelColor": "0",
    "SpecialEditionColor": "0",
    "FavouriteNumber": "24"
  },
  "TotalPrice": "293290",
  "Name": "John Doe",
  "Phone": "9876543210",
  "Email": "user@example.com",
  "VehicleCode": "0",
  "VehicleName": "NA",
  "VariantCode": "NA",
  "VariantName": "NA",
  "ColorCode": "NA",
  "ColorName": "NA",
  "City": "NA"
}
```

#### Response (200 OK)

```json
{
  "RedirectUrl": "https://www.tvsmotor.com/payment/checkout?orderId=12345&token=abc"
}
```

#### Post-Response Behavior

```javascript
if (data["RedirectUrl"] != null) {
    // Notify parent TVS website frame
    window.parent.postMessage(data["RedirectUrl"], "https://www.tvsmotor.com");
    // Navigate parent to payment page
    window.parent.location.href = data["RedirectUrl"];
}
```

#### Validation Rules
- `UserId` must be authenticated (non-guest)
- `PartId` must match a valid configuration variant
- `TotalPrice` must match sum of Price components (server validates)
- Terms & Conditions must be accepted (client-side gate: `tncAccepted = true`)
- User must not have existing active order (`isBuyNowClicked` check)

#### Error Responses

| Status | Scenario |
|--------|----------|
| 400 | Invalid PartId or price mismatch |
| 401 | User not authenticated |
| 409 | Booking limit exceeded (MaxBooking reached) |
| 500 | Payment gateway unavailable |

---

### API 4: Get Vehicle Booking Count

Checks remaining booking availability for the RR310.

| Property | Value |
|----------|-------|
| **URL** | `GET https://www.tvsmotor.com/api/Booking/GetVehicleOrderCountFromVehicleCode` |
| **Auth Required** | No |
| **Cache** | Browser default caching |

#### Request

```
GET /api/Booking/GetVehicleOrderCountFromVehicleCode?vehicleCode=101
```

#### Response (200 OK)

```json
{
  "MaxBooking": "500",
  "SuccessRecord": "450"
}
```

#### Business Logic

```javascript
totalAvailableBooking = parseInt(data["MaxBooking"]) - parseInt(data["SuccessRecord"]);
// If totalAvailableBooking <= 0, show "bookingalert" (booking full)
```

---

### API 5: Get 3D Model Chunk URLs

Retrieves signed Azure Blob Storage URLs for the split GLB model chunks.

| Property | Value |
|----------|-------|
| **URL** | `GET https://uat-www.tvsmotor.net/api/Headless/Get?api=/api/BlobSas/GetRes?t=rr310` |
| **Auth Required** | No |
| **Cache** | `cache: 'no-store'` (always fresh) |

#### Request

```
GET /api/Headless/Get?api=/api/BlobSas/GetRes?t=rr310
```

#### Response (200 OK)

```json
{
  "Message": "[\"https://tvsblob.blob.core.windows.net/rr310/chunk_001.bin?sv=2022-11-02&se=...\",\"https://tvsblob.blob.core.windows.net/rr310/chunk_002.bin?sv=2022-11-02&se=...\",\"https://tvsblob.blob.core.windows.net/rr310/chunk_003.bin?sv=2022-11-02&se=...\"]"
}
```

#### Processing Flow

```javascript
// 1. Parse chunk URLs from response
const urls = JSON.parse(json.Message);

// 2. Download all chunks in parallel
const buffers = await Promise.all(urls.map(url => 
    fetch(url, { cache: 'no-store' }).then(r => r.arrayBuffer())
));

// 3. Concatenate into single ArrayBuffer
const total = buffers.reduce((s, b) => s + b.byteLength, 0);
const merged = new Uint8Array(total);
let offset = 0;
buffers.forEach(b => { merged.set(new Uint8Array(b), offset); offset += b.byteLength; });

// 4. Validate as GLB (magic: 0x46546C67, version: 2, length matches)
if (!validateGLB(merged.buffer)) throw new Error('Invalid GLB');

// 5. Parse with THREE.GLTFLoader
loader.parse(merged.buffer, '', onLoad, onError);
```

#### Error Responses

| Status | Scenario |
|--------|----------|
| 200 + invalid `Message` | API format change, fallback to local GLB |
| 403 | Expired SAS token on blob URLs |
| 404 | Model chunks not found |
| 500 | Azure storage unavailable |

---

### API 6: Firebase — Save Configuration (Legacy)

> **Status: Partially deprecated** — Being replaced by TVS Headless API

| Property | Value |
|----------|-------|
| **URL** | `POST https://us-central1-tvs-configurator.cloudfunctions.net/SaveConfiguration` |
| **Auth Required** | Yes (userid in body) |

#### Request

```json
{
  "userid": "USER123",
  "config": { ... },
  "currentConfigNo": "0"
}
```

#### Response (200 OK)

```json
{
  "status": "success"
}
```

---

### API 7: Firebase — Record Order Placement (Legacy)

> **Status: Still in use** for order tracking alongside TVS Booking API

| Property | Value |
|----------|-------|
| **URL** | `POST https://us-central1-tvs-configurator.cloudfunctions.net/UserPlacedOrder` |
| **Auth Required** | Yes (userid in body) |

#### Request

```json
{
  "userid": "USER123",
  "buynow": true
}
```

#### Response (200 OK)

```json
{
  "status": "success"
}
```

---

### API 8: Firebase — Get User Details (Legacy)

> **Status: Partially deprecated** — Used for checking prior order status

| Property | Value |
|----------|-------|
| **URL** | `POST https://us-central1-tvs-configurator.cloudfunctions.net/GetUserDetails` |
| **Auth Required** | Yes (userid in body) |

#### Request

```json
{
  "userid": "USER123"
}
```

#### Response (200 OK)

```json
{
  "userId": "USER123",
  "isBuyNowClicked": false,
  "configData": {
    "configurationNumber": "0",
    "FavoriteNumber": "24"
  }
}
```

---

## Authentication Redirect URL

When a guest user attempts to save/order, they are redirected to the TVS login page:

```
https://uat-www.tvsmotor.net/account/login
  ?authtoken={authToken}
  &returnurl={parentUrl}
  /?oldUserId={userid}
  &saveConfiguration={saveFlag}
  &configurationNo={currentConfigNo}
  &favouriteNo={currentRaceNo}
```

**Parameters:**

| Param | Source | Description |
|-------|--------|-------------|
| `authtoken` | URL param from parent | Current auth token |
| `returnurl` | `parentUrl` variable | Page to return after login |
| `oldUserId` | `userid` variable | Guest user ID to migrate data |
| `saveConfiguration` | Boolean | Whether save was triggered |
| `configurationNo` | `skuSchema.globalVariables.currentConfigurationNo` | Active variant |
| `favouriteNo` | `skuSchema.globalVariables.currentRaceNo` | Selected race number |

---

## Rate Limits

| API | Known Rate Limits | Notes |
|-----|-------------------|-------|
| TVS Headless API | Not documented | Standard web API; likely behind WAF/CDN |
| Firebase Cloud Functions | GCP free tier: 125K/month | Auto-scales on paid plan |
| Azure Blob Storage | 20,000 requests/sec/storage account | Effectively unlimited for this use case |
| Google Analytics | 500 hits/session | GA4 sampling applies at high volumes |

> **Client-side throttling:** The configurator has no explicit client-side rate limiting or retry logic. The "Place Order" button uses a 500ms debounce (`blockClick` flag) to prevent double-submission.

---

## External API Dependencies

| Dependency | URL Pattern | Purpose | Failure Impact |
|------------|-------------|---------|----------------|
| Google Draco Decoder | `https://www.gstatic.com/draco/v1/decoders/` | 3D mesh decompression | Model won't render |
| Google Fonts | `https://fonts.googleapis.com/css2` | Typography | Fallback fonts used |
| Google Model Viewer | `https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js` | AR on mobile | AR feature unavailable |
| jQuery CDN | `https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js` | DOM manipulation | App won't initialize |
| QRCode Generator | `https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js` | QR for AR sharing | QR feature unavailable |
| Google Tag Manager | `https://www.googletagmanager.com/gtm.js?id=GTM-KD53L7` | Analytics tags | Analytics disabled |
| Google Analytics | `https://www.googletagmanager.com/gtag/js?id=G-9QYYD82JSC` | Event tracking | Tracking disabled |

---

## Cache Busting Strategy

All internal API calls use a timestamp parameter to prevent caching:

```javascript
function withTimestamp(apiUrl) {
    const separator = apiUrl.includes("?") ? "&" : "?";
    return `${apiUrl}${separator}t=${Date.now()}`;
}
```

**Example:** `/api/WebSiteUserConfiguration/GetWebSiteUserConfigurations?t=1718400000000`

For 3D model chunks: `cache: 'no-store'` header ensures fresh fetch.

---

## Request/Response Headers

### All Outgoing Requests

```http
Content-Type: application/json; charset=UTF-8
```

### CORS Configuration

```javascript
{
  method: "POST",
  mode: "cors",
  headers: { "Content-Type": "application/json; charset=UTF-8" },
  body: JSON.stringify(data)
}
```

### For Blob Chunk Fetches

```javascript
{
  method: "GET",
  headers: { "Accept": "*/*" },
  cache: "no-store"
}
```

---

## Error Handling Summary

| Error Type | Client Behavior | User Impact |
|------------|----------------|-------------|
| Network failure (fetch throws) | `.catch()` logs to console | Silent failure; user can retry |
| HTTP 4xx/5xx | Checked via `response.ok` or `response.status` | No explicit user notification |
| Invalid JSON response | `JSON.parse()` in try/catch | Logged as warning; skipped |
| `Success: false` in response | Logged; early return | Feature silently unavailable |
| GLB validation failure | Throws error in `_0xb2()` | 3D model doesn't load |
| Timeout | No custom timeout configured | Browser default (~30-60s) |

> **Note:** The application lacks comprehensive error recovery UX. Most failures result in silent degradation rather than user-visible error messages.

---

## Part ID Reference

Each configuration variant has a unique Part ID used in order placement:

| Variant | PartId |
|---------|--------|
| Dynamic Kit + Racing Red + Black Alloy | `N71904208F` |
| Dynamic Kit + Titanium Black + Black Alloy | `N7190420LH` |
| Dynamic Kit + Titanium Black + Red Alloy | *(see configmaster)* |
| Dynamic Pro + Racing Red + Black Alloy | *(see configmaster)* |
| Race Kit + Sepang Blue | *(see configmaster)* |

> Full Part ID mapping is in `configmaster_tvs_preprod_new.js` → `ConfigurationDetails[N].PartId`

---

## Sample Integration Code

### Save Configuration — Complete Flow

```javascript
async function saveConfig(userId, configName, raceNo, partId, configNo) {
    const payload = {
        api: `/api/WebSiteUserConfiguration/WebSiteUserConfigurations?t=${Date.now()}`,
        jsonRequest: JSON.stringify({
            userid: userId,
            config: JSON.stringify({
                ConfigurationName: configName,    // max 10 chars
                FavouriteNumber: raceNo,          // "00" to "99"
                PartId: partId,                   // e.g., "N71904208F"
                configurationNumber: "0",
                currentConfigNo: configNo,
                isLastConfig: true,
                modelName: "RR310"
            }),
            isBuyNowClicked: false,
            isSaveClicked: true,
            currentConfigNo: configNo,
            modelName: "RR310"
        })
    };

    const response = await fetch("https://www.tvsmotor.com/api/Headless/Post", {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=UTF-8" },
        body: JSON.stringify(payload),
        mode: "cors"
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}
```

### Load Configurations — Complete Flow

```javascript
async function loadConfigs(userId) {
    const payload = {
        api: `/api/WebSiteUserConfiguration/GetWebSiteUserConfigurations?t=${Date.now()}`,
        jsonRequest: JSON.stringify({
            userid: userId,
            modelName: "RR310"
        })
    };

    const response = await fetch("https://www.tvsmotor.com/api/Headless/Post", {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=UTF-8" },
        body: JSON.stringify(payload),
        mode: "cors"
    });

    const result = await response.json();
    if (!result.Success || !result.Message) return [];

    const entries = JSON.parse(result.Message);
    return entries.map(entry => {
        let config = JSON.parse(entry.Config);
        // Unwrap {"0": {...}} format if present
        if (Object.keys(config).length === 1 && config["0"]) {
            config = config["0"];
        }
        return { ...config, slot: entry.CurrentConfigNo };
    });
}
```

### Place Order — Complete Flow

```javascript
async function placeOrder(userId, sessionId, vehicleName, configDetails, raceNo) {
    const orderData = {
        SessionId: sessionId,
        UserId: userId,
        CustomVehicleName: vehicleName,
        PartId: configDetails.PartId,
        Price: { ...configDetails.priceAPI, FavouriteNumber: raceNo },
        TotalPrice: configDetails.priceAPI.total,
        Name: "User Name",       // From TVS user profile
        Phone: "9876543210",     // From TVS user profile
        Email: "user@email.com", // From TVS user profile
        VehicleCode: "0",
        VehicleName: "NA",
        VariantCode: "NA",
        VariantName: "NA",
        ColorCode: "NA",
        ColorName: "NA",
        City: "NA"
    };

    const response = await fetch("https://www.tvsmotor.com/api/placeorderforavataar", {
        method: "POST",
        headers: { "content-type": "application/json; charset=UTF-8" },
        body: JSON.stringify(orderData),
        mode: "cors"
    });

    if (response.status !== 200) throw new Error(`Order failed: ${response.status}`);
    
    const data = await response.json();
    if (data.RedirectUrl) {
        // Redirect parent frame to payment
        window.parent.postMessage(data.RedirectUrl, "https://www.tvsmotor.com");
        window.parent.location.href = data.RedirectUrl;
    }
}
```

---

*Document generated: June 2026 | Version: 1.0 | For external engineering vendor integration*

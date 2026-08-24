# TVSM Marketplace Service — API Specification

> Companion to `docs/openapi.yaml`. The OpenAPI YAML is the canonical machine-readable contract; this document captures the cross-cutting concerns (auth flow, rate limits, external dependencies, sample payloads) that the YAML format alone doesn't carry well.
>
> All endpoints are exposed under context-path `/marketplace`. Confidential business logic, exact webhook secrets, tenant URLs, and credentials are intentionally excluded.

## 1. Endpoint List (with HTTP methods)

| # | Method | Path | Tag | Auth | Notes |
|---|--------|------|-----|------|-------|
| 1 | GET    | `/v1/order/list` | Orders | APIM Bearer | Paginated |
| 2 | GET    | `/v1/order/{orderId}` | Orders | APIM Bearer | Aggregated detail (Lead/Booking/Marketplace shipment included best-effort) |
| 3 | GET    | `/v1/order/process/{marketplace}` | Orders | APIM Bearer | Async batch |
| 4 | PUT    | `/v1/order/{marketplace}/marketplace-status?action=refresh` | Orders | APIM Bearer | Async sync |
| 5 | GET    | `/v1/order/{marketplace}/cancellation-discrepancies?action=notify` | Orders | APIM Bearer | Async notify |
| 6 | POST   | `/v1/products/upsert` | Products | APIM Bearer | Bulk upsert |
| 7 | POST   | `/v1/products/{marketplace}/upsert` | Products | APIM Bearer | Bulk upsert per marketplace |
| 8 | POST   | `/v1/dealer-refresh-token/upsert` | DealerTokens | APIM Bearer | Bulk upsert |
| 9 | POST   | `/webhook/flipkart/order-management/notifications-receiver/dealer/common` | FlipkartWebhook | Flipkart-signed | Hash-validated |
| 10 | GET    | `/test/flipkart/token/generate` | Ops | APIM Bearer | Pre-warm dealer tokens |
| 11 | GET    | `/v1/test/health` | Ops | APIM Bearer | Diagnostic |
| 12 | GET    | `/v1/test/hello` | Ops | APIM Bearer | APIM passthrough echo |
| 13 | POST   | `/v1/test/sendVehiclePriceDataToEcommerceClients` | Ops | APIM Bearer | Manual fan-out |
| 14 | GET    | `/v1/test/start-bulk-price-update-flipkart` | Ops | APIM Bearer | Async bulk reconciliation |
| 15 | GET    | `/v1/test/processOrderAsync?orderId=…` | Ops | APIM Bearer | Replay |
| 16 | GET    | `/v1/test/moveOrderForwardOneStep?orderId=…` | Ops | APIM Bearer | Single transition |
| 17 | DELETE | `/v1/test/cache/{cacheName}/{key}` | Ops | APIM Bearer | Evict cache |
| 18 | GET    | `/v1/test/service-bus/status` | ServiceBus | APIM Bearer | Health of SB processors |
| 19 | GET    | `/v1/test/service-bus/start-receiver?receiverId=…` | ServiceBus | APIM Bearer | Start a SB processor |
| 20 | GET    | `/v1/test/service-bus/stop-receiver?receiverId=…` | ServiceBus | APIM Bearer | Stop a SB processor |

## 2. Authentication

Two distinct schemes apply:

### 2.1 Internal callers → Marketplace Service (via APIM)

- All endpoints under `/v1/**` and `/test/**` are fronted by Azure API Management.
- Callers must present a bearer token issued by Azure AD B2C using the `client_credentials` grant.
- For some downstream paths (e.g. those that subsequently call the Booking service), APIM additionally enforces an `Ocp-Apim-Subscription-Key` header. The Marketplace Service does not validate this header itself.
- The Marketplace Service does not implement role-based authorisation; APIM is the perimeter.

### 2.2 Flipkart webhook → Marketplace Service

- `POST /webhook/flipkart/order-management/notifications-receiver/dealer/common`
- Headers required: `X-Date`, `X-Authorization` (prefixed `FKLOGIN <signature>`).
- The service strips the `FKLOGIN ` prefix and re-computes a SHA-1 of `epochSeconds + webhookUrl + httpMethod + sharedSecret`, base64-encodes `applicationId:sha1Hex`, and compares to the incoming value. Mismatch → HTTP 400.
- This endpoint is excluded from the APIM bearer scheme.

### 2.3 Outbound auth (this service → other services)

| Target | Auth |
|---|---|
| Internal TVS APIs (MDP, ATP, Lead, Booking, Notification, Location-Master) | Azure AD B2C bearer token (client_credentials) issued/cached by `AzureB2CTokenManager` |
| Booking service | Bearer + `Ocp-Apim-Subscription-Key` |
| Flipkart Seller API | Per-dealer access token (Dealer-as-Seller) refreshed from a long-lived refresh token; or per-state `client_credentials` (OEM-as-Seller) |

## 3. Validation Rules (summary)

Validation lives in service-layer `validate(...)` methods and DTO `validateAndSanitize(...)` helpers. Examples:

| Field | Rule |
|---|---|
| `Order.marketplaceShipmentId` | non-null, non-empty, ≤ 100 chars |
| `Order.marketplaceOrderId` / `marketplaceOrderItemId` | non-null, non-empty, ≤ 100 chars |
| `Order.lastFailureReason` | ≤ 255 chars (when present) |
| `Order.marketplaceOrderStatus` | ≤ 50 chars (when present), uppercased on save |
| `OrderDetails.quantity` | positive integer |
| `OrderDetails.leadId` / `bookingId` | ≤ 50 chars |
| `OrderDetails.dmsInvoiceNumber` | ≤ 100 chars |
| `OrderDetails.assignedDealerSapCode` | ≤ 25 chars |
| `OrderDetails.deliveryDate` | ≤ 30 chars |
| `TvsProductDetailsDto.partId` / `modelId` | ≤ 50 chars |
| `TvsProductDetailsDto.partName` / `modelName` | ≤ 100 chars |
| `TvsProductDetailsDto.leadServiceBrandCode` | positive integer |
| `TvsProductDetailsDto.vehicleType` | required (`ICE` or `EV`) |
| `VehicleMarketplaceCodeDto.partId` | ≤ 100 chars |
| `VehicleMarketplaceCodeDto.marketplaceCode` | ≤ 50 chars |
| `DealerRefreshTokenDto.sapDealerCode` | ≤ 50 chars |
| `DealerRefreshTokenDto.refreshToken` | ≤ 150 chars |
| `DealerRefreshTokenDto.refreshTokenExpiryTimeInSec` | required, **must be in the future** (epoch seconds) |
| `PriceData.partId` / `state` | required |
| `PriceData.price.ex_showroomprice` | required, valid price |
| `FlipkartShipmentWebhookRequest.eventType` | non-null, ≤ 50 chars |
| `FlipkartShipmentWebhookRequest.shipmentId` | non-null, ≤ 100 chars |
| For `SHIPMENT_CREATED`: `locationId`, every `orderItem.{fsn, orderId, orderItemId, paymentType, orderDate, priceComponents.*}` are validated |
| For `SHIPMENT_CANCELLED`: every `orderItem.{orderItemId, reason, quantity}` are validated |
| Action params on order endpoints | `marketplace-status` requires `action=refresh`; `cancellation-discrepancies` requires `action=notify` |

Idempotency rules:

| Resource | Idempotency key |
|---|---|
| Webhook-driven Order create | `marketplaceShipmentId` (existing rows → ignore) |
| Booking create (downstream) | `OrderDetails.bookingId` (skip if already set) |
| Marketplace price update | Compares current vs target; equal → no-op |
| State transitions | Re-reads `Order` and dispatches by current `status` → safe replays |
| Service Bus messages | `complete()` only on success; broker redelivers otherwise |

## 4. Error Responses

Standard envelope (always returned by `RestExceptionHandler`):

```json
{
  "data": null,
  "errorMessage": "<violation or 'Internal Error occurred'>",
  "time": "Thu May 28 12:00:00 IST 2026",
  "uuid": "<per-request transaction id>",
  "timeTakenInMs": 12,
  "serverId": "ab12"
}
```

| HTTP | Trigger | `errorMessage` example |
|---|---|---|
| 400 | `ValidationException` thrown by service / DTO / webhook hash check | `"order.marketplaceShipmentId : cannot be null/empty (max length: 100)"` |
| 400 | Webhook hash mismatch | `"Invalid hash"` |
| 400 | Unsupported `action` query param | `"Unsupported action: <value>."` |
| 500 | Any other exception | `"Internal Error occurred"` (stack-trace fields under `data.*` only when `SHOW_HTTP_500_ERROR_DETAILS=true`) |

Outbound API failures bubble as 500 unless explicitly translated to a `ValidationException` by the caller service.

## 5. Rate Limits

The service does not enforce rate limits at the HTTP layer; APIM is expected to apply quotas if needed.

Internally, downstream protection is implemented as:

| Surface | Mechanism |
|---|---|
| Flipkart bulk operations | Parallel batches of 10 with 1s inter-batch sleep (`ParallelTaskExecutorService`) |
| Single-SKU price update loop | 2s sleep between iterations; max 100 iterations |
| Async job pool | Fixed thread pool of 20 (`AsyncJobService`) |
| Service Bus consumers | `maxConcurrentSessions` = 50 (price events), 10 (booking events) |
| HikariCP | min 20 / max 50 connections per pod |
| OkHttp | 30s read timeout |

Spring-Retry settings on outbound callers:

| Caller | maxAttempts | initial delay | multiplier |
|---|---|---|---|
| Flipkart Seller API (most) | 6 | 2s | 1.5 (jittered) |
| MDP API | 5 | 2s | 1.5 (jittered) |
| Booking API | 5 | 2s | 1.5 (jittered) |
| Lead API | 6 | 2s | 1.5 (jittered) |
| Notification | 3 | 1s | 2.0 |
| Azure B2C token | 5 | default | (`RetryableException` only) |
| Booking SB consumer | 3 | 2s | 1.5 |

## 6. External API Dependencies

| Dependency | Direction | Auth | Purpose |
|---|---|---|---|
| Azure AD B2C `/token` | Outbound | client_credentials with `B2C_CLIENT_ID` / `B2C_CLIENT_SECRET` | Bearer token for internal API calls |
| Flipkart Seller API | Outbound | Bearer (per-dealer access token or per-state OEM token) | Token gen, listing search, SKU lookup, price update single & bulk, shipment retrieve, self-ship dispatch & delivery |
| Flipkart Webhook | Inbound | SHA-1 signed `X-Authorization` | Shipment created/cancelled events |
| MDP service | Outbound | Bearer | Dealer master, eligibility, proximity-based dealer list |
| ATP service | Outbound | Bearer | Inventory check |
| Location-Master | Outbound | Bearer | Pincode → lat/long |
| Lead service | Outbound | Bearer | Push lead, get lead details |
| Booking service | Outbound | Bearer + `Ocp-Apim-Subscription-Key` | Create / update payment / cancel / get booking |
| Notification service | Outbound | Bearer | Send templated email |
| Azure Service Bus topics | Inbound | SAS connection string | `vehiclePriceData`, `bookingUpdates` |
| MySQL 8 | Outbound (DB) | Username/password | Primary OLTP store |

## 7. Sample Requests / Responses

### 7.1 Bulk upsert TVS products

`POST /v1/products/upsert`

```http
POST /marketplace/v1/products/upsert HTTP/1.1
Host: api.example.tvsmotor.local
Authorization: Bearer <token>
Content-Type: application/json

[
  {
    "partId": "KE1903002F",
    "modelId": "000030000300000028",
    "partName": "iQube ST",
    "modelName": "iQube",
    "mdpDealerFlagName": "IQUBE_FLAG",
    "leadServiceBrandCode": 12,
    "vehicleType": "EV"
  }
]
```

```json
{
  "data": { "insertCount": 1, "updateCount": 0 },
  "errorMessage": null,
  "time": "Thu May 28 12:00:00 IST 2026",
  "uuid": "0b7d-...",
  "timeTakenInMs": 41,
  "serverId": "ab12"
}
```

### 7.2 Upsert dealer refresh tokens

`POST /v1/dealer-refresh-token/upsert`

```json
[
  {
    "sapDealerCode": "SAP123456",
    "refreshToken": "<opaque-token-from-flipkart>",
    "refreshTokenExpiryTimeInSec": 1781596800
  }
]
```

```json
{
  "data": { "insertCount": 1, "updateCount": 0 },
  "errorMessage": null,
  "time": "Thu May 28 12:00:00 IST 2026",
  "uuid": "12c4-...",
  "timeTakenInMs": 33,
  "serverId": "ab12"
}
```

If `refreshTokenExpiryTimeInSec` is in the past:

```json
{
  "data": null,
  "errorMessage": "Validation failed for sapDealerCode SAP123456 : refreshTokenExpiryTimeInSec must be in the future",
  "time": "Thu May 28 12:00:00 IST 2026",
  "uuid": "12c4-...",
  "timeTakenInMs": 4,
  "serverId": "ab12"
}
```

### 7.3 Get aggregated order detail

`GET /v1/order/42`

```json
{
  "data": {
    "order": {
      "id": 42,
      "marketplace": "FLIPKART",
      "marketplaceOrderId": "OD12345",
      "marketplaceOrderItemId": "OI67890",
      "marketplaceShipmentId": "SH99999",
      "status": "INVOICE_GENERATED",
      "marketplaceOrderDate": "2026-05-20 18:30:00",
      "marketplaceOrderStatus": "APPROVED",
      "lastFailureReason": null,
      "lastFailureAt": null,
      "version": 7
    },
    "orderDetails": {
      "id": 42,
      "orderId": 42,
      "tvsProductId": 11,
      "quantity": 1,
      "assignedDealerSapCode": "SAP123456",
      "leadId": "LEAD-...",
      "bookingId": "BK-...",
      "dmsInvoiceNumber": "INV-...",
      "dmsInvoiceDate": "2026-05-22T10:00:00+05:30"
    },
    "tvsProductDetails": { "partId": "KE1903002F", "modelName": "iQube", "vehicleType": "EV" },
    "customerAddressDetails": [
      { "type": "DELIVERY", "firstName": "...", "city": "...", "pincode": "560047", "stateId": 17 }
    ],
    "customerPaymentDetails": {
      "marketplacePaymentId": "PAY-...",
      "paidAmountInInr": 200000.00,
      "paymentMode": "PREPAID"
    },
    "leadDetails": {  "...": "opaque from Lead Service" },
    "bookingDetails": { "...": "opaque from Booking Service" },
    "shipmentDetailsFromMarketplace": { "...": "opaque from Flipkart" },
    "exceptions": []
  },
  "errorMessage": null
}
```

If e.g. Lead Service is down:

```json
{
  "data": {
    "order": { "id": 42 },
    "leadDetails": null,
    "bookingDetails": { "...": "..." },
    "shipmentDetailsFromMarketplace": { "...": "..." },
    "exceptions": [
      "Lead details could not be fetched: e.getMessage() = Read timed out"
    ]
  },
  "errorMessage": null
}
```

### 7.4 Trigger async batch processing

`GET /v1/order/process/FLIPKART`

```json
{
  "data": "Order processing triggered successfully for marketplace: FLIPKART",
  "errorMessage": null
}
```

### 7.5 Sync marketplace order status

`PUT /v1/order/FLIPKART/marketplace-status?action=refresh`

```json
{
  "data": "Triggered ASYNC job to sync order status for mid-stage orders for marketplace: FLIPKART",
  "errorMessage": null
}
```

### 7.6 Notify cancellation discrepancies

`GET /v1/order/FLIPKART/cancellation-discrepancies?action=notify`

```json
{
  "data": "Triggered ASYNC job to notify cancellation discrepancies for marketplace: FLIPKART",
  "errorMessage": null
}
```

### 7.7 Flipkart webhook — SHIPMENT_CREATED

```http
POST /marketplace/webhook/flipkart/order-management/notifications-receiver/dealer/common HTTP/1.1
Host: api.example.tvsmotor.local
X-Date: Mon, 04 Aug 2025 18:30:00 GMT+05:30
X-Authorization: FKLOGIN <base64Signature>
Content-Type: application/json

{
  "shipmentId": "SH99999",
  "eventType": "SHIPMENT_CREATED",
  "locationId": "LOC123",
  "source": "FLIPKART",
  "timestamp": "2026-05-20T18:30:00+05:30",
  "attributes": {
    "orderItems": [
      {
        "fsn": "MOTABXYZ123",
        "quantity": 1,
        "orderId": "OD12345",
        "orderItemId": "OI67890",
        "listingId": "LST...",
        "paymentType": "PREPAID",
        "priceComponents": {
          "sellingPrice": 200000,
          "totalPrice": 200000,
          "shippingCharge": 0,
          "customerPrice": 200000,
          "flipkartDiscount": 0
        },
        "orderDate": "2026-05-20T18:30:00+05:30",
        "status": "APPROVED"
      }
    ]
  }
}
```

```json
{
  "data": "Shipment data successfully received",
  "errorMessage": null
}
```

If signature does not validate:

```json
{
  "data": null,
  "errorMessage": "Invalid hash"
}
```

If `marketplaceShipmentId` already exists, the response is the same `200`; the duplicate is recorded in the audit log and ignored — idempotent by design.

### 7.8 Flipkart webhook — SHIPMENT_CANCELLED

```json
{
  "shipmentId": "SH99999",
  "eventType": "SHIPMENT_CANCELLED",
  "locationId": "LOC123",
  "attributes": {
    "orderItems": [
      {
        "orderItemId": "OI67890",
        "quantity": 1,
        "reason": "CUSTOMER_REQUEST",
        "subReason": "ADDRESS_CHANGE_REQUESTED"
      }
    ]
  }
}
```

```json
{
  "data": "Shipment data successfully received",
  "errorMessage": null
}
```

If the order is in a non-cancelable status (`INVOICE_GENERATED`, `SHIPPED`, `GATE_PASS_GENERATED`, `DELIVERED`, `CANCELLED`):

```json
{
  "data": null,
  "errorMessage": "Order with id = 42 and shipmentId = SH99999 cannot be cancelled as it is already in status = SHIPPED."
}
```

### 7.9 Trigger bulk price reconciliation

`GET /v1/test/start-bulk-price-update-flipkart`

```json
{ "data": "DONE", "errorMessage": null }
```

### 7.10 Service Bus processor status

`GET /v1/test/service-bus/status`

```json
{
  "data": {
    "ccpVehiclePriceData_ProcessorClientRunning": true,
    "bookingUpdates_ProcessorClientRunning": true
  },
  "errorMessage": null
}
```

### 7.11 Evict cache

`DELETE /v1/test/cache/AZURE_B2C_TOKEN/AZURE_B2C_TOKEN`

```json
{
  "data": "Cache cleared successfully for cacheName = AZURE_B2C_TOKEN, key = AZURE_B2C_TOKEN",
  "errorMessage": null
}
```

## 8. Operational notes

- **Async semantics**: most order endpoints return 200 immediately and submit the actual work to the in-process async pool. Final outcomes are recorded in the `audit_log` table (queryable by `transaction_id`).
- **Tracing**: every response carries a `uuid` (transaction id) which is also written into all log lines and audit-log rows associated with the request. Use it as the join key during incident investigation.
- **CORS**: `OrderController` and `TestController` allow `http://localhost:3000/` and `https://arsh-tvs.github.io/` origins for local dev tooling. PROD deployments should rely on APIM CORS policy and ignore these annotations.
- **Stability**: The shape of `GeneralResponse` is stable across the public APIs. Endpoint-specific data lives under `data`; clients should treat unknown fields tolerantly.

# API Specification — PaymentService

**TVS Motor Company Ltd — Common Backend Services**

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | PaymentService |
| Repo | TVS-CS/PaymentService (GitHub) |
| Team | Common Backend Services |
| Tech Lead | Arun Kumar Reddy |
| Deployment | Azure Functions v4 (Isolated Worker) |
| Runtime | .NET 8 (C#) |
| Trigger | Azure Service Bus queue: `cpg-juspay` |
| Base URL (prod) | N/A — not an HTTP API (message-driven) |

---

## 2. Ownership & Contacts

| Role | Person / Team |
|------|---------------|
| Product Owner | Avinash Kumar |
| Tech Lead | Arun Kumar Reddy |
| Developer | Rachel Bennet |
| Dev Team | Common Backend Services |

---

## 3. Important: This Is NOT a REST API

PaymentService does not expose any HTTP endpoints for external callers to hit. It is a **message-driven processor** that:

1. **Receives** messages from an Azure Service Bus queue (inbound)
2. **Makes** HTTP POST calls to downstream services (outbound)

There is no REST API to call. If you need to trigger this service, you send a message to the Service Bus queue.

---

## 4. Inbound — Service Bus Trigger (Who Calls Me)

| Method | Endpoint/Queue | Auth | Description | Called By |
|--------|----------------|------|-------------|-----------|
| Service Bus Trigger | Queue: `cpg-juspay` | SAS (Send permission) | Receives JusPay payment/refund/payout/mandate webhook events | JusPay (payment gateway) |

### Queue Details

| Property | Value |
|----------|-------|
| Queue Name | `cpg-juspay` |
| Protocol | AMQP (Azure Service Bus) |
| Auth | Shared Access Signature (SAS) |
| Delivery Mode | PeekLock |
| Function Trigger | `[ServiceBusTrigger("cpg-juspay")]` |

**Who Sends Messages Here?** JusPay (the payment gateway) is configured to push webhook events to this queue. This service only consumes from the queue — it never publishes to it.

---

## 5. Outbound — Who I Call

| Target | Method | Endpoint | Auth | Purpose |
|--------|--------|----------|------|---------|
| Azure AD (Entra ID) | POST | Token endpoint (`TokenUrl` env var) | client_credentials | Get OAuth2 Bearer token for downstream auth |
| iQubeWebsite | POST | `iQubeWebsite` env var | Bearer token | EV scooter payment callbacks (encrypted) |
| CreonWebsite | POST | `CreonWebsite` env var | Bearer token | EV scooter payment callbacks (encrypted) |
| iQubeHDCB | POST | `iQubeHDCB` env var | Bearer token | EV scooter payment callbacks — HDCB (encrypted) |
| EvScooter | POST | `EvScooter` env var | Bearer token | EV scooter payment callbacks (encrypted) |
| TVSConnectEV | POST | `TVSConnectEV` env var | Bearer token | EV subscription payment callbacks (encrypted) |
| TVSRacing | POST | `TVSRacing` env var | Bearer token | Racing platform payment callbacks (encrypted) |
| TVSConnectFleet | POST | `TVSConnectFleet` env var | Bearer token | Fleet management payment callbacks (encrypted) |
| BookingService | POST | `BookingService` env var | Bearer token + APIM key | Payment status + refund callbacks (plain JSON) |
| iceWebsiteShopify | POST | `iceWebsiteShopify` env var | Bearer token | Shopify refund callbacks (encrypted) |
| TVSSparesAutoRefunds | POST | `TVSSparesAutoRefunds` env var | Bearer token | TVS Spares auto-refund callbacks (encrypted) |
| TVSConnectEVMandate | POST | `TVSConnectEVMandate` env var | Bearer token | Mandate lifecycle callbacks (encrypted) |

---

## 6. Events & Messaging

### Topics/Queues This Service Subscribes To

| Topic/Queue | Events | Source | Action |
|-------------|--------|--------|--------|
| `cpg-juspay` (Service Bus queue) | ORDER_SUCCEEDED, ORDER_FAILED | JusPay | Map status → forward payment webhook to downstream client |
| `cpg-juspay` (Service Bus queue) | REFUND_INITIATED, ORDER_REFUNDED, ORDER_REFUND_FAILED | JusPay | Map status → forward refund webhook to BookingService/Shopify/Spares |
| `cpg-juspay` (Service Bus queue) | FULFILLMENTS_SUCCESSFUL, FULFILLMENTS_FAILURE, FULFILLMENTS_MANUAL_REVIEW, FULFILLMENTS_CANCELLED | JusPay | Map status → forward payout webhook to downstream client |
| `cpg-juspay` (Service Bus queue) | MANDATE_CREATED, MANDATE_ACTIVATED, MANDATE_FAILED | JusPay | Forward mandate webhook to TVSConnectEVMandate |

### Topics/Queues This Service Publishes To

None. This service is a consumer-only relay — it does not publish any events.

---

## 7. External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| JusPay | Payment Gateway | Source of all payment/refund/payout/mandate events (via Service Bus) | SAS key (Send permission on queue) |
| Azure AD (Entra ID) | Identity Provider | OAuth2 Bearer tokens for downstream auth | client_credentials grant |
| Azure API Management | API Gateway | Gateway-level auth for non-encrypted downstream calls | Subscription key (`Ocp-Apim-Subscription-Key`) |
| Azure Service Bus | Message Broker | Message delivery/buffering between JusPay and this function | SAS connection string |
| Application Insights | Monitoring | Telemetry, logging, diagnostics | Azure SDK (auto) |

---

## 8. Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| None | — | This service is 100% stateless. No database, no cache, no file storage. |

---

## 9. Message Formats (Inbound)

### 9.1 Payment / Refund / Mandate Events

```json
{
  "event_name": "ORDER_SUCCEEDED",
  "label": null,
  "content": {
    "order": {
      "order_id": "string — JusPay order ID",
      "status": "string — CHARGED | AUTHENTICATION_FAILED | AUTHORIZATION_FAILED | JUSPAY_DECLINED | AUTHORIZING | STARTED | AUTO_REFUNDED | PENDING_VBV | NEW",
      "amount": 0.00,
      "effective_amount": 0.00,
      "txn_id": "string — JusPay transaction ID",
      "txn_uuid": "string — transaction UUID",
      "currency": "INR",
      "date_created": "2026-01-15T10:30:00Z",
      "payment_method_type": "UPI | CARD | NB | WALLET",
      "udf2": "string — client app transaction ID",
      "udf4": "string — payment type label",
      "udf5": "string — CLIENT CODE (determines routing)",
      "udf6": "string — booking ID",
      "txn_detail": {
        "gateway": "string — bank gateway name",
        "order_id": "string"
      },
      "payment_gateway_response": {
        "epg_txn_id": "string — gateway transaction ref",
        "resp_message": "string",
        "resp_code": "string",
        "created": "2026-01-15T10:30:05Z"
      },
      "refunds": [
        {
          "unique_request_id": "string — refund reference (suffix -S means Shopify)",
          "ref": "string — bank reference number",
          "error_message": "string | null",
          "status": "SUCCESS | PENDING | MANUAL_REVIEW | FAILURE",
          "last_updated": "2026-01-16T14:00:00Z",
          "amount": 0.00
        }
      ],
      "mandate": {
        "status": "string",
        "start_date": "string",
        "end_date": "string",
        "order_id": "string (prefix TE means TVS Connect EV)",
        "max_amount": "string",
        "mandate_token": "string",
        "mandate_id": "string",
        "frequency": "string",
        "amount_rule": "string"
      }
    },
    "mandate": {
      "...same structure as order.mandate..."
    }
  }
}
```

**Supported `event_name` values:**

| Event | When It Fires |
|-------|--------------|
| `ORDER_SUCCEEDED` | Payment completed successfully |
| `ORDER_FAILED` | Payment failed |
| `ORDER_REFUNDED` | Refund processed on an order |
| `ORDER_REFUND_FAILED` | Refund attempt failed |
| `REFUND_INITIATED` | Refund was initiated |
| `REFUND_SUCCEEDED` | Individual refund succeeded |
| `REFUND_FAILED` | Individual refund failed |
| `MANDATE_CREATED` | Recurring mandate was created |
| `MANDATE_ACTIVATED` | Mandate was activated |
| `MANDATE_FAILED` | Mandate creation/activation failed |

### 9.2 Payout Events (identified by `label: "ORDER"`)

```json
{
  "createdAt": "2026-01-15T10:30:00Z",
  "category": "string",
  "value": "string — remarks/description",
  "id": "string",
  "updatedAt": "2026-01-15T10:31:00Z",
  "label": "ORDER",
  "info": {
    "status": "FULFILLMENTS_SUCCESSFUL | FULFILLMENTS_FAILURE | FULFILLMENTS_MANUAL_REVIEW | FULFILLMENTS_CANCELLED",
    "amount": 500,
    "createdAt": "2026-01-15T10:30:00Z",
    "orderType": "string",
    "merchantOrderId": "string",
    "merchantCustomerId": "string",
    "id": "string — transaction ID",
    "updatedAt": "string",
    "udf1": "string — client app user ID",
    "udf2": "string — client refund reference",
    "udf3": "string",
    "udf4": "string",
    "udf5": "string — CLIENT CODE (determines routing)"
  }
}
```

---

## 10. Outbound Payload Formats

### 10.1 Payment Callback — Encrypted (EV Clients)

**Targets**: iQubeWebsite, CreonWebsite, iQubeHDCB, EvScooter, TVSConnectEV, TVSRacing, TVSConnectFleet

| Property | Value |
|----------|-------|
| Method | POST |
| Content-Type | application/json |
| Authorization | Bearer {access_token} |

**Request Body:**
```json
{
  "data": "Base64-encoded-AES-encrypted-PaymentWebhook-JSON",
  "clientcode": ""
}
```

**What's inside `data` after decryption:**
```json
{
  "paymentinitiationcode": "ORD-001",
  "orderid": "ORD-001",
  "orderamount": 2500.00,
  "effectiveamount": 2500.00,
  "transactionid": "TXN-123",
  "transactiondate": "2026-01-15T10:30:00Z",
  "status": "Success",
  "bankreferencenumber": "uuid-value",
  "clientapptransactionid": "APP-TXN-001",
  "bookingid": "BK-001",
  "paymentmode": "UPI",
  "currency": "INR",
  "paymenttype": "FULL_PAYMENT",
  "paymentgateway": "RAZORPAY",
  "statuscode": "00",
  "statusmessage": "Transaction Successful",
  "mandate": null
}
```

### 10.2 Payment Callback — Plain JSON (Non-EV Clients)

**Targets**: BookingService (and any non-EV client)

| Property | Value |
|----------|-------|
| Method | POST |
| Content-Type | application/json |
| Authorization | Bearer {access_token} |
| Ocp-Apim-Subscription-Key | From `OcpApimSubscriptionValue` env var |

**Request Body:** Same PaymentWebhook structure as above (unencrypted).

**Note**: `mandate` field is only included when `order.mandate` exists and `mandate_id` is not null/empty. Otherwise it's null.

### 10.3 Refund Callback — Plain JSON (Booking Service)

| Property | Value |
|----------|-------|
| Method | POST |
| Content-Type | application/json |
| Authorization | Bearer {access_token} |
| Ocp-Apim-Subscription-Key | From `OcpApimSubscriptionValue` env var |

**Request Body:**
```json
{
  "paymentinitiationcode": "ORD-001",
  "orderid": "ORD-001",
  "orderamount": 500.00,
  "transactionid": "EPG-12345",
  "transactiondate": "2026-01-15T10:30:05Z",
  "status": "refunded",
  "bookingid": "BK-001",
  "clientapptransactionid": "APP-TXN-001",
  "paymenttype": "PARTIAL_REFUND",
  "statusmessage": null,
  "refundreferenceno": "REF-001",
  "refundstatus": "RefundConfirmed | RefundAwaited | RefundFailed",
  "refundbankreferenceno": "BANK-REF-ABC",
  "refundcompletiondate": "2026-01-16T14:00:00Z"
}
```

### 10.4 Refund Callback — Encrypted (Shopify / TVS Spares)

**Targets**:
- iceWebsiteShopify (when `unique_request_id` ends with `-S`)
- TVSSparesAutoRefunds (when `order_id` starts with `SPR-`)

**Request Body:**
```json
{
  "data": "Base64-encoded-AES-encrypted-RefundWebhook-JSON",
  "clientcode": ""
}
```

**What's inside `data` after decryption:** Same RefundWebhook structure as section 10.3.

### 10.5 Payout Callback — Plain JSON

**Target**: Determined by `info.udf5` value

| Property | Value |
|----------|-------|
| Method | POST |
| Content-Type | application/json |
| Authorization | Bearer {access_token} |
| Ocp-Apim-Subscription-Key | From `OcpApimSubscriptionValue` env var |

**Request Body:**
```json
{
  "clientcode": "BookingService",
  "clientappuserid": "USER-001",
  "clientrefundreferencenumber": "REFUND-REF-001",
  "refundreferencenumber": "MO-123",
  "refundamount": 500,
  "payrefno": "MO-123",
  "refundstatus": "Success | Failure | Awaited | Rejected",
  "remarks": "Refund for order cancellation",
  "transactionid": "TXN-789",
  "transactiondate": "2026-01-15T10:30:00Z",
  "paymentreceiveddatetime": "2026-01-15T10:31:00"
}
```

**Note**: `paymentreceiveddatetime` is only populated when status is `FULFILLMENTS_SUCCESSFUL`. Otherwise it's an empty string `""`.

### 10.6 Mandate Callback — Encrypted

**Target**: TVSConnectEVMandate (only for orders starting with `TE`)

**Request Body:**
```json
{
  "data": "Base64-encoded-AES-encrypted-MandateWebhook-JSON",
  "clientcode": ""
}
```

**What's inside `data` after decryption:**
```json
{
  "token": "mandate-token-abc",
  "status": "CREATED | ACTIVATED | FAILED",
  "id": "MANDATE-001",
  "startdate": "2026-01-01",
  "enddate": "2027-01-01",
  "maxamount": "5000",
  "frequency": "MONTHLY",
  "rulevalue": null,
  "amountrule": "MAX",
  "orderid": "TE-ORD-123"
}
```

---

## 11. Authentication Details

### 11.1 Inbound (How Messages Get on the Queue)

| Layer | Mechanism |
|-------|-----------|
| Service Bus | Shared Access Signature (SAS) with Send permission |

JusPay is given a SAS connection string with **Send** permission only. They cannot read or manage the queue.

### 11.2 Outbound (How This Service Authenticates to Downstream)

| Header | Value | Used In |
|--------|-------|---------|
| `Authorization` | `Bearer {oauth2_token}` | All outbound calls |
| `Ocp-Apim-Subscription-Key` | From `OcpApimSubscriptionValue` env var | `PostToClient()` and `PaymentStatusPostToClient()` only |

The APIM subscription key is NOT used for encrypted (EV) calls. Those only use the Bearer token.

### 11.3 OAuth2 Token Flow

The service acquires a token via client_credentials grant on every message:
1. POST to Azure AD token endpoint with `grant_type=client_credentials`, `client_id`, `client_secret`, and `scope`
2. Azure AD returns `{ access_token: "eyJ..." }`
3. PaymentService uses the Bearer token for all downstream POST calls

**Note**: A new token is acquired for every message processed. There is no token caching.

---

## 12. Routing & Validation Rules

| Rule | Field | Behavior |
|------|-------|----------|
| Payout detection | `messageBody.label` | If `"ORDER"` → payout flow |
| Null check | `messageBody` | If null → skip everything |
| Null check | `payoutsMessageBody` (payout path) | If null → skip |
| URL existence | Env var for client code | If null → complete message (payment) or skip (payout) |
| EV client check | `order.udf5` | Determines encrypted vs plain delivery |
| Shopify routing | `refund.unique_request_id` ends with `-S` | Routes to iceWebsiteShopify |
| Spares routing | `order_id` starts with `SPR-` | Routes to TVSSparesAutoRefunds |
| Mandate routing | `mandate.order_id` starts with `TE` | Routes to TVSConnectEVMandate |
| Mandate inclusion | `order.mandate != null && mandate_id not empty` | Includes mandate in payment webhook |
| Success check | HTTP response from downstream | Only completes message on HTTP 200 |

---

## 13. Error Handling

| What Goes Wrong | What Happens |
|----------------|--------------|
| Message JSON is malformed | Deserialization throws → message retries |
| Can't get OAuth2 token | Token request throws → message retries |
| Downstream returns non-200 | Message is NOT completed → stays in queue → retries |
| Downstream is unreachable | HTTP exception thrown → message retries |
| Exceeded max retries | Message moves to Dead Letter Queue |

**There is no error response to any caller** — the only signal is whether the message gets completed or not.

---

## 14. Client Endpoint Registry

| Client Code | Env Variable | Encrypted? | Auth Headers | Use Case |
|------------|-------------|------------|--------------|----------|
| iQubeWebsite | `iQubeWebsite` | Yes (AES) | Bearer only | EV scooter payments |
| CreonWebsite | `CreonWebsite` | Yes (AES) | Bearer only | EV scooter payments |
| iQubeHDCB | `iQubeHDCB` | Yes (AES) | Bearer only | EV scooter payments (HDCB) |
| EvScooter | `EvScooter` | Yes (AES) | Bearer only | EV scooter payments |
| TVSConnectEV | `TVSConnectEV` | Yes (AES) | Bearer only | EV subscription payments |
| TVSRacing | `TVSRacing` | Yes (AES) | Bearer only | Racing platform |
| TVSConnectFleet | `TVSConnectFleet` | Yes (AES) | Bearer only | Fleet management |
| BookingService | `BookingService` | No | Bearer + APIM key | Payment status + refund callbacks |
| iceWebsiteShopify | `iceWebsiteShopify` | Yes (AES) | Bearer only | Shopify refund callbacks |
| TVSSparesAutoRefunds | `TVSSparesAutoRefunds` | Yes (AES) | Bearer only | Spares auto-refund |
| TVSConnectEVMandate | `TVSConnectEVMandate` | Yes (AES) | Bearer only | Mandate callbacks |

---

## 15. End-to-End Examples

### Example 1: Successful EV Payment (iQube)

**Step 1 — Message arrives on queue:**
```json
{
  "event_name": "ORDER_SUCCEEDED",
  "content": {
    "order": {
      "order_id": "IQ-20260115-001",
      "status": "CHARGED",
      "amount": 2500.00,
      "effective_amount": 2500.00,
      "txn_id": "TXN-98765",
      "txn_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "currency": "INR",
      "date_created": "2026-01-15T10:30:00Z",
      "payment_method_type": "UPI",
      "udf2": "APP-TXN-001",
      "udf4": "FULL_PAYMENT",
      "udf5": "iQubeWebsite",
      "udf6": "BK-001",
      "txn_detail": { "gateway": "RAZORPAY", "order_id": "IQ-20260115-001" },
      "payment_gateway_response": {
        "epg_txn_id": "EPG-12345",
        "resp_message": "Transaction Successful",
        "resp_code": "00",
        "created": "2026-01-15T10:30:05Z"
      },
      "refunds": [],
      "mandate": null
    }
  }
}
```

**Step 2** — Service gets OAuth2 token from Azure AD

**Step 3** — Service maps status: `CHARGED` → `Success`

**Step 4** — Service builds PaymentWebhook, encrypts it (iQubeWebsite is an EV client)

**Step 5** — Service POSTs to iQubeWebsite URL:
```
POST <iQubeWebsite env var URL>
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "data": "aGVsbG8gd29ybGQgdGhpcyBpcyBlbmNyeXB0ZWQ=",
  "clientcode": ""
}
```

**Step 6** — Downstream returns 200 → message completed

---

### Example 2: Shopify Refund

**Step 1 — Message arrives:**
```json
{
  "event_name": "ORDER_REFUNDED",
  "content": {
    "order": {
      "order_id": "SHOP-20260115-002",
      "udf2": "APP-TXN-002",
      "udf4": "CANCELLATION",
      "udf5": "iceWebsiteShopify",
      "udf6": "BK-002",
      "txn_detail": { "gateway": "HDFC", "order_id": "SHOP-20260115-002" },
      "payment_gateway_response": {
        "epg_txn_id": "EPG-67890",
        "resp_message": "Refund Processed",
        "resp_code": "00",
        "created": "2026-01-15T14:00:00Z"
      },
      "refunds": [
        {
          "unique_request_id": "REF-001-S",
          "ref": "BANK-REF-ABC",
          "error_message": null,
          "status": "SUCCESS",
          "last_updated": "2026-01-16T14:00:00Z",
          "amount": 1200.00
        }
      ]
    }
  }
}
```

**Step 2** — Service sees `unique_request_id` ends with `-S` → routes to Shopify

**Step 3** — Service maps refund status: `SUCCESS` → `RefundConfirmed`

**Step 4** — Service builds RefundWebhook, encrypts it

**Step 5** — Service POSTs encrypted payload to iceWebsiteShopify URL

**Step 6** — Downstream returns 200 → message completed

---

### Example 3: Payout to Booking Service

**Step 1 — Message arrives with `label: "ORDER"`:**
```json
{
  "createdAt": "2026-01-15T10:30:00Z",
  "category": "payout",
  "value": "Cancellation refund",
  "id": "PAY-555",
  "updatedAt": "2026-01-15T10:31:00Z",
  "label": "ORDER",
  "info": {
    "status": "FULFILLMENTS_SUCCESSFUL",
    "amount": 500,
    "merchantOrderId": "MO-123",
    "merchantCustomerId": "CUST-456",
    "id": "TXN-789",
    "updatedAt": "2026-01-15T10:31:00",
    "udf1": "USER-001",
    "udf2": "REFUND-REF-001",
    "udf5": "BookingService"
  }
}
```

**Step 2** — Service detects `label == "ORDER"` → payout flow

**Step 3** — Service maps status: `FULFILLMENTS_SUCCESSFUL` → `Success`

**Step 4** — Service POSTs plain JSON to BookingService URL:
```json
{
  "clientcode": "BookingService",
  "clientappuserid": "USER-001",
  "clientrefundreferencenumber": "REFUND-REF-001",
  "refundreferencenumber": "MO-123",
  "refundamount": 500,
  "payrefno": "MO-123",
  "refundstatus": "Success",
  "remarks": "Cancellation refund",
  "transactionid": "TXN-789",
  "transactiondate": "2026-01-15T10:30:00Z",
  "paymentreceiveddatetime": "2026-01-15T10:31:00"
}
```

**Step 5** — Downstream returns 200 → message completed

---

## 16. Rate Limits

This service has no explicit rate limiting. Throughput is governed by:

| Factor | Constraint |
|--------|-----------|
| Service Bus tier | Throughput limits of the Azure Service Bus namespace |
| Function App plan | Consumption plan: ~200 instances max; Premium: configurable |
| Azure AD | Standard tenant-level throttling on token endpoint |
| Downstream services | Their individual capacity / rate limits |

---

## 17. External API Dependencies

| Dependency | What This Service Needs From It | What Happens If It's Down |
|-----------|--------------------------------|--------------------------|
| Azure Service Bus | Delivers messages (trigger) | No messages processed; events buffer |
| Azure AD Token Endpoint | OAuth2 Bearer tokens | All downstream calls fail; messages retry |
| Downstream TVS services | Accept webhook POSTs | Messages retry until downstream recovers |
| Azure API Management | Some calls route through it | Non-EV plain JSON calls fail |

---

*This specification documents the message contracts for integration purposes. No credentials or sensitive values are included.*

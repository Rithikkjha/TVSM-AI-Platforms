# Low Level Design (LLD) — PaymentService

**TVS Motor Company Ltd — Connected Services Engineering**  
*Detailed Implementation Guide for Engineering Vendors*

---

## 1. Module Breakdown

This service has a simple, flat structure. Here's every module with exactly what's inside:

### Functions Module (1 file)

**File**: `Functions/JusPayWebhooks.cs`

This is the heart of the service. It contains:
- The Azure Function entry point (`Run` method)
- All event classification logic (payment vs refund vs payout vs mandate)
- Token generation logic
- Three HTTP delivery methods (plain, encrypted, payment-specific)

### Models Module (9 files)

| File | Direction | Used For |
|------|-----------|----------|
| `MessageBody.cs` | Inbound | Main JusPay message (contains `Order`, `Content`, `Refund`, `TxnDetail`, `PaymentGatewayResponse` classes) |
| `MandateBody.cs` | Inbound | Mandate data from JusPay (`Mandate` class) |
| `PayoutsMessageBody.cs` | Inbound | Payout-specific message (`PayoutsMessageBody` + `Info` classes) |
| `PaymentWebhook.cs` | Outbound | What we send downstream for payment events |
| `RefundWebhook.cs` | Outbound | What we send downstream for refund events |
| `PayoutWebhook.cs` | Outbound | What we send downstream for payout events |
| `MandateWebhook.cs` | Outbound | What we send downstream for mandate events |
| `TokenRequest.cs` | Internal | OAuth2 token request shape (not actually used — token body is a raw string from config) |
| `TokenResponse.cs` | Internal | OAuth2 token response deserialization |

### Mappers Module (1 file)

**File**: `Mappers/StatusMapper.cs`

Three static methods that map JusPay status strings to internal CPG status strings. Pure logic, no side effects.

### Helpers Module (1 file)

**File**: `Helpers/AesCrypto.cs`

One static method that takes a plaintext string, encrypts it with AES-128-CBC, and returns Base64.

### Constants Module (6 files)

| File | What's Inside |
|------|--------------|
| `ClientCode.cs` | 11 string constants — one per downstream client |
| `EventName.cs` | 14 string constants — one per JusPay event type |
| `General.cs` | Config key names, content type, auth header names, APIM subscription key value |
| `JusPayPaymentStatus.cs` | 9 string constants for JusPay payment statuses |
| `JusPayRefundStatus.cs` | 4 string constants for JusPay refund statuses |
| `JusPayPayoutStatus.cs` | 4 string constants for JusPay payout statuses |

### Enums Module (2 files)

| File | What's Inside |
|------|--------------|
| `CPGPaymentStatus.cs` | `PaymentStatusEnum` — 16 possible payment outcomes |
| `CPGRefundStatus.cs` | `RefundStatusEnum` (4 values) + `PayoutStatusEnum` (5 values) |

---

## 2. Class Responsibilities

### JusPayWebhooks

| Responsibility | Details |
|---------------|---------|
| Message receipt | Triggered by Service Bus; receives `ServiceBusReceivedMessage` |
| Event classification | Checks `label` and `event_name` to determine processing path |
| Token acquisition | Calls Azure AD for OAuth2 Bearer token |
| Payload transformation | Builds outbound webhook objects from inbound message data |
| Client routing | Determines target URL from environment variables |
| Delivery decision | Chooses encrypted vs plain delivery based on client code |
| Message completion | Marks Service Bus message as complete on successful delivery |

### StatusMapper

| Responsibility | Details |
|---------------|---------|
| Payment status translation | `GetPaymentStatus(string)` — 9 JusPay values → 5 CPG values |
| Refund status translation | `GetRefundStatus(string)` — 4 JusPay values → 3 CPG values |
| Payout status translation | `GetPayoutStatus(string)` — 4 JusPay values → 4 CPG values |

### AesCrypto

| Responsibility | Details |
|---------------|---------|
| Encrypt payloads | AES-128-CBC encryption with PKCS7 padding, outputs Base64 string |

---

## 3. Detailed API Flow

### 3.1 What Comes IN (from JusPay via Service Bus)

There are two message formats that arrive on the queue:

**Format A: Standard Message (Payment, Refund, or Mandate)**

```json
{
  "event_name": "ORDER_SUCCEEDED",       ← Tells us what type of event this is
  "label": null,                          ← If this is "ORDER", it's a payout instead
  "content": {
    "order": {
      "order_id": "ORD-20260115-001",     ← JusPay order ID
      "status": "CHARGED",                ← JusPay's status (we translate this)
      "amount": 2500.00,                  ← Total order amount
      "effective_amount": 2500.00,        ← Amount actually charged
      "txn_id": "TXN-98765",             ← JusPay transaction ID
      "txn_uuid": "550e8400-...",         ← UUID for the transaction
      "currency": "INR",
      "date_created": "2026-01-15T10:30:00Z",
      "payment_method_type": "UPI",       ← How the customer paid
      "udf2": "APP-TXN-001",             ← Client app's transaction ID
      "udf4": "FULL_PAYMENT",            ← Payment type label
      "udf5": "iQubeWebsite",            ← ⚠️ ROUTING KEY — determines which downstream service gets the callback
      "udf6": "BK-001",                  ← Booking ID
      "txn_detail": {
        "gateway": "RAZORPAY",            ← Which bank gateway was used
        "order_id": "ORD-20260115-001"
      },
      "payment_gateway_response": {
        "epg_txn_id": "EPG-12345",        ← Gateway's transaction reference
        "resp_message": "Success",        ← Gateway's response text
        "resp_code": "00",                ← Gateway's response code
        "created": "2026-01-15T10:30:05Z"
      },
      "refunds": [],                      ← Array of refund items (for refund events)
      "mandate": null                     ← Mandate data (if applicable)
    },
    "mandate": null                       ← Top-level mandate (for mandate events)
  }
}
```

**Format B: Payout Message (identified by `label: "ORDER"`)**

```json
{
  "createdAt": "2026-01-15T10:30:00Z",
  "category": "payout",
  "value": "Refund for order cancellation",   ← Remarks
  "id": "PAY-123",
  "updatedAt": "2026-01-15T10:31:00Z",
  "label": "ORDER",                            ← ⚠️ This is what identifies it as a payout
  "info": {
    "status": "FULFILLMENTS_SUCCESSFUL",       ← JusPay payout status
    "amount": 500,
    "createdAt": "2026-01-15T10:30:00Z",
    "orderType": "PAYOUT",
    "merchantOrderId": "MO-123",               ← Merchant's order reference
    "merchantCustomerId": "CUST-456",
    "id": "TXN-789",                           ← Transaction ID
    "updatedAt": "2026-01-15T10:31:00",
    "udf1": "USER-001",                        ← Client app user ID
    "udf2": "REFUND-REF-001",                  ← Client's refund reference number
    "udf3": "",
    "udf4": "",
    "udf5": "BookingService"                   ← ⚠️ ROUTING KEY
  }
}
```

### 3.2 What Goes OUT (to downstream services)

**Payment Webhook (outbound payload for payment events)**

```json
{
  "paymentinitiationcode": "ORD-20260115-001",
  "orderid": "ORD-20260115-001",
  "orderamount": 2500.00,
  "effectiveamount": 2500.00,
  "transactionid": "TXN-98765",
  "transactiondate": "2026-01-15T10:30:00Z",
  "status": "Success",                        ← Translated from "CHARGED"
  "bankreferencenumber": "550e8400-...",       ← txn_uuid
  "clientapptransactionid": "APP-TXN-001",    ← from udf2
  "bookingid": "BK-001",                      ← from udf6
  "paymentmode": "UPI",
  "currency": "INR",
  "paymenttype": "FULL_PAYMENT",              ← from udf4
  "paymentgateway": "RAZORPAY",
  "statuscode": "00",
  "statusmessage": "Success",
  "mandate": null                             ← Included only if mandate data exists
}
```

**Refund Webhook (outbound payload for refund events)**

```json
{
  "paymentinitiationcode": "ORD-20260115-001",  ← from txn_detail.order_id
  "orderid": "ORD-20260115-001",                ← from txn_detail.order_id
  "orderamount": 500.00,                        ← individual refund amount
  "transactionid": "EPG-12345",                 ← from payment_gateway_response.epg_txn_id
  "transactiondate": "2026-01-15T10:30:05Z",    ← from payment_gateway_response.created
  "status": "refunded",                         ← always hardcoded as "refunded"
  "bookingid": "BK-001",                        ← from udf6
  "clientapptransactionid": "APP-TXN-001",      ← from udf2
  "paymenttype": "FULL_PAYMENT",                ← from udf4
  "statusmessage": null,                        ← from refund.error_message
  "refundreferenceno": "REF-001",               ← from refund.unique_request_id
  "refundstatus": "RefundConfirmed",            ← translated from refund.status
  "refundbankreferenceno": "BANK-REF-ABC",      ← from refund.ref
  "refundcompletiondate": "2026-01-16T14:00:00Z" ← from refund.last_updated
}
```

**Payout Webhook (outbound payload for payout events)**

```json
{
  "clientcode": "BookingService",               ← from info.udf5
  "clientappuserid": "USER-001",               ← from info.udf1
  "clientrefundreferencenumber": "REFUND-REF-001", ← from info.udf2
  "refundreferencenumber": "MO-123",           ← from info.merchantOrderId
  "refundamount": 500,                         ← from info.amount
  "payrefno": "MO-123",                        ← from info.merchantOrderId
  "refundstatus": "Success",                   ← translated from info.status
  "remarks": "Refund for order cancellation",  ← from value field
  "transactionid": "TXN-789",                  ← from info.id
  "transactiondate": "2026-01-15T10:30:00Z",   ← from createdAt
  "paymentreceiveddatetime": "2026-01-15T10:31:00" ← info.updatedAt (only if status is FULFILLMENTS_SUCCESSFUL, else empty string)
}
```

**Mandate Webhook (outbound payload for mandate events)**

```json
{
  "token": "mandate-token-abc",
  "status": "CREATED",
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

**Encrypted Wrapper (for EV clients)**

When a payload is encrypted, the HTTP body looks like this:

```json
{
  "data": "aGVsbG8gd29ybGQgdGhpcyBpcyBhIHNhbXBsZQ==",   ← AES-encrypted JSON, Base64-encoded
  "clientcode": ""                                          ← Always empty string
}
```

---

## 4. Internal Component Interactions

Here's the exact call chain for each event type:

### Payment Event Processing

```
Run() is called with ServiceBusReceivedMessage
  │
  ├── JsonConvert.DeserializeObject<MessageBody>(message.Body)
  │
  ├── GenerateToken() → POST to Azure AD → get access_token
  │
  ├── Check: label == "ORDER"? → NO (it's a payment, not a payout)
  │
  ├── Check: event_name == ORDER_SUCCEEDED or ORDER_FAILED? → YES
  │
  ├── StatusMapper.GetPaymentStatus(order.status)
  │     └── e.g., "CHARGED" → "Success"
  │
  ├── Build PaymentWebhook object (map all fields from order)
  │
  ├── Check: order.mandate != null && mandate_id not empty?
  │     └── If yes: attach MandateWebhook to PaymentWebhook
  │
  ├── Look up URL: Environment.GetEnvironmentVariable(order.udf5)
  │
  ├── If URL is null → CompleteMessage (no target configured)
  │
  ├── If udf5 is EV client (iQube/Creon/iQubeHDCB/EvScooter/TVSConnectEV/TVSRacing/TVSConnectFleet):
  │     ├── AesCrypto.EncryptString(key, iv, JSON payload)
  │     └── EVPostToClient(url, token, encryptedData)
  │
  └── Else (non-EV client):
        └── PaymentStatusPostToClient(url, token, paymentWebhook)
```

### Refund Event Processing

```
Run() → event_name is REFUND_INITIATED / ORDER_REFUNDED / ORDER_REFUND_FAILED
  │
  ├── Get order.refunds list
  │
  └── FOR EACH refund item in the list:
        │
        ├── Build RefundWebhook base fields (from order + gateway response)
        │
        ├── StatusMapper.GetRefundStatus(item.status)
        │
        ├── If item.unique_request_id ends with "-S":
        │     ├── Target: iceWebsiteShopify URL
        │     ├── AES Encrypt
        │     └── EVPostToClient()
        │
        ├── Else if order_id starts with "SPR-":
        │     ├── Target: TVSSparesAutoRefunds URL
        │     ├── AES Encrypt
        │     └── EVPostToClient()
        │
        └── Else (default):
              ├── Target: BookingService URL
              └── PostToClient() (plain JSON)
```

### Payout Event Processing

```
Run() → label == "ORDER"
  │
  ├── JsonConvert.DeserializeObject<PayoutsMessageBody>(message.Body)
  │
  ├── StatusMapper.GetPayoutStatus(info.status)
  │
  ├── Build PayoutWebhook object
  │
  ├── Special logic: paymentreceiveddatetime =
  │     info.updatedAt (if FULFILLMENTS_SUCCESSFUL) else empty string
  │
  ├── Look up URL: Environment.GetEnvironmentVariable(info.udf5)
  │
  └── PostToClient(url, token, payoutWebhook)
```

### Mandate Event Processing

```
Run() → event_name is MANDATE_CREATED / MANDATE_ACTIVATED / MANDATE_FAILED
  │
  ├── Get content.mandate object
  │
  ├── Build MandateWebhook object
  │
  ├── Check: mandate.order_id starts with "TE"?
  │     └── If yes:
  │           ├── AesCrypto.EncryptString(mandateWebhook JSON)
  │           └── EVPostToClient(TVSConnectEVMandate URL, token, encrypted)
  │
  └── If order_id doesn't start with "TE": no delivery happens
```

---

## 5. Database Schema

**Not applicable.** This service uses no database. It is a pure message transformer/relay.

---

## 6. Request/Response Lifecycle

### Complete Step-by-Step for a Single Message

```
 1. Azure Service Bus delivers a JSON message to the function (PeekLock mode)
    → Message is now "locked" — other instances won't pick it up

 2. Function deserializes the message body as MessageBody
    → If deserialization fails: exception thrown → message unlocks → retry

 3. Function calls GenerateToken():
    → Creates HttpClient
    → POSTs to Azure AD token endpoint (form-urlencoded body from config)
    → Deserializes response as TokenResponse
    → Returns access_token string
    → If this fails: exception thrown → message unlocks → retry

 4. Function checks message.label:
    → If "ORDER": switches to payout processing path
    → Otherwise: continues to event_name classification

 5. Function checks event_name:
    → ORDER_SUCCEEDED / ORDER_FAILED → payment path
    → REFUND_INITIATED / ORDER_REFUNDED / ORDER_REFUND_FAILED → refund path
    → MANDATE_CREATED / MANDATE_ACTIVATED / MANDATE_FAILED → mandate path

 6. Function calls StatusMapper to translate JusPay status → CPG status

 7. Function builds the outbound webhook payload object

 8. Function determines target URL from environment variable (using client code)

 9. If encryption needed: calls AesCrypto.EncryptString()
    → Decodes Base64 key and IV
    → Creates AES cipher (CBC mode)
    → Encrypts JSON string
    → Returns Base64 ciphertext

10. Function makes HTTP POST:
    → Sets Authorization: Bearer {token}
    → Optionally sets Ocp-Apim-Subscription-Key header
    → Sends JSON body (either encrypted wrapper or plain webhook)

11. Function checks response:
    → If HTTP 200: calls messageActions.CompleteMessageAsync()
       → Message is permanently removed from the queue
    → If NOT 200: returns false → message stays in queue → will be retried

12. If any exception at any step:
    → Exception is re-thrown
    → Function execution fails
    → Service Bus message lock expires
    → Message is redelivered (up to max delivery count)
    → After max retries: message goes to Dead Letter Queue
```

---

## 7. Validation Logic

### What Gets Validated (and What Doesn't)

| Check | Where | What Happens If It Fails |
|-------|-------|-------------------------|
| `messageBody != null` | After deserializing main message | Entire message is skipped (no processing, no completion) |
| `messageBody.label == "ORDER"` | Payout detection | Determines which processing path to take |
| `payoutsMessageBody != null` | After deserializing payout message | Payout processing skipped, function returns |
| `webhooks URL != null` (env var lookup) | Before posting payment | Message is completed immediately (no target = nothing to do) |
| `webhooks URL != null` (env var lookup) | Before posting payout | Payout skipped |
| `order.mandate != null && mandate_id not empty` | Before attaching mandate to payment | Mandate section simply not included in payload |
| `unique_request_id.EndsWith("-S")` | Refund routing | Determines Shopify vs other targets |
| `orderid.StartsWith("SPR-")` | Refund routing | Determines Spares vs Booking Service |
| `mandate.order_id.StartsWith("TE")` | Mandate routing | Only processes if starts with "TE" |
| `response.StatusCode == 200` | After HTTP POST | If not 200, message stays for retry |

### What Is NOT Validated (potential risks)

- No schema validation on incoming messages
- No null checks on `order.txn_detail` or `order.payment_gateway_response` before accessing their properties
- No check that the encryption key/IV are valid Base64 before using them
- No size limits on incoming messages
- No validation that `event_name` is a known event (unknown events silently fall through)

---

## 8. Error Handling

### Current Strategy

The entire function body is wrapped in a single try/catch:

```csharp
try {
    // All processing logic
} catch (Exception ex) {
    throw;  // Re-throws the exception, preserving stack trace
}
```

This means:
- **Any unhandled exception** causes the function to fail
- **Azure Functions runtime** catches it and marks the invocation as failed
- **Service Bus** does not receive a `CompleteMessage` call
- **Message lock expires** and the message is redelivered
- **After max delivery attempts** → Dead Letter Queue

### Error Scenarios and Outcomes

| Scenario | Exception Type | Result |
|----------|---------------|--------|
| Invalid JSON in message | `JsonSerializationException` | Message retries |
| Azure AD token endpoint unreachable | `HttpRequestException` | Message retries |
| Azure AD returns non-200 | `HttpRequestException` (via EnsureSuccessStatusCode) | Message retries |
| Downstream service returns 500 | No exception — returns `false` | Message retries (not completed) |
| Downstream service unreachable | `HttpRequestException` or `TaskCanceledException` | Message retries |
| Null reference (e.g., order.txn_detail is null) | `NullReferenceException` | Message retries |
| Invalid Base64 in crypto key | `FormatException` | Message retries |
| Environment variable missing (URL is null for payments) | No exception — message completed | Message completed (silent skip) |

### Dead Letter Queue

When a message exceeds its max delivery count (configured on the Service Bus queue), it moves to the Dead Letter Queue (DLQ). These messages need manual investigation — typically through Azure Portal or Service Bus Explorer.

---

## 9. Key Business Rules

### 9.1 Status Mapping (Complete Reference)

**Payment Status Mapping** (`StatusMapper.GetPaymentStatus`):

| Input (JusPay) | Output (CPG) | Business Meaning |
|----------------|-------------|------------------|
| `CHARGED` | `Success` | Payment completed successfully |
| `AUTHENTICATION_FAILED` | `Failure` | Customer failed OTP/password |
| `AUTHORIZATION_FAILED` | `Failure` | Bank rejected the transaction |
| `JUSPAY_DECLINED` | `OnHold` | JusPay itself declined (fraud check, etc.) |
| `AUTHORIZING` | `OnHold` | Bank is processing (intermediate state) |
| `STARTED` | `OnHold` | Transaction started but not completed |
| `AUTO_REFUNDED` | `OnHold` | JusPay auto-refunded (needs review) |
| `PENDING_VBV` | `InProgress` | Waiting for 3D Secure / Verified by Visa |
| `NEW` | `Initiated` | Order just created, no payment attempted |
| Any other value | `""` (empty string) | Unmapped status — empty string returned |

**Refund Status Mapping** (`StatusMapper.GetRefundStatus`):

| Input (JusPay) | Output (CPG) | Business Meaning |
|----------------|-------------|------------------|
| `SUCCESS` | `RefundConfirmed` | Refund completed |
| `PENDING` | `RefundAwaited` | Refund in progress |
| `MANUAL_REVIEW` | `RefundAwaited` | Needs manual review by ops |
| `FAILURE` | `RefundFailed` | Refund failed |

**Payout Status Mapping** (`StatusMapper.GetPayoutStatus`):

| Input (JusPay) | Output (CPG) | Business Meaning |
|----------------|-------------|------------------|
| `FULFILLMENTS_SUCCESSFUL` | `Success` | Payout completed |
| `FULFILLMENTS_FAILURE` | `Failure` | Payout failed |
| `FULFILLMENTS_MANUAL_REVIEW` | `Awaited` | Needs manual review |
| `FULFILLMENTS_CANCELLED` | `Rejected` | Payout was cancelled |

### 9.2 Client Routing Rules

**Rule 1 — Payout Detection**: If `message.label == "ORDER"`, the message is a payout (not a regular payment). Process it differently using `PayoutsMessageBody` structure.

**Rule 2 — EV Client Encryption**: The following clients get AES-encrypted payloads:
- iQubeWebsite, CreonWebsite, iQubeHDCB, EvScooter, TVSConnectEV, TVSRacing, TVSConnectFleet

**Rule 3 — Refund Routing by ID Pattern**:
- If `unique_request_id` ends with `-S` → Shopify (encrypted)
- If `order_id` starts with `SPR-` → TVS Spares (encrypted)
- Otherwise → Booking Service (plain)

**Rule 4 — Mandate Routing**: Only mandates with `order_id` starting with `TE` are processed and forwarded to TVSConnectEVMandate.

**Rule 5 — Payout Received DateTime**: The `paymentreceiveddatetime` field is only populated when the payout status is `FULFILLMENTS_SUCCESSFUL`. Otherwise it's an empty string.

### 9.3 AES Encryption Details

| Property | Value |
|----------|-------|
| Algorithm | AES |
| Mode | CBC (Cipher Block Chaining) |
| Key Size | 128 bits (16 bytes) |
| IV Size | 128 bits (16 bytes) |
| Padding | PKCS7 (default .NET AES behavior) |
| Key Format | Base64-encoded string (from environment variable) |
| IV Format | Base64-encoded string (from environment variable) |
| Output Format | Base64-encoded ciphertext |

---

## 10. Configuration Handling

### How Configuration Works

All configuration is read from **environment variables** using `Environment.GetEnvironmentVariable()`. In Azure, these are set as App Settings on the Function App. Locally, they come from `local.settings.json`.

### Configuration Categories

**Connection Strings:**

| Variable | Purpose |
|----------|---------|
| `AzureWebJobsServiceBus` | Service Bus connection string (triggers the function) |
| `AzureWebJobsStorage` | Azure Storage connection (required by Functions runtime) |

**Authentication:**

| Variable | Purpose |
|----------|---------|
| `TokenUrl` | Azure AD OAuth2 token endpoint URL |
| `TokenRequest` | Form-urlencoded body for token request (contains client_id, client_secret, scope) |

**Encryption:**

| Variable | Purpose |
|----------|---------|
| `CryptoKey` | Base64-encoded AES-128 key |
| `CryptoVector` | Base64-encoded AES IV (16 bytes) |

**Client Endpoint URLs:**

| Variable | Target Client |
|----------|--------------|
| `iQubeWebsite` | TVS iQube EV payment callbacks |
| `CreonWebsite` | TVS Creon EV payment callbacks |
| `iQubeHDCB` | iQube HDCB payment callbacks |
| `EvScooter` | EV Scooter payment callbacks |
| `TVSConnectEV` | TVS Connect EV subscription payments |
| `TVSRacing` | TVS Racing platform payments |
| `TVSConnectFleet` | TVS Fleet payments |
| `BookingService` | Booking Service refund callbacks |
| `BookingServiceDREF` | Booking Service (DREF variant) |
| `iceWebsite` | ICE website webhooks |
| `iceWebsiteShopify` | Shopify refund callbacks |
| `TVSSparesAutoRefunds` | TVS Spares auto-refund callbacks |
| `TVSConnectEVMandate` | TVS Connect EV mandate callbacks |

**Runtime:**

| Variable | Purpose |
|----------|---------|
| `FUNCTIONS_WORKER_RUNTIME` | Must be `dotnet-isolated` |

### host.json Configuration

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      },
      "enableLiveMetricsFilters": true
    }
  }
}
```

This means:
- Application Insights sampling is enabled (not all telemetry is sent — reduces cost)
- Request-type telemetry is excluded from sampling (all requests are logged)
- Live Metrics Stream filters are enabled

---

## 11. Field Mapping Reference (Source → Destination)

### Payment Event: JusPay Order → PaymentWebhook

| PaymentWebhook Field | Source | Notes |
|---------------------|--------|-------|
| `paymentinitiationcode` | `order.order_id` | |
| `orderid` | `order.order_id` | Same as above |
| `orderamount` | `order.amount` | Decimal |
| `effectiveamount` | `order.effective_amount` | Decimal |
| `transactionid` | `order.txn_id` | |
| `transactiondate` | `order.date_created` | DateTime |
| `status` | `StatusMapper.GetPaymentStatus(order.status)` | Translated |
| `bankreferencenumber` | `order.txn_uuid` | |
| `clientapptransactionid` | `order.udf2` | |
| `bookingid` | `order.udf6` | |
| `paymentmode` | `order.payment_method_type` | |
| `currency` | `order.currency` | |
| `paymenttype` | `order.udf4` | |
| `paymentgateway` | `order.txn_detail.gateway` | |
| `statuscode` | `order.payment_gateway_response.resp_code` | |
| `statusmessage` | `order.payment_gateway_response.resp_message` | |
| `mandate` | Built from `order.mandate` | Only if mandate_id is not null/empty |

### Refund Event: JusPay Refund Item → RefundWebhook

| RefundWebhook Field | Source | Notes |
|--------------------|--------|-------|
| `paymentinitiationcode` | `order.txn_detail.order_id` | |
| `orderid` | `order.txn_detail.order_id` | |
| `orderamount` | `refund_item.amount` | Per-refund amount |
| `transactionid` | `order.payment_gateway_response.epg_txn_id` | |
| `transactiondate` | `order.payment_gateway_response.created` | |
| `status` | `"refunded"` (hardcoded) | Always this string |
| `bookingid` | `order.udf6` | |
| `clientapptransactionid` | `order.udf2` | |
| `paymenttype` | `order.udf4` | |
| `statusmessage` | `refund_item.error_message` | Null on success |
| `refundreferenceno` | `refund_item.unique_request_id` | |
| `refundstatus` | `StatusMapper.GetRefundStatus(refund_item.status)` | Translated |
| `refundbankreferenceno` | `refund_item.ref` | Bank reference |
| `refundcompletiondate` | `refund_item.last_updated` | DateTime |

### Payout Event: PayoutsMessageBody → PayoutWebhook

| PayoutWebhook Field | Source | Notes |
|--------------------|--------|-------|
| `clientcode` | `info.udf5` | |
| `clientappuserid` | `info.udf1` | |
| `clientrefundreferencenumber` | `info.udf2` | |
| `refundreferencenumber` | `info.merchantOrderId` | |
| `refundamount` | `info.amount` | Integer |
| `payrefno` | `info.merchantOrderId` | Same as refundreferencenumber |
| `refundstatus` | `StatusMapper.GetPayoutStatus(info.status)` | Translated |
| `remarks` | `message.value` | Top-level field |
| `transactionid` | `info.id` | |
| `transactiondate` | `message.createdAt` | Top-level field |
| `paymentreceiveddatetime` | `info.updatedAt` or `""` | Only if FULFILLMENTS_SUCCESSFUL |

### Mandate Event: JusPay Mandate → MandateWebhook

| MandateWebhook Field | Source | Notes |
|---------------------|--------|-------|
| `token` | `mandate.mandate_token` | |
| `status` | `mandate.status` | Not translated — passed as-is |
| `id` | `mandate.mandate_id` | |
| `startdate` | `mandate.start_date` | |
| `enddate` | `mandate.end_date` | |
| `maxamount` | `mandate.max_amount.ToString()` | |
| `frequency` | `mandate.frequency` | |
| `rulevalue` | Not mapped (always null) | Field exists but never populated |
| `amountrule` | `mandate.amount_rule` | |
| `orderid` | `mandate.order_id` | |

---

## 12. HTTP Delivery Methods (Comparison)

| Method | Used For | Headers | Body Format |
|--------|----------|---------|-------------|
| `PostToClient()` | Payout webhooks, Booking Service refunds | Bearer token + APIM subscription key | Raw JSON object |
| `EVPostToClient()` | EV client payments, Shopify/Spares refunds, Mandates | Bearer token only | `{ "data": "<encrypted>", "clientcode": "" }` |
| `PaymentStatusPostToClient()` | Non-EV payment webhooks | Bearer token + APIM subscription key | Typed PaymentWebhook JSON |

All three methods:
- Create a new `HttpClient` per call (no connection pooling)
- Return `true` only if response is HTTP 200
- Throw on network-level exceptions
- Read the response body (but don't use it for anything)

---

*This document helps new engineering vendors understand the implementation. No secrets or credentials are included.*

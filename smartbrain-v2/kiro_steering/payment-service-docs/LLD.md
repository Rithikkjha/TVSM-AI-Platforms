# Low Level Design (LLD) — PaymentService

**TVS Motor Company Ltd — Common Backend Services**

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | PaymentService |
| Team | Common Backend Services |
| Tech Lead | Arun Kumar Reddy |
| Product Owner | Avinash Kumar |
| Developer | Rachel Bennet |

---

## 2. Code Structure

```
PaymentService/
├── Constants/                     ← String constants used throughout the code
│   ├── ClientCode.cs              ← Names of all downstream clients (11 total)
│   ├── EventName.cs               ← JusPay event type strings (14 events)
│   ├── General.cs                 ← Config keys, HTTP headers, content types
│   ├── JusPayPaymentStatus.cs     ← JusPay payment status strings (9 values)
│   ├── JusPayPayoutStatus.cs      ← JusPay payout status strings (4 values)
│   └── JusPayRefundStatus.cs      ← JusPay refund status strings (4 values)
│
├── Enums/                         ← Internal status enumerations
│   ├── CPGPaymentStatus.cs        ← Payment outcomes (Success, Failure, OnHold, etc.)
│   └── CPGRefundStatus.cs         ← Refund + Payout outcomes
│
├── Functions/                     ← Azure Function trigger (the "main" code)
│   └── JusPayWebhooks.cs         ← ALL processing logic lives here
│
├── Helpers/                       ← Utility code
│   └── AesCrypto.cs              ← AES-128-CBC encryption
│
├── Mappers/                       ← Status translation
│   └── StatusMapper.cs           ← 3 methods: payment, refund, payout mapping
│
├── Models/                        ← Data transfer objects
│   ├── MessageBody.cs            ← Inbound: main JusPay message structure
│   ├── PayoutsMessageBody.cs     ← Inbound: payout-specific message structure
│   ├── MandateBody.cs            ← Inbound: mandate data from JusPay
│   ├── PaymentWebhook.cs         ← Outbound: payment callback payload
│   ├── RefundWebhook.cs          ← Outbound: refund callback payload
│   ├── PayoutWebhook.cs          ← Outbound: payout callback payload
│   ├── MandateWebhook.cs         ← Outbound: mandate callback payload
│   ├── TokenRequest.cs           ← OAuth2 token request shape
│   └── TokenResponse.cs          ← OAuth2 token response shape
│
├── payment-service-docs/          ← Documentation
├── Program.cs                     ← Application startup (host builder, DI)
├── Startup.cs                     ← FunctionsStartup (empty, unused — app uses Program.cs)
├── PaymentService.csproj          ← .NET project file (dependencies)
├── PaymentService.sln             ← Visual Studio solution file
├── host.json                      ← Azure Functions runtime config
└── local.settings.json            ← Local dev config (NEVER deployed)
```

---

## 3. Module Breakdown

### Functions Module (1 file)

**File**: `Functions/JusPayWebhooks.cs`

Contains:
- The Azure Function entry point (`Run` method)
- All event classification logic (payment vs refund vs payout vs mandate)
- Token generation logic
- Three HTTP delivery methods (plain, encrypted, payment-specific)

### Models Module (9 files)

| File | Direction | Used For |
|------|-----------|----------|
| `MessageBody.cs` | Inbound | Main JusPay message (`Order`, `Content`, `Refund`, `TxnDetail`, `PaymentGatewayResponse`) |
| `MandateBody.cs` | Inbound | Mandate data from JusPay (`Mandate` class) |
| `PayoutsMessageBody.cs` | Inbound | Payout-specific message (`PayoutsMessageBody` + `Info`) |
| `PaymentWebhook.cs` | Outbound | Payment callback payload |
| `RefundWebhook.cs` | Outbound | Refund callback payload |
| `PayoutWebhook.cs` | Outbound | Payout callback payload |
| `MandateWebhook.cs` | Outbound | Mandate callback payload |
| `TokenRequest.cs` | Internal | OAuth2 token request shape (unused — token body is raw string) |
| `TokenResponse.cs` | Internal | OAuth2 token response deserialization |

### Mappers Module (1 file)

**File**: `Mappers/StatusMapper.cs`

Three static methods that map JusPay status strings to internal status strings. Pure logic, no side effects.

### Helpers Module (1 file)

**File**: `Helpers/AesCrypto.cs`

One static method that encrypts plaintext with AES-128-CBC and returns Base64.

### Constants Module (6 files)

| File | What's Inside |
|------|--------------|
| `ClientCode.cs` | 11 string constants — one per downstream client |
| `EventName.cs` | 14 string constants — one per JusPay event type |
| `General.cs` | Config key names, content type, auth header names, APIM key |
| `JusPayPaymentStatus.cs` | 9 string constants for JusPay payment statuses |
| `JusPayRefundStatus.cs` | 4 string constants for JusPay refund statuses |
| `JusPayPayoutStatus.cs` | 4 string constants for JusPay payout statuses |

### Enums Module (2 files)

| File | What's Inside |
|------|--------------|
| `CPGPaymentStatus.cs` | `PaymentStatusEnum` — 16 possible payment outcomes |
| `CPGRefundStatus.cs` | `RefundStatusEnum` (4 values) + `PayoutStatusEnum` (5 values) |

---

## 4. Class Responsibilities

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

| Method | Input Example | Output Example |
|--------|--------------|----------------|
| `GetPaymentStatus("CHARGED")` | JusPay status | `"Success"` |
| `GetRefundStatus("SUCCESS")` | JusPay refund status | `"RefundConfirmed"` |
| `GetPayoutStatus("FULFILLMENTS_SUCCESSFUL")` | JusPay payout status | `"Success"` |

### AesCrypto

| Responsibility | Details |
|---------------|---------|
| Encrypt payloads | AES-128-CBC with PKCS7 padding, outputs Base64 string |

---

## 5. Internal Processing Logic

### Payment Event Processing

```
Run() is called with ServiceBusReceivedMessage
  │
  ├── JsonConvert.DeserializeObject<MessageBody>(message.Body)
  ├── GenerateToken() → POST to Azure AD → get access_token
  ├── Check: label == "ORDER"? → NO (payment, not payout)
  ├── Check: event_name == ORDER_SUCCEEDED or ORDER_FAILED? → YES
  ├── StatusMapper.GetPaymentStatus(order.status)
  ├── Build PaymentWebhook object (map all fields from order)
  ├── Check: order.mandate != null && mandate_id not empty?
  │     └── If yes: attach MandateWebhook to PaymentWebhook
  ├── Look up URL: Environment.GetEnvironmentVariable(order.udf5)
  ├── If URL is null → CompleteMessage (no target configured)
  ├── If udf5 is EV client:
  │     ├── AesCrypto.EncryptString(key, iv, JSON payload)
  │     └── EVPostToClient(url, token, encryptedData)
  └── Else (non-EV client):
        └── PaymentStatusPostToClient(url, token, paymentWebhook)
```

### Refund Event Processing

```
Run() → event_name is REFUND_INITIATED / ORDER_REFUNDED / ORDER_REFUND_FAILED
  │
  ├── Get order.refunds list
  └── FOR EACH refund item in the list:
        ├── Build RefundWebhook base fields
        ├── StatusMapper.GetRefundStatus(item.status)
        ├── If item.unique_request_id ends with "-S":
        │     → Shopify (iceWebsiteShopify) — encrypted
        ├── Else if order_id starts with "SPR-":
        │     → TVS Spares (TVSSparesAutoRefunds) — encrypted
        └── Else (default):
              → BookingService — plain JSON
```

### Payout Event Processing

```
Run() → label == "ORDER"
  │
  ├── JsonConvert.DeserializeObject<PayoutsMessageBody>(message.Body)
  ├── StatusMapper.GetPayoutStatus(info.status)
  ├── Build PayoutWebhook object
  ├── paymentreceiveddatetime = info.updatedAt (if FULFILLMENTS_SUCCESSFUL) else ""
  ├── Look up URL: Environment.GetEnvironmentVariable(info.udf5)
  └── PostToClient(url, token, payoutWebhook)
```

### Mandate Event Processing

```
Run() → event_name is MANDATE_CREATED / MANDATE_ACTIVATED / MANDATE_FAILED
  │
  ├── Get content.mandate object
  ├── Build MandateWebhook object
  ├── Check: mandate.order_id starts with "TE"?
  │     └── If yes: encrypt → EVPostToClient(TVSConnectEVMandate URL)
  └── If not "TE": no delivery (silently ignored)
```

---

## 6. Database Schema

**Not applicable.** This service uses no database. It is a pure message transformer/relay.

---

## 7. Status Mapping (Complete Reference)

### Payment Status Mapping

| Input (JusPay) | Output (Internal) | Business Meaning |
|----------------|-------------|------------------|
| `CHARGED` | `Success` | Payment completed successfully |
| `AUTHENTICATION_FAILED` | `Failure` | Customer failed OTP/password |
| `AUTHORIZATION_FAILED` | `Failure` | Bank rejected the transaction |
| `JUSPAY_DECLINED` | `OnHold` | JusPay itself declined (fraud check) |
| `AUTHORIZING` | `OnHold` | Bank is processing (intermediate) |
| `STARTED` | `OnHold` | Transaction started but not completed |
| `AUTO_REFUNDED` | `OnHold` | JusPay auto-refunded (needs review) |
| `PENDING_VBV` | `InProgress` | Waiting for 3D Secure / VBV |
| `NEW` | `Initiated` | Order just created, no payment attempted |
| Any other value | `""` (empty string) | Unmapped status |

### Refund Status Mapping

| Input (JusPay) | Output (Internal) | Business Meaning |
|----------------|-------------|------------------|
| `SUCCESS` | `RefundConfirmed` | Refund completed |
| `PENDING` | `RefundAwaited` | Refund in progress |
| `MANUAL_REVIEW` | `RefundAwaited` | Needs manual review by ops |
| `FAILURE` | `RefundFailed` | Refund failed |

### Payout Status Mapping

| Input (JusPay) | Output (Internal) | Business Meaning |
|----------------|-------------|------------------|
| `FULFILLMENTS_SUCCESSFUL` | `Success` | Payout completed |
| `FULFILLMENTS_FAILURE` | `Failure` | Payout failed |
| `FULFILLMENTS_MANUAL_REVIEW` | `Awaited` | Needs manual review |
| `FULFILLMENTS_CANCELLED` | `Rejected` | Payout was cancelled |

---

## 8. Field Mapping Reference

### Payment: JusPay Order → PaymentWebhook

| PaymentWebhook Field | Source | Notes |
|---------------------|--------|-------|
| `paymentinitiationcode` | `order.order_id` | |
| `orderid` | `order.order_id` | Same as above |
| `orderamount` | `order.amount` | Decimal — total order amount |
| `effectiveamount` | `order.effective_amount` | Decimal — amount actually charged |
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

### Refund: JusPay Refund Item → RefundWebhook

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

### Payout: PayoutsMessageBody → PayoutWebhook

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

### Mandate: JusPay Mandate → MandateWebhook

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

## 9. HTTP Delivery Methods

| Method | Used For | Headers | Body Format |
|--------|----------|---------|-------------|
| `PostToClient()` | Payout webhooks, Booking Service refunds | Bearer + APIM key | Raw JSON object |
| `EVPostToClient()` | EV client payments, Shopify/Spares refunds, Mandates | Bearer only | `{ "data": "<encrypted>", "clientcode": "" }` |
| `PaymentStatusPostToClient()` | Non-EV payment webhooks | Bearer + APIM key | Typed PaymentWebhook JSON |

All three methods:
- Create a new `HttpClient` per call (no connection pooling)
- Return `true` only if response is HTTP 200
- Throw on network-level exceptions
- Read the response body (but don't use it)

---

## 10. Validation Logic

### What Gets Validated

| Check | Where | What Happens If It Fails |
|-------|-------|-------------------------|
| `messageBody != null` | After deserializing | Entire message skipped |
| `messageBody.label == "ORDER"` | Payout detection | Determines processing path |
| `payoutsMessageBody != null` | After deserializing payout | Payout processing skipped |
| `webhooks URL != null` (payment) | Before posting | Message completed immediately |
| `webhooks URL != null` (payout) | Before posting | Payout skipped |
| `order.mandate != null && mandate_id not empty` | Before attaching mandate | Mandate section not included |
| `unique_request_id.EndsWith("-S")` | Refund routing | Shopify vs other |
| `orderid.StartsWith("SPR-")` | Refund routing | Spares vs Booking Service |
| `mandate.order_id.StartsWith("TE")` | Mandate routing | Only TE orders processed |
| `response.StatusCode == 200` | After HTTP POST | If not 200, message stays for retry |

### What Is NOT Validated (potential risks)

- No schema validation on incoming messages
- No null checks on `order.txn_detail` or `order.payment_gateway_response` before accessing properties
- No check that encryption key/IV are valid Base64
- No size limits on incoming messages
- No validation that `event_name` is a known event (unknown events silently fall through)

---

## 11. Error Handling

The entire function body is wrapped in a single try/catch:

```csharp
try {
    // All processing logic
} catch (Exception ex) {
    throw;  // Re-throws, preserving stack trace
}
```

| Scenario | Exception Type | Result |
|----------|---------------|--------|
| Invalid JSON in message | `JsonSerializationException` | Message retries |
| Azure AD unreachable | `HttpRequestException` | Message retries |
| Azure AD returns non-200 | `HttpRequestException` (EnsureSuccessStatusCode) | Message retries |
| Downstream returns 500 | No exception — returns `false` | Message retries (not completed) |
| Downstream unreachable | `HttpRequestException` or `TaskCanceledException` | Message retries |
| Null reference (missing field) | `NullReferenceException` | Message retries |
| Invalid Base64 in crypto key | `FormatException` | Message retries |
| Env var URL is null (payment) | No exception — message completed | Silent skip |

Messages that exceed max delivery count go to the Dead Letter Queue for manual investigation.

---

## 12. Configuration Management

All configuration is read from **environment variables** via `Environment.GetEnvironmentVariable()`. In Azure, these are App Settings. Locally, from `local.settings.json`.

### Connection Strings

| Variable | Purpose |
|----------|---------|
| `AzureWebJobsServiceBus` | Service Bus connection string |
| `AzureWebJobsStorage` | Azure Storage (required by runtime) |

### Authentication

| Variable | Purpose |
|----------|---------|
| `TokenUrl` | Azure AD OAuth2 token endpoint URL |
| `TokenRequest` | Form-urlencoded body (client_id, secret, scope, grant_type) |

### Encryption

| Variable | Purpose |
|----------|---------|
| `CryptoKey` | Base64-encoded AES-128 key |
| `CryptoVector` | Base64-encoded AES IV (16 bytes) |

### API Gateway

| Variable | Purpose |
|----------|---------|
| `OcpApimSubscriptionValue` | APIM subscription key |

### Client Endpoint URLs

| Variable | Target Client |
|----------|--------------|
| `iQubeWebsite` | TVS iQube EV |
| `CreonWebsite` | TVS Creon EV |
| `iQubeHDCB` | iQube HDCB |
| `EvScooter` | EV Scooter |
| `TVSConnectEV` | TVS Connect EV subscriptions |
| `TVSRacing` | TVS Racing |
| `TVSConnectFleet` | TVS Fleet |
| `BookingService` | Booking Service refunds |
| `BookingServiceDREF` | Booking Service (DREF variant) |
| `iceWebsite` | ICE website |
| `iceWebsiteShopify` | Shopify refunds |
| `TVSSparesAutoRefunds` | TVS Spares auto-refund |
| `TVSConnectEVMandate` | TVS Connect EV mandates |

---

## 13. AES Encryption Details

| Property | Value |
|----------|-------|
| Algorithm | AES |
| Mode | CBC (Cipher Block Chaining) |
| Key Size | 128 bits (16 bytes) |
| IV Size | 128 bits (16 bytes) |
| Padding | PKCS7 (default .NET AES) |
| Key Format | Base64-encoded string (from env var) |
| IV Format | Base64-encoded string (from env var) |
| Output Format | Base64-encoded ciphertext |

---

## 14. Testing Strategy

### Current State

No automated unit tests exist. Testing is manual:

1. Start function locally (`func start`)
2. Send test messages to `cpg-juspay` queue via Azure Portal / Service Bus Explorer
3. Monitor function logs for processing output
4. Verify downstream service received the callback

### Recommended Improvements

| Area | Suggestion |
|------|-----------|
| Unit tests | Test StatusMapper methods, AesCrypto, payload building |
| Integration tests | Mock Service Bus + downstream, verify end-to-end flow |
| Contract tests | Validate inbound message schema against expected format |
| Load tests | Verify behavior under high message volume |

---

## 15. Known Business Rules

1. **Payout Detection**: `message.label == "ORDER"` → payout flow (not regular payment)
2. **EV Client Encryption**: iQubeWebsite, CreonWebsite, iQubeHDCB, EvScooter, TVSConnectEV, TVSRacing, TVSConnectFleet get AES-encrypted payloads
3. **Refund Routing by ID Pattern**: `-S` suffix → Shopify; `SPR-` prefix → Spares; default → BookingService
4. **Mandate Routing**: Only `TE` prefix orders are processed
5. **Payout DateTime**: `paymentreceiveddatetime` only populated for `FULFILLMENTS_SUCCESSFUL`
6. **Message Completion**: Only on HTTP 200 from downstream; all other outcomes → retry

---

*This document helps engineering teams understand the implementation. No secrets or credentials are included.*

# PaymentService


## Product Context


# Product: JusPay Payment Webhook Relay Service

## What This Service Does

This is a payment webhook relay/router for TVS Motor Company. It sits between the JusPay payment gateway and multiple internal TVS applications, acting as a centralized message broker that normalizes, transforms, and routes payment event notifications to the correct downstream consumer.

## Core Business Flow

1. JusPay publishes payment/refund/payout/mandate event notifications to an Azure Service Bus queue (`cpg-juspay`)
2. This service consumes those messages, maps JusPay-specific statuses to internal CPG (Common Payment Gateway) statuses
3. The normalized payload is forwarded to the appropriate downstream TVS application via HTTP POST
4. For EV-related clients, the payload is AES-encrypted before forwarding
5. Messages are only acknowledged (completed) on successful downstream delivery; otherwise they remain in the queue for retry

## Domain Entities

### Payment (Order)
Represents a payment transaction. Key fields: order_id, amount, effective_amount, status, payment method, gateway, currency. Mapped from JusPay ORDER_SUCCEEDED / ORDER_FAILED events.

### Refund
Represents a refund against a payment. Key fields: unique_request_id, amount, status, bank reference. Mapped from REFUND_INITIATED / ORDER_REFUNDED / ORDER_REFUND_FAILED events. A single order can have multiple refunds.

### Payout (Fulfillment)
Represents an outbound payout/disbursement. Key fields: merchantOrderId, amount, status, customer ID. Identified by messages with label "ORDER" and FULFILLMENTS_* statuses.

### Mandate
Represents a recurring payment authorization (autopay). Key fields: mandate_id, mandate_token, start/end dates, max_amount, frequency. Mapped from MANDATE_CREATED / MANDATE_ACTIVATED / MANDATE_FAILED events.

## Integrations

### Upstream (Source)
- **JusPay Payment Gateway** → publishes events to Azure Service Bus queue `cpg-juspay`

### Downstream (Consumers)
- **TVS EV Web API** — iQubeWebsite, CreonWebsite, iQubeHDCB, EvScooter, TVSConnectEV, TVSRacing (AES-encrypted payloads)
- **TVS Booking Service** — receives plain JSON refund status callbacks
- **TVS Shopify E-commerce** (iceWebsiteShopify) — receives encrypted refund webhooks for orders ending in "-S"
- **TVS Spares/Parts** (TVSSparesAutoRefunds) — receives encrypted refund webhooks for orders prefixed "SPR-"
- **TVS Connect EV Mandate** — receives encrypted mandate webhooks for orders prefixed "TE"

### Authentication
- **Microsoft Identity Platform (Azure AD)** — OAuth2 client_credentials flow to obtain bearer tokens for downstream API calls
- **Azure API Management** — Ocp-Apim-Subscription-Key header for non-EV downstream calls

## Business Rules

### Status Mapping
- JusPay payment statuses are mapped to internal CPG statuses (Success, Failure, OnHold, InProgress, Initiated)
- JusPay refund statuses map to CPG refund statuses (RefundConfirmed, RefundAwaited, RefundFailed)
- JusPay payout statuses map to CPG payout statuses (Success, Failure, Awaited, Rejected)

### Client Routing Logic
- The `udf5` field in the JusPay payload identifies the target client application
- Client webhook URLs are stored as environment variables keyed by client code
- EV clients receive AES-encrypted payloads; other clients receive plain JSON

### Refund Routing
- Refund unique_request_id ending in "-S" → routed to Shopify endpoint
- Order ID starting with "SPR-" → routed to TVS Spares endpoint
- All other refunds → routed to Booking Service

### Mandate Routing
- Only mandates with order_id starting with "TE" are forwarded (to TVSConnectEVMandate)

### Message Acknowledgment
- Messages are completed (removed from queue) only after successful downstream delivery
- If downstream call fails, the message remains in the queue for Service Bus retry
- If no webhook URL is configured for a client, the message is completed (dropped silently)



## Code Structure


# Project Structure

## Directory Layout

```
PaymentService/
├── Functions/
│   └── JusPayWebhooks.cs        # Single Azure Function — Service Bus trigger, all routing logic
├── Models/
│   ├── MessageBody.cs            # Inbound JusPay message DTOs (Order, Refund, Mandate, etc.)
│   ├── PayoutsMessageBody.cs     # Inbound payout-specific message DTO
│   ├── PaymentWebhook.cs         # Outbound payment webhook DTO
│   ├── RefundWebhook.cs          # Outbound refund webhook DTO
│   ├── PayoutWebhook.cs          # Outbound payout webhook DTO
│   ├── MandateWebhook.cs         # Outbound mandate webhook DTO
│   ├── MandateBody.cs            # Mandate entity model
│   ├── TokenRequest.cs           # OAuth token request DTO
│   └── TokenResponse.cs          # OAuth token response DTO
├── Constants/
│   ├── ClientCode.cs             # Client application identifiers (iQubeWebsite, BookingService, etc.)
│   ├── EventName.cs              # JusPay event name strings (ORDER_SUCCEEDED, REFUND_INITIATED, etc.)
│   ├── General.cs                # Misc constants (env var keys, HTTP headers, content types)
│   ├── JusPayPaymentStatus.cs    # JusPay payment status strings (CHARGED, AUTHENTICATION_FAILED, etc.)
│   ├── JusPayPayoutStatus.cs     # JusPay payout status strings (FULFILLMENTS_SUCCESSFUL, etc.)
│   └── JusPayRefundStatus.cs     # JusPay refund status strings (SUCCESS, PENDING, FAILURE, etc.)
├── Enums/
│   ├── CPGPaymentStatus.cs       # Internal payment status enum (Success, Failure, OnHold, etc.)
│   └── CPGRefundStatus.cs        # Internal refund + payout status enums
├── Mappers/
│   └── StatusMapper.cs           # JusPay → CPG status translation (payment, refund, payout)
├── Helpers/
│   └── AesCrypto.cs              # AES-128-CBC encryption for EV client payloads
├── Program.cs                    # .NET 8 isolated worker host builder
├── Startup.cs                    # Legacy FunctionsStartup (empty, vestigial)
├── PaymentService.csproj         # Project file — .NET 8, Azure Functions v4 isolated
├── PaymentService.sln            # Solution file
├── host.json                     # Azure Functions host config (App Insights sampling)
├── local.settings.json           # Local dev settings (connection strings, client URLs, keys)
└── Properties/
    └── ServiceDependencies/      # ARM templates for UAT and PRD deployments
```

## Module Dependencies

```
JusPayWebhooks (Function)
├── Models/MessageBody          — deserialize inbound Service Bus messages
├── Models/PayoutsMessageBody   — deserialize payout-specific messages
├── Models/PaymentWebhook       — build outbound payment payloads
├── Models/RefundWebhook        — build outbound refund payloads
├── Models/PayoutWebhook        — build outbound payout payloads
├── Models/MandateWebhook       — build outbound mandate payloads
├── Models/TokenResponse        — parse OAuth token response
├── Constants/EventName         — match event types
├── Constants/ClientCode        — identify client routing targets
├── Constants/General           — env var keys, HTTP constants
├── Constants/JusPayPayoutStatus — check payout completion status
├── Mappers/StatusMapper        — translate statuses
│   ├── Constants/JusPayPaymentStatus
│   ├── Constants/JusPayRefundStatus
│   ├── Constants/JusPayPayoutStatus
│   ├── Enums/CPGPaymentStatus
│   └── Enums/CPGRefundStatus
└── Helpers/AesCrypto           — encrypt payloads for EV clients
```

## Architectural Decisions

### Single Function, Procedural Routing
All webhook processing lives in one function (`JusPayWebhooks.Run`). Event type determines the code path via if/else branching. This keeps deployment simple but concentrates complexity in one file.

### No Dependency Injection for Business Logic
HTTP clients, token generation, and posting logic are instance methods on the function class. No interfaces, no DI registration. Configuration is read directly from `Environment.GetEnvironmentVariable`.

### Message Completion as Delivery Guarantee
The Service Bus message is only completed after a successful HTTP POST to the downstream client. This leverages Service Bus's built-in retry (peek-lock) for at-least-once delivery.

### Two Posting Patterns
- `PostToClient` / `PaymentStatusPostToClient` — plain JSON with Bearer token + APIM subscription key
- `EVPostToClient` — AES-encrypted payload wrapped in a dictionary (`{ "data": "...", "clientcode": "" }`)

### Environment-Driven Client Configuration
Downstream webhook URLs are stored as environment variables keyed by client code. Adding a new client requires only a new env var — no code change for routing (assuming it fits an existing pattern).



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Runtime | .NET 8.0 (C#) |
| Hosting | Azure Functions v4 (isolated worker model) |
| Trigger | Azure Service Bus (queue: `cpg-juspay`) |
| Telemetry | Application Insights |
| Serialization | Newtonsoft.Json |
| Encryption | System.Security.Cryptography (AES-128-CBC) |
| Auth (outbound) | OAuth2 client_credentials via Microsoft Identity Platform |
| API Gateway | Azure API Management (Ocp-Apim-Subscription-Key) |
| Deployment | Azure Web Deploy (ARM templates for UAT + PRD) |

## Key NuGet Packages

- `Microsoft.Azure.Functions.Worker` 2.0.0 — isolated worker SDK
- `Microsoft.Azure.Functions.Worker.Extensions.ServiceBus` 5.22.0 — Service Bus trigger binding
- `Microsoft.Azure.Functions.Worker.Extensions.Http.AspNetCore` 2.0.0 — HTTP support
- `Microsoft.ApplicationInsights.WorkerService` 2.22.0 — telemetry
- `Microsoft.Extensions.Configuration` 8.0.0 — configuration

## Coding Conventions

### Naming
- Model properties use **lowercase** names to match JusPay JSON payloads directly (no `[JsonProperty]` attributes needed)
- Constants classes use **PascalCase** for class names and **UPPER_CASE** or **PascalCase** for constant values
- Enums use **PascalCase** values

### Project Settings
- Nullable reference types enabled (`<Nullable>enable</Nullable>`)
- Implicit usings enabled
- Output type: Exe (isolated worker)

### Configuration
- All configuration via `Environment.GetEnvironmentVariable()` — no IOptions/IConfiguration injection
- Environment variable keys match client code names (e.g., `iQubeWebsite` → URL)
- Secrets (keys, connection strings) stored as environment variables

### Model Design
- Plain DTOs with auto-properties, no validation attributes
- Separate models for inbound (MessageBody, PayoutsMessageBody) and outbound (PaymentWebhook, RefundWebhook, etc.)
- No base classes or interfaces on models

## Patterns

### Message Processing
1. Deserialize Service Bus message body to `MessageBody`
2. Generate OAuth token for downstream calls
3. Branch on `label` (payout) or `event_name` (payment/refund/mandate)
4. Map JusPay status → CPG status via `StatusMapper`
5. Build outbound webhook DTO
6. Determine client URL from environment variables
7. POST to client (encrypted or plain depending on client type)
8. Complete message on success

### Status Mapping
Switch-based mapping in `StatusMapper` — each JusPay status string maps to a CPG enum value returned as a string. Returns empty string for unmapped statuses.

### Encryption
AES-128-CBC encryption via `AesCrypto.EncryptString`. Key and IV from environment variables (Base64-encoded). Used for EV client payloads to add transport-layer security beyond HTTPS.

## Error Handling

### Current Approach
- Try/catch blocks with `throw;` (re-throw without modification)
- No logging in catch blocks — relies on Azure Functions runtime to log unhandled exceptions to Application Insights
- Failed messages remain in Service Bus queue (not completed) for automatic retry
- No dead-letter queue handling in code (relies on Service Bus DLQ configuration)

### Known Risks
- `.Result` calls on async methods inside an async function — potential deadlock in certain synchronization contexts
- `HttpClient` instantiated per request — should use `IHttpClientFactory` for connection pooling
- No explicit timeout configuration on HTTP calls
- No circuit breaker or retry policy for downstream HTTP calls

## Testing

- No test project or test files exist in the repository
- No test framework configured
- When adding tests, use xUnit (standard for .NET Azure Functions) with Moq for mocking

## Deployment

### Environments
- **UAT**: `tvsmazcmnsvcftauat01` (Azure Function App)
- **PRD**: `tvsmazcmnsvcftaprd01-justpay-api` (Azure Function App)

### Infrastructure
- ARM templates in `Properties/ServiceDependencies/` define:
  - Application Insights resource
  - Storage account
  - Function App deployment profile
- `local.settings.json` is excluded from publish (`CopyToPublishDirectory: Never`)

### Configuration Management
- All client URLs, crypto keys, Service Bus connection strings, and OAuth credentials are environment variables
- Different values per environment (UAT vs PRD) managed via Azure Function App Settings


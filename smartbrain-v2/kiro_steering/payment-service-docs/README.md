# PaymentService

**Version:** 1.0.0 | **Last Updated:** June 22, 2026  
**Runtime:** .NET 8 (Isolated Worker) | **Hosting:** Azure Functions v4  
**Language:** C# | **Trigger:** Azure Service Bus

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | PaymentService |
| Repo | TVS-CS/PaymentService (GitHub) |
| Team | Common Backend Services |
| Tech Lead | Arun Kumar Reddy |
| Product Owner | Avinash Kumar |
| Developer | Rachel Bennet |
| Deployment | Azure Functions v4 (Isolated Worker) |
| Base URL | N/A — message-driven (no HTTP endpoints) |

---

## 2. Ownership & Contacts

| Role | Person / Team |
|------|---------------|
| Product Owner | Avinash Kumar |
| Tech Lead | Arun Kumar Reddy |
| Developer | Rachel Bennet |
| Dev Team | Common Backend Services |

---

## 3. Overview

PaymentService is a **serverless webhook relay** that receives JusPay payment events and forwards them to internal TVS Motor Company services.

---

## 4. Quick Start

```bash
git clone <repository-url>
cd PaymentService
dotnet restore
dotnet build
```

Configure `local.settings.json` with values from the APIM team → run `func start` → send a test message to the `cpg-juspay` queue.

**Critical:** `local.settings.json` contains secrets and is **never committed to source control**. Create it locally using the template below.

---

## 5. Prerequisites

| Requirement | Version | Mandatory | Purpose |
|-------------|---------|-----------|---------|
| .NET SDK | 8.0+ | Yes | Build and run the function |
| Azure Functions Core Tools | v4 | Yes | Local function runtime |
| Azure CLI | Latest | Conditional | Deployment to Azure |
| Visual Studio 2022 or VS Code | Latest | Yes | IDE with C# support |
| Azurite | Latest | Yes (local dev) | Local storage emulator |
| Azure Service Bus access | — | Yes | Queue trigger source |

### Access Requirements

| Resource | Purpose | Point of Contact |
|----------|---------|-----------------|
| Azure Service Bus (cpg-juspay queue) | Message trigger source | APIM / DevOps team |
| Azure AD App Registration | OAuth2 token for downstream auth | APIM team |
| AES Encryption Keys | Encrypt payloads for EV clients | APIM team |
| APIM Subscription Key | API gateway auth for non-EV calls | APIM team |
| Downstream Service URLs | Webhook delivery endpoints | APIM team |
| Application Insights | Monitoring and diagnostics | DevOps team |
| Azure Function App | Deployment target | DevOps team |

---

## 6. What Does This Service Do?

This service **does not** expose any API endpoints. It **does not** call JusPay. It simply:

1. Picks up payment events from a Service Bus queue
2. Translates JusPay statuses to internal format
3. Delivers the data to the right downstream service (optionally encrypted)

---

## 7. Quick Facts

| Property | Value |
|----------|-------|
| Language | C# (.NET 8) |
| Type | Azure Function (serverless) |
| Trigger | Azure Service Bus queue `cpg-juspay` |
| Database | None (stateless) |
| Hosting | Azure Functions v4 (Isolated Worker) |

---

## 8. Setup Instructions

### Install & Build

```bash
git clone <repository-url>
cd PaymentService
dotnet restore
dotnet build
```

---

## 9. Local Development

### Step 1: Configure `local.settings.json`

This file holds all environment variables for local dev. It's never deployed. You need real/UAT values for:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet-isolated",
    "AzureWebJobsServiceBus": "<service-bus-connection-string>",
    "CryptoKey": "<base64-aes-key>",
    "CryptoVector": "<base64-aes-iv>",
    "OcpApimSubscriptionValue": "<apim-subscription-key>",
    "TokenUrl": "<azure-ad-token-endpoint>",
    "TokenRequest": "<oauth2-client-credentials-body>",
    "iQubeWebsite": "<downstream-url>",
    "CreonWebsite": "<downstream-url>",
    "BookingService": "<downstream-url>",
    "iceWebsiteShopify": "<downstream-url>",
    "TVSConnectEV": "<downstream-url>",
    "TVSSparesAutoRefunds": "<downstream-url>",
    "TVSConnectEVMandate": "<downstream-url>",
    "TVSConnectFleet": "<downstream-url>"
  }
}
```

Ask your team lead for the actual values.

**Where to get these values:**

| Variable | Source |
|----------|--------|
| `AzureWebJobsServiceBus` | APIM / DevOps team (Service Bus connection string with Listen permission) |
| `TokenUrl`, `TokenRequest` | APIM team (Azure AD app registration details) |
| `CryptoKey`, `CryptoVector` | APIM team (shared AES keys for EV clients) |
| `OcpApimSubscriptionValue` | APIM team (API Management subscription key) |
| Client URLs (iQubeWebsite, etc.) | APIM team (downstream service endpoint URLs) |

### Step 2: Start Azure Storage Emulator

The Functions runtime needs a storage account even though this service doesn't use one directly.

```bash
npm install -g azurite
azurite --silent
```

### Step 3: Run the Function

```bash
func start
```

The function will start and wait for messages on the `cpg-juspay` queue.

### Step 4: Test by Sending a Message

Use Azure Portal → Service Bus Explorer (or a tool like Service Bus Explorer desktop app) to send a test JSON message to the `cpg-juspay` queue. See [API_SPEC.md](./API_SPEC.md) for message format examples.

---

## 10. Environment Variables

### Required for the Service to Work

| Variable | What It Is |
|----------|-----------|
| `AzureWebJobsServiceBus` | Connection string to the Service Bus namespace (with the queue) |
| `AzureWebJobsStorage` | Azure Storage connection (or `UseDevelopmentStorage=true` locally) |
| `FUNCTIONS_WORKER_RUNTIME` | Must be `dotnet-isolated` |
| `TokenUrl` | Azure AD OAuth2 token endpoint URL |
| `TokenRequest` | Full form-urlencoded body for OAuth2 client_credentials grant |
| `CryptoKey` | Base64-encoded AES-128 encryption key (16 bytes) |
| `CryptoVector` | Base64-encoded AES IV (16 bytes) |
| `OcpApimSubscriptionValue` | Azure API Management subscription key |

### Client Endpoint URLs (one per downstream service)

| Variable | Target Service |
|----------|--------------|
| `iQubeWebsite` | TVS iQube EV API |
| `CreonWebsite` | TVS Creon EV API |
| `iQubeHDCB` | iQube HDCB API |
| `EvScooter` | EV Scooter API |
| `TVSConnectEV` | TVS Connect EV API |
| `TVSRacing` | TVS Racing API |
| `TVSConnectFleet` | TVS Fleet API |
| `BookingService` | Booking Service (refunds) |
| `BookingServiceDREF` | Booking Service (DREF) |
| `iceWebsite` | ICE Website |
| `iceWebsiteShopify` | Shopify (refund callbacks) |
| `TVSSparesAutoRefunds` | TVS Spares (auto-refunds) |
| `TVSConnectEVMandate` | TVS Connect EV (mandates) |

---

## 11. Build & Deploy

### Build

```bash
dotnet restore
dotnet build
dotnet build --configuration Release
dotnet publish --configuration Release --output ./publish
```

### Deploy to Azure

**Option A — Azure Functions Core Tools:**
```bash
func azure functionapp publish <function-app-name>
```

**Option B — Visual Studio:**
1. Right-click project → Publish
2. Select Azure Function App
3. Choose the target app
4. Publish

**Option C — CI/CD Pipeline:**
- Build with `dotnet publish --configuration Release`
- Deploy the output folder to the Azure Function App using Web Deploy or Azure DevOps task

### After Deploying

1. Verify all App Settings (environment variables) are configured in Azure Portal
2. Check that the Service Bus connection is active
3. Look at Application Insights for successful function invocations
4. Send a test message to confirm end-to-end delivery works

---

## 12. Testing

### Manual Testing (Recommended Approach)

1. Start the function locally (`func start`)
2. Send a test message to the Service Bus queue using Azure Portal or Service Bus Explorer
3. Watch the function logs for processing output
4. Verify the downstream service received the callback

**Sample test message (payment success):**
```json
{
  "event_name": "ORDER_SUCCEEDED",
  "content": {
    "order": {
      "order_id": "TEST-001",
      "status": "CHARGED",
      "amount": 100.00,
      "effective_amount": 100.00,
      "txn_id": "TXN-TEST",
      "txn_uuid": "uuid-test",
      "currency": "INR",
      "date_created": "2026-01-01T00:00:00Z",
      "payment_method_type": "UPI",
      "udf2": "test-txn",
      "udf4": "TEST",
      "udf5": "BookingService",
      "udf6": "BK-TEST",
      "txn_detail": { "gateway": "TEST", "order_id": "TEST-001" },
      "payment_gateway_response": {
        "epg_txn_id": "EPG-TEST",
        "resp_message": "Success",
        "resp_code": "00",
        "created": "2026-01-01T00:00:00Z"
      },
      "refunds": [],
      "mandate": null
    }
  }
}
```

### What to Check When Things Go Wrong

- **Application Insights** → Function invocation logs (success/failure)
- **Service Bus** → Dead Letter Queue (messages that failed too many times)
- **Azure Portal** → Function App → Monitor (recent executions)

---

## 13. Folder Structure

```
PaymentService/
├── Constants/           ← String constants (client codes, event names, config key names)
├── Enums/              ← Internal status enumerations
├── Functions/          ← The Azure Function entry point (JusPayWebhooks.cs)
├── Helpers/            ← AES encryption utility
├── Mappers/            ← JusPay → internal status translation
├── Models/             ← Data shapes (inbound messages + outbound webhooks)
├── payment-service-docs/ ← You are here
├── Program.cs          ← App startup and DI config
├── PaymentService.csproj  ← Project file (dependencies)
├── host.json           ← Azure Functions runtime settings
└── local.settings.json ← Local dev config (NEVER deployed)
```

---

## 14. Common Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Function doesn't trigger | Bad Service Bus connection string | Check `AzureWebJobsServiceBus` value |
| "401 Unauthorized" in logs | OAuth2 token acquisition failing | Verify `TokenUrl` and `TokenRequest` values |
| Messages going to Dead Letter Queue | Downstream service returning errors | Check downstream service health; inspect DLQ messages |
| Downstream returns non-200 | Wrong URL or service is down | Verify client URL environment variables |
| Encryption errors | Invalid CryptoKey or CryptoVector | Ensure they're valid Base64 strings (16 bytes each decoded) |
| Build fails | Missing NuGet packages | Run `dotnet restore` |
| `local.settings.json` not found | File missing from project root | Create it (see template above) |
| Function starts but no messages processed | Queue is empty or wrong queue name | Verify messages exist in `cpg-juspay` queue |

---

## 15. Security Requirements

| Requirement | Implementation |
|-------------|---------------|
| No secrets in source control | All secrets stored in Azure App Settings / `local.settings.json` (gitignored) |
| No hardcoded production URLs | All URLs resolved from environment variables |
| APIM subscription key | Read from `OcpApimSubscriptionValue` env var at runtime |
| Payload encryption | AES-128-CBC for EV client payloads (key from env var) |
| Auth tokens | OAuth2 client_credentials grant via Azure AD; short-lived Bearer tokens |
| Service Bus security | SAS keys with minimum required permissions (Listen for this function, Send for JusPay) |
| No PII in logs | Service does not log message payloads (only Application Insights telemetry) |

---

## 16. Developer Onboarding Path

| Step | Action | Outcome |
|------|--------|---------|
| 1 | Read this README | Understand project setup and purpose |
| 2 | Read [HLC.md](./HLC.md) | Understand all modules and data flows (15 min) |
| 3 | Read [HLD.md](./HLD.md) | Understand architecture, deployment, and security |
| 4 | Read [API_SPEC.md](./API_SPEC.md) | Understand exact message formats and examples |
| 5 | Request access from APIM team | Get Service Bus conn string, OAuth details, URLs |
| 6 | Create `local.settings.json` | Use template above with real values |
| 7 | Run `func start` locally | Verify the function starts without errors |
| 8 | Send a test message | Confirm end-to-end processing works |
| 9 | Read [LLD.md](./LLD.md) | Deep dive into field mappings and routing logic (reference) |

---

## 17. Related Documentation

| Document | What's In It |
|----------|-------------|
| [HLC.md](./HLC.md) | High Level Code — modules, workflows, data flow overview |
| [HLD.md](./HLD.md) | High Level Design — architecture, deployment, security, scalability |
| [LLD.md](./LLD.md) | Low Level Design — detailed class logic, field mappings, validation |
| [API_SPEC.md](./API_SPEC.md) | API Specification — exact message formats, payloads, examples |
| [README.md](./README.md) | This file — setup, build, deploy, troubleshooting |

---

## 18. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | June 2026 | Initial documentation release |

---

## 19. Maintainers

| Role | Contact |
|------|---------|
| Team | TVS Motor Company — Common Backend Services |
| Product Owner | Avinash Kumar |
| Tech Lead | Arun Kumar Reddy |
| Developer | Rachel Bennet |

---

*Confidentiality: This document is intended for authorized engineering partners. It excludes API keys, secrets, production credentials, and proprietary business logic details.*

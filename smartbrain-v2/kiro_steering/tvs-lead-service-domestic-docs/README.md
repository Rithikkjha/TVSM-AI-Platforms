# TVS Motor — Lead Service

> A cloud-native, event-driven microservices platform that manages the complete lifecycle of two-wheeler sales leads — from customer enquiry to dealer assignment, CRM registration, finance eligibility, and marketing engagement.

---

## Platform Overview

The TVS Motor Lead Service (LS) consists of **5 independently deployable microservices** that communicate via Azure Service Bus:

| Service | Repository | Role | Framework |
|---------|-----------|------|-----------|
| Lead Acquisition | `lms` | Front door — receives, validates, persists leads; provides master data APIs | ASP.NET Core 8 Web API |
| Process Lead | `lms_process` | Brain — classifies leads (LCE), allocates dealers (Latlong.in), fans out to downstream | ASP.NET Core 8 Background Worker |
| EMS Integration | `lms_ems` | Pushes leads to TVS Enquiry Management System (dealer-facing) | ASP.NET Core 8 Background Worker |
| CRM Integration | `lms_crm` | Pushes leads to Salesforce CDP, CCP, Voice AI, Dialer, CMP | ASP.NET Core 8 Background Worker |
| TVS Credit | `lms_tvs_credit` | Pushes finance-eligible leads to TVS Credit API and Salesforce CCP | ASP.NET Core 8 Background Worker |

**Tech Stack (all services):** .NET 8 · ASP.NET Core · Entity Framework Core · Azure Service Bus · Azure SQL (shared) · OpenTelemetry · Docker · AKS

---

## Lead Acquisition Service (`lms`)

### What It Does

The **Lead Acquisition Service** is the single entry point for all incoming leads. It:

- Accepts leads via REST API from partners, websites, and mobile apps
- Handles Facebook and Google Ads webhook integrations (strategy pattern)
- Validates every lead against configurable business rules
- Detects duplicates at the database level
- Persists leads and all related details to Azure SQL
- Publishes messages to Azure Service Bus for asynchronous downstream processing
- Provides query endpoints for dashboards and CRM tools
- Provides master data management APIs (brands, models, lead sources, lead flow config, event configurators)

**Tech Stack:** .NET 8 · ASP.NET Core · Entity Framework Core · Azure Service Bus · Azure SQL · Azure Key Vault · OpenTelemetry

---

## Prerequisites

Before setting up locally, ensure you have:

| Tool | Version | Why It's Needed |
|------|---------|-----------------|
| .NET SDK | 8.0+ | Builds and runs the application |
| Visual Studio 2022 or VS Code | Latest | IDE with C# support |
| Docker Desktop | Latest | For containerized builds and testing |
| Azure CLI | Latest | For authenticating to Azure resources (Key Vault, SQL) |
| SQL Server Management Studio (optional) | Any | For inspecting the database directly |

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url> lms
cd lms
```

### 2. Restore NuGet Packages

This downloads all third-party libraries the project depends on (EF Core, Service Bus SDK, AutoMapper, etc.).

```bash
dotnet restore lms.sln
```

### 3. Configure Environment Variables

The application reads configuration from `appsettings.json` → `appsettings.{Environment}.json` → environment variables (highest priority). For local development, create or update `leadLogs/appsettings.Development.json` with your environment-specific values.

> **Never commit secrets to source control.** Use environment variables or Azure Key Vault for production credentials.

### 4. Authenticate to Azure (for Key Vault and SQL)

The service uses Azure Active Directory Service Principal authentication for both Key Vault and Azure SQL. Locally, authenticate via:

```bash
az login
```

This ensures your local machine can access Azure resources that the service needs.

### 5. Build the Solution

```bash
dotnet build lms.sln
```

### 6. Run the Service

```bash
cd leadLogs
dotnet run
```

The API will start on `https://localhost:8081` and `http://localhost:8080`. Swagger UI is available at `/swagger`.

---

## Local Development Steps

### Daily Development Workflow

1. Pull latest changes: `git pull origin ls_dev`
2. Restore packages (if dependencies changed): `dotnet restore`
3. Build: `dotnet build`
4. Run: `cd leadLogs && dotnet run`
5. Test via Swagger UI: `http://localhost:8080/swagger`
6. Run unit tests: `dotnet test`

### Running with Docker

```bash
docker build -t lms-acquisition .
docker run -p 8080:8080 -p 8081:8081 --env-file .env lms-acquisition
```

The Dockerfile uses a multi-stage build:
- **Build stage:** Uses the .NET 8 SDK image to compile the application
- **Publish stage:** Creates an optimized release build
- **Runtime stage:** Uses the lightweight ASP.NET 8 runtime image (smaller, more secure)

### Debugging

- Set breakpoints in Visual Studio / VS Code
- Use the `Development` environment for verbose logging
- Check Swagger UI for interactive API testing
- The health check endpoint `GET /` returns the service version

---

## Environment Variables

All configuration keys the service requires. Values come from `appsettings.Development.json` locally, or from environment variables / Azure Key Vault in deployed environments.

| Variable | Purpose | Example Format |
|----------|---------|----------------|
| `DB_CONNECTION` | Azure SQL Server connection string | `Server=...;Database=...;Authentication=Active Directory Service Principal;...` |
| `SERVICE_BUS_CONNECTION_STRING` | Azure Service Bus connection (includes SAS key) | `Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...` |
| `TOPIC_NAME` | Service Bus topic to publish leads to | `dev.oclns.lead` |
| `EVENT_TARGET_VALUE` | Target label for dispatched messages | `PROCESS` |
| `EVENT_SOURCE_VALUE` | Source label identifying this service | `LEAD_ACQUISITION` |
| `LEAD_PROCESS` | Event type for new leads | `LEAD_PROCESS` |
| `UPDATE_LEAD_PROCESS` | Event type for lead updates | `UPDATE_LEAD_PROCESS` |
| `PARTIAL_LEAD_PROCESS` | Event type for partial leads | `PARTIAL_LEAD_PROCESS` |
| `API_KEY_VALUE` | API key expected in the `APIKey` request header | (64-char hex string) |
| `OLD_LMS_URL` | Legacy LMS callback URL (can be empty) | `https://old-lms.example.com/callback` |
| `EMS_SEARCH_API_URL` | EMS search endpoint | `https://api.example.com/api/enquiry-search` |
| `REDIS_CONNECTION` | Azure Redis Cache connection string | `host:port,password=...,ssl=True` |
| `LATLONG_TOKEN_URL` | Latlong.in OAuth2 token endpoint | `https://api.latlong.in/oauth/token` |
| `LATLONG_RONIN_CLIENT_ID` | OAuth2 client ID for Ronin brand | (64-char hex) |
| `LATLONG_RONIN_CLIENT_SECRET` | OAuth2 secret for Ronin brand | (64-char hex) |
| `LATLONG_RTR_CLIENT_ID/SECRET` | OAuth2 credentials for RTR (Apache) brand | Same format |
| `LATLONG_COMMON_CLIENT_ID/SECRET` | OAuth2 credentials for Common brands (Jupiter, etc.) | Same format |
| `LATLONG_3W_CLIENT_ID/SECRET` | OAuth2 credentials for Three-Wheeler brand | Same format |
| `LATLONG_EV_CLIENT_ID/SECRET` | OAuth2 credentials for EV (iQube) brand | Same format |
| `LATLONG_*_API_URL` | Per-brand Latlong dealer discovery API URLs | `https://api.latlong.in/v2/brands/{id}/find.json` |
| `FACEBOOK_VERSION` | Facebook Graph API version | `v23.0` |
| `OpenTelemetry_ServiceName` | Service name in traces | `Lead-Service` |
| `OpenTelemetry_Endpoint` | OTLP collector URL | `http://otel-gw-logs.tvsmotor.com` |
| `SERVICE_VERSION` | Application version tag in telemetry | `1.0.0` |
| `DEPLOYMENT_ENVIRONMENT` | Environment tag in telemetry | `development` |
| `KeyVault` (section) | Azure Key Vault configuration section | `{ "VaultUri": "https://..." }` |


---

## Build Instructions

### Local Build

```bash
# Build the entire solution (service + shared library + tests)
dotnet build lms.sln -c Debug

# Build only the main service
dotnet build leadLogs/leadReceiptService.csproj -c Release
```

### Docker Build

```bash
# From the repository root (where Dockerfile lives)
docker build -t lms-acquisition:latest .
```

The Docker build produces a Linux container based on `mcr.microsoft.com/dotnet/aspnet:8.0`, exposing ports 8080 (HTTP) and 8081 (HTTPS).

### CI/CD Build (Azure Pipelines)

The service is built automatically via Azure DevOps Pipelines using a shared template from the `TVSM-Common-Support/tvsm-norton-pipelines` repository. The pipeline:

1. Triggers on push to `ls_dev` branch
2. Runs `dotnet restore` → `dotnet build` → `dotnet test` (with code coverage)
3. Publishes the Docker image to Azure Container Registry
4. Deploys to the target environment via Helm chart

---

## Deployment Steps

### Deployment Environments

| Environment | Branch | Approval Required |
|-------------|--------|-------------------|
| Development | `ls_dev` | No — auto-deploys on push |
| UAT | `ls_uat` | Yes — manual gate |
| Production | `ls_release` / `main` | Yes — manual gate |

### Manual Deployment (if needed)

1. Build Docker image: `docker build -t lms-acquisition .`
2. Tag for registry: `docker tag lms-acquisition <acr-url>/ls-acquisition:<version>`
3. Push to ACR: `docker push <acr-url>/ls-acquisition:<version>`
4. Update Helm chart values with new image tag
5. Deploy via Helm: `helm upgrade ls-acquisition ./charts -f values-<env>.yaml`

### Environment-Specific Configuration

- **Dev/UAT:** Configuration loaded from `appsettings.Development.json` + environment variables in Kubernetes ConfigMap/Secrets
- **Production:** All secrets retrieved from Azure Key Vault at startup; no secrets in config files or environment variables

---

## Testing Instructions

### Run All Unit Tests

```bash
dotnet test LMSUnitTest/LMSUnitTest.csproj
```

### Run with Code Coverage

```bash
dotnet test LMSUnitTest/LMSUnitTest.csproj --collect:"XPlat Code Coverage"
```

Coverage reports are generated in Cobertura XML format at `LMSUnitTest/coverage.cobertura.xml`.

### Test Structure

The `LMSUnitTest` project uses **xUnit** with **Moq** and **NSubstitute** for mocking dependencies. Key test files:

| Test File | What It Covers |
|-----------|---------------|
| `LeadAcquisitionTests.cs` | End-to-end lead submission flow |
| `ValidationUnitTests.cs` | All field-level validation rules |
| `LeadLogUnitTests.cs` | Main orchestrator (LeadLogService) |
| `DelegateUnitTests.cs` | Lead delegate and setup logic |
| `ProcessDuplicateLeadServiceTests.cs` | Duplicate detection and handling |
| `WebhookServiceTests.cs` | Facebook webhook processing |
| `CommsServiceTests.cs` | Communications event handling |
| `UpdateLeadServiceTests.cs` | Lead update processing |
| `LeadDispatchServiceTests.cs` | Service Bus dispatch logic |
| `LatlongServiceTests.cs` | Dealer geo-allocation |
| `TokenServiceUnitTests.cs` | Token refresh lifecycle |
| `DealerTransferServiceTests.cs` | Inter-dealer transfer |
| `MdpUnitTests.cs` | MDP dealer lookup |
| `MasterControllerTests.cs` | Master data API controller routing |
| `MasterServiceTests.cs` | Master data CRUD service logic |
| `BrandValidatorTests.cs` | Brand validation rules |
| `ModelValidatorTests.cs` | Model/Part validation rules |
| `LeadSourceValidatorTests.cs` | Lead source validation rules |
| `LeadFlowConfigurationValidatorTests.cs` | Lead flow config validation rules |
| `EventConfiguratorValidatorTests.cs` | Event configurator validation rules |

### Manual API Testing

With the service running locally, use Swagger UI at `http://localhost:8080/swagger` or send requests via curl:

```bash
curl -X POST http://localhost:8080/api/lead \
  -H "Content-Type: application/json" \
  -H "APIKey: <your-dev-api-key>" \
  -d '{"customer_name":"Test","mobile_number":"9876543210","source_id":1,"brand_code":3,"model_id":"JUPITER","part_id":"JUPITER_125","enquiry_date":"2026-06-22 10:00:00.000","area":"560001"}'
```

---

## Folder Structure

```
lms/
├── leadLogs/                         ← Main service project (runs as the web API)
│   ├── Controllers/                  ← HTTP endpoint handlers (5 controllers)
│   ├── Services/                     ← Business logic layer (20+ service classes)
│   ├── Repository/                   ← Database access layer (16 repositories)
│   ├── Latlong/                      ← Dealer geo-allocation (factory + strategy pattern)
│   ├── ExchangeService/              ← HTTP client wrappers for external APIs
│   ├── Extensions/                   ← DI registration (MvcExtensions.cs)
│   ├── Const/                        ← AppSettingsService + Constants
│   ├── AutoMappings/                 ← AutoMapper profile configuration
│   ├── Properties/                   ← Launch settings
│   ├── Program.cs                    ← Application entry point
│   ├── Startup.cs                    ← DI container + middleware pipeline setup
│   ├── appsettings.json              ← Base configuration
│   ├── appsettings.Development.json  ← Dev environment overrides (gitignored)
│   └── leadReceiptService.csproj     ← Project file (dependencies, build config)
│
├── lms.config/                       ← Shared class library (referenced by service + tests)
│   ├── Entities/                     ← EF Core entity classes (map to DB tables)
│   ├── Models/                       ← DTOs (request models, response models, bus messages)
│   ├── LMSContext/                   ← LMSDbContext (EF Core database session)
│   ├── Utils/                        ← Shared utility functions
│   └── lms.config.csproj             ← Class library project file
│
├── LMSUnitTest/                      ← Unit test project (xUnit + Moq)
│   ├── *Tests.cs                     ← Test classes for each service
│   └── LMSUnitTest.csproj            ← Test project file
│
├── azure-pipeline/                   ← Norton pipeline configs (international)
├── azure-pipelines-domestic/         ← Domestic pipeline configs (India)
├── Dockerfile                        ← Multi-stage Docker build definition
├── lms.sln                           ← Visual Studio solution file
├── .gitignore                        ← Git ignore rules
└── readme.md                         ← Original readme (basic)
```


---

## Common Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `Unable to connect to SQL Server` | Azure AD auth not configured locally | Run `az login` to authenticate your Azure session |
| `Service Bus connection failed` | SAS key expired or firewall blocking port 443 | Verify the connection string is current; Service Bus uses AMQP over WebSockets (port 443) |
| `404 on /api/lead` | Service not running or wrong port | Check that you're hitting port 8080 (HTTP) or 8081 (HTTPS) |
| `400 "Invalid source"` | The `source_id` in your request doesn't exist in the DB | Check the `lead_sources` table for valid source IDs in your environment |
| `400 "Lead flow is not configured"` | No flow config for this source | Add a row to `lead_flow_configuration` for the source_id |
| Build fails with `Could not resolve project reference` | Missing `lms.config` project | Ensure you cloned the full repo including the `lms.config/` folder |
| `KeyVault` section errors on startup | Key Vault not accessible locally | Either configure a local Key Vault section in appsettings, or remove the Key Vault setup when running locally |
| Docker build fails at COPY step | Build context wrong | Run `docker build` from the repository root (where `Dockerfile` is), not from `leadLogs/` |
| Tests fail with `DbContext` errors | Missing test database or incorrect connection | Unit tests use mocked repositories (Moq/NSubstitute) — they should not need a real DB. Check test setup. |
| `Parallel Requests Received` error | Sent same lead twice rapidly | This is the duplicate safety net — not a bug. Wait a moment and the original lead will be processed. |

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `ls_dev` | Active development — auto-deploys to Dev environment |
| `ls_uat` | UAT testing — requires manual approval for deployment |
| `ls_release` | Production releases |
| `main` | Stable production baseline |
| `multi-country-deployment` | International deployment variant |

### Workflow

1. Create feature branch from `ls_dev`
2. Develop and test locally
3. Push and create PR to `ls_dev`
4. CI runs automatically (build + tests)
5. After merge, Dev auto-deploys
6. When ready for UAT: merge `ls_dev` → `ls_uat` (requires approval)
7. When ready for production: merge `ls_uat` → `ls_release` (requires approval)

---

## Process Lead Service (`lms_process`)

### What It Does

The **Process Lead Service** is the central brain that decides what happens to a lead after it is received. It runs entirely in the background — no public HTTP endpoints.

- Consumes messages from the PROCESS subscription on Azure Service Bus
- Classifies leads (EV / ICE / Aggregator) via the LCE API
- Allocates the nearest dealer using Latlong.in geo API (per-brand OAuth2 credentials)
- Enforces dealer daily threshold caps
- Fans out leads to EMS, CRM, and Finance subscriptions simultaneously
- Handles lead update events (compares old vs new state, publishes changes)
- Consumes MDP (Master Data Platform) dealer events from a separate Service Bus

### How to Run

```bash
cd processLeadService
dotnet run
```

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_CONNECTION` | Azure SQL connection string |
| `SERVICE_BUS_CONNECTION_STRING` | Main Service Bus (consume + publish) |
| `TOPIC_NAME` / `PROCESS_SUBSCRIPTION` | Consumer configuration |
| `EMS_SUBSCRIPTION` / `CRM_SUBSCRIPTION` / `FINANCE_SUBSCRIPTION` | Fan-out targets |
| `MDP_CONNECTION_STRING` / `MDP_TOPIC_NAME` / `MDP_LMS_SUBSCRIPTION` | Separate MDP Service Bus |
| `LCE_URL` / `LCE_TOKEN_URL` / `LCE_CLIENT_ID` / `LCE_CLIENT_SECRET` | Lead Classification Engine |
| `LATLONG_*` | Per-brand Latlong.in OAuth2 credentials |

---

## EMS Integration Service (`lms_ems`)

### What It Does

The **EMS Service** pushes leads to the TVS Enquiry Management System — the dealer-facing platform that sales staff use to manage leads.

- Consumes messages from the EMS subscription
- Routes leads to the correct EMS API endpoint (HO / Aggregator / EV / EV Test Ride)
- Handles threshold-exceeded responses (schedules next-day retry)
- On dealer error, publishes back to PROCESS subscription for dealer re-allocation
- On transient failure, schedules 30-minute delayed retry
- Consumes booking lifecycle events from a separate booking Service Bus

### How to Run

```bash
cd emsService
dotnet run
```

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_CONNECTION` | Azure SQL connection string |
| `SERVICE_BUS_CONNECTION_STRING` | Main Service Bus |
| `TOPIC_NAME` / `EMS_SUBSCRIPTION` | Consumer configuration |
| `EMS_API_URL` / `EMS_API_AGGREGATOR_URL` | TVS EMS endpoints |
| `API_KEY_VALUE` | EMS API key header |
| `BOOKING_SERVICE_BUS_CONNECTION_STRING` / `BOOKING_TOPIC_NAME` / `BOOKING_SUBSCRIPTION` | Separate booking queue |

---

## CRM Integration Service (`lms_crm`)

### What It Does

The **CRM Service** pushes leads to multiple customer engagement systems for sales follow-up and marketing.

- Consumes messages from the CRM subscription
- Pushes to Salesforce CDP (Customer 360 profile)
- Pushes to Salesforce Service Cloud / CCP (Lead records, Test Ride upserts)
- Pushes to Voice AI (automated outbound calls with business-hours scheduling 9AM–7PM IST)
- Pushes to Dialer (call centre queue)
- Pushes to CMP (push notifications)
- Handles lead update events (updates CDP and CCP records)
- Handles scheduled Voice AI messages (after-hours leads re-delivered next day)

### How to Run

```bash
cd crmService
dotnet run
```

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_CONNECTION` | Azure SQL connection string |
| `SERVICE_BUS_CONNECTION_STRING` | Main Service Bus |
| `TOPIC_NAME` / `CRM_SUBSCRIPTION` | Consumer configuration |
| `CCP_URL` / `CCP_TOKEN_URL` / `CCP_CLIENT_ID` / `CCP_CLIENT_SECRET` | Salesforce CCP OAuth2 |
| `CDP_URL` | Salesforce CDP endpoint |
| `CMP_URL` / `CMP_TOKEN_URL` / `CMP_CLIENT_ID` / `CMP_CLIENT_SECRET` | Push notifications |
| `DIALER_URL` / `DIALER_TOKEN_URL` | Auto-dialer |

---

## TVS Credit Integration Service (`lms_tvs_credit`)

### What It Does

The **TVS Credit Service** pushes finance-eligible leads to the TVS Credit partner for loan/financing follow-up.

- Consumes messages from the FINANCE subscription
- Maps LMS dealer IDs to TVS Credit dealer codes
- Maps state/city names to TVS Credit internal codes
- Posts finance leads to the TVS Credit API
- Also pushes EV leads to Salesforce Service Cloud / CCP

### How to Run

```bash
cd lms_tvs_credit
dotnet run
```

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_CONNECTION` | Azure SQL connection string |
| `SERVICE_BUS_CONNECTION_STRING` | Main Service Bus |
| `TOPIC_NAME` / `SUBSCRIPTION_NAME` | Consumer configuration |
| `TVS_CREDIT_LEAD_PUSH_URL` | TVS Credit API endpoint |
| `PRODUCT_CODE` / `CHANNEL_CODE` / `AGENCY_CODE` | Fixed codes for TVS Credit requests |
| `CCP_URL` / `CCP_TOKEN_URL` / `CCP_CLIENT_ID` / `CCP_CLIENT_SECRET` | Salesforce CCP OAuth2 |

---

## Maintainers / Contact

| Role | Name | Contact |
|------|------|---------|
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com |
| Tech Lead | Arun Kumar | Arunkumar.Reddy@tvsd.ai |
| Dev Team | Common Backend- Lead Service | ls.support@tvsmotor.com |

---

## Related Documentation

| Document | Location | Description |
|----------|----------|-------------|
| High Level Design (HLD) | `TVS_LMS_DOCS/HLD.md` | Architecture, integrations, infrastructure |
| High Level Code (HLC) | `TVS_LMS_DOCS/HLC.md` | Modules, workflows, service classes |
| Low Level Design (LLD) | `TVS_LMS_DOCS/LLD.md` | Detailed module interactions, validation, error handling |
| API Specification | `TVS_LMS_DOCS/API_SPEC.md` | Endpoint details, payloads, errors, samples |

---

*Last updated: July 2026*

# Lead Management System (LMS) — README

## 1. Application Overview

The Lead Management System (LMS) is a distributed, event-driven platform that manages the full lifecycle of automotive leads for TVS Motor Company. It is composed of three independently deployable repositories:

| Repository | Role | Description |
|---|---|---|
| **lms** | API Gateway | .NET Core 8 REST API with 13 endpoints. Handles lead ingestion, validation, deduplication, and publishes events to Azure Service Bus. |
| **lms_process** | Event Consumer | Service Bus consumer that classifies leads (LCE ML API), allocates dealers (Lat/Long API), applies business rules, and routes to downstream systems. |
| **lms_crm** | CRM Dispatcher | Service Bus consumer that dispatches processed leads to CRM platforms: CCP, CDP, CMP, Rezo AI, and Auto-Dialer. |

All three services are deployed per-region with isolated databases and messaging infrastructure.

---

## 2. Setup Instructions

### Prerequisites

- .NET SDK 8.0+
- Azure CLI (for local Service Bus emulation or connection)
- SQL Server (local or Azure SQL)
- Visual Studio 2022 / VS Code / Rider

### Clone Repositories

```bash
git clone https://github.com/TVSM-DMS/lms.git -b ls_uat_ib
git clone https://github.com/TVSM-DMS/lms_process.git -b ls_uat_ib
git clone https://github.com/TVSM-DMS/lms_crm.git -b ls_uat_ib
```

### Restore Dependencies

```bash
cd lms && dotnet restore
cd ../lms_process && dotnet restore
cd ../lms_crm && dotnet restore
```

### Configure Environment

Copy the sample environment file and update values:

```bash
cp appsettings.Development.sample.json appsettings.Development.json
```

Update connection strings, Service Bus connection, and API URLs (see Section 4 for all variables).

### Database Setup

```bash
cd lms
dotnet ef database update
```

### Run

```bash
# Terminal 1 — API
cd lms && dotnet run

# Terminal 2 — Process Consumer
cd lms_process && dotnet run

# Terminal 3 — CRM Dispatcher
cd lms_crm && dotnet run
```

---

## 3. Local Development

| Step | Command | Notes |
|---|---|---|
| Start API | `dotnet run --project lms` | Runs on configured port |
| Start Process | `dotnet run --project lms_process` | Requires Service Bus connection |
| Start CRM | `dotnet run --project lms_crm` | Requires Service Bus connection |
| Run tests | `dotnet test` | Per-project test execution |
| Watch mode | `dotnet watch run --project lms` | Auto-reload on changes |
| EF migration | `dotnet ef migrations add <Name>` | In lms project |
| Update DB | `dotnet ef database update` | Apply pending migrations |

### Local Service Bus Options

1. **Azure Service Bus (Dev namespace)** — Use a shared dev namespace connection string
2. **Azurite + local emulator** — Limited topic support
3. **Skip consumer** — Test API in isolation, messages queue in Service Bus

---

## 4. Environment Variables

### lms (API Gateway)

| Variable | Required | Description |
|---|---|---|
| TOKEN | Yes | Static authentication token |
| AppPrefix | Yes | Route prefix (e.g., `in`, `bd`, `ke`) |
| ConnectionStrings__DefaultConnection | Yes | Azure SQL connection string |
| ServiceBus__ConnectionString | Yes | Service Bus namespace connection |
| ServiceBus__TopicName | Yes | Topic name (`lead-events`) |
| ASPNETCORE_ENVIRONMENT | Yes | `Development` / `Production` |
| ASPNETCORE_URLS | No | Binding URLs |

### lms_process (Consumer)

| Variable | Required | Description |
|---|---|---|
| ConnectionStrings__DefaultConnection | Yes | Azure SQL connection string |
| ServiceBus__ConnectionString | Yes | Service Bus namespace connection |
| ServiceBus__TopicName | Yes | Topic name (`lead-events`) |
| ServiceBus__SubscriptionName | Yes | Subscription (`PROCESS`) |
| LceApi__BaseUrl | Yes | LCE ML classification API URL |
| LatLongApi__RoninUrl | Yes | Lat/Long endpoint for Ronin brand |
| LatLongApi__RtrUrl | Yes | Lat/Long endpoint for RTR brand |
| LatLongApi__EvUrl | Yes | Lat/Long endpoint for EV brand |
| LatLongApi__ThreeWheelerUrl | Yes | Lat/Long endpoint for 3W brand |
| LatLongApi__CommonUrl | Yes | Lat/Long endpoint for other brands |
| MdpTopic__ConnectionString | Yes | MDP topic Service Bus connection |
| MdpTopic__TopicName | Yes | MDP topic name (`mdp-events`) |

### lms_crm (Dispatcher)

| Variable | Required | Description |
|---|---|---|
| ConnectionStrings__DefaultConnection | Yes | Azure SQL connection string |
| ServiceBus__ConnectionString | Yes | Service Bus namespace connection |
| ServiceBus__TopicName | Yes | Topic name (`lead-events`) |
| ServiceBus__SubscriptionName | Yes | Subscription (`CRM`) |
| CrmConfig__CacheDurationMinutes | No | Cache TTL (default: 30) |
| CcpApi__BaseUrl | Yes | CCP API URL |
| CdpApi__BaseUrl | Yes | CDP API URL |
| CmpApi__BaseUrl | Yes | CMP API URL |
| RezoAi__BaseUrl | Yes | Rezo AI API URL |
| AutoDialer__BaseUrl | Yes | Auto-Dialer API URL |

---

## 5. Build Instructions

```bash
# Build all projects
dotnet build lms/lms.csproj -c Release
dotnet build lms_process/lms_process.csproj -c Release
dotnet build lms_crm/lms_crm.csproj -c Release

# Publish for deployment
dotnet publish lms/lms.csproj -c Release -o ./publish/lms
dotnet publish lms_process/lms_process.csproj -c Release -o ./publish/lms_process
dotnet publish lms_crm/lms_crm.csproj -c Release -o ./publish/lms_crm
```

---

## 6. Deployment

### Deployment

Services are deployed as Azure App Services. Each service connects to:
- Azure Service Bus (shared topic per environment)
- Azure SQL (country-specific DB connection)

Branch for IB: `ls_uat_ib`

### Deployment Steps

1. Build and publish artifacts (see Section 5)
2. Set environment variables in App Service Configuration
3. Deploy to Azure App Service via Azure CLI or CI/CD pipeline
4. Verify health check endpoint: `GET /{AppPrefix}/`
5. Verify Service Bus connectivity (check consumer logs)

### Rollout

Deploy and verify per-environment (DEV → UAT → Production).

---

## 7. Testing

### Sample cURL — Create Lead

```bash
curl -X POST "https://<host>/{AppPrefix}/api/lead" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-static-token-here" \
  -H "countryCode: IN" \
  -d '{
    "customer_name": "Test User",
    "mobile_number": "9876543210",
    "source_id": 8,
    "brand_code": 1,
    "model_id": "APACHE",
    "part_id": "RTR160",
    "city": "Bangalore",
    "enquiry_date": "2026-07-01 10:30:00.000"
  }'
```

### Expected Response

```json
{
  "message": "Success",
  "requestId": 789012,
  "leadId": "ENQ789012",
  "status": 200
}
```

### Sample cURL — Get Lead Details

```bash
curl -X POST "https://<host>/{AppPrefix}/api/leads/getDetails" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-static-token-here" \
  -H "countryCode: IN" \
  -d '{ "internet_enquiry_id": "ENQ789012" }'
```

### Running Unit Tests

```bash
cd lms && dotnet test
cd lms_process && dotnet test
cd lms_crm && dotnet test
```

---

## 8. Folder Structure

```
lms/                              (API Gateway)
├── leadLogs/
│   ├── Controllers/
│   │   ├── LeadAcquisitionController.cs  (5 endpoints)
│   │   ├── LeadGetController.cs          (5 endpoints)
│   │   ├── LeadCommsController.cs        (1 endpoint)
│   │   └── WebhooksController.cs         (2 endpoints, no auth)
│   ├── Services/
│   │   ├── LeadLogService.cs             (Core orchestrator)
│   │   ├── ProcessValidLeadService.cs
│   │   ├── ProcessDuplicateLeadService.cs
│   │   ├── LeadDispatchService.cs        (Service Bus publish)
│   │   ├── LatlongService.cs             (Dealer allocation)
│   │   ├── UpdateLeadService.cs
│   │   ├── LeadValidator.cs
│   │   └── ... (20+ services)
│   ├── Repository/                       (16 repos)
│   ├── Latlong/
│   │   ├── DealerAllocationFactory.cs
│   │   ├── EvDealerAllocationService.cs
│   │   └── GeneralDealerAllocationService.cs
│   ├── ExchangeService/
│   │   └── ApiExchangeService.cs         (External HTTP calls)
│   ├── Token/
│   │   └── StaticTokenAuthenticationHandler.cs
│   └── Const/
│       ├── Constants.cs
│       └── AppSettingsService.cs
├── lms.config/                   (Shared entities/config)
│   └── Entities/                 (EF Core entity classes)
└── Startup.cs / Program.cs

lms_process/                      (Processing Consumer)
├── processLeadService/
│   ├── ListenerService/
│   │   ├── QueueConsumer.cs      (process_subscription)
│   │   └── MdpConsumer.cs        (MDP topic, session-based)
│   ├── Services/
│   │   ├── LeadService.cs        (Message router)
│   │   ├── LeadDelegate.cs       (LCE + dual push)
│   │   ├── TwoWheelerService.cs  (New lead flow)
│   │   ├── UpdateLeadService.cs
│   │   ├── RetryService.cs
│   │   ├── ThresholdService.cs
│   │   └── DispatchService.cs    (Re-publish to topic)
│   ├── Latlong/
│   ├── LeadQualification/        (LCE integration)
│   ├── MdpService/
│   └── Startup.cs

lms_ems/                          (EMS Consumer)
├── emsService/
│   ├── ListenerService/
│   │   ├── EmsListenerService.cs     (ems_subscription)
│   │   └── BookingListenerService.cs (Booking topic, session-based)
│   ├── Services/
│   │   ├── EmsRoutingService.cs
│   │   ├── EmsService.cs
│   │   ├── BookingService.cs
│   │   └── DispatchService.cs
│   └── Startup.cs

lms_crm/                          (CRM Dispatcher)
├── ListenerService/
│   └── CrmListenerService.cs     (crm_subscription)
├── Services/
│   ├── CrmDispatcher.cs          (Multi-CRM router by country)
│   ├── CcpService.cs             (Salesforce CCP)
│   ├── CdpService.cs             (Salesforce C360)
│   ├── CmpService.cs             (Marketing Cloud)
│   ├── DialerService.cs          (C-Zentrix)
│   ├── RezoService.cs            (Rezo AI)
│   ├── Services/India/           (Country-specific)
│   ├── Services/Nepal/
│   └── Services/Sri Lanka/
└── Startup.cs
```

---

## 9. Common Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| 401 on all requests | Invalid or missing TOKEN env var | Verify TOKEN is set correctly in App Service config |
| Leads not processing | Service Bus connection failure | Check ServiceBus__ConnectionString, verify namespace is accessible |
| Classification returns null | LCE API unreachable | Verify LceApi__BaseUrl, check network/firewall rules |
| Dealer not allocated | Lat/Long API timeout | Check LatLongApi URLs, increase timeout if needed |
| Duplicate not detected | Dedup logic mismatch | Verify mobile + dealer + branch + active combination |
| CRM dispatch failing | CRM platform down | Check lms_crm logs, messages will dead-letter after retries |
| 404 on endpoints | Wrong AppPrefix | Verify AppPrefix env var matches URL path prefix |
| Database connection timeout | SQL Server unavailable | Check connection string, firewall rules, Azure SQL status |
| Messages in DLQ | Processing exception | Inspect dead-letter queue messages for error details |
| Facebook webhook fails verify | verify_token mismatch | Token must be exactly "lms" (hardcoded) |
| High memory usage | CRM config cache bloat | Restart service, verify cache TTL is 30 min |
| Build fails after clone | Missing .NET SDK 8 | Install .NET SDK 8.0+ |

---

## 10. Maintainers & Contact

| Role | Name | Contact |
|---|---|---|
| App Engineering Lead | Suman Kumar | Suman.Kumar@tvsmotor.com |
| Tech Lead | Arun Kumar Reddy | Arunkumar.Reddy@tvsd.ai |
| DevOps | Koyel Nath | Koyel.Nath@tvsmotor.com |
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com |
| Backend Dev | Nikhil Reddy | nikhil.reddy@tvsmotor.com |
| Backend Dev | Sriniketh | Sriniketh@tvsmotor.com |
| Support | Lead Service Support | ls.support@tvsmotor.com |

**Repositories:**
- lms: `https://github.com/TVSM-DMS/lms` (branch: ls_uat_ib)
- lms_process: `https://github.com/TVSM-DMS/lms_process` (branch: ls_uat_ib)
- lms_ems: `https://github.com/TVSM-DMS/lms_ems` (branch: ls_uat_ib)
- lms_crm: `https://github.com/TVSM-DMS/lms_crm` (branch: ls_uat_ib)

**Related Documentation:**
- [High-Level Context (HLC)](./HLC.md)
- [High-Level Design (HLD)](./HLD.md)
- [Low-Level Design (LLD)](./LLD.md)
- [API Specification](./API_SPEC.md)
- [API Specification IB](./API_SPEC_IB.md)

---

## 11. Architecture Quick Reference

```mermaid
graph TD
    subgraph Sources["Lead Sources"]
        direction LR
        WEB["TVS Website"] ~~~ FB["Facebook"] ~~~ AGG["Aggregators"] ~~~ EV["EV Portal"] ~~~ B2B["B2B"]
    end

    Sources -->|"HTTPS + Static Token + countryCode"| API

    subgraph API["lms — API Layer (leadLogs/)"]
        direction LR
        A1["Validate & Dedup"] --> A2["Latlong Dealer Allocation"] --> A3["Save to DB"] --> A4["Publish to Service Bus"]
    end

    API -->|"uat.oclns-lead-ib: EVENT_TYPE=LEAD_PROCESS"| SB1["process_subscription"]

    SB1 --> Process

    subgraph Process["lms_process — Processing Engine"]
        direction LR
        P1["LCE Classification<br/>(HOT/WARM/COLD)"] --> P2["Dual Push Rules"] --> P3["Determine Destinations"]
    end

    Process -->|"Re-publishes to uat.oclns-lead-ib with EVENT_TARGET"| SB2

    subgraph SB2["Downstream Subscriptions (IB)"]
        direction LR
        R1["ems_subscription"] ~~~ R2["crm_subscription"]
    end

    R1 --> EMS["lms_ems<br/>(constructs payload → publishes back to Service Bus)"]
    R2 --> CRM

    subgraph CRM["lms_crm — CRM Dispatcher (identifies country → routes)"]
        direction LR
        IND["India CRM"] ~~~ NPL["Nepal CRM"] ~~~ LKA["Sri Lanka CRM"]
    end
```

### Key Processing Responsibilities

| Step | Where | Service/Method |
|------|-------|----------------|
| Validate request | **lms** (API) | LeadValidator |
| Deduplicate | **lms** (API) | ProcessDuplicateLeadService |
| Dealer Allocation (Latlong) | **lms** (API) | LatlongService → DealerAllocationFactory |
| Persist lead | **lms** (API) | LeadRepository → Azure SQL |
| Publish to Service Bus | **lms** (API) | LeadDispatchService.Dispatch() |
| LCE Classification | **lms_process** | LeadDelegate.ApplyChecks() |
| Dual Push Evaluation | **lms_process** | LeadDelegate.IsCommutorDualPush() |
| Route to subscriptions | **lms_process** | DispatchService.Dispatch() |
| EMS push | **lms_ems** | EmsRoutingService → EmsService |
| CRM dispatch | **lms_crm** | CrmDispatcher → country-specific services |
| Finance push | **tvs_credit** | → TVS Credit Leads API |
| Communications | **lead_comms** | → CMP/Dialer/Rezo |

---

*Document Version: 1.0 | Last Updated: 2025*

---
service_id: lms-crm
doc_type: hlc
last_reviewed: 2026-10-11
---

# lms-crm — High-Level Code

## Application Overview
lms-crm is a C# / ASP.NET Core service in repo `lms_crm` (default branch per `runs/TVS-CS/lms_crm/meta.json`). Its HTTP surface is only `GET /`; the work happens in a Service Bus processor registered at startup.

## Module Summary
lms-crm modules:

| Module | Responsibility |
|---|---|
| `./ (repo root)` | ASP.NET Core host `crmService.csproj` (net7.0): Controllers, ListenerService, Services, ExchangeService, Repository, Entities, LMSContext, Models, Utils |
| `bin/, .vs/` | Committed build output / IDE files |
| `LMS_crm-CI-Dev.YML` | Azure DevOps CI |

## Folder Structure
lms-crm top-level folders (real paths):
```
./ (repo root)
bin/, .vs/
LMS_crm-CI-Dev.YML
```

## Core Workflows in Code
lms-crm entry → handler → service → client/repository:
- `CrmListenerService.ProcessMessagesAsync` → `CrmService.PushCrmLeads` → `RezoService` / `CcpService` / `DialerService` / `ProcessCrmLeads` → `ApiExchangeService` (HTTP) + `CrmRepository` / `ThresholdRepository` / `DialerRepository`

## Integration Clients
lms-crm client classes:

| Kind | Client | Evidence |
|---|---|---|
| HTTP | `ApiExchangeService` (CRM_URL, DIALER_URL, CCP_URL) | `Services/ApiExchangeService.cs:27` |
| HTTP | `LeadExchangeService` (OLD_LMS_URL) | `ExchangeService/LeadExchangeService.cs:27` |
| Service Bus | `CrmListenerService` processor; `DispatchService` sender (no caller found) | `Services/DispatchService.cs:19` |
| SQL Server | EF Core `LMSDbContext` | `LMSContext/LMSDbContext.cs` |

## Cross-Cutting Concerns
lms-crm cross-cutting concerns:
- Configuration via `AppSettingsService` (`AppSettings:*`, `Utils/Constants.cs:16-17`)
- AutoMapper (`AutoMappings/AutoMapping.cs`)

## Build and Test
lms-crm build/test (dotnet CLI against the committed solution/project files; CI pipelines use shared templates):
- `dotnet build crmService.csproj`

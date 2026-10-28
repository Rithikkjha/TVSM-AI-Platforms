---
service_id: lms-process
doc_type: hlc
last_reviewed: 2026-10-11
---

# lms-process — High-Level Code

## Application Overview
lms-process is a C# / ASP.NET Core service in repo `lms_process` (default branch per `runs/TVS-CS/lms_process/meta.json`). Its HTTP surface is only `GET /`; the work happens in a Service Bus processor registered at startup.

## Module Summary
lms-process modules:

| Module | Responsibility |
|---|---|
| `processLeadService/` | ASP.NET Core host (net7.0): ListenerService, Services, MdpService, Latlong, LeadQualification, ExchangeService, Repository, Const, Utils |
| `lms.config/` | Shared EF Core entities/context (`Entities/`, `LMSContext/`) |
| `leadQualification/` | Lead qualification library (`leadQualification.csproj`) |
| `ProcessLeadTest/` | Unit tests |
| `publish/` | Committed publish output (binaries + appsettings copies) |
| `azure-pipelines/, LMS_Process-CI-Dev.YML` | Azure DevOps CI (templates from `tvsm-norton-pipelines`) |

## Folder Structure
lms-process top-level folders (real paths):
```
processLeadService/
lms.config/
leadQualification/
ProcessLeadTest/
publish/
azure-pipelines/, LMS_Process-CI-Dev.YML
```

## Core Workflows in Code
lms-process entry → handler → service → client/repository:
- `QueueConsumer.ProcessMessagesAsync` → `LeadService.ProcessLead` → `TwoWheelerService` / `PartialLeadService` / `UpdateLeadService` / `RetryService` → `DispatchService.Dispatch` (`processLeadService/Services/`)
- `MdpConsumer.ProcessMessagesAsync` → `MdpDealerService.ProcessDealerData` → `MappingService` + repositories

## Integration Clients
lms-process client classes:

| Kind | Client | Evidence |
|---|---|---|
| Service Bus sender/processors | `DispatchService`, `QueueConsumer`, `MdpConsumer` | `processLeadService/Services/DispatchService.cs:25` |
| HTTP | `ApiExchangeService` (old-LMS push `OLD_LMS_URL`, generic GET/POST) | `processLeadService/ExchangeService/ApiExchangeService.cs:47` |
| HTTP (Latlong) | `LatlongService` per brand credentials (`Latlong:*` keys) | `processLeadService/Latlong/LatlongService.cs:130` |
| SQL Server | EF Core `LMSDbContext` (lms.config) | `lms.config/LMSContext` |

## Cross-Cutting Concerns
lms-process cross-cutting concerns:
- Configuration via `AppSettingsService` reading `AppSettings:*`, `Latlong:*`, `ApiUrls:*` keys (`processLeadService/Const/Constants.cs`)
- AutoMapper profiles (`processLeadService/AutoMappings/`)

## Build and Test
lms-process build/test (dotnet CLI against the committed solution/project files; CI pipelines use shared templates):
- `dotnet build processLeadService.sln`
- `dotnet test ProcessLeadTest/ProcessLeadTest.csproj`

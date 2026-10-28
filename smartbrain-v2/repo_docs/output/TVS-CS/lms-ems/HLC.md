---
service_id: lms-ems
doc_type: hlc
last_reviewed: 2026-10-11
---

# lms-ems — High-Level Code

## Application Overview
lms-ems is a C# / ASP.NET Core service in repo `lms_ems` (default branch per `runs/TVS-CS/lms_ems/meta.json`). Its HTTP surface is only `GET /`; the work happens in a Service Bus processor registered at startup.

## Module Summary
lms-ems modules:

| Module | Responsibility |
|---|---|
| `emsService/` | ASP.NET Core host (net7.0): ListenerService, Services, ExchangeService, Repository, Entities, LMSContext, Models, Const |
| `emsTest/` | Unit tests |
| `azure-pipelines/, LMS_ems-CI-Dev.YML` | Azure DevOps CI/CD (`dotnet build` at `LMS_ems-CI-Dev.YML:47`) |

## Folder Structure
lms-ems top-level folders (real paths):
```
emsService/
emsTest/
azure-pipelines/, LMS_ems-CI-Dev.YML
```

## Core Workflows in Code
lms-ems entry → handler → service → client/repository:
- `EmsListenerService.ProcessMessagesAsync` → `EmsService.ProcessEmsLead` → `PushEmsLeads` (HTTP) → repositories → `DispatchService` (Service Bus) / `ApiExchangeService.PublishToOldLms`

## Integration Clients
lms-ems client classes:

| Kind | Client | Evidence |
|---|---|---|
| Service Bus | `DispatchService` (send + `ScheduleMessageAsync`), `EmsListenerService` (processor) | `emsService/Services/DispatchService.cs:18` |
| HTTP | `HttpClient` in `EmsService.SendPostRequest`; `ApiExchangeService` (old LMS) | `emsService/Services/EmsService.cs:152` |
| SQL Server | EF Core `LMSDbContext` | `emsService/LMSContext` |

## Cross-Cutting Concerns
lms-ems cross-cutting concerns:
- Configuration via `AppSettingsService` (`AppSettings:*` keys, `emsService/Const/Constants.cs:13-17`)
- AutoMapper (`emsService/AutoMappings/`)

## Build and Test
lms-ems build/test (dotnet CLI against the committed solution/project files; CI pipelines use shared templates):
- `dotnet build emsService.sln`
- `dotnet test emsTest/emsTest.csproj`

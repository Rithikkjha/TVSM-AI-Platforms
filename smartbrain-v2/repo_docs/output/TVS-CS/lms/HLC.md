---
service_id: lms
doc_type: hlc
last_reviewed: 2026-10-11
---

# lms — High-Level Code

## Application Overview
lms is a C# / ASP.NET Core service in repo `lms` (default branch per `runs/TVS-CS/lms/meta.json`). It hosts HTTP controllers and a Service Bus sender.

## Module Summary
lms modules:

| Module | Responsibility |
|---|---|
| `leadLogs/` | ASP.NET Core API (`leadReceiptService.csproj`, net8.0): Controllers, Services, Repository, Latlong, ExchangeService, AutoMappings, Const |
| `lms.config/` | Shared EF Core model: `Entities/`, `LMSContext/`, `Models/`, `Utils/` |
| `LMSUnitTest/` | Unit tests (`LMSUnitTest.csproj`) |
| `azure-pipeline/, azure-pipelines-domestic/, ci-pipeline.yaml, cd-pipeline.yaml` | Azure DevOps CI/CD (templates from a `devopsRepo` resource, `ci-pipeline.yaml:7`) |
| `dmsService/, emsService/, persistLeadService/` | Only `obj/` build leftovers in this clone; no source |

## Folder Structure
lms top-level folders (real paths):
```
leadLogs/
lms.config/
LMSUnitTest/
azure-pipeline/, azure-pipelines-domestic/, ci-pipeline.yaml, cd-pipeline.yaml
dmsService/, emsService/, persistLeadService/
```

## Core Workflows in Code
lms entry → handler → service → client/repository:
- `POST /api/lead`: `LeadAcquisitionController.Lead` → `LeadLogService.ProcessLead` → `LeadDelegate.ProcessBasic` → `LeadValidator` → `ProcessValidLeadService` / `ProcessInvalidLeadService` / `ProcessDuplicateLeadService` → `LeadDispatchService.Dispatch` (Service Bus) + repositories (`leadLogs/Repository/*.cs`, EF Core `LMSDbContext`)
- `POST /api/b2b/lead`: `WebhooksController.Post` → `WebhookService` (`leadLogs/Services/WebhookService.cs`)
- `POST /api/leads/*`: `LeadGetController` → `LeadGetService` / `LeadOneViewService` → `LeadGetRepository` / `LeadOneViewRepository`

## Integration Clients
lms client classes:

| Kind | Client | Evidence |
|---|---|---|
| Service Bus sender | `LeadDispatchService` (`Azure.Messaging.ServiceBus`, `ServiceBusClient.CreateSender`) | `leadLogs/Services/LeadDispatchService.cs:21` |
| Key Vault | `AddAzureClients` with `KeyVault` config section | `leadLogs/Startup.cs:74-77` |
| SQL Server | EF Core `LMSDbContext` (`AddDbContext`) | `leadLogs/Startup.cs:67` |
| HTTP | `HttpClient` in `WebhookService` | `leadLogs/Services/WebhookService.cs:145` |

## Cross-Cutting Concerns
lms cross-cutting concerns:
- Validation: FluentValidation + custom `LeadValidator` / `UpdateValidator` / `CommsValidator` (`leadLogs/Services/`)
- Mapping: AutoMapper profiles in `leadLogs/AutoMappings/`
- Configuration: `AppSettingsService` builds config from `appsettings.json`, `appsettings.{env}.json` and environment variables (`leadLogs/Const/AppSettingsService.cs:11-15`)
- Swagger: Swashbuckle `AddSwaggerGen` (`leadLogs/Startup.cs:91`)

## Build and Test
lms build/test (dotnet CLI against the committed solution/project files; CI pipelines use shared templates):
- `dotnet build lms.sln`
- `dotnet test LMSUnitTest/LMSUnitTest.csproj`
- `docker build -f Dockerfile .` (base images `mcr.microsoft.com/dotnet/sdk:8.0` / `aspnet:8.0`, ports 8080/8081)

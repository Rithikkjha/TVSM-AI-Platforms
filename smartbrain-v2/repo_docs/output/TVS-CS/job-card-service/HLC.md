---
service_id: job-card-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# job-card-service — High-Level Code

## Application Overview
job-card-service (`job-card-service`) is a `backend-api` codebase; stacks dotnet; head `a8a8a11835722bc55aea8aac7f98a62256ae902f`.
Entry points: `src/Jobcard.API/Program.cs`.

## Module Summary
job-card-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| src/Jobcard.API | `src/Jobcard.API` | service: 16 endpoints, 1 outbound calls, 0 messaging, 0 data-access |
| src/Jobcard.APITests | `src/Jobcard.APITests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Jobcard.Application | `src/Jobcard.Application` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Jobcard.ApplicationTests | `src/Jobcard.ApplicationTests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Jobcard.Domain | `src/Jobcard.Domain` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Jobcard.Infrastructure | `src/Jobcard.Infrastructure` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 2 data-access |
| src/Jobcard.InfrastructureTests | `src/Jobcard.InfrastructureTests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
job-card-service top-level folders (3 levels):

```
job-card-service/
├── azure_pipelines/
├── src/
│   ├── Jobcard.API/
│   │   ├── Attributes/
│   │   ├── Controllers/
│   │   ├── Filters/
│   │   ├── Models/
│   │   ├── Properties/
│   │   ├── Security/
│   │   ├── wwwroot/
│   ├── Jobcard.APITests/
│   │   ├── Controllers/
│   ├── Jobcard.Application/
│   │   ├── Extensions/
│   │   ├── Jobcard/
│   ├── Jobcard.ApplicationTests/
│   │   ├── Jobcard/
│   ├── Jobcard.Domain/
│   │   ├── Entities/
│   │   ├── Exceptions/
│   │   ├── Repositories/
│   │   ├── Seedwork/
│   ├── Jobcard.Infrastructure/
│   │   ├── EntityConfigurations/
│   │   ├── Extensions/
│   │   ├── Factory/
│   │   ├── Interfaces/
│   │   ├── Migrations/
│   │   ├── Persistence/
│   │   ├── Repositories/
│   ├── Jobcard.InfrastructureTests/
│   │   ├── Extensions/
```

## Core Workflows in Code
job-card-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### JobcardController
1. `src/Jobcard.API/Controllers/JobcardController.cs` receives 6 route(s), e.g. `GET /api/jobcard/configurations/fetch/{frameNo}` → `JobcardController.GetJobTypes`.
2. Module `src/Jobcard.API` makes outbound calls to: `Unknown(env:OTEL_EXPORTER_OTLP_ENDPOINT)`.

### LabourController
1. `src/Jobcard.API/Controllers/LabourController.cs` receives 5 route(s), e.g. `GET /api/labour/frt/fetch/{dealerId}/{branchId}/{labourTypes}` → `LabourController.FetchLabour`.
2. Module `src/Jobcard.API` makes outbound calls to: `Unknown(env:OTEL_EXPORTER_OTLP_ENDPOINT)`.

### AutoLaborController
1. `src/Jobcard.API/Controllers/AutoLaborController.cs` receives 3 route(s), e.g. `GET /api/master/labour/fetch` → `AutoLaborController.FetchMasterLabor`.
2. Module `src/Jobcard.API` makes outbound calls to: `Unknown(env:OTEL_EXPORTER_OTLP_ENDPOINT)`.

### AmcController
1. `src/Jobcard.API/Controllers/AmcController.cs` receives 1 route(s), e.g. `GET /api/service/amc/fetch/{frame-no}` → `AmcController.GetAmcInfoByFrameNo`.
2. Module `src/Jobcard.API` makes outbound calls to: `Unknown(env:OTEL_EXPORTER_OTLP_ENDPOINT)`.

### PartsController
1. `src/Jobcard.API/Controllers/PartsController.cs` receives 1 route(s), e.g. `GET /api/service/frt/parts/fetch/{modelId}/{dealerId}/{branchId}` → `PartsController.GetFrtPartsBasedOnModelId`.
2. Module `src/Jobcard.API` makes outbound calls to: `Unknown(env:OTEL_EXPORTER_OTLP_ENDPOINT)`.

## Integration Clients
job-card-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/Jobcard.API/Program.cs` | env:OTEL_EXPORTER_OTLP_ENDPOINT |
| data store (db) | `src/Jobcard.Infrastructure/Extensions/ServiceCollectionExtensions.cs:24` | Unknown |
| data store (db) | `src/Jobcard.Infrastructure/Extensions/ServiceCollectionExtensions.cs:23` | Unknown |

## Cross-Cutting Concerns
job-card-service cross-cutting code:
- Auth: none found
- Error handling: `src/Jobcard.API/Program.cs:386` (UseExceptionHandler)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `Microsoft.Extensions.Logging`

## Build and Test
job-card-service build/test commands from manifests:
- .NET: `dotnet build` / `dotnet test` (`Jobcard.sln`)
- CI pipelines: `azure_pipelines/ast-image-scan-job-card-service-pipeline.yaml:1`, `azure_pipelines/ast-job-card-prod-pipeline.yaml:1`, `azure_pipelines/ast-job-card-uat-pipeline.yaml:1`, `azure_pipelines/cd-pipeline.yaml:1`, `azure_pipelines/ci-pipeline.yaml:1`, `azure_pipelines/sonar.yaml:1`, `sonar.yaml:1`

---
service_id: appointment-booking-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# appointment-booking-service — High-Level Code

## Application Overview
appointment-booking-service (`appointment-booking-service`) is a `backend-api` codebase; stacks dotnet; head `712beccc5ad6ce206de00631bbbdfdcb3911ead2`.
Entry points: `src/Appointment.API/Program.cs`.

## Module Summary
appointment-booking-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| src/Appointment.API | `src/Appointment.API` | service: 10 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Appointment.API.Tests | `src/Appointment.API.Tests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Appointment.Application | `src/Appointment.Application` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Appointment.Application.Tests | `src/Appointment.Application.Tests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Appointment.Domain | `src/Appointment.Domain` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| src/Appointment.Infrastructure | `src/Appointment.Infrastructure` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 1 data-access |
| src/Appointment.Infrastructure.Tests | `src/Appointment.Infrastructure.Tests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
appointment-booking-service top-level folders (3 levels):

```
appointment-booking-service/
├── azure_pipelines/
├── src/
│   ├── Appointment.API/
│   │   ├── Attributes/
│   │   ├── Controllers/
│   │   ├── Filters/
│   │   ├── Properties/
│   │   ├── Security/
│   │   ├── wwwroot/
│   ├── Appointment.API.Tests/
│   │   ├── Controllers/
│   ├── Appointment.Application/
│   │   ├── Appointment/
│   │   ├── Extensions/
│   │   ├── VehicleServices/
│   ├── Appointment.Application.Tests/
│   │   ├── Appointment/
│   │   ├── VehicleTests/
│   ├── Appointment.Domain/
│   │   ├── AggregatesModel/
│   │   ├── Entities/
│   │   ├── Exceptions/
│   │   ├── Repositories/
│   │   ├── SeedWork/
│   ├── Appointment.Infrastructure/
│   │   ├── EntityConfigurations/
│   │   ├── Extensions/
│   │   ├── Migrations/
│   │   ├── Persistence/
│   │   ├── Repositories/
│   ├── Appointment.Infrastructure.Tests/
│   │   ├── Extensions/
│   │   ├── Repositories/
```

## Core Workflows in Code
appointment-booking-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### AppointmentController
1. `src/Appointment.API/Controllers/AppointmentController.cs` receives 7 route(s), e.g. `GET /api/service/appointment-request/fetch/{frameNo}` → `AppointmentController.GetByFrameNo`.

### swagger-original
1. `src/Appointment.API/wwwroot/swagger-original.json` receives 2 route(s), e.g. `GET /virts/tvsmotorcompany/appointment-booking-service/1.0.0/api/service/appointment-request/fetch/{frame-no}` → `None`.

### VehicleController
1. `src/Appointment.API/Controllers/VehicleController.cs` receives 1 route(s), e.g. `POST /api/Vehicle/fetch` → `VehicleController.GetVehicleDetailsAsync`.

## Integration Clients
appointment-booking-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| data store (db) | `src/Appointment.Infrastructure/Extensions/ServiceCollectionExtensions.cs:19` | Unknown |

## Cross-Cutting Concerns
appointment-booking-service cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 7 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `Microsoft.Extensions.Logging.Abstractions`

## Build and Test
appointment-booking-service build/test commands from manifests:
- .NET: `dotnet build` / `dotnet test` (`Appointment.sln`)
- CI pipelines: `azure_pipelines/ast-appointment-bs-prod-pipeline.yaml:1`, `azure_pipelines/ast-appointment-bs-uat-pipeline.yaml:1`, `azure_pipelines/ast-image-scan-appointment-booking-service-pipeline.yaml:1`, `azure_pipelines/cd-pipeline.yaml:1`, `azure_pipelines/ci-pipeline.yaml:1`, `azure_pipelines/sonar.yaml:1`

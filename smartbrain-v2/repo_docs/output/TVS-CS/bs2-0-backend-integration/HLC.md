---
service_id: bs2-0-backend-integration
doc_type: hlc
last_reviewed: 2026-10-11
---

# bs2-0-backend-integration — High-Level Code

## Application Overview
bs2-0-backend-integration (`BS2.0Backend_Integration`) is a `backend-api` codebase; stacks dotnet; head `f2caa16c18a0e41c1d22549e1eaebafb409795e2`.
Entry points: `Program.cs`.

## Module Summary
bs2-0-backend-integration modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 27 endpoints, 1 outbound calls, 2 messaging, 1 data-access |

## Folder Structure
bs2-0-backend-integration top-level folders (3 levels):

```
BS2.0Backend_Integration/
├── AutoMapper/
├── Const/
├── Controllers/
├── CustomerBayAppContext/
├── Entities/
├── Model/
├── Properties/
│   ├── PublishProfiles/
├── QueueDispatcher/
├── QueueListeners/
├── Repository/
├── Services/
├── TopicListener/
```

## Core Workflows in Code
bs2-0-backend-integration workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### DealerDashboardController
1. `Controllers/DealerDashboardController.cs` receives 13 route(s), e.g. `GET /api/Export` → `DealerDashboardController.GetExport`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `Controllers/SAPController.cs:247`.

### BookingsController
1. `Controllers/BookingsController.cs` receives 10 route(s), e.g. `GET /api/areaAccountant/Tdr` → `BookingsController.TdrDetails`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `Controllers/SAPController.cs:247`.

### BookingExport
1. `Controllers/BookingExport.cs` receives 2 route(s), e.g. `GET /api/areaAccountant/downloadDetails` → `BookingExport.GetDownloadDetails`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `Controllers/SAPController.cs:247`.

### SAPController
1. `Controllers/SAPController.cs` receives 2 route(s), e.g. `GET /api/sap/GetSAPDocumentNumber` → `SAPController.GetSAPDocumentNumberAsync`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `Controllers/SAPController.cs:247`.

### Job ExportQueue
1. `QueueListeners/ExportQueue.cs:234` runs on hosted-service `None`.

### Consumer prod.booking
1. `TopicListener/BookingServiceTopicListener.cs:62` handles messages (azure-service-bus, trigger processor).

## Integration Clients
bs2-0-backend-integration outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `Services/EmailServices.cs` | literal |
| azure-service-bus publish Unknown (`unresolved`) | `QueueDispatcher/Dispatcher.cs:15` | unknown |
| azure-service-bus subscribe prod.booking | `TopicListener/BookingServiceTopicListener.cs:62` | ServiceBusSettings:TopicName |
| data store (tvsmazevsdbprd01-dealer) | `Controllers/SAPController.cs:247` | Unknown |

## Cross-Cutting Concerns
bs2-0-backend-integration cross-cutting code:
- Auth: `Program.cs:28` (AddAuthentication)
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
bs2-0-backend-integration build/test commands from manifests:
- .NET: `dotnet build` / `dotnet test` ()
- CI pipelines: none found

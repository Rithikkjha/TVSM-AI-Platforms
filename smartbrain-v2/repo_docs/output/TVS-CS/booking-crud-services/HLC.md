---
service_id: booking-crud-services
doc_type: hlc
last_reviewed: 2026-10-11
---

# booking-crud-services — High-Level Code

## Application Overview
booking-crud-services (`booking-crud-services`) is a `backend-api` codebase; stacks express, nest, node; head `efca504995a5be9258e300f4a1bf123a1c252474`.
Entry points: `src/main.ts`, `src/app.module.ts`.

## Module Summary
booking-crud-services modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 13 endpoints, 1 outbound calls, 6 messaging, 1 data-access |

## Folder Structure
booking-crud-services top-level folders (3 levels):

```
booking-crud-services/
├── azure-pipelines/
├── docs/
├── scripts/
│   ├── sql/
├── src/
│   ├── bookings/
│   │   ├── controllers/
│   │   ├── dto/
│   │   ├── services/
│   ├── cloud-conductor/
│   │   ├── services/
│   ├── database/
│   │   ├── entities/
│   ├── logger/
│   ├── shared/
│   │   ├── constants/
│   │   ├── exceptions/
│   │   ├── interceptors/
├── test/
```

## Core Workflows in Code
booking-crud-services workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### Booking Service.openapi
1. `Booking Service.openapi.yaml` receives 13 route(s), e.g. `GET /bookings/health` → `BookingsController.getHealthCheck`.
2. Module `.` makes outbound calls to: `Unknown(env:CCAURL)`.
3. Module `.` data access via `scripts/sql/create-retail-finance-detail-table.sql:58`.

### Consumer Unknown (`ATP_TOPIC_NAME`)
1. `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` handles messages (azure-service-bus, trigger processor).

### Consumer Unknown (`DEALER_TOPIC_NAME`)
1. `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` handles messages (azure-service-bus, trigger processor).

### Consumer Unknown (`DMS_TOPIC_NAME`)
1. `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` handles messages (azure-service-bus, trigger processor).

### Consumer Unknown (`TOPIC_NAME`)
1. `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` handles messages (azure-service-bus, trigger processor).

## Integration Clients
booking-crud-services outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/bookings/services/booking-refund-status-update/ccavenue-refund-status-update.service.ts` | env:CCAURL |
| azure-service-bus publish Unknown (name from `env:NORTON_BS_TOPIC_NAME`) | `src/bookings/services/norton-bs-sync/norton-bs-sync.service.ts:67` | NORTON_BS_TOPIC_NAME |
| azure-service-bus publish Unknown (`TOPIC_NAME`) | `src/cloud-conductor/services/publisher/topic-publisher.service.ts:43` | TOPIC_NAME |
| azure-service-bus subscribe Unknown (`ATP_TOPIC_NAME`) | `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` | ATP_TOPIC_NAME |
| azure-service-bus subscribe Unknown (`DEALER_TOPIC_NAME`) | `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` | DEALER_TOPIC_NAME |
| azure-service-bus subscribe Unknown (`DMS_TOPIC_NAME`) | `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` | DMS_TOPIC_NAME |
| azure-service-bus subscribe Unknown (`TOPIC_NAME`) | `src/cloud-conductor/services/listener/base-topic-listener.service.ts:121` | TOPIC_NAME |
| data store (db) | `scripts/sql/create-retail-finance-detail-table.sql:58` | Unknown |

## Cross-Cutting Concerns
booking-crud-services cross-cutting code:
- Auth: none found
- Error handling: `src/shared/exceptions/global.exception.ts:9` (@Catch()
- Validation: 433 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `@nestjs/cache-manager`, `@opentelemetry/api-logs`, `@opentelemetry/exporter-logs-otlp-http`, `@opentelemetry/sdk-logs`, `cache-manager`, `file-entry-cache`, `flat-cache`, `ioredis`

## Build and Test
booking-crud-services build/test commands from manifests:
- `package.json` scripts: `npm run build`, `npm run start`, `npm run start:dev`, `npm run start:prod`, `npm run lint`, `npm run test`, `npm run test:cov`, `npm run test:e2e`
- CI pipelines: `AST_Website_Corporate_booking_crud_services_DEV_Pipeline.yml:2`, `azure-pipelines/ast-booking-crud-prod-pipeline.yaml:1`, `azure-pipelines/ast-booking-crud-uat-pipeline.yaml:1`, `azure-pipelines/ast-image-scan-booking-crud-pipeline.yaml:1`, `azure-pipelines/cd-pipeline.yaml:1`, `azure-pipelines/ci-pipeline.yaml:1`, `azure-pipelines/sonar.yaml:1`

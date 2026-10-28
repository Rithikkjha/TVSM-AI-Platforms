---
service_id: async-communication-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# async-communication-service — High-Level Code

## Application Overview
async-communication-service (`async-communication-service`) is a `backend-api` codebase; stacks nest, node; head `5ed01ba3c9130f0c18709bee2c2c2454735606e7`.
Entry points: `src/main.ts`, `src/app.module.ts`.

## Module Summary
async-communication-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 0 endpoints, 0 outbound calls, 1 messaging, 1 data-access |

## Folder Structure
async-communication-service top-level folders (3 levels):

```
async-communication-service/
├── azure_pipelines/
├── src/
│   ├── communication/
│   │   ├── bto-mailer/
│   │   ├── dto/
│   │   ├── ev-mailer/
│   │   ├── ice-mailer/
│   │   ├── spd-mailer/
│   ├── custom-repositories/
│   │   ├── booking-repository/
│   │   ├── dbLogger/
│   ├── database/
│   │   ├── entities/
│   ├── logger/
│   ├── shared/
│   │   ├── btoSMSBody/
│   │   ├── cloudService/
│   │   ├── constants/
│   │   ├── mailBody/
│   │   ├── salesforce/
├── test/
```

## Core Workflows in Code
async-communication-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### Job None
1. `src/shared/salesforce/scheduler/bto-scheduler.ts:13` runs on node-cron `30 15 * * *`.

### Job None
1. `src/shared/salesforce/scheduler/bto-scheduler.ts:24` runs on node-cron `30 16 * * *`.

### Consumer Unknown (`TOPIC_NAME`)
1. `src/shared/cloudService/topicListener/topic-listener.service.ts:71` handles messages (azure-service-bus, trigger processor).

## Integration Clients
async-communication-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| azure-service-bus subscribe Unknown (`TOPIC_NAME`) | `src/shared/cloudService/topicListener/topic-listener.service.ts:71` | TOPIC_NAME |
| data store (db) | `src/app.module.ts:40` | Unknown |

## Cross-Cutting Concerns
async-communication-service cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
async-communication-service build/test commands from manifests:
- `package.json` scripts: `npm run build`, `npm run start`, `npm run start:dev`, `npm run start:prod`, `npm run lint`, `npm run test`, `npm run test:cov`, `npm run test:e2e`
- CI pipelines: `azure_pipelines/ast-async-comm-uat-pipeline.yaml:1`, `azure_pipelines/ast-image-scan-async-comm-pipeline.yaml:1`, `azure_pipelines/cd-pipeline.yaml:1`, `azure_pipelines/ci-pipeline.yaml:1`, `azure_pipelines/sonar.yaml:1`

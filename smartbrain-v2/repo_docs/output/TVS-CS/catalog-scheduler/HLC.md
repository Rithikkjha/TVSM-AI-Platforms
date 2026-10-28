---
service_id: catalog-scheduler
doc_type: hlc
last_reviewed: 2026-10-11
---

# catalog-scheduler — High-Level Code

## Application Overview
catalog-scheduler (`Catalog-Scheduler`) is a `function` codebase; stacks node; head `64e1298bf49074040116365c990893fda0ea11a2`.
Entry points: Unknown.

## Module Summary
catalog-scheduler modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | function-app: 0 endpoints, 8 outbound calls, 1 messaging, 1 data-access |

## Folder Structure
catalog-scheduler top-level folders (3 levels):

```
Catalog-Scheduler/
├── src/
│   ├── constants/
│   ├── db-connection/
│   ├── functions/
│   ├── http/
│   ├── merchandise-accessories-ingestion-job/
│   │   ├── constants/
│   │   ├── db-connection/
│   │   ├── merchandise-accessories-service/
│   │   ├── wrapper-service/
│   ├── product-master-ingestion-job/
│   ├── product-price-ingestion-job/
│   │   ├── catalog-service/
│   │   ├── constants/
│   │   ├── data-sources/
│   │   ├── db-connection/
│   │   ├── master-data/
│   │   ├── price-updates/
│   │   ├── wrapper-service/
│   ├── secrete-keys-service/
```

## Core Workflows in Code
catalog-scheduler workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### Job merchandise-accessories-ingestion-job
1. `src/functions/merchandise-accessories-ingestion-job.js:5` runs on timer-trigger `None`.

### Job product-price-ingestion-job
1. `src/functions/product-price-ingestion-job.js:6` runs on timer-trigger `None`.

## Integration Clients
catalog-scheduler outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js` | env:AUTHORIZATION_TOKEN_URL |
| Unknown | `src/product-price-ingestion-job/catalog-service/catalog-service.js` | env:CATALOG_BASE_URL |
| Unknown | `src/merchandise-accessories-ingestion-job/merchandise-accessories-service/merchandise-accessories-implementer.js` | env:MERCHANDISE_ACCESSORIES_BASE_URL |
| Unknown | `src/product-price-ingestion-job/data-sources/discount-data-source/discount-data-source-api.js` | literal |
| `core-commerce-platform-api-service` | `src/product-price-ingestion-job/catalog-service/catalog-config-service.js`, `src/product-price-ingestion-job/catalog-service/catalog-service.js`, `src/product-price-ingestion-job/data-sources/product-data-source/product-data-source-api.js` | env:CATALOG_BASE_URL |
| `price-engine-micro-service-backend` | `src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js` | env:PRICE_URL |
| azure-service-bus publish Unknown (name from `env:SERVICE_BUS_TOPIC_NAME`) | `src/product-price-ingestion-job/price-updates/price-updates.js:399` | SERVICE_BUS_TOPIC_NAME |
| data store (db) | `src/db-connection/db-configuration.js:19` | Unknown |

## Cross-Cutting Concerns
catalog-scheduler cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
catalog-scheduler build/test commands from manifests:
- `package.json` scripts: `npm run start`
- CI pipelines: `AST_CCP_Catalog_Service_Catalog_Scheduler_Release_Pipeline.yml:1`, `AST_CCP_Catalog_Service_Catalog_Scheduler_UAT_Pipeline.yml:1`, `cd-dev-pipeline.yaml:1`, `cd-prod-pipeline.yaml:1`, `cd-uat-pipeline.yaml:1`, `ci-dev-pipeline.yaml:1`, `ci-prod-pipeline.yaml:1`, `ci-uat-pipeline.yaml:1`

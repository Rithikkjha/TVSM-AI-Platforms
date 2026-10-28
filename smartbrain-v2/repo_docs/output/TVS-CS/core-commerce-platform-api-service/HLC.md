---
service_id: core-commerce-platform-api-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# core-commerce-platform-api-service — High-Level Code

## Application Overview
core-commerce-platform-api-service (`Core-Commerce-Platform-API-Service`) is a `backend-api` codebase; stacks express, node; head `70a97b8843ba9e245a936ad595939f673d935a62`.
Entry points: Unknown.

## Module Summary
core-commerce-platform-api-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 13 endpoints, 7 outbound calls, 0 messaging, 3 data-access |

## Folder Structure
core-commerce-platform-api-service top-level folders (3 levels):

```
Core-Commerce-Platform-API-Service/
├── data-insertion-scripts/
├── sonar-exclusion-function/
│   ├── scripts/
├── src/
│   ├── config/
│   ├── constants/
│   ├── db/
│   │   ├── mongodb/
│   ├── handlers/
│   │   ├── test/
│   │   ├── validators/
│   ├── middleware/
│   │   ├── test/
│   ├── models/
│   │   ├── mongodb/
│   ├── rest/
│   │   ├── API-directories/
│   │   ├── http/
│   │   ├── https/
│   ├── routes/
│   │   ├── api/
│   ├── services/
│   │   ├── cache/
│   │   ├── test/
│   │   ├── validators/
│   ├── utils/
│   │   ├── classes/
│   │   ├── decorators/
│   │   ├── functions/
│   │   ├── implementers/
│   │   ├── interface/
│   │   ├── reshapeObjects/
│   │   ├── test/
```

## Core Workflows in Code
core-commerce-platform-api-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### catalog-routes
1. `src/routes/api/catalog-routes.ts` receives 7 route(s), e.g. `DELETE /catalogs/{id}` → `catalogHandler.deleteCatalog`.
2. Module `.` makes outbound calls to: `Unknown(env:BUMBLEBEE_EV_API_URL)`, `Unknown(env:BUMBLEBEE_ICE_API_URL)`, `Unknown(env:SHOPIFY_API_URL)`, `Unknown(literal)`, `Unknown(unknown)`.
3. Module `.` data access via `sonar-exclusion-function/scripts/data-migration-script.ts:35`, `src/db/mongodb/db.ts:18`, `src/config/redis-config.ts:63`.

### catalog-configuration-routes
1. `src/routes/api/catalog-configuration-routes.ts` receives 2 route(s), e.g. `GET /catalog-configs/{nameSpace}` → `catalogConfigurationHandler.getCatalogConfiguration`.
2. Module `.` makes outbound calls to: `Unknown(env:BUMBLEBEE_EV_API_URL)`, `Unknown(env:BUMBLEBEE_ICE_API_URL)`, `Unknown(env:SHOPIFY_API_URL)`, `Unknown(literal)`, `Unknown(unknown)`.
3. Module `.` data access via `sonar-exclusion-function/scripts/data-migration-script.ts:35`, `src/db/mongodb/db.ts:18`, `src/config/redis-config.ts:63`.

### cache-routes
1. `src/routes/api/cache-routes.ts` receives 1 route(s), e.g. `DELETE /cache/clear` → `cacheHandler.clearAllCache`.
2. Module `.` makes outbound calls to: `Unknown(env:BUMBLEBEE_EV_API_URL)`, `Unknown(env:BUMBLEBEE_ICE_API_URL)`, `Unknown(env:SHOPIFY_API_URL)`, `Unknown(literal)`, `Unknown(unknown)`.
3. Module `.` data access via `sonar-exclusion-function/scripts/data-migration-script.ts:35`, `src/db/mongodb/db.ts:18`, `src/config/redis-config.ts:63`.

### application-heath-routes
1. `src/routes/api/application-heath-routes.ts` receives 1 route(s), e.g. `GET /health` → `applicationHealthHandler.checkApplicationHealth`.
2. Module `.` makes outbound calls to: `Unknown(env:BUMBLEBEE_EV_API_URL)`, `Unknown(env:BUMBLEBEE_ICE_API_URL)`, `Unknown(env:SHOPIFY_API_URL)`, `Unknown(literal)`, `Unknown(unknown)`.
3. Module `.` data access via `sonar-exclusion-function/scripts/data-migration-script.ts:35`, `src/db/mongodb/db.ts:18`, `src/config/redis-config.ts:63`.

### shopify-routes
1. `src/routes/api/shopify-routes.ts` receives 1 route(s), e.g. `GET /shopify/products` → `shopifyHandler.getProducts`.
2. Module `.` makes outbound calls to: `Unknown(env:BUMBLEBEE_EV_API_URL)`, `Unknown(env:BUMBLEBEE_ICE_API_URL)`, `Unknown(env:SHOPIFY_API_URL)`, `Unknown(literal)`, `Unknown(unknown)`.
3. Module `.` data access via `sonar-exclusion-function/scripts/data-migration-script.ts:35`, `src/db/mongodb/db.ts:18`, `src/config/redis-config.ts:63`.

### vehicle-accessories-pricing-routes
1. `src/routes/api/vehicle-accessories-pricing-routes.ts` receives 1 route(s), e.g. `POST /vehicle-accessories-pricing/prices` → `vehicleAccessoriesPricingHandler.bulkInsertPricing`.
2. Module `.` makes outbound calls to: `Unknown(env:BUMBLEBEE_EV_API_URL)`, `Unknown(env:BUMBLEBEE_ICE_API_URL)`, `Unknown(env:SHOPIFY_API_URL)`, `Unknown(literal)`, `Unknown(unknown)`.
3. Module `.` data access via `sonar-exclusion-function/scripts/data-migration-script.ts:35`, `src/db/mongodb/db.ts:18`, `src/config/redis-config.ts:63`.

## Integration Clients
core-commerce-platform-api-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/utils/implementers/ev-implementer/ev-implementer.ts` | env:BUMBLEBEE_EV_API_URL |
| Unknown | `src/utils/implementers/ice-implementer/ice-implementer.ts` | env:BUMBLEBEE_ICE_API_URL |
| Unknown | `src/utils/implementers/shopify-implementer/shopify-implementer.ts` | env:SHOPIFY_API_URL |
| Unknown | `sonar-exclusion-function/scripts/ice-ev-model-data-grouping.ts` | literal |
| Unknown | `src/services/shopify-service.ts` | unknown |
| data store (db) | `sonar-exclusion-function/scripts/data-migration-script.ts:35` | Unknown |
| data store (db) | `src/db/mongodb/db.ts:18` | Unknown |
| data store (db) | `src/config/redis-config.ts:63` | Unknown |

## Cross-Cutting Concerns
core-commerce-platform-api-service cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `redis`

## Build and Test
core-commerce-platform-api-service build/test commands from manifests:
- `package.json` scripts: `npm run build`, `npm run dev`, `npm run start`, `npm run test`
- CI pipelines: `azure-pipelines.yml:6`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`

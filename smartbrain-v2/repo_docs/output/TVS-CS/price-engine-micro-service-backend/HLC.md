---
service_id: price-engine-micro-service-backend
doc_type: hlc
last_reviewed: 2026-10-11
---

# price-engine-micro-service-backend — High-Level Code

## Application Overview
price-engine-micro-service-backend (`Price-Engine-MicroService-Backend`) is a `backend-api` codebase; stacks express, node; head `1d3f3859fa0342ee651d66074925c98053bfe16a`.
Entry points: Unknown.

## Module Summary
price-engine-micro-service-backend modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 17 endpoints, 3 outbound calls, 5 messaging, 3 data-access |

## Folder Structure
price-engine-micro-service-backend top-level folders (3 levels):

```
Price-Engine-MicroService-Backend/
├── data-insertion-scripts/
├── sonar-exclusion-function/
│   ├── scripts/
│   ├── service-bus/
│   │   ├── implemeters/
├── src/
│   ├── config/
│   │   ├── test/
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
│   │   ├── http/
│   ├── routes/
│   │   ├── api/
│   ├── services/
│   │   ├── test/
│   ├── utils/
│   │   ├── classes/
│   │   ├── decorators/
│   │   ├── functions/
│   │   ├── interface/
│   │   ├── reshape-objects/
│   │   ├── service-bus-implementors/
│   │   ├── test/
```

## Core Workflows in Code
price-engine-micro-service-backend workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### on-road-price-routes
1. `src/routes/api/on-road-price-routes.ts` receives 7 route(s), e.g. `GET /on-road-prices/models/{engineType}` → `onRoadPriceHandler.getVehicleModelsBasedOnEngineType`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### product-price-components-routes
1. `src/routes/api/product-price-components-routes.ts` receives 4 route(s), e.g. `GET /product-price-components/custom/engineType/{engineType}` → `productPriceComponentsHandler.getComponentsForCustomCreation`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### region-routes
1. `src/routes/api/region-routes.ts` receives 2 route(s), e.g. `GET /regions/cities` → `regionHandler.getAllCities`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### cache-routes
1. `src/routes/api/cache-routes.ts` receives 1 route(s), e.g. `DELETE /cache/clear` → `cacheHandler.clearAllCache`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### price-component-routes
1. `src/routes/api/price-component-routes.ts` receives 1 route(s), e.g. `GET /price-components/{engineType}` → `priceComponentHandler.getComponentNames`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### product-routes
1. `src/routes/api/product-routes.ts` receives 1 route(s), e.g. `GET /products/vehicle/{engineType}/models` → `productHandler.getAllVehicleModels`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### price-upload-routes
1. `src/routes/api/price-upload-routes.ts` receives 1 route(s), e.g. `POST /price/upload` → `priceUploadHandler.uploadPriceFile`.
2. Module `.` makes outbound calls to: `Unknown(literal)`, `master-data-platform`.
3. Module `.` data access via `sonar-exclusion-function/scripts/insert-states-data.ts:35`, `src/db/mongodb/db.ts:16`, `src/config/redis-config.ts:24`.

### Consumer Unknown (name from `env:TOPIC_NAME_PRICE`)
1. `src/utils/service-bus-implementors/service-bus-connection-implementer.ts:21` handles messages (azure-service-bus, trigger processor).

### Consumer Unknown (name from `env:TOPIC_NAME_PRODUCT`)
1. `src/utils/service-bus-implementors/service-bus-connection-implementer.ts:21` handles messages (azure-service-bus, trigger processor).

### Consumer uat.mdp.price.vehicle
1. `sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18` handles messages (azure-service-bus, trigger processor).

### Consumer uat.mdp.product.vehicle
1. `sonar-exclusion-function/service-bus/implemeters/product-service-bus-implementer.ts:28` handles messages (azure-service-bus, trigger processor).

## Integration Clients
price-engine-micro-service-backend outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `sonar-exclusion-function/service-bus/service-bus.ts` | literal |
| `master-data-platform` | `sonar-exclusion-function/service-bus/service-bus.ts` | literal |
| azure-service-bus publish Unknown (name from `env:TOPIC_NAME_MARKETPLACE`) | `src/services/price-engine-price-publisher.ts:17` | TOPIC_NAME_MARKETPLACE |
| azure-service-bus subscribe Unknown (name from `env:TOPIC_NAME_PRICE`) | `src/utils/service-bus-implementors/service-bus-connection-implementer.ts:21` | TOPIC_NAME_PRICE |
| azure-service-bus subscribe Unknown (name from `env:TOPIC_NAME_PRODUCT`) | `src/utils/service-bus-implementors/service-bus-connection-implementer.ts:21` | TOPIC_NAME_PRODUCT |
| azure-service-bus subscribe uat.mdp.price.vehicle | `sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18` | literal |
| azure-service-bus subscribe uat.mdp.product.vehicle | `sonar-exclusion-function/service-bus/implemeters/product-service-bus-implementer.ts:28` | literal |
| data store (db) | `sonar-exclusion-function/scripts/insert-states-data.ts:35` | Unknown |
| data store (db) | `src/db/mongodb/db.ts:16` | Unknown |
| data store (db) | `src/config/redis-config.ts:24` | Unknown |

## Cross-Cutting Concerns
price-engine-micro-service-backend cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `redis`

## Build and Test
price-engine-micro-service-backend build/test commands from manifests:
- `package.json` scripts: `npm run build`, `npm run dev`, `npm run start`, `npm run test`
- CI pipelines: `AST_MDP_Price-Engine-MicroService-Backend_release_Pipeline.yml:1`, `pe-ms-be-prod-cd.yml:1`, `pe-ms-be-prod-ci.yml:1`

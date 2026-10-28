---
service_id: price-engine-micro-service-backend
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# price-engine-micro-service-backend — API Specification

## Authentication
price-engine-micro-service-backend endpoint auth as extracted: `None` × 17.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
price-engine-micro-service-backend exposes 17 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| DELETE | `/cache/clear` | Unknown | handler `cacheHandler.clearAllCache` | Unknown |
| GET | `/on-road-prices/models/{engineType}` | Unknown | handler `onRoadPriceHandler.getVehicleModelsBasedOnEngineType` | Unknown |
| GET | `/on-road-prices/products/{modelId}` | Unknown | handler `onRoadPriceHandler.getORPComponents` | Unknown |
| GET | `/on-road-prices/vehicles/engineType/{engineType}` | Unknown | handler `onRoadPriceHandler.getOnRoadPrices` | catalog-scheduler |
| GET | `/on-road-prices/{modelId}` | Unknown | handler `onRoadPriceHandler.getOnRoadPriceBasedOnModelId` | Unknown |
| GET | `/price-components/{engineType}` | Unknown | handler `priceComponentHandler.getComponentNames` | Unknown |
| GET | `/product-price-components/custom/engineType/{engineType}` | Unknown | handler `productPriceComponentsHandler.getComponentsForCustomCreation` | Unknown |
| GET | `/product-price-components/{engineType}/{componentId}` | Unknown | handler `productPriceComponentsHandler.getComponentAssociatedModelsAndRegions` | Unknown |
| GET | `/products/vehicle/{engineType}/models` | Unknown | handler `productHandler.getAllVehicleModels` | Unknown |
| GET | `/regions/cities` | Unknown | handler `regionHandler.getAllCities` | Unknown |
| GET | `/regions/{country}/states` | Unknown | handler `regionHandler.getAllStates` | Unknown |
| POST | `/on-road-prices` | Unknown | handler `onRoadPriceHandler.generateOnRoadPrice` | Unknown |
| POST | `/price/upload` | Unknown | handler `priceUploadHandler.uploadPriceFile` | Unknown |
| POST | `/product-price-components` | Unknown | handler `productPriceComponentsHandler.createProductPriceComponent` | Unknown |
| PUT | `/on-road-prices/publish/{modelId}` | Unknown | handler `onRoadPriceHandler.publishORP` | Unknown |
| PUT | `/on-road-prices/{modelId}` | Unknown | handler `onRoadPriceHandler.editOnRoadPrice` | Unknown |
| PUT | `/product-price-components/publish/{componentId}` | Unknown | handler `productPriceComponentsHandler.publishProductPriceComponent` | Unknown |

## Endpoints
price-engine-micro-service-backend endpoint details (from inventory `inbound_http`).

### DELETE /cache/clear
Handler: `cacheHandler.clearAllCache` in `src/routes/api/cache-routes.ts:9`. Purpose: Unknown. Callers: Unknown.

### GET /on-road-prices/models/{engineType}
Handler: `onRoadPriceHandler.getVehicleModelsBasedOnEngineType` in `src/routes/api/on-road-price-routes.ts:26`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /on-road-prices/products/{modelId}
Handler: `onRoadPriceHandler.getORPComponents` in `src/routes/api/on-road-price-routes.ts:19`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### GET /on-road-prices/vehicles/engineType/{engineType}
Handler: `onRoadPriceHandler.getOnRoadPrices` in `src/routes/api/on-road-price-routes.ts:31`. Purpose: Unknown. Callers: catalog-scheduler.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /on-road-prices/{modelId}
Handler: `onRoadPriceHandler.getOnRoadPriceBasedOnModelId` in `src/routes/api/on-road-price-routes.ts:16`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### GET /price-components/{engineType}
Handler: `priceComponentHandler.getComponentNames` in `src/routes/api/price-component-routes.ts:9`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /product-price-components/custom/engineType/{engineType}
Handler: `productPriceComponentsHandler.getComponentsForCustomCreation` in `src/routes/api/product-price-components-routes.ts:11`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /product-price-components/{engineType}/{componentId}
Handler: `productPriceComponentsHandler.getComponentAssociatedModelsAndRegions` in `src/routes/api/product-price-components-routes.ts:14`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |
| componentId | path | string | True | |

### GET /products/vehicle/{engineType}/models
Handler: `productHandler.getAllVehicleModels` in `src/routes/api/product-routes.ts:9`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /regions/cities
Handler: `regionHandler.getAllCities` in `src/routes/api/region-routes.ts:12`. Purpose: Unknown. Callers: Unknown.

### GET /regions/{country}/states
Handler: `regionHandler.getAllStates` in `src/routes/api/region-routes.ts:9`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| country | path | string | True | |

### POST /on-road-prices
Handler: `onRoadPriceHandler.generateOnRoadPrice` in `src/routes/api/on-road-price-routes.ts:9`. Purpose: Unknown. Callers: Unknown.

### POST /price/upload
Handler: `priceUploadHandler.uploadPriceFile` in `src/routes/api/price-upload-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

### POST /product-price-components
Handler: `productPriceComponentsHandler.createProductPriceComponent` in `src/routes/api/product-price-components-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

### PUT /on-road-prices/publish/{modelId}
Handler: `onRoadPriceHandler.publishORP` in `src/routes/api/on-road-price-routes.ts:22`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### PUT /on-road-prices/{modelId}
Handler: `onRoadPriceHandler.editOnRoadPrice` in `src/routes/api/on-road-price-routes.ts:13`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### PUT /product-price-components/publish/{componentId}
Handler: `productPriceComponentsHandler.publishProductPriceComponent` in `src/routes/api/product-price-components-routes.ts:17`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| componentId | path | string | True | |

## Outbound Calls
price-engine-micro-service-backend outbound HTTP calls (4 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:site24x7` | - | - | - | - | Unknown | Unknown |
| Unknown (literal) | GET | `/mdp/v1/token/generate` | - | - | Unknown | Unknown |
| `master-data-platform` | POST | `/mdp/v1/price/test/service-bus/push-price-data` | - | - | Unknown | hard |
| `master-data-platform` | POST | `/mdp/v1/product/test/service-bus/push-product-data` | - | - | Unknown | hard |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/mdp/v1/token/generate` | axios | literal | `sonar-exclusion-function/service-bus/service-bus.ts:40` |
| POST | `/mdp/v1/price/test/service-bus/push-price-data` | axios | literal | `sonar-exclusion-function/service-bus/service-bus.ts:23` |
| POST | `/mdp/v1/product/test/service-bus/push-product-data` | axios | literal | `sonar-exclusion-function/service-bus/service-bus.ts:9` |

## Schemas
price-engine-micro-service-backend DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
price-engine-micro-service-backend publishes 1 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| Unknown (name from `env:TOPIC_NAME_MARKETPLACE`) | topic | azure-service-bus | - | Unknown | `src/services/price-engine-price-publisher.ts:17` | none resolved |

## Events Consumed
price-engine-micro-service-backend consumes 4 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| Unknown (name from `env:TOPIC_NAME_PRICE`) | env:SUBSCRIPTION_PRICE | - | - | Unknown | `src/utils/service-bus-implementors/service-bus-connection-implementer.ts:21` | none resolved | Unknown | Unknown |
| Unknown (name from `env:TOPIC_NAME_PRODUCT`) | env:SUBSCRIPTION_PRODUCT | - | - | Unknown | `src/utils/service-bus-implementors/service-bus-connection-implementer.ts:21` | none resolved | Unknown | Unknown |
| uat.mdp.price.vehicle | ccp | - | - | Unknown | `sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18` | master-data-platform | Unknown | Unknown |
| uat.mdp.product.vehicle | ccp | - | - | Unknown | `sonar-exclusion-function/service-bus/implemeters/product-service-bus-implementer.ts:28` | master-data-platform | Unknown | Unknown |

## External Integrations
price-engine-micro-service-backend third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:site24x7` | category analytics; matched `apminsight` at `package.json:48` | Unknown |

## Rate Limits and SLAs
price-engine-micro-service-backend: N/A — not determinable from code.

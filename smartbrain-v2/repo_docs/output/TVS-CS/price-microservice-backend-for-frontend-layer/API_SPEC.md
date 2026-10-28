---
service_id: price-microservice-backend-for-frontend-layer
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# price-microservice-backend-for-frontend-layer — API Specification

## Authentication
price-microservice-backend-for-frontend-layer endpoint auth as extracted: `None` × 14.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
price-microservice-backend-for-frontend-layer exposes 14 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/on-road-prices/models/{engineType}` | Unknown | handler `onRoadPriceHandler.getVehicleModelsBasedOnEngineType` | Unknown |
| GET | `/on-road-prices/products/{modelId}` | Unknown | handler `onRoadPriceHandler.getORPComponents` | Unknown |
| GET | `/on-road-prices/{modelId}` | Unknown | handler `onRoadPriceHandler.getOnRoadPriceBasedOnModelId` | Unknown |
| GET | `/price-components/{engineType}` | Unknown | handler `priceComponentHandler.getComponentNames` | Unknown |
| GET | `/product-price-components/custom/engineType/{engineType}` | Unknown | handler `productPriceComponentsHandler.getComponentsForCustomCreation` | Unknown |
| GET | `/product-price-components/{engineType}/{componentId}` | Unknown | handler `productPriceComponentsHandler.getComponentAssociatedModelsAndRegions` | Unknown |
| GET | `/products/vehicle/{engineType}/models` | Unknown | handler `productHandler.getAllVehicleModels` | Unknown |
| GET | `/regions/cities` | Unknown | handler `regionHandler.getAllCities` | Unknown |
| GET | `/regions/{country}/states` | Unknown | handler `regionHandler.getAllStates` | Unknown |
| POST | `/on-road-prices` | Unknown | handler `onRoadPriceHandler.generateOnRoadPrice` | Unknown |
| POST | `/product-price-components` | Unknown | handler `productPriceComponentsHandler.createProductPriceComponent` | Unknown |
| PUT | `/on-road-prices/publish/{modelId}` | Unknown | handler `onRoadPriceHandler.publishORP` | Unknown |
| PUT | `/on-road-prices/{modelId}` | Unknown | handler `onRoadPriceHandler.editOnRoadPrice` | Unknown |
| PUT | `/product-price-components/publish/{componentId}` | Unknown | handler `productPriceComponentsHandler.publishProductPriceComponent` | Unknown |

## Endpoints
price-microservice-backend-for-frontend-layer endpoint details (from inventory `inbound_http`).

### GET /on-road-prices/models/{engineType}
Handler: `onRoadPriceHandler.getVehicleModelsBasedOnEngineType` in `src/routes/api/on-road-price-routes.ts:27`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /on-road-prices/products/{modelId}
Handler: `onRoadPriceHandler.getORPComponents` in `src/routes/api/on-road-price-routes.ts:19`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### GET /on-road-prices/{modelId}
Handler: `onRoadPriceHandler.getOnRoadPriceBasedOnModelId` in `src/routes/api/on-road-price-routes.ts:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### GET /price-components/{engineType}
Handler: `priceComponentHandler.getComponentNames` in `src/routes/api/price-component-route.ts:8`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /product-price-components/custom/engineType/{engineType}
Handler: `productPriceComponentsHandler.getComponentsForCustomCreation` in `src/routes/api/product-price-components-route.ts:11`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /product-price-components/{engineType}/{componentId}
Handler: `productPriceComponentsHandler.getComponentAssociatedModelsAndRegions` in `src/routes/api/product-price-components-route.ts:14`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |
| componentId | path | string | True | |

### GET /products/vehicle/{engineType}/models
Handler: `productHandler.getAllVehicleModels` in `src/routes/api/product-route.ts:8`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| engineType | path | string | True | |

### GET /regions/cities
Handler: `regionHandler.getAllCities` in `src/routes/api/region-routes.ts:11`. Purpose: Unknown. Callers: Unknown.

### GET /regions/{country}/states
Handler: `regionHandler.getAllStates` in `src/routes/api/region-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| country | path | string | True | |

### POST /on-road-prices
Handler: `onRoadPriceHandler.generateOnRoadPrice` in `src/routes/api/on-road-price-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

### POST /product-price-components
Handler: `productPriceComponentsHandler.createProductPriceComponent` in `src/routes/api/product-price-components-route.ts:8`. Purpose: Unknown. Callers: Unknown.

### PUT /on-road-prices/publish/{modelId}
Handler: `onRoadPriceHandler.publishORP` in `src/routes/api/on-road-price-routes.ts:23`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### PUT /on-road-prices/{modelId}
Handler: `onRoadPriceHandler.editOnRoadPrice` in `src/routes/api/on-road-price-routes.ts:11`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| modelId | path | string | True | |

### PUT /product-price-components/publish/{componentId}
Handler: `productPriceComponentsHandler.publishProductPriceComponent` in `src/routes/api/product-price-components-route.ts:17`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| componentId | path | string | True | |

## Outbound Calls
price-microservice-backend-for-frontend-layer outbound HTTP calls (15 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:site24x7` | - | - | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/on-road-prices/models/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/on-road-prices/products/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/on-road-prices/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/price-components/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/product-price-components/custom/engineType/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/product-price-components/{}/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/products/vehicle/{}/models` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/regions/cities` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | GET | `/regions/{}/states` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | POST | `/on-road-prices` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | POST | `/product-price-components` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | PUT | `/on-road-prices/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | PUT | `/on-road-prices/{}` | - | - | Unknown | Unknown |
| Unknown (env:PRICE_MICROSERVICE_BASE_URL) | PUT | `/product-price-components/publish/{}` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/on-road-prices/models/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/on-road-price-implemeter.ts:43` |
| GET | `/on-road-prices/products/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/on-road-price-implemeter.ts:29` |
| GET | `/on-road-prices/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/on-road-price-implemeter.ts:22` |
| GET | `/price-components/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/price-implementer.ts:9` |
| GET | `/product-price-components/custom/engineType/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/product-price-components-implementer.ts:17` |
| GET | `/product-price-components/{}/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/product-price-components-implementer.ts:28` |
| GET | `/products/vehicle/{}/models` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/product-implementer.ts:10` |
| GET | `/regions/cities` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/region-implementer.ts:18` |
| GET | `/regions/{}/states` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/region-implementer.ts:10` |
| POST | `/on-road-prices` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/on-road-price-implemeter.ts:9` |
| POST | `/product-price-components` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/product-price-components-implementer.ts:10` |
| PUT | `/on-road-prices/publish/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/on-road-price-implemeter.ts:36` |
| PUT | `/on-road-prices/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/on-road-price-implemeter.ts:15` |
| PUT | `/product-price-components/publish/{}` | axios | env:PRICE_MICROSERVICE_BASE_URL | `src/rest/implementers/product-price-components-implementer.ts:35` |

## Schemas
price-microservice-backend-for-frontend-layer DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
price-microservice-backend-for-frontend-layer publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
price-microservice-backend-for-frontend-layer consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
price-microservice-backend-for-frontend-layer third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:site24x7` | category analytics; matched `apminsight` at `package.json:46` | Unknown |

## Rate Limits and SLAs
price-microservice-backend-for-frontend-layer: N/A — not determinable from code.

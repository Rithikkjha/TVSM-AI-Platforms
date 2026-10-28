---
service_id: core-commerce-platform-api-service
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# core-commerce-platform-api-service — API Specification

## Authentication
core-commerce-platform-api-service endpoint auth as extracted: `None` × 13.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
core-commerce-platform-api-service exposes 13 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| DELETE | `/cache/clear` | Unknown | handler `cacheHandler.clearAllCache` | Unknown |
| DELETE | `/catalogs/{id}` | Unknown | handler `catalogHandler.deleteCatalog` | Unknown |
| GET | `/catalog-configs/{nameSpace}` | Unknown | handler `catalogConfigurationHandler.getCatalogConfiguration` | catalog-microservice-backend-for-frontend-layer |
| GET | `/catalogs` | Unknown | handler `catalogHandler.getDefaultCatalog` | Unknown |
| GET | `/catalogs/{id}` | Unknown | handler `catalogHandler.getCatalogById` | Unknown |
| GET | `/catalogs/{catalogId}/catalog-item` | Unknown | handler `catalogHandler.getCatalogItemOfACatalog` | Unknown |
| GET | `/health` | Unknown | handler `applicationHealthHandler.checkApplicationHealth` | Unknown |
| GET | `/shopify/products` | Unknown | handler `shopifyHandler.getProducts` | catalog-scheduler |
| POST | `/catalogs` | Unknown | handler `catalogHandler.createCatalog` | Unknown |
| POST | `/vehicle-accessories-pricing/prices` | Unknown | handler `vehicleAccessoriesPricingHandler.bulkInsertPricing` | Unknown |
| PUT | `/catalog-configs/{nameSpace}` | Unknown | handler `catalogConfigurationHandler.updateCatalogConfiguration` | catalog-scheduler |
| PUT | `/catalogs/refresh/default-catalogs/{nameSpace}` | Unknown | handler `catalogHandler.updateLatestDefaultCatalog` | catalog-scheduler |
| PUT | `/catalogs/{id}` | Unknown | handler `catalogHandler.updateCatalogById` | Unknown |

## Endpoints
core-commerce-platform-api-service endpoint details (from inventory `inbound_http`).

### DELETE /cache/clear
Handler: `cacheHandler.clearAllCache` in `src/routes/api/cache-routes.ts:9`. Purpose: Unknown. Callers: Unknown.

### DELETE /catalogs/{id}
Handler: `catalogHandler.deleteCatalog` in `src/routes/api/catalog-routes.ts:19`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### GET /catalog-configs/{nameSpace}
Handler: `catalogConfigurationHandler.getCatalogConfiguration` in `src/routes/api/catalog-configuration-routes.ts:8`. Purpose: Unknown. Callers: catalog-microservice-backend-for-frontend-layer.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| nameSpace | path | string | True | |

### GET /catalogs
Handler: `catalogHandler.getDefaultCatalog` in `src/routes/api/catalog-routes.ts:24`. Purpose: Unknown. Callers: Unknown.

### GET /catalogs/{id}
Handler: `catalogHandler.getCatalogById` in `src/routes/api/catalog-routes.ts:12`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### GET /catalogs/{catalogId}/catalog-item
Handler: `catalogHandler.getCatalogItemOfACatalog` in `src/routes/api/catalog-routes.ts:27`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| catalogId | path | string | True | |

### GET /health
Handler: `applicationHealthHandler.checkApplicationHealth` in `src/routes/api/application-heath-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

### GET /shopify/products
Handler: `shopifyHandler.getProducts` in `src/routes/api/shopify-routes.ts:8`. Purpose: Unknown. Callers: catalog-scheduler.

### POST /catalogs
Handler: `catalogHandler.createCatalog` in `src/routes/api/catalog-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

### POST /vehicle-accessories-pricing/prices
Handler: `vehicleAccessoriesPricingHandler.bulkInsertPricing` in `src/routes/api/vehicle-accessories-pricing-routes.ts:8`. Purpose: Unknown. Callers: Unknown.

### PUT /catalog-configs/{nameSpace}
Handler: `catalogConfigurationHandler.updateCatalogConfiguration` in `src/routes/api/catalog-configuration-routes.ts:12`. Purpose: Unknown. Callers: catalog-scheduler.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| nameSpace | path | string | True | |

### PUT /catalogs/refresh/default-catalogs/{nameSpace}
Handler: `catalogHandler.updateLatestDefaultCatalog` in `src/routes/api/catalog-routes.ts:30`. Purpose: Unknown. Callers: catalog-scheduler.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| nameSpace | path | string | True | |

### PUT /catalogs/{id}
Handler: `catalogHandler.updateCatalogById` in `src/routes/api/catalog-routes.ts:16`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

## Outbound Calls
core-commerce-platform-api-service outbound HTTP calls (8 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:site24x7` | - | - | - | - | Unknown | Unknown |
| Unknown (unknown) | GET | `/admin/api/2023-07/products/{}.json` | - | - | Unknown | Unknown |
| Unknown (unknown) | GET | `/admin/api/2023-07/variants/{}/metafields.json` | - | - | Unknown | Unknown |
| Unknown (env:BUMBLEBEE_EV_API_URL) | GET | `/` | - | - | Unknown | Unknown |
| Unknown (env:BUMBLEBEE_ICE_API_URL) | GET | `/` | - | - | Unknown | Unknown |
| Unknown (env:SHOPIFY_API_URL) | GET | `/2023-07/products.json` | - | - | Unknown | Unknown |
| Unknown (literal) | GET | `/sandbox-data/website-db-orp-data/tvsorp_ev_output.json` | - | - | Unknown | Unknown |
| Unknown (literal) | GET | `/sandbox-data/website-db-orp-data/tvsorp_ice_output.json` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/admin/api/2023-07/products/{}.json` | axios | unknown | `src/services/shopify-service.ts:21` |
| GET | `/admin/api/2023-07/variants/{}/metafields.json` | axios | unknown | `src/services/shopify-service.ts:53` |
| GET | `/` | axios | env:BUMBLEBEE_EV_API_URL | `src/utils/implementers/ev-implementer/ev-implementer.ts:10` |
| GET | `/` | axios | env:BUMBLEBEE_ICE_API_URL | `src/utils/implementers/ice-implementer/ice-implementer.ts:11` |
| GET | `/2023-07/products.json` | axios | env:SHOPIFY_API_URL | `src/utils/implementers/shopify-implementer/shopify-implementer.ts:13` |
| GET | `/sandbox-data/website-db-orp-data/tvsorp_ev_output.json` | axios | literal | `sonar-exclusion-function/scripts/ice-ev-model-data-grouping.ts:35` |
| GET | `/sandbox-data/website-db-orp-data/tvsorp_ice_output.json` | axios | literal | `sonar-exclusion-function/scripts/ice-ev-model-data-grouping.ts:9` |

## Schemas
core-commerce-platform-api-service DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
core-commerce-platform-api-service publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
core-commerce-platform-api-service consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
core-commerce-platform-api-service third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:site24x7` | category analytics; matched `apminsight` at `package.json:45` | Unknown |

## Rate Limits and SLAs
core-commerce-platform-api-service: N/A — not determinable from code.

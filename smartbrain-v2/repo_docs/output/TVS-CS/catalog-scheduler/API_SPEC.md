---
service_id: catalog-scheduler
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# catalog-scheduler — API Specification

## Authentication
catalog-scheduler endpoint auth as extracted: no endpoints.
Auth libraries: `@azure/identity`.

## Endpoint Index
catalog-scheduler exposes 0 HTTP endpoint(s) and 2 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

Scheduled jobs:

| Job | Trigger | Expression | Handler |
|---|---|---|---|
| `merchandise-accessories-ingestion-job` | timer-trigger | `Unknown` (env:CRON_EXPRESSION_FOR_MERCHANDISE_ACCESSORIES_INGESTION_JOB) | `src/functions/merchandise-accessories-ingestion-job.js:5` |
| `product-price-ingestion-job` | timer-trigger | `Unknown` (env:CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB) | `src/functions/product-price-ingestion-job.js:6` |

## Endpoints
catalog-scheduler endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
catalog-scheduler outbound HTTP calls (8 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| Unknown (env:CATALOG_BASE_URL) | DELETE | `/cache/clear` | - | - | Unknown | Unknown |
| `core-commerce-platform-api-service` | GET | `/shopify/products` | - | - | Unknown | hard |
| Unknown (env:MERCHANDISE_ACCESSORIES_BASE_URL) | GET | `/admin/api/2025-01/products.json` | - | - | Unknown | Unknown |
| `price-engine-micro-service-backend` | GET | `/on-road-prices/vehicles/engineType/{}` | - | - | Unknown | hard |
| Unknown (literal) | GET | `/sandbox-data/website-db-orp-data/tvsorp_discount_output.json` | - | - | Unknown | Unknown |
| Unknown (env:AUTHORIZATION_TOKEN_URL) | POST | `/{}/oauth2/v2.0/token` | - | - | Unknown | Unknown |
| `core-commerce-platform-api-service` | PUT | `/catalog-configs/{}` | - | - | Unknown | hard |
| `core-commerce-platform-api-service` | PUT | `/catalogs/refresh/default-catalogs/{}` | - | - | Unknown | hard |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| DELETE | `/cache/clear` | axios | env:CATALOG_BASE_URL | `src/product-price-ingestion-job/catalog-service/catalog-service.js:154` |
| GET | `/shopify/products` | axios | env:CATALOG_BASE_URL | `src/product-price-ingestion-job/data-sources/product-data-source/product-data-source-api.js:192` |
| GET | `/admin/api/2025-01/products.json` | axios | env:MERCHANDISE_ACCESSORIES_BASE_URL | `src/merchandise-accessories-ingestion-job/merchandise-accessories-service/merchandise-accessories-implementer.js:32` |
| GET | `/on-road-prices/vehicles/engineType/{}` | axios | env:PRICE_URL | `src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21` |
| GET | `/sandbox-data/website-db-orp-data/tvsorp_discount_output.json` | axios | literal | `src/product-price-ingestion-job/data-sources/discount-data-source/discount-data-source-api.js:16` |
| POST | `/{}/oauth2/v2.0/token` | axios | env:AUTHORIZATION_TOKEN_URL | `src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:39` |
| PUT | `/catalog-configs/{}` | axios | env:CATALOG_BASE_URL | `src/product-price-ingestion-job/catalog-service/catalog-config-service.js:73` |
| PUT | `/catalogs/refresh/default-catalogs/{}` | axios | env:CATALOG_BASE_URL | `src/product-price-ingestion-job/catalog-service/catalog-service.js:20` |

## Schemas
catalog-scheduler DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
catalog-scheduler publishes 1 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| Unknown (name from `env:SERVICE_BUS_TOPIC_NAME`) | topic | azure-service-bus | - | Unknown | `src/product-price-ingestion-job/price-updates/price-updates.js:399` | none resolved |

## Events Consumed
catalog-scheduler consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
catalog-scheduler third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
catalog-scheduler: N/A — not determinable from code.

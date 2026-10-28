---
service_id: price-engine-frontend
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# price-engine-frontend — API Specification

## Authentication
price-engine-frontend endpoint auth as extracted: no endpoints.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
price-engine-frontend exposes 0 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

## Endpoints
price-engine-frontend endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
price-engine-frontend outbound HTTP calls (17 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/on-road-prices/models/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/on-road-prices/products/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/on-road-prices/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/price-components/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/price-components/{}/models/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/price-components/{}/products` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/product-price-components/custom/engineType/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/product-price-components/{}/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/products/vehicle/{}/models` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/regions/cities` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | GET | `/regions/{}/states` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | POST | `/on-road-prices` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | POST | `/product-price-components` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | PUT | `/on-road-prices/publish/{}{}{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | PUT | `/on-road-prices/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | PUT | `/product-price-components/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL) | PUT | `/product-price-components/{}` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/on-road-prices/models/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:68` |
| GET | `/on-road-prices/products/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:25` |
| GET | `/on-road-prices/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:41` |
| GET | `/price-components/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:52` |
| GET | `/price-components/{}/models/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:8` |
| GET | `/price-components/{}/products` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:59` |
| GET | `/product-price-components/custom/engineType/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:76` |
| GET | `/product-price-components/{}/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:30` |
| GET | `/products/vehicle/{}/models` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/vehicle-models.ts:31` |
| GET | `/regions/cities` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/location.ts:51` |
| GET | `/regions/{}/states` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/location.ts:42` |
| POST | `/on-road-prices` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:31` |
| POST | `/product-price-components` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:18` |
| PUT | `/on-road-prices/publish/{}{}{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:48` |
| PUT | `/on-road-prices/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/product-price.ts:74` |
| PUT | `/product-price-components/publish/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:46` |
| PUT | `/product-price-components/{}` | axios | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL | `src/store/actions/price-component.ts:24` |

## Schemas
price-engine-frontend DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
price-engine-frontend publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
price-engine-frontend consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
price-engine-frontend third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
price-engine-frontend: N/A — not determinable from code.

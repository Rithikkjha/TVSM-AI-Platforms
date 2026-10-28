---
service_id: catalog-microservice-backend-for-frontend-layer
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# catalog-microservice-backend-for-frontend-layer — API Specification

## Authentication
catalog-microservice-backend-for-frontend-layer endpoint auth as extracted: `None` × 2.
Auth libraries: `@azure/identity`.

## Endpoint Index
catalog-microservice-backend-for-frontend-layer exposes 2 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/catalogs` | Unknown | handler `catalogHandler.getDefaultCatalog` | Unknown |
| GET | `/health` | Unknown | handler `applicationHealthHandler.checkApplicationHealth` | Unknown |

## Endpoints
catalog-microservice-backend-for-frontend-layer endpoint details (from inventory `inbound_http`).

### GET /catalogs
Handler: `catalogHandler.getDefaultCatalog` in `src/routes/api/catalog-route.ts:7`. Purpose: Unknown. Callers: Unknown.

### GET /health
Handler: `applicationHealthHandler.checkApplicationHealth` in `src/routes/api/application-health-route.ts:8`. Purpose: Unknown. Callers: Unknown.

## Outbound Calls
catalog-microservice-backend-for-frontend-layer outbound HTTP calls (4 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:site24x7` | - | - | - | - | Unknown | Unknown |
| `core-commerce-platform-api-service` | GET | `/catalog-configs/{}` | - | - | Unknown | hard |
| Unknown (env:CATALOG_MICRO_SERVICES_BASE_URL) | GET | `/catalogs` | - | - | Unknown | Unknown |
| Unknown (env:AZURE_OAUTH_TOKEN_BASE_URL) | POST | `/{}/oauth2/v2.0/token` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/catalog-configs/{}` | axios | env:CATALOG_MICRO_SERVICES_BASE_URL | `src/rest/implementers/catalog-implementer.ts:31` |
| GET | `/catalogs` | axios | env:CATALOG_MICRO_SERVICES_BASE_URL | `src/rest/implementers/catalog-implementer.ts:15` |
| POST | `/{}/oauth2/v2.0/token` | axios | env:AZURE_OAUTH_TOKEN_BASE_URL | `src/rest/implementers/azure-service-implementers.ts:22` |

## Schemas
catalog-microservice-backend-for-frontend-layer DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
catalog-microservice-backend-for-frontend-layer publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
catalog-microservice-backend-for-frontend-layer consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
catalog-microservice-backend-for-frontend-layer third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:site24x7` | category analytics; matched `apminsight` at `package.json:49` | Unknown |

## Rate Limits and SLAs
catalog-microservice-backend-for-frontend-layer: N/A — not determinable from code.

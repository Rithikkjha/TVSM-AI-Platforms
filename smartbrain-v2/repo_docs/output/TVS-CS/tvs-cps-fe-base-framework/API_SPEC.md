---
service_id: tvs-cps-fe-base-framework
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# TVS-CPS-FE-BASE-FRAMEWORK — API Specification

## Authentication
tvs-cps-fe-base-framework: Next middleware reads the `token` cookie; unauthenticated requests (except `/login`) redirect to login, authenticated users on `/` or `/login` redirect to `/dashboard` (`channel-partner-system/src/middleware.ts:5-31`). `/api/set-token` and `/api/clear-token` have no auth of their own (`src/app/api/set-token/route.ts:3`). Token issuer Unknown.

## Endpoint Index
tvs-cps-fe-base-framework exposes 2 HTTP endpoints.

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| POST | `/api/clear-token` | Unknown | `channel-partner-system/src/app/api/clear-token/route.ts#POST` (channel-partner-system/src/app/api/clear-token/route.ts:3) | `tvs-cps-fe-base-framework` |
| POST | `/api/set-token` | Unknown | `channel-partner-system/src/app/api/set-token/route.ts#POST` (channel-partner-system/src/app/api/set-token/route.ts:3) | `tvs-cps-fe-base-framework` |

## Endpoints
tvs-cps-fe-base-framework endpoint details (params/schemas from service.yaml; `Unknown` = not extracted).
### POST /api/clear-token

Handler: `channel-partner-system/src/app/api/clear-token/route.ts#POST` (channel-partner-system/src/app/api/clear-token/route.ts:3)

Callers: `tvs-cps-fe-base-framework`

### POST /api/set-token

Handler: `channel-partner-system/src/app/api/set-token/route.ts#POST` (channel-partner-system/src/app/api/set-token/route.ts:3)

Callers: `tvs-cps-fe-base-framework`

## Outbound Calls
tvs-cps-fe-base-framework outbound HTTP calls (service.yaml `outbound`):

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| Unknown | GET | `/tenants/{}/logo.svg` | Unknown | Unknown | Unknown (base URL: env:RUNTIME_ASSETS_BASE_URL) | Unknown |
| Unknown | GET | `/tenants/{}/variable.css` | Unknown | Unknown | Unknown (base URL: env:RUNTIME_ASSETS_BASE_URL) | Unknown |
| Unknown | GET | `/tenants/{}/{}` | Unknown | Unknown | Unknown (base URL: env:RUNTIME_ASSETS_BASE_URL) | Unknown |
| Unknown | GET | `/public/tenants/{}/config.json` | Unknown | RuntimeTenantConfig | Unknown (base URL: env:RUNTIME_CONFIG_BASE_URL) | Unknown |
| Unknown | GET | `/tenants/{}/features.json` | Unknown | RuntimeTenantFeatures | Unknown (base URL: env:RUNTIME_CONFIG_BASE_URL) | Unknown |
| tvs-cps-fe-base-framework | POST | `/api/clear-token` | Unknown | Unknown | Unknown (base URL: env:NEXT_PUBLIC_API_BASE_URL) | hard |
| tvs-cps-fe-base-framework | POST | `/api/set-token` | Unknown | Unknown | Unknown (base URL: env:NEXT_PUBLIC_API_BASE_URL) | hard |

tvs-cps-fe-base-framework calls: tenant assets (`/tenants/{}/logo.svg`, `/tenants/{}/variable.css`, `/tenants/{}/{}`) from `RUNTIME_ASSETS_BASE_URL` at build time (`channel-partner-system/scripts/build-tools.ts:23-34`); tenant `config.json`/`features.json` from `RUNTIME_CONFIG_BASE_URL` (`src/server/runtime-config.ts:40`, `:55`); its own `/api/set-token` and `/api/clear-token` via axios (`shared/src/services/auth.service.ts:24-28`). Target hosts Unknown.

## Schemas
tvs-cps-fe-base-framework schemas referenced by endpoints/events (0 of 2 extracted).
Other extracted schemas (see service.yaml `schemas`): `RuntimeTenantConfig`, `RuntimeTenantFeatures`

## Events Published
tvs-cps-fe-base-framework publishes:

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| none | | | | | | |

## Events Consumed
tvs-cps-fe-base-framework consumes:

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| none | | | | | | | | |

## External Integrations
tvs-cps-fe-base-framework external integrations:

| System | Purpose | Auth |
|---|---|---|
| none resolved | | |

## Rate Limits and SLAs
tvs-cps-fe-base-framework: N/A — not determinable from code.

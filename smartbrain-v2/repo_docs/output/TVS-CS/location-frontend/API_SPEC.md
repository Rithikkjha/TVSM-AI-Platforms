---
service_id: location-frontend
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# location-frontend — API Specification

## Authentication
location-frontend endpoint auth as extracted: no endpoints.
Auth libraries: `@types/jwt-decode`.

## Endpoint Index
location-frontend exposes 0 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

## Endpoints
location-frontend endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
location-frontend outbound HTTP calls (32 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:google-maps` | - | - | - | - | Unknown | Unknown |
| `tvsmbe-location` | GET | `/dealer/{}/location-type/{}` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/rejection-comments` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/summary` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/{}/contacts/SERVICE` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/api/v1/dealer/summary` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/api/v1/dealer/template` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/api/v1/user-x/{}/countries` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/dealer/{}` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/dealer/{}/location-type/{}` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/api/v1/dealer-flow/dealerInfo` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/api/v1/geo/geocode` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/api/v1/user-x/{}/countries` | - | - | Unknown | hard |
| `tvsmbe-location` | GET | `/country/{}/filter-config` | - | any | Unknown | hard |
| `tvsmbe-location` | GET | `/country/{}/provinces` | - | any | Unknown | hard |
| `tvsmbe-location` | GET | `/geo/geocode` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/list` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/send-location-update-sms` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/verification` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/api/v1/admin/migrate/import-dealership-locations` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/api/v1/dealer` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/api/v1/dealer/export` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/api/v1/dealer/list` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/v1/dealer-location/submit` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/charging-station/nearby` | - | ChargingStationSearchResponse | Unknown | hard |
| `tvsmbe-location` | POST | `/dealer-search` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/domestic-dealer/brands` | - | BrandsApiResponse | Unknown | hard |
| `tvsmbe-location` | POST | `/domestic-dealer/clusters` | - | - | Unknown | hard |
| `tvsmbe-location` | POST | `/domestic-dealer/get-sms` | - | any | Unknown | hard |
| `tvsmbe-location` | POST | `/domestic-dealer/send-otp` | - | any | Unknown | hard |
| `tvsmbe-location` | POST | `/finder/dealers` | - | any | Unknown | hard |
| `tvsmbe-location` | PUT | `/api/v1/dealer/{}` | - | - | Unknown | hard |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/dealer/{}/location-type/{}` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:38` |
| GET | `/rejection-comments` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:69` |
| GET | `/summary` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:60` |
| GET | `/{}/contacts/SERVICE` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:115` |
| GET | `/api/v1/dealer/summary` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/DealerDetailsService.ts:135` |
| GET | `/api/v1/dealer/template` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/AdminDealerService.ts:21` |
| GET | `/api/v1/user-x/{}/countries` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/DealerDetailsService.ts:159` |
| GET | `/dealer/{}` | axios | env:REACT_APP_DEALERWEB_BASE_URL | `src/services/DealerFlowDealerDetailsService.ts:7` |
| GET | `/dealer/{}/location-type/{}` | axios | env:REACT_APP_DEALERWEB_BASE_URL | `src/services/DealerFlowDealerDetailsService.ts:19` |
| GET | `/api/v1/dealer-flow/dealerInfo` | axios | env:REACT_APP_DEALER_BASE_URL | `src/services/DealerDetailsService.ts:9` |
| GET | `/api/v1/geo/geocode` | axios | env:REACT_APP_DEALER_BASE_URL | `src/services/DealerDetailsService.ts:104` |
| GET | `/api/v1/user-x/{}/countries` | axios | env:REACT_APP_DEALER_BASE_URL | `src/services/DealerDetailsService.ts:125` |
| GET | `/country/{}/filter-config` | axios, fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:33` |
| GET | `/country/{}/provinces` | axios, fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:39` |
| GET | `/geo/geocode` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/geocodeService.ts:76` |
| POST | `/list` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:50` |
| POST | `/send-location-update-sms` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:91` |
| POST | `/verification` | axios | env:REACT_APP_ADMIN_BASE_URL | `src/services/DealerDetailsService.ts:81` |
| POST | `/api/v1/admin/migrate/import-dealership-locations` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/AdminDealerService.ts:8` |
| POST | `/api/v1/dealer` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/DealerService.ts:5` |
| POST | `/api/v1/dealer/export` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/DealerDetailsService.ts:169` |
| POST | `/api/v1/dealer/list` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/DealerDetailsService.ts:147` |
| POST | `/v1/dealer-location/submit` | axios | env:REACT_APP_DEALER_BASE_URL | `src/services/DealerDetailsService.ts:21` |
| POST | `/charging-station/nearby` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:316` |
| POST | `/dealer-search` | axios | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/services/DealerLocaterService.ts:7` |
| POST | `/domestic-dealer/brands` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:191` |
| POST | `/domestic-dealer/clusters` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/clusterService.ts:17` |
| POST | `/domestic-dealer/get-sms` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:249` |
| POST | `/domestic-dealer/send-otp` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:224` |
| POST | `/finder/dealers` | fetch | env:REACT_APP_DEALER_LOCATER_BASE_URL | `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:126` |
| PUT | `/api/v1/dealer/{}` | axios | env:REACT_APP_ADMIN_IB_BASE_URL | `src/services/DealerService.ts:15` |

## Schemas
location-frontend DTOs/payloads referenced in this file.

### ChargingStationSearchResponse
Defined in: `src/DealerLocatorV2/types.ts:97`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | ChargingStationRaw[] | True | - |
| errorMessage | string | True | - |

### BrandsApiResponse
Defined in: `src/DealerLocatorV2/services/dealerLocatorV2Service.ts:173`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | object | False | - |
| errorMessage | string | False | - |

## Events Published
location-frontend publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
location-frontend consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
location-frontend third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:google-maps` | category maps; matched `maps.googleapis.com` at `.env.dev:5` | Unknown |

## Rate Limits and SLAs
location-frontend: N/A — not determinable from code.

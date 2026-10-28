---
service_id: cbs-admin-portal
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# cbs-admin-portal — API Specification

## Authentication
cbs-admin-portal endpoint auth as extracted: no endpoints.
Auth-related code: `backend/src/main/java/com/tvs/leadsadmin/workflow/controller/WorkflowController.java:45` (@PreAuthorize).

## Endpoint Index
cbs-admin-portal exposes 0 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

## Endpoints
cbs-admin-portal endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
cbs-admin-portal outbound HTTP calls (76 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| Unknown (env:REACT_APP_API_URL) | DELETE | `/lms-drafts/draft/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/action-items/approvals` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/action-items/mine` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/audit` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/audit/entity/{}/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/audit/type/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/dealers` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/dealers/code/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/dealers/dependencies/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/dealers/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/dealers/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/form-config` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/form-config/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/form-config/metadata` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/form-config/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms-drafts/brand/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms-drafts/event-configurator/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms-drafts/lead-flow/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms-drafts/lead-source/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms-drafts/model/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/brand/all` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/brand/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/event-configurator/all` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/event-configurator/name/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/event-configurator/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/lead-flow/all` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/lead-flow/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/lead-source/all` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/lead-source/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/model/all` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/lms/model/{}` | - | - | Unknown | Unknown |
| `tvsmbe-mdp-bff` | GET | `/mdp/dealer/{}` | - | - | Unknown | hard |
| Unknown (env:REACT_APP_API_URL) | GET | `/mdp/part/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/mdp/price/vehicle/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/mdp/vehicle/part/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/mdp/vehicle/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/rbac/me` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sources` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sources/dependencies/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sources/drafts` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sources/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sync/out-of-sync` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sync/out-of-sync/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sync/status/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/sync/status/{}/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/workflows/assignments` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | GET | `/workflows/templates` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/action-items/reject/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/action-items/resubmit/{}` | - | - | Unknown | Unknown |
| `tvsmbe-qrcode` | POST | `/auth/login` | - | - | Unknown | hard |
| Unknown (env:REACT_APP_API_URL) | POST | `/booking/lookup` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/dealers/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/dealers/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/form-config/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/form-config/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/brand/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/brand/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/event-configurator/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/event-configurator/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/lead-flow/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/lead-flow/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/lead-source/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/lead-source/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/model/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms-drafts/model/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms/brand` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms/lead-flow` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/lms/lead-source` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/sources/draft` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/sources/publish/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | POST | `/workflows/assign` | - | - | Unknown | Unknown |
| `booking-crud-services` | POST | `/dms-vehicle-master` | - | - | Unknown | hard |
| Unknown (env:REACT_APP_API_URL) | PUT | `/booking/dealer-change` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | PUT | `/lms/brand/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | PUT | `/lms/lead-flow/{}` | - | - | Unknown | Unknown |
| Unknown (env:REACT_APP_API_URL) | PUT | `/lms/lead-source/{}` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| DELETE | `/lms-drafts/draft/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:199` |
| GET | `/action-items/approvals` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:92` |
| GET | `/action-items/mine` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:94` |
| GET | `/audit` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:83` |
| GET | `/audit/entity/{}/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:87` |
| GET | `/audit/type/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:85` |
| GET | `/dealers` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:45` |
| GET | `/dealers/code/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:47` |
| GET | `/dealers/dependencies/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:51` |
| GET | `/dealers/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:48` |
| GET | `/dealers/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:46` |
| GET | `/form-config` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:64` |
| GET | `/form-config/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:66` |
| GET | `/form-config/metadata` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:67` |
| GET | `/form-config/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:65` |
| GET | `/lms-drafts/brand/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:173` |
| GET | `/lms-drafts/event-configurator/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:214` |
| GET | `/lms-drafts/lead-flow/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:193` |
| GET | `/lms-drafts/lead-source/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:183` |
| GET | `/lms-drafts/model/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:205` |
| GET | `/lms/brand/all` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:169` |
| GET | `/lms/brand/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:170` |
| GET | `/lms/event-configurator/all` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:211` |
| GET | `/lms/event-configurator/name/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:213` |
| GET | `/lms/event-configurator/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:212` |
| GET | `/lms/lead-flow/all` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:189` |
| GET | `/lms/lead-flow/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:190` |
| GET | `/lms/lead-source/all` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:179` |
| GET | `/lms/lead-source/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:180` |
| GET | `/lms/model/all` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:203` |
| GET | `/lms/model/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:204` |
| GET | `/mdp/dealer/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:225` |
| GET | `/mdp/part/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:237` |
| GET | `/mdp/price/vehicle/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:234` |
| GET | `/mdp/vehicle/part/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:231` |
| GET | `/mdp/vehicle/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:228` |
| GET | `/rbac/me` | axios | env:REACT_APP_API_URL | `src/hooks/useAuth.js:35` |
| GET | `/sources` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:55` |
| GET | `/sources/dependencies/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:60` |
| GET | `/sources/drafts` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:57` |
| GET | `/sources/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:56` |
| GET | `/sync/out-of-sync` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:122` |
| GET | `/sync/out-of-sync/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:124` |
| GET | `/sync/status/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:118` |
| GET | `/sync/status/{}/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:120` |
| GET | `/workflows/assignments` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:249` |
| GET | `/workflows/templates` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:246` |
| POST | `/action-items/reject/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:96` |
| POST | `/action-items/resubmit/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:98` |
| POST | `/auth/login` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:32` |
| POST | `/booking/lookup` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:134` |
| POST | `/dealers/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:49` |
| POST | `/dealers/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:50` |
| POST | `/form-config/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:68` |
| POST | `/form-config/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:69` |
| POST | `/lms-drafts/brand/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:174` |
| POST | `/lms-drafts/brand/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:175` |
| POST | `/lms-drafts/event-configurator/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:215` |
| POST | `/lms-drafts/event-configurator/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:216` |
| POST | `/lms-drafts/lead-flow/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:194` |
| POST | `/lms-drafts/lead-flow/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:195` |
| POST | `/lms-drafts/lead-source/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:184` |
| POST | `/lms-drafts/lead-source/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:185` |
| POST | `/lms-drafts/model/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:206` |
| POST | `/lms-drafts/model/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:207` |
| POST | `/lms/brand` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:171` |
| POST | `/lms/lead-flow` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:191` |
| POST | `/lms/lead-source` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:181` |
| POST | `/sources/draft` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:58` |
| POST | `/sources/publish/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:59` |
| POST | `/workflows/assign` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:252` |
| POST | `/dms-vehicle-master` | axios | env:REACT_APP_BOOKING_API_URL | `src/services/dataService.js:76` |
| PUT | `/booking/dealer-change` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:148` |
| PUT | `/lms/brand/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:172` |
| PUT | `/lms/lead-flow/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:192` |
| PUT | `/lms/lead-source/{}` | axios | env:REACT_APP_API_URL | `src/services/dataService.js:182` |

## Schemas
cbs-admin-portal DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
cbs-admin-portal publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
cbs-admin-portal consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
cbs-admin-portal third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
cbs-admin-portal: N/A — not determinable from code.

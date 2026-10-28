---
service_id: lms-ems
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# lms-ems — API Specification

## Authentication
lms-ems exposes only `GET /` with no auth attribute. Outbound EMS calls send an API key from config key `API_KEY_VALUE` (name only, `emsService/Const/AppSettingsService.cs:25`).
API contract: openapi-3 generated at runtime by swashbuckle (`/swagger/v1/swagger.json`; `emsService/emsService.csproj:17`), no committed contract file.

## Endpoint Index
lms-ems exposes 1 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Handler | Auth | Callers (service_id) |
|---|---|---|---|---|
| GET | `/` | `EmsController.Ems` | none in code | - |

## Endpoints
lms-ems endpoint details (from inventory `inbound_http` + service.yaml `schemas`).

### GET /
Handler `EmsController.Ems`; auth: none in code.
Request body: none.
Responses: 200, 422.

## Outbound Calls
lms-ems outbound HTTP calls (0 in service.yaml).

| Target (service_id) | Method | Path | Criticality | Client |
|---|---|---|---|---|
| N/A | - | - | - | no registry-resolved outbound HTTP; config-driven HTTP clients listed in HLC.md |

## Schemas
lms-ems DTOs referenced by endpoints.
N/A — no schemas extracted (listener service; message payloads are deserialised from JSON in handlers).

## Events Published
lms-ems publishes 1 messaging entit(y/ies).

| Topic / Queue | Type | Broker | name_from | Message types | Payload | Published from | Consumers |
|---|---|---|---|---|---|---|---|
| `lms` | topic | azure-service-bus | `config:AppSettings:TOPIC_NAME` | see LLD State Machines | JSON string | `emsService/Services/DispatchService.cs:18`, `emsService/Services/DispatchService.cs:28`, `emsService/Services/DispatchService.cs:39`, `emsService/Services/DispatchService.cs:50` | `lms-crm`, `lms-ems`, `lms-process`, `lms-tvs-credit` |

## Events Consumed
lms-ems consumes 1 messaging entit(y/ies).

| Topic / Queue | Subscription | Broker | name_from | Handler | Producers | DLQ / retry |
|---|---|---|---|---|---|---|
| `lms` | `EMS` | azure-service-bus | `config:AppSettings:TOPIC_NAME` | `emsService/ListenerService/EmsListenerService.cs:62` | `lms-ems`, `lms-process` | none in code |

Phase-2 extraction for lms-ems left these entity names unresolved; topic names above come from `runs/TVS-CS/lms_ems/llm_notes.json` (inferred from appsettings, file:line evidence there):
- `messaging:emsService:publish:azure-service-bus:unknown` — evidence `emsService/Services/DispatchService.cs:18`, `emsService/Services/DispatchService.cs:28`, `emsService/Services/DispatchService.cs:39`, `emsService/Services/DispatchService.cs:50`
- `messaging:emsService:subscribe:azure-service-bus:unknown` — evidence `emsService/ListenerService/EmsListenerService.cs:43`

## External Integrations
lms-ems third-party systems detected in code.
N/A — no `external:` system matched by the registry.

## Rate Limits and SLAs
lms-ems: N/A — not determinable from code.

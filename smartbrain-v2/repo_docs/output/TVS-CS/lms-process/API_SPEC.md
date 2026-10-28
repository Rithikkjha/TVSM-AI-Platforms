---
service_id: lms-process
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# lms-process — API Specification

## Authentication
lms-process exposes only `GET /` with no auth attribute; it is a background listener. Service Bus access uses connection-string config keys (names only; `MdpServiceBusConnectionString`, `processLeadService/Const/Constants.cs:8`).
API contract: openapi-3 generated at runtime by swashbuckle (`/swagger/v1/swagger.json`; `processLeadService/processLeadService.csproj:13`), no committed contract file.

## Endpoint Index
lms-process exposes 1 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Handler | Auth | Callers (service_id) |
|---|---|---|---|---|
| GET | `/` | `leadProcessController.GetLead` | none in code | - |

## Endpoints
lms-process endpoint details (from inventory `inbound_http` + service.yaml `schemas`).

### GET /
Handler `leadProcessController.GetLead`; auth: none in code.
Request body: none.
Responses: 200, 422.

## Outbound Calls
lms-process outbound HTTP calls (0 in service.yaml).

| Target (service_id) | Method | Path | Criticality | Client |
|---|---|---|---|---|
| N/A | - | - | - | no registry-resolved outbound HTTP; config-driven HTTP clients listed in HLC.md |

## Schemas
lms-process DTOs referenced by endpoints.
N/A — no schemas extracted (listener service; message payloads are deserialised from JSON in handlers).

## Events Published
lms-process publishes 1 messaging entit(y/ies).

| Topic / Queue | Type | Broker | name_from | Message types | Payload | Published from | Consumers |
|---|---|---|---|---|---|---|---|
| `lms` | topic | azure-service-bus | `config:AppSettings:TOPIC_NAME` | see LLD State Machines | JSON string | `processLeadService/Services/DispatchService.cs:25`, `processLeadService/Services/DispatchService.cs:43` | `lms-crm`, `lms-ems`, `lms-process`, `lms-tvs-credit` |

## Events Consumed
lms-process consumes 2 messaging entit(y/ies).

| Topic / Queue | Subscription | Broker | name_from | Handler | Producers | DLQ / retry |
|---|---|---|---|---|---|---|
| Unknown (`config:AppSettings:MDP_TOPIC_NAME`) | `lms` | azure-service-bus | `config:AppSettings:MDP_TOPIC_NAME` | `processLeadService/ListenerService/MdpConsumer.cs:58` | `master-data-platform` | none in code |
| `lms` | `PROCESS` | azure-service-bus | `config:AppSettings:TOPIC_NAME` | `processLeadService/ListenerService/QueueConsumer.cs:52` | `lms-ems`, `lms-process` | none in code |

Phase-2 extraction for lms-process left these entity names unresolved; topic names above come from `runs/TVS-CS/lms_process/llm_notes.json` (inferred from appsettings, file:line evidence there):
- `messaging:processLeadService:publish:azure-service-bus:unknown` — evidence `processLeadService/Services/DispatchService.cs:25`, `processLeadService/Services/DispatchService.cs:43`
- `messaging:processLeadService:subscribe:azure-service-bus:unknown` — evidence `processLeadService/ListenerService/MdpConsumer.cs:42`, `processLeadService/ListenerService/QueueConsumer.cs:36`

## External Integrations
lms-process third-party systems detected in code.
N/A — no `external:` system matched by the registry.

## Rate Limits and SLAs
lms-process: N/A — not determinable from code.

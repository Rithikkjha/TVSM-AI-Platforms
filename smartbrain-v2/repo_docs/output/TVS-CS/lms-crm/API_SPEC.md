---
service_id: lms-crm
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# lms-crm — API Specification

## Authentication
lms-crm exposes only `GET /` with no auth attribute. Outbound CCP and dialer calls obtain tokens from `CCP_TOKEN_URL` / `DIALER_TOKEN_URL` (names only, `Utils/AppSettingsService.cs:29-32`); tokens cached in `dialer_token`.
API contract: openapi-3 generated at runtime by swashbuckle (`/swagger/v1/swagger.json`; `crmService.csproj:13`), no committed contract file.

## Endpoint Index
lms-crm exposes 1 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Handler | Auth | Callers (service_id) |
|---|---|---|---|---|
| GET | `/` | `CrmController.Crm` | none in code | - |

## Endpoints
lms-crm endpoint details (from inventory `inbound_http` + service.yaml `schemas`).

### GET /
Handler `CrmController.Crm`; auth: none in code.
Request body: none.
Responses: 200, 422.

## Outbound Calls
lms-crm outbound HTTP calls (1 in service.yaml).

| Target (service_id) | Method | Path | Criticality | Client |
|---|---|---|---|---|
| `external:salesforce` | - | - | Unknown | see HLC.md Integration Clients |

## Schemas
lms-crm DTOs referenced by endpoints.
N/A — no schemas extracted (listener service; message payloads are deserialised from JSON in handlers).

## Events Published
lms-crm publishes 1 messaging entit(y/ies).

| Topic / Queue | Type | Broker | name_from | Message types | Payload | Published from | Consumers |
|---|---|---|---|---|---|---|---|
| Unknown (`unknown`) | queue | azure-service-bus | `unknown` | see LLD State Machines | JSON string | `Services/DispatchService.cs:19` | none resolved |

## Events Consumed
lms-crm consumes 1 messaging entit(y/ies).

| Topic / Queue | Subscription | Broker | name_from | Handler | Producers | DLQ / retry |
|---|---|---|---|---|---|---|
| `lms` | `CRM` | azure-service-bus | `config:AppSettings:TOPIC_NAME` | `ListenerService/CrmListenerService.cs:63` | `lms-ems`, `lms-process` | none in code |

Phase-2 extraction for lms-crm left these entity names unresolved; topic names above come from `runs/TVS-CS/lms_crm/llm_notes.json` (inferred from appsettings, file:line evidence there):
- `messaging:.:publish:azure-service-bus:unknown` — evidence `Services/DispatchService.cs:19`
- `messaging:.:subscribe:azure-service-bus:unknown` — evidence `ListenerService/CrmListenerService.cs:44`

## External Integrations
lms-crm third-party systems detected in code.

| System | Category | Evidence |
|---|---|---|
| `external:salesforce` | crm | config key `CCP_URL` host (`appsettings.Development.json:16`) |

## Rate Limits and SLAs
lms-crm: N/A — not determinable from code.

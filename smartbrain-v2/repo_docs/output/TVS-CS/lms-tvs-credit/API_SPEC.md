---
service_id: lms-tvs-credit
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# lms-tvs-credit — API Specification

## Authentication
lms-tvs-credit exposes only `GET /` with no auth attribute; outbound auth to TVS Credit: Unknown (see `TvscreditService.cs`).
API contract: openapi-3 generated at runtime by swashbuckle (`/swagger/v1/swagger.json`; `lms_tvs_credit/lms_tvs_credit.csproj:22`), no committed contract file.

## Endpoint Index
lms-tvs-credit exposes 1 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Handler | Auth | Callers (service_id) |
|---|---|---|---|---|
| GET | `/` | `TvsCreditController.Credit` | none in code | - |

## Endpoints
lms-tvs-credit endpoint details (from inventory `inbound_http` + service.yaml `schemas`).

### GET /
Handler `TvsCreditController.Credit`; auth: none in code.
Request body: none.
Responses: 200, 422.

## Outbound Calls
lms-tvs-credit outbound HTTP calls (0 in service.yaml).

| Target (service_id) | Method | Path | Criticality | Client |
|---|---|---|---|---|
| N/A | - | - | - | no registry-resolved outbound HTTP; config-driven HTTP clients listed in HLC.md |

## Schemas
lms-tvs-credit DTOs referenced by endpoints.
N/A — no schemas extracted (listener service; message payloads are deserialised from JSON in handlers).

## Events Published
lms-tvs-credit publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | name_from | Message types | Payload | Published from | Consumers |
|---|---|---|---|---|---|---|---|
| N/A | | | | | | no publisher in code | |

## Events Consumed
lms-tvs-credit consumes 1 messaging entit(y/ies).

| Topic / Queue | Subscription | Broker | name_from | Handler | Producers | DLQ / retry |
|---|---|---|---|---|---|---|
| `lms` | `FINANCE` | azure-service-bus | `config:AppSettings:TOPIC_NAME` | `lms_tvs_credit/ListenerService/TvscreditListenerService.cs:62` | `lms-ems`, `lms-process` | none in code |

Phase-2 extraction for lms-tvs-credit left these entity names unresolved; topic names above come from `runs/TVS-CS/lms_tvs_credit/llm_notes.json` (inferred from appsettings, file:line evidence there):
- `messaging:lms_tvs_credit:subscribe:azure-service-bus:unknown` — evidence `lms_tvs_credit/ListenerService/TvscreditListenerService.cs:46`

## External Integrations
lms-tvs-credit third-party systems detected in code.
N/A — no `external:` system matched by the registry.

## Rate Limits and SLAs
lms-tvs-credit: N/A — not determinable from code.

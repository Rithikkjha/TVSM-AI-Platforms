---
service_id: parts-catalogue-ingestion-service
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# parts-catalogue-ingestion-service — API Specification

## Authentication
parts-catalogue-ingestion-service endpoint auth as extracted: no endpoints.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
parts-catalogue-ingestion-service exposes 0 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

## Endpoints
parts-catalogue-ingestion-service endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
parts-catalogue-ingestion-service outbound HTTP calls (4 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| Unknown (config:catalogue.api.mdp.baseUrl) | GET | `/` | - | MdpResponseDto | Unknown | Unknown |
| Unknown (config:catalogue.api.norton.baseUrl) | GET | `/` | ParameterizedTypeReference | - | Unknown | Unknown |
| Unknown (config:catalogue.api.price.baseUrl) | GET | `/` | - | PriceApiResponseDto | Unknown | Unknown |
| Unknown (config:catalogue.api.mdp.tokenUrl) | POST | `/` | - | object | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/` | restclient | config:catalogue.api.mdp.baseUrl | `src/main/java/org/com/graph/config/ApiClientConfig.java:219` |
| GET | `/` | restclient | config:catalogue.api.norton.baseUrl | `src/main/java/org/com/graph/config/ApiClientConfig.java:151` |
| GET | `/` | restclient | config:catalogue.api.price.baseUrl | `src/main/java/org/com/graph/config/ApiClientConfig.java:197` |
| POST | `/` | restclient | config:catalogue.api.mdp.tokenUrl | `src/main/java/org/com/graph/config/ApiClientConfig.java:240` |

## Schemas
parts-catalogue-ingestion-service DTOs/payloads referenced in this file.

### MdpResponseDto
Defined in: `src/main/java/org/com/graph/dto/MdpResponseDto.java:11`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | MdpData | False | - |

### ParameterizedTypeReference
Defined in: `None`
Fields: Unknown (no fields extracted)

### PriceApiResponseDto
Defined in: `src/main/java/org/com/graph/dto/PriceApiResponseDto.java:16`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| Parts | PricePartDto[] | False | - |

## Events Published
parts-catalogue-ingestion-service publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
parts-catalogue-ingestion-service consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
parts-catalogue-ingestion-service third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
parts-catalogue-ingestion-service: rate-limit related: `org.springframework.cloud:spring-cloud-starter-circuitbreaker-resilience4j`; SLAs N/A — not determinable from code.

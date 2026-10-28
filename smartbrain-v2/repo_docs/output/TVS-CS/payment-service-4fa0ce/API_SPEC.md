---
service_id: payment-service-4fa0ce
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# payment-service-4fa0ce — API Specification

## Authentication
payment-service-4fa0ce endpoint auth as extracted: no endpoints.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
payment-service-4fa0ce exposes 0 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

## Endpoints
payment-service-4fa0ce endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
payment-service-4fa0ce outbound HTTP calls (6 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:juspay` | - | - | - | - | Unknown | hard |
| Unknown (env:BookingService) | POST | `/` | object | - | Unknown | Unknown |
| Unknown (env:TVSConnectEVMandate) | POST | `/` | map<string,string> | - | Unknown | Unknown |
| Unknown (env:TVSSparesAutoRefunds) | POST | `/` | map<string,string> | - | Unknown | Unknown |
| Unknown (env:TokenUrl) | POST | `/` | - | - | Unknown | Unknown |
| Unknown (env:iceWebsiteShopify) | POST | `/` | map<string,string> | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| POST | `/` | httpclient | env:BookingService | `Functions/JusPayWebhooks.cs:193` |
| POST | `/` | httpclient | env:TVSConnectEVMandate | `Functions/JusPayWebhooks.cs:223` |
| POST | `/` | httpclient | env:TVSSparesAutoRefunds | `Functions/JusPayWebhooks.cs:175` |
| POST | `/` | httpclient | env:TokenUrl | `Functions/JusPayWebhooks.cs:244` |
| POST | `/` | httpclient | env:iceWebsiteShopify | `Functions/JusPayWebhooks.cs:158` |

## Schemas
payment-service-4fa0ce DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
payment-service-4fa0ce publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
payment-service-4fa0ce consumes 1 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| cpg-juspay | Unknown | - | - | Unknown | `Functions/JusPayWebhooks.cs:23` | none resolved | Unknown | Unknown |

## External Integrations
payment-service-4fa0ce third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:juspay` | category payments; matched `JusPayPaymentStatus` at `Constants/JusPayPaymentStatus.cs:3` | Unknown |

## Rate Limits and SLAs
payment-service-4fa0ce: N/A — not determinable from code.

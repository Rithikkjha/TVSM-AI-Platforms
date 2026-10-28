---
service_id: qrcode-frontend
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# qrcode-frontend — API Specification

## Authentication
qrcode-frontend endpoint auth as extracted: no endpoints.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
qrcode-frontend exposes 0 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|

## Endpoints
qrcode-frontend endpoint details (from inventory `inbound_http`).
N/A — no inbound HTTP endpoints in this repo.

## Outbound Calls
qrcode-frontend outbound HTTP calls (15 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `tvsmbe-qrcode` | GET | `/api/analytics/summary` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | GET | `/api/analytics/timeline` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | GET | `/api/analytics/top` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | GET | `/api/auth/config` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | GET | `/api/auth/me` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | PATCH | `/api/qr-library/{}/redirect` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | PATCH | `/api/qr-library/{}/status` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/auth/login` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/auth/logout` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/auth/refresh` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/qr-create/preview` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/qr-create/save` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/qr/generate` | - | - | Unknown | hard |
| `tvsmbe-qrcode` | POST | `/api/qr/save` | - | - | Unknown | hard |
| Unknown (env:VITE_API_BASE) | POST | `/api/qr/shortcode` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/api/analytics/summary` | fetch | env:VITE_API_BASE | `src/api.ts:218` |
| GET | `/api/analytics/timeline` | fetch | env:VITE_API_BASE | `src/api.ts:236` |
| GET | `/api/analytics/top` | fetch | env:VITE_API_BASE | `src/api.ts:226` |
| GET | `/api/auth/config` | fetch | env:VITE_API_BASE | `src/auth/AuthProvider.tsx:116` |
| GET | `/api/auth/me` | fetch | env:VITE_API_BASE | `src/auth/AuthProvider.tsx:140` |
| PATCH | `/api/qr-library/{}/redirect` | fetch | env:VITE_API_BASE | `src/api.ts:166` |
| PATCH | `/api/qr-library/{}/status` | fetch | env:VITE_API_BASE | `src/api.ts:183` |
| POST | `/api/auth/login` | fetch | env:VITE_API_BASE | `src/api.ts:32` |
| POST | `/api/auth/logout` | fetch | env:VITE_API_BASE | `src/api.ts:61` |
| POST | `/api/auth/refresh` | fetch | env:VITE_API_BASE | `src/api.ts:47` |
| POST | `/api/qr-create/preview` | fetch | env:VITE_API_BASE | `src/api.ts:93` |
| POST | `/api/qr-create/save` | fetch | env:VITE_API_BASE | `src/api.ts:114` |
| POST | `/api/qr/generate` | fetch | env:VITE_API_BASE | `src/api.ts:248` |
| POST | `/api/qr/save` | fetch | env:VITE_API_BASE | `src/api.ts:265` |
| POST | `/api/qr/shortcode` | fetch | env:VITE_API_BASE | `src/api.ts:71` |

## Schemas
qrcode-frontend DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
qrcode-frontend publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
qrcode-frontend consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
qrcode-frontend third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
qrcode-frontend: N/A — not determinable from code.

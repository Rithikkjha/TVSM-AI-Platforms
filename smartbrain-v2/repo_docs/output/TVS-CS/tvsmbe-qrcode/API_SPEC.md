---
service_id: tvsmbe-qrcode
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# tvsmbe-qrcode — API Specification

## Authentication
tvsmbe-qrcode endpoint auth as extracted: `None` × 21.
Auth-related code: `src/main/java/com/tvsmotor/qrcode/auth/JwtService.java:4` (jsonwebtoken), `src/main/java/com/tvsmotor/qrcode/auth/TvsmAuthFilter.java:5` (jsonwebtoken).
Auth libraries: `io.jsonwebtoken:jjwt-api`, `io.jsonwebtoken:jjwt-impl`, `io.jsonwebtoken:jjwt-jackson`, `org.springframework.security:spring-security-crypto`.

## Endpoint Index
tvsmbe-qrcode exposes 21 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/api/analytics/scans/{shortCode}` | Unknown | handler `AnalyticsController.scansByShortCode` | Unknown |
| GET | `/api/analytics/summary` | Unknown | handler `AnalyticsController.summary` | qrcode-frontend |
| GET | `/api/analytics/timeline` | Unknown | handler `AnalyticsController.timeline` | qrcode-frontend |
| GET | `/api/analytics/top` | Unknown | handler `AnalyticsController.topQrCodes` | qrcode-frontend |
| GET | `/api/auth/config` | Unknown | handler `AuthController.getConfig` | qrcode-frontend |
| GET | `/api/auth/me` | Unknown | handler `AuthController.me` | qrcode-frontend |
| GET | `/api/qr-library` | Unknown | handler `QrLibraryController.list` | Unknown |
| GET | `/api/qr-library/{id}` | Unknown | handler `QrLibraryController.getOne` | Unknown |
| GET | `/api/v1/logos` | Unknown | handler `LogosController.list` | Unknown |
| GET | `/api/v1/logos/file` | Unknown | handler `LogosController.file` | Unknown |
| GET | `/{shortCode}` | Unknown | handler `RedirectController.resolve` | Unknown |
| PATCH | `/api/qr-library/{id}/redirect` | Unknown | handler `QrLibraryController.updateRedirect` | qrcode-frontend |
| PATCH | `/api/qr-library/{id}/status` | Unknown | handler `QrLibraryController.updateStatus` | qrcode-frontend |
| POST | `/api/auth/login` | Unknown | handler `AuthController.login` | cbs-admin-portal, qrcode-frontend |
| POST | `/api/auth/logout` | Unknown | handler `AuthController.logout` | qrcode-frontend |
| POST | `/api/auth/refresh` | Unknown | handler `AuthController.refresh` | qrcode-frontend |
| POST | `/api/auth/signup` | Unknown | handler `AuthController.signup` | Unknown |
| POST | `/api/qr-create/preview` | Unknown | handler `QrCreateController.preview` | qrcode-frontend |
| POST | `/api/qr-create/save` | Unknown | handler `QrCreateController.save` | qrcode-frontend |
| POST | `/api/qr/generate` | Unknown | handler `QrComposeController.generateOnly` | qrcode-frontend |
| POST | `/api/qr/save` | Unknown | handler `QrComposeController.save` | qrcode-frontend |

## Endpoints
tvsmbe-qrcode endpoint details (from inventory `inbound_http`).

### GET /api/analytics/scans/{shortCode}
Handler: `AnalyticsController.scansByShortCode` in `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:27`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| shortCode | path | string | True | |
| page | query | integer | False | |
| size | query | integer | False | |

Response `200`: `map<string,object>`

### GET /api/analytics/summary
Handler: `AnalyticsController.summary` in `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:27`. Purpose: Unknown. Callers: qrcode-frontend.

Response `200`: `map<string,object>`

### GET /api/analytics/timeline
Handler: `AnalyticsController.timeline` in `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:27`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| days | query | integer | False | |
| shortCode | query | string | False | |

Response `200`: `map<string,object>[]`

### GET /api/analytics/top
Handler: `AnalyticsController.topQrCodes` in `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:27`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| limit | query | integer | False | |
| days | query | integer | False | |

Response `200`: `map<string,object>[]`

### GET /api/auth/config
Handler: `AuthController.getConfig` in `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java:30`. Purpose: Unknown. Callers: qrcode-frontend.

Response `200`: `map<string,object>`

### GET /api/auth/me
Handler: `AuthController.me` in `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java:30`. Purpose: Unknown. Callers: qrcode-frontend.

Response `200`: `map<string,object>`

### GET /api/qr-library
Handler: `QrLibraryController.list` in `src/main/java/com/tvsmotor/qrcode/controller/QrLibraryController.java:38`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| page | query | integer | False | |
| size | query | integer | False | |
| sort | query | string | False | |
| filter | query | string | False | |
| q | query | string | False | |
| status | query | string | False | |
| subjectType | query | string | False | |

Response `200`: `map<string,object>`

### GET /api/qr-library/{id}
Handler: `QrLibraryController.getOne` in `src/main/java/com/tvsmotor/qrcode/controller/QrLibraryController.java:38`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

Response `200`: `Unknown`

### GET /api/v1/logos
Handler: `LogosController.list` in `src/main/java/com/tvsmotor/qrcode/controller/LogosController.java:23`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| q | query | string | False | |

Response `200`: `map<string,object>`

### GET /api/v1/logos/file
Handler: `LogosController.file` in `src/main/java/com/tvsmotor/qrcode/controller/LogosController.java:23`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| path | query | string | True | |

Response `200`: `binary`

### GET /{shortCode}
Handler: `RedirectController.resolve` in `src/main/java/com/tvsmotor/qrcode/controller/RedirectController.java:27`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| shortCode | path | string | True | |

Response `200`: `Unknown`

### PATCH /api/qr-library/{id}/redirect
Handler: `QrLibraryController.updateRedirect` in `src/main/java/com/tvsmotor/qrcode/controller/QrLibraryController.java:38`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |
| body | body | map<string,string> | True | |

Request body: `map<string,string>` (schema Unknown)

Response `200`: `Unknown`

### PATCH /api/qr-library/{id}/status
Handler: `QrLibraryController.updateStatus` in `src/main/java/com/tvsmotor/qrcode/controller/QrLibraryController.java:38`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |
| body | body | map<string,string> | True | |

Request body: `map<string,string>` (schema Unknown)

Response `200`: `Unknown`

### POST /api/auth/login
Handler: `AuthController.login` in `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java:30`. Purpose: Unknown. Callers: cbs-admin-portal, qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| body | body | map<string,string> | True | |

Request body: `map<string,string>` (schema Unknown)

Response `200`: `map<string,object>`

### POST /api/auth/logout
Handler: `AuthController.logout` in `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java:30`. Purpose: Unknown. Callers: qrcode-frontend.

Response `200`: `map<string,object>`

### POST /api/auth/refresh
Handler: `AuthController.refresh` in `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java:30`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| body | body | map<string,string> | True | |

Request body: `map<string,string>` (schema Unknown)

Response `200`: `map<string,object>`

### POST /api/auth/signup
Handler: `AuthController.signup` in `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java:30`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| body | body | map<string,string> | True | |

Request body: `map<string,string>` (schema Unknown)

Response `200`: `map<string,object>`

### POST /api/qr-create/preview
Handler: `QrCreateController.preview` in `src/main/java/com/tvsmotor/qrcode/controller/QrCreateController.java:41`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| redirectUrl | query | string | True | |
| size | query | integer | False | |
| logoScale | query | number | False | |
| fgColorHex | query | string | False | |
| bgColorHex | query | string | False | |
| cornerColorHex | query | string | False | |
| qrStyle | query | string | False | |
| labelText | query | string | False | |
| logoPath | query | string | False | |
| logo | form | binary | False | |
| shortCode | query | string | False | |

Response `200`: `string`

### POST /api/qr-create/save
Handler: `QrCreateController.save` in `src/main/java/com/tvsmotor/qrcode/controller/QrCreateController.java:41`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| redirectUrl | query | string | True | |
| scopeType | query | string | True | |
| marketTag | query | string | False | |
| regionCode | query | string | False | |
| countryCode | query | string | False | |
| subjectType | query | string | True | |
| subjectKey | query | string | True | |
| size | query | integer | False | |
| logoScale | query | number | False | |
| fgColorHex | query | string | False | |
| bgColorHex | query | string | False | |
| cornerColorHex | query | string | False | |
| qrStyle | query | string | False | |
| labelText | query | string | False | |
| logoPath | query | string | False | |
| logo | form | binary | False | |
| metadata | query | string | False | |
| shortCode | query | string | False | |

Response `200`: `Unknown`

### POST /api/qr/generate
Handler: `QrComposeController.generateOnly` in `src/main/java/com/tvsmotor/qrcode/controller/QrComposeController.java:66`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| targetUrl | query | string | True | |
| size | query | integer | False | |
| logoScale | query | number | False | |
| fgColorHex | query | string | False | |
| bgColorHex | query | string | False | |
| cornerColorHex | query | string | False | |
| qrStyle | query | string | False | |
| labelText | query | string | False | |
| logoPath | query | string | False | |
| logo | form | binary | False | |

Response `200`: `string`

### POST /api/qr/save
Handler: `QrComposeController.save` in `src/main/java/com/tvsmotor/qrcode/controller/QrComposeController.java:66`. Purpose: Unknown. Callers: qrcode-frontend.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| targetUrl | query | string | True | |
| shortCode | query | string | False | |
| scopeType | query | string | True | |
| marketTag | query | string | False | |
| regionCode | query | string | False | |
| countryCode | query | string | False | |
| subjectType | query | string | True | |
| subjectKey | query | string | True | |
| size | query | integer | False | |
| logoScale | query | number | False | |
| fgColorHex | query | string | False | |
| bgColorHex | query | string | False | |
| cornerColorHex | query | string | False | |
| qrStyle | query | string | False | |
| labelText | query | string | False | |
| logoPath | query | string | False | |
| logo | form | binary | False | |
| metadata | query | string | False | |

Response `200`: `Unknown`

## Outbound Calls
tvsmbe-qrcode outbound HTTP calls (0 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| N/A | | | | | no outbound calls extracted | |

## Schemas
tvsmbe-qrcode DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
tvsmbe-qrcode publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
tvsmbe-qrcode consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
tvsmbe-qrcode third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
tvsmbe-qrcode: N/A — not determinable from code.

---
service_id: tvsm-securesigner-service
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# tvsm-securesigner-service — API Specification

## Authentication
tvsm-securesigner-service endpoint auth as extracted: `None` × 6.
Auth-related code: `src/main/java/com/tvsm/urlsigner/service/SignerService.java:12` (jsonwebtoken).
Auth libraries: `com.nimbusds:nimbus-jose-jwt`, `io.jsonwebtoken:jjwt-api`, `io.jsonwebtoken:jjwt-impl`, `io.jsonwebtoken:jjwt-jackson`, `org.springframework.security:spring-security-crypto`.

## Endpoint Index
tvsm-securesigner-service exposes 6 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/generate/bcrypt-hash` | Unknown | handler `SignerController.generateBCryptHash` | Unknown |
| GET | `/generate/decrypted-jwt` | Unknown | handler `SignerController.decryptJwt` | Unknown |
| GET | `/generate/jwt` | Unknown | handler `SignerController.getToken` | Unknown |
| GET | `/generate/sign` | Unknown | handler `SignerController.getSignedUrl` | Unknown |
| GET | `/test/test` | Unknown | handler `TestController.healthTest` | Unknown |
| POST | `/generate/encrypted-jwt` | Unknown | handler `SignerController.createEncryptedJwt` | Unknown |

## Endpoints
tvsm-securesigner-service endpoint details (from inventory `inbound_http`).

### GET /generate/bcrypt-hash
Handler: `SignerController.generateBCryptHash` in `src/main/java/com/tvsm/urlsigner/controller/SignerController.java:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| data | query | string | True | |
| strength | query | integer | True | |

Response `200`: `string`

### GET /generate/decrypted-jwt
Handler: `SignerController.decryptJwt` in `src/main/java/com/tvsm/urlsigner/controller/SignerController.java:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| jwe | query | string | True | |
| X-PRIVATE-KEY | header | string | True | |
| X-PUBLIC-KEY | header | string | True | |

Response `200`: `map<string,object>`

### GET /generate/jwt
Handler: `SignerController.getToken` in `src/main/java/com/tvsm/urlsigner/controller/SignerController.java:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| queryParams | query | map<string,string> | True | |
| exp | query | integer | True | |
| sig | query | string | True | |

Response `200`: `string`

### GET /generate/sign
Handler: `SignerController.getSignedUrl` in `src/main/java/com/tvsm/urlsigner/controller/SignerController.java:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| url | query | string | True | |
| expiry | query | integer | True | |

Response `200`: `string`

### GET /test/test
Handler: `TestController.healthTest` in `src/main/java/com/tvsm/urlsigner/controller/TestController.java:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| beacon | query | string | True | |

Response `200`: `object`

### POST /generate/encrypted-jwt
Handler: `SignerController.createEncryptedJwt` in `src/main/java/com/tvsm/urlsigner/controller/SignerController.java:15`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| payload | body | map<string,object> | True | |
| X-PRIVATE-KEY | header | string | True | |
| X-PUBLIC-KEY | header | string | True | |
| X-KEY-ID | header | string | True | |

Request body: `map<string,object>` (schema Unknown)

Response `200`: `string`

## Outbound Calls
tvsm-securesigner-service outbound HTTP calls (0 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| N/A | | | | | no outbound calls extracted | |

## Schemas
tvsm-securesigner-service DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
tvsm-securesigner-service publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
tvsm-securesigner-service consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
tvsm-securesigner-service third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| N/A | none detected | |

## Rate Limits and SLAs
tvsm-securesigner-service: N/A — not determinable from code.

---
service_id: tvsmbe-qrcode
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvsmbe qrcode", "backend public", "qrcode"]
---

# tvsmbe-qrcode — Overview

## Purpose
Summary: Backend for QR code generation, library, logos, composition and analytics with auth endpoints; no README.
Also known as: tvsmbe qrcode, backend public, qrcode
tvsmbe-qrcode is a `backend-api` repository (`tvsmbe-qrcode`; service.yaml `type: backend-api`). Business purpose: Unknown — not stated in README/code.

## Users and Consumers
tvsmbe-qrcode is called over HTTP by: `cbs-admin-portal`, `qrcode-frontend`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvsmbe-qrcode capabilities derived from code:
- `AuthController`: 6 HTTP endpoint(s)
- `AnalyticsController`: 4 HTTP endpoint(s)
- `QrLibraryController`: 4 HTTP endpoint(s)
- `LogosController`: 2 HTTP endpoint(s)
- `QrCreateController`: 2 HTTP endpoint(s)
- `QrComposeController`: 2 HTTP endpoint(s)
- `RedirectController`: 1 HTTP endpoint(s)

## Tech Stack
tvsmbe-qrcode tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mongo | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure:azure-storage-blob`, `com.google.zxing:core`, `com.google.zxing:javase`, `io.jsonwebtoken:jjwt-api`, `io.jsonwebtoken:jjwt-impl`, `io.jsonwebtoken:jjwt-jackson`, `org.apache.xmlgraphics:batik-codec`, `org.apache.xmlgraphics:batik-transcoder`, `org.modelmapper:modelmapper`, `org.projectlombok:lombok`, `org.springframework.boot:spring-boot-starter-data-mongodb`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.security:spring-security-crypto`

## Dependencies at a Glance
Upstream (calls tvsmbe-qrcode): `cbs-admin-portal`, `qrcode-frontend`
Downstream (tvsmbe-qrcode calls): none resolved
Brokers: none. Data stores: `tvs_qr` (mongo, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsmbe-qrcode environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |

## Environment Variables
tvsmbe-qrcode configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Unknown | Unknown | True | Unknown |
| `MONGO_INITDB_DATABASE` | Unknown | Unknown | False | Unknown |
| `MONGO_INITDB_ROOT_PASSWORD` | Unknown | Unknown | True | Unknown |
| `MONGO_INITDB_ROOT_USERNAME` | Unknown | Unknown | False | Unknown |
| `MONGO_URI` | Unknown | Unknown | True | Unknown |
| `SPRING_PROFILES_ACTIVE` | Unknown | Unknown | False | Unknown |
| `TVSM_AUTH_JWT_SECRET` | Unknown | Unknown | True | Unknown |
| `TVSM_AUTH_PASSWORD_PEPPER` | Unknown | Unknown | True | Unknown |
| `APP_DOMAIN_BASE` | Unknown | True | False | app-settings, unknown |
| `AZURE_STORAGE_CONTAINER` | Unknown | Unknown | False | app-settings, unknown |
| `AZURE_STORAGE_ENABLED` | Unknown | Unknown | False | app-settings, unknown |
| `SERVER_PORT` | Unknown | Unknown | False | app-settings, unknown |
| `TVSM_AUTH_ENABLED` | Unknown | Unknown | False | app-settings, unknown |
| `app.qr.folder-root` | Unknown | True | False | app-settings |
| `azure.storage.connection-string` | Unknown | Unknown | True | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.auto-index-creation` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.uri` | Unknown | Unknown | True | app-settings |
| `spring.mvc.cors.mappings.[/**].allow-credentials` | Unknown | Unknown | True | app-settings |
| `spring.mvc.cors.mappings.[/**].allowed-headers` | Unknown | Unknown | False | app-settings |
| `spring.mvc.cors.mappings.[/**].allowed-methods` | Unknown | Unknown | False | app-settings |
| `spring.mvc.cors.mappings.[/**].allowed-origins` | Unknown | Unknown | False | app-settings |
| `tvsm.auth.jwt-secret` | Unknown | Unknown | True | app-settings |
| `tvsm.auth.password-pepper` | Unknown | Unknown | True | app-settings |

## Ownership
tvsmbe-qrcode ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsmbe-qrcode local setup evidence:
- README: none
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsmbe-qrcode limitations evidenced by extraction:
- N/A — none evidenced in code

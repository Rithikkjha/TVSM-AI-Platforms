---
service_id: tvsm-otp-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["otp service", "otp generate verify", "tvsm otp service", "otp", "tvsm otp"]
---

# tvsm-otp-service — Overview

## Purpose
Summary: Spring Boot OTP service with generate and verify endpoints.
Also known as: otp service, otp generate verify, tvsm otp service, otp, tvsm otp
tvsm-otp-service is a `backend-api` repository (`tvsm-otp-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: OTP Service - Spring Boot Application.

## Users and Consumers
tvsm-otp-service is called over HTTP by: `tvs-cps-backend`, `tvsmbe-location`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvsm-otp-service capabilities derived from code:
- `OtpController`: 2 HTTP endpoint(s)

## Tech Stack
tvsm-otp-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | redis | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.googlecode.libphonenumber:libphonenumber`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-aop`, `org.springframework.boot:spring-boot-starter-data-redis`, `org.springframework.boot:spring-boot-starter-log4j2`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`

## Dependencies at a Glance
Upstream (calls tvsm-otp-service): `tvs-cps-backend`, `tvsmbe-location`
Downstream (tvsm-otp-service calls): none resolved
Brokers: none. Data stores: `config:spring.redis.host` (redis, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsm-otp-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| local | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvsm-otp-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `JAVA_OPTS` | Unknown | Unknown | False | Unknown |
| `app.environment` | Unknown | True | False | app-settings |
| `app.last-merged-pr` | Unknown | True | False | app-settings |
| `hmac.secret-key` | Unknown | True | True | app-settings |
| `management.endpoint.health.enabled` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `spring.redis.cacheTtl` | Unknown | Unknown | False | app-settings |
| `spring.redis.cluster-enabled` | Unknown | Unknown | False | app-settings |
| `spring.redis.database` | Unknown | True | False | app-settings |
| `spring.redis.host` | Unknown | True | False | app-settings |
| `spring.redis.password` | Unknown | True | True | app-settings |
| `spring.redis.port` | Unknown | True | False | app-settings |
| `spring.redis.ssl-enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |

## Ownership
tvsm-otp-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsm-otp-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsm-otp-service limitations evidenced by extraction:
- N/A — none evidenced in code

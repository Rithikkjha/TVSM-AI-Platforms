---
service_id: tvsm-securesigner-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvsm securesigner service", "tvsmbe securesigner", "securesigner", "securesigner service", "tvsm securesigner"]
---

# tvsm-securesigner-service — Overview

## Purpose
Summary: Spring Boot utility API that generates signatures, JWTs (plain/encrypted/decrypted) and bcrypt hashes; README gives only the title.
Also known as: tvsm securesigner service, tvsmbe securesigner, securesigner, securesigner service, tvsm securesigner
tvsm-securesigner-service is a `backend-api` repository (`tvsm-securesigner-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as:  — "# tvsm-securesigner-service".

## Users and Consumers
tvsm-securesigner-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
tvsm-securesigner-service capabilities derived from code:
- `SignerController`: 5 HTTP endpoint(s)
- `TestController`: 1 HTTP endpoint(s)

## Tech Stack
tvsm-securesigner-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure.spring:spring-cloud-azure-starter-keyvault-secrets`, `com.nimbusds:nimbus-jose-jwt`, `io.jsonwebtoken:jjwt-api`, `io.jsonwebtoken:jjwt-impl`, `io.jsonwebtoken:jjwt-jackson`, `org.springframework.boot:spring-boot-starter-cache`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.security:spring-security-crypto`

## Dependencies at a Glance
Upstream (calls tvsm-securesigner-service): Unknown
Downstream (tvsm-securesigner-service calls): none resolved
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsm-securesigner-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvsm-securesigner-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `signer-key-name` | Unknown | True | True | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.cache.jcache.config` | Unknown | Unknown | False | app-settings |
| `spring.cloud.azure.client-id` | Unknown | Unknown | False | app-settings |
| `spring.cloud.azure.credential.managed-identity-enabled` | Unknown | Unknown | True | app-settings |
| `spring.cloud.azure.keyvault.endpoint` | Unknown | Unknown | False | app-settings |

## Ownership
tvsm-securesigner-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsm-securesigner-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsm-securesigner-service limitations evidenced by extraction:
- No inbound callers resolved in the registry.

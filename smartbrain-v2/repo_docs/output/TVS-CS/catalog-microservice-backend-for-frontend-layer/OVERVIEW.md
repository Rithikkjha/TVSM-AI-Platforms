---
service_id: catalog-microservice-backend-for-frontend-layer
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["catalog microservice backend for frontend layer", "nodejs catalog bff layer", "ems catalog", "ems catalog bff", "catalog"]
---

# catalog-microservice-backend-for-frontend-layer — Overview

## Purpose
Summary: Node BFF exposing a catalogue endpoint plus health check, forwarding requests to core-commerce-platform-api-service catalog configuration APIs.
Also known as: catalog microservice backend for frontend layer, nodejs catalog bff layer, ems catalog, ems catalog bff, catalog
catalog-microservice-backend-for-frontend-layer is a `bff` repository (`Catalog-Microservice-Backend-for-Frontend-Layer`; service.yaml `type: bff`). Business purpose: README (`README.md`) describes it as: README #.

## Users and Consumers
catalog-microservice-backend-for-frontend-layer is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
catalog-microservice-backend-for-frontend-layer capabilities derived from code:
- `catalogHandler`: 1 HTTP endpoint(s)
- `applicationHealthHandler`: 1 HTTP endpoint(s)

## Tech Stack
catalog-microservice-backend-for-frontend-layer tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | express | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | Unknown (build: express,node) | Unknown |

Key libraries: `@azure/identity`, `@azure/keyvault-secrets`, `@types/cors`, `@types/express`, `@types/jest`, `@types/mongoose`, `@types/node`, `@types/nodemon`, `@types/supertest`, `@types/swagger-ui-express`, `apminsight`, `axios`, `cors`, `dotenv`, `express`, `husky`, `jest`, `lint-staged`, `mongodb`, `mongoose`, `nodemon`, `npm-force-resolutions`, `prettier`, `supertest`, `swagger-ui-express`, `ts-jest`, `ts-node`, `typescript`, `winston`

## Dependencies at a Glance
Upstream (calls catalog-microservice-backend-for-frontend-layer): Unknown
Downstream (catalog-microservice-backend-for-frontend-layer calls): `core-commerce-platform-api-service` (hard), `external:site24x7` (None); plus 2 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
catalog-microservice-backend-for-frontend-layer environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Unknown | Unknown | from config/infra file names |

## Environment Variables
catalog-microservice-backend-for-frontend-layer configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `API_SERVER_PORT` | Unknown | Unknown | False | Unknown |
| `AZURE_OAUTH_TOKEN_BASE_URL` | Unknown | Unknown | True | Unknown |
| `CATALOG_MICRO_SERVICES_BASE_URL` | points to core-commerce-platform-api-service | Unknown | False | Unknown |
| `HOST_NAME` | Unknown | Unknown | False | Unknown |
| `KEY_VAULT_NAME` | Unknown | Unknown | True | Unknown |
| `SERVER_HOST_URL` | Unknown | Unknown | False | Unknown |

## Ownership
catalog-microservice-backend-for-frontend-layer ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
catalog-microservice-backend-for-frontend-layer local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
catalog-microservice-backend-for-frontend-layer limitations evidenced by extraction:
- 2 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- No inbound callers resolved in the registry.

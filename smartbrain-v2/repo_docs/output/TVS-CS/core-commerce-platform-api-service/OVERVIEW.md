---
service_id: core-commerce-platform-api-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["core commerce platform api service", "catalog micro services", "catalogs", "catalog", "catalog micro service", "core commerce platform"]
---

# core-commerce-platform-api-service — Overview

## Purpose
Summary: Node catalogue API serving catalogs, catalog configs, cache control, Shopify products and vehicle accessories; README is a starter-kit template.
Also known as: core commerce platform api service, catalog micro services, catalogs, catalog, catalog micro service, core commerce platform
core-commerce-platform-api-service is a `backend-api` repository (`Core-Commerce-Platform-API-Service`; service.yaml `type: backend-api`). Business purpose: Unknown — not stated in README/code.

## Users and Consumers
core-commerce-platform-api-service is called over HTTP by: `catalog-microservice-backend-for-frontend-layer`, `catalog-scheduler`. Event consumers of its published messages: none resolved.

## Key Capabilities
core-commerce-platform-api-service capabilities derived from code:
- `catalogHandler`: 7 HTTP endpoint(s)
- `catalogConfigurationHandler`: 2 HTTP endpoint(s)
- `cacheHandler`: 1 HTTP endpoint(s)
- `applicationHealthHandler`: 1 HTTP endpoint(s)
- `shopifyHandler`: 1 HTTP endpoint(s)
- `vehicleAccessoriesPricingHandler`: 1 HTTP endpoint(s)

## Tech Stack
core-commerce-platform-api-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | express | Unknown |
| Data | mongo, redis | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: express,node) | Unknown |

Key libraries: `@types/cors`, `@types/express`, `@types/jest`, `@types/lodash`, `@types/node`, `@types/nodemon`, `@types/supertest`, `apminsight`, `axios`, `cors`, `dotenv`, `express`, `husky`, `jest`, `lint-staged`, `lodash`, `mongodb`, `mongoose`, `nodemon`, `npm-force-resolutions`, `prettier`, `redis`, `supertest`, `ts-jest`, `ts-node`, `typescript`, `winston`

## Dependencies at a Glance
Upstream (calls core-commerce-platform-api-service): `catalog-microservice-backend-for-frontend-layer`, `catalog-scheduler`
Downstream (core-commerce-platform-api-service calls): `external:site24x7` (None); plus 7 outbound call(s) with unresolved target
Brokers: none. Data stores: `_` (mongo, None), `env:DB_HOST` (mongo, None), `_` (redis, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
core-commerce-platform-api-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
core-commerce-platform-api-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `API_SERVER_PORT` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_API_URL` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_SIGNATURE` | Unknown | Unknown | True | Unknown |
| `BUMBLEBEE_EV_SIGNED_EXPIRY_TIME` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_SIGNED_PERMISSION` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_SIGNED_PROTOCOL` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_SIGNED_RESOURCE` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_SIGNED_START_TIME` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_EV_SIGNED_VERSION` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_API_URL` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_SIGNATURE` | Unknown | Unknown | True | Unknown |
| `BUMBLEBEE_ICE_SIGNED_EXPIRY_TIME` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_SIGNED_PERMISSION` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_SIGNED_PROTOCOL` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_SIGNED_RESOURCE` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_SIGNED_START_TIME` | Unknown | Unknown | False | Unknown |
| `BUMBLEBEE_ICE_SIGNED_VERSION` | Unknown | Unknown | False | Unknown |
| `DB_HOST` | Unknown | Unknown | False | Unknown |
| `DB_NAME` | Unknown | Unknown | False | Unknown |
| `DB_PASSWORD` | Unknown | Unknown | True | Unknown |
| `DB_PORT` | Unknown | Unknown | False | Unknown |
| `DB_SCHEME` | Unknown | Unknown | False | Unknown |
| `DB_USER_NAME` | Unknown | Unknown | False | Unknown |
| `HOST_NAME` | Unknown | Unknown | False | Unknown |
| `NODE_ENV` | Unknown | Unknown | False | Unknown |
| `REDIS_HOST` | Unknown | Unknown | False | Unknown |
| `REDIS_PASSWORD` | Unknown | Unknown | True | Unknown |
| `SERVER_HOST_URL` | Unknown | Unknown | False | Unknown |
| `SHOPIFY_ACCESS_TOKEN` | Unknown | Unknown | True | Unknown |
| `SHOPIFY_API_URL` | Unknown | Unknown | False | Unknown |
| `SHOPIFY_PRODUCT_IDS` | Unknown | Unknown | False | Unknown |
| `X_SHOPIFY_ACCESS_TOKEN` | Unknown | Unknown | True | Unknown |

## Ownership
core-commerce-platform-api-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
core-commerce-platform-api-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
core-commerce-platform-api-service limitations evidenced by extraction:
- 7 outbound HTTP call(s) have no resolved target service (base URL from config/env).

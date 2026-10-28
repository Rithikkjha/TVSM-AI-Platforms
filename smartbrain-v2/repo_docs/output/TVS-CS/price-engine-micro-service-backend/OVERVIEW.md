---
service_id: price-engine-micro-service-backend
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["price engine micro service backend", "price-engine-microservice-backend", "price engine", "priceengine api", "price", "price engine micro service", "priceengine"]
---

# price-engine-micro-service-backend — Overview

## Purpose
Summary: Node PriceEngine backend computing on-road prices, product price components and regions, calling master-data-platform and publishing one message.
Also known as: price engine micro service backend, price-engine-microservice-backend, price engine, priceengine api, price, price engine micro service, priceengine
price-engine-micro-service-backend is a `backend-api` repository (`Price-Engine-MicroService-Backend`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: PriceEngine.

## Users and Consumers
price-engine-micro-service-backend is called over HTTP by: `catalog-scheduler`. Event consumers of its published messages: none resolved.

## Key Capabilities
price-engine-micro-service-backend capabilities derived from code:
- `onRoadPriceHandler`: 7 HTTP endpoint(s)
- `productPriceComponentsHandler`: 4 HTTP endpoint(s)
- `regionHandler`: 2 HTTP endpoint(s)
- `cacheHandler`: 1 HTTP endpoint(s)
- `priceComponentHandler`: 1 HTTP endpoint(s)
- `productHandler`: 1 HTTP endpoint(s)
- `priceUploadHandler`: 1 HTTP endpoint(s)
- Publishes 1 messaging entit(y/ies); consumes 4

## Tech Stack
price-engine-micro-service-backend tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | express | Unknown |
| Data | mongo, redis | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: express,node) | Unknown |

Key libraries: `@azure/service-bus`, `@types/cors`, `@types/express`, `@types/jest`, `@types/multer`, `@types/node`, `@types/nodemon`, `@types/supertest`, `apminsight`, `axios`, `cors`, `dotenv`, `exceljs`, `express`, `husky`, `jest`, `lint-staged`, `mongodb`, `mongodb-memory-server`, `mongoose`, `multer`, `nodemon`, `npm-force-resolutions`, `prettier`, `redis`, `supertest`, `ts-jest`, `ts-node`, `typescript`, `winston`

## Dependencies at a Glance
Upstream (calls price-engine-micro-service-backend): `catalog-scheduler`
Downstream (price-engine-micro-service-backend calls): `external:site24x7` (None), `master-data-platform` (hard); plus 1 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `_` (mongo, None), `env:DB_HOST` (mongo, None), `_` (redis, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
price-engine-micro-service-backend environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| staging | Unknown | from config/infra file names |

## Environment Variables
price-engine-micro-service-backend configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `API_SERVER_PORT` | Unknown | Unknown | False | env-file |
| `CONNECTION_STRING_MARKETPLACE` | Unknown | Unknown | True | Unknown |
| `CONNECTION_STRING_PRICE` | Unknown | Unknown | True | Unknown |
| `CONNECTION_STRING_PRODUCT` | Unknown | Unknown | True | Unknown |
| `DB_HOST` | Unknown | Unknown | False | env-file |
| `DB_NAME` | Unknown | Unknown | False | env-file |
| `DB_PASSWORD` | Unknown | Unknown | True | env-file |
| `DB_PORT` | Unknown | Unknown | False | Unknown |
| `DB_SCHEME` | Unknown | Unknown | False | env-file |
| `DB_USER_NAME` | Unknown | Unknown | False | env-file |
| `ERROR_ROW_LIMIT` | Unknown | Unknown | False | Unknown |
| `HOST_NAME` | Unknown | Unknown | False | Unknown |
| `NODEJS_STARTER_ENV` | Unknown | Unknown | False | env-file |
| `NODE_ENV` | Unknown | Unknown | False | Unknown |
| `REDIS_HOST` | Unknown | Unknown | False | Unknown |
| `REDIS_PASSWORD` | Unknown | Unknown | True | Unknown |
| `SERVER_HOST_URL` | Unknown | Unknown | False | env-file |
| `SUBSCRIPTION_PRICE` | Unknown | Unknown | False | Unknown |
| `SUBSCRIPTION_PRODUCT` | Unknown | Unknown | False | Unknown |
| `TOPIC_NAME_MARKETPLACE` | Unknown | Unknown | False | Unknown |
| `TOPIC_NAME_PRICE` | Unknown | Unknown | False | Unknown |
| `TOPIC_NAME_PRODUCT` | Unknown | Unknown | False | Unknown |

## Ownership
price-engine-micro-service-backend ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
price-engine-micro-service-backend local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
price-engine-micro-service-backend limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- 3 messaging entit(y/ies) whose topic/queue name is not resolvable from code.

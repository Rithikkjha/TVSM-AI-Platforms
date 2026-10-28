---
service_id: price-microservice-backend-for-frontend-layer
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["price microservice backend for frontend layer", "price"]
---

# price-microservice-backend-for-frontend-layer — Overview

## Purpose
Summary: Node BFF exposing on-road price, price-component, region and product endpoints for frontends; README is a placeholder.
Also known as: price microservice backend for frontend layer, price
price-microservice-backend-for-frontend-layer is a `bff` repository (`Price-Microservice-Backend-for-Frontend-Layer`; service.yaml `type: bff`). Business purpose: README (`README.md`) describes it as: README #.

## Users and Consumers
price-microservice-backend-for-frontend-layer is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
price-microservice-backend-for-frontend-layer capabilities derived from code:
- `onRoadPriceHandler`: 6 HTTP endpoint(s)
- `productPriceComponentsHandler`: 4 HTTP endpoint(s)
- `regionHandler`: 2 HTTP endpoint(s)
- `priceComponentHandler`: 1 HTTP endpoint(s)
- `productHandler`: 1 HTTP endpoint(s)

## Tech Stack
price-microservice-backend-for-frontend-layer tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | express | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | Unknown (build: express,node) | Unknown |

Key libraries: `@types/cors`, `@types/express`, `@types/jest`, `@types/node`, `@types/nodemon`, `@types/supertest`, `apminsight`, `axios`, `cors`, `dotenv`, `express`, `husky`, `jest`, `lint-staged`, `nodemon`, `npm-force-resolutions`, `prettier`, `supertest`, `ts-jest`, `ts-node`, `typescript`, `winston`

## Dependencies at a Glance
Upstream (calls price-microservice-backend-for-frontend-layer): Unknown
Downstream (price-microservice-backend-for-frontend-layer calls): `external:site24x7` (None); plus 14 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
price-microservice-backend-for-frontend-layer environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |

## Environment Variables
price-microservice-backend-for-frontend-layer configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `API_SERVER_PORT` | Unknown | Unknown | False | env-file |
| `HOST_NAME` | Unknown | Unknown | False | Unknown |
| `NODEJS_STARTER_ENV` | Unknown | Unknown | False | env-file |
| `PRICE_MICROSERVICE_BASE_URL` | Unknown | Unknown | False | env-file |
| `SERVER_HOST_URL` | Unknown | Unknown | False | env-file |

## Ownership
price-microservice-backend-for-frontend-layer ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
price-microservice-backend-for-frontend-layer local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
price-microservice-backend-for-frontend-layer limitations evidenced by extraction:
- 14 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- No inbound callers resolved in the registry.

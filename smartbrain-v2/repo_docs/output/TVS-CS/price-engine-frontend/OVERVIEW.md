---
service_id: price-engine-frontend
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["price engine frontend", "price engine"]
---

# price-engine-frontend — Overview

## Purpose
Summary: Frontend for the price engine calling on-road price and price-component APIs; README is a placeholder.
Also known as: price engine frontend, price engine
price-engine-frontend is a `frontend-web` repository (`Price-Engine-Frontend`; service.yaml `type: frontend-web`). Business purpose: README (`README.md`) describes it as: README #.

## Users and Consumers
price-engine-frontend is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
price-engine-frontend capabilities derived from code:
- UI making 17 backend API calls

## Tech Stack
price-engine-frontend tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | react | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | Unknown (build: node,react) | Unknown |

Key libraries: `@reduxjs/toolkit`, `@testing-library/jest-dom`, `@testing-library/react`, `@testing-library/user-event`, `@types/jest`, `@types/node`, `@types/react`, `@types/react-dom`, `@types/react-router-dom`, `@types/redux-mock-store`, `@types/uuid`, `axios`, `classnames`, `env-cmd`, `expr-eval`, `react`, `react-dom`, `react-redux`, `react-router`, `react-router-dom`, `react-scripts`, `redux-mock-store`, `tailwind-scrollbar`, `tailwindcss`, `typeface-poppins`, `typescript`, `uuid`, `web-vitals`

## Dependencies at a Glance
Upstream (calls price-engine-frontend): Unknown
Downstream (price-engine-frontend calls): none resolved; plus 17 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
price-engine-frontend environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| sample | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
price-engine-frontend configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `REACT_APP_ENV` | Unknown | True | False | env-file |
| `REACT_APP_PRICE_ENGINE_BFF_BASE_URL` | Unknown | Unknown | False | env-file |

## Ownership
price-engine-frontend ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
price-engine-frontend local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
price-engine-frontend limitations evidenced by extraction:
- 17 outbound HTTP call(s) have no resolved target service (base URL from config/env).

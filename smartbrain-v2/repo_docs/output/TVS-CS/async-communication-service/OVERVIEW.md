---
service_id: async-communication-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["async communication service", "async comm", "async communication"]
---

# async-communication-service — Overview

## Purpose
Summary: Node backend that consumes one messaging entity and forwards payloads to Salesforce, with two daily node-cron jobs; README is a placeholder, so exact business purpose is unclear.
Also known as: async communication service, async comm, async communication
async-communication-service is a `backend-api` repository (`async-communication-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: README #.

## Users and Consumers
async-communication-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
async-communication-service capabilities derived from code:
- Scheduled job `None` (node-cron `30 15 * * *`)
- Scheduled job `None` (node-cron `30 16 * * *`)
- Consumes 1 messaging entit(y/ies)

## Tech Stack
async-communication-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | nest, node | Unknown |
| Data | mssql | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: nest,node) | Unknown |

Key libraries: `@azure/identity`, `@azure/keyvault-secrets`, `@azure/service-bus`, `@nestjs/cli`, `@nestjs/common`, `@nestjs/config`, `@nestjs/core`, `@nestjs/platform-express`, `@nestjs/schedule`, `@nestjs/schematics`, `@nestjs/swagger`, `@nestjs/testing`, `@nestjs/typeorm`, `@prisma/client`, `@sendgrid/mail`, `@types/config`, `@types/express`, `@types/istanbul-lib-coverage`, `@types/istanbul-lib-report`, `@types/jest`, `@types/mssql`, `@types/node`, `@types/supertest`, `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`, `axios`, `class-transformer`, `class-validator`, `cron`, `dotenv` …

## Dependencies at a Glance
Upstream (calls async-communication-service): Unknown
Downstream (async-communication-service calls): `external:salesforce` (hard)
Brokers: azure-service-bus. Data stores: `_` (mssql, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
async-communication-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
async-communication-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `APP_PORT` | Unknown | Unknown | False | Unknown |
| `COMMS_DB_CLIENT_ID` | Unknown | Unknown | False | Unknown |
| `COMMS_DB_CLIENT_SECRET` | Unknown | Unknown | True | Unknown |
| `COMMS_DB_TENANT_ID` | Unknown | Unknown | False | Unknown |
| `COMMS_SERVICE_CONFIG` | Unknown | Unknown | False | Unknown |
| `COMMS_SERVICE_DB_CONFIG` | Unknown | Unknown | False | Unknown |
| `KEYVAULT_URL` | Unknown | Unknown | False | Unknown |
| `NODE_ENV` | Unknown | Unknown | False | Unknown |

## Ownership
async-communication-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
async-communication-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
async-communication-service limitations evidenced by extraction:
- 1 messaging entit(y/ies) whose topic/queue name is not resolvable from code.

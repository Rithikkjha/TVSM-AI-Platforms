---
service_id: bto-api
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["bto api", "bto_api", "bto"]
---

# bto-api — Overview

## Purpose
Summary: NestJS API with booking info, bookings, reports and sign-in/sign-up endpoints; README is the default Nest template, so the BTO business purpose is not documented.
Also known as: bto api, bto_api, bto
bto-api is a `backend-api` repository (`bto_api`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: Description — $ yarn install.

## Users and Consumers
bto-api is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
bto-api capabilities derived from code:
- `BookingController`: 2 HTTP endpoint(s)
- `AuthController`: 2 HTTP endpoint(s)
- `ReportController`: 1 HTTP endpoint(s)

## Tech Stack
bto-api tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | nest | Unknown |
| Data | mssql | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | Unknown (build: nest,node) | Unknown |

Key libraries: `@nestjs/cli`, `@nestjs/common`, `@nestjs/config`, `@nestjs/core`, `@nestjs/jwt`, `@nestjs/passport`, `@nestjs/platform-express`, `@nestjs/schematics`, `@nestjs/swagger`, `@nestjs/testing`, `@prisma/client`, `@types/express`, `@types/jest`, `@types/node`, `@types/passport-jwt`, `@types/supertest`, `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`, `argon2`, `class-transformer`, `class-validator`, `dotenv`, `eslint`, `eslint-config-prettier`, `eslint-plugin-prettier`, `jest`, `nest-winston`, `pactum`, `passport`, `passport-jwt` …

## Dependencies at a Glance
Upstream (calls bto-api): Unknown
Downstream (bto-api calls): none resolved
Brokers: none. Data stores: `env:DATABASE_URL` (mssql, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
bto-api environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Unknown | Unknown | from config/infra file names |

## Environment Variables
bto-api configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Unknown | Unknown | False | Unknown |
| `JWT_SECRET` | Unknown | Unknown | True | Unknown |
| `PORT` | Unknown | Unknown | False | Unknown |

## Ownership
bto-api ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
bto-api local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
bto-api limitations evidenced by extraction:
- No inbound callers resolved in the registry.

---
service_id: booking-crud-services
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["booking service", "booking crud services", "bookings", "booking", "booking crud", "booking crud service", "booking services"]
---

# booking-crud-services — Overview

## Purpose
Summary: Centralised Booking Service (NestJS) managing vehicle bookings across TVS platforms and third parties via 13 booking endpoints, Azure Service Bus events and Juspay payments.
Also known as: booking service, booking crud services, bookings, booking, booking crud, booking crud service, booking services
booking-crud-services is a `backend-api` repository (`booking-crud-services`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: Booking Service — The Booking Service is a centralized system for managing bookings across various platforms used by TVS Motor Company. This service integrates with TVSM managed services(dealer systems, website, etc.) and third party applications, ensuring a unified booking process..

## Users and Consumers
booking-crud-services is called over HTTP by: `cbs-admin-portal`, `tvs-cps-backend`, `tvsm-marketplace-service`. Event consumers of its published messages: none resolved.

## Key Capabilities
booking-crud-services capabilities derived from code:
- `BookingsController`: 13 HTTP endpoint(s)
- Publishes 2 messaging entit(y/ies); consumes 4

## Tech Stack
booking-crud-services tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | nest | Unknown |
| Data | mssql | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: express,nest,node) | Unknown |

Key libraries: `@apollo/server`, `@azure/identity`, `@azure/keyvault-secrets`, `@azure/msal-node`, `@azure/service-bus`, `@nestjs/cache-manager`, `@nestjs/cli`, `@nestjs/common`, `@nestjs/config`, `@nestjs/core`, `@nestjs/platform-express`, `@nestjs/schematics`, `@nestjs/swagger`, `@nestjs/testing`, `@nestjs/typeorm`, `@opentelemetry/api`, `@opentelemetry/api-logs`, `@opentelemetry/auto-instrumentations-node`, `@opentelemetry/exporter-logs-otlp-http`, `@opentelemetry/exporter-trace-otlp-http`, `@opentelemetry/instrumentation-nestjs-core`, `@opentelemetry/resources`, `@opentelemetry/sdk-logs`, `@opentelemetry/sdk-node`, `@opentelemetry/semantic-conventions`, `@types/express`, `@types/jest`, `@types/mime`, `@types/node`, `@types/supertest` …

## Dependencies at a Glance
Upstream (calls booking-crud-services): `cbs-admin-portal`, `tvs-cps-backend`, `tvsm-marketplace-service`
Downstream (booking-crud-services calls): `external:juspay` (hard); plus 1 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `_` (mssql, write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
booking-crud-services environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
booking-crud-services configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `APP_PORT` | Unknown | Unknown | False | Unknown |
| `BAS_DB_CLIENT_ID` | Unknown | Unknown | False | Unknown |
| `BAS_DB_CLIENT_SECRET` | Unknown | Unknown | True | Unknown |
| `BOOKING_SERVICE_CONFIG` | Unknown | Unknown | False | Unknown |
| `BOOKING_SERVICE_DB_CONFIG` | Unknown | Unknown | False | Unknown |
| `DEPLOYMENT_ENVIRONMENT` | Unknown | Unknown | False | Unknown |
| `NODE_ENV` | Unknown | Unknown | False | Unknown |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Unknown | Unknown | False | Unknown |
| `OTEL_LOG_LEVEL` | Unknown | Unknown | False | Unknown |
| `OTEL_SERVICE_NAME` | Unknown | Unknown | False | Unknown |
| `SERVICE_VERSION` | Unknown | Unknown | False | Unknown |

## Ownership
booking-crud-services ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
booking-crud-services local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
booking-crud-services limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- 6 messaging entit(y/ies) whose topic/queue name is not resolvable from code.

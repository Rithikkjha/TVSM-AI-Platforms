---
service_id: catalog-scheduler
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["catalog scheduler", "ccp catalog service scheduler"]
---

# catalog-scheduler — Overview

## Purpose
Summary: Timer-triggered jobs that ingest product prices and merchandise/accessories into the catalogue, calling core-commerce-platform-api-service and the price engine and publishing one message.
Also known as: catalog scheduler, ccp catalog service scheduler
catalog-scheduler is a `function` repository (`Catalog-Scheduler`; service.yaml `type: function`). Business purpose: README (`README.md`) describes it as: README #.

## Users and Consumers
catalog-scheduler is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
catalog-scheduler capabilities derived from code:
- Scheduled job `merchandise-accessories-ingestion-job` (timer-trigger `None`)
- Scheduled job `product-price-ingestion-job` (timer-trigger `None`)
- Publishes 1 messaging entit(y/ies); consumes 0

## Tech Stack
catalog-scheduler tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | JavaScript | Unknown |
| Framework | node | Unknown |
| Data | mongo | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | Unknown (build: node) | Unknown |

Key libraries: `@azure/functions`, `@azure/identity`, `@azure/keyvault-secrets`, `@azure/service-bus`, `axios`, `dotenv`, `lodash`, `mongodb`, `nodemon`

## Dependencies at a Glance
Upstream (calls catalog-scheduler): Unknown
Downstream (catalog-scheduler calls): `core-commerce-platform-api-service` (hard), `price-engine-micro-service-backend` (hard); plus 4 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `env:DB_HOST` (mongo, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
catalog-scheduler environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| local | Unknown | from config/infra file names |

## Environment Variables
catalog-scheduler configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `AUTHORIZATION_TOKEN_URL` | Unknown | Unknown | True | Unknown |
| `AzureWebJobsFeatureFlags` | Unknown | Unknown | False | app-settings |
| `AzureWebJobsStorage` | Unknown | Unknown | False | app-settings |
| `CATALOG_BASE_URL` | points to core-commerce-platform-api-service | Unknown | False | Unknown |
| `CRON_EXPRESSION_FOR_MERCHANDISE_ACCESSORIES_INGESTION_JOB` | Unknown | Unknown | False | Unknown |
| `CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB` | Unknown | Unknown | False | Unknown |
| `DB_HOST` | Unknown | Unknown | False | Unknown |
| `DB_NAME` | Unknown | Unknown | False | Unknown |
| `FUNCTIONS_WORKER_RUNTIME` | Unknown | Unknown | False | app-settings |
| `IsEncrypted` | Unknown | Unknown | False | app-settings |
| `KEY_VAULT_NAME` | Unknown | Unknown | True | Unknown |
| `MERCHANDISE_ACCESSORIES_BASE_URL` | Unknown | Unknown | False | Unknown |
| `PRICE_URL` | points to price-engine-micro-service-backend | Unknown | False | Unknown |
| `PRODUCT_MASTER_SUBSCRIPTION` | Unknown | Unknown | False | Unknown |
| `PRODUCT_MASTER_TOPIC` | Unknown | Unknown | False | Unknown |
| `SERVICE_BUS_ENDPOINT` | Unknown | Unknown | False | Unknown |
| `SERVICE_BUS_MESSAGE_COUNT` | Unknown | Unknown | False | Unknown |
| `SERVICE_BUS_TOPIC_NAME` | Unknown | Unknown | False | Unknown |
| `extensionBundle:id` | Unknown | Unknown | False | app-settings |
| `extensionBundle:version` | Unknown | Unknown | False | app-settings |
| `functionTimeout` | Unknown | Unknown | False | app-settings |
| `logging:applicationInsights:samplingSettings:excludedTypes` | Unknown | Unknown | False | app-settings |
| `logging:applicationInsights:samplingSettings:isEnabled` | Unknown | Unknown | False | app-settings |
| `version` | Unknown | Unknown | False | app-settings |

## Ownership
catalog-scheduler ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
catalog-scheduler local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
catalog-scheduler limitations evidenced by extraction:
- 4 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- 1 messaging entit(y/ies) whose topic/queue name is not resolvable from code.

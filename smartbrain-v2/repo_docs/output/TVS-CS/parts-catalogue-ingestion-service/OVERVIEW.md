---
service_id: parts-catalogue-ingestion-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["parts catalogue ingestion service", "ingestion service", "multi source ingestion", "parts catalogue ingestion", "ingestion"]
---

# parts-catalogue-ingestion-service — Overview

## Purpose
Summary: Spring Boot service ingesting parts catalogue data from external APIs into NebulaGraph and OpenSearch; no HTTP endpoints or jobs were extracted.
Also known as: parts catalogue ingestion service, ingestion service, multi source ingestion, parts catalogue ingestion, ingestion
parts-catalogue-ingestion-service is a `Unknown` repository (`Parts-Catalogue-Ingestion-Service`; service.yaml `type: None`). Business purpose: README (`README.md`) describes it as: Parts Catalogue Ingestion Service — A Spring Boot microservice for ingesting parts catalogue data from external APIs and storing it in Nebula Graph database and OpenSearch for search capabilities..

## Users and Consumers
parts-catalogue-ingestion-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
parts-catalogue-ingestion-service capabilities derived from code:
- Unknown — no endpoints, jobs or messaging extracted

## Tech Stack
parts-catalogue-ingestion-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | java | Unknown |
| Data | nebula, opensearch | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `ch.qos.logback:logback-classic`, `ch.qos.logback:logback-core`, `com.alibaba:fastjson`, `com.fasterxml.jackson.core:jackson-core`, `com.fasterxml.jackson.core:jackson-databind`, `com.fasterxml.jackson.datatype:jackson-datatype-jsr310`, `com.squareup.okhttp3:okhttp`, `com.squareup.okio:okio`, `com.vesoft:client`, `io.micrometer:micrometer-core`, `org.bouncycastle:bcprov-jdk18on`, `org.eclipse.parsson:parsson`, `org.opensearch.client:opensearch-java`, `org.opensearch.client:opensearch-rest-client`, `org.projectlombok:lombok`, `org.springframework.boot:spring-boot-configuration-processor`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.cloud:spring-cloud-starter-circuitbreaker-resilience4j`

## Dependencies at a Glance
Upstream (calls parts-catalogue-ingestion-service): Unknown
Downstream (parts-catalogue-ingestion-service calls): none resolved; plus 4 outbound call(s) with unresolved target
Brokers: none. Data stores: `config:nebula.graph.space` (nebula, read-write), `config:opensearch.host` (opensearch, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
parts-catalogue-ingestion-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
parts-catalogue-ingestion-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).
156 keys total; table lists secret/externally-provided/pointer keys (10). Key counts by prefix: `price` 42, `catalogue` 29, `resilience4j` 25, `opensearch` 17, `warranty` 11, `nebula` 10, `ingestion` 8, `logging` 5, `async` 4, `azure` 3, `spring` 2.

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `azure.blob.account-key` | Unknown | Unknown | True | app-settings |
| `catalogue.api.mdp.client-secret` | Unknown | True | True | app-settings |
| `catalogue.api.mdp.token-url` | Unknown | True | True | app-settings |
| `catalogue.api.norton.api-key` | Unknown | Unknown | True | app-settings |
| `catalogue.api.price.api-key` | Unknown | Unknown | True | app-settings |
| `catalogue.api.tvs.api-key` | Unknown | Unknown | True | app-settings |
| `nebula.graph.password` | Unknown | True | True | app-settings |
| `opensearch.password` | Unknown | True | True | app-settings |
| `resilience4j.retry.instances.catalogueApi.retry-exceptions` | Unknown | Unknown | True | app-settings |
| `resilience4j.retry.instances.mdpApi.retry-exceptions` | Unknown | Unknown | True | app-settings |

## Ownership
parts-catalogue-ingestion-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
parts-catalogue-ingestion-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
parts-catalogue-ingestion-service limitations evidenced by extraction:
- 4 outbound HTTP call(s) have no resolved target service (base URL from config/env).

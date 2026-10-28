---
service_id: parts-catalogue-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["product catalogue", "product catalogue service", "parts catalogue service", "parts catalogue"]
---

# parts-catalogue-service — Overview

## Purpose
Summary: Spring Boot Product Catalogue Service serving product catalogues, parts and hierarchical relationships from NebulaGraph with OpenSearch full-text search.
Also known as: product catalogue, product catalogue service, parts catalogue service, parts catalogue
parts-catalogue-service is a `backend-api` repository (`Parts-Catalogue-Service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: Product Catalogue Service — A Spring Boot microservice that gives product catalogues, parts inventory, and hierarchical relationships using graph databases. This service integrates with NebulaGraph for graph-based queries and OpenSearch for advanced full-text search capabilities..

## Users and Consumers
parts-catalogue-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
parts-catalogue-service capabilities derived from code:
- `EntitiesController`: 6 HTTP endpoint(s)
- `ChartController`: 4 HTTP endpoint(s)
- `ProductDetailsController`: 2 HTTP endpoint(s)
- `EpcController`: 2 HTTP endpoint(s)
- `TraversalController`: 1 HTTP endpoint(s)
- `SearchController`: 1 HTTP endpoint(s)
- `ProductDetailsControllerV2`: 1 HTTP endpoint(s)
- `TraversalControllerV2`: 1 HTTP endpoint(s)
- `SearchControllerV2`: 1 HTTP endpoint(s)

## Tech Stack
parts-catalogue-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | nebula, opensearch | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `ch.qos.logback:logback-classic`, `ch.qos.logback:logback-core`, `com.alibaba:fastjson`, `com.azure:azure-storage-blob`, `com.fasterxml.jackson.core:jackson-core`, `com.fasterxml.jackson.core:jackson-databind`, `com.fasterxml.jackson.datatype:jackson-datatype-jsr310`, `com.github.ben-manes.caffeine:caffeine`, `com.squareup.okhttp3:okhttp`, `com.squareup.okio:okio`, `com.vesoft:client`, `io.netty:netty-codec`, `io.netty:netty-codec-http`, `io.netty:netty-codec-http2`, `org.apache.tomcat.embed:tomcat-embed-core`, `org.apache.tomcat.embed:tomcat-embed-el`, `org.apache.tomcat.embed:tomcat-embed-websocket`, `org.bouncycastle:bcprov-jdk18on`, `org.eclipse.parsson:parsson`, `org.opensearch.client:opensearch-java`, `org.opensearch.client:opensearch-rest-client`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-configuration-processor`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-aop`, `org.springframework.boot:spring-boot-starter-cache`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-validation` …

## Dependencies at a Glance
Upstream (calls parts-catalogue-service): Unknown
Downstream (parts-catalogue-service calls): none resolved
Brokers: none. Data stores: `parts_catalogue_graph` (nebula, read), `config:opensearch.host` (opensearch, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
parts-catalogue-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
parts-catalogue-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `async.executor.core-pool-size` | Unknown | Unknown | False | app-settings |
| `async.executor.max-pool-size` | Unknown | Unknown | False | app-settings |
| `async.executor.queue-capacity` | Unknown | Unknown | False | app-settings |
| `async.executor.thread-name-prefix` | Unknown | Unknown | False | app-settings |
| `azure.blob.cache-max-size` | Unknown | True | False | app-settings |
| `azure.blob.cache-ttl-minutes` | Unknown | True | False | app-settings |
| `azure.blob.catalogue-prefix` | Unknown | True | False | app-settings |
| `azure.blob.connectionString` | Unknown | True | True | Unknown |
| `azure.blob.container-name` | Unknown | True | False | app-settings |
| `azure.blob.image-prefix` | Unknown | True | False | app-settings |
| `azure.blob.sas-expiry-minutes` | Unknown | True | True | app-settings |
| `batch.operation-timeout-ms` | Unknown | True | False | app-settings |
| `cache.hierarchyTtlMinutes` | Unknown | True | False | Unknown |
| `cache.maxHierarchySize` | Unknown | True | False | Unknown |
| `cache.maxNodeSize` | Unknown | True | False | Unknown |
| `cache.maxSearchSize` | Unknown | True | False | Unknown |
| `cache.nodeTtlMinutes` | Unknown | True | False | Unknown |
| `cache.searchTtlMinutes` | Unknown | True | False | Unknown |
| `logging.level.com.vesoft.nebula` | Unknown | Unknown | False | app-settings |
| `logging.level.io.github.resilience4j` | Unknown | Unknown | False | app-settings |
| `logging.level.org.com.graph` | Unknown | Unknown | False | app-settings |
| `logging.level.org.opensearch.client` | Unknown | Unknown | False | app-settings |
| `logging.pattern.console` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `management.health.circuitbreakers.enabled` | Unknown | Unknown | False | app-settings |
| `nebula.hosts` | Unknown | True | False | Unknown |
| `nebula.idle-time-ms` | Unknown | True | False | app-settings |
| `nebula.max-conn-size` | Unknown | True | False | app-settings |
| `nebula.min-conn-size` | Unknown | True | False | app-settings |
| `nebula.password` | Unknown | True | True | Unknown |
| `nebula.port` | Unknown | True | False | Unknown |
| `nebula.reconnect` | Unknown | True | False | app-settings |
| `nebula.space` | Unknown | True | False | Unknown |
| `nebula.timeout-ms` | Unknown | True | False | app-settings |
| `nebula.username` | Unknown | True | False | Unknown |
| `opensearch.brandCataloguesIndex` | Unknown | True | False | Unknown |
| `opensearch.bulk-size` | Unknown | True | False | app-settings |
| `opensearch.connection-timeout-ms` | Unknown | True | False | app-settings |
| `opensearch.hierarchiesIndex` | Unknown | True | False | Unknown |
| `opensearch.host` | Unknown | True | False | Unknown |
| `opensearch.number-of-replicas` | Unknown | True | False | app-settings |
| `opensearch.number-of-shards` | Unknown | True | False | app-settings |
| `opensearch.partsIndex` | Unknown | True | False | Unknown |
| `opensearch.password` | Unknown | True | True | Unknown |
| `opensearch.port` | Unknown | True | False | Unknown |
| `opensearch.pricesIndex` | Unknown | True | False | Unknown |
| `opensearch.scheme` | Unknown | True | False | app-settings |
| `opensearch.socket-timeout-ms` | Unknown | True | False | app-settings |
| `opensearch.use-ssl` | Unknown | True | False | app-settings |
| `opensearch.username` | Unknown | True | False | Unknown |
| `opensearch.verify-ssl` | Unknown | True | False | app-settings |
| `opensearch.warrantiesIndex` | Unknown | True | False | Unknown |
| `resilience4j.circuitbreaker.instances.azureBlobCircuitBreaker.failure-rate-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.azureBlobCircuitBreaker.permitted-number-of-calls-in-half-open-state` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.azureBlobCircuitBreaker.record-exceptions` | Unknown | Unknown | True | app-settings |
| `resilience4j.circuitbreaker.instances.azureBlobCircuitBreaker.sliding-window-size` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.azureBlobCircuitBreaker.sliding-window-type` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.azureBlobCircuitBreaker.wait-duration-in-open-state` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.automatic-transition-from-open-to-half-open-enabled` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.failure-rate-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.permitted-number-of-calls-in-half-open-state` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.record-exceptions` | Unknown | Unknown | True | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.register-health-indicator` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.sliding-window-size` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.sliding-window-type` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.slow-call-duration-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.slow-call-rate-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.nebulaCircuitBreaker.wait-duration-in-open-state` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.automatic-transition-from-open-to-half-open-enabled` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.failure-rate-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.permitted-number-of-calls-in-half-open-state` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.record-exceptions` | Unknown | Unknown | True | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.register-health-indicator` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.sliding-window-size` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.sliding-window-type` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.slow-call-duration-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.slow-call-rate-threshold` | Unknown | Unknown | False | app-settings |
| `resilience4j.circuitbreaker.instances.opensearchCircuitBreaker.wait-duration-in-open-state` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.azureBlobRetry.enable-exponential-backoff` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.azureBlobRetry.exponential-backoff-multiplier` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.azureBlobRetry.max-attempts` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.azureBlobRetry.retry-exceptions` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.azureBlobRetry.wait-duration` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.nebulaRetry.enable-exponential-backoff` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.nebulaRetry.exponential-backoff-multiplier` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.nebulaRetry.max-attempts` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.nebulaRetry.retry-exceptions` | Unknown | Unknown | True | app-settings |
| `resilience4j.retry.instances.nebulaRetry.wait-duration` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.opensearchRetry.enable-exponential-backoff` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.opensearchRetry.exponential-backoff-multiplier` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.opensearchRetry.max-attempts` | Unknown | Unknown | False | app-settings |
| `resilience4j.retry.instances.opensearchRetry.retry-exceptions` | Unknown | Unknown | True | app-settings |
| `resilience4j.retry.instances.opensearchRetry.wait-duration` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `tenant.allowed-ids` | Unknown | True | False | app-settings |

## Ownership
parts-catalogue-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
parts-catalogue-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
parts-catalogue-service limitations evidenced by extraction:
- No inbound callers resolved in the registry.

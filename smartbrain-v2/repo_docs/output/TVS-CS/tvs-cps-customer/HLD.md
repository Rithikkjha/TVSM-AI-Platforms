---
service_id: tvs-cps-customer
doc_type: hld
last_reviewed: 2026-10-11
---

# tvs-cps-customer — High-Level Design

## Context
tvs-cps-customer is a `backend-api` in the TVS-CS org (domain: Unknown). Neighbours: callers `tvs-cps-backend`; downstream none resolved.

## Architecture
tvs-cps-customer components and connections (from service.yaml):

```mermaid
flowchart LR
  svc["tvs-cps-customer"]
  in_tvs_cps_backend["tvs-cps-backend"] --> svc
  svc --> db0[("customer")]
```

## Integration Points
tvs-cps-customer registry edges (9):

| Direction | Peer | Kind | Via | Criticality | Source | Match |
|---|---|---|---|---|---|---|
| in | `tvs-cps-backend` | http | POST /api/v1/customer/add-vehicle | hard | code | path-unique |
| in | `tvs-cps-backend` | http | POST /api/v1/customer/create | hard | code | path-unique |
| in | `tvs-cps-backend` | http | POST /api/v1/customer/delete | hard | code | path-unique |
| in | `tvs-cps-backend` | http | POST /api/v1/customer/external/search | hard | code | path-unique |
| in | `tvs-cps-backend` | http | POST /api/v1/customer/search | hard | code | path-unique |
| in | `tvs-cps-backend` | http | POST /api/v1/customer/update | hard | code | path-unique |
| in | `tvs-cps-backend` | http | POST /api/v1/vehiclesearch | hard | code | path-unique |
| out | `tvs-cps-be-base-framework` | library_dependency | com.tvsm:tvsm-be-core | hard | code | artifact |
| out | `tvs-cps-be-base-framework` | library_dependency | com.tvsm:tvsm-be-starter-parent | hard | code | artifact |

## Data Ownership
tvs-cps-customer data stores (service.yaml `data_stores`; ownership flag not determinable unless set):

| Store | Type | Access | Owned | Key entities |
|---|---|---|---|---|
| `customer` | postgres | read-write | Unknown | Customer, CustomerAddress, CustomerAudit, CustomerDealerMapping, CustomerVehicle |

## Key Design Decisions
tvs-cps-customer: N/A — not determinable from code.

| Decision | Alternatives considered | Reason |
|---|---|---|
| Unknown | Unknown | Unknown |

## Non-Functional Requirements
tvs-cps-customer NFR targets: N/A — not determinable from code. Tuning-related config keys: `app.rest.timeout.connect`, `app.rest.timeout.read`, `tvsm.core.multitenant.datasource.default-data-source.maximum-pool-size`.

## Security
tvs-cps-customer security: endpoint auth values None. Auth code: `src/main/java/com/tvsm/customer/audit/AuditContextFilter.java:10`. 1 secret config key(s), sourced via: {'app-settings': 1} (names in OVERVIEW.md). PII handling: Unknown.

## Resilience and Failure Modes
tvs-cps-customer hard dependencies: none resolved. No retry/circuit-breaker code found; failure behaviour Unknown.

## Deployment Topology
tvs-cps-customer deployment artefacts (platform/regions: Unknown unless listed):

| Kind | Name | File | Environments | Image | Ports | Variable groups |
|---|---|---|---|---|---|---|
| azure-pipeline | AST_cps_customer_prod_Pipeline.yml | `AST_cps_customer_prod_Pipeline.yml:1` | - | - | - | PROD_Threshold, Tenable |
| azure-pipeline | AST_cps_customer_uat_Pipeline.yml | `AST_cps_customer_uat_Pipeline.yml:1` | - | - | - | Checkmarx_Common, Tenable, UAT_Threshold |
| azure-pipeline | ast-image-scan.yaml | `ast-image-scan.yaml:1` | - | - | - | Checkmarx_Common, UAT_Threshold |
| azure-pipeline | cd-pipeline.yaml | `cd-pipeline.yaml:1` | dev | - | - | - |
| azure-pipeline | ci-pipeline.yaml | `ci-pipeline.yaml:2` | - | - | - | - |
| azure-pipeline | sonar_ci.yml | `sonar_ci.yml:1` | - | - | - | - |
| azure-pipeline | uk-cd-pipeline.yaml | `uk-cd-pipeline.yaml:1` | dev, prod, uat | - | - | - |
| azure-pipeline | uk-training-cd-pipeline.yaml | `uk-training-cd-pipeline.yaml:1` | training | - | - | - |
| dockerfile | Dockerfile | `Dockerfile:4` | - | tvsmazcmnsvcacrdev01.azurecr.io/tvs-cs/tvs-cps-be-base-framework:41532-d25ff29, amazoncorretto:26.0.2-al2023-headful | 8080 | - |

## Observability
tvs-cps-customer observability libraries: `org.springframework.boot:spring-boot-starter-actuator`. Related config keys: `logging.level.com.tvsm.core`, `logging.level.com.tvsm.customer`, `logging.pattern.console`, `logging.pattern.file`, `management.endpoint.health.show-details`, `management.endpoints.web.exposure.include`. Dashboards/alerts: Unknown.

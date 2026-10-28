---
service_id: tvs-cps-billing
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-billing — High-Level Code

## Application Overview
tvs-cps-billing (`TVS-CPS-BILLING`) is a `backend-api` codebase; stacks java; head `9d0dd407d65ef3cbb650986f57a0f2f46a6ca7af`.
Entry points: `src/main/java/com/tvsm/billing/TVSCPSBillingApplication.java`.

## Module Summary
tvs-cps-billing modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 8 endpoints, 3 outbound calls, 0 messaging, 1 data-access |

## Folder Structure
tvs-cps-billing top-level folders (3 levels):

```
TVS-CPS-BILLING/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvs-cps-billing workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### BillingController
1. `src/main/java/com/tvsm/billing/controller/BillingController.java` receives 6 route(s), e.g. `GET /api/v1/billing/get/{invoiceNumber}` → `BillingController.getInvoiceByNumber`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/billing/entity/Invoice.java:18`.

### HealthController
1. `src/main/java/com/tvsm/billing/controller/HealthController.java` receives 1 route(s), e.g. `GET /api/health` → `HealthController.health`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/billing/entity/Invoice.java:18`.

### BillingReportController
1. `src/main/java/com/tvsm/billing/controller/BillingReportController.java` receives 1 route(s), e.g. `POST /api/v1/billing/report/invoice-list` → `BillingReportController.getInvoiceReport`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/billing/entity/Invoice.java:18`.

## Integration Clients
tvs-cps-billing outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/test/java/com/tvsm/billing/util/ApiPassthroughUtilTest.java` | literal |
| data store (billing_db) | `src/main/java/com/tvsm/billing/entity/Invoice.java:18` | Unknown |

## Cross-Cutting Concerns
tvs-cps-billing cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-billing build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_cps_billing_prod_Pipeline.yml:1`, `AST_cps_billing_uat_Pipeline.yml:1`, `ast-image-scan.yaml:1`, `ci-pipeline.yaml:1`, `sonar_ci.yml:1`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`

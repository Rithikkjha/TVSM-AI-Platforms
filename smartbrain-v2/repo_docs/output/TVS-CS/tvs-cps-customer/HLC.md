---
service_id: tvs-cps-customer
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-customer — High-Level Code

## Application Overview
tvs-cps-customer (`TVS-CPS-CUSTOMER`) is a `backend-api` codebase; stacks java; head `5ff4ceb070ad731f016c87a5f0a68d537ebd63e8`.
Entry points: `src/main/java/com/tvsm/customer/CustomerServiceApplication.java`.

## Module Summary
tvs-cps-customer modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 9 endpoints, 0 outbound calls, 0 messaging, 1 data-access |

## Folder Structure
tvs-cps-customer top-level folders (3 levels):

```
TVS-CPS-CUSTOMER/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvs-cps-customer workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### CustomerController
1. `src/main/java/com/tvsm/customer/controller/CustomerController.java` receives 5 route(s), e.g. `POST /api/v1/customer/add-vehicle` → `CustomerController.addVehicleToCustomer`.
3. Module `.` data access via `src/main/java/com/tvsm/customer/entity/Customer.java:15`.

### ExternalCustomerController
1. `src/main/java/com/tvsm/customer/controller/ExternalCustomerController.java` receives 3 route(s), e.g. `POST /api/v1/customer/external/create` → `ExternalCustomerController.createCustomer`.
3. Module `.` data access via `src/main/java/com/tvsm/customer/entity/Customer.java:15`.

### VehicleSearchController
1. `src/main/java/com/tvsm/customer/controller/VehicleSearchController.java` receives 1 route(s), e.g. `POST /api/v1/vehiclesearch` → `VehicleSearchController.searchCustomersByVehicle`.
3. Module `.` data access via `src/main/java/com/tvsm/customer/entity/Customer.java:15`.

## Integration Clients
tvs-cps-customer outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| data store (customer) | `src/main/java/com/tvsm/customer/entity/Customer.java:15` | Unknown |

## Cross-Cutting Concerns
tvs-cps-customer cross-cutting code:
- Auth: `src/main/java/com/tvsm/customer/audit/AuditContextFilter.java:10` (OncePerRequestFilter)
- Error handling: none found
- Validation: 5 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-customer build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_cps_customer_prod_Pipeline.yml:1`, `AST_cps_customer_uat_Pipeline.yml:1`, `ast-image-scan.yaml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:2`, `sonar_ci.yml:1`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`

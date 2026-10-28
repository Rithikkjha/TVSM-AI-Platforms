---
service_id: tvs-cps-inventory
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-inventory — High-Level Code

## Application Overview
tvs-cps-inventory (`TVS-CPS-INVENTORY`) is a `backend-api` codebase; stacks java; head `07bd50afb5809e02d46e7383e32b95d0d4f7c1cb`.
Entry points: `src/main/java/com/tvsm/inventory/TVSCPSInventoryApplication.java`.

## Module Summary
tvs-cps-inventory modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 25 endpoints, 2 outbound calls, 0 messaging, 1 data-access |

## Folder Structure
tvs-cps-inventory top-level folders (3 levels):

```
TVS-CPS-INVENTORY/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvs-cps-inventory workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### VehicleController
1. `src/main/java/com/tvsm/inventory/controller/VehicleController.java` receives 8 route(s), e.g. `GET /api/v1/vehicle/global/get-by-vin/{vin}` → `VehicleController.getVehicleByVin`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### InventoryController
1. `src/main/java/com/tvsm/inventory/controller/InventoryController.java` receives 5 route(s), e.g. `GET /api/v1/inventory/accumulated-stock/{productCatalogId}` → `InventoryController.getAccumulatedStock`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### ExternalVehicleController
1. `src/main/java/com/tvsm/inventory/controller/ExternalVehicleController.java` receives 2 route(s), e.g. `GET /api/v1/external/vehicle/global/get-by-vin/{vin}` → `ExternalVehicleController.getVehicleByVin`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### BinController
1. `src/main/java/com/tvsm/inventory/controller/BinController.java` receives 2 route(s), e.g. `GET /api/v1/inventory/bin/get` → `BinController.getBins`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### LocationController
1. `src/main/java/com/tvsm/inventory/controller/LocationController.java` receives 2 route(s), e.g. `GET /api/v1/inventory/location/get` → `LocationController.getLocation`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### RackController
1. `src/main/java/com/tvsm/inventory/controller/RackController.java` receives 2 route(s), e.g. `GET /api/v1/inventory/rack/get` → `RackController.getDefaultRacks`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### InventoryDashboardController
1. `src/main/java/com/tvsm/inventory/controller/InventoryDashboardController.java` receives 2 route(s), e.g. `POST /system/api/v1/inventory/analytics/list` → `InventoryDashboardController.getProductCatalogCountGrouped`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### HealthController
1. `src/main/java/com/tvsm/inventory/controller/HealthController.java` receives 1 route(s), e.g. `GET /api/health` → `HealthController.health`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

### VehicleReportController
1. `src/main/java/com/tvsm/inventory/controller/VehicleReportController.java` receives 1 route(s), e.g. `POST /api/v1/inventory/report/vehicle-stock-report-list` → `VehicleReportController.getVehicleStockReportList`.
2. Module `.` makes outbound calls to: `Unknown(literal)`.
3. Module `.` data access via `src/main/java/com/tvsm/inventory/entity/Bin.java:14`.

## Integration Clients
tvs-cps-inventory outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/test/java/com/tvsm/inventory/util/ApiPassthroughUtilTest.java` | literal |
| data store (inventory_db) | `src/main/java/com/tvsm/inventory/entity/Bin.java:14` | Unknown |

## Cross-Cutting Concerns
tvs-cps-inventory cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-inventory build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_cps_inventory_prod_Pipeline.yml:1`, `AST_cps_inventory_uat_Pipeline.yml:1`, `ast-image-scan.yaml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar_ci.yml:1`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`

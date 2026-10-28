---
service_id: tvs-cps-jobs
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-jobs — High-Level Code

## Application Overview
tvs-cps-jobs (`TVS-CPS-JOBS`) is a `backend-api` codebase; stacks java; head `d490cdc6ef697d327287aa7f5acf187a4c8631af`.
Entry points: `src/main/java/com/tvsm/jobs/TVSCPSJobsApplication.java`.

## Module Summary
tvs-cps-jobs modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 3 endpoints, 7 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
tvs-cps-jobs top-level folders (3 levels):

```
TVS-CPS-JOBS/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
│   │   ├── resources/
```

## Core Workflows in Code
tvs-cps-jobs workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### CronJobsController
1. `src/main/java/com/tvsm/jobs/controller/CronJobsController.java` receives 2 route(s), e.g. `POST /api/v1/cron-jobs/fetch-invoices` → `CronJobsController.fetchInvoices`.
2. Module `.` makes outbound calls to: `Unknown(config:azure-datalake.api-url)`, `Unknown(config:tvs-cps-backend.base-url)`, `Unknown(literal)`, `tvs-cps-backend`.

### HealthController
1. `src/main/java/com/tvsm/jobs/controller/HealthController.java` receives 1 route(s), e.g. `GET /api/health` → `HealthController.health`.
2. Module `.` makes outbound calls to: `Unknown(config:azure-datalake.api-url)`, `Unknown(config:tvs-cps-backend.base-url)`, `Unknown(literal)`, `tvs-cps-backend`.

### Job CronJobScheduler.allBookingsScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:108` runs on cron `0 8 0 * * *`.

### Job CronJobScheduler.allEnquiriesScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:118` runs on cron `0 11 0 * * *`.

### Job CronJobScheduler.testRidesMissedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:128` runs on cron `0 14 0 * * *`.

### Job CronJobScheduler.unassignedEnquiriesScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:138` runs on cron `0 17 0 * * *`.

### Job CronJobScheduler.followupsMissedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:148` runs on cron `0 20 0 * * *`.

### Job CronJobScheduler.stock90DaysScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:158` runs on cron `0 23 0 * * *`.

### Job CronJobScheduler.retailCountScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:168` runs on cron `0 26 0 * * *`.

### Job CronJobScheduler.vehiclesPendingPdiScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:178` runs on cron `0 29 0 * * *`.

### Job CronJobScheduler.averageStockDaysScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:188` runs on cron `0 32 0 * * *`.

### Job CronJobScheduler.availableStockScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:198` runs on cron `0 35 0 * * *`.

### Job CronJobScheduler.vehicleOrderTatScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:208` runs on cron `0 41 0 * * *`.

### Job CronJobScheduler.partsOrderTatScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:218` runs on cron `0 38 0 * * *`.

### Job CronJobScheduler.orderStatusSyncJobScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:22` runs on cron `0 0 9,21 * * *`.

### Job CronJobScheduler.vehicleOrder60Scheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:228` runs on cron `0 44 0 * * *`.

### Job CronJobScheduler.vehicleGrnPendingScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:238` runs on cron `0 47 0 * * *`.

### Job CronJobScheduler.partsGrnPendingScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:248` runs on cron `0 50 0 * * *`.

### Job CronJobScheduler.vehicleOrderPendingGrnScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:258` runs on cron `0 53 0 * * *`.

### Job CronJobScheduler.totalOrderQtyScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:268` runs on cron `0 56 0 * * *`.

### Job CronJobScheduler.partsPurchaseOrderValueScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:278` runs on cron `0 59 0 * * *`.

### Job CronJobScheduler.vehicleOrderSubmittedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:288` runs on cron `0 2 1 * * *`.

### Job CronJobScheduler.vehicleOrderApprovedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:298` runs on cron `0 5 1 * * *`.

### Job CronJobScheduler.vehicleOrderCompletedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:308` runs on cron `0 8 1 * * *`.

### Job CronJobScheduler.vehicleOrderPickedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:318` runs on cron `0 11 1 * * *`.

### Job CronJobScheduler.vehicleOrderDispatchedScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:328` runs on cron `0 14 1 * * *`.

### Job CronJobScheduler.partsStockValueScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:338` runs on cron `0 17 1 * * *`.

### Job CronJobScheduler.pullOrderInvoicesJobScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:39` runs on cron `0 0 2 * * *`.

### Job CronJobScheduler.closeAppointmentJobScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:55` runs on cron `0 0 14 * * *`.

### Job CronJobScheduler.claimSAPSyncJobScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:70` runs on cron `0 */30 * * * *`.

### Job CronJobScheduler.l1DashboardCalculationSyncJobScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:85` runs on cron `0 0 * * * *`.

### Job CronJobScheduler.bookingPendingAllotmentScheduler
1. `src/main/java/com/tvsm/jobs/scheduler/CronJobScheduler.java:98` runs on cron `0 5 0 * * *`.

## Integration Clients
tvs-cps-jobs outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/com/tvsm/jobs/service/DataLakeService.java` | config:azure-datalake.api-url |
| Unknown | `src/main/java/com/tvsm/jobs/service/InvoiceProcessingService.java` | config:tvs-cps-backend.base-url |
| Unknown | `src/test/java/com/tvsm/jobs/service/RestCallServiceTest.java` | literal |
| `tvs-cps-backend` | `src/main/java/com/tvsm/jobs/service/AnalyticsService.java` | config:scheduler.analytics.base-url |
| `tvs-cps-backend` | `src/main/java/com/tvsm/jobs/service/AppointmentService.java`, `src/main/java/com/tvsm/jobs/service/ClaimService.java`, `src/main/java/com/tvsm/jobs/service/L1DashboardService.java` | config:tvs-cps-backend.base-url |

## Cross-Cutting Concerns
tvs-cps-jobs cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-jobs build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_cps_jobs_prod_Pipeline.yml:1`, `ast-image-scan.yaml:1`, `ast_cps_jobs_uat_Pipeline.yml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `pr-build-validation.yaml:1`, `sonar.yaml:1`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`

---
service_id: tvs-cps-jobs
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvs cps jobs", "cron jobs", "cps job", "cps jobs", "job", "jobs", "tvs cps job", "cron job"]
---

# tvs-cps-jobs — Overview

## Purpose
Summary: CPS scheduled jobs (cron) for bookings, enquiries and analytics that call tvs-cps-backend system APIs.
Also known as: tvs cps jobs, cron jobs, cps job, cps jobs, job, jobs, tvs cps job, cron job
tvs-cps-jobs is a `backend-api` repository (`TVS-CPS-JOBS`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: tvs-cps-jobs — Order Service - A TVSM Spring Boot application that has an Order sample.

## Users and Consumers
tvs-cps-jobs is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
tvs-cps-jobs capabilities derived from code:
- `CronJobsController`: 2 HTTP endpoint(s)
- `HealthController`: 1 HTTP endpoint(s)
- Scheduled job `CronJobScheduler.allBookingsScheduler` (cron `0 8 0 * * *`)
- Scheduled job `CronJobScheduler.allEnquiriesScheduler` (cron `0 11 0 * * *`)
- Scheduled job `CronJobScheduler.testRidesMissedScheduler` (cron `0 14 0 * * *`)
- Scheduled job `CronJobScheduler.unassignedEnquiriesScheduler` (cron `0 17 0 * * *`)
- Scheduled job `CronJobScheduler.followupsMissedScheduler` (cron `0 20 0 * * *`)
- Scheduled job `CronJobScheduler.stock90DaysScheduler` (cron `0 23 0 * * *`)
- Scheduled job `CronJobScheduler.retailCountScheduler` (cron `0 26 0 * * *`)
- Scheduled job `CronJobScheduler.vehiclesPendingPdiScheduler` (cron `0 29 0 * * *`)
- Scheduled job `CronJobScheduler.averageStockDaysScheduler` (cron `0 32 0 * * *`)
- Scheduled job `CronJobScheduler.availableStockScheduler` (cron `0 35 0 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderTatScheduler` (cron `0 41 0 * * *`)
- Scheduled job `CronJobScheduler.partsOrderTatScheduler` (cron `0 38 0 * * *`)
- Scheduled job `CronJobScheduler.orderStatusSyncJobScheduler` (cron `0 0 9,21 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrder60Scheduler` (cron `0 44 0 * * *`)
- Scheduled job `CronJobScheduler.vehicleGrnPendingScheduler` (cron `0 47 0 * * *`)
- Scheduled job `CronJobScheduler.partsGrnPendingScheduler` (cron `0 50 0 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderPendingGrnScheduler` (cron `0 53 0 * * *`)
- Scheduled job `CronJobScheduler.totalOrderQtyScheduler` (cron `0 56 0 * * *`)
- Scheduled job `CronJobScheduler.partsPurchaseOrderValueScheduler` (cron `0 59 0 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderSubmittedScheduler` (cron `0 2 1 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderApprovedScheduler` (cron `0 5 1 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderCompletedScheduler` (cron `0 8 1 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderPickedScheduler` (cron `0 11 1 * * *`)
- Scheduled job `CronJobScheduler.vehicleOrderDispatchedScheduler` (cron `0 14 1 * * *`)
- Scheduled job `CronJobScheduler.partsStockValueScheduler` (cron `0 17 1 * * *`)
- Scheduled job `CronJobScheduler.pullOrderInvoicesJobScheduler` (cron `0 0 2 * * *`)
- Scheduled job `CronJobScheduler.closeAppointmentJobScheduler` (cron `0 0 14 * * *`)
- Scheduled job `CronJobScheduler.claimSAPSyncJobScheduler` (cron `0 */30 * * * *`)
- Scheduled job `CronJobScheduler.l1DashboardCalculationSyncJobScheduler` (cron `0 0 * * * *`)
- Scheduled job `CronJobScheduler.bookingPendingAllotmentScheduler` (cron `0 5 0 * * *`)

## Tech Stack
tvs-cps-jobs tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.tvsm:tvsm-be-core`, `com.tvsm:tvsm-be-starter-parent`, `org.mapstruct:mapstruct`, `org.mapstruct:mapstruct-processor`, `org.postgresql:postgresql`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`

## Dependencies at a Glance
Upstream (calls tvs-cps-jobs): Unknown
Downstream (tvs-cps-jobs calls): `tvs-cps-backend` (hard); plus 2 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-jobs environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| test | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvs-cps-jobs configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `app.rest.timeout.connect` | Unknown | Unknown | False | app-settings |
| `app.rest.timeout.read` | Unknown | Unknown | False | app-settings |
| `azure-datalake.api-url` | Unknown | True | False | app-settings |
| `azure-datalake.function-code` | Unknown | True | False | app-settings |
| `azure-datalake.invoice.before.days` | Unknown | True | False | app-settings |
| `azure-datalake.invoice.type` | Unknown | True | False | app-settings |
| `azure-datalake.order-status.batch-size` | Unknown | True | False | app-settings |
| `azure-datalake.table.invoice` | Unknown | True | False | app-settings |
| `azure-datalake.table.order-status` | Unknown | True | False | app-settings |
| `azure.client-id` | Unknown | Unknown | False | app-settings |
| `azure.client-secret` | Unknown | Unknown | True | app-settings |
| `azure.grant-type` | Unknown | Unknown | False | app-settings |
| `azure.scope` | Unknown | Unknown | False | app-settings |
| `azure.token-url` | Unknown | Unknown | True | app-settings |
| `bff.header-forwarding.allowed-headers[0]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[1]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[2]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[3]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[4]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[5]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[6]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[7]` | Unknown | Unknown | False | app-settings |
| `bff.order-service.base-url` | Unknown | Unknown | False | app-settings |
| `default.skip-path` | Unknown | Unknown | False | app-settings |
| `erp.api.bearer.token` | Unknown | Unknown | True | app-settings |
| `erp.api.url` | Unknown | Unknown | False | app-settings |
| `erp.oauth.client.id` | Unknown | Unknown | False | app-settings |
| `erp.oauth.client.secret` | Unknown | Unknown | True | app-settings |
| `erp.oauth.token.url` | Unknown | Unknown | True | app-settings |
| `lead.api.client-id` | Unknown | Unknown | False | app-settings |
| `lead.api.secret-key` | Unknown | Unknown | True | app-settings |
| `lead.api.subscription-key` | Unknown | Unknown | True | app-settings |
| `lead.api.url` | Unknown | Unknown | False | app-settings |
| `logging.level.com.tvsm.jobs` | Unknown | Unknown | False | app-settings |
| `logging.level.com.tvsm.order` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.SQL` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.type.descriptor.sql.BasicBinder` | Unknown | Unknown | False | app-settings |
| `logging.level.org.mockito` | Unknown | Unknown | False | app-settings |
| `logging.level.org.springframework` | Unknown | Unknown | False | app-settings |
| `logging.level.org.springframework.web` | Unknown | Unknown | False | app-settings |
| `logging.pattern.console` | Unknown | Unknown | False | app-settings |
| `logging.pattern.file` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `order-sync-job.batch-size` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-api-path` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-exact-words` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.all-bookings.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.all-enquiries.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.available-stock.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.average-stock-days.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.base-url` | points to tvs-cps-backend | True | False | app-settings |
| `scheduler.analytics.booking-pending-allotment.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.followups-missed.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.parts-grn-pending.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.parts-order-tat.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.parts-purchase-order-value.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.parts-stock-value.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.retail-count.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.stock-90-days.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.test-rides-missed.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.total-order-qty.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.unassigned-enquiries.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-grn-pending.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-60.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-approved.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-completed.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-dispatched.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-pending-grn.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-picked.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-submitted.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicle-order-tat.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.analytics.vehicles-pending-pdi.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.appointment-close-job.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.appointment-close-job.enabled` | Unknown | Unknown | False | app-settings |
| `scheduler.claim-sap-sync-job.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.claim-sap-sync-job.enabled` | Unknown | Unknown | False | app-settings |
| `scheduler.fetch-invoice-job.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.fetch-invoice-job.enabled` | Unknown | Unknown | False | app-settings |
| `scheduler.l1-dashboard-sync-job.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.l1-dashboard-sync-job.enabled` | Unknown | Unknown | False | app-settings |
| `scheduler.order-sync-job.batch-size` | Unknown | Unknown | False | app-settings |
| `scheduler.order-sync-job.cron` | Unknown | Unknown | False | app-settings |
| `scheduler.order-sync-job.enabled` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `service.auth-token.client-id` | Unknown | True | True | app-settings |
| `service.auth-token.client-secret` | Unknown | True | True | app-settings |
| `service.auth-token.enable` | Unknown | True | True | app-settings |
| `service.auth-token.scope` | Unknown | True | True | app-settings |
| `service.auth-token.tenant-id` | Unknown | True | True | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.autoconfigure.exclude[0]` | Unknown | Unknown | False | app-settings |
| `spring.autoconfigure.exclude[1]` | Unknown | Unknown | False | app-settings |
| `spring.jmx.enabled` | Unknown | Unknown | False | app-settings |
| `spring.jpa.database-platform` | Unknown | Unknown | False | app-settings |
| `spring.jpa.hibernate.ddl-auto` | Unknown | Unknown | False | app-settings |
| `spring.jpa.properties.hibernate.format_sql` | Unknown | Unknown | False | app-settings |
| `spring.jpa.show-sql` | Unknown | Unknown | False | app-settings |
| `spring.main.web-application-type` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.path` | Unknown | Unknown | False | app-settings |
| `springdoc.info.description` | Unknown | Unknown | False | app-settings |
| `springdoc.info.title` | Unknown | Unknown | False | app-settings |
| `springdoc.info.version` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |
| `tenant.default-tenant-id` | Unknown | True | False | app-settings |
| `tenant.ids` | Unknown | True | False | app-settings |
| `tvs-cps-backend.base-url` | points to tvs-cps-backend | True | False | app-settings |
| `tvs-cps-backend.data-process.batch-size` | Unknown | True | False | app-settings |
| `tvs-cps-backend.insert-invoice.endpoint` | Unknown | True | False | app-settings |
| `tvs-cps-backend.sales-order-no-list.endpoint` | Unknown | True | False | app-settings |
| `tvs-cps-backend.sync-erp-status.endpoint` | Unknown | True | False | app-settings |
| `tvsm.core.cloud-storage.azure.connection-string` | Unknown | Unknown | True | app-settings |
| `tvsm.core.cloud-storage.azure.container-name` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.provider` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.methodLevel.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.thresholdMs` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[0]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[1]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[2]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.jwt.publicKey.key1` | Unknown | Unknown | True | app-settings |
| `valid` | Unknown | True | False | app-settings |
| `validation.files` | Unknown | Unknown | False | app-settings |

## Ownership
tvs-cps-jobs ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-jobs local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvs-cps-jobs limitations evidenced by extraction:
- 2 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- No inbound callers resolved in the registry.

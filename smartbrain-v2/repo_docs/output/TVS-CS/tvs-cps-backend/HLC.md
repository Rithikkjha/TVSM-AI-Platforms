---
service_id: tvs-cps-backend
doc_type: hlc
last_reviewed: 2026-10-11
---

# TVS-CPS-BACKEND — High-Level Code

## Application Overview

`tvs-cps-backend` is a Java 21 Spring Boot multi-module Maven project; entry point `tvs-cps-app/src/main/java/com/tvsm/cps/backend/TVSCPSBackendApplication.java`; configuration `tvs-cps-app/src/main/resources/config/application.yml`.

## Module Summary

`tvs-cps-backend` modules.

| Module | Path | Responsibility |
|---|---|---|
| tvs-cps-app | `tvs-cps-app` | Runnable Spring Boot application assembling all modules (README.md) |
| common-service | `common-service` | Shared infrastructure (README.md) |
| data-access-service | `data-access-service` | Shared data-access infrastructure (README.md) |
| bff-service | `bff-service` | Backend-for-Frontend aggregation layer (README.md) |
| order-service | `order-service` | Orders domain |
| appointment-service | `appointment-service` | Appointments domain |
| claim-service | `claim-service` | Claims domain |
| workflow-service | `workflow-service` | Workflow domain |
| training-service | `training-service` | Training domain |
| collateral-service | `collateral-service` | Collateral domain |
| announcement-service | `announcement-service` | Announcements domain |
| notification-service | `notification-service` | Notifications domain (module, not the `notification-service` repo) |
| npqr-service | `npqr-service` | NPQR domain |
| lead-allocation | `lead-allocation` | Lead allocation domain |

## Folder Structure

`tvs-cps-backend` top-level layout (generated from the clone; build output dirs omitted).

```
TVS-CPS-BACKEND/
├── announcement-service/
│   └── src/
│       ├── main/
│       └── test/
├── appointment-service/
│   └── src/
│       ├── main/
│       └── test/
├── bff-service/
│   └── src/
│       ├── main/
│       └── test/
├── claim-service/
│   └── src/
│       ├── main/
│       └── test/
├── collateral-service/
│   └── src/
│       ├── main/
│       └── test/
├── common-service/
│   └── src/
│       ├── main/
│       └── test/
├── data-access-service/
│   └── src/
│       ├── main/
│       └── test/
├── lead-allocation/
│   └── src/
│       ├── main/
│       └── test/
├── notification-service/
│   └── src/
│       ├── main/
│       └── test/
├── npqr-service/
│   └── src/
│       ├── main/
│       └── test/
├── order-service/
│   └── src/
│       ├── main/
│       └── test/
├── training-service/
│   └── src/
│       ├── main/
│       └── test/
├── tvs-cps-app/
│   └── src/
│       ├── main/
│       └── test/
├── workflow-service/
│   └── src/
│       ├── main/
│       └── test/
├── AST_cps_app_prod_Pipeline.yml
├── AST_cps_app_uat_Pipeline.yml
├── Dockerfile
├── Notification_BFF_API_Document.md
├── Notification_BFF_Layer_Documentation.docx
├── Notification_BFF_Layer_Documentation.md
├── Notification_Service_LLD.docx
└── Notification_Service_LLD.md
```

## Core Workflows in Code

`tvs-cps-backend` entry points by handler (from inventory).

| Handler class | File | Endpoints |
|---|---|---|
| `OrderBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java` | 27 |
| `OrderController` | `order-service/src/main/java/com/tvsm/order/controller/OrderController.java` | 21 |
| `InventoryBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java` | 19 |
| `CatalogController` | `bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java` | 14 |
| `ClaimController` | `claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java` | 14 |
| `AppointmentController` | `appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java` | 13 |
| `ClaimBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java` | 13 |
| `EnquiryBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java` | 12 |
| `JobcardBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java` | 12 |
| `AppointmentBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java` | 11 |
| `InternalServiceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java` | 11 |
| `AnnouncementController` | `announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java` | 10 |
| `AnnouncementBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | 10 |
| `WorkflowBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java` | 10 |
| `CartBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java` | 9 |
| `CartController` | `order-service/src/main/java/com/tvsm/order/controller/CartController.java` | 9 |
| `BookingBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java` | 8 |
| `GrnBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java` | 8 |
| `CustomerBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java` | 7 |
| `GrnController` | `order-service/src/main/java/com/tvsm/order/controller/GrnController.java` | 7 |
| `BillingBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java` | 6 |
| `TenantConfigController` | `bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java` | 5 |
| `DocController` | `bff-service/src/main/java/com/tvsm/bff/controller/DocController.java` | 5 |
| `LeadAllocationController` | `lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java` | 5 |
| `NotificationCategoryController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java` | 5 |
| `NotificationMessageController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java` | 5 |
| `WorkflowController` | `workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java` | 5 |
| `WorkflowTemplateController` | `workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java` | 5 |
| `TrainingBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java` | 4 |
| `LeadServiceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/LeadServiceBFFController.java` | 4 |
| `NotificationCategoryBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java` | 4 |
| `NotificationMessageBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java` | 4 |
| `NotificationActionConfigController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationActionConfigController.java` | 4 |
| `TrainingController` | `training-service/src/main/java/com/tvsm/training/controller/TrainingController.java` | 4 |
| `DashboardBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/DashboardBFFController.java` | 3 |
| `PermissionBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java` | 3 |
| `WarrantyBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/WarrantyBFFController.java` | 3 |
| `LeadAllocationBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/LeadAllocationBFFController.java` | 3 |
| `NotificationBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/NotificationBFFController.java` | 3 |
| `SmartSearchBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/SmartSearchBFFController.java` | 3 |
| `LeadAllocationSystemController` | `lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationSystemController.java` | 3 |
| `InvoiceController` | `order-service/src/main/java/com/tvsm/order/controller/InvoiceController.java` | 3 |
| `InternalERPServiceController` | `order-service/src/main/java/com/tvsm/order/controller/InternalERPServiceController.java` | 3 |
| `AppointmentSystemController` | `appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentSystemController.java` | 2 |
| `ReportsBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/ReportsBFFController.java` | 2 |
| `InvoiceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/InvoiceBFFController.java` | 2 |
| `LocationMasterController` | `bff-service/src/main/java/com/tvsm/bff/controller/LocationMasterController.java` | 2 |
| `CollateralBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/CollateralBFFController.java` | 2 |
| `NotificationDeviceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationDeviceBFFController.java` | 2 |
| `NotificationEventBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationEventBFFController.java` | 2 |
| `NotificationPreferenceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationPreferenceBFFController.java` | 2 |
| `NpqrBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/NpqrBFFController.java` | 2 |
| `VehicleBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/VehicleBFFController.java` | 2 |
| `CollateralController` | `collateral-service/src/main/java/com/tvsm/collateral/controller/CollateralController.java` | 2 |
| `NotificationDeviceController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationDeviceController.java` | 2 |
| `NotificationPreferenceController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationPreferenceController.java` | 2 |
| `NpqrController` | `npqr-service/src/main/java/com/tvsm/npqr/controller/NpqrController.java` | 2 |
| `ApplicationHealthController` | `tvs-cps-app/src/main/java/com/tvsm/cps/backend/controller/ApplicationHealthController.java` | 2 |
| `AppointmentAnalyticsController` | `appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentAnalyticsController.java` | 1 |
| `ExternalAppointmentController` | `appointment-service/src/main/java/com/tvsm/appointment/controller/ExternalAppointmentController.java` | 1 |
| `AppointmentJobController` | `appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentJobController.java` | 1 |
| `L1DashboardController` | `bff-service/src/main/java/com/tvsm/bff/controller/L1DashboardController.java` | 1 |
| `ChannelPartnerBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/ChannelPartnerBFFController.java` | 1 |
| `UmsBffController` | `bff-service/src/main/java/com/tvsm/bff/controller/UmsBffController.java` | 1 |
| `AppointmentAnalyticsBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentAnalyticsBFFController.java` | 1 |
| `BillingReportController` | `bff-service/src/main/java/com/tvsm/bff/controller/BillingReportController.java` | 1 |
| `CalendarBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/CalendarBFFController.java` | 1 |
| `ClaimAnalyticsBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/ClaimAnalyticsBFFController.java` | 1 |
| `NotificationEventTriggerController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationEventTriggerController.java` | 1 |
| `AnalyticsController` | `bff-service/src/main/java/com/tvsm/bff/controller/AnalyticsController.java` | 1 |
| `InventoryAnalyticsBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/InventoryAnalyticsBFFController.java` | 1 |
| `ClaimAnalyticsController` | `claim-service/src/main/java/com/tvsm/claim/controller/ClaimAnalyticsController.java` | 1 |
| `ClaimJobController` | `claim-service/src/main/java/com/tvsm/claim/controller/ClaimJobController.java` | 1 |
| `NotificationEventConsumerController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationEventConsumerController.java` | 1 |
| `NotificationSeedController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationSeedController.java` | 1 |
| `OrderReportController` | `order-service/src/main/java/com/tvsm/order/controller/OrderReportController.java` | 1 |
| `OrderAnalyticsController` | `order-service/src/main/java/com/tvsm/order/controller/OrderAnalyticsController.java` | 1 |
| `UserAssignmentController` | `workflow-service/src/main/java/com/tvsm/workflow/controller/UserAssignmentController.java` | 1 |
| `UserAssignmentSystemController` | `workflow-service/src/main/java/com/tvsm/workflow/controller/UserAssignmentSystemController.java` | 1 |

### Scheduled job JobScheduler.loadCatalogData

1. Triggered by cron `0 0 0/2 * * *` (from config:catalog.cron.schedule) at `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:111`.

### Scheduled job JobScheduler.retrieveMDPDealers

1. Triggered by cron `0 0 0/2 * * *` (from config:mdp.dealer.cron.schedule) at `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:65`.

### Scheduled job JobScheduler.retrieveMerchandiseStock

1. Triggered by cron `0 0 * * * *` (from config:merchandise.oem-stock.cron.schedule) at `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:80`.

### Scheduled job JobScheduler.warmUpUmsCache

1. Triggered by cron `0 0 */2 * * *` (from config:ums.cache.cron.schedule) at `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:93`.

### Scheduled job NotificationDeviceCleanupScheduler.deactivateStaleDevices

1. Triggered by cron `0 0 2 * * *` (from config:notification.device.cleanup-cron) at `notification-service/src/main/java/com/tvsm/notification/scheduler/NotificationDeviceCleanupScheduler.java:36`.

### Consume dev.cp-booking

1. `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingEventConsumer.java:73` receives messages from azure-service-bus topic `dev.cp-booking`.

### Consume dev.oclns.cp-lead

1. `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/EnquiryEventConsumer.java:73` receives messages from azure-service-bus topic `dev.oclns.cp-lead`.

### Consume dev.ums.user

1. `bff-service/src/main/java/com/tvsm/bff/service/UMSUserLifecycleConsumer.java:120` receives messages from azure-service-bus topic `dev.ums.user`.

### Consume dev.cp.booking

1. `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingServiceConsumer.java:45` receives messages from kafka kafka-topic `dev.cp.booking`.

### Consume dev.cp.service_lead

1. `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/WarrantyRegistrationConsumer.java:44` receives messages from kafka kafka-topic `dev.cp.service_lead`.

### Consume dev.cp.notification1

1. `notification-service/src/main/java/com/tvsm/notification/consumer/NotificationEventConsumer.java:139` receives messages from kafka kafka-topic `dev.cp.notification1`.

### Consume dev.cp.order

1. `order-service/src/main/java/com/tvsm/order/messaging/consumer/OrderEventConsumer.java:38` receives messages from kafka kafka-topic `dev.cp.order`.

## Integration Clients

`tvs-cps-backend` integration client wiring (HTTP, messaging, DB).

| Target service_id | Client class / file | Config key |
|---|---|---|
| tvs-cps-backend | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentExcelProcessorService.java` | config:bff.customer-service-local.base-url |
| tvs-cps-customer | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/util/ExternalAppointmentNotificationTriggerUtil.java` | config:bff.customer-service.base-url |
| tvs-cps-backend | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java` | config:bff.lead-allocation.base-url |
| Unknown | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/client/WorkflowAppointmentAssignmentClient.java` | config:bff.workflow-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | config:bff.announcement-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.announcement-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java` | config:bff.appointment-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.appointment-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.billing-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java` | config:bff.catalog-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java` | config:bff.catalog-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java` | config:bff.catalog-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.catalog-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java` | config:bff.claim-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.claim-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CustomerVehicleClient.java` | config:bff.inventory-service-internal.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.inventory-service-internal.base-url |
| tvs-cps-inventory | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java` | config:bff.inventory-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.inventory-service.base-url |
| tvs-cps-job-card-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/JobCardClient.java` | config:bff.jobcard-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.jobcard-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/LocationMasterClient.java` | config:bff.location-master-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java` | config:bff.order-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java` | config:bff.order-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.order-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.training-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/UmsClient.java` | config:bff.ums-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java` | config:bff.workflow-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:bff.workflow-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java` | config:cps-backend.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:cps-backend.base-url |
| external:onetrust | resttemplate `bff-service/src/main/java/com/tvsm/bff/auth/AuthService.java` | config:one-trust.one-trust-collection-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:azure.token-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | config:bff.announcement-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AppointmentAnalyticsBFFService.java` | config:bff.appointment-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/AppointmentClient.java` | config:bff.appointment-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java` | config:bff.appointment-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AppointmentBFFService.java` | config:bff.appointment-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AnalyticsService.java` | config:bff.appointment-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java` | config:bff.appointment-service.base-url |
| tvs-cps-billing | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java` | config:bff.billing-service.base-url |
| tvs-cps-billing | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BillingBFFService.java` | config:bff.billing-service.base-url |
| tvs-cps-billing | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BillingReportService.java` | config:bff.billing-service.base-url |
| booking-crud-services | webclient `bff-service/src/main/java/com/tvsm/bff/client/BookingServiceClient.java` | config:bff.booking-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/ServiceReminderClient.java` | config:bff.booking-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/ClaimAnalyticsBFFService.java` | config:bff.claim-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/ClaimBFFService.java` | config:bff.claim-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/SmartSearchBFFService.java` | config:bff.claim-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/ClaimClient.java` | config:bff.claim-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AnalyticsService.java` | config:bff.claim-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java` | config:bff.claim-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CollateralBFFController.java` | config:bff.collateral-service.base-url |
| tvs-cps-customer | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java` | config:bff.customer-service.base-url |
| tvs-cps-customer | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/VehicleBFFController.java` | config:bff.customer-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/InventoryClient.java` | config:bff.inventory-service-local.base-url |
| tvs-cps-inventory | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/reports/strategies/VehicleStockStrategy.java` | config:bff.inventory-service.base-url |
| tvs-cps-inventory | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryAnalyticsBFFController.java` | config:bff.inventory-service.base-url |
| tvs-cps-inventory | resttemplate `bff-service/src/main/java/com/tvsm/bff/strategy/InventoryAnalyticsStrategy.java` | config:bff.inventory-service.base-url |
| tvs-cps-job-card-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java` | config:bff.jobcard-service.base-url |
| tvs-cps-job-card-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AppointmentAnalyticsBFFService.java` | config:bff.jobcard-service.base-url |
| tvs-cps-job-card-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java` | config:bff.jobcard-service.base-url |
| tvs-cps-job-card-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/JobcardBFFService.java` | config:bff.jobcard-service.base-url |
| tvs-cps-backend | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java` | config:bff.lead-allocation.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java` | config:bff.lead-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java` | config:bff.notification-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationDeviceBFFController.java` | config:bff.notification-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java` | config:bff.notification-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationPreferenceBFFController.java` | config:bff.notification-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | config:bff.notification-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/NpqrBFFController.java` | config:bff.npqr-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/GRNClient.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InvoiceBFFController.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/OrderBffService.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/reports/strategies/AccessoriesOrderStrategy.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/strategy/OrderAnalyticsStrategy.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/InternalBffService.java` | config:bff.order-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | config:bff.order-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java` | config:bff.training-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/WorkflowBffService.java` | config:bff.workflow-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/WorkflowAssignmentClient.java` | config:bff.workflow-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | config:bff.workflow-service.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/GrnBFFService.java` | config:cps-backend.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/InvoiceClient.java` | config:cps-backend.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/SmartSearchBFFService.java` | config:cps-backend.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/reports/strategies/PartInvoiceStrategy.java` | config:cps-backend.base-url |
| tvs-cps-backend | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BookingBFFService.java` | config:cps-backend.base-url |
| tvs-cps-backend | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentExcelProcessorService.java` | config:cps-backend.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:erp.data-lake.api-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java` | config:lead.api.url |
| Unknown | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadServiceClient.java` | config:lead.api.url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:mdp.dealer.api.url |
| notification-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java` | config:notification.service.url |
| external:onetrust | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:one-trust.consent.url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:one-trust.token-url |
| tvsm-otp-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java` | config:otp.service.url |
| tvs-cps-inventory | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/inspection/VehicleInspectionServiceImpl.java` | config:bff.inventory-service.base-url |
| tvs-cps-job-card-service | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/JobCardInvoiceService.java` | config:bff.jobcard-service.base-url |
| Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java` | config:bff.workflow-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:claim.sap.api.url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:claim.sap.data-lake.api-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:claim.sap.oauth.token.url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:workflow.service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:notification.gateway.email.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:notification.gateway.push.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:notification.gateway.sms.base-url |
| tvs-cps-backend | resttemplate `order-service/src/main/java/com/tvsm/order/service/OrderService.java` | config:bff.order-service.base-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:erp.api.sale-order-change-url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:erp.api.url |
| Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java` | config:erp.oauth.token.url |
| tvs-cps-backend | resttemplate `order-service/src/main/java/com/tvsm/order/utils/WorkflowIntegrationUtil.java` | config:workflow.service.base-url |
| kafka:dev.cp.appointment | `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentProducerService.java:29` | azure.eventhub.appointment.hub-name |
| kafka:dev.cp.service_lead | `bff-service/src/main/java/com/tvsm/bff/producer/ServiceLeadEventProducer.java:44` | bff.servicelead.messaging.kafka.topics.service-lead |
| azure-service-bus:dev.cp-booking | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingEventConsumer.java:73` | booking.servicebus.topic-name |
| azure-service-bus:dev.oclns.cp-lead | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/EnquiryEventConsumer.java:73` | lead.servicebus.topic-name |
| azure-service-bus:dev.ums.user | `bff-service/src/main/java/com/tvsm/bff/service/UMSUserLifecycleConsumer.java:120` | ums.servicebus.topic-name |
| kafka:dev.cp.booking | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingServiceConsumer.java:45` | bff.booking.messaging.kafka.topics.booking |
| kafka:dev.cp.service_lead | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/WarrantyRegistrationConsumer.java:44` | bff.servicelead.messaging.kafka.topics.service-lead |
| kafka:dev.cp.notification1 | `notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:44, notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:58, notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:71, notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:125, notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:140, notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:154` | notification.messaging.kafka.hub-name |
| kafka:dev.cp.notification1 | `notification-service/src/main/java/com/tvsm/notification/consumer/NotificationEventConsumer.java:139` | notification.messaging.kafka.hub-name |
| kafka:dev.cp.booking | `order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java:54` | order.messaging.kafka.topics.booking |
| kafka:dev.cp.order | `order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java:41` | order.messaging.kafka.topics.order |
| kafka:dev.cp.order | `order-service/src/main/java/com/tvsm/order/messaging/consumer/OrderEventConsumer.java:38` | order.messaging.kafka.topics.order |
| db:nmazcpsdbdev01-cps | `announcement-service/src/main/java/com/tvsm/announcement/entity/Announcement.java` | — |
| db:nmazcpsdbdev01-cps | `appointment-service/src/main/java/com/tvsm/appointment/entity/Appointment.java` | — |
| db:nmazcpsdbdev01-cps | `bff-service/src/main/java/com/tvsm/bff/entity/AnalyticsDashboard.java` | — |
| db:nmazcpsdbdev01-cps | `claim-service/src/main/java/com/tvsm/claim/entity/BulkUpload.java` | — |
| db:nmazcpsdbdev01-cps | `collateral-service/src/main/java/com/tvsm/collateral/entity/Collateral.java` | — |
| db:nmazcpsdbdev01-cps | `lead-allocation/src/main/java/com/tvsm/leadallocation/entity/LeadAllocationEntityMapping.java` | — |
| db:Unknown | `notification-service/src/main/resources/db/migration/V10__seed_notification_action_config.sql` | — |
| db:nmazcpsdbdev01-cps | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationActionConfig.java` | — |
| db:nmazcpsdbdev01-cps | `npqr-service/src/main/java/com/tvsm/npqr/entity/NPQRFileMapping.java` | — |
| db:nmazcpsdbdev01-cps | `order-service/src/main/java/com/tvsm/order/entity/Cart.java` | — |
| db:nmazcpsdbdev01-cps | `training-service/src/main/java/com/tvsm/training/entity/Training.java` | — |
| db:nmazcpsdbdev01-cps | `workflow-service/src/main/java/com/tvsm/workflow/entity/Workflow.java` | — |

## Cross-Cutting Concerns

`tvs-cps-backend` cross-cutting concerns: JWT security, multi-tenancy (tenant header, multi-tenant datasource) and method/performance logging come from `tvsm-be-core` (`tvs-cps-app/src/main/resources/config/application.yml:103-133`); global exception handlers `bff-service/src/main/java/com/tvsm/bff/config/BFFExceptionHandler.java` and `data-access-service/src/main/java/com/tvsm/dataaccess/common/exception/handler/CommonDataAccessExceptionHandler.java`; Bean Validation (`jakarta.validation`), MapStruct mapping, Caffeine caching, Drools rules (service.yaml key_libraries).

## Build and Test

`tvs-cps-backend` builds with Maven: `mvn clean install` at the root (`README.md`); Docker build skips tests (`Dockerfile`). About 661 `*Test.java` files exist across modules (e.g. `announcement-service/src/test/java`); run with `mvn test`. CI: `ci-pipeline.yaml`; Sonar: `sonar.yaml`, `sonar.pr.yaml`.

---
service_id: tvs-cps-backend
doc_type: lld
last_reviewed: 2026-10-11
---

# TVS-CPS-BACKEND — Low-Level Design

## Data Model

`tvs-cps-backend` entities from `data_access` items; columns from resolved schemas where available.

### nmazcpsdbdev01-cps (`announcement-service/src/main/java/com/tvsm/announcement/entity/Announcement.java:17`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| Announcement | announcement | Unknown | both | `announcement-service/src/main/java/com/tvsm/announcement/entity/Announcement.java:17` |
| AnnouncementMedia | Unknown | Unknown | both | `announcement-service/src/main/java/com/tvsm/announcement/entity/AnnouncementMedia.java:13` |
| AnnouncementReadLog | announcement_read_log | Unknown | both | `announcement-service/src/main/java/com/tvsm/announcement/entity/AnnouncementReadLog.java:15` |
| AnnouncementTarget | announcement_target | Unknown | both | `announcement-service/src/main/java/com/tvsm/announcement/entity/AnnouncementTarget.java:12` |
| announcement | announcement | Unknown | read | `announcement-service/src/main/java/com/tvsm/announcement/repository/AnnouncementRepository.java:89` |
| announcement_target | announcement_target | Unknown | read | `announcement-service/src/main/java/com/tvsm/announcement/repository/AnnouncementRepository.java:89` |

### nmazcpsdbdev01-cps (`appointment-service/src/main/java/com/tvsm/appointment/entity/Appointment.java:20`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| Appointment | appointment | Unknown | both | `appointment-service/src/main/java/com/tvsm/appointment/entity/Appointment.java:20` |
| AppointmentBulkUpload | bulk_upload | Unknown | both | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentBulkUpload.java:13` |
| AppointmentContextMapping | appointment_context_mapping | Unknown | Unknown | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentContextMapping.java:13` |
| AppointmentDetail | appointment_detail | Unknown | Unknown | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentDetail.java:12` |
| AppointmentFileMapping | file_mapping | Unknown | Unknown | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentFileMapping.java:11` |
| AppointmentFollowUp | appointment_follow_up | Unknown | Unknown | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentFollowUp.java:13` |
| AppointmentJobTypeMaster | appointment_job_type_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentJobTypeMaster.java:6` |
| AppointmentServiceTypeMaster | appointment_service_type_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentServiceTypeMaster.java:6` |
| AppointmentStatusMaster | appointment_status_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/AppointmentStatusMaster.java:7` |
| BulkUploadError | bulk_upload_error | Unknown | both | `appointment-service/src/main/java/com/tvsm/appointment/entity/BulkUploadError.java:12` |
| CallResultMaster | call_result_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/CallResultMaster.java:7` |
| CancellationReasonMaster | cancellation_reason_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/CancellationReasonMaster.java:6` |
| FollowUpMethodMaster | follow_up_method_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/FollowUpMethodMaster.java:6` |
| RescheduleReasonMaster | reschedule_reason_master | Unknown | read | `appointment-service/src/main/java/com/tvsm/appointment/entity/RescheduleReasonMaster.java:6` |

### nmazcpsdbdev01-cps (`bff-service/src/main/java/com/tvsm/bff/entity/AnalyticsDashboard.java:15`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| AnalyticsDashboard | analytics_dashboard | Unknown | write | `bff-service/src/main/java/com/tvsm/bff/entity/AnalyticsDashboard.java:15` |
| AnalyticsIndicator | analytics_indicator | Unknown | both | `bff-service/src/main/java/com/tvsm/bff/entity/AnalyticsIndicator.java:13` |
| EnquiryBulkUpload | bulk_upload | Unknown | both | `bff-service/src/main/java/com/tvsm/bff/entity/EnquiryBulkUpload.java:13` |
| EnquiryBulkUploadError | bulk_upload_error | Unknown | both | `bff-service/src/main/java/com/tvsm/bff/entity/EnquiryBulkUploadError.java:12` |
| TenantConfig | tenant_config | Unknown | both | `bff-service/src/main/java/com/tvsm/bff/entity/TenantConfig.java:15` |
| WarrantyRegistrationAudit | warranty_registration_audit | Unknown | both | `bff-service/src/main/java/com/tvsm/bff/entity/WarrantyRegistrationAudit.java:8` |

### nmazcpsdbdev01-cps (`claim-service/src/main/java/com/tvsm/claim/entity/BulkUpload.java:13`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| BulkUpload | bulk_upload | Unknown | both | `claim-service/src/main/java/com/tvsm/claim/entity/BulkUpload.java:13` |
| BulkUploadError | bulk_upload_error | Unknown | both | `claim-service/src/main/java/com/tvsm/claim/entity/BulkUploadError.java:12` |
| CatalogAdditionalInfo | catalog_additional_info | Unknown | Unknown | `claim-service/src/main/java/com/tvsm/claim/entity/CatalogAdditionalInfo.java:10` |
| Claim | claim | Unknown | both | `claim-service/src/main/java/com/tvsm/claim/entity/Claim.java:19` |
| ClaimCatalogApproval | claim_catalog_approval | cps | both | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimCatalogApproval.java:11` |
| ClaimCatalogMapping | claim_catalog_mapping | Unknown | both | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimCatalogMapping.java:16` |
| ClaimCatalogStatusMaster | claim_catalog_status_master | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimCatalogStatusMaster.java:6` |
| ClaimERPMapping | claim_erp_mapping | Unknown | Unknown | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimERPMapping.java:13` |
| ClaimEntityMapping | claim_entity_mapping | Unknown | Unknown | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimEntityMapping.java:12` |
| ClaimRejectReasonMaster | claim_reject_reason_master | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimRejectReasonMaster.java:6` |
| ClaimStatusMaster | claim_status_master | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimStatusMaster.java:6` |
| ClaimSubTypeMaster | claim_sub_type_master | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimSubTypeMaster.java:6` |
| ClaimTimelineMapping | claim_timeline_mapping | Unknown | write | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimTimelineMapping.java:13` |
| ClaimTypeMaster | claim_type_master | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/entity/ClaimTypeMaster.java:6` |
| FaultTypeMaster | fault_type_master | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/entity/FaultTypeMaster.java:6` |
| FileMapping | file_mapping | Unknown | both | `claim-service/src/main/java/com/tvsm/claim/entity/FileMapping.java:11` |
| agg | agg | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:167` |
| base | base | Unknown | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:167` |
| claim | claim | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:121` |
| claim_catalog_mapping | claim_catalog_mapping | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:121` |
| claim_erp_mapping | claim_erp_mapping | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:306` |
| claim_timeline_mapping | claim_timeline_mapping | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:167` |
| grn | grn | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:268` |
| invoice | invoice | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:268` |
| invoice_erp_info | invoice_erp_info | cps | read | `claim-service/src/main/java/com/tvsm/claim/repository/ClaimL1DashboardRepository.java:268` |

### nmazcpsdbdev01-cps (`collateral-service/src/main/java/com/tvsm/collateral/entity/Collateral.java:16`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| Collateral | collateral | Unknown | both | `collateral-service/src/main/java/com/tvsm/collateral/entity/Collateral.java:16` |
| collateral | collateral | Unknown | read | `collateral-service/src/main/java/com/tvsm/collateral/repository/CollateralRepository.java:17` |

### nmazcpsdbdev01-cps (`lead-allocation/src/main/java/com/tvsm/leadallocation/entity/LeadAllocationEntityMapping.java:29`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| LeadAllocationEntityMapping | lead_allocation_entity_mapping | Unknown | both | `lead-allocation/src/main/java/com/tvsm/leadallocation/entity/LeadAllocationEntityMapping.java:29` |
| LeadAllocationJobTypeMaster | appointment_job_type_master | Unknown | read | `lead-allocation/src/main/java/com/tvsm/leadallocation/entity/LeadAllocationJobTypeMaster.java:6` |
| LeadAllocationMapping | lead_allocation_mapping | Unknown | both | `lead-allocation/src/main/java/com/tvsm/leadallocation/entity/LeadAllocationMapping.java:27` |
| RoundRobinTracker | round_robin_tracker | Unknown | both | `lead-allocation/src/main/java/com/tvsm/leadallocation/entity/RoundRobinTracker.java:29` |

### Unknown database (`notification-service/src/main/resources/db/migration/V10__seed_notification_action_config.sql:11`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| notification_action_config | notification_action_config | Unknown | write | `notification-service/src/main/resources/db/migration/V10__seed_notification_action_config.sql:11` |
| notification_category | notification_category | Unknown | write | `notification-service/src/main/resources/db/migration/V11__seed_category_subcategory_roles_notification_types.sql:14` |
| notification_message | notification_message | Unknown | write | `notification-service/src/main/resources/db/migration/V12__alter_deep_url_to_jsonb.sql:51` |
| notification_subcategory | notification_subcategory | Unknown | write | `notification-service/src/main/resources/db/migration/V11__seed_category_subcategory_roles_notification_types.sql:90` |
| notification_template | notification_template | Unknown | write | `notification-service/src/main/resources/db/migration/V12__alter_deep_url_to_jsonb.sql:23` |
| notification_type | notification_type | Unknown | write | `notification-service/src/main/resources/db/migration/V16__seed_categories_GB_7500000101.sql:7` |

### nmazcpsdbdev01-cps (`notification-service/src/main/java/com/tvsm/notification/entity/NotificationActionConfig.java:28`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| NotificationActionConfig | notification_action_config | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationActionConfig.java:28` |
| NotificationCategory | notification_category | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationCategory.java:18` |
| NotificationDevice | notification_device | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationDevice.java:13` |
| NotificationMessage | notification_message | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationMessage.java:17` |
| NotificationPreference | user_notification_preference | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationPreference.java:13` |
| NotificationSubCategory | notification_subcategory | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationSubCategory.java:18` |
| NotificationTemplate | notification_template | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationTemplate.java:24` |
| NotificationType | notification_type | Unknown | both | `notification-service/src/main/java/com/tvsm/notification/entity/NotificationType.java:12` |

### nmazcpsdbdev01-cps (`npqr-service/src/main/java/com/tvsm/npqr/entity/NPQRFileMapping.java:13`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| NPQRFileMapping | file_mapping | Unknown | both | `npqr-service/src/main/java/com/tvsm/npqr/entity/NPQRFileMapping.java:13` |
| QualityReport | quality_report | Unknown | both | `npqr-service/src/main/java/com/tvsm/npqr/entity/QualityReport.java:13` |

### nmazcpsdbdev01-cps (`order-service/src/main/java/com/tvsm/order/entity/Cart.java:13`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| Cart | cart | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/Cart.java:13` |
| CartLine | cart_line | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/CartLine.java:13` |
| Grn | grn | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/Grn.java:13` |
| GrnDeliveryDetail | grn_delivery_detail | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/GrnDeliveryDetail.java:15` |
| GrnDetail | grn_detail | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/GrnDetail.java:13` |
| Invoice | invoice | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/Invoice.java:13` |
| InvoiceErpInfo | invoice_erp_info | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/InvoiceErpInfo.java:14` |
| InvoiceLineItem | invoice_line_item | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/InvoiceLineItem.java:12` |
| InvoiceOrderMapping | invoice_order_mapping | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/InvoiceOrderMapping.java:14` |
| Order | orders | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/Order.java:15` |
| OrderErpInfo | order_erp_info | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/OrderErpInfo.java:13` |
| OrderLine | order_line | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/OrderLine.java:14` |
| OrderStateHistory | order_state_history | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/OrderStateHistory.java:12` |
| UserPreference | user_preferences | Unknown | both | `order-service/src/main/java/com/tvsm/order/entity/UserPreference.java:13` |
| grn | grn | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/GrnRepository.java:20` |
| grn_delivery_detail | grn_delivery_detail | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/GrnRepository.java:20` |
| grn_detail | grn_detail | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/GrnRepository.java:48` |
| invoice | invoice | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/GrnRepository.java:20` |
| invoice_erp_info | invoice_erp_info | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/GrnRepository.java:20` |
| invoice_line_item | invoice_line_item | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/GrnRepository.java:84` |
| jsonb_array_elements | jsonb_array_elements | Unknown | read | `order-service/src/main/java/com/tvsm/order/repository/OrderRepository.java:220` |
| order_line | order_line | cps | read | `order-service/src/main/java/com/tvsm/order/repository/OrderL1DashboardRepository.java:95` |
| order_state_history | order_state_history | cps | read | `order-service/src/main/java/com/tvsm/order/repository/OrderL1DashboardRepository.java:16` |
| orders | orders | cps | read | `order-service/src/main/java/com/tvsm/order/repository/OrderL1DashboardRepository.java:16` |

### invoice

| Column | Type | Nullable | Notes |
|---|---|---|---|
| invoiceId | uuid | True | — |
| tenantId | string | True | — |
| orderingEntityId | string | True | — |
| orderingEntityType | string | True | — |
| shipmentInfo | map<string,object> | True | — |
| orderCategoryType | string | True | — |
| invoiceValue | number | True | — |
| currency | string | True | — |
| invoiceDate | datetime | True | — |
| additionalInfo | map<string,object> | True | — |
| createdAt | datetime | True | — |
| createdBy | string | True | — |
| invoiceNumber | string | True | — |

### nmazcpsdbdev01-cps (`training-service/src/main/java/com/tvsm/training/entity/Training.java:15`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| Training | training | Unknown | both | `training-service/src/main/java/com/tvsm/training/entity/Training.java:15` |
| TrainingMedia | training_media | Unknown | both | `training-service/src/main/java/com/tvsm/training/entity/TrainingMedia.java:12` |
| TrainingReadLog | training_read_log | Unknown | both | `training-service/src/main/java/com/tvsm/training/entity/TrainingReadLog.java:15` |

### nmazcpsdbdev01-cps (`workflow-service/src/main/java/com/tvsm/workflow/entity/Workflow.java:16`)

| Entity | Table | Schema | Operation | Defined in |
|---|---|---|---|---|
| Workflow | workflow | Unknown | both | `workflow-service/src/main/java/com/tvsm/workflow/entity/Workflow.java:16` |
| WorkflowHistory | workflow_history | Unknown | both | `workflow-service/src/main/java/com/tvsm/workflow/entity/WorkflowHistory.java:14` |
| WorkflowTemplate | workflow_template | Unknown | both | `workflow-service/src/main/java/com/tvsm/workflow/entity/WorkflowTemplate.java:17` |

## State Machines

`tvs-cps-backend` status/state enums found in code (transitions not traced):

| Enum | Values | Defined in |
|---|---|---|
| AnnouncementStatus | enum[DRAFT,PUBLISHED,ARCHIVED] | `announcement-service/src/main/java/com/tvsm/announcement/entity/Announcement.java:53` |
| AppointmentStatus | enum[AWAITING_ACTION,BOOKED,RESCHEDULED,CANCELLED,CLOSED,CONFIRMED] | `appointment-service/src/main/java/com/tvsm/appointment/enums/AppointmentStatus.java:3` |
| ClaimCatalogStatus | enum[UNDER_REVIEW,SUBMITTED,APPROVED,REJECTED,IN_APPEAL] | `claim-service/src/main/java/com/tvsm/claim/constants/ClaimCatalogStatus.java:3` |
| ClaimStatus | enum[SUBMITTED,APPROVED,REJECTED,UNDER_REVIEW,PAID] | `claim-service/src/main/java/com/tvsm/claim/constants/ClaimStatus.java:3` |
| GrnStatus | enum[INITIATED,DRAFT,DRAFT_COMPLETED,PARTIAL_COMPLETED,COMPLETED] | `order-service/src/main/java/com/tvsm/order/entity/Grn.java:68` |
| WorkflowStatus | enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED] | `workflow-service/src/main/java/com/tvsm/workflow/entity/WorkflowStatus.java:3` |

## Business Rules

`tvs-cps-backend`: N/A — not determinable from code.

## Key Classes and Functions

`tvs-cps-backend` key classes.

| Class / Function | File | Responsibility |
|---|---|---|
| `OrderBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java` | HTTP handler (27 endpoints) |
| `OrderController` | `order-service/src/main/java/com/tvsm/order/controller/OrderController.java` | HTTP handler (21 endpoints) |
| `InventoryBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java` | HTTP handler (19 endpoints) |
| `CatalogController` | `bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java` | HTTP handler (14 endpoints) |
| `ClaimController` | `claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java` | HTTP handler (14 endpoints) |
| `AppointmentController` | `appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java` | HTTP handler (13 endpoints) |
| `ClaimBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java` | HTTP handler (13 endpoints) |
| `EnquiryBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java` | HTTP handler (12 endpoints) |
| `JobcardBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java` | HTTP handler (12 endpoints) |
| `AppointmentBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java` | HTTP handler (11 endpoints) |
| `InternalServiceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java` | HTTP handler (11 endpoints) |
| `AnnouncementController` | `announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java` | HTTP handler (10 endpoints) |
| `AnnouncementBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java` | HTTP handler (10 endpoints) |
| `WorkflowBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java` | HTTP handler (10 endpoints) |
| `CartBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java` | HTTP handler (9 endpoints) |
| `CartController` | `order-service/src/main/java/com/tvsm/order/controller/CartController.java` | HTTP handler (9 endpoints) |
| `BookingBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java` | HTTP handler (8 endpoints) |
| `GrnBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java` | HTTP handler (8 endpoints) |
| `CustomerBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java` | HTTP handler (7 endpoints) |
| `GrnController` | `order-service/src/main/java/com/tvsm/order/controller/GrnController.java` | HTTP handler (7 endpoints) |
| `BillingBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java` | HTTP handler (6 endpoints) |
| `TenantConfigController` | `bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java` | HTTP handler (5 endpoints) |
| `DocController` | `bff-service/src/main/java/com/tvsm/bff/controller/DocController.java` | HTTP handler (5 endpoints) |
| `LeadAllocationController` | `lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java` | HTTP handler (5 endpoints) |
| `NotificationCategoryController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java` | HTTP handler (5 endpoints) |
| `NotificationMessageController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java` | HTTP handler (5 endpoints) |
| `WorkflowController` | `workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java` | HTTP handler (5 endpoints) |
| `WorkflowTemplateController` | `workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java` | HTTP handler (5 endpoints) |
| `TrainingBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java` | HTTP handler (4 endpoints) |
| `LeadServiceBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/LeadServiceBFFController.java` | HTTP handler (4 endpoints) |
| `NotificationCategoryBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java` | HTTP handler (4 endpoints) |
| `NotificationMessageBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java` | HTTP handler (4 endpoints) |
| `NotificationActionConfigController` | `notification-service/src/main/java/com/tvsm/notification/controller/NotificationActionConfigController.java` | HTTP handler (4 endpoints) |
| `TrainingController` | `training-service/src/main/java/com/tvsm/training/controller/TrainingController.java` | HTTP handler (4 endpoints) |
| `DashboardBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/DashboardBFFController.java` | HTTP handler (3 endpoints) |
| `PermissionBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java` | HTTP handler (3 endpoints) |
| `WarrantyBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/WarrantyBFFController.java` | HTTP handler (3 endpoints) |
| `LeadAllocationBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/LeadAllocationBFFController.java` | HTTP handler (3 endpoints) |
| `NotificationBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/NotificationBFFController.java` | HTTP handler (3 endpoints) |
| `SmartSearchBFFController` | `bff-service/src/main/java/com/tvsm/bff/controller/SmartSearchBFFController.java` | HTTP handler (3 endpoints) |
| `AppointmentProducerService.java` | `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentProducerService.java:29` | publish dev.cp.appointment |
| `ServiceLeadEventProducer.java` | `bff-service/src/main/java/com/tvsm/bff/producer/ServiceLeadEventProducer.java:44` | publish dev.cp.service_lead |
| `BookingEventConsumer.java` | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingEventConsumer.java:73` | subscribe dev.cp-booking |
| `EnquiryEventConsumer.java` | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/EnquiryEventConsumer.java:73` | subscribe dev.oclns.cp-lead |
| `UMSUserLifecycleConsumer.java` | `bff-service/src/main/java/com/tvsm/bff/service/UMSUserLifecycleConsumer.java:120` | subscribe dev.ums.user |
| `BookingServiceConsumer.java` | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingServiceConsumer.java:45` | subscribe dev.cp.booking |
| `WarrantyRegistrationConsumer.java` | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/WarrantyRegistrationConsumer.java:44` | subscribe dev.cp.service_lead |
| `NotificationTriggerService.java` | `notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:44, notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:58, notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:71, notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:125, notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:140, notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:154` | publish dev.cp.notification1 |
| `NotificationEventConsumer.java` | `notification-service/src/main/java/com/tvsm/notification/consumer/NotificationEventConsumer.java:139` | subscribe dev.cp.notification1 |
| `OrderProducerService.java` | `order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java:54` | publish dev.cp.booking |
| `OrderProducerService.java` | `order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java:41` | publish dev.cp.order |
| `OrderEventConsumer.java` | `order-service/src/main/java/com/tvsm/order/messaging/consumer/OrderEventConsumer.java:38` | subscribe dev.cp.order |
| `JobScheduler.loadCatalogData` | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:111` | scheduled job |
| `JobScheduler.retrieveMDPDealers` | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:65` | scheduled job |
| `JobScheduler.retrieveMerchandiseStock` | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:80` | scheduled job |
| `JobScheduler.warmUpUmsCache` | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:93` | scheduled job |
| `NotificationDeviceCleanupScheduler.deactivateStaleDevices` | `notification-service/src/main/java/com/tvsm/notification/scheduler/NotificationDeviceCleanupScheduler.java:36` | scheduled job |

## Sequence Details

`tvs-cps-backend`: N/A — no multi-step sequence traced beyond DATA_FLOWS.md.

## Error Handling

`tvs-cps-backend` maps exceptions centrally: `BFFExceptionHandler` handles `ConstraintViolationException` (`bff-service/src/main/java/com/tvsm/bff/config/BFFExceptionHandler.java:55`), `BulkUploadValidationException` (`:91`) and `MissingColumnValidationException` (`:127`); `CommonDataAccessExceptionHandler` handles `InvalidRequestException` (`data-access-service/src/main/java/com/tvsm/dataaccess/common/exception/handler/CommonDataAccessExceptionHandler.java:14`). Response codes per handler: Unknown (not read).

## Configuration Details

`tvs-cps-backend` config keys grouped by prefix (names only; behaviour per key Unknown unless stated).

| Prefix | Keys | Examples | Read at |
|---|---|---|---|
| `reports` | 281 | `reports`, `reports.ACCESSORIES_PURCHASE_ORDER_LIST.columns[0]`, `reports.ACCESSORIES_PURCHASE_ORDER_LIST.columns[10]`, `reports.ACCESSORIES_PURCHASE_ORDER_LIST.columns[11]`, `reports.ACCESSORIES_PURCHASE_ORDER_LIST.columns[12]`, `reports.ACCESSORIES_PURCHASE_ORDER_LIST.columns[1]` … | `bff-service/src/main/java/com/tvsm/bff/config/ReportConfigLoader.java:21` |
| `bff` | 140 | `bff.appointment-service.base-url`, `bff.catalog-service.base-url`, `bff.customer-service.base-url`, `bff.customer-service-local.base-url`, `bff.doc-service.base-url`, `bff.lead-allocation.base-url` … | `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentService.java:62`, `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentExcelProcessorService.java:49` |
| `notification` | 85 | `notification.app.base-url`, `notification.app.preferences-path`, `notification.app.base-url`, `notification.app.preferences-path`, `notification.email.first-name`, `notification.email.sender` … | `appointment-service/src/main/java/com/tvsm/appointment/util/ExternalAppointmentNotificationTriggerUtil.java:50`, `appointment-service/src/main/java/com/tvsm/appointment/util/ExternalAppointmentNotificationTriggerUtil.java:53` |
| `order` | 43 | `order.statuses.tracked`, `order.messaging.kafka.consumer.consumers.order.bootstrap-servers`, `order.messaging.kafka.consumer.consumers.order.enabled-dlt`, `order.messaging.kafka.consumer.consumers.order.group-id-prefix`, `order.messaging.kafka.consumer.consumers.order.security.sasl-jaas-config`, `order.messaging.kafka.consumer.consumers.order.security.sasl-mechanism` … | `order-service/src/main/java/com/tvsm/order/config/OrderStatusConfigProperties.java:19` |
| `smartsearch` | 36 | `smartsearch.details.active-events.appointment-statuses`, `smartsearch.details.active-events.booking-statuses`, `smartsearch.details.active-events.claim-statuses`, `smartsearch.details.active-events.jobcard-statuses`, `smartsearch.details.active-events.max-booking`, `smartsearch.details.active-events.max-open-enquiry` … | `bff-service/src/main/java/com/tvsm/bff/service/SmartSearchBFFService.java:181`, `bff-service/src/main/java/com/tvsm/bff/service/SmartSearchBFFService.java:199` |
| `commons` | 35 | `commons.messaging.kafka.consumer.bootstrap-servers`, `commons.messaging.kafka.consumer.enabled`, `commons.messaging.kafka.consumer.enabled-dlt`, `commons.messaging.kafka.consumer.group-id-prefix`, `commons.messaging.kafka.consumer.security.sasl-jaas-config`, `commons.messaging.kafka.consumer.security.sasl-mechanism` … | Unknown |
| `common` | 31 | `common.cache.notificationActionConfigs`, `common.cache.notificationCategories`, `common.cache.notificationCategoriesByRole`, `common.cache.notificationCategory`, `common.cache.notificationTemplates`, `common.cache.umsEmployeeList` … | `common-service/src/main/java/com/tvsm/common/config/CacheProperties.java:46`, `common-service/src/main/java/com/tvsm/common/config/CacheProperties.java:44` |
| `one-trust` | 30 | `one-trust.client-id`, `one-trust.client-secret`, `one-trust.consent.url`, `one-trust.grant-type`, `one-trust.onetrust-collection-point-guid`, `one-trust.one-trust-collection-url` … | `bff-service/src/main/java/com/tvsm/bff/auth/AuthService.java:45`, `bff-service/src/main/java/com/tvsm/bff/auth/AuthService.java:48` |
| `l1-dashboard` | 28 | `l1-dashboard.mdp.dealer-type.cache-enabled`, `l1-dashboard.tableRows`, `l1-dashboard.mdp.dealer-type.cache-enabled`, `l1-dashboard.tableRows.ORDERS[0]`, `l1-dashboard.tableRows.ORDERS[1]`, `l1-dashboard.tableRows.ORDERS[2]` … | `bff-service/src/main/java/com/tvsm/bff/service/AnalyticsService.java:46`, `bff-service/src/main/java/com/tvsm/bff/config/L1DashboardConfiguration.java:13` |
| `tvsm` | 28 | `tvsm.core.cloud-storage.azure.connection-string`, `tvsm.core.cloud-storage.azure.container-name`, `tvsm.core.cloud-storage.enabled`, `tvsm.core.cloud-storage.provider`, `tvsm.core.logging.methodLevel.enabled`, `tvsm.core.logging.performance.enabled` … | Unknown |
| `doc-upload` | 26 | `doc-upload.allowedContentType`, `doc-upload.allowedExtensions`, `doc-upload.service.view-path-prefix`, `doc-upload.allowed-content-type[0]`, `doc-upload.allowed-content-type[10]`, `doc-upload.allowed-content-type[1]` … | `bff-service/src/main/java/com/tvsm/bff/config/DocUploadProperties.java:15`, `bff-service/src/main/java/com/tvsm/bff/config/DocUploadProperties.java:16` |
| `taxation` | 26 | `taxation.de`, `taxation.default.taxPercentage`, `taxation.es`, `taxation.fr`, `taxation.gb`, `taxation.it` … | `bff-service/src/main/java/com/tvsm/bff/config/TaxationConfig.java:26`, `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java:119` |
| `erp` | 22 | `erp.data-lake.api-url`, `erp.data-lake.function-code`, `erp.data-lake.table-name.vehicle-master`, `erp.data-lake.api-url`, `erp.data-lake.function-code`, `erp.data-lake.table-name.stock-master` … | `bff-service/src/main/java/com/tvsm/bff/service/VehicleDatalakeBFFService.java:24`, `bff-service/src/main/java/com/tvsm/bff/service/VehicleDatalakeBFFService.java:27` |
| `merchandise` | 20 | `merchandise.keyword-search-fields`, `merchandise.sizeOrder`, `merchandise.oem-stock.default-stock-quantity`, `merchandise.oem-stock.flag`, `merchandise.keyword-search-fields`, `merchandise.oem-stock.cron.schedule` … | `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java:91`, `bff-service/src/main/java/com/tvsm/bff/config/MerchandiseConfig.java:16` |
| `azure` | 18 | `azure.eventhub.appointment.hub-name`, `azure.kafka.bootstrap-servers`, `azure.kafka.properties.sasl.jaas.config`, `azure.client-id`, `azure.client-secret`, `azure.grant-type` … | `appointment-service/src/main/java/com/tvsm/appointment/config/EventHubConfig.java:20`, `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentProducerService.java:15` |
| `apim` | 18 | `apim.client-id`, `apim.client-secret`, `apim.scope`, `apim.scope-ui`, `apim.tenant-id`, `apim.clientId` … | `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java:79`, `bff-service/src/main/java/com/tvsm/bff/client/CustomerVehicleClient.java:43` |
| `claim` | 18 | `claim.sap.data-lake.table-name`, `claim.catalog.appeal.limit`, `claim.sap.api.url`, `claim.sap.data-lake.api-url`, `claim.sap.data-lake.function-code`, `claim.sap.data-lake.table-name` … | `bff-service/src/main/java/com/tvsm/bff/service/VehicleDatalakeBFFService.java:30`, `claim-service/src/main/java/com/tvsm/claim/service/ClaimCatalogService.java:86` |
| `tenants` | 18 | `tenants.default.currency-code`, `tenants.default.locale`, `tenants.default.timezone`, `tenants.list`, `tenants.default.currency-code`, `tenants.default.locale` … | `bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java:47`, `bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java:50` |
| `springdoc` | 16 | `springdoc.api-docs.path`, `springdoc.default-consumes-media-type`, `springdoc.default-produces-media-type`, `springdoc.info.description`, `springdoc.info.title`, `springdoc.info.version` … | Unknown |
| `booking` | 15 | `booking.servicebus.connection-string`, `booking.servicebus.subscription-name`, `booking.servicebus.topic-name`, `booking.status.confirmed-status`, `booking.statusMapping`, `booking.servicebus.connection-string` … | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingEventConsumer.java:34`, `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingEventConsumer.java:40` |
| `spring` | 13 | `spring.application.name`, `spring.autoconfigure.exclude[0]`, `spring.autoconfigure.exclude[1]`, `spring.config.import`, `spring.jmx.enabled`, `spring.jpa.database-platform` … | Unknown |
| `workflow` | 12 | `workflow.service.action-context-path`, `workflow.service.base-url`, `workflow.service.init-context-path`, `workflow.service.base-url`, `workflow.actions.claim_approval.APPEAL`, `workflow.actions.claim_approval.IN_APPEAL` … | `claim-service/src/main/java/com/tvsm/claim/util/WorkflowIntegrationUtils.java:38`, `claim-service/src/main/java/com/tvsm/claim/util/WorkflowIntegrationUtils.java:35` |
| `lead` | 11 | `lead.api.exclude-service-reminder-lead`, `lead.api.url`, `lead.servicebus.connection-string`, `lead.servicebus.subscription-name`, `lead.servicebus.topic-name`, `lead.api.exclude-service-reminder-lead` … | `bff-service/src/main/java/com/tvsm/bff/client/LeadServiceClient.java:46`, `bff-service/src/main/java/com/tvsm/bff/client/LeadServiceClient.java:43` |
| `ums` | 11 | `ums.servicebus.connection-string`, `ums.servicebus.subscription-name`, `ums.servicebus.topic-name`, `ums.cache.cron.schedule`, `ums.consumer.enabled`, `ums.servicebus.connection-string` … | `bff-service/src/main/java/com/tvsm/bff/service/UMSUserLifecycleConsumer.java:68`, `bff-service/src/main/java/com/tvsm/bff/service/UMSUserLifecycleConsumer.java:74` |
| `billing` | 10 | `billing.catalog.parts-price-key`, `billing.catalog.vehicle-price-key`, `billing.default.currency-code`, `billing.default.tax-percentage`, `billing.default.tax-type`, `billing.catalog.parts-price-key` … | `bff-service/src/main/java/com/tvsm/bff/service/BillingBFFService.java:103`, `bff-service/src/main/java/com/tvsm/bff/service/BillingBFFService.java:100` |
| `bulk-upload` | 10 | `bulk-upload.excel-template.header-size.enquiry`, `bulk-upload.excel-template.header-size.accessories-order`, `bulk-upload.excel-template.header-size.merchandise-order`, `bulk-upload.excel-template.header-size.parts-order`, `bulk-upload.excel-template.header-size.vehicle-order`, `bulk-upload.excel-template.header-size.accessories-order` … | `bff-service/src/main/java/com/tvsm/bff/service/EnquiryExcelParserService.java:25`, `order-service/src/main/java/com/tvsm/order/service/ExcelParserService.java:34` |
| `enquiry` | 10 | `enquiry.service.calendar-event-duration-minutes`, `enquiry.service.followup-days`, `enquiry.service.master-data-file-path`, `enquiry.service.page-size`, `enquiry.service.source-id`, `enquiry.service.calendar-event-duration-minutes` … | `bff-service/src/main/java/com/tvsm/bff/mapper/CalendarEventMapper.java:19`, `bff-service/src/main/java/com/tvsm/bff/service/EnquiryBFFService.java:107` |
| `warranty-document` | 8 | `warranty-document.content-type`, `warranty-document.name`, `warranty-document.size`, `warranty-document.url`, `warranty-document.content-type`, `warranty-document.name` … | `bff-service/src/main/java/com/tvsm/bff/service/customer/CustomerVehicleEnrichmentService.java:51`, `bff-service/src/main/java/com/tvsm/bff/service/customer/CustomerVehicleEnrichmentService.java:45` |
| `rbac` | 7 | `rbac.config.api-mapping.path`, `rbac.config.permission-groups.path`, `rbac.config.permissions.path`, `rbac.config.roles.path`, `rbac.configEnabled`, `rbac.default-unmapped-api-behavior` … | Unknown |
| `app` | 6 | `app.reminder-days`, `app.rest.timeout.connect`, `app.rest.timeout.read`, `app.reminder-days`, `app.rest.timeout.connect`, `app.rest.timeout.read` | `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:76`, `order-service/src/main/java/com/tvsm/order/config/Config.java:20` |
| `template` | 6 | `template.appointment.url`, `template.claim.url`, `template.jobcard.url`, `template.appointment.url`, `template.claim.url`, `template.jobcard.url` | `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:62`, `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:68` |
| `logging` | 6 | `logging.level.com.tvsm.order`, `logging.level.org.hibernate.SQL`, `logging.level.org.hibernate.type.descriptor.sql.BasicBinder`, `logging.level.org.springframework.web`, `logging.pattern.console`, `logging.pattern.file` | Unknown |
| `enquiries` | 5 | `enquiries.view-all-access.roles`, `enquiries.view-all-access.oem-role[0]`, `enquiries.view-all-access.oem-role[1]`, `enquiries.view-all-access.roles[0]`, `enquiries.view-all-access.roles[1]` | `bff-service/src/main/java/com/tvsm/bff/config/EnquiryRoleConfig.java:14` |
| `tenant` | 5 | `tenant.api.base-path`, `tenant.api.create`, `tenant.api.current`, `tenant.api.handler-patch-path`, `tenant.api.tenant-id-path` | Unknown |
| `appointment` | 4 | `appointment.auto-close-days`, `appointment.external.allowed-tenant-ids`, `appointment.auto-close-days`, `appointment.external.allowed-tenant-ids` | `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentService.java:68`, `appointment-service/src/main/java/com/tvsm/appointment/service/ExternalAppointmentService.java:24` |
| `analytics` | 4 | `analytics.default.page-size`, `analytics.default.start-date`, `analytics.default.page-size`, `analytics.default.start-date` | `bff-service/src/main/java/com/tvsm/bff/strategy/AllBookingsStrategy.java:29`, `bff-service/src/main/java/com/tvsm/bff/strategy/AllEnquiriesStrategy.java:27` |
| `otp` | 4 | `otp.service.url`, `otp.email-enabled`, `otp.service.url`, `otp.sms-enabled` | `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java:29` |
| `reports-file-config` | 4 | `reports-file-config.default_column_width`, `reports-file-config.flush_every_n_rows`, `reports-file-config.default_column_width`, `reports-file-config.flush_every_n_rows` | `bff-service/src/main/java/com/tvsm/bff/service/reports/ReportService.java:36`, `bff-service/src/main/java/com/tvsm/bff/service/reports/ReportService.java:33` |
| `brands` | 4 | `brands`, `brands`, `brands.COMMANDO`, `brands.V4` | `common-service/src/main/java/com/tvsm/common/config/BrandConfig.java:12`, `lead-allocation/src/main/java/com/tvsm/leadallocation/config/BrandConfig.java:27` |
| `catalog` | 4 | `catalog.vehicle.filter-available-for-sale`, `catalog.cron.schedule`, `catalog.labour.tax-percentage`, `catalog.vehicle.filter-available-for-sale` | `common-service/src/main/java/com/tvsm/common/service/CatalogCacheService.java:39` |

## Edge Cases

`tvs-cps-backend`: N/A — not determinable from code.

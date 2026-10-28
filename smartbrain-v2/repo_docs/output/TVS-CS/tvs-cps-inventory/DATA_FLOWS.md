---
service_id: tvs-cps-inventory
doc_type: data_flows
last_reviewed: 2026-10-11
flows: [tvs-cps-backend--tvs-cps-inventory, tvs-cps-jobs--tvs-cps-inventory, tvs-cps-portal--tvs-cps-inventory]   # flow_ids, must match service.yaml `flows`
---

# tvs-cps-inventory — Data Flows

## Flow Index
tvs-cps-inventory takes part in 3 end-to-end flow(s) in registry/flows.json.

| flow_id | Name | Role of tvs-cps-inventory | Trigger |
|---|---|---|---|
| tvs-cps-backend--tvs-cps-inventory | tvs-cps-backend → tvs-cps-inventory (1 hop) | terminal | scheduled job(s) in tvs-cps-backend (job-to-call link not resolved): JobScheduler.loadCatalogData, JobScheduler.retrieveMDPDealers, JobScheduler.retrieveMerchandiseStock (+2 more) |
| tvs-cps-jobs--tvs-cps-inventory | tvs-cps-jobs → tvs-cps-inventory (2 hops) | terminal | scheduled job(s) in tvs-cps-jobs (job-to-call link not resolved): CronJobScheduler.allBookingsScheduler, CronJobScheduler.allEnquiriesScheduler, CronJobScheduler.availableStockScheduler (+27 more); request to tvs-cps-jobs from outside the registry (no internal caller) |
| tvs-cps-portal--tvs-cps-inventory | tvs-cps-portal → tvs-cps-inventory (2 hops) | terminal | user action in tvs-cps-portal (frontend) |

## Flow: tvs-cps-backend--tvs-cps-inventory
Summary: Starting at `tvs-cps-backend` (scheduled job(s) in tvs-cps-backend (job-to-call link not resolved): JobScheduler.loadCatalogData, JobScheduler.retrieveMDPDealers, JobScheduler.retrieveMerchandiseStock (+2 more)), the flow ends at `tvs-cps-inventory`, using 1 sync HTTP hop(s) and 0 async event hop(s); tvs-cps-inventory role: terminal; confidence high.

```mermaid
sequenceDiagram
  participant tvs_cps_backend as tvs-cps-backend
  participant tvs_cps_inventory as tvs-cps-inventory
  tvs_cps_backend->>tvs_cps_inventory: GET /api/v1/inventory/bin/get (+16 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvs-cps-backend | tvs-cps-inventory | GET /api/v1/inventory/bin/get, GET /api/v1/inventory/location/get, GET /api/v1/inventory/rack/get (+14 more) | APIResponse<AddDeliveryDateResponseDto>, APIResponse<BinResponseDto>, APIResponse<BinResponseDto[]>, APIResponse<LocationResponseDto>, APIResponse<LocationResponseDto[]> (+22 more) | sync | high |

Data touched: tvs-cps-backend: postgres, postgres:nmazcpsdbsdev01-cmn-postgres-uks.postgres.database.azure.com:nmazcpsdbdev01-cps; tvs-cps-inventory: postgres:localhost:inventory_db

Failure points: hop 1 tvs-cps-backend → tvs-cps-inventory: criticality hard

Evidence:
- hop 1 (tvs-cps-backend → tvs-cps-inventory): `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:315`, `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/util/ApiPassthroughUtil.java:132`, `TVS-CPS-INVENTORY/src/main/java/com/tvsm/inventory/controller/BinController.java:24` (+32 more)

## Flow: tvs-cps-jobs--tvs-cps-inventory
Summary: Starting at `tvs-cps-jobs` (scheduled job(s) in tvs-cps-jobs (job-to-call link not resolved): CronJobScheduler.allBookingsScheduler, CronJobScheduler.allEnquiriesScheduler, CronJobScheduler.availableStockScheduler (+27 more); request to tvs-cps-jobs from outside the registry (no internal caller)), the flow passes through `tvs-cps-backend` and ends at `tvs-cps-inventory`, using 2 sync HTTP hop(s) and 0 async event hop(s); tvs-cps-inventory role: terminal; confidence high.

```mermaid
sequenceDiagram
  participant tvs_cps_jobs as tvs-cps-jobs
  participant tvs_cps_backend as tvs-cps-backend
  participant tvs_cps_inventory as tvs-cps-inventory
  tvs_cps_jobs->>tvs_cps_backend: POST /system/api/v1/analytic/booking/stats (+3 more)
  tvs_cps_backend->>tvs_cps_inventory: GET /api/v1/inventory/bin/get (+16 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvs-cps-jobs | tvs-cps-backend | POST /system/api/v1/analytic/booking/stats, POST /system/api/v1/analytics-dashboard/indicators/calculate, POST /system/api/v1/appointments/auto-close (+1 more) | APIResponse<map<string,object>>, AnalyticsDto, AnalyticsRequestDTO | sync | high |
| 2 | tvs-cps-backend | tvs-cps-inventory | GET /api/v1/inventory/bin/get, GET /api/v1/inventory/location/get, GET /api/v1/inventory/rack/get (+14 more) | APIResponse<AddDeliveryDateResponseDto>, APIResponse<BinResponseDto>, APIResponse<BinResponseDto[]>, APIResponse<LocationResponseDto>, APIResponse<LocationResponseDto[]> (+22 more) | sync | high |

Data touched: tvs-cps-backend: postgres, postgres:nmazcpsdbsdev01-cmn-postgres-uks.postgres.database.azure.com:nmazcpsdbdev01-cps; tvs-cps-inventory: postgres:localhost:inventory_db

Failure points: hop 1 tvs-cps-jobs → tvs-cps-backend: criticality hard; hop 2 tvs-cps-backend → tvs-cps-inventory: criticality hard

Evidence:
- hop 1 (tvs-cps-jobs → tvs-cps-backend): `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/controller/AnalyticsController.java:23`, `TVS-CPS-JOBS/src/main/java/com/tvsm/jobs/service/AnalyticsService.java:32`, `TVS-CPS-JOBS/src/main/java/com/tvsm/jobs/service/RestCallService.java:50` (+4 more)
- hop 2 (tvs-cps-backend → tvs-cps-inventory): `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:315`, `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/util/ApiPassthroughUtil.java:132`, `TVS-CPS-INVENTORY/src/main/java/com/tvsm/inventory/controller/BinController.java:24` (+32 more)

## Flow: tvs-cps-portal--tvs-cps-inventory
Summary: Starting at `tvs-cps-portal` (user action in tvs-cps-portal (frontend)), the flow passes through `tvs-cps-backend` and ends at `tvs-cps-inventory`, using 2 sync HTTP hop(s) and 0 async event hop(s); tvs-cps-inventory role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant tvs_cps_portal as tvs-cps-portal
  participant tvs_cps_backend as tvs-cps-backend
  participant tvs_cps_inventory as tvs-cps-inventory
  tvs_cps_portal->>tvs_cps_backend: GET /api/v1/announcement/get/{announcementId} (+128 more)
  tvs_cps_backend->>tvs_cps_inventory: GET /api/v1/inventory/bin/get (+16 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvs-cps-portal | tvs-cps-backend | GET /api/v1/announcement/get/{announcementId}, GET /api/v1/announcement/user/banners, GET /api/v1/appointments/{appointmentId} (+126 more) | APIResponse<AnnouncementResponseDto>, APIResponse<AnnouncementResponseDto[]>, APIResponse<AppointmentCountResponseDTO>, APIResponse<AppointmentDashboardResponseDTO>, APIResponse<AppointmentDetailResponseDTO> (+105 more) | sync | medium |
| 2 | tvs-cps-backend | tvs-cps-inventory | GET /api/v1/inventory/bin/get, GET /api/v1/inventory/location/get, GET /api/v1/inventory/rack/get (+14 more) | APIResponse<AddDeliveryDateResponseDto>, APIResponse<BinResponseDto>, APIResponse<BinResponseDto[]>, APIResponse<LocationResponseDto>, APIResponse<LocationResponseDto[]> (+22 more) | sync | high |

Data touched: tvs-cps-backend: postgres, postgres:nmazcpsdbsdev01-cmn-postgres-uks.postgres.database.azure.com:nmazcpsdbdev01-cps; tvs-cps-inventory: postgres:localhost:inventory_db

Failure points: hop 1 tvs-cps-portal → tvs-cps-backend: criticality hard; hop 2 tvs-cps-backend → tvs-cps-inventory: criticality hard

Evidence:
- hop 1 (tvs-cps-portal → tvs-cps-backend): `TVS-CPS-BACKEND/announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:31`, `TVS-CPS-PORTAL/channel-partner-system/src/services/notification.service.ts:140`, `TVS-CPS-PORTAL/channel-partner-system/src/services/notification.service.ts:144` (+194 more)
- hop 2 (tvs-cps-backend → tvs-cps-inventory): `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:315`, `TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/util/ApiPassthroughUtil.java:132`, `TVS-CPS-INVENTORY/src/main/java/com/tvsm/inventory/controller/BinController.java:24` (+32 more)

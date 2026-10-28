---
service_id: tvs-cps-backend
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# TVS-CPS-BACKEND — API Specification

## Authentication

`tvs-cps-backend` uses the shared `tvsm-be-core` framework security: JWT validation with a configured public key, multi-tenant header handling (`isHeaderXTenantIDOptional: true`) and a list of excluded (unauthenticated) paths such as `/actuator/**`, `/api/health/**`, `/swagger-ui/**`, `/api-docs/**`, `/permissions/**`, `/system/**`, `/api/v1/notification-action-config/**`, `/api/v1/notification-category/**`, `/api/v1/appointments/external/**` (`tvs-cps-app/src/main/resources/config/application.yml:103-133`). Per-endpoint roles: Unknown (not extracted). RBAC permission files are configured under `tvsm.core` (same file, header comment).

API contracts detected: openapi-3 via springdoc (/api-docs); openapi-3 via springdoc (/api-docs); openapi-3 via springdoc (/api-docs); openapi-3 via springdoc (/api-docs); openapi-3 via springdoc (/api-docs)

## Endpoint Index

`tvs-cps-backend` exposes 388 inbound HTTP endpoint(s) (from `inventory.json`).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/api/v1/announcement/get/{announcementId}` | Unknown | AnnouncementController.getAnnouncementById | tvs-cps-portal |
| GET | `/api/v1/announcement/user/banners` | Unknown | AnnouncementController.getHomeAnnouncementsForUser | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/announcement/admin/search` | Unknown | AnnouncementController.searchAnnouncements | tvs-cps-backend |
| POST | `/api/v1/announcement/create` | Unknown | AnnouncementController.createAnnouncement | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/announcement/delete/{announcementId}` | Unknown | AnnouncementController.deleteAnnouncement | tvs-cps-portal |
| POST | `/api/v1/announcement/read` | Unknown | AnnouncementController.markRead | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/announcement/update` | Unknown | AnnouncementController.updateAnnouncement | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/announcement/user/search` | Unknown | AnnouncementController.getAnnouncementsForUser | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/announcement/{announcementId}/media/add/{docType}` | Unknown | AnnouncementController.addMedia | tvs-cps-portal |
| POST | `/api/v1/announcement/{announcementId}/media/delete/{mediaId}` | Unknown | AnnouncementController.deleteMedia | tvs-cps-portal |
| GET | `/api/v1/appointments/bulk-upload/{bulkUploadId}/error` | Unknown | AppointmentController.getBulkUploadErrors | Unknown |
| GET | `/api/v1/appointments/master` | Unknown | AppointmentController.getAppointmentMasterData | tvs-cps-backend |
| GET | `/api/v1/appointments/{appointmentId}` | Unknown | AppointmentController.getAppointmentDetail | tvs-cps-portal |
| POST | `/api/v1/appointments/analytics/stats` | Unknown | AppointmentAnalyticsController.retrieveAppointmentIndicators | tvs-cps-backend |
| POST | `/api/v1/appointments/bulk-upload` | Unknown | AppointmentController.bulkUploadAppointments | tvs-cps-backend |
| POST | `/api/v1/appointments/bulk-upload/history` | Unknown | AppointmentController.getBulkUploadList | tvs-cps-backend |
| POST | `/api/v1/appointments/count` | Unknown | AppointmentController.getAppointmentCount | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/appointments/create` | Unknown | AppointmentController.createAppointment | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/appointments/dashboard` | Unknown | AppointmentController.getAppointmentDashboard | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/appointments/details` | Unknown | AppointmentController.getAppointmentsByFilter | tvs-cps-backend |
| POST | `/api/v1/appointments/download` | Unknown | AppointmentController.downloadAppointment | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/appointments/event/send` | Unknown | AppointmentController.eventSend | Unknown |
| POST | `/api/v1/appointments/external/create` | Unknown | ExternalAppointmentController.createAppointment | Unknown |
| POST | `/api/v1/appointments/list` | Unknown | AppointmentController.getAppointments | tvs-cps-backend, tvs-cps-portal |
| POST | `/api/v1/appointments/update` | Unknown | AppointmentController.updateAppointment | tvs-cps-backend, tvs-cps-portal |
| POST | `/system/api/v1/appointments/list` | Unknown | AppointmentSystemController.getAppointmentsForLeadAllocation | tvs-cps-backend |
| POST | `/system/api/v1/appointments/update` | Unknown | AppointmentSystemController.updateAppointment | tvs-cps-backend |
| POST | `/system/api/v2/appointments/auto-close` | Unknown | AppointmentJobController.autoCloseSyncAppointment | tvs-cps-backend |
| DELETE | `/api/v1/tenant-config/{tenantId}` | Unknown | TenantConfigController.deleteTenantConfig | Unknown |
| GET | `/api/v1/tenant-config/current` | Unknown | TenantConfigController.getCurrentTenantConfig | Unknown |
| GET | `/api/v1/tenant-config/{tenantId}` | Unknown | TenantConfigController.getTenantConfig | Unknown |
| GET | `/cps/api/reports/list` | Unknown | ReportsBFFController.getAvailableReports | tvs-cps-portal |
| GET | `/cps/api/v1/analytics-dashboard/indicators/get` | Unknown | L1DashboardController.getDashboardIndicatorData | tvs-cps-portal |
| GET | `/cps/api/v1/announcement/get/{announcementId}` | Unknown | AnnouncementBFFController.getAnnouncementById | Unknown |
| GET | `/cps/api/v1/announcement/user/banners` | Unknown | AnnouncementBFFController.getHomeAnnouncementsForUser | Unknown |
| GET | `/cps/api/v1/appointments/bulk-upload/{bulkUploadId}/error` | Unknown | AppointmentBFFController.getAppointmentBulkUploadErrors | Unknown |
| GET | `/cps/api/v1/appointments/master` | Unknown | AppointmentBFFController.getAggregatedAppointmentMasterData | Unknown |
| GET | `/cps/api/v1/appointments/{appointmentId}` | Unknown | AppointmentBFFController.getAppointmentDetail | Unknown |
| GET | `/cps/api/v1/billing/get/{invoiceNumber}` | Unknown | BillingBFFController.getInvoiceDetails | Unknown |
| GET | `/cps/api/v1/booking/get` | Unknown | BookingBFFController.getBookingByBookingId | tvs-cps-portal |
| GET | `/cps/api/v1/booking/get-booking-list` | Unknown | BookingBFFController.getBooking | tvs-cps-portal |
| GET | `/cps/api/v1/booking/master-data` | Unknown | BookingBFFController.getEnquiryMasterData | tvs-cps-portal |
| GET | `/cps/api/v1/cart/active-cart` | Unknown | CartBFFController.getActiveCart | tvs-cps-portal |
| GET | `/cps/api/v1/cart/{cartId}` | Unknown | CartBFFController.getCartById | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/assemblies` | Unknown | CatalogController.allAssembly | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/catalog-summary` | Unknown | CatalogController.getCatalogSummary | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/details/{partId}` | Unknown | CatalogController.getItemDetailsByPartId | Unknown |
| GET | `/cps/api/v1/catalogs/get/{partId}` | Unknown | CatalogController.getPartsDetails | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/labor/area/{brand}` | Unknown | CatalogController.getLabourArea | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/merchandise/categories` | Unknown | CatalogController.getMerchandiseCategories | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/merchandise/colors` | Unknown | CatalogController.getMerchandiseColors | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/merchandise/{partReferenceNo}` | Unknown | CatalogController.getMerchandiseByPartReferenceNo | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/parts` | Unknown | CatalogController.getParts | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/parts/vehicleCatalogSkus/{catalogSkuId}` | Unknown | CatalogController.getPartsForVehicleSKUID | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/vehicle` | Unknown | CatalogController.getVehicleDetail | tvs-cps-portal |
| GET | `/cps/api/v1/catalogs/vehicle-data` | Unknown | CatalogController.vehicleMasterdata | tvs-cps-portal |
| GET | `/cps/api/v1/channel-partner/list` | Unknown | ChannelPartnerBFFController.getChannelPartners | tvs-cps-portal |
| GET | `/cps/api/v1/claims/bulk-upload/{bulkUploadId}/error` | Unknown | ClaimBFFController.getClaimBulkUploadErrors | Unknown |
| GET | `/cps/api/v1/claims/grn/details/{grnId}` | Unknown | ClaimBFFController.getGrnDetails | tvs-cps-portal |
| GET | `/cps/api/v1/claims/master` | Unknown | ClaimBFFController.getAggregatedClaimMasterData | tvs-cps-portal |
| GET | `/cps/api/v1/claims/timeline/{claimCatalogMappingId}` | Unknown | ClaimBFFController.getCatalogTimeline | tvs-cps-portal |
| GET | `/cps/api/v1/claims/{claimId}` | Unknown | ClaimBFFController.getClaimDetails | tvs-cps-portal |
| GET | `/cps/api/v1/dashboard/cache/refresh/{type}` | Unknown | DashboardBFFController.refreshDashboardCache | Unknown |
| GET | `/cps/api/v1/dashboard/list/{type}` | Unknown | DashboardBFFController.getDashboardList | tvs-cps-portal |
| GET | `/cps/api/v1/docs/download/{docType}/**` | Unknown | DocController.downloadDocument | Unknown |
| GET | `/cps/api/v1/docs/stream/{docType}/**` | Unknown | DocController.streamVideo | Unknown |
| GET | `/cps/api/v1/docs/view/{docType}/**` | Unknown | DocController.viewDocument | Unknown |
| GET | `/cps/api/v1/enquiry/bulk-upload/{bulkUploadId}/error` | Unknown | EnquiryBFFController.getBulkUploadErrors | Unknown |
| GET | `/cps/api/v1/enquiry/get-enquiry` | Unknown | EnquiryBFFController.getEnquiry | tvs-cps-portal |
| GET | `/cps/api/v1/enquiry/getEnquiryMaster` | Unknown | EnquiryBFFController.getEnquiryMasterData | tvs-cps-portal |
| GET | `/cps/api/v1/enquiry/vehicles` | Unknown | EnquiryBFFController.getAllVehicles | tvs-cps-portal |
| GET | `/cps/api/v1/enquiry/vehicles/{model}/variants` | Unknown | EnquiryBFFController.getVehicleVariants | tvs-cps-portal |
| GET | `/cps/api/v1/grn/details/{grnId}` | Unknown | GrnBFFController.getGrnDetails | tvs-cps-portal |
| GET | `/cps/api/v1/inventory/accumulated-stock/{productCatalogId}` | Unknown | InventoryBFFController.getAccumulatedStock | tvs-cps-backend |
| GET | `/cps/api/v1/inventory/bin/get` | Unknown | InventoryBFFController.getBins | Unknown |
| GET | `/cps/api/v1/inventory/get/{productCatalogId}` | Unknown | InventoryBFFController.getInventoryBySku | Unknown |
| GET | `/cps/api/v1/inventory/location/get` | Unknown | InventoryBFFController.getLocations | Unknown |
| GET | `/cps/api/v1/inventory/rack/get` | Unknown | InventoryBFFController.getRacks | Unknown |
| GET | `/cps/api/v1/invoice/delivery-view/{invoiceId}` | Unknown | InvoiceBFFController.getInvoiceDeliveryView | tvs-cps-portal |
| GET | `/cps/api/v1/jobcards/bulk-upload/{bulkUploadId}/error` | Unknown | JobcardBFFController.getJobCardBulkUploadErrors | Unknown |
| GET | `/cps/api/v1/jobcards/master` | Unknown | JobcardBFFController.getJobCardMasterData | Unknown |
| GET | `/cps/api/v1/jobcards/{jobcardId}` | Unknown | JobcardBFFController.jobCardsDetails | Unknown |
| GET | `/cps/api/v1/location/address/autocomplete` | Unknown | LocationMasterController.getAddressAutocomplete | tvs-cps-portal |
| GET | `/cps/api/v1/location/address/details` | Unknown | LocationMasterController.getAddressDetails | tvs-cps-portal |
| GET | `/cps/api/v1/order` | Unknown | OrderBFFController.getOrders | tvs-cps-backend |
| GET | `/cps/api/v1/order/active-cart` | Unknown | OrderBFFController.getActiveCart | Unknown |
| GET | `/cps/api/v1/order/cancellation-reasons` | Unknown | OrderBFFController.getCancellationReasons | Unknown |
| GET | `/cps/api/v1/order/get` | Unknown | OrderBFFController.getOrder | tvs-cps-portal |
| GET | `/cps/api/v1/order/get-booking-list` | Unknown | OrderBFFController.getPartsDetails | tvs-cps-backend |
| GET | `/cps/api/v1/order/get-branch` | Unknown | OrderBFFController.getAllBranches | tvs-cps-backend, tvs-cps-portal |
| GET | `/cps/api/v1/order/get-draft` | Unknown | OrderBFFController.getAllDraftOrders | tvs-cps-backend |
| GET | `/cps/api/v1/order/orderedPartDetails` | Unknown | OrderBFFController.getOrderedPartsDetails | tvs-cps-portal |
| GET | `/cps/api/v1/order/part/get/{partId}` | Unknown | OrderBFFController.getPartsDetails | Unknown |
| GET | `/cps/api/v1/order/status-counts` | Unknown | OrderBFFController.getOrderStatusCounts | tvs-cps-portal |
| GET | `/cps/api/v1/permissions/user` | Unknown | PermissionBFFController.getUserPermissions | Unknown |
| GET | `/cps/api/v1/permissions/user-info` | Unknown | PermissionBFFController.getUserDetails | tvs-cps-portal |
| GET | `/cps/api/v1/permissions/user-role/list` | Unknown | PermissionBFFController.getAllUserRoles | tvs-cps-portal |
| GET | `/cps/api/v1/training/get/{trainingId}` | Unknown | TrainingBFFController.getTraining | tvs-cps-portal |
| GET | `/cps/api/v1/user/list-all` | Unknown | UmsBffController.getUserList | Unknown |
| GET | `/cps/api/v1/vehicle/global/get-by-vin/{vin}` | Unknown | InventoryBFFController.getVehicleByVin | Unknown |
| GET | `/cps/api/v1/workflow/instance/{workflowId}` | Unknown | WorkflowBFFController.getWorkflowInstance | Unknown |
| GET | `/cps/api/v1/workflow/instance/{workflowId}/status` | Unknown | WorkflowBFFController.getWorkflowStatus | Unknown |
| GET | `/cps/api/v1/workflow/items` | Unknown | WorkflowBFFController.getWorkflowItems | Unknown |
| GET | `/cps/api/v1/workflow/template/{entityOperationType}` | Unknown | WorkflowBFFController.getActiveTemplate | Unknown |
| GET | `/system/api/v1/vehicle/global/get-by-vin/{vin}` | Unknown | InternalServiceBFFController.getVehicleByVin | Unknown |
| GET | `/system/api/v1/vehicle/global/get/{vehicleId}` | Unknown | InternalServiceBFFController.getByVehicleId | Unknown |
| GET | `/system/user/{tenantId}/{dealerId}/by-id/{userId}` | Unknown | InternalServiceBFFController.getUmsUserById | Unknown |
| GET | `/system/user/{tenantId}/{dealerId}/{role}/list-all` | Unknown | InternalServiceBFFController.getUmsAuthUserList | Unknown |
| GET | `/system/user/{tenantId}/{dealerId}/{role}/list-all-employees` | Unknown | InternalServiceBFFController.getUmsEmployeeList | Unknown |
| PATCH | `/api/v1/tenant-config/{tenantId}/handler` | Unknown | TenantConfigController.patchTenantHandler | Unknown |
| POST | `/api/v1/tenant-config/create` | Unknown | TenantConfigController.createTenantConfigs | Unknown |
| POST | `/cps/api/reports/download` | Unknown | ReportsBFFController.downloadReport | tvs-cps-portal |
| POST | `/cps/api/v1/announcement/admin/search` | Unknown | AnnouncementBFFController.searchAnnouncements | Unknown |
| POST | `/cps/api/v1/announcement/create` | Unknown | AnnouncementBFFController.createAnnouncement | Unknown |
| POST | `/cps/api/v1/announcement/delete/{announcementId}` | Unknown | AnnouncementBFFController.deleteAnnouncement | Unknown |
| POST | `/cps/api/v1/announcement/read` | Unknown | AnnouncementBFFController.markRead | Unknown |
| POST | `/cps/api/v1/announcement/update` | Unknown | AnnouncementBFFController.updateAnnouncement | Unknown |
| POST | `/cps/api/v1/announcement/user/search` | Unknown | AnnouncementBFFController.getAnnouncementsForUser | Unknown |
| POST | `/cps/api/v1/announcement/{announcementId}/media/add/{docType}` | Unknown | AnnouncementBFFController.addMedia | Unknown |
| POST | `/cps/api/v1/announcement/{announcementId}/media/delete/{mediaId}` | Unknown | AnnouncementBFFController.deleteMedia | Unknown |
| POST | `/cps/api/v1/appointments/analytics/stats/process` | Unknown | AppointmentAnalyticsBFFController.processAppointmentStats | tvs-cps-backend |
| POST | `/cps/api/v1/appointments/bulk-upload` | Unknown | AppointmentBFFController.bulkUploadAppointments | Unknown |
| POST | `/cps/api/v1/appointments/bulk-upload/history` | Unknown | AppointmentBFFController.getBulkUploadAppointmentsHistory | Unknown |
| POST | `/cps/api/v1/appointments/count` | Unknown | AppointmentBFFController.getAppointmentCount | Unknown |
| POST | `/cps/api/v1/appointments/create` | Unknown | AppointmentBFFController.createAppointment | Unknown |
| POST | `/cps/api/v1/appointments/dashboard` | Unknown | AppointmentBFFController.getAppointmentDashboard | Unknown |
| POST | `/cps/api/v1/appointments/download` | Unknown | AppointmentBFFController.downloadAppointments | Unknown |
| POST | `/cps/api/v1/appointments/list` | Unknown | AppointmentBFFController.getAppointmentsList | Unknown |
| POST | `/cps/api/v1/appointments/update` | Unknown | AppointmentBFFController.updateAppointment | Unknown |
| POST | `/cps/api/v1/billing/create` | Unknown | BillingBFFController.createInvoice | tvs-cps-backend |
| POST | `/cps/api/v1/billing/discard` | Unknown | BillingBFFController.discardInvoice | Unknown |
| POST | `/cps/api/v1/billing/invoices/search` | Unknown | BillingBFFController.searchBillingInvoices | tvs-cps-backend |
| POST | `/cps/api/v1/billing/post-invoice` | Unknown | BillingBFFController.postInvoice | tvs-cps-backend |
| POST | `/cps/api/v1/billing/report/invoice-list` | Unknown | BillingReportController.getAggregatedInvoiceReport | tvs-cps-backend |
| POST | `/cps/api/v1/billing/update` | Unknown | BillingBFFController.updateInvoice | Unknown |
| POST | `/cps/api/v1/booking/cancel` | Unknown | BookingBFFController.cancelBooking | tvs-cps-portal |
| POST | `/cps/api/v1/booking/create` | Unknown | BookingBFFController.createBooking | tvs-cps-portal |
| POST | `/cps/api/v1/booking/search` | Unknown | BookingBFFController.search | tvs-cps-portal |
| POST | `/cps/api/v1/booking/stats` | Unknown | BookingBFFController.bookingDashboard | tvs-cps-portal |
| POST | `/cps/api/v1/booking/update` | Unknown | BookingBFFController.updateBooking | tvs-cps-portal |
| POST | `/cps/api/v1/calendar/get` | Unknown | CalendarBFFController.getCalendar | tvs-cps-portal |
| POST | `/cps/api/v1/cart/bulk-upload` | Unknown | CartBFFController.bulkUploadCart | Unknown |
| POST | `/cps/api/v1/cart/create` | Unknown | CartBFFController.createCart | tvs-cps-portal |
| POST | `/cps/api/v1/cart/create-active-cart` | Unknown | CartBFFController.setActiveCart | tvs-cps-portal |
| POST | `/cps/api/v1/cart/delete/{cartId}` | Unknown | CartBFFController.deleteCart | tvs-cps-portal |
| POST | `/cps/api/v1/cart/reorder` | Unknown | CartBFFController.reorderCart | tvs-cps-portal |
| POST | `/cps/api/v1/cart/search` | Unknown | CartBFFController.searchCarts | tvs-cps-portal |
| POST | `/cps/api/v1/cart/update` | Unknown | CartBFFController.updateCart | tvs-cps-portal |
| POST | `/cps/api/v1/catalogs/all` | Unknown | CatalogController.getAll | tvs-cps-portal |
| POST | `/cps/api/v1/catalogs/product-details` | Unknown | CatalogController.getPAMDetails | tvs-cps-portal |
| POST | `/cps/api/v1/claims` | Unknown | ClaimBFFController.createClaims | tvs-cps-backend, tvs-cps-portal |
| POST | `/cps/api/v1/claims/analytics/stats/process` | Unknown | ClaimAnalyticsBFFController.processClaimStats | tvs-cps-backend |
| POST | `/cps/api/v1/claims/bulk-upload` | Unknown | ClaimBFFController.bulkUploadClaims | Unknown |
| POST | `/cps/api/v1/claims/bulk-upload/history` | Unknown | ClaimBFFController.bulkUploadClaimsHistory | Unknown |
| POST | `/cps/api/v1/claims/close` | Unknown | ClaimBFFController.closeClaim | tvs-cps-portal |
| POST | `/cps/api/v1/claims/dashboard` | Unknown | ClaimBFFController.getClaimDashboard | tvs-cps-portal |
| POST | `/cps/api/v1/claims/download` | Unknown | ClaimBFFController.downloadClaims | tvs-cps-portal |
| POST | `/cps/api/v1/claims/list` | Unknown | ClaimBFFController.getClaimsList | tvs-cps-portal |
| POST | `/cps/api/v1/collateral/create` | Unknown | CollateralBFFController.createCollateral | tvs-cps-portal |
| POST | `/cps/api/v1/collateral/search` | Unknown | CollateralBFFController.getCollaterals | tvs-cps-portal |
| POST | `/cps/api/v1/customer/add-vehicle` | Unknown | CustomerBFFController.addVehicleToCustomer | Unknown |
| POST | `/cps/api/v1/customer/create` | Unknown | CustomerBFFController.createCustomer | tvs-cps-backend |
| POST | `/cps/api/v1/customer/delete` | Unknown | CustomerBFFController.deleteCustomer | Unknown |
| POST | `/cps/api/v1/customer/inward-vehicle` | Unknown | CustomerBFFController.createCustomerWithVehicle | tvs-cps-portal |
| POST | `/cps/api/v1/customer/search` | Unknown | CustomerBFFController.searchCustomers | tvs-cps-backend |
| POST | `/cps/api/v1/customer/search-vehicle` | Unknown | CustomerBFFController.searchCustomersWithDatalake | tvs-cps-portal |
| POST | `/cps/api/v1/customer/update` | Unknown | CustomerBFFController.updateCustomer | tvs-cps-backend |
| POST | `/cps/api/v1/dashboard/create` | Unknown | DashboardBFFController.createDashboard | Unknown |
| POST | `/cps/api/v1/docs/delete/{docType}/**` | Unknown | DocController.deleteDocument | Unknown |
| POST | `/cps/api/v1/docs/upload` | Unknown | DocController.uploadDocument | tvs-cps-portal |
| POST | `/cps/api/v1/enquiry/bulk-assign` | Unknown | EnquiryBFFController.bulkAssignEnquiries | tvs-cps-portal |
| POST | `/cps/api/v1/enquiry/bulk-upload` | Unknown | EnquiryBFFController.bulkUploadEnquiries | Unknown |
| POST | `/cps/api/v1/enquiry/bulk-upload/history` | Unknown | EnquiryBFFController.getBulkUploadEnquiriesHistory | tvs-cps-portal |
| POST | `/cps/api/v1/enquiry/create` | Unknown | EnquiryBFFController.createEnquiry | tvs-cps-portal |
| POST | `/cps/api/v1/enquiry/filter` | Unknown | EnquiryBFFController.filterEnquiry | tvs-cps-portal |
| POST | `/cps/api/v1/enquiry/stats` | Unknown | EnquiryBFFController.enquiryStatusCount | tvs-cps-portal |
| POST | `/cps/api/v1/enquiry/update` | Unknown | EnquiryBFFController.updateEnquiry | tvs-cps-portal |
| POST | `/cps/api/v1/grn/complete` | Unknown | GrnBFFController.completeGrn | tvs-cps-portal |
| POST | `/cps/api/v1/grn/delivery-details/add` | Unknown | GrnBFFController.addDeliveryDetails | tvs-cps-portal |
| POST | `/cps/api/v1/grn/initiate` | Unknown | GrnBFFController.createGrn | tvs-cps-portal |
| POST | `/cps/api/v1/grn/search` | Unknown | GrnBFFController.searchGrns | tvs-cps-portal |
| POST | `/cps/api/v1/grn/update` | Unknown | GrnBFFController.updateGrn | tvs-cps-portal |
| POST | `/cps/api/v1/grn/update-claim-initiated` | Unknown | GrnBFFController.updateClaimInitiated | Unknown |
| POST | `/cps/api/v1/grn/upload-docs` | Unknown | GrnBFFController.uploadGrnDocument | tvs-cps-backend |
| POST | `/cps/api/v1/inventory/allocate` | Unknown | InventoryBFFController.allocate | tvs-cps-portal |
| POST | `/cps/api/v1/inventory/bin/create` | Unknown | InventoryBFFController.createBin | Unknown |
| POST | `/cps/api/v1/inventory/deallocate` | Unknown | InventoryBFFController.deallocate | tvs-cps-portal |
| POST | `/cps/api/v1/inventory/get-add-by-vin` | Unknown | WarrantyBFFController.getAddVin | tvs-cps-portal |
| POST | `/cps/api/v1/inventory/issue` | Unknown | InventoryBFFController.issueInventory | tvs-cps-backend |
| POST | `/cps/api/v1/inventory/list` | Unknown | InventoryBFFController.listInventory | Unknown |
| POST | `/cps/api/v1/inventory/location/create` | Unknown | InventoryBFFController.createLocation | Unknown |
| POST | `/cps/api/v1/inventory/rack/create` | Unknown | InventoryBFFController.createRack | Unknown |
| POST | `/cps/api/v1/inventory/receive` | Unknown | InventoryBFFController.receiveInventory | Unknown |
| POST | `/cps/api/v1/invoice/search` | Unknown | InvoiceBFFController.searchInvoices | tvs-cps-portal |
| POST | `/cps/api/v1/jobcards/bulk-upload` | Unknown | JobcardBFFController.saveJobCardBulkUploads | Unknown |
| POST | `/cps/api/v1/jobcards/bulk-upload/history` | Unknown | JobcardBFFController.getJobCardBulkUploads | Unknown |
| POST | `/cps/api/v1/jobcards/create` | Unknown | JobcardBFFController.createJobCards | tvs-cps-portal |
| POST | `/cps/api/v1/jobcards/dashboard` | Unknown | JobcardBFFController.getJobcardDashboard | Unknown |
| POST | `/cps/api/v1/jobcards/download` | Unknown | JobcardBFFController.downloadJobcards | Unknown |
| POST | `/cps/api/v1/jobcards/invoice/generate` | Unknown | JobcardBFFController.createInvoice | tvs-cps-portal |
| POST | `/cps/api/v1/jobcards/list` | Unknown | JobcardBFFController.getJobCards | Unknown |
| POST | `/cps/api/v1/jobcards/warranty-check` | Unknown | JobcardBFFController.vehicleAndPartWarrantyCheck | Unknown |
| POST | `/cps/api/v1/lead-allocation/assign` | Unknown | LeadAllocationBFFController.assignDefaultUsers | Unknown |
| POST | `/cps/api/v1/lead-allocation/list` | Unknown | LeadAllocationBFFController.getLeadAllocationList | tvs-cps-portal |
| POST | `/cps/api/v1/lead-allocation/update` | Unknown | LeadAllocationBFFController.updateAllocation | tvs-cps-portal |
| POST | `/cps/api/v1/lead/dashboard` | Unknown | LeadServiceBFFController.getLeadServiceDashboard | tvs-cps-portal |
| POST | `/cps/api/v1/lead/details` | Unknown | LeadServiceBFFController.getLeadDetails | tvs-cps-portal |
| POST | `/cps/api/v1/lead/filter` | Unknown | LeadServiceBFFController.getAllLeads | tvs-cps-portal |
| POST | `/cps/api/v1/lead/update` | Unknown | LeadServiceBFFController.createFollowUp | tvs-cps-portal |
| POST | `/cps/api/v1/notification-category/all` | Unknown | NotificationCategoryBFFController.getAllCategoriesUnfiltered | tvs-cps-portal |
| POST | `/cps/api/v1/notification-category/cache/refresh` | Unknown | NotificationCategoryBFFController.refreshCategoriesCache | Unknown |
| POST | `/cps/api/v1/notification-category/list` | Unknown | NotificationCategoryBFFController.getAllCategories | Unknown |
| POST | `/cps/api/v1/notification-category/role-mapping/reload` | Unknown | NotificationCategoryBFFController.reloadCategoryRoleMapping | Unknown |
| POST | `/cps/api/v1/notification-device/deregister` | Unknown | NotificationDeviceBFFController.deregisterDeviceForUser | tvs-cps-portal |
| POST | `/cps/api/v1/notification-device/register` | Unknown | NotificationDeviceBFFController.registerDeviceForUser | tvs-cps-portal |
| POST | `/cps/api/v1/notification-events/publish` | Unknown | NotificationEventBFFController.publishAsync | Unknown |
| POST | `/cps/api/v1/notification-events/publish/sync` | Unknown | NotificationEventBFFController.publishSync | Unknown |
| POST | `/cps/api/v1/notification-events/trigger` | Unknown | NotificationEventTriggerController.triggerEvent | Unknown |
| POST | `/cps/api/v1/notification-message/read/all` | Unknown | NotificationMessageBFFController.markAllAsReadForUser | Unknown |
| POST | `/cps/api/v1/notification-message/read/bulk` | Unknown | NotificationMessageBFFController.bulkMarkAsReadForUser | Unknown |
| POST | `/cps/api/v1/notification-message/read/{messageId}` | Unknown | NotificationMessageBFFController.markAsReadForUser | tvs-cps-portal |
| POST | `/cps/api/v1/notification-message/search` | Unknown | NotificationMessageBFFController.searchMessagesByUserId | tvs-cps-portal |
| POST | `/cps/api/v1/notification-preference/list` | Unknown | NotificationPreferenceBFFController.getPreferencesByUser | tvs-cps-portal |
| POST | `/cps/api/v1/notification-preference/update` | Unknown | NotificationPreferenceBFFController.updatePreferencesByUserId | tvs-cps-portal |
| POST | `/cps/api/v1/npqr/create` | Unknown | NpqrBFFController.createQualityReport | tvs-cps-portal |
| POST | `/cps/api/v1/npqr/list` | Unknown | NpqrBFFController.getQualityReportList | tvs-cps-portal |
| POST | `/cps/api/v1/order/bulk-upload` | Unknown | OrderBFFController.bulkUploadOrders | Unknown |
| POST | `/cps/api/v1/order/cancel` | Unknown | OrderBFFController.cancelOrder | tvs-cps-portal |
| POST | `/cps/api/v1/order/create` | Unknown | OrderBFFController.createOrder | Unknown |
| POST | `/cps/api/v1/order/create-active-cart` | Unknown | OrderBFFController.createActiveCart | Unknown |
| POST | `/cps/api/v1/order/delete-order/{id}` | Unknown | OrderBFFController.deleteOrder | Unknown |
| POST | `/cps/api/v1/order/draft/update` | Unknown | OrderBFFController.handleOrderAction | tvs-cps-portal |
| POST | `/cps/api/v1/order/get-all-order` | Unknown | OrderBFFController.getAllOrders | tvs-cps-backend |
| POST | `/cps/api/v1/order/get-all-parts` | Unknown | OrderBFFController.getAllParts | tvs-cps-backend |
| POST | `/cps/api/v1/order/get-placed-order` | Unknown | OrderBFFController.getPlacedOrder | tvs-cps-backend |
| POST | `/cps/api/v1/order/place-order` | Unknown | OrderBFFController.placeOrder | tvs-cps-portal |
| POST | `/cps/api/v1/order/reorder` | Unknown | OrderBFFController.reorder | Unknown |
| POST | `/cps/api/v1/order/sale-order-no/list` | Unknown | OrderBFFController.retrieveERPSaleNumber | Unknown |
| POST | `/cps/api/v1/order/search` | Unknown | OrderBFFController.searchOrder | Unknown |
| POST | `/cps/api/v1/order/search/{partNumber}` | Unknown | OrderBFFController.searchByPartNumber | Unknown |
| POST | `/cps/api/v1/order/update-allocation` | Unknown | OrderBFFController.updateOrderLineAllocation | tvs-cps-portal |
| POST | `/cps/api/v1/order/workflow/update` | Unknown | OrderBFFController.workflowUpdate | Unknown |
| POST | `/cps/api/v1/otp/generate` | Unknown | NotificationBFFController.generateOtp | tvs-cps-portal |
| POST | `/cps/api/v1/otp/notify` | Unknown | NotificationBFFController.notifyOtp | Unknown |
| POST | `/cps/api/v1/otp/verify` | Unknown | NotificationBFFController.validateOtp | tvs-cps-portal |
| POST | `/cps/api/v1/smart-search/additional-details` | Unknown | SmartSearchBFFController.smartSearchAdditionalDetails | tvs-cps-portal |
| POST | `/cps/api/v1/smart-search/details` | Unknown | SmartSearchBFFController.smartSearchDetails | tvs-cps-portal |
| POST | `/cps/api/v1/smart-search/search` | Unknown | SmartSearchBFFController.smartSearch | tvs-cps-portal |
| POST | `/cps/api/v1/training/create` | Unknown | TrainingBFFController.createTraining | tvs-cps-portal |
| POST | `/cps/api/v1/training/read` | Unknown | TrainingBFFController.recordTrainingRead | tvs-cps-portal |
| POST | `/cps/api/v1/training/search` | Unknown | TrainingBFFController.getTrainings | tvs-cps-portal |
| POST | `/cps/api/v1/vehicle/delivery` | Unknown | InventoryBFFController.markVehicleDelivery | tvs-cps-portal |
| POST | `/cps/api/v1/vehicle/delivery-date/add` | Unknown | InventoryBFFController.addVehicleDeliveryDate | Unknown |
| POST | `/cps/api/v1/vehicle/inventory/lookup` | Unknown | InventoryBFFController.vehicleInventoryLookup | Unknown |
| POST | `/cps/api/v1/vehicle/pdi` | Unknown | InventoryBFFController.updatePDiDone | Unknown |
| POST | `/cps/api/v1/vehicle/submit-inspection` | Unknown | VehicleBFFController.submitInspection | tvs-cps-portal |
| POST | `/cps/api/v1/vehicle/update/stock-type` | Unknown | InventoryBFFController.updateStockType | Unknown |
| POST | `/cps/api/v1/vehiclesearch` | Unknown | VehicleBFFController.searchCustomersByVehicle | Unknown |
| POST | `/cps/api/v1/warranty-registration/create` | Unknown | WarrantyBFFController.createWarranty | tvs-cps-portal |
| POST | `/cps/api/v1/warranty-registration/search` | Unknown | WarrantyBFFController.listWarranties | Unknown |
| POST | `/cps/api/v1/workflow/action` | Unknown | WorkflowBFFController.performWorkflowAction | tvs-cps-portal |
| POST | `/cps/api/v1/workflow/init` | Unknown | WorkflowBFFController.initializeWorkflow | tvs-cps-backend |
| POST | `/cps/api/v1/workflow/template/create` | Unknown | WorkflowBFFController.createTemplate | Unknown |
| POST | `/cps/api/v1/workflow/template/process-activations` | Unknown | WorkflowBFFController.processTemplateActivations | Unknown |
| POST | `/cps/api/v1/workflow/template/update` | Unknown | WorkflowBFFController.updateTemplate | Unknown |
| POST | `/system/api/v1/analytic/booking/stats` | Unknown | AnalyticsController.retrieveBooking | tvs-cps-jobs |
| POST | `/system/api/v1/analytics-dashboard/indicators/calculate` | Unknown | InternalServiceBFFController.calculateDashboardIndicators | tvs-cps-jobs |
| POST | `/system/api/v1/appointments/auto-close` | Unknown | InternalServiceBFFController.autoCloseAppointments | tvs-cps-jobs |
| POST | `/system/api/v1/claims/sap-sync` | Unknown | InternalServiceBFFController.claimSAPSync | tvs-cps-jobs |
| POST | `/system/api/v1/invoice/insert` | Unknown | InternalServiceBFFController.insertInvoice | Unknown |
| POST | `/system/api/v1/order/sale-order-no/list` | Unknown | InternalServiceBFFController.retrieveERPDetails | Unknown |
| POST | `/system/api/v1/order/sync-erp-status` | Unknown | InternalServiceBFFController.syncErpOrderStatus | Unknown |
| POST | `/system/system/api/v1/inventory/analytics/list` | Unknown | InventoryAnalyticsBFFController.productCatalogCount | Unknown |
| PUT | `/cps/api/v1/claims/update` | Unknown | ClaimBFFController.updateClaim | tvs-cps-portal |
| PUT | `/cps/api/v1/jobcards/update` | Unknown | JobcardBFFController.updateJobCards | Unknown |
| PUT | `/cps/api/v1/order/update` | Unknown | OrderBFFController.updateOrder | Unknown |
| PUT | `/cps/api/v1/workflow/template/{id}/decommission` | Unknown | WorkflowBFFController.decommissionTemplate | Unknown |
| GET | `/api/v1/claims/bulk-upload/{bulkUploadId}/error` | Unknown | ClaimController.getBulkUploadErrors | Unknown |
| GET | `/api/v1/claims/master` | Unknown | ClaimController.getClaimMasterData | tvs-cps-backend |
| GET | `/api/v1/claims/timeline/{claimCatalogMappingId}` | Unknown | ClaimController.getCatalogTimeline | Unknown |
| GET | `/api/v1/claims/{claimId}` | Unknown | ClaimController.getClaimDetails | Unknown |
| POST | `/api/v1/claims` | Unknown | ClaimController.createClaims | tvs-cps-backend |
| POST | `/api/v1/claims/analytics/stats` | Unknown | ClaimAnalyticsController.retrieveClaimIndicators | tvs-cps-backend |
| POST | `/api/v1/claims/bulk-upload` | Unknown | ClaimController.bulkUploadClaims | tvs-cps-backend |
| POST | `/api/v1/claims/bulk-upload/history` | Unknown | ClaimController.getBulkUploadList | tvs-cps-backend |
| POST | `/api/v1/claims/close` | Unknown | ClaimController.closeClaim | tvs-cps-backend |
| POST | `/api/v1/claims/dashboard` | Unknown | ClaimController.getClaimDashboard | tvs-cps-backend |
| POST | `/api/v1/claims/details` | Unknown | ClaimController.getClaimsByVinAndStatus | tvs-cps-backend |
| POST | `/api/v1/claims/download` | Unknown | ClaimController.downloadClaims | tvs-cps-backend |
| POST | `/api/v1/claims/list` | Unknown | ClaimController.getClaims | tvs-cps-backend |
| POST | `/api/v1/claims/workflow/update` | Unknown | ClaimController.workflowUpdate | Unknown |
| POST | `/system/api/v2/claims/sap-sync` | Unknown | ClaimJobController.sapDataLakeSyncClaims | tvs-cps-backend |
| PUT | `/api/v1/claims/update` | Unknown | ClaimController.updateClaim | tvs-cps-backend |
| POST | `/api/v1/collateral/create` | Unknown | CollateralController.createCollateral | tvs-cps-backend |
| POST | `/api/v1/collateral/search` | Unknown | CollateralController.getCollaterals | tvs-cps-backend |
| POST | `/api/v1/lead-allocation/assign` | Unknown | LeadAllocationController.assignDefaultUsers | tvs-cps-backend |
| POST | `/api/v1/lead-allocation/list` | Unknown | LeadAllocationController.getLeadAllocationList | tvs-cps-backend |
| POST | `/api/v1/lead-allocation/tracker/get` | Unknown | LeadAllocationController.getTracker | tvs-cps-backend |
| POST | `/api/v1/lead-allocation/tracker/upsert` | Unknown | LeadAllocationController.upsertTracker | tvs-cps-backend |
| POST | `/api/v1/lead-allocation/update` | Unknown | LeadAllocationController.updateAllocation | tvs-cps-backend |
| POST | `/system/api/v1/lead-allocation/list` | Unknown | LeadAllocationSystemController.getLeadAllocationList | tvs-cps-backend |
| POST | `/system/api/v1/lead-allocation/tracker/get` | Unknown | LeadAllocationSystemController.getTracker | tvs-cps-backend |
| POST | `/system/api/v1/lead-allocation/tracker/upsert` | Unknown | LeadAllocationSystemController.upsertTracker | tvs-cps-backend |
| GET | `/api/v1/notification-action-config/all` | Unknown | NotificationActionConfigController.getAllActiveConfigs | Unknown |
| GET | `/api/v1/notification-action-config/event-type/{eventType}` | Unknown | NotificationActionConfigController.getByEventType | Unknown |
| GET | `/api/v1/notification-action-config/subcategory/{subcategoryCode}` | Unknown | NotificationActionConfigController.getBySubcategoryCode | Unknown |
| GET | `/api/v1/notification-category/by-subcategory-code/{code}` | Unknown | NotificationCategoryController.getCategoryBySubCategoryCode | Unknown |
| POST | `/api/v1/notification-action-config/cache/refresh` | Unknown | NotificationActionConfigController.refreshCache | Unknown |
| POST | `/api/v1/notification-category/all` | Unknown | NotificationCategoryController.getAllCategories | tvs-cps-backend |
| POST | `/api/v1/notification-category/cache/refresh` | Unknown | NotificationCategoryController.refreshCache | tvs-cps-backend |
| POST | `/api/v1/notification-category/list` | Unknown | NotificationCategoryController.getCategoriesForUser | tvs-cps-backend |
| POST | `/api/v1/notification-category/role-mapping/reload` | Unknown | NotificationCategoryController.reloadRoleMapping | tvs-cps-backend |
| POST | `/api/v1/notification-device/deregister` | Unknown | NotificationDeviceController.deregisterDeviceForUser | tvs-cps-backend |
| POST | `/api/v1/notification-device/register` | Unknown | NotificationDeviceController.registerDeviceForUser | tvs-cps-backend |
| POST | `/api/v1/notification-event-consumer/process` | Unknown | NotificationEventConsumerController.process | Unknown |
| POST | `/api/v1/notification-message/push/send` | Unknown | NotificationMessageController.sendPushNotification | Unknown |
| POST | `/api/v1/notification-message/read/all` | Unknown | NotificationMessageController.markAllAsReadForUser | tvs-cps-backend |
| POST | `/api/v1/notification-message/read/bulk` | Unknown | NotificationMessageController.bulkMarkAsReadForUser | tvs-cps-backend |
| POST | `/api/v1/notification-message/read/{messageId}` | Unknown | NotificationMessageController.markAsReadForUser | Unknown |
| POST | `/api/v1/notification-message/search` | Unknown | NotificationMessageController.searchMessagesByUserId | tvs-cps-backend |
| POST | `/api/v1/notification-preference/list` | Unknown | NotificationPreferenceController.getPreferencesByUserIdFromRequest | tvs-cps-backend |
| POST | `/api/v1/notification-preference/update` | Unknown | NotificationPreferenceController.updatePreferencesByUserId | tvs-cps-backend |
| POST | `/system/api/v1/notification-seed/reseed` | Unknown | NotificationSeedController.reseed | Unknown |
| POST | `/api/v1/npqr/create` | Unknown | NpqrController.createQualityReport | tvs-cps-backend |
| POST | `/api/v1/npqr/list` | Unknown | NpqrController.getQualityReportList | tvs-cps-backend |
| GET | `/api/v1/cart/active-cart` | Unknown | CartController.getActiveCart | tvs-cps-backend |
| GET | `/api/v1/cart/{cartId}` | Unknown | CartController.getCartById | Unknown |
| GET | `/api/v1/grn/details/{grnId}` | Unknown | GrnController.getGrnDetails | Unknown |
| GET | `/api/v1/invoice/delivery-view/{invoiceId}` | Unknown | InvoiceController.getInvoiceDeliveryView | Unknown |
| GET | `/api/v1/order/active-cart` | Unknown | OrderController.getActiveCart | tvs-cps-backend |
| GET | `/api/v1/order/cancellation-reasons` | Unknown | OrderController.getCancellationReasons | tvs-cps-backend |
| GET | `/api/v1/order/get` | Unknown | OrderController.getOrder | tvs-cps-backend |
| GET | `/api/v1/order/open-qty/{productCatalogId}` | Unknown | OrderController.getOpenQtyByProductCatalogId | Unknown |
| GET | `/api/v1/order/orderedPartDetails` | Unknown | OrderController.getOrderedPartsDetails | tvs-cps-backend |
| GET | `/api/v1/order/status-counts` | Unknown | OrderController.getOrderStatusCounts | tvs-cps-backend |
| POST | `/api/v1/cart/bulk-upload` | Unknown | CartController.bulkUploadCart | tvs-cps-backend |
| POST | `/api/v1/cart/create` | Unknown | CartController.createCart | tvs-cps-backend |
| POST | `/api/v1/cart/create-active-cart` | Unknown | CartController.setActiveCart | tvs-cps-backend |
| POST | `/api/v1/cart/delete/{cartId}` | Unknown | CartController.deleteCart | Unknown |
| POST | `/api/v1/cart/reorder` | Unknown | CartController.reorderCart | tvs-cps-backend |
| POST | `/api/v1/cart/search` | Unknown | CartController.searchCarts | tvs-cps-backend |
| POST | `/api/v1/cart/update` | Unknown | CartController.updateCart | tvs-cps-backend |
| POST | `/api/v1/grn/complete` | Unknown | GrnController.completeGrn | tvs-cps-backend |
| POST | `/api/v1/grn/delivery-details/add` | Unknown | GrnController.addDeliveryDetails | tvs-cps-backend |
| POST | `/api/v1/grn/initiate` | Unknown | GrnController.createGrn | tvs-cps-backend |
| POST | `/api/v1/grn/search` | Unknown | GrnController.searchGrns | tvs-cps-backend |
| POST | `/api/v1/grn/update` | Unknown | GrnController.updateGrn | tvs-cps-backend |
| POST | `/api/v1/grn/update-claim-initiated` | Unknown | GrnController.updateClaimInitiated | tvs-cps-backend |
| POST | `/api/v1/invoice/sample-insert` | Unknown | InvoiceController.createInvoiceForOrder | Unknown |
| POST | `/api/v1/invoice/search` | Unknown | InvoiceController.searchInvoices | tvs-cps-backend |
| POST | `/api/v1/order/bulk-upload` | Unknown | OrderController.bulkUploadOrders | tvs-cps-backend |
| POST | `/api/v1/order/cancel` | Unknown | OrderController.cancelOrder | tvs-cps-backend |
| POST | `/api/v1/order/create` | Unknown | OrderController.createOrder | tvs-cps-backend |
| POST | `/api/v1/order/create-active-cart` | Unknown | OrderController.setCart | tvs-cps-backend |
| POST | `/api/v1/order/delete-order/{id}` | Unknown | OrderController.deleteOrder | Unknown |
| POST | `/api/v1/order/draft/update` | Unknown | OrderController.handleOrderAction | tvs-cps-backend |
| POST | `/api/v1/order/place-order` | Unknown | OrderController.placeOrder | tvs-cps-backend |
| POST | `/api/v1/order/reorder` | Unknown | OrderController.reorder | tvs-cps-backend |
| POST | `/api/v1/order/report` | Unknown | OrderReportController.getOrderReport | tvs-cps-backend |
| POST | `/api/v1/order/sale-order-no/list` | Unknown | OrderController.retrieveERPSaleNumber | tvs-cps-backend |
| POST | `/api/v1/order/search` | Unknown | OrderController.searchOrders | tvs-cps-backend |
| POST | `/api/v1/order/status/reconciliation` | Unknown | OrderController.reconciliationOrderStatusFromGRN | Unknown |
| POST | `/api/v1/order/sync-erp-status` | Unknown | OrderController.syncErpOrderStatus | Unknown |
| POST | `/api/v1/order/update-allocation` | Unknown | OrderController.updateOrderLineAllocation | tvs-cps-backend |
| POST | `/api/v1/order/workflow/update` | Unknown | OrderController.workflowUpdate | tvs-cps-backend |
| POST | `/system/api/v1/erp-invoice/insert` | Unknown | InternalERPServiceController.insertERPInvoice | tvs-cps-backend |
| POST | `/system/api/v1/order/analytics` | Unknown | OrderAnalyticsController.retrieveBooking | tvs-cps-backend |
| POST | `/system/api/v1/order/erp-sale-order-no/list` | Unknown | InternalERPServiceController.retrieveERPSaleNumber | tvs-cps-backend |
| POST | `/system/api/v1/order/erp-sync-status` | Unknown | InternalERPServiceController.syncErpOrderStatus | tvs-cps-backend |
| PUT | `/api/v1/order/update` | Unknown | OrderController.updateOrder | tvs-cps-backend |
| GET | `/api/v1/training/get/{trainingId}` | Unknown | TrainingController.getTraining | Unknown |
| POST | `/api/v1/training/create` | Unknown | TrainingController.createTraining | tvs-cps-backend |
| POST | `/api/v1/training/read` | Unknown | TrainingController.recordTrainingRead | tvs-cps-backend |
| POST | `/api/v1/training/search` | Unknown | TrainingController.getTrainings | tvs-cps-backend |
| GET | `/api/health` | Unknown | ApplicationHealthController.health | Unknown |
| GET | `/api/health/simple` | Unknown | ApplicationHealthController.simpleHealth | Unknown |
| GET | `/api/v1/workflow/instance/{workflowId}` | Unknown | WorkflowController.getWorkflowDetail | Unknown |
| GET | `/api/v1/workflow/instance/{workflowId}/status` | Unknown | WorkflowController.getWorkflowStatus | Unknown |
| GET | `/api/v1/workflow/items` | Unknown | WorkflowController.getWorkflowItems | tvs-cps-backend |
| GET | `/api/v1/workflow/template/{entityOperationType}` | Unknown | WorkflowTemplateController.getActiveTemplate | Unknown |
| POST | `/api/v1/workflow/action` | Unknown | WorkflowController.performAction | tvs-cps-backend |
| POST | `/api/v1/workflow/assignment/process` | Unknown | UserAssignmentController.processAssignment | Unknown |
| POST | `/api/v1/workflow/init` | Unknown | WorkflowController.initializeWorkflow | tvs-cps-backend |
| POST | `/api/v1/workflow/template/create` | Unknown | WorkflowTemplateController.createTemplate | tvs-cps-backend |
| POST | `/api/v1/workflow/template/process-activations` | Unknown | WorkflowTemplateController.processTemplateActivations | tvs-cps-backend |
| POST | `/api/v1/workflow/template/update` | Unknown | WorkflowTemplateController.updateTemplate | tvs-cps-backend |
| POST | `/system/api/v1/workflow/assignment/process` | Unknown | UserAssignmentSystemController.processAssignment | Unknown |
| PUT | `/api/v1/workflow/template/{id}/decommission` | Unknown | WorkflowTemplateController.decommissionTemplate | Unknown |

### Scheduled Jobs

| Job | Trigger | Expression | Expression from | Handler |
|---|---|---|---|---|
| JobScheduler.loadCatalogData | cron | `0 0 0/2 * * *` | config:catalog.cron.schedule | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:111` |
| JobScheduler.retrieveMDPDealers | cron | `0 0 0/2 * * *` | config:mdp.dealer.cron.schedule | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:65` |
| JobScheduler.retrieveMerchandiseStock | cron | `0 0 * * * *` | config:merchandise.oem-stock.cron.schedule | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:80` |
| JobScheduler.warmUpUmsCache | cron | `0 0 */2 * * *` | config:ums.cache.cron.schedule | `bff-service/src/main/java/com/tvsm/bff/scheduler/JobScheduler.java:93` |
| NotificationDeviceCleanupScheduler.deactivateStaleDevices | cron | `0 0 2 * * *` | config:notification.device.cleanup-cron | `notification-service/src/main/java/com/tvsm/notification/scheduler/NotificationDeviceCleanupScheduler.java:36` |

## Endpoints

`tvs-cps-backend` endpoint details. Field tables come from schemas resolved in code; `Unknown` means the extractor could not resolve the type.

### GET /api/v1/announcement/get/{announcementId}

Handler: `AnnouncementController.getAnnouncementById` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:119`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | uuid | True | — |

Response `200`: `APIResponse<AnnouncementResponseDto>` — fields Unknown (schema not resolved from code)


### GET /api/v1/announcement/user/banners

Handler: `AnnouncementController.getHomeAnnouncementsForUser` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:139`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| count | query | integer | False | — |

Response `200`: `APIResponse<AnnouncementResponseDto[]>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/admin/search

Handler: `AnnouncementController.searchAnnouncements` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:156`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AnnouncementSearchRequestDto` (defined in `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementSearchRequestDto.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| page | integer | False | minimum=0 |
| count | integer | False | minimum=1 |
| criticality | enum[LOW,MEDIUM,HIGH][] | False | — |
| validFrom | datetime | False | — |
| validTo | datetime | False | — |
| self | boolean | False | — |

Response `200`: `APIResponse<Page<AnnouncementResponseDto>>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/create

Handler: `AnnouncementController.createAnnouncement` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:42`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `AnnouncementRequestDto` (defined in `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementRequestDto.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| announcementId | uuid | False | — |
| title | string | False | — |
| description | string | False | — |
| validFrom | datetime | False | — |
| validTo | datetime | False | — |
| templateType | string | False | — |
| criticality | string | False | — |
| userAction | ActionButton[] | False | — |
| displayOnHome | boolean | False | — |
| targetAudience | map<enum[ADD,REMOVE],AnnouncementTargetAudienceDto[]> | False | — |
| externalLinks | string[] | False | — |

Response `200`: `APIResponse<AnnouncementResponseDto>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/delete/{announcementId}

Handler: `AnnouncementController.deleteAnnouncement` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:101`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | uuid | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/read

Handler: `AnnouncementController.markRead` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:216`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `AnnouncementReadLogRequestDto` (defined in `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementReadLogRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| announcementId | uuid | False | — |
| userId | string | False | — |
| auditUserAction | string | False | — |
| clickedAt | datetime | False | — |

Response `200`: `APIResponse<LogReadResponse>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/update

Handler: `AnnouncementController.updateAnnouncement` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:79`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `AnnouncementRequestDto` (defined in `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementRequestDto.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| announcementId | uuid | False | — |
| title | string | False | — |
| description | string | False | — |
| validFrom | datetime | False | — |
| validTo | datetime | False | — |
| templateType | string | False | — |
| criticality | string | False | — |
| userAction | ActionButton[] | False | — |
| displayOnHome | boolean | False | — |
| targetAudience | map<enum[ADD,REMOVE],AnnouncementTargetAudienceDto[]> | False | — |
| externalLinks | string[] | False | — |

Response `200`: `APIResponse<AnnouncementResponseDto>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/user/search

Handler: `AnnouncementController.getAnnouncementsForUser` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:58`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `AnnouncementSearchRequestDto` (defined in `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementSearchRequestDto.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| page | integer | False | minimum=0 |
| count | integer | False | minimum=1 |
| criticality | enum[LOW,MEDIUM,HIGH][] | False | — |
| validFrom | datetime | False | — |
| validTo | datetime | False | — |
| self | boolean | False | — |

Response `200`: `APIResponse<Page<AnnouncementResponseDto>>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/{announcementId}/media/add/{docType}

Handler: `AnnouncementController.addMedia` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:178`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | uuid | True | — |
| file | form | binary | True | — |
| mediaType | form | string | True | — |
| docType | path | string | True | — |

Response `200`: `APIResponse<MediaResponseDto>` — fields Unknown (schema not resolved from code)


### POST /api/v1/announcement/{announcementId}/media/delete/{mediaId}

Handler: `AnnouncementController.deleteMedia` (`announcement-service/src/main/java/com/tvsm/announcement/controller/AnnouncementController.java:196`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | uuid | True | — |
| mediaId | path | uuid | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)


### GET /api/v1/appointments/bulk-upload/{bulkUploadId}/error

Handler: `AppointmentController.getBulkUploadErrors` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:237`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bulkUploadId | path | uuid | True | — |

Response `200`: `APIResponse<BulkUploadErrorDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)


### GET /api/v1/appointments/master

Handler: `AppointmentController.getAppointmentMasterData` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:126`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |

Response `200`: `APIResponse<AppointmentMasterDataResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/appointments/{appointmentId}

Handler: `AppointmentController.getAppointmentDetail` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:89`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| appointmentId | path | string | True | — |

Response `200`: `APIResponse<AppointmentDetailResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/appointments/analytics/stats

Handler: `AppointmentAnalyticsController.retrieveAppointmentIndicators` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentAnalyticsController.java:33`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AnalyticsRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AnalyticsRequestDTO.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| jobCardIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| dealerId | string | False | — |

Response `200`: `APIResponse<AnalyticsResponseDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /api/v1/appointments/bulk-upload

Handler: `AppointmentController.bulkUploadAppointments` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:199`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `BulkUploadRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/BulkUploadRequestDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| parsedData | ParsedAppointmentData[] | False | — |
| bulkUploadDTO | AppointmentBulkUploadDTO | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/appointments/bulk-upload/history

Handler: `AppointmentController.getBulkUploadList` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:219`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<PageResponseDTO<AppointmentBulkUploadDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/count

Handler: `AppointmentController.getAppointmentCount` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:260`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<AppointmentCountResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/create

Handler: `AppointmentController.createAppointment` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:59`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `AppointmentCreateRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentCreateRequestDTO.java:21`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channel | enum[CPS,WEBSITE,SALES_FORCE,NORTON_CONNECT_APP] | True | — |
| entityType | string | True | — |
| entitySubType | string | True | — |
| appointmentDateTime | datetime | True | — |
| jobType | string | True | — |
| serviceType | string | True | — |
| followUpDateTime | datetime | True | — |
| remark | string | False | maxLength=500 |
| reason | string | False | — |
| cceId | string | False | — |
| executive | string | False | — |
| customerName | string | True | pattern=^([A-Za-z]+)(\s[A-Za-z]+){0,2}$ |
| context | AppointmentContextDTO[] | True | valid |
| customerVehicleDetails | map<string,CustomerVehicleDTO> | False | — |
| status | enum[AWAITING_ACTION,BOOKED,RESCHEDULED,CANCELLED,CLOSED,CONFIRMED] | False | — |
| lead_id | string | False | — |
| tenantId | string | False | — |
| channelPartnerId | string | False | — |
| vin | string | False | — |
| dealerName | string | False | — |

Response `200`: `APIResponse<AppointmentResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/dashboard

Handler: `AppointmentController.getAppointmentDashboard` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:144`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<AppointmentDashboardResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/details

Handler: `AppointmentController.getAppointmentsByFilter` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:104`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `StatusFilterRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/StatusFilterRequestDTO.java:21`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| filters | FilterEntry[] | True | valid |

Response `200`: `APIResponse<AppointmentDetailResponseDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/appointments/download

Handler: `AppointmentController.downloadAppointment` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:180`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |
| timeZone | query | string | True | — |
| channelPartnerId | query | string | False | — |

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<AppointmentsDownloadDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/event/send

Handler: `AppointmentController.eventSend` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:161`)  
Callers: Unknown  
Auth: Unknown

Request body: `AppointmentCreateEventDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentCreateEventDTO.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| payload | AppointmentCreateEventPayloadDTO | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/external/create

Handler: `ExternalAppointmentController.createAppointment` (`appointment-service/src/main/java/com/tvsm/appointment/controller/ExternalAppointmentController.java:45`)  
Callers: Unknown  
Auth: Unknown

Request body: `AppointmentCreateRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentCreateRequestDTO.java:21`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channel | enum[CPS,WEBSITE,SALES_FORCE,NORTON_CONNECT_APP] | True | — |
| entityType | string | True | — |
| entitySubType | string | True | — |
| appointmentDateTime | datetime | True | — |
| jobType | string | True | — |
| serviceType | string | True | — |
| followUpDateTime | datetime | True | — |
| remark | string | False | maxLength=500 |
| reason | string | False | — |
| cceId | string | False | — |
| executive | string | False | — |
| customerName | string | True | pattern=^([A-Za-z]+)(\s[A-Za-z]+){0,2}$ |
| context | AppointmentContextDTO[] | True | valid |
| customerVehicleDetails | map<string,CustomerVehicleDTO> | False | — |
| status | enum[AWAITING_ACTION,BOOKED,RESCHEDULED,CANCELLED,CLOSED,CONFIRMED] | False | — |
| lead_id | string | False | — |
| tenantId | string | False | — |
| channelPartnerId | string | False | — |
| vin | string | False | — |
| dealerName | string | False | — |

Response `200`: `APIResponse<AppointmentResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/list

Handler: `AppointmentController.getAppointments` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:44`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<PageResponseDTO<AppointmentResponseDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/appointments/update

Handler: `AppointmentController.updateAppointment` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentController.java:74`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `AppointmentUpdateRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentUpdateRequestDTO.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentId | string | False | — |
| status | string | False | — |
| appointmentDateTime | datetime | False | — |
| jobType | string | False | — |
| serviceType | string | False | — |
| followUpDateTime | datetime | False | — |
| remark | string | False | maxLength=500 |
| reason | string | False | — |
| cceId | string | False | — |
| executive | string | False | — |
| customerName | string | False | pattern=^([A-Za-z]+)(\s[A-Za-z]+){0,2}$ |
| followUpOperations | FollowUpOperationsRequestDTO | False | valid |
| channelPartnerId | string | False | — |
| tenantId | string | False | — |
| userId | string | False | — |

Response `200`: `APIResponse<AppointmentResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v1/appointments/list

Handler: `AppointmentSystemController.getAppointmentsForLeadAllocation` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentSystemController.java:34`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AppointmentSystemSearchRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentSystemSearchRequestDTO.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| tenantId | string | True | — |
| dealerId | string | True | — |
| page | integer | False | positiveOrZero |
| size | integer | False | positive;maximum=1000 |
| searchText | string | False | — |
| ids | string[] | False | — |
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| sort | SortOrder[] | False | — |

Response `200`: `APIResponse<PageResponseDTO<AppointmentResponseDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v1/appointments/update

Handler: `AppointmentSystemController.updateAppointment` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentSystemController.java:79`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AppointmentUpdateRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentUpdateRequestDTO.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentId | string | False | — |
| status | string | False | — |
| appointmentDateTime | datetime | False | — |
| jobType | string | False | — |
| serviceType | string | False | — |
| followUpDateTime | datetime | False | — |
| remark | string | False | maxLength=500 |
| reason | string | False | — |
| cceId | string | False | — |
| executive | string | False | — |
| customerName | string | False | pattern=^([A-Za-z]+)(\s[A-Za-z]+){0,2}$ |
| followUpOperations | FollowUpOperationsRequestDTO | False | valid |
| channelPartnerId | string | False | — |
| tenantId | string | False | — |
| userId | string | False | — |

Response `200`: `APIResponse<AppointmentResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v2/appointments/auto-close

Handler: `AppointmentJobController.autoCloseSyncAppointment` (`appointment-service/src/main/java/com/tvsm/appointment/controller/AppointmentJobController.java:32`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `APIResponse<AppointmentAutoCloseResponseDTO[]>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### DELETE /api/v1/tenant-config/{tenantId}

Handler: `TenantConfigController.deleteTenantConfig` (`bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java:87`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | path | string | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)


### GET /api/v1/tenant-config/current

Handler: `TenantConfigController.getCurrentTenantConfig` (`bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java:57`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `APIResponse<TenantConfigResponse>` — fields Unknown (schema not resolved from code)


### GET /api/v1/tenant-config/{tenantId}

Handler: `TenantConfigController.getTenantConfig` (`bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java:68`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | path | string | True | — |

Response `200`: `APIResponse<TenantConfigResponse>` — fields Unknown (schema not resolved from code)


### GET /cps/api/reports/list

Handler: `ReportsBFFController.getAvailableReports` (`bff-service/src/main/java/com/tvsm/bff/controller/ReportsBFFController.java:42`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/analytics-dashboard/indicators/get

Handler: `L1DashboardController.getDashboardIndicatorData` (`bff-service/src/main/java/com/tvsm/bff/controller/L1DashboardController.java:46`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| channelPartnerId | query | string | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/announcement/get/{announcementId}

Handler: `AnnouncementBFFController.getAnnouncementById` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:106`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/announcement/user/banners

Handler: `AnnouncementBFFController.getHomeAnnouncementsForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:122`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| count | query | integer | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/appointments/bulk-upload/{bulkUploadId}/error

Handler: `AppointmentBFFController.getAppointmentBulkUploadErrors` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:354`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bulkUploadId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/appointments/master

Handler: `AppointmentBFFController.getAggregatedAppointmentMasterData` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:212`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/appointments/{appointmentId}

Handler: `AppointmentBFFController.getAppointmentDetail` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:187`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| appointmentId | path | string | True | — |
| Authorization | header | string | True | — |

Response `200`: `AppointmentDetailsResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/AppointmentDetailsResponseDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | False | — |
| statusCode | string | False | — |
| message | string | False | — |
| data | DataDTO | False | — |

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/billing/get/{invoiceNumber}

Handler: `BillingBFFController.getInvoiceDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:164`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| invoiceNumber | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/booking/get

Handler: `BookingBFFController.getBookingByBookingId` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:70`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bookingId | query | string | True | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/booking/get-booking-list

Handler: `BookingBFFController.getBooking` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:83`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productCatalogId | query | string | True | — |
| includeOnlyUnorderedBookings | query | boolean | False | — |
| pageNumber | query | integer | False | — |
| pageSize | query | integer | False | — |

Response `200`: `APIResponse<BookingSearchResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/booking/master-data

Handler: `BookingBFFController.getEnquiryMasterData` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:108`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/cart/active-cart

Handler: `CartBFFController.getActiveCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:124`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderCategory | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/cart/{cartId}

Handler: `CartBFFController.getCartById` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:93`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| cartId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/assemblies

Handler: `CatalogController.allAssembly` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:210`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| brandCode | query | integer | False | — |

Response `200`: `APIResponse<AssemblyCategoryDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/catalog-summary

Handler: `CatalogController.getCatalogSummary` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:383`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productType | query | string | True | — |

Response `200`: `APIResponse<CatalogSummaryDto[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/details/{partId}

Handler: `CatalogController.getItemDetailsByPartId` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:271`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partId | path | string | True | — |
| orderCategoryType | query | string | True | — |

Response `200`: `APIResponse<PartDetailsDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### GET /cps/api/v1/catalogs/get/{partId}

Handler: `CatalogController.getPartsDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:259`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partId | path | string | True | — |

Response `200`: `APIResponse<PartDetailsDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/catalogs/labor/area/{brand}

Handler: `CatalogController.getLabourArea` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:335`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| brand | path | string | True | — |
| dealerRate | query | string | True | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/merchandise/categories

Handler: `CatalogController.getMerchandiseCategories` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:307`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<MerchandiseCategoryDto[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/merchandise/colors

Handler: `CatalogController.getMerchandiseColors` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:321`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<string[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/merchandise/{partReferenceNo}

Handler: `CatalogController.getMerchandiseByPartReferenceNo` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:289`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partReferenceNo | path | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/parts

Handler: `CatalogController.getParts` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:74`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| catalogType | query | string | True | — |
| catalogSkuId | query | string | False | — |
| part | query | string | False | — |
| modelName | query | string | False | — |
| variant | query | string | False | — |
| variantPartId | query | string | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/parts/vehicleCatalogSkus/{catalogSkuId}

Handler: `CatalogController.getPartsForVehicleSKUID` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:156`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| catalogSkuId | path | string | True | — |
| assembly | query | string | False | — |
| subAssembly | query | string | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/vehicle

Handler: `CatalogController.getVehicleDetail` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:196`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| catalogSkuId | query | string | False | — |

Response `200`: `APIResponse<map<string,object>[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/catalogs/vehicle-data

Handler: `CatalogController.vehicleMasterdata` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:244`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<map<string,object>[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/channel-partner/list

Handler: `ChannelPartnerBFFController.getChannelPartners` (`bff-service/src/main/java/com/tvsm/bff/controller/ChannelPartnerBFFController.java:32`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<TVSChannelPartner[]>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/claims/bulk-upload/{bulkUploadId}/error

Handler: `ClaimBFFController.getClaimBulkUploadErrors` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:542`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bulkUploadId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)


### GET /cps/api/v1/claims/grn/details/{grnId}

Handler: `ClaimBFFController.getGrnDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:450`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| grnId | path | string | True | — |

Response `200`: `APIResponse<GRNDetailsClaimBFFResponseDTO>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### GET /cps/api/v1/claims/master

Handler: `ClaimBFFController.getAggregatedClaimMasterData` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:390`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/claims/timeline/{claimCatalogMappingId}

Handler: `ClaimBFFController.getCatalogTimeline` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:311`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| claimCatalogMappingId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### GET /cps/api/v1/claims/{claimId}

Handler: `ClaimBFFController.getClaimDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:129`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| claimId | path | string | True | — |

Response `200`: `object` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### GET /cps/api/v1/dashboard/cache/refresh/{type}

Handler: `DashboardBFFController.refreshDashboardCache` (`bff-service/src/main/java/com/tvsm/bff/controller/DashboardBFFController.java:75`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| type | path | string | True | — |

Response `200`: `APIResponse<any>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/dashboard/list/{type}

Handler: `DashboardBFFController.getDashboardList` (`bff-service/src/main/java/com/tvsm/bff/controller/DashboardBFFController.java:43`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| type | path | string | True | — |

Response `200`: `DashboardListResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/DashboardListResponseDTO.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| overview | DashboardEntryDTO[] | False | — |
| reports | DashboardEntryDTO[] | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/docs/download/{docType}/**

Handler: `DocController.downloadDocument` (`bff-service/src/main/java/com/tvsm/bff/controller/DocController.java:94`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| docType | path | string | True | — |

Response `200`: `binary` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/docs/stream/{docType}/**

Handler: `DocController.streamVideo` (`bff-service/src/main/java/com/tvsm/bff/controller/DocController.java:186`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| docType | path | string | True | — |
| Range | header | string | False | — |

Response `200`: `binary` — fields Unknown (schema not resolved from code)

Response `206`: None (no body)

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `416`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/docs/view/{docType}/**

Handler: `DocController.viewDocument` (`bff-service/src/main/java/com/tvsm/bff/controller/DocController.java:156`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| docType | path | string | True | — |

Response `200`: `binary` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/enquiry/bulk-upload/{bulkUploadId}/error

Handler: `EnquiryBFFController.getBulkUploadErrors` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:224`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bulkUploadId | path | uuid | True | — |

Response `200`: `APIResponse<EnquiryBulkUploadErrorDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)


### GET /cps/api/v1/enquiry/get-enquiry

Handler: `EnquiryBFFController.getEnquiry` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:75`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| enquiryId | query | string | True | — |

Response `200`: `APIResponse<EnquiryDetailsResponse>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/enquiry/getEnquiryMaster

Handler: `EnquiryBFFController.getEnquiryMasterData` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:117`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<EnquiryMasterData>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/enquiry/vehicles

Handler: `EnquiryBFFController.getAllVehicles` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:86`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `APIResponse<VehicleDto[]>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/enquiry/vehicles/{model}/variants

Handler: `EnquiryBFFController.getVehicleVariants` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:99`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| model | path | string | True | — |

Response `200`: `APIResponse<VehicleVariantDto[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/grn/details/{grnId}

Handler: `GrnBFFController.getGrnDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:48`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| grnId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/inventory/accumulated-stock/{productCatalogId}

Handler: `InventoryBFFController.getAccumulatedStock` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:92`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productCatalogId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/inventory/bin/get

Handler: `InventoryBFFController.getBins` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:294`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| isDefault | query | boolean | False | — |
| rackId | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/inventory/get/{productCatalogId}

Handler: `InventoryBFFController.getInventoryBySku` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:45`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productCatalogId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/inventory/location/get

Handler: `InventoryBFFController.getLocations` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:225`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| isDefault | query | boolean | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/inventory/rack/get

Handler: `InventoryBFFController.getRacks` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:255`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| isDefault | query | boolean | False | — |
| locationId | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/invoice/delivery-view/{invoiceId}

Handler: `InvoiceBFFController.getInvoiceDeliveryView` (`bff-service/src/main/java/com/tvsm/bff/controller/InvoiceBFFController.java:54`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| invoiceId | path | uuid | True | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/jobcards/bulk-upload/{bulkUploadId}/error

Handler: `JobcardBFFController.getJobCardBulkUploadErrors` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:407`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bulkUploadId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/jobcards/master

Handler: `JobcardBFFController.getJobCardMasterData` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:270`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/jobcards/{jobcardId}

Handler: `JobcardBFFController.jobCardsDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:253`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| jobcardId | path | string | True | — |
| isServiceHistory | query | boolean | False | — |

Response `200`: `APIResponse<JCDetailsWithMappingsBFFResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/location/address/autocomplete

Handler: `LocationMasterController.getAddressAutocomplete` (`bff-service/src/main/java/com/tvsm/bff/controller/LocationMasterController.java:35`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| input | query | string | True | — |

Response `200`: `APIResponse<map<string,object>[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/location/address/details

Handler: `LocationMasterController.getAddressDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/LocationMasterController.java:61`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| placeId | query | string | True | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/order

Handler: `OrderBFFController.getOrders` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:63`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| status | query | string | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |
| sortBy | query | string | False | — |
| sortDir | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/order/active-cart

Handler: `OrderBFFController.getActiveCart` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:293`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderCategory | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/order/cancellation-reasons

Handler: `OrderBFFController.getCancellationReasons` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:138`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/order/get

Handler: `OrderBFFController.getOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:151`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | query | string | True | — |
| requiredOrderLine | query | boolean | False | — |
| requireOrderHistory | query | boolean | False | — |
| requireDeliveryView | query | boolean | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/order/get-booking-list

Handler: `OrderBFFController.getPartsDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:372`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/order/get-branch

Handler: `OrderBFFController.getAllBranches` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:221`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | query | string | True | — |
| dealerCode | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/order/get-draft

Handler: `OrderBFFController.getAllDraftOrders` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:185`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderCategory | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/order/orderedPartDetails

Handler: `OrderBFFController.getOrderedPartsDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:358`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partId | query | string | True | — |
| orderId | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/order/part/get/{partId}

Handler: `OrderBFFController.getPartsDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:345`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /cps/api/v1/order/status-counts

Handler: `OrderBFFController.getOrderStatusCounts` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:459`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productType | query | string | True | — |
| dealerId | query | string | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/permissions/user

Handler: `PermissionBFFController.getUserPermissions` (`bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java:54`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `UserPermissionsResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/UserPermissionsResponseDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| permissions | PermissionDTO[] | False | — |

Response `401`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/permissions/user-info

Handler: `PermissionBFFController.getUserDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java:96`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `UserDetailInfoResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/UserDetailInfoResponseDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| sub | string | False | — |
| firstName | string | False | — |
| lastName | string | False | — |
| userId | string | False | — |
| dealerId | string | False | — |
| userType | string | False | — |
| country | string | False | — |
| uid | string | False | — |
| employeeId | string | False | — |
| primaryPhoneNumber | string | False | — |
| dealerName | string | False | — |
| email | string | False | — |
| profilePicture | string | False | — |
| timezone | string | False | — |
| currencyCode | string | False | — |
| locale | string | False | — |
| tenantId | string | False | — |
| permissions | PermissionDTO[] | False | — |
| roles | string[] | False | — |
| reservation | ReservationConfigDTO | False | — |

Response `401`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/permissions/user-role/list

Handler: `PermissionBFFController.getAllUserRoles` (`bff-service/src/main/java/com/tvsm/bff/controller/PermissionBFFController.java:76`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Response `200`: `Role` — fields Unknown (schema not resolved from code)

Response `401`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/training/get/{trainingId}

Handler: `TrainingBFFController.getTraining` (`bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:67`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| trainingId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/user/list-all

Handler: `UmsBffController.getUserList` (`bff-service/src/main/java/com/tvsm/bff/controller/UmsBffController.java:39`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| roleNames | query | string[] | True | — |
| groupName | query | string | False | — |
| appId | query | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/vehicle/global/get-by-vin/{vin}

Handler: `InventoryBFFController.getVehicleByVin` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:107`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| vin | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/workflow/instance/{workflowId}

Handler: `WorkflowBFFController.getWorkflowInstance` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:98`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| workflowId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/workflow/instance/{workflowId}/status

Handler: `WorkflowBFFController.getWorkflowStatus` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:113`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| workflowId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /cps/api/v1/workflow/items

Handler: `WorkflowBFFController.getWorkflowItems` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:70`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| actorType | query | string | True | — |
| actorId | query | string | True | — |
| allFlows | query | boolean | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /cps/api/v1/workflow/template/{entityOperationType}

Handler: `WorkflowBFFController.getActiveTemplate` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:160`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| entityOperationType | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /system/api/v1/vehicle/global/get-by-vin/{vin}

Handler: `InternalServiceBFFController.getVehicleByVin` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:119`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| vin | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /system/api/v1/vehicle/global/get/{vehicleId}

Handler: `InternalServiceBFFController.getByVehicleId` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:135`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| vehicleId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /system/user/{tenantId}/{dealerId}/by-id/{userId}

Handler: `InternalServiceBFFController.getUmsUserById` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:395`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | path | string | True | — |
| dealerId | path | string | True | — |
| userId | path | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /system/user/{tenantId}/{dealerId}/{role}/list-all

Handler: `InternalServiceBFFController.getUmsAuthUserList` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:288`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | path | string | True | — |
| dealerId | path | string | True | — |
| role | path | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /system/user/{tenantId}/{dealerId}/{role}/list-all-employees

Handler: `InternalServiceBFFController.getUmsEmployeeList` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:318`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | path | string | True | — |
| dealerId | path | string | True | — |
| role | path | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### PATCH /api/v1/tenant-config/{tenantId}/handler

Handler: `TenantConfigController.patchTenantHandler` (`bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java:79`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| tenantId | path | string | True | — |

Request body: `TenantHandlerPatchRequest` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/TenantHandlerPatchRequest.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| currencyCode | string | False | — |
| configuration | map<string,object> | False | valid |

Response `200`: `APIResponse<TenantConfigResponse>` — fields Unknown (schema not resolved from code)


### POST /api/v1/tenant-config/create

Handler: `TenantConfigController.createTenantConfigs` (`bff-service/src/main/java/com/tvsm/bff/controller/TenantConfigController.java:46`)  
Callers: Unknown  
Auth: Unknown

Request body: `TenantConfigRequest[]` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<TenantConfigResponse[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/reports/download

Handler: `ReportsBFFController.downloadReport` (`bff-service/src/main/java/com/tvsm/bff/controller/ReportsBFFController.java:73`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `ReportRequest` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/reports/ReportRequest.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerId | string | False | — |
| reportType | string | False | — |
| startDate | string | False | — |
| endDate | string | False | — |
| page | integer | False | — |
| size | integer | False | — |
| tenant | string | False | — |
| locale | string | False | — |
| timeZone | string | False | — |

Response `200`: `StreamingResponseBody` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/admin/search

Handler: `AnnouncementBFFController.searchAnnouncements` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:141`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/create

Handler: `AnnouncementBFFController.createAnnouncement` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:42`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/delete/{announcementId}

Handler: `AnnouncementBFFController.deleteAnnouncement` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:90`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/read

Handler: `AnnouncementBFFController.markRead` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:156`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `201`: None (no body)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/update

Handler: `AnnouncementBFFController.updateAnnouncement` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:73`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/user/search

Handler: `AnnouncementBFFController.getAnnouncementsForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:58`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/{announcementId}/media/add/{docType}

Handler: `AnnouncementBFFController.addMedia` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:173`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | string | True | — |
| file | form | binary | True | — |
| mediaType | form | string | True | — |
| docType | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `201`: None (no body)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/announcement/{announcementId}/media/delete/{mediaId}

Handler: `AnnouncementBFFController.deleteMedia` (`bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:207`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| announcementId | path | string | True | — |
| mediaId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/appointments/analytics/stats/process

Handler: `AppointmentAnalyticsBFFController.processAppointmentStats` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentAnalyticsBFFController.java:34`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AnalyticsRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AnalyticsRequestDTO.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| jobCardIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| dealerId | string | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/appointments/bulk-upload

Handler: `AppointmentBFFController.bulkUploadAppointments` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:299`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | query | binary | True | — |
| Authorization | header | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/appointments/bulk-upload/history

Handler: `AppointmentBFFController.getBulkUploadAppointmentsHistory` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:333`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/appointments/count

Handler: `AppointmentBFFController.getAppointmentCount` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:372`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/appointments/create

Handler: `AppointmentBFFController.createAppointment` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:93`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/appointments/dashboard

Handler: `AppointmentBFFController.getAppointmentDashboard` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:247`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/appointments/download

Handler: `AppointmentBFFController.downloadAppointments` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:270`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |
| timeZone | query | string | True | — |
| channelPartnerId | query | string | False | — |

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/appointments/list

Handler: `AppointmentBFFController.getAppointmentsList` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:66`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/appointments/update

Handler: `AppointmentBFFController.updateAppointment` (`bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:132`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/billing/create

Handler: `BillingBFFController.createInvoice` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:56`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `BillingBFFCreateRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/BillingBFFCreateRequestDto.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| entityId | uuid | False | — |
| entityType | string | False | — |
| invoiceType | string | False | — |
| currencyCode | string | False | — |
| invoiceId | string | False | — |
| invoiceLevelDiscountAmount | number | False | — |
| invoiceLevelDiscountContext | string | False | — |
| invoiceLevelDiscountType | string | False | — |
| bookingId | string | False | — |
| dealerSalesExecutiveId | string | False | — |
| paymentTerms | string | False | — |
| totalLineitemlevelDiscountAmount | number | False | — |
| invoicelevelDiscountPercentage | number | False | — |
| totalInvoiceTaxAmount | number | False | — |
| totalInvoiceAmount | number | False | — |
| additionalNotes | map<string,object> | False | — |
| lineItems | LineItemsDto | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/billing/discard

Handler: `BillingBFFController.discardInvoice` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:179`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/billing/invoices/search

Handler: `BillingBFFController.searchBillingInvoices` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:194`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/billing/post-invoice

Handler: `BillingBFFController.postInvoice` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:216`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `PostInvoiceRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/PostInvoiceRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| invoiceId | string | False | — |
| invoiceNumber | string | False | — |
| invoiceType | string | False | — |
| payment | PaymentDetail | False | — |

Response `200`: `APIResponse<PostInvoiceResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/billing/report/invoice-list

Handler: `BillingReportController.getAggregatedInvoiceReport` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingReportController.java:30`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| page | query | integer | True | — |
| size | query | integer | True | — |

Request body: `ReportRequest` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/reports/ReportRequest.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerId | string | False | — |
| reportType | string | False | — |
| startDate | string | False | — |
| endDate | string | False | — |
| page | integer | False | — |
| size | integer | False | — |
| tenant | string | False | — |
| locale | string | False | — |
| timeZone | string | False | — |

Response `200`: `APIResponse<PaginatedResponse<object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/billing/update

Handler: `BillingBFFController.updateInvoice` (`bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:79`)  
Callers: Unknown  
Auth: Unknown

Request body: `BillingBFFCreateRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/BillingBFFCreateRequestDto.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| entityId | uuid | False | — |
| entityType | string | False | — |
| invoiceType | string | False | — |
| currencyCode | string | False | — |
| invoiceId | string | False | — |
| invoiceLevelDiscountAmount | number | False | — |
| invoiceLevelDiscountContext | string | False | — |
| invoiceLevelDiscountType | string | False | — |
| bookingId | string | False | — |
| dealerSalesExecutiveId | string | False | — |
| paymentTerms | string | False | — |
| totalLineitemlevelDiscountAmount | number | False | — |
| invoicelevelDiscountPercentage | number | False | — |
| totalInvoiceTaxAmount | number | False | — |
| totalInvoiceAmount | number | False | — |
| additionalNotes | map<string,object> | False | — |
| lineItems | LineItemsDto | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/booking/cancel

Handler: `BookingBFFController.cancelBooking` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:99`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `BookingCancellationRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingCancellationRequestDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| uuid | string | False | — |
| isATPConfigured | boolean | False | — |
| checkSum | string | False | — |
| version | integer | False | — |
| cancellationSource | string | False | — |
| cancellationReason | string | False | — |
| cancellationSubReason | string | False | — |
| cancellationFee | number | False | — |
| cancellationFeeRemarks | string | False | — |
| refundAmount | number | False | — |
| customerRemarks | string | False | — |
| CRMId | integer | False | — |
| dateOfCancellation | string | False | — |
| refundDetails | map<string,object> | False | — |
| vehicleId | integer | False | — |
| productIds | integer[] | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/booking/create

Handler: `BookingBFFController.createBooking` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:31`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `BookingBFFRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingBFFRequestDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| booking | Booking | False | — |

Response `200`: `APIResponse<BookingResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/booking/search

Handler: `BookingBFFController.search` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:42`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `BookingSearchRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingSearchRequestDto.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| retrievalType | string | False | — |
| pageNumber | integer | False | — |
| pageSize | integer | False | — |
| bookingRetrieval | BookingRetrievalRequest | False | — |

Response `200`: `APIResponse<BookingSearchResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/booking/stats

Handler: `BookingBFFController.bookingDashboard` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:123`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `BookingSearchRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingSearchRequestDto.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| retrievalType | string | False | — |
| pageNumber | integer | False | — |
| pageSize | integer | False | — |
| bookingRetrieval | BookingRetrievalRequest | False | — |

Response `200`: `APIResponse<BookingStatusCountDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/booking/update

Handler: `BookingBFFController.updateBooking` (`bff-service/src/main/java/com/tvsm/bff/controller/BookingBFFController.java:56`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `BookingUpdateDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingUpdateDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| bookingUuid | string | False | — |
| checksum | string | False | — |
| version | integer | False | — |
| customerId | string | False | — |
| addressId | string | False | — |
| bookingSource | string | False | — |
| dse | string | False | — |
| location | BookingLocationDto | False | — |
| vehicle | Vehicle | False | — |
| expectedDeliveryDate | string | False | — |
| payment | Payment | False | — |
| products | ProductItem[] | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/calendar/get

Handler: `CalendarBFFController.getCalendar` (`bff-service/src/main/java/com/tvsm/bff/controller/CalendarBFFController.java:31`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `EnquiryFilter` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryFilter.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| mobileNumber | string | False | — |
| customerName | string | False | — |
| isActive | boolean | False | — |
| dealerId | string | False | — |
| dealerIds | string[] | False | — |
| sourceCategory | integer[] | False | — |
| enquiryType | string[] | False | — |
| source | string[] | False | — |
| startTime | string | False | — |
| endTime | string | False | — |
| dseId | string | False | — |
| dseIds | string[] | False | — |
| leadCategory | string | False | — |
| emailId | string | False | — |
| testRideStatus | string | False | — |
| sortBy | string | False | — |
| followUpStatus | string | False | — |
| status | string | False | — |
| modelId | string | False | — |
| partId | string | False | — |
| leadId | string | False | — |
| nextFollowUpStartDate | string | False | — |
| nextFollowUpEndDate | string | False | — |
| testRideScheduledStartDate | string | False | — |
| testRideScheduledEndDate | string | False | — |
| page | integer | False | — |
| size | integer | False | — |
| calendarType | enum[TESTRIDE,FOLLOWUP] | False | — |

Response `200`: `APIResponse<CalendarResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/cart/bulk-upload

Handler: `CartBFFController.bulkUploadCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:173`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | form | binary | True | — |
| orderCategoryType | form | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/cart/create

Handler: `CartBFFController.createCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:45`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/cart/create-active-cart

Handler: `CartBFFController.setActiveCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:144`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| cartId | query | string | True | — |
| categoryType | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/cart/delete/{cartId}

Handler: `CartBFFController.deleteCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:108`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| cartId | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/cart/reorder

Handler: `CartBFFController.reorderCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:221`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/cart/search

Handler: `CartBFFController.searchCarts` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:78`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /cps/api/v1/cart/update

Handler: `CartBFFController.updateCart` (`bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:61`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/catalogs/all

Handler: `CatalogController.getAll` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:225`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `CatalogRequest` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/CatalogRequest.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| currentPage | integer | False | — |
| pageLimit | integer | False | — |
| productType | string | False | — |
| filter | Filter | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/catalogs/product-details

Handler: `CatalogController.getPAMDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:369`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/claims

Handler: `ClaimBFFController.createClaims` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:153`)  
Callers: `tvs-cps-backend`, `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/claims/analytics/stats/process

Handler: `ClaimAnalyticsBFFController.processClaimStats` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimAnalyticsBFFController.java:34`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AnalyticsRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AnalyticsRequestDTO.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| jobCardIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| dealerId | string | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/claims/bulk-upload

Handler: `ClaimBFFController.bulkUploadClaims` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:498`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | query | binary | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/claims/bulk-upload/history

Handler: `ClaimBFFController.bulkUploadClaimsHistory` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:521`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/claims/close

Handler: `ClaimBFFController.closeClaim` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:333`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /cps/api/v1/claims/dashboard

Handler: `ClaimBFFController.getClaimDashboard` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:367`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/claims/download

Handler: `ClaimBFFController.downloadClaims` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:471`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |
| timeZone | query | string | False | — |
| channelPartnerId | query | string | False | — |

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `object` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/claims/list

Handler: `ClaimBFFController.getClaimsList` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:85`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `object` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/collateral/create

Handler: `CollateralBFFController.createCollateral` (`bff-service/src/main/java/com/tvsm/bff/controller/CollateralBFFController.java:38`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/collateral/search

Handler: `CollateralBFFController.getCollaterals` (`bff-service/src/main/java/com/tvsm/bff/controller/CollateralBFFController.java:53`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /cps/api/v1/customer/add-vehicle

Handler: `CustomerBFFController.addVehicleToCustomer` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:235`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/customer/create

Handler: `CustomerBFFController.createCustomer` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:172`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/customer/delete

Handler: `CustomerBFFController.deleteCustomer` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:254`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/customer/inward-vehicle

Handler: `CustomerBFFController.createCustomerWithVehicle` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:191`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `CreateCustomerWithVehicleRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/CreateCustomerWithVehicleRequestDto.java:18`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| vin | string | True | — |
| customer | map<string,object> | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/customer/search

Handler: `CustomerBFFController.searchCustomers` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:51`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/customer/search-vehicle

Handler: `CustomerBFFController.searchCustomersWithDatalake` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:97`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/customer/update

Handler: `CustomerBFFController.updateCustomer` (`bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:210`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/dashboard/create

Handler: `DashboardBFFController.createDashboard` (`bff-service/src/main/java/com/tvsm/bff/controller/DashboardBFFController.java:105`)  
Callers: Unknown  
Auth: Unknown

Request body: `CreateAnalyticsDashboardRequestDTO[]` — fields Unknown (schema not resolved from code)

Response `200`: `DashboardEntryDTO[]` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/docs/delete/{docType}/**

Handler: `DocController.deleteDocument` (`bff-service/src/main/java/com/tvsm/bff/controller/DocController.java:124`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| docType | path | string | True | — |

Response `200`: `APIResponse<any>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/docs/upload

Handler: `DocController.uploadDocument` (`bff-service/src/main/java/com/tvsm/bff/controller/DocController.java:46`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | form | binary | True | — |
| docType | form | string | True | — |
| purpose | form | string | True | — |

Response `200`: `DocumentUploadResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/DocumentUploadResponseDTO.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| url | string | False | — |
| originalFilename | string | False | — |
| size | integer | False | — |
| contentType | string | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/enquiry/bulk-assign

Handler: `EnquiryBFFController.bulkAssignEnquiries` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:243`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `BulkAssignRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/BulkAssignRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| enquiryIds | string[] | True | — |
| dseId | string | True | — |
| dseName | string | True | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/enquiry/bulk-upload

Handler: `EnquiryBFFController.bulkUploadEnquiries` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:150`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | form | binary | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/enquiry/bulk-upload/history

Handler: `EnquiryBFFController.getBulkUploadEnquiriesHistory` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:208`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<PageResponseDTO<EnquiryBulkUploadDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/enquiry/create

Handler: `EnquiryBFFController.createEnquiry` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:40`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `EnquiryBFFRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryBFFRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customerName | string | False | — |
| mobileNumber | string | False | — |
| email | string | False | — |
| interestedBrand | InterestedBrandBFFDto[] | False | — |
| modeOfCommunication | map<string,object> | False | — |
| enquiryClassification | string | False | — |
| additionalNotes | string | False | — |
| additionalDetails | EnquiryAdditionalInfo | False | — |
| assignedTo | string | False | — |
| sourceOfAwareness | string | False | — |
| followUp | EnquiryFollowUpDto | False | — |
| ageGroup | string | False | — |
| gender | string | False | — |
| postalCode | string | False | — |
| addressLine1 | string | False | — |
| addressLine2 | string | False | — |
| peferredPurchaseMode | string | False | — |
| interestedInExchange | string | False | — |
| existingVehicle | ExistingVehicle | False | — |
| preferredLanguage | string | False | — |
| customerInterest | string | False | — |
| hasCustomerVisited | boolean | False | — |
| enquiryTag | EnquiryTag[] | False | — |

Response `200`: `APIResponse<EnquiryBFFResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/enquiry/filter

Handler: `EnquiryBFFController.filterEnquiry` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:50`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `EnquiryFilter` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryFilter.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| mobileNumber | string | False | — |
| customerName | string | False | — |
| isActive | boolean | False | — |
| dealerId | string | False | — |
| dealerIds | string[] | False | — |
| sourceCategory | integer[] | False | — |
| enquiryType | string[] | False | — |
| source | string[] | False | — |
| startTime | string | False | — |
| endTime | string | False | — |
| dseId | string | False | — |
| dseIds | string[] | False | — |
| leadCategory | string | False | — |
| emailId | string | False | — |
| testRideStatus | string | False | — |
| sortBy | string | False | — |
| followUpStatus | string | False | — |
| status | string | False | — |
| modelId | string | False | — |
| partId | string | False | — |
| leadId | string | False | — |
| nextFollowUpStartDate | string | False | — |
| nextFollowUpEndDate | string | False | — |
| testRideScheduledStartDate | string | False | — |
| testRideScheduledEndDate | string | False | — |
| page | integer | False | — |
| size | integer | False | — |
| calendarType | enum[TESTRIDE,FOLLOWUP] | False | — |

Response `200`: `APIResponse<EnquiryFilterResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/enquiry/stats

Handler: `EnquiryBFFController.enquiryStatusCount` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:132`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `EnquiryFilter` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryFilter.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| mobileNumber | string | False | — |
| customerName | string | False | — |
| isActive | boolean | False | — |
| dealerId | string | False | — |
| dealerIds | string[] | False | — |
| sourceCategory | integer[] | False | — |
| enquiryType | string[] | False | — |
| source | string[] | False | — |
| startTime | string | False | — |
| endTime | string | False | — |
| dseId | string | False | — |
| dseIds | string[] | False | — |
| leadCategory | string | False | — |
| emailId | string | False | — |
| testRideStatus | string | False | — |
| sortBy | string | False | — |
| followUpStatus | string | False | — |
| status | string | False | — |
| modelId | string | False | — |
| partId | string | False | — |
| leadId | string | False | — |
| nextFollowUpStartDate | string | False | — |
| nextFollowUpEndDate | string | False | — |
| testRideScheduledStartDate | string | False | — |
| testRideScheduledEndDate | string | False | — |
| page | integer | False | — |
| size | integer | False | — |
| calendarType | enum[TESTRIDE,FOLLOWUP] | False | — |

Response `200`: `APIResponse<EnquiryStatusCountDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/enquiry/update

Handler: `EnquiryBFFController.updateEnquiry` (`bff-service/src/main/java/com/tvsm/bff/controller/EnquiryBFFController.java:65`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `UpdateEnquiryRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/UpdateEnquiryRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| enquiryId | string | False | — |
| enquiryClassification | string | False | — |
| interestedBrand | InterestedBrandBFFDto[] | False | — |
| testRides | EnquiryTestRideDto[] | False | — |
| followUps | FollowUps | False | — |
| status | string | False | — |
| pincode | string | False | — |
| addressLine1 | string | False | — |
| addressLine2 | string | False | — |
| preferredLanguage | string | False | — |
| preferredPurchaseMode | string | False | — |
| interestedInExchange | string | False | — |
| hasCustomerVisited | boolean | False | — |
| customerInterest | string | False | — |
| additionalDetails | EnquiryAdditionalInfo | False | — |
| city | string | False | — |
| existingVehicle | ExistingVehicle | False | — |

Response `200`: `APIResponse<EnquiryBFFResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/grn/complete

Handler: `GrnBFFController.completeGrn` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:96`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/grn/delivery-details/add

Handler: `GrnBFFController.addDeliveryDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:112`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/grn/initiate

Handler: `GrnBFFController.createGrn` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:64`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/grn/search

Handler: `GrnBFFController.searchGrns` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:163`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/grn/update

Handler: `GrnBFFController.updateGrn` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:80`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/grn/update-claim-initiated

Handler: `GrnBFFController.updateClaimInitiated` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:179`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/grn/upload-docs

Handler: `GrnBFFController.uploadGrnDocument` (`bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:128`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| grnId | form | string | True | — |
| file | form | binary | True | — |
| document_type | form | string | True | — |
| description | form | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/allocate

Handler: `InventoryBFFController.allocate` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:333`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `VehicleAllocateRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/VehicleAllocateRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| bookingUuid | string | False | — |
| checkSum | string | False | — |
| version | integer | False | — |
| customerId | string | False | — |
| frameNumber | string | False | — |
| engineNumber | string | False | — |
| vehicleId | string | False | — |
| productCatalogId | string | False | — |
| source | string | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/bin/create

Handler: `InventoryBFFController.createBin` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:279`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/deallocate

Handler: `InventoryBFFController.deallocate` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:348`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `VehicleDeallocationRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/VehicleDeallocationRequestDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| bookingUuid | string | False | — |
| checkSum | string | False | — |
| version | integer | False | — |
| customerId | string | False | — |
| frameNumber | string | False | — |
| engineNumber | string | False | — |
| vehicleId | string | False | — |
| productCatalogId | string | False | — |
| source | string | False | — |
| manufactureYear | string | False | — |
| manufactureMonth | string | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/get-add-by-vin

Handler: `WarrantyBFFController.getAddVin` (`bff-service/src/main/java/com/tvsm/bff/controller/WarrantyBFFController.java:60`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `GetAddVehicleRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/GetAddVehicleRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| vin | string | False | — |
| type | string | False | — |

Response `200`: `APIResponse<VehicleResponseDto>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/issue

Handler: `InventoryBFFController.issueInventory` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:61`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/list

Handler: `InventoryBFFController.listInventory` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:318`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/location/create

Handler: `InventoryBFFController.createLocation` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:210`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/rack/create

Handler: `InventoryBFFController.createRack` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:240`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/inventory/receive

Handler: `InventoryBFFController.receiveInventory` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:77`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>[]` — fields Unknown (schema not resolved from code)

Response `200`: `string` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/invoice/search

Handler: `InvoiceBFFController.searchInvoices` (`bff-service/src/main/java/com/tvsm/bff/controller/InvoiceBFFController.java:38`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/jobcards/bulk-upload

Handler: `JobcardBFFController.saveJobCardBulkUploads` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:344`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | query | binary | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/bulk-upload/history

Handler: `JobcardBFFController.getJobCardBulkUploads` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:332`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/create

Handler: `JobcardBFFController.createJobCards` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:105`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/dashboard

Handler: `JobcardBFFController.getJobcardDashboard` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:310`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/download

Handler: `JobcardBFFController.downloadJobcards` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:365`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |
| timeZone | query | string | True | — |
| channelPartnerId | query | string | False | — |

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `object` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/invoice/generate

Handler: `JobcardBFFController.createInvoice` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:390`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `JobcardCreateInvoiceDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/JobcardCreateInvoiceDTO.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| jobCardId | string | False | — |
| vin | string | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/list

Handler: `JobcardBFFController.getJobCards` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:76`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| isServiceHistory | query | boolean | False | — |

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/jobcards/warranty-check

Handler: `JobcardBFFController.vehicleAndPartWarrantyCheck` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:296`)  
Callers: Unknown  
Auth: Unknown

Request body: `WarrantyCheckRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/WarrantyCheckRequestDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| vehicleSaleDateStr | string | True | — |
| vehicleWarrantyPeriod | integer | False | — |
| vehicleWarrantyEndDate | string | False | — |
| partWarrantyPeriod | integer | False | — |
| warrantyUnit | string | True | — |
| customerVehicleId | string | True | — |
| partCatalogSkuId | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/lead-allocation/assign

Handler: `LeadAllocationBFFController.assignDefaultUsers` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadAllocationBFFController.java:80`)  
Callers: Unknown  
Auth: Unknown

Request body: `AssignDefaultUsersRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/AssignDefaultUsersRequestDTO.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | DataPayload | True | valid |

Response `200`: `APIResponse<AssignDefaultUsersResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/lead-allocation/list

Handler: `LeadAllocationBFFController.getLeadAllocationList` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadAllocationBFFController.java:36`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `LeadAllocationListRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/LeadAllocationListRequestDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| type | string | False | pattern=SERVICE\|SALES |

Response `200`: `APIResponse<LeadAllocationDataDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/lead-allocation/update

Handler: `LeadAllocationBFFController.updateAllocation` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadAllocationBFFController.java:58`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `UpdateAllocationRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/UpdateAllocationRequestDTO.java:22`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | ContentItemDTO[] | True | valid |

Response `200`: `APIResponse<UpdateAllocationResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/lead/dashboard

Handler: `LeadServiceBFFController.getLeadServiceDashboard` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadServiceBFFController.java:36`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<LeadServiceDashboardResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/lead/details

Handler: `LeadServiceBFFController.getLeadDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadServiceBFFController.java:109`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `LeadDetailsRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/LeadDetailsRequestDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| leadId | string | True | — |

Response `200`: `APIResponse<ServiceReminderDetailResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /cps/api/v1/lead/filter

Handler: `LeadServiceBFFController.getAllLeads` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadServiceBFFController.java:57`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| page | query | integer | False | — |
| size | query | integer | False | — |

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<LeadServiceListResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/lead/update

Handler: `LeadServiceBFFController.createFollowUp` (`bff-service/src/main/java/com/tvsm/bff/controller/LeadServiceBFFController.java:84`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/notification-category/all

Handler: `NotificationCategoryBFFController.getAllCategoriesUnfiltered` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:73`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `NotificationCategoryRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationCategoryRequestDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationCategoryResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-category/cache/refresh

Handler: `NotificationCategoryBFFController.refreshCategoriesCache` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:88`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `NotificationCategoryResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-category/list

Handler: `NotificationCategoryBFFController.getAllCategories` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:43`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationCategoryRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationCategoryRequestDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationCategoryResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-category/role-mapping/reload

Handler: `NotificationCategoryBFFController.reloadCategoryRoleMapping` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:100`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `string` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-device/deregister

Handler: `NotificationDeviceBFFController.deregisterDeviceForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationDeviceBFFController.java:57`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `NotificationDeviceDeregisterRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationDeviceDeregisterRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| deviceToken | string | True | maxLength=2000 |
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationDeviceResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationDeviceResponseDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationDeviceId | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| currentUserId | string | False | — |
| deviceToken | string | False | — |
| platform | string | False | — |
| isActive | boolean | False | — |
| lastActiveAt | datetime | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### POST /cps/api/v1/notification-device/register

Handler: `NotificationDeviceBFFController.registerDeviceForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationDeviceBFFController.java:42`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `NotificationDeviceRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationDeviceRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| deviceToken | string | True | maxLength=2000 |
| platform | string | False | maxLength=50 |
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationDeviceResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationDeviceResponseDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationDeviceId | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| currentUserId | string | False | — |
| deviceToken | string | False | — |
| platform | string | False | — |
| isActive | boolean | False | — |
| lastActiveAt | datetime | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### POST /cps/api/v1/notification-events/publish

Handler: `NotificationEventBFFController.publishAsync` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationEventBFFController.java:65`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationEventRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationEventRequestDto.java:33`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| eventId | string | True | — |
| tenantId | string | True | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| recipients | NotificationRecipientDto[] | False | — |
| categoryCode | string | True | — |
| subCategoryCode | string | True | — |
| referenceId | string | False | — |
| payload | object | False | — |
| params | map<string,object> | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `202`: `object` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-events/publish/sync

Handler: `NotificationEventBFFController.publishSync` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationEventBFFController.java:117`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationEventRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationEventRequestDto.java:33`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| eventId | string | True | — |
| tenantId | string | True | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| recipients | NotificationRecipientDto[] | False | — |
| categoryCode | string | True | — |
| subCategoryCode | string | True | — |
| referenceId | string | False | — |
| payload | object | False | — |
| params | map<string,object> | False | — |

Response `200`: `object` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-events/trigger

Handler: `NotificationEventTriggerController.triggerEvent` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationEventTriggerController.java:39`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationTriggerRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationTriggerRequestDto.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| eventType | string | True | — |
| referenceId | string | True | — |
| payload | map<string,object> | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-message/read/all

Handler: `NotificationMessageBFFController.markAllAsReadForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:97`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `NotificationMessageReadResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageId | string | False | — |
| markedRead | boolean | False | — |
| updatedCount | integer | False | — |


### POST /cps/api/v1/notification-message/read/bulk

Handler: `NotificationMessageBFFController.bulkMarkAsReadForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:82`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationMessageBulkReadRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationMessageBulkReadRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageIds | string[] | True | — |

Response `200`: `NotificationMessageReadResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageId | string | False | — |
| markedRead | boolean | False | — |
| updatedCount | integer | False | — |


### POST /cps/api/v1/notification-message/read/{messageId}

Handler: `NotificationMessageBFFController.markAsReadForUser` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:68`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| messageId | path | string | True | — |

Response `200`: `NotificationMessageReadResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageId | string | False | — |
| markedRead | boolean | False | — |
| updatedCount | integer | False | — |


### POST /cps/api/v1/notification-message/search

Handler: `NotificationMessageBFFController.searchMessagesByUserId` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:52`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `NotificationMessageSearchRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationMessageSearchRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| currentUserId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationMessageResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-preference/list

Handler: `NotificationPreferenceBFFController.getPreferencesByUser` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationPreferenceBFFController.java:45`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `NotificationPreferenceRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationPreferenceRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| tenantId | string | False | — |
| dealerId | string | False | — |

Response `200`: `NotificationCategoryPreferenceResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/notification-preference/update

Handler: `NotificationPreferenceBFFController.updatePreferencesByUserId` (`bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationPreferenceBFFController.java:63`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `NotificationPreferenceUpdateRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationPreferenceUpdateRequestDto.java:15`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| preferences | PreferenceItemDto[] | True | valid |

Response `200`: `NotificationPreferenceUpdateResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationPreferenceUpdateResponseDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| updatedCount | integer | False | — |
| updated | boolean | False | — |


### POST /cps/api/v1/npqr/create

Handler: `NpqrBFFController.createQualityReport` (`bff-service/src/main/java/com/tvsm/bff/controller/NpqrBFFController.java:37`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/npqr/list

Handler: `NpqrBFFController.getQualityReportList` (`bff-service/src/main/java/com/tvsm/bff/controller/NpqrBFFController.java:59`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/bulk-upload

Handler: `OrderBFFController.bulkUploadOrders` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:484`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | form | binary | True | — |
| orderCategoryType | form | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/cancel

Handler: `OrderBFFController.cancelOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:107`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/create

Handler: `OrderBFFController.createOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:47`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/create-active-cart

Handler: `OrderBFFController.createActiveCart` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:409`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderId | query | string | True | — |
| categoryType | query | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/order/delete-order/{id}

Handler: `OrderBFFController.deleteOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:428`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/order/draft/update

Handler: `OrderBFFController.handleOrderAction` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:205`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/get-all-order

Handler: `OrderBFFController.getAllOrders` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:443`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/order/get-all-parts

Handler: `OrderBFFController.getAllParts` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:277`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/get-placed-order

Handler: `OrderBFFController.getPlacedOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:261`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/place-order

Handler: `OrderBFFController.placeOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:243`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/reorder

Handler: `OrderBFFController.reorder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:329`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/sale-order-no/list

Handler: `OrderBFFController.retrieveERPSaleNumber` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:395`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/order/search

Handler: `OrderBFFController.searchOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:536`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/search/{partNumber}

Handler: `OrderBFFController.searchByPartNumber` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:383`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partNumber | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/order/update-allocation

Handler: `OrderBFFController.updateOrderLineAllocation` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:122`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/order/workflow/update

Handler: `OrderBFFController.workflowUpdate` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:313`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/otp/generate

Handler: `NotificationBFFController.generateOtp` (`bff-service/src/main/java/com/tvsm/bff/controller/NotificationBFFController.java:41`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `ChannelsDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/OtpRequestDTO.java:20`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channel | string | False | — |
| entity | string | False | — |

Response `200`: `object` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/otp/notify

Handler: `NotificationBFFController.notifyOtp` (`bff-service/src/main/java/com/tvsm/bff/controller/NotificationBFFController.java:61`)  
Callers: Unknown  
Auth: Unknown

Request body: `OtpRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/OtpRequestDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channels | ChannelsDTO[] | False | — |

Response `200`: `object` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/otp/verify

Handler: `NotificationBFFController.validateOtp` (`bff-service/src/main/java/com/tvsm/bff/controller/NotificationBFFController.java:75`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `ValidateOtpRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/ValidateOtpRequestDTO.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channel | string | False | pattern=EMAIL\|MOBILE |
| entity | string | False | — |
| otp | string | False | — |

Response `200`: `object` — fields Unknown (schema not resolved from code)


### POST /cps/api/v1/smart-search/additional-details

Handler: `SmartSearchBFFController.smartSearchAdditionalDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/SmartSearchBFFController.java:168`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `SmartSearchAdditionalDetailsRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchAdditionalDetailsRequestDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customerId | string | False | — |
| vehicleId | string | False | — |
| mobileNumber | string | False | — |
| retrieve | string | False | — |

Response `200`: `SmartSearchAdditionalDetailsResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchAdditionalDetailsResponseDTO.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| preSales | EventsDTO[] | False | — |
| ownershipBilling | object[] | False | — |
| afterSales | AdditionalDetailItemDTO[] | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/smart-search/details

Handler: `SmartSearchBFFController.smartSearchDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/SmartSearchBFFController.java:106`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `SmartSearchDetailsRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchDetailsRequestDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customerId | string | False | — |
| vehicleId | string | False | — |
| vin | string | False | — |
| mobileNumber | string | False | — |

Response `200`: `SmartSearchDetailsResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchDetailsResponseDTO.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customerLinked | boolean | False | — |
| profile | CustomerProfileDTO | False | — |
| vehicles | SmartSearchVehicleDTO[] | False | — |
| activeEvents | EventsDTO[] | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/smart-search/search

Handler: `SmartSearchBFFController.smartSearch` (`bff-service/src/main/java/com/tvsm/bff/controller/SmartSearchBFFController.java:41`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `SmartSearchRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchRequestDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| searchType | string | False | — |
| searchValue | string | False | — |
| page | integer | False | — |
| size | integer | False | — |

Response `200`: `SmartSearchResponseDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchResponseDTO.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| searchType | string | False | — |
| searchValue | string | False | — |
| totalCount | integer | False | — |
| results | T[] | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `403`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/training/create

Handler: `TrainingBFFController.createTraining` (`bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:36`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/training/read

Handler: `TrainingBFFController.recordTrainingRead` (`bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:83`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `201`: None (no body)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/training/search

Handler: `TrainingBFFController.getTrainings` (`bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:52`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /cps/api/v1/vehicle/delivery

Handler: `InventoryBFFController.markVehicleDelivery` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:149`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `VehicleDeliveryRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/VehicleDeliveryRequestDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| vin | string | False | — |
| deliveryDate | string | False | — |
| additionalDocuments | map<string,object> | False | — |
| registrationNumber | string | False | — |
| bookingId | string | False | — |
| bookingChecksum | string | False | — |
| bookingVersion | integer | False | — |
| customerId | string | False | — |

Response `200`: `APIResponse<VehicleDeliveryResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/vehicle/delivery-date/add

Handler: `InventoryBFFController.addVehicleDeliveryDate` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:133`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/vehicle/inventory/lookup

Handler: `InventoryBFFController.vehicleInventoryLookup` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:179`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/vehicle/pdi

Handler: `InventoryBFFController.updatePDiDone` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:363`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/vehicle/submit-inspection

Handler: `VehicleBFFController.submitInspection` (`bff-service/src/main/java/com/tvsm/bff/controller/VehicleBFFController.java:98`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `InspectionSubmitRequest` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/inspection/InspectionSubmitRequest.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| submissionId | string | True | — |
| type | string | True | — |
| vin | string | True | — |
| formId | string | True | — |
| technicianName | string | True | — |
| customerName | string | False | — |
| inspectionDate | string | True | — |
| mileage | integer | False | — |
| keyNumber | string | False | — |
| status | string | True | — |
| submissionDate | string | True | — |
| score | integer | False | positiveOrZero |

Response `200`: `APIResponse<InspectionDetailResponse>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /cps/api/v1/vehicle/update/stock-type

Handler: `InventoryBFFController.updateStockType` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:163`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/vehiclesearch

Handler: `VehicleBFFController.searchCustomersByVehicle` (`bff-service/src/main/java/com/tvsm/bff/controller/VehicleBFFController.java:49`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/warranty-registration/create

Handler: `WarrantyBFFController.createWarranty` (`bff-service/src/main/java/com/tvsm/bff/controller/WarrantyBFFController.java:34`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `WarrantyCreateRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/WarrantyCreateRequestDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customerName | string | False | — |
| mobileNumber | string | False | — |
| alternateMobileNumber | string | False | — |
| email | string | False | — |
| gender | string | False | — |
| postalCode | string | False | — |
| city | string | False | — |
| state | string | False | — |
| address | string | False | — |
| area | string | False | — |
| region | string | False | — |
| countryCode | string | False | — |
| vin | string | False | — |
| registrationNumber | string | False | — |
| engineNumber | string | False | — |
| keyNumber | string | False | — |
| bookingId | string | False | — |
| model | string | False | — |
| vehicleId | string | False | — |
| vehicleReceiveDate | string | False | — |
| saleDate | string | False | — |
| vehicleDeliveryDate | string | False | — |
| salesExecutiveAssigned | string | False | — |
| saleInvoiceNumber | string | False | — |
| customerId | string | False | — |
| customerVerificationStatus | integer | False | — |
| additionalDocuments | AdditionalDocumentDto | False | — |
| includeAdditionalDocument | boolean | False | — |

Response `200`: `APIResponse<WarrantyCreateResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/warranty-registration/search

Handler: `WarrantyBFFController.listWarranties` (`bff-service/src/main/java/com/tvsm/bff/controller/WarrantyBFFController.java:46`)  
Callers: Unknown  
Auth: Unknown

Request body: `WarrantySearchRequestDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/WarrantySearchRequestDto.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| retrievalType | string | False | — |
| pageNumber | integer | False | — |
| pageSize | integer | False | — |
| phone | string | False | — |

Response `200`: `APIResponse<WarrantyListResponse[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /cps/api/v1/workflow/action

Handler: `WorkflowBFFController.performWorkflowAction` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:54`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/workflow/init

Handler: `WorkflowBFFController.initializeWorkflow` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:39`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/workflow/template/create

Handler: `WorkflowBFFController.createTemplate` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:129`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /cps/api/v1/workflow/template/process-activations

Handler: `WorkflowBFFController.processTemplateActivations` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:190`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /cps/api/v1/workflow/template/update

Handler: `WorkflowBFFController.updateTemplate` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:144`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/analytic/booking/stats

Handler: `AnalyticsController.retrieveBooking` (`bff-service/src/main/java/com/tvsm/bff/controller/AnalyticsController.java:31`)  
Callers: `tvs-cps-jobs`  
Auth: Unknown

Request body: `AnalyticsDto` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/AnalyticsDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerId | string | False | — |
| indicatorKey | string | False | — |
| tenantId | string | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/analytics-dashboard/indicators/calculate

Handler: `InternalServiceBFFController.calculateDashboardIndicators` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:258`)  
Callers: `tvs-cps-jobs`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/appointments/auto-close

Handler: `InternalServiceBFFController.autoCloseAppointments` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:162`)  
Callers: `tvs-cps-jobs`  
Auth: Unknown

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/claims/sap-sync

Handler: `InternalServiceBFFController.claimSAPSync` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:189`)  
Callers: `tvs-cps-jobs`  
Auth: Unknown

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/invoice/insert

Handler: `InternalServiceBFFController.insertInvoice` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:104`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/order/sale-order-no/list

Handler: `InternalServiceBFFController.retrieveERPDetails` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:73`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/order/sync-erp-status

Handler: `InternalServiceBFFController.syncErpOrderStatus` (`bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:89`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/system/api/v1/inventory/analytics/list

Handler: `InventoryAnalyticsBFFController.productCatalogCount` (`bff-service/src/main/java/com/tvsm/bff/controller/InventoryAnalyticsBFFController.java:39`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### PUT /cps/api/v1/claims/update

Handler: `ClaimBFFController.updateClaim` (`bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:226`)  
Callers: `tvs-cps-portal`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### PUT /cps/api/v1/jobcards/update

Handler: `JobcardBFFController.updateJobCards` (`bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:172`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### PUT /cps/api/v1/order/update

Handler: `OrderBFFController.updateOrder` (`bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:91`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### PUT /cps/api/v1/workflow/template/{id}/decommission

Handler: `WorkflowBFFController.decommissionTemplate` (`bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:175`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /api/v1/claims/bulk-upload/{bulkUploadId}/error

Handler: `ClaimController.getBulkUploadErrors` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:223`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| bulkUploadId | path | uuid | True | — |

Response `200`: `APIResponse<BulkUploadErrorDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `403`: None (no body)

Response `404`: None (no body)


### GET /api/v1/claims/master

Handler: `ClaimController.getClaimMasterData` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:158`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |

Response `200`: `APIResponse<ClaimMasterDataResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/claims/timeline/{claimCatalogMappingId}

Handler: `ClaimController.getCatalogTimeline` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:130`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| claimCatalogMappingId | path | string | True | — |

Response `200`: `APIResponse<CatalogTimelineResponseDTO>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### GET /api/v1/claims/{claimId}

Handler: `ClaimController.getClaimDetails` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:75`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| claimId | path | string | True | — |

Response `200`: `APIResponse<ClaimResponseDTO>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### POST /api/v1/claims

Handler: `ClaimController.createClaims` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:89`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `ClaimCreateRequestDTO` (defined in `bff-service/src/main/java/com/tvsm/bff/dto/ClaimCreateRequestDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channel | string | False | — |
| claimData | ClaimDataDTO[] | False | — |

Response `200`: `APIResponse<ClaimSummaryResponseDTO>` — fields Unknown (schema not resolved from code)

Response `201`: None (no body)

Response `400`: None (no body)


### POST /api/v1/claims/analytics/stats

Handler: `ClaimAnalyticsController.retrieveClaimIndicators` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimAnalyticsController.java:33`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AnalyticsRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/AnalyticsRequestDTO.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| jobCardIndicatorKeys | enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][] | False | — |
| dealerId | string | False | — |

Response `200`: `APIResponse<AnalyticsResponseDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /api/v1/claims/bulk-upload

Handler: `ClaimController.bulkUploadClaims` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:190`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `ClaimBulkUploadRequestDTO` (defined in `claim-service/src/main/java/com/tvsm/claim/dto/ClaimBulkUploadRequestDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| url | string | False | — |
| name | string | False | — |
| size | integer | False | — |
| type | string | False | — |
| parsedClaimOperations | ParsedClaimOperation[] | False | — |

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/claims/bulk-upload/history

Handler: `ClaimController.getBulkUploadList` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:207`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<PageResponseDTO<BulkUploadDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/claims/close

Handler: `ClaimController.closeClaim` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:175`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CloseClaimRequestDTO` (defined in `claim-service/src/main/java/com/tvsm/claim/dto/CloseClaimRequestDTO.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| claimId | string | False | — |
| comment | string | False | — |

Response `200`: `APIResponse<ClaimIdResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/claims/dashboard

Handler: `ClaimController.getClaimDashboard` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:144`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<ClaimDashboardResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/claims/details

Handler: `ClaimController.getClaimsByVinAndStatus` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:246`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `StatusFilterRequestDTO` (defined in `appointment-service/src/main/java/com/tvsm/appointment/dto/StatusFilterRequestDTO.java:21`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| filters | FilterEntry[] | True | valid |

Response `200`: `APIResponse<ClaimResponseDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/claims/download

Handler: `ClaimController.downloadClaims` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:58`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| locale | query | string | False | — |
| timeZone | query | string | False | — |
| channelPartnerId | query | string | False | — |

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<ClaimsDownloadDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/claims/list

Handler: `ClaimController.getClaims` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:44`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<PageResponseDTO<ClaimResponseDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/claims/workflow/update

Handler: `ClaimController.workflowUpdate` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:118`)  
Callers: Unknown  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v2/claims/sap-sync

Handler: `ClaimJobController.sapDataLakeSyncClaims` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimJobController.java:29`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `APIResponse<ClaimIdResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### PUT /api/v1/claims/update

Handler: `ClaimController.updateClaim` (`claim-service/src/main/java/com/tvsm/claim/controller/ClaimController.java:103`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `ClaimUpdateRequestDTO` (defined in `claim-service/src/main/java/com/tvsm/claim/dto/ClaimUpdateRequestDTO.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| claimId | string | True | — |
| status | enum[SUBMITTED,APPROVED,REJECTED,UNDER_REVIEW,PAID] | False | — |
| catalogOperations | CatalogOperationsRequestDTO | True | valid |

Response `200`: `APIResponse<ClaimIdResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/collateral/create

Handler: `CollateralController.createCollateral` (`collateral-service/src/main/java/com/tvsm/collateral/controller/CollateralController.java:35`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CollateralDto` (defined in `collateral-service/src/main/java/com/tvsm/collateral/dto/CollateralDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| collateralId | uuid | False | — |
| title | string | False | — |
| documentType | string | False | — |
| tags | string[] | False | — |
| validFrom | datetime | False | — |
| media | CollateralMediaDto | False | — |
| createdAt | datetime | False | — |

Response `200`: `APIResponse<CollateralDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/collateral/search

Handler: `CollateralController.getCollaterals` (`collateral-service/src/main/java/com/tvsm/collateral/controller/CollateralController.java:54`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CollateralSearchRequestDto` (defined in `collateral-service/src/main/java/com/tvsm/collateral/dto/CollateralSearchRequestDto.java:6`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| page | integer | False | — |
| limit | integer | False | — |
| sort | Sort[] | False | — |

Response `200`: `APIResponse<PaginatedResponse<CollateralDto>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/lead-allocation/assign

Handler: `LeadAllocationController.assignDefaultUsers` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java:74`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AssignDefaultUsersRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/AssignDefaultUsersRequestDTO.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | DataPayload | True | valid |

Response `200`: `APIResponse<AssignDefaultUsersResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)

Response `501`: None (no body)


### POST /api/v1/lead-allocation/list

Handler: `LeadAllocationController.getLeadAllocationList` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java:34`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `LeadAllocationListRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/LeadAllocationListRequestDTO.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| type | string | False | pattern=SERVICE\|SALES |

Response `200`: `APIResponse<LeadAllocationDataDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/lead-allocation/tracker/get

Handler: `LeadAllocationController.getTracker` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java:135`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `RoundRobinTrackerGetRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/RoundRobinTrackerGetRequestDTO.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channelPartnerId | string | True | — |
| tenantId | string | True | — |
| allocationType | string | True | — |
| entityId | string | True | — |

Response `200`: `APIResponse<RoundRobinTrackerResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/lead-allocation/tracker/upsert

Handler: `LeadAllocationController.upsertTracker` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java:95`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `RoundRobinTrackerUpsertRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/RoundRobinTrackerUpsertRequestDTO.java:17`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channelPartnerId | string | True | — |
| tenantId | string | True | — |
| allocationType | string | True | — |
| entityId | string | True | — |
| lastAssignedUserId | string | True | — |
| modifiedBy | string | False | — |

Response `200`: `APIResponse<RoundRobinTrackerResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/lead-allocation/update

Handler: `LeadAllocationController.updateAllocation` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationController.java:54`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `UpdateAllocationRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/UpdateAllocationRequestDTO.java:22`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | ContentItemDTO[] | True | valid |

Response `200`: `APIResponse<UpdateAllocationResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/lead-allocation/list

Handler: `LeadAllocationSystemController.getLeadAllocationList` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationSystemController.java:48`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `LeadAllocationListWrapperDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/LeadAllocationListWrapperDTO.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerId | string | True | — |
| tenantId | string | True | — |
| leadAllocationListRequest | LeadAllocationListRequestDTO | True | valid |

Response `200`: `APIResponse<LeadAllocationDataDTO[]>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/lead-allocation/tracker/get

Handler: `LeadAllocationSystemController.getTracker` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationSystemController.java:74`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `RoundRobinTrackerGetRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/RoundRobinTrackerGetRequestDTO.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channelPartnerId | string | True | — |
| tenantId | string | True | — |
| allocationType | string | True | — |
| entityId | string | True | — |

Response `200`: `APIResponse<RoundRobinTrackerResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/lead-allocation/tracker/upsert

Handler: `LeadAllocationSystemController.upsertTracker` (`lead-allocation/src/main/java/com/tvsm/leadallocation/controller/LeadAllocationSystemController.java:120`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `RoundRobinTrackerUpsertRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/RoundRobinTrackerUpsertRequestDTO.java:17`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| channelPartnerId | string | True | — |
| tenantId | string | True | — |
| allocationType | string | True | — |
| entityId | string | True | — |
| lastAssignedUserId | string | True | — |
| modifiedBy | string | False | — |

Response `200`: `APIResponse<RoundRobinTrackerResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /api/v1/notification-action-config/all

Handler: `NotificationActionConfigController.getAllActiveConfigs` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationActionConfigController.java:40`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `NotificationActionConfigResponseDto[]` — fields Unknown (schema not resolved from code)


### GET /api/v1/notification-action-config/event-type/{eventType}

Handler: `NotificationActionConfigController.getByEventType` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationActionConfigController.java:60`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | path | string | True | — |

Response `200`: `NotificationActionConfigResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationActionConfigResponseDto.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationActionConfigId | string | False | — |
| eventType | string | False | — |
| actionType | string | False | — |
| targetSubcategoryCode | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| personas | PersonaConfig[] | False | — |
| expectedData | ExpectedDataConfig[] | False | — |
| isActive | boolean | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### GET /api/v1/notification-action-config/subcategory/{subcategoryCode}

Handler: `NotificationActionConfigController.getBySubcategoryCode` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationActionConfigController.java:92`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| subcategoryCode | path | string | True | — |

Response `200`: `NotificationActionConfigResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationActionConfigResponseDto.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationActionConfigId | string | False | — |
| eventType | string | False | — |
| actionType | string | False | — |
| targetSubcategoryCode | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| personas | PersonaConfig[] | False | — |
| expectedData | ExpectedDataConfig[] | False | — |
| isActive | boolean | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### GET /api/v1/notification-category/by-subcategory-code/{code}

Handler: `NotificationCategoryController.getCategoryBySubCategoryCode` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java:72`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| code | path | string | True | — |
| tenantId | query | string | True | — |
| channelEntityId | query | string | True | — |

Response `200`: `NotificationCategoryResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationCategoryResponseDto.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationCategoryId | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| code | string | False | — |
| name | string | False | — |
| description | string | False | — |
| isActive | boolean | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |
| subCategories | NotificationSubCategoryResponseDto[] | False | — |


### POST /api/v1/notification-action-config/cache/refresh

Handler: `NotificationActionConfigController.refreshCache` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationActionConfigController.java:128`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `NotificationActionConfigResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-category/all

Handler: `NotificationCategoryController.getAllCategories` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java:39`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationCategoryRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationCategoryRequestDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationCategoryResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-category/cache/refresh

Handler: `NotificationCategoryController.refreshCache` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java:88`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `NotificationCategoryResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-category/list

Handler: `NotificationCategoryController.getCategoriesForUser` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java:56`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationCategoryRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationCategoryRequestDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationCategoryResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-category/role-mapping/reload

Handler: `NotificationCategoryController.reloadRoleMapping` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationCategoryController.java:102`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `string` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-device/deregister

Handler: `NotificationDeviceController.deregisterDeviceForUser` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationDeviceController.java:56`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationDeviceDeregisterRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationDeviceDeregisterRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| deviceToken | string | True | maxLength=2000 |
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationDeviceResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationDeviceResponseDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationDeviceId | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| currentUserId | string | False | — |
| deviceToken | string | False | — |
| platform | string | False | — |
| isActive | boolean | False | — |
| lastActiveAt | datetime | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### POST /api/v1/notification-device/register

Handler: `NotificationDeviceController.registerDeviceForUser` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationDeviceController.java:40`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationDeviceRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationDeviceRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| deviceToken | string | True | maxLength=2000 |
| platform | string | False | maxLength=50 |
| userId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationDeviceResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationDeviceResponseDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationDeviceId | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| currentUserId | string | False | — |
| deviceToken | string | False | — |
| platform | string | False | — |
| isActive | boolean | False | — |
| lastActiveAt | datetime | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### POST /api/v1/notification-event-consumer/process

Handler: `NotificationEventConsumerController.process` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationEventConsumerController.java:45`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationEventDto<any>` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/model/NotificationEventDto.java:26`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| recipients | NotificationRecipientDto[] | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| categoryCode | string | False | — |
| subCategoryCode | string | False | — |
| eventId | string | False | — |
| referenceId | string | False | — |
| payload | any | False | — |
| params | map<string,object> | False | — |

Response `200`: `map<string,object>` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-message/push/send

Handler: `NotificationMessageController.sendPushNotification` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java:49`)  
Callers: Unknown  
Auth: Unknown

Request body: `PushNotificationRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/PushNotificationRequestDto.java:15`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | True | — |
| subCategoryCode | string | True | maxLength=100 |
| eventId | string | True | maxLength=100 |
| referenceId | string | False | maxLength=100 |
| title | string | True | maxLength=500 |
| message | string | True | — |
| deepUrl | DeepUrlDto[] | False | — |

Response `200`: `NotificationMessageResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageResponseDto.java:14`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationMessageId | string | False | — |
| tenantId | string | False | — |
| channelEntityType | string | False | — |
| channelEntityId | string | False | — |
| eventId | string | False | — |
| currentUserId | string | False | — |
| notificationCategoryId | string | False | — |
| categoryCode | string | False | — |
| categoryName | string | False | — |
| notificationSubCategoryId | string | False | — |
| subCategoryCode | string | False | — |
| subCategoryName | string | False | — |
| notificationTypeId | string | False | — |
| typeCode | string | False | — |
| typeName | string | False | — |
| providerMessageId | string | False | — |
| referenceId | string | False | — |
| title | string | False | — |
| message | string | False | — |
| deepUrl | DeepUrlDto[] | False | — |
| status | string | False | — |
| retryCount | integer | False | — |
| providerResponse | string | False | — |
| errorMessage | string | False | — |
| sentAt | datetime | False | — |
| deliveredAt | datetime | False | — |
| readAt | datetime | False | — |
| readStatus | boolean | False | — |
| createdAt | datetime | False | — |
| updatedAt | datetime | False | — |


### POST /api/v1/notification-message/read/all

Handler: `NotificationMessageController.markAllAsReadForUser` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java:131`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `NotificationMessageReadResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageId | string | False | — |
| markedRead | boolean | False | — |
| updatedCount | integer | False | — |


### POST /api/v1/notification-message/read/bulk

Handler: `NotificationMessageController.bulkMarkAsReadForUser` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java:115`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| userId | path | string | True | — |

Request body: `NotificationMessageBulkReadRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationMessageBulkReadRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageIds | string[] | True | — |

Response `200`: `NotificationMessageReadResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageId | string | False | — |
| markedRead | boolean | False | — |
| updatedCount | integer | False | — |


### POST /api/v1/notification-message/read/{messageId}

Handler: `NotificationMessageController.markAsReadForUser` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java:101`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| messageId | path | string | True | — |

Response `200`: `NotificationMessageReadResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| messageId | string | False | — |
| markedRead | boolean | False | — |
| updatedCount | integer | False | — |


### POST /api/v1/notification-message/search

Handler: `NotificationMessageController.searchMessagesByUserId` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationMessageController.java:81`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationMessageSearchRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationMessageSearchRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| currentUserId | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `NotificationMessageResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-preference/list

Handler: `NotificationPreferenceController.getPreferencesByUserIdFromRequest` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationPreferenceController.java:41`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationPreferenceRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationPreferenceRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| tenantId | string | False | — |
| dealerId | string | False | — |

Response `200`: `NotificationCategoryPreferenceResponseDto[]` — fields Unknown (schema not resolved from code)


### POST /api/v1/notification-preference/update

Handler: `NotificationPreferenceController.updatePreferencesByUserId` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationPreferenceController.java:55`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `NotificationPreferenceUpdateRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationPreferenceUpdateRequestDto.java:15`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| preferences | PreferenceItemDto[] | True | valid |

Response `200`: `NotificationPreferenceUpdateResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationPreferenceUpdateResponseDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| userId | string | False | — |
| updatedCount | integer | False | — |
| updated | boolean | False | — |


### POST /system/api/v1/notification-seed/reseed

Handler: `NotificationSeedController.reseed` (`notification-service/src/main/java/com/tvsm/notification/controller/NotificationSeedController.java:37`)  
Callers: Unknown  
Auth: Unknown

Request body: `NotificationSeedRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationSeedRequestDto.java:15`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| update | boolean | False | — |
| updateData | NotificationSeedData | False | — |
| dealers | DealerDetail[] | True | valid |

Response `200`: `NotificationSeedResponseDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationSeedResponseDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| update | boolean | False | — |
| requested | integer | False | — |
| succeeded | integer | False | — |
| failed | integer | False | — |
| results | DealerResult[] | False | — |


### POST /api/v1/npqr/create

Handler: `NpqrController.createQualityReport` (`npqr-service/src/main/java/com/tvsm/npqr/controller/NpqrController.java:31`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| Authorization | header | string | True | — |

Request body: `QualityReportCreateRequestDTO` (defined in `npqr-service/src/main/java/com/tvsm/npqr/dto/QualityReportCreateRequestDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| productType | string | True | — |
| catalogSkuId | string | False | — |
| partNo | string | False | — |
| vehicleSAPNo | string | False | — |
| issueType | string | True | — |
| issueDescription | string | True | — |
| isStandardPart | boolean | True | — |
| catalogName | string | True | — |
| quantity | integer | False | — |
| uom | string | False | — |
| issueMode | string | False | — |
| faultType | string | False | — |
| defectCode | string | False | — |
| vin | string | False | — |
| mileageReading | integer | False | — |
| fileMapping | FileMappingCreateRequestDTO[] | True | valid |

Response `200`: `APIResponse<QualityReportResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/npqr/list

Handler: `NpqrController.getQualityReportList` (`npqr-service/src/main/java/com/tvsm/npqr/controller/NpqrController.java:46`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| Authorization | header | string | True | — |

Request body: `SearchRequestDTO` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<NpqrListResponseDTO>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/cart/active-cart

Handler: `CartController.getActiveCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:112`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderCategory | query | string | True | — |

Response `200`: `APIResponse<CartDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### GET /api/v1/cart/{cartId}

Handler: `CartController.getCartById` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:83`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| cartId | path | uuid | True | — |

Response `200`: `APIResponse<CartResponse>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### GET /api/v1/grn/details/{grnId}

Handler: `GrnController.getGrnDetails` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:30`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| grnId | path | uuid | True | — |

Response `200`: `APIResponse<GrnDetailResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/invoice/delivery-view/{invoiceId}

Handler: `InvoiceController.getInvoiceDeliveryView` (`order-service/src/main/java/com/tvsm/order/controller/InvoiceController.java:55`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| invoiceId | path | uuid | True | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `APIResponse<InvoiceDeliveryViewResponseDto>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)


### GET /api/v1/order/active-cart

Handler: `OrderController.getActiveCart` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:168`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderCategory | query | string | True | — |

Response `200`: `APIResponse<OrderDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/order/cancellation-reasons

Handler: `OrderController.getCancellationReasons` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:106`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `APIResponse<map<string,string>[]>` — fields Unknown (schema not resolved from code)


### GET /api/v1/order/get

Handler: `OrderController.getOrder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:118`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | query | string | True | — |
| requiredOrderLine | query | boolean | False | — |
| requireOrderHistory | query | boolean | False | — |
| requireDeliveryView | query | boolean | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `APIResponse<OrderDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/order/open-qty/{productCatalogId}

Handler: `OrderController.getOpenQtyByProductCatalogId` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:217`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productCatalogId | path | string | True | — |
| dealerId | query | string | False | — |

Response `200`: `APIResponse<map<string,integer>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/order/orderedPartDetails

Handler: `OrderController.getOrderedPartsDetails` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:206`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| partId | query | string | True | — |
| orderId | query | string | True | — |

Response `200`: `APIResponse<PartDetailsResponse>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/order/status-counts

Handler: `OrderController.getOrderStatusCounts` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:307`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productType | query | string | True | — |
| dealerId | query | string | False | — |

Response `200`: `APIResponse<OrderStatusCountDto>` — fields Unknown (schema not resolved from code)


### POST /api/v1/cart/bulk-upload

Handler: `CartController.bulkUploadCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:145`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | query | binary | True | — |
| orderCategoryType | query | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/cart/create

Handler: `CartController.createCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:35`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CartRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/CartRequest.java:6`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderCategoryType | string | False | — |
| cartName | string | False | — |
| cartLines | CartLineRequest[] | False | — |

Response `200`: `APIResponse<CartResponse>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/cart/create-active-cart

Handler: `CartController.setActiveCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:127`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| cartId | query | string | True | — |
| categoryType | query | string | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/cart/delete/{cartId}

Handler: `CartController.deleteCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:67`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| cartId | path | uuid | True | — |

Response `200`: `APIResponse<any>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/cart/reorder

Handler: `CartController.reorderCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:168`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CartReorderRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/CartReorderRequest.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| cartId | string | False | — |

Response `200`: `APIResponse<CartResponse>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/cart/search

Handler: `CartController.searchCarts` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:97`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/common/request/SearchRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| page | integer | False | — |
| limit | integer | False | — |
| sort | Sort[] | False | — |

Response `200`: `APIResponse<PaginatedResponse<CartDto>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/cart/update

Handler: `CartController.updateCart` (`order-service/src/main/java/com/tvsm/order/controller/CartController.java:51`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CartUpdateRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/CartUpdateRequest.java:5`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| cartId | string | False | — |
| cartName | string | False | — |
| isDeleted | boolean | False | — |
| entityId | string | False | — |
| entityType | string | False | — |
| orderCategoryType | string | False | — |
| orderLineOperations | CartLineOperations | False | — |

Response `200`: `APIResponse<CartUpdateResponse>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/grn/complete

Handler: `GrnController.completeGrn` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:71`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `GrnCompleteRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/GrnCompleteRequestDto.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| grnId | uuid | False | — |
| invoiceId | uuid | False | — |

Response `200`: `APIResponse<GrnCompleteResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/grn/delivery-details/add

Handler: `GrnController.addDeliveryDetails` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:86`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `GrnDeliveryDetailsRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/GrnDeliveryDetailsRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| grnId | uuid | False | — |
| deliveryStatus | string | False | — |
| receivedAt | datetime | False | — |
| transporterName | string | False | — |
| deliveryVehicleNumber | string | False | — |
| deliveryProofs | DeliveryProofDto[] | False | — |

Response `200`: `APIResponse<GrnDeliveryDetailResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/grn/initiate

Handler: `GrnController.createGrn` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:41`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `GrnCreateRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/GrnCreateRequestDto.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| invoiceId | uuid | False | — |

Response `200`: `APIResponse<GrnDetailResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/grn/search

Handler: `GrnController.searchGrns` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:102`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/common/request/SearchRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| page | integer | False | — |
| limit | integer | False | — |
| sort | Sort[] | False | — |

Response `200`: `APIResponse<PaginatedResponse<GRNSearchResponseDTO>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/grn/update

Handler: `GrnController.updateGrn` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:56`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `GrnUpdateRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/GrnUpdateRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| invoiceId | uuid | False | — |
| grnId | uuid | False | — |
| transitionState | string | False | — |
| grnDetails | GrnDetailUpdateDto[] | False | — |

Response `200`: `APIResponse<GrnUpdateSummaryResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/grn/update-claim-initiated

Handler: `GrnController.updateClaimInitiated` (`order-service/src/main/java/com/tvsm/order/controller/GrnController.java:116`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `UpdateClaimInitiatedRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/UpdateClaimInitiatedRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| grnId | uuid | False | — |
| invoiceId | uuid | False | — |
| claimInitiated | boolean | False | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/invoice/sample-insert

Handler: `InvoiceController.createInvoiceForOrder` (`order-service/src/main/java/com/tvsm/order/controller/InvoiceController.java:47`)  
Callers: Unknown  
Auth: Unknown

Request body: `InvoiceCreateRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/InvoiceCreateRequest.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderId | uuid | False | — |

Response `200`: `APIResponse<Invoice>` — fields Unknown (schema not resolved from code)


### POST /api/v1/invoice/search

Handler: `InvoiceController.searchInvoices` (`order-service/src/main/java/com/tvsm/order/controller/InvoiceController.java:33`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/common/request/SearchRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| page | integer | False | — |
| limit | integer | False | — |
| sort | Sort[] | False | — |

Response `200`: `APIResponse<PaginatedResponse<InvoiceListResponseDto>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/bulk-upload

Handler: `OrderController.bulkUploadOrders` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:278`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| file | query | binary | True | — |
| orderCategoryType | query | string | True | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/cancel

Handler: `OrderController.cancelOrder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:68`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `CancelOrderRequestDTO` (defined in `order-service/src/main/java/com/tvsm/order/dto/CancelOrderRequestDTO.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderId | string | False | — |
| orderCategoryType | string | False | — |
| cancellationReason | string | False | — |
| cancellationComment | string | False | — |
| orderLines | OrderLineRequest[] | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/create

Handler: `OrderController.createOrder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:46`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `OrderRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/OrderRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderCategoryType | string | False | — |
| orderLines | OrderLineRequestDto[] | False | — |
| orderId | string | False | — |
| orderLineOperations | map<string,OrderLineRequestDto[]> | False | — |

Response `200`: `APIResponse<OrderResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/create-active-cart

Handler: `OrderController.setCart` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:229`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| orderId | query | string | True | — |
| categoryType | query | string | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/delete-order/{id}

Handler: `OrderController.deleteOrder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:240`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/draft/update

Handler: `OrderController.handleOrderAction` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:134`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `OrderActionRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/OrderActionRequestDto.java:5`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | string | False | — |
| action | string | False | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/place-order

Handler: `OrderController.placeOrder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:144`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `PlaceOrderRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/PlaceOrderRequestDto.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderId | string | False | — |
| cartId | string | False | — |
| needOrderBy | string | False | — |
| shipTo | string | False | — |
| orderPriority | string | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)


### POST /api/v1/order/reorder

Handler: `OrderController.reorder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:194`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `OrderRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/OrderRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderCategoryType | string | False | — |
| orderLines | OrderLineRequestDto[] | False | — |
| orderId | string | False | — |
| orderLineOperations | map<string,OrderLineRequestDto[]> | False | — |

Response `200`: `APIResponse<OrderResponseDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/report

Handler: `OrderReportController.getOrderReport` (`order-service/src/main/java/com/tvsm/order/controller/OrderReportController.java:35`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `ReportRequest` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/reports/ReportRequest.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerId | string | False | — |
| reportType | string | False | — |
| startDate | string | False | — |
| endDate | string | False | — |
| page | integer | False | — |
| size | integer | False | — |
| tenant | string | False | — |
| locale | string | False | — |
| timeZone | string | False | — |

Response `200`: `APIResponse<PaginatedResponse<object>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/sale-order-no/list

Handler: `OrderController.retrieveERPSaleNumber` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:252`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SalesOrderNoRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/SalesOrderNoRequest.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| tenantIds | string[] | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/search

Handler: `OrderController.searchOrders` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:321`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SearchRequestDto` (defined in `data-access-service/src/main/java/com/tvsm/dataaccess/common/request/SearchRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| page | integer | False | — |
| limit | integer | False | — |
| sort | Sort[] | False | — |

Response `200`: `APIResponse<PaginatedResponse<OrderDto>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/status/reconciliation

Handler: `OrderController.reconciliationOrderStatusFromGRN` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:335`)  
Callers: Unknown  
Auth: Unknown

Request body: `uuid[]` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/sync-erp-status

Handler: `OrderController.syncErpOrderStatus` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:262`)  
Callers: Unknown  
Auth: Unknown

Request body: `SyncERPStatusRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/SyncERPStatusRequest.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| erpOrderUpdateDtos | ERPOrderUpdateDto[] | False | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/update-allocation

Handler: `OrderController.updateOrderLineAllocation` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:84`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `UpdateAllocationRequestDTO` (defined in `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/UpdateAllocationRequestDTO.java:22`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | ContentItemDTO[] | True | valid |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /api/v1/order/workflow/update

Handler: `OrderController.workflowUpdate` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:181`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `map<string,object>` — fields Unknown (schema not resolved from code)

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v1/erp-invoice/insert

Handler: `InternalERPServiceController.insertERPInvoice` (`order-service/src/main/java/com/tvsm/order/controller/InternalERPServiceController.java:31`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `InsertInvoiceRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/InsertInvoiceRequest.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| erpInvoices | ERPInvoiceDto[] | False | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v1/order/analytics

Handler: `OrderAnalyticsController.retrieveBooking` (`order-service/src/main/java/com/tvsm/order/controller/OrderAnalyticsController.java:29`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `AnalyticsRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/AnalyticsRequestDto.java:8`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| indicatorKey | string | False | — |
| dealerId | string | False | — |
| tenantId | string | False | — |

Response `200`: `APIResponse<map<string,integer>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/order/erp-sale-order-no/list

Handler: `InternalERPServiceController.retrieveERPSaleNumber` (`order-service/src/main/java/com/tvsm/order/controller/InternalERPServiceController.java:43`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SalesOrderNoRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/SalesOrderNoRequest.java:7`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| tenantIds | string[] | False | — |

Response `200`: `APIResponse<object>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### POST /system/api/v1/order/erp-sync-status

Handler: `InternalERPServiceController.syncErpOrderStatus` (`order-service/src/main/java/com/tvsm/order/controller/InternalERPServiceController.java:53`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `SyncERPStatusRequest` (defined in `order-service/src/main/java/com/tvsm/order/dto/SyncERPStatusRequest.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| erpOrderUpdateDtos | ERPOrderUpdateDto[] | False | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### PUT /api/v1/order/update

Handler: `OrderController.updateOrder` (`order-service/src/main/java/com/tvsm/order/controller/OrderController.java:58`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `OrderRequestDto` (defined in `order-service/src/main/java/com/tvsm/order/dto/OrderRequestDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| orderCategoryType | string | False | — |
| orderLines | OrderLineRequestDto[] | False | — |
| orderId | string | False | — |
| orderLineOperations | map<string,OrderLineRequestDto[]> | False | — |

Response `200`: `APIResponse<OrderOperationResults>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)


### GET /api/v1/training/get/{trainingId}

Handler: `TrainingController.getTraining` (`training-service/src/main/java/com/tvsm/training/controller/TrainingController.java:56`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| trainingId | path | uuid | True | — |

Response `200`: `APIResponse<TrainingDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /api/v1/training/create

Handler: `TrainingController.createTraining` (`training-service/src/main/java/com/tvsm/training/controller/TrainingController.java:36`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `TrainingDto` (defined in `training-service/src/main/java/com/tvsm/training/dto/TrainingDto.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| trainingId | uuid | False | — |
| type | string | False | — |
| title | string | False | — |
| description | string | False | — |
| validFrom | datetime | False | — |
| validTo | datetime | False | — |
| criticality | string | False | — |
| duration | string | False | — |
| readCount | integer | False | — |
| tags | string[] | False | — |
| media | TrainingMediaDto[] | False | — |
| externalLinks | string[] | False | — |
| userAction | UserAction[] | False | — |

Response `200`: `APIResponse<TrainingDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/training/read

Handler: `TrainingController.recordTrainingRead` (`training-service/src/main/java/com/tvsm/training/controller/TrainingController.java:107`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `TrainingReadLogDto` (defined in `training-service/src/main/java/com/tvsm/training/dto/TrainingReadLogDto.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| trainingReadLogId | uuid | False | — |
| trainingId | uuid | False | — |
| userId | string | False | — |
| readAt | datetime | False | — |

Response `200`: `APIResponse<TrainingReadLogDto>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/training/search

Handler: `TrainingController.getTrainings` (`training-service/src/main/java/com/tvsm/training/controller/TrainingController.java:77`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `TrainingSearchRequestDto` (defined in `training-service/src/main/java/com/tvsm/training/dto/TrainingSearchRequestDto.java:6`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| and | Filter[] | False | — |
| or | Filter[] | False | — |
| page | integer | False | — |
| limit | integer | False | — |
| sort | Sort[] | False | — |

Response `200`: `APIResponse<PaginatedResponse<TrainingSearchResponse>>` — fields Unknown (schema not resolved from code)

Response `400`: None (no body)

Response `500`: None (no body)


### GET /api/health

Handler: `ApplicationHealthController.health` (`tvs-cps-app/src/main/java/com/tvsm/cps/backend/controller/ApplicationHealthController.java:39`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `APIResponse<map<string,object>>` — fields Unknown (schema not resolved from code)


### GET /api/health/simple

Handler: `ApplicationHealthController.simpleHealth` (`tvs-cps-app/src/main/java/com/tvsm/cps/backend/controller/ApplicationHealthController.java:66`)  
Callers: Unknown  
Auth: Unknown

Response `200`: `APIResponse<map<string,string>>` — fields Unknown (schema not resolved from code)


### GET /api/v1/workflow/instance/{workflowId}

Handler: `WorkflowController.getWorkflowDetail` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java:81`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| workflowId | path | uuid | True | — |

Response `200`: `WorkflowResponse` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowResponse.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| wfId | uuid | False | — |
| tenantId | string | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| initContext | object | False | — |
| createdOn | datetime | False | — |
| initiatingChannelType | string | False | — |
| initiatingChannelId | string | False | — |
| entityId | string | False | — |
| initiatedBy | string | False | — |
| updatedBy | string | False | — |
| lastUpdatedOn | datetime | False | — |
| latestStatus | string | False | — |
| nextActorType | string | False | — |
| nextActorId | string | False | — |
| nextActorContext | object | False | — |
| history | WorkflowHistoryResponse[] | False | — |

Response `404`: None (no body)

Response `500`: None (no body)


### GET /api/v1/workflow/instance/{workflowId}/status

Handler: `WorkflowController.getWorkflowStatus` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java:95`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| workflowId | path | uuid | True | — |

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)


### GET /api/v1/workflow/items

Handler: `WorkflowController.getWorkflowItems` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java:63`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| actorType | query | string | True | — |
| actorId | query | string | True | — |
| allFlows | query | boolean | False | — |
| page | query | integer | False | — |
| size | query | integer | False | — |

Response `200`: `APIResponse<WorkflowResponse[]>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### GET /api/v1/workflow/template/{entityOperationType}

Handler: `WorkflowTemplateController.getActiveTemplate` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java:63`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| entityOperationType | path | string | True | — |

Response `200`: `WorkflowTemplateResponse` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateResponse.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | uuid | False | — |
| tenantId | string | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| workflowMetadata | string | False | — |
| workflowRules | string | False | — |
| createdOn | datetime | False | — |
| updatedOn | datetime | False | — |
| status | enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED] | False | — |
| createdBy | string | False | — |
| addlInfo | string | False | — |
| activationDate | datetime | False | — |

Response `404`: None (no body)

Response `500`: None (no body)


### POST /api/v1/workflow/action

Handler: `WorkflowController.performAction` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java:48`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `WorkflowActionRequest` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowActionRequest.java:11`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| wfId | uuid | False | — |
| action | string | False | — |
| comments | string | False | — |
| actionContext | object | False | — |

Response `200`: `WorkflowResponse` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowResponse.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| wfId | uuid | False | — |
| tenantId | string | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| initContext | object | False | — |
| createdOn | datetime | False | — |
| initiatingChannelType | string | False | — |
| initiatingChannelId | string | False | — |
| entityId | string | False | — |
| initiatedBy | string | False | — |
| updatedBy | string | False | — |
| lastUpdatedOn | datetime | False | — |
| latestStatus | string | False | — |
| nextActorType | string | False | — |
| nextActorId | string | False | — |
| nextActorContext | object | False | — |
| history | WorkflowHistoryResponse[] | False | — |

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /api/v1/workflow/assignment/process

Handler: `UserAssignmentController.processAssignment` (`workflow-service/src/main/java/com/tvsm/workflow/controller/UserAssignmentController.java:37`)  
Callers: Unknown  
Auth: Unknown

Request body: `AssignmentTriggerRequestDTO` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/assignment/AssignmentTriggerRequestDTO.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| genericServiceId | string | True | — |
| channelPartnerId | string | True | — |
| dealerName | string | False | — |
| tenantId | string | True | — |
| channel | string | False | — |
| entityType | string | True | — |
| entitySubType | string | False | — |
| eligibleUsers | EligibleUserDTO[] | False | — |
| lastAssignedUserId | string | False | — |

Response `200`: `AssignmentTriggerResponseDTO` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/assignment/AssignmentTriggerResponseDTO.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| genericServiceId | string | False | — |
| strategy | enum[FALLBACK,SINGLE_USER,ROUND_ROBIN] | False | — |
| selectedUserId | string | False | — |
| executiveName | string | False | — |
| serviceUpdated | boolean | False | — |
| trackerUpdated | boolean | False | — |
| reason | string | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### POST /api/v1/workflow/init

Handler: `WorkflowController.initializeWorkflow` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowController.java:34`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `WorkflowInitRequest` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowInitRequest.java:9`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| entityOperationType | string | False | — |
| initiatingChannelType | string | False | — |
| initiatingChannelId | string | False | — |
| entityId | string | False | — |
| initContext | object | False | — |

Response `200`: `WorkflowResponse` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowResponse.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| wfId | uuid | False | — |
| tenantId | string | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| initContext | object | False | — |
| createdOn | datetime | False | — |
| initiatingChannelType | string | False | — |
| initiatingChannelId | string | False | — |
| entityId | string | False | — |
| initiatedBy | string | False | — |
| updatedBy | string | False | — |
| lastUpdatedOn | datetime | False | — |
| latestStatus | string | False | — |
| nextActorType | string | False | — |
| nextActorId | string | False | — |
| nextActorContext | object | False | — |
| history | WorkflowHistoryResponse[] | False | — |

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/workflow/template/create

Handler: `WorkflowTemplateController.createTemplate` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java:34`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `WorkflowTemplateRequest` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateRequest.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | uuid | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| workflowMetadata | string | False | — |
| workflowRules | string | False | — |
| status | enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED] | False | — |
| addlInfo | string | False | — |
| activationDate | datetime | False | — |

Response `200`: `WorkflowTemplateResponse` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateResponse.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | uuid | False | — |
| tenantId | string | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| workflowMetadata | string | False | — |
| workflowRules | string | False | — |
| createdOn | datetime | False | — |
| updatedOn | datetime | False | — |
| status | enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED] | False | — |
| createdBy | string | False | — |
| addlInfo | string | False | — |
| activationDate | datetime | False | — |

Response `400`: None (no body)

Response `500`: None (no body)


### POST /api/v1/workflow/template/process-activations

Handler: `WorkflowTemplateController.processTemplateActivations` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java:90`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Response `200`: `APIResponse<string>` — fields Unknown (schema not resolved from code)

Response `500`: None (no body)


### POST /api/v1/workflow/template/update

Handler: `WorkflowTemplateController.updateTemplate` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java:48`)  
Callers: `tvs-cps-backend`  
Auth: Unknown

Request body: `WorkflowTemplateRequest` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateRequest.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | uuid | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| workflowMetadata | string | False | — |
| workflowRules | string | False | — |
| status | enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED] | False | — |
| addlInfo | string | False | — |
| activationDate | datetime | False | — |

Response `200`: `WorkflowTemplateResponse` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateResponse.java:13`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | uuid | False | — |
| tenantId | string | False | — |
| entityOperationType | string | False | — |
| version | string | False | — |
| workflowMetadata | string | False | — |
| workflowRules | string | False | — |
| createdOn | datetime | False | — |
| updatedOn | datetime | False | — |
| status | enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED] | False | — |
| createdBy | string | False | — |
| addlInfo | string | False | — |
| activationDate | datetime | False | — |

Response `400`: None (no body)

Response `404`: None (no body)

Response `500`: None (no body)


### POST /system/api/v1/workflow/assignment/process

Handler: `UserAssignmentSystemController.processAssignment` (`workflow-service/src/main/java/com/tvsm/workflow/controller/UserAssignmentSystemController.java:37`)  
Callers: Unknown  
Auth: Unknown

Request body: `AssignmentTriggerRequestDTO` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/assignment/AssignmentTriggerRequestDTO.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| genericServiceId | string | True | — |
| channelPartnerId | string | True | — |
| dealerName | string | False | — |
| tenantId | string | True | — |
| channel | string | False | — |
| entityType | string | True | — |
| entitySubType | string | False | — |
| eligibleUsers | EligibleUserDTO[] | False | — |
| lastAssignedUserId | string | False | — |

Response `200`: `AssignmentTriggerResponseDTO` (defined in `workflow-service/src/main/java/com/tvsm/workflow/dto/assignment/AssignmentTriggerResponseDTO.java:16`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| genericServiceId | string | False | — |
| strategy | enum[FALLBACK,SINGLE_USER,ROUND_ROBIN] | False | — |
| selectedUserId | string | False | — |
| executiveName | string | False | — |
| serviceUpdated | boolean | False | — |
| trackerUpdated | boolean | False | — |
| reason | string | False | — |

Response `400`: None (no body)

Response `401`: None (no body)

Response `500`: None (no body)


### PUT /api/v1/workflow/template/{id}/decommission

Handler: `WorkflowTemplateController.decommissionTemplate` (`workflow-service/src/main/java/com/tvsm/workflow/controller/WorkflowTemplateController.java:77`)  
Callers: Unknown  
Auth: Unknown

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | uuid | True | — |

Response `200`: `APIResponse<any>` — fields Unknown (schema not resolved from code)

Response `404`: None (no body)

Response `500`: None (no body)

## Outbound Calls

`tvs-cps-backend` makes 240 outbound call(s) listed in service.yaml `outbound`.

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality | Client (file:line) |
|---|---|---|---|---|---|---|---|
| external:onetrust | http | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| tvs-cps-backend | POST | `/cps/api/v1/customer/search` | CustomerVehicleSearchRequestDTO | CustomerListResponseDTO | base URL from config:bff.customer-service-local.base-url | hard | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentExcelProcessorService.java:314` |
| tvs-cps-customer | POST | `/api/v1/customer/external/search` | CustomerVehicleSearchRequestDTO | string | base URL from config:bff.customer-service.base-url | hard | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/util/ExternalAppointmentNotificationTriggerUtil.java:269` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/list` | LeadAllocationListRequestDTO, LeadAllocationListWrapperDTO | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java:59` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/tracker/get` | map<string,string> | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java:59` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/tracker/upsert` | map<string,string> | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java:59` |
| Unknown | POST | `/{}{}` | map<string,object> | Unknown | base URL from config:bff.workflow-service.base-url | Unknown | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/client/WorkflowAppointmentAssignmentClient.java:66` |
| tvs-cps-backend | GET | `/api/v1/announcement/user/banners` | Unknown | map<string,object> | base URL from config:bff.announcement-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:137` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.announcement-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| tvs-cps-backend | GET | `/api/v1/appointments/master` | Unknown | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:230` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.appointment-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.billing-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/v2/catalogs/labour` | Unknown | map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java:897` |
| Unknown | GET | `/v2/catalogs/parts/assemblies` | Unknown | map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java:311` |
| Unknown | GET | `/v2/catalogs/search/part` | Unknown | map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java:632` |
| Unknown | GET | `/v2/catalogs/vehicles` | string | VehicleSearchResponseDTO, map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java:187` |
| Unknown | GET | `/v2/catalogs{}` | Unknown | map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CatalogController.java:193` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| tvs-cps-backend | GET | `/api/v1/claims/master` | Unknown | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:408` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.claim-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/` | HttpHeaders | string | base URL from config:bff.inventory-service-internal.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CustomerVehicleClient.java:131` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.inventory-service-internal.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| tvs-cps-inventory | GET | `/api/v1/inventory/bin/get` | Unknown | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:315` |
| tvs-cps-inventory | GET | `/api/v1/inventory/location/get{}` | Unknown | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:237` |
| tvs-cps-inventory | GET | `/api/v1/inventory/rack/get` | Unknown | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:276` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.inventory-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| tvs-cps-job-card-service | GET | `/api/v1/jobcards/{}` | string | JCDetailsWithMappingsCoreResponseDTO | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/JobCardClient.java:106` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.jobcard-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/api/address/autocomplete` | Unknown | map<string,object>[] | base URL from config:bff.location-master-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/LocationMasterClient.java:73` |
| Unknown | GET | `/api/address/details` | Unknown | map<string,object> | base URL from config:bff.location-master-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/LocationMasterClient.java:129` |
| tvs-cps-backend | GET | `/api/v1/cart/active-cart` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:141` |
| tvs-cps-backend | GET | `/api/v1/order` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:87` |
| tvs-cps-backend | GET | `/api/v1/order/active-cart` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:309` |
| tvs-cps-backend | GET | `/api/v1/order/cancellation-reasons` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:147` |
| tvs-cps-backend | GET | `/api/v1/order/get` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:181` |
| tvs-cps-backend | GET | `/api/v1/order/get-booking-list` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:379` |
| tvs-cps-backend | GET | `/api/v1/order/get-branch` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:239` |
| tvs-cps-backend | GET | `/api/v1/order/get-draft` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:201` |
| tvs-cps-backend | GET | `/api/v1/order/orderedPartDetails` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:369` |
| tvs-cps-backend | GET | `/api/v1/order/status-counts` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:474` |
| Unknown | GET | `/cps{}` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java:558` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.order-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.training-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/list-all` | Unknown | map<string,object> | base URL from config:bff.ums-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/UmsClient.java:93` |
| tvs-cps-backend | GET | `/api/v1/workflow/items` | Unknown | map<string,object> | base URL from config:bff.workflow-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:95` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:bff.workflow-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| Unknown | GET | `/cps{}` | Unknown | map<string,object> | base URL from config:cps-backend.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/CatalogService.java:558` |
| Unknown | GET | `/{}` | Unknown | map<string,object> | base URL from config:cps-backend.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:126` |
| external:onetrust | GET | `/{}/token` | Unknown | string | base URL from config:one-trust.one-trust-collection-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/auth/AuthService.java:142` |
| Unknown | POST | `/` | Unknown | string | base URL from config:azure.token-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| tvs-cps-backend | POST | `/api/v1/announcement/admin/search` | map<string,object> | map<string,object> | base URL from config:bff.announcement-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:152` |
| tvs-cps-backend | POST | `/api/v1/announcement/create` | map<string,object> | map<string,object> | base URL from config:bff.announcement-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:54` |
| tvs-cps-backend | POST | `/api/v1/announcement/read` | map<string,object> | map<string,object> | base URL from config:bff.announcement-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:169` |
| tvs-cps-backend | POST | `/api/v1/announcement/update` | map<string,object> | map<string,object> | base URL from config:bff.announcement-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:86` |
| tvs-cps-backend | POST | `/api/v1/announcement/user/search` | map<string,object> | map<string,object> | base URL from config:bff.announcement-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:69` |
| Unknown | POST | `/{}` | map<string,object> | map<string,object> | base URL from config:bff.announcement-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:102` |
| tvs-cps-backend | POST | `/api/v1/appointments/analytics/stats` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AppointmentAnalyticsBFFService.java:76` |
| tvs-cps-backend | POST | `/api/v1/appointments/bulk-upload` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:323` |
| tvs-cps-backend | POST | `/api/v1/appointments/bulk-upload/history` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:344` |
| tvs-cps-backend | POST | `/api/v1/appointments/count` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:389` |
| tvs-cps-backend | POST | `/api/v1/appointments/create` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/AppointmentClient.java:71` |
| tvs-cps-backend | POST | `/api/v1/appointments/dashboard` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:260` |
| tvs-cps-backend | POST | `/api/v1/appointments/details` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:916` |
| tvs-cps-backend | POST | `/api/v1/appointments/download` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AppointmentBFFService.java:693` |
| tvs-cps-backend | POST | `/api/v1/appointments/list` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AppointmentBFFController.java:82` |
| tvs-cps-backend | POST | `/api/v1/appointments/update` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/AppointmentClient.java:105` |
| tvs-cps-backend | POST | `/cps/api/v1/appointments/analytics/stats/process` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AnalyticsService.java:139` |
| tvs-cps-backend | POST | `/system/api/v1/appointments/list` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/AppointmentClient.java:203` |
| tvs-cps-backend | POST | `/system/api/v1/appointments/update` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/AppointmentClient.java:96` |
| tvs-cps-backend | POST | `/system/api/v2/appointments/auto-close` | map<string,object> | map<string,object> | base URL from config:bff.appointment-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:178` |
| tvs-cps-billing | POST | `/api/v1/billing/create` | map<string,object> | map<string,object> | base URL from config:bff.billing-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:69` |
| tvs-cps-billing | POST | `/api/v1/billing/discard` | map<string,object> | map<string,object> | base URL from config:bff.billing-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:191` |
| tvs-cps-billing | POST | `/api/v1/billing/invoices/search` | map<string,object> | map<string,object> | base URL from config:bff.billing-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:206` |
| tvs-cps-billing | POST | `/api/v1/billing/post-invoice` | map<string,object> | map<string,object> | base URL from config:bff.billing-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BillingBFFService.java:1171` |
| tvs-cps-billing | POST | `/api/v1/billing/report/invoice-list` | map<string,object> | map<string,object> | base URL from config:bff.billing-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BillingReportService.java:173` |
| tvs-cps-billing | POST | `/api/v1/billing/update` | map<string,object> | map<string,object> | base URL from config:bff.billing-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/BillingBFFController.java:91` |
| booking-crud-services | POST | `/booking-service/v2/bookings` | BookingRequestDto | Unknown | base URL from config:bff.booking-service.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/BookingServiceClient.java:50` |
| booking-crud-services | POST | `/booking-service/v2/bookings/search` | BookingSearchRequestDto | Unknown | base URL from config:bff.booking-service.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/BookingServiceClient.java:50` |
| Unknown | POST | `/lead-service/api/leads/one-view` | OneViewRequestDto | Unknown | base URL from config:bff.booking-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/ServiceReminderClient.java:209` |
| Unknown | POST | `/` | map<string,object> | object | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/v2/catalogs/merchandise/colours` | map<string,object> | map<string,object> | base URL from config:bff.catalog-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/CatalogClient.java:822` |
| tvs-cps-backend | POST | `/api/v1/claims` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:166` |
| tvs-cps-backend | POST | `/api/v1/claims/analytics/stats` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/ClaimAnalyticsBFFService.java:65` |
| tvs-cps-backend | POST | `/api/v1/claims/bulk-upload` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/ClaimBFFService.java:883` |
| tvs-cps-backend | POST | `/api/v1/claims/bulk-upload/history` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:532` |
| tvs-cps-backend | POST | `/api/v1/claims/close` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:346` |
| tvs-cps-backend | POST | `/api/v1/claims/dashboard` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:380` |
| tvs-cps-backend | POST | `/api/v1/claims/details` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/SmartSearchBFFService.java:1459` |
| tvs-cps-backend | POST | `/api/v1/claims/download` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/ClaimBFFService.java:913` |
| tvs-cps-backend | POST | `/api/v1/claims/list` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:98` |
| tvs-cps-backend | POST | `/cps/api/v1/claims` | ClaimCreateRequestDTO | string | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/ClaimClient.java:110` |
| tvs-cps-backend | POST | `/cps/api/v1/claims/analytics/stats/process` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AnalyticsService.java:119` |
| tvs-cps-backend | POST | `/system/api/v2/claims/sap-sync` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:205` |
| tvs-cps-backend | POST | `/api/v1/collateral/create` | map<string,object> | map<string,object> | base URL from config:bff.collateral-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CollateralBFFController.java:50` |
| tvs-cps-backend | POST | `/api/v1/collateral/search` | map<string,object> | map<string,object> | base URL from config:bff.collateral-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CollateralBFFController.java:64` |
| tvs-cps-backend | POST | `/cps/api/v1/customer/search` | CustomerVehicleSearchRequestDTO | CustomerListResponseDTO | base URL from config:bff.customer-service-local.base-url | hard | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentExcelProcessorService.java:314` |
| tvs-cps-customer | POST | `/api/v1/customer/add-vehicle` | map<string,object> | map<string,object> | base URL from config:bff.customer-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:250` |
| tvs-cps-customer | POST | `/api/v1/customer/create` | map<string,object> | map<string,object> | base URL from config:bff.customer-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:187` |
| tvs-cps-customer | POST | `/api/v1/customer/delete` | map<string,object> | map<string,object> | base URL from config:bff.customer-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:269` |
| tvs-cps-customer | POST | `/api/v1/customer/external/search` | string | string | base URL from config:bff.customer-service.base-url | hard | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/util/ExternalAppointmentNotificationTriggerUtil.java:269` |
| tvs-cps-customer | POST | `/api/v1/customer/search` | map<string,object> | map<string,object> | base URL from config:bff.customer-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:79` |
| tvs-cps-customer | POST | `/api/v1/customer/update` | map<string,object> | map<string,object> | base URL from config:bff.customer-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CustomerBFFController.java:231` |
| tvs-cps-customer | POST | `/api/v1/vehiclesearch` | map<string,object> | map<string,object> | base URL from config:bff.customer-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/VehicleBFFController.java:80` |
| tvs-cps-backend | POST | `/cps/api/v1/inventory/issue` | UpdateInventoryDTO | string | base URL from config:bff.inventory-service-local.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/InventoryClient.java:54` |
| tvs-cps-inventory | POST | `/api/v1/inventory/bin/create` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:291` |
| tvs-cps-inventory | POST | `/api/v1/inventory/issue` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:74` |
| tvs-cps-inventory | POST | `/api/v1/inventory/list` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:330` |
| tvs-cps-inventory | POST | `/api/v1/inventory/location/create` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:222` |
| tvs-cps-inventory | POST | `/api/v1/inventory/rack/create` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:252` |
| tvs-cps-inventory | POST | `/api/v1/inventory/receive` | map<string,object>[] | object, string | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:89` |
| tvs-cps-inventory | POST | `/api/v1/inventory/report/vehicle-stock-report-list` | ReportRequest | Unknown | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/reports/strategies/VehicleStockStrategy.java:55` |
| tvs-cps-inventory | POST | `/api/v1/vehicle/delivery-date/add` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:146` |
| tvs-cps-inventory | POST | `/api/v1/vehicle/inventory/lookup` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:192` |
| tvs-cps-inventory | POST | `/api/v1/vehicle/pdi` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:375` |
| tvs-cps-inventory | POST | `/api/v1/vehicle/update/stock-type` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryBFFController.java:176` |
| tvs-cps-inventory | POST | `/system/api/v1/inventory/analytics/list` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryAnalyticsBFFController.java:55` |
| tvs-cps-inventory | POST | `/system/api/v1/inventory/analytics/stats` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/strategy/InventoryAnalyticsStrategy.java:83` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:131` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/analytics/stats` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/AppointmentAnalyticsBFFService.java:114` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/bulk-upload` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/JobCardClient.java:328` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/bulk-upload/history` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:341` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/dashboard` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/JobcardBFFController.java:323` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/details` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:1217` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/download` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/JobcardBFFService.java:883` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/list` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/JobCardClient.java:117` |
| tvs-cps-job-card-service | POST | `/api/v1/jobcards/warranty-check` | map<string,object> | map<string,object> | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/JobCardClient.java:302` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/assign` | AssignDefaultUsersRequestDTO | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java:47` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/list` | LeadAllocationListRequestDTO | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java:59` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/tracker/get` | map<string,string> | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java:59` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/tracker/upsert` | map<string,string> | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `appointment-service/src/main/java/com/tvsm/appointment/client/LeadAllocationForAppointmentServiceClient.java:59` |
| tvs-cps-backend | POST | `/api/v1/lead-allocation/update` | UpdateAllocationRequestDTO | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java:47` |
| tvs-cps-backend | POST | `/system/api/v1/lead-allocation/list` | LeadAllocationListBFFWrapperDTO | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java:55` |
| tvs-cps-backend | POST | `/system/api/v1/lead-allocation/tracker/get` | map<string,string> | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java:55` |
| tvs-cps-backend | POST | `/system/api/v1/lead-allocation/tracker/upsert` | map<string,string> | Unknown | base URL from config:bff.lead-allocation.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java:55` |
| Unknown | POST | `/lead-service/api/v2/lead` | LeadCreateRequestDTO | string | base URL from config:bff.lead-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:123` |
| Unknown | POST | `/lead-service/api/v2/lead/update` | map<string,object> | map<string,object> | base URL from config:bff.lead-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:669` |
| Unknown | POST | `/lead-service/api/v2/leads/Count` | map<string,object> | Unknown | base URL from config:bff.lead-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:395` |
| Unknown | POST | `/lead-service/api/v2/leads/all` | map<string,object> | map<string,object> | base URL from config:bff.lead-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:480` |
| Unknown | POST | `/lead-service/api/v2/leads/getdetails` | map<string,object> | map<string,object> | base URL from config:bff.lead-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:802` |
| tvs-cps-backend | POST | `/api/v1/notification-category/all` | NotificationCategoryRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:84` |
| tvs-cps-backend | POST | `/api/v1/notification-category/cache/refresh` | map<string,object> | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:96` |
| tvs-cps-backend | POST | `/api/v1/notification-category/list` | NotificationCategoryRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:57` |
| tvs-cps-backend | POST | `/api/v1/notification-category/role-mapping/reload` | map<string,object> | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationCategoryBFFController.java:108` |
| tvs-cps-backend | POST | `/api/v1/notification-device/deregister` | NotificationDeviceDeregisterRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationDeviceBFFController.java:67` |
| tvs-cps-backend | POST | `/api/v1/notification-device/register` | NotificationDeviceRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationDeviceBFFController.java:52` |
| tvs-cps-backend | POST | `/api/v1/notification-message/read/all` | map<string,object> | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:105` |
| tvs-cps-backend | POST | `/api/v1/notification-message/read/bulk` | NotificationMessageBulkReadRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:93` |
| tvs-cps-backend | POST | `/api/v1/notification-message/search` | NotificationMessageSearchRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationMessageBFFController.java:64` |
| tvs-cps-backend | POST | `/api/v1/notification-preference/list` | NotificationPreferenceRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationPreferenceBFFController.java:59` |
| tvs-cps-backend | POST | `/api/v1/notification-preference/update` | NotificationPreferenceUpdateRequestDto | map<string,object> | base URL from config:bff.notification-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/notification/NotificationPreferenceBFFController.java:76` |
| Unknown | POST | `/{}` | map<string,object> | map<string,object> | base URL from config:bff.notification-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:102` |
| tvs-cps-backend | POST | `/api/v1/npqr/create` | map<string,object> | map<string,object> | base URL from config:bff.npqr-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/NpqrBFFController.java:49` |
| tvs-cps-backend | POST | `/api/v1/npqr/list` | map<string,object> | map<string,object> | base URL from config:bff.npqr-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/NpqrBFFController.java:75` |
| tvs-cps-backend | POST | `/api/v1/cart/bulk-upload` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:208` |
| tvs-cps-backend | POST | `/api/v1/cart/create` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:57` |
| tvs-cps-backend | POST | `/api/v1/cart/create-active-cart` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:162` |
| tvs-cps-backend | POST | `/api/v1/cart/reorder` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:234` |
| tvs-cps-backend | POST | `/api/v1/cart/search` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:89` |
| tvs-cps-backend | POST | `/api/v1/cart/update` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/CartBFFController.java:74` |
| tvs-cps-backend | POST | `/api/v1/grn/delivery-details/add` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:124` |
| tvs-cps-backend | POST | `/api/v1/grn/initiate` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:76` |
| tvs-cps-backend | POST | `/api/v1/grn/search` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:175` |
| tvs-cps-backend | POST | `/api/v1/grn/update` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:92` |
| tvs-cps-backend | POST | `/api/v1/grn/update-claim-initiated` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/GRNClient.java:53` |
| tvs-cps-backend | POST | `/api/v1/grn/upload-docs` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/GrnBFFController.java:160` |
| tvs-cps-backend | POST | `/api/v1/invoice/search` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InvoiceBFFController.java:50` |
| tvs-cps-backend | POST | `/api/v1/order/bulk-upload` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:526` |
| tvs-cps-backend | POST | `/api/v1/order/cancel` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:119` |
| tvs-cps-backend | POST | `/api/v1/order/create` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:59` |
| tvs-cps-backend | POST | `/api/v1/order/create-active-cart` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:424` |
| tvs-cps-backend | POST | `/api/v1/order/draft/update` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:217` |
| tvs-cps-backend | POST | `/api/v1/order/get-all-order` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:454` |
| tvs-cps-backend | POST | `/api/v1/order/get-all-parts` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:289` |
| tvs-cps-backend | POST | `/api/v1/order/get-placed-order` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:273` |
| tvs-cps-backend | POST | `/api/v1/order/place-order` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/OrderBffService.java:39` |
| tvs-cps-backend | POST | `/api/v1/order/reorder` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:341` |
| tvs-cps-backend | POST | `/api/v1/order/report` | ReportRequest | APIResponse<PaginatedResponse<AccessoryPurchaseModel>>, APIResponse<PaginatedResponse<MerchandisePurchaseModel>> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/reports/strategies/AccessoriesOrderStrategy.java:47` |
| tvs-cps-backend | POST | `/api/v1/order/sale-order-no/list` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:404` |
| tvs-cps-backend | POST | `/api/v1/order/search` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:548` |
| tvs-cps-backend | POST | `/api/v1/order/update-allocation` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:134` |
| tvs-cps-backend | POST | `/api/v1/order/workflow/update` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:325` |
| tvs-cps-backend | POST | `/system/api/v1/erp-invoice/insert` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:116` |
| tvs-cps-backend | POST | `/system/api/v1/order/analytics` | AnalyticsRequestDto | Unknown | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/strategy/OrderAnalyticsStrategy.java:168` |
| tvs-cps-backend | POST | `/system/api/v1/order/erp-sale-order-no/list` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InternalServiceBFFController.java:85` |
| tvs-cps-backend | POST | `/system/api/v1/order/erp-sync-status` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/InternalBffService.java:43` |
| Unknown | POST | `/{}` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:102` |
| tvs-cps-backend | POST | `/api/v1/training/create` | map<string,object> | map<string,object> | base URL from config:bff.training-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:48` |
| tvs-cps-backend | POST | `/api/v1/training/read` | map<string,object> | map<string,object> | base URL from config:bff.training-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:96` |
| tvs-cps-backend | POST | `/api/v1/training/search` | map<string,object> | map<string,object> | base URL from config:bff.training-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/TrainingBFFController.java:63` |
| tvs-cps-backend | POST | `/api/v1/workflow/action` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/WorkflowBffService.java:39` |
| tvs-cps-backend | POST | `/api/v1/workflow/init` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:51` |
| tvs-cps-backend | POST | `/api/v1/workflow/template/create` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:141` |
| tvs-cps-backend | POST | `/api/v1/workflow/template/process-activations` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:199` |
| tvs-cps-backend | POST | `/api/v1/workflow/template/update` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:157` |
| Unknown | POST | `/system{}` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/WorkflowAssignmentClient.java:65` |
| Unknown | POST | `/{}` | map<string,object> | map<string,object> | base URL from config:bff.workflow-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/AnnouncementBFFController.java:102` |
| tvs-cps-backend | POST | `/api/v1/grn/complete` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/GrnBFFService.java:44` |
| tvs-cps-backend | POST | `/cps/api/v1/billing/create` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/InvoiceClient.java:39` |
| tvs-cps-backend | POST | `/cps/api/v1/billing/invoices/search` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/SmartSearchBFFService.java:2156` |
| tvs-cps-backend | POST | `/cps/api/v1/billing/post-invoice` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/InvoiceClient.java:75` |
| tvs-cps-backend | POST | `/cps/api/v1/billing/report/invoice-list` | ReportRequest | Unknown | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/reports/strategies/PartInvoiceStrategy.java:53` |
| tvs-cps-backend | POST | `/cps/api/v1/customer/create` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BookingBFFService.java:1077` |
| tvs-cps-backend | POST | `/cps/api/v1/customer/search` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentExcelProcessorService.java:314` |
| tvs-cps-backend | POST | `/cps/api/v1/customer/update` | map<string,object> | map<string,object> | base URL from config:cps-backend.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/BookingBFFService.java:1201` |
| Unknown | POST | `/` | string | VehicleDetailsResponseDto[] | base URL from config:erp.data-lake.api-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/lead-service/api/v2/lead` | EnquiryRequestDto | Unknown | base URL from config:lead.api.url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:123` |
| Unknown | POST | `/lead-service/api/v2/lead/bulk-assign` | BulkAssignLeadRequestDto | Unknown | base URL from config:lead.api.url | Unknown | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadServiceClient.java:51` |
| Unknown | POST | `/lead-service/api/v2/lead/update` | UpdateLeadRequestDto | Unknown | base URL from config:lead.api.url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:669` |
| Unknown | POST | `/lead-service/api/v2/leads/all` | LeadFilterRequestDto, map<string,object> | string | base URL from config:lead.api.url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:480` |
| Unknown | POST | `/lead-service/api/v2/leads/getdetails` | EnquiryFilter | Unknown | base URL from config:lead.api.url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/LeadService.java:802` |
| Unknown | POST | `/lead-service/api/v2{}` | LeadFilterRequestDto | Unknown | base URL from config:lead.api.url | Unknown | webclient `bff-service/src/main/java/com/tvsm/bff/client/LeadServiceClient.java:51` |
| Unknown | POST | `/` | string | string | base URL from config:mdp.dealer.api.url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| notification-service | POST | `/email` | map<string,object> | string | base URL from config:notification.service.url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java:176` |
| notification-service | POST | `/sms` | map<string,object> | string | base URL from config:notification.service.url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java:145` |
| external:onetrust | POST | `/` | string | string | base URL from config:one-trust.consent.url | hard | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | string | string | base URL from config:one-trust.token-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| tvsm-otp-service | POST | `/generate` | OtpRequestDTO | string | base URL from config:otp.service.url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java:97` |
| tvsm-otp-service | POST | `/verify` | ValidateOtpRequestDTO | string | base URL from config:otp.service.url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/client/OptAndNotificationClient.java:334` |
| booking-crud-services | PUT | `/booking-service/v2/bookings` | BookingActionRequest | Unknown | base URL from config:bff.booking-service.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/BookingServiceClient.java:50` |
| booking-crud-services | PUT | `/booking-service/v2/bookings/cancel` | BookingCancellationRequestDto | Unknown | base URL from config:bff.booking-service.base-url | hard | webclient `bff-service/src/main/java/com/tvsm/bff/client/BookingServiceClient.java:50` |
| tvs-cps-backend | PUT | `/api/v1/claims/update` | map<string,object> | map<string,object> | base URL from config:bff.claim-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/ClaimBFFController.java:242` |
| tvs-cps-inventory | PUT | `/api/v1/vehicle/submit-inspection` | map<string,object> | map<string,object> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/inspection/VehicleInspectionServiceImpl.java:126` |
| tvs-cps-job-card-service | PUT | `/api/v1/jobcards/update` | map<string,object> | map<string,object>, string | base URL from config:bff.jobcard-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/service/JobCardInvoiceService.java:142` |
| tvs-cps-backend | PUT | `/api/v1/order/update` | map<string,object> | map<string,object> | base URL from config:bff.order-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/OrderBFFController.java:103` |
| Unknown | PUT | `/{}` | Unknown | map<string,object> | base URL from config:bff.workflow-service.base-url | Unknown | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/WorkflowBFFController.java:187` |
| Unknown | POST | `/` | string | string | base URL from config:claim.sap.api.url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | string | string | base URL from config:claim.sap.data-lake.api-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | map<string,string> | string | base URL from config:claim.sap.oauth.token.url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | WorkflowActionRequestDTO, WorkflowInitRequestDto | string | base URL from config:workflow.service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | string | string | base URL from config:erp.data-lake.api-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | EmailGatewayRequestDto | object | base URL from config:notification.gateway.email.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | FcmPushGatewayRequestDto | object | base URL from config:notification.gateway.push.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | SmsGatewayRequestDto | object | base URL from config:notification.gateway.sms.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| tvs-cps-backend | GET | `/cps/api/v1/inventory/accumulated-stock/{}` | Unknown | object | base URL from config:bff.order-service.base-url | hard | resttemplate `order-service/src/main/java/com/tvsm/order/service/OrderService.java:1665` |
| Unknown | POST | `/` | InventoryReceiveRequestDto[] | string | base URL from config:bff.inventory-service.base-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| tvs-cps-inventory | POST | `/system/api/v1/inventory/analytics/list` | map<string,object> | APIResponse<map<string,ProductCatalogResponseDto[]>> | base URL from config:bff.inventory-service.base-url | hard | resttemplate `bff-service/src/main/java/com/tvsm/bff/controller/InventoryAnalyticsBFFController.java:55` |
| Unknown | POST | `/` | map<string,object> | string | base URL from config:erp.api.sale-order-change-url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | map<string,object> | string | base URL from config:erp.api.url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| Unknown | POST | `/` | map<string,string> | string | base URL from config:erp.oauth.token.url | Unknown | resttemplate `bff-service/src/test/java/com/tvsm/bff/util/ApiPassthroughUtilTest.java:1347` |
| tvs-cps-backend | POST | `/cps/api/v1/workflow/init` | WorkflowInitRequestDto | string | base URL from config:workflow.service.base-url | hard | resttemplate `order-service/src/main/java/com/tvsm/order/utils/WorkflowIntegrationUtil.java:72` |

## Schemas

`tvs-cps-backend` schemas referenced by its endpoints and outbound calls (249).

### APIResponse<AnnouncementResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AnnouncementResponseDto[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AnnouncementSearchRequestDto

Defined in: `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementSearchRequestDto.java:14`

Fields: `page` (integer), `count` (integer), `criticality` (enum[LOW,MEDIUM,HIGH][]), `validFrom` (datetime), `validTo` (datetime), `self` (boolean)

### APIResponse<Page<AnnouncementResponseDto>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AnnouncementRequestDto

Defined in: `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementRequestDto.java:16`

Fields: `announcementId` (uuid), `title` (string), `description` (string), `validFrom` (datetime), `validTo` (datetime), `templateType` (string), `criticality` (string), `userAction` (ActionButton[]), `displayOnHome` (boolean), `targetAudience` (map<enum[ADD,REMOVE],AnnouncementTargetAudienceDto[]>), `externalLinks` (string[])

### APIResponse<string>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AnnouncementReadLogRequestDto

Defined in: `announcement-service/src/main/java/com/tvsm/announcement/dto/AnnouncementReadLogRequestDto.java:9`

Fields: `announcementId` (uuid), `userId` (string), `auditUserAction` (string), `clickedAt` (datetime)

### APIResponse<LogReadResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<MediaResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<BulkUploadErrorDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AppointmentMasterDataResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AppointmentDetailResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AnalyticsRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/AnalyticsRequestDTO.java:9`

Fields: `appointmentIndicatorKeys` (enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][]), `jobCardIndicatorKeys` (enum[OVERDUE_REMINDERS,NO_SHOW_APPOINTMENTS,PENDING_JOB_CARDS_GT_24_HRS,APPOINTMENTS_VALUE,APPOINTMENTS_CONVERSION,JOB_CARDS_VALUE,JOB_CARDS_CONVERSION,APPOINTMENTS_CLOSED,APPOINTMENTS_CANCELLED,APPOINTMENTS_BOOKED,APPOINTMENTS_RESCHEDULED,JOB_CARDS_PDI,JOB_CARDS_MILEAGE_SERVICE,JOB_CARDS_ANNUAL_SERVICE,JOB_CARDS_ACCIDENT_REPAIR,JOB_CARDS_OPEN_TIME,ALL_INDICATORS][]), `dealerId` (string)

### APIResponse<AnalyticsResponseDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### BulkUploadRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/BulkUploadRequestDTO.java:11`

Fields: `parsedData` (ParsedAppointmentData[]), `bulkUploadDTO` (AppointmentBulkUploadDTO)

### APIResponse<map<string,object>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### SearchRequestDTO

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PageResponseDTO<AppointmentBulkUploadDTO>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AppointmentCountResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AppointmentCreateRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentCreateRequestDTO.java:21`

Fields: `channel` (enum[CPS,WEBSITE,SALES_FORCE,NORTON_CONNECT_APP], required), `entityType` (string, required), `entitySubType` (string, required), `appointmentDateTime` (datetime, required), `jobType` (string, required), `serviceType` (string, required), `followUpDateTime` (datetime, required), `remark` (string), `reason` (string), `cceId` (string), `executive` (string), `customerName` (string, required), `context` (AppointmentContextDTO[], required), `customerVehicleDetails` (map<string,CustomerVehicleDTO>), `status` (enum[AWAITING_ACTION,BOOKED,RESCHEDULED,CANCELLED,CLOSED,CONFIRMED]), `lead_id` (string), `tenantId` (string), `channelPartnerId` (string), `vin` (string), `dealerName` (string)

### APIResponse<AppointmentResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AppointmentDashboardResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### StatusFilterRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/StatusFilterRequestDTO.java:21`

Fields: `filters` (FilterEntry[], required)

### APIResponse<AppointmentDetailResponseDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AppointmentsDownloadDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AppointmentCreateEventDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentCreateEventDTO.java:7`

Fields: `payload` (AppointmentCreateEventPayloadDTO)

### map<string,object>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PageResponseDTO<AppointmentResponseDTO>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AppointmentUpdateRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentUpdateRequestDTO.java:13`

Fields: `appointmentId` (string), `status` (string), `appointmentDateTime` (datetime), `jobType` (string), `serviceType` (string), `followUpDateTime` (datetime), `remark` (string), `reason` (string), `cceId` (string), `executive` (string), `customerName` (string), `followUpOperations` (FollowUpOperationsRequestDTO), `channelPartnerId` (string), `tenantId` (string), `userId` (string)

### AppointmentSystemSearchRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/AppointmentSystemSearchRequestDTO.java:14`

Fields: `tenantId` (string, required), `dealerId` (string, required), `page` (integer), `size` (integer), `searchText` (string), `ids` (string[]), `and` (Filter[]), `or` (Filter[]), `sort` (SortOrder[])

### APIResponse<AppointmentAutoCloseResponseDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<TenantConfigResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<object>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AppointmentDetailsResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/AppointmentDetailsResponseDTO.java:11`

Fields: `status` (string), `statusCode` (string), `message` (string), `data` (DataDTO)

### APIResponse<BookingSearchResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<AssemblyCategoryDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<CatalogSummaryDto[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PartDetailsDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<MerchandiseCategoryDto[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<string[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<map<string,object>[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<TVSChannelPartner[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<GRNDetailsClaimBFFResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### object

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<any>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### DashboardListResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/DashboardListResponseDTO.java:12`

Fields: `overview` (DashboardEntryDTO[]), `reports` (DashboardEntryDTO[])

### binary

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<EnquiryBulkUploadErrorDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<EnquiryDetailsResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<EnquiryMasterData>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<VehicleDto[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<VehicleVariantDto[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<JCDetailsWithMappingsBFFResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### UserPermissionsResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/UserPermissionsResponseDTO.java:10`

Fields: `permissions` (PermissionDTO[])

### UserDetailInfoResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/UserDetailInfoResponseDTO.java:11`

Fields: `sub` (string), `firstName` (string), `lastName` (string), `userId` (string), `dealerId` (string), `userType` (string), `country` (string), `uid` (string), `employeeId` (string), `primaryPhoneNumber` (string), `dealerName` (string), `email` (string), `profilePicture` (string), `timezone` (string), `currencyCode` (string), `locale` (string), `tenantId` (string), `permissions` (PermissionDTO[]), `roles` (string[]), `reservation` (ReservationConfigDTO)

### Role

Defined in: Unknown

Fields: Unknown (not resolved from code)

### TenantHandlerPatchRequest

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/TenantHandlerPatchRequest.java:11`

Fields: `currencyCode` (string), `configuration` (map<string,object>)

### TenantConfigRequest[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<TenantConfigResponse[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### ReportRequest

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/reports/ReportRequest.java:8`

Fields: `dealerId` (string), `reportType` (string), `startDate` (string), `endDate` (string), `page` (integer), `size` (integer), `tenant` (string), `locale` (string), `timeZone` (string)

### StreamingResponseBody

Defined in: Unknown

Fields: Unknown (not resolved from code)

### BillingBFFCreateRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/BillingBFFCreateRequestDto.java:14`

Fields: `entityId` (uuid), `entityType` (string), `invoiceType` (string), `currencyCode` (string), `invoiceId` (string), `invoiceLevelDiscountAmount` (number), `invoiceLevelDiscountContext` (string), `invoiceLevelDiscountType` (string), `bookingId` (string), `dealerSalesExecutiveId` (string), `paymentTerms` (string), `totalLineitemlevelDiscountAmount` (number), `invoicelevelDiscountPercentage` (number), `totalInvoiceTaxAmount` (number), `totalInvoiceAmount` (number), `additionalNotes` (map<string,object>), `lineItems` (LineItemsDto)

### PostInvoiceRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/PostInvoiceRequestDto.java:8`

Fields: `invoiceId` (string), `invoiceNumber` (string), `invoiceType` (string), `payment` (PaymentDetail)

### APIResponse<PostInvoiceResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PaginatedResponse<object>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### BookingCancellationRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingCancellationRequestDto.java:11`

Fields: `uuid` (string), `isATPConfigured` (boolean), `checkSum` (string), `version` (integer), `cancellationSource` (string), `cancellationReason` (string), `cancellationSubReason` (string), `cancellationFee` (number), `cancellationFeeRemarks` (string), `refundAmount` (number), `customerRemarks` (string), `CRMId` (integer), `dateOfCancellation` (string), `refundDetails` (map<string,object>), `vehicleId` (integer), `productIds` (integer[])

### BookingBFFRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingBFFRequestDto.java:11`

Fields: `booking` (Booking)

### APIResponse<BookingResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### BookingSearchRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingSearchRequestDto.java:13`

Fields: `retrievalType` (string), `pageNumber` (integer), `pageSize` (integer), `bookingRetrieval` (BookingRetrievalRequest)

### APIResponse<BookingStatusCountDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### BookingUpdateDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingUpdateDto.java:11`

Fields: `bookingUuid` (string), `checksum` (string), `version` (integer), `customerId` (string), `addressId` (string), `bookingSource` (string), `dse` (string), `location` (BookingLocationDto), `vehicle` (Vehicle), `expectedDeliveryDate` (string), `payment` (Payment), `products` (ProductItem[])

### EnquiryFilter

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryFilter.java:12`

Fields: `mobileNumber` (string), `customerName` (string), `isActive` (boolean), `dealerId` (string), `dealerIds` (string[]), `sourceCategory` (integer[]), `enquiryType` (string[]), `source` (string[]), `startTime` (string), `endTime` (string), `dseId` (string), `dseIds` (string[]), `leadCategory` (string), `emailId` (string), `testRideStatus` (string), `sortBy` (string), `followUpStatus` (string), `status` (string), `modelId` (string), `partId` (string), `leadId` (string), `nextFollowUpStartDate` (string), `nextFollowUpEndDate` (string), `testRideScheduledStartDate` (string), `testRideScheduledEndDate` (string), `page` (integer), `size` (integer), `calendarType` (enum[TESTRIDE,FOLLOWUP])

### APIResponse<CalendarResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### CatalogRequest

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/CatalogRequest.java:11`

Fields: `currentPage` (integer), `pageLimit` (integer), `productType` (string), `filter` (Filter)

### CreateCustomerWithVehicleRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/CreateCustomerWithVehicleRequestDto.java:18`

Fields: `vin` (string, required), `customer` (map<string,object>, required)

### CreateAnalyticsDashboardRequestDTO[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### DashboardEntryDTO[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### DocumentUploadResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/DocumentUploadResponseDTO.java:8`

Fields: `url` (string), `originalFilename` (string), `size` (integer), `contentType` (string)

### BulkAssignRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/BulkAssignRequestDto.java:12`

Fields: `enquiryIds` (string[], required), `dseId` (string, required), `dseName` (string, required)

### APIResponse<PageResponseDTO<EnquiryBulkUploadDTO>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### EnquiryBFFRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryBFFRequestDto.java:12`

Fields: `customerName` (string), `mobileNumber` (string), `email` (string), `interestedBrand` (InterestedBrandBFFDto[]), `modeOfCommunication` (map<string,object>), `enquiryClassification` (string), `additionalNotes` (string), `additionalDetails` (EnquiryAdditionalInfo), `assignedTo` (string), `sourceOfAwareness` (string), `followUp` (EnquiryFollowUpDto), `ageGroup` (string), `gender` (string), `postalCode` (string), `addressLine1` (string), `addressLine2` (string), `peferredPurchaseMode` (string), `interestedInExchange` (string), `existingVehicle` (ExistingVehicle), `preferredLanguage` (string), `customerInterest` (string), `hasCustomerVisited` (boolean), `enquiryTag` (EnquiryTag[])

### APIResponse<EnquiryBFFResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<EnquiryFilterResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<EnquiryStatusCountDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### UpdateEnquiryRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/UpdateEnquiryRequestDto.java:12`

Fields: `enquiryId` (string), `enquiryClassification` (string), `interestedBrand` (InterestedBrandBFFDto[]), `testRides` (EnquiryTestRideDto[]), `followUps` (FollowUps), `status` (string), `pincode` (string), `addressLine1` (string), `addressLine2` (string), `preferredLanguage` (string), `preferredPurchaseMode` (string), `interestedInExchange` (string), `hasCustomerVisited` (boolean), `customerInterest` (string), `additionalDetails` (EnquiryAdditionalInfo), `city` (string), `existingVehicle` (ExistingVehicle)

### VehicleAllocateRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/VehicleAllocateRequestDto.java:12`

Fields: `bookingUuid` (string), `checkSum` (string), `version` (integer), `customerId` (string), `frameNumber` (string), `engineNumber` (string), `vehicleId` (string), `productCatalogId` (string), `source` (string)

### VehicleDeallocationRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/VehicleDeallocationRequestDto.java:10`

Fields: `bookingUuid` (string), `checkSum` (string), `version` (integer), `customerId` (string), `frameNumber` (string), `engineNumber` (string), `vehicleId` (string), `productCatalogId` (string), `source` (string), `manufactureYear` (string), `manufactureMonth` (string)

### GetAddVehicleRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/GetAddVehicleRequestDto.java:8`

Fields: `vin` (string), `type` (string)

### APIResponse<VehicleResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### map<string,object>[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### string

Defined in: Unknown

Fields: Unknown (not resolved from code)

### JobcardCreateInvoiceDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/JobcardCreateInvoiceDTO.java:9`

Fields: `jobCardId` (string), `vin` (string)

### WarrantyCheckRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/WarrantyCheckRequestDTO.java:10`

Fields: `vehicleSaleDateStr` (string, required), `vehicleWarrantyPeriod` (integer), `vehicleWarrantyEndDate` (string), `partWarrantyPeriod` (integer), `warrantyUnit` (string, required), `customerVehicleId` (string, required), `partCatalogSkuId` (string, required)

### AssignDefaultUsersRequestDTO

Defined in: `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/AssignDefaultUsersRequestDTO.java:16`

Fields: `data` (DataPayload, required)

### APIResponse<AssignDefaultUsersResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### LeadAllocationListRequestDTO

Defined in: `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/LeadAllocationListRequestDTO.java:10`

Fields: `type` (string)

### APIResponse<LeadAllocationDataDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### UpdateAllocationRequestDTO

Defined in: `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/UpdateAllocationRequestDTO.java:22`

Fields: `data` (ContentItemDTO[], required)

### APIResponse<UpdateAllocationResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<LeadServiceDashboardResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### LeadDetailsRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/LeadDetailsRequestDto.java:10`

Fields: `leadId` (string, required)

### APIResponse<ServiceReminderDetailResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<LeadServiceListResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### NotificationCategoryRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationCategoryRequestDto.java:11`

Fields: `userId` (string), `dealerId` (string), `tenantId` (string)

### NotificationCategoryResponseDto[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### NotificationDeviceDeregisterRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationDeviceDeregisterRequestDto.java:12`

Fields: `deviceToken` (string, required), `userId` (string), `dealerId` (string), `tenantId` (string)

### NotificationDeviceResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationDeviceResponseDto.java:12`

Fields: `notificationDeviceId` (string), `tenantId` (string), `channelEntityType` (string), `channelEntityId` (string), `currentUserId` (string), `deviceToken` (string), `platform` (string), `isActive` (boolean), `lastActiveAt` (datetime), `createdAt` (datetime), `updatedAt` (datetime)

### NotificationDeviceRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationDeviceRequestDto.java:12`

Fields: `deviceToken` (string, required), `platform` (string), `userId` (string), `dealerId` (string), `tenantId` (string)

### NotificationEventRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationEventRequestDto.java:33`

Fields: `eventId` (string, required), `tenantId` (string, required), `channelEntityType` (string), `channelEntityId` (string), `recipients` (NotificationRecipientDto[]), `categoryCode` (string, required), `subCategoryCode` (string, required), `referenceId` (string), `payload` (object), `params` (map<string,object>)

### NotificationTriggerRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationTriggerRequestDto.java:13`

Fields: `eventType` (string, required), `referenceId` (string, required), `payload` (map<string,object>)

### NotificationMessageReadResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageReadResponseDto.java:10`

Fields: `messageId` (string), `markedRead` (boolean), `updatedCount` (integer)

### NotificationMessageBulkReadRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationMessageBulkReadRequestDto.java:12`

Fields: `messageIds` (string[], required)

### NotificationMessageSearchRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationMessageSearchRequestDto.java:9`

Fields: `currentUserId` (string), `dealerId` (string), `tenantId` (string)

### NotificationMessageResponseDto[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### NotificationPreferenceRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationPreferenceRequestDto.java:9`

Fields: `userId` (string), `tenantId` (string), `dealerId` (string)

### NotificationCategoryPreferenceResponseDto[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### NotificationPreferenceUpdateRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationPreferenceUpdateRequestDto.java:15`

Fields: `preferences` (PreferenceItemDto[], required)

### NotificationPreferenceUpdateResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationPreferenceUpdateResponseDto.java:9`

Fields: `userId` (string), `updatedCount` (integer), `updated` (boolean)

### ChannelsDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/OtpRequestDTO.java:20`

Fields: `channel` (string), `entity` (string)

### OtpRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/OtpRequestDTO.java:10`

Fields: `channels` (ChannelsDTO[])

### ValidateOtpRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/ValidateOtpRequestDTO.java:12`

Fields: `channel` (string), `entity` (string), `otp` (string)

### SmartSearchAdditionalDetailsRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchAdditionalDetailsRequestDTO.java:10`

Fields: `customerId` (string), `vehicleId` (string), `mobileNumber` (string), `retrieve` (string)

### SmartSearchAdditionalDetailsResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchAdditionalDetailsResponseDTO.java:13`

Fields: `preSales` (EventsDTO[]), `ownershipBilling` (object[]), `afterSales` (AdditionalDetailItemDTO[])

### SmartSearchDetailsRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchDetailsRequestDTO.java:10`

Fields: `customerId` (string), `vehicleId` (string), `vin` (string), `mobileNumber` (string)

### SmartSearchDetailsResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchDetailsResponseDTO.java:14`

Fields: `customerLinked` (boolean), `profile` (CustomerProfileDTO), `vehicles` (SmartSearchVehicleDTO[]), `activeEvents` (EventsDTO[])

### SmartSearchRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchRequestDTO.java:11`

Fields: `searchType` (string), `searchValue` (string), `page` (integer), `size` (integer)

### SmartSearchResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/smartsearch/SmartSearchResponseDTO.java:12`

Fields: `searchType` (string), `searchValue` (string), `totalCount` (integer), `results` (T[])

### VehicleDeliveryRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/VehicleDeliveryRequestDto.java:10`

Fields: `vin` (string), `deliveryDate` (string), `additionalDocuments` (map<string,object>), `registrationNumber` (string), `bookingId` (string), `bookingChecksum` (string), `bookingVersion` (integer), `customerId` (string)

### APIResponse<VehicleDeliveryResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### InspectionSubmitRequest

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/inspection/InspectionSubmitRequest.java:10`

Fields: `submissionId` (string, required), `type` (string, required), `vin` (string, required), `formId` (string, required), `technicianName` (string, required), `customerName` (string), `inspectionDate` (string, required), `mileage` (integer), `keyNumber` (string), `status` (string, required), `submissionDate` (string, required), `score` (integer)

### APIResponse<InspectionDetailResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### WarrantyCreateRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/WarrantyCreateRequestDto.java:10`

Fields: `customerName` (string), `mobileNumber` (string), `alternateMobileNumber` (string), `email` (string), `gender` (string), `postalCode` (string), `city` (string), `state` (string), `address` (string), `area` (string), `region` (string), `countryCode` (string), `vin` (string), `registrationNumber` (string), `engineNumber` (string), `keyNumber` (string), `bookingId` (string), `model` (string), `vehicleId` (string), `vehicleReceiveDate` (string), `saleDate` (string), `vehicleDeliveryDate` (string), `salesExecutiveAssigned` (string), `saleInvoiceNumber` (string), `customerId` (string), `customerVerificationStatus` (integer), `additionalDocuments` (AdditionalDocumentDto), `includeAdditionalDocument` (boolean)

### APIResponse<WarrantyCreateResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### WarrantySearchRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/WarrantySearchRequestDto.java:7`

Fields: `retrievalType` (string), `pageNumber` (integer), `pageSize` (integer), `phone` (string)

### APIResponse<WarrantyListResponse[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### AnalyticsDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/AnalyticsDto.java:9`

Fields: `dealerId` (string), `indicatorKey` (string), `tenantId` (string)

### APIResponse<ClaimMasterDataResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<CatalogTimelineResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<ClaimResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### ClaimCreateRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/ClaimCreateRequestDTO.java:11`

Fields: `channel` (string), `claimData` (ClaimDataDTO[])

### APIResponse<ClaimSummaryResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### ClaimBulkUploadRequestDTO

Defined in: `claim-service/src/main/java/com/tvsm/claim/dto/ClaimBulkUploadRequestDTO.java:11`

Fields: `url` (string), `name` (string), `size` (integer), `type` (string), `parsedClaimOperations` (ParsedClaimOperation[])

### APIResponse<PageResponseDTO<BulkUploadDTO>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### CloseClaimRequestDTO

Defined in: `claim-service/src/main/java/com/tvsm/claim/dto/CloseClaimRequestDTO.java:9`

Fields: `claimId` (string), `comment` (string)

### APIResponse<ClaimIdResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<ClaimDashboardResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<ClaimResponseDTO[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<ClaimsDownloadDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PageResponseDTO<ClaimResponseDTO>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### ClaimUpdateRequestDTO

Defined in: `claim-service/src/main/java/com/tvsm/claim/dto/ClaimUpdateRequestDTO.java:13`

Fields: `claimId` (string, required), `status` (enum[SUBMITTED,APPROVED,REJECTED,UNDER_REVIEW,PAID]), `catalogOperations` (CatalogOperationsRequestDTO, required)

### CollateralDto

Defined in: `collateral-service/src/main/java/com/tvsm/collateral/dto/CollateralDto.java:12`

Fields: `collateralId` (uuid), `title` (string), `documentType` (string), `tags` (string[]), `validFrom` (datetime), `media` (CollateralMediaDto), `createdAt` (datetime)

### APIResponse<CollateralDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### CollateralSearchRequestDto

Defined in: `collateral-service/src/main/java/com/tvsm/collateral/dto/CollateralSearchRequestDto.java:6`

Fields: `and` (Filter[]), `or` (Filter[]), `page` (integer), `limit` (integer), `sort` (Sort[])

### APIResponse<PaginatedResponse<CollateralDto>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### RoundRobinTrackerGetRequestDTO

Defined in: `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/RoundRobinTrackerGetRequestDTO.java:13`

Fields: `channelPartnerId` (string, required), `tenantId` (string, required), `allocationType` (string, required), `entityId` (string, required)

### APIResponse<RoundRobinTrackerResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### RoundRobinTrackerUpsertRequestDTO

Defined in: `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/RoundRobinTrackerUpsertRequestDTO.java:17`

Fields: `channelPartnerId` (string, required), `tenantId` (string, required), `allocationType` (string, required), `entityId` (string, required), `lastAssignedUserId` (string, required), `modifiedBy` (string)

### LeadAllocationListWrapperDTO

Defined in: `lead-allocation/src/main/java/com/tvsm/leadallocation/dto/LeadAllocationListWrapperDTO.java:8`

Fields: `dealerId` (string, required), `tenantId` (string, required), `leadAllocationListRequest` (LeadAllocationListRequestDTO, required)

### NotificationActionConfigResponseDto[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### NotificationActionConfigResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationActionConfigResponseDto.java:16`

Fields: `notificationActionConfigId` (string), `eventType` (string), `actionType` (string), `targetSubcategoryCode` (string), `tenantId` (string), `channelEntityType` (string), `channelEntityId` (string), `personas` (PersonaConfig[]), `expectedData` (ExpectedDataConfig[]), `isActive` (boolean), `createdAt` (datetime), `updatedAt` (datetime)

### NotificationCategoryResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationCategoryResponseDto.java:14`

Fields: `notificationCategoryId` (string), `tenantId` (string), `channelEntityType` (string), `channelEntityId` (string), `code` (string), `name` (string), `description` (string), `isActive` (boolean), `createdAt` (datetime), `updatedAt` (datetime), `subCategories` (NotificationSubCategoryResponseDto[])

### NotificationEventDto<any>

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/model/NotificationEventDto.java:26`

Fields: `recipients` (NotificationRecipientDto[]), `tenantId` (string), `channelEntityType` (string), `channelEntityId` (string), `categoryCode` (string), `subCategoryCode` (string), `eventId` (string), `referenceId` (string), `payload` (any), `params` (map<string,object>)

### PushNotificationRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/PushNotificationRequestDto.java:15`

Fields: `userId` (string, required), `subCategoryCode` (string, required), `eventId` (string, required), `referenceId` (string), `title` (string, required), `message` (string, required), `deepUrl` (DeepUrlDto[])

### NotificationMessageResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationMessageResponseDto.java:14`

Fields: `notificationMessageId` (string), `tenantId` (string), `channelEntityType` (string), `channelEntityId` (string), `eventId` (string), `currentUserId` (string), `notificationCategoryId` (string), `categoryCode` (string), `categoryName` (string), `notificationSubCategoryId` (string), `subCategoryCode` (string), `subCategoryName` (string), `notificationTypeId` (string), `typeCode` (string), `typeName` (string), `providerMessageId` (string), `referenceId` (string), `title` (string), `message` (string), `deepUrl` (DeepUrlDto[]), `status` (string), `retryCount` (integer), `providerResponse` (string), `errorMessage` (string), `sentAt` (datetime), `deliveredAt` (datetime), `readAt` (datetime), `readStatus` (boolean), `createdAt` (datetime), `updatedAt` (datetime)

### NotificationSeedRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/NotificationSeedRequestDto.java:15`

Fields: `update` (boolean), `updateData` (NotificationSeedData), `dealers` (DealerDetail[], required)

### NotificationSeedResponseDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/response/NotificationSeedResponseDto.java:12`

Fields: `update` (boolean), `requested` (integer), `succeeded` (integer), `failed` (integer), `results` (DealerResult[])

### QualityReportCreateRequestDTO

Defined in: `npqr-service/src/main/java/com/tvsm/npqr/dto/QualityReportCreateRequestDTO.java:11`

Fields: `productType` (string, required), `catalogSkuId` (string), `partNo` (string), `vehicleSAPNo` (string), `issueType` (string, required), `issueDescription` (string, required), `isStandardPart` (boolean, required), `catalogName` (string, required), `quantity` (integer), `uom` (string), `issueMode` (string), `faultType` (string), `defectCode` (string), `vin` (string), `mileageReading` (integer), `fileMapping` (FileMappingCreateRequestDTO[], required)

### APIResponse<QualityReportResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<NpqrListResponseDTO>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<CartDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<CartResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<GrnDetailResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<InvoiceDeliveryViewResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<OrderDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<map<string,string>[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<map<string,integer>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PartDetailsResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<OrderStatusCountDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### CartRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/CartRequest.java:6`

Fields: `orderCategoryType` (string), `cartName` (string), `cartLines` (CartLineRequest[])

### CartReorderRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/CartReorderRequest.java:8`

Fields: `cartId` (string)

### SearchRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/common/request/SearchRequestDto.java:8`

Fields: `and` (Filter[]), `or` (Filter[]), `page` (integer), `limit` (integer), `sort` (Sort[])

### APIResponse<PaginatedResponse<CartDto>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### CartUpdateRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/CartUpdateRequest.java:5`

Fields: `cartId` (string), `cartName` (string), `isDeleted` (boolean), `entityId` (string), `entityType` (string), `orderCategoryType` (string), `orderLineOperations` (CartLineOperations)

### APIResponse<CartUpdateResponse>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### GrnCompleteRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/GrnCompleteRequestDto.java:7`

Fields: `grnId` (uuid), `invoiceId` (uuid)

### APIResponse<GrnCompleteResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### GrnDeliveryDetailsRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/GrnDeliveryDetailsRequestDto.java:9`

Fields: `grnId` (uuid), `deliveryStatus` (string), `receivedAt` (datetime), `transporterName` (string), `deliveryVehicleNumber` (string), `deliveryProofs` (DeliveryProofDto[])

### APIResponse<GrnDeliveryDetailResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### GrnCreateRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/GrnCreateRequestDto.java:7`

Fields: `invoiceId` (uuid)

### APIResponse<PaginatedResponse<GRNSearchResponseDTO>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### GrnUpdateRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/GrnUpdateRequestDto.java:8`

Fields: `invoiceId` (uuid), `grnId` (uuid), `transitionState` (string), `grnDetails` (GrnDetailUpdateDto[])

### APIResponse<GrnUpdateSummaryResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### UpdateClaimInitiatedRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/UpdateClaimInitiatedRequestDto.java:9`

Fields: `grnId` (uuid), `invoiceId` (uuid), `claimInitiated` (boolean)

### InvoiceCreateRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/InvoiceCreateRequest.java:9`

Fields: `orderId` (uuid)

### APIResponse<Invoice>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PaginatedResponse<InvoiceListResponseDto>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### CancelOrderRequestDTO

Defined in: `order-service/src/main/java/com/tvsm/order/dto/CancelOrderRequestDTO.java:11`

Fields: `orderId` (string), `orderCategoryType` (string), `cancellationReason` (string), `cancellationComment` (string), `orderLines` (OrderLineRequest[])

### OrderRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/OrderRequestDto.java:12`

Fields: `orderCategoryType` (string), `orderLines` (OrderLineRequestDto[]), `orderId` (string), `orderLineOperations` (map<string,OrderLineRequestDto[]>)

### APIResponse<OrderResponseDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### OrderActionRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/OrderActionRequestDto.java:5`

Fields: `id` (string), `action` (string)

### PlaceOrderRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/PlaceOrderRequestDto.java:9`

Fields: `orderId` (string), `cartId` (string), `needOrderBy` (string), `shipTo` (string), `orderPriority` (string)

### SalesOrderNoRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/SalesOrderNoRequest.java:7`

Fields: `tenantIds` (string[])

### APIResponse<PaginatedResponse<OrderDto>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### uuid[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### SyncERPStatusRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/SyncERPStatusRequest.java:9`

Fields: `erpOrderUpdateDtos` (ERPOrderUpdateDto[])

### InsertInvoiceRequest

Defined in: `order-service/src/main/java/com/tvsm/order/dto/InsertInvoiceRequest.java:7`

Fields: `erpInvoices` (ERPInvoiceDto[])

### AnalyticsRequestDto

Defined in: `order-service/src/main/java/com/tvsm/order/dto/AnalyticsRequestDto.java:8`

Fields: `indicatorKey` (string), `dealerId` (string), `tenantId` (string)

### APIResponse<OrderOperationResults>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<TrainingDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### TrainingDto

Defined in: `training-service/src/main/java/com/tvsm/training/dto/TrainingDto.java:12`

Fields: `trainingId` (uuid), `type` (string), `title` (string), `description` (string), `validFrom` (datetime), `validTo` (datetime), `criticality` (string), `duration` (string), `readCount` (integer), `tags` (string[]), `media` (TrainingMediaDto[]), `externalLinks` (string[]), `userAction` (UserAction[])

### TrainingReadLogDto

Defined in: `training-service/src/main/java/com/tvsm/training/dto/TrainingReadLogDto.java:11`

Fields: `trainingReadLogId` (uuid), `trainingId` (uuid), `userId` (string), `readAt` (datetime)

### APIResponse<TrainingReadLogDto>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### TrainingSearchRequestDto

Defined in: `training-service/src/main/java/com/tvsm/training/dto/TrainingSearchRequestDto.java:6`

Fields: `and` (Filter[]), `or` (Filter[]), `page` (integer), `limit` (integer), `sort` (Sort[])

### APIResponse<PaginatedResponse<TrainingSearchResponse>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<map<string,string>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### WorkflowResponse

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowResponse.java:13`

Fields: `wfId` (uuid), `tenantId` (string), `entityOperationType` (string), `version` (string), `initContext` (object), `createdOn` (datetime), `initiatingChannelType` (string), `initiatingChannelId` (string), `entityId` (string), `initiatedBy` (string), `updatedBy` (string), `lastUpdatedOn` (datetime), `latestStatus` (string), `nextActorType` (string), `nextActorId` (string), `nextActorContext` (object), `history` (WorkflowHistoryResponse[])

### APIResponse<WorkflowResponse[]>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### WorkflowTemplateResponse

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateResponse.java:13`

Fields: `id` (uuid), `tenantId` (string), `entityOperationType` (string), `version` (string), `workflowMetadata` (string), `workflowRules` (string), `createdOn` (datetime), `updatedOn` (datetime), `status` (enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED]), `createdBy` (string), `addlInfo` (string), `activationDate` (datetime)

### WorkflowActionRequest

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowActionRequest.java:11`

Fields: `wfId` (uuid), `action` (string), `comments` (string), `actionContext` (object)

### AssignmentTriggerRequestDTO

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/assignment/AssignmentTriggerRequestDTO.java:16`

Fields: `genericServiceId` (string, required), `channelPartnerId` (string, required), `dealerName` (string), `tenantId` (string, required), `channel` (string), `entityType` (string, required), `entitySubType` (string), `eligibleUsers` (EligibleUserDTO[]), `lastAssignedUserId` (string)

### AssignmentTriggerResponseDTO

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/assignment/AssignmentTriggerResponseDTO.java:16`

Fields: `genericServiceId` (string), `strategy` (enum[FALLBACK,SINGLE_USER,ROUND_ROBIN]), `selectedUserId` (string), `executiveName` (string), `serviceUpdated` (boolean), `trackerUpdated` (boolean), `reason` (string)

### WorkflowInitRequest

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowInitRequest.java:9`

Fields: `entityOperationType` (string), `initiatingChannelType` (string), `initiatingChannelId` (string), `entityId` (string), `initContext` (object)

### WorkflowTemplateRequest

Defined in: `workflow-service/src/main/java/com/tvsm/workflow/dto/WorkflowTemplateRequest.java:13`

Fields: `id` (uuid), `entityOperationType` (string), `version` (string), `workflowMetadata` (string), `workflowRules` (string), `status` (enum[DRAFT,ACTIVE,DEPRECATED,DECOMMISSIONED]), `addlInfo` (string), `activationDate` (datetime)

### CustomerVehicleSearchRequestDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/CustomerVehicleSearchRequestDTO.java:11`

Fields: `page` (integer), `size` (integer), `and` (FilterCondition[])

### CustomerListResponseDTO

Defined in: `appointment-service/src/main/java/com/tvsm/appointment/dto/CustomerListResponseDTO.java:12`

Fields: `status` (string), `statusCode` (string), `message` (string), `data` (Data)

### map<string,string>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### VehicleSearchResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/VehicleSearchResponseDTO.java:12`

Fields: `_id` (string), `id` (integer), `name` (string), `market` (string), `isDefaultCatalog` (boolean), `nameSpace` (string), `industry` (string), `productType` (string), `categories` (CategoryDTO[]), `isArchived` (boolean), `createdDate` (datetime), `modifiedDate` (datetime)

### HttpHeaders

Defined in: Unknown

Fields: Unknown (not resolved from code)

### JCDetailsWithMappingsCoreResponseDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/JCDetailsWithMappingsCoreResponseDTO.java:10`

Fields: `status` (string), `statusCode` (string), `message` (string), `data` (DataDTO)

### BookingRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingRequestDto.java:18`

Fields: `type` (string), `booking` (Booking), `isATPConfigured` (boolean)

### OneViewRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/OneViewRequestDto.java:12`

Fields: `leadId` (string), `sources` (integer[]), `events` (integer[]), `sort_by` (string)

### UpdateInventoryDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/UpdateInventoryDTO.java:11`

Fields: `productCatalogId` (string, required), `quantity` (integer, required), `type` (string), `productCategoryType` (string)

### LeadAllocationListBFFWrapperDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/LeadAllocationListBFFWrapperDTO.java:6`

Fields: `dealerId` (string), `tenantId` (string), `leadAllocationListRequest` (LeadAllocationListRequestDTO)

### LeadCreateRequestDTO

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/LeadCreateRequestDTO.java:11`

Fields: `customer_name` (string), `dealer_id` (string), `mobile_number` (string), `email_id` (string), `enquiry_date` (string), `city` (string), `utm_source` (string), `utm_medium` (string), `utm_campaign` (string), `gclid` (string), `language_code` (string), `source_id` (integer), `area` (string), `brand_code` (integer), `model_id` (string), `part_id` (string), `customer_voice` (string), `branch_id` (string), `address_line1` (string), `utm_term` (string), `utm_content` (string), `parm1` (string), `parm2` (string), `parm3` (string), `parm4` (string), `parm5` (string), `customer_state` (string), `finance` (string), `finance_company` (string), `pincode` (string), `intent_for_purchase` (string), `device` (string), `lead_category` (string), `possiblebrandname` (string), `dealername` (string), `test_rides` (object[]), `interested_brand` (string), `follow_up` (string), `extra_attributes` (ExtraAttributeDTO[]), `finance_details` (object), `enquiry_tag` (object[]), `referral_customer_details` (object), `additional_details` (map<string,object>)

### APIResponse<PaginatedResponse<AccessoryPurchaseModel>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<PaginatedResponse<MerchandisePurchaseModel>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

### VehicleDetailsResponseDto[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### EnquiryRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/EnquiryRequestDto.java:12`

Fields: `customer_name` (string), `dealer_id` (string), `mobile_number` (string), `email_id` (string), `enquiry_date` (string), `city` (string), `utm_source` (string), `utm_medium` (string), `utm_campaign` (string), `gclid` (string), `language_code` (string), `source_id` (integer), `area` (string), `brand_code` (integer), `model_id` (string), `part_id` (string), `customer_voice` (string), `branch_id` (string), `address_line1` (string), `customer_state` (string), `finance` (string), `finance_company` (string), `pincode` (string), `intent_for_purchase` (string), `device` (string), `lead_category` (string), `possiblebrandname` (string), `dealername` (string), `test_rides` (TestRideDto), `interested_brand` (InterestedBrandDto[]), `additional_details` (AdditionalDetailsDto), `follow_up` (FollowUpDto), `extra_attributes` (object), `finance_details` (object), `referral_customer_details` (object), `status` (string), `enquiry_tag` (EnquiryTag[]), `existing_vehicle` (ExistingVehicle)

### BulkAssignLeadRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/BulkAssignLeadRequestDto.java:11`

Fields: `lead_ids` (string[]), `dse_id` (string), `dse_name` (string), `updated_by` (integer)

### UpdateLeadRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/UpdateLeadRequestDto.java:11`

Fields: `customer_name` (string), `dealer_id` (string), `email` (string), `update_date` (string), `city` (string), `language_code` (string), `updated_by` (integer), `area` (string), `branch_id` (integer), `address_line1` (string), `customer_state` (string), `finance` (string), `pincode` (string), `finance_company` (string), `intent_for_purchase` (string), `lead_id` (string), `updated_date` (string), `status` (string), `events` (integer[]), `test_rides` (TestRideDto[]), `additional_details` (AdditionalDetailsDto), `follow_up` (FollowUpDto), `enquiry_tag` (EnquiryTag[]), `interested_brand` (InterestedBrandDto[]), `existing_vehicle` (ExistingVehicle), `referral_customer_details` (object), `finance_details` (object), `lead_invoice` (object), `lead_extra_attributes` (object), `lead_category` (string), `customer_voice` (string), `parm2` (string), `parm3` (string), `parm4` (string), `parm5` (string)

### LeadFilterRequestDto

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/LeadFilterRequestDto.java:11`

Fields: `mobileNumber` (string), `CustomerName` (string), `DealerId` (string), `DealerIds` (string[]), `Status` (string), `IsActive` (boolean), `StartTime` (string), `EndTime` (string), `ModelId` (string), `PartId` (string), `SourceIds` (integer[]), `SortBy` (string), `DseId` (string), `CustomerType` (string), `LeadCategory` (string), `EmailId` (string), `FollowUpStatus` (string), `TestRideStatus` (string), `DseIds` (string[]), `L1Sources` (string[]), `EnquiryTypes` (string[]), `LeadIncludes` (string[]), `testRideScheduledStartDate` (string), `testRideScheduledEndDate` (string), `nextFollowUpStartDate` (string), `nextFollowUpEndDate` (string), `ExcludeServiceReminderLead` (boolean)

### BookingActionRequest

Defined in: `bff-service/src/main/java/com/tvsm/bff/dto/bookingService/BookingActionRequest.java:10`

Fields: `action` (string), `uuid` (string), `checkSum` (string), `version` (integer), `updateSource` (string), `bookingStatus` (string), `assignedDealerSalesExecutiveId` (string), `bookingUpdate` (map<string,object>), `isATPConfigured` (boolean), `CRMId` (string)

### WorkflowActionRequestDTO

Defined in: `claim-service/src/main/java/com/tvsm/claim/dto/WorkflowActionRequestDTO.java:11`

Fields: `wfId` (uuid), `action` (string), `comments` (string), `actionContext` (object)

### WorkflowInitRequestDto

Defined in: `claim-service/src/main/java/com/tvsm/claim/dto/WorkflowInitRequestDto.java:13`

Fields: `entityOperationType` (string), `initiatingChannelType` (string), `initiatingChannelId` (string), `entityId` (string), `initContext` (object)

### EmailGatewayRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/EmailGatewayRequestDto.java:13`

Fields: `priority` (string), `email` (EmailPayload)

### FcmPushGatewayRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/FcmPushGatewayRequestDto.java:12`

Fields: `priority` (string), `fcmPush` (FcmPushPayload)

### SmsGatewayRequestDto

Defined in: `data-access-service/src/main/java/com/tvsm/dataaccess/notification/request/SmsGatewayRequestDto.java:11`

Fields: `priority` (string), `sms` (SmsPayload)

### InventoryReceiveRequestDto[]

Defined in: Unknown

Fields: Unknown (not resolved from code)

### APIResponse<map<string,ProductCatalogResponseDto[]>>

Defined in: Unknown

Fields: Unknown (not resolved from code)

## Events Published

`tvs-cps-backend` publishes to 5 messaging entit(ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| dev.cp.appointment | kafka-topic | kafka | Unknown | T | `appointment-service/src/main/java/com/tvsm/appointment/service/AppointmentProducerService.java:29` | Unknown |
| dev.cp.service_lead | kafka-topic | kafka | Unknown | Unknown | `bff-service/src/main/java/com/tvsm/bff/producer/ServiceLeadEventProducer.java:44` | tvs-cps-backend |
| dev.cp.notification1 | kafka-topic | kafka | Unknown | Consumer<Throwable>, NotificationEventRequestDto, integer | `['notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:44', 'notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:58', 'notification-service/src/main/java/com/tvsm/notification/producer/NotificationEventProducer.java:71', 'notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:125', 'notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:140', 'notification-service/src/main/java/com/tvsm/notification/service/NotificationTriggerService.java:154']` | tvs-cps-backend |
| dev.cp.booking | kafka-topic | kafka | Unknown | Unknown | `order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java:54` | tvs-cps-backend |
| dev.cp.order | kafka-topic | kafka | Unknown | Unknown | `order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java:41` | tvs-cps-backend |

Name source per entity: dev.cp.appointment ← `config:azure.eventhub.appointment.hub-name`; dev.cp.service_lead ← `config:bff.servicelead.messaging.kafka.topics.service-lead`; dev.cp.notification1 ← `config:notification.messaging.kafka.hub-name`; dev.cp.booking ← `config:order.messaging.kafka.topics.booking`; dev.cp.order ← `config:order.messaging.kafka.topics.order`

## Events Consumed

`tvs-cps-backend` consumes 7 messaging entit(ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| dev.cp-booking | tnh-subscription | Unknown | Unknown | Unknown | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingEventConsumer.java:73` | Unknown | processor | error_handler=True |
| dev.oclns.cp-lead | tnh_subscription | Unknown | Unknown | Unknown | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/EnquiryEventConsumer.java:73` | Unknown | processor | error_handler=True |
| dev.ums.user | cps-user-subscription | Unknown | Unknown | Unknown | `bff-service/src/main/java/com/tvsm/bff/service/UMSUserLifecycleConsumer.java:120` | Unknown | processor | error_handler=True |
| dev.cp.booking | Unknown | Unknown | Unknown | binary | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/BookingServiceConsumer.java:45` | tvs-cps-backend | listener-annotation | Unknown |
| dev.cp.service_lead | Unknown | Unknown | Unknown | binary | `bff-service/src/main/java/com/tvsm/bff/messaging/consumer/WarrantyRegistrationConsumer.java:44` | tvs-cps-backend | listener-annotation | Unknown |
| dev.cp.notification1 | Unknown | Unknown | Unknown | Unknown | `notification-service/src/main/java/com/tvsm/notification/consumer/NotificationEventConsumer.java:139` | tvs-cps-backend | listener-annotation | Unknown |
| dev.cp.order | Unknown | Unknown | Unknown | Unknown | `order-service/src/main/java/com/tvsm/order/messaging/consumer/OrderEventConsumer.java:38` | tvs-cps-backend | listener-annotation | Unknown |

Name source per entity: dev.cp-booking ← `config:booking.servicebus.topic-name`; dev.oclns.cp-lead ← `config:lead.servicebus.topic-name`; dev.ums.user ← `config:ums.servicebus.topic-name`; dev.cp.booking ← `config:bff.booking.messaging.kafka.topics.booking`; dev.cp.service_lead ← `config:bff.servicelead.messaging.kafka.topics.service-lead`; dev.cp.notification1 ← `config:notification.messaging.kafka.hub-name`; dev.cp.order ← `config:order.messaging.kafka.topics.order`

## External Integrations

`tvs-cps-backend` third-party integrations found in code.

| System | Purpose | Auth | Evidence |
|---|---|---|---|
| external:onetrust | category: other | Unknown | `bff-service/src/main/java/com/tvsm/bff/auth/AuthService.java:142` |

## Rate Limits and SLAs

`tvs-cps-backend`: N/A — not determinable from code.

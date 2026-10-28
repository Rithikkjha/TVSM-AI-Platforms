---
service_id: tvs-cps-portal
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# tvs-cps-portal — API Specification

## Authentication
tvs-cps-portal endpoint auth as extracted: `None` × 12.
Auth-related code: `channel-partner-system/src/app/api/chatbot/route.ts:64` (middleware.ts).
Auth libraries: `identity-obj-proxy`.

## Endpoint Index
tvs-cps-portal exposes 12 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/thenortonhub/api/claim/claim-details/{claimId}` | Unknown | handler `channel-partner-system/src/app/api/claim/claim-details/[claimId]/route.ts#GET` | Unknown |
| GET | `/thenortonhub/api/claim/master` | Unknown | handler `channel-partner-system/src/app/api/claim/master/route.ts#GET` | Unknown |
| GET | `/thenortonhub/api/file` | Unknown | handler `channel-partner-system/src/app/api/file/route.ts#GET` | Unknown |
| GET | `/thenortonhub/api/get-image` | Unknown | handler `channel-partner-system/src/app/api/get-image/route.ts#GET` | Unknown |
| GET | `/thenortonhub/api/getEnvConfig` | Unknown | handler `channel-partner-system/src/app/api/getEnvConfig/route.ts#GET` | tvs-cps-portal |
| GET | `/thenortonhub/api/stream` | Unknown | handler `channel-partner-system/src/app/api/stream/route.ts#GET` | Unknown |
| GET | `/thenortonhub/firebase-messaging-sw.js` | Unknown | handler `channel-partner-system/src/app/firebase-messaging-sw.js/route.ts#GET` | Unknown |
| POST | `/thenortonhub/api/chatbot` | Unknown | handler `channel-partner-system/src/app/api/chatbot/route.ts#POST` | tvs-cps-portal |
| POST | `/thenortonhub/api/claim/dashboard` | Unknown | handler `channel-partner-system/src/app/api/claim/dashboard/route.ts#POST` | Unknown |
| POST | `/thenortonhub/api/claim/update` | Unknown | handler `channel-partner-system/src/app/api/claim/update/route.ts#POST` | Unknown |
| POST | `/thenortonhub/api/clear-token` | Unknown | handler `channel-partner-system/src/app/api/clear-token/route.ts#POST` | tvs-cps-portal |
| POST | `/thenortonhub/api/set-token` | Unknown | handler `channel-partner-system/src/app/api/set-token/route.ts#POST` | tvs-cps-portal |

## Endpoints
tvs-cps-portal endpoint details (from inventory `inbound_http`).

### GET /thenortonhub/api/claim/claim-details/{claimId}
Handler: `channel-partner-system/src/app/api/claim/claim-details/[claimId]/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| claimId | path | string | True | |

### GET /thenortonhub/api/claim/master
Handler: `channel-partner-system/src/app/api/claim/master/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### GET /thenortonhub/api/file
Handler: `channel-partner-system/src/app/api/file/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### GET /thenortonhub/api/get-image
Handler: `channel-partner-system/src/app/api/get-image/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### GET /thenortonhub/api/getEnvConfig
Handler: `channel-partner-system/src/app/api/getEnvConfig/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: tvs-cps-portal.

### GET /thenortonhub/api/stream
Handler: `channel-partner-system/src/app/api/stream/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### GET /thenortonhub/firebase-messaging-sw.js
Handler: `channel-partner-system/src/app/firebase-messaging-sw.js/route.ts#GET` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### POST /thenortonhub/api/chatbot
Handler: `channel-partner-system/src/app/api/chatbot/route.ts#POST` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: tvs-cps-portal.

### POST /thenortonhub/api/claim/dashboard
Handler: `channel-partner-system/src/app/api/claim/dashboard/route.ts#POST` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### POST /thenortonhub/api/claim/update
Handler: `channel-partner-system/src/app/api/claim/update/route.ts#POST` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: Unknown.

### POST /thenortonhub/api/clear-token
Handler: `channel-partner-system/src/app/api/clear-token/route.ts#POST` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: tvs-cps-portal.

### POST /thenortonhub/api/set-token
Handler: `channel-partner-system/src/app/api/set-token/route.ts#POST` in `channel-partner-system/next.config.ts:50`. Purpose: Unknown. Callers: tvs-cps-portal.

## Outbound Calls
tvs-cps-portal outbound HTTP calls (184 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:firebase` | - | - | - | - | Unknown | Unknown |
| `tvs-cps-portal` | GET | `/thenortonhub/api/getEnvConfig` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/reports/list` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/analytics-dashboard/indicators/get` | - | DashboardResponse | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/announcement/get/{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/announcement/user/banners` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/appointments/{}` | - | AppointmentInterface | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/billing/get` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | GET | `/v1/booking/get` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/booking/get-booking-list` | - | BookingsData | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/booking/master-data` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/cart/active-cart` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/cart/{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/assemblies` | - | AssemblyResponse[] | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/assemblies{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/catalog-summary` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/get/{}` | - | any | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/labor/area/{}` | - | LabourCatalogResponse | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/merchandise/categories` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/merchandise/colors` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/merchandise/{}` | - | MerchandiseDetails | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/parts` | - | PartsInterface | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/parts/vehicleCatalogSkus/{}{}` | - | PartsApiResponse | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/vehicle` | - | VehicleCatalogResponse, VehicleCatalogResponse[] | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/catalogs/vehicle-data` | - | VehicleVariantResponse[] | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/channel-partner/list` | - | ChannelPartnerListResponse, DealersResponse | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/claims/grn/details/{}` | - | GrnDetailsData | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/claims/master` | - | ClaimMasterData | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/claims/timeline/{}` | - | TimelineResponse | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/claims/{}` | - | ClaimDetailInterface | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/collateral/categories` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/collateral/departments` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/collateral/get/{}` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/collateral/stats/{}` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | GET | `/v1/dashboard/list/{}` | - | Partial<Record<string, DatabricksDashboardListItem[]>> | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/enquiry/get-enquiry` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/enquiry/getEnquiryMaster` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/enquiry/vehicles` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/enquiry/vehicles/{}/variants` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/grn/details/{}` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/inventory/get/{}` | - | PartsInventory[] | Unknown | Unknown |
| `tvs-cps-backend` | GET | `/v1/invoice/delivery-view/{}` | - | DeliveryOrderApiData | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/jobcards/formbuilder/token` | - | CheckListTokenResponse | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/jobcards/master` | - | JobCardMasterData | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/jobcards/{}` | - | JobCardInterface | Unknown | Unknown |
| `tvs-cps-backend` | GET | `/v1/location/address/autocomplete` | - | AddressSuggestion[] | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/location/address/details` | - | AddressDetails | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/order/get` | - | any | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/order/get-branch` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/order/orderedPartDetails` | - | any | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/order/status-counts` | - | - | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/permissions/user-info` | - | UserResponse | Unknown | hard |
| `tvs-cps-backend` | GET | `/v1/permissions/user-role/list` | - | DealerRolesResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/product/inventory/summary/{}` | - | ProductInventorySummaryResponse | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/product/order/{}` | - | ProductOrderResponse | Unknown | Unknown |
| `tvs-cps-backend` | GET | `/v1/training/get/{}` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/v1/user/list-all` | - | RoleResponse | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | GET | `/{}/{}/error` | - | BulkUploadErrorItem[] | Unknown | Unknown |
| Unknown (env:RUNTIME_ASSETS_BASE_URL) | GET | `/tenants/{}/logo.svg` | - | - | Unknown | Unknown |
| Unknown (env:RUNTIME_ASSETS_BASE_URL) | GET | `/tenants/{}/variable.css` | - | - | Unknown | Unknown |
| Unknown (env:RUNTIME_ASSETS_BASE_URL) | GET | `/tenants/{}/{}` | - | - | Unknown | Unknown |
| Unknown (env:RUNTIME_CONFIG_BASE_URL) | GET | `/public/tenants/{}/config.json` | - | RuntimeTenantConfig | Unknown | Unknown |
| Unknown (env:RUNTIME_CONFIG_BASE_URL) | GET | `/tenants/{}/features.json` | - | RuntimeTenantFeatures | Unknown | Unknown |
| `tvs-cps-portal` | POST | `/thenortonhub/api/chatbot` | - | - | Unknown | hard |
| Unknown (env:DATABRICKS_TOKEN_URL) | POST | `/oidc/v1/token` | - | - | Unknown | Unknown |
| Unknown (env:DATABRICKS_WORKSPACE_URL) | POST | `/invocations` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/auth/v2/app/token-exchange` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/login` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/reports/download` | - | - | Unknown | hard |
| `tvs-cps-portal` | POST | `/thenortonhub/api/clear-token` | - | - | Unknown | hard |
| `tvs-cps-portal` | POST | `/thenortonhub/api/set-token` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/$1/bulk-upload/history` | - | FileUploadListResponse | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/announcement/create` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/announcement/delete/{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/announcement/read` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/announcement/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/announcement/user/search` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/announcement/{}/media/add/GENERAL` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/announcement/{}/media/delete/{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/appointments/count` | - | AppointmentCountResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/appointments/create` | - | CreateAppointmentResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/appointments/dashboard` | - | AppointmentDashboardResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/appointments/download` | - | AppointmentDownloadResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/appointments/list` | - | AppointmentListResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/appointments/update` | - | RescheduleAppointmentResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/billing/post-invoice` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/billing/{}` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/booking/cancel` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/booking/create` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/booking/search` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/booking/stats` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/booking/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/calendar/get` | - | TestRideCalendarApiResponse["data"] | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/cart/create` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/cart/create-active-cart` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/cart/delete/{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/cart/reorder` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/cart/search` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/cart/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/catalogs/all` | - | PartCatalogResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/catalogs/product-details` | - | PAMDetailsData, PartProductDetailResponse, any | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/claims` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/claims/close` | - | CloseClaimResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/claims/dashboard` | - | ClaimDashboardResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/claims/download` | - | ClaimDownloadResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/claims/list` | - | ClaimListResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/collateral/create` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/collateral/delete/{}` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/collateral/download/{}` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/collateral/search` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/collateral/update/{}` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/collateral/view` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/collateral/{}/file/delete/{}` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/collateral/{}/file/upload` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/customer/create` | - | CreateJCCustomerResponseData, any | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/customer/inward-vehicle` | - | CreateJCCustomerResponseData | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/customer/search` | - | CustomerSearch | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/customer/search-vehicle` | - | CustomerSearchVehicle | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/customer/update` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/docs/upload` | - | UploadResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/enquiry/bulk-assign` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/enquiry/bulk-upload/history` | - | EnquiryUploadHistoryResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/enquiry/bulk-upload/{}/errors` | - | EnquiryBulkUploadError[] | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/enquiry/create` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/enquiry/filter` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/enquiry/stats` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/enquiry/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/grn/complete` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/grn/delivery-details/add` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/grn/initiate` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/grn/search` | - | GrnSearchResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/grn/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/inventory/allocate` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/inventory/deallocate` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/inventory/get-add-by-vin` | - | VehicleVinSearchResponseData, any | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/inventory/list` | - | PartInventoryListResponse | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/invoice/search` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/jobcards/create` | - | JobCardCreateResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/jobcards/dashboard` | - | JobCardDashboardResponse | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/jobcards/download` | - | JobCardDownloadResponse | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/jobcards/invoice/generate` | - | JobCardInvoiceGenerateResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/jobcards/list` | - | JobCardListResponse | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/jobcards/warranty-check` | - | PartWarrantyResponse | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/lead-allocation/list` | - | LeadAllocationItem[] | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/lead-allocation/update` | - | any | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/lead/dashboard` | - | ServiceReminderDashboardResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/lead/details` | - | ServiceReminderDetailsData | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/lead/filter` | - | ServiceReminderListData | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/lead/update` | - | LeadUpdateResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-category/all` | - | NotificationCategoryItem[] | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-device/deregister` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-device/register` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-message/read/{}` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-message/search` | - | NotificationMessageSearchResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-preference/list` | - | NotificationPreferenceCategory[] | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/notification-preference/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/npqr/create` | - | CreateNpqrResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/npqr/list` | - | NpqrListResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/order/cancel` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/order/draft/update` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/order/place-order` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/order/search` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/order/update-allocation` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/otp/generate` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/otp/verify` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/smart-search/additional-details` | - | SmartSearchAdditionalDetailsResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/smart-search/details` | - | SmartSearchDetailsResponse | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/smart-search/search` | - | SmartSearchResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/training/complete` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/training/create` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/training/delete/{}` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/training/read` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/training/search` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/training/update` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/vehicle/delivery` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/vehicle/inventory/lookup` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/vehicle/pdi` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/vehicle/submit-inspection` | - | VehicleInspectionSubmitResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | POST | `/v1/vehicle/update/stock-type` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | POST | `/v1/warranty-registration/create` | - | - | Unknown | hard |
| `tvs-cps-backend` | POST | `/v1/workflow/action` | - | - | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_UMS_AUTH_SERVICE_URL) | POST | `/auth/v2/app/refresh-token` | - | - | Unknown | Unknown |
| `tvs-cps-backend` | PUT | `/v1/claims/update` | - | ClaimUpdateResponse | Unknown | hard |
| Unknown (env:NEXT_PUBLIC_API_BASE_URL) | PUT | `/v1/jobcards/update` | - | JobCardDashboardResponse | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| GET | `/thenortonhub/api/getEnvConfig` | axios | unknown | `channel-partner-system/src/constants/environment.constant.ts:50` |
| GET | `/reports/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/reports.service.ts:51` |
| GET | `/v1/analytics-dashboard/indicators/get` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/dashboard.service.ts:8` |
| GET | `/v1/announcement/get/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:140` |
| GET | `/v1/announcement/user/banners` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:144` |
| GET | `/v1/appointments/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:54` |
| GET | `/v1/billing/get` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/invoice.service.ts:477` |
| GET | `/v1/booking/get` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:101` |
| GET | `/v1/booking/get-booking-list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:92` |
| GET | `/v1/booking/master-data` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:55` |
| GET | `/v1/cart/active-cart` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:229` |
| GET | `/v1/cart/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Parts/PlaceOrder/hooks/usePlaceOrderData.ts:51` |
| GET | `/v1/catalogs/assemblies` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:103` |
| GET | `/v1/catalogs/assemblies{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/catalog.slice.ts:86` |
| GET | `/v1/catalogs/catalog-summary` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/stocks.service.ts:277` |
| GET | `/v1/catalogs/get/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/invoice.service.ts:801` |
| GET | `/v1/catalogs/labor/area/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/common.service.ts:41` |
| GET | `/v1/catalogs/merchandise/categories` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/catalog.slice.ts:117` |
| GET | `/v1/catalogs/merchandise/colors` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/catalog.slice.ts:129` |
| GET | `/v1/catalogs/merchandise/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/merchandise.service.ts:112` |
| GET | `/v1/catalogs/parts` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:52` |
| GET | `/v1/catalogs/parts/vehicleCatalogSkus/{}{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:165` |
| GET | `/v1/catalogs/vehicle` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/customer.service.ts:18` |
| GET | `/v1/catalogs/vehicle-data` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:99` |
| GET | `/v1/channel-partner/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/common.service.ts:33` |
| GET | `/v1/claims/grn/details/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:132` |
| GET | `/v1/claims/master` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:172` |
| GET | `/v1/claims/timeline/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:31` |
| GET | `/v1/claims/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:26` |
| GET | `/v1/collateral/categories` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:151` |
| GET | `/v1/collateral/departments` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:155` |
| GET | `/v1/collateral/get/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:142` |
| GET | `/v1/collateral/stats/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:170` |
| GET | `/v1/dashboard/list/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/dashboard.service.ts:12` |
| GET | `/v1/enquiry/get-enquiry` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:55` |
| GET | `/v1/enquiry/getEnquiryMaster` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:66` |
| GET | `/v1/enquiry/vehicles` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:40` |
| GET | `/v1/enquiry/vehicles/{}/variants` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:44` |
| GET | `/v1/grn/details/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/Inwarding/inwarding.slice.ts:159` |
| GET | `/v1/inventory/get/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:73` |
| GET | `/v1/invoice/delivery-view/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/deliveryOrder.service.ts:89` |
| GET | `/v1/jobcards/formbuilder/token` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:69` |
| GET | `/v1/jobcards/master` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:178` |
| GET | `/v1/jobcards/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:15` |
| GET | `/v1/location/address/autocomplete` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/location.service.ts:27` |
| GET | `/v1/location/address/details` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/location.service.ts:42` |
| GET | `/v1/order/get` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/merchandise/merchandiseOrder.slice.ts:164` |
| GET | `/v1/order/get-branch` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:69` |
| GET | `/v1/order/orderedPartDetails` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/merchandise/merchandiseOrder.slice.ts:190` |
| GET | `/v1/order/status-counts` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/order.slice.ts:182` |
| GET | `/v1/permissions/user-info` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/user.service.ts:8` |
| GET | `/v1/permissions/user-role/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/dealer/dealer.slice.ts:35` |
| GET | `/v1/product/inventory/summary/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/merchandise.service.ts:126` |
| GET | `/v1/product/order/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/merchandise.service.ts:119` |
| GET | `/v1/training/get/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:133` |
| GET | `/v1/user/list-all` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/user.service.ts:29` |
| GET | `/{}/{}/error` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/upload.service.ts:31` |
| GET | `/tenants/{}/logo.svg` | fetch | env:RUNTIME_ASSETS_BASE_URL | `channel-partner-system/scripts/build-tools.ts:22` |
| GET | `/tenants/{}/variable.css` | fetch | env:RUNTIME_ASSETS_BASE_URL | `channel-partner-system/scripts/build-tools.ts:19` |
| GET | `/tenants/{}/{}` | fetch | env:RUNTIME_ASSETS_BASE_URL | `channel-partner-system/scripts/build-tools.ts:30` |
| GET | `/public/tenants/{}/config.json` | fetch | env:RUNTIME_CONFIG_BASE_URL | `channel-partner-system/src/server/runtime-config.ts:40` |
| GET | `/tenants/{}/features.json` | fetch | env:RUNTIME_CONFIG_BASE_URL | `channel-partner-system/src/server/runtime-config.ts:55` |
| POST | `/thenortonhub/api/chatbot` | fetch | unknown | `channel-partner-system/src/services/chatbot.service.ts:24` |
| POST | `/oidc/v1/token` | fetch | env:DATABRICKS_TOKEN_URL | `channel-partner-system/src/app/api/chatbot/route.ts:28` |
| POST | `/invocations` | fetch | env:DATABRICKS_WORKSPACE_URL | `channel-partner-system/src/app/api/chatbot/route.ts:123` |
| POST | `/auth/v2/app/token-exchange` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/auth.service.ts:53` |
| POST | `/login` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/auth.service.ts:38` |
| POST | `/reports/download` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/reports.service.ts:98` |
| POST | `/thenortonhub/api/clear-token` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/auth.service.ts:34` |
| POST | `/thenortonhub/api/set-token` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/auth.service.ts:30` |
| POST | `/v1/$1/bulk-upload/history` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/fileupload.service.ts:18` |
| POST | `/v1/announcement/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:136` |
| POST | `/v1/announcement/delete/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:163` |
| POST | `/v1/announcement/read` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:151` |
| POST | `/v1/announcement/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:167` |
| POST | `/v1/announcement/user/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:159` |
| POST | `/v1/announcement/{}/media/add/GENERAL` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:171` |
| POST | `/v1/announcement/{}/media/delete/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:175` |
| POST | `/v1/appointments/count` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:41` |
| POST | `/v1/appointments/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:63` |
| POST | `/v1/appointments/dashboard` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:46` |
| POST | `/v1/appointments/download` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:72` |
| POST | `/v1/appointments/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:22` |
| POST | `/v1/appointments/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/appointment.service.ts:59` |
| POST | `/v1/billing/post-invoice` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/invoice.service.ts:446` |
| POST | `/v1/billing/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/invoice.service.ts:399` |
| POST | `/v1/booking/cancel` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:59` |
| POST | `/v1/booking/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:44` |
| POST | `/v1/booking/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/allotment.service.ts:114` |
| POST | `/v1/booking/stats` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:68` |
| POST | `/v1/booking/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/booking.service.ts:63` |
| POST | `/v1/calendar/get` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/testRide.service.ts:178` |
| POST | `/v1/cart/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:77` |
| POST | `/v1/cart/create-active-cart` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Parts/DraftOrder/hooks/useDraftOrder.tsx:133` |
| POST | `/v1/cart/delete/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:99` |
| POST | `/v1/cart/reorder` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Merchandise/MerchandiseOrderDetails/hook/useMerchandiseOrderActions.ts:44` |
| POST | `/v1/cart/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:487` |
| POST | `/v1/cart/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:427` |
| POST | `/v1/catalogs/all` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/invoice.service.ts:320` |
| POST | `/v1/catalogs/product-details` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Invoices/QuickInvoice/hooks/useQuickInvoiceDetails.ts:73` |
| POST | `/v1/claims` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:184` |
| POST | `/v1/claims/close` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:200` |
| POST | `/v1/claims/dashboard` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:65` |
| POST | `/v1/claims/download` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:56` |
| POST | `/v1/claims/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:47` |
| POST | `/v1/collateral/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:174` |
| POST | `/v1/collateral/delete/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:182` |
| POST | `/v1/collateral/download/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:159` |
| POST | `/v1/collateral/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:102` |
| POST | `/v1/collateral/update/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:178` |
| POST | `/v1/collateral/view` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:166` |
| POST | `/v1/collateral/{}/file/delete/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:190` |
| POST | `/v1/collateral/{}/file/upload` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/collateral.service.ts:186` |
| POST | `/v1/customer/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/customer.service.ts:22` |
| POST | `/v1/customer/inward-vehicle` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/customer.service.ts:52` |
| POST | `/v1/customer/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/UniversalSearch/ProfileSection/Profile.tsx:84` |
| POST | `/v1/customer/search-vehicle` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/customer.service.ts:10` |
| POST | `/v1/customer/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/customer.service.ts:14` |
| POST | `/v1/docs/upload` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/upload.service.ts:12` |
| POST | `/v1/enquiry/bulk-assign` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:85` |
| POST | `/v1/enquiry/bulk-upload/history` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:136` |
| POST | `/v1/enquiry/bulk-upload/{}/errors` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:140` |
| POST | `/v1/enquiry/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:36` |
| POST | `/v1/enquiry/filter` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:48` |
| POST | `/v1/enquiry/stats` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:70` |
| POST | `/v1/enquiry/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/enquiry.service.ts:59` |
| POST | `/v1/grn/complete` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/Inwarding/inwarding.slice.ts:177` |
| POST | `/v1/grn/delivery-details/add` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/Inwarding/inwarding.slice.ts:97` |
| POST | `/v1/grn/initiate` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/Inwarding/inwarding.slice.ts:46` |
| POST | `/v1/grn/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:120` |
| POST | `/v1/grn/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/Inwarding/inwarding.slice.ts:79` |
| POST | `/v1/inventory/allocate` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/allotment.service.ts:10` |
| POST | `/v1/inventory/deallocate` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/allotment.service.ts:23` |
| POST | `/v1/inventory/get-add-by-vin` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/invoice.service.ts:788` |
| POST | `/v1/inventory/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Invoices/common/hooks/useStockAvailability.ts:16` |
| POST | `/v1/invoice/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/Inwarding/inwarding.slice.ts:143` |
| POST | `/v1/jobcards/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:48` |
| POST | `/v1/jobcards/dashboard` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:44` |
| POST | `/v1/jobcards/download` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:39` |
| POST | `/v1/jobcards/invoice/generate` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:30` |
| POST | `/v1/jobcards/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:23` |
| POST | `/v1/jobcards/warranty-check` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:65` |
| POST | `/v1/lead-allocation/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/leadAllocation.service.ts:30` |
| POST | `/v1/lead-allocation/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/leadAllocation.service.ts:53` |
| POST | `/v1/lead/dashboard` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/serviceReminder.service.ts:176` |
| POST | `/v1/lead/details` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/serviceReminder.service.ts:276` |
| POST | `/v1/lead/filter` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/serviceReminder.service.ts:227` |
| POST | `/v1/lead/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/serviceReminder.service.ts:280` |
| POST | `/v1/notification-category/all` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:196` |
| POST | `/v1/notification-device/deregister` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:184` |
| POST | `/v1/notification-device/register` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:181` |
| POST | `/v1/notification-message/read/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:200` |
| POST | `/v1/notification-message/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:193` |
| POST | `/v1/notification-preference/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:187` |
| POST | `/v1/notification-preference/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/notification.service.ts:190` |
| POST | `/v1/npqr/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/npqr.service.ts:274` |
| POST | `/v1/npqr/list` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Npqr/NpqrDetails/NpqrDetails.tsx:66` |
| POST | `/v1/order/cancel` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Merchandise/MerchandiseOrderDetails/hook/useMerchandiseOrderActions.ts:92` |
| POST | `/v1/order/draft/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:145` |
| POST | `/v1/order/place-order` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/parts/cart.slice.ts:193` |
| POST | `/v1/order/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/store/reducers/merchandise/merchandiseOrder.slice.ts:125` |
| POST | `/v1/order/update-allocation` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Merchandise/MerchandiseOrderDetails/hook/useMerchandiseOrderActions.ts:140` |
| POST | `/v1/otp/generate` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/otp.service.ts:6` |
| POST | `/v1/otp/verify` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/otp.service.ts:10` |
| POST | `/v1/smart-search/additional-details` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/smartSearch.service.ts:49` |
| POST | `/v1/smart-search/details` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/smartSearch.service.ts:38` |
| POST | `/v1/smart-search/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/smartSearch.service.ts:27` |
| POST | `/v1/training/complete` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:149` |
| POST | `/v1/training/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:137` |
| POST | `/v1/training/delete/{}` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:145` |
| POST | `/v1/training/read` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:155` |
| POST | `/v1/training/search` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:95` |
| POST | `/v1/training/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/training.service.ts:141` |
| POST | `/v1/vehicle/delivery` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/vehicles.service.ts:135` |
| POST | `/v1/vehicle/inventory/lookup` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/VinList/hooks/useVinList.tsx:88` |
| POST | `/v1/vehicle/pdi` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/allotment.service.ts:36` |
| POST | `/v1/vehicle/submit-inspection` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/vehicleInspection.service.ts:171` |
| POST | `/v1/vehicle/update/stock-type` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/stocks.service.ts:258` |
| POST | `/v1/warranty-registration/create` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/warranty.service.ts:21` |
| POST | `/v1/workflow/action` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/components/ui/Parts/OemOrderDetails/hooks/useOemOrderActions.ts:90` |
| POST | `/auth/v2/app/refresh-token` | axios | env:NEXT_PUBLIC_UMS_AUTH_SERVICE_URL | `channel-partner-system/src/services/auth.service.ts:86` |
| PUT | `/v1/claims/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/claim.service.ts:60` |
| PUT | `/v1/jobcards/update` | axios | env:NEXT_PUBLIC_API_BASE_URL | `channel-partner-system/src/services/jobCard.service.ts:61` |

## Schemas
tvs-cps-portal DTOs/payloads referenced in this file.

### DashboardResponse
Defined in: `channel-partner-system/src/types/Dashboard.interface.ts:29`
Fields: Unknown (no fields extracted)

### AppointmentInterface
Defined in: `channel-partner-system/src/store/reducers/Appointment/Appointment.interface.ts:1`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| listStatus | string | False | - |

### BookingsData
Defined in: `channel-partner-system/src/services/vehicles.service.ts:44`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| bookings | ApiBookingData[] | True | - |
| totalBookings | number | False | - |

### AssemblyResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:852`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| catalogSkuId | string | True | - |
| assemblyName | string | True | - |
| subAssemblyList | SubAssemblyResponse[] | True | - |

### LabourCatalogResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:748`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| productType | string | True | - |
| categories | LabourCategory[] | True | - |

### MerchandiseDetails
Defined in: `channel-partner-system/src/components/ui/Merchandise/MerchandiseDelivery/components/MerchandiseDetailsDisplay.tsx:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| merchandiseDescription | string | True | - |
| merchandiseName | string | True | - |
| merchandiseId | string | True | - |
| merchandiseNumber | string | True | - |
| merchandiseColor | string | False | - |
| merchandiseSize | string | False | - |
| stockStatus | string | True | - |
| unitPrice | string | True | - |
| currentQtyInMyStock | string | True | - |
| currentMyStockValue | string | True | - |
| qtyOrdered | string | True | - |
| orderValue | string | True | - |
| merchandiseType | string | True | - |
| currentStockLocation | string | True | - |
| merchandiseImageUrl | string | False | - |
| merchandiseImageUrls | string[] | False | - |

### PartsInterface
Defined in: `channel-partner-system/src/types/Parts.interface.ts:26`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| content | PartsCategory[] | True | - |
| page | number | True | - |
| size | number | True | - |
| total | number | True | - |

### PartsApiResponse
Defined in: `channel-partner-system/src/types/Parts.interface.ts:210`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| _id | string | True | - |
| id | number | True | - |
| name | string | True | - |
| market | string | True | - |
| isDefaultCatalog | boolean | True | - |
| nameSpace | string | True | - |
| industry | string | True | - |
| productType | string | True | - |
| categories | PartItem[] | True | - |
| isArchived | boolean | True | - |
| createdDate | string | True | - |
| modifiedDate | string | True | - |
| page | number | False | - |
| size | number | False | - |
| totalElements | number | False | - |
| totalPages | number | False | - |

### VehicleCatalogResponse
Defined in: `channel-partner-system/src/services/npqr.service.ts:74`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | object[] | True | - |

### VehicleVariantResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:864`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| modelName | string | True | - |
| vehicleName | string | True | - |
| catalogSkuId | string | True | - |
| variants | VariantResponse[] | True | - |

### DealersResponse
Defined in: `channel-partner-system/src/store/reducers/dealer/dealer.interface.ts:23`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | Dealer[] | True | - |

### GrnDetailsData
Defined in: `channel-partner-system/src/types/ShortageTransit.interface.ts:201`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| invoiceId | string | True | - |
| deliveryId | string | True | - |
| orderId | string | True | - |
| invoiceIdLocation | string | True | - |
| damagedItemsCount | number | True | - |
| damagedItemsValue | number | True | - |
| missingItemsCount | number | True | - |
| missingItemsValue | number | True | - |
| orderCategoryType | string | True | - |
| vehicles | VehiclesData | True | - |
| parts | object | False | - |

### ClaimMasterData
Defined in: `channel-partner-system/src/types/ShortageTransit.interface.ts:85`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| faultType | FaultType[] | True | - |
| kitWithAssemblies | KitWithAssembly[] | True | - |
| labour | LabourCategory[] | True | - |

### TimelineResponse
Defined in: `channel-partner-system/src/components/ui/Timeline/ClaimTimeline.ts:21`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | object | True | - |

### ClaimDetailInterface
Defined in: `channel-partner-system/src/types/ClaimDetail.interface.ts:177`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| claimId | string | True | - |
| claimType | string | True | - |
| entityType | string | False | - |
| createdAt | string | True | - |
| claimValue | string | True | - |
| updatedAt | string | True | - |
| approvedValue | string | True | - |
| status | string | True | - |
| dealerCode | string | False | - |
| dealerName | string | False | - |
| userApprovalLevel | string | False | - |
| jobCardDetails | JobCardDetails | False | - |
| orderDetails | OrderDetails | False | - |
| grnDetails | GrnDetails | False | - |
| vehicleDetails | VehicleDetails | False | - |
| customerDetails | CustomerDetails | False | - |
| parts | Part[] | False | - |
| labours | Labour[] | False | - |
| customerFeedback | Feedback[] | False | - |
| serviceHistory | ServiceHistory[] | False | - |
| totalLaborClaim | string | False | - |
| totalPartClaim | string | False | - |
| erpDetails | ErpDetails | False | - |

### DatabricksDashboardListItem
Defined in: `channel-partner-system/src/types/Dashboard.interface.ts:35`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dashboardId | string | True | - |
| dashboardName | string | True | - |
| dashboardType | string | True | - |
| priority | number | True | - |

### PartsInventory
Defined in: `channel-partner-system/src/types/Parts.interface.ts:20`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| availableQuantity | string | True | - |
| productCatalogId | string | True | - |
| productCategoryType | string | True | - |

### DeliveryOrderApiData
Defined in: `channel-partner-system/src/types/deliveryOrder.types.ts:51`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| deliveryId | string | True | - |
| deliveryValue | number | True | - |
| estimatedDeliveryDate | string | True | - |
| items | DeliveryOrderApiItemsPage | True | - |

### CheckListTokenResponse
Defined in: `channel-partner-system/src/types/JobCard.interface.ts:172`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| token_type | string | True | - |
| expires_in | number | True | - |
| ext_expires_in | number | True | - |
| token | string | True | - |

### JobCardMasterData
Defined in: `channel-partner-system/src/store/reducers/MasterData/MasterData.interface.ts:41`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| jobCardStatus | MasterDataItem[] | True | - |
| jobType | MasterDataItem[] | True | - |
| serviceType | MasterDataItem[] | True | - |
| issueMode | MasterDataItem[] | True | - |
| complaint | MasterDataItem[] | True | - |
| complaintGroup | MasterDataItem[] | True | - |
| labourType | MasterDataItem[] | True | - |
| isLoaded | boolean | False | - |
| feedbackGroup | MasterDataItem[] | True | - |
| feedback | MasterDataItem[] | True | - |
| labour | MasterLabourTask[] | True | - |
| templateUrl | string | True | - |

### JobCardInterface
Defined in: `channel-partner-system/src/store/reducers/JobCard/JobCard.interface.ts:62`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| listStatus | string | False | - |
| serializedFilter | SerializedJobCardListFilter | False | - |
| historyCustomerVehicleId | HistoryVehicleData | True | - |
| createJobCard | object | True | - |
| currentJobDetails | JobCardDetailsInterface | True | - |
| labourData | LabourCategory[] | True | - |
| isHistoryOpened | boolean | True | - |

### AddressSuggestion
Defined in: `channel-partner-system/src/types/Location.interface.ts:16`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| description | string | True | - |
| placeId | string | True | - |

### AddressDetails
Defined in: `channel-partner-system/src/types/Location.interface.ts:26`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| placeId | string | True | - |
| formattedAddress | string | True | - |
| streetNumber | string | True | - |
| streetName | string | True | - |
| city | string | True | - |
| state | string | True | - |
| postalCode | string | True | - |
| country | string | True | - |
| countryCode | string | True | - |
| latitude | number | True | - |
| longitude | number | True | - |

### UserResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:640`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| sub | string | True | - |
| firstName | string | True | - |
| lastName | string | True | - |
| dealerId | string | True | - |
| userType | string | True | - |
| country | string | True | - |
| uid | number | True | - |
| employeeId | string | True | - |
| primaryPhoneNumber | string | True | - |
| dealerName | string | True | - |
| email | string | True | - |
| userId | string | True | - |
| profilePicture | string | True | - |
| permissions | object[] | True | - |
| timezone | string | False | - |
| currencyCode | string | False | - |
| locale | string | False | - |
| tenantId | string | False | - |

### DealerRolesResponse
Defined in: `channel-partner-system/src/store/reducers/dealer/dealer.interface.ts:16`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | DealerRole[] | True | - |

### ProductInventorySummaryResponse
Defined in: `channel-partner-system/src/services/merchandise.service.ts:82`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| productCatalogId | string | True | - |
| productName | string | False | - |
| model | string | False | - |
| variant | string | False | - |
| color | string | False | - |
| image | string | False | - |
| inevntoryDetail | ProductInventoryDetail | True | - |

### ProductOrderResponse
Defined in: `channel-partner-system/src/services/merchandise.service.ts:65`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| productCatalogId | string | True | - |
| productName | string | False | - |
| model | string | False | - |
| variant | string | False | - |
| color | string | False | - |
| image | string | False | - |
| orderDetail | ProductOrderDetail | True | - |

### RoleResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:661`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | RoleUser[] | True | - |

### BulkUploadErrorItem
Defined in: `channel-partner-system/src/types/common.interface.ts:633`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| errorMessage | string | True | - |
| errorType | string | True | - |
| additionalInfo | object | True | - |
| createdAt | string | True | - |

### RuntimeTenantConfig
Defined in: `channel-partner-system/src/server/runtime-config.ts:5`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| siteName | string | True | - |
| siteDescription | string | True | - |
| defaultLocale | string | True | - |
| supportedLocales | string[] | True | - |
| manifest | string | True | - |
| applicationInsightsKey | string | False | - |
| loaderColor | string | False | - |

### RuntimeTenantFeatures
Defined in: `channel-partner-system/src/server/runtime-config.ts:15`
Fields: Unknown (no fields extracted)

### FileUploadListResponse
Defined in: `channel-partner-system/src/types/FileUploadList.interface.ts:61`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| page | number | True | - |
| size | number | True | - |
| total | number | True | - |
| content | FileUploadListContentItem[] | True | - |

### AppointmentCountResponse
Defined in: `channel-partner-system/src/types/AppointmentList.interface.ts:104`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| totalCount | number | True | - |
| summary | AppointmentCountSummaryItem[] | True | - |

### CreateAppointmentResponse
Defined in: `channel-partner-system/src/types/Appointment.interface.ts:121`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentId | string | True | - |
| appointmentNo | string | True | - |
| channel | string | True | - |
| entityType | string | True | - |
| entitySubType | string | True | - |
| appointmentDateTime | string | True | - |
| followUpDateTime | string | True | - |
| numberOfFollowUps | number | True | - |
| status | string | True | - |
| remark | string | True | - |
| cceId | string | True | - |
| reason | string | True | - |
| jobType | string | True | - |
| serviceType | string | True | - |
| createdAt | string | True | - |
| createdBy | string | True | - |
| updatedAt | string | True | - |
| updatedBy | string | True | - |
| context | object[] | True | - |
| followUps | FollowUp[] | True | - |

### AppointmentDashboardResponse
Defined in: `channel-partner-system/src/types/AppointmentDashboard.interface.ts:44`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentCounts | object | True | - |

### AppointmentDownloadResponse
Defined in: `channel-partner-system/src/types/AppointmentList.interface.ts:138`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| content | AppointmentDownloadInterface[] | True | - |
| totalItems | number | True | - |

### AppointmentListResponse
Defined in: `channel-partner-system/src/types/AppointmentList.interface.ts:59`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| page | number | True | - |
| size | number | True | - |
| total | number | True | - |
| content | AppointmentListContentItem[] | True | - |

### RescheduleAppointmentResponse
Defined in: `channel-partner-system/src/types/Appointment.interface.ts:92`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| success | boolean | True | - |
| message | string | True | - |
| data | AppointmentInterface | True | - |

### TestRideCalendarApiResponse
Defined in: `channel-partner-system/src/types/TestRide.interface.ts:40`
Fields: Unknown (no fields extracted)

### PartCatalogResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:840`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| catalogItems | PartCatalogItem[] | True | - |
| currentPage | number | False | - |
| totalRecords | number | False | - |

### PartProductDetailResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:835`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| partsData | PartCatalogItem[] | True | - |

### CloseClaimResponse
Defined in: `channel-partner-system/src/services/claim.service.ts:193`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| success | boolean | True | - |
| message | string | False | - |

### ClaimDashboardResponse
Defined in: `channel-partner-system/src/components/ui/ClaimList/ClaimList.interface.ts:169`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| claimCounts | ClaimDashboardCounts | True | - |

### ClaimDownloadResponse
Defined in: `channel-partner-system/src/components/ui/ClaimList/ClaimList.interface.ts:204`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | object | True | - |

### ClaimListResponse
Defined in: `channel-partner-system/src/components/ui/ClaimList/ClaimList.interface.ts:25`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| total | number | False | - |
| totalItems | number | False | - |
| page | number | True | - |
| size | number | True | - |
| claims | ClaimListInterface[] | False | - |
| content | ClaimListInterface[] | False | - |

### CreateJCCustomerResponseData
Defined in: `channel-partner-system/src/types/common.interface.ts:547`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customerId | string | True | - |
| firstName | string | True | - |
| lastName | string | True | - |
| email | string | True | - |
| mobileNumber | string | True | - |
| addressCount | number | True | - |
| vehicleCount | number | True | - |
| status | string | True | - |
| isCustomerVerified | boolean | True | - |
| isPhoneVerified | boolean | True | - |
| isEmailVerified | boolean | True | - |

### CustomerSearch
Defined in: `channel-partner-system/src/types/common.interface.ts:418`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| customer | CustomerSearchData[] | True | - |

### CustomerSearchVehicle
Defined in: `channel-partner-system/src/types/common.interface.ts:422`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| datalakeObject | DatalakeVehicleObject | True | - |
| customerObject | object | True | - |

### UploadResponse
Defined in: `channel-partner-system/src/types/common.interface.ts:595`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| url | string | True | - |
| originalFilename | string | True | - |
| size | number | True | - |
| contentType | string | True | - |

### EnquiryUploadHistoryResponse
Defined in: `channel-partner-system/src/services/enquiry.service.ts:103`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| page | number | True | - |
| size | number | True | - |
| total | number | True | - |
| content | object[] | True | - |

### EnquiryBulkUploadError
Defined in: `channel-partner-system/src/services/enquiry.service.ts:130`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| errorMessage | string | True | - |
| additionalInfo | object | True | - |

### GrnSearchResponse
Defined in: `channel-partner-system/src/types/ShortageTransit.interface.ts:170`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | object | True | - |

### VehicleVinSearchResponseData
Defined in: `channel-partner-system/src/types/warranty.interface.ts:37`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| deliveryDate | string | True | - |
| invoiceDate | string | True | - |
| additionalInfo | VehicleAdditionalInfo | True | - |
| warrantyExpiryDate | string | True | - |
| entityId | string | True | - |
| vehicleId | string | True | - |
| productCatalogId | string | True | - |
| vin | string | True | - |
| chassisNumber | string | True | - |
| manufactureYear | string | True | - |
| manufactureMonth | string | True | - |
| locationName | string | True | - |

### PartInventoryListResponse
Defined in: `channel-partner-system/src/types/Parts.interface.ts:14`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| content | PartsInventory[] | True | - |
| page | number | True | - |
| size | number | True | - |
| total | number | True | - |

### JobCardCreateResponse
Defined in: `channel-partner-system/src/types/JobCard.interface.ts:163`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| jobCardId | string | True | - |
| jobCardNumber | string | True | - |
| jobType | string | True | - |
| serviceType | string | True | - |
| promisedDeliveryDateTime | string | True | - |
| estimatedCost | number | True | - |

### JobCardDashboardResponse
Defined in: `channel-partner-system/src/types/JobCardDashboard.interface.ts:30`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| jobcardCounts | object | True | - |

### JobCardDownloadResponse
Defined in: `channel-partner-system/src/types/JobCardList.interface.ts:129`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| content | JobCardDownloadInterface[] | True | - |
| totalItems | number | True | - |

### JobCardInvoiceGenerateResponse
Defined in: `channel-partner-system/src/types/JobCardUpdate.interface.ts:34`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| invoiceNumber | string | True | - |

### JobCardListResponse
Defined in: `channel-partner-system/src/types/JobCardList.interface.ts:46`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| total | number | True | - |
| page | number | True | - |
| size | number | True | - |
| content | JobCardListInterface[] | True | - |

### PartWarrantyResponse
Defined in: `channel-partner-system/src/types/Parts.interface.ts:116`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| isUnderWarranty | boolean | True | - |

### LeadAllocationItem
Defined in: `channel-partner-system/src/types/leadAllocation.interface.ts:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| type | string | True | - |
| entityTypeId | string | True | - |
| entityType | string | True | - |
| assignedUsers | AssignedUser[] | True | - |

### ServiceReminderDashboardResponse
Defined in: `channel-partner-system/src/types/ServiceReminderDashboard.interface.ts:31`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| leadCounts | LeadCounts | True | - |

### ServiceReminderDetailsData
Defined in: `channel-partner-system/src/services/serviceReminder.service.ts:66`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| appointmentId | string | False | - |
| appointmentNo | string | False | - |
| reminderInformation | object | False | - |
| interactionDetails | object | False | - |
| serviceHistory | object | False | - |
| vehicleCustomerId | string | False | - |

### ServiceReminderListData
Defined in: `channel-partner-system/src/types/ServiceReminderList.interface.ts:57`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| content | ServiceReminderApiItem[] | True | - |
| totalRecords | number | True | - |
| pageSize | number | True | - |
| currentPage | number | True | - |
| totalPages | number | True | - |

### LeadUpdateResponse
Defined in: `channel-partner-system/src/services/serviceReminder.service.ts:58`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | False | - |
| message | string | False | - |
| messageKey | string | False | - |
| data | any | False | - |

### NotificationCategoryItem
Defined in: `channel-partner-system/src/services/notification.service.ts:123`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationCategoryId | string | True | - |
| name | string | True | - |

### NotificationMessageSearchResponse
Defined in: `channel-partner-system/src/services/notification.service.ts:107`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| content | NotificationMessageSearchResponseItem[] | True | - |
| totalRecords | number | False | - |

### NotificationPreferenceCategory
Defined in: `channel-partner-system/src/services/notification.service.ts:78`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| notificationCategoryId | string | True | - |
| categoryCode | string | True | - |
| categoryName | string | True | - |
| subCategories | NotificationPreferenceSubCategory[] | True | - |

### CreateNpqrResponse
Defined in: `channel-partner-system/src/services/npqr.service.ts:123`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | string | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | object | True | - |

### NpqrListResponse
Defined in: `channel-partner-system/src/components/ui/Npqr/List/NpqrList.interface.ts:38`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| page | number | True | - |
| size | number | True | - |
| total | number | True | - |
| content | NpqrListInterface[] | True | - |

### SmartSearchAdditionalDetailsResponse
Defined in: `channel-partner-system/src/types/SmartSearch.interface.ts:240`
Fields: Unknown (no fields extracted)

### SmartSearchDetailsResponse
Defined in: `channel-partner-system/src/types/SmartSearch.interface.ts:160`
Fields: Unknown (no fields extracted)

### SmartSearchResponse
Defined in: `channel-partner-system/src/types/SmartSearch.interface.ts:98`
Fields: Unknown (no fields extracted)

### VehicleInspectionSubmitResponse
Defined in: `channel-partner-system/src/services/vehicleInspection.service.ts:94`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| pdiStatus | string | True | - |
| deliveryStatus | string | True | - |
| pdiSubmissionStatus | string | True | - |
| deliverySubmissionStatus | string | True | - |
| pdiSubmissionId | string | True | - |
| deliverySubmissionId | string | True | - |
| pdiSubmissionDate | string | True | - |
| deliverySubmissionDate | string | True | - |

### ClaimUpdateResponse
Defined in: `channel-partner-system/src/components/ui/ClaimList/ClaimList.interface.ts:101`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| status | ClaimUpdateStatus | True | - |
| statusCode | string | True | - |
| message | string | True | - |
| data | claimUpdateData | False | - |
| errors | string[] | False | - |

## Events Published
tvs-cps-portal publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
tvs-cps-portal consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
tvs-cps-portal third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:firebase` | category other; matched `firebase` at `channel-partner-system/package.json:22` | Unknown |

## Rate Limits and SLAs
tvs-cps-portal: N/A — not determinable from code.

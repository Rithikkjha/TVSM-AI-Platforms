---
service_id: lms
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# lms — API Specification

## Authentication
No `[Authorize]` attribute and no authentication scheme registration found; `Startup.cs:120-121` calls `UseAuthentication()`/`UseAuthorization()` without a configured scheme, and CORS is configured at `leadLogs/Startup.cs:49,110`. Effective endpoint auth: none evidenced in code (gateway-level auth Unknown).
API contract: openapi-3 generated at runtime by swashbuckle (`/swagger/v1/swagger.json`; `leadLogs/Startup.cs:91`), no committed contract file.

## Endpoint Index
lms exposes 13 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Handler | Auth | Callers (service_id) |
|---|---|---|---|---|
| GET | `/` | `LeadAcquisitionController.GetLead` | none in code | - |
| GET | `/api/b2b/lead` | `WebhooksController.Get` | none in code | - |
| POST | `/api/b2b/lead` | `WebhooksController.Post` | none in code | - |
| POST | `/api/b2b/lead/update` | `LeadAcquisitionController.UpdateB2BLead` | none in code | - |
| POST | `/api/lead` | `LeadAcquisitionController.Lead` | none in code | `tvsm-marketplace-service`, `tvsmbe-location` |
| POST | `/api/lead/comms` | `LeadCommsController.comms` | none in code | - |
| POST | `/api/lead/update` | `LeadAcquisitionController.UpdateLead` | none in code | - |
| POST | `/api/leads/Count` | `LeadGetController.GetLeadsByFilter` | none in code | - |
| POST | `/api/leads/all` | `LeadGetController.GetallLeads` | none in code | - |
| POST | `/api/leads/filter` | `LeadGetController.GetReferrerLeads` | none in code | - |
| POST | `/api/leads/getDetails` | `LeadGetController.GetLeadsByFilter` | none in code | `tvsm-marketplace-service` |
| POST | `/api/leads/one-view` | `LeadGetController.LeadOnview` | none in code | `tvs-cps-backend` |
| POST | `/dealers` | `LeadAcquisitionController.GetDealers` | none in code | - |

## Endpoints
lms endpoint details (from inventory `inbound_http` + service.yaml `schemas`).

### GET /
Handler `LeadAcquisitionController.GetLead`; auth: none in code.
Request body: none.
Responses: 200, 422.

### GET /api/b2b/lead
Handler `WebhooksController.Get`; auth: none in code.
Request body: none.
Responses: 200, 400.

### POST /api/b2b/lead
Handler `WebhooksController.Post`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `data` | body | WebhookRequestModel | True |
Request body: `WebhookRequestModel` (fields in Schemas below).
Responses: 400.

### POST /api/b2b/lead/update
Handler `LeadAcquisitionController.UpdateB2BLead`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `updateLeadRequest` | body | LeadUpdateRequestModel | True |
| `countryCode` | header | string | False |
Request body: `LeadUpdateRequestModel` (fields in Schemas below).
Responses: 422.

### POST /api/lead
Handler `LeadAcquisitionController.Lead`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `leadRequestModel` | body | LeadRequestModel | True |
| `countryCode` | header | string | False |
Request body: `LeadRequestModel` (fields in Schemas below).
Responses: 422.

### POST /api/lead/comms
Handler `LeadCommsController.comms`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `commsRequestModel` | body | CommsRequestModel | True |
Request body: `CommsRequestModel` (fields in Schemas below).
Responses: 422.

### POST /api/lead/update
Handler `LeadAcquisitionController.UpdateLead`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `updateLeadRequest` | body | LeadUpdateRequestModel | True |
| `countryCode` | header | string | False |
Request body: `LeadUpdateRequestModel` (fields in Schemas below).
Responses: 422.

### POST /api/leads/Count
Handler `LeadGetController.GetLeadsByFilter`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `filterRequest` | body | LeadFilterRequestForAllLeads | True |
Request body: `LeadFilterRequestForAllLeads` (fields in Schemas below).
Responses: 200, 500.

### POST /api/leads/all
Handler `LeadGetController.GetallLeads`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `filterRequest` | body | LeadFilterRequestForAllLeads | True |
| `pagination` | query | PaginationModel | True |
Request body: `LeadFilterRequestForAllLeads` (fields in Schemas below).
Responses: 200, 500.

### POST /api/leads/filter
Handler `LeadGetController.GetReferrerLeads`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `filterRequest` | body | ReferrerLeadsRequest | True |
| `pagination` | query | PaginationModel | True |
Request body: `ReferrerLeadsRequest` (fields in Schemas below).
Responses: 200, 500.

### POST /api/leads/getDetails
Handler `LeadGetController.GetLeadsByFilter`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `filterRequest` | body | LeadsFilterRequestForSingleLead | True |
Request body: `LeadsFilterRequestForSingleLead` (fields in Schemas below).
Responses: 200, 500.

### POST /api/leads/one-view
Handler `LeadGetController.LeadOnview`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `leadOneViewRequest` | body | LeadOneViewRequest | True |
Request body: `LeadOneViewRequest` (fields in Schemas below).
Responses: 200, 500.

### POST /dealers
Handler `LeadAcquisitionController.GetDealers`; auth: none in code.

| Param | In | Type | Required |
|---|---|---|---|
| `mdpCriteria` | body | MdpCriteria | True |
Request body: `MdpCriteria` (fields in Schemas below).
Responses: 422.

## Outbound Calls
lms outbound HTTP calls (0 in service.yaml).

| Target (service_id) | Method | Path | Criticality | Client |
|---|---|---|---|---|
| N/A | - | - | - | no registry-resolved outbound HTTP; config-driven HTTP clients listed in HLC.md |

## Schemas
lms DTOs referenced by endpoints.

### WebhookRequestModel
Defined in `lms.config/Models/WebhookRequestModel.cs:11`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `entry` | Entry[] | False | - |
| `object` | string | False | - |

### LeadUpdateRequestModel
Defined in `lms.config/Models/LeadUpdateRequestModel.cs:135`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `customer_name` | string | False | - |
| `dealer_id` | string | False | - |
| `email` | string | False | - |
| `update_date` | string | False | - |
| `city` | string | False | - |
| `language_code` | string | False | - |
| `updated_by` | integer | True | - |
| `area` | string | False | - |
| `branch_id` | integer | False | - |
| `address_line1` | string | False | - |
| `customer_state` | string | False | - |
| `finance` | string | False | - |
| `pincode` | string | False | - |
| `finance_company` | string | False | - |
| `intent_for_purchase` | string | False | - |
| `lead_id` | string | False | - |
| `updated_date` | string | False | - |
| `status` | string | False | - |
| `events` | integer[] | False | - |
| `test_rides` | TestRide[] | False | - |
| `additional_details` | AdditionalDetails | False | - |
| `follow_up` | FollowUp | False | - |
| `enquiry_tag` | EnquiryTag[] | False | - |
| `interested_brand` | InterestedBrand[] | False | - |
| `referral_customer_details` | ReferralCustomerDetails | False | - |
| `finance_details` | FinanceDetails | False | - |
| `lead_invoice` | LeadInvoice | False | - |
| `extra_attributes` | ExtraAttribute[] | False | - |

### LeadRequestModel
Defined in `lms.config/Models/LeadRequestModel.cs:7`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `customer_name` | string | False | - |
| `dealer_id` | string | False | - |
| `mobile_number` | string | False | - |
| `email_id` | string | False | - |
| `enquiry_date` | string | False | - |
| `city` | string | False | - |
| `utm_source` | string | False | - |
| `utm_medium` | string | False | - |
| `utm_campaign` | string | False | - |
| `utm_copy` | string | False | - |
| `utm_ctr` | string | False | - |
| `utm_tg` | string | False | - |
| `gclid` | string | False | - |
| `language_code` | string | False | - |
| `source_id` | integer | True | - |
| `area` | string | False | - |
| `brand_code` | integer | True | - |
| `model_id` | string | False | - |
| `part_id` | string | False | - |
| `customer_voice` | string | False | - |
| `branch_id` | string | False | - |
| `address_line1` | string | False | - |
| `utm_term` | string | False | - |
| `utm_content` | string | False | - |
| `parm1` | string | False | - |
| `parm2` | string | False | - |
| `parm3` | string | False | - |
| `parm4` | string | False | - |
| `parm5` | string | False | - |
| `customer_state` | string | False | - |
| `finance` | string | False | - |
| `finance_company` | string | False | - |
| `pincode` | string | False | - |
| `intent_for_purchase` | string | False | - |
| `device` | string | False | - |
| `lead_category` | string | False | - |
| `possiblebrandname` | string | False | - |
| `dealername` | string | False | - |
| `test_rides` | TestRideModel[] | False | - |
| `interested_brand` | LeadBrandModel[] | False | - |
| `additional_details` | LeadAdditionalDetailsRequestModel | False | - |
| `follow_up` | LeadFollowUpRequestModel | False | - |
| `extra_attributes` | ExtraAttributeModel[] | False | - |
| `finance_details` | FinanceDetailsModel | False | - |
| `enquiry_tag` | EnquiryTagModel[] | False | - |
| `referral_customer_details` | ReferralCustomerDetailsModel | False | - |

### CommsRequestModel
Defined in `lms.config/Models/CommsRequestModel.cs:11`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `LeadId` | string | False | - |
| `Mobile` | string | False | - |
| `BrandCodes` | integer[] | False | - |
| `EventId` | integer | True | - |
| `Email` | string | False | - |
| `Response` | string | False | - |
| `ResponseDate` | datetime | True | - |
| `ActivityName` | string | False | - |
| `JourneyName` | string | False | - |
| `JbDefinitionId` | string | False | - |
| `JbActivityId` | string | False | - |
| `SubscriberKey` | string | False | - |
| `CampaignName` | string | False | - |
| `SourceId` | integer | True | - |
| `Link` | string | False | - |
| `Medium` | string | False | - |
| `MessageData` | string | False | - |
| `ContactKey` | string | False | - |
| `SendIdentifier` | string | False | - |
| `Category` | string | False | - |
| `SubCategory` | string | False | - |
| `Segment` | string | False | - |
| `CustomerJourney` | string | False | - |
| `ActivityType` | string | False | - |
| `ReplyText` | string | False | - |
| `EventSourceId` | string | False | - |

### LeadUpdateRequestModel
Defined in `lms.config/Models/LeadUpdateRequestModel.cs:135`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `customer_name` | string | False | - |
| `dealer_id` | string | False | - |
| `email` | string | False | - |
| `update_date` | string | False | - |
| `city` | string | False | - |
| `language_code` | string | False | - |
| `updated_by` | integer | True | - |
| `area` | string | False | - |
| `branch_id` | integer | False | - |
| `address_line1` | string | False | - |
| `customer_state` | string | False | - |
| `finance` | string | False | - |
| `pincode` | string | False | - |
| `finance_company` | string | False | - |
| `intent_for_purchase` | string | False | - |
| `lead_id` | string | False | - |
| `updated_date` | string | False | - |
| `status` | string | False | - |
| `events` | integer[] | False | - |
| `test_rides` | TestRide[] | False | - |
| `additional_details` | AdditionalDetails | False | - |
| `follow_up` | FollowUp | False | - |
| `enquiry_tag` | EnquiryTag[] | False | - |
| `interested_brand` | InterestedBrand[] | False | - |
| `referral_customer_details` | ReferralCustomerDetails | False | - |
| `finance_details` | FinanceDetails | False | - |
| `lead_invoice` | LeadInvoice | False | - |
| `extra_attributes` | ExtraAttribute[] | False | - |

### LeadFilterRequestForAllLeads
Defined in `lms.config/Models/LeadFilterRequest.cs:66`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `StartTime` | datetime | False | - |
| `EndTime` | datetime | False | - |
| `SourceIDs` | integer[] | False | - |
| `L1Source` | string[] | False | - |
| `MobileNumber` | string | False | - |
| `RequestId` | integer | False | - |
| `Status` | string | False | - |
| `IsActive` | boolean | False | - |

### LeadFilterRequestForAllLeads
Defined in `lms.config/Models/LeadFilterRequest.cs:66`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `StartTime` | datetime | False | - |
| `EndTime` | datetime | False | - |
| `SourceIDs` | integer[] | False | - |
| `L1Source` | string[] | False | - |
| `MobileNumber` | string | False | - |
| `RequestId` | integer | False | - |
| `Status` | string | False | - |
| `IsActive` | boolean | False | - |

### ReferrerLeadsRequest
Defined in `lms.config/Models/LeadFilterRequest.cs:45`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `StartTime` | datetime | False | - |
| `EndTime` | datetime | False | - |
| `SourceIDs` | integer[] | False | - |
| `IsActive` | boolean | False | - |
| `EmployeeId` | string | False | - |
| `dealerId` | string | False | - |
| `MobileNumber` | string | False | - |
| `Status` | string | False | - |
| `CscId` | string | False | - |

### LeadsFilterRequestForSingleLead
Defined in `lms.config/Models/LeadFilterRequest.cs:36`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `leadId` | string | False | - |
| `RequestId` | integer | False | - |

### LeadOneViewRequest
Defined in `lms.config/Models/LeadOneViewRequest.cs:10`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `leadId` | string | True | - |
| `sources` | integer[] | False | - |
| `events` | integer[] | False | - |
| `sort_by` | string | False | - |

### MdpCriteria
Defined in `lms.config/Models/MdpCriteria.cs:4`.

| Field | Type | Required | Validation |
|---|---|---|---|
| `DealerId` | string | False | - |
| `All` | integer | True | - |
| `TwoWheeler` | integer | False | - |
| `ThreeWheeler` | integer | False | - |
| `Iqube` | integer | False | - |
| `Rr310` | integer | False | - |
| `Rtr310` | integer | False | - |
| `Ronin` | integer | False | - |
| `Date` | string | False | - |
| `PageNumber` | integer | True | - |
| `PageSize` | integer | True | - |

Other extracted schemas (fields in service.yaml `schemas`): `AdditionalDetails`, `Change`, `EnquiryTag`, `EnquiryTagModel`, `Entry`, `ExtraAttribute`, `ExtraAttributeModel`, `FinanceDetails`, `FinanceDetailsModel`, `FollowUp`, `InterestedBrand`, `LeadAdditionalDetailsRequestModel`, `LeadBrandModel`, `LeadFollowUpRequestModel`, `LeadInvoice`, `ReferralCustomerDetails`, `ReferralCustomerDetailsModel`, `TestRide`, `TestRideModel`, `Value`.

## Events Published
lms publishes 1 messaging entit(y/ies).

| Topic / Queue | Type | Broker | name_from | Message types | Payload | Published from | Consumers |
|---|---|---|---|---|---|---|---|
| Unknown (`unknown`) | Unknown | azure-service-bus | `unknown` | see LLD State Machines | JSON string | `leadLogs/Services/LeadDispatchService.cs:21` | none resolved |

## Events Consumed
lms consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Broker | name_from | Handler | Producers | DLQ / retry |
|---|---|---|---|---|---|---|
| N/A | | | | no subscriber in code | | |

Phase-2 messaging items for lms:
- `messaging:leadLogs:publish:azure-service-bus:unknown` — evidence `leadLogs/Services/LeadDispatchService.cs:21`

## External Integrations
lms third-party systems detected in code.
N/A — no `external:` system matched by the registry.

## Rate Limits and SLAs
lms: N/A — not determinable from code.

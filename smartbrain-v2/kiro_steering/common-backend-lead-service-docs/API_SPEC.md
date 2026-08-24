# Lead Management System (LMS) — API Specification

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | Lead Management System (LMS) |
| Repos | TVSM-DMS/lms, TVSM-DMS/lms_process, TVSM-DMS/lms_ems, TVSM-DMS/lms_crm |
| Branch | ls_uat_ib |
| Team | App Engineering — Lead Service |
| Tech Lead | Arun Kumar Reddy (@arunkumar.reddy) |
| Deployment | Azure App Service |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| App Engineering Lead | Suman Kumar | Suman.Kumar@tvsmotor.com |
| Tech Lead | Arun Kumar Reddy | Arunkumar.Reddy@tvsd.ai |
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com |
| DevOps | Koyel Nath | Koyel.Nath@tvsmotor.com |
| Backend Dev | Nikhil Reddy | nikhil.reddy@tvsmotor.com |
| Backend Dev | Sriniketh | Sriniketh@tvsmotor.com |

---

## 1. Authentication

| Aspect | Detail |
|--------|--------|
| Mechanism | Static Bearer token (conditional) |
| Header | `Authorization: Bearer <TOKEN>` |
| Token source | `TOKEN` environment variable |
| Handler | `StaticTokenAuthenticationHandler` |
| Toggle | `IS_TOKEN_REQUIRED` env var ("true"/"false") |
| Exceptions | Facebook webhook endpoints (`/api/b2b/lead`) do NOT require auth |

### Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Conditional | `Bearer <TOKEN>` — required when `IS_TOKEN_REQUIRED=true` |
| countryCode | Yes | Country code (e.g., "IN", "LK", "NP", "BD"). Processed by `CountryCodeMiddleWare` to set `CountryContext`. Defaults to `DEFAULT_COUNTRY` env var if absent. |
| Content-Type | Yes | `application/json` |

---

## 2. All Endpoints (lms API — `leadLogs` project)

| # | Method | Route | Controller | Auth | Purpose |
|---|--------|-------|------------|------|---------|
| 1 | GET | `/` | LeadAcquisitionController | ✅ | Health check — returns version string |
| 2 | POST | `/dealers` | LeadAcquisitionController | ✅ | Get dealers by MDP criteria |
| 3 | POST | `/api/lead` | LeadAcquisitionController | ✅ | **Create a new lead** |
| 4 | POST | `/api/lead/update` | LeadAcquisitionController | ✅ | **Update an existing lead** |
| 5 | POST | `/api/b2b/lead/update` | LeadAcquisitionController | ✅ | Update B2B lead (same logic as #4) |
| 6 | POST | `/api/lead/comms` | LeadCommsController | ✅ | Process communication status |
| 7 | POST | `/api/leads/Count` | LeadGetController | ✅ | Get lead count by filter |
| 8 | POST | `/api/leads/getDetails` | LeadGetController | ✅ | Get single lead details |
| 9 | POST | `/api/leads/all` | LeadGetController | ✅ | Get all leads (paginated) |
| 10 | POST | `/api/leads/filter` | LeadGetController | ✅ | Get referrer leads (paginated) |
| 11 | POST | `/api/leads/one-view` | LeadGetController | ✅ | Get lead one-view events |
| 12 | GET | `/api/b2b/lead` | WebhooksController | ❌ | Facebook webhook verification |
| 13 | POST | `/api/b2b/lead` | WebhooksController | ❌ | Facebook webhook lead ingestion |

> **Note:** All routes are prefixed with the `AppPrefix` env var value at deployment (e.g., `/{prefix}/api/lead`).

---

## 3. POST /api/lead — Create Lead

### Flow
1. `LeadAcquisitionController.Post()` → `LeadLogService.ProcessLead()`
2. `LeadValidator.Validate()` — validates request fields
3. `ProcessDuplicateLeadService` — deduplication check
4. If valid + not duplicate → `ProcessValidLeadService.ProcessValidLead()`
5. Lead persisted to DB via `LeadRepository`
6. `LeadDispatchService.Dispatch()` — publishes to Service Bus topic

### Request Body (`LeadRequestModel`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| customer_name | string | Yes | Customer full name |
| mobile_number | string | Yes | Customer mobile number |
| email_id | string | No | Customer email |
| enquiry_date | string | No | Enquiry date (yyyy-MM-dd HH:mm:ss.fff) |
| source_id | int32 | Yes | Lead source identifier |
| brand_code | int32 | Yes | Vehicle brand code |
| model_id | string | No | Vehicle model ID |
| part_id | string | No | Vehicle variant/part ID |
| dealer_id | string | No | Dealer ID (if pre-assigned) |
| branch_id | string | No | Branch ID |
| city | string | No | Customer city |
| area | string | No | Customer area / pincode |
| pincode | string | No | Postal code |
| customer_state | string | No | Customer state |
| address_line1 | string | No | Customer address |
| utm_source | string | No | Marketing UTM source |
| utm_medium | string | No | Marketing UTM medium |
| utm_campaign | string | No | Marketing UTM campaign |
| utm_term | string | No | Marketing UTM term |
| utm_content | string | No | Marketing UTM content |
| gclid | string | No | Google Click ID |
| language_code | string | No | Language preference |
| customer_voice | string | No | Customer remarks |
| finance | string | No | Finance interest flag |
| finance_company | string | No | Preferred finance company |
| intent_for_purchase | string | No | Purchase intent |
| device | string | No | Customer device |
| lead_category | string | No | Lead category |
| possiblebrandname | string | No | Possible brand name |
| dealername | string | No | Dealer name |
| parm1–parm5 | string | No | Custom parameters |
| test_rides | TestRideModel[] | No | Array of test ride requests |
| interested_brand | LeadBrandModel[] | No | Array of interested brands |
| additional_details | object | No | Additional lead details (age_group, gender, mode_of_purchase, etc.) |
| follow_up | object | No | Follow-up details (disposition, next_follow_up_date, etc.) |
| extra_attributes | ExtraAttributeModel[] | No | Custom key-value attributes |
| finance_details | object | No | Finance application details |
| enquiry_tag | EnquiryTagModel[] | No | Enquiry tags |
| referral_customer_details | object | No | Referral customer info |

### Nested: TestRideModel

| Field | Type | Description |
|-------|------|-------------|
| brand_code | int32 | Brand code for test ride |
| model_id | string | Model ID |
| part_id | string | Part/variant ID |
| status | string | Test ride status |
| ride_type | string | Type of ride |
| ride_scheduled_date | string | Scheduled date |
| comments | string | Comments |
| address_line1/2 | string | Address |
| state | string | State |
| city | string | City |
| pin_code | string | PIN code |
| reason_type | string | Reason type |
| reason_comment | string | Reason comment |
| feedback | string | Feedback |
| test_ride_id | string | External test ride ID |
| test_ride_slot | string | Time slot |
| test_ride_source | string | Source |
| vehicle_name | string | Vehicle name |

### Nested: AdditionalDetails

| Field | Type | Description |
|-------|------|-------------|
| age_group | string | Customer age group |
| gender | string | Gender |
| alternative_mobile | string | Alternate mobile |
| mode_of_purchase | string | Mode of purchase |
| vehicle_exchanged | string | Exchange vehicle |
| has_previous_vehicle | int32 | Has previous vehicle flag |
| existing_vehicle_company | string | Existing vehicle company |
| existing_vehicle_model_id | string | Existing vehicle model |
| first_walk_in_date | string | First walk-in date |
| enquiry_type | string | Enquiry type |
| customer_type | string | Customer type |
| marketing_consent | int32 | Marketing consent (0/1) |
| user_consent | int32 | User consent (0/1) |
| consent_date | string | Consent date |
| client_id | string | Client ID |
| l2_source | string | L2 source |
| event_id | string | Event ID |
| source_of_awareness | string | Source of awareness |
| interested_in_exchange | string | Exchange interest |
| event_name | string | Event name |
| vehicle_user | string | Vehicle user |
| permit_status | string | Permit status |
| outdoor_event_id | string | Outdoor event ID |
| expected_delivery_date | string | Expected delivery |
| location | string | Location |
| user_id | string | User ID |
| user_type | string | User type |
| customer_area_id | int64 | Customer area ID |
| enquiry_number | int64 | Enquiry number |
| available_for_down_payment | string | Down payment availability |

### Success Response (200)

```json
{
  "message": "Success",
  "requestId": 12345,
  "leadId": "ENQ12345",
  "status": 200
}
```

---

## 4. POST /api/lead/update — Update Lead

### Flow
1. `LeadAcquisitionController.PostUpdate()` → `LeadLogService.ProcessUpdatedLead()`
2. `UpdateValidator.Validate()` — validates update request
3. `UpdateLeadService.ProcessUpdatedLead()` — processes update + dealer transfer events
4. `LeadDispatchService.Dispatch()` — publishes update event to Service Bus

### Request Body (`LeadUpdateRequestModel`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | string | Yes | Internet enquiry ID of the lead to update |
| events | int32[] | No | Event IDs to trigger (e.g., [2, 16]) |
| updated_by | int32 | No | User who updated |
| status | string | No | New lead status |
| dealer_id | string | No | New dealer ID (triggers transfer) |
| branch_id | int32 | No | New branch ID |
| customer_name | string | No | Updated name |
| email | string | No | Updated email |
| city | string | No | Updated city |
| area | string | No | Updated area |
| pincode | string | No | Updated pincode |
| customer_state | string | No | Updated state |
| address_line1 | string | No | Updated address |
| language_code | string | No | Updated language |
| finance | string | No | Finance interest |
| finance_company | string | No | Finance company |
| intent_for_purchase | string | No | Purchase intent |
| update_date | string | No | Update timestamp |
| updated_date | string | No | Updated date |
| test_rides | TestRide[] | No | Test ride updates |
| additional_details | object | No | Additional details update |
| follow_up | object | No | Follow-up update |
| enquiry_tag | EnquiryTag[] | No | Enquiry tag updates |
| interested_brand | InterestedBrand[] | No | Brand interest updates |
| referral_customer_details | object | No | Referral details update |
| finance_details | object | No | Finance details update |
| lead_invoice | LeadInvoice | No | Invoice details |
| extra_attributes | ExtraAttribute[] | No | Extra attributes update |

### Nested: LeadInvoice

| Field | Type | Description |
|-------|------|-------------|
| invoice_id | string | Invoice ID |
| invoice_generated_date | string | Invoice generation date |
| brand_code | int32 | Brand code |
| model_id | string | Model ID |
| part_id | string | Part ID |
| vin_number | string | VIN number |

---

## 5. Other Endpoints

### POST /dealers (`MdpCriteria`)

| Field | Type | Description |
|-------|------|-------------|
| dealerId | string | Dealer ID filter |
| all | int32 | Get all dealers flag |
| twoWheeler | int32 | 2W dealer filter |
| threeWheeler | int32 | 3W dealer filter |
| iqube | int32 | iQube dealer filter |
| rr310 | int32 | RR310 dealer filter |
| rtr310 | int32 | RTR310 dealer filter |
| ronin | int32 | Ronin dealer filter |
| date | string | Date filter |
| pageNumber | int32 | Page number |
| pageSize | int32 | Page size |

### POST /api/lead/comms (`CommsRequestModel`)

| Field | Type | Description |
|-------|------|-------------|
| leadId | string | Lead ID |
| mobile | string | Mobile number |
| brandCodes | int32[] | Brand codes |
| eventId | int32 | Event ID |
| email | string | Email |
| response | string | Response status |
| responseDate | datetime | Response timestamp |
| activityName | string | Activity name |
| journeyName | string | Journey name |
| jbDefinitionId | string | Journey builder definition ID |
| jbActivityId | string | Journey builder activity ID |
| subscriberKey | string | Subscriber key |
| campaignName | string | Campaign name |
| sourceId | int32 | Source ID |
| link | string | Link |
| medium | string | Medium |
| messageData | string | Message data |
| contactKey | string | Contact key |
| sendIdentifier | string | Send identifier |
| category | string | Category |
| subCategory | string | Sub-category |
| segment | string | Segment |
| customerJourney | string | Customer journey |
| activityType | string | Activity type |
| replyText | string | Reply text |
| eventSourceId | string | Event source ID |

### POST /api/leads/Count & /api/leads/all (`LeadFilterRequestForAllLeads`)

| Field | Type | Description |
|-------|------|-------------|
| startTime | datetime | Start of date range |
| endTime | datetime | End of date range |
| sourceIDs | int32[] | Filter by source IDs |
| l1Source | string[] | Filter by L1 sources |
| mobileNumber | string | Filter by mobile |
| requestId | int64 | Filter by request ID |
| status | string | Filter by status |
| isActive | boolean | Filter by active flag |

**Query params for /api/leads/all:** `PageNumber` (int32), `PageSize` (int32)

### POST /api/leads/getDetails (`LeadsFilterRequestForSingleLead`)

| Field | Type | Description |
|-------|------|-------------|
| leadId | string | Internet enquiry ID |
| requestId | int64 | Request ID |

### POST /api/leads/filter (`ReferrerLeadsRequest`)

| Field | Type | Description |
|-------|------|-------------|
| startTime | datetime | Start date |
| endTime | datetime | End date |
| sourceIDs | int32[] | Source IDs |
| isActive | boolean | Active flag |
| employeeId | string | Employee ID |
| dealerId | string | Dealer ID |
| mobileNumber | string | Mobile number |
| status | string | Status |
| cscId | string | CSC ID |

**Query params:** `PageNumber` (int32), `PageSize` (int32)

### POST /api/leads/one-view (`LeadOneViewRequest`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| leadId | string | Yes | Lead ID (internet_enquiry_id) |
| sources | int32[] | No | Filter by sources |
| events | int32[] | No | Filter by events |
| sort_by | string | No | Sort field |

### GET /api/b2b/lead (Facebook Verification)
Facebook sends query params. Returns challenge value.

### POST /api/b2b/lead (`WebhookRequestModel`)

| Field | Type | Description |
|-------|------|-------------|
| object | string | Webhook object type |
| entry | Entry[] | Array of webhook entries |

**Entry:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Page ID |
| time | int32 | Timestamp |
| changes | Change[] | Array of changes |

**Change → Value:**
| Field | Type | Description |
|-------|------|-------------|
| ad_id | string | Ad ID |
| form_id | string | Form ID |
| leadgen_id | string | Leadgen ID |
| created_time | int32 | Creation timestamp |
| page_id | string | Page ID |
| adgroup_id | string | Ad group ID |

---

## 6. Response Format

```json
{
  "message": "Success",
  "requestId": 12345,
  "leadId": "ENQ12345",
  "status": 200
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Success (or duplicate lead with existing ID) |
| 400 | Validation error |
| 401 | Authentication failed (invalid/missing token) |
| 422 | Unprocessable entity (server exception) |
| 500 | Internal server error |

---

## 7. Inbound — Who Calls Me

| Method | Endpoint | Called By |
|--------|----------|-----------|
| POST | /api/lead | TVS Website, Aggregators, B2B Partners, EV Portal |
| POST | /api/lead/update | Dealer Portals, CRM Systems, EMS |
| POST | /api/b2b/lead/update | B2B Partners |
| POST | /api/lead/comms | Comms Platform (SMS/WhatsApp providers) |
| POST | /api/leads/* | Admin Portal, BI Reports, Internal Tools |
| GET/POST | /api/b2b/lead | Facebook Platform |
| POST | /dealers | Internal services needing dealer data |

---

## 8. Outbound — Who I Call

| Target | Method | Purpose | Called By Service |
|--------|--------|---------|-------------------|
| Azure Service Bus (TOPIC_NAME) | PUBLISH | Emit lead events (LEAD_PROCESS, UPDATE_LEAD_PROCESS) | lms API |
| Latlong Ronin API | GET | Dealer allocation for Ronin brand | lms API (LatlongService) |
| Latlong RTR API | GET | Dealer allocation for RTR brand | lms API (LatlongService) |
| Latlong EV API | GET | Dealer allocation for EV brand | lms API (LatlongService) |
| Latlong 3W API | GET | Dealer allocation for 3W brand | lms API (LatlongService) |
| Latlong Common API | GET | Dealer allocation for other brands | lms API (LatlongService) |
| Latlong Token API | POST | OAuth2 client_credentials token for latlong | lms API (ApiExchangeService) |
| Facebook Graph API | GET | Retrieve lead ad form data | lms API (WebhookService) |

---

## 9. Service Bus Message Contract

### Message Published by lms API

```json
// Message body = serialized lead/update model
```

**Message Properties:**
| Property | Description | Example |
|----------|-------------|---------|
| EVENT_TYPE | Event type identifier | "LEAD_PROCESS", "UPDATE_LEAD_PROCESS", "PARTIAL_LEAD_PROCESS" |
| EVENT_SOURCE | Source service identifier | configured via `EVENT_SOURCE_VALUE` |
| EVENT_TARGET | Target service/subscription | configured via `EVENT_TARGET_VALUE` |
| CREATED_AT | Timestamp | ISO 8601 |
| VERSION | Message version | "1.0" |

---

## 10. Configuration (Environment Variables)

| Variable | Required | Description |
|----------|----------|-------------|
| TOKEN | Yes | Static authentication token |
| IS_TOKEN_REQUIRED | Yes | Enable/disable auth ("true"/"false") |
| AppPrefix | Yes | Route prefix (e.g., "cin", "srilanka") |
| DEFAULT_COUNTRY | Yes | Default country code if header absent |
| DOM_DB_CONN | Yes | India database connection string |
| SRILANKA_DB_CONN | Yes | Sri Lanka database connection |
| SERVICE_BUS_CONNECTION_STRING | Yes | Azure Service Bus connection |
| TOPIC_NAME | Yes | Service Bus topic name |
| EVENT_TARGET_VALUE | Yes | Target value for published messages |
| EVENT_SOURCE_VALUE | Yes | Source identifier for messages |
| LEAD_PROCESS | Yes | Event type string for new leads |
| UPDATE_LEAD_PROCESS | Yes | Event type string for updates |
| LATLONG_TOKEN_URL | Yes | OAuth2 token endpoint for latlong |
| LATLONG_RONIN_API_URL | Yes | Ronin dealer allocation URL |
| LATLONG_RTR_API_URL | Yes | RTR dealer allocation URL |
| LATLONG_COMMON_API_URL | Yes | Common dealer allocation URL |
| LATLONG_3W_API_URL | Yes | 3W dealer allocation URL |
| LATLONG_EV_API_URL | Yes | EV dealer allocation URL |
| OLD_LMS_URL | No | Legacy LMS endpoint (disabled) |

---

*Document Version: 2.0 | Last Updated: July 2026*

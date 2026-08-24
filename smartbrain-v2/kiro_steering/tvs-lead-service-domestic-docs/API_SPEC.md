# TVSM Lead Service (LS) — API Specification

**Document Version:** 2.0  
**Date:** July 2026  
**Platform:** TVS Motor Lead Service  
**Audience:** Integration Partners · Frontend Developers · Vendor Teams · QA Engineers

---

## Table of Contents

1. [Service Identity](#1-service-identity)
2. [Inbound — API Endpoints](#2-inbound--api-endpoints)
3. [Outbound — Who This Service Calls](#3-outbound--who-this-service-calls)
4. [Events & Messaging](#4-events--messaging)
5. [Data Storage](#5-data-storage)
6. [Authentication Requirements](#6-authentication-requirements)
7. [Request Payloads](#7-request-payloads)
8. [Response Payloads](#8-response-payloads)
9. [Error Responses](#9-error-responses)
10. [Validation Rules](#10-validation-rules)
11. [Rate Limits](#11-rate-limits)
12. [External API Dependencies](#12-external-api-dependencies)
13. [Sample Requests and Responses](#13-sample-requests-and-responses)

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | Lead Acquisition Service (ls-acquisition) |
| Repo | `lms` (Azure DevOps) |
| Team | Common Backend Services |
| Tech Lead | Arun Kumar |
| Deployment | Docker containers on AKS (Azure Kubernetes Service) |
| Base URL (prod) | `https://ls-acquisition.azurewebsites.net` |

### Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com |
| Tech Lead | Arun Kumar | Arunkumar.Reddy@tvsd.ai |
| Dev Team | Common Backend- Lead Service | ls.support@tvsmotor.com |

---

## 2. Inbound — API Endpoints

The LMS platform exposes its public API through the **Lead Acquisition Service** (`lms`). All other services (lms_process, lms_ems, lms_crm, lms_tvs_credit) are internal consumers with no public HTTP endpoints — they communicate only via Azure Service Bus.

### 2.1 My API Endpoints (Inbound)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/` | None | Health check — returns service version | Load balancer, Monitoring |
| POST | `/api/lead` | APIKey header | Submit a new lead | TVS Website, Aggregators (BikeWale, BikeDekho, 91Wheels), Mobile App, Partners |
| POST | `/api/lead/update` | APIKey header | Update an existing lead (status, dealer transfer, follow-up, test ride, invoice) | EMS, Internal systems, Partner portals |
| POST | `/api/b2b/lead/update` | APIKey header | B2B lead update (functionally identical to above) | B2B partner systems |
| GET | `/api/b2b/lead` | None (verify_token) | Facebook webhook verification handshake | Facebook / Meta |
| POST | `/api/b2b/lead` | None (platform-signed) | Webhook intake — Facebook Lead Ads and Google Ads lead forms | Facebook / Meta, Google Ads |
| POST | `/api/lead/comms` | None (network-level) | Record communication events (SMS, email, WhatsApp) | Marketing automation / Comms service |
| POST | `/dealers` | None (network-level) | Search dealers by criteria (brand flags, location) | Internal tools, Admin portal |
| POST | `/api/leads/Count` | None (network-level) | Lead count with filters | Internal dashboards |
| POST | `/api/leads/getDetails` | None (network-level) | Full details of a single lead | Internal dashboards, CRM tools |
| POST | `/api/leads/all` | None (network-level) | Paginated lead list with filters | Internal dashboards |
| POST | `/api/leads/filter` | None (network-level) | Referral-specific lead list | Referral management portal |
| POST | `/api/leads/one-view` | None (network-level) | Full event timeline for a lead | CRM, Support tools |
| POST | `/api/brand` | None (network-level) | Create a new brand | Admin portal |
| GET | `/api/brand/all` | None (network-level) | Get all brands | Admin portal |
| GET | `/api/brand/{brandCode}` | None (network-level) | Get brand by code | Admin portal |
| PUT | `/api/brand/{brandCode}` | None (network-level) | Update a brand | Admin portal |
| POST | `/api/model` | None (network-level) | Create a new model/part | Admin portal |
| GET | `/api/model/all` | None (network-level) | Get all models/parts | Admin portal |
| GET | `/api/model/{id}` | None (network-level) | Get model/part by ID | Admin portal |
| PUT | `/api/model/{id}` | None (network-level) | Update a model/part | Admin portal |
| POST | `/api/lead-source` | None (network-level) | Create a new lead source | Admin portal |
| GET | `/api/lead-source/all` | None (network-level) | Get all lead sources | Admin portal |
| GET | `/api/lead-source/{id}` | None (network-level) | Get lead source by ID | Admin portal |
| PUT | `/api/lead-source/{id}` | None (network-level) | Update a lead source | Admin portal |
| POST | `/api/lead-flow` | None (network-level) | Create lead flow configuration | Admin portal |
| GET | `/api/lead-flow/all` | None (network-level) | Get all lead flow configurations | Admin portal |
| GET | `/api/lead-flow/{id}` | None (network-level) | Get lead flow config by ID | Admin portal |
| PUT | `/api/lead-flow/{id}` | None (network-level) | Update lead flow configuration | Admin portal |
| POST | `/api/event-configurator` | None (network-level) | Create event configurator | Admin portal |
| GET | `/api/event-configurator/all` | None (network-level) | Get all event configurators | Admin portal |
| GET | `/api/event-configurator/{id}` | None (network-level) | Get event configurator by ID | Admin portal |
| GET | `/api/event-configurator/name/{eventName}` | None (network-level) | Get event configurator by name | Admin portal |
| PUT | `/api/event-configurator/{id}` | None (network-level) | Update event configurator | Admin portal |

### 2.2 Base URL Pattern

```
https://{environment-host}:{port}/{endpoint}

Examples:
  Development: https://ls-acquisition-dev.azurewebsites.net/api/lead
  UAT:         https://ls-acquisition-uat.azurewebsites.net/api/lead
  Production:  https://ls-acquisition.azurewebsites.net/api/lead
```

---

## 3. Outbound — Who This Service Calls

### 3.1 Lead Acquisition Service (`lms`)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| Azure Service Bus | PUBLISH | topic: `lms_topic` | Dispatch validated leads for downstream processing (EVENT_TYPE: LEAD_PROCESS, UPDATE_LEAD_PROCESS) |
| Facebook Graph API | GET | `https://graph.facebook.com/{version}/{leadgen_id}` | Fetch lead form data from Meta/Facebook Lead Ads |
| Latlong.in | GET | Per-brand dealer discovery URL | Geo-based dealer allocation by customer pincode |
| Azure Key Vault | GET | Vault secrets | Retrieve application secrets at startup |

### 3.2 Process Lead Service (`lms_process`)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| Azure Service Bus | PUBLISH | topic: `lms_topic` (EMS, CRM, FINANCE subscriptions) | Fan-out leads to downstream services |
| LCE API | POST | LCE classification endpoint | Score lead with retail probability |
| Latlong.in | GET | Per-brand dealer discovery URL | Geo-based dealer allocation |
| Legacy LMS | POST | `OLD_LMS_URL` | Backward-compatible callback (fire and forget) |

### 3.3 EMS Service (`lms_ems`)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| TVS EMS API | POST | HO / Aggregator / EV endpoints | Push leads to dealer-facing EMS system |
| Azure Service Bus | PUBLISH | topic: `lms_topic` (PROCESS subscription) | Dealer retry / re-allocation requests |
| Azure Service Bus | SCHEDULE | topic: `lms_topic` (EMS subscription) | 30-minute delayed retry on failure |

### 3.4 CRM Service (`lms_crm`)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| Salesforce CDP | POST | CDP REST endpoint | Create/update customer 360 profile |
| Salesforce Service Cloud (CCP) | POST | CCP REST endpoint | Create/update Lead records, upsert Test Rides |
| Voice AI API | POST | Voice AI endpoint | Automated outbound voice calls |
| Dialer API | POST | Dialer endpoint | Submit lead to call centre queue |
| CMP (Push Notifications) | POST | CMP endpoint | Trigger push notifications to TVS app |
| Legacy LMS | POST | `OLD_LMS_URL` | Backward-compatible callback |
| Azure Service Bus | SCHEDULE | topic: `lms_topic` (CRM subscription) | Schedule after-hours Voice AI calls for next day |

### 3.5 TVS Credit Service (`lms_tvs_credit`)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| TVS Credit API | POST | TVS Credit lead push endpoint | Submit finance-eligible leads |
| Salesforce Service Cloud (CCP) | POST | CCP REST endpoint | Push EV leads to Salesforce |

---

## 4. Events & Messaging

### 4.1 Topics This Platform Publishes To

| Topic/Queue | Events | Published By |
|-------------|--------|--------------|
| `lms_topic` (main) | `LEAD_PROCESS`, `UPDATE_LEAD_PROCESS`, `PARTIAL_LEAD_PROCESS` | lms (Lead Acquisition) |
| `lms_topic` (fan-out) | `CREATE`, `LEAD_UPDATE_EVENT`, `THRESHOLD_LEAD_EVENT`, `VOICEAI_SCHEDULED` | lms_process, lms_ems, lms_crm |

### 4.2 Subscriptions This Platform Consumes From

| Topic/Queue | Subscription | Events Consumed | Consumer Service |
|-------------|-------------|-----------------|-----------------|
| `lms_topic` | PROCESS subscription | `LEAD_PROCESS`, `UPDATE_LEAD_PROCESS`, `RETRY_PROCESS` | lms_process |
| `lms_topic` | EMS subscription | Lead push events, threshold events | lms_ems |
| `lms_topic` | CRM subscription | Lead push events, update events, `VOICEAI_SCHEDULED` | lms_crm |
| `lms_topic` | FINANCE subscription | Finance and EV CRM events | lms_tvs_credit |
| MDP Service Bus (separate) | MDP subscription | Dealer create/update/migration events | lms_process |
| Booking Service Bus (separate) | Booking subscription | Booking lifecycle events (session-based) | lms_ems |

---

## 5. Data Storage

| Store | Type | Purpose | Used By |
|-------|------|---------|---------|
| Azure SQL Server (LMS Database) | MSSQL | Primary data store — leads, dealers, brands, sources, logs, configurations | All 5 services (shared) |
| Azure Redis Cache | Cache | In-memory caching for brands, models, lead sources, lead flow configs | lms (Lead Acquisition) |
| Azure Key Vault | Secrets | Connection strings, API keys, client secrets | lms (Lead Acquisition) |

---

## 6. Authentication Requirements

### 6.1 API Key Authentication

The Lead Acquisition Service uses a static API key for authenticating incoming requests from integration partners.

| Header | Value | Required |
|---|---|---|
| `APIKey` | Configured per environment (provided to partners during onboarding) | Yes — for lead submission and update endpoints |

Requests without a valid API key will be rejected.

### 6.2 Country Code Header

| Header | Value | Required |
|---|---|---|
| `countryCode` | ISO country code (e.g., `IN` for India, `LK` for Sri Lanka) | Conditional — required only when the lead source's flow configuration has `IsCountryCodeMandatory = true` |

### 6.3 Webhook Verification (Facebook)

The `GET /api/b2b/lead` endpoint is called by Facebook during webhook registration. It expects:

| Query Parameter | Description |
|---|---|
| `hub.mode` | Always "subscribe" |
| `hub.challenge` | A random string that must be returned as-is in the response body |
| `hub.verify_token` | Must match the configured verification token (`lms`) |

### 6.4 No Authentication Required

The following endpoints do not require API key authentication:
- `GET /` — Health check
- `GET /api/b2b/lead` — Facebook webhook verification
- `POST /api/b2b/lead` — Webhook intake (authenticated by the ad platform's own signature/token mechanisms)

### 6.5 Internal Reporting Endpoints

The reporting endpoints (`/api/leads/all`, `/api/leads/Count`, etc.) are intended for internal dashboards and tools. Access is controlled at the network level (internal VNet / API gateway rules) rather than by API key in the request.

---

## 7. Request Payloads

### 7.1 POST /api/lead — New Lead Submission

**When to use:** Every time a customer expresses interest in a TVS vehicle — from a website form, mobile app, aggregator integration, or partner system.

```json
{
  "customer_name": "Rajesh Kumar",
  "mobile_number": "9876543210",
  "email_id": "rajesh@example.com",
  "source_id": 1,
  "brand_code": 5,
  "model_id": "IQUBE",
  "part_id": "IQUBE_ST",
  "dealer_id": "12345",
  "branch_id": "1",
  "area": "600001",
  "city": "Chennai",
  "customer_state": "Tamil Nadu",
  "pincode": "600001",
  "enquiry_date": "2026-06-22 10:30:00.000",
  "finance": "true",
  "finance_company": "TVS Credit",
  "intent_for_purchase": "Within 1 Month",
  "device": "mobile",
  "language_code": "EN",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "iqube_chennai",
  "utm_term": "electric_scooter",
  "utm_content": "ad_variant_1",
  "gclid": "CjwKCAjw...",
  "parm1": "custom_param_1",
  "parm2": "custom_param_2",
  "parm3": "custom_param_3",
  "parm4": "custom_param_4",
  "parm5": "custom_param_5",
  "address_line1": "123 Anna Nagar",
  "customer_voice": "Interested in iQube for daily commute",
  "lead_category": "hot",
  "interested_brand": [
    {
      "brand_code": 5,
      "model_id": "IQUBE",
      "part_id": "IQUBE_ST"
    },
    {
      "brand_code": 5,
      "model_id": "IQUBE",
      "part_id": "IQUBE_S"
    }
  ],
  "test_rides": [
    {
      "brand_code": 5,
      "model_id": "IQUBE",
      "part_id": "IQUBE_ST",
      "ride_type": "dealer",
      "ride_scheduled_date": "2026-06-25 14:00:00.000",
      "comments": "Prefer afternoon slot"
    }
  ],
  "follow_up": {
    "next_follow_up_date": "2026-06-23 10:00:00.000",
    "next_follow_up_time": "2026-06-23 10:00:00.000"
  },
  "additional_details": {
    "alternative_mobile": "9876543211",
    "consent_date": "2026-06-22 10:30:00.000",
    "marketing_consent": 1,
    "user_consent": 1
  },
  "extra_attributes": [
    {
      "attribute_name": "preferred_color",
      "attribute_description": "Customer's preferred color",
      "attribute_value": "Titanium Grey"
    }
  ],
  "finance_details": {
    "financier_name": "TVS Credit",
    "loan_amount": "80000",
    "down_payment": "20000",
    "tenure": "24",
    "emi": "3800",
    "status": 1
  },
  "enquiry_tag": [
    {
      "tag_name": "high_intent",
      "description": "Customer confirmed purchase timeline",
      "source": "website",
      "status": 1
    }
  ],
  "referral_customer_details": {
    "referral_customer_type": "employee",
    "referral_customer_name": "Suresh M",
    "referral_customer_mobile_number": "9876543299",
    "employee_id": "TVS001234"
  }
}
```

**Field Reference:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_name` | string | Conditional (per source config) | Customer's full name. Max 100 characters. |
| `mobile_number` | string | Conditional (per source config) | 10-digit Indian mobile number (no country prefix) |
| `email_id` | string | No | Customer email address |
| `source_id` | int | **Yes** | Identifies the lead source (website=1, aggregator=various). Must exist in `lead_sources` table. |
| `brand_code` | int | Conditional | Vehicle brand identifier (e.g., 5=iQube). Must exist in `brand_master` table. |
| `model_id` | string | Conditional | Vehicle model identifier |
| `part_id` | string | Conditional | Vehicle variant/part identifier |
| `dealer_id` | string | Conditional | TVS dealer SAP code. If not provided, system auto-assigns via Latlong geo-lookup. |
| `branch_id` | string | No | Dealer branch number (defaults to "1" if not provided) |
| `area` | string | Conditional | Customer's 6-digit pincode (used for geo-dealer allocation) |
| `city` | string | No | Customer's city name |
| `customer_state` | string | No | Customer's state name |
| `pincode` | string | No | Dealer's pincode (different from `area` which is customer pincode) |
| `enquiry_date` | string | **Yes** | When the customer expressed interest. Format: `yyyy-MM-dd HH:mm:ss.fff` (UTC). Cannot be in the future. |
| `finance` | string | No | "true" if customer wants financing |
| `intent_for_purchase` | string | No | Purchase timeline (e.g., "Within 1 Month") |
| `utm_source/medium/campaign/term/content` | string | No | Marketing attribution fields |
| `gclid` | string | No | Google Click ID for attribution |
| `interested_brand[]` | array | No | Additional brand/model/variant combinations the customer is interested in |
| `test_rides[]` | array | No | Test ride booking requests |
| `follow_up` | object | No | Next follow-up scheduling |
| `additional_details` | object | No | Extended customer attributes |
| `extra_attributes[]` | array | No | Dynamic key-value pairs for source-specific fields |
| `finance_details` | object | No | Finance application details |
| `enquiry_tag[]` | array | No | Tags/labels for categorization |
| `referral_customer_details` | object | No | Referral program information |

---

### 7.2 POST /api/lead/update — Lead Update

**When to use:** When a lead's status changes — dealer follow-up completed, test ride booked, stage progression, invoice generated, dealer transfer.

```json
{
  "lead_id": "IEQ000012345",
  "updated_by": 1,
  "events": [1, 5],
  "status": "test_ride_booked",
  "customer_name": "Rajesh Kumar",
  "dealer_id": "12345",
  "branch_id": 1,
  "city": "Chennai",
  "customer_state": "Tamil Nadu",
  "area": "600001",
  "pincode": "600001",
  "finance": "true",
  "finance_company": "TVS Credit",
  "intent_for_purchase": "This Week",
  "test_rides": [
    {
      "brand_code": 5,
      "model_id": "IQUBE",
      "part_id": "IQUBE_ST",
      "status": "scheduled",
      "ride_type": "dealer",
      "ride_scheduled_date": "2026-06-25 14:00:00.000",
      "test_ride_id": "TR001"
    }
  ],
  "follow_up": {
    "follow_up_method": "phone",
    "disposition": "interested",
    "sub_disposition": "callback_requested",
    "next_follow_up_date": "2026-06-24 10:00:00.000",
    "customer_voice": "Will visit showroom this weekend",
    "qualification": "hot"
  },
  "additional_details": {
    "first_walk_in_date": "2026-06-23 11:00:00.000",
    "enquiry_type": "fresh",
    "source_of_awareness": "social_media"
  },
  "interested_brand": [
    { "brand_code": 5, "model_id": "IQUBE", "part_id": "IQUBE_ST" }
  ],
  "lead_invoice": {
    "invoice_id": "INV20260625001",
    "invoice_generated_date": "2026-06-25 16:00:00.000",
    "brand_code": 5,
    "model_id": "IQUBE",
    "part_id": "IQUBE_ST",
    "vin_number": "MD2A14CZ..."
  },
  "enquiry_tag": [
    { "tag_name": "test_ride_completed", "source": "ems", "status": 1 }
  ],
  "finance_details": {
    "application_no": "FIN2026001",
    "application_status": "approved",
    "status": 1
  },
  "extra_attributes": [
    { "attribute_name": "preferred_color", "attribute_value": "Titanium Grey" }
  ]
}
```

**Field Reference:**

| Field | Type | Required | Description |
|---|---|---|---|
| `lead_id` | string | **Yes** | The `internet_enquiry_id` of the lead to update (e.g., "IEQ000012345") |
| `updated_by` | int | **Yes** | Source ID of the system making the update |
| `events` | int[] | **Yes** | Event codes indicating what type of update this is (e.g., 1=status change, 12=dealer transfer) |
| `status` | string | No | New lead status (e.g., "test_ride_booked", "enquiry_lost") |
| `dealer_id` | string | No | New dealer (for dealer transfer events 12, 13, 31, 32) |
| `branch_id` | int | No | New branch (for dealer transfer) |
| `test_rides[]` | array | No | Test ride updates |
| `follow_up` | object | No | Follow-up activity record |
| `additional_details` | object | No | Extended field updates |
| `interested_brand[]` | array | No | Updated brand interests |
| `lead_invoice` | object | No | Invoice details (for invoiced leads) |
| `finance_details` | object | No | Finance application updates |

---

### 7.3 POST /api/b2b/lead — Webhook Intake (Facebook/Meta)

**When to use:** Automatically called by Facebook when a user submits a Lead Ad form. Not called manually by integration partners.

```json
{
  "object": "page",
  "entry": [
    {
      "id": "123456789",
      "time": 1719043800,
      "changes": [
        {
          "field": "leadgen",
          "value": {
            "ad_id": "987654321",
            "form_id": "111222333",
            "leadgen_id": "444555666",
            "created_time": 1719043800,
            "page_id": "123456789",
            "adgroup_id": "777888999"
          }
        }
      ]
    }
  ]
}
```

---

### 7.4 POST /api/b2b/lead — Webhook Intake (Google Ads)

**When to use:** Automatically called by Google Ads when a user submits a lead form extension. Not called manually.

```json
{
  "lead_id": "google_lead_abc123",
  "form_id": 12345678,
  "campaign_id": 98765432,
  "google_key": "configured_key",
  "is_test": false,
  "gcl_id": "CjwKCAjw...",
  "adgroup_id": 11223344,
  "creative_id": 55667788,
  "lead_stage": "OPEN",
  "lead_submit_time": "2026-06-22T10:30:00Z",
  "user_column_data": [
    { "column_name": "FULL_NAME", "column_id": "FULL_NAME", "string_value": "Rajesh Kumar" },
    { "column_name": "PHONE_NUMBER", "column_id": "PHONE_NUMBER", "string_value": "+919876543210" },
    { "column_name": "EMAIL", "column_id": "EMAIL", "string_value": "rajesh@example.com" },
    { "column_name": "CITY", "column_id": "CITY", "string_value": "Chennai" },
    { "column_name": "POSTAL_CODE", "column_id": "POSTAL_CODE", "string_value": "600001" }
  ]
}
```

---

### 7.5 POST /api/lead/comms — Communications Event

**When to use:** When a communication event occurs — SMS delivered, email opened, link clicked, WhatsApp reply received.

```json
{
  "LeadId": "IEQ000012345",
  "Mobile": "9876543210",
  "BrandCodes": [5, 3],
  "EventId": 101,
  "Email": "rajesh@example.com",
  "Response": "delivered",
  "ResponseDate": "2026-06-22T11:00:00Z",
  "ActivityName": "Welcome SMS",
  "JourneyName": "New Lead Nurture",
  "CampaignName": "iQube_June2026",
  "SourceId": 1,
  "Medium": "sms",
  "Category": "transactional",
  "SubCategory": "welcome",
  "ActivityType": "send"
}
```

---

### 7.6 POST /dealers — Dealer Lookup

**When to use:** When a system needs to find dealers matching specific criteria (brand capabilities, location, status).

```json
{
  "DealerId": null,
  "All": 0,
  "TwoWheeler": 1,
  "ThreeWheeler": 0,
  "Iqube": 1,
  "Rr310": 0,
  "Rtr310": 0,
  "Ronin": 0,
  "Date": "2026-06-22",
  "PageNumber": 1,
  "PageSize": 50
}
```

---

### 7.7 POST /api/leads/Count — Lead Count

**When to use:** Dashboard widgets that show lead counts by filter (source, date range, status).

```json
{
  "StartTime": "2026-06-01T00:00:00Z",
  "EndTime": "2026-06-22T23:59:59Z",
  "SourceIDs": [1, 2, 3],
  "L1Source": ["website", "facebook"],
  "MobileNumber": null,
  "Status": "new_enquiry",
  "IsActive": true
}
```

---

### 7.8 POST /api/leads/getDetails — Single Lead Details

**When to use:** When you need full details of one specific lead — by lead ID or by request ID.

```json
{
  "leadId": "IEQ000012345",
  "RequestId": null
}
```

---

### 7.9 POST /api/leads/all — Paginated Lead List

**When to use:** Reporting dashboards, export tools, or admin panels that need to browse leads.

```json
{
  "StartTime": "2026-06-01T00:00:00Z",
  "EndTime": "2026-06-22T23:59:59Z",
  "SourceIDs": [1, 2],
  "L1Source": null,
  "MobileNumber": null,
  "Status": null,
  "IsActive": true
}
```

Query parameters for pagination:
- `page` (int) — Page number (1-based)
- `pageSize` (int) — Number of records per page

---

### 7.10 POST /api/leads/filter — Referral Lead Filter

**When to use:** Referral management portals that need to view leads generated through referral programs.

```json
{
  "StartTime": "2026-06-01T00:00:00Z",
  "EndTime": "2026-06-22T23:59:59Z",
  "SourceIDs": [34],
  "IsActive": true,
  "EmployeeId": "TVS001234",
  "dealerId": "12345",
  "MobileNumber": null,
  "Status": null,
  "CscId": null
}
```

---

### 7.11 POST /api/leads/one-view — Lead Timeline

**When to use:** CRM interfaces or support tools that need to see every event that happened to a lead — creation, updates, EMS push, CRM push, follow-ups, test rides, invoicing.

```json
{
  "leadId": "IEQ000012345",
  "sources": [1, 2, 3],
  "events": [1, 5, 12],
  "sort_by": "desc"
}
```


---

### 7.12 Master Data APIs — Request Payloads

#### POST /api/brand — Create Brand

```json
{
  "modelName": "Jupiter",
  "brandCode": 3,
  "crmBrandCode": "TVS03",
  "crmTeam": 1,
  "isDualPush": false,
  "visible": true,
  "rank": 5,
  "modelId": "JUPITER",
  "partId": "JUPITER_125",
  "isElectric": false
}
```

#### PUT /api/brand/{brandCode} — Update Brand

All fields optional (null = no change):

```json
{
  "modelName": "Jupiter 125",
  "crmTeam": 2,
  "isDualPush": true,
  "visible": true,
  "rank": 4,
  "modelId": "JUPITER",
  "partId": "JUPITER_125_NEW",
  "isElectric": false
}
```

#### POST /api/model — Create Model/Part

```json
{
  "brandCode": 3,
  "modelId": "JUPITER",
  "partId": "JUPITER_125_DRUM",
  "modelName": "Jupiter 125 Drum",
  "isEnabled": true
}
```

#### PUT /api/model/{id} — Update Model/Part

All fields optional (null = no change):

```json
{
  "brandCode": 3,
  "modelId": "JUPITER",
  "partId": "JUPITER_125_DISC",
  "modelName": "Jupiter 125 Disc",
  "isEnabled": true
}
```

#### POST /api/lead-source — Create Lead Source

```json
{
  "id": 50,
  "source": "BikeWale Premium",
  "emsSource": "BIKEWALE_PREM",
  "lceSource": "BIKEWALE",
  "crmSource": "BikeWale Premium",
  "l1Source": "aggregator",
  "enqModeId": "ONLINE",
  "emsEventType": "AGGREGATOR_LEADS"
}
```

#### PUT /api/lead-source/{id} — Update Lead Source

All fields optional (null = no change):

```json
{
  "source": "BikeWale Premium Updated",
  "emsSource": "BIKEWALE_PREM_V2",
  "active": true
}
```

#### POST /api/lead-flow — Create Lead Flow Configuration

```json
{
  "sourceId": 50,
  "isMobileMandatory": true,
  "mobileValidation": "^[1-9][0-9]{9}$",
  "isDealerMandatory": false,
  "isBrandMandatory": true,
  "isModelMandatory": true,
  "isNameMandatory": true,
  "isLceEnabled": true,
  "defaultClassification": "HOT",
  "isEmsPush": true,
  "isCrmPush": true,
  "isDualPush": false,
  "isFinanceEnabled": true,
  "isAggregator": true,
  "isLatlongEnabled": true,
  "isPincodeMandatory": true
}
```

#### PUT /api/lead-flow/{id} — Update Lead Flow Configuration

All fields optional (null = no change):

```json
{
  "isMobileMandatory": true,
  "mobileValidation": "^[6-9][0-9]{9}$",
  "isEmsPush": false,
  "isCrmPush": true,
  "lceApiUrl": "https://lce-api.tvsmotor.com/v2/classify"
}
```

#### POST /api/event-configurator — Create Event Configurator

```json
{
  "eventName": "LEAD_PROCESS",
  "eventRules": "{\"target\": [\"EMS\", \"CRM\"]}",
  "eventAttribute": "lead_submission"
}
```

#### PUT /api/event-configurator/{id} — Update Event Configurator

All fields optional (null = no change):

```json
{
  "eventName": "LEAD_PROCESS_V2",
  "eventRules": "{\"target\": [\"EMS\", \"CRM\", \"FINANCE\"]}",
  "eventAttribute": "lead_submission"
}
```

---

## 8. Response Payloads

### 8.1 Standard Response Model

All lead submission and update endpoints return a consistent response structure:

```json
{
  "Message": "Success",
  "RequestId": 12345,
  "LeadId": "IEQ000012345",
  "Status": 200
}
```

| Field | Type | Description |
|---|---|---|
| `Message` | string | Human-readable result description ("Success", error message, or "DUPLICATE_LEAD") |
| `RequestId` | long | The internal request log ID — useful for support tickets and tracing |
| `LeadId` | string | The generated internet enquiry ID for the lead (e.g., "IEQ000012345"). Empty on validation failure. |
| `Status` | int | HTTP status code (200 = success, 400 = validation error, 500 = server error) |

### 8.2 Response Scenarios for POST /api/lead

**Successful new lead (200):**
```json
{
  "Message": "Success",
  "RequestId": 56789,
  "LeadId": "IEQ000056789",
  "Status": 200
}
```

**Duplicate lead — same dealer (200):**
The system detects that this mobile number already has an active lead for the same dealer. The original lead ID is returned. No new lead is created.
```json
{
  "Message": "DUPLICATE_LEAD",
  "RequestId": 56790,
  "LeadId": "IEQ000045678",
  "Status": 200
}
```

**Duplicate lead — different dealer (200):**
Same mobile number but for a different dealer. A new child lead IS created (with reference to the parent).
```json
{
  "Message": "DUPLICATE_LEAD",
  "RequestId": 56791,
  "LeadId": "IEQ000056791",
  "Status": 200
}
```

**Validation failure (400):**
```json
{
  "Message": "Invalid mobile number",
  "RequestId": 56792,
  "LeadId": "",
  "Status": 400
}
```

**Parallel duplicate — database constraint (400):**
Two identical requests arrived simultaneously and the database unique constraint blocked the second one.
```json
{
  "Message": "Parallel Requests Received",
  "RequestId": 56793,
  "LeadId": "",
  "Status": 400
}
```

**Server error (500):**
```json
{
  "Message": "Server Error",
  "RequestId": 56794,
  "LeadId": "",
  "Status": 500
}
```

### 8.3 Response for POST /api/lead/update

**Successful update (200):**
```json
{
  "Message": "Success",
  "RequestId": 56795,
  "LeadId": "IEQ000012345",
  "Status": 200
}
```

**Lead not found (400):**
```json
{
  "Message": "INVALID_LEAD_ID",
  "RequestId": 56796,
  "LeadId": "",
  "Status": 400
}
```

**Validation failure (400):**
```json
{
  "Message": "Invalid/Inactive Dealer or Branch",
  "RequestId": 56797,
  "LeadId": "",
  "Status": 400
}
```

### 8.4 Response for GET /api/b2b/lead (Webhook Verification)

**Successful verification:**
- HTTP 200
- Body: the raw `hub.challenge` string (not JSON)

**Failed verification:**
- HTTP 400
- Body: `"Invalid verification token"`

### 8.5 Response for POST /api/b2b/lead (Webhook Intake)

Returns the same `ServerResponse` model as `/api/lead`:
```json
{
  "Message": "Success",
  "RequestId": 56798,
  "LeadId": "IEQ000056798",
  "Status": 200
}
```

On error:
```json
{
  "Message": "Token not found.",
  "RequestId": 0,
  "LeadId": "",
  "Status": 400
}
```

### 8.6 Response for POST /api/leads/Count

```json
{
  "Message": "Success",
  "Response": {
    "total_count": 1542
  },
  "Status": 200
}
```

### 8.7 Response for POST /api/leads/getDetails

Returns full lead details including all sub-entities:
```json
{
  "Message": "Success",
  "Response": {
    "id": 12345,
    "internet_enquiry_id": "IEQ000012345",
    "customer_name": "Rajesh Kumar",
    "mobile_number": "9876543210",
    "dealer_id": "12345",
    "branch_id": 1,
    "brand_code": 5,
    "model_id": "IQUBE",
    "part_id": "IQUBE_ST",
    "status": "test_ride_booked",
    "ems_status": 1,
    "crm_status": 1,
    "source_id": 1,
    "enquiry_date": "2026-06-22T10:30:00",
    "created_at": "2026-06-22T10:30:05",
    "is_active": true,
    "lead_brand_details": [...],
    "lead_test_rides": [...],
    "lead_followups": [...],
    "lead_extra_attributes": [...]
  },
  "Status": 200
}
```

### 8.8 Response for POST /api/leads/all

Returns a paginated array of lead summaries:
```json
{
  "Message": "Success",
  "Response": [
    {
      "id": 12345,
      "internet_enquiry_id": "IEQ000012345",
      "customer_name": "Rajesh Kumar",
      "mobile_number": "9876543210",
      "dealer_id": "12345",
      "status": "new_enquiry",
      "source_id": 1,
      "brand_code": 5,
      "created_at": "2026-06-22T10:30:05"
    },
    {
      "id": 12346,
      "internet_enquiry_id": "IEQ000012346",
      "customer_name": "Priya S",
      "mobile_number": "9876543220",
      "dealer_id": "12346",
      "status": "test_ride_booked",
      "source_id": 2,
      "brand_code": 3,
      "created_at": "2026-06-22T11:15:00"
    }
  ],
  "Status": 200
}
```

### 8.9 Response for POST /api/leads/one-view

Returns the complete event timeline for a lead:
```json
{
  "Message": "Success",
  "Response": [
    {
      "event_id": 1,
      "event_name": "Lead Created",
      "source_id": 1,
      "created_at": "2026-06-22T10:30:05",
      "metadata": "{...}"
    },
    {
      "event_id": 5,
      "event_name": "EMS Pushed",
      "source_id": 1,
      "created_at": "2026-06-22T10:30:45",
      "metadata": "{...}"
    },
    {
      "event_id": 12,
      "event_name": "Dealer Transfer",
      "source_id": 1,
      "created_at": "2026-06-23T09:15:00",
      "metadata": "{\"old_dealer\":\"12345\",\"new_dealer\":\"67890\"}"
    }
  ],
  "Status": 200
}
```

### 8.10 Response for POST /dealers

```json
{
  "Message": "Success",
  "Response": [
    {
      "sap_dealer_code": "12345",
      "name": "TVS Dealer - Anna Nagar",
      "city": "Chennai",
      "state": "Tamil Nadu",
      "pincode": "600040",
      "two_wheeler": 1,
      "iqube": 1,
      "ems": 1
    }
  ],
  "Status": 200
}
```

### 8.11 Response for POST /api/lead/comms

```json
{
  "Message": "Success",
  "RequestId": 56799,
  "LeadId": "IEQ000012345",
  "Status": 200
}
```

### 8.12 Error Response Summary

| HTTP Status | Meaning | When It Occurs |
|---|---|---|
| **200** | Success OR Duplicate detected (still returns 200 with message) | Lead created successfully, or duplicate identified |
| **400** | Bad Request — validation failure | Missing/invalid field, lead not found, inactive dealer |
| **422** | Unprocessable Entity | Unhandled exception in controller |
| **500** | Internal Server Error | Unexpected server-side failure |

### 8.13 Master Data API Responses

Master data create/update endpoints return `MasterResponse` (no `LeadId` field):

**Create success (200):**
```json
{
  "message": "Success",
  "requestId": 121,
  "status": 200
}
```

**Update success (200):**
```json
{
  "message": "Success",
  "requestId": 3,
  "status": 200
}
```

**Validation failure (400):**
```json
{
  "message": "model_name is required",
  "requestId": 0,
  "status": 400
}
```

**Duplicate / Conflict (409):**
```json
{
  "message": "brand_code already exists",
  "requestId": 0,
  "status": 409
}
```

**Not found (404):**
```json
{
  "message": "brand not found",
  "requestId": 0,
  "status": 404
}
```

Master data GET endpoints return `ServerDataResponse`:

**Get all (200):**
```json
{
  "message": "Success",
  "response": [ { ... }, { ... } ],
  "status": 200
}
```

**Get by ID (200):**
```json
{
  "message": "Success",
  "response": { "brandCode": 3, "modelName": "Jupiter", ... },
  "status": 200
}
```

**Get by ID — not found (404):**
```json
{
  "message": "brand not found",
  "response": null,
  "status": 404
}
```

---

## 9. Error Responses

### 9.1 Error Response Structure

All error responses follow the same `ServerResponse` envelope used by success responses. The `Status` field mirrors the HTTP status code, and `Message` provides a human-readable explanation of what went wrong.

```json
{
  "Message": "<error description>",
  "RequestId": <request_log_id or 0>,
  "LeadId": "",
  "Status": <http_status_code>
}
```

### 9.2 Complete Error Code Catalogue

| Error Code | HTTP Status | Message | Plain English Meaning | Endpoint |
|---|---|---|---|---|
| 1 | 400 | "Invalid brand code" / "Brand code should be greater than 0" | The `brand_code` value does not exist in the brand master table, or was sent as 0 when required | `/api/lead` |
| 2 | 400 | "Invalid mobile number" | Mobile number is null, not 10 digits, or fails the per-source regex pattern | `/api/lead`, `/api/lead/update` |
| 3 | 400 | "Invalid source" | The `source_id` does not exist in the `lead_sources` table | `/api/lead` |
| 4 | 400 | "Invalid/missing Enquiry Date" / "Enquiry date cannot be in future" | Date field is missing, uses wrong format (`yyyy-MM-dd HH:mm:ss.fff` expected), or is a future date | `/api/lead` |
| 5 | 400 | "Too many requests from same mobile number" | The same phone has submitted too many leads (per source threshold) | `/api/lead` |
| 6 | 400 | "Invalid model or part id" / "Model Id is missing" / "Part_id is missing" | The model_id + part_id combination does not exist in `model_id_part_id_master`, or a required field is null | `/api/lead` |
| 7 | 400 | "Missing customer name" / "Customer Name cannot exceed 100 characters" | Name is required by source config but is empty, or exceeds 100 chars | `/api/lead` |
| 8 | 400 | "Dealer Id is missing" / "Invalid/Inactive Dealer or Branch" / "Failed to allocate dealer for the area" | Dealer is required but not provided; dealer/branch combination is inactive; Latlong could not find a dealer for the pincode | `/api/lead` |
| 11 | 400 | "INVALID_COUNTRY_CODE" | `countryCode` header is required by source config but is missing or not found in `country_master` | `/api/lead` |
| 12 | 400 | "INVALID_PINCODE" | Pincode is required and is not a valid 6-digit number existing in `pincode_master` | `/api/lead` |
| 13 | 400 | "Lead flow is not configured for the source" | No row exists in `lead_flow_configuration` for the given `source_id` | `/api/lead` |
| 14 | 400 | "DUPLICATE_LEAD" | Same mobile + same dealer + active lead already exists (dealer-level duplicate) | `/api/lead` |
| 16 | 400 | "INVALID_LEAD_ID" | The `lead_id` in an update request does not match any existing lead | `/api/lead/update` |
| 19 | 400 | "Invalid referral mobile number" | Referral mobile fails validation (not 10 digits or regex) | `/api/lead` |
| 20 | 400 | "Missing referral mobile number" | Referral details provided but mobile is empty | `/api/lead` |
| 21 | 400 | "Invalid test ride model or part id" | Test ride model_id + part_id combination is invalid | `/api/lead` |
| 22 | 400 | "Extra attribute name/value cannot be null" | An entry in `extra_attributes[]` has a null key or null value | `/api/lead` |
| — | 400 | "Parallel Requests Received" | Two identical requests hit the system at the same moment; the database unique constraint blocked the second | `/api/lead` |
| — | 400 | "leadId or RequestId is required" | Neither `leadId` nor `RequestId` was provided in the query | `/api/leads/getDetails` |
| — | 400 | "Token not found." | Facebook webhook — access token could not be located for the form/page combination | `/api/b2b/lead` |
| — | 400 | "No data received from Facebook API." | Graph API returned empty response | `/api/b2b/lead` |
| — | 400 | "Invalid verification token" | Facebook webhook handshake — `hub.verify_token` does not match | `GET /api/b2b/lead` |
| — | 500 | "Server Error" | An unhandled exception occurred. Details are logged internally but not exposed to the caller. | All endpoints |

**Master Data API Error Codes:**

| HTTP Status | Message | Meaning | Endpoint |
|---|---|---|---|
| 400 | "model_name is required" | Required field missing on brand create | `/api/brand` |
| 400 | "brand_code is required and must be greater than zero" | BrandCode is zero or negative | `/api/brand` |
| 400 | "model_id and part_id are required" | Missing required fields on model create | `/api/model` |
| 400 | "Invalid SourceId" | SourceId is null, zero, or negative | `/api/lead-flow` |
| 400 | "event_name is required" | EventName is empty on event configurator create | `/api/event-configurator` |
| 400 | "MobileValidation must be a valid regex pattern" | Invalid regex pattern provided | `/api/lead-flow` |
| 400 | "LceApiUrl must be a valid HTTP/HTTPS URL" | Non-URL value in LceApiUrl field | `/api/lead-flow` |
| 400 | "event_rules must be valid JSON" | Invalid JSON in EventRules field | `/api/event-configurator` |
| 404 | "brand not found" | BrandCode does not exist in brand_master | `/api/brand/{brandCode}` |
| 404 | "Model Not found" | Model ID does not exist | `/api/model/{id}` |
| 404 | "Lead source not found" | Lead source ID does not exist | `/api/lead-source/{id}`, `/api/lead-flow` |
| 404 | "LeadFlowConfiguration not found" | Lead flow config ID does not exist | `/api/lead-flow/{id}` |
| 404 | "event configurator not found" | Event configurator ID does not exist | `/api/event-configurator/{id}` |
| 409 | "brand_code already exists" | Duplicate brand code on create | `/api/brand` |
| 409 | "crm_brand_code already exists" | Duplicate CRM brand code | `/api/brand` |
| 409 | "model+part already exists for brand" | Duplicate model+part+brand combination | `/api/model` |
| 409 | "Id already exists" | Duplicate lead source ID on create | `/api/lead-source` |
| 409 | "Lead source already exists" | Duplicate source name | `/api/lead-source` |
| 409 | "LeadFlowConfiguration for this SourceId already exists" | One config per source constraint | `/api/lead-flow` |
| 409 | "event_name already exists" | Duplicate event name | `/api/event-configurator` |

### 9.3 Error Handling Behaviour by Scenario

| Scenario | What the API Does | What the Caller Should Do |
|---|---|---|
| Validation fails at field level | Returns 400 with specific field error message | Fix the invalid field and retry |
| Duplicate detected (same dealer) | Returns 200 with "DUPLICATE_LEAD" and the original lead ID | Treat as success — lead already exists |
| Duplicate detected (different dealer) | Returns 200 with "DUPLICATE_LEAD" but a NEW lead ID | Treat as success — new child lead was created |
| Database constraint violation | Returns 400 "Parallel Requests Received" | This is a race condition; typically safe to ignore |
| Facebook token expired | Returns 400 "Token not found" | System will attempt token refresh automatically on next webhook |
| Server error | Returns 500 "Server Error" | Retry after a short delay; raise support ticket if persistent |

### 9.4 HTTP Status Code Summary

| Code | Meaning | When Used |
|---|---|---|
| 200 | OK — request processed successfully | Success and controlled duplicates |
| 400 | Bad Request — caller error | Validation failures, missing fields, invalid references |
| 422 | Unprocessable Entity — exception in controller layer | Rare — unhandled exception that bypasses normal error handling |
| 500 | Internal Server Error — system failure | Unexpected exceptions, database connectivity issues |


---

## 10. Validation Rules

### 10.1 Validation Execution Order

Validation runs in strict sequential order for `POST /api/lead`. The **first failure stops execution** and returns immediately — subsequent checks are not performed.

```
Step 1:  Source validation
Step 2:  Lead flow configuration check
Step 3:  Country code validation (if required by flow)
Step 4:  Mobile number validation (if required by flow)
Step 5:  Enquiry date format + not-in-future check
Step 6:  Brand code validation (if required by flow)
Step 7:  Model ID + Part ID combination validation
Step 8:  Follow-up date validation
Step 9:  Alternate mobile validation
Step 10: Consent date validation
Step 11: Pincode validation (if required by flow)
Step 12: Test ride details validation
Step 13: Interested brands validation
Step 14: Latlong dealer auto-allocation (if enabled by flow)
Step 15: Dealer ID mandatory check (if required by flow)
Step 16: Dealer active/inactive check
Step 17: Customer name validation (if required by flow)
Step 18: Referral details validation
Step 19: Extra attributes null-key check
Step 20: Duplicate detection
```


### 10.2 Field-Level Validation Rules

| Field | Rule | Condition | Error on Failure |
|---|---|---|---|
| `source_id` | Must exist in `lead_sources` table | Always | "Invalid source" |
| `source_id` | Must have a row in `lead_flow_configuration` | Always | "Lead flow is not configured for the source" |
| `countryCode` (header) | Must exist in `country_master` table | Only when flow config `IsCountryCodeMandatory = true` | "INVALID_COUNTRY_CODE" |
| `mobile_number` | Must be exactly 10 digits | Only when flow config `IsMobileMandatory = true` | "Invalid mobile number" |
| `mobile_number` | Must match per-source regex pattern stored in `lead_flow_configuration.MobileValidation` | Only when regex is configured | "Invalid mobile number" |
| `enquiry_date` | Must parse as `yyyy-MM-dd HH:mm:ss.fff` format | Always | "Invalid/missing Enquiry Date" |
| `enquiry_date` | Must not be in the future (compared to UTC now) | Always | "Enquiry date cannot be in future" |
| `brand_code` | Must be > 0 | Only when flow config `IsBrandMandatory = true` or when brand_code is non-zero | "Brand code should be greater than 0" |
| `brand_code` | Must exist in `brand_master` table | When provided | "Invalid brand code" |
| `model_id` | Must not be null | Only when flow config `IsModelMandatory = true` | "Model Id is missing" |
| `part_id` | Must not be null | Only when flow config `IsModelMandatory = true` | "Part_id is missing" |
| `model_id` + `part_id` | Combination must exist in `model_id_part_id_master` | When both are provided | "Invalid model or part id" |
| `area` (pincode) | Must be 6 digits, numeric, and exist in `pincode_master` | Only when flow config `IsPincodeMandatory = true` or `IsLatlongEnabled = true` | "INVALID_PINCODE" |
| `dealer_id` | Must not be empty | Only when flow config `IsDealerMandatory = true` | "Dealer Id is missing" |
| `dealer_id` + `branch_id` | Combination must be an active dealer in `dealer_master` | When dealer_id is provided | "Invalid/Inactive Dealer or Branch" |
| `customer_name` | Must not be empty | Only when flow config `IsNameMandatory = true` | "Missing customer name" |
| `customer_name` | Must not exceed 100 characters | Always (when provided) | "Customer Name cannot exceed 100 characters" |
| `follow_up.next_follow_up_date` | Must parse as valid date format | When provided | "Invalid/missing next follow up date" |
| `follow_up.next_follow_up_date` | Must not be before `enquiry_date` | When provided | "Next follow up date cannot be in past" |
| `additional_details.alternative_mobile` | Must be exactly 10 digits + pass regex | When provided | "Invalid mobile number" |
| `additional_details.consent_date` | Must parse as valid date format, must not be in future | When provided | "Invalid/missing consent date" |
| `test_rides[].brand_code` | Must be > 0 and exist in `brand_master` | When test rides provided | "Invalid test ride brand code" |
| `test_rides[].ride_scheduled_date` | Must parse as valid date format | When provided | "Invalid/missing test ride scheduled date" |
| `test_rides[].model_id` + `part_id` | Must be valid combination in master table | When provided | "Invalid test ride model or part id" |
| `referral_customer_details.referral_customer_mobile_number` | Must be valid 10-digit mobile | When referral details provided | "Invalid/Missing referral mobile number" |
| `extra_attributes[]` | Each entry must have non-null `attribute_name` and `attribute_value` | When provided | "Extra attribute name/value cannot be null" |


### 10.3 Duplicate Detection Rules

Duplicate detection runs AFTER all field-level validations pass. The algorithm:

1. Query the `leads` table for all records with the same `mobile_number`
2. For each match:
   - If `dealer_id` matches AND `branch_id` matches AND `is_active = true` → **Dealer Duplicate** (lead is NOT created; original ID returned)
   - If `dealer_id` is different → **Mobile Duplicate** (new lead IS created as a child with `parent_lead` reference)
3. If no matches found → **Not a duplicate** (proceed normally)

### 10.4 Configurable Validation (Lead Flow Configuration)

Validation rules are NOT hardcoded — they are configurable per source via the `lead_flow_configuration` database table. This means different lead sources can have different mandatory fields:

| Flow Config Flag | When TRUE | When FALSE |
|---|---|---|
| `IsMobileMandatory` | Mobile number validated | Mobile can be null |
| `IsBrandMandatory` | Brand code required and validated | Brand is optional |
| `IsModelMandatory` | Model + Part IDs required | Model is optional (defaults assigned from brand) |
| `IsDealerMandatory` | Dealer must be in request | Dealer auto-assigned or optional |
| `IsNameMandatory` | Customer name required | Name is optional |
| `IsPincodeMandatory` | Pincode must be valid 6-digit Indian pincode | Pincode optional |
| `IsLatlongEnabled` | System auto-allocates dealer via geo-API if dealer not provided | No auto-allocation |
| `IsCountryCodeMandatory` | countryCode header validated | Header ignored |
| `IsTestRideMandatory` | Test ride details must be present | Test ride optional |

### 10.5 Update Validation Rules (POST /api/lead/update)

| Check | Rule | Error |
|---|---|---|
| `lead_id` exists | Must match an `internet_enquiry_id` in the `leads` table | "INVALID_LEAD_ID" |
| Lead is active | If lead is inactive or status = "enquiry_lost", forces status to "enquiry_lost" | (no error — status forced) |
| Transfer events | Events [12, 13, 31, 32] require a valid `dealer_id` + `branch_id` for the target dealer | "Invalid/Inactive Dealer or Branch" |
| Date fields | Same format rules as new lead (yyyy-MM-dd HH:mm:ss.fff) | varies |

---

## 11. Rate Limits

### 11.1 Application-Level Rate Limiting

The LMS API does **not implement explicit HTTP rate limiting** (no 429 responses). However, the following implicit limits apply:

| Mechanism | Limit | Scope | Behaviour When Exceeded |
|---|---|---|---|
| **Duplicate detection** | 1 active lead per mobile + dealer + branch combination | Per lead | Returns 200 "DUPLICATE_LEAD" — effectively prevents spam from the same mobile number to the same dealer |
| **Database unique constraint** | 1 insert per mobile + dealer + branch + active | Per database row | Returns 400 "Parallel Requests Received" — prevents concurrent identical inserts |
| **Dealer daily threshold** | Configurable per dealer (e.g., 50 leads/day) | Per dealer per day | Lead is accepted and queued but NOT pushed to EMS until next day — no error to caller |
| **Service Bus MaxConcurrentCalls** | 1 message at a time per consumer instance | Per service instance | Messages queue up in Service Bus and are processed sequentially |

### 11.2 Infrastructure-Level Limits

| Layer | Limit | Notes |
|---|---|---|
| Azure Service Bus | 1000 messages/second per topic (Standard tier) | Shared across all publishers |
| Azure SQL | DTU/vCore-based throughput | Shared database — all 5 services compete for resources |
| Kubernetes pod resources | CPU and memory per container | Configured via Helm charts per environment |
| External API rate limits (Latlong.in, LCE, EMS) | Varies per contract | Latlong calls are per-brand; LCE has OAuth token-based limits |

### 11.3 Recommendations for Integration Partners

- **Do not retry 200 "DUPLICATE_LEAD" responses** — the lead already exists
- **Retry 500 errors** with exponential backoff (suggested: 1s, 5s, 30s)
- **Do not send more than 100 leads/second** from a single source to avoid overwhelming the database
- **Batch submissions are not supported** — each lead must be a separate HTTP request


---

## 12. External API Dependencies

The LMS platform calls several external APIs as part of its lead processing pipeline. These are NOT called directly by integration partners — they are called internally by the backend services after a lead is submitted.

### 12.1 External APIs Called by the Platform

| External API | Called By | When | Auth Method | What It Does |
|---|---|---|---|---|
| **Facebook Graph API** | lms (Lead Acquisition) | When a Meta/Facebook webhook arrives | App access token (from DB) | Fetches the full lead form field data using the `leadgen_id` from the webhook. URL: `https://graph.facebook.com/{version}/{leadgen_id}` |
| **Latlong.in Dealer API** | lms, lms_process | When a lead has no dealer_id and `IsLatlongEnabled=true` | OAuth2 client_credentials (per brand) | Sends customer pincode → receives ranked list of nearby authorised dealers with distance. Separate credentials per brand family (Ronin, RTR, Common, 3W, EV). |
| **LCE (Lead Classification Engine)** | lms_process | For every new valid lead during processing | OAuth2 client_credentials | Sends lead attributes (model, pincode, dealer, UTM params) → receives retail probability score and category (HOT/WARM/COLD). |
| **TVS EMS API** | lms_ems | After lead is classified and assigned a dealer | API key header (`x-api-key`) | Pushes the full lead payload to the dealer-facing EMS system. Separate endpoints for HO, Aggregator, and EV leads. |
| **Salesforce CDP** | lms_crm | For every new lead routed to CRM subscription | OAuth2 chained (Salesforce login → CDP token exchange) | Creates/updates the customer's unified profile in the Customer 360 platform. |
| **Salesforce Service Cloud (CCP)** | lms_crm, lms_tvs_credit | For new leads and updates routed to CRM/Finance | OAuth2 client_credentials (token cached 23 hours) | Creates Lead records, updates Lead records, and upserts Test Ride records in Salesforce. |
| **Voice AI API** | lms_crm | For leads assigned to whitelisted dealers | Direct POST (no auth header in request) | Initiates automated outbound voice calls to customers for lead qualification. |
| **Rezo API** | lms_crm | For premium-brand leads only | API key header | Distributes leads to the Rezo partner platform for premium vehicle follow-up. |
| **Dialer API** | lms_crm | For leads that qualify for call centre assignment | OAuth2 bearer token | Submits lead to the auto-dialer queue for call centre outreach. |
| **TVS Credit API** | lms_tvs_credit | For finance-eligible leads | Parameters in body (channel/product/agency codes) | Submits finance-eligible leads with dealer code, state/city codes, and customer details. |
| **Legacy LMS** | lms_crm | For backward compatibility | None (fire and forget HTTP POST) | Sends lead data to the old LMS system. Response is not checked — failures are silently ignored. |
| **MDP (Master Data Platform)** | lms_process | Continuous (Service Bus consumer) | Azure Service Bus SAS | Receives dealer create/update/migration events from the Master Data Platform via a separate Service Bus namespace. |

### 12.2 External API Failure Impact on Callers

| External API Fails | Impact on POST /api/lead Caller | Impact on Lead |
|---|---|---|
| Latlong.in down | If `IsDealerMandatory=true` → 400 "Failed to allocate dealer". If optional → 200 Success (lead created without dealer) | Lead may not reach EMS until dealer is manually assigned |
| LCE API down | No impact on caller (processing is async) | Lead gets default classification ("HOT") and continues processing |
| TVS EMS API down | No impact on caller (processing is async) | Lead is auto-retried after 30 minutes via Service Bus scheduled message |
| Salesforce CDP/CCP down | No impact on caller (processing is async) | Push logged as failed in `lead_push_logs`; no automatic retry |
| TVS Credit API down | No impact on caller (processing is async) | Push logged as failed; no automatic retry |
| Facebook Graph API down | 400 returned to Facebook webhook | Facebook will retry the webhook delivery |

### 12.3 External API Timeout Configuration

| API | Timeout | Retry Behaviour |
|---|---|---|
| Legacy LMS | 10 seconds | No retry — fire and forget |
| EMS API | Default HttpClient timeout (100s) | 30-minute scheduled retry on failure |
| Latlong.in | Default HttpClient timeout | No retry — returns null if fails |
| LCE | Default HttpClient timeout | Falls back to default classification |
| Voice AI | Default HttpClient timeout | 3 retries with 2s × attempt backoff |


---

## 13. Sample Requests and Responses

### 13.1 Minimal Lead Submission (Website — Only Required Fields)

**Use case:** A simple website form with just name, phone, source, brand, and enquiry date.

**Request:**
```
POST /api/lead HTTP/1.1
Host: ls-acquisition.azurewebsites.net
Content-Type: application/json
APIKey: <your_api_key>
countryCode: IN

{
  "customer_name": "Anitha R",
  "mobile_number": "8765432109",
  "source_id": 1,
  "brand_code": 3,
  "model_id": "JUPITER",
  "part_id": "JUPITER_125",
  "enquiry_date": "2026-06-22 09:15:00.000",
  "area": "560001"
}
```

**Response (201 — Success):**
```json
{
  "Message": "Success",
  "RequestId": 100234,
  "LeadId": "IEQ000100234",
  "Status": 200
}
```

---

### 13.2 Full Lead Submission (Aggregator — All Fields)

**Use case:** BikeWale or BikeDekho sending a complete lead with test ride, finance interest, and UTM tracking.

**Request:**
```
POST /api/lead HTTP/1.1
Host: ls-acquisition.azurewebsites.net
Content-Type: application/json
APIKey: <your_api_key>

{
  "customer_name": "Vikram S",
  "mobile_number": "9012345678",
  "email_id": "vikram@email.com",
  "source_id": 15,
  "brand_code": 2,
  "model_id": "APACHE",
  "part_id": "RTR_200_4V",
  "dealer_id": "54321",
  "branch_id": "1",
  "area": "400001",
  "city": "Mumbai",
  "customer_state": "Maharashtra",
  "pincode": "400001",
  "enquiry_date": "2026-06-22 14:45:00.000",
  "finance": "true",
  "intent_for_purchase": "Within 2 Weeks",
  "device": "desktop",
  "utm_source": "bikewale",
  "utm_medium": "referral",
  "utm_campaign": "apache_mumbai_june",
  "interested_brand": [
    { "brand_code": 2, "model_id": "APACHE", "part_id": "RTR_200_4V" },
    { "brand_code": 2, "model_id": "APACHE", "part_id": "RTR_160_4V" }
  ],
  "test_rides": [
    {
      "brand_code": 2,
      "model_id": "APACHE",
      "part_id": "RTR_200_4V",
      "ride_type": "dealer",
      "ride_scheduled_date": "2026-06-25 11:00:00.000"
    }
  ],
  "finance_details": {
    "financier_name": "TVS Credit",
    "loan_amount": "120000",
    "tenure": "36"
  },
  "extra_attributes": [
    { "attribute_name": "referral_code", "attribute_value": "BW2026VIKRAM" }
  ]
}
```

**Response (200 — Success):**
```json
{
  "Message": "Success",
  "RequestId": 100235,
  "LeadId": "IEQ000100235",
  "Status": 200
}
```

---

### 13.3 Lead Submission — Validation Failure

**Use case:** Partner sends a lead with an invalid mobile number.

**Request:**
```
POST /api/lead HTTP/1.1
Content-Type: application/json
APIKey: <your_api_key>

{
  "customer_name": "Test User",
  "mobile_number": "12345",
  "source_id": 1,
  "brand_code": 3,
  "model_id": "JUPITER",
  "part_id": "JUPITER_125",
  "enquiry_date": "2026-06-22 10:00:00.000"
}
```

**Response (400 — Validation Error):**
```json
{
  "Message": "Invalid mobile number",
  "RequestId": 100236,
  "LeadId": "",
  "Status": 400
}
```

---

### 13.4 Lead Submission — Duplicate Detected

**Use case:** Same customer (same phone) submits again to the same dealer.

**Request:**
```
POST /api/lead HTTP/1.1
Content-Type: application/json
APIKey: <your_api_key>

{
  "customer_name": "Anitha R",
  "mobile_number": "8765432109",
  "source_id": 1,
  "brand_code": 3,
  "model_id": "JUPITER",
  "part_id": "JUPITER_125",
  "dealer_id": "12345",
  "branch_id": "1",
  "enquiry_date": "2026-06-22 15:00:00.000",
  "area": "560001"
}
```

**Response (200 — Duplicate, original lead ID returned):**
```json
{
  "Message": "DUPLICATE_LEAD",
  "RequestId": 100237,
  "LeadId": "IEQ000100234",
  "Status": 200
}
```


---

### 13.5 Lead Update — Dealer Transfer

**Use case:** A dealer transfers a lead to another dealer outlet.

**Request:**
```
POST /api/lead/update HTTP/1.1
Content-Type: application/json
APIKey: <your_api_key>

{
  "lead_id": "IEQ000100234",
  "updated_by": 1,
  "events": [12],
  "dealer_id": "67890",
  "branch_id": 1,
  "area": "560002",
  "city": "Bangalore",
  "customer_state": "Karnataka"
}
```

**Response (200 — Transfer successful, new child lead created):**
```json
{
  "Message": "Success",
  "RequestId": 100238,
  "LeadId": "IEQ000100238",
  "Status": 200
}
```

---

### 13.6 Lead Update — Follow-Up Logged

**Use case:** Call centre agent logs a follow-up after speaking with the customer.

**Request:**
```
POST /api/lead/update HTTP/1.1
Content-Type: application/json
APIKey: <your_api_key>

{
  "lead_id": "IEQ000100234",
  "updated_by": 5,
  "events": [5],
  "status": "follow_up",
  "follow_up": {
    "follow_up_method": "phone",
    "disposition": "interested",
    "sub_disposition": "will_visit_showroom",
    "next_follow_up_date": "2026-06-25 10:00:00.000",
    "customer_voice": "Customer confirmed visit this Saturday",
    "qualification": "hot"
  }
}
```

**Response (200):**
```json
{
  "Message": "Success",
  "RequestId": 100239,
  "LeadId": "IEQ000100234",
  "Status": 200
}
```

---

### 13.7 Lead Update — Invalid Lead ID

**Use case:** System tries to update a lead that doesn't exist.

**Request:**
```
POST /api/lead/update HTTP/1.1
Content-Type: application/json
APIKey: <your_api_key>

{
  "lead_id": "IEQ999999999",
  "updated_by": 1,
  "events": [1],
  "status": "test_ride_booked"
}
```

**Response (400):**
```json
{
  "Message": "INVALID_LEAD_ID",
  "RequestId": 100240,
  "LeadId": "",
  "Status": 400
}
```

---

### 13.8 Webhook Verification — Facebook

**Use case:** Facebook verifying the webhook URL during app setup.

**Request:**
```
GET /api/b2b/lead?hub.mode=subscribe&hub.challenge=abc123xyz&hub.verify_token=lms HTTP/1.1
Host: ls-acquisition.azurewebsites.net
```

**Response (200):**
```
abc123xyz
```

---

### 13.9 Communications Event

**Use case:** Marketing automation system reports that an SMS was delivered.

**Request:**
```
POST /api/lead/comms HTTP/1.1
Content-Type: application/json

{
  "LeadId": "IEQ000100234",
  "Mobile": "8765432109",
  "BrandCodes": [3],
  "EventId": 101,
  "Response": "delivered",
  "ResponseDate": "2026-06-22T11:00:00Z",
  "ActivityName": "Welcome SMS",
  "JourneyName": "New Lead Welcome",
  "CampaignName": "Jupiter_June2026",
  "SourceId": 1,
  "Medium": "sms",
  "Category": "transactional",
  "ActivityType": "send"
}
```

**Response (200):**
```json
{
  "Message": "Success",
  "RequestId": 100241,
  "LeadId": "IEQ000100234",
  "Status": 200
}
```

---

### 13.10 Lead One-View Timeline

**Use case:** Support agent looking at the full history of a lead.

**Request:**
```
POST /api/leads/one-view HTTP/1.1
Content-Type: application/json

{
  "leadId": "IEQ000100234",
  "sources": null,
  "events": null,
  "sort_by": "desc"
}
```

**Response (200):**
```json
[
  {
    "event_id": 12,
    "event_name": "Dealer Transfer",
    "source_id": 1,
    "created_at": "2026-06-23T09:15:00",
    "metadata": "{\"old_dealer\":\"12345\",\"new_dealer\":\"67890\"}"
  },
  {
    "event_id": 5,
    "event_name": "Follow-up Logged",
    "source_id": 5,
    "created_at": "2026-06-22T15:30:00",
    "metadata": "{\"disposition\":\"interested\",\"qualification\":\"hot\"}"
  },
  {
    "event_id": 1,
    "event_name": "Lead Created",
    "source_id": 1,
    "created_at": "2026-06-22T09:15:05",
    "metadata": "{\"brand_code\":3,\"dealer_id\":\"12345\"}"
  }
]
```

---

### 13.11 Dealer Lookup

**Use case:** Internal tool searching for iQube-enabled dealers.

**Request:**
```
POST /dealers HTTP/1.1
Content-Type: application/json

{
  "DealerId": null,
  "All": 0,
  "TwoWheeler": 0,
  "Iqube": 1,
  "PageNumber": 1,
  "PageSize": 10
}
```

**Response (200):**
```json
{
  "Message": "Success",
  "Response": [
    {
      "sap_dealer_code": "12345",
      "name": "TVS - Anna Nagar",
      "city": "Chennai",
      "state": "Tamil Nadu",
      "pincode": "600040",
      "iqube": 1,
      "ems": 1
    },
    {
      "sap_dealer_code": "12346",
      "name": "TVS - T Nagar",
      "city": "Chennai",
      "state": "Tamil Nadu",
      "pincode": "600017",
      "iqube": 1,
      "ems": 1
    }
  ],
  "Status": 200
}
```

---

## Appendix: OpenAPI Summary (Swagger-Friendly)

Below is a condensed OpenAPI 3.0-style summary of the primary endpoint for tooling and code generation purposes.

```yaml
openapi: 3.0.3
info:
  title: TVS Motor LMS — Lead Acquisition API
  version: 2.0.1
  description: >
    Receives, validates, and processes vehicle purchase leads from websites,
    aggregators, Facebook Lead Ads, and Google Ads lead forms.

servers:
  - url: https://ls-acquisition-dev.azurewebsites.net
    description: Development
  - url: https://ls-acquisition-uat.azurewebsites.net
    description: UAT
  - url: https://ls-acquisition.azurewebsites.net
    description: Production

paths:
  /api/lead:
    post:
      summary: Submit a new lead
      description: >
        Primary lead intake endpoint. Accepts lead data from any source,
        validates, checks for duplicates, persists, and dispatches for
        async processing to EMS, CRM, and Finance systems.
      parameters:
        - name: APIKey
          in: header
          required: true
          schema:
            type: string
        - name: countryCode
          in: header
          required: false
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LeadRequestModel'
      responses:
        '200':
          description: Lead accepted (or duplicate detected)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ServerResponse'
        '400':
          description: Validation failure
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ServerResponse'
        '500':
          description: Internal server error

  /api/lead/update:
    post:
      summary: Update an existing lead
      description: >
        Updates lead status, dealer assignment, follow-up, test ride,
        or invoice details for an existing lead.
      parameters:
        - name: APIKey
          in: header
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LeadUpdateRequestModel'
      responses:
        '200':
          description: Update successful
        '400':
          description: Lead not found or validation failure

  /api/b2b/lead:
    get:
      summary: Facebook webhook verification
      description: >
        Called by Facebook during webhook registration.
        Returns hub.challenge if verify_token matches.
      parameters:
        - name: hub.mode
          in: query
          schema:
            type: string
        - name: hub.challenge
          in: query
          schema:
            type: string
        - name: hub.verify_token
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Challenge returned
        '400':
          description: Invalid verification token
    post:
      summary: Receive webhook events (Facebook/Google)
      description: >
        Receives lead form submission events from Facebook Lead Ads
        or Google Ads. Auto-routes to the correct handler based on
        payload structure.
      responses:
        '200':
          description: Lead processed
        '400':
          description: Processing error

components:
  schemas:
    LeadRequestModel:
      type: object
      required:
        - source_id
        - enquiry_date
      properties:
        customer_name:
          type: string
          maxLength: 100
        mobile_number:
          type: string
          pattern: '^\d{10}$'
        email_id:
          type: string
          format: email
        source_id:
          type: integer
        brand_code:
          type: integer
        model_id:
          type: string
        part_id:
          type: string
        dealer_id:
          type: string
        branch_id:
          type: string
        area:
          type: string
          description: Customer 6-digit pincode
        city:
          type: string
        customer_state:
          type: string
        enquiry_date:
          type: string
          format: date-time
          description: 'Format: yyyy-MM-dd HH:mm:ss.fff (UTC)'
        finance:
          type: string
          enum: ['true', 'false']
        interested_brand:
          type: array
          items:
            $ref: '#/components/schemas/InterestedBrand'
        test_rides:
          type: array
          items:
            $ref: '#/components/schemas/TestRide'

    LeadUpdateRequestModel:
      type: object
      required:
        - lead_id
        - updated_by
        - events
      properties:
        lead_id:
          type: string
          description: internet_enquiry_id of the lead
        updated_by:
          type: integer
        events:
          type: array
          items:
            type: integer
        status:
          type: string
        dealer_id:
          type: string
        branch_id:
          type: integer

    ServerResponse:
      type: object
      properties:
        Message:
          type: string
        RequestId:
          type: integer
          format: int64
        LeadId:
          type: string
        Status:
          type: integer

    InterestedBrand:
      type: object
      properties:
        brand_code:
          type: integer
        model_id:
          type: string
        part_id:
          type: string

    TestRide:
      type: object
      properties:
        brand_code:
          type: integer
        model_id:
          type: string
        part_id:
          type: string
        ride_type:
          type: string
        ride_scheduled_date:
          type: string
          format: date-time
```

---

*End of API Specification Document.*

*This document reflects the API surface as of July 2026. Update when endpoints are added, modified, or deprecated.*

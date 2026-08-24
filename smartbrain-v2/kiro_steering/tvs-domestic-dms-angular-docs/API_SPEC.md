# DMS Domestic — API Specification

> Authored against `.kiro/steering/API_SPEC.md`. OpenAPI/Swagger 3.0-friendly.
>
> **Source repos**
> - .NET Web API (primary source of endpoints): `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`
> - Angular Frontend (client-side consumption): `D:\DMS_DOMESTIC\ANGULAR_DMS`
>
> **Companion diagrams**
> - [Endpoint Map](../diagrams/api-endpoint-map.md)
> - [Request Sequence](../diagrams/api-request-sequence.md)
> - [Auth Sequence](../diagrams/api-auth-sequence.md)
> - [External Dependencies](../diagrams/api-external-dependencies.md)
>
> ⚠️ No secrets, keys, tokens or connection strings appear in this document. All credential values are shown as placeholders such as `<TOKEN>`.

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | OnlineDMS-WebAPI (DMS Domestic) |
| Repo | D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI |
| Team | CPShopBuy - Squad 3 (Retail - Inventory, Invoice, Delivery & Return) |
| Tech Lead | Ankit.Anjan |
| Deployment | Azure App Service + Azure API Management (APIM) |
| Base URL (prod) | https://prod-onlinedms.tvsmotor.net/OnlineSalesAPI |
| Framework | ASP.NET Web API (.NET Framework 4.7.2) |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | BibinSam Peter | bibinsam.peter@tvsmotor.com |
| Tech Lead | Ankit Anjan | Ankit.Anjan@tvsmotor.com |
| Dev Team | CPB3 - DMS Domestic Engineering | Jira: CPB3 Board |
| QA Lead | AshokKumar K | ashokkumar.k@tvsmotor.com |
| On-call | Rotational | Teams: #dms-support |
| Vendor (if external) | TVSD.AI | varsha.bagewadi@tvsd.ai |

---

## 2. My API Endpoints (Inbound) — Who Calls Them

### Auth & Session

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `Login/CheckLoginValidationUMS` | None (bootstrap) | Validate UMS login and return dealer/session context | Angular DMS, C# DMS Client |
| POST | `OTP/...` (OTPController) | Bearer JWT | Generate & send OTP for PSF closure | Angular DMS Service Module |
| POST | `JobCard/DSClosure_OTP` | Bearer JWT | DS Closure OTP generation | Angular DMS, C# DMS |

### Vehicle Master

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `Vehicle/SaveVehicle` | Bearer JWT | Create / update a vehicle master record | Angular DMS, C# DMS |
| GET | `Vehicle/GetVehicleDetails` | Bearer JWT | Fetch vehicle by ID + dealer context | Angular DMS, TVS Connect App |
| GET | `Vehicle/VehicleSearch` | Bearer JWT | Search vehicles by frame/engine/customer | Angular DMS, TVS Connect App, External APIs |
| GET | `Vehicle/GetVehicleDetailsByTrackingDeviceId` | Bearer JWT | Get vehicle by tracking device | TVS Connect App |
| GET | `Vehicle/CheckPremiumStatus` | Bearer JWT | Check premium model status | Angular DMS |

### Vehicle Invoice & Sales

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `Sales/...` (SalesProcessController) | Bearer JWT | Sales enquiry, booking, invoice operations | Angular DMS, C# DMS |
| POST | `MultiVehicleInvoice/...` | Bearer JWT | Multi-vehicle invoice operations | Angular DMS |
| POST | `VehicleReturn/SaveVehicleReturn` | Bearer JWT | Save vehicle return | Angular DMS |
| POST | `VehicleReturn/SearchInvoiceNo` | Bearer JWT | Search invoice for return | Angular DMS |

### Voucher / Accounting

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `Voucher/SaveVoucher` | Bearer JWT | Save accounting voucher | Angular DMS, C# DMS |
| POST | `Voucher/CreatePaymentReceipt` | Bearer JWT | Create payment receipt | Angular DMS |
| POST | `Voucher/ReverseReceipt` | Bearer JWT | Reverse a receipt voucher | Angular DMS |
| POST | `Voucher/getBookingVoucherList` | Bearer JWT | Get booking voucher list | Angular DMS |

### Vendor Master

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `VendorMaster/SaveVendorMaster` | Bearer JWT | Save vendor master record | Angular DMS |
| POST | `VendorMaster/GetVendorDetails` | Bearer JWT | Get vendor details | Angular DMS |
| POST | `VendorMaster/GetAllVendorDetails` | Bearer JWT | Get all vendors | Angular DMS |

### Webhook / Inbound Events

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `Webhook/ATP/*` | Bearer JWT | ATP allocation events | ATP Service |
| POST | `Webhook/BookingEngine/*` | Bearer JWT | Booking engine 2.0 events | Booking Service (BS) |
| POST | `Webhook/BookingService/*` | Bearer JWT | Booking service events | Booking Service (BS) |
| POST | `Webhook/EnquiryService/*` | Bearer JWT | Enquiry/lead events | EMS / LMS |
| POST | `Webhook/CWIService/*` | Bearer JWT | CWI events | CWI Service |
| POST | `Webhook/NotificationService/*` | Bearer JWT | Notification callbacks | DIGI Notification Service |

### Service / Job Card

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST/GET | `JobCard/...` (137 endpoints) | Bearer JWT | Job card CRUD, service operations | Angular DMS, C# DMS |
| POST/GET | `ServiceProcess/...` (84 endpoints) | Bearer JWT | Service process management | Angular DMS |
| POST/GET | `ServiceClaims/...` (63 endpoints) | Bearer JWT | Service claim processing | Angular DMS |

### Parts

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST/GET | `Parts/...` (48 endpoints) | Bearer JWT | Parts inventory, GRN, ordering | Angular DMS, C# DMS |
| POST/GET | `OtherVendorGRN/...` (13 endpoints) | Bearer JWT | Other vendor GRN | Angular DMS |

---

## 3. Outbound (Who I Call)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| UMS / Azure AD B2C | POST | UMS token validation endpoint | Token validation + role resolution on every request |
| Azure API Management (APIM) | POST | APIM token acquisition | Gateway token management |
| Booking Service (BS) | POST | BS API endpoints | Push vehicle allocation, payment, invoice events to BS |
| DA Report Service | POST | `Generate_DA_ReportToken` | Generate dealer analytics report token |
| SAP / ZMC | SOAP | SAP Service References | ERP integration (GRN, invoice, inventory sync) |
| Oracle (Legacy) | SOAP | OnlineDmsOracleService | Legacy data reads |
| Azure Blob Storage | REST | Blob upload/download endpoints | File upload/download (invoices, documents) |
| SendGrid | REST | SendGrid API | Email notifications (invoice confirmations, alerts) |
| Infobip / TinySMS / Mahale | REST | SMS gateway endpoints | SMS notifications (OTP, booking confirmations) |
| DigiSigner | REST | DigiSigner API | Digital signature for documents |
| EMS (Enquiry Management) | REST | EMS API | Enquiry/lead status sync |
| NGD | REST | NGD API | New Gen Dealer integration |
| ATP Service | REST | ATP API | Available-to-Promise vehicle allocation |
| BookingEngine 2.0 | REST | BE 2.0 API | Booking lifecycle management |
| Notification Service (DIGI) | REST | DIGI Notification API | SMS/notification abstraction layer |
| Application Insights / OTLP | REST | Telemetry endpoints | Logging & monitoring via OpenTelemetry |
| Insurance Partners | SOAP/REST | Insurance APIs | Insurance policy generation |
| HSRP Service | REST | HSRP API | High Security Registration Plate events |
| TVS Connect App Backend | REST | Connect App API | Vehicle onboarding, customer data |
| Marketplace (Flipkart, etc.) | REST | Marketplace APIs | Marketplace booking sync |

---

## 4. Events & Messaging

### Topics This Service Publishes To

| Topic/Queue | Events | Format |
|-------------|--------|--------|
| Azure Service Bus: `booking-events` | BOOKING_CREATED, BOOKING_CONSUMED, BOOKING_CANCELLED | JSON |
| Azure Service Bus: `vehicle-events` | VEHICLE_ALLOCATION, PAYMENT_UPDATE, INVOICE_UPDATE | JSON |
| Azure Service Bus: `hsrp-events` | HSRP_CREATED, HSRP_UPDATED | JSON |
| Azure Service Bus: `invoice-events` | INVOICE_CREATED, INVOICE_CANCELLED | JSON |
| DMSFunctionApp (ServiceBusTopicFunction) | DMS domain events (async processing) | JSON |

### Topics This Service Subscribes To

| Topic/Queue | Events | Action |
|-------------|--------|--------|
| `booking-service-events` | BOOKING_PUSHED, BOOKING_UPDATED, BOOKING_CANCELLED | Create/update booking in DMS |
| `enquiry-events` | ENQUIRY_CREATED, LEAD_ASSIGNED | Create enquiry in DMS |
| `atp-events` | VEHICLE_ALLOCATED, ALLOCATION_CANCELLED | Update vehicle allocation status |
| `payment-events` | PAYMENT_SUCCEEDED, PAYMENT_FAILED, REFUND_COMPLETED | Update payment/receipt status |
| `cwi-events` | CWI_NOTIFICATION | Process CWI notifications |

---

## 5. External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| UMS / Azure AD B2C | Identity Provider | OAuth2 token validation + user roles | Client credentials / JWT |
| Azure API Management (APIM) | API Gateway | Rate limiting, token validation, routing | Subscription key + JWT |
| SAP ERP | ERP | GRN, invoice posting, inventory sync | SOAP / Service account |
| Oracle (Legacy) | Database | Legacy DMS data reads | Service account |
| Azure Blob Storage | Object Storage | Invoice PDFs, documents, images | SAS token / Managed Identity |
| Azure Service Bus | Message Broker | Async event publishing/subscribing | Connection string |
| SendGrid | Email Service | Invoice confirmations, alerts | API key |
| Infobip / TinySMS | SMS Gateway | OTP, booking confirmations, notifications | API key |
| DigiSigner | E-Signature | Digital document signing | API key |
| JusPay / Payment Partners | Payment Gateway | Payment processing for bookings | API key + HMAC |
| Booking Service (BS) | Internal Microservice | Booking lifecycle management | Bearer JWT |
| EMS / LMS | Internal Service | Enquiry & Lead management | Bearer JWT |
| ATP Service | Internal Service | Available-to-Promise allocation | Bearer JWT |
| Marketplace (Flipkart, Amazon) | E-Commerce | Marketplace booking ingestion | API key / OAuth |
| HSRP Service | Government Integration | High Security Registration Plate | API key |
| Optimove / OBL | Marketing | Campaign redirection/integration | API key |
| MeraFrnd / CRM | Loyalty | Referral code validation | SOAP / Basic Auth |
| Application Insights | Monitoring | APM, logging, tracing | Instrumentation key |
| OpenTelemetry (OTLP) | Observability | Distributed tracing, structured logs | OTLP endpoint |

---

## 6. Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| DMS MSSQL (Primary) | Microsoft SQL Server | Primary DMS data — dealers, vehicles, invoices, bookings, parts, accounts, masters |
| Oracle (Legacy) | Oracle DB | Legacy DMS reads (OnlineDmsOracleService) |
| Redis Cache | In-memory Cache | Session caching, frequently accessed masters |
| Azure Blob Storage | Object Storage | Invoice PDFs, insurance documents, uploaded files |
| Azure Service Bus | Message Queue | Async event processing between services |

### Key Database Tables (MSSQL)

| Table | Domain |
|-------|--------|
| `MDMS_VEHICLE` | Vehicle master |
| `MDMS_VEHICLE_INVOICE` | Vehicle invoices |
| `MDMS_DEALER` | Dealer master |
| `MDMS_DEALER_SETTING` | Dealer configuration |
| `MDMS_CUSTOMER` | Customer master |
| `MDMS_CUSTOMER_ADDRESS` | Customer addresses |
| `MDMS_INV_FRAME_TAX` | Invoice tax details |
| `MDMS_SAP_VEHICLE` | SAP vehicle sync |
| `MDMS_DEALER_VEHICLE_MAPPING` | Dealer-vehicle mapping |
| `MDMS_DEALER_AD_MAPPING` | AMD-AD dealer mapping |

---

## Conventions

The OnlineDMS Web API is an ASP.NET Web API (.NET Framework 4.7.2) using **attribute routing**. Endpoints follow a consistent shape:

- **Route template:** `[Route("{Controller}/{Action}")]` — e.g. `Vehicle/SaveVehicle`
- **HTTP verb:** Declared per action via `[HttpPost]` or `[HttpGet]`
- **Auth:** Endpoints decorated with `[Authentication]` (custom JWT/UMS filter) require a valid Bearer token
- **Response envelope:** Most endpoints return a uniform envelope:

```json
{
  "data": { },
  "message": "Success",
  "statusCode": 200
}
```

- **Base URLs (per environment):**
  - `hostWebApi` → OnlineDMS Sales/Core API (e.g. `https://<env>-onlinedms.tvsmotor.net/OnlineSalesAPI`)
  - `host` → Master web service (`.asmx`)
  - `uvdHost` → Parts/UVD API (`OnlinePartsAPI`)
  - All calls front-doored through Azure API Management (APIM)

---

## Authentication Requirements

| Mechanism | Where | Notes |
|---|---|---|
| **UMS / Azure AD B2C JWT** | `[Authentication]` filter | Primary scheme. Client obtains JWT from UMS, sends `Authorization: Bearer <TOKEN>`. APIM validates via `validate-jwt`. |
| **Token claim validation** | `SettingsController.ValidateToken` | Validates `DealerId / BranchId / UserId` claims against request body. Failure → `statusCode: 401`. |
| **APIM subscription key** | `Ocp-Apim-Subscription-Key` header | Required for all APIM-fronted calls. |
| **Haritha / Basic Auth** | `HarithaAuthenticationAttribute` | Used for specific partner/legacy endpoints. |

**Required headers for authenticated calls:**

```
Authorization: Bearer <TOKEN>
Ocp-Apim-Subscription-Key: <SUBSCRIPTION_KEY>
Content-Type: application/json
```

---

## Error Responses

| statusCode | message (example) | Cause |
|---|---|---|
| 200 | `"Success"` | Happy path |
| 200 | `"OTP Max limit is 3"` | Business-rule rejection (200 + message) |
| 401 | `"Unauthorized Access"` | Token claim validation failed |
| 500 | `"Invalid request payload"` | Body deserialized to null |
| 500 | `<exception message>` | Unhandled exception |

---

## Rate Limits

- **No application-level rate limiting** inside the Web API controllers
- **APIM** is the enforcement point — quota / spike-arrest / rate-limit policies at the gateway
- **Business throttles** — OTP max 3 per PSF; SMS monthly cap per mobile

---

## Sample Requests / Responses

### Login (unauthenticated bootstrap)

**Request**
```http
POST /OnlineSalesAPI/Login/CheckLoginValidationUMS HTTP/1.1
Host: <env>-onlinedms.tvsmotor.net
Content-Type: application/json
Ocp-Apim-Subscription-Key: <SUBSCRIPTION_KEY>

{
  "DEALER_ID": "1001",
  "BRANCH_ID": "1",
  "UMS_USER_ID": "<UMS_USER_ID>",
  "LOGIN_ID": "dealer.user"
}
```

**Response (200)**
```json
{
  "data": {
    "User": { "LOGIN_ID": "dealer.user", "ROLE_ID": 6, "DEALER_ID": 1001, "BRANCH_ID": 1 },
    "DealerDetail": { "DEALER_ID": 1001, "BRANCH_ID": 1, "COUNTRY_CODE": "IN", "FIN_YEAR": "2026" },
    "DA_Report_Token": "<TOKEN>"
  },
  "message": "Success",
  "statusCode": 200
}
```

### Authenticated POST — Save Vehicle

**Request**
```http
POST /OnlineSalesAPI/Vehicle/SaveVehicle HTTP/1.1
Authorization: Bearer <TOKEN>
Ocp-Apim-Subscription-Key: <SUBSCRIPTION_KEY>
Content-Type: application/json

{
  "DEALER_ID": 1001,
  "BRANCH_ID": 1,
  "COUNTRY_CODE": "IN",
  "FRAME_NO": "<FRAME_NO>",
  "ENGINE_NO": "<ENGINE_NO>",
  "ROW_STATE": "Created"
}
```

**Response (200)**
```json
{ "data": { "VEHICLE_ID": 55012 }, "message": "Success", "statusCode": 200 }
```

### Unauthorized example

```json
{ "data": "", "message": "Unauthorized Access", "statusCode": 401 }
```

---

## Endpoint Summary

69 controller files scanned. Total ~900+ attribute-routed endpoints.

| Controller | Route Prefix | Endpoints | GET | POST |
|---|---|---|---|---|
| JobCardController | JobCard | 137 | 87 | 50 |
| SalesProcessController | Sales | 101 | 35 | 66 |
| ServiceProcessController | Service | 84 | 63 | 21 |
| SalesInvoiceProcessController | Sales | 67 | 38 | 28 |
| ServiceClaimProcessController | ServiceClaims | 63 | 43 | 21 |
| PartsController | Parts | 48 | 32 | 16 |
| MultiVehicleInvoiceController | MultiVehicle | 28 | 6 | 21 |
| ExternalAPIController | Customer | 16 | 3 | 13 |
| SettingsController | Login | 16 | 8 | 8 |
| VehicleSchemeController | VehicleScheme | 14 | 2 | 12 |
| ATWSController | ATWS | 13 | 10 | 3 |
| OtherVendorGRNController | OtherVendorGRN | 13 | 3 | 10 |
| MasterController | Master | 12 | 7 | 5 |
| VehicleReturnController | VehicleReturn | 12 | 2 | 10 |
| VoucherController | Voucher | 11 | 0 | 11 |
| VendorMasterController | VendorMaster | 10 | 0 | 10 |

---

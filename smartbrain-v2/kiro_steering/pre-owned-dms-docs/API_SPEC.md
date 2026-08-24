# API Specification — PreOwnedDMS (UVD) [OpenAPI]

> Restored from Confluence: https://tvsmotorcompany.atlassian.net/wiki/pages/viewpage.action?pageId=5274075138

**Audience:** Integration / engineering partners. **Scope:** the `PreOwnedDMS` (`UVD.sln`) Web API (ASP.NET Web API 2 + OWIN). **Confidentiality:** no secrets/credentials reproduced; integrations described by config key name only. **Machine-readable contract:** `docs/openapi-uvd.yaml` (OpenAPI 3.0) in the repository.

## 1. Overview & Conventions

- **Style:** RESTful JSON over HTTP. Controllers derive from `ApiController` and use **attribute routing** (`[RoutePrefix("X")]` + `[Route("action")]`), so effective paths are `/{Prefix}/{action}` plus a fallback `api/{controller}/{id}`.
- **Live contract:** the service ships **Swagger/Swashbuckle**; each action is annotated with `[SwaggerResponse(HttpStatusCode.OK, Type = typeof(ResponseVM*))]`. Use Swagger UI for the always-current list.
- **Response envelopes:** `CodeMessage` (`statusCode`, `statusMessage`, `documentId`, `documentNo`), `OutputResult` (`statusCode`, `message`, `data`), and typed `ResponseVM*`.
- **Multi-tenancy:** most requests carry `dealerId`, `branchId`, often `userId`/`companyId`/`countryCode`.

This document details the **PurchaseOrder** module and authentication in full, plus representative endpoints from other modules. All modules follow identical conventions, so the patterns generalize across the ~40 controllers.

## 2. Authentication Requirements

![Auth Sequence](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5274075138/child/attachment/att5273878551/download)

**Token acquisition (brokered, 2 steps):**

1. `POST /Setting/tokenGeneration` with body `{ dealerId, branchId, roleId, loginId, userId }`. The service validates the principal (`BLLValidateToken`) and internally calls the OWIN OAuth server `/Token` with `grant_type=password` and those fields as form values.
2. Response: `{ "access_token": "<token>" }`. Token lifetime ≈ **1 day**.

**Authorized calls:** every business endpoint is decorated with `[Authorize]` (OWIN bearer validation) **and** calls `ValidateToken((ClaimsIdentity)User.Identity)`, which re-checks that claims `dealerId`, `branchId`, `roleId`, `loginId`, `userId` are present/non-zero. Send `Authorization: Bearer <access_token>`.

**Exceptions:** `tokenGeneration` is anonymous; some endpoints accept an `isAutomationRequest` flag that bypasses the interactive token check for trusted automation callers. Identity store is ASP.NET Identity (EntityFramework); OWIN endpoints under `api/Account/*`.

## 3. API Endpoint List (surface map)

![API Surface](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5274075138/child/attachment/att5274075161/download)

| Route prefix | Module | Representative endpoints |
| --- | --- | --- |
| `Setting` | Auth / settings | `tokenGeneration`, `Theme/saveAndUpdateTheme`, `Theme/getUserTheme` |
| `Procurement` | Procurement & valuation | `createProcurement`, `getCustomerInfo`, `getCityBasePrice`, `getEngineList`, `getOBVPrice`, `listProcurement` |
| `Sales` | Sales | `getSalesIntialInfo`, `createSalesEnquiry`, sale order / invoice / block |
| `PurchaseOrder` | Spare PO | `purchaseOrderTypeList`, `getVendorList`, `getPurchaseOrderList`, `getViewPurchaseOrder`, `savePO`, `updatePO`, `confirmPO`, `reconfirmPO`, `cancelPO`, `getPrintPO`, `UploadExcel` |
| `masterManagement` | Masters | `getCategory`, `createVehicleModelColor`, base-price/valuation maps |
| `JobCard`/`Service(s)` | Service & warranty | job card create/list, issue spares, labour, appointments |
| `SpareParts`/`SparePartGRN`/`SparePartAMD` | Parts | part master/help, stock, GRN |
| `PartsSaleOrder`/`PartsPickSlipInvoice`/`PartSalesReturn` | Parts sales | sale order, pick-slip invoice, returns |
| `Voucher`/`LedgerEntries`/`BankReconciliation`/`CreditDebitNoteReconciliation`/`TrackingPayment` | Accounts | vouchers, ledger, reconciliation |
| `Portal`/`WebOrder`/`ReferralVehicle` | Portal & web | order feeds, web orders, referral vehicles |
| `Image`/`DirectInvoice`/`Refurbishment`/`PhysicalInventory` | Misc | uploads, direct invoice, refurbishment, inventory |
| `Extentia` | Inbound sync | master-data sync (SHA-512 hash-token auth, not bearer) |
| `api/Account` | OWIN identity | `UserInfo`, `Logout`, `ManageInfo` |

## 4. Request Methods

- **GET** — reads/lookups; parameters in the query string.
- **POST** — creates/updates/searches and most "list" operations; `RequestVM*` JSON bodies (some also take query-string scalars).
- **Multipart POST** — file uploads (`UploadExcel`, document/image upload) via `multipart/form-data` with a `file` part.

## 5. Request Payloads (examples)

```json
// RequestVMTokenGeneration
{ "dealerId": 1234, "branchId": 1, "roleId": 5, "loginId": "jdoe", "userId": 98765 }

// RequestVMListOfPurchaseOrder
{ "dealerId": 1234, "branchId": 1, "sparePONumber": null, "potType": null,
  "fromDate": "2026-01-01T00:00:00", "toDate": "2026-06-01T00:00:00" }

// RequestVMSparePOConfirm (abridged)
{ "dealerId": 1234, "branchId": 1, "countryCode": "IND",
  "spare_PO_Id": 5001, "spare_PO_No": 80012, "companyId": 10,
  "vendorId": 7001, "vendorCategoryId": 2, "orderType": 1,
  "modifiedBy": "jdoe", "IS_POMS_ENABLED": true,
  "SparesPODetails": [ { "partNo": "ABC123", "orderQty": 10, "invoicePrice": 250.00, "row_state": 1 } ] }
```

## 6. Response Payloads

```json
// CodeMessage envelope
{ "statusCode": 200, "statusMessage": "Success", "documentId": null, "documentNo": null }

// Token response
{ "access_token": "eyJ0eXAiOiJKV1CiLCJhbGciOi..." }
```

Typed responses are named `ResponseVM*` (e.g. `ResponseVMPuchaseOrderList`, `ResponseVMPOView`, `ResponseVMGetOBVPrice`) — shapes visible in Swagger and `UVD.VM/Response/*`.

## 7. Error Responses

| Status | When | Body |
| --- | --- | --- |
| `200 OK` | Success | `ResponseVM*` / `CodeMessage` |
| `204 No Content` | No records found (some list endpoints) | `{ statusCode: 204, statusMessage: "No Records Found" }` |
| `400 Bad Request` | Validation/guard failure | `{ statusCode: 400, statusMessage: "Bad Request" }` |
| `401 Unauthorized` | Missing/invalid token or failed scope check | empty / `CodeMessage` |
| `406 Not Acceptable` | Unsupported upload file type | `{ statusCode: 406, statusMessage: "Not Acceptable File" }` |
| `500 Internal Server Error` | Unhandled exception | `{ statusCode: 500, statusMessage: "Internal server error.." }` |

Errors are logged server-side via `ExceptionLogging` to `~/LogFiles/UVD-App-Error.txt`.

**Security note (defect to fix):** the `confirmPO` POMS-failure branch currently appends POMS endpoint/ID/password config values into the `500` message, leaking credentials. Remove from error messages and move to a secret store. Values are **not** reproduced here.

## 8. Validation Rules

Centralized in `UVD.Helper.Validator` (one boolean method per request type); controllers return `400` on `false`. Pattern: explicit guards (`== 0`, `== null`, `string.IsNullOrEmpty`, allowed-value checks). Some controllers use inline guards.

- **`validateConfirmPO`** — `dealerId`, `branchId`, non-empty `countryCode`, `spare_PO_Id`, `spare_PO_No`, `companyId`, `vendorId`, `orderType`, non-empty `modifiedBy`, non-empty `SparesPODetails`; each line requires `spare_PO_DET_Id` unless `row_state == RowState.Created`.
- **`CreateProcurement`** — dealer/branch/company/enquiry keys, non-empty customer name/city/mobile/address/state, `areaId`, `brandId`, `modelId`, `manu_year`, `partId`, `runningKMS`, `hpEndorsement`.
- **`ValCreateSalesInvoice`** — header keys, `TOT_AMT > 0`, single-unit part (`QTY == 1`), at least one GST component + percentage.
- **Inline GET guards** — e.g. `getViewPurchaseOrder` requires `dealerId > 0 && branchId > 0 && SparePOId > 0`.

## 9. Rate Limits & Idempotency

No application-level rate limiting exists in the codebase; throttling (if any) is at the **edge** (load balancer / API gateway / WAF) and is environment-specific. **Idempotency:** GETs are idempotent; writes (e.g. `confirmPO`) are guarded by server-side status checks plus an outbox/correlation-id pattern for POMS publishing so retries don't double-publish. No client idempotency key.

## 10. External API Dependencies

| System | Used by | Purpose | Auth pattern (key names only) |
| --- | --- | --- | --- |
| **POMS / IDP** | `IDPService` (confirm/reconfirm PO) | Publish spare purchase orders | Login token (`POMSTokenEndPoint`, `POMSID`, `POMSPassword`) + `X-Client-Id` |
| **SAP** | `SAPAccessoriesService` | Accessory orders / posting | OAuth client-credentials (`sap_token_url`, `sap_client_id`, `sap_client_secret`) |
| **Orange Book Value** | `Procurement/getOBVPrice` | Used-vehicle valuation | API token (`OBVToken`, `OBVPriceUrl`) |
| **Srichakra vendor API** | `confirmPO` | External tyre Sale Order creation | vendor-specific |
| **Azure** | `AzureBusinessService` | Token + storage | function code (`AzureTokenGenURL`, `AzureTokenGenCode`) |
| **Extentia** | `ExtentiaController` | Master-data sync (inbound) | SHA-512 daily hash token |
| **SMTP / SMS** | `EmailService`, SMS helper | Notifications / OTP | `SMTPHost`/`SMTPPort`/`SMTPUserID`, `SMS1`/`SMS2`/`SMS3` |

All integration calls force **TLS 1.2** and use `HttpClient`/`RestSharp`.

## 11. Sample Requests / Responses

```text
A. Acquire token
POST /Setting/tokenGeneration
Content-Type: application/json
{ "dealerId": 1234, "branchId": 1, "roleId": 5, "loginId": "jdoe", "userId": 98765 }
-> 200 OK
{ "access_token": "eyJ0eXAiOiJKV1Qi..." }

B. Search purchase orders
POST /PurchaseOrder/getPurchaseOrderList
Authorization: Bearer eyJ0eXAiOiJKV1Qi...
Content-Type: application/json
{ "dealerId": 1234, "branchId": 1, "fromDate": "2026-01-01T00:00:00", "toDate": "2026-06-01T00:00:00" }
-> 200 OK
{ "statusCode": 200, "statusMessage": "Success", "data": [ /* ResponseVMPuchaseOrderList */ ] }

C. View a purchase order (GET)
GET /PurchaseOrder/getViewPurchaseOrder?dealerId=1234&branchId=1&SparePOId=5001
Authorization: Bearer eyJ0eXAiOiJKV1Qi...
-> 200 OK { /* ResponseVMPOView */ }

D. Unauthorized (no token)
GET /PurchaseOrder/getViewPurchaseOrder?dealerId=1234&branchId=1&SparePOId=5001
-> 401 Unauthorized

E. Validation failure
-> 400 Bad Request { "statusCode": 400, "statusMessage": "Bad Request" }
```

## Appendix — OpenAPI & Diagram Regeneration

Machine-readable contract: `docs/openapi-uvd.yaml` (OpenAPI 3.0). Diagrams:

```bash
cd PreOwnedDMS
python -m pip install --user matplotlib
python docs\diagrams\gen_api_diagrams.py
```

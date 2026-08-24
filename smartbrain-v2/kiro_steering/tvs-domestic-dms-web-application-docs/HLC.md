# High Level Code (HLC) — MicroDMS.Web (DMS Domestic Web)

> High Level Code document for the **MicroDMS.Web** project (assembly `MicroDMS.UI`) — the ASP.NET Web Forms UI of the TVS Motor Dealer Management System (DMS Domestic) — and its referenced class libraries.
> Source: `MICRO_DMS/MicroDMS/MicroDMS.Web` and sibling projects in `MicroDMS.sln`.
>
> Companion diagrams (draw.io): [`diagram web/hlc-module-map.md`](../diagram%20web/hlc-module-map.md), [`diagram web/hlc-dependency-graph.md`](../diagram%20web/hlc-dependency-graph.md), [`diagram web/hlc-runtime-flow.md`](../diagram%20web/hlc-runtime-flow.md)

---

## 1. Application Overview

MicroDMS.Web is the **server-rendered Web Forms presentation tier** of DMS Domestic, used by TVS Motor channel partners (dealers / ASCs). It hosts the operational screens for **Sales, Service, Parts, Accounts, Masters, HO operations, Dashboards and Reports**, built with the Telerik RadControls suite.

The codebase follows a classic **layered (n-tier) architecture**.

### Logical Architecture

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hlc-system-architecture.png                            ║
     ║  (or use the existing PNG in diagram web/hlc-system-architecture.png)     ║
     ║                                                                            ║
     ║  To generate PNG from DrawIO:                                             ║
     ║  Run: diagram web/_render/generate_all_pngs.bat                           ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![System Architecture](../diagram%20web/hlc-system-architecture.png)

| Attribute | Value |
|---|---|
| Project | `MicroDMS.Web` (assembly / namespace `MicroDMS.UI`) |
| Style | ASP.NET **Web Forms** (`.aspx` / `.ascx` / `.master`) |
| Framework | .NET Framework **4.5.2** |
| UI toolkit | Telerik Web UI (RadControls), AjaxControlToolkit |
| Pattern | Page → BL → DAL → DB; DTOs via `BusinessEntities` |
| Auth | UMS (Azure AD B2C / OAuth2) + JWT; legacy session login |
| Solution role | One of 12 projects in `MicroDMS.sln`; depends on 9 shared libraries |

---

## 2. Module Summary

### 2.1 UI modules (folders in `MicroDMS.Web`)

| Module (folder) | Responsibility |
|---|---|
| `Sales/` | Enquiry, quotation, booking, vehicle invoice, vehicle return, stock transfer |
| `Parts/` | Spares GRN, issue, direct invoice, purchase return, schemes, stock |
| `Service/` | Job card, service appointment, PSF, warranty/FSC claim screens |
| `Accounts/` | Vouchers, receipts, ledgers, commission/registration payments, tally extract |
| `Masters/` | Customer, vehicle, employee, dealer/branch, RTO, tax, rack, vendor masters |
| `WebAdmin/` | Admin, permissions, change password, mobile job-card APK (`MobileJCAPP`) |
| `DashBoard/` · `Reports/` | Telerik report dashboards and report viewers |
| `DataMigration/` | Excel-based master/stock imports |
| `ConsentForm/` · `PrivacyPolicy/` | Consent and policy pages |
| `DealerTvsManage/` | TVS-side dealer management screens |
| `Webhook/` · `SMShelper/` | Inbound webhook handling and SMS helpers |
| `WebServices/` | ASMX AJAX endpoints powering Telerik combo-box lookups |
| `Controls/` | Reusable user controls (`.ascx`) embedded across pages |

### 2.2 Cross-cutting framework files (project root)

| File | Responsibility |
|---|---|
| `Global.asax(.cs)` | Application / session / error lifecycle events |
| `BasePage.cs`, `BasePageAdmin.cs` | Page base classes exposing `UserSession`, `AppLayer`, `AppConfigLayer`; enforce login |
| `BaseUserControl.cs` | Base for user controls |
| `ProjectConstants.cs` | Constants, UI messages, `EnumToList`, `DataBindingUtilities` (dropdown binding) |
| `Encryption64.cs`, `EncryptQueryString.cs` | Query-string encryption/decryption |
| `SMS.cs`, `TranslateText.cs`, `SpreadSheetService.cs` | SMS dispatch, localization, Excel export |
| `MainMaster.master` | Master page / UI shell |

### 2.3 Referenced libraries (the rest of the solution)

| Library | Responsibility |
|---|---|
| `MicroDMS.BusinessLayer` | ~166 `*BL` classes — business rules, orchestration, tax/posting logic |
| `MicroDMS.BusinessEntities` | ~297 DTO/entity classes (`*DO`) passed between layers |
| `MicroDMS.DataLayer` | ~140 `*DAL`/`*DH` classes + `DataAccessLayer` provider abstraction |
| `MicroDMS.EntityObjects` | Entity definitions / typed objects |
| `MicroDMS.CacheLibrary` | Cache helpers (master/lookup caching) |
| `MicroDMS.ConfigHelper` | `SessionLayer`, `ApplicationLayer`, `ConfigSettings` accessors |
| `MicroDMS.ExceptionManager` | Centralized logging and exception policy |
| `MicroDMS.Utilities` | Cross-cutting helpers |
| `MicroDMS.RadMessageBox` (VB) | Telerik message-box helper |

---

## 3. Folder Structure Explanation

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hlc-module-map.png                                     ║
     ║  Location: diagram web/hlc-module-map.png                                 ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Module Map](../diagram%20web/hlc-module-map.png)

```
MicroDMS.Web/  (assembly MicroDMS.UI)
├── Global.asax(.cs)                # app lifecycle + error logging
├── Web.config / Web.*.config       # config + XDT transforms (secrets redacted)
├── MicroDMS.UI.csproj              # 9 ProjectReferences + NuGet refs
├── BasePage.cs / BasePageAdmin.cs  # page base classes (session/config/login)
├── BaseUserControl.cs
├── ProjectConstants.cs             # constants, messages, binding utilities
├── Encryption64.cs / EncryptQueryString.cs
├── Login.aspx / UMSDMSLogin.aspx / Logout.aspx   # auth entry points
├── default.aspx / Home.aspx / Settings.aspx       # landing
├── MainMaster.master               # UI shell
├── Sales/ Parts/ Service/ Accounts/ Masters/      # functional screens
├── WebAdmin/ DashBoard/ Reports/                  # admin, dashboards, reports
├── DataMigration/ DealerTvsManage/ Webhook/
├── WebServices/                    # ASMX AJAX lookups
├── Controls/                       # reusable .ascx controls
├── App_Themes/ App_GlobalResources/  # themes + localization
├── images/ js/ XmlLiterals/        # static assets + literal cache
├── Service References/ Web References/  # SOAP / legacy refs
└── Properties/AssemblyInfo.cs
```

Layer separation is by **project**, not by folder: UI pages live in `MicroDMS.Web`; rules in `*.BusinessLayer`; SQL/Oracle access in `*.DataLayer`. Data flows as DTOs from `*.BusinessEntities`.

---

## 4. Core Business Workflows

| Workflow | UI module | BL → DAL chain (representative) |
|---|---|---|
| **Vehicle Sales** | `Sales/` | `EnquiryMasterBL`/`BookingBL`/`SalesVehicleInvoiceBL` → `EnquiryMasterDAL`/`BookingDAL`/`SalesVehicleInvoiceDAL` |
| **Service Job Card** | `Service/` | `JobCardBL` → `JobCardDAL`/`JobCardDH`; invoicing via `JobCardInvoiceBL` → `JobCardInvoiceDAL` |
| **Parts / Spares** | `Parts/` | `SparesGRNBL`/`SparesIssueBL`/`DirectInvoiceBL` → `SparesGRNDAL`/`SpareIssueDAL`/`DirectInvoiceDAL` |
| **Warranty / FSC Claims** | `Service/` | `ASCWarrantyClaimBL`/`FSCClaimBL` → `ASCWarrantyClaimDAL`/`FSCClaimDAL` |
| **Accounts / Posting** | `Accounts/` | `VouchersBL` + `*AccountPosting` (`SaleInvoiceAccountPosting`, `ServiceInvoiceAccountPosting`) → `PostManagerDAL` |
| **Taxation (GST)** | cross-cutting | `TaxProcessor`/`GSTTaxProcessor` + `TaxMapFinder`/`TaxGroupFinder` → `TaxMasterDAL` |
| **Masters** | `Masters/` | `CustomerMasterBL`/`VehicleBL`/`EmployeeMasterBL` → matching `*DAL` (+ `*_MDP_DMS_DAL` MDM variants) |
| **Data Migration** | `DataMigration/` | `ExcelUploadBL`/`StockUploadBL` → `ExcelUploadDAL`/`StockUploadDAL` |
| **Authentication** | `UMSDMSLogin.aspx` | `UMSIntegrationBL` → `UMSIntegrationDAL`; token via RestSharp to UMS |

Common pattern: a page event handler builds a `*DO` DTO from RadControls, calls a `*BL` method, which delegates to a `*DAL` method that executes a stored procedure / SQL through the `DataAccessLayer` provider, returning DTOs or `DataSet`s for binding back to the grid.

---

## 5. Key Services / Classes

### Presentation framework
- **`BasePage`** — base for all pages; exposes `UserSession` (`SessionLayer`), `AppLayer` (`ApplicationLayer`), `AppConfigLayer` (`ConfigSettings`); centralizes login checks in `OnInit`/`OnPreInit`.
- **`DataBindingUtilities`** (in `ProjectConstants.cs`) — uniform binding for `DropDownList`, `RadComboBox`, `GroupDropDownList`, checkbox/radio lists; `NumberToWords` helper.
- **`EnumToList`** — converts enums to bindable lists.

### Configuration / session
- **`SessionLayer`** — strongly-typed session accessors (`DEALERID`, `DEALERNAME`, `UMS_USER_ID`, user identity, etc.).
- **`ConfigSettings`** — strongly-typed `appSettings` accessors (page routes, flags, links).
- **`ApplicationLayer`** — application-scope values.

### Business layer (examples)
- **`JobCardBL`**, **`SalesVehicleInvoiceBL`**, **`SparesGRNBL`**, **`ASCWarrantyClaimBL`**, **`VouchersBL`** — workflow orchestration.
- **`TaxProcessor` / `GSTTaxProcessor`** and finder/holder helpers — GST computation strategy.
- **`*AccountPosting`** classes — accounting document posting rules.
- **`UMSIntegrationBL`**, **`EmailBL`**, **`SMSTemplateBL`** — integration-oriented services.

### Data layer
- **`DataAccessLayer`** (`DBFactoryHelper`, `SqlDataAccessLayer`, `OracleHelper`) — provider abstraction over SQL Server / Oracle with `SQLConnectionType` selection (OnlineDMS, Report, CentralPortal, Retail, FSCClaim, etc.).
- **`DALHelper`**, **`DeadLockRetryHelper`** — shared execution helpers and deadlock retry.
- **`*DAL`/`*DH`** — per-domain data access and data-helper pairs (e.g. `JobCardDAL`/`JobCardDH`).
- **`SAP_Operations` / `SAPDealerAPI`** — SAP-facing data operations.

---

## 6. Integration Summary

| Integration | Mechanism | Code touchpoints |
|---|---|---|
| **UMS (Azure AD B2C / OAuth2)** | RestSharp HTTP + JWT; browser redirect to UMS auth | `UMSDMSLogin.aspx.cs`, `UMSIntegrationBL`, `UMSIntegrationDAL` (`UMS_*` settings) |
| **SAP portals** | Web Dynpro deep links + service refs | SAP `*Link` app settings; `Service References/`; `SAP_Operations` |
| **SQL Server** | ADO.NET via `DataAccessLayer` | `*DAL` classes; `DMSConnection`/`DMSConnReport`/`DMSSecConnReport` |
| **Oracle** | OleDb / OracleClient | `OracleHelper`; `OracleConnection*` |
| **SMS / OTP** | HTTP to Airtel IQMS / Infobip | `SMS.cs`, `SMShelper/`, `SMSTemplateBL` |
| **Email** | SendGrid SMTP | `EmailBL` (`SMTP*` settings) |
| **Booking Engine / BS API** | OAuth2 client-credentials REST | `BE*` app settings, `BookingEngineApiBaseUrl` |
| **Reporting** | Telerik Reporting / ReportViewer | `Reports/`, `DashBoard/` |
| **PDF / docs** | PDFsharp / MigraDoc | warranty/invoice PDF generation |
| **Excel** | DocumentFormat.OpenXml | `SpreadSheetService.cs`, `ExcelUploadBL` |

> Secrets for these integrations live in `Web.config` and are **redacted** in all documentation. Reference them by key name only.

---

## 7. Dependency Overview

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hlc-dependency-graph.png                               ║
     ║  Location: diagram web/hlc-dependency-graph.png                           ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Dependency Graph](../diagram%20web/hlc-dependency-graph.png)

**Internal (ProjectReference):** `MicroDMS.BusinessLayer`, `MicroDMS.BusinessEntities`, `MicroDMS.DataLayer`, `MicroDMS.EntityObjects`, `MicroDMS.CacheLibrary`, `MicroDMS.ConfigHelper`, `MicroDMS.ExceptionManager`, `MicroDMS.Utilities`, `MicroDMS.RadMessageBox`.

**Third-party / NuGet & bin:**
- Telerik Web UI (RadControls), Telerik Reporting / ReportViewer
- AjaxControlToolkit
- `Microsoft.IdentityModel.*` + `System.IdentityModel.Tokens.Jwt` 6.11.1
- `Newtonsoft.Json`, `RestSharp`
- `PDFsharp` / `PDFsharp-MigraDoc-gdi`, `Portable.BouncyCastle`
- `DocumentFormat.OpenXml`, `MessagingToolkit.QRCode`
- Microsoft Enterprise Library 4.1 (Logging / Exception Handling / Caching)

---

## 8. Runtime Architecture

1. **Host:** IIS / IIS Express serves the compiled `MicroDMS.UI.dll` and `.aspx` pages.
2. **Lifecycle:** `Global.asax` handles `Application_Start`, `Session_*`, and `Application_Error` (centralized logging via `ExceptionManager` / Enterprise Library).
3. **Page execution:** every page derives from `BasePage`, which on `OnInit` wires `SessionLayer`/`ApplicationLayer`/`ConfigSettings` and enforces authenticated access.
4. **AJAX:** Telerik RadControls call `WebServices/*.asmx` (`ScriptService`, `EnableSession=true`) for type-ahead lookups (customers, parts, labour, complaints, frame numbers).
5. **Business call:** page handlers invoke `*BL`, which calls `*DAL`; the `DataAccessLayer` provider opens the correct connection (`SQLConnectionType`) and runs stored procedures/SQL with deadlock-retry.
6. **State:** in-process session holds dealer/user context; master lookups cached via `CacheLibrary`.
7. **Config:** `Web.config` `appSettings`/`connectionStrings` (with `Web.Debug/Release.config` transforms) read through `ConfigSettings`.

---

## 9. Important Entry Points

| Entry point | Role |
|---|---|
| `Global.asax` | Application/session/error events |
| `Login.aspx` | Legacy session login |
| `UMSDMSLogin.aspx` | UMS (Azure AD B2C) sign-in; token acquisition via RestSharp |
| `Logout.aspx` | Session teardown / UMS logout |
| `default.aspx` / `Home.aspx` | Landing pages (`DealerHomePage`) |
| `MainMaster.master` | Shared UI shell hosting all content pages |
| `WebServices/*.asmx` | AJAX lookup endpoints (`CustomerSearch`, `PartSearch`, `LabourSearch`, `ComplaintSearch`, `FrameNoCheck`, `FramenoAvailability`, `JobCarddetails`, `GetCustVehByVehInvDate`, `GetCustVehByVehModifyDate`) |

---

## 10. High-Level Data Flow

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hlc-runtime-flow.png                                   ║
     ║  Location: diagram web/hlc-runtime-flow.png                               ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Runtime Flow](../diagram%20web/hlc-runtime-flow.png)

```
Dealer (browser, Telerik UI)
   │  HTTP postback / AJAX (.asmx)
   ▼
MicroDMS.UI page  (BasePage → SessionLayer/ConfigSettings)
   │  build *DO (BusinessEntities)
   ▼
*BL  (MicroDMS.BusinessLayer)  ── tax/posting rules, validation ──┐
   │  call *DAL                                                    │ cache (CacheLibrary)
   ▼                                                               │ log (ExceptionManager)
*DAL / *DH  (MicroDMS.DataLayer)                                   ┘
   │  DataAccessLayer provider (SQLConnectionType)
   ▼
SQL Server (OnlineDMS / Report / Portal DBs) · Oracle
   ▲
   └── External: UMS (REST/JWT) · SAP portals · SMS · Email · Booking Engine
```

Reads return `DataSet`/DTO collections bound to RadGrid/RadComboBox; writes flow as DTOs into stored procedures, with accounting documents posted via `*AccountPosting` → `PostManagerDAL`.

---

_Source: MICRO_DMS / MicroDMS / MicroDMS.Web (MicroDMS.UI) and referenced libraries. Secrets redacted; class/file counts are approximate._

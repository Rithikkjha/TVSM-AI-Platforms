# MicroDMS.Web (MicroDMS.UI) — DMS Domestic Web

> Onboarding README for the **MicroDMS.Web** project — the legacy ASP.NET Web Forms UI of the TVS Motor Dealer Management System (DMS Domestic).
> Source: `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\MicroDMS.Web` (assembly name: `MicroDMS.UI`)
>
> Folder structure diagram: see [`diagram web/readme-folder-structure.md`](../diagram%20web/readme-folder-structure.md)

---

## 1. Application Overview

MicroDMS.Web is the **server-rendered Web Forms surface** of the DMS Domestic product used by TVS Motor channel partners (dealers / ASCs). It delivers the dealer-facing screens for Sales, Service, Parts, Accounts, Masters, HO operations and Reports, built on the Telerik RadControls UI suite.

| Attribute | Value |
|---|---|
| Project | `MicroDMS.Web` |
| Assembly / Root namespace | `MicroDMS.UI` |
| Tech | ASP.NET **Web Forms** (`.aspx`), C# |
| Target framework | .NET Framework **4.5.2** |
| UI toolkit | Telerik Web UI (RadControls), AjaxControlToolkit |
| Hosting | IIS / IIS Express (Library output, web project) |
| Auth | UMS (Azure AD B2C / OAuth2) + JWT, legacy session login |

It is one project inside the `MicroDMS.sln` solution and depends on shared class libraries (business, data, entities, utilities) described in [Section 8](#8-folder-structure). The companion REST surface (`OnlineDMS_WebAPI`) and Angular SPA are separate projects in the same repository.

**Major functional modules** (folders): `Sales/`, `Parts/`, `Masters/`, `WebAdmin/`, `DashBoard/`, `Reports/`, `Accounts/`, `ConsentForm/`, `DealerTvsManage/`, `Webhook/`, `DataMigration/`.

**AJAX/ASMX services** under `WebServices/` back Telerik combo-box lookups and integration calls: `CustomerSearch`, `PartSearch`, `PartrSearch`, `LabourSearch`, `ComplaintSearch`, `FrameNoCheck`, `FramenoAvailability`, `JobCarddetails`, `GetCustVehByVehInvDate`, `GetCustVehByVehModifyDate`.

---

## 2. Setup Instructions

### Prerequisites

| Tool | Version (recommended) |
|---|---|
| Visual Studio | 2019 / 2022 (ASP.NET & web dev workload) |
| .NET Framework Developer Pack | 4.5.2 (4.7.2+ runtime works) |
| IIS Express | 10+ (ships with VS) |
| Telerik UI for ASP.NET AJAX | matching `Telerik.Web.UI` referenced version |
| SQL Server access | provided by ops (see connection strings) |
| Oracle client (optional) | for `OracleConnection*` flows |
| NuGet | bundled with VS |

### Get the code

```bash
git clone <MICRO_DMS repo URL> MicroDMS
# Open MicroDMS\MicroDMS.sln in Visual Studio; allow NuGet restore
```

NuGet packages used by this project (`packages.config`): `Microsoft.IdentityModel.*` + `System.IdentityModel.Tokens.Jwt` (6.11.1), `Newtonsoft.Json`, `PDFsharp` / `PDFsharp-MigraDoc-gdi`, `Portable.BouncyCastle`, `RestSharp`.

> Some references resolve from the local `bin/` (e.g. `Telerik.Web.UI`, `AjaxControlToolkit`, `MessagingToolkit.QRCode`, Enterprise Library DLLs) and from `..\packages\`. Restore the `bin/` reference DLLs from artifact storage if a fresh clone is missing them.

> **Never commit real values** for any setting in [Section 4](#4-environment-variables).

---

## 3. Local Development Steps

1. Open `MicroDMS\MicroDMS.sln` in Visual Studio.
2. Set **MicroDMS.UI** (`MicroDMS.Web`) as the startup project.
3. Confirm `Web.config` `connectionStrings` and `appSettings` point at a **dev/staging** database and dev UMS endpoints (do not use production values locally).
4. Press **F5** → IIS Express hosts the site.
5. Land on the login entry point:
   - `Login.aspx` — legacy login, or
   - `UMSDMSLogin.aspx` — UMS (Azure AD B2C) sign-in handoff.
6. After auth, `Home.aspx` is the dealer landing page (`DealerHomePage` app setting).

Tip: the project mixes absolute and `localhost` URLs in `appSettings` (e.g. `UMS_token_auth`, `OnlineImagePath`). Point these at your local API/image hosts while developing.

---

## 4. Environment Variables

Configuration lives in **`Web.config`** (`appSettings` + `connectionStrings`), with environment overrides in `Web.Debug.config` / `Web.Release.config` (XDT transforms). **All values must be treated as secrets — only key names are listed below; values are redacted (`<REDACTED>`).**

### Connection strings (`<connectionStrings>`)

| Name | Purpose |
|---|---|
| `DMSConnection` | Primary SQL Server (OnlineDMS) |
| `DMSConnReport` | Reporting (read) connection |
| `DMSSecConnReport` | Secondary read-only reporting replica |
| `OracleConnection` / `OracleConnectionClient` | Oracle (legacy / specific flows) |
| `FSCOTPConnection` | FSC OTP / claims DB |
| `CENTRALPORTALCONN` | Central Portal DB |
| `RETAILSCONN` | Retails DB |
| `OracleSQLPortal` | CWI portal DB |
| `OnlineDMS2`, `OfflineDMS2`, `SqlPortalCon` | Additional/legacy DB targets |

> All connection strings embed server, user id and password — **never expose**. Encrypt with `aspnet_regiis -pe connectionStrings` per environment or move to a secret store.

### Key `appSettings` (names only)

| Category | Keys (examples) |
|---|---|
| Auth / UMS | `UMS_token_auth`, `UMS_Auth_Base_URL`, `UMS_Auth_Token_Validate_URL`, `UMS_AppId`, `ums_callback_URL`, `UMS_Param_added`, `UMS_logout`, `UMS_logout_AppId`, `UMSDMSLogin`, `NEW_EMPLOYEE_ID_UMS`, `ClientID_UMS`, `ClientSecret_UMS` |
| Booking Engine / BS API | `BEDMSClientID`, `BEDMSClientSecret`, `BEScope`, `BEGrantType`, `BETenantId`, `BEOCPAPIMSubscriptionKey`, `BookingEngineApiBaseUrl` |
| Email (SendGrid) | `SMTPUserID`, `SMTPPwd`, `SMTPPort`, `SMTPHost`, `EmailFrom`, `AlertEmailCC`, `EmailToList` |
| SMS / OTP | `isAirtelOTP`, `AirtelSms.*` (BaseUrl, Username, Password, AuthTokenSingle/Multi, DLT ids), `InfobipBaseURL`, `InfobipSenderId`, `Infobip_API_KEY`, `IsInfobip` |
| SAP / portal links | `SAPConn`, `DealerLedgerLink`, `PartPackingLink`, `OnlineWarrantyApprLink`, `ESugamLink`, `CreditNoteLink`, `WarrantyCostLink`, `GoodsAcknowledgement` |
| API keys / misc | `APIKEY`, `RecallUserID`, `RecallPassword`, `Partsplanmonthly`, `DMSPass`, report passwords (`*Pass`) |
| Page routing | `LoginURL`, `DealerHomePage`, `JobCardPage`, `BookingPage`, and many `*.aspx` route keys |
| Paths / storage | `OnlineImagePath`, `NewsFileUploadPath`, `ExcelUploadPath`, `WarrantyImages`, `PQFImage*` |
| Tax / business config | `TCSWithPAN`, `TCSWithoutPAN`, `GSTVehicleTaxPerc`, `WarrantyValidDays`, `FSCValidDays`, `AMCAmount` |

> The repository's current `Web.config` contains **live secrets** (DB passwords, SendGrid key, SMS auth tokens, UMS client secret, `APIKEY`). Before sharing this code externally, rotate and externalize these. Do not paste real values into docs, tickets, or commits.

---

## 5. Build Instructions

### Visual Studio
**Build → Build Solution** (Debug or Release). The web project output is `bin\` (assembly `MicroDMS.UI.dll`).

### MSBuild (CLI)

```bash
msbuild MicroDMS\MicroDMS.sln /p:Configuration=Release /p:Platform="Any CPU"
```

### Web Deploy package

```bash
msbuild MicroDMS\MicroDMS.Web\MicroDMS.UI.csproj ^
  /p:Configuration=Release ^
  /p:DeployOnBuild=true ^
  /p:WebPublishMethod=Package ^
  /p:PackageLocation=.\publish\MicroDMS.Web.zip
```

Build configurations available: `Debug|Any CPU`, `Release|Any CPU`, plus `x64` variants.

---

## 6. Deployment Steps

CI workflow: `MICRO_DMS/MicroDMS/.github/workflows/main.yml`.

Typical promotion flow:

1. Merge to the integration branch → CI builds the solution.
2. Produce the Web Deploy package (Section 5) for `MicroDMS.Web`.
3. Deploy the package to the target **IIS** site / app pool (.NET Framework 4.x, Integrated pipeline).
4. Apply the correct `Web.<Env>.config` transform so `connectionStrings`, UMS endpoints and external URLs match the environment.
5. Encrypt sensitive config sections in the target (`aspnet_regiis -pe connectionStrings` / `appSettings`) if not already done.
6. Smoke-test: UMS login → `Home.aspx` loads → one master lookup (e.g. `CustomerSearch.asmx`) → one transactional screen.

---

## 7. Testing Instructions

- Solution unit-test project: `MICRO_DMS/MicroDMS/MicroDMS.Tests`
- Run from Visual Studio **Test Explorer**, or:

```bash
vstest.console.exe MicroDMS\MicroDMS.Tests\bin\Release\MicroDMS.Tests.dll
```

Manual verification of ASMX services:

```bash
# Example: WebService1 health method
curl "https://<host>/WebServices/WebService1.asmx/HelloWorld"
```

> Most `WebServices/*.asmx` methods are `EnableSession = true` and expect an authenticated session; exercise them after logging in via the browser.

---

## 8. Folder Structure

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: readme-folder-structure.png                            ║
     ║  Location: diagram web/readme-folder-structure.png                        ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Folder Structure](../diagram%20web/readme-folder-structure.png)

High-level layout (full diagram in [`diagram web/readme-folder-structure.md`](../diagram%20web/readme-folder-structure.md)):

```
MICRO_DMS/MicroDMS/
├── MicroDMS.sln
├── MicroDMS.Web/                         # THIS PROJECT (assembly: MicroDMS.UI)
│   ├── MicroDMS.UI.csproj
│   ├── Global.asax(.cs)                  # App/session/error events
│   ├── Web.config / Web.Debug/Release.config
│   ├── packages.config
│   ├── BasePage.cs · BasePageAdmin.cs · BaseUserControl.cs   # Page base classes
│   ├── ProjectConstants.cs               # Constants, messages, EnumToList, DataBinding helpers
│   ├── Encryption64.cs · EncryptQueryString.cs               # Query-string crypto
│   ├── SMS.cs · TranslateText.cs · SpreadSheetService.cs
│   ├── Login.aspx · UMSDMSLogin.aspx · Logout.aspx           # Entry points
│   ├── default.aspx · Home.aspx · Settings.aspx
│   ├── MainMaster.master                 # Master page / shell
│   ├── Sales/                            # Sales screens
│   ├── Parts/                            # Parts/spares screens
│   ├── Masters/                          # Master data screens
│   ├── WebAdmin/                         # Admin (incl. MobileJCAPP)
│   ├── DashBoard/ · Reports/ · Accounts/ # Dashboards, reports, accounts
│   ├── ConsentForm/ · PrivacyPolicy/ · ConsentForm
│   ├── DealerTvsManage/ · DataMigration/ · Webhook/
│   ├── WebServices/                      # ASMX AJAX services (lookups/integration)
│   ├── Controls/ · Parts/ · Service/     # User controls & partials
│   ├── App_Themes/ · App_GlobalResources/ # Themes & localization
│   ├── images/ · js/ · XmlLiterals/      # Static assets & literal cache
│   ├── Service References/ · Web References/  # SOAP/legacy refs
│   ├── Errors/ · Help/ · HelpDocument/
│   └── Properties/AssemblyInfo.cs
│
└── Referenced class libraries (project references):
    ├── MicroDMS.BusinessLayer/           # Business logic
    ├── MicroDMS.BusinessEntities/        # DTO / entity classes
    ├── MicroDMS.DataLayer/               # ADO.NET data access
    ├── MicroDMS.EntityObjects/           # Entity definitions
    ├── MicroDMS.CacheLibrary/            # Cache helpers
    ├── MicroDMS.ConfigHelper/            # Config readers
    ├── MicroDMS.ExceptionManager/        # Centralized logging/exceptions
    ├── MicroDMS.Utilities/               # Cross-cutting helpers
    └── MicroDMS.RadMessageBox/ (VB)      # Telerik message-box helper
```

---

## 9. Common Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Build fails: `Telerik.Web.UI` / `AjaxControlToolkit` / `MessagingToolkit.QRCode` not found | `bin/` reference DLLs missing on fresh clone | Restore `bin/` DLLs from artifact storage; verify HintPaths in `MicroDMS.UI.csproj` |
| Build fails: Enterprise Library DLL not found | Microsoft Enterprise Library 4.1 not installed/copied | Install EntLib 4.1 or copy the referenced DLLs into `bin/` |
| `aspnet_compiler`/NuGet restore errors | Wrong target framework | Install .NET Framework 4.5.2 Developer Pack |
| Login loops / 401 after UMS | UMS endpoints or `UMS_AppId`/`ums_callback_URL` mismatch | Align `UMS_*` app settings with the environment; check `UMSDMSLogin.aspx` flow |
| 500 on master lookups (`*.asmx`) | DB connection down or wrong `DMSConnection` | Verify `connectionStrings`; check `LogFiles/` |
| Blank dropdowns / RadComboBox not loading | ASMX `ScriptHandlerFactory` mapping or session expired | Confirm `*.asmx` handler mapping in `Web.config`; re-login |
| SAP portal links fail | `*.tvsmotor.co.in` SAP link settings/network | Verify SAP link app settings and VPN/network reachability |
| SMS/OTP not delivered | Provider keys/toggles | Check `isAirtelOTP` / `IsInfobip` and provider creds (redacted) |
| Images not showing | `OnlineImagePath` points at `localhost` | Set environment-correct image host |

---

## 10. Maintainers / Contact

| Role | Name | Contact |
|---|---|---|
| Tech Lead — DMS Web | _<TBD>_ | _<email@tvsmotor.com>_ |
| Backend / API | _<TBD>_ | _<email@tvsmotor.com>_ |
| DevOps / Release | _<TBD>_ | _<email@tvsmotor.com>_ |
| Product Owner | _<TBD>_ | _<email@tvsmotor.com>_ |
| Support / Escalation | _<TBD>_ | _<email@tvsmotor.com>_ |

> Update placeholders before sharing externally.

---

_Source: MICRO_DMS / MicroDMS / MicroDMS.Web (MicroDMS.UI) and referenced class libraries. Secrets redacted._

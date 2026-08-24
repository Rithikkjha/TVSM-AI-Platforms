# DMS Domestic — Angular Frontend + OnlineDMS Web API

> Combined onboarding README for the **DMS Domestic Angular** application.
> Source repos:
> - Angular Frontend: `D:\DMS_DOMESTIC\ANGULAR_DMS`
> - .NET Web API: `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`
>
> Folder structure diagram: see [`diagrams/readme-folder-structure.md`](../diagrams/readme-folder-structure.md)

---

## 1. Application Overview

DMS Domestic is the Dealer Management System used by TVS Motor channel partners (dealers / ASCs) for the domestic market. The application is delivered in two cooperating tiers:

| Tier | Project | Tech | Purpose |
|---|---|---|---|
| Client | `AngularDMS` | Angular 6 + TypeScript, PrimeNG, Bootstrap, Electron (optional desktop build) | Dealer-facing UI for Sales, Service, Parts, Accounts, Master data, HO ops, Reports |
| Server | `OnlineDMS_WebAPI` | ASP.NET Web API on .NET Framework 4.7.2 (OWIN, Unity DI) | REST API backing all UI flows; orchestrates SAP, Oracle, UMS, Redis, Azure Blob, SendGrid, OTP, SMS providers |

The two repos are deployed and operated together as one product. The Angular SPA calls the Web API; the Web API calls SQL/Oracle/SAP/external services.

---

## 2. Setup Instructions

### Prerequisites

| Tool | Version (recommended) | Used by |
|---|---|---|
| Node.js | 8.x – 10.x (matches Angular CLI 6.1) | Angular |
| npm | 6.x | Angular |
| Angular CLI | 6.1.1 | Angular |
| .NET Framework | 4.7.2 (Developer Pack) | Web API |
| Visual Studio | 2019 / 2022 (with ASP.NET workload) | Web API |
| IIS Express / IIS | 10+ | Web API local hosting |
| SQL Server / Oracle access | provided by ops | Web API runtime |
| Redis (StackExchange.Redis) | 6.x | Caching layer |

### Get the code

```bash
# Frontend
git clone <ANGULAR_DMS repo URL> AngularDMS
cd AngularDMS/Work_In_Progress/Source_Code/AngularDMS
npm install

# Backend
git clone <MICRO_DMS repo URL> MicroDMS
# Open MicroDMS\MicroDMS.sln in Visual Studio and let NuGet restore
```

> Do **not** commit values for any settings listed in [Section 4](#4-environment-variables).

---

## 3. Local Development Steps

### Frontend (Angular)

From `AngularDMS/Work_In_Progress/Source_Code/AngularDMS/`:

```bash
npm start                # ng serve — http://localhost:4200/
npm run serve:dev        # use src/environments/environment.dev.ts
npm run serve:qa         # use src/environments/environment.qa.ts
npm run lint             # tslint
```

Optional desktop build (Electron):

```bash
npm install -g electron-packager
npm run ele-build        # produces dms-desktop
```

### Backend (Web API)

1. Open `MicroDMS\MicroDMS.sln` in Visual Studio.
2. Set **OnlineDMS_WebAPI** as the startup project.
3. Press **F5** → IIS Express hosts the API (default port from `Properties/launchSettings.json` / `.csproj`).
4. Confirm `Web.config` `connectionStrings`, `appSettings` and `RSAKeys/` are populated locally (see env section below).
5. Verify Swagger or `/api/...` controllers respond.

Tip: point the Angular `environment.dev.ts → hostWebApi` to your local Web API URL while developing both ends.

---

## 4. Environment Variables

Secrets are **not** stored in the repo. The placeholders below describe what each tier needs at runtime — do not fill values into source control.

### Angular — `src/environments/environment.<env>.ts`

| Key | Purpose |
|---|---|
| `production` | Build flag (true/false) |
| `host` | Master web service base URL (`*.asmx` legacy master) |
| `hostWebApi` | OnlineDMS Web API base URL |
| `uvdHost` | UVD / Parts API base URL |
| `umsLogin` | UMS auth UI base URL |
| `umsLogin_WebApi` | UMS auth API base URL |
| `umsLogout` | UMS logout URL |
| `ImageHost` | Image / blob host (Azure Storage CDN) |
| `timeApiBaseUrl` | External time service (used by some flows) |

### Web API — `Web.config` (`appSettings` + `connectionStrings`)

Key categories used at runtime (full list in `Web.config`):

- **Connection strings**: SQL Server primary, Oracle (where applicable)
- **SAP integration**: `SAPConn`, related SAP service endpoints under `Service References/OnlineDmsSapServices`
- **UMS / Auth**: JWT signing keys (under `RSAKeys/`), UMS endpoints, client credentials
- **APIM**: APIM token acquisition keys (`ApimTokenAcquisition.cs`, `ApimTokenDo.cs`)
- **Email**: SendGrid API key, sender, templates
- **SMS / OTP**: Infobip / TinySMS / Mahale provider keys, OTP secret
- **Redis**: connection string for `RedisCacheLayer.cs`
- **Azure Storage**: blob account / SAS for upload flows
- **Application Insights**: instrumentation key (in `ApplicationInsights.config`)
- **OpenTelemetry**: OTLP endpoint, resource attributes (`LogGenerationOTel.cs`, `OtelActivityModule.cs`)
- **Webhook**: signing secret used by `Webhook/`
- **Page-route constants**: many `appSettings` entries map legacy aspx page names — leave as-is unless changing routes

> Treat every value as a secret. Use IIS-encrypted config sections (`aspnet_regiis -pe appSettings`) or move sensitive keys to Azure Key Vault / environment variables for non-dev environments.

---

## 5. Build Instructions

### Frontend

```bash
npm run build           # default
npm run build:dev       # dev configuration
npm run build:qa        # qa configuration
npm run build:prod      # production (AOT, optimized, large heap)
```

Output: `AngularDMS/Work_In_Progress/Source_Code/AngularDMS/dist/`.

### Backend

- Visual Studio: **Build → Build Solution** (Debug or Release)
- CLI:

```bash
msbuild MicroDMS\MicroDMS.sln /p:Configuration=Release /p:Platform="Any CPU"
```

Web deploy package:

```bash
msbuild OnlineDMS_WebAPI\OnlineDMS_WebAPI.csproj ^
  /p:Configuration=Release ^
  /p:DeployOnBuild=true ^
  /p:WebPublishMethod=Package ^
  /p:PackageLocation=.\publish\OnlineDMS_WebAPI.zip
```

---

## 6. Deployment Steps

CI workflows live in each repo:

- `ANGULAR_DMS/AngularDMS/.github/workflows/AngularDMS.yml`
- `MICRO_DMS/MicroDMS/.github/workflows/main.yml`

Typical promotion flow:

1. Merge to the integration branch → CI builds the artifact.
2. **Frontend**: deploy `dist/` to the static host / Azure Storage static site / IIS virtual directory; update CDN if used.
3. **Backend**: deploy the Web Deploy package to the target IIS app pool (App Pool runs on .NET Framework 4.7.2). Run `aspnet_regiis -pe` to encrypt sensitive sections in target environment if not already done.
4. Update the Angular environment file's `hostWebApi`, `host`, `umsLogin*` to point at the matching environment.
5. Smoke-test: Login (UMS), one master fetch, one transactional save (e.g. JobCard list).

> Production builds use `extractCss`, AOT, hashed file names, and `--max_old_space_size=18000` for the build step.

---

## 7. Testing Instructions

### Frontend

```bash
npm test           # ng test — Karma + Jasmine, runs in Chrome
npm run e2e        # ng e2e — Protractor (legacy)
npm run lint       # tslint
```

Karma config: `src/karma.conf.js`. Spec files live alongside components (`*.spec.ts`).

### Backend

- Unit tests project: `MICRO_DMS/MicroDMS/MicroDMS.Tests`
- Run from Visual Studio **Test Explorer** or:

```bash
vstest.console.exe MicroDMS\MicroDMS.Tests\bin\Release\MicroDMS.Tests.dll
```

Manual API verification:

- Use Postman / `curl` against `https://<host>/OnlineSalesAPI/api/<controller>`
- Login flow first (UMS / JWT) to obtain bearer token, then exercise downstream endpoints.

---

## 8. Folder Structure

High-level layout (full diagram in [`diagrams/readme-folder-structure.md`](../diagrams/readme-folder-structure.md)):

```
DMS_DOMESTIC/
├── ANGULAR_DMS/
│   └── AngularDMS/
│       ├── .github/workflows/AngularDMS.yml      # Frontend CI
│       ├── package.json                           # root proxy package
│       └── Work_In_Progress/Source_Code/AngularDMS/
│           ├── angular.json                       # CLI workspace config
│           ├── package.json                       # actual deps + scripts
│           ├── main.js                            # Electron entry
│           ├── tsconfig.json / tslint.json
│           └── src/
│               ├── index.html, main.ts, polyfills.ts, styles.scss
│               ├── environments/                  # environment.[dev|qa|prod].ts
│               ├── assets/                        # images, icons, azure-storage shim
│               └── app/
│                   ├── app.module.ts, app.routing.ts, app.component.*
│                   ├── api-services/              # HTTP service layer
│                   ├── shared/, layout/, pipes/, directive/, service/
│                   ├── session/, Conviva-Service/, azure-storage/
│                   ├── sales/, service/, parts/, accounts/, master/
│                   ├── ho/, homedashboard/
│                   ├── dmsreports/, uvd-reports/, UVD/
│
└── MICRO_DMS/
    └── MicroDMS/
        ├── MicroDMS.sln
        ├── .github/workflows/main.yml             # Backend CI
        ├── DMSFunctionApp/                        # Azure Function (Service Bus topic worker)
        ├── MicroDMS.Web/                          # Legacy Web Forms surface
        ├── MicroDMS/                              # Web project (legacy)
        ├── MicroDMS.BusinessLayer/                # ~166 BL classes
        ├── MicroDMS.BusinessEntities/             # ~297 DTO/entity classes
        ├── MicroDMS.DataLayer/                    # ADO data access
        ├── MicroDMS.EntityObjects/                # Entity definitions
        ├── MicroDMS.ServiceLayer/                 # External service contracts
        ├── MicroDMS.CacheLibrary/                 # Redis cache helpers
        ├── MicroDMS.ConfigHelper/                 # Config readers
        ├── MicroDMS.ExceptionManager/             # Centralized exception handling
        ├── MicroDMS.RadMessageBox/                # UI helper (legacy)
        ├── MicroDMS.Utilities/                    # Cross-cutting helpers
        ├── MicroDMS.Tests/                        # Unit tests
        └── OnlineDMS_WebAPI/                      # PRIMARY API SURFACE
            ├── App_Start/                         # WebApiConfig, RouteConfig, FilterConfig, UnityResolver
            ├── Controllers/                       # ~67 REST controllers
            ├── Areas/, Models/, DTOs/, Enums/, Results/, Providers/
            ├── ExternalAPIs/                      # Outbound HTTP clients
            ├── EmailServices/, OtpServices/, SmsServices/, SMSHelper/
            ├── DealerFSCClaim/, Webhook/, WarrantyInvPDF/
            ├── Service References/                # SOAP refs (SAP, Oracle, ZMC, Insurance)
            ├── Web References/                    # legacy web refs
            ├── RSAKeys/                           # JWT keys (DO NOT COMMIT real keys)
            ├── Security/, Properties/, Content/, Scripts/, Views/
            ├── Web.config, Web.Debug.config, Web.Release.config
            ├── Global.asax(.cs)                   # OWIN startup
            ├── Authentication.cs, JwtAuthorizationFilterAttribute.cs,
            │   UMSAuthenticationAttribute.cs, HarithaAuthenticationAttribute.cs,
            │   BasicAuthenticationAttribute.cs   # Auth filters
            ├── ApimTokenAcquisition.cs, TokenManager*.cs, TokenValidation.cs
            ├── RedisCacheLayer.cs                  # Redis adapter
            ├── LogGenerationOTel.cs, OtelActivityModule.cs,
            │   TraceContextLogProcessor.cs        # OpenTelemetry hooks
            └── ApplicationInsights.config
```

---

## 9. Common Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `npm install` fails on `node-sass` / `node-gyp` | Node version too new for legacy Angular 6 / Python missing | Use Node 10.x; install Python 2.7 or windows-build-tools; clear `node_modules` and lockfile |
| `ng build:prod` runs out of memory | Heap default too low | Already set via `--max_old_space_size=18000`; on lower-RAM machines use `build:qa` |
| Angular page is blank after deploy | Wrong `--base-href` | QA/Prod builds set `--base-href ./`; verify host folder/virtual dir |
| API calls return CORS errors | `hostWebApi` mismatch or CORS not allowed for env | Check `WebApiConfig.cs` CORS / `Web.config` and update Angular `environment.<env>.ts` |
| 401 from API after login | UMS JWT not included or expired | Confirm `umsLogin*` URLs and `Authorization: Bearer ...` is sent; check `JwtAuthorizationFilterAttribute` logs |
| 500 on master fetch | DB connection / SAP RFC down | Check `connectionStrings` in `Web.config`, SAP `SAPConn`, `LogFiles/` |
| Redis not caching | Bad Redis connection string | Check `RedisCacheLayer.cs` log output; verify network/firewall |
| Build fails: `MessagingToolkit.QRCode.dll not found` | Missing local-only DLL in `bin/` | Restore the `bin/` reference DLLs from artifact storage |
| OpenTelemetry not exporting | OTLP endpoint env not set | Verify `LogGenerationOTel.cs` config; check Application Insights key |
| Electron build window blank | Wrong `--base-href` or missing `dist/` | Run `ng build` first; ensure `loadURL('file://.../dist/index.html')` resolves |

---

## 10. Maintainers / Contact

| Role | Name | Contact |
|---|---|---|
| Tech Lead — Frontend | _<TBD>_ | _<email@tvsmotor.com>_ |
| Tech Lead — Backend | _<TBD>_ | _<email@tvsmotor.com>_ |
| DevOps / Release | _<TBD>_ | _<email@tvsmotor.com>_ |
| Product Owner | _<TBD>_ | _<email@tvsmotor.com>_ |
| Escalation | _<TBD>_ | _<email@tvsmotor.com>_ |

> Update placeholders before sharing externally.

---

_Source: ANGULAR_DMS + OnlineDMS_WebAPI_

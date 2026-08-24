# README — PreOwnedDMS (UVD)

> Restored from Confluence: https://tvsmotorcompany.atlassian.net/wiki/pages/viewpage.action?pageId=5273288825

Onboarding-focused README for the **PreOwnedDMS (UVD)** repository — the Used-Vehicle Dealership platform in the TVS Motor DMS ecosystem. No secrets are included; configuration is described by key name only.

## 1. Application Overview

PreOwnedDMS is a stateless **ASP.NET Web API 2 (OWIN)** backend managing the full used-vehicle lifecycle for TVS Motor dealerships: **procurement → valuation → refurbishment → resale**, plus after-sales **service, spare parts, accessories, and accounting**. It is consumed by a mobile app and a dealer web portal, is multi-tenant by **dealer / branch**, and persists to **SQL Server** via stored procedures.

![Overview](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5273288825/child/attachment/att5274206232/download)

| Aspect | Detail |
| --- | --- |
| Platform | .NET Framework 4.5.2 / 4.6.1, ASP.NET Web API 2, OWIN |
| Database | Microsoft SQL Server (stored-procedure driven) |
| Auth | OWIN OAuth2 bearer tokens + per-request dealer/branch/user scope checks |
| API docs | Swagger / Swashbuckle |
| Build | MSBuild / Visual Studio 2019, NuGet `packages.config` |

## 2. Setup Instructions

**Prerequisites:** Windows + Visual Studio 2019 (or Build Tools) with .NET desktop/web workloads; .NET Framework 4.6.1 developer pack; IIS / IIS Express; access to a SQL Server instance with the DMS/UVD database (stored procedures provisioned); NuGet CLI.

```bash
git clone <repo-url> PreOwnedDMS
cd PreOwnedDMS
nuget restore UVD.sln
```

Open `UVD.sln` in Visual Studio. The startup project is **UVD** (the Web API).

## 3. Local Development Steps

1. Configure connection strings and integration keys in `UVD/Web.config` (see Environment Variables). Use a local/staging DB — never production.
2. Set **UVD** as the startup project; run with IIS Express (F5).
3. Browse the Swagger UI (via `App_Start/SwaggerConfig.cs`) to exercise endpoints.
4. Acquire a token: `POST /Setting/tokenGeneration` with `{ dealerId, branchId, roleId, loginId, userId }`, then send `Authorization: Bearer <token>` on subsequent calls.

Most endpoints require a valid bearer token plus a dealer/branch/user scope check, so seed a valid user/dealer in your dev DB.

## 4. Environment Variables / Configuration

Configuration is read at runtime from `UVD/Web.config` (`<connectionStrings>` and `<appSettings>`). **Do not commit real secrets** — use per-environment config or a secret store.

| Key | Purpose |
| --- | --- |
| `UVDDbConnection` | Primary SQL Server connection |
| `DMSConnection` | Shared DMS database connection |
| `DMSConnReport` | Reporting database connection |
| `OBVPriceUrl` / `OBVEngineListUrl` / `OBVToken` | Orange Book Value valuation API |
| `POMSTokenEndPoint` / `POMSID` / `POMSPassword` / `POMSPublishPODataEndPoint` | POMS/IDP order publishing |
| `sap_token_url` / `sap_client_id` / `sap_client_secret` / `sap_posting_base_url` | SAP integration |
| `AzureTokenGenURL` / `AzureTokenGenCode` / `AzureTokenGenVersion` | Azure token/storage |
| `SMTPHost` / `SMTPPort` / `SMTPUserID` / `EmailFrom` | Email notifications |
| `SMS1` / `SMS2` / `SMS3` | SMS gateway URL parts |
| `WebUri` | Base web URI for callbacks/links |
| `OTEL_ENABLED` / `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_SERVICE_NAME` | OpenTelemetry logging |
| `EnableLogging` | Toggles verbose data logging |
| `GSTDate` / `TCS*` / `CentralTaxDate` / `KFCDate` | Tax/business rule effective dates |

The checked-in `Web.config` currently contains live values for several of these keys. Externalize them to a secret store (e.g. Azure Key Vault) and rotate any exposed credentials.

## 5. Build Instructions

**Visual Studio:** Build → Build Solution (Debug/Release).

```bash
nuget restore UVD.sln
msbuild UVD.sln /p:Configuration=Debug
msbuild UVD.sln /p:Configuration=Release
```

Build outputs land in each project's `bin/` folder. The UVD web project produces a deployable ASP.NET application.

## 6. Deployment Steps

1. Build a **Release** web-deploy package for the `UVD` project (VS Publish or `msbuild /p:DeployOnBuild=true /p:PublishProfile=<profile>`).
2. Apply the environment-specific `Web.Release.config` transform / config (connection strings, integration endpoints).
3. Deploy to IIS node(s). For multi-node setups behind a load balancer, deploy **node-by-node (rolling)** and health-check before re-adding each node.
4. Verify: hit the Swagger UI and a token request against the deployed instance.

**Rollback:** redeploy the previous package and revert config; the API tier is stateless, so node replacement is safe. See the HLD/Deployment pages for infra topology (SQL Server AlwaysOn AG, edge load balancer, OTel collector).

## 7. Testing Instructions

- No automated test project exists today. Verify changes by: building clean; running locally and exercising affected endpoints via **Swagger UI** or Postman (acquire a token first); checking `~/LogFiles/UVD-App-Error.txt` for exceptions.
- **Recommended:** add an MSTest/xUnit/NUnit project for `UVD.BLL` and `UVD.Helper` (e.g. `Validator` rules) and wire it into CI.

## 8. Folder Structure

```text
PreOwnedDMS/
├── UVD.sln                        # Solution entry point
├── UVD/                           # ASP.NET Web API host (controllers, OWIN, App_Start, Web.config)
│   ├── App_Start/                 # WebApiConfig, Startup.Auth, FilterConfig, RouteConfig, SwaggerConfig
│   ├── Controllers/                # ~40 API controllers (one per functional area)
│   ├── Models/ Providers/ Results/ # Identity/OAuth models, providers, custom results
│   └── Document/ Content/ Scripts/ # Uploaded docs + static assets
├── UVD.BLL/                       # Business services (*BusinessService.cs) + integrations
├── UVD.DAL/                       # Data access (*DataAccess.cs, DbConnector, DataAccessLayerFactory)
├── UVD.VM/                        # Request/ + Response/ view models + Common/ (CodeMessage, OutputResult)
├── UVD.Helper/                    # Validator, ExceptionLogging, Encryptor, ReUsableEnum
├── MicroDMS.BusinessEntities/     # Shared domain data objects (*DO.cs)
├── MicroDMS.BusinessLayer/        # Shared business logic (*BL.cs, tax processors)
├── MicroDMS.DataLayer/            # Shared data access (*DAL.cs, DeadLockRetryHelper)
├── packages/                      # NuGet packages (packages.config style)
└── docs/                          # Architecture docs + generated diagrams (HLD/LLD/API/HLCD)
```

**Conventions:** controllers `XxxController`, business services `XxxBusinessService` (methods `BLL…`), data access `XxxDataAccess` (methods `DAL…`), DTOs `RequestVMXxx`/`ResponseVMXxx`, shared entities `XxxDO`.

## 9. Common Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| NuGet restore fails / missing refs | Run `nuget restore UVD.sln`; ensure `packages/` populated and VS targets installed |
| Build errors on `MicroDMS.*` | Confirm shared projects build first; check references and target framework (4.6.1) |
| `401 Unauthorized` on every call | Missing/expired bearer token, or `ValidateToken` scope claims not all present/non-zero |
| `400 Bad Request` | Validation failure — check the relevant `Validator` rule for required fields |
| `500 Internal server error..` | Inspect `~/LogFiles/UVD-App-Error.txt` (method, message, inner, stack) |
| SQL connection/timeouts | Verify `UVDDbConnection`; check AG listener / `MultiSubnetFailover`; confirm stored procedures exist |
| Integration failures (POMS/SAP/OBV) | Verify endpoint/credential config keys; ensure TLS 1.2 and network egress |
| File upload returns `406` | Unsupported file type — only allowed extensions are accepted |

## 10. Maintainers / Contact

*Replace the placeholders below during onboarding.*

| Role | Contact |
| --- | --- |
| Product Owner | *<name / email>* |
| Engineering Lead | *<name / email>* |
| DevOps / Infra | *<name / email>* |
| Team / Channel | *<Teams/Slack channel>* |
| Jira board | *<board key>* |
| Confluence space | *<space link>* |
| On-call / support | *<rotation or alias>* |

## Related Documentation

High Level Design (HLD), Low Level Design (LLD), API Specification, and High Level Code Document (HLCD) — see the project Confluence space. Machine-readable API contract: `docs/openapi-uvd.yaml`.

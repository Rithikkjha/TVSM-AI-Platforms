# TVS Connect Web API

Backend REST API platform powering the TVS Connect mobile application ecosystem — connected vehicle services for TVS Motor Company's two-wheeler lineup.

---

## Application Overview

TVS Connect Web API is an ASP.NET Web API 2 application (.NET Framework 4.8) that provides:

- User authentication (OTP-based, social login)
- Vehicle onboarding and management
- Ride tracking and telemetry analytics
- Push notifications (Azure Notification Hubs)
- Connected vehicle features (geofencing, crash alerts, TPMS, OTA)
- Dealer and service integration (DMS)
- Multi-region deployment support (10+ countries)

---

## Prerequisites

- Visual Studio 2019+ (with ASP.NET workload)
- .NET Framework 4.8 SDK
- SQL Server / Azure SQL Database
- Azure Storage Emulator (optional, for local blob storage)
- IIS Express (included with VS)

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tvs-connect-web-api
```

### 2. Open Solution

Open `TVS-App.sln` in Visual Studio.

### 3. Restore NuGet Packages

```
Right-click Solution → Restore NuGet Packages
```

Or via CLI:
```bash
nuget restore TVS-App.sln
```

### 4. Configure Database Connection

Update connection strings in `TVS.ApiService.Api/Web.config`:
- `TVSServiceConnectionString` — Primary database
- `TVSModel` — Entity Framework context
- `iQubeNotificationConnectionString` — Notification database

### 5. Run Database Scripts

Execute scripts from `DatabaseScriptForPipeline/` against your SQL Server instance in order:
1. `ChangeScript.sql`
2. `DataScript.sql`

### 6. Configure App Settings

Update `Web.config` appSettings with your environment-specific values (see Environment Variables section below).

---

## Local Development

### Running the API

1. Set `TVS.ApiService.Api` as the startup project
2. Select **Debug** configuration
3. Press `F5` or `Ctrl+F5` to run
4. API will start on `https://localhost:{port}/`
5. Root URL redirects to `/api/Health/CheckHealth`

### Running the Web Client

1. Set `TVS.WebClient.Web` as the startup project
2. Run in Debug mode

### Running Both

1. Right-click Solution → Properties → Multiple Startup Projects
2. Set both `TVS.ApiService.Api` and `TVS.WebClient.Web` to "Start"

---

## Environment Variables (App Settings)

| Key | Purpose |
|-----|---------|
| `BaseUrl` | API base URL |
| `AzureKeyVaultUrl` | Azure Key Vault endpoint |
| `AesSecretKey` | AES encryption key (GDPR) |
| `EntityFrameworkContext` | EF context name |
| `AzureHostName` | Azure Storage account name |
| `AzureHostkey` | Azure Storage account key |
| `NotificationURL` | Azure Notification Hub connection |
| `NotificationAppName` | Notification hub name |
| `PrimarySMSProvider` | SMS provider (TataCommunication/Airtel) |
| `SecondarySMSProvider` | Fallback SMS provider |
| `heremap_api_key` | HERE Maps API key |
| `openweather-url` | OpenWeather API endpoint |
| `P360URL` | P360 platform URL |
| `P360Token` | P360 authentication token |
| `TntCertificatePath` | TrakNTell client certificate path |
| `TntCertificatePassword` | Certificate password |
| `countryName` | Deployment country identifier |
| `accessTokenLifeTimeInMinutes` | Token expiry configuration |
| `refreshTokenLifeTimeInMinutes` | Refresh token expiry |
| `swagger-enable` | Enable/disable Swagger UI |

> **Note**: Never commit actual secrets to the repository. Use Azure Key Vault or environment-specific config transforms.

---

## Build Instructions

### Visual Studio

```
Build → Build Solution (Ctrl+Shift+B)
```

### Command Line (MSBuild)

```bash
msbuild TVS-App.sln /p:Configuration=Release /p:Platform="Any CPU"
```

### Build Configurations

| Configuration | Purpose |
|--------------|---------|
| Debug | Local development |
| Dev | Development environment |
| Staging | Staging/UAT |
| Release | Generic release |
| Prod | Production |

---

## Deployment

### Azure DevOps Pipeline

Deployment is automated via Azure DevOps pipelines defined in `azure-pipelines/`:

- **DEV**: Auto-triggered on feature branch merges
- **UAT**: Manual approval gate
- **PROD**: Manual approval gate

### Regional Deployments

Each region has dedicated pipeline files:
- `azure-pipeline-{region}-dev.yml`
- `azure-pipeline-{region}-stg.yml`
- `azure-pipeline-{region}-prod.yml`

### Manual Deployment

1. Build in Release/Prod configuration
2. Publish `TVS.ApiService.Api` project
3. Deploy to Azure App Service via Web Deploy or ZIP deploy
4. Apply country-specific configs from `Country_Specific_Configuration_Files/{region}/`

---

## Testing

### Unit Tests

```bash
# Using Visual Studio Test Explorer
Test → Run All Tests

# Using vstest.console
vstest.console.exe TVS.ApiService.UnitTest\bin\Debug\TVS.ApiService.UnitTest.dll
```

### Test Project Structure

```
TVS.ApiService.UnitTest/
├── TVS.ApiService.Api/           # Controller tests
├── TVS.ApiService.Service/       # Service layer tests
├── TVS.ApiService.Repository/    # Repository tests
└── TVS.ApiService.ProviderService/  # Provider tests
```

### API Testing

- Swagger UI: `https://{host}/swagger` (when enabled)
- Postman Collection: Available in `Docs/Postman/Postman Collection.json`

---

## Folder Structure

```
tvs-connect-web-api/
├── TVS.ApiService.Api/          # Web API host (controllers, auth, config)
├── TVS.ApiService.Service/      # Business logic layer
├── TVS.ApiService.Repository/   # Data access layer
├── TVS.ApiService.Model/        # DTOs and models
├── TVS.ApiService.DAL/          # Entity Framework (EDMX)
├── TVS.ApiService.Common/       # Shared utilities
├── TVS.ApiService.Database/     # SSDT database project
├── TVS.SMSService/              # SMS provider abstraction
├── TVS.WebClient.Web/           # MVC web portal
├── TVS.ApiService.UnitTest/     # Unit tests
├── azure-pipelines/             # CI/CD pipeline definitions
├── Country_Specific_Configuration_Files/  # Per-region configs
├── DBScript/                    # Database scripts
├── DatabaseScriptForPipeline/   # Pipeline DB scripts
├── docs/                        # Documentation
└── TVS-App.sln                  # Solution file
```

---

## Common Troubleshooting

| Issue | Solution |
|-------|----------|
| NuGet restore fails | Clear NuGet cache: `nuget locals all -clear` |
| EF model errors | Regenerate EDMX: Right-click `.edmx` → Update Model from Database |
| Connection timeout | Check SQL Server accessibility, verify connection strings |
| 401 Unauthorized | Token expired — re-authenticate via `/token` endpoint |
| SMS not sending | Check SMS provider config, verify test mobile numbers |
| Blob storage errors | Verify `AzureHostName` and `AzureHostkey` in config |
| Build errors (local DLLs) | Ensure `localpackages/` contains required DLLs |
| Port conflicts | Change IIS Express port in project properties |
| Certificate errors (TrakNTell) | Verify `.pfx` file exists at configured path |
| Country-specific issues | Ensure correct `countryName` in appSettings |

---

## Key Entry Points

| What | Where |
|------|-------|
| Application Start | `TVS.ApiService.Api/Global.asax.cs` |
| Auth Config | `TVS.ApiService.Api/App_Start/Startup.Auth.cs` |
| Route Config | `TVS.ApiService.Api/App_Start/WebApiConfig.cs` |
| DI Container | `TVS.ApiService.Api/App_Start/UnityConfig.cs` |
| Health Check | `GET /api/Health/CheckHealth` |
| Swagger | `GET /swagger` (when enabled) |

---

## Project Ownership & Stakeholders

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |

---

## Additional Documentation

- [High Level Code Document](./HLC.md)
- [High Level Design](./HLD.md)
- [Low Level Design](./LLD.md)
- [API Specification](./API_SPEC.md)

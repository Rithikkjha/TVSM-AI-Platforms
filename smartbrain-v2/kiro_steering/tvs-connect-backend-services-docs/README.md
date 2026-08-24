# TVS Connect Web API

Backend platform powering the TVS Connect mobile application — connected vehicle services for TVS Motor two-wheeler owners (ICE + EV).

---

## Application Overview

TVS Connect Web API provides REST APIs for:
- User registration and OTP-based authentication
- Vehicle onboarding and management (ICE + EV)
- Real-time vehicle telemetry and diagnostics
- Ride recording, analytics, and history
- Push notifications (FCM/APNS)
- Service booking and dealer integration
- OTA firmware updates
- Third-party content (weather, news, sports)

**Stack:** .NET Framework 4.8 | ASP.NET Web API 2 | Entity Framework 6 | Azure App Service

---

## Setup Instructions

### Prerequisites

- Visual Studio 2019+ (with .NET Framework 4.8 targeting pack)
- SQL Server 2016+ or Azure SQL access
- .NET Framework 4.8 SDK
- NuGet Package Manager
- Azure Storage Emulator (optional, for Blob/Event Hub local testing)

### Clone & Restore

```bash
git clone <repo-url>
cd tvs-connect-web-api
nuget restore TVS-App.sln
```


---

## Local Development Steps

1. Open `TVS-App.sln` in Visual Studio
2. Set `TVS.ApiService.Api` as the startup project
3. Configure `Web.config` connection strings (see Environment Variables below)
4. Build solution: `Ctrl+Shift+B`
5. Run: `F5` (launches IIS Express on `https://localhost:44300`)
6. Swagger UI available at: `https://localhost:44300/swagger`

---

## Environment Variables

All configuration is in `TVS.ApiService.Api/Web.config`:

| Category | Key | Description |
|----------|-----|-------------|
| **Database** | `TVSModelEntities` | ICE database connection string |
| **Database** | `EVModelEntities` | EV database connection string |
| **Auth** | `CommunicationKey` | JWT signing key (HMAC-SHA256) |
| **Auth** | `accessTokenLifeTimeInMinutes` | Access token lifetime |
| **Azure** | `BlobStorageConnectionString` | Azure Blob Storage |
| **Azure** | `NotificationHubConnectionString` | Push notification hub |
| **Azure** | `EventHubNamespace` | Telemetry Event Hub |
| **SMS** | `AirtelSMSUrl` | Airtel Digimate endpoint |
| **SMS** | `TataSMSUrl` | Tata Communications endpoint |
| **External** | `P360BaseUrl` | P360 Telematics API |
| **External** | `DMSDigiApiUrl` | DMS Digi API |
| **External** | `MapMyIndiaApiKey` | MapMyIndia API key |
| **Feature** | `IsSendOTP` | Toggle OTP sending (false for local) |
| **Feature** | `swagger-enable` | Enable Swagger UI |

---

## Build Instructions

### Visual Studio
```
Build → Build Solution (Ctrl+Shift+B)
Configuration: Debug / Release
Platform: Any CPU
```

### Command Line (MSBuild)
```bash
msbuild TVS-App.sln /p:Configuration=Release /p:Platform="Any CPU" /t:Rebuild
```

### NuGet Restore
```bash
nuget restore TVS-App.sln
```

---

## Deployment Steps

Deployment is managed via **Azure DevOps Pipelines**:

1. **CI Pipeline** (`azure-pipelines.yml`):
   - NuGet restore → MSBuild (Release) → Web Deploy package → Publish artifacts
   - Agent pool: `TVSConnectAgent` (self-hosted)

2. **CD Pipeline** (Release):
   - DEV: Auto-deploy on CI success
   - UAT: Manual approval gate
   - PROD: Manual approval gate

### Manual Deployment
```bash
msbuild TVS.ApiService.Api/TVS.ApiService.Api.csproj /p:DeployOnBuild=true /p:PublishProfile=<profile>
```

---

## Testing Instructions

### Unit Tests
```bash
# Run via Visual Studio Test Explorer or:
vstest.console TVS.ApiService.UnitTest/bin/Release/TVS.ApiService.UnitTest.dll
```

### API Testing
- Import Postman collection from `Docs/Postman/` folder
- Set environment variables (baseUrl, accesstoken, userid)
- Run collection against DEV/UAT

### Health Check
```bash
curl https://<host>/api/Health/CheckHealth
```

---

## Folder Structure

```
tvs-connect-web-api/
├── TVS-App.sln                      # Solution (24 projects)
├── TVS.ApiService.Api/              # Web API host (controllers, filters, config)
├── TVS.ApiService.Service/          # Business logic layer (173 classes)
├── TVS.ApiService.Repository/       # Data access abstraction (103 classes)
├── TVS.ApiService.DAL/              # EF6 context — ICE database
├── TVS.ApiService.EV.DAL/           # EF6 context — EV database
├── TVS.ApiService.Model/            # DTOs, request/response models
├── TVS.ApiService.Common/           # Shared utilities, constants
├── TVS.ApiService.ProviderService/  # HTTP resilience (circuit breaker)
├── TVS.SMSService/                  # SMS delivery (Airtel/Tata)
├── TVS.WebJob.PushNotifications/    # WebJob: push delivery
├── TVS.Webjob.UnifiedMappingTableICE/ # WebJob: vehicle sync
├── ConsoleForSaveNotifications/     # Console: notification persistence
├── ConsoleForSendNotifications/     # Console: notification dispatch
├── ConsoleServiceReminder/          # Console: service reminders
├── ConsoleAppForSendDataToNGD/      # Console: NGD data forwarding
├── TVS.ApiService.UnitTest/         # Unit tests
├── DBScript/                        # Database scripts
├── Docs/                            # Documentation
├── azure-pipelines/                 # CI/CD YAML templates
└── azure-pipelines.yml              # Main pipeline definition
```

---

## Common Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Build fails with NuGet errors | Missing packages | Run `nuget restore TVS-App.sln` |
| 401 Unauthorized on all APIs | Invalid/expired JWT | Generate new token via login flow |
| Connection timeout to DB | Wrong connection string | Verify Web.config `TVSModelEntities` |
| SMS not sending locally | `IsSendOTP` = false | Set to true (or use test mobile numbers) |
| Swagger not loading | `swagger-enable` = FALSE | Set to TRUE in Web.config |
| EDMX model errors | DB schema mismatch | Update Model from Database in VS |
| WebJob not running | Not attached to App Service | Deploy via Publish or attach manually |

---

## Project Ownership & Stakeholders

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner (iOS)** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |
| **Owner (Android)** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
| **DevOps** | Raju Nimse | raju.nimse@tvsmotor.com |
| **Contact Person (Backend)** | Raju Nimse | raju.nimse@tvsmotor.com |

---

*Keep this README concise and onboarding-focused.*

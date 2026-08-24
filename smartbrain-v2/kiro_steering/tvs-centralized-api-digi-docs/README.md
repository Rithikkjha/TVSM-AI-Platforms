# CentralisedAPI (DIGI DMS)

Centralized backend API for TVS Motor's Dealer Management System (DMS). Powers the Digi DMS mobile app and web portal used by TVS Motor dealership service centers across India and international markets for the complete vehicle service lifecycle.

## Quick Start

### Prerequisites
- Visual Studio 2022 (or later)
- .NET Framework 4.8 SDK
- SQL Server access (Dev/UAT instances)
- Azure Key Vault access (for secrets)

### Run Locally
1. Clone the repo
2. Open `EMSUI.sln` in Visual Studio
3. Ensure `Web.config` connection strings point to your dev database
4. Ensure Azure AD credentials (ClientID, TenantID, ClientSecret) are configured for Key Vault access
5. Press F5 or `Ctrl+F5` to run under IIS Express

### Environment Variables / Config
All configuration lives in `EMSUI/Web.config`:
- `connectionStrings` — DB connections (DMSOnlineConnection, SMRSqlConnection, etc.)
- `appSettings` — Azure AD creds, SMS provider config, external service URLs, feature flags, JWT secrets
- Secrets are partially managed via Azure Key Vault (DigiKeyVaultName, ClientID, etc.)

### Key Contacts / Ownership

| Role | Contact |
|------|---------|
| Dev Team | DMS Backend Team |
| Email Alerts | sapna.bhandari@tvsmotor.com, g.santhoshkumar@tvsmotor.com |
| Prod Approval | sapna.bhandari@tvsmotor.com, Suraj.Ray@tvsmotor.com, Dushyant.Satyapal@tvsmotor.com |

### Build
```
msbuild EMSUI.sln /p:Configuration=Release
```

### Deployment
- **Target**: IIS / Azure App Service
- **Framework**: ASP.NET Web API on .NET Framework 4.8
- **Environments**: Dev, UAT, Production (toggle via Web.config appSettings sections)

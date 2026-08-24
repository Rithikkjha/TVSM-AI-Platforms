# Employee Referral & Loyalty Portal

An internal web application enabling TVS Motor employees to participate in referral programs, self-purchase schemes, loyalty redemptions, and employee engagement activities.

---

## Application Overview

| Attribute | Detail |
|-----------|--------|
| **Framework** | ASP.NET MVC 4 / .NET Framework 4.8 |
| **ORM** | Entity Framework 6.4.4 |
| **Database** | Microsoft SQL Server 2016+ |
| **Web Server** | IIS 8.5+ |
| **Frontend** | Razor Views, jQuery 1.9.1, Bootstrap 3.x |
| **Auth** | Microsoft Entra ID (SSO), Kiosk API, OTP-based login |

### Key Features

- Employee referral code generation and tracking
- Self-purchase and accessories discount management
- Dealer information lookup
- EMI calculator
- Complaint management
- SMS and email notifications
- Role-based access control (Admin, Employee, Dealer, Kiosk)

---

## Prerequisites

- **Visual Studio** 2019 or later (with ASP.NET and web development workload)
- **.NET Framework 4.8** Developer Pack
- **SQL Server** 2016+ (local or remote)
- **IIS** or IIS Express (bundled with Visual Studio)
- **NuGet** package manager (included with Visual Studio)

---

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Employee-Referral-Portal
   ```

2. **Restore NuGet packages**
   Open the solution in Visual Studio and restore packages, or run:
   ```bash
   nuget restore
   ```

3. **Configure the database**
   - Create the required SQL Server databases (see [Database Setup](#database-setup) below).
   - Update connection strings in `Employee_UI/Web.config`.

4. **Run database scripts**
   Execute `Database_Diagnostic_Script.sql` against your SQL Server instance to verify schema and stored procedures.

5. **Build the solution**
   ```bash
   msbuild /p:Configuration=Release
   ```

---

## Local Development

1. Open the `.sln` file in Visual Studio.
2. Set `Employee_UI` as the startup project.
3. Press **F5** (or Ctrl+F5 for without debugging) to launch with IIS Express.
4. The application starts at `https://localhost:{port}/Login/Login`.

### Database Setup

The application uses two database contexts:

| Context | Purpose |
|---------|---------|
| Employee | Primary application data |
| TVSONEVIEW | Repurchase model data (read-only) |

> Connection string names are defined in `Web.config`. Obtain actual values from your team lead or secrets vault.

Ensure both databases are provisioned and the stored procedures listed in `API_SPECIFICATION.md` (Section 9) are deployed.

---

## Environment Variables / AppSettings

Configure these in `Employee_UI/Web.config` under `<appSettings>`. Actual values must be obtained from the team lead or your organization's secrets vault (Azure Key Vault, etc.).

| Category | Keys Required | Purpose |
|----------|---------------|---------|
| **SSO / Entra ID** | Tenant ID, Client ID, Client Secret, Audience | Azure AD authentication |
| **Notification OAuth** | Tenant ID, Client ID, Client Secret, Scope, API URL | OTP email delivery service |
| **OTP Configuration** | Max attempts, Block duration | Rate limiting for OTP generation |
| **Connection Strings** | Primary DB, Read-only DB | SQL Server database connectivity |

### Connection Strings

```xml
<connectionStrings>
  <add name="<PrimaryDbName>" connectionString="Server=<SERVER>;Database=<DB>;Integrated Security=True;" />
  <add name="<ReadOnlyDbName>" connectionString="Server=<SERVER>;Database=<DB>;Integrated Security=True;" />
</connectionStrings>
```

> **⚠️ Security:** Never commit real credentials or connection strings to source control. Use Web.config transforms (`Web.Release.config`), environment variables, or a secrets manager (e.g., Azure Key Vault).

---

## Build Instructions

### Debug Build
```bash
msbuild /p:Configuration=Debug
```

### Release Build
```bash
msbuild /p:Configuration=Release
```

### Publish (for deployment)
```bash
msbuild /p:Configuration=Release /p:DeployOnBuild=true /p:PublishProfile=<ProfileName>
```

Or use Visual Studio: Right-click `Employee_UI` → **Publish**.

---

## Deployment

### IIS Deployment

1. **Create an IIS Application Pool**
   - .NET CLR Version: v4.0
   - Managed Pipeline Mode: Integrated

2. **Deploy the published output** to the IIS site directory.

3. **Configure bindings** for HTTPS (TLS 1.2 required for external API calls).

4. **Set application pool identity** with appropriate SQL Server and network permissions.

5. **Verify connectivity** to external services:
   - Azure AD login endpoint (port 443)
   - Internal Employee/Auth API gateway (port 443)
   - Notification service API Management endpoint (port 443)
   - SQL Server instance (port 1433)
   
   > Exact hostnames are documented internally. Contact DevOps for the environment-specific endpoint list.

### Environment-Specific Configuration

Use Web.config transforms for each environment:
- `Web.Debug.config` — local development
- `Web.Release.config` — production settings

---

## Testing

### Manual Testing

1. Launch the application locally.
2. Test authentication flows:
   - Standard login (`/Login/Login`)
   - SSO login (`/SSO/SignIn`)
   - OTP login (sister company email)
3. Test core workflows: referral creation, self-purchase, dealer lookup.

### Database Diagnostics

Run the diagnostic script to verify database health:
```sql
-- Execute against your target database
:r Database_Diagnostic_Script.sql
```

### Diagnostic Endpoint

```
GET /Login/TestDatabase
```
Returns database connectivity status (disable in production).

### Error Monitoring

ELMAH is configured for error logging. Access error logs at:
```
/elmah.axd
```
(Restricted to local requests by default.)

---

## Folder Structure

```
├── Employee_Domain/            # Domain layer (Class Library)
│   ├── Abstract/               # Interfaces (IEmployee)
│   ├── Concrete/               # Implementations (Repository, LoyaltyAPI, Membership)
│   ├── Entity/                 # Data models / EF entities
│   ├── Properties/             # Assembly metadata
│   └── Scripts/                # jQuery libraries
│
├── Employee_UI/                # Presentation layer (ASP.NET MVC)
│   ├── App_Start/              # Startup config (Routes, Bundles, Filters, WebAPI)
│   ├── CallingWebservices/     # External API client classes
│   ├── Content/                # Static assets (CSS, fonts, images)
│   ├── Controllers/            # MVC Controllers
│   ├── Views/                  # Razor views
│   └── Web.config              # Application configuration
│
├── API_SPECIFICATION.md        # Full API endpoint documentation
├── HIGH_LEVEL_DESIGN_DOCUMENT.md
├── LOW_LEVEL_DESIGN_DOCUMENT.md
├── DOMAIN_VALIDATION_IMPLEMENTATION.md
├── Database_Diagnostic_Script.sql
└── README.md                   # This file
```

---

## Common Troubleshooting

| Issue | Resolution |
|-------|-----------|
| **NuGet packages not found** | Right-click solution → Restore NuGet Packages. Ensure `packages/` folder is populated. |
| **Database connection failure** | Verify connection strings in `Web.config`. Run `GET /Login/TestDatabase` to diagnose. |
| **SSO redirect loop** | Confirm Entra ID tenant, client, and reply URL settings are configured correctly in Azure AD app registration. |
| **OTP not sending** | Check notification API URL, verify OAuth credentials, and confirm network access to the API Management endpoint. |
| **External API timeouts** | Ensure outbound HTTPS (port 443) is allowed to all required external service endpoints. |
| **ELMAH not logging** | Verify ELMAH modules are registered in `Web.config` `<system.webServer>` section. |
| **Session lost after deploy** | Application uses InProc session state. Ensure single-server deployment or migrate to SQL/Redis session. |
| **Build errors after clone** | Delete `bin/` and `obj/` folders, restore NuGet packages, and rebuild. |

---

## Maintainers

| Role | Name | Contact |
|------|------|---------|
| Project Owner | _TBD_ | _email@example.com_ |
| Tech Lead | _TBD_ | _email@example.com_ |
| DBA | _TBD_ | _email@example.com_ |
| DevOps | _TBD_ | _email@example.com_ |

---

## Additional Documentation

- [API Specification](API_SPECIFICATION.md) — Full endpoint reference
- [High-Level Design](HIGH_LEVEL_DESIGN_DOCUMENT.md) — Architecture and system design
- [Low-Level Design](LOW_LEVEL_DESIGN_DOCUMENT.md) — Implementation details
- [Domain Validation](DOMAIN_VALIDATION_IMPLEMENTATION.md) — Email domain validation logic

---

## License

Internal use only. Proprietary to TVS Motor Company.

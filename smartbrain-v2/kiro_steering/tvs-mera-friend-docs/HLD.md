# TVS Motor Employee Referral Portal - High Level Code Document

---

## 1. Application Overview

### Purpose
The TVS Motor Employee Referral Portal is an ASP.NET MVC web application that manages employee benefit programs for TVS Motor Company. The system enables employees to:
- Refer friends and family for TVS vehicle purchases with discount codes
- Purchase vehicles for themselves or others with employee discounts
- Track referral history and redemption status
- Access EMI calculators and dealer information
- Submit complaints and feedback

### Technology Stack
| Layer | Technology |
|-------|-----------|
| Framework | ASP.NET MVC 4.0 (.NET Framework 4.8) |
| Language | C# |
| Database | SQL Server via Entity Framework 6.4.4 |
| Authentication | Forms Auth + Microsoft Entra ID SSO + KIOS + OTP |
| Error Logging | ELMAH (SQL Server backend) |
| Frontend | jQuery 1.9.1, Bootstrap, Razor Views |
| Web Services | SOAP + REST integrations |

### Deployment Environment
- **Web Server**: IIS (Internet Information Services)
- **Database Server**: SQL Server (Dev / UAT / Production environments)
- **External APIs**: TVS1Hub REST API, OAuth2 Notification Service, SAP Intranet SOAP, Dealer SOAP Service

---

## 2. Major Modules/Components

### 2.1 Authentication & Authorization Module
- **Multi-mode login**: Forms-based (encrypted credentials), Microsoft Entra ID SSO, KIOS (TVS Kiosk system), Sister Company OTP
- **Domain Validation**: Email domain whitelist via `TVSAPP_DOMAIN_MASTER` table
- **OTP Management**: OAuth2-based generation with rate limiting (3 attempts / 2-minute block)
- **Session Management**: 120-minute timeout, secure cookie handling

### 2.2 Employee Referral Module
- Unique referral code generation and tracking
- Multi-level approval workflow
- SMS/Email notifications to referee and employee
- Cancellation & resend of referral codes
- Complete referral history audit trail

### 2.3 Self-Purchase / Repurchase Module
- Self-purchase (employee buys for self) and purchase-for-others
- Automated discount calculation and validation
- Unique purchase codes with SMS/Email delivery
- Purchase history tracking

### 2.4 Accessories Module
- Accessories-specific code generation
- Remaining discount balance tracking
- Purchase history

### 2.5 EMI Calculator Module
- EMI calculation based on loan amount, tenure, and interest rate
- Multiple financing schemes
- Brand/model-based calculation

### 2.6 Dealer Management Module
- Dealer lookup by state, city, area
- Real-time data from external dealer web service
- Contact details and address display

### 2.7 Complaint Management Module
- Complaint submission with attachments
- Status tracking and resolution
- SMS/Email alerts on updates

### 2.8 Reporting Module
- Referral reports, repurchase reports, summary dashboards
- Export functionality

---

## 3. Folder Structure Explanation

```
Employee_Portal/
│
├── Employee_Domain/                    # Domain / Data Layer (Class Library)
│   ├── Abstract/                       # Interface definitions
│   │   └── IEmployee.cs               # Repository interface contract
│   ├── Concrete/                       # Implementation classes
│   │   ├── Employee.cs                # EF DbContext — defines all DbSets
│   │   ├── Repository.cs              # IEmployee implementation (LINQ queries)
│   │   ├── RepositoryActions.cs       # Stored procedure execution wrapper
│   │   ├── LoyaltyAPI.cs              # SMS & Email API integration
│   │   ├── Membership.cs             # Membership/encryption utilities
│   │   ├── Constants.cs              # Application constants
│   │   ├── MyPolicy.cs               # Certificate policy for web requests
│   │   └── TVSONEVIEW.cs             # TVS One View integration
│   ├── Entity/                         # EF entity models (DB table mappings)
│   │   ├── Login.cs                   # t_base_login_details
│   │   ├── UserMaster.cs             # User information
│   │   ├── EmployeeMaster.cs         # T_LOYALTY_EMP_MASTER
│   │   ├── Dealer.cs                  # Dealer information
│   │   ├── ModelMaster.cs            # Vehicle models
│   │   ├── TVSAPPDomainMaster.cs     # Domain whitelist table
│   │   ├── TVSGroupCompany.cs        # Group company mapping
│   │   ├── ActivityPermission.cs     # Menu/activity permissions
│   │   ├── Complaints.cs            # Complaint records
│   │   └── [14 other entities]       # State, City, Brand, Loan, etc.
│   └── Employee_Domain.csproj         # Project file (.NET 4.8 Class Library)
│
├── Employee_UI/                        # Presentation Layer (ASP.NET MVC Web App)
│   ├── App_Start/                      # Application startup configuration
│   │   ├── BundleConfig.cs            # CSS/JS bundling definitions
│   │   ├── FilterConfig.cs            # Global MVC filters
│   │   ├── RouteConfig.cs            # URL routing rules
│   │   └── WebApiConfig.cs           # Web API route configuration
│   ├── CallingWebservices/             # External service integration layer
│   │   ├── WebserviceCalling.cs       # TVS1Hub + KIOS + Dealer calls
│   │   ├── EmployeeJsonClass.cs      # Employee API response model
│   │   └── DealerJson.cs             # Dealer API response model
│   ├── Controllers/                    # MVC Controllers
│   │   ├── LoginController.cs         # All authentication logic (~2400 lines)
│   │   ├── SSOController.cs          # Microsoft Entra ID SSO
│   │   ├── EmployeeController.cs     # Core features (~4200 lines)
│   │   ├── DashBoardController.cs    # Dashboard views
│   │   └── HomeController.cs         # Public/home pages
│   ├── Models/                         # View models and DTOs
│   ├── Views/                          # Razor view templates
│   │   ├── Login/                     # Login, OTP, SSO pages
│   │   ├── Employee/                  # Feature pages (referral, purchase, etc.)
│   │   ├── Home/                      # Public content pages
│   │   └── Shared/                    # _Layout, partial views
│   ├── Content/                        # Static assets
│   │   ├── css/                       # Bootstrap + custom stylesheets
│   │   ├── images/                    # 158 image assets
│   │   └── Fonts/                     # Web fonts (Roboto, DINPro)
│   ├── Scripts/                        # JavaScript files
│   ├── Web.config                     # IIS/app configuration
│   ├── Global.asax.cs                 # Application lifecycle events
│   └── GenericError.htm               # Security-safe error page
│
├── Database_Diagnostic_Script.sql      # DB connection diagnostic utility
└── DOMAIN_VALIDATION_IMPLEMENTATION.md # Implementation documentation
```

---

## 4. Core Business Workflows

### 4.1 Employee Referral Workflow
```
Employee Login → Authentication
       ↓
Navigate to "Refer a Friend"
       ↓
Validate referral eligibility (PROC_EMP_REFERRAL_BLOCK)
       ↓
Enter referee details (name, mobile, email)
       ↓
System generates unique referral code
       ↓
Send SMS to referee with code (LoyaltyAPI.SMSAPI)
       ↓
Send Email to referee (LoyaltyAPI.EMAILAPI)
       ↓
Send confirmation notification to employee
       ↓
Referee presents code at dealer during purchase
       ↓
Dealer validates code → Employee receives benefit
```

### 4.2 Self-Purchase Workflow
```
Employee Login → Authentication
       ↓
Navigate to "Self Purchase"
       ↓
Validate purchase eligibility (proc_emp_repurchase_block)
       ↓
Select purchase type: Self Buy / Buy for Others
       ↓
Enter vehicle details + buyer information
       ↓
System calculates discount (PROC_GET_EMP_REMEANING_DISCOUNT_DET)
       ↓
Generate unique purchase code
       ↓
Send SMS/Email with code to employee (and buyer if different)
       ↓
Employee/buyer uses code at dealer
       ↓
Dealer validates and applies discount
```

### 4.3 OTP Login Workflow (Sister Company)
```
User enters corporate email address
       ↓
System validates domain against TVSAPP_DOMAIN_MASTER whitelist
       ↓
Domain Allowed? ── No ──→ Show "No access to this domain" error
       ↓ Yes
Acquire OAuth token (Client Credentials flow)
       ↓
Call Notification API to send OTP via email
       ↓
Store OTP in database (proc_store_sistercompany_otp)
       ↓
User enters OTP
       ↓
Verify OTP (rate limited: 3 attempts / 2-min block)
       ↓
On success → Create session → Redirect to dashboard
```

### 4.4 SSO Login Workflow (Microsoft Entra ID)
```
User clicks "SSO Login"
       ↓
Redirect to Microsoft Entra ID login
       ↓
User authenticates with corporate credentials
       ↓
Entra ID issues JWT token → redirect back to app
       ↓
System validates JWT token (signature, audience, expiry)
       ↓
Extract claims (email, name, employee ID)
       ↓
Lookup/create user in local database
       ↓
Create Forms Authentication session → Dashboard
```

### 4.5 KIOS Login Workflow
```
User enters employee number + password
       ↓
Call TVS1Hub API (GetEmployeeDetailsFromEmpno)
       ↓
Validate: email domain = tvsmotor.com AND category ≠ "workmen"?
       ↓
If SSO-eligible → Redirect to SSO ("SSOLogin Failure" message)
       ↓
If KIOS-eligible → Call KioskAPI (Auth/LoginCheck)
       ↓
KIOS returns authentication token
       ↓
Store token in session → Create app session → Dashboard
```

---

## 5. Key Services/Classes

### 5.1 Data Access Layer

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `Employee.cs` (DbContext) | Entity Framework DB context | Defines 18 DbSets for all entities |
| `Repository.cs` | Read-only data access | `GetAllLogin()`, `IsDomainAllowed()`, `GetGroupCompaniesByDomain()` |
| `RepositoryActions.cs` | Stored procedure executor | `PRO_LOGIN_CREDENTIALS()`, `PROC_SelfPurchaseValidate()`, `PROC_ReferAFriendValidate()`, `PROC_GetDiscountBalance()`, `PROC_Store_SisterCompany_OTP()` |

### 5.2 Business Logic / Integration Layer

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `LoyaltyAPI.cs` | SMS & Email dispatch | `SMSAPI()` — template-based SMS, `EMAILAPI()` — campaign emails, `EMAILAPI_REFERRAL_Refere()` |
| `WebserviceCalling.cs` | External API gateway | `Login()` — KIOS auth, `GetEmployeeList()` — SAP data, `GetEmployeeListByEmail()`, `GetDealerDropdown()` |

### 5.3 Presentation Layer (Controllers)

| Controller | Purpose | Key Actions |
|------------|---------|-------------|
| `LoginController` | All authentication flows | `Login()`, `SisterCompanyLogin()`, `KIOSLogin_Authentication()`, `VerifyOtp()`, `CheckDomainAccess()`, `LogOut()` |
| `EmployeeController` | Core business features | `Index()`, `EmployeeReferral()`, `SelfPurchase()`, `EmployeeRepurchase()`, `Ambassadors()`, `EMICalculator()`, `Reports()` |
| `SSOController` | Microsoft Entra ID SSO | `SignIn()`, `SignOut()`, `Consumer()` |
| `DashBoardController` | Dashboard rendering | Dashboard view actions |
| `HomeController` | Public pages | `AboutTheProgram()`, `Err()` |

---

## 6. External Integrations

### 6.1 TVS1Hub REST API
| Aspect | Details |
|--------|---------|
| Purpose | Employee master data + KIOS authentication |
| Base URL | `https://tvs1hub.tvsmotor.com` |
| Endpoints | `GET /TVSApi/api/TVSM/GetEmployeeDetailsFromEmpno`, `GET /TVSApi/api/TVSM/GetEmployeeDetailsFromEmailID`, `POST /KioskAPI/api/Auth/LoginCheck` |
| Auth | API Key header |
| Protocol | HTTPS / REST / JSON |

### 6.2 Microsoft Entra ID (Azure AD)
| Aspect | Details |
|--------|---------|
| Purpose | Single Sign-On for corporate employees |
| Protocol | OpenID Connect / OAuth 2.0 |
| Authority | `https://login.microsoftonline.com/{tenantId}/v2.0` |
| Libraries | Microsoft.Owin.Security.OpenIdConnect, Microsoft.Identity.Client |

### 6.3 OAuth Notification API (OTP Delivery)
| Aspect | Details |
|--------|---------|
| Purpose | Send OTP emails for sister company login |
| Endpoint | `https://apim.tvsmotor.com/notification-service/api/v1/notification/email` |
| Auth | OAuth 2.0 Client Credentials |
| Token URL | `https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token` |

### 6.4 Bulk SMS Provider
| Aspect | Details |
|--------|---------|
| Purpose | Transactional SMS (referral codes, OTPs, notifications) |
| Protocol | HTTP GET with query parameters |
| Config | URL, credentials, sender ID stored in database |
| Compliance | DLT-registered templates with Template IDs |

### 6.5 ExactTouch Email Campaign API
| Aspect | Details |
|--------|---------|
| Purpose | Marketing/transactional email delivery |
| Base URL | `https://api.exacttouch.com/API/mailing/` |
| Features | List management, batch upload, campaign scheduling |
| Protocol | HTTPS / XML response |

### 6.6 Dealer Web Service
| Aspect | Details |
|--------|---------|
| Purpose | Dealer information lookup by geography |
| Endpoint | `https://www.advantagetvs.com/DealerWS/WSDealersinfo.asmx` |
| Protocol | SOAP 1.2 over HTTPS |
| Method | `getDealerInfo(username, password, city, state)` |

### 6.7 SAP Intranet Service (Legacy)
| Aspect | Details |
|--------|---------|
| Purpose | Employee data (being replaced by TVS1Hub) |
| Endpoint | Internal SOAP service |
| Status | Legacy — mostly replaced by REST API calls |

---

## 7. Major Dependencies

### 7.1 Core Framework Packages
| Package | Version | Purpose |
|---------|---------|---------|
| EntityFramework | 6.4.4 | ORM / database access |
| Microsoft.AspNet.Mvc | 4.0.30506.0 | MVC web framework |
| Microsoft.AspNet.WebApi | 4.0.30506.0 | Web API support |
| Microsoft.AspNet.Razor | 2.0.30506.0 | View engine |

### 7.2 Authentication & Security
| Package | Version | Purpose |
|---------|---------|---------|
| Microsoft.Owin.Security.OpenIdConnect | 4.2.2 | SSO integration |
| Microsoft.Owin.Security.Cookies | 4.2.2 | Cookie auth middleware |
| Microsoft.IdentityModel.Tokens | 8.7.0 | JWT token validation |
| System.IdentityModel.Tokens.Jwt | 8.7.0 | JWT parsing |
| Microsoft.Identity.Client | 4.70.0 | MSAL authentication |
| Microsoft.Owin.Host.SystemWeb | 4.2.2 | OWIN hosting |

### 7.3 Utilities & Infrastructure
| Package | Version | Purpose |
|---------|---------|---------|
| Newtonsoft.Json | 10.0.3 | JSON serialization |
| System.Text.Json | 8.0.5 | Modern JSON handling |
| elmah | 1.2.2 | Error logging to SQL Server |
| WebGrease | 1.5.2 | CSS/JS minification |

### 7.4 Frontend Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| jQuery | 1.9.1 | DOM manipulation, AJAX |
| jQuery Validate | (bundled) | Client-side form validation |
| Bootstrap | (bundled) | Responsive UI framework |

---

## 8. Runtime Architecture

### 8.1 Layered Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                         │
│        HTML / CSS / jQuery / AJAX                            │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP/HTTPS
┌─────────────────────────▼────────────────────────────────────┐
│                  IIS WEB SERVER                               │
│   ASP.NET Pipeline → Routing → Controller Selection          │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│              PRESENTATION LAYER (Employee_UI)                 │
│  Controllers → Views (Razor) → ViewModels                    │
│  Global.asax (lifecycle) → App_Start (config)                │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│          BUSINESS / INTEGRATION LAYER                        │
│  WebserviceCalling (external APIs)                           │
│  LoyaltyAPI (SMS/Email)                                      │
│  RepositoryActions (stored procedures)                       │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│              DATA ACCESS LAYER (Employee_Domain)              │
│  Repository (IEmployee) → Employee DbContext (EF 6)          │
│  Entity Models → Database Tables                             │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                   SQL SERVER DATABASE                         │
│  Tables, Stored Procedures, Views                            │
│  Database: TVS_MOTOR_EMP_REF                                 │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 Request Processing Pipeline

```
User Request → IIS → ASP.NET Pipeline
    ↓
Global.asax.Application_BeginRequest()
  • Reject duplicate query parameters (HTTP 400)
  • Set no-cache headers
    ↓
Forms Authentication Module
  • Check auth cookie → redirect to /Login/Login if missing
    ↓
MVC Routing (RouteConfig.cs)
  • Map URL → Controller/Action
    ↓
Controller Action Execution
  • Session validation
  • Business logic (via RepositoryActions / WebserviceCalling)
  • External API calls (if needed)
    ↓
View Rendering (Razor)
  • Generate HTML response
    ↓
Global.asax.Application_PreSendRequestHeaders()
  • Strip server version headers
    ↓
HTTP Response → Browser
```

### 8.3 Authentication Modes

| Mode | Flow | Token Storage |
|------|------|---------------|
| Forms Login | Employee No + Password → DB validation → Forms cookie | `.ASPXAUTH` cookie |
| SSO (Entra ID) | OpenID Connect → JWT → Claims → Forms cookie | Session + cookie |
| KIOS | Employee No + Password → TVS1Hub API → KIOS token | Session variable |
| OTP (Sister Co.) | Email → Domain check → OAuth → OTP Email → Verify → Forms cookie | Session + cookie |

### 8.4 Session & Error Handling
- **Session Timeout**: 120 minutes (in-process)
- **Auth Cookie**: `401kAppemployee`, 110-minute expiry
- **Error Logging**: ELMAH → SQL Server (accessible at `/elmah.axd`)
- **Error Display**: Generic error page (`GenericError.htm`) — no stack traces exposed
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection

---

## 9. Important Entry Points

### 9.1 Application Lifecycle
| Entry Point | File | Purpose |
|-------------|------|---------|
| `Application_Start()` | `Global.asax.cs` | Register routes, filters, bundles, Web API |
| `Application_BeginRequest()` | `Global.asax.cs` | Security checks, cache headers |
| `Application_Error()` | `Global.asax.cs` | Global exception handler |

### 9.2 Authentication URLs
| URL | Controller.Action | Method | Purpose |
|-----|-------------------|--------|---------|
| `/Login/Login` | `LoginController.Login()` | GET/POST | Standard employee login |
| `/Login/LoginNew` | `LoginController.LoginNew()` | GET | New login UI (OTP-enabled) |
| `/Login/SisterCompanyLogin` | `LoginController.SisterCompanyLogin()` | GET/POST | Sister company OTP login |
| `/Login/KIOS_Login` | `LoginController.KIOS_Login()` | GET | KIOS login page |
| `/Login/KIOSLogin_Authentication` | `LoginController.KIOSLogin_Authentication()` | GET | KIOS auth processing |
| `/SSO/SignIn` | `SSOController.SignIn()` | GET | Initiate Entra ID SSO |
| `/SSO/Consumer` | `SSOController.Consumer()` | GET | SSO callback handler |
| `/Login/LogOut` | `LoginController.LogOut()` | GET | Session termination |

### 9.3 Core Feature URLs
| URL | Controller.Action | Purpose |
|-----|-------------------|---------|
| `/Employee/Index` | `EmployeeController.Index()` | Main dashboard |
| `/Employee/EmployeeRepurchase` | `EmployeeController.EmployeeRepurchase()` | Referral submission |
| `/Employee/SelfPurchase` | `EmployeeController.SelfPurchase()` | Self-purchase flow |
| `/Employee/Ambassadors` | `EmployeeController.Ambassadors()` | Accessories purchase |
| `/Employee/EMICalculator` | `EmployeeController.EMICalculator()` | EMI calculation |
| `/Employee/EmployeeReferralHistory` | `EmployeeController.EmployeeReferralHistory()` | Referral history |
| `/Employee/EmployeeRepurchaseHistory` | `EmployeeController.EmployeeRepurchaseHistory()` | Purchase history |
| `/Employee/Reports` | `EmployeeController.Reports()` | Reporting |

### 9.4 AJAX / API Endpoints
| URL | Method | Returns | Purpose |
|-----|--------|---------|---------|
| `/Login/CheckDomainAccess` | POST | `{allowed: bool}` | Domain whitelist check |
| `/Login/VerifyOtp` | POST | JSON | OTP verification |
| `/Login/ResendOtp` | POST | JSON | Resend OTP |
| `/Employee/DealerList` | POST | JSON array | Dealer lookup |
| `/Employee/DealerAddress` | POST | JSON | Dealer details |
| `/Employee/GetDealerName` | POST | JSON | Dealer by area |
| `/Employee/CancelReferral` | POST | JSON | Cancel referral code |
| `/Employee/ResendReferralCode` | POST | JSON | Resend referral SMS |
| `/Employee/ResendRepurchase` | POST | JSON | Resend purchase SMS |

---

## 10. High-Level Data Flow

### 10.1 Authentication Data Flow
```
User Credentials (Employee No + Password)
       ↓
LoginController.Login() [POST]
       ↓
Encrypt credentials (salt-based hashing)
       ↓
RepositoryActions.PRO_LOGIN_CREDENTIALS() → SQL Server
       ↓
DB returns: Response, RoleID, UserInternalID, UserNumber, Salt
       ↓
FormsAuthentication.SetAuthCookie() → Set session variables
       ↓
Redirect → /Employee/Index (Dashboard)
```

### 10.2 Referral Data Flow
```
Employee (Web Form: referee name, mobile, email)
       ↓
EmployeeController [POST]
       ↓
RepositoryActions.PROC_ReferAFriendValidate() → Eligibility check
       ↓
Generate unique referral code (via stored procedure)
       ↓
Insert referral record → Database
       ↓
LoyaltyAPI.SMSAPI() → Send SMS to referee
       ↓
LoyaltyAPI.EMAILAPI() → Send email to referee
       ↓
RepositoryActions.PRO_INSERT_SMS_EMAIL_HISTORY() → Log communication
       ↓
Return success response → Update UI
```

### 10.3 Self-Purchase Data Flow
```
Employee (Web Form: vehicle model, buyer details, purchase type)
       ↓
EmployeeController.SelfPurchase() [POST]
       ↓
RepositoryActions.PROC_SelfPurchaseValidate() → Block check
       ↓
RepositoryActions.PROC_GetDiscountBalance() → Remaining discount
       ↓
Calculate applicable discount
       ↓
Generate unique purchase code (via stored procedure)
       ↓
Insert purchase record → Database
       ↓
LoyaltyAPI.SMSAPI() → Send code via SMS
       ↓
LoyaltyAPI.EMAILAPI() → Send code via Email
       ↓
Log communication → Return success
```

### 10.4 OTP Login Data Flow
```
User Email Address
       ↓
AJAX → LoginController.CheckDomainAccess()
       ↓
Repository.IsDomainAllowed() → Query TVSAPP_DOMAIN_MASTER
       ↓
Domain Allowed? ── No ──→ Return {allowed: false} → Show error
       ↓ Yes
Acquire OAuth Bearer Token (Client Credentials grant)
       ↓
Call Notification API → Send OTP email
       ↓
RepositoryActions.PROC_Store_SisterCompany_OTP() → Store in DB
       ↓
User enters OTP → AJAX → LoginController.VerifyOtp()
       ↓
Validate OTP (check attempts, expiry, match)
       ↓
Rate Limit Exceeded? ── Yes ──→ Block for 2 minutes
       ↓ No
OTP Valid? ── No ──→ Increment attempts → Return error
       ↓ Yes
Create session → FormsAuthentication cookie → Dashboard
```

### 10.5 External Employee Data Sync Flow
```
Login Request (KIOS / SSO)
       ↓
WebserviceCalling.GetEmployeeList(empNo)
       ↓
HTTP GET → tvs1hub.tvsmotor.com/TVSApi/api/TVSM/GetEmployeeDetailsFromEmpno
       ↓
Parse JSON response → EmployeeJsonClass
       ↓
Validate email domain + employee category
       ↓
Route to appropriate auth method (SSO vs KIOS)
       ↓
On success → Sync employee data to local DB → Create session
```

### 10.6 SMS/Email Notification Flow
```
Business Event (Referral, Purchase, OTP, Password Reset)
       ↓
Determine template code (e.g., "self_purchase_self_buy")
       ↓
RepositoryActions.PROC_GET_SMS_EMAIL_TEMPLATE() → Get message template
       ↓
Replace placeholders (@@CODE, @@EmployeeName, @@MOBILENO)
       ↓
RepositoryActions.PROC_GET_SMS_EMAIL_TEMPLATEID() → Get DLT Template ID
       ↓
LoyaltyAPI.SMSAPI() → HTTP GET to SMS gateway
       ↓
RepositoryActions.PRO_INSERT_SMS_EMAIL_HISTORY() → Log result
       ↓
Return Success/Failure
```

---

## Document Information
| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | June 2026 |
| Audience | Vendor Onboarding |
| Classification | Internal Use Only |

---

**Note**: This document provides a high-level architectural overview. For detailed API specifications, database schema, and implementation details, refer to companion documents in the `/docs` folder.
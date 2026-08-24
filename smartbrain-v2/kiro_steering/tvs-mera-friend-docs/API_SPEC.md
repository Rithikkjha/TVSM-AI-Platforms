# TVS Employee Referral Portal - API Specification

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | employee-referral-portal |
| Repo | github.com/tvsmotorcompany/EmployeeReferralPortal |
| Team | Connected Commerce / D2C |
| Tech Lead | <!-- TODO: Add tech lead --> |
| Deployment | IIS / Azure App Service (ASP.NET MVC 5) |
| Base URL (prod) | https://{host}/{controller}/{action}/{id} |
| API Route | api/{controller}/{id} (Web API routing) |
| Default Entry Point | Login/Login |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | <!-- TODO: Add product owner --> | <!-- TODO --> |
| Tech Lead | <!-- TODO: Add tech lead --> | <!-- TODO --> |
| Dev Team | Connected Commerce / D2C Backend | <!-- TODO: Teams channel --> |
| On-call | <!-- TODO: Add rotation details --> | <!-- TODO --> |
| Vendor (if external) | N/A | N/A |

---

## Overview

This document provides a comprehensive API specification for the TVS Employee Referral Portal, an ASP.NET MVC 5 application with both server-rendered views and JSON API endpoints. The application manages employee loyalty programs including referrals, self-purchases, repurchases, and accessories.

---

## Inbound — My API Endpoints (Who Calls Me)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | /Login/CheckDomainAccess | None | Validates if an email domain is allowed | TVS Connect App, Sister Company Portal, Admin Portal |
| POST | /Login/SendOtp | None | Generates and sends OTP via email | TVS Connect App, Sister Company Portal |
| POST | /Login/ValidateOtp | None (session-bound) | Validates the OTP entered by user | TVS Connect App, Sister Company Portal |
| POST | /Login/LoginAzureAD | None (self-authenticating) | Azure AD SSO login with token validation | TVS Motor Employees (browser), Admin Portal |
| GET | /Login/KIOSLogin_Authentication | None | Authenticates KIOS kiosk users | KIOS Kiosk Terminals, Dealer Kiosks |
| POST | /Employee/EmployeeReferral | Session + Token | Submits a new employee referral | TVS Employee Portal (browser), KIOS Terminals |
| POST | /Employee/EmployeeRepurchase | Session + Token | Submits repurchase request | TVS Employee Portal (browser), KIOS Terminals |
| POST | /Employee/SelfPurchase | Session + Token | Submits self-purchase request | TVS Employee Portal (browser) |
| POST | /Employee/EmployeeRedemption | Session + Token | Processes point redemption | TVS Employee Portal (browser) |
| GET | /Employee/EmployeeReferralHistory | Session + Token | Retrieves referral history | TVS Employee Portal (browser) |
| POST | /Employee/DealerList | Session + Token | Retrieves dealer list by location | TVS Employee Portal (browser), KIOS Terminals |
| POST | /Employee/CancelReferral | Session + Token | Cancels an existing referral | TVS Employee Portal (browser) |
| POST | /Employee/ResendReferralCode | Session + Token | Resends referral code via SMS | TVS Employee Portal (browser) |
| POST | /Employee/ComplaintsDetail | Session + Token | Saves a new complaint | TVS Employee Portal (browser) |
| POST | /Employee/UploadID | Session + Token | Uploads identification document | TVS Employee Portal (browser) |
| POST | /Employee/REFERRAL_APPROVAL | Session + Token | Approves pending referral | Admin Portal |
| POST | /Employee/ReferalRejected | Session + Token | Rejects pending referral | Admin Portal |
| POST | /Employee/Reports | Session + Token | Generates various reports | Admin Portal |

---

## Outbound — Who This Service Calls

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| TVS Employee API (tvs1hub) | GET | /TVSApi/api/TVSM/GetEmployeeDetailsFromEmpno | Fetch employee details by emp number |
| TVS Employee API (tvs1hub) | GET | /TVSApi/api/TVSM/GetEmployeeDetailsFromEmailID | Fetch employee details by email |
| KIOS Auth API (tvs1hub) | POST | /KioskAPI/api/Auth/LoginCheck | KIOS user authentication |
| Notification Service (APIM) | POST | /notification-service/api/v1/notification/email | Send OTP emails and notifications |
| Azure AD Token Endpoint | POST | /oauth2/v2.0/token | Acquire OAuth2 bearer tokens |
| Azure AD JWKS Endpoint | GET | /discovery/v2.0/keys | Fetch public signing keys for JWT validation |
| SMS Panel API | GET | {PanelURL}?user=...&msg=... | Send transactional SMS (referrals, codes, alerts) |
| Dealer Info SOAP Service | SOAP | WSDealersInfoSoap12.getDealerInfo() | Get dealer information by city/state |
| Intranet SOAP Service (Legacy) | SOAP | intranetService.asmx (iLogin, iEmployee) | Employee lookup (deprecated) |
| ExactTouch Email Marketing API | POST | /API/mailing/ | Email campaigns for referrals and repurchases |

---

## Events & Messaging

### Topics This Service Publishes To

| Topic/Queue | Events | Format |
|-------------|--------|--------|
| N/A | This service does not currently use message queues or service bus topics | — |

### Topics This Service Subscribes To

| Topic/Queue | Events | Action |
|-------------|--------|--------|
| N/A | This service does not currently subscribe to any message topics | — |

> **Note:** This application uses synchronous REST/SOAP calls and SMS/email notifications. There is no event-driven messaging infrastructure (Azure Service Bus, RabbitMQ, etc.) in this service.

---

## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Azure AD (Entra ID) | Identity Provider | OAuth2/OIDC SSO for @tvsmotor.com employees | Client credentials + JWKS |
| TVS Employee Hub (tvs1hub) | REST API | Employee data lookup and KIOS authentication | API Key header |
| Notification Service (APIM) | REST API | OTP email delivery via Microsoft-hosted service | OAuth2 Bearer token |
| SMS Panel | REST API (HTTP) | Transactional SMS for referrals, codes, alerts | Username/Password in URL |
| Dealer Info Service | SOAP | Dealer information retrieval | Username/Password |
| ExactTouch | Email Marketing API | Referral/repurchase email campaigns | API Key |
| Intranet Service (Legacy) | SOAP (HTTP) | Employee data (deprecated, migrating to REST) | None |

---

## Data Storage

| Store | Type | Purpose |
|-------|------|---------|
| SQL Server (primary) | MSSQL | Primary application data — employees, referrals, repurchases, complaints, login, SMS/email history |
| IIS In-Process Session | Memory | Session state (auth tokens, OTP tracking, rate limiting, user context) |
| File System / Azure Blob | File Storage | Uploaded ID documents and profile pictures (jpg/pdf) |

> **Note:** No Redis or distributed cache is currently used. Rate limiting and session state are in-process only, which limits horizontal scaling.

---

## API Endpoint List (Detailed)

**Base URL:** `{controller}/{action}/{id}` (MVC routing)  
**API Route:** `api/{controller}/{id}` (Web API routing)  
**Default Entry Point:** `Login/Login`

---

## 1. API Endpoint List

### 1.1 Authentication Endpoints (LoginController)

| # | Endpoint | Description |
|---|----------|-------------|
| 1 | POST /Login/CheckDomainAccess | Validates if an email domain is allowed access |
| 2 | POST /Login/SendOtp | Generates and sends OTP via email |
| 3 | POST /Login/ValidateOtp | Validates the OTP entered by user |
| 4 | POST /Login/LoginAzureAD | Azure AD SSO login with token validation |
| 5 | GET /Login/TestDatabase | Tests database connectivity (diagnostic) |
| 6 | GET /Login/KIOSLogin_Authentication | Authenticates KIOS (kiosk) users |
| 7 | POST /Login/VerifyOtp | Verifies OTP for standard login flow |
| 8 | POST /Login/ResendOtp | Resends OTP to registered contact |
| 9 | POST /Login/ClearOrInitializationSessionOnAnchorClick | Clears/resets session variables |
| 10 | GET /Login/LogOut | Logs out user and clears session |
| 11 | GET /Login/Login | Renders primary login view |
| 12 | GET /Login/Login_2 | Renders secondary login view |
| 13 | GET /Login/Login_Creat | Renders login creation view |
| 14 | GET /Login/KIOS_Login | Renders KIOS login view |
| 15 | GET /Login/Admin_Login_Creat | Renders admin login view |
| 16 | GET /Login/LoginNew | Renders new login view with OAuth config |
| 17 | GET /Login/SisterCompanyLogin | Renders sister company login view |
| 18 | GET /Login/KIOSLOGINNEW | Sister company KIOS login flow |

### 1.2 SSO Endpoints (SSOController)

| # | Endpoint | Description |
|---|----------|-------------|
| 19 | GET /SSO/Login | Renders SSO login view |
| 20 | GET /SSO/Consumer | Renders SSO consumer callback view |
| 21 | GET /SSO/SignIn | Initiates OpenID Connect authentication challenge |
| 22 | GET /SSO/SignOut | Signs out from OIDC and Cookie authentication |

### 1.3 Employee Endpoints (EmployeeController)

| # | Endpoint | Description |
|---|----------|-------------|
| 23 | POST /Employee/UpdateProfile | Updates employee profile information |
| 24 | GET /Employee/UpdateProfile/{id} | Retrieves employee profile for editing |
| 25 | GET /Employee/EmployeeReferral | Loads referral creation form with master data |
| 26 | POST /Employee/EmployeeReferral | Submits a new employee referral |
| 27 | GET /Employee/EmployeeRepurchase | Loads repurchase form |
| 28 | POST /Employee/EmployeeRepurchase | Submits employee repurchase request |
| 29 | GET /Employee/SelfPurchase | Loads self-purchase form |
| 30 | POST /Employee/SelfPurchase | Submits self-purchase request |
| 31 | POST /Employee/EmployeeRedemption | Processes employee point redemption |
| 32 | GET /Employee/EmployeeReferralHistory | Retrieves referral history |
| 33 | GET /Employee/EmployeeAccessoriesHistory | Retrieves accessories purchase history |
| 34 | GET /Employee/EmployeeRepurchaseHistory | Retrieves repurchase history |
| 35 | POST /Employee/DealerList | Retrieves dealer list filtered by location |
| 36 | POST /Employee/DealerAddress | Gets dealer address by ID and location |
| 37 | POST /Employee/CancelReferral | Cancels an existing referral |
| 38 | POST /Employee/ResendReferralCode | Resends referral code via SMS |
| 39 | POST /Employee/ResendRepurchase | Resends repurchase code via SMS |
| 40 | POST /Employee/GetDealerName | Gets dealer names by area/state/city |
| 41 | POST /Employee/GetArea | Gets area list by state/city |
| 42 | GET /Employee/ComplaintsDetail | Retrieves complaint details |
| 43 | POST /Employee/ComplaintsDetail | Saves a new complaint |
| 44 | POST /Employee/UploadID | Uploads identification document |
| 45 | POST /Employee/UploadProfilePicture | Uploads employee profile picture |
| 46 | GET /Employee/EMICalculatorNew | Loads EMI calculator with active models |
| 47 | POST /Employee/Reports | Generates various reports |
| 48 | GET /Employee/Ambassadors | Loads ambassadors page |
| 49 | POST /Employee/REFERRAL_APPROVAL | Approves pending referral |
| 50 | POST /Employee/ReferalRejected | Rejects pending referral |

### 1.4 Home/Navigation Endpoints (HomeController)

| # | Endpoint | Description |
|---|----------|-------------|
| 51 | GET /Home/Index | Home page |
| 52 | GET /Home/EmployeeHome | Employee home (sets auth cookie) |
| 53 | GET /Home/EmployeeHomeNew | New employee home layout |
| 54 | GET /Home/NotFound | Custom 404 page |
| 55 | GET /Home/Err | Error page with ELMAH integration |
| 56 | GET /Home/ProgramFeatures | Program features info page |
| 57 | GET /Home/ReferralSelfPurchaseCode | Referral/self-purchase code info |
| 58 | GET /Home/RedemptionProcess | Redemption process info |
| 59 | GET /Home/Others | Other info page |
| 60 | GET /Home/winner | Winners page |
| 61 | GET /Home/FAQ | FAQ page |
| 62 | GET /Home/ABOUTPPROGRAM | About program page |
| 63 | GET /Home/AboutPageOthers | About page (others) |

### 1.5 Dashboard Endpoints (DashBoardController)

| # | Endpoint | Description |
|---|----------|-------------|
| 64 | GET /DashBoard/Index | Dashboard home |

---

## 2. Request Methods

| HTTP Method | Count | Endpoints |
|-------------|-------|-----------|
| GET | 34 | Login views, Employee forms, Home pages, SSO, History, Reports |
| POST | 30 | Authentication, Form submissions, AJAX operations, File uploads |

### Method Distribution by Controller

| Controller | GET | POST | Total |
|------------|-----|------|-------|
| LoginController | 8 | 10 | 18 |
| SSOController | 4 | 0 | 4 |
| EmployeeController | 12 | 16 | 28 |
| HomeController | 13 | 0 | 13 |
| DashBoardController | 1 | 0 | 1 |

### Content Types

| Content-Type | Usage |
|--------------|-------|
| `application/x-www-form-urlencoded` | Standard form submissions, AJAX POST |
| `multipart/form-data` | File uploads (UploadID, UploadProfilePicture) |
| `application/json` | LoginAzureAD response, DealerList response |
| `text/html` | View-based GET responses |

---

## 3. Authentication Requirements

### 3.1 Authentication Methods

| Method | Description | Target Users |
|--------|-------------|--------------|
| Azure AD SSO (OpenID Connect) | Enterprise SSO for @tvsmotor.com employees | Primary staff login |
| KIOS Login | Kiosk-based login via external API + password | Group company / dealer users |
| Sister Company OTP | Email OTP-based authentication | Sister company employees |
| Forms Authentication | ASP.NET session-based cookie auth | All authenticated sessions |

### 3.2 Token Management

| Token Type | Storage | Lifetime | Validation |
|------------|---------|----------|------------|
| Azure Entra JWT | Session["AzureEntraToken"] | 30 minutes | JWKS endpoint verification |
| KIOS API Token | Returned from external API | Per-session | Third-party validated |
| Forms Auth Cookie | .ASPXAUTH cookie | Session duration | ASP.NET built-in |

### 3.3 Endpoint Authentication Matrix

| Endpoint Category | Auth Required | Auth Type |
|-------------------|---------------|-----------|
| Login views (GET) | No | Public |
| CheckDomainAccess | No | Public |
| SendOtp | No | Public |
| ValidateOtp | No | Public (session-bound) |
| LoginAzureAD | No | Self-authenticating |
| TestDatabase | No | Public (diagnostic) |
| Employee/* (GET forms) | Yes | Session + Token + KIOS check |
| Employee/* (POST actions) | Yes | Session + Token + KIOS check |
| Home/* | No | Public |
| SSO/SignIn | No | Triggers OIDC |
| SSO/SignOut | Yes | Authenticated user |

### 3.4 OAuth Configuration (Web.config AppSettings)

| Key | Purpose |
|-----|---------|
| `EntraTenantId` | Azure AD Tenant ID |
| `EntraClientId` | Application Client ID |
| `EntraClientSecret` | Application Client Secret |
| `EntraAudience` | Token audience |
| `OAuthTenantId` | Notification service tenant |
| `OAuthClientId` | Notification service client |
| `OAuthClientSecret` | Notification service secret |
| `OAuthScope` | Notification service scope |
| `OAuthNotificationAPI` | Notification API URL |

### 3.5 Session Variables (Post-Authentication)

| Variable | Purpose |
|----------|---------|
| `Session["AzureEntraToken"]` | Bearer token for API authorization |
| `Session["UserID"]` | Logged-in user ID |
| `Session["RoleID"]` | User role identifier |
| `Session["EmployeeCode"]` | Employee number |
| `Session["EmployeeName"]` | Employee display name |
| `Session["LoginType"]` | Login type (Normal/KIOS/GROUPKIOS/SISTERCOMPANY) |
| `Session["AttemptKios"]` | KIOS login state flag |
| `Session["KIOS_DOJ_Validated"]` | DOJ validation completion flag |
| `Session["Menu"]` | Authorized menu items |

---

## 4. Request Payloads

### 4.1 POST /Login/CheckDomainAccess

```json
{
  "email": "user@tvsmotor.com"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email address to check domain access |

---

### 4.2 POST /Login/SendOtp

```json
{
  "email": "user@tvsgroup.com"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email address to receive OTP |

---

### 4.3 POST /Login/ValidateOtp

```json
{
  "email": "user@tvsgroup.com",
  "otp": "aB3xY9"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email used to generate OTP |
| otp | string | Yes | 6-character alphanumeric OTP |

---

### 4.4 POST /Login/LoginAzureAD

```json
{
  "employee_email": "user@tvsmotor.com",
  "id_token": "<JWT_ID_TOKEN>"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| employee_email | string | Yes | Employee email address |
| id_token | string | Yes | Azure AD JWT ID token |

---

### 4.5 GET /Login/KIOSLogin_Authentication

Query string parameters:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| UserID | string | Yes | Employee number |
| source | string | No | Login source identifier |

---

### 4.6 POST /Login/VerifyOtp

```json
{
  "otpTextVal": "123456"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| otpTextVal | string | Yes | OTP value to verify |

---

### 4.7 POST /Employee/UpdateProfile

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| EmployeeCode | string | Yes | Employee identifier |
| EmployeeName | string | Yes | Full name |
| DOB | string | Yes | Date of birth |
| MobileNumber | string | Yes | Primary mobile number |
| EmailId | string | Yes | Email address |
| FatherName | string | No | Father's name |
| BloodGroup | string | No | Blood group |
| City | string | No | City |
| State | string | No | State |
| Pincode | string | No | PIN code |
| Address1 | string | No | Address line 1 |
| Address2 | string | No | Address line 2 |
| Address3 | string | No | Address line 3 |
| AlterNameContactNumber | string | No | Alternate contact number |
| AlterNameEmailId | string | No | Alternate email address |

---

### 4.8 POST /Employee/EmployeeReferral

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ReferredPersonname | string | Yes | Name of referred person |
| EmployeeModel | string | Yes | Vehicle model of interest |
| Insentives | string | Yes* | Incentive scheme ID (0 or 1) |
| EmployeeMobileNo | string | Yes | Employee mobile number |
| EmployeeFriendMobileNo | string | Yes | Referred person's mobile |
| TentativeTime | string | No | Preferred contact time |
| TentativeDate | string | No | Preferred contact date |
| EmployeeRelation | string | No | Relationship to referred person |
| EmployeeName | string | No | Employee name |
| EmployeeGroupCompanyName | string | No | Group company name |
| EmployeeGroupCompanyNameOther | string | No | Other company name |
| DealerId | string | No | Preferred dealer (format: DEAL_XXXXX) |
| file | File | No | Supporting document (jpg/pdf) |

*Required only for KIOS 99999 non-GROUPKIOS/SISTERCOMPANY users.

---

### 4.9 POST /Employee/DealerList

```json
{
  "Operation": "C",
  "State": "TN",
  "City": "1"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Operation | string | Yes | "C" for DB query, others for SOAP call |
| State | string | Yes | State code/ID |
| City | string | Yes | City code/ID |

---

### 4.10 POST /Employee/DealerAddress

```json
{
  "DealerID": "D001",
  "City": "Chennai",
  "State": "TN"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| DealerID | string | Yes | Dealer identifier |
| City | string | Yes | City name |
| State | string | Yes | State name |

---

### 4.11 POST /Employee/CancelReferral

```json
{
  "REFERRED_CODE": "EMR150200000005RF20",
  "EMP_NO": "6774"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| REFERRED_CODE | string | Yes | Referral code to cancel |
| EMP_NO | string | Yes | Employee number |

---

### 4.12 POST /Employee/ResendReferralCode

```json
{
  "REFERRED_CODE": "EMR150200000005RF20",
  "EMP_NO": "6774"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| REFERRED_CODE | string | Yes | Referral code to resend |
| EMP_NO | string | Yes | Employee number |

---

### 4.13 POST /Employee/ResendRepurchase

```json
{
  "REPURCHASECODE": "REP20240001",
  "EMP_NO": "6774",
  "EMP_NAME": "John Doe",
  "MOBILE_NO": "9876543210"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| REPURCHASECODE | string | Yes | Repurchase code |
| EMP_NO | string | Yes | Employee number |
| EMP_NAME | string | Yes | Employee name |
| MOBILE_NO | string | Yes | Mobile number for SMS |

---

### 4.14 POST /Employee/GetDealerName

```json
{
  "AreaName": "North",
  "StateName": "Tamil Nadu",
  "CityName": "Chennai",
  "Type": "S"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| AreaName | string | Yes | Area filter |
| StateName | string | Yes | State filter |
| CityName | string | Yes | City filter |
| Type | string | Yes | Query type |

---

### 4.15 POST /Employee/ComplaintsDetail (Save)

```json
{
  "TYPE": 1,
  "ABOUT": 2,
  "DEALER_SERVICE_STN": 101,
  "CUSTOMER_ID": 5001,
  "DETAILS": "Issue description text",
  "FrameNumber": "MD2A17EZ5RCA12345",
  "COMPLAINT_SOURCE": "PORTAL",
  "EMP_ID": "6774",
  "EMP_PHONE": "9876543210"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| TYPE | int | Yes | Complaint type ID |
| ABOUT | int | Yes | Complaint about category |
| DEALER_SERVICE_STN | int | No | Dealer/service station ID |
| CUSTOMER_ID | int | No | Customer ID |
| DETAILS | string | Yes | Complaint description |
| FrameNumber | string | No | Vehicle frame number |
| COMPLAINT_SOURCE | string | No | Source of complaint |
| EMP_ID | string | Yes | Employee ID |
| EMP_PHONE | string | No | Employee phone |

---

### 4.16 POST /Employee/UploadID

Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | ID document (jpg/pdf only) |

---

## 5. Response Payloads

### 5.1 Standard JSON Success Response

```json
{
  "success": true,
  "message": "Operation completed successfully"
}
```

### 5.2 POST /Login/CheckDomainAccess

**Success:**
```json
{
  "success": true,
  "message": "Domain access allowed"
}
```

**Failure:**
```json
{
  "success": false,
  "message": "No access to this domain"
}
```

---

### 5.3 POST /Login/SendOtp

**Success:**
```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

**Rate Limited:**
```json
{
  "success": false,
  "message": "Please wait 15 minute(s) before requesting OTP again."
}
```

---

### 5.4 POST /Login/ValidateOtp

**Success:**
```json
{
  "success": true,
  "message": "OTP validated"
}
```

**Expired:**
```json
{
  "success": false,
  "message": "OTP expired. Please request a new one."
}
```

**Incorrect:**
```json
{
  "success": false,
  "message": "Incorrect OTP. 4 attempts remaining."
}
```

**Locked:**
```json
{
  "success": false,
  "message": "Too many failed attempts. Account locked for 15 minutes."
}
```

---

### 5.5 POST /Login/LoginAzureAD

**Success:** Session established with redirect to employee home.

**Failure:**
```json
["Invalid Credentials", "Invalid or expired token. Please sign in again."]
```

**Email Mismatch:**
```json
["Invalid Credentials", "Please enter valid user name and password"]
```

---

### 5.6 GET /Login/TestDatabase

```json
{
  "success": true,
  "message": "Database connection successful. TVSAPPDomainMaster table has 5 records."
}
```

---

### 5.7 GET /Login/KIOSLogin_Authentication

**Success:**
```json
{
  "redirectUrl": "/Employee/ReferAFriend"
}
```

**Failure:**
```json
{
  "redirectUrl": "/Login/KIOS_Login"
}
```

---

### 5.8 POST /Employee/DealerList

```json
[
  {
    "DealerID": "D001",
    "DealerName": "TVS Showroom Chennai",
    "Address1": "123 Main Road",
    "Address2": "Anna Nagar",
    "Location": "Chennai",
    "City": "Chennai",
    "State": "TN",
    "PinCode": "600040"
  }
]
```

---

### 5.9 POST /Employee/DealerAddress

```json
"123 Main Road, Anna Nagar"
```

---

### 5.10 POST /Employee/CancelReferral

```json
"Deleted Successfully"
```

---

### 5.11 POST /Employee/ResendReferralCode

```json
"Succesfully Sent"
```

---

### 5.12 POST /Employee/ResendRepurchase

```json
"Succesfully Sent"
```

---

### 5.13 Data Models in Responses

#### EmployeeJsonClass

```json
{
  "EMPNAME": "string",
  "EMP_FNAME": "string",
  "EMP_DESIG": "string",
  "DOB": "string",
  "DOJ": "string",
  "GRADE": "string",
  "CATG_DESC": "string",
  "LOC": "string",
  "GENDER": "string",
  "MOBILE": "string",
  "DISTRICT": "string",
  "DEPT": "string",
  "email_id": "string",
  "EMPNO": "string"
}
```

#### DealerJson

```json
{
  "DealerID": "string",
  "DealerName": "string",
  "Address1": "string",
  "Address2": "string",
  "Location": "string",
  "City": "string",
  "State": "string",
  "PinCode": "string",
  "Phone1": "string",
  "EmailID": "string",
  "SalesOffice": "string",
  "AreaManagerId": "string",
  "AreaManagerName": "string",
  "ContactPersonName": "string",
  "ContactPersonPhoneNumber": "string"
}
```

#### Complaints Entity

```json
{
  "Id": "int64",
  "TYPE": "int32",
  "ABOUT": "int32",
  "DEALER_SERVICE_STN": "int32",
  "CUSTOMER_ID": "int32",
  "DETAILS": "string",
  "TRACK": "string",
  "FrameNumber": "string",
  "Status": "int32 (nullable)",
  "OPENDATE": "datetime",
  "CLOSEDATE": "datetime (nullable)",
  "COMPLAINT_SOURCE": "string",
  "COMPLAINT_TYPE_MASTER_ID": "int64 (nullable)",
  "EMP_ID": "string",
  "EMP_PHONE": "string",
  "ISEMAILSENT": "string",
  "MAILSENTDATE": "datetime (nullable)",
  "REMARKS": "string"
}
```

#### Login Entity

```json
{
  "Id": "int64",
  "EncUserid": "string (encrypted)",
  "EncrPassword": "string (encrypted)",
  "Salt": "int64",
  "Track": "string"
}
```

---

## 6. Error Responses

### 6.1 Standard Error Format

Most JSON endpoints return:
```json
{
  "success": false,
  "message": "Error description"
}
```

### 6.2 Authentication Error (Array Format)

Used by LoginAzureAD and token-protected endpoints:
```json
["401", "Unauthorized - Token missing or invalid"]
```

### 6.3 Unhandled Exception Error

```json
{
  "success": false,
  "message": "Error [action]: [exception message]"
}
```

### 6.4 HTTP Status Codes

| Code | Usage | Trigger |
|------|-------|---------|
| 200 | Success | Successful JSON or view response |
| 302 | Redirect | After form submission or auth failure redirect |
| 400 | Bad Request | Duplicate/invalid query parameters |
| 401 | Unauthorized | Missing/invalid/expired token |
| 404 | Not Found | Unmatched URL (catch-all route) |
| 500 | Server Error | Unhandled exceptions (ELMAH logged) |

### 6.5 Error Responses by Endpoint

| Endpoint | Error Scenario | Response |
|----------|----------------|----------|
| CheckDomainAccess | Empty email | `{"success":false,"message":"Email is required"}` |
| CheckDomainAccess | Domain not allowed | `{"success":false,"message":"No access to this domain"}` |
| SendOtp | Empty email | `{"success":false,"message":"Email is required"}` |
| SendOtp | Domain not allowed | `{"success":false,"message":"No access to this domain"}` |
| SendOtp | Rate limited | `{"success":false,"message":"Please wait X minute(s)..."}` |
| SendOtp | Token failure | `{"success":false,"message":"Authentication failed while acquiring token"}` |
| SendOtp | Email send failure | `{"success":false,"message":"Failed to send OTP","detail":"..."}` |
| ValidateOtp | Missing fields | `{"success":false,"message":"Email and OTP are required"}` |
| ValidateOtp | No OTP in session | `{"success":false,"message":"OTP not found. Please request again."}` |
| ValidateOtp | Email mismatch | `{"success":false,"message":"Email mismatch for OTP validation"}` |
| ValidateOtp | OTP expired | `{"success":false,"message":"OTP expired. Please request a new one."}` |
| ValidateOtp | Wrong OTP | `{"success":false,"message":"Incorrect OTP. N attempts remaining."}` |
| ValidateOtp | Account locked | `{"success":false,"message":"Too many failed attempts. Account locked for 15 minutes."}` |
| LoginAzureAD | Invalid token | `["Invalid Credentials","Invalid or expired token..."]` |
| LoginAzureAD | No email in token | `["Invalid Credentials","Unable to verify identity..."]` |
| KIOSLogin_Authentication | No token | `["401","Unauthorized - Token missing or invalid"]` |
| Employee/* | Session expired | Redirect to `/Login/Login_Creat` |
| Employee/* | Token invalid | `["401","Unauthorized - Token missing or invalid"]` |
| EmployeeReferral | Mobile starts with 0 | Redirect with TempData["Message"] = "Mobile Number first digit should not be zero" |

---

## 7. Validation Rules

### 7.1 Authentication Validation

| Rule | Endpoint(s) | Description |
|------|-------------|-------------|
| Email required | CheckDomainAccess, SendOtp | Must not be null or empty |
| Email format | SendOtp, ValidateOtp | Must contain @ with valid domain |
| Domain whitelist | CheckDomainAccess, SendOtp | Domain must exist in TVSAPPDomainMaster with IsActive=true |
| OTP format | Server-generated | 6-character alphanumeric (A-Z, a-z, 0-9) |
| OTP expiry | ValidateOtp | 15 minutes from generation time |
| OTP case-sensitive | ValidateOtp | Exact ordinal string comparison |
| Email-OTP match | ValidateOtp | Email must match the one used to generate OTP |
| JWT validation | LoginAzureAD | Signature, issuer, audience, lifetime validated |
| Email-token match | LoginAzureAD | Token-extracted email must match supplied email (case-insensitive) |
| Identity from token only | LoginAzureAD | Email derived ONLY from verified token, never from client input |

### 7.2 Employee Operations Validation

| Rule | Endpoint(s) | Description |
|------|-------------|-------------|
| Session auth required | All Employee endpoints | Valid Session["UserID"], Session["LoginType"], Session["RoleID"] |
| Token in session | All Employee endpoints | Valid Azure Entra token in session |
| KIOS auth check | EmployeeReferral, EmployeeRepurchase | `IsKIOSUserAuthenticated()` - verifies DOJ validation |
| Mobile no zero start | EmployeeReferral (POST) | First digit of mobile number must not be zero |
| Model validation | EmployeeReferral (POST) | Must be in valid model list from PROC_GET_SERIES |
| OTP verified mobiles | EmployeeReferral (POST) | EmployeeFriendMobileNo must match Session["VerifiedFriendNo"] |
| File type restriction | UploadID | Only jpg/pdf files allowed |
| DealerId format | EmployeeReferral (POST) | First 5 characters stripped if present |
| Referral eligibility | EmployeeReferral (POST) | PROC_ReferAFriendValidate must pass |
| Transfer Incentives required | EmployeeReferral (POST) | Required for KIOS 99999 non-GROUPKIOS/SISTERCOMPANY |

### 7.3 Session Security Validation (KIOS)

| Check | Description |
|-------|-------------|
| Session["UserID"] != null | User must have valid user ID |
| Session["LoginType"] != null | Login type must be set |
| Session["RoleID"] != null | Role must be assigned |
| Session["AttemptKios"] == "Start" | KIOS login flow must be completed |
| Session["KIOS_DOJ_Validated"] != null | DOJ validation prevents response manipulation |

---

## 8. Rate Limits

### 8.1 OTP Generation Rate Limit

| Parameter | Value | Configurable | Config Key |
|-----------|-------|--------------|------------|
| Max generation attempts | 3 (default) | Yes | `OTP_MaxAttempts` in Web.config |
| Block duration | 15 minutes (default) | Yes | `OTP_BlockDurationMinutes` in Web.config |
| Scope | Per email address | — | Session-based tracking |
| Reset mechanism | Automatic after block expires | — | — |
| Tracking storage | Server session | — | Session[rateLimitKey + "_Count"] |

**Behavior:**
1. Each OTP request increments the counter for that email
2. When counter reaches max attempts, user is blocked
3. Block persists for configured duration
4. After block expires, counter resets to 0

---

### 8.2 OTP Verification Rate Limit

| Parameter | Value | Configurable | Notes |
|-----------|-------|--------------|-------|
| Max failed verification attempts | 5 | No (hardcoded) | Per-email tracking |
| Lock duration | 15 minutes | No (hardcoded) | Blocks all verification attempts |
| Scope | Per email address | — | Session-based tracking |
| Reset mechanism | Automatic after lock expires | — | — |
| Tracking storage | Server session | — | Session[verifyRateLimitKey + "_FailedCount"] |

**Behavior:**
1. Each incorrect OTP increments the failed counter
2. After 5 failures, account is locked for 15 minutes
3. Successful OTP validation resets the counter
4. Lock expiry automatically resets the counter

---

### 8.3 Referral Resend Rate Limit

| Parameter | Value | Notes |
|-----------|-------|-------|
| Counter reset | On successful referral submission | Session-based |
| Scope | Per user (EncUserid) | Session[rateLimitKey + "_Count"] |

---

### 8.4 Rate Limiting Limitations

| Limitation | Description |
|------------|-------------|
| Session-based only | Clearing cookies/session resets all rate limits |
| Not IP-based | Same IP can bypass by creating new sessions |
| Not distributed | Multiple app servers don't share rate limit state |
| No global throttle | No application-level request throttling for non-OTP endpoints |
| No API gateway | No external rate limiting infrastructure |

---

## 9. External API Dependencies

### 9.1 TVS Employee Details API (REST)

| Property | Value |
|----------|-------|
| Base URL | `https://tvs1hub.tvsmotor.com/TVSApi/api/TVSM/` |
| Protocol | HTTPS (TLS 1.2) |
| Authentication | Header: `APIKey: TAAIN657JHBERT789ERT379BNH` |
| Timeout | Default HttpClient timeout |

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GetEmployeeDetailsFromEmpno?empno={id}` | GET | Get employee details by employee number |
| `GetEmployeeDetailsFromEmailID?emailID={email}` | GET | Get employee details by email ID |

**Response Schema:**
```json
{
  "data": [
    {
      "EMPNAME": "John Doe",
      "EMP_FNAME": "Robert Doe",
      "EMP_DESIG": "Manager",
      "DOB": "1990-01-15",
      "DOJ": "2015-06-01",
      "GRADE": "M1",
      "CATG_DESC": "Staff",
      "LOC": "Chennai",
      "GENDER": "M",
      "MOBILE": "9876543210",
      "DISTRICT": "Chennai",
      "DEPT": "Engineering",
      "email_id": "john.doe@tvsmotor.com",
      "EMPNO": "6774",
      "EMAIL": "john.doe@tvsmotor.com"
    }
  ]
}
```

---

### 9.2 KIOS Authentication API (REST)

| Property | Value |
|----------|-------|
| URL | `https://tvs1hub.tvsmotor.com/KioskAPI/api/Auth/LoginCheck` |
| Method | POST |
| Content-Type | `application/json` |
| Protocol | HTTPS (TLS 1.2) |

**Request:**
```json
{
  "empno": "6774",
  "password": "userpassword"
}
```

**Response:**
```json
{
  "statusMessage": "login Sucess",
  "data": "<JWT_TOKEN>"
}
```

**Business Logic:**
- If employee has `@tvsmotor.com` email AND `CATG_DESC != "workmen"` → "SSOLogin Failure" (must use SSO)
- Otherwise → KIOS password authentication proceeds

---

### 9.3 Notification Service API (REST)

| Property | Value |
|----------|-------|
| URL | Configured via `OAuthNotificationAPI` AppSetting |
| Example | `https://apim.tvsmotor.com/notification-service/api/v1/notification/email` |
| Method | POST |
| Authentication | Bearer token (OAuth2 client_credentials) |
| Token Endpoint | `https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token` |

**Request:**
```json
{
  "priority": "HIGH",
  "email": {
    "templateId": "200000000195649",
    "sender": "notify",
    "to": ["user@tvsgroup.com"],
    "sameThread": false,
    "bodyValues": {
      "otp": "aB3xY9"
    },
    "subjectValues": {}
  }
}
```

---

### 9.4 SMS Panel API (REST)

| Property | Value |
|----------|-------|
| URL | Configured in database (GET_PANEL_DETAILS stored procedure) |
| Method | GET (URL with query parameters) |
| Authentication | Username/Password (encrypted in DB, decrypted at runtime) |
| Purpose | Transactional SMS for referrals, repurchases, codes |

**URL Pattern:**
```
{PanelURL}user={username}&pswd={password}&sender={senderid}&recipient={mobile}&msg={text}&PE_ID=1601100000000004424&Template_ID={templateId}
```

**SMS Template Types:**
| Template | Trigger |
|----------|---------|
| First_Time | First-time employee portal login |
| self_purchase_self_buy | Self-purchase by employee |
| self_purchase_others_sms_to_employee | Purchase for others (to employee) |
| self_purchase_others_sms_to_customer | Purchase for others (to customer) |
| RepurchaseSecondMsg | Repurchase second message |
| Refere_First | First referral notification |
| Refere | Referral code to employee |
| Referred | Referral code to referred person |
| Forget Password | Password reset code |
| accessories_code_generation | Accessories code |
| Complain_alert_sms | Complaint alert |
| Reject_Referal_Request | Referral rejection |
| Approval_Referal_Request | Referral approval |

---

### 9.5 Dealer Info SOAP Service

| Property | Value |
|----------|-------|
| Client | `WSDealersInfoSoapClient("WSDealersInfoSoap12")` |
| Method | `getDealerInfo(username, password, city, state)` |
| Credentials | Username: `ePagemaker`, Password: `tvss@les123` |
| Protocol | SOAP |

**Response Fields:** DealerID, DealerName, Address1, Address2, Location, City, State, PinCode, Phone1, EmailID, SalesOffice, AreaManagerId, AreaManagerName, ContactPersonName, ContactPersonPhoneNumber

---

### 9.6 Intranet SOAP Service (Legacy/Deprecated)

| Property | Value |
|----------|-------|
| URL | `http://10.121.2.50/webservices_intranet/intranetService.asmx` |
| Methods | `iLogin`, `iEmployee`, `iEmployeeByEmail` |
| Status | Partially deprecated — migrated to REST APIs (9.1) |
| Protocol | SOAP over HTTP |

---

### 9.7 Azure AD Token Endpoint

| Property | Value |
|----------|-------|
| URL | `https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token` |
| Grant Type | `client_credentials` |
| Purpose | Acquire access tokens for notification service |
| Scope | Configured via `OAuthScope` AppSetting |

---

### 9.8 Azure AD JWKS Endpoint

| Property | Value |
|----------|-------|
| URL | `https://login.microsoftonline.com/{tenantId}/discovery/v2.0/keys` |
| Purpose | Fetch public signing keys for JWT token validation |
| Used By | `AzureEntraToken.ValidateTokenAsync()` |

---

### 9.9 Email Marketing API (ExactTouch)

| Property | Value |
|----------|-------|
| Base URL | `https://api.exacttouch.com/API/mailing/` |
| Authentication | API Key: `dee00a7343e40851aa413677c016a5ae` |
| Purpose | Email campaigns for referrals and repurchases |
| Operations | List creation, batch upload, message scheduling |

---

### 9.10 Dependency Summary

| # | Service | Protocol | Auth Method | Used For |
|---|---------|----------|-------------|----------|
| 1 | TVS Employee API | REST/HTTPS | API Key header | Employee lookup |
| 2 | KIOS Auth API | REST/HTTPS | None (credentials in body) | KIOS user login |
| 3 | Notification Service | REST/HTTPS | OAuth2 Bearer token | OTP email delivery |
| 4 | SMS Panel | REST/HTTP | Username/Password in URL | Transactional SMS |
| 5 | Dealer SOAP Service | SOAP/HTTP | Username/Password | Dealer information |
| 6 | Intranet SOAP (Legacy) | SOAP/HTTP | None | Employee data (deprecated) |
| 7 | Azure AD Token | REST/HTTPS | Client credentials | Token acquisition |
| 8 | Azure AD JWKS | REST/HTTPS | None | Token validation |
| 9 | ExactTouch Email | REST/HTTPS | API Key in URL | Email campaigns |

---

## 10. Sample Requests/Responses

### 10.1 Flow: Sister Company OTP Login

```http
### Step 1: Check Domain Access
POST /Login/CheckDomainAccess HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com
```
```json
Response: { "success": true, "message": "Domain access allowed" }
```

```http
### Step 2: Send OTP
POST /Login/SendOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com
```
```json
Response: { "success": true, "message": "OTP sent successfully" }
```

```http
### Step 3: Validate OTP
POST /Login/ValidateOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com&otp=aB3xY9
```
```json
Response: { "success": true, "message": "OTP validated" }
```

```http
### Step 4: KIOS Authentication
GET /Login/KIOSLogin_Authentication?UserID=99999&source=sister HTTP/1.1
```
```json
Response: { "redirectUrl": "/Employee/ReferAFriend" }
```

---

### 10.2 Flow: Azure AD SSO Login

```http
### Step 1: Initiate SSO
GET /SSO/SignIn HTTP/1.1
```
```
Response: 302 Redirect to https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/authorize?...
```

```http
### Step 2: Azure AD callback (handled by OWIN middleware)
### Step 3: Login with token
POST /Login/LoginAzureAD HTTP/1.1
Content-Type: application/x-www-form-urlencoded

employee_email=user@tvsmotor.com&id_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```
```json
Response (Success): Redirect to /Home/EmployeeHomeNew with session established
Response (Failure): ["Invalid Credentials", "Invalid or expired token. Please sign in again."]
```

---

### 10.3 Flow: Employee Referral Submission

```http
### Step 1: Load Referral Form
GET /Employee/EmployeeReferral HTTP/1.1
Cookie: .ASPXAUTH=<auth_cookie>
```
```
Response: 200 OK (HTML view with model/state/dealer dropdowns)
```

```http
### Step 2: Submit Referral
POST /Employee/EmployeeReferral HTTP/1.1
Content-Type: multipart/form-data; boundary=----FormBoundary
Cookie: .ASPXAUTH=<auth_cookie>

------FormBoundary
Content-Disposition: form-data; name="ReferredPersonname"

Jane Smith
------FormBoundary
Content-Disposition: form-data; name="EmployeeModel"

Apache RTR 160
------FormBoundary
Content-Disposition: form-data; name="Insentives"

1
------FormBoundary
Content-Disposition: form-data; name="EmployeeMobileNo"

9876543210
------FormBoundary
Content-Disposition: form-data; name="EmployeeFriendMobileNo"

9123456789
------FormBoundary
Content-Disposition: form-data; name="TentativeDate"

2026-06-15
------FormBoundary
Content-Disposition: form-data; name="DealerId"

DEAL_D001
------FormBoundary--
```
```
Response: 302 Redirect to /Employee/ReferAFriend
TempData["Message"]: "Thank you for your request. Your Referral code : EMR260600000001RF01"
```

---

### 10.4 Flow: Dealer Lookup

```http
### Get Dealer List
POST /Employee/DealerList HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: .ASPXAUTH=<auth_cookie>

Operation=C&State=TN&City=1
```
```json
Response: [
  {
    "DealerID": "D001",
    "DealerName": "TVS Showroom Anna Nagar",
    "Address1": "123 Main Road",
    "Address2": "Anna Nagar, Chennai"
  },
  {
    "DealerID": "D002",
    "DealerName": "TVS Showroom T Nagar",
    "Address1": "456 South Usman Road",
    "Address2": "T Nagar, Chennai"
  }
]
```

```http
### Get Dealer Address
POST /Employee/DealerAddress HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: .ASPXAUTH=<auth_cookie>

DealerID=D001&City=Chennai&State=TN
```
```json
Response: "123 Main Road, Anna Nagar, Chennai"
```

---

### 10.5 Flow: Cancel and Resend Referral

```http
### Cancel Referral
POST /Employee/CancelReferral HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: .ASPXAUTH=<auth_cookie>

REFERRED_CODE=EMR150200000005RF20&EMP_NO=6774
```
```json
Response: "Deleted Successfully"
```

```http
### Resend Referral Code
POST /Employee/ResendReferralCode HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: .ASPXAUTH=<auth_cookie>

REFERRED_CODE=EMR150200000005RF20&EMP_NO=6774
```
```json
Response: "Succesfully Sent"
```
*Side Effect: SMS sent to both employee and referred person*

---

### 10.6 Flow: OTP Rate Limiting Scenario

```http
### Attempt 1 - Success
POST /Login/SendOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com
```
```json
Response: { "success": true, "message": "OTP sent successfully" }
```

```http
### Attempt 2 - Success
POST /Login/SendOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com
```
```json
Response: { "success": true, "message": "OTP sent successfully" }
```

```http
### Attempt 3 - Success (but triggers block)
POST /Login/SendOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com
```
```json
Response: { "success": true, "message": "OTP sent successfully" }
```

```http
### Attempt 4 - Blocked
POST /Login/SendOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com
```
```json
Response: { "success": false, "message": "Please wait 15 minute(s) before requesting OTP again." }
```

---

### 10.7 Flow: OTP Verification with Lockout

```http
### Wrong OTP - Attempt 1
POST /Login/ValidateOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com&otp=WRONG1
```
```json
Response: { "success": false, "message": "Incorrect OTP. 4 attempts remaining." }
```

```http
### Wrong OTP - Attempt 5 (Lockout)
POST /Login/ValidateOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com&otp=WRONG5
```
```json
Response: { "success": false, "message": "Too many failed attempts. Account locked for 15 minutes." }
```

```http
### After lockout (within 15 min)
POST /Login/ValidateOtp HTTP/1.1
Content-Type: application/x-www-form-urlencoded

email=user@tvsgroup.com&otp=aB3xY9
```
```json
Response: { "success": false, "message": "Too many failed attempts. Please try again after 14 minutes." }
```

---

## Appendix A: OpenAPI 3.0 Specification

```yaml
openapi: 3.0.3
info:
  title: TVS Employee Referral Portal API
  version: 1.0.0
  description: Internal employee loyalty and referral management system

servers:
  - url: https://{host}
    variables:
      host:
        default: localhost

paths:
  /Login/CheckDomainAccess:
    post:
      summary: Check if email domain is allowed
      tags: [Authentication]
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [email]
              properties:
                email:
                  type: string
                  format: email
      responses:
        '200':
          description: Domain check result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiResponse'

  /Login/SendOtp:
    post:
      summary: Send OTP to email
      tags: [Authentication]
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [email]
              properties:
                email:
                  type: string
                  format: email
      responses:
        '200':
          description: OTP send result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiResponse'

  /Login/ValidateOtp:
    post:
      summary: Validate OTP
      tags: [Authentication]
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [email, otp]
              properties:
                email:
                  type: string
                  format: email
                otp:
                  type: string
                  minLength: 6
                  maxLength: 6
      responses:
        '200':
          description: OTP validation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiResponse'

  /Login/LoginAzureAD:
    post:
      summary: Azure AD SSO login
      tags: [Authentication]
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [employee_email, id_token]
              properties:
                employee_email:
                  type: string
                  format: email
                id_token:
                  type: string
                  description: Azure AD JWT ID token
      responses:
        '200':
          description: Login result
          content:
            application/json:
              schema:
                type: array
                items:
                  type: string

  /Login/KIOSLogin_Authentication:
    get:
      summary: KIOS kiosk user authentication
      tags: [Authentication]
      parameters:
        - name: UserID
          in: query
          required: true
          schema:
            type: string
        - name: source
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Authentication result with redirect URL
          content:
            application/json:
              schema:
                type: object
                properties:
                  redirectUrl:
                    type: string

  /Employee/DealerList:
    post:
      summary: Get dealers by location
      tags: [Employee]
      security:
        - sessionAuth: []
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [Operation, State, City]
              properties:
                Operation:
                  type: string
                  enum: [C, W]
                State:
                  type: string
                City:
                  type: string
      responses:
        '200':
          description: Dealer list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Dealer'

  /Employee/DealerAddress:
    post:
      summary: Get dealer address
      tags: [Employee]
      security:
        - sessionAuth: []
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [DealerID, City, State]
              properties:
                DealerID:
                  type: string
                City:
                  type: string
                State:
                  type: string
      responses:
        '200':
          description: Dealer address string
          content:
            application/json:
              schema:
                type: string

  /Employee/CancelReferral:
    post:
      summary: Cancel a referral
      tags: [Employee]
      security:
        - sessionAuth: []
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [REFERRED_CODE, EMP_NO]
              properties:
                REFERRED_CODE:
                  type: string
                EMP_NO:
                  type: string
      responses:
        '200':
          description: Cancellation result
          content:
            application/json:
              schema:
                type: string
                example: "Deleted Successfully"

  /Employee/ResendReferralCode:
    post:
      summary: Resend referral code via SMS
      tags: [Employee]
      security:
        - sessionAuth: []
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [REFERRED_CODE, EMP_NO]
              properties:
                REFERRED_CODE:
                  type: string
                EMP_NO:
                  type: string
      responses:
        '200':
          description: Resend result
          content:
            application/json:
              schema:
                type: string
                example: "Succesfully Sent"

  /Employee/ResendRepurchase:
    post:
      summary: Resend repurchase code via SMS
      tags: [Employee]
      security:
        - sessionAuth: []
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required: [REPURCHASECODE, EMP_NO, EMP_NAME, MOBILE_NO]
              properties:
                REPURCHASECODE:
                  type: string
                EMP_NO:
                  type: string
                EMP_NAME:
                  type: string
                MOBILE_NO:
                  type: string
      responses:
        '200':
          description: Resend result
          content:
            application/json:
              schema:
                type: string
                example: "Succesfully Sent"

components:
  securitySchemes:
    sessionAuth:
      type: apiKey
      in: cookie
      name: .ASPXAUTH
      description: ASP.NET Forms Authentication cookie
    bearerToken:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    ApiResponse:
      type: object
      properties:
        success:
          type: boolean
        message:
          type: string

    Dealer:
      type: object
      properties:
        DealerID:
          type: string
        DealerName:
          type: string
        Address1:
          type: string
        Address2:
          type: string
        Location:
          type: string
        City:
          type: string
        State:
          type: string
        PinCode:
          type: string
        Phone1:
          type: string
        EmailID:
          type: string
          format: email
        SalesOffice:
          type: string
        AreaManagerId:
          type: string
        AreaManagerName:
          type: string
        ContactPersonName:
          type: string
        ContactPersonPhoneNumber:
          type: string

    Employee:
      type: object
      properties:
        EMPNAME:
          type: string
        EMP_FNAME:
          type: string
        EMP_DESIG:
          type: string
        DOB:
          type: string
        DOJ:
          type: string
        GRADE:
          type: string
        CATG_DESC:
          type: string
        LOC:
          type: string
        GENDER:
          type: string
        MOBILE:
          type: string
        DISTRICT:
          type: string
        DEPT:
          type: string
        email_id:
          type: string
          format: email
        EMPNO:
          type: string

    Complaint:
      type: object
      required: [TYPE, ABOUT, DETAILS, EMP_ID]
      properties:
        TYPE:
          type: integer
        ABOUT:
          type: integer
        DEALER_SERVICE_STN:
          type: integer
        CUSTOMER_ID:
          type: integer
        DETAILS:
          type: string
        FrameNumber:
          type: string
        COMPLAINT_SOURCE:
          type: string
        EMP_ID:
          type: string
        EMP_PHONE:
          type: string
```

---

## Appendix B: Architecture Notes

| Property | Value |
|----------|-------|
| Framework | ASP.NET MVC 5 with Web API |
| ORM | Entity Framework (Code-First with data annotations) |
| Database | SQL Server (stored procedures for business logic) |
| Authentication | Hybrid (Azure AD SSO + Forms Auth + OTP) |
| Error Logging | ELMAH |
| External Integrations | REST APIs, SOAP services, SMS gateway |
| Session Storage | In-process (IIS session state) |
| TLS | TLS 1.2 enforced for all outbound HTTP calls |

## Appendix C: Stored Procedures (Database API Layer)

| Procedure | Purpose |
|-----------|---------|
| `PRO_LOGIN_CREDENTIALS` | Validate login credentials |
| `PROC_SelfPurchaseValidate` | Validate self-purchase eligibility |
| `PROC_SelfPurchaseSisterCompanyValidate` | Sister company purchase validation |
| `PROC_Store_SisterCompany_OTP` | Store OTP for sister company |
| `PROC_ReferAFriendValidate` | Validate referral eligibility |
| `PROC_ReferAFriendSisterCompanyValidate` | Sister company referral validation |
| `PROC_AccessoriesValidate` | Validate accessories purchase |
| `PROC_GetDiscountBalance` | Get remaining discount balance |
| `PROC_FORGET_PASSWORD` | Password reset |
| `PRO_INSERT_SMS_EMAIL_HISTORY` | Log SMS/email communications |
| `PROC_GET_SMS_EMAIL_TEMPLATE` | Get message template by touch code |
| `PROC_GET_SMS_EMAIL_TEMPLATEID` | Get template ID |
| `PRO_GET_USER_DTL` | Get user details by role |
| `PRO_EMP_EMI_INSERT_DTL` | Insert EMI calculation |
| `PRO_EMP_REDEMPTION_DTL` | Process redemption |
| `PROC_INSERT_LOGIN_USER_DTL` | Insert/update login user |
| `GET_PANEL_DETAILS` | Get SMS panel configuration |
| `GetCity` | Get cities by state |
| `ComplaintsSave` | Save complaint |
| `DELETE_REFERRAL` | Cancel referral |
| `PROC_REFERRAL_RESEND` | Resend referral code |
| `PROC_KIOS_OUTSIDER_LOGIN` | KIOS user login |
| `PROC_GET_DOCUMENT_SIZE_FORMATS` | Get upload constraints |
| `PROC_DOCUMENT_UPLOAD` | Process document upload |
| `PROC_EMP_KIOS_LOGIN_VERIFACTION` | KIOS login verification |
| `PROC_EMP_SEND_VELIDATION_CODE` | Send validation code |
| `PROC_EMP_PRE_REFERRAL_NOTIFICATION` | Pre-referral notification |
| `PROC_EMP_PRE_REFERRAL_CHECK` | Pre-referral eligibility check |
| `LoginCheckAzureAD` | Azure AD login check |

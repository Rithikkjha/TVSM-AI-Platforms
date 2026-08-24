# High Level Design — Employee Referral & Loyalty Portal

---

## Overview

The Employee Referral & Loyalty Portal is an internal web application that enables TVS Motor employees and sister company employees to participate in referral programs, self-purchase schemes, loyalty redemptions, and employee engagement activities. The system solves the problem of fragmented employee benefit tracking by providing a unified platform for referral code generation, discount management, dealer coordination, and automated notifications — while enforcing role-based access across multiple authentication channels (SSO, Kiosk, OTP).

---

## Tier Classification

**Tier 2: Business Critical but not Life-or-Death**

Rationale: The portal directly supports employee loyalty and referral programs which drive business outcomes (vehicle sales through employee referrals and self-purchase discounts). Downtime impacts employee engagement and dealer redemption workflows but does not affect mission-critical vehicle manufacturing or customer safety systems.

---

## Background

- The system was originally built on legacy SOAP-based SAP Intranet services for employee data. These have since been migrated to REST APIs via TVS1Hub platform.
- Authentication was initially employee-number + password only. SSO via Microsoft Entra ID was added to support corporate email users, and OTP-based login was introduced for sister company employees who don't have Entra ID accounts.
- Domain validation (TVSAPP_DOMAIN_MASTER table) was added to control which sister company email domains can access the portal.
- The application carries tech debt in the form of synchronous API calls, in-process session state, Base64 password encoding (not hashing), and no retry/circuit-breaker patterns on external dependencies.

---

## Requirements

### Functional

| # | Requirement |
|---|-------------|
| FR-1 | Employees authenticate via SSO (Microsoft Entra ID) for corporate users |
| FR-2 | Kiosk-based login for workmen/field staff via employee number + password |
| FR-3 | Sister company login via OTP to whitelisted email domains |
| FR-4 | Generate and track referral codes for employee-to-customer referrals |
| FR-5 | Generate self-purchase discount codes with eligibility validation |
| FR-6 | Generate accessories purchase codes |
| FR-7 | Process redemption at dealer level with discount calculation |
| FR-8 | EMI calculator for loan planning |
| FR-9 | Complaint registration and tracking with SMS alerts |
| FR-10 | Role-based menu and access control (Admin, Employee, Dealer, Kiosk) |
| FR-11 | SMS and email notifications for all key transactions |
| FR-12 | Employee profile sync from HR/SAP system |

### Non-Functional

| # | Requirement | Target |
|---|-------------|--------|
| NFR-1 | Availability | Business hours; corporate intranet hosted |
| NFR-2 | Session timeout | 120 minutes (server-side) / 110 minutes (auth cookie) |
| NFR-3 | Response time | < 3 seconds for page loads (excluding external API latency) |
| NFR-4 | Security headers | X-Frame-Options, X-Content-Type-Options, X-XSS-Protection |
| NFR-5 | OTP rate limiting | Max 3 generation attempts per 2-min window; Max 5 verification attempts per 15-min window |
| NFR-6 | TLS enforcement | TLS 1.2 for all outbound API calls |
| NFR-7 | Error logging | ELMAH with SQL-based persistent storage |
| NFR-8 | Browser support | IE11+, Chrome, Firefox, Edge |

---

## Current Architecture (HLD)

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                          │
│         ASP.NET MVC Views (Razor) + jQuery 1.9 + Bootstrap 3    │
├─────────────────────────────────────────────────────────────────┤
│                      CONTROLLER LAYER                            │
│  LoginController │ EmployeeController │ DashBoardController      │
│  SSOController   │ HomeController                                │
├─────────────────────────────────────────────────────────────────┤
│                      SERVICE / BUSINESS LAYER                    │
│  WebserviceCalling │ LoyaltyAPI │ OAuthTokenService              │
│  AzureEntraToken   │ Membership (Crypto)                         │
├─────────────────────────────────────────────────────────────────┤
│                      DATA ACCESS LAYER                           │
│  Repository (IEmployee) │ RepositoryActions (Stored Procedures)  │
│  Employee DbContext      │ TVSONEVIEW DbContext                   │
├─────────────────────────────────────────────────────────────────┤
│                      DATA STORE                                   │
│              Microsoft SQL Server (Entity Framework 6.4)          │
└─────────────────────────────────────────────────────────────────┘
```

**Key characteristics of current system:**
- Monolithic ASP.NET MVC 4 application on .NET Framework 4.8
- Two-project solution: `Employee_UI` (web app) + `Employee_Domain` (class library)
- In-process session state (not web-farm ready)
- Synchronous external API calls with no retry logic
- SOAP + REST hybrid integration pattern
- Forms Authentication with cookie-based sessions

---

## Proposed Architecture (HLD)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            USERS                                          │
│      Corporate Employees │ Workmen/Kiosk │ Sister Company Staff           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         IIS WEB SERVER                                    │
│                     ASP.NET MVC Application                               │
│                                                                          │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐    │
│  │   Login    │  │  Employee    │  │ Dashboard  │  │    SSO       │    │
│  │ Controller │  │ Controller   │  │ Controller │  │ Controller   │    │
│  └─────┬──────┘  └──────┬───────┘  └─────┬──────┘  └──────┬───────┘    │
│        │                 │                │                 │            │
│  ┌─────┴─────────────────┴────────────────┴─────────────────┴───────┐   │
│  │                    BUSINESS / SERVICE LAYER                        │   │
│  │  WebserviceCalling │ LoyaltyAPI │ RepositoryActions │ Membership   │   │
│  └───────────┬──────────────────────────────┬────────────────────────┘   │
│              │                              │                            │
│  ┌───────────┴──────────┐      ┌───────────┴──────────┐                │
│  │  Entity Framework 6  │      │   ADO.NET (SP Calls) │                │
│  │  (Read Operations)   │      │  (Write Operations)  │                │
│  └───────────┬──────────┘      └───────────┬──────────┘                │
└──────────────┼──────────────────────────────┼────────────────────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        SQL SERVER DATABASE                                │
│                     TVS_MOTOR_EMP_REF (Primary)                          │
│                     TVS_ONE_VIEW (Read-only)                             │
└──────────────────────────────────────────────────────────────────────────┘

               EXTERNAL DEPENDENCIES (shown in different shade)
┌──────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────┐ ┌───────────────┐ ┌─────────────────────────────┐    │
│  │ Microsoft     │ │ TVS1Hub       │ │ Azure API Management        │    │
│  │ Entra ID      │ │ Platform      │ │ (Notification Service)      │    │
│  │ (OIDC SSO)   │ │ (REST APIs)   │ │ (OAuth 2.0 Client Creds)    │    │
│  └───────────────┘ └───────────────┘ └─────────────────────────────┘    │
│                                                                          │
│  ┌───────────────┐ ┌───────────────┐ ┌─────────────────────────────┐    │
│  │ SMS Gateway   │ │ ExactTouch    │ │ Dealer Web Service           │    │
│  │ (HTTP GET)    │ │ (Email API)   │ │ (SOAP/HTTPS)                │    │
│  └───────────────┘ └───────────────┘ └─────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key Components & Interactions

| Component | Responsibility | Boundary |
|-----------|---------------|----------|
| **LoginController** | Authentication orchestration (SSO redirect, Kiosk auth, OTP flow) | Internal |
| **EmployeeController** | Referral, self-purchase, accessories, redemption, profile | Internal |
| **SSOController** | OpenID Connect sign-in/sign-out via OWIN middleware | Internal → Entra ID |
| **WebserviceCalling** | External API integration layer (TVS1Hub, Dealer WS) | Internal → External |
| **LoyaltyAPI** | SMS and Email dispatch orchestration | Internal → SMS/Email gateways |
| **OAuthTokenService** | OAuth 2.0 client credentials token acquisition | Internal → Azure AD |
| **Repository** | EF-based read operations + domain validation | Internal → SQL Server |
| **RepositoryActions** | Stored procedure execution for write operations | Internal → SQL Server |

### External Dependencies & Contracts

| Dependency | Contract | Protocol |
|------------|----------|----------|
| TVS1Hub — GetEmployeeDetailsFromEmpno | REST GET, API Key header | HTTPS |
| TVS1Hub — GetEmployeeDetailsFromEmailID | REST GET, API Key header | HTTPS |
| TVS1Hub — KioskAPI/Auth/LoginCheck | REST POST, JSON payload | HTTPS |
| Notification Service | REST POST, Bearer token (OAuth 2.0) | HTTPS via APIM |
| Dealer Info Service | SOAP, credentials in request body | HTTPS |
| SMS Gateway | HTTP GET, credentials in query string | HTTP/HTTPS |
| ExactTouch Email | HTTP GET, API Key in URL | HTTPS |

### Pros

- Proven, stable technology stack (.NET Framework 4.8, Entity Framework 6)
- Simple deployment model (single IIS application)
- Well-understood authentication patterns (Forms Auth + OWIN OIDC)
- Direct stored procedure calls provide fine-grained database control
- ELMAH provides zero-config error logging

### Cons

- Monolithic architecture limits independent scaling of modules
- In-process session prevents horizontal scaling without sticky sessions
- Synchronous external calls risk thread pool exhaustion under load
- No circuit breaker/retry pattern on external API failures
- Base64 password encoding (not industry-standard hashing like bcrypt/PBKDF2)
- Mixed SOAP + REST integration increases maintenance complexity

> **Note**: External dependency services/blocks are highlighted separately in the architecture diagram above (bottom section). These represent systems outside the team's operational control.

---

## Data Flow / Sequence Diagram

### Main User Flow: Employee Login

```
┌────────┐      ┌────────────────┐      ┌───────────┐      ┌──────────┐      ┌──────────┐
│Employee│      │LoginController │      │TVS1Hub API│      │Kiosk API │      │ Database │
└───┬────┘      └───────┬────────┘      └─────┬─────┘      └────┬─────┘      └────┬─────┘
    │                   │                     │                  │                  │
    │── EmpNo+Password ▶│                     │                  │                  │
    │                   │── GET /Employee ────▶│                  │                  │
    │                   │◀── {email, catg} ───│                  │                  │
    │                   │                     │                  │                  │
    │                   │─┐ Check: corporate                     │                  │
    │                   │ │ email & non-workmen?                  │                  │
    │                   │◀┘                   │                  │                  │
    │                   │                     │                  │                  │
    │              [If YES: return "SSOLogin Failure" → client redirects to SSO]    │
    │                   │                     │                  │                  │
    │              [If NO: proceed with Kiosk auth]              │                  │
    │                   │── POST /LoginCheck ────────────────────▶│                  │
    │                   │◀── {statusMessage, token} ─────────────│                  │
    │                   │                     │                  │                  │
    │                   │── PROC_INSERT_LOGIN_USER_DTL ─────────────────────────────▶│
    │                   │── PRO_LOGIN_CREDENTIALS ──────────────────────────────────▶│
    │                   │◀── {role, userId, session data} ──────────────────────────│
    │                   │                     │                  │                  │
    │◀── FormsAuth Cookie + Redirect to Home  │                  │                  │
```

### Sister Company OTP Flow

```
┌──────┐    ┌────────────────┐    ┌──────────┐    ┌────────────┐    ┌──────────────────┐
│ User │    │LoginController │    │Repository│    │OAuthService│    │Notification API  │
└──┬───┘    └───────┬────────┘    └────┬─────┘    └─────┬──────┘    └────────┬─────────┘
   │                │                  │                 │                    │
   │── Email ──────▶│                  │                 │                    │
   │                │── IsDomainAllowed▶│                 │                    │
   │                │◀── true ─────────│                 │                    │
   │                │                  │                 │                    │
   │                │── Generate 6-char OTP              │                    │
   │                │── GetAccessToken ─────────────────▶│                    │
   │                │◀── Bearer token ──────────────────│                    │
   │                │                  │                 │                    │
   │                │── POST /notification/email ────────────────────────────▶│
   │                │◀── 200 OK ─────────────────────────────────────────────│
   │                │                  │                 │                    │
   │                │── Store OTP (Session + proc_store_sistercompany_otp)   │
   │◀── "OTP Sent" ─│                  │                 │                    │
   │                │                  │                 │                    │
   │── Enter OTP ──▶│                  │                 │                    │
   │                │── Validate (session match, 15-min expiry, rate limit)  │
   │◀── Auth Cookie ─│                  │                 │                    │
```

### Retry & Error Handling Paths

| Scenario | Current Behavior | Failover Path |
|----------|-----------------|---------------|
| TVS1Hub API unavailable | Exception caught, generic error returned | No retry; user sees login failure |
| SMS Gateway timeout | Exception caught, logged to ELMAH | No retry; SMS silently fails |
| Notification API auth failure | Returns `null` token, OTP not sent | User informed "Authentication failed" |
| Database connection failure | Exception propagates to ELMAH | Custom error page displayed |
| OTP rate limit exceeded | Session-based block (2-min / 15-min) | User must wait; no bypass |

### Dependencies (Illustrated Example)

**Referral Code Generation Flow:**
1. Employee submits referral → EmployeeController
2. Controller calls `PROC_EMP_REFERRAL_BLOCK` → SQL Server validates eligibility
3. If eligible, controller calls referral insert stored procedure → Code generated
4. Controller calls `LoyaltyAPI.SMSAPI()` → SMS Gateway sends code to referred person
5. SMS history logged via `PRO_INSERT_SMS_EMAIL_HISTORY` → SQL Server

---

## Deployment & Rollout Plan

### Current Deployment Model

| Aspect | Detail |
|--------|--------|
| Hosting | IIS on Windows Server (corporate intranet) |
| Deployment method | Manual publish via Visual Studio / MSDeploy |
| Environments | Dev → UAT → Production (connection strings swapped per environment) |
| Configuration | Environment-specific via Web.config connection string comments |

### Rollback & Hotfix Strategy

| Strategy | Approach |
|----------|----------|
| Rollback | Re-deploy previous build artifact to IIS; no blue/green deployment |
| Hotfix | Direct code fix → build → deploy to production IIS |
| Database rollback | Manual SQL script execution (no automated migration) |
| Feature flags | Not implemented; full deployment per release |

### Recommended Improvements

- Implement feature flags for gradual rollout of new login flows
- Add health check endpoint (`/health`) for load balancer integration
- Move to CI/CD pipeline with automated deployment to UAT/Production
- Add blue/green or canary deployment capability

---

## Metrics to be Tracked

### Application Metrics / Alarms

| Metric | Source | Alarm Threshold |
|--------|--------|----------------|
| Login success/failure rate | ELMAH + custom logging | > 10% failure rate in 5-min window |
| OTP generation count | Session tracking / DB | Anomaly: > 100 OTPs/hour |
| External API response time | Application logs | > 5 seconds (TVS1Hub, Notification API) |
| Unhandled exceptions | ELMAH SQL log | > 5 errors in 10-min window |
| Session count (concurrent users) | IIS performance counters | Approaching application pool limits |
| SMS delivery failures | `PRO_INSERT_SMS_EMAIL_HISTORY` | > 20% failure rate |
| Database connection pool exhaustion | SQL Server DMVs | Active connections > 80% of max pool |

### Data Analytics / Data Engineering Metrics / Tables

| Table / Data Source | Purpose | Data Lake Enabled |
|---------------------|---------|-------------------|
| `PRO_INSERT_SMS_EMAIL_HISTORY` (SMS/Email log) | Track notification delivery rates | Not currently enabled |
| ELMAH error log | Error trend analysis | Not currently enabled |
| Login audit (via stored procedures) | Authentication analytics | Not currently enabled |
| Referral/Redemption transactions | Business KPI tracking | Not currently enabled |

> **Status**: Data lake integration is **not currently enabled**. All reporting is direct-from-database via stored procedures.

---

## Alternatives Considered

### Option A: Migrate to .NET Core / .NET 8 Microservices

| Aspect | Detail |
|--------|--------|
| Description | Decompose monolith into microservices (Auth Service, Referral Service, Notification Service) on .NET 8 with containerized deployment |

**Pros:**
- Independent scaling per module
- Modern async/await throughout
- Cross-platform deployment (Linux containers)
- Built-in dependency injection and health checks
- Industry-standard password hashing (ASP.NET Core Identity)

**Cons:**
- High migration effort (full rewrite)
- Requires container orchestration infrastructure (Kubernetes/ECS)
- Team reskilling needed for .NET Core patterns
- All stored procedures need re-evaluation
- Risk of regression during migration

### Option B: Incremental Modernization (Current Path with Enhancements)

| Aspect | Detail |
|--------|--------|
| Description | Keep .NET Framework 4.8 monolith but address critical gaps: externalize sessions, add retry policies, implement proper password hashing, add health checks |

**Pros:**
- Minimal disruption to current operations
- Incremental investment, lower risk
- Team can continue with existing skillset
- No infrastructure changes needed
- Faster time-to-value for each improvement

**Cons:**
- Remains on legacy framework (EOL considerations)
- Horizontal scaling still limited without session externalization
- Cannot leverage modern cloud-native patterns fully
- Accumulates more tech debt over time

---

## Risks (If Any)

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | In-process session loss on IIS recycle | Active users lose session mid-workflow | Medium | Externalize to SQL Server or Redis |
| 2 | TVS1Hub API downtime blocks all logins | Complete authentication failure | Low | Implement cached fallback for employee data |
| 3 | SMS Gateway failure silently drops notifications | Employees don't receive referral/purchase codes | Medium | Add retry with dead-letter queue; alert on failure rate |
| 4 | Base64 password encoding is reversible | Credential exposure if database is compromised | Medium | Migrate to bcrypt/PBKDF2 hashing |
| 5 | No request timeout on external HTTP calls | Thread pool exhaustion under load | Medium | Configure explicit HttpClient timeouts (30s) |
| 6 | .NET Framework 4.8 approaching end of mainstream support | Future security patches may not be available | Low | Plan migration path to .NET 8 LTS |
| 7 | Single database instance with no failover | Database outage = full application outage | Low | Configure SQL Always On or read replica |

---

## Appendix

### A. Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | .NET Framework | 4.8 |
| Web Framework | ASP.NET MVC | 4 |
| ORM | Entity Framework | 6.4.4 |
| Authentication | OWIN + Microsoft.IdentityModel | 4.2.2 / 8.7.0 |
| SSO Provider | Microsoft Entra ID | OAuth 2.0 / OIDC |
| JSON Library | Newtonsoft.Json | 10.0 |
| Error Logging | ELMAH | SQL-backed |
| Client-Side | jQuery 1.9.1 + Bootstrap 3 | — |
| Web Server | IIS | 8.5+ |
| Database | SQL Server | 2016+ |

### B. Database Schema (Key Tables)

| Table | Schema | Purpose |
|-------|--------|---------|
| `t_base_login_details` | dbo | Encrypted credentials + salt |
| `t_base_user_master` | dbo | User profiles, roles, org mapping |
| `t_base_user_role` | dbo | User-to-role assignments |
| `T_LOYALTY_EMP_MASTER` | dbo | Employee master records |
| `TVSAPP_DOMAIN_MASTER` | dbo | Whitelisted email domains |
| `TVS_GROUP_COMPANY` | dbo | Group company reference |

### C. Stored Procedures Reference

| Procedure | Purpose |
|-----------|---------|
| `PRO_LOGIN_CREDENTIALS` | Login validation with salt |
| `PROC_INSERT_LOGIN_USER_DTL` | First-time user registration |
| `PROC_FORGET_PASSWORD` | Password reset |
| `proc_emp_repurchase_block` | Self-purchase eligibility |
| `PROC_EMP_REFERRAL_BLOCK` | Referral eligibility |
| `PRO_EMP_REDEMPTION_DTL` | Redemption processing |
| `PRO_EMP_EMI_INSERT_DTL` | EMI calculation storage |
| `PRO_INSERT_SMS_EMAIL_HISTORY` | Notification audit trail |
| `proc_store_sistercompany_otp` | OTP storage |
| `PROC_CHECK_IS_FIELD_INSENTIVE` | Field incentive check |

### D. Role Matrix

| Role ID | Role Name | Access Level |
|---------|-----------|--------------|
| 999 | Administration | Full system access |
| 1 | Dealer | Dealer-specific operations |
| 2 | Customer | Customer-facing features |
| 3 | Employee | Employee referral, self-purchase, profile |
| 9 | Kiosk | Limited kiosk-based access |

### E. Network Endpoints

| Endpoint | Port | Protocol | Purpose |
|----------|------|----------|---------|
| SQL Server (internal) | 1433 | TCP | Database |
| login.microsoftonline.com | 443 | HTTPS | Entra ID SSO |
| tvs1hub.tvsmotor.com | 443 | HTTPS | Employee/Auth APIs |
| apim.tvsmotor.com | 443 | HTTPS | Notification Service |
| www.advantagetvs.com | 443 | HTTPS | Dealer SOAP service |
| SMS Gateway | 80/443 | HTTP/S | SMS delivery |
| api.exacttouch.com | 443 | HTTPS | Email delivery |

---

*Document generated from source code analysis. Sensitive credentials, connection strings, and internal IP addresses have been excluded for security.*

# CentralisedAPI — API Specification

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | CentralisedAPI (DIGI DMS) |
| Repo | github.com/tvsmotorcompany/CentralisedAPI |
| Team | DMS Backend |
| Deployment | IIS / Azure App Service |
| Base URL (prod) | https://www.advantagetvs.com/PartsAPISQL/ |
| Framework | ASP.NET Web API (.NET Framework 4.8) |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Dev Team | DMS Backend | sapna.bhandari@tvsmotor.com |
| Prod Approval | Engineering Leads | Dushyant.Satyapal@tvsmotor.com |

---

## My API Endpoints (Inbound)

### Authentication & Login

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | Login/GetDealerDetails | JWT Bearer | Fetch dealer details for login |
| POST | Login/ValidateLogin | None | Validate login credentials, return JWT |
| POST | Login/SaveEmployeeLoginDetails | JWT Bearer | Save employee login session |
| GET | Authentication/Callback | None | UMS OAuth callback |
| POST | Authentication/ums/profileinfo | JWT (UMS) | Get UMS user profile |
| POST | Authentication/ums/logout | JWT (UMS) | UMS logout (cache invalidation) |

### Job Card

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | JobCard/IsMobileNumberExist | JWT Bearer | Check if mobile number exists |
| GET | JobCard/GetComplaint | JWT Bearer | Get complaints for a job card |
| POST | JobCard/AddComplaints | JWT Bearer | Add complaints to job card |
| POST | JobCard/SaveJobCard | JWT Bearer | Create/update job card |
| GET | JobCard/GetJobCardDetails | JWT Bearer | Fetch job card details |
| POST | JobCard/CloseJobCard | JWT Bearer | Close a job card |
| GET | JobCard/GetFrameDetails | JWT Bearer | Get vehicle frame details |
| POST | JobCard/ValidateImage | HeaderKey | WIP image validation forwarding |

### Invoice

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | Invoice/GetProformaInvoice | JWT Bearer | Get proforma invoice |
| POST | Invoice/SaveInvoice | JWT Bearer | Save/generate invoice |
| GET | Invoice/GetInvoicePrint | JWT Bearer | Get invoice for printing |

### Customer

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | Customer/GetCustomerDetails | JWT Bearer | Fetch customer data |
| POST | Customer/SaveCustomer | JWT Bearer | Create/update customer |

### Master Data

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | Master/GetModelList | JWT Bearer | Vehicle model master |
| GET | Master/GetBranchList | JWT Bearer | Branch master |
| GET | Master/GetEmployeeList | JWT Bearer | Employee master |

### Parts

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | Parts/GetPartsList | JWT Bearer | Spare parts catalog |
| POST | Parts/IssueParts | JWT Bearer | Issue parts to job card |

### FRT (Flat Rate Time)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | FRTMaster/GetFRTList | JWT Bearer | FRT master data |
| GET | FRTModule/GetFRTModule | JWT Bearer | FRT module calculations |
| GET | FRTLabour/GetFRTLabour | JWT Bearer | FRT labour rates |

### Service Reminder (SMR)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | ServiceReminder/GetReminders | JWT Bearer | Get pending service reminders |
| POST | ServiceReminder/UpdateStatus | JWT Bearer | Update reminder status |
| GET | SMR/GetSMRData | JWT Bearer | SMR analytics |

### PSF (Post-Service Feedback)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | Psf/GetPsfList | JWT Bearer | PSF pending list |
| POST | Psf/SavePsf | JWT Bearer | Save PSF response |
| POST | PsfFeedBack/SaveFeedBack | JWT Bearer | Save PSF feedback |

### TVS Connect / External Integrations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | TVSConnect/* | Basic Auth | TVS Connect app endpoints |
| GET/POST | SuperDMS/* | SuperDMS JWT | SuperDMS integration |
| POST | SelfJC/* | SJP JWT | Customer self-service job card |

### Others

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | AMC/* | JWT Bearer | Annual Maintenance Contracts |
| GET/POST | PDIJobCard/* | JWT Bearer | Pre-Delivery Inspection |
| GET/POST | PickNDrop/* | JWT Bearer | Pick & drop service |
| GET/POST | PND/* | JWT Bearer | Pick & drop (alternate) |
| GET/POST | Dashboard/* | JWT Bearer | Dashboard analytics |
| POST | Prediction/* | JWT Bearer | CCE predictions |
| POST | Integrity/ValidateToken | JWT Bearer | Play Integrity check |
| POST | Transcribe/* | JWT Bearer | Voice transcription |
| GET/POST | Attendance/* | JWT Bearer | Staff attendance |
| GET/POST | Sales/* | JWT Bearer | Vehicle sales |
| GET/POST | Audit/* | Audit JWT | Audit operations |
| GET/POST | App5S/* | JWT Bearer | 5S workplace audit |

---

## Outbound (Who I Call)

| Target | Method | Endpoint/Purpose | Auth |
|--------|--------|------------------|------|
| Airtel IQ SMS | POST | https://iqsms.airtel.in/api/v1/msg/send-bulk-sms-tvs | Basic Auth Header |
| Infobip | POST | https://893r91.api.infobip.com/sms/2/text/advanced | API Key (Basic) |
| Notification Service | POST | NotificationServiceBaseUrl + NotificationSmsUrl (via APIM) | Bearer JWT + APIM Key |
| UMS Auth Service | POST | https://dev-api.tvsmotor.net/auth/v1/app/token/validate | Bearer JWT |
| Pickup & Drop Service | POST | https://dev-dmsdigiapi.tvsmotor.net/pickupdropservice/appointments | Bearer JWT + APIM Key |
| WIP Service (DIGI) | POST | WIP_Service_BaseURL + JobCard/ValidateImage (via APIM) | Bearer JWT + APIM Key |
| Job Card Service | HTTP | https://dev-api.tvsmotor.net/job-card-service/ | Bearer JWT |
| P360 EV GraphQL | POST | https://p360.tvsmotor.com/gapi (timeseries, stats, DTC) | Bearer JWT |
| Google Distance Matrix | GET | https://maps.googleapis.com/api/distancematrix/json | API Key |
| Waybeo Click-to-Call | POST | https://tvs.waybeo.com/api/outbound/generate-server-number | Bearer JWT |
| Harita Insurance | GET | https://policy.haritaib.com/api/api/GetPolicyData | Basic Auth |
| Azure Key Vault | SDK | Secret management | Azure Identity |
| Azure AD / APIM Token | POST | https://login.microsoftonline.com/{tenantId}/oauth2/v2.0/token | Client Credentials |
| Google Play Integrity | POST | https://playintegrity.googleapis.com/v1/{pkg}:decodeIntegrityToken | Service Account |
| SendGrid | SMTP | smtp.sendgrid.net:587 | API Key |
| SMTP Internal | SMTP | 10.121.2.222 | None |
| OnlineDMS SAP WCF | SOAP | advantagetvs.com/OnlineWCF/OnlineDmsSAPService.svc | N/A |
| Azure Databricks | POST | adb-329402708680292.12.azuredatabricks.net (voice transcription) | Bearer JWT |
| OTEL Gateway | POST | http://otel-gw-logs.tvsmotor.com/v1/traces, /v1/logs | None |
| GeoFencing API | HTTP | https://uat-api.tvsmotor.net/ | B2C Token |

---

## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Azure AD | Identity Provider | OAuth2 tokens for APIM services | Client Credentials |
| Azure Key Vault | Secret Store | Manage secrets (SuperDMS key, SendGrid, etc.) | Azure Identity SDK |
| Airtel IQ | SMS Gateway | Bulk + single SMS delivery | Basic Auth |
| Infobip | SMS + WhatsApp | Messaging fallback | API Key |
| SendGrid | Email | Booking confirmations, alerts | API Key |
| Google Play Integrity | Mobile Security | App integrity verification | Service Account |
| Waybeo | Telephony | Click-to-call functionality | JWT |
| Harita Insurance | Insurance Provider | Policy data lookup | Basic Auth |
| Azure Databricks | ML Platform | Voice-based transcription | Bearer JWT |

---

## Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| onlineDMS_Staging (DMSOnlineConnection) | MSSQL | Primary DMS data (online dealers) |
| DMS_SMR_Trans_UAT (SMRSqlConnection) | MSSQL | Service Maintenance Reminders |
| ADVTVS_UAT (DMSOfflineConnection) | MSSQL | Offline dealer data |
| EMS_APP (EMSPORTALCONN) | MSSQL | EMS Portal data |
| tvsmazdigisdbdev01-wip (WIPValidConnection) | Azure SQL | WIP validation data |
| FSCLAIM_Dev (FSCOTPConnection) | MSSQL | Free Service Claims + OTP |
| PARTS_QR_CODE (PartsConnection) | MSSQL | Parts QR code data |
| TVS_ONE_VIEW (SqlLoyaltyConnection) | MSSQL | Loyalty/One View data |
| Azure Blob Storage | Files | Play Integrity service account JSON |
| File System | Files | Centralized job card images |

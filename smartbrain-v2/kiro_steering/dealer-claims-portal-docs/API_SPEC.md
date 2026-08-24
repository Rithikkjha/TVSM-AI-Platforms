API Specification — Dealer Claims Portal

Purpose: Complete API specification document for external engineering partners and integration teams.
Version: 1.0 | Author: Samyucktha S | Status: CURRENT

_______________________________________________________________________________________


1. API Endpoint List

Dealer Dashboard APIs (Base: /api/):

#   Method  Endpoint                    Purpose
1   POST    /api/login                  Dealer/Admin authentication
2   POST    /api/SendOtp                Send OTP to dealer phone
3   POST    /api/VerifyOtp              Verify OTP and issue JWT
4   POST    /api/bookings               Get all bookings (paginated)
5   POST    /api/AllCount               Get booking counts by category
6   POST    /api/BookingUpdate          Bookings needing document upload
7   POST    /api/ReadyForPayment        Bookings ready for SAP processing
8   POST    /api/PaymentStatus          SAP settled bookings
9   POST    /api/ReturnCases            Rejected bookings for re-upload
10  POST    /api/InvoiceUpload          Upload invoice PDF
11  POST    /api/InsuranceUpload        Upload insurance PDF
12  POST    /api/AcknowledgmentUpload   Upload acknowledgment PDF
13  POST    /api/InvoiceDetail          Update invoice metadata
14  POST    /api/InsuranceDetail        Update insurance metadata
15  GET     /api/Export                 Export booking data

TRV APIs (Base: /api/TRV/):

#   Method  Endpoint                            Purpose
16  POST    /api/TRV/branches                   Get dealer branches from DMS
17  POST    /api/TRV/summary                    Get dealer TR summary/classification
18  POST    /api/TRV/norm-approval-form         Get models + variants for norm form
19  GET     /api/TRV/GetDealerTRNorms           Get dealer TRV norm config
20  POST    /api/TRV/SubmitNormsApproval        Submit norm approval request
21  POST    /api/TRV/GetTRVNorms                Get TRV norms status
22  POST    /api/TRV/SaveExistingTrvVehicles    Save vehicle + upload documents
23  POST    /api/TRV/GetExistingTrvVehicles     Get existing TRV vehicle list
24  GET     /api/TRV/get-frame-details          Validate frame number via DMS
25  GET     /api/TRV/download-file/{id}/{type}  Download uploaded document
26  POST    /api/TRV/upload-declaration-file    Upload declaration + submit claim
27  GET     /api/TRV/submit-email-request       AM email approval entry point
28  POST    /api/TRV/GetClaimSubmissions        Get claims (Area Accountant)

SAP APIs (Base: /api/sap/):

#   Method  Endpoint                        Purpose
29  GET     /api/sap/GetSAPDocumentNumber   Generate SAP documents
30  POST    /api/sap                        Receive SAP callback (doc number)
31  POST    /api/sap/claim-request          Area Accountant approve/reject

_______________________________________________________________________________________


2. Request Methods

POST: Data retrieval with filters, mutations (uploads, approvals, submissions)
GET: Simple lookups (frame details, downloads, SSO flow, SAP generation)
FormData POST: File uploads (invoice, insurance, TRV documents, declaration)

_______________________________________________________________________________________


3. Authentication Requirements

Endpoint Group              Auth Method             Header
/api/ (Dealer Dashboard)    JWT Bearer              Token: {jwt_token}
/api/TRV/                   JWT Bearer              Token: {jwt_token}
/api/sap/                   JWT Bearer OR API Key   Token: {jwt_token} OR ?authKey={key}

JWT Structure:
    Algorithm: HMAC SHA256
    Expiry: 120 minutes
    Issuer/Audience: domain.com
    Claims: Name = dealerId, Role = roleId

_______________________________________________________________________________________


4. Request Payloads

POST /api/login:
    { "username": "dealer@email.com", "password": "password123" }

POST /api/bookings (BookingFilter):
    {
      "dealerId": "12345",
      "startDate": "20260101",
      "endDate": "20260131",
      "dateType": "BookingDate",
      "mobileNumber": "9876543210",
      "customerName": "John Doe",
      "dealerType": "amd&ad",
      "pageNo": 1,
      "pageSize": 20
    }

POST /api/TRV/SubmitNormsApproval:
    [{ "dealerId": 12345, "branchId": 1, "dealerName": "ABC Motors",
       "dealerTrNormId": 42,
       "vehicleDetails": [{ "brand": "Jupiter 110", "variant": ["Disc"] }] }]

POST /api/TRV/SaveExistingTrvVehicles (FormData):
    NORM_ID: 123, DEALER_ID: 12345, BRANCH_ID: 1
    BRAND_NAME: Jupiter 110, VARIANT_NAME: Disc
    FRAME_NO: MD2A47AZ1RCA12345 (17 chars)
    INVOICE_NO: 98765, INVOICE_DATE: 2026-01-15
    ENGINE_NO: ABC123456789, NET_BILLING_AMOUNT: 85000.00
    SaveRequest: 0 (norm-based, mandatory docs)
    RcFile: [binary], InsuranceFile: [binary], HsrpFile: [binary]

POST /api/sap/claim-request:
    { "DealerId": 12345, "BranchId": 1, "NORM_ID": 101,
      "REQUEST_TYPE": 1, "FrameNo": "MD2A47AZ1RCA12345",
      "BrandName": "Jupiter 110", "FirstTrancheAmount": 12750.00 }

_______________________________________________________________________________________


5. Response Payloads

POST /api/login (Success - Role 10):
    { "status": 200, "message": "Success",
      "response": { "id": 42, "userId": "12345", "role": 10, "name": "TVS Dealer" },
      "token": null }

POST /api/VerifyOtp (Success):
    { "status": 200, "message": "Success",
      "response": { "userId": "12345", "role": 10 },
      "token": "eyJhbGciOiJIUzI1NiIs..." }

POST /api/AllCount:
    { "status": 200, "data": { "bookingUpdateCount": 15, "readyForPaymentCount": 8,
      "paymentStatusCount": 42, "returnCasesCount": 3, "totalCount": 68 } }

POST /api/TRV/SaveExistingTrvVehicles:
    { "status": 200, "message": "Vehicle details and files saved successfully.",
      "data": { "trvDetailId": 789 } }

_______________________________________________________________________________________


6. Error Responses

Standard format: { "status": 400, "message": "Error description" }

Status  Scenario                    Example Message
400     Missing token               "Token is missing."
400     Validation failure          "FRAME_NO is required"
400     Invalid input               "Invalid dealerId. Only numeric values are allowed."
401     Invalid/expired JWT         "Invalid or expired token."
401     Unauthorized access         "Access to dealer(12345) data is not allowed"
404     Not found                   "TRV vehicle record not found."
408     SAP timeout                 "Request timeout. Please try again."
409     Duplicate                   "Vehicle details already exists."
500     Server error                "An unexpected error occurred..."
503     Service unavailable         "Service unavailable. Please try again later."

_______________________________________________________________________________________


7. Validation Rules

BookingFilter Validation:

Field               Type        Required            Rules
dealerId            string      No (from token)     Numeric only (^\d+$)
startDate/endDate   string      Paired              yyyyMMdd, start <= end
dateType            string      With dates          Enum: BookingDate, InvoiceDate, SettlementDate
mobileNumber        string      No                  Exactly 10 digits
customerEmail       string      No                  Valid email (MailAddress)
customerName        string      No                  ^[A-Za-z0-9 .'-]+$
dealerType          string      No                  Enum: amdId, adId, amd&ad, spdId
pageSize            int         No                  1-200 (default 50)

TRV Vehicle Validation:

Field                           Required            Rules
DEALER_ID                       Yes                 > 0
BRANCH_ID                       Yes                 > 0
FRAME_NO                        Yes                 Non-empty, 17 characters
INVOICE_NO                      Yes                 > 0
REGISTRATION_NO                 Yes                 Non-empty
RcFile/InsuranceFile/HsrpFile   If SaveRequest=0    All 3 mandatory; allowed types; <= 100MB
SaveRequest                     Yes                 0 (TrvNormSave) or 1 (ExistingSave)

_______________________________________________________________________________________


8. Rate Limits

No explicit application-level rate limiting implemented. Protection via:
    IIS request queue limits (server-level)
    Azure SQL connection limits
    JWT token expiry (120 min) limits session duration
    Service Bus MaxConcurrentSessions=1 limits event processing

_______________________________________________________________________________________


9. External API Dependencies

External API                Called By                   Auth                Timeout     Purpose
DMS LoadBranch2             TRVController               None                Default     Branch listing
DMS TrvFrameNumberDetails   TRVController               None                Default     Frame validation
DMS load-variants-by-series TRVServices                 None                Default     Variant lookup
DMS GetEmployeeActiveStatus DealerDashboardController   SOAP creds          Default     OTP eligibility
SAP Token endpoint          SAPController               Basic Auth          Default     OAuth2 token
SAP Claim API               SAPController               Bearer (OAuth2)     30s         Financial posting
Databricks OCR              TRVController               Bearer token        60s         Document validation
Airtel SMS                  DealerDashboardController   Payload DLT         Default     OTP delivery

_______________________________________________________________________________________


10. Sample Requests/Responses

Complete Login Flow:

    Step 1: POST /api/login
    Body: {"username":"dealer@email.com","password":"P@ss123"}
    Response: {"status":200,"response":{"id":42,"userId":"12345","role":10},"token":null}

    Step 2: POST /api/SendOtp
    Body: {"id":42,"dealerId":"12345","role":10,"phoneNumber":"9876543210"}
    Response: {"status":200,"message":"Success","response":{"statusCode":200}}

    Step 3: POST /api/VerifyOtp
    Body: {"id":42,"dealerId":"12345","role":10,"otp":1234}
    Response: {"status":200,"token":"eyJhbGciOiJIUzI1Ni..."}

    Step 4: All subsequent calls
    Headers: Token: eyJhbGciOiJIUzI1Ni...

TRV Vehicle Save:

    POST /api/TRV/SaveExistingTrvVehicles
    Headers: Token: eyJhbG..., Content-Type: multipart/form-data
    Body: [FormData with fields + RC/Insurance/HSRP files]

    Success: {"status":200,"message":"Vehicle details and files saved successfully.","data":{"trvDetailId":789}}
    Duplicate: {"status":409,"message":"Vehicle details already exists."}
    Validation: {"status":400,"message":"FRAME_NO is required"}

File Download:

    GET /api/TRV/download-file/789/rc
    Headers: Token: eyJhbG...

    Success: Binary file stream (application/pdf)
    Content-Disposition: attachment; filename="12345_1_789_RC_20260115.pdf"

    Not Found: {"status":404,"message":"RC file not uploaded for this vehicle."}

Note: For interactive API testing, access Swagger UI at /swagger in the Development environment.

_______________________________________________________________________________________


_______________________________________________________________________________________


Service Identity

Field               Value
Service Name        dealer-claims-portal
Repo                BS2.0Backend_Integration + dealer-dashboard
Team                Dealer Portal Team
Deployment          IIS on Azure Virtual Machine
Base URL (prod)     https://iqubeprod.tvsmotor.com/DealerDashboardApi/api/
Base URL (UAT)      https://uat-bookingapi.tvsmotor.net/BS/api/

Ownership and Contacts

Role                Person / Team                   Contact
Support Email       Dealer Dashboard Support        dealersupport@tvsmotor.com
Ticket System       BoldDesk                        tvsmotor.bolddesk.com/support
Confluence Space    D2W                             tvsmotorcompany.atlassian.net/wiki/spaces/D2W

_______________________________________________________________________________________


Inbound — API Endpoints and Who Calls Them

Method  Endpoint                            Auth            Description                             Called By
POST    /api/login                          None            Dealer authentication                   Dealer Portal (React SPA)
POST    /api/SendOtp                        None            Send OTP to dealer                      Dealer Portal (React SPA)
POST    /api/VerifyOtp                      None            Verify OTP, issue JWT                   Dealer Portal (React SPA)
POST    /api/bookings                       JWT Token       Get bookings (paginated)                Dealer Portal (React SPA)
POST    /api/AllCount                       JWT Token       Get tab counts                          Dealer Portal (React SPA)
POST    /api/BookingUpdate                  JWT Token       Bookings needing docs                   Dealer Portal (React SPA)
POST    /api/ReadyForPayment                JWT Token       Ready for SAP                           Dealer Portal (React SPA)
POST    /api/PaymentStatus                  JWT Token       Settled bookings                        Dealer Portal (React SPA)
POST    /api/ReturnCases                    JWT Token       Rejected bookings                       Dealer Portal (React SPA)
POST    /api/InvoiceUpload                  JWT Token       Upload invoice PDF                      Dealer Portal (React SPA)
POST    /api/InsuranceUpload                JWT Token       Upload insurance PDF                    Dealer Portal (React SPA)
POST    /api/InvoiceDetail                  JWT Token       Update invoice metadata                 Dealer Portal (React SPA)
POST    /api/InsuranceDetail                JWT Token       Update insurance metadata               Dealer Portal (React SPA)
POST    /api/TRV/branches                   JWT Token       Get dealer branches                     Dealer Portal, AA Portal
POST    /api/TRV/summary                    JWT Token       Dealer classification                   Dealer Portal
POST    /api/TRV/SubmitNormsApproval        JWT Token       Submit norm request                     Dealer Portal
POST    /api/TRV/SaveExistingTrvVehicles    JWT Token       Save vehicle + docs                     Dealer Portal
POST    /api/TRV/upload-declaration-file    JWT Token       Upload declaration                      Dealer Portal
GET     /api/TRV/submit-email-request       Azure AD        AM email approve/reject                 Area Manager (Email link)
POST    /api/TRV/GetClaimSubmissions        JWT Token       Get TRV claims                          AA Portal
POST    /api/sap/claim-request              JWT Token       Approve/reject TRV claim                AA Portal
GET     /api/sap/GetSAPDocumentNumber       API Key         Generate SAP documents                  Scheduled/Internal
POST    /api/sap                            None            SAP callback (doc number)               SAP CPI (External)

_______________________________________________________________________________________


Outbound — Who This Service Calls

Target                      Method      Endpoint/Topic                              Purpose
DMS REST API                GET         {DMS_BASE}/OnlineMasterAPI/Master.asmx/LoadBranch2   Branch lookup
DMS REST API                GET         {DMS_BASE}/OnlineSalesAPI/Sales/TrvFrameNumberDetails Frame validation
DMS REST API                POST        {DMS_BASE}/OnlineSalesAPI/load-variants-by-series    Variant loading
DMS SOAP Web Service        POST        GetEmployeeActiveStatus                     Employee status before OTP
SAP CPI                     POST        {SAP_TOKEN_URL} (client_credentials)        OAuth2 token
SAP CPI                     POST        {SAP_API_URL}                               Financial document posting
Azure Databricks            POST        {DS_URL}/invocations                        OCR document compliance
Airtel SMS Gateway          POST        digimate.airtel.in/BulkPush/InstantJsonPush OTP delivery
SendGrid / SMTP             SMTP        smtp.sendgrid.net                           Email notifications

_______________________________________________________________________________________


Events and Messaging

Topics This Service Subscribes To:

Topic/Queue                         Events                                              Action
uat.booking (Service Bus Topic)     BOOKING_CREATED, BOOKING_CANCELLED,                 Upsert BookingClaim + PaymentDetail + VehicleDetail
                                    FULL_PAYMENT_UPDATED, INVOICED,
                                    INVOICE_CANCEL, DEALER_UPDATED
export_queue (Service Bus Queue)    Export request (logId)                              Generate Excel file and save to IIS

This service does not publish to any topics.

_______________________________________________________________________________________


Database and Storage

Store                       Type            Purpose
CustomerBay DB              Azure SQL       Primary booking/claim/TRV data (BookingClaim, TRVNorms, ExistingTRVDetail, Users, SAP)
TravelNew DB                Azure SQL       AM/TM email lookups (sp_GetDealerAMTMMails)
IIS Local Disk (TVS-BSIV)  File System     Invoice, Insurance, Acknowledgement documents
IIS Local Disk (TVS-TRV)   File System     RC, Insurance, HSRP, Declaration documents

_______________________________________________________________________________________

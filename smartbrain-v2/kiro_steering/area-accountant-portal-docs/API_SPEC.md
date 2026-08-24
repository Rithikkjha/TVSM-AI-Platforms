# API Specification Document — TVS CustomerBay

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | customerbay (Area Accountant Portal) |
| Repo | TVS_REPOS_NEW/customerbay |
| Team | TVS Digital Engineering |
| Deployment | Azure DevOps CI/CD → AWS S3 / TVS Production Infrastructure |
| Base URL (prod) | https://iqubeprod.tvsmotor.com/bsvi |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Project Owner | TVS Digital Engineering Team | Gujjar Neha Gagana|
| Frontend Team | Connected Commerce Frontend | Samyucktha |
| Backend Team | Connected Commerce Backend | Samyucktha |
| DevOps | TVS DevOps | Azure DevOps Pipelines |
| IT Support | TVS IT Team | Contact for access issues |

---

## Base URLs

| Environment | Base URL |
|-------------|----------|
| Production | `https://iqubeprod.tvsmotor.com/bsvi` |
| UAT | `https://uat-bookingapi.tvsmotor.net/bsvi` |
| Local | `http://localhost:5201/api/` |

> **Note:** TRV and SAP endpoints use the base URL without `/areaAccountant` segment:
> `https://iqubeprod.tvsmotor.com/bsvi`

---

## Authentication

All API requests (except `login` and SSO endpoints) require a JWT token in the request header:

```
Token: <JWT_TOKEN>
```

The token is obtained either through:
1. Username/password login (`POST /login`)
2. SSO flow (`GET /auth/sso/token`)

---

## API Endpoints

### 1. Authentication

#### POST /login

Authenticate user with username and password.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "********"
}
```

**Headers:**
```
Content-Type: application/json
Token: (empty string)
```

**Response (Success):**
```json
{
  "message": "Success",
  "response": {
    "userId": "user@example.com",
    "role": 3,
    "name": "Area Accountant",
    "id": "12345"
  },
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (Failure):**
```json
{
  "message": "Invalid credentials"
}
```

**Validation Rules:**
- Only role 3 (Area Accountant) is allowed to login via username/password
- Other roles receive "Invalid" state

---

#### GET /auth/sso/login

Initiate Microsoft SSO authentication flow.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| returnUrl | string | Yes | URL to redirect after authentication |

**Response:** HTTP 302 redirect to Microsoft Identity Platform

---

#### GET /auth/sso/ssologin

Complete SSO authentication and retrieve user data.

**Headers:**
```
Credentials: include (cookies)
```

**Response (Success):**
```json
{
  "email": "user@tvsmotor.com",
  "role": 3,
  "id": "12345"
}
```

**Response (Failure):**
```json
{
  "message": "You are not authorised to access this portal. Please contact IT Team."
}
```

---

#### GET /auth/sso/token

Retrieve JWT token after successful SSO authentication.

**Headers:**
```
Credentials: include (cookies)
```

**Response (Success):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "id": "12345"
}
```

---

### 2. Booking Claims (Area Accountant)

#### GET /bookings

Fetch approved booking claims with pagination.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dateType | string | No | `BookingDate`, `invoiceDate`, or `SettlementDate` |
| startDate | string | No | Start date (YYYYMMDD format) |
| endDate | string | No | End date (YYYYMMDD format) |
| dealerType | string | No | `amd&ad`, `amdId`, `adId`, `spdId` |
| dealerId | string | No | Dealer code |
| mobileNumber | string | No | Customer mobile number |
| customerEmail | string | No | Customer email |
| customerName | string | No | Customer name |
| orderId | string | No | CCAvenue tracking ID |
| ccAvenueNumber | string | No | CCAvenue order number |
| pageNo | number | Yes | Page number (1-based) |
| pageSize | number | Yes | Items per page (default: 20) |

**Response:**
```json
{
  "data": [
    {
      "dealerCode": "12345",
      "dealerType": "AMD",
      "customerName": "John Doe",
      "customerEmail": "john@example.com",
      "customerMobile": "9876543210",
      "model": "Apache RTR 160",
      "variant": "4V",
      "color": "Racing Red",
      "vehicleType": "ICE",
      "invoiceNumber": "INV001",
      "invoiceFileName": "invoice_001.pdf",
      "insuranceNumber": "POL001",
      "insuranceFileName": "insurance_001.pdf",
      "partialPaymentAmount": 5000,
      "fullPaymentAmount": 150000,
      "partialCCARefNumber": "CCA123456",
      "fullPaymentCcarefTransactionNumber": "CCA789012",
      "partialPayoutId": "PO001",
      "fullPaymentPayoutId": "PO002",
      "bookingDate": "2024-01-15T10:30:00",
      "invoiceUploadDate": "2024-01-20T14:00:00",
      "documentStatus": 0,
      "uuid": "abc-def-123",
      "amdMapping": "AMD001",
      "DisplayFlag": 1,
      "fullPaymentDocMessage": "Posted",
      "fullPaymentDocNo": "DOC001",
      "fullPaymentDocDate": "2024-01-25"
    }
  ]
}
```

---

#### GET /TransactionReport

Fetch claims pending approval.

**Query Parameters:** Same as `/bookings`

**Response:** Same structure as `/bookings`

---

#### GET /rejected

Fetch rejected claims.

**Query Parameters:** Same as `/bookings`

**Response:** Same structure as `/bookings`

---

#### GET /settledClaims

Fetch settled (SAP-processed) claims.

**Query Parameters:** Same as `/bookings`

**Response:** Same structure as `/bookings`

---

#### GET /allBookings

Fetch all claims regardless of status.

**Query Parameters:** Same as `/bookings`

**Response:** Same structure as `/bookings`

---

#### GET /TransactionReportCount

Get counts for all claim categories.

**Query Parameters:** Same as `/bookings`

**Response:**
```json
{
  "count": {
    "totalCount": 150,
    "transactionCount": 45,
    "rejectedCount": 12,
    "allCount": 200,
    "settledCount": 93
  }
}
```

---

#### POST /Approved

Approve one or more booking claims.

**Request:**
```json
[
  {
    "DealerId": "12345",
    "BookingId": 1,
    "Uuid": "abc-def-123",
    "ComeFrom": "ICE",
    "loginId": "user123",
    "UserEmail": "user@tvsmotor.com"
  }
]
```

**Response (Success):**
```json
{
  "status": 200,
  "message": "Booking approved successfully"
}
```

**Response (Failure):**
```json
{
  "status": 400,
  "message": "Failed to Approve Booking"
}
```

---

#### POST /Reject

Reject one or more booking claims.

**Request:**
```json
[
  {
    "DealerId": "12345",
    "BookingId": 1,
    "Uuid": "abc-def-123",
    "ComeFrom": "ICE",
    "Reason": "Invalid invoice document",
    "ToModify": "invoice",
    "loginId": "user123",
    "UserEmail": "user@tvsmotor.com"
  }
]
```

**Response (Success):**
```json
{
  "status": 200,
  "message": "Booking rejected successfully"
}
```

---

### 3. TRV Claims

#### POST /TRV/branches

Fetch dealer branches for TRV module.

**Request:**
```json
{
  "dealerId": "12345",
  "loginId": "user123"
}
```

**Response (Success):**
```json
{
  "status": 200,
  "data": {
    "dealerName": "TVS Dealer ABC",
    "branches": [
      {
        "branchId": 1,
        "branchName": "Main Branch"
      },
      {
        "branchId": 2,
        "branchName": "Sub Branch"
      }
    ]
  }
}
```

---

#### POST /TRV/GetClaimSubmissions

Fetch TRV claim submissions.

**Request:**
```json
{
  "fromDate": "2024-01-01T00:00:00.000Z",
  "toDate": "2024-02-01T00:00:00.000Z",
  "action_Type": 4,
  "dealerId": "12345",
  "branchId": "1",
  "loginId": "user123"
}
```

**Notes:**
- `action_Type`: 4 = fetch all claims (one view)
- `dealerId` and `branchId` are optional

**Response (Success):**
```json
{
  "claims": [
    {
      "norM_ID": 1001,
      "dealerId": 12345,
      "branchId": 1,
      "dealershipName": "TVS Dealer ABC",
      "branchName": "Main Branch",
      "brandName": "Apache",
      "variant": "RTR 160 4V",
      "frameNo": "MD2A1234567",
      "invoiceNo": "INV001",
      "invoiceDate": "2024-01-15T00:00:00",
      "registrationNo": "TN01AB1234",
      "netBillingPrice": 125000,
      "percentageSupport": 5,
      "reimbursement": 6250,
      "firstTrancheAmount": 3000,
      "remark": "",
      "claim_Status": 1,
      "capitalization_Status": 0,
      "createdOn": "2024-01-16T10:00:00",
      "approvedDate": null,
      "rejectedDate": null
    }
  ],
  "message": "Claims fetched successfully"
}
```

**Response (No Data):**
```json
{
  "claims": null,
  "message": "No claims found for the given criteria"
}
```

---

#### POST /TRV/GetExistingTrvVehicles

Fetch vehicle details for a TRV claim.

**Request:**
```json
{
  "dealerId": "12345",
  "branchId": "1",
  "brand_Name": "Apache",
  "variant_Name": "RTR 160 4V",
  "frame_No": "MD2A1234567",
  "loginId": "user123"
}
```

**Response (Success):**
```json
{
  "response": {
    "statusCode": 200,
    "data": [
      {
        "trvDetailId": 5001,
        "brandName": "Apache",
        "variantName": "RTR 160 4V",
        "frameNo": "MD2A1234567",
        "customerName": "John Doe",
        "customerPhoneNo": "9876543210",
        "invoiceNo": "INV001",
        "invoiceDate": "2024-01-15T00:00:00",
        "registrationNo": "TN01AB1234",
        "registrationDate": "2024-01-20T00:00:00",
        "hsrpDate": "2024-01-25T00:00:00",
        "isRCUploaded": true,
        "rcName": "rc_document.pdf",
        "isInsuranceUploaded": true,
        "insuranceName": "insurance_doc.pdf",
        "isHSRPUploaded": false,
        "hsrpName": "",
        "isCompliant": true,
        "compliantRemark": null
      }
    ]
  }
}
```

---

#### GET /TRV/download-file/{vehicleId}/{documentType}

Download a vehicle document (RC, Insurance, or HSRP).

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vehicleId | number | TRV detail ID |
| documentType | string | `rc`, `insurance`, or `hsrp` |

**Headers:**
```
Token: <JWT_TOKEN>
```

**Response:**
- Content-Type: application/pdf (or appropriate MIME type)
- Content-Disposition: attachment; filename="document_name.pdf"
- Body: Binary file content

**Error Responses:**
| Status | Description |
|--------|-------------|
| 404 | File not found on server |
| 401 | Unauthorized access |
| 500 | Server error |

---

### 4. SAP Integration

#### POST /sap/claim-request

Submit claim approval or rejection to SAP system.

**Request:**
```json
{
  "REQUEST_TYPE": 1,
  "NORM_ID": 1001,
  "dealerId": 12345,
  "branchId": 1,
  "dealershipName": "TVS Dealer ABC",
  "branchName": "Main Branch",
  "brandName": "Apache",
  "variant": "RTR 160 4V",
  "frameNo": "MD2A1234567",
  "invoiceNo": 12345,
  "invoiceDate": "2024-01-15T00:00:00.000Z",
  "registrationNo": "TN01AB1234",
  "percentageSupport": 5,
  "reimbursement": 6250,
  "remark": "",
  "firstTrancheAmount": 3000,
  "netBillingPrice": 125000,
  "status": 1,
  "createdOn": "2024-01-16T10:00:00.000Z",
  "approvedDate": "2024-02-01T10:00:00.000Z",
  "rejectedDate": null,
  "igst": "",
  "loginId": "user123"
}
```

**Field Notes:**
- `REQUEST_TYPE`: 1 = Approve, 0 = Reject
- `NORM_ID`: Unique claim identifier from backend
- `status`: Original claim_Status value
- `remark`: Required for rejection, optional for approval

**Response (Success):**
```json
{
  "message": "Claim approved successfully"
}
```

**Response (Failure):**
```json
{
  "message": "Failed to process claim: [error details]"
}
```

---

### 5. Export

#### POST /downloadDetails

Request a file export of claim data.

**Request:**
```json
{
  "startDate": "20240101",
  "endDate": "20240201",
  "DealerCode": "12345",
  "exportType": "ClaimsForApproval",
  "dateType": "bookingDate",
  "loginId": "user123"
}
```

**Export Types:**
| Value | Description |
|-------|-------------|
| `ClaimsForApproval` | Tab 1 - Pending claims |
| `ApprovedClaims` | Tab 2 - Approved claims |
| `RejectedClaims` | Tab 3 - Rejected claims |
| `SettledClaims` | Tab 4 - Settled claims |
| `AllRecords` | Tab 5 - All records |

**Response:**
```json
{
  "status": 200,
  "message": "Export request queued successfully"
}
```

---

#### GET /downloadDetails

Fetch list of export file requests.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| loginId | string | Yes | User's login ID |

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "fileName": "export_20240201.csv",
      "status": "completed",
      "createdDate": "2024-02-01T10:00:00",
      "downloadUrl": "https://..."
    }
  ]
}
```

---

### 6. Supplementary Endpoints

#### GET /SapName

Fetch SAP details for a booking.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| bookingId | string | Yes | Booking UUID |

**Response:**
```json
{
  "response": {
    "sapName": "SAP_ENTRY_001",
    "sapDate": "2024-01-25",
    "sapStatus": "Posted"
  }
}
```

---

#### GET /Tdr

Fetch TDR (Transaction Detail Report) data.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refno | string | Yes | Tracking/reference number |

**Response:**
```json
{
  "response": {
    "trackingId": "CCA123456",
    "transactionDate": "2024-01-15",
    "amount": 5000,
    "status": "Success",
    "bankRefNo": "BANK001"
  }
}
```

---

## Error Responses (Common)

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success (check `status` field in body for business errors) |
| 401 | Unauthorized — invalid or expired token |
| 403 | Forbidden — insufficient role permissions |
| 404 | Resource not found |
| 500 | Internal server error |

**Standard Error Body:**
```json
{
  "status": 400,
  "message": "Error description"
}
```

---

## Rate Limits

No explicit rate limiting is implemented on the frontend. The backend may enforce rate limits — consult backend documentation for specifics.

---

## My API Endpoints — Inbound (Who Calls Me)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | /login | None | Authenticate Area Accountant | CustomerBay Portal (browser) |
| GET | /auth/sso/login | None | Initiate Microsoft SSO | CustomerBay Portal (browser) |
| GET | /auth/sso/ssologin | Cookie | Complete SSO authentication | CustomerBay Portal (browser) |
| GET | /auth/sso/token | Cookie | Retrieve JWT token | CustomerBay Portal (browser) |
| GET | /bookings | Bearer JWT | Fetch approved claims | CustomerBay Portal (Area Accountant) |
| GET | /TransactionReport | Bearer JWT | Fetch claims pending approval | CustomerBay Portal (Area Accountant) |
| GET | /rejected | Bearer JWT | Fetch rejected claims | CustomerBay Portal (Area Accountant) |
| GET | /settledClaims | Bearer JWT | Fetch settled claims | CustomerBay Portal (Area Accountant) |
| GET | /allBookings | Bearer JWT | Fetch all claims | CustomerBay Portal (Area Accountant) |
| GET | /TransactionReportCount | Bearer JWT | Get claim category counts | CustomerBay Portal (Area Accountant) |
| POST | /Approved | Bearer JWT | Approve booking claims | CustomerBay Portal (Area Accountant) |
| POST | /Reject | Bearer JWT | Reject booking claims | CustomerBay Portal (Area Accountant) |
| POST | /TRV/branches | Bearer JWT | Get dealer branches | CustomerBay Portal (Area Accountant, AMTM) |
| POST | /TRV/GetClaimSubmissions | Bearer JWT | Fetch TRV claims | CustomerBay Portal (Area Accountant, AMTM) |
| POST | /TRV/GetExistingTrvVehicles | Bearer JWT | Get vehicle details | CustomerBay Portal (Area Accountant, AMTM) |
| GET | /TRV/download-file/{id}/{type} | Bearer JWT | Download vehicle document | CustomerBay Portal (Area Accountant, AMTM) |
| POST | /sap/claim-request | Bearer JWT | Submit claim to SAP | CustomerBay Portal (Area Accountant) |
| POST | /downloadDetails | Bearer JWT | Request file export | CustomerBay Portal (Area Accountant) |
| GET | /downloadDetails | Bearer JWT | Get export file list | CustomerBay Portal (Area Accountant) |
| GET | /SapName | Bearer JWT | Fetch SAP details | CustomerBay Portal (Area Accountant) |
| GET | /Tdr | Bearer JWT | Fetch TDR data | CustomerBay Portal (Area Accountant) |

---

## Outbound (Who I Call)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| .NET Backend API (iqubeprod.tvsmotor.com/BS) | REST (GET/POST) | /api/areaAccountant/* | All booking claims CRUD, approval, export |
| .NET Backend API (iqubeprod.tvsmotor.com/BS) | REST (POST) | /api/TRV/* | TRV claims, vehicle details, document download |
| .NET Backend API (iqubeprod.tvsmotor.com/BS) | REST (POST) | /api/sap/claim-request | Claim approval/rejection to SAP system |
| .NET Backend API (iqubeprod.tvsmotor.com/BS) | REST (GET) | /auth/sso/* | Microsoft SSO authentication and token management |
| Microsoft Identity Platform | OAuth 2.0 / SAML | Redirect-based | Corporate SSO authentication |
| TVS Document Server | HTTPS (GET) | https://iqubeprod.tvsmotor.com/TVSBSVIApp/ | Invoice and insurance document viewing |
| AWS S3 | HTTPS | s3://krust.krscode.com | Deployment target (static assets) |

---

## Events & Messaging

This service (frontend SPA) does not directly publish or subscribe to message queues or event topics. All event-driven communication is handled by the .NET backend API.

### Known Backend Event Flows (via SAP Integration)
| Flow | Trigger | Action |
|------|---------|--------|
| Claim Approval | POST /sap/claim-request (REQUEST_TYPE=1) | Backend posts approval to SAP for capitalization |
| Claim Rejection | POST /sap/claim-request (REQUEST_TYPE=0) | Backend posts rejection to SAP |
| Export Generation | POST /downloadDetails | Backend queues export job and generates file asynchronously |

---

## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Microsoft Identity Platform | Identity Provider | Corporate SSO authentication (OAuth 2.0 / SAML) | Redirect + session cookie |
| SAP System | ERP | Claim processing, capitalization, approval/rejection | Via backend (JWT pass-through) |
| CCAvenue | Payment Gateway | Payment tracking reference IDs (read-only) | N/A (reference data only) |
| TVS Document Server (TVSBSVIApp) | File Storage | Invoice and insurance document viewing/download | Authenticated session |
| Azure DevOps | CI/CD Platform | Build, test, and deployment automation | Pipeline service connection |
| AWS S3 | Cloud Storage | Static asset deployment target | AWS CLI credentials |

---

## Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| localStorage (Browser) | Client-side | JWT token, user credentials, session data |
| sessionStorage (Browser) | Client-side | SSO login flag (`ssoLogin`) |
| Backend Database (SQL Server) | Relational (via API) | Booking claims, TRV claims, user data, document metadata |
| TVS Document Server | File Storage | Invoice PDFs, insurance documents, RC/HSRP files |
| AWS S3 (krust.krscode.com) | Object Storage | Deployed static frontend assets |

# API Specification - DMS Domestic Web (.in)

## Overview
This document describes the API endpoints for the MicroDMS (Dealer Management System) Web Application. The system is built on ASP.NET WebForms with ASMX WebServices and follows a three-tier architecture (UI → Business Layer → Data Layer).

**Base URL**: `https://{domain}/WebServices/`  
**Protocol**: HTTPS  
**Format**: XML/JSON (SOAP-based Web Services)  
**Authentication**: Session-based (Forms Authentication with ASP.NET Session)

---

## Authentication

### Overview
The DMS system uses ASP.NET Forms Authentication with session-based authorization.

### Login Flow
1. User submits credentials via `Login.aspx`
2. System validates credentials against database
3. On success, creates ASP.NET authentication ticket
4. Session variables are populated:
   - `DEALERID` - Dealer identifier
   - `BranchID` - Branch identifier
   - `CountryCode` - Country code (IN/ID)
   - `AllotmentLocationId` - Storage location
   - `OrderType` - Order type for current context

### Session Requirements
All API endpoints require `EnableSession = true` and valid authentication cookie.

**Request Headers:**
```
Cookie: ASP.NET_SessionId={session-id}; .ASPXAUTH={auth-ticket}
```

### Authorization
Role-based access control enforced at page/service level based on user roles stored in session.

---

## API Categories

### 1. Customer Management APIs
### 2. Vehicle Management APIs
### 3. Parts & Spares Management APIs
### 4. Service & Job Card APIs
### 5. Sales & Booking APIs
### 6. Accounts & Finance APIs
### 7. Inventory APIs
### 8. Warranty & Claims APIs

---

## 1. Customer Management APIs

### 1.1 Search Customer

**Endpoint**: `CustomerSearch.asmx/GetCustomerName`  
**Method**: POST  
**Authentication**: Required (Session-based)

**Description**: Search for customers by name with autocomplete support.

**Request Body** (JSON):
```json
{
  "context": {
    "Text": "John",
    "NumberOfItems": 0
  }
}
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| context.Text | string | Yes | Customer name search text |
| context.NumberOfItems | integer | No | Pagination offset (default: 0) |

**Response** (JSON):
```json
{
  "d": {
    "EndOfItems": false,
    "Message": "Items <b>1</b>-<b>8</b> out of <b>25</b>",
    "Items": [
      {
        "Text": "John Doe - 9876543210",
        "Value": "12345"
      },
      {
        "Text": "John Smith - 9123456789",
        "Value": "12346"
      }
    ]
  }
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| EndOfItems | boolean | True if no more items to load |
| Message | string | Status message with count |
| Items | array | Customer records |
| Items[].Text | string | Display text (Name - Phone) |
| Items[].Value | string | Customer ID |

**Error Responses**:
- **401 Unauthorized**: Session expired or invalid
- **500 Internal Server Error**: Database or business logic error

**Validation Rules**:
- Text: Minimum 2 characters for search
- Results limited to dealer's customers only

**Rate Limiting**: Not explicitly enforced

**Sample cURL**:
```bash
curl -X POST https://domain/WebServices/CustomerSearch.asmx/GetCustomerName \
  -H "Content-Type: application/json" \
  -H "Cookie: ASP.NET_SessionId=xxx; .ASPXAUTH=yyy" \
  -d '{"context":{"Text":"John","NumberOfItems":0}}'
```

---

### 1.2 Create Customer

**Endpoint**: `Masters/CustomerMaster.aspx` (Page-based)  
**Method**: POST (Form submission)  
**Authentication**: Required

**Description**: Create new customer record with contact and address details.

**Request Body** (Form Data):
```
txtCustomerName=John Doe
txtMobileNo=9876543210
txtEmail=john@example.com
txtAddress=123 Main Street
ddlCustomerType=1
ddlArea=5
txtPincode=600001
... (additional fields)
```

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| txtCustomerName | string | Yes | Customer full name |
| txtMobileNo | string | Yes | Mobile number (10 digits) |
| txtEmail | string | No | Email address |
| txtAddress | string | Yes | Communication address |
| ddlCustomerType | integer | Yes | Customer type ID |
| ddlArea | integer | Yes | Area ID |
| txtPincode | string | Yes | Postal code (6 digits) |
| txtPANNo | string | No | PAN card number |
| txtAadharNo | string | No | Aadhar card number |
| txtGSTIN | string | No | GSTIN for business customers |

**Response**: Page redirect or inline message

**Validation Rules**:
- Mobile: 10-digit numeric, unique per dealer
- Email: Valid email format
- PAN: 10 characters alphanumeric (uppercase)
- Aadhar: 12 digits
- GSTIN: 15 characters alphanumeric

---

## 2. Vehicle Management APIs

### 2.1 Frame Number Check

**Endpoint**: `WebServices/FrameNoCheck.asmx/getValidFrameNo`  
**Method**: POST  
**Authentication**: Required

**Description**: Validate frame number against SAP/Oracle system.

**Request Body** (JSON):
```json
{
  "FrameNo": "MBLHA10FXHJXXXXXX"
}
```

**Response** (JSON):
```json
{
  "d": "Valid Frame No"
}
```

**Error Responses**:
```json
{
  "d": "Invalid Frame No : MBLHA10FXHJXXXXXX"
}
```

**Validation Rules**:
- Frame number: 17 characters alphanumeric
- Must exist in manufacturer's database
- Must not be already invoiced

---

### 2.2 Frame Number Availability

**Endpoint**: `WebServices/FramenoAvailability.asmx`  
**Method**: POST  
**Authentication**: Required

**Description**: Check frame number availability in dealer stock.

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| FrameNo | string | Yes | 17-char frame number |
| DealerID | integer | Yes | Current dealer ID |
| LocationID | integer | No | Storage location filter |

**Response**:
```json
{
  "IsAvailable": true,
  "Status": "In Stock",
  "Model": "Apache RTR 160",
  "Color": "Red",
  "ReceivedDate": "2024-01-15"
}
```

---

## 3. Parts & Spares Management APIs

### 3.1 Search Parts (With Stock)

**Endpoint**: `WebServices/PartSearch.asmx/GetPartDetailsWithLocation`  
**Method**: POST  
**Authentication**: Required

**Description**: Search spare parts with stock availability.

**Request Body**:
```json
{
  "context": {
    "Text": "BRAKE",
    "NumberOfItems": 0
  }
}
```

**Response**:
```json
{
  "d": {
    "EndOfItems": false,
    "Message": "Items <b>1</b>-<b>10</b> out of <b>45</b>",
    "Items": [
      {
        "Text": "BRAKE SHOE ASSY - FRONT",
        "Value": "2334567"
      },
      {
        "Text": "BRAKE CABLE - REAR",
        "Value": "2334568"
      }
    ]
  }
}
```

**Request Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| context.Text | string | Part number or description |
| context.NumberOfItems | integer | Pagination offset |

**Session Dependencies**:
- DEALERID
- AllotmentLocationId
- BranchID
- CountryCode

---

### 3.2 Search Parts (For Purchase Order)

**Endpoint**: `WebServices/PartSearch.asmx/GetPOPartDetails`  
**Method**: POST  
**Authentication**: Required

**Description**: Search parts available from manufacturer for PO creation.

**Request/Response**: Similar to 3.1 but filters by manufacturer availability

**Session Dependencies**:
- OrderType (TVS/APS/Others)

---

## 4. Service & Job Card APIs

### 4.1 Search Job Card

**Endpoint**: `WebServices/JobCarddetails.asmx`  
**Method**: POST  
**Authentication**: Required

**Description**: Retrieve job card details by job card number or frame number.

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| JobCardNo | string | No | Job card number |
| FrameNo | string | No | Vehicle frame number |
| DealerID | integer | Yes | Current dealer ID |

**Response**:
```json
{
  "JobCardID": 45678,
  "JobCardNo": "JC-2024-001234",
  "CustomerName": "John Doe",
  "MobileNo": "9876543210",
  "FrameNo": "MBLHA10FXHJXXXXXX",
  "Model": "Apache RTR 160",
  "Complaints": "Engine noise, brake issue",
  "Status": "In Progress",
  "EstimatedAmount": 2500.00,
  "CreatedDate": "2024-02-01",
  "LabourDetails": [...],
  "PartsDetails": [...]
}
```

---

### 4.2 Search Labour

**Endpoint**: `WebServices/LabourSearch.asmx`  
**Method**: POST  
**Authentication**: Required

**Description**: Search labour operations for job card.

**Request/Response**: Similar pattern to part search

---

### 4.3 Search Complaints

**Endpoint**: `WebServices/ComplaintSearch.asmx`  
**Method**: POST  
**Authentication**: Required

**Description**: Search predefined complaint descriptions.

---

## 5. Sales & Booking APIs

### 5.1 Create Booking

**Endpoint**: `Sales/Booking.aspx` (Page-based)  
**Method**: POST  
**Authentication**: Required

**Description**: Create vehicle booking with customer and advance details.

**Request Parameters**: Complex form with customer, vehicle, payment details

**Validation Rules**:
- Advance amount: Minimum as per vehicle scheme
- Model availability check
- Customer KYC details mandatory

---

### 5.2 Search Booking

**Endpoint**: `Sales/BookingSearch.aspx`  
**Method**: GET/POST  
**Authentication**: Required

**Description**: Search bookings by various criteria.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| BookingNo | string | Booking number |
| CustomerName | string | Customer name search |
| FromDate | date | Start date filter |
| ToDate | date | End date filter |
| Status | string | Booking status |

---

## 6. Accounts & Finance APIs

### 6.1 Create Receipt Voucher

**Endpoint**: `Accounts/ReceiptVoucher.aspx`  
**Method**: POST  
**Authentication**: Required

**Description**: Create receipt voucher for customer payments.

---

### 6.2 Create Payment Voucher

**Endpoint**: `Accounts/CreatePaymentVoucher.aspx`  
**Method**: POST  
**Authentication**: Required

---

## 7. Inventory APIs

### 7.1 GRN from TVS

**Endpoint**: `Parts/SparesGRNForTVS.aspx`  
**Method**: POST  
**Authentication**: Required

**Description**: Goods Receipt Note from TVS manufacturer.

---

### 7.2 Stock Transfer

**Endpoint**: `Parts/StockTransfer.aspx`  
**Method**: POST  
**Authentication**: Required

---

## 8. Warranty & Claims APIs

### 8.1 Warranty Claim

**Endpoint**: `Service/WarrantyClaim.aspx`  
**Method**: POST  
**Authentication**: Required

**Description**: Submit warranty claim for vehicle.

---

### 8.2 ASC Warranty Claim

**Endpoint**: `Service/ASCWarrantyClaim.aspx`  
**Method**: POST  
**Authentication**: Required

---

## External API Dependencies

### 8.1 SAP Integration

**Service**: Oracle/SAP RFC Calls  
**Function Modules**:
- `ZDIS07_CHECK_FRAME` - Frame number validation
- Vehicle master data sync
- Parts pricing and availability

**Connection**: RFC Destination configured in web.config

---

### 8.2 CRM Integration

**Service References**:
- CRMAvailablePoints
- CRMBurnPoints  
- CRMReferralCustomer

**Purpose**: Loyalty points management and referral tracking

---

### 8.3 Insurance Policy Upload

**Service**: InsurancePolicyUpload  
**Purpose**: Upload insurance policy details to central system

---

### 8.4 SMS Gateway

**Service**: AirtelSmsService  
**Configuration**: SMS helper with API credentials  
**Usage**: 
- Booking confirmation
- Service reminders
- Payment receipts
- PSF notifications

---

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "ERR_INVALID_INPUT",
    "message": "Invalid frame number format",
    "details": "Frame number must be 17 characters"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| ERR_UNAUTHORIZED | Session expired or invalid | 401 |
| ERR_FORBIDDEN | Insufficient permissions | 403 |
| ERR_NOT_FOUND | Resource not found | 404 |
| ERR_VALIDATION | Input validation failed | 400 |
| ERR_DUPLICATE | Duplicate record | 409 |
| ERR_SAP_CONN | SAP connection failure | 502 |
| ERR_DB_CONN | Database connection error | 500 |
| ERR_BUSINESS_RULE | Business rule violation | 422 |

---

## Rate Limiting

**Current Implementation**: Not explicitly enforced  
**Recommendation**: Implement per-user rate limiting at application level

---

## Versioning

**Current**: No explicit API versioning  
**Format**: Embedded in service/page structure  
**Recommendation**: Implement URL-based versioning for future APIs

---

## Data Formats

### Date Format
- Input: `YYYY-MM-DD` or `DD/MM/YYYY`
- Output: `YYYY-MM-DD` (JSON) or `DD/MM/YYYY` (UI)

### Currency
- Format: Decimal (18, 2)
- Currency: INR (Indian Rupees)

### Phone Numbers
- Format: 10-digit numeric (India)
- Validation: Pattern `^[6-9][0-9]{9}$`

---

## Security Considerations

### Authentication
- Session timeout: Configurable in web.config (default 20 minutes)
- Password: Encrypted storage (hashing recommended)
- HTTPS required for production

### Input Validation
- Server-side validation mandatory
- SQL injection prevention: Parameterized queries
- XSS prevention: Input encoding

### Authorization
- Role-based access control
- Dealer data isolation
- Branch-level segregation

---

## Sample Request/Response Examples

### Complete Example: Create Job Card

**Request** (Form Data):
```
txtJobCardDate=2024-02-01
ddlCustomer=12345
txtFrameNo=MBLHA10FXHJXXXXXX
txtOdometer=15000
txtComplaints=Engine making unusual noise
chkServices=1,2,5
... (labour and parts grid data)
```

**Response**: Page redirect with success message or inline validation errors

---

## Appendices

### A. Session Variables Reference

| Variable | Type | Description |
|----------|------|-------------|
| DEALERID | integer | Current dealer ID |
| BranchID | integer | Current branch ID |
| UserID | integer | Logged-in user ID |
| UserName | string | User display name |
| RoleID | integer | User role identifier |
| CountryCode | string | IN/ID |
| AllotmentLocationId | integer | Default storage location |
| OrderType | string | TVS/APS/Others |
| FinancialYear | string | Current FY (YYYY-YY) |

### B. Common Validation Patterns

**Frame Number**: `^[A-Z0-9]{17}$`  
**Mobile (India)**: `^[6-9][0-9]{9}$`  
**Email**: Standard RFC 5322  
**PAN**: `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`  
**Aadhar**: `^[0-9]{12}$`  
**GSTIN**: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`  
**Pincode**: `^[0-9]{6}$`

### C. Business Object Entities

**CustomerDO**: Customer master data  
**VehicleDO**: Vehicle master data  
**SparePartDO**: Spare parts data  
**JobCardDO**: Job card details  
**BookingDO**: Vehicle booking  
**InvoiceDO**: Sales invoice

---

## Support & Contact

**Technical Support**: [Placeholder]  
**API Documentation Updates**: [Placeholder]  
**Issue Tracking**: [Placeholder]

---

*Document Version: 1.0*  
*Last Updated: June 4, 2026*  
*Generated for: DMS Domestic Web - Channel Partner ART*

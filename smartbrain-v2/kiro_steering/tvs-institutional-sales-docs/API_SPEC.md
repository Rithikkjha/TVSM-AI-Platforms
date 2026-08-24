# API Specification — Institutional Sales Process

## Overview

- **Title**: Institutional Sales API
- **Version**: 1.0
- **Base URL**: `https://institutional-sales-server.azurewebsites.net`
- **Local URL**: `http://localhost:8080`
- **Swagger UI**: `/api-docs`
- **Format**: REST (JSON)

---

## Authentication

All endpoints require a Bearer token in the `Authorization` header:
```
Authorization: Bearer <azure_ad_jwt_token>
```

Token is obtained via Azure AD (MSAL) OAuth 2.0 flow. The API validates tokens using JWKS (RS256) from the Azure AD tenant discovery endpoint.

### Token Claims Used
| Claim | Purpose |
|-------|---------|
| `roles` | Application roles (`Document.Create`, `Document.Approve`) |
| `oid` | User's Azure AD Object ID |
| `preferred_username` | User's email address |
| `name` | User's display name |

---

## Endpoints

### 1. Quotations

#### GET /quotations
Get all quotations (filtered by user role).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (draft, review, approved, etc.) |
| `doc_type` | string | Filter by document type |

**Response 200:**
```json
{
  "statusCode": 200,
  "message": "Success",
  "data": [
    {
      "doc_id": "QT-2024-001",
      "doc_type": "Vehicle Quotation",
      "status": "draft",
      "created_at": "2024-01-15T10:30:00Z",
      "created_by": { "id": "...", "name": "John Doe", "role": "Document.Create" },
      "institution_details": { "name": "ABC Corp", "email": "..." },
      "summary": { "gross_amount": 500000, "net_quantity": 10, "total_discount": 50000, "net_amount": 450000 }
    }
  ]
}
```

#### POST /quotations
Create a new quotation.

**Request Body:**
```json
{
  "doc_type": "Vehicle Quotation",
  "institution_details": {
    "_id": "inst_id",
    "name": "ABC Corp",
    "email": "contact@abc.com",
    "phone": "9876543210",
    "contact_person": "Jane Smith",
    "address": {
      "line": "123 Main St",
      "city": "Chennai",
      "state": "Tamil Nadu",
      "pincode": "600001"
    }
  },
  "line_items": [
    {
      "product_name": "TVS Apache RTR 160",
      "state": "Tamil Nadu",
      "city": "Chennai",
      "actual_price": 120000,
      "special_price": 115000,
      "quantity": 5,
      "gross_value": 600000,
      "discount": 5000,
      "total_discount": 25000,
      "net_value": 575000,
      "dealer_contribution": 2000,
      "tvs_contribution": 3000
    }
  ],
  "summary": {
    "gross_amount": 600000,
    "net_quantity": 5,
    "total_discount": 25000,
    "net_amount": 575000
  }
}
```

**Response 201:**
```json
{
  "statusCode": 201,
  "message": "Quotation created successfully",
  "data": { "...quotation_document..." }
}
```

#### GET /quotations/:identifier
Get a quotation by MongoDB `_id` or `doc_id`.

**Response 200:**
```json
{
  "statusCode": 200,
  "data": { "...full_quotation_document..." }
}
```

#### PATCH /quotations/:identifier
Update a quotation (status change, field edits).

**Request Body:**
```json
{
  "status": "review",
  "line_items": [...],
  "summary": {...}
}
```

#### GET /quotations/pdf/:identifier
Get base64-encoded PDF for a quotation.

**Response 200:**
```json
{
  "statusCode": 200,
  "data": { "pdf": "<base64_encoded_pdf>" }
}
```

---

### 2. Proforma Invoices

#### GET /proforma-invoices
List all proforma invoices (role-filtered).

#### POST /proforma-invoices
Create a new proforma invoice.

**Request Body:**
```json
{
  "doc_type": "Vehicle Proforma Invoice",
  "quotation_id": "QT-2024-001",
  "institution_details": { ... },
  "line_items": [
    {
      "product_name": "TVS Apache RTR 160",
      "quantity": 3,
      "quantity_quoted": 5,
      "actual_price": 120000,
      "special_price": 115000,
      "gross_value": 360000,
      "discount": 5000,
      "total_discount": 15000,
      "net_value": 345000
    }
  ],
  "summary": { ... }
}
```

#### GET /proforma-invoices/:identifier
Get proforma invoice by ID or doc_id.

#### PATCH /proforma-invoices/:identifier
Update proforma invoice.

#### GET /proforma-invoices/pdf/:identifier
Get proforma invoice PDF.

#### GET /proforma-invoices/related/:identifier
Get all proforma invoices related to the same quotation.

---

### 3. Payment Receipts

#### GET /payment-receipts
List all payment receipts (role-filtered).

#### POST /payment-receipts
Create a new payment receipt.

**Request Body:**
```json
{
  "doc_type": "Vehicle Payment Receipt",
  "quotation_id": "QT-2024-001",
  "proforma_invoice_id": "PI-2024-001",
  "proforma_invoice_date": "2024-02-01",
  "institution_details": { ... },
  "amount": 345000,
  "reference_number": "REF-001",
  "utr_number": "UTR123456789",
  "transaction_date": "2024-02-10"
}
```

#### GET /payment-receipts/:identifier
Get payment receipt by ID or doc_id.

#### PATCH /payment-receipts/:identifier
Update payment receipt.

#### GET /payment-receipts/pdf/:identifier
Get payment receipt PDF.

---

### 4. Vouchers

#### GET /vouchers
List all vouchers (role-filtered).

#### POST /vouchers
Create a new voucher.

**Request Body:**
```json
{
  "doc_type": "Vehicle Voucher",
  "quotation_id": "QT-2024-001",
  "proforma_invoice_id": "PI-2024-001",
  "product_identifier": "prod_001",
  "voucher_value": 115000,
  "voucher_face_value": 120000,
  "institution_details": { ... },
  "beneficiary_details": {
    "name": "Beneficiary Name",
    "contact": "9876543210",
    "address_line": "456 Street",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "pincode": "600001",
    "aadhar_number": "1234-5678-9012"
  },
  "dealer_details": {
    "name": "Dealer ABC",
    "dealer_code": "DLR001",
    "contact": "9876543211",
    "address_line_1": "789 Road",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "pincode": "600002"
  },
  "vehicle_details": { ... }
}
```

#### GET /vouchers/:identifier
Get voucher by ID or doc_id.

#### PATCH /vouchers/:identifier
Update voucher.

#### GET /vouchers/pdf/:identifier
Get voucher PDF.

---

### 5. Institutions

#### GET /institutions
List all registered institutions.

**Response 200:**
```json
[
  {
    "_id": "inst_001",
    "name": "ABC Corporation",
    "branches": [
      {
        "address_line1": "123 Main St",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
        "pincode": "600001",
        "contacts": [
          { "name": "Jane Smith", "email": "jane@abc.com", "phone": "9876543210", "is_active": true }
        ]
      }
    ]
  }
]
```

#### POST /institutions
Create a new institution.

**Request Body:**
```json
{
  "name": "New Institution",
  "branches": [
    {
      "address_line1": "Address Line 1",
      "city": "City",
      "state": "State",
      "country": "India",
      "pincode": "600001",
      "contacts": [
        { "name": "Contact Person", "email": "contact@inst.com", "phone": "9876543210" }
      ]
    }
  ]
}
```

---

### 6. Vehicles

#### POST /vehicles
Get vehicle price based on filters.

**Request Body:**
```json
{
  "product_name": "TVS Apache RTR 160",
  "state": "Tamil Nadu",
  "city": "Chennai"
}
```

#### GET /vehicles/states
Get list of available states.

#### GET /vehicles/cities
Get list of cities (filterable by state via query params).

#### GET /vehicles/locations
Search locations by keyword.

---

### 7. Dealers

#### GET /dealers/:dealerCode
Get dealer details by dealer code.

**Response 200:**
```json
{
  "statusCode": 200,
  "data": {
    "name": "TVS Dealer Chennai",
    "dealer_code": "DLR001",
    "contact": "9876543211",
    "address_line_1": "789 Road",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "pincode": "600002"
  }
}
```

---

### 8. Dashboard

#### GET /dashboard
Get aggregated counts across all document types.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `doc_type` | string | Filter by document type |

**Response 200:**
```json
{
  "statusCode": 200,
  "data": {
    "quotations": { "draft": 5, "review": 3, "approved": 10, "total": 18 },
    "proformas": { "draft": 2, "review": 1, "approved": 8, "total": 11 },
    "payments": { "draft": 1, "total": 5 },
    "vouchers": { "active": 15, "redeemed": 30, "total": 45 }
  }
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "statusCode": 400 | 401 | 403 | 404 | 500,
  "message": "Error description"
}
```

### Common Errors
| Status | Scenario |
|--------|----------|
| 400 | Invalid request body, failed DTO validation |
| 401 | Missing or invalid Bearer token |
| 403 | User lacks required role for the action |
| 404 | Document not found by identifier |
| 500 | Internal server error (unhandled exception) |

---

## Validation Rules

| Field | Rule |
|-------|------|
| `doc_type` | Must be one of defined DocTypes constants |
| `status` | Must follow valid state transitions |
| `institution_details` | Required for create operations |
| `line_items` | Must have at least 1 item for quotations/proformas |
| `amount` | Required, must be positive number (payment receipts) |
| `transaction_date` | Required (payment receipts) |
| `quotation_id` | Required for proformas, payments, vouchers |
| `proforma_invoice_id` | Required for payments, vouchers |

---

## Rate Limits

Currently no rate limiting is implemented. Recommended for production:
- 100 requests/minute per user for read operations
- 20 requests/minute per user for write operations

---

## External API Dependencies

| External API | Purpose | Method |
|-------------|---------|--------|
| Azure AD JWKS | Token validation key retrieval | GET (HTTPS) |
| Azure Blob Storage | Document upload/download | SDK operations |
| Cloud Conductor Topics | Master data synchronization | Event listener |

---

*API Specification generated from codebase analysis — June 2026*

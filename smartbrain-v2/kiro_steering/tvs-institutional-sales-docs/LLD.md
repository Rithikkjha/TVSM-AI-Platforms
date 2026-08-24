# Low Level Design (LLD) — Institutional Sales Process

## 1. Detailed Module Breakdown

### Backend Modules (NestJS)

| Module | File | Responsibilities |
|--------|------|-----------------|
| `QuotationModule` | `quotation.module.ts` | Quotation CRUD, PDF generation, state transitions |
| `ProformaInvoiceModule` | `proformas.module.ts` | Proforma invoice lifecycle management |
| `PaymentModule` | `payments.module.ts` | Payment receipt creation and tracking |
| `VoucherModule` | `voucher.module.ts` | Voucher generation, validation, redemption |
| `InstitutionModule` | `institution.module.ts` | Institution master data management |
| `VehicleModule` | `vehicle.module.ts` | Vehicle catalog, pricing, location lookups |
| `DealerModule` | `dealer.module.ts` | Dealer master data retrieval |
| `DashboardModule` | `dashboard.module.ts` | Aggregated statistics and counts |
| `DocumentServiceModule` | `document.module.ts` | PDF/DOCX generation using templates |
| `UsersModule` | `users.module.ts` | User profile and contact lookup |
| `VoucherRedemptionModule` | `voucher-redemption.module.ts` | Dealer-side voucher redemption flow |

### Frontend Modules (React)

| Module | Path | Purpose |
|--------|------|---------|
| Authentication | `src/authConfig.js`, `src/routes/PrivateRouter.js` | MSAL login, token management |
| Quotation Dashboard | `src/pages/quotations-dashboard/` | List, filter, navigate quotations |
| Proforma Dashboard | `src/pages/proforma-invoices-dashborad/` | List proforma invoices |
| Payment Dashboard | `src/pages/payment-receipts-dashboard/` | List payment receipts |
| Voucher Dashboard | `src/pages/vehicle-voucher-dashboard/` | List vehicle vouchers |
| Add/Show Quotation | `src/pages/add-show-quotation/` | Create/view/edit quotations |
| Add/Show Proforma | `src/pages/add-show-proforma-invoice/` | Create/view proforma invoices |
| Add/Show Payment | `src/pages/add-show-payment-receipt/` | Create/view payment receipts |
| Add/Show Voucher | `src/pages/add-show-vehicle-voucher/` | Create/view vouchers |
| Generate Voucher | `src/pages/generate-vehicle-voucher/` | Bulk voucher generation |
| Store (State) | `src/components/stores/` | MobX stores for state management |

---

## 2. Class/Service Responsibilities

### Service Layer (API)

| Service | Responsibilities |
|---------|-----------------|
| `QuotationService` | Create/update/get quotations, PDF generation, role-based filtering, state validation |
| `ProformaInvoiceService` | Create/update/get proformas, link to quotations, related document queries |
| `PaymentReceiptService` | Create/update/get payments, link to proformas, PDF generation |
| `VoucherService` | Create/update/get vouchers, link to proformas, PDF generation, redemption status |
| `InstitutionService` | Get/create institutions, branch management |
| `VehicleService` | Retrieve vehicles by filters, price lookup, state/city queries |
| `DealerService` | Get dealer by code from master collection |
| `DashboardService` | Aggregate document counts by status and role |
| `UserService` | Find user by email, get contact info |
| `VoucherRedemptionService` | Validate voucher, redeem, update status |
| `DocumentService` | Template-based PDF/DOCX generation (Puppeteer, docxtemplater) |
| `EmailService` | Send notification emails on status changes |
| `TokenService` | Token parsing and user context extraction |

### Repository Layer (API)

| Repository | Collection | Operations |
|-----------|-----------|-----------|
| `QuotationRepository` | `quotations` | find, findById, create, update, aggregate |
| `ProformaInvoiceRepository` | `proforma_invoices` | find, findById, create, update |
| `PaymentReceiptRepository` | `payment_receipts` | find, findById, create, update |
| `VoucherRepository` | `vouchers` | find, findById, create, update |
| `InstitutionRepository` | `institutions` | find, create |
| `VehicleRepository` | `vehicles`, `price_catalog` | find by filters, price lookup |
| `DashboardRepository` | All collections | aggregate counts by status |
| `VoucherRedeemRepository` | `vouchers` | validate, redeem |

### Transformer Layer

| Transformer | Purpose |
|------------|---------|
| `QuotationTransformer` | Transform DB document → API response format |
| `ProformaTransformer` | Transform proforma data for response |
| `PaymentTransformer` | Transform payment receipt data |
| `VoucherTransformer` | Transform voucher data |
| `DealerTransformer` | Transform dealer master data |

---

## 3. API Flow Details

### Base URL
```
Production: https://institutional-sales-server.azurewebsites.net
Local: http://localhost:8080
Swagger: /api-docs
```

### Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/quotations` | List all quotations (filtered by role) |
| POST | `/quotations` | Create new quotation |
| GET | `/quotations/:identifier` | Get quotation by ID or doc_id |
| PATCH | `/quotations/:identifier` | Update quotation (status, fields) |
| GET | `/quotations/pdf/:identifier` | Get quotation PDF |
| GET | `/proforma-invoices` | List all proforma invoices |
| POST | `/proforma-invoices` | Create new proforma invoice |
| GET | `/proforma-invoices/:identifier` | Get proforma by ID |
| PATCH | `/proforma-invoices/:identifier` | Update proforma invoice |
| GET | `/proforma-invoices/pdf/:identifier` | Get proforma PDF |
| GET | `/proforma-invoices/related/:identifier` | Get related proformas |
| GET | `/payment-receipts` | List all payment receipts |
| POST | `/payment-receipts` | Create new payment receipt |
| GET | `/payment-receipts/:identifier` | Get payment receipt by ID |
| PATCH | `/payment-receipts/:identifier` | Update payment receipt |
| GET | `/payment-receipts/pdf/:identifier` | Get payment receipt PDF |
| GET | `/vouchers` | List all vouchers |
| POST | `/vouchers` | Create new voucher |
| GET | `/vouchers/:identifier` | Get voucher by ID |
| PATCH | `/vouchers/:identifier` | Update voucher |
| GET | `/vouchers/pdf/:identifier` | Get voucher PDF |
| GET | `/institutions` | List all institutions |
| POST | `/institutions` | Create new institution |
| POST | `/vehicles` | Get vehicle price by filters |
| GET | `/vehicles/states` | Get list of states |
| GET | `/vehicles/cities` | Get list of cities |
| GET | `/vehicles/locations` | Search locations |
| GET | `/dealers/:dealerCode` | Get dealer by code |
| GET | `/dashboard` | Get dashboard counts |

---

## 4. Internal Component Interactions

```
Controller → Service → Repository → MongoDB
    ↓            ↓
 Middleware    Transformer
 (Auth/Role)   (Response Format)
    ↓
  Utility
  (State Transition, RBAC, Email)
```

### Request Pipeline
```
HTTP Request
  → TokenRoleMiddleware (extract JWT claims, roles)
  → Controller (route handling)
  → Service (business logic, state validation, RBAC check)
  → Repository (database operations)
  → Transformer (format response)
  → Controller (return HTTP response)
```

---

## 5. Database Schema Usage

### Quotation Schema
```typescript
{
  doc_id: string (unique),          // e.g., "QT-2024-001"
  doc_type: string,                 // "Vehicle Quotation" | "Value Quotation"
  status: string,                   // draft | review | approved | rework | submitted | accepted
  created_at: string,
  created_by: { id, name, role, email, phone },
  institution_details: { _id, name, email, phone, contact_person, address },
  line_items: [{
    product_name, state, city,
    actual_price, special_price, value,
    quantity, gross_value, discount,
    total_discount, net_value,
    dealer_contribution, tvs_contribution
  }],
  summary: { gross_amount, net_quantity, total_discount, net_amount },
  audit_trail: [{ action, action_by, action_on, file_name, file_key }],
  rework_message: string
}
```

### Proforma Invoice Schema
```typescript
{
  doc_id: string (unique),
  doc_type: string,
  quotation_id: string,             // Link to parent quotation
  status: string,
  created_at: string,
  created_by: { id, name, role, email, phone },
  institution_details: { ... },
  line_items: [{ ..., quantity_quoted }],
  summary: { gross_amount, net_quantity, total_discount, net_amount },
  audit_trail: [{ ... }],
  rework_message: string
}
```

### Payment Receipt Schema
```typescript
{
  doc_id: string (unique),
  doc_type: string,
  quotation_id: string,
  proforma_invoice_id: string,      // Link to parent proforma
  proforma_invoice_date: string,
  status: string,
  created_at: string,
  created_by: { ... },
  institution_details: { ... },
  amount: number,
  reference_number: string,
  utr_number: string,
  transaction_date: string,
  summary: { ... },
  audit_trail: [{ ... }]
}
```

### Voucher Schema
```typescript
{
  doc_id: string (unique),
  doc_type: string,
  is_voucher_redeemed: boolean,
  product_identifier: string,
  quotation_id: string,
  proforma_invoice_id: string,
  status: string,
  voucher_value: number,
  voucher_face_value: number,
  created_by: { ... },
  institution_details: { ... },
  beneficiary_details: { name, contact, address_line, city, state, pincode, aadhar_number },
  dealer_details: { name, dealer_code, branch_code, contact, address_line_1, city, state, pincode },
  vehicle_details: { product_name, state, city, actual_price, special_price, ... },
  value_details: { value, quantity, net_value },
  audit_trail: [{ ... }]
}
```

### Institution Schema
```typescript
{
  name: string,
  branches: [{
    address_line1, address_line2, city, state, country, pincode,
    contacts: [{ name, email, phone, is_active }]
  }],
  created_at: string,
  created_by: { id, name, role, email, phone }
}
```

---

## 6. Request/Response Lifecycle

### Successful Create Request
```
POST /quotations
Headers: { Authorization: "Bearer <jwt_token>" }
Body: { doc_type, institution_details, line_items, summary }

Response 201:
{
  statusCode: 201,
  message: "Quotation created successfully",
  data: { ...quotation_document }
}
```

### Error Response Format
```json
{
  "statusCode": 400 | 401 | 403 | 404 | 500,
  "message": "Descriptive error message"
}
```

---

## 7. Validation Logic

### Input Validation
- **class-validator** decorators on DTOs enforce field types, required fields, and constraints
- **ValidationPipe** (global) with `whitelist: true` strips unknown properties
- Custom validation in services for business rules

### State Transition Validation
```typescript
validTransitions = {
  draft: ['draft', 'review'],
  review: ['approved', 'rework'],
  approved: ['submitted'],
  submitted: ['accepted'],
  rework: ['rework', 'review'],
}
```
Attempting an invalid transition returns 400 Bad Request.

### Role-Based Validation
| Action | Required Role |
|--------|--------------|
| Create draft | `Document.Create` |
| Submit for review | `Document.Create` |
| Approve document | `Document.Approve` |
| Request rework | `Document.Approve` |
| Submit/Accept | `Document.Create` or `Document.Approve` |

---

## 8. Error Handling

### Global Error Strategy
- Controllers wrap all operations in try/catch
- 500 Internal Server Error returned as fallback
- `UnauthorizedException` for invalid/missing tokens
- `ForbiddenException` for access denied (wrong creator, no role)
- `NotFoundException` for missing documents

### Audit Trail
Every status change is recorded in the `audit_trail` array with:
- `action` — the status transition performed
- `action_by` — user who performed the action
- `action_on` — ISO timestamp
- `file_name` / `file_key` — attached document references

---

## 9. Key Algorithms / Business Rules

### Document ID Generation
- Format: `{PREFIX}-{YEAR}-{SEQUENTIAL_NUMBER}`
- Prefixes: QT (Quotation), PI (Proforma), PR (Payment), VH (Voucher)

### Pricing Calculation
```
gross_value = actual_price × quantity
discount = (actual_price - special_price) × quantity
net_value = special_price × quantity
total_discount = Σ(discount per line item)
net_amount = Σ(net_value per line item)
```

### Voucher Generation
- One voucher per line item in an approved proforma invoice
- `voucher_value` = net_value of the line item
- `voucher_face_value` = actual_price of the line item
- Voucher linked back to quotation and proforma IDs

### Document Ownership
- Creators can only see/edit their own documents
- Approvers can see all documents in their scope
- Access check: `document.created_by.id === userData.userId` for creators

---

## 10. Configuration Handling

### Environment Configuration
- `dotenv` loads `.env` at startup
- `process.env.MONGODB_URL` — Database connection
- `process.env.PORT` — Server port (default: 8080)
- `process.env.AZURE_TENANT_ID` — Auth tenant validation

### CORS Configuration
```typescript
app.enableCors({
  origin: 'http://localhost:3000',
  methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
  credentials: true,
});
```

### Swagger Configuration
- Title: "Institutional Sales API"
- Available at: `/api-docs`
- All DTOs registered as extra models

---

*Document generated from codebase analysis — June 2026*

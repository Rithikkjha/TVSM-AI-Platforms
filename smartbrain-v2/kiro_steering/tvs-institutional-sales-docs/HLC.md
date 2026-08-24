# High Level Code Document — Institutional Sales Process

## 1. Application Overview

The Institutional Sales Process is a web application for TVS Motor Company that digitizes the institutional (bulk) vehicle sales workflow. It manages the complete document lifecycle from quotation creation through proforma invoice generation, payment tracking, and vehicle voucher issuance/redemption.

The system consists of:
- **Backend API**: NestJS (TypeScript) REST API with MongoDB persistence
- **Frontend SPA**: React 18 application with MobX state management and Azure AD authentication

---

## 2. Major Modules/Components

### Backend Modules

| Module | Description |
|--------|-------------|
| **Bookings** | Core business module containing all sales document management (quotations, proformas, payments, vouchers) |
| **Dealer Redemption** | Separate module for dealer-side voucher validation and redemption |
| **Cloud Conductor** | Event listener module for master data synchronization (dealer, price, product) |

### Frontend Modules

| Module | Description |
|--------|-------------|
| **Authentication** | MSAL-based Azure AD login/logout with token management |
| **Dashboards** | List views for quotations, proformas, payments, vouchers with filtering |
| **Document Forms** | Create/edit/view forms for each document type |
| **PDF Generation** | Client-side PDF preview and generation utilities |
| **State Management** | MobX stores for application state |
| **Routing** | React Router with private route guards |

---

## 3. Folder Structure Explanation

### API Structure
```
src/
├── main.ts                          # Application bootstrap, Swagger setup, CORS
├── app.module.ts                    # Root module, imports all feature modules
├── app.controller.ts                # Health check endpoint
├── app.service.ts                   # Root service
│
├── bookings/                        # Core business domain
│   ├── controllers/                 # HTTP request handlers (one per entity)
│   ├── services/                    # Business logic (one folder per entity)
│   ├── repositories/                # Database access (one folder per entity)
│   ├── schemas/                     # Mongoose schema definitions
│   ├── dto/                         # Data Transfer Objects (create/update per entity)
│   ├── modules/                     # NestJS module definitions
│   ├── middlewares/                 # Token validation middleware
│   ├── transformers/                # Response data transformers
│   ├── utils/                       # Shared utilities (auth, state, email, constants)
│   └── mock-datas/                  # Test mock data
│
├── cloud-conductor/                 # External data sync
│   └── topic-listener/              # Event listeners for master data
│
└── dealerRedeemption/               # Voucher redemption (dealer portal)
    ├── RedeemVoucher.controller.ts  # Redemption endpoints
    ├── voucher-redemption.module.ts # Module definition
    ├── redeemptionDtos/             # DTOs for redemption
    ├── voucher-redeempation-service/ # Redemption business logic
    └── voucher-redemption-repository/ # Redemption data access
```

### Frontend Structure
```
src/
├── App.js                           # Root component with MSAL provider
├── authConfig.js                    # Azure AD MSAL configuration
├── index.js                         # Application entry point
├── storeContext.js                   # MobX store context provider
│
├── routes/
│   ├── AppRoutes.js                 # Route definitions and navigation
│   └── PrivateRouter.js             # Authentication guard wrapper
│
├── pages/                           # Page-level components (one per route)
│   ├── quotations-dashboard/
│   ├── proforma-invoices-dashborad/
│   ├── payment-receipts-dashboard/
│   ├── vehicle-voucher-dashboard/
│   ├── add-show-quotation/
│   ├── add-show-proforma-invoice/
│   ├── add-show-payment-receipt/
│   ├── add-show-vehicle-voucher/
│   ├── generate-vehicle-voucher/
│   └── Login/
│
├── components/                      # Reusable UI components
│   ├── dashboard/                   # Dashboard widgets
│   ├── navbar/                      # Navigation bar
│   ├── addQuotation/                # Quotation form components
│   ├── payment-receipt/             # Payment receipt components
│   ├── proformaTemplate/            # Proforma display template
│   ├── stores/                      # MobX stores
│   ├── common/                      # Shared components
│   └── ...                          # Various UI components
│
├── utils/                           # Helper functions
│   ├── constants.js                 # API URLs, config
│   ├── routeConstants.js            # Route path constants
│   ├── createQuotation.js           # Quotation data builders
│   ├── createProforma.js            # Proforma data builders
│   ├── formateCurrency.js           # Currency formatting
│   ├── numberToWords.js             # Number-to-word conversion
│   ├── dateExpiryChecker.js         # Date validation
│   └── ...                          # Other utilities
│
├── styles/
│   └── tailwind.css                 # Tailwind CSS entry point
│
└── assets/                          # Static assets
    ├── icons/
    ├── images/
    └── font-family/
```

---

## 4. Core Business Workflows

### Quotation Workflow
1. Creator selects an institution
2. Adds vehicle/value line items with quantities and pricing
3. Saves as **Draft**
4. Submits for **Review**
5. Approver either **Approves** or sends for **Rework**
6. Approved quotation is **Submitted** to the institution
7. Institution acknowledges → status becomes **Accepted**

### Proforma Invoice Workflow
1. Created from an approved quotation
2. Line items carry over with quantity adjustments
3. Follows same state machine: Draft → Review → Approved → Submitted → Accepted
4. Multiple proformas can be created against one quotation

### Payment Receipt Workflow
1. Created against a proforma invoice
2. Records payment amount, UTR number, transaction date
3. Follows state machine for approval

### Voucher Workflow
1. Generated from approved proforma invoice line items
2. Each line item generates individual vouchers
3. Contains beneficiary and dealer assignment
4. Can be redeemed by dealers through the redemption portal

---

## 5. Key Services/Classes

### Backend Services

| Service | Key Methods |
|---------|-------------|
| `QuotationService` | `getQuotations()`, `createQuotation()`, `updateQuotation()`, `getQuotationPDF()` |
| `ProformaInvoiceService` | `getProformaInvoices()`, `createProformaInvoice()`, `updateProformaInvoice()`, `getProformaPDF()`, `getAllDocumentRelatedProformas()` |
| `PaymentReceiptService` | `getPaymentReceipts()`, `createPaymentReceipt()`, `updatePaymentReceipt()`, `getPaymentReceiptPDF()` |
| `VoucherService` | `getVouchers()`, `createVoucher()`, `updateVoucher()`, `getVoucherPDF()` |
| `VehicleService` | `retrieveVehicles()`, `retrieveStates()`, `retrieveCitiesName()`, `searchLocation()` |
| `DashboardService` | `getDashboardCounts()` |
| `VoucherRedemptionService` | `validateVoucher()`, `redeemVoucher()` |

### Utility Classes

| Utility | Purpose |
|---------|---------|
| `StateTransitionUtil` | Validates allowed status transitions |
| `role-based-access.util` | Checks user authorization for actions |
| `ResponseUtilService` | Standardizes API response format |
| `TokenService` | JWT token parsing and validation |
| `EmailService` | Sends notification emails |
| `formatCurrency` | Currency number formatting |

---

## 6. External Integrations

| Integration | Library/SDK | Purpose |
|------------|-------------|---------|
| Azure AD (MSAL) | `@azure/msal-browser`, `@azure/msal-react` | Frontend authentication |
| Azure AD (JWT) | `jsonwebtoken`, `jwks-rsa` | Backend token validation |
| Azure Blob Storage | `@azure/storage-blob` | File upload/download |
| Azure Cosmos DB | `mongoose`, `@nestjs/mongoose` | Database operations |
| PDF Generation | `puppeteer`, `pdfkit`, `pdf-lib` | Server-side PDF creation |
| Document Templates | `docxtemplater`, `pizzip` | DOCX template processing |
| HTTP Client | `axios`, `@nestjs/axios` | External API calls |

---

## 7. Major Dependencies

### Backend (NestJS)
| Package | Version | Purpose |
|---------|---------|---------|
| `@nestjs/core` | ^10.3.10 | Framework core |
| `@nestjs/mongoose` | ^10.0.10 | MongoDB ODM integration |
| `@nestjs/swagger` | ^7.4.0 | API documentation |
| `@nestjs/jwt` | ^10.2.0 | JWT utilities |
| `mongoose` | ^8.9.5 | MongoDB ODM |
| `puppeteer` | ^22.13.0 | PDF generation |
| `class-validator` | ^0.14.1 | DTO validation |
| `jsonwebtoken` | ^9.0.2 | Token verification |
| `jwks-rsa` | ^3.1.0 | JWKS key fetching |
| `@azure/storage-blob` | ^12.24.0 | Blob storage SDK |

### Frontend (React)
| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^18.3.1 | UI framework |
| `react-router-dom` | ^6.24.1 | Client-side routing |
| `@azure/msal-browser` | ^3.18.0 | Authentication |
| `@azure/msal-react` | ^2.0.20 | React auth hooks |
| `mobx` | ^6.4.1 | State management |
| `mobx-react` | ^7.3.0 | MobX React bindings |
| `axios` | ^1.7.9 | HTTP client |
| `tailwindcss` | ^3.4.4 | CSS framework |
| `jspdf` | ^2.5.1 | Client-side PDF |
| `@react-pdf/renderer` | ^3.4.4 | PDF rendering |

---

## 8. Runtime Architecture

```
Browser (React SPA)
  │
  ├── MSAL Authentication Layer
  │     └── Acquires Azure AD token
  │
  ├── MobX Store Layer
  │     └── Application state, API response caching
  │
  ├── Axios HTTP Layer
  │     └── Bearer token injection, API calls
  │
  └── React Component Tree
        └── Pages → Components → Utils

NestJS Server
  │
  ├── Express/Fastify HTTP Server (port 8080)
  │
  ├── Global Middleware Pipeline
  │     └── TokenRoleMiddleware → JWKS validation → role extraction
  │
  ├── Global Validation Pipe
  │     └── class-validator DTO enforcement
  │
  ├── Module-scoped Services
  │     └── Business logic, state machine, RBAC
  │
  ├── Repository Layer
  │     └── Mongoose Model operations
  │
  └── External Service Connectors
        ├── Azure Blob Storage
        ├── Email Service
        └── Cloud Conductor Listeners
```

---

## 9. Important Entry Points

### API Entry Points
| File | Purpose |
|------|---------|
| `src/main.ts` | Application bootstrap, Swagger setup, CORS, port binding |
| `src/app.module.ts` | Root module — registers all feature modules |
| `src/bookings/middlewares/token-role.middleware.ts` | Auth gate for all routes |

### Frontend Entry Points
| File | Purpose |
|------|---------|
| `src/index.js` | React DOM render, MSAL provider setup |
| `src/App.js` | Root component with routing |
| `src/authConfig.js` | Azure AD configuration (client ID, tenant, redirect) |
| `src/routes/AppRoutes.js` | Route definitions and page mapping |
| `src/storeContext.js` | MobX store initialization |

---

## 10. High-Level Data Flow

```
┌────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Action  │────>│  React Component │────>│  MobX Store     │
│  (Click/Form)  │     │  (Page/Form)     │     │  (State Update) │
└────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Axios + Token  │
                                               │  (API Call)     │
                                               └────────┬────────┘
                                                        │
                                                        ▼
┌────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MongoDB      │<────│  Repository      │<────│  Service        │
│  (Cosmos DB)   │     │  (Mongoose)      │     │  (Business)     │
└────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Transformer    │
                                               │  (Format Resp)  │
                                               └────────┬────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  HTTP Response  │
                                               │  (JSON)         │
                                               └─────────────────┘
```

---

*Document generated from codebase analysis — June 2026*

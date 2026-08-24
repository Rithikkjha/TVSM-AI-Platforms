# High Level Design (HLD) — Institutional Sales Process

## 1. System Architecture

The Institutional Sales Process is a three-tier web application deployed on Microsoft Azure, designed to manage bulk/institutional vehicle sales for TVS Motor Company.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  React SPA (Azure Static Web Apps)                          │    │
│  │  - MSAL Authentication                                      │    │
│  │  - MobX State Management                                    │    │
│  │  - Tailwind CSS                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │ HTTPS (REST API)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  NestJS API (Azure App Service)                             │    │
│  │  - JWT/JWKS Token Validation                                │    │
│  │  - Role-Based Access Control                                │    │
│  │  - Document State Machine                                   │    │
│  │  - PDF Generation (Puppeteer)                               │    │
│  │  - Email Notifications                                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  MongoDB         │ │ Azure Blob   │ │ Azure AD         │
│  (Cosmos DB)     │ │ Storage      │ │ (Identity)       │
│  - Quotations    │ │ - PDFs       │ │ - Authentication │
│  - Proformas     │ │ - Documents  │ │ - User Roles     │
│  - Payments      │ │              │ │                  │
│  - Vouchers      │ │              │ │                  │
│  - Institutions  │ │              │ │                  │
│  - Vehicles      │ │              │ │                  │
└──────────────────┘ └──────────────┘ └──────────────────┘
```

---

## 2. Major Components/Services

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| Frontend SPA | React 18, MSAL, MobX | User interface, authentication, state management |
| API Gateway | NestJS 10 | REST endpoints, validation, middleware pipeline |
| Auth Middleware | JWT/JWKS | Token validation, role extraction |
| Quotation Service | NestJS Service | CRUD + state transitions for quotations |
| Proforma Service | NestJS Service | CRUD + state transitions for proforma invoices |
| Payment Service | NestJS Service | CRUD + state transitions for payment receipts |
| Voucher Service | NestJS Service | CRUD + state transitions + redemption for vouchers |
| Document Service | Puppeteer/docxtemplater | PDF and DOCX generation |
| Vehicle Service | NestJS Service | Vehicle catalog, pricing, locations |
| Dashboard Service | NestJS Service | Aggregated counts and analytics |
| Dealer Service | NestJS Service | Dealer master data lookup |
| Cloud Conductor | Event Listeners | Sync dealer/price/product master data |

---

## 3. Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    AZURE CLOUD                                  │
│                                                                │
│  ┌─────────────────────┐    ┌─────────────────────┐           │
│  │ Azure Static Web    │    │ Azure App Service   │           │
│  │ Apps (Frontend)     │    │ (NestJS API)        │           │
│  │ - CDN distributed   │    │ - Auto-scaling      │           │
│  │ - Custom domain     │    │ - Node.js runtime   │           │
│  └─────────────────────┘    └─────────────────────┘           │
│             │                         │                        │
│             │         ┌───────────────┼──────────┐             │
│             │         ▼               ▼          ▼             │
│  ┌──────────┴────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐     │
│  │ Azure AD      │ │ Cosmos  │ │ Blob     │ │ Cloud   │     │
│  │ B2C/Entra ID  │ │ DB      │ │ Storage  │ │Conductor│     │
│  └───────────────┘ └─────────┘ └──────────┘ └─────────┘     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Bitbucket Pipelines (CI/CD)                             │  │
│  │ - Build → Test → Deploy (main branch)                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Deployment Flow
1. Developer pushes to `main` branch on Bitbucket
2. Pipeline triggers: install → build → deploy
3. API: Azure CLI deploys to App Service
4. Frontend: Azure Static Web Apps deploy pipe

---

## 4. Database Interactions

### MongoDB Collections

| Collection | Purpose |
|-----------|---------|
| `quotations` | Store quotation documents with line items and audit trail |
| `proforma_invoices` | Store proforma invoices linked to quotations |
| `payment_receipts` | Store payment receipts linked to proformas |
| `vouchers` | Store vehicle/value vouchers with redemption status |
| `institutions` | Master data for institutional customers |
| `vehicles` | Vehicle catalog with pricing |
| `dealer_details_master` | Dealer information synced from master |
| `price_catalog` | Price catalog synced from master |
| `cities` | City master data |
| `states` | State master data |
| `users` | Internal user records |

### Data Relationships
```
Institution → Quotation → Proforma Invoice → Payment Receipt
                                           → Voucher (per line item)
```

---

## 5. API Integrations

| Integration | Protocol | Purpose |
|------------|----------|---------|
| Azure AD / Entra ID | OAuth 2.0 / OIDC | User authentication and role claims |
| Azure Blob Storage | REST (SDK) | Document storage (PDFs, attachments) |
| Cloud Conductor | Event-driven | Master data sync (dealer, price, product) |
| Email Service | SMTP/API | Notifications on status changes |

---

## 6. Authentication & Authorization Flow

```
┌──────┐         ┌──────────┐         ┌─────────┐         ┌──────┐
│Client│         │ Azure AD │         │   API   │         │  DB  │
└──┬───┘         └────┬─────┘         └────┬────┘         └──┬───┘
   │ 1. Login Request │                    │                  │
   │─────────────────>│                    │                  │
   │ 2. Auth Token    │                    │                  │
   │<─────────────────│                    │                  │
   │ 3. API Request + Bearer Token         │                  │
   │──────────────────────────────────────>│                  │
   │                  │ 4. Validate JWT    │                  │
   │                  │   (JWKS endpoint)  │                  │
   │                  │<───────────────────│                  │
   │                  │ 5. Public Key      │                  │
   │                  │───────────────────>│                  │
   │                  │                    │ 6. Extract Roles │
   │                  │                    │ 7. Check RBAC    │
   │                  │                    │ 8. Query DB      │
   │                  │                    │─────────────────>│
   │                  │                    │ 9. Response      │
   │                  │                    │<─────────────────│
   │ 10. API Response │                    │                  │
   │<──────────────────────────────────────│                  │
```

### Roles
| Role | Permissions |
|------|------------|
| `Document.Create` | Create drafts, submit for review, edit reworks |
| `Document.Approve` | Approve/reject documents, request rework |

---

## 7. External Systems

| System | Integration Type | Data Flow |
|--------|-----------------|-----------|
| Azure Active Directory | OAuth 2.0 | Inbound (auth tokens) |
| Azure Blob Storage | SDK | Bidirectional (upload/download) |
| Cloud Conductor (TVS Internal) | Event Listener | Inbound (master data sync) |
| Email Service | API/SMTP | Outbound (notifications) |
| TVS Dealer Master | Event-driven | Inbound (dealer data) |
| TVS Price Master | Event-driven | Inbound (price catalog) |
| TVS Product Master | Event-driven | Inbound (vehicle data) |

---

## 8. Infrastructure Dependencies

| Resource | Service | Purpose |
|----------|---------|---------|
| Azure App Service | PaaS | API hosting |
| Azure Static Web Apps | PaaS | Frontend hosting with CDN |
| Azure Cosmos DB (MongoDB API) | DBaaS | Primary database |
| Azure Blob Storage | Storage | Document/file storage |
| Azure AD / Entra ID | Identity | Authentication & authorization |
| Bitbucket Pipelines | CI/CD | Build and deployment automation |

---

## 9. High-Level Sequence Flows

### Quotation Creation Flow
```
User → Login (Azure AD) → Dashboard → Create Quotation
  → Select Institution → Add Line Items → Save as Draft
  → Submit for Review → Approver Reviews
  → Approve / Rework → Generate PDF → Submit to Customer
```

### Document State Machine
```
  draft → review → approved → submitted → accepted
    ↑        │
    └── rework ←┘
```

### Voucher Redemption Flow
```
Dealer → Validate Voucher Code → Check Status
  → Verify Beneficiary → Redeem Voucher → Mark as Redeemed
```

---

## 10. Scalability & Resiliency Considerations

| Aspect | Strategy |
|--------|----------|
| Horizontal Scaling | Azure App Service auto-scale on CPU/memory thresholds |
| Database Scaling | Cosmos DB auto-partition with throughput scaling |
| CDN / Static Assets | Azure Static Web Apps with global edge distribution |
| Session Management | Stateless API (JWT-based); no server-side sessions |
| Error Recovery | Global exception filters, audit trail for all operations |
| Data Consistency | MongoDB transactions for multi-document updates |
| Monitoring | Azure Application Insights (recommended) |
| Rate Limiting | To be implemented (currently not enforced) |

---

*Document generated from codebase analysis — June 2026*

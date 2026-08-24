# Institutional Sales Process Application

## Application Overview

The Institutional Sales Process application is a full-stack web solution for TVS Motor Company that manages the end-to-end institutional sales workflow. It enables sales teams to create quotations, proforma invoices, payment receipts, and vehicle vouchers for institutional customers (bulk buyers like corporates, government agencies, and organizations).

### Key Capabilities
- **Quotation Management** — Create, review, approve, and track quotations for institutional clients
- **Proforma Invoice Generation** — Generate proforma invoices from approved quotations
- **Payment Receipt Tracking** — Record and manage payment receipts against proforma invoices
- **Vehicle Voucher Issuance** — Issue and redeem vehicle vouchers for institutional purchases
- **Dashboard Analytics** — Real-time counts and status tracking across all document types
- **Role-Based Access Control** — Separate flows for Document Creators and Document Approvers
- **PDF Generation** — Generate downloadable PDF documents for all transaction types

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18, MobX, Tailwind CSS, MSAL (Azure AD) |
| Backend | NestJS 10 (Node.js), TypeScript |
| Database | MongoDB (via Mongoose), Azure Cosmos DB |
| Authentication | Azure AD (MSAL), JWT with JWKS validation |
| Storage | Azure Blob Storage |
| Deployment | Azure App Service (API), Azure Static Web Apps (Frontend) |
| CI/CD | Bitbucket Pipelines |

---

## Setup Instructions

### Prerequisites
- Node.js v18+ (Frontend) / v14+ (API)
- npm v8+
- MongoDB instance (local or Azure Cosmos DB)
- Azure AD tenant configured
- Azure Storage account (for document storage)

### Clone Repositories
```bash
# API
git clone <bitbucket-repo-url>/process_api.git

# Frontend
git clone <bitbucket-repo-url>/institutionsales-frontend.git
```

---

## Local Development

### API (Backend)
```bash
cd api/Institutional_sales_process_api
npm install
npm run start:dev
```
The API server runs on `http://localhost:8080` with Swagger docs at `/api-docs`.

### Frontend
```bash
cd Frontend/institutionsales-frontend
npm install
npm start
```
The frontend runs on `http://localhost:3000`.

---

## Environment Variables

### API (.env)
| Variable | Description |
|----------|-------------|
| `MONGODB_URL` | MongoDB connection string |
| `PORT` | Server port (default: 8080) |
| `AZURE_TENANT_ID` | Azure AD Tenant ID for JWT validation |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection string |
| `AZURE_STORAGE_CONTAINER_NAME` | Blob container for document storage |

### Frontend (.env)
| Variable | Description |
|----------|-------------|
| `REACT_APP_API_URL` | Backend API base URL |
| `REACT_APP_CLIENT_ID` | Azure AD Application Client ID |
| `REACT_APP_AUTHORITY` | Azure AD Authority URL |
| `REACT_APP_REDIRECT_URI` | Post-login redirect URI |

---

## Build Instructions

### API
```bash
cd api/Institutional_sales_process_api
npm run build
```
Output: `dist/` directory

### Frontend
```bash
cd Frontend/institutionsales-frontend
npm run build
```
Output: `build/` directory (static assets)

---

## Deployment

### API Deployment (Azure App Service)
- Deployed via Bitbucket Pipelines on `main` branch push
- Target: Azure App Service (`institutional-sales-server`)
- Resource Group: `tvs`

### Frontend Deployment (Azure Static Web Apps)
- Deployed via Bitbucket Pipelines on `main` branch push
- Target: Azure Static Web Apps
- Configuration: `staticwebapp.config.json` handles routing

---

## Testing

### API
```bash
npm run test          # Run unit tests
npm run test:cov      # Run tests with coverage
npm run test:e2e      # Run end-to-end tests
```

### Frontend
```bash
npm run test          # Run React testing library tests
```

---

## Folder Structure

```
├── api/
│   └── Institutional_sales_process_api/
│       └── src/
│           ├── bookings/
│           │   ├── controllers/     # REST API controllers
│           │   ├── dto/             # Data Transfer Objects
│           │   ├── middlewares/     # Auth middleware
│           │   ├── modules/        # NestJS modules
│           │   ├── repositories/   # Database access layer
│           │   ├── schemas/        # Mongoose schemas
│           │   ├── services/       # Business logic
│           │   ├── transformers/   # Data transformers
│           │   └── utils/          # Utilities (auth, state, email)
│           ├── cloud-conductor/    # Event listeners (dealer/price/product masters)
│           └── dealerRedeemption/  # Voucher redemption module
├── Frontend/
│   └── institutionsales-frontend/
│       └── src/
│           ├── components/         # Reusable UI components
│           ├── pages/              # Route-level page components
│           ├── routes/             # React Router configuration
│           ├── utils/              # Helper functions and constants
│           └── assets/             # Static assets (icons, images, fonts)
└── docs/                           # Documentation
```

---

## Common Troubleshooting

| Issue | Resolution |
|-------|-----------|
| `Token verification failed` | Ensure `AZURE_TENANT_ID` matches your Azure AD tenant |
| MongoDB connection timeout | Verify `MONGODB_URL` and network access rules |
| CORS errors on localhost | API enables CORS for `http://localhost:3000` by default |
| Frontend auth redirect loop | Check `redirectUri` in `authConfig.js` matches your environment |
| PDF generation fails | Ensure Puppeteer dependencies are installed on the server |
| Swagger not loading | Visit `/api-docs` (not `/swagger`) |

---

## Maintainers / Contact

| Role | Contact |
|------|---------|
| Project Owner | [TVS Motor - Digital Engineering Team] |
| Backend Lead | [TBD] |
| Frontend Lead | [TBD] |
| DevOps | [TBD] |
| HO Team Email | aditya.sekhar@tvsmotor.com |

---

*Last updated: June 2026*

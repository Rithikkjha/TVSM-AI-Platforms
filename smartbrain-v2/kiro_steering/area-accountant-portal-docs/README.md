# TVS CustomerBay — Area Accountant Portal

A React-based internal portal for TVS Motor Company's Area Accountants to manage vehicle booking claims, payment transactions, and TRV (Two-wheeler Registration Verification) claims.

---

## Application Overview

CustomerBay provides:
- **Claims Management** — Review, approve, or reject dealer booking claims
- **TRV Claims** — Verify vehicle registration documents and process claims via SAP
- **Export** — Download filtered claim data as CSV files
- **Role-based Access** — Area Accountant (full access) and AMTM (TRV only)

Deployed at: `/bsvi` path on TVS production infrastructure.

---

## Setup Instructions

### Prerequisites
- **Node.js** v18.x or higher
- **npm** v8.x or higher
- Access to TVS corporate network (for API connectivity)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd customerbay

# Install dependencies
npm install
```

---

## Local Development

### Start Development Server

```bash
npm start
```

The app runs at `http://localhost:3000/bsvi` by default.

### API Configuration

To point to a local backend, edit `src/components/stores/APIEndpoints.js`:

```javascript
// Uncomment for local development:
const backendHost = 'http://localhost:5201/api/areaAccountant/';

// Comment out production URL:
// const backendHost = 'https://iqubeprod.tvsmotor.com/BS/api/areaAccountant/';
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start development server with hot reload |
| `npm run build` | Create production build |
| `npm test` | Run test suite |

---

## Environment Variables

This project does not use `.env` files. Configuration is managed through:

| Config | Location | Description |
|--------|----------|-------------|
| API Base URL | `src/components/stores/APIEndpoints.js` | Backend API endpoint |
| Homepage path | `package.json` → `homepage` | Set to `/bsvi` |
| Source maps | `npm run deploy` script | Disabled via `GENERATE_SOURCEMAP=false` |

---

## Build Instructions

### Production Build

```bash
npm run build
```

This generates optimized static files in the `build/` directory using `react-app-rewired`.

### Build Configuration

Custom webpack overrides are in `config-overrides.js`:
- Legacy decorators enabled (for MobX)
- ESLint disabled during build

### Deploy

```bash
npm run deploy
```

This builds the app (without source maps) and syncs to AWS S3.

---

## Deployment Steps

### CI/CD Pipeline (Azure DevOps)

The project uses Azure DevOps pipelines:

1. **PR Validation** (`Prod-PR.yaml`) — Runs on pull request creation
2. **CI Build** (`Area-Accountant-UI-prod-ci.yaml`) — Builds on merge to main
3. **CD Deploy** (`Area-Accountant-Prod-CD.yaml`) — Deploys to production

### Manual Deployment

```bash
# Build production bundle
GENERATE_SOURCEMAP=false npm run build

# Deploy to S3 (requires AWS CLI configured)
aws s3 sync build/ s3://krust.krscode.com
```

### Environments

| Environment | URL |
|-------------|-----|
| Production | `https://iqubeprod.tvsmotor.com/bsvi` |
| UAT | `https://uat-bookingapi.tvsmotor.net` (backend only) |
| Local | `http://localhost:3000/bsvi` |

---

## Testing Instructions

```bash
# Run tests
npm test

# Run tests in CI mode (non-interactive)
npm test -- --watchAll=false
```

Testing stack:
- `@testing-library/react` — Component testing
- `@testing-library/jest-dom` — DOM assertions
- `@testing-library/user-event` — User interaction simulation

---

## Folder Structure

```
customerbay/
├── public/                     # Static assets
├── src/
│   ├── App.js                  # Root component
│   ├── components/
│   │   ├── stores/             # MobX state management
│   │   ├── areaAccountant/     # Claims management module
│   │   ├── TRVDetails/         # TRV claims module
│   │   ├── Modals/             # Shared modal components
│   │   └── util/               # Utilities (Style, Util)
│   └── App.css                 # Global styles
├── config-overrides.js         # Webpack customization
├── package.json                # Dependencies and scripts
└── *.yaml                      # CI/CD pipeline definitions
```

---

## Common Troubleshooting

| Issue | Solution |
|-------|----------|
| `Module not found` errors | Run `npm install` to ensure all dependencies are installed |
| API calls failing locally | Check `APIEndpoints.js` points to correct backend URL |
| SSO not working locally | SSO requires corporate network; use username/password login for local dev |
| Build fails with decorator errors | Ensure `config-overrides.js` is present and `react-app-rewired` is installed |
| Blank page after build | Verify `homepage` in `package.json` matches deployment path (`/bsvi`) |
| AG Grid not rendering | Check `ag-grid-community` CSS imports in `App.js` |
| Session expired immediately | JWT token may be invalid; clear localStorage and re-login |

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 17.x | UI framework |
| MobX | 6.x | State management |
| Ant Design | 4.x | UI components |
| AG Grid | 27.x | Data grids |
| Axios | 1.x | HTTP client (file uploads) |
| Moment.js | — | Date handling |
| react-app-rewired | 2.x | Build customization |

---

## Maintainer / Contact

| Role | Contact |
|------|---------|
| Project Owner | [TVS Digital Engineering Team] |
| Frontend Team | [Contact placeholder] |
| Backend Team | [Contact placeholder] |
| DevOps | [Contact placeholder] |
| IT Support | Contact IT Team for access issues |

---

## Additional Documentation

- [High Level Code Document](./HLC.md)
- [High Level Design](./HLD.md)
- [Low Level Design](./LLD.md)
- [API Specification](./API_SPEC.md)

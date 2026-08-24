# High Level Code Document — TVS CustomerBay (Area Accountant Portal)

## 1. Application Overview

TVS CustomerBay is an internal web portal built for **TVS Motor Company** to manage vehicle booking claims, payment transactions, and TRV (Two-wheeler Registration Verification) claims. The application is primarily used by **Area Accountants** and **AMTM** (Area Manager — Two-wheeler Marketing) roles to review, approve, or reject dealer claims related to vehicle bookings and registrations.

The application is deployed at the path `/bsvi` on the TVS iQube production infrastructure and communicates with a .NET backend API for all data operations.

---

## 2. Module Summary

| Module | Description |
|--------|-------------|
| **Area Accountant Dashboard** | Main claims management interface with tabbed views: Claims For Approval, Approved Claims, Rejected Claims, Settled Claims, One View |
| **TRV Dashboard** | Vehicle registration verification claims — approve/reject with document viewing and SAP integration |
| **Export Document** | Export filtered claim data to downloadable files (CSV) |
| **Authentication (SSO)** | Microsoft corporate SSO-based login with JWT session management |
| **Modals** | Shared modal components for Approve, Reject, Upload, ViewMore, SapDetails, and Document viewing |
| **State Management (Stores)** | MobX-based stores managing application state, API communication, and business logic |

---

## 3. Folder Structure

```
customerbay/
├── public/                         # Static assets (index.html, favicon, manifest)
├── src/
│   ├── App.js                      # Root component — Layout, Toolbar, SelectedComponent
│   ├── App.css                     # Global styles
│   ├── components/
│   │   ├── stores/                 # MobX state management layer
│   │   │   ├── AppStore.js         # Central app state, auth, navigation, session
│   │   │   ├── LoginStore.js       # Authentication logic (username/password)
│   │   │   ├── APIProxy.js         # HTTP client wrapper (fetch + axios)
│   │   │   ├── APIEndpoints.js     # Backend URL configuration
│   │   │   ├── TRVStore.js         # TRV claims state management
│   │   │   ├── Util.js             # Utility functions
│   │   │   └── menus/              # Role-based navigation menu JSON configs
│   │   │       ├── GuestMenu.json
│   │   │       ├── areaAccountant.json
│   │   │       └── amtm.json
│   │   ├── areaAccountant/         # Area Accountant business module
│   │   │   ├── AADashboardUI.js    # Dashboard with tabbed claim views
│   │   │   ├── CriteriaForm.js     # Search/filter criteria form
│   │   │   ├── TransactionReport.js# Claims for approval (AG Grid)
│   │   │   ├── RejectedList.js     # Rejected claims grid
│   │   │   ├── SettledClaims.js    # Settled claims grid
│   │   │   ├── OneView.js          # All claims combined view
│   │   │   ├── bookingStatus/      # Booking list component + store
│   │   │   │   ├── BookingList.js
│   │   │   │   └── BookingListStore.js
│   │   │   └── exportFile/         # Export functionality
│   │   │       ├── ExportDocument.js
│   │   │       └── ExportFileStore.js
│   │   ├── TRVDetails/             # TRV module
│   │   │   ├── TRVDashboard.js     # TRV claims dashboard
│   │   │   ├── ClaimTable.js       # Claims data table component
│   │   │   ├── ClaimVehicleDetailsModal.js
│   │   │   └── DetailsPopup.js
│   │   ├── Modals/                 # Shared modal components
│   │   │   ├── ApproveModal.js
│   │   │   ├── ApproveAllModal.js
│   │   │   ├── RejectModal.js
│   │   │   ├── DocumentModal.js
│   │   │   ├── ViewMoreModal.js
│   │   │   ├── SapDetailsModal.js
│   │   │   ├── UploadForm.js
│   │   │   └── ModalStore.js
│   │   ├── LoginUI.js              # Login page layout
│   │   ├── SignIn.js               # SSO sign-in component
│   │   ├── SelectedComponent.js    # Component router/switcher
│   │   ├── ToolBar.js              # Top navigation bar
│   │   ├── About.js                # About page
│   │   ├── Registration.js         # User registration
│   │   └── PasswordReset.js        # Password reset
│   └── util/                       # Shared utilities (Style, Util)
├── config-overrides.js             # Webpack customization (decorators, ESLint disabled)
├── package.json                    # Dependencies and scripts
├── Area-Accountant-Prod-CD.yaml    # CI/CD pipeline (Azure DevOps)
├── Area-Accountant-UI-prod-ci.yaml # CI pipeline
└── Prod-PR.yaml                    # PR validation pipeline
```

---

## 4. Core Business Workflows

### 4.1 Claim Approval Workflow (Area Accountant Dashboard)
1. User searches claims using criteria (dealer code, date range, customer info, CCAvenue ID)
2. Claims are displayed in AG Grid tables across tabs
3. Area Accountant reviews claim details, invoice documents, and insurance documents
4. Approves or rejects individual claims (or bulk approve selected)
5. Approved claims move to "Approved Claims" tab; rejected claims to "Rejected Claims"
6. Settled claims (processed by SAP) appear in "Settled Claims" tab

### 4.2 TRV Claims Workflow
1. User searches by dealer ID, branch, and date range
2. System fetches claims from backend with status mapping (pending/approved/rejected)
3. User views vehicle details including uploaded documents (RC, Insurance, HSRP)
4. Approves or rejects claims — sends request to SAP via `sap/claim-request` endpoint
5. Claims are deduplicated using NORM_ID from backend

### 4.3 Export Workflow
1. User selects search criteria and export type (Claims For Approval, Approved, Rejected, Settled, All)
2. System sends export request to backend
3. User downloads exported file from "Export Dashboard" tab

### 4.4 Authentication Flow
1. User clicks "Sign in with SSO" → redirected to backend SSO endpoint
2. Backend authenticates via Microsoft corporate identity
3. On success, redirects back to app with session cookie
4. App fetches user data and JWT token from backend
5. Token stored in localStorage; auto-logout on expiry

---

## 5. Key Services and Classes

| Service/Class | Responsibility |
|---------------|----------------|
| `AppStore` | Central application state — credentials, navigation, session management, menu resolution, SSO flow |
| `BookingListStore` | Fetches and manages booking claims with pagination, approve/reject actions, URL construction |
| `TRVStore` | TRV claims CRUD, vehicle details fetching, document download, approve/reject via SAP |
| `ModalStore` | Modal visibility state management, SAP data fetching, TDR data retrieval |
| `ExportFileStore` | File export request management and status tracking |
| `LoginStore` | Username/password authentication (validates role = 3 for Area Accountant) |
| `APIProxy` | HTTP abstraction layer — GET, POST, blob download, file upload with auth token injection |

---

## 6. Dependency Overview

### Production Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| React | ^17.0.2 | UI framework (class components) |
| MobX | ^6.4.1 | Reactive state management |
| mobx-react | ^7.3.0 | MobX-React bindings |
| antd | ^4.18.8 | UI component library (Ant Design) |
| ag-grid-react | ^27.0.1 | Data grid for claims tables |
| axios | ^1.2.4 | HTTP client (file uploads) |
| jwt-decode | ^4.0.0 | JWT token parsing for session timeout |
| moment | (via antd) | Date manipulation |
| @ant-design/charts | ^1.3.6 | Data visualization |
| react-player | ^2.9.0 | Video player component |

### Dev Dependencies
| Package | Purpose |
|---------|---------|
| react-app-rewired | Custom webpack configuration without ejecting |
| customize-cra | Webpack override utilities |
| @testing-library/react | Testing utilities |

---

## 7. Runtime Flow

```
Browser → App.js (Layout + Toolbar + SelectedComponent)
              ↓
         AppStore (MobX) ← SSO/Login → Backend Auth
              ↓
         SelectedComponent (switch on currentComponent.key)
              ↓
    ┌─────────────────────────────────────────┐
    │  AADashboard  │  TRVDashboard  │  Export │
    └─────────────────────────────────────────┘
              ↓
         Store Actions → APIProxy → Backend API
              ↓
         MobX Observable Update → Component Re-render
```

### Entry Points
- `src/index.js` → `src/App.js` → `SelectedComponent.js`
- Landing page determined by role-based menu JSON (`isLandingPage: true`)
- Guest → Login page
- Area Accountant (role 3) → AADashboard
- AMTM (role 13) → TRVDashboard

---

## 8. Integration Summary

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| .NET Backend API | REST (fetch/axios) | All business data operations |
| Microsoft SSO | OAuth/SAML redirect | Corporate authentication |
| SAP | Via backend endpoint (`sap/claim-request`) | Claim approval/rejection processing |
| CCAvenue | Reference data | Payment gateway tracking IDs |
| AWS S3 | Deployment | Static asset hosting |
| Azure DevOps | CI/CD | Build and deployment pipelines |
| TVS BSVI Document Server | File hosting | Invoice and insurance document storage |

---

## 9. Important Notes

- The application uses **class-based React components** throughout (no hooks or functional components for main views)
- Navigation is handled via a custom component switcher (`SelectedComponent.js`), not React Router
- State is passed via props from `AppStore` — no React Context or dependency injection
- The backend API base URL is hardcoded in `APIEndpoints.js`
- No `.env` file is used — all configuration is in source code
- Build uses `react-app-rewired` with legacy decorators enabled and ESLint disabled

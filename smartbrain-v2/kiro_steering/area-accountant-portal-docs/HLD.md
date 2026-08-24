# High Level Design (HLD) — TVS CustomerBay

## 1. Architecture Diagram Description

The TVS CustomerBay application follows a **Single Page Application (SPA)** architecture with a clear separation between the frontend React client and the backend .NET API services.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                               │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    React SPA (CustomerBay)                     │  │
│  │                                                               │  │
│  │  ┌─────────┐  ┌──────────────┐  ┌──────────────────────────┐│  │
│  │  │ToolBar  │  │SelectedComp  │  │  MobX Stores             ││  │
│  │  │(Nav)    │  │(Router)      │  │  ├─ AppStore              ││  │
│  │  └─────────┘  └──────────────┘  │  ├─ BookingListStore      ││  │
│  │                                   │  ├─ TRVStore             ││  │
│  │                                   │  ├─ ExportFileStore      ││  │
│  │                                   │  └─ ModalStore           ││  │
│  │                                   └──────────────────────────┘│  │
│  │                         │                                     │  │
│  │                    ┌────┴────┐                                │  │
│  │                    │APIProxy │                                │  │
│  │                    └────┬────┘                                │  │
│  └─────────────────────────┼─────────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────────┘
                             │ HTTPS (JWT Token in Header)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVICES                                │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           .NET Web API (iqubeprod.tvsmotor.com/BS)            │   │
│  │                                                              │   │
│  │  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐   │   │
│  │  │AreaAccountant  │  │  TRV API     │  │  Auth/SSO      │   │   │
│  │  │ Controller     │  │  Controller  │  │  Controller    │   │   │
│  │  └───────┬────────┘  └──────┬───────┘  └───────┬────────┘   │   │
│  │          │                   │                   │            │   │
│  │  ┌───────┴───────────────────┴───────────────────┴────────┐  │   │
│  │  │                   Business Logic Layer                  │  │   │
│  │  └───────┬───────────────────┬───────────────────┬────────┘  │   │
│  │          │                   │                   │            │   │
│  │  ┌───────┴────┐     ┌───────┴────┐     ┌───────┴────────┐   │   │
│  │  │  Database  │     │  SAP System │     │ Microsoft SSO  │   │   │
│  │  └────────────┘     └────────────┘     └────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │         Document Storage (TVSBSVIApp)                         │   │
│  │         Invoice & Insurance Documents                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Major Components/Services

### 2.1 Frontend Components

| Component | Responsibility |
|-----------|---------------|
| **App.js** | Root layout — initializes AppStore, renders Toolbar and SelectedComponent |
| **SelectedComponent** | Custom component router — switches views based on `currentComponent.key` |
| **AADashboardUI** | Area Accountant dashboard — tabbed interface for claim management |
| **TRVDashboard** | TRV claims management — search, view, approve/reject |
| **ExportDocument** | File export management interface |
| **SignIn** | SSO login interface |
| **APIProxy** | Centralized HTTP client with authentication header injection |

### 2.2 Backend Services (External)

| Service | Base URL | Purpose |
|---------|----------|---------|
| Area Accountant API | `/api/areaAccountant/` | Booking claims CRUD, approval, export |
| TRV API | `/api/TRV/` | TRV claims, vehicle details, document download |
| SAP API | `/api/sap/` | Claim approval/rejection to SAP system |
| Auth/SSO API | `/auth/sso/` | Microsoft SSO authentication and token management |

---

## 3. Service Interaction

```
┌──────────┐     ┌──────────────┐     ┌─────────────────┐
│  Browser │────▶│  React SPA   │────▶│  .NET Backend   │
│          │◀────│  (APIProxy)  │◀────│  API            │
└──────────┘     └──────────────┘     └────────┬────────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        │                      │                      │
                        ▼                      ▼                      ▼
                 ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
                 │  Database   │      │  SAP System  │      │  Microsoft   │
                 │  (SQL)      │      │              │      │  Identity    │
                 └─────────────┘      └──────────────┘      └──────────────┘
```

### Request Flow
1. **User Action** → React Component triggers Store action
2. **Store Action** → Calls `APIProxy` method (getAsync, post, asyncPost, getBlob)
3. **APIProxy** → Constructs request with auth headers (`Token: JWT`) and sends to backend
4. **Backend** → Processes request, interacts with DB/SAP, returns JSON response
5. **Store** → Updates MobX observables with response data
6. **Component** → Re-renders via MobX observer pattern

---

## 4. Infra Topology

```
┌─────────────────────────────────────────────────────────┐
│                    TVS Infrastructure                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  iqubeprod.tvsmotor.com                          │    │
│  │                                                 │    │
│  │  /bsvi/          → React SPA (Static Files)    │    │
│  │  /BS/api/        → .NET Backend API             │    │
│  │  /TVSBSVIApp/    → Document Storage             │    │
│  │  /CustomerBayApi/ → Legacy API (commented out)  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────┐  ┌────────────────────────┐   │
│  │  UAT Environment    │  │  AWS S3 (Deployment)   │   │
│  │  uat-bookingapi.    │  │  s3://krust.krscode.com│   │
│  │  tvsmotor.net       │  └────────────────────────┘   │
│  └─────────────────────┘                                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Azure DevOps (CI/CD Pipelines)                  │    │
│  │  - Area-Accountant-Prod-CD.yaml                 │    │
│  │  - Area-Accountant-UI-prod-ci.yaml              │    │
│  │  - Prod-PR.yaml                                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Deployment Flow

```
Developer → Git Push → Azure DevOps PR Pipeline (Prod-PR.yaml)
                              │
                              ▼ (PR Approved)
                    CI Pipeline (Area-Accountant-UI-prod-ci.yaml)
                              │
                              ▼ (Build: react-app-rewired build)
                    CD Pipeline (Area-Accountant-Prod-CD.yaml)
                              │
                              ▼
                    Deploy to Production Server
                    (iqubeprod.tvsmotor.com/bsvi)
```

### Build Process
1. `react-app-rewired build` — Compiles React app with custom webpack config
2. Source maps disabled (`GENERATE_SOURCEMAP=false`)
3. Output to `build/` directory
4. Deployed to hosting infrastructure (AWS S3 or direct server)

---

## 6. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **MobX over Redux** | Simpler API with decorators, less boilerplate for observable state; fits class-based component pattern |
| **Class components over Hooks** | Project initiated before hooks maturity; MobX decorator pattern integrates naturally with classes |
| **Custom component router over React Router** | Simpler navigation model with menu-driven switching; no URL-based routing needed for internal portal |
| **react-app-rewired over eject** | Enables decorator support and ESLint override without ejecting CRA and losing upgrade path |
| **AG Grid for data tables** | Enterprise-grade grid with built-in pagination, sorting, selection — needed for large claim datasets |
| **Ant Design for UI** | Comprehensive component library with built-in form validation, modals, notifications |
| **JWT in localStorage** | Simplicity for internal portal; SSO-based auth reduces token exposure risk |
| **Single backend host** | All API traffic routes through one .NET API gateway; backend handles SAP/DB orchestration |
| **No .env files** | Configuration baked into source (`APIEndpoints.js`); environment switching via code comments |
| **Server-side pagination** | Claims data can be large; client cannot hold full dataset in memory |

---

## 7. Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| **API Communication** | Try/catch around all fetch calls; state set to ERROR on failure; empty arrays prevent UI crashes |
| **User Notifications** | Ant Design `notification` and `message` components for success/error feedback |
| **SSO Failures** | Modal.error with descriptive message; clear session flags; redirect to login |
| **Session Expiry** | `setInterval` checks JWT `exp` claim; auto-logout and page reload on expiry |
| **Document Downloads** | HTTP status-specific error messages (404, 401, 500); empty blob detection |
| **Form Validation** | Client-side validation before API call (criteria check, remark length, required fields) |
| **Graceful Degradation** | Missing data fields render as empty/N/A; null-safe access patterns throughout |
| **No Global Error Boundary** | Errors are handled per-component/per-store; no React Error Boundary wrapper |

---

## 8. External Integrations

| External System | Protocol | Purpose |
|-----------------|----------|---------|
| **Microsoft Identity Platform** | OAuth 2.0 / SAML | Corporate SSO authentication |
| **SAP** | REST (via backend) | Claim processing and capitalization |
| **CCAvenue** | Reference only | Payment gateway — tracking IDs used for search |
| **TVS Document Server** | HTTPS (file download) | Invoice and insurance document storage |
| **Azure DevOps** | CI/CD | Build, test, and deployment automation |

---

## 9. Authentication and Authorization Flow

### SSO Authentication Sequence
```
┌────────┐     ┌──────────┐     ┌──────────────┐     ┌─────────────┐
│ Browser │     │ React App│     │ Backend API  │     │ Microsoft   │
│         │     │          │     │              │     │ Identity    │
└────┬────┘     └────┬─────┘     └──────┬───────┘     └──────┬──────┘
     │               │                   │                     │
     │  Click SSO    │                   │                     │
     │──────────────▶│                   │                     │
     │               │  Set ssoLogin=1   │                     │
     │               │  Redirect to      │                     │
     │◀──────────────│  /auth/sso/login  │                     │
     │                                   │                     │
     │  GET /auth/sso/login?returnUrl    │                     │
     │──────────────────────────────────▶│                     │
     │                                   │  Redirect to MS     │
     │◀──────────────────────────────────│────────────────────▶│
     │                                   │                     │
     │  User authenticates with MS       │                     │
     │──────────────────────────────────────────────────────▶│
     │                                   │  Auth callback      │
     │◀──────────────────────────────────│◀────────────────────│
     │                                   │                     │
     │  Redirect to /bsvi               │                     │
     │◀──────────────────────────────────│                     │
     │               │                   │                     │
     │  App loads    │                   │                     │
     │──────────────▶│                   │                     │
     │               │  GET /auth/sso/   │                     │
     │               │  ssologin         │                     │
     │               │──────────────────▶│                     │
     │               │  {email, role}    │                     │
     │               │◀──────────────────│                     │
     │               │                   │                     │
     │               │  GET /auth/sso/   │                     │
     │               │  token            │                     │
     │               │──────────────────▶│                     │
     │               │  {token, id}      │                     │
     │               │◀──────────────────│                     │
     │               │                   │                     │
     │  Dashboard    │                   │                     │
     │◀──────────────│                   │                     │
```

### Role-Based Access Control
| Role ID | Role Name | Access |
|---------|-----------|--------|
| 3 | Area Accountant | Full access: Dashboard + TRV + Export + About |
| 13 | AMTM | Limited: TRV + About only |
| Guest | Unauthenticated | Login page only |

### Session Management
- JWT token stored in `localStorage`
- Token sent as `Token` header on every API request
- Auto-logout triggered when JWT `exp` claim expires
- Session timeout uses `setInterval` to check expiry

---

## 10. Database Interactions

The frontend does not interact with databases directly. All data access is through the .NET backend API. The backend manages:

- **Booking Claims Data** — CRUD operations for vehicle booking claims
- **TRV Claims Data** — Vehicle registration verification records
- **User Authentication Data** — Login credentials and role assignments
- **Document Metadata** — References to uploaded invoice/insurance files
- **Export Requests** — Queued file export jobs and their status

---

## 11. High-Level Sequence Flows

### Claim Approval Flow
```
User → CriteriaForm → BookingListStore.saveCriteria()
                              │
                    ┌─────────┼─────────┐─────────┐─────────┐
                    ▼         ▼         ▼         ▼         ▼
              fetchBookings  fetchTxn  fetchRej  fetchSettled fetchAll
                    │         │         │         │         │
                    ▼         ▼         ▼         ▼         ▼
              APIProxy.getAsync() → Backend → Response
                    │
                    ▼
              MobX Observables Updated → AG Grid Re-renders
                    │
                    ▼
              User clicks Approve/Reject → Modal → APIProxy.asyncPostArray()
                    │
                    ▼
              Backend processes → Notification shown
```

### TRV Claim Flow
```
User → TRVDashboard.handleSearch()
              │
              ▼
       TRVStore.fetchClaims() → APIProxy.asyncPost('TRV/GetClaimSubmissions')
              │
              ▼
       Claims mapped with status (pending/approved/rejected)
       Deduplicated by NORM_ID
              │
              ▼
       User clicks View → TRVStore.openVehicleDetailsModal()
              │                    → APIProxy.asyncPost('TRV/GetExistingTrvVehicles')
              ▼
       User clicks Approve → TRVStore.approveClaim()
              │                    → APIProxy.asyncPost('sap/claim-request')
              ▼
       Claims list updated → UI re-renders
```

---

## 12. Scalability and Resiliency Considerations

### Current Design
- **Pagination**: All claim lists use server-side pagination (20 items per page)
- **Debouncing**: Page change API calls are debounced (400ms) to prevent rapid-fire requests
- **Client-side filtering**: TRV claims fetched in bulk (action_type=4) and filtered on frontend
- **Deduplication**: TRV claims deduplicated by NORM_ID to handle backend duplicates

### Considerations for Scale
- **No caching layer**: Every search triggers fresh API calls; consider adding request caching
- **No retry logic**: API failures result in empty state; consider exponential backoff
- **Single API endpoint**: All traffic routes through one backend host; consider load balancing
- **LocalStorage dependency**: Session data in localStorage; consider secure cookie-based sessions
- **No WebSocket/SSE**: Real-time updates require manual refresh; consider push notifications for claim status changes

### Resiliency Patterns
- **Graceful degradation**: Empty arrays returned on API failure (no crash)
- **Error notifications**: User-facing error messages via Ant Design notifications
- **Session recovery**: Credentials persisted in localStorage; restored on page reload
- **Fallback data**: Vehicle details modal falls back to claim data if API fails

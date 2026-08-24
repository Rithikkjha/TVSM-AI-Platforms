# Low Level Design (LLD) — TVS CustomerBay

## 1. Detailed Module Breakdown

### 1.1 Authentication Module

| File | Responsibility |
|------|---------------|
| `SignIn.js` | Renders SSO login button, handles redirect to backend SSO endpoint |
| `LoginUI.js` | Login page layout with background image and SignIn component |
| `LoginStore.js` | Username/password authentication logic (POST to `login` endpoint) |
| `AppStore.js` (auth methods) | SSO flow orchestration, session persistence, token management |

### 1.2 Area Accountant Module

| File | Responsibility |
|------|---------------|
| `AADashboardUI.js` | Main dashboard — initializes stores, renders tabs with claim views |
| `CriteriaForm.js` | Search form with dealer code, customer info, date range, dealer type |
| `TransactionReport.js` | AG Grid for "Claims For Approval" with approve/reject actions |
| `BookingList.js` | AG Grid for "Approved Claims" |
| `RejectedList.js` | AG Grid for "Rejected Claims" |
| `SettledClaims.js` | AG Grid for "Settled Claims" |
| `OneView.js` | AG Grid showing all claims combined |
| `BookingListStore.js` | State management for all claim data, pagination, approve/reject |

### 1.3 TRV Module

| File | Responsibility |
|------|---------------|
| `TRVDashboard.js` | Search form + tabbed claim views (Pending, Approved, Rejected, One View) |
| `ClaimTable.js` | Reusable table component for TRV claims |
| `ClaimVehicleDetailsModal.js` | Modal showing vehicle details and uploaded documents |
| `DetailsPopup.js` | Popup for additional claim details |
| `TRVStore.js` | State management — claims CRUD, vehicle details, SAP integration |

### 1.4 Export Module

| File | Responsibility |
|------|---------------|
| `ExportDocument.js` | Export dashboard UI — shows export requests and download links |
| `ExportFileStore.js` | Export request logic — payload construction, API calls |

### 1.5 Modal Module

| File | Responsibility |
|------|---------------|
| `ModalStore.js` | Centralized modal state — open/close, data, SAP/TDR fetching |
| `ApproveModal.js` | Single claim approval confirmation |
| `ApproveAllModal.js` | Bulk approval confirmation |
| `RejectModal.js` | Rejection with reason input |
| `DocumentModal.js` | Document viewer (invoice/insurance) |
| `ViewMoreModal.js` | Extended claim details view |
| `SapDetailsModal.js` | SAP processing details |
| `UploadForm.js` | File upload interface |

---

## 2. Class/Service Responsibilities

### 2.1 AppStore (Central State Manager)

```
AppStore
├── Properties
│   ├── state: string (init|pending|invalid|done|error)
│   ├── credentials: {email, token, role, username, id, loginId, authToken}
│   ├── currentComponent: {label, key, params}
│   ├── menus: Array<MenuItem>
│   ├── isLoggin: boolean
│   ├── apiProxy: APIProxy
│   ├── loginStore: LoginStore
│   └── exportFileStore: ExportFileStore
│
├── Authentication Methods
│   ├── authenticate(values) → POST login, set credentials
│   ├── setSessionFromSso() → GET /auth/sso/ssologin + /auth/sso/token
│   ├── setSessionFromStorage() → Restore from localStorage
│   ├── setSessionTimeout() → Auto-logout on JWT expiry
│   └── logout() → Clear localStorage, reload page
│
├── Navigation Methods
│   ├── resolveMenu() → Load role-based menu JSON
│   ├── resolveLandingPage() → Set initial component
│   ├── navigateTo(index) → Switch to menu item by index
│   └── transitionTo(key) → Switch to component by key name
│
└── Utility Methods
    ├── updateContext() → Update API headers + resolve menu/landing
    ├── persistCredentials() → Save to localStorage
    └── isLoggedIn() → Check if email and token are non-blank
```

### 2.2 BookingListStore (Claims Data Manager)

```
BookingListStore
├── Properties
│   ├── bookings, transactions, rejectedRecords, settledRecords, allBookings: Array
│   ├── *PageNo: number (pagination state per tab)
│   ├── *Count: number (total counts per tab)
│   ├── criteria: object (current search criteria)
│   ├── selectedItems: Array (for bulk approve)
│   └── state: string (init|pending|done|error)
│
├── Fetch Methods
│   ├── saveCriteria(criteria) → Reset pages, fetch all tabs
│   ├── fetchbookings(criteria) → GET bookings (approved)
│   ├── fetchTransactions(criteria) → GET TransactionReport (for approval)
│   ├── fetchRejected(criteria) → GET rejected
│   ├── fetchSettled(criteria) → GET settledClaims
│   ├── fetchAllData(criteria) → GET allBookings
│   └── getCount(url) → GET TransactionReportCount
│
├── Action Methods
│   ├── approveBooking(booking) → POST Approved (single)
│   ├── approveAll() → POST Approved (bulk)
│   ├── rejectBooking(booking) → POST Reject
│   └── onPageChange(type, pageNo) → Debounced pagination
│
└── Utility Methods
    ├── makeUrl(criteria, type) → Construct query string URL
    ├── seprateBooking(bookings) → Split full payment bookings
    ├── seprateTransaction(bookings) → Split transaction records
    ├── filterVisibleClaims(claims) → Filter by DisplayFlag
    └── isClaimBlockedForDisplay(claim) → Check DisplayFlag === 0
```

### 2.3 TRVStore (TRV Claims Manager)

```
TRVStore
├── Properties
│   ├── dealerId, dealershipName, branchId, branchName: string
│   ├── branchOptions: Array<{branchId, branchName}>
│   ├── dateRange: [startDate, endDate]
│   ├── claims, filteredClaims: Array
│   ├── activeTab: string ('1'|'2'|'3'|'4')
│   ├── vehicleDetailsData: object (modal data)
│   ├── isVehicleDetailsModalOpen, isRejectModalOpen: boolean
│   ├── approvingClaims, rejectingClaims: Map (loading state per claim)
│   └── isApprovingClaim: boolean (full-screen loader)
│
├── Search Methods
│   ├── fetchDealerDetails() → POST TRV/branches
│   ├── fetchClaims() → POST TRV/GetClaimSubmissions
│   └── filterClaims() → Client-side filter by activeTab
│
├── Action Methods
│   ├── approveClaim(claim, onSuccess, onError) → POST sap/claim-request (REQUEST_TYPE=1)
│   ├── rejectClaim(claim, onSuccess, onError) → POST sap/claim-request (REQUEST_TYPE=0)
│   └── downloadDocument(vehicleId, type, fileName) → GET TRV/download-file/{id}/{type}
│
├── Vehicle Details Methods
│   ├── openVehicleDetailsModal(claim) → Fetch + show vehicle details
│   ├── closeVehicleDetailsModal() → Reset + hide
│   └── fetchVehicleDetailsForClaim(claim) → POST TRV/GetExistingTrvVehicles
│
└── Utility Methods
    ├── mapStatus(capitalizationStatus, claimStatus) → Convert numeric to string
    ├── isClaimApproving(id), isClaimRejecting(id), isClaimProcessing(id)
    └── setDealerId, setDateRange, setBranchName, setActiveTab, setRejectRemark
```

### 2.4 APIProxy (HTTP Client)

```
APIProxy
├── Properties
│   └── authHeaders: {token, email, userFuzzyId, loginId, authToken}
│
├── Methods
│   ├── updateCredentialHeaders(credentials) → Set auth headers
│   ├── getAsync(url, type?) → GET with Token header
│   ├── post(url, data) → POST with JSON body (returns parsed JSON)
│   ├── asyncPost(url, bodyParams) → POST with loginId injection
│   ├── asyncPostArray(url, bodyParams) → POST array with loginId per item
│   ├── asyncPostFile(url, formData) → POST multipart (axios)
│   └── getBlob(url, data?) → GET binary file with filename extraction
│
└── URL Routing Logic
    └── TRV/SAP endpoints: Remove '/areaAccountant' from base URL
```

---

## 3. API Flow Details

### 3.1 Search Claims (Area Accountant)

```
CriteriaForm.onFinish(values)
    │
    ├── Parse criteria: dateType, rangeDate, dealerCode, dealerType, ccAvenue, userData
    ├── Format dates: YYYY/MM/DD
    ├── Detect userData type: email | name | number (via inputSperator utility)
    ├── Validate: at least one non-date field must be filled
    │
    └── BookingListStore.saveCriteria(criteria)
            │
            ├── Reset all page numbers to 1
            ├── fetchbookings(criteria)     → GET bookings?dateType=X&startDate=X&endDate=X&...&pageNo=1&pageSize=20
            ├── fetchTransactions(criteria)  → GET TransactionReport?...
            ├── fetchRejected(criteria)     → GET rejected?...
            ├── fetchSettled(criteria)      → GET settledClaims?...
            └── fetchAllData(criteria)      → GET allBookings?...
```

### 3.2 TRV Claim Search

```
TRVDashboard.handleSearch()
    │
    └── TRVStore.fetchClaims()
            │
            ├── Construct payload:
            │   {
            │     fromDate: "YYYY-MM-DDTHH:mm:ss.SSSZ",
            │     toDate: "YYYY-MM-DDTHH:mm:ss.SSSZ",
            │     action_Type: 4,          // Always fetch all
            │     dealerId?: string,        // Optional
            │     branchId?: string         // Optional
            │   }
            │
            ├── POST TRV/GetClaimSubmissions
            │
            ├── Deduplicate by NORM_ID (norM_ID | NORM_ID | norm_id)
            │
            ├── Map each claim:
            │   - id: normId || composite key
            │   - status: mapStatus(capitalization_Status, claim_Status)
            │   - Dates formatted: DD-MM-YYYY
            │
            └── filterClaims() → Filter by activeTab (pending|approved|rejected|all)
```

### 3.3 Approve/Reject TRV Claim

```
TRVStore.approveClaim(claim) / rejectClaim(claim)
    │
    ├── Set loading state (approvingClaims/rejectingClaims Map)
    │
    ├── Construct payload:
    │   {
    │     REQUEST_TYPE: 1 (approve) | 0 (reject),
    │     NORM_ID: claim.normId,
    │     dealerId, branchId, dealershipName, branchName,
    │     brandName, variant, frameNo, invoiceNo, invoiceDate,
    │     registrationNo, percentageSupport, reimbursement,
    │     remark, firstTrancheAmount, netBillingPrice,
    │     status, createdOn, approvedDate, rejectedDate, igst
    │   }
    │
    ├── POST sap/claim-request
    │
    ├── On success: Update claim status in local array, re-filter
    └── On error: Show error notification
```

---

## 4. Internal Component Interactions

```
App.js
  │
  ├── Creates AppStore (singleton for app lifecycle)
  ├── Calls appStore.setSessionFromSso() on mount
  │
  ├── Renders ToolBar (receives appStore)
  │   └── Displays menus, handles navigation via appStore.navigateTo()
  │
  └── Renders SelectedComponent (receives appStore)
      │
      ├── switch(currentComponent.key)
      │   ├── 'AADashboard' → AADashboardUI
      │   │   ├── Creates BookingListStore (new per mount)
      │   │   ├── Creates ModalStore (new per mount)
      │   │   ├── Uses appStore.exportFileStore (shared)
      │   │   └── Renders: CriteriaForm, TransactionReport, BookingList, etc.
      │   │
      │   ├── 'TRVDashboard' → TRVDashboard
      │   │   ├── Creates TRVStore (new per mount)
      │   │   └── Renders: Search form, ClaimTable, Modals
      │   │
      │   ├── 'DocumentExport' → ExportDocument
      │   │   └── Uses appStore.exportFileStore (shared)
      │   │
      │   └── 'login' → LoginUI → SignIn
      │
      └── Store → Component data flow via MobX @observer
```

---

## 5. Database Schema Usage

The frontend does not directly access the database. Data structures inferred from API responses:

### Booking/Claim Record (Area Accountant)
```
{
  dealerCode: string,
  dealerType: string,
  customerName: string,
  customerEmail: string,
  customerMobile: string,
  model: string,
  variant: string,
  color: string,
  vehicleType: string (EV|ICE|BTO),
  invoiceNumber: string,
  invoiceFileName: string,
  insuranceNumber: string,
  insuranceFileName: string,
  partialPaymentAmount: number,
  fullPaymentAmount: number,
  partialCCARefNumber: string,
  fullPaymentCcarefTransactionNumber: string,
  partialPayoutId: string,
  fullPaymentPayoutId: string,
  bookingDate: datetime,
  invoiceUploadDate: datetime,
  documentStatus: number (0=pending, 1=initiated, 2=processed),
  uuid: string,
  amdMapping: string,
  DisplayFlag: number (0=hidden, 1=visible),
  fullPaymentDocMessage: string,
  fullPaymentDocNo: string,
  fullPaymentDocDate: string
}
```

### TRV Claim Record
```
{
  norM_ID: number (unique identifier),
  dealerId: number,
  branchId: number,
  dealershipName: string,
  branchName: string,
  brandName: string,
  variant: string,
  frameNo: string,
  invoiceNo: string,
  invoiceDate: datetime,
  registrationNo: string,
  netBillingPrice: number,
  percentageSupport: number,
  reimbursement: number,
  firstTrancheAmount: number,
  remark: string,
  claim_Status: number (0=DocPending, 1=ClaimSubmitted, 2=ApprovedAO, 3=RejectedAO, 4=DocUploaded),
  capitalization_Status: number (0=DocPending, 1=AreaAccountantApproved, 2=Capitalized, 3=Rejected),
  createdOn: datetime,
  approvedDate: datetime,
  rejectedDate: datetime
}
```

### TRV Vehicle Details
```
{
  trvDetailId: number,
  brandName: string,
  variantName: string,
  frameNo: string,
  customerName: string,
  customerPhoneNo: string,
  invoiceNo: string,
  invoiceDate: datetime,
  registrationNo: string,
  registrationDate: datetime,
  hsrpDate: datetime,
  isRCUploaded: boolean,
  rcName: string,
  isInsuranceUploaded: boolean,
  insuranceName: string,
  isHSRPUploaded: boolean,
  hsrpName: string,
  isCompliant: boolean,
  compliantRemark: string
}
```

---

## 6. Request/Response Lifecycle

### Generic API Request Flow
```
1. Component triggers action (user click, form submit)
2. Store method called
3. Store sets state = PENDING
4. APIProxy constructs request:
   - URL: backendHost + endpoint + query params
   - Headers: { Content-Type: application/json, Token: JWT }
   - Body: JSON.stringify(payload + loginId)
5. fetch() / axios call executed
6. Response received:
   - Success: Parse JSON, update MobX observables, state = DONE
   - Error: Set state = ERROR, show notification
7. MobX triggers re-render of @observer components
```

### Blob Download Flow (TRV Documents)
```
1. User clicks download button
2. TRVStore.downloadDocument(vehicleId, documentType, fileName)
3. APIProxy.getBlob('TRV/download-file/{id}/{type}')
4. Response: Binary blob + Content-Disposition header
5. Create object URL from blob
6. Create temporary <a> element with download attribute
7. Trigger click → browser downloads file
8. Cleanup: revoke object URL, remove element
```

---

## 7. Validation Logic

### CriteriaForm Validation
- At least one non-date field must be filled (dealer code, customer info, or CCAvenue)
- `criteriaCheck()` iterates criteria keys, skips `dateType` and `rangeDate`
- Shows Alert component if validation fails

### TRV Reject Validation
- Remark is required (non-empty after trim)
- Maximum 250 characters (truncated with warning notification)

### Input Type Detection (`inputSperator` utility)
- Contains `@` → email
- All digits → number (mobile)
- Otherwise → name (customer name)

### Approve Button Visibility (TransactionReport)
- Only shown if both `invoiceFileName` AND `insuranceFileName` exist
- Disabled if `documentStatus === 1` (already initiated)

### Row Selection Rules (AG Grid)
- Row selectable only if: `insuranceFileName` AND `invoiceFileName` exist AND `documentStatus` is 0, null, or 2

---

## 8. Error Handling

### API Error Patterns
```javascript
// Pattern 1: State-based error handling
try {
  this.state = PENDING;
  const response = await this.apiProxy.getAsync(url);
  const result = await response.json();
  // process result
  this.state = DONE;
} catch (e) {
  this.state = ERROR;
}

// Pattern 2: Notification-based feedback
try {
  let response = await this.apiProxy.asyncPostArray(url, data);
  response = await response.json();
  if (response.status === 200) {
    notification["success"]({ message: response.message });
  } else {
    notification["error"]({ message: "Failed to Approve Booking" });
  }
} catch (e) { }

// Pattern 3: Callback-based (TRV)
this.trvStore.approveClaim(claim,
  (successMessage) => antdMessage.success({ content: successMessage }),
  (errorMessage) => antdMessage.error({ content: errorMessage })
);
```

### SSO Error Handling
- Non-200 response → Modal.error with "Access Denied" message
- Missing email in response → Modal.error with authorization message
- Token fetch failure → Modal.error with redirect to `/bsvi`
- All errors clear `ssoLogin` session flag

### Blob Download Error Handling
- 404 → "File not found on server"
- 401 → "Unauthorized access. Please login again."
- 500 → "Server error occurred. Please try again later."
- Empty blob → "The file appears to be empty on the server"

---

## 9. Key Algorithms/Business Rules

### Status Mapping (TRV Claims)
```javascript
mapStatus(capitalizationStatus, claimStatus) {
  // Primary: claim_Status
  // 0 (DocPending) → 'pending'
  // 1 (ClaimSubmitted) → 'pending'
  // 2 (ClaimApprovedAO) → 'approved'
  // 3 (ClaimRejectedAO) → 'rejected'
  // 4 (DocUploaded) → 'pending'

  // Fallback: capitalization_Status
  // 0 (DocPending) → 'pending'
  // 1 (AreaAccountantApproved) → 'approved'
  // 2 (Capitalized) → 'approved'
  // 3 (Rejected) → 'rejected'
}
```

### Claim Deduplication (TRV)
```javascript
// Uses NORM_ID as primary key
// Fallback: frameNo + claim_Status composite key
const key = normId ? `norm_${normId}` : `${claim.frameNo}_${claimStatusValue}`;
// First occurrence wins (Map-based dedup)
```

### Booking Separation Logic
```javascript
// Bookings with fullPaymentAmount are duplicated:
// - Original record (partial payment)
// - New record with full payment fields mapped to common fields
// This allows both partial and full payments to appear as separate rows
```

### DisplayFlag Filtering
```javascript
// Claims with DisplayFlag === 0 are hidden from all views
// Applied after every fetch via filterVisibleClaims()
```

### AD Claims Detection
```javascript
// Dealer code between 50000-70000 → AD Claim = "Yes"
// Otherwise → "No"
```

---

## 10. Configuration Handling

### API Endpoint Configuration (`APIEndpoints.js`)
```javascript
// Production
const backendHost = 'https://iqubeprod.tvsmotor.com/BS/api/areaAccountant/';

// UAT (commented)
// const backendHost = 'https://uat-bookingapi.tvsmotor.net/BS/api/areaAccountant/';

// Local (commented)
// const backendHost = 'http://localhost:5201/api/areaAccountant/';
```

### Build Configuration (`config-overrides.js`)
```javascript
module.exports = override(
  addDecoratorsLegacy(),  // Enable legacy decorator syntax
  disableEsLint(),        // Disable ESLint during build
);
```

### Application Configuration (`package.json`)
- Homepage: `/bsvi` (sets PUBLIC_URL for asset paths)
- Build tool: `react-app-rewired` (custom webpack without ejecting)
- Deploy: `GENERATE_SOURCEMAP=false` + AWS S3 sync

### Menu Configuration (JSON files)
- `GuestMenu.json` — Login page only
- `areaAccountant.json` — Dashboard, TRV, Export, About
- `amtm.json` — TRV, About

### Document Storage URL
```javascript
// Hardcoded in TransactionReport.js
const url = `https://iqubeprod.tvsmotor.com/TVSBSVIApp/${fileType}%20Documents/${fileName}`;
```

---

## 11. Testing Strategy

### Test Framework
| Tool | Purpose |
|------|---------|
| `@testing-library/react` | Component rendering and interaction testing |
| `@testing-library/jest-dom` | DOM assertion matchers |
| `@testing-library/user-event` | Simulating user interactions (clicks, typing) |
| Jest (via CRA) | Test runner, assertions, mocking |

### Test Execution
```bash
# Interactive watch mode (local development)
npm test

# CI mode (non-interactive, single run)
npm test -- --watchAll=false
```

### Testing Approach
| Layer | Strategy |
|-------|----------|
| **Components** | Render with mocked stores; verify UI output and user interactions |
| **Stores (MobX)** | Unit test action methods with mocked APIProxy; verify observable state changes |
| **APIProxy** | Mock `fetch`/`axios`; verify correct URL construction, headers, and body |
| **Modals** | Render with props; verify visibility toggling and callback invocations |
| **Integration** | Component + Store interaction; verify end-to-end flows with mocked API |

### Current Coverage Notes
- Test infrastructure is configured but coverage is minimal
- Priority areas for testing: BookingListStore (pagination, approve/reject), TRVStore (status mapping, deduplication), APIProxy (URL routing)
- SSO flow difficult to unit test due to redirect-based authentication
- AG Grid rendering requires AG Grid test utilities or shallow rendering

### Mocking Strategy
- **API calls**: Mock `fetch` globally or per-test using Jest mock functions
- **MobX stores**: Create store instances with mocked APIProxy for isolated testing
- **Browser APIs**: Mock `localStorage`, `sessionStorage`, `window.location` as needed
- **External libraries**: Mock `jwt-decode`, `moment` for deterministic test results

---

## 12. Component Lifecycle and Initialization

### App Initialization Sequence
```
1. App constructor → new AppStore()
2. AppStore constructor → new APIProxy(), new LoginStore(), new ExportFileStore()
3. App.componentDidMount() → appStore.setSessionFromSso()
4. setSessionFromSso():
   a. Check sessionStorage for 'ssoLogin' flag
   b. If flag set: GET /auth/sso/ssologin → GET /auth/sso/token
   c. Set credentials, update context, persist
5. updateContext():
   a. apiProxy.updateCredentialHeaders()
   b. resolveMenu() → Load role-based menu JSON
   c. resolveLandingPage() → Set currentComponent to landing page
6. SelectedComponent renders appropriate view
```

### AADashboard Initialization
```
1. Constructor: Create BookingListStore, ModalStore
2. Reference appStore.exportFileStore (shared instance)
3. No automatic data fetch — waits for user search
```

### TRVDashboard Initialization
```
1. Constructor: Create TRVStore with appStore.apiProxy
2. No automatic data fetch — waits for user search
3. Default date range: last 1 month to today
```

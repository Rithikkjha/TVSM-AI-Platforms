# master-data-platform-frontend


## Product Context


# Product Context — TVS Master Data Platform (Frontend)

## What This Service Does

The Master Data Platform (MDP) frontend is a role-based web application for managing master data records (Dealers, Products, Regions) for TVS Motor Company. It provides data entry, validation, approval workflows, and audit trails with strict team-level data segregation.

Currently operates with mock data; designed for future integration with a backend API.

## Domain Entities

### User
- Fields: username, password, role, name
- Roles: `admin`, `team1`, `team2`, `team3`
- Admin has full cross-team visibility; team users see only their own data

### Master Data Record
- Fields: id, entityType, code, name, region/category/territory (varies by type), team, status, lastUpdated, updatedBy
- Entity types: **Dealer**, **Product**, **Region**
- Status values: `Active`, `Inactive`

### Pending Validation Record
- Fields: id, entityType, code, name, region/category, team, status, submittedBy, submittedOn, validationErrors[]
- Status values: `Pending`, `Validation Failed`

### Audit Log Entry
- Fields: id, timestamp, user, action, entityType, entityCode, details
- Action types: `CREATE`, `UPDATE`, `DELETE`

### Statistics
- Admin stats include teamBreakdown array
- Team stats are scoped to the team's own records

## Integrations

| Integration | Current State | Future State |
|---|---|---|
| Authentication API | Mock (in-memory user list) | `POST /api/auth/login` with JWT |
| Master Data API | Mock (static JS objects) | `GET /api/master-data?team=` |
| Submission API | Mock (client-side alert) | `POST /api/master-data/validate-and-submit` |
| Session Storage | Used for login persistence | Will be replaced by token-based auth |

## Business Rules

### Authentication & Authorization
- Users authenticate with username/password
- Session persists via `sessionStorage` (key: `mdp_user`)
- Routes are protected by role; unauthorized access redirects to `/unauthorized`
- Admin role accesses `/admin`; team roles access `/dashboard`

### Data Segregation
- Team users can only view and submit data belonging to their own team
- Admin can view all data across all teams

### Validation (Pre-Submission)
- All entity types: `code` and `name` are required, no empty strings
- Dealer: `region` is mandatory
- Product: `category` is mandatory
- Region: no additional required fields beyond code/name in current implementation
- Validation errors block submission entirely — invalid data never enters the pending queue

### Approval Workflow
1. Team submits record → frontend validates → enters Pending queue
2. Admin reviews pending records
3. Only records with zero validation errors can be approved
4. Admin can approve (→ production) or reject (→ feedback to team)

### Audit Trail
- All CREATE, UPDATE, DELETE actions are logged
- Admin sees all logs; teams see only their own actions



## Code Structure


# Project Structure — TVS Master Data Platform (Frontend)

## Annotated Directory Layout

```
master-data-platform-frontend/
├── public/                        # Static assets served by CRA dev server
│   ├── index.html                 # HTML shell (root div mount point)
│   ├── favicon.ico
│   ├── manifest.json              # PWA manifest
│   └── robots.txt
├── src/
│   ├── index.js                   # Entry point — renders <App> into DOM
│   ├── App.js                     # Root component — routing + AuthProvider
│   ├── App.css                    # Global app styles
│   ├── index.css                  # Base/reset styles
│   ├── mockData.js                # All mock data (users, records, stats, logs)
│   ├── context/
│   │   └── AuthContext.js         # React Context for auth state (login/logout/user)
│   ├── components/
│   │   └── ProtectedRoute.js      # Route guard — checks auth + role permissions
│   ├── component/                 # ⚠️ Legacy/unused folder
│   │   └── Dashboard.js           # Placeholder component (not wired into app)
│   └── pages/
│       ├── Login.js               # Login form with credential validation
│       ├── Login.css
│       ├── AdminDashboard.js      # Admin panel (5 tabs: overview, data, pending, audit, users)
│       ├── TeamDashboard.js       # Team panel (5 tabs: overview, data, submit, pending, audit)
│       ├── Dashboard.css          # Shared styles for both dashboards
│       ├── Unauthorized.js        # 403 access denied page
│       └── Unauthorized.css
├── package.json                   # Dependencies and scripts
├── package-lock.json
├── FRONTEND_README.md             # Detailed project documentation
├── README.md                      # CRA boilerplate readme
└── .gitignore
```

## Module Dependencies

```
index.js
  └── App.js
        ├── context/AuthContext.js      ← provides auth state to entire tree
        │     └── mockData.js           ← user credentials
        ├── components/ProtectedRoute.js ← consumes AuthContext
        └── pages/
              ├── Login.js              ← consumes AuthContext
              ├── AdminDashboard.js     ← consumes AuthContext + mockData
              ├── TeamDashboard.js      ← consumes AuthContext + mockData
              └── Unauthorized.js       ← standalone (no context dependency)
```

## Architectural Decisions

### Single-Page Application with Client-Side Routing
- React Router v7 handles all navigation
- No server-side rendering; the app is a static SPA bundle

### Context API for State Management
- AuthContext provides `user`, `login()`, `logout()`, `loading` to the component tree
- No external state library (Redux, Zustand, etc.) — app complexity doesn't warrant it

### Mock Data Layer
- All data lives in `src/mockData.js` as exported constants
- Designed for easy swap to API calls (axios is already a dependency)
- Data is keyed by role (`admin`, `team1`, `team2`, `team3`)

### Role-Based Route Protection
- `ProtectedRoute` component wraps protected routes
- Accepts `allowedRoles` prop to declaratively control access
- Redirects unauthenticated users to `/login`, unauthorized to `/unauthorized`

### Flat Page Architecture
- Each dashboard is a single large component with tab-based navigation
- No sub-routing within dashboards; tabs are managed via local `useState`

### Session Persistence
- `sessionStorage` stores serialized user object
- AuthContext rehydrates from storage on mount (handles page refresh)

### Legacy Code
- `src/component/Dashboard.js` is unused and not imported anywhere — likely leftover from initial scaffolding



## Tech Stack & Dependencies


# Tech Stack & Conventions — TVS Master Data Platform (Frontend)

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | React | 19.2.x |
| Routing | react-router-dom | 7.14.x |
| HTTP Client | axios | 1.15.x (installed, not yet used) |
| Build Tool | Create React App (react-scripts) | 5.0.1 |
| Testing | Jest + React Testing Library | @testing-library/react 16.x |
| Linting | ESLint (react-app preset) | Built into CRA |
| Styling | Plain CSS (no preprocessor, no CSS-in-JS) | — |
| Package Manager | npm | — |

## Scripts

```bash
npm start        # Dev server on localhost:3000
npm run build    # Production build to /build
npm test         # Jest in watch mode
npm run eject    # One-way CRA eject (not recommended)
```

## Coding Conventions

### File Organization
- One component per file
- Pages go in `src/pages/` with co-located CSS files
- Shared/reusable components go in `src/components/`
- Context providers go in `src/context/`
- File names use PascalCase for components, camelCase for utilities

### Component Patterns
- Functional components only (no class components)
- React hooks for all state and side effects (`useState`, `useEffect`, `useContext`)
- Custom hooks for shared logic (e.g., `useAuth`)
- Props destructuring in function signature
- Default exports for page/component files

### State Management
- Local state via `useState` for UI concerns (active tab, form fields, search)
- Context API for cross-cutting concerns (auth)
- No prop drilling beyond one level — use context when needed

### Styling
- Plain CSS with class-based selectors
- BEM-like naming in some places (e.g., `stat-card`, `stat-number`, `stat-label`)
- CSS files co-located with their page component
- Shared dashboard styles in `Dashboard.css`
- No utility-first framework (Tailwind, etc.)

### Naming
- Components: PascalCase (`AdminDashboard`, `ProtectedRoute`)
- Variables/functions: camelCase (`handleSubmit`, `searchCode`)
- CSS classes: kebab-case (`login-container`, `data-table`)
- Constants/mock data exports: camelCase (`mockMasterData`, `mockUsers`)

## Patterns

### Authentication Flow
```
Login.js → useAuth().login(username, password)
  → AuthContext validates against mockUsers
  → Stores user in state + sessionStorage
  → Returns { success, user } or { success: false, error }
  → Login.js navigates based on role
```

### Route Protection Pattern
```jsx
<ProtectedRoute allowedRoles={['admin']}>
  <AdminDashboard />
</ProtectedRoute>
```
- Shows loading spinner while auth state initializes
- Redirects to `/login` if not authenticated
- Redirects to `/unauthorized` if role not in `allowedRoles`

### Form Validation Pattern
- Validation runs synchronously on submit (not on blur)
- Errors stored in local state array
- Errors cleared when user modifies any field
- Submission blocked if errors exist
- Uses `alert()` for success/failure feedback (placeholder for proper UX)

### Search Pattern
- Form-based search by entity code
- Exact match (case-insensitive) against in-memory data
- Results displayed inline below search input
- Clear button resets search state

## Error Handling

- **Auth errors**: Displayed inline on login form (`error-message` div)
- **Validation errors**: Rendered as a list above the form (`validation-errors` div)
- **Search misses**: Inline error message below search input
- **No global error boundary** — unhandled errors will show React's default error screen
- **No try/catch around data access** — mock data is always available; will need error handling when API integration happens

## Testing

- Testing Library + Jest configured via CRA
- `src/setupTests.js` imports `@testing-library/jest-dom` for extended matchers
- `src/App.test.js` exists (default CRA smoke test)
- No comprehensive test suite currently — minimal coverage
- Run with `npm test` (interactive watch mode) or `CI=true npm test` (single run)

## Deployment

- **Build**: `npm run build` produces optimized static bundle in `/build`
- **Hosting**: Any static file server (S3, Nginx, Vercel, Netlify)
- **No environment variables** currently configured
- **No CI/CD pipeline** defined in the repository
- **Browser support**: Last 1 version of Chrome, Firefox, Safari (dev); >0.2% market share (prod)

## Known Technical Debt

1. `src/component/Dashboard.js` — unused legacy file, should be removed
2. `alert()` used for user feedback — should be replaced with toast/notification component
3. Large monolithic dashboard components — could be split into smaller tab components
4. No API error handling patterns — needs implementation before backend integration
5. No environment-based configuration (API URLs, feature flags)
6. Hardcoded demo credentials displayed on login page


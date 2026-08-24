# FormBuilder


## Product Context


# Product Overview

## What This Service Does

Checklist Form Builder is an internal platform for TVS Motor that enables admins to design, configure, and publish dynamic forms and checklists (powered by SurveyJS). External users (dealers, field staff) fill and submit these forms — typically vehicle delivery checklists, feedback forms, and quizzes — via an embedded iframe in parent applications.

The app follows a BFF (Backend-for-Frontend) pattern: the Next.js frontend proxies all backend calls through its own API routes, adding authentication headers and APIM subscription keys before forwarding to the `formbuilder-service` microservice.

## Domain Entities

### Template
A form definition containing:
- `templateId` (numeric, external) and `_id` (internal MongoDB ID)
- `templateName` — display name
- `templateJson` — SurveyJS JSON schema defining form structure
- `clientId` / `internalClientId` — owning client
- `configurations` — approval workflow, PDF generation, scoring, theme, draft mode, validation settings

### Submission
A filled form instance:
- `submissionId` — unique identifier
- `templateId` / `internalTemplateId` — reference to source template
- `submittedData` — user responses
- `submissionStatus` — `draft` or `saved`
- `additionalData` — contextual data (enquiryId, bookingId)
- `approver` — assigned approver (if approval workflow enabled)
- `score` — computed score (for quiz-type forms)
- `submittedBy` — user identifier

### Client
An organizational entity that owns templates:
- `clientId` (numeric), `clientName`, `countryCode`

### User (Admin Portal)
- `userName`, `email`, `mobileNumber`
- `role` — one of: `admin`, `designer`, `viewer`, `collaborator`
- `clientLevelAccess` — which clients the user can manage
- `templateLevelAccess` — which templates the user can access
- `isActive` — soft-delete flag

## Integrations

| Integration | Purpose | Details |
|---|---|---|
| **Microsoft Entra ID (MSAL)** | SSO for admin users | `@azure/msal-browser`, tenant-specific authority |
| **Azure API Management** | Backend API gateway | Subscription key via `Ocp-Apim-Subscription-Key` header |
| **Azure Blob Storage** | File uploads | Signed URLs for PDF/image uploads |
| **Firebase Analytics** | Event tracking | Conditionally enabled, tracks submissions, user CRUD, PDF generation, login |
| **SurveyJS** | Form rendering engine | `survey-react-ui` + `surveyjs-widgets` for form display and interaction |
| **formbuilder-service** | Backend microservice | Template CRUD, submission CRUD, user management, PDF generation |
| **Parent App (iframe)** | Embedding host | Communication via `window.top.postMessage` |

## Business Rules

### Authentication & Authorization
- Admin users authenticate via Microsoft SSO (MSAL). Only `@tvsmotor.com` domain emails are accepted.
- External feedback users receive a token via URL query parameters (passed from parent app).
- Tokens are AES-encrypted (CryptoJS) before storing in sessionStorage.
- Expired tokens are silently refreshed via MSAL `acquireTokenSilent`.
- User roles control access: `admin`/`designer` can create/edit forms; `viewer` can only view; `collaborator` has limited access.

### Template Management
- Templates must have a client assigned and a modified name before publishing.
- Templates can be saved (draft in Redis/temp storage) and published (permanent in database).
- Initial template JSON starts with a single empty page titled "Form Builder".

### Form Submission
- File uploads are limited to 10MB, accepted types: `.pdf`, `.jpg`, `.jpeg`, `.png`.
- Draft mode allows saving incomplete submissions for later completion.
- Quiz mode supports time-limited forms that auto-redirect on expiry.
- Checklist questions answered "No" when required trigger validation errors.

### Approval Workflow
- When enabled, submissions require review by an assigned approver.
- Supports per-question comments and a final comment.
- Approver can approve/reject submissions.

### PDF Generation
- Optional per-template configuration.
- Generates and downloads a PDF of the submitted form data.

### Scoring
- Quiz-type templates can compute scores based on correct answers.
- Score is stored with the submission.



## Code Structure


# Codebase Structure

## Annotated Directory Layout

```
/
├── app/                              # Next.js App Router (client-side pages & UI)
│   ├── layout.tsx                    # Root layout: MSAL provider, Redux provider, Firebase init, runtime config loading
│   ├── page.tsx                      # Entry point: routes to feedback or admin login based on URL params
│   ├── providers.tsx                 # Redux Provider wrapper
│   ├── admin/                        # Admin portal pages (protected by withAdminAuth)
│   │   ├── page.tsx                  # Admin dashboard
│   │   └── templatebuilder/          # Form designer pages
│   │       ├── page.tsx              # Template list / create new
│   │       └── [id]/page.tsx         # Edit existing template
│   ├── auth/                         # Unauthorized access page
│   ├── error/                        # Error display page
│   ├── feedback/                     # Form filling pages (protected by withAuth)
│   │   ├── page.tsx                  # Feedback landing
│   │   ├── [templateID]/             # Fill a form by template ID
│   │   │   ├── page.tsx
│   │   │   └── layout.tsx
│   │   └── submission/
│   │       └── [submissionID]/       # View/edit existing submission
│   │           ├── page.tsx
│   │           └── layout.tsx
│   ├── components/                   # React components
│   │   ├── Admin/                    # Admin-specific components
│   │   │   ├── Dashboard.tsx         # Admin dashboard view
│   │   │   ├── Login.tsx             # MSAL SSO login flow
│   │   │   ├── Sidebar.tsx           # Admin navigation sidebar
│   │   │   ├── TemplateBuilder.tsx   # Main form builder orchestrator
│   │   │   ├── NoData.tsx            # Empty state component
│   │   │   ├── FormManagement/       # Form builder sub-components
│   │   │   │   ├── Designer.tsx      # Drag-and-drop form designer
│   │   │   │   ├── Preview.tsx       # Live form preview (SurveyJS)
│   │   │   │   ├── Configuration.tsx # Template settings (approval, PDF, scoring)
│   │   │   │   ├── Theme.tsx         # Theme selection UI
│   │   │   │   ├── ThemeSetting.tsx  # Custom theme configuration
│   │   │   │   ├── JSONEditor.tsx    # Raw JSON editor for template
│   │   │   │   ├── ComponentSetting.tsx  # Per-component property editor
│   │   │   │   ├── FormGrid.tsx      # Template list grid view
│   │   │   │   ├── FormList.tsx      # Template list table view
│   │   │   │   ├── FileManagementSiderbar.tsx  # Component palette sidebar
│   │   │   │   └── FileComponentMobile.tsx     # Mobile component palette
│   │   │   └── UserManagement/       # User CRUD components
│   │   │       ├── AddUser.tsx       # Create/edit user form
│   │   │       ├── UserGrid.tsx      # User grid view
│   │   │       └── UserList.tsx      # User table view
│   │   ├── RenderForms.tsx           # SurveyJS form renderer for feedback
│   │   ├── Header.tsx                # App header
│   │   ├── Footer.tsx                # App footer
│   │   ├── Button.tsx                # Reusable button component
│   │   ├── Loader.tsx                # Loading spinner
│   │   └── svgIcons.jsx              # SVG icon components
│   ├── constants/                    # Application constants
│   │   ├── app.constant.ts           # Central config class (runtime config, messages, roles)
│   │   ├── file-component.constant.tsx       # Form component definitions for designer
│   │   └── file-component-icon.constant.tsx  # Icons for form components
│   ├── hooks/                        # Custom React hooks
│   │   ├── debounce.ts               # Debounce utility hook
│   │   └── use-analytics-log.ts      # Firebase analytics event logger
│   ├── lib/                          # Core libraries and configuration
│   │   ├── authConfig.ts             # MSAL PublicClientApplication setup
│   │   ├── axiosUIInterceptor.ts     # Client-side Axios: token refresh, auth headers
│   │   ├── firebase.ts              # Firebase Analytics initialization
│   │   ├── upload-middleware.ts      # Multer config for file uploads
│   │   └── redux/                    # Redux state management
│   │       ├── store.ts              # Store configuration (feedback + formbuilder slices)
│   │       ├── feedback/
│   │       │   └── feedbackSlice.ts  # State for form filling (template data, submission data)
│   │       └── formbuilder/
│   │           ├── formbuilderSlice.ts  # State for form designer (components, theme, config)
│   │           └── themeConfigs.ts      # Predefined theme definitions
│   ├── types/                        # TypeScript type definitions
│   │   ├── template-builder.ts       # Component, Client, User interfaces
│   │   └── templates.ts             # Template, Configuration, Submission interfaces
│   └── styles/                       # SCSS/CSS stylesheets
│       ├── global.scss
│       └── font.scss
│
├── pages/                            # Next.js Pages Router (API routes only)
│   └── api/                          # BFF proxy layer — all backend communication
│       ├── get-env-config.ts         # Exposes server env vars to client at runtime
│       ├── templates.ts              # GET template by ID
│       ├── save-template-data.ts     # Create submission
│       ├── get-submission-data.ts    # GET submission by ID
│       ├── submission-update.ts      # Update existing submission
│       ├── submission-approval.ts    # Approve/reject submission
│       ├── generate-pdf.ts           # Generate and return PDF
│       ├── get-masterdata.ts         # Fetch master/reference data
│       └── admin/                    # Admin-only API routes
│           ├── login-sso-user.ts     # Validate SSO user against backend
│           ├── get-client.ts         # List clients
│           ├── get-form-list.ts      # List templates (paginated)
│           ├── get-form/             # Get single form details
│           ├── create-template.ts    # Publish new template
│           ├── update-template.ts    # Update existing template
│           ├── delete-form/          # Delete template
│           ├── get-user-list.ts      # List users (paginated)
│           ├── get-user/             # Get single user
│           ├── add-user.ts           # Create user
│           ├── edit-user/            # Update user
│           └── delete-user/          # Delete user
│
├── utils/                            # Shared utilities (used by both app/ and pages/)
│   ├── withAuth.tsx                  # HOC: feedback route guard (checks encrypted token)
│   ├── withAdminAuth.tsx             # HOC: admin route guard (checks loginuser session)
│   ├── interceptors/
│   │   └── axiosInterceptor.ts       # Server-side Axios: strips headers, adds APIM key
│   ├── functions/
│   │   ├── encrypt-decrypt.ts        # AES encrypt/decrypt (CryptoJS)
│   │   ├── server-error-handle.ts    # Centralized API error response handler
│   │   ├── decode-html-entities.ts   # HTML entity decoding
│   │   ├── file-component-mapping.ts # Maps component types to SurveyJS elements
│   │   ├── format-date-string.ts     # Date formatting utility
│   │   ├── get-analytic-object.ts    # Firebase analytics event builder
│   │   ├── handle-toast-log-error.ts # Client-side error toast + logging
│   │   └── validate-domain.ts        # Email domain validation (@tvsmotor.com)
│   └── data/                         # Sample/seed template JSON files
│       ├── checklist-template.json
│       ├── checklist-ice-template.json
│       ├── checklist-without-divider.json
│       ├── equipment.json
│       ├── score.json
│       ├── multi-page-form/
│       ├── single-page-form/
│       └── quiz/
│
├── __tests__/                        # Jest test files
│   ├── page.test.tsx                 # Root page component tests
│   └── feedback.test.tsx             # Feedback page tests
│
├── .develop                          # Environment config (dev)
├── .development                      # Environment config (development)
├── .uat                              # Environment config (UAT)
├── .production                       # Environment config (production)
├── Dockerfile                        # Docker build (Node 23 Alpine, non-root user)
├── ci-pipeline.yaml                  # Azure DevOps CI pipeline
├── cd-pipeline.yaml                  # Azure DevOps CD pipeline (dev → UAT → prod)
├── next.config.ts                    # Next.js config (basePath, CSP headers, HSTS)
├── tsconfig.json                     # TypeScript config (strict null checks, bundler resolution)
├── jest.config.ts                    # Jest config (jsdom, V8 coverage, sonar reporter)
├── package.json                      # Dependencies and scripts
└── tailwind.config.ts                # Tailwind CSS configuration
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Browser)                          │
├─────────────────────────────────────────────────────────────┤
│  app/pages (App Router)                                      │
│    ├── uses → app/components/*                               │
│    ├── uses → app/lib/redux/store (via react-redux)          │
│    ├── uses → app/lib/axiosUIInterceptor (HTTP calls)        │
│    ├── uses → app/constants/app.constant (config + messages) │
│    ├── uses → utils/withAuth | utils/withAdminAuth (guards)  │
│    └── uses → utils/functions/* (encrypt, toast, etc.)       │
├─────────────────────────────────────────────────────────────┤
│  app/lib/axiosUIInterceptor                                  │
│    ├── uses → app/lib/authConfig (MSAL token refresh)        │
│    ├── uses → utils/functions/encrypt-decrypt                │
│    └── calls → pages/api/* (BFF routes)                      │
├─────────────────────────────────────────────────────────────┤
│  pages/api/* (BFF Layer — runs on server)                    │
│    ├── uses → utils/interceptors/axiosInterceptor            │
│    ├── uses → utils/functions/server-error-handle            │
│    └── calls → External backend (formbuilder-service via APIM)│
└─────────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

### Hybrid Next.js Routing
App Router (`app/`) handles all client-side pages and UI. Pages Router (`pages/api/`) handles API routes exclusively. This allows the BFF proxy layer to use the simpler Pages Router API while the UI benefits from App Router features (layouts, loading states, server components).

### BFF Proxy Pattern
The client never communicates directly with the backend microservice. All requests go through `/pages/api/` routes which:
1. Extract the auth token from incoming request headers
2. Strip unnecessary headers
3. Add the `Ocp-Apim-Subscription-Key` for Azure APIM
4. Forward to the backend service
5. Return structured error responses via `handleServerError`

### Runtime Configuration Loading
Environment variables are NOT baked into the client bundle. Instead, `AppConstants.loadConfig()` fetches them from `/api/get-env-config` at app startup. This enables a single Docker image to be deployed across all environments (dev, UAT, prod) with different env vars.

### Client-Side State Management
Redux Toolkit with two slices:
- `formbuilder` — complex state for the drag-and-drop form designer (components, pages, theme, config)
- `feedback` — simpler state for form filling (current template, submission data)

### Session-Based Authentication (Two Flows)
1. **Admin flow**: MSAL SSO → token stored encrypted in sessionStorage → `withAdminAuth` HOC guards routes
2. **Feedback flow**: Token received via URL params from parent app → encrypted in sessionStorage → `withAuth` HOC guards routes

### Iframe Embedding
Feedback forms are designed to be embedded in parent applications. Results and navigation events are communicated back via `window.top.postMessage`.

### SurveyJS as Form Engine
The form designer produces SurveyJS-compatible JSON. The form renderer uses `survey-react-ui` to display and collect responses. Custom components extend SurveyJS via `surveyjs-widgets`.



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router + Pages Router hybrid) | 15.x |
| UI Library | React | 19.x |
| Language | TypeScript | 5.x |
| State Management | Redux Toolkit | 2.7.x |
| Styling | Tailwind CSS + SCSS | Tailwind 3.4, Sass 1.86 |
| Form Engine | SurveyJS (`survey-react-ui`, `surveyjs-widgets`) | 1.12.x |
| Drag & Drop | `react-dnd` + `react-dnd-html5-backend` | 16.x |
| HTTP Client | Axios | 1.7.x |
| Authentication | `@azure/msal-browser` + `@azure/msal-react` | 4.13 / 3.0 |
| Analytics | Firebase (`firebase/analytics`) | 11.9.x |
| Encryption | CryptoJS | 4.2.x |
| Notifications | `react-hot-toast` | 2.5.x |
| Logging | `loglevel` | 1.9.x |
| Forms (admin) | `react-hook-form` | 7.56.x |
| Date Handling | `dayjs` | 1.11.x |
| File Upload | `multer` | 2.0.x |
| Testing | Jest + React Testing Library | Jest 29.7, RTL 16.2 |
| Build Tool | Turbopack (dev), Next.js bundler (prod) | — |
| Container | Docker (Node 23 Alpine) | — |
| CI/CD | Azure DevOps Pipelines | — |
| Code Quality | ESLint (next config), SonarQube (via jest-sonar-reporter) | — |

## Coding Conventions

### File & Component Patterns
- All page and component files use `"use client"` directive (client-side rendering dominant)
- Components are functional with hooks (no class components)
- Higher-Order Components (HOCs) for route protection: `withAuth`, `withAdminAuth`
- Dynamic imports via `next/dynamic` for heavy components (SurveyJS)
- `Suspense` boundaries with `<Loader />` fallback for async content

### Naming Conventions
- Components: PascalCase (`TemplateBuilder.tsx`, `FormGrid.tsx`)
- Utilities: kebab-case (`encrypt-decrypt.ts`, `server-error-handle.ts`)
- Constants: PascalCase class with UPPER_SNAKE_CASE static properties (`AppConstants.MAX_FILE_SIZE`)
- Redux slices: camelCase (`formbuilderSlice.ts`, `feedbackSlice.ts`)
- Types: PascalCase interfaces (`TemplateData`, `SaveSubmissionPayload`)
- API routes: kebab-case (`save-template-data.ts`, `get-env-config.ts`)

### Import Aliases
- `@/*` maps to project root (configured in `tsconfig.json`)
- Example: `import { AppConstants } from '@/app/constants/app.constant'`

### State Management Patterns
- Redux Toolkit `createSlice` with typed `PayloadAction`
- Store types exported: `RootState`, `AppDispatch`
- State accessed via `useSelector`, dispatched via `useDispatch`
- Complex state (form builder) uses nested objects; simpler state (feedback) uses flat structure

### API Communication Pattern
- Client-side: `axiosUIInstance` (from `app/lib/axiosUIInterceptor.ts`)
  - Automatically attaches `Access-Token` header
  - Handles token expiry with silent MSAL refresh
  - Clears session on 401/403 responses
- Server-side (BFF): `axiosInstance` (from `utils/interceptors/axiosInterceptor.ts`)
  - Strips incoming headers, sets `Authorization` and `Ocp-Apim-Subscription-Key`
  - Logs errors via `loglevel`

### Configuration Pattern
- `AppConstants` is a static class that loads config at runtime from `/api/get-env-config`
- Must call `AppConstants.loadConfig()` before accessing any config property
- Static readonly properties for compile-time constants (messages, limits)
- Static getters for runtime config (API URLs, auth settings)

## Error Handling

### Server-Side (BFF API Routes)
All API routes use the centralized `handleServerError` utility:
```typescript
// utils/functions/server-error-handle.ts
// Handles AxiosError → maps to HTTP status + structured JSON response
// Handles generic Error → 500 with message
// Fallback → 500 with "unknown error"
```
Response format: `{ statusCode, message, response? }`

### Client-Side
- `try/catch` blocks around API calls
- User-facing errors shown via `toast.error()` (react-hot-toast)
- Technical errors logged via `log.error()` (loglevel)
- Utility: `utils/functions/handle-toast-log-error.ts` combines both
- Auth errors (401/403) trigger session clear and redirect

### Error Constants
All error messages are centralized in `AppConstants.SERVER_ERROR_MESSAGES` and individual `*_ERROR_MESSAGE` constants. Never hardcode error strings in components.

## Testing

### Framework & Configuration
- Jest with `jsdom` test environment (configured via `next/jest`)
- React Testing Library for component rendering and interaction
- Coverage provider: V8
- Coverage output: `coverage/` directory
- SonarQube integration via `jest-sonar-reporter`

### Commands
```bash
npm run test          # Run all tests
npm run test:watch    # Watch mode
npm run coverage      # Run with coverage report
```

### Test Patterns
- Tests live in `__tests__/` directory at project root
- Mock external dependencies: `next/navigation`, `axios`, `react-hot-toast`, utility functions
- Test file naming: `*.test.tsx`
- Focus on component rendering and routing logic

### Current Coverage
Limited test coverage (2 test files). New features should include tests following the existing patterns in `__tests__/`.

## Deployment

### Environments
| Environment | Config File | Approval |
|---|---|---|
| Dev | `.develop` | Automatic |
| Development | `.development` | Automatic |
| UAT | `.uat` | Manual (email approval) |
| Production | `.production` | Manual (email approval) |

### Docker Build
```dockerfile
# Node 23 Alpine, non-root user (appuser:appgroup)
# BASE_PATH configurable via build arg (default: /asa/in/formbuilder)
# Single image deployed to all environments (runtime config via env vars)
```

### CI/CD Pipeline (Azure DevOps)
1. **CI** (`ci-pipeline.yaml`): Triggered by SonarQube pipeline on `main` branch. Uses shared build template from `TVSM-DMS/Devops_ISSM_pipelines` repo.
2. **CD** (`cd-pipeline.yaml`): Triggered by CI completion. Deploys via Helm charts to Kubernetes.
   - Dev: automatic
   - UAT: requires manual approval (1440 min timeout)
   - Prod: requires manual approval (1440 min timeout)

### Build & Run
```bash
# Local development
npm run dev           # Next.js dev server with Turbopack

# Production build
npm run build         # Next.js production build
npm run start         # Start production server

# Docker
docker-compose build
docker-compose up
```

### Security Headers (next.config.ts)
- **Content-Security-Policy**: Restricts script, style, image, connect, and font sources
- **Strict-Transport-Security**: 2-year max-age with includeSubDomains and preload
- **Base Path**: `/asa/in/formbuilder` (configurable via `BASE_PATH` env var)

### Key Environment Variables
| Variable | Purpose |
|---|---|
| `API_URL` | Backend microservice URL |
| `BASE_PATH` | Application base path for reverse proxy |
| `OCP_APIM_SUBSCRIPTION_KEY` | Azure APIM subscription key |
| `NEXT_PUBLIC_CLIENT_ID` | MSAL client ID |
| `NEXT_PUBLIC_AUTHORITY` | MSAL authority URL |
| `NEXT_PUBLIC_REDIRECT_URI` | MSAL redirect URI |
| `NEXT_PUBLIC_FIREBASE_*` | Firebase configuration |
| `NEXT_PUBLIC_SECRET_KEY` | AES encryption key |
| `NEXT_PUBLIC_LOGIN_SCOPE` | MSAL login scope |
| `NEXT_PUBLIC_FIREBASE_ENABLE` | Toggle Firebase analytics |


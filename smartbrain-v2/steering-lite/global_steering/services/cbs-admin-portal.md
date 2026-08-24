# cbs-admin-portal


## Product Context


# Product Context — TVS Lead Service Admin Portal

## What This Service Does

An internal admin portal for managing the configuration of TVS Motor's Lead Service. It provides a safe, auditable way for operations teams to create and update business configurations (dealers, lead sources, form mappings) that feed into the production Lead Service pipeline.

The core value proposition: **no direct writes to production tables**. All changes go through a Draft → Validate → Publish workflow with full audit trails and versioning.

## Domain Entities

### Production Entities (LS DB — read-heavy, controlled writes)

| Entity | Table | Purpose |
|--------|-------|---------|
| **DealerMaster** | `dealer_master` | Dealer network — main dealers and branch dealers with SAP codes, contact info, geography |
| **LeadSource** | `lead_sources` | Lead ingestion sources (website, campaigns, partners) with mappings to EMS/LCE/CRM systems |
| **LeadFlowConfiguration** | `lead_flow_configuration` | Per-source flow rules — validation toggles, push destinations, thresholds |
| **FormConfiguration** | `FormConfigurations` | Field mapping configs — maps external form fields to internal system fields per form/source/product |

### Admin Entities (Admin DB — full read/write)

| Entity | Table | Purpose |
|--------|-------|---------|
| **ConfigDraft** | `config_drafts` | Pending changes awaiting publish. Stores serialized payload as JSON |
| **ConfigVersion** | `config_versions` | Immutable version history of every published config, per environment |
| **ConfigSyncStatus** | `config_sync_status` | Tracks UAT vs PROD version parity per entity |
| **AuditLog** | `audit_logs` | Every create/update/publish action with before/after payloads |
| **AdminUser** | `admin_users` | Portal users with roles (ADMIN, PO, VIEWER) |

## Key Relationships

- A **LeadSource** has one **LeadFlowConfiguration** (1:1 via `source_id`)
- A **FormConfiguration** references a source (`source_id`) and optionally a dealer (`dealer_id`)
- **ConfigDraft** is polymorphic — `entity_type` enum determines which domain entity the payload represents
- **DealerMaster** has a self-referential relationship: branch dealers reference a `parent_dealer_code`

## Integrations

| System | Integration Point |
|--------|-------------------|
| **Azure SQL Server** | Primary database (both Admin DB and LS DB on same Azure SQL instance) |
| **Azure Active Directory** | Database authentication via `ActiveDirectoryPassword` |
| **MSAL4J / Azure Identity** | Azure AD token acquisition for DB connections |
| **EMS (Event Management System)** | Lead sources map to EMS sources/event types |
| **LCE (Lead Conversion Engine)** | Sources can push to LCE with configurable API URLs |
| **CRM** | Sources map to CRM source identifiers |
| **Dialer / Rezo / CCP / CMP** | Various push destinations toggled per source |

## Business Rules

### Draft → Publish Workflow
1. User submits data → saved as DRAFT in Admin DB only
2. Validation runs (field validation + business rule checks)
3. Publish → transactional write to LS DB + version record + audit log
4. Draft is deleted after successful publish

### Dealer Rules
- SAP Dealer Code must be unique
- Codes containing "BD" are auto-detected as BRANCH type
- Branch dealers MUST have a `parent_dealer_code` that exists in the system
- Branch number is extracted from numeric suffix of the code
- No hard deletes — use `is_active` toggle

### Source Rules
- Source name must be unique
- New sources get the next sequential ID (`max(id) + 1`)
- Flow configuration is published atomically with the source
- Dependency check warns (non-blocking) if source is used in FormConfigurations

### Form Configuration Rules
- Composite uniqueness key: `form_id + source_id + product_type`
- CUSTOMER_NAME and PHONE_NUMBER system fields are always required in mappings
- Field mappings are stored as JSON (`{"SYSTEM_FIELD": "input_field"}`)
- The backend auto-generates `field_mapping_json` from structured mapping DTOs
- Valid product types: EV, ICE, MOPED, THREE_WHEELER, ALL
- Referenced source and dealer must exist in LS DB

### Audit Rules
- Every create/update/publish action MUST be logged
- Logs capture before/after payload for diffing
- Environment is tracked (UAT/PROD)

### Sync Rules
- Each entity tracks UAT version and PROD version separately
- Status is computed: IN_SYNC (versions match), OUT_OF_SYNC (versions differ), NOT_IN_PROD (no prod version)

### Access Control
- ADMIN / PO: full read + write (can draft and publish)
- VIEWER: read-only access
- No anonymous access except `/api/auth/login`



## Code Structure


# Project Structure — TVS Lead Service Admin Portal

## Annotated Directory Layout

```
cbs-admin-portal/
├── backend/                              # Java Spring Boot 3.2 — Modular Monolith
│   ├── pom.xml                           # Maven build, Spring Boot parent 3.2.4, Java 17
│   ├── build_out.txt                     # Build output log (not committed ideally)
│   └── src/main/
│       ├── java/com/tvs/leadsadmin/
│       │   ├── LeadsAdminApplication.java        # Spring Boot entry point
│       │   │
│       │   ├── config/                           # Cross-cutting infrastructure
│       │   │   ├── AdminDataSourceConfig.java    # Primary datasource — Admin DB (drafts, audit, users)
│       │   │   ├── LsDataSourceConfig.java       # Secondary datasource — LS DB (production tables)
│       │   │   ├── SecurityConfig.java           # Spring Security + CORS + stateless JWT
│       │   │   ├── JwtUtil.java                  # JWT generation and validation (HMAC-SHA)
│       │   │   ├── JwtAuthFilter.java            # OncePerRequestFilter — extracts JWT from Bearer header
│       │   │   └── DataInitializer.java          # Dev-profile seed data (default users)
│       │   │
│       │   ├── common/                           # Shared cross-module code
│       │   │   ├── dto/
│       │   │   │   └── ApiResponse.java          # Uniform API envelope {success, message, data, errors}
│       │   │   ├── enums/
│       │   │   │   ├── EntityType.java           # DEALER, SOURCE, FLOW_CONFIG, FORM_CONFIG
│       │   │   │   ├── DraftStatus.java          # DRAFT, READY
│       │   │   │   ├── AuditAction.java          # CREATE, UPDATE, PUBLISH
│       │   │   │   ├── Environment.java          # UAT, PROD
│       │   │   │   └── SyncStatus.java           # IN_SYNC, OUT_OF_SYNC, NOT_IN_PROD
│       │   │   ├── exception/
│       │   │   │   ├── GlobalExceptionHandler.java   # @RestControllerAdvice — maps exceptions to ApiResponse
│       │   │   │   ├── ValidationException.java      # Multi-error validation (List<String> errors)
│       │   │   │   └── EntityNotFoundException.java  # 404 for missing entities
│       │   │   └── service/
│       │   │       └── DependencyCheckerService.java # Cross-module FK dependency warnings
│       │   │
│       │   ├── auth/                             # Authentication module
│       │   │   ├── controller/AuthController.java
│       │   │   ├── dto/{LoginRequest, LoginResponse}.java
│       │   │   ├── entity/AdminUser.java
│       │   │   ├── repository/AdminUserRepository.java
│       │   │   └── service/AuthService.java      # Login + password verification
│       │   │
│       │   ├── audit/                            # Draft/Version/Audit infrastructure
│       │   │   ├── controller/
│       │   │   │   ├── AuditController.java      # GET /api/audit — paginated logs
│       │   │   │   └── SyncController.java       # GET /api/sync — environment sync status
│       │   │   ├── dto/DraftDto.java
│       │   │   ├── entity/
│       │   │   │   ├── ConfigDraft.java          # Polymorphic draft storage
│       │   │   │   ├── ConfigVersion.java        # Immutable version snapshots
│       │   │   │   ├── ConfigSyncStatus.java     # UAT/PROD version tracking
│       │   │   │   └── AuditLog.java             # Action log with before/after
│       │   │   ├── repository/
│       │   │   │   ├── ConfigDraftRepository.java
│       │   │   │   ├── ConfigVersionRepository.java
│       │   │   │   ├── ConfigSyncStatusRepository.java
│       │   │   │   └── AuditLogRepository.java
│       │   │   └── service/
│       │   │       ├── DraftService.java         # Save/get/delete drafts, create versions
│       │   │       ├── AuditService.java         # Log actions, query audit history
│       │   │       └── ConfigSyncService.java    # Track sync status across environments
│       │   │
│       │   ├── dealer/                           # Dealer Management module
│       │   │   ├── controller/DealerController.java
│       │   │   ├── dto/DealerDto.java
│       │   │   ├── entity/DealerMaster.java
│       │   │   ├── repository/DealerMasterRepository.java
│       │   │   ├── service/DealerService.java    # Draft + publish workflow
│       │   │   └── validation/
│       │   │       ├── DealerValidator.java      # Business rules (uniqueness, parent check)
│       │   │       └── DealerCodeParser.java     # SAP code → type/branch detection
│       │   │
│       │   ├── source/                           # Source + Flow Config module
│       │   │   ├── controller/SourceController.java
│       │   │   ├── dto/{SourceDto, FlowConfigDto}.java
│       │   │   ├── entity/
│       │   │   │   ├── LeadSource.java           # Implements Persistable (manual ID assignment)
│       │   │   │   └── LeadFlowConfiguration.java
│       │   │   ├── repository/
│       │   │   │   ├── LeadSourceRepository.java
│       │   │   │   └── LeadFlowConfigRepository.java
│       │   │   ├── service/SourceService.java    # Draft + publish (source + flow config atomically)
│       │   │   └── validation/SourceValidator.java
│       │   │
│       │   └── formconfig/                       # Form Configuration module
│       │       ├── controller/FormConfigController.java
│       │       ├── dto/{FormConfigDto, FieldMappingDto}.java
│       │       ├── entity/FormConfiguration.java
│       │       ├── repository/FormConfigurationRepository.java
│       │       ├── service/FormConfigService.java    # Draft + publish + JSON generation
│       │       └── validation/FormConfigValidator.java  # Field mapping rules, metadata lists
│       │
│       └── resources/
│           ├── application.yml               # Multi-profile config (default = Azure SQL, dev = H2)
│           ├── schema-admin.sql              # Admin DB DDL
│           └── data-ls.sql                   # LS DB seed data
│
└── frontend/                             # React 18 SPA (Create React App)
    ├── package.json                      # react 18, react-router-dom 6, axios, lucide-react, react-hot-toast
    ├── public/                           # Static assets
    └── src/
        ├── index.js                      # React DOM entry
        ├── App.js                        # BrowserRouter + AuthProvider + protected routes
        ├── components/
        │   ├── Layout.js                 # Sidebar navigation + header
        │   └── shared.js                 # Reusable UI components
        ├── hooks/
        │   └── useAuth.js                # AuthContext — login/logout, token management
        ├── pages/
        │   ├── LoginPage.js              # JWT login form
        │   ├── DashboardPage.js          # Overview/stats
        │   ├── DealerManagement.js       # Dealer CRUD with draft/publish
        │   ├── SourceManagement.js       # Source + flow config management
        │   ├── FormConfigManagement.js   # Visual field mapping UI
        │   └── AuditLogPage.js           # Paginated audit log viewer
        ├── services/
        │   ├── api.js                    # Axios instance with JWT interceptor + 401 redirect
        │   └── dataService.js            # Domain-specific API methods (dealer, source, formConfig, audit, sync)
        └── styles/
            └── index.css                 # Global styles (dark theme — Catppuccin-inspired)
```

## Module Dependencies

```
                    ┌─────────────┐
                    │   common    │  (enums, dto, exceptions, DependencyCheckerService)
                    └──────┬──────┘
                           │ used by all modules
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼──────┐
    │   dealer   │   │   source   │   │ formconfig  │
    └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ all use
                    ┌──────▼──────┐
                    │    audit    │  (DraftService, AuditService, ConfigSyncService)
                    └─────────────┘
                           │
                    ┌──────▼──────┐
                    │    auth     │  (AuthService, AdminUser)
                    └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   config    │  (DataSources, Security, JWT)
                    └─────────────┘
```

- **dealer**, **source**, **formconfig** are peer modules — they don't import each other directly
- **DependencyCheckerService** (in common) bridges cross-module queries (e.g., "is this dealer used in any FormConfiguration?")
- **audit** module provides shared infrastructure (drafts, versions, audit logs) consumed by all domain modules
- **config** is pure infrastructure — no business logic

## Architectural Decisions

### Dual-Database with Separate EntityManagers
- **Admin DB** (`adminEntityManagerFactory`): owns drafts, versions, audit, users. `ddl-auto: update`.
- **LS DB** (`lsEntityManagerFactory`): owns production business tables. `ddl-auto: none` — schema managed externally.
- Each has its own `PlatformTransactionManager`. Services explicitly reference `@Transactional("lsTransactionManager")` or `@Transactional("adminTransactionManager")`.

### Modular Monolith (Package-by-Feature)
- Each domain module is self-contained: controller → dto → entity → repository → service → validation.
- Modules communicate only through the `common` and `audit` packages.
- Repository scanning is split by datasource config (`@EnableJpaRepositories(basePackages = ...)`).

### Polymorphic Draft Storage
- A single `config_drafts` table stores drafts for all entity types.
- The `entity_type` enum discriminates, and `payload` holds the full DTO as JSON.
- This avoids per-entity draft tables and simplifies the workflow.

### No Delete Operations
- Entities use `is_active` / `active` boolean flags for soft-delete.
- The system never issues DELETE statements against LS DB tables.

### Frontend as Thin Client
- React SPA with no state management library (uses component state + context).
- All business logic lives on the backend — frontend is purely presentational.
- API proxy via CRA's `proxy` field in package.json (dev mode).



## Tech Stack & Dependencies


# Tech Stack & Conventions — TVS Lead Service Admin Portal

## Tech Stack

### Backend
| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Spring Boot | 3.2.4 |
| Language | Java | 17 |
| Build | Maven | 3.8+ |
| ORM | Spring Data JPA / Hibernate | (managed by Boot) |
| Security | Spring Security + JWT (jjwt 0.12.5) | |
| Database (prod) | Azure SQL Server (MS SQL) | via `mssql-jdbc` |
| Database (dev) | H2 in-memory (MSSQLServer mode) | |
| Azure Auth | MSAL4J 1.14.0, azure-identity 1.11.3 | |
| JSON | Jackson (jackson-databind, jackson-datatype-jsr310) | |
| Boilerplate | Lombok | |
| Connection Pool | HikariCP | (Spring Boot default) |

### Frontend
| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | React | 18.2 |
| Routing | react-router-dom | 6.22 |
| HTTP Client | axios | 1.6.7 |
| Icons | lucide-react | 0.344 |
| Notifications | react-hot-toast | 2.4.1 |
| Tooling | Create React App (react-scripts 5.0.1) | |
| State | Component state + React Context (no Redux/Zustand) | |

## Coding Conventions

### Java / Backend

**Package structure**: `com.tvs.leadsadmin.{module}.{layer}`
- Modules: `auth`, `audit`, `dealer`, `source`, `formconfig`, `common`, `config`
- Layers within each module: `controller`, `dto`, `entity`, `repository`, `service`, `validation`

**Naming**:
- Entities: singular nouns matching the domain (`DealerMaster`, `LeadSource`, `FormConfiguration`)
- DTOs: `{Entity}Dto` (e.g., `DealerDto`, `SourceDto`, `FormConfigDto`)
- Repositories: `{Entity}Repository`
- Services: `{Module}Service` (e.g., `DealerService`, `SourceService`)
- Validators: `{Module}Validator` (e.g., `DealerValidator`, `FormConfigValidator`)
- Controllers: `{Module}Controller` with `@RequestMapping("/api/{resource}")`

**Dependency injection**: Constructor injection exclusively (no `@Autowired` on fields).

**Lombok usage**: `@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder` on entities and DTOs. `@Data` on simple DTOs like `ApiResponse`.

**Logging**: SLF4J via `LoggerFactory.getLogger(ClassName.class)` — not Lombok's `@Slf4j`.

**Transaction management**: Explicit transaction manager references:
```java
@Transactional("lsTransactionManager")    // for LS DB writes
@Transactional("adminTransactionManager") // for Admin DB writes
```

**API response envelope**: All endpoints return `ResponseEntity<ApiResponse<T>>`:
```java
return ResponseEntity.ok(ApiResponse.ok(data, "Success message"));
return ResponseEntity.badRequest().body(ApiResponse.error("message", errors));
```

**Access control**: Method-level with `@PreAuthorize("hasAnyRole('ADMIN', 'PO')")` on write endpoints.

**Entity timestamps**: Use `@PrePersist` and `@PreUpdate` lifecycle callbacks (not `@CreatedDate`).

### JavaScript / Frontend

**File naming**: PascalCase for components/pages (`DealerManagement.js`), camelCase for services/hooks (`dataService.js`, `useAuth.js`).

**Component style**: Functional components with hooks. No class components.

**API calls**: All go through the centralized `api.js` axios instance. Domain methods in `dataService.js` return `r.data` (unwrap axios response).

**Auth pattern**: `useAuth()` hook provides `{ user, login, logout }`. Token stored in `localStorage`.

**Routing**: Protected routes via `<ProtectedRoute>` wrapper that checks `useAuth().user`.

**Notifications**: `react-hot-toast` for success/error feedback (dark theme styled).

## Patterns

### Draft → Publish (Core Pattern)

Every domain service follows this template:

```java
// 1. saveDraft — validates, stores in Admin DB
public ConfigDraft saveDraft(Dto dto, String username) {
    validator.validate(dto, false);
    return draftService.saveDraft(EntityType.X, entityKey, dto, username);
}

// 2. publish — reads draft, writes to LS DB, versions, audits, deletes draft
@Transactional("lsTransactionManager")
public Entity publish(Long draftId, String username) {
    ConfigDraft draft = draftService.getDraft(draftId);
    Dto dto = objectMapper.readValue(draft.getPayload(), Dto.class);
    
    // Check existing (create vs update)
    // Write to LS DB
    // Create version in Admin DB
    // Log audit
    // Delete draft
}
```

### Validation Pattern

Validators are `@Component` classes with a `validate(Dto, boolean isUpdate)` method that:
1. Collects errors into a `List<String>`
2. Throws `ValidationException(errors)` if non-empty
3. May enrich the DTO with derived data (e.g., `DealerValidator` sets `detectedType`)

### Entity Mapping

Manual `toDto()` methods in service classes (no MapStruct or ModelMapper). Keeps it simple and explicit.

### Cross-Module Queries

When module A needs to check data in module B's tables, it goes through `DependencyCheckerService` in `common` — not by importing module B's service directly.

## Error Handling

### Exception Hierarchy
```
Exception
├── ValidationException        → 400 + list of field errors
├── EntityNotFoundException    → 404 + entity type/key message
├── AccessDeniedException      → 403 (Spring Security)
├── MethodArgumentNotValidException → 400 (Bean Validation)
└── Exception (catch-all)      → 500 + generic message (details logged server-side)
```

### GlobalExceptionHandler
- `@RestControllerAdvice` catches all exceptions
- Always returns `ApiResponse<Void>` with `success: false`
- Validation errors include the full error list in `errors` field
- Unexpected exceptions log the stack trace but return a generic message to the client

### Service-Level Error Handling
- Publish methods wrap the entire operation in try/catch
- On failure, throw `RuntimeException` with context (the `@Transactional` annotation ensures rollback)
- Dependency check warnings are logged but non-blocking (don't prevent publish)

## Testing

### Backend
- **Framework**: Spring Boot Test + JUnit 5 + Spring Security Test
- **Dev profile**: Uses H2 in MSSQLServer compatibility mode for local/CI testing
- **Data seeding**: `DataInitializer` (dev profile only) creates default users
- **No test files currently exist** — when adding tests, use:
  - `@SpringBootTest` for integration tests
  - `@WebMvcTest` for controller slice tests
  - `@DataJpaTest` for repository tests (specify which datasource)

### Frontend
- **Framework**: Jest + React Testing Library (via react-scripts)
- **No test files currently exist** — when adding tests, use component rendering tests with RTL

## Build & Run

### Backend
```bash
# Dev mode (H2 in-memory)
cd backend
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# Production build
mvn clean package -DskipTests
java -jar target/leads-admin-portal-1.0.0-SNAPSHOT.jar
```

### Frontend
```bash
cd frontend
npm install
npm start          # Dev server on :3000, proxies to :8080
npm run build      # Production build to build/
```

## Configuration

### Profiles
| Profile | Database | DDL | Use Case |
|---------|----------|-----|----------|
| (default) | Azure SQL Server | none | Production / UAT deployment |
| `dev` | H2 in-memory | update | Local development, CI |

### Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `JWT_SECRET` | HMAC signing key for JWT tokens | Hardcoded fallback (dev only) |
| `REACT_APP_API_URL` | Frontend API base URL override | `/api` (uses proxy) |

### Multi-Datasource Config Keys
```yaml
spring.datasource.admin.*    # Admin DB connection
spring.datasource.ls.*       # LS DB connection
```

## Deployment Notes

- Backend runs on port 8080
- Frontend proxies `/api` to backend in dev; in production, serve frontend static files behind a reverse proxy or embed in the Spring Boot jar
- Azure SQL uses `ActiveDirectoryPassword` authentication — requires valid Azure AD credentials
- HikariCP pool: max 10 connections, 5-minute idle timeout, 10-minute max lifetime per datasource
- No Docker/Kubernetes config exists yet — deploy as a standard Spring Boot fat JAR
- H2 console available at `/h2-console` in dev profile only


# tvsm-securesigner-service


## Product Context


# Product: TVS Motor Secure Signer Service

## What This Service Does

The Secure Signer Service is an internal cryptographic utility microservice for TVS Motor. It provides URL signing, JWT generation/encryption, and hashing capabilities to other services in the TVS Motor ecosystem. It acts as a centralized signing authority that keeps cryptographic keys secure in Azure Key Vault and exposes simple HTTP APIs for consumers.

## Domain Entities

- **Signed URL**: A URL augmented with an expiry timestamp (`exp`) and an HMAC signature (`sig`). Used to create tamper-proof, time-limited links.
- **JWT (JSON Web Token)**: A signed token containing custom claims, issued with a configurable expiry. Used for service-to-service authentication via APIM gateway.
- **Encrypted JWT (JWE)**: A nested JWT that is first signed with RSA (RS256) then encrypted with RSA-OAEP-256 + AES-256-GCM. Used for secure payload exchange with payment partners.
- **BCrypt Hash**: A one-way hash of input data at a configurable strength. Used for integrity verification.
- **Signing Key**: An HMAC secret stored in Azure Key Vault, used for URL signing and standard JWT generation.
- **RSA Key Pair**: Private and public keys stored as PEM secrets in Azure Key Vault, used for JWE encryption/decryption.

## Integrations

| System | Purpose | Protocol |
|--------|---------|----------|
| Azure Key Vault | Stores all cryptographic keys (HMAC secrets, RSA key pairs) | Azure SDK with Managed Identity |
| APIM Gateway | Consumer of signed JWTs (audience: `apim-gateway`) | HTTP (downstream) |
| Payment Partners | Consumer/producer of encrypted JWTs for payment transactions | HTTP (downstream) |
| Internal TVSM Services | Consumers of URL signing and hashing APIs | HTTP REST |

## Business Rules

1. **URL Signing**
   - URL must not be empty and cannot exceed 10,000 characters.
   - Expiry must be between 1 and 10,000 minutes.
   - The signed URL appends `exp` (epoch seconds) and `sig` (Base64 HMAC) as query parameters.
   - URLs are HTML-escaped before signing to prevent injection.

2. **JWT Generation**
   - The `aud` (audience) claim is mandatory; requests without it return HTTP 400.
   - Expiry is provided as epoch seconds and must be between 1 and 3,000,000,000.
   - Claims map cannot exceed 1,000 entries; keys max 1,000 chars; string values max 10,000 chars.
   - Issuer is always `https://tvsmotor.com/secure-signer`.
   - All query parameters are HTML-escaped before processing.

3. **Encrypted JWT (JWE)**
   - Caller specifies private key name, public key name, and key ID via request headers.
   - Signing uses RSA256; encryption uses RSA-OAEP-256 with AES-256-GCM.
   - Keys are resolved from Azure Key Vault by name.

4. **BCrypt Hashing**
   - Caller specifies the data and BCrypt strength (cost factor).

5. **Caching**
   - Key Vault secrets are cached for 1 hour (3600s) to reduce vault calls.
   - RSA private and public keys are cached separately for 1 hour after PEM parsing.
   - Cache is heap-based with a max of 10 entries per cache.

6. **Security**
   - Authentication to Azure Key Vault uses Managed Identity (no secrets in config).
   - No user-facing authentication on the service itself (expected to be network-isolated behind APIM/internal network).



## Code Structure


# Project Structure

## Directory Layout

```
tvsm-securesigner-service/
├── .kiro/steering/              # Kiro steering files (project context)
├── src/
│   ├── main/
│   │   ├── java/com/tvsm/urlsigner/
│   │   │   ├── URLSignerApplication.java      # Spring Boot entry point, enables caching
│   │   │   ├── config/
│   │   │   │   └── KeyVaultConfig.java        # Azure Key Vault SecretClient bean setup
│   │   │   ├── controller/
│   │   │   │   ├── SignerController.java      # REST endpoints for signing/token/encryption/hashing
│   │   │   │   └── TestController.java        # Health-check / upness endpoint
│   │   │   ├── exception/
│   │   │   │   └── SignerException.java       # Domain-specific unchecked exception
│   │   │   ├── service/
│   │   │   │   ├── AzureKeyVaultClient.java   # Thin wrapper over Azure SecretClient with caching
│   │   │   │   ├── CacheService.java          # Caches parsed RSA keys (private + public)
│   │   │   │   └── SignerService.java         # Core business logic: signing, JWT, JWE, BCrypt
│   │   │   └── util/
│   │   │       ├── AppUtils.java              # Validation helpers and general utilities
│   │   │       └── PemUtils.java              # PEM string → RSA key object parsing
│   │   └── resources/
│   │       ├── application.yml                # Spring config (Azure Key Vault, cache, app name)
│   │       └── ehcache.xml                    # Ehcache3/JSR-107 cache definitions (secrets, keys)
│   └── test/
│       └── java/com/tvsm/urlsigner/
│           ├── controller/test/
│           │   └── SignerControllerTest.java   # Integration tests via MockMvc
│           └── service/test/
│               └── SignerServiceTest.java      # Service-layer tests with mocked vault
├── pom.xml                                    # Maven build (Spring Boot 3.5.3, Java 17)
├── Dockerfile                                 # Multi-stage build: Maven → Amazon Corretto 17
├── ci-pipeline.yaml                           # Azure DevOps CI (triggers CD on dev branch)
├── cd-pipeline.yaml                           # Azure DevOps CD (dev → UAT → prod with approvals)
├── AST_Image_Scan_secure_signer_Pipeline.yml  # Container image security scanning pipeline
└── AST_secure_signer_UAT_Pipeline.yml         # UAT deployment + security scan pipeline
```

## Module Dependencies

```
Controller Layer
  └── SignerController ──→ SignerService
  └── TestController (standalone, no dependencies)

Service Layer
  └── SignerService ──→ AzureKeyVaultClient (for HMAC key retrieval)
                    ──→ CacheService (for RSA key retrieval)
  └── CacheService ──→ AzureKeyVaultClient (fetches raw PEM)
                   ──→ PemUtils (parses PEM to RSA key objects)
  └── AzureKeyVaultClient ──→ Azure SecretClient (Spring bean from KeyVaultConfig)

Config Layer
  └── KeyVaultConfig ──→ AzureKeyVaultProperties (Spring Cloud Azure auto-config)

Utility Layer (stateless, no Spring dependencies)
  └── AppUtils (validation)
  └── PemUtils (PEM parsing)
```

## Architectural Decisions

1. **Layered architecture** — Standard controller → service → external-client layering. No repository/database layer since this service is stateless (all state lives in Azure Key Vault).

2. **Caching as a first-class concern** — Three separate Ehcache regions (`secrets`, `security-keys-private`, `security-keys-public`) with 1-hour TTL. This avoids repeated Key Vault round-trips for the same keys. Cache is declared via `@Cacheable` annotations at the service layer.

3. **Separation of raw secret retrieval and key parsing** — `AzureKeyVaultClient` caches raw secret strings; `CacheService` caches the parsed RSA key objects. This two-tier approach means a cache miss on the parsed key doesn't necessarily hit Key Vault if the raw PEM is still cached.

4. **Stateless design** — No database, no session state. The service can scale horizontally without coordination. Each instance maintains its own local cache.

5. **Multi-stage Docker build** — Build stage uses Maven + Corretto 17; runtime stage uses a minimal headless Corretto image to reduce attack surface.

6. **Azure DevOps pipelines with environment promotion** — CI builds on dev branch, CD promotes through dev → UAT (with manual approval) → prod (with manual approval). Container security scanning gates deployment.

7. **Key flexibility via headers** — For JWE operations, callers specify key names via `X-PRIVATE-KEY`, `X-PUBLIC-KEY`, and `X-KEY-ID` headers, allowing the same service to handle multiple key pairs for different partners.



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.3 |
| Build Tool | Maven | 3.9.9 |
| Cloud SDK | Spring Cloud Azure (Key Vault) | 5.19.0 |
| JWT (HMAC) | jjwt (io.jsonwebtoken) | 0.12.6 |
| JWT (RSA/JWE) | Nimbus JOSE+JWT | 10.3 |
| Hashing | Spring Security Crypto (BCrypt) | managed by Spring Boot |
| Caching | Ehcache 3 via JSR-107 (JCache) | managed by Spring Boot |
| Container Runtime | Amazon Corretto | 17.0.13 (AL2023 headless) |
| CI/CD | Azure DevOps Pipelines | — |
| Secret Management | Azure Key Vault | — |

## Coding Conventions

### Naming
- Package root: `com.tvsm.urlsigner`
- Controllers suffixed with `Controller`, services with `Service`, configs with `Config`
- Test classes suffixed with `Test`, placed in a `test` sub-package mirroring the source package
- Constants are `private static final` with UPPER_SNAKE_CASE

### Dependency Injection
- Field injection via `@Autowired` (project convention, not constructor injection)
- Configuration values via `@Value("${property-name}")`

### REST API Style
- Base path: `/generate` for all signing/token operations
- GET for idempotent operations (sign, jwt, decrypt, bcrypt-hash)
- POST for encrypted-jwt creation (accepts JSON body)
- Query parameters for simple inputs; headers (`X-PRIVATE-KEY`, `X-PUBLIC-KEY`, `X-KEY-ID`) for key selection
- No DTO classes — uses raw `Map<String, String>` / `Map<String, Object>` for flexibility

### Input Validation
- Validation is performed inline at the start of service methods using `AppUtils` helper methods
- Pattern: validate → sanitize (HTML escape) → process
- Validation failures throw `SignerException` (unchecked)
- No Bean Validation annotations (`@Valid`, `@NotNull`) — all validation is imperative

### Logging
- SLF4J with `LoggerFactory.getLogger(ClassName.class)` pattern
- Log at INFO level for key vault access and initialization
- Log at ERROR level for missing required parameters

## Patterns

### Caching Strategy
```
Request → @Cacheable check → cache hit? return cached value
                           → cache miss? call Key Vault → store in cache → return
```
- Three cache regions: `secrets` (raw strings), `security-keys-private` (RSAPrivateKey), `security-keys-public` (RSAPublicKey)
- TTL: 3600 seconds (1 hour) for all caches
- Max entries: 10 per cache (heap-only, no overflow to disk)
- Cache key: the secret/key name string

### Key Resolution
- HMAC key: retrieved by configured name (`signer-key-name` property), Base64-decoded to bytes
- RSA keys: retrieved by caller-specified name (header), PEM-parsed via `PemUtils`

### JWE Nested JWT Pattern
1. Build claims → create `SignedJWT` with RS256 using private key
2. Wrap signed JWT as payload in `JWEObject` with RSA-OAEP-256 + A256GCM
3. Encrypt using public key → serialize

### URL Signing Pattern
1. Append `exp=<epoch>` to URL
2. HMAC-sign the full URL string (including exp)
3. Append `sig=<base64-encoded-hmac>` (URL-encoded)

## Error Handling

- **SignerException** — single domain exception extending `RuntimeException`. Wraps both checked exceptions and validation errors.
- **ResponseStatusException** — used in controllers for HTTP-specific errors (e.g., 400 for missing `aud`).
- No global `@ControllerAdvice` or `@ExceptionHandler` — exceptions propagate to Spring's default error handling.
- Checked exceptions from crypto/Key Vault operations are caught and re-thrown as `SignerException`.

## Testing

### Framework
- JUnit 5 (Jupiter) with Spring Boot Test
- Mockito for mocking `AzureKeyVaultClient`

### Test Types
- **Controller tests** (`SignerControllerTest`): `@SpringBootTest` + `@AutoConfigureMockMvc` — full context integration tests using `MockMvc`
- **Service tests** (`SignerServiceTest`): `@SpringBootTest` with `@MockBean` for the vault client

### Test Conventions
- Mock the `AzureKeyVaultClient` to return known keys/secrets (avoids real Azure calls)
- Inline test keys as `private static final String` constants (PEM format)
- Assertions use JUnit 5 `Assertions` class
- Tests print results to stdout for manual inspection alongside assertions

### Running Tests
```bash
mvn test                    # Run all tests
mvn test -Dtest=SignerServiceTest  # Run specific test class
```

## Build & Deployment

### Local Build
```bash
mvn clean install           # Build + run tests
mvn clean install -DskipTests  # Build without tests
```

### Docker Build
```bash
docker build -t tvsmbe-securesigner .
docker run -p 8080:8080 \
  -e AZURE_CLIENT_ID=<client-id> \
  -e AZURE_KEYVAULT_ENDPOINT=<vault-url> \
  tvsmbe-securesigner
```

### Required Environment Variables
| Variable | Purpose |
|----------|---------|
| `AZURE_CLIENT_ID` | Managed Identity client ID for Azure auth |
| `AZURE_KEYVAULT_ENDPOINT` | Azure Key Vault URL (e.g., `https://myvault.vault.azure.net/`) |

### CI/CD Pipeline
- **CI** (`ci-pipeline.yaml`): Triggered by CD pipeline completion on `dev` branch. Uses shared build template from `Devops_ISSM_pipelines` repo.
- **CD** (`cd-pipeline.yaml`): Promotes through environments:
  - `dev` → automatic
  - `uat` → manual approval (24h timeout)
  - `prod` → manual approval (24h timeout)
- **Security scanning**: Container image scan pipeline gates deployment between CI and CD.
- Pipelines extend shared templates hosted in `TVSM-DMS/Devops_ISSM_pipelines` GitHub repo.

### Deployment Target
- Kubernetes (Helm charts, chart name matches service name: `securesigner`)
- Container exposed on port 8080


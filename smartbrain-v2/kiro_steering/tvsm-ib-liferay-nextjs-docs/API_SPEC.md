# API Specification — TVSM IB Next.js Website

> Audience: integration partners, QA, and engineers working against the TVSM IB website APIs.
> Scope: all HTTP endpoints exposed by the Next.js application, plus the upstream APIs the application depends on.
> Notes: secrets are referenced by environment variable name only. Country values use the `<COUNTRY>` placeholder.

---

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | tvsm-ib-nextjs (TVS IB Liferay Next.js Websites) |
| Repo | _TBD — fill in Git remote URL_ |
| Team | _TBD_ |
| Tech Lead | _TBD (@firstname.lastname)_ |
| Deployment | AKS (Kubernetes) — Azure Application Gateway ingress; primary + DR clusters |
| Base URL (prod) | Per country: `https://malta.tvsmotor.com`, `https://spain.tvsmotor.com`, `https://portugal.tvsmotor.com`, `https://france.tvsmotor.com`, `https://hungary.tvsmotor.com` |
| Base URL (UAT) | Per country: `https://uat-<country>.tvsmotor.net` |
| Runtime | Next.js 16 (App Router, `output: standalone`), Node.js, React 19 |

> This is a multi-country Next.js website. One image serves all countries; the country is resolved at the edge from the host name (or the `country` cookie on localhost).

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | _TBD_ | _TBD_ |
| Tech Lead | _TBD_ | _TBD_ |
| Dev Team | _TBD_ | _TBD_ |
| On-call | _TBD_ | _TBD_ |
| Vendor (if external) | N/A | N/A |

> Contacts are not stored in the repository. Fill these in from your team directory / on-call tooling before publishing.

---

## My API Endpoints (Inbound)

Every HTTP endpoint this Next.js service exposes, and who calls it. Inbound endpoints are **not authenticated at the application layer** — they are expected to be called same-origin from the website; edge protection (Azure Application Gateway / WAF) applies.

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `/api/contact-submit` | None (same-origin) | Validate + forward Contact Us lead to TVS Lead API | Website Contact Us form (browser) |
| POST | `/api/become-dealer-submit` | None (same-origin) | Validate + forward Become Dealer lead to TVS Lead API | Website Become a Dealer form (browser) |
| GET | `/api/health` | None | Liveness/readiness probe (returns `OK`) | Kubernetes probes (Application Gateway health) |
| GET | `/health_check/data_source` | None | Verify Liferay backend reachability (10s timeout) | Ops / monitoring, manual checks |
| GET | `/sitemap.xml` | None | Per-country sitemap (from Liferay `SITEMAP` structure) | Search engine crawlers |
| GET | `/robots.txt` | None | Per-country robots policy (from Liferay `ROBOTS` structure) | Search engine crawlers |

> All other paths (`/`, `/[lang]`, `/[lang]/products/...`, etc.) are server-rendered HTML pages, not API endpoints.

## Outbound (Who I Call)

Every external service/system this application calls.

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| Liferay DXP (CMS) | POST | `/o/oauth2/token` | OAuth2 client-credentials token (cached per pod) |
| Liferay DXP — Headless Delivery | GET | `/o/headless-delivery/v1.0/...` | Pages, structured content, navigation menus, SEO settings |
| Liferay DXP — Headless Admin List Type | GET | `/o/headless-admin-list-type/v1.0/list-type-definitions/...` | Picklist (list type) entries for form dropdowns/options |
| Liferay DXP — TVS catalog (custom) | GET | `/o/tvs/getProducts`, `/o/tvs/getAllProductsCategories`, `/o/tvs/product-options/...`, `/o/tvs/getProductAttachments/{id}`, `/o/tvs/webcontent/{siteId}/{id}` | Products, categories, options (incl. colours/prices), attachments, web content |
| TVS Lead Submission API (LMS) | POST | `<TVS_LEAD_URL_<COUNTRY>>` (e.g. `https://uat-lms-api.tvsmotor.net/weu/api/lead`) | Submit Contact Us / Become Dealer leads (`Bearer` + `CountryCode` header) |
| Google Tag Manager | GET (script) | `https://www.googletagmanager.com/gtag/js?id=<GAEVENTID>` | Analytics tag load (client-side, lazy) |

## Events & Messaging

**Not applicable.** This service does **not** publish to or subscribe from any message bus or event topic (no Azure Service Bus, Event Hub, Kafka, or queue integration). All integration is synchronous HTTP (see Outbound). This section is retained for dependency-mapping completeness.

### Topics This Service Publishes To
| Topic/Queue | Events | Format |
|-------------|--------|--------|
| — (none) | — | — |

### Topics This Service Subscribes To
| Topic/Queue | Events | Action |
|-------------|--------|--------|
| — (none) | — | — |

## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Liferay DXP | Headless CMS / Commerce | Pages, content, navigation, products, prices, form option picklists | OAuth2 client credentials (`LIFERAY_CLIENT_ID` / `LIFERAY_CLIENT_SECRET`) |
| TVS Lead Submission API (LMS) | Lead management | Receive Contact Us / Become Dealer leads | Bearer token (`TVS_LEAD_TOKEN`) + `CountryCode` header |
| Google Tag Manager | Analytics | Page/event analytics | Container ID (`GAEVENTID`), no secret |
| Azure Key Vault | Secrets management | Source of application secrets (`VAULT_ACCOUNT_NAME`) | Azure AD (`AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET`) |
| Azure Application Gateway | Edge / ingress | TLS termination, routing, cookie affinity, WAF | N/A (infra) |
| Azure Front Door | Global edge | Routing / load balancing across origins (primary + DR) | N/A (infra) |

## Data Storage

| Store | Type | Purpose |
|-------|------|---------|
| Redis | Cache | Optional shared/session cache and rate limiting (config via `REDIS_HOST`/`REDIS_PORT`/`REDIS_PASSWORD`/`REDIS_TLS`) |
| Per-pod in-memory | Cache | Next.js ISR page cache and per-pod OAuth2 token cache |
| Liferay DXP | System of record | All content, product, and catalog data (this service holds no primary database of its own) |

> This service has **no dedicated relational/NoSQL database**. Persistent business data lives in Liferay; the app is stateless apart from caches.

---

## 1. Endpoint Overview

The Next.js service exposes two categories of HTTP surface:

- **Inbound APIs** served by Next.js route handlers under `app/`.
- **Outbound APIs** consumed by the application (Liferay DXP and TVS Lead Submission API).

### 1.1 Inbound endpoint list

| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/contact-submit` | Submit Contact Us lead | None (same-origin) |
| `POST` | `/api/become-dealer-submit` | Submit Become Dealer lead | None (same-origin) |
| `GET`  | `/api/health` | Liveness/readiness probe | None |
| `GET`  | `/health_check/data_source` | Verify Liferay backend reachability | None |
| `GET`  | `/sitemap.xml` | Sitemap (per country) | None |
| `GET`  | `/robots.txt` | Robots policy (per country) | None |

> All other paths under the application are HTML pages rendered by Next.js (`/`, `/[lang]`, `/[lang]/our-products/...`, etc.) and are out of scope of this API specification.

### 1.2 Outbound dependencies

| Provider | Auth | Notes |
| --- | --- | --- |
| Liferay DXP — `o/oauth2/token` | client_credentials | Returns access token; cached per pod. |
| Liferay DXP — Headless Delivery | Bearer | Pages, structured content, navigation menus. |
| Liferay DXP — Headless Admin List Type | Bearer | List type definitions for form options. |
| Liferay DXP — TVS catalog (`o/tvs/...`) | Bearer | Products, categories, options, attachments. |
| TVS Lead Submission API | Bearer + `CountryCode` header | Receives form payloads. |

### 1.3 Rate limits

The application itself does **not** enforce rate limits in code. Edge protection is delegated to **Azure Application Gateway** and any upstream WAF policy. Upstream APIs (Liferay, Lead API) may apply their own quotas — clients should treat any `429` response from the Next.js handler as upstream-originated.

---

## 2. OpenAPI 3.0 Specification (Inbound APIs)

```yaml
openapi: 3.0.3
info:
  title: TVSM IB Next.js — Public API
  description: |
    HTTP endpoints exposed by the TVSM IB Next.js website.
    The site is multi-country; the country is resolved at the edge from the host
    name (e.g. `malta.tvsmotor.com`) or the `country` cookie.
    Secrets are stored as Kubernetes Secrets and never appear in requests.
  version: 1.0.0

servers:
  - url: https://malta.tvsmotor.com
    description: Production — Malta
  - url: https://spain.tvsmotor.com
    description: Production — Spain
  - url: https://portugal.tvsmotor.com
    description: Production — Portugal
  - url: https://uat-malta.tvsmotor.net
    description: UAT — Malta
  - url: https://uat-spain.tvsmotor.net
    description: UAT — Spain
  - url: https://uat-portugal.tvsmotor.net
    description: UAT — Portugal

tags:
  - name: forms
    description: Lead-capture form submissions
  - name: health
    description: Health and readiness checks
  - name: seo
    description: SEO assets

paths:

  /api/contact-submit:
    post:
      tags: [forms]
      summary: Submit a Contact Us lead
      description: |
        Validates and forwards a Contact Us form submission to the TVS Lead
        Submission API. Country and language are derived from cookies set by
        the edge middleware.
      operationId: submitContactUs
      parameters:
        - in: cookie
          name: country
          schema: { type: string }
          required: false
          description: Lower-case country code; set automatically by middleware.
        - in: cookie
          name: langCode
          schema: { type: string }
          required: false
        - in: cookie
          name: fullLangCode
          schema: { type: string }
          required: false
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ContactUsNextPayload'
            examples:
              malta:
                summary: Malta English request
                value:
                  firstName: Alice
                  lastName: Mizzi
                  email: alice@example.com
                  phone: '99001122'
                  city: VLT
                  typeRequested: SALES
                  message: I would like a brochure for the Apache RTR.
                  termsAndConditions: true
                  communicationConsent: true
                  dialCode: 356
                  mandatoryFields:
                    - firstName
                    - email
                    - phone
                    - city
                    - termsAndConditions
      responses:
        '200':
          description: Submission processed (check `success` for upstream status).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LeadSubmissionResponse'
              examples:
                success:
                  value:
                    success: true
                    apiStatus: 200
                    apiData:
                      lead_id: 1234567
                      message: Lead created
        '400':
          description: Invalid input or malformed JSON.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ApiError'
              examples:
                bad_json:
                  value:
                    error: Invalid input
        '500':
          description: Upstream Lead API failure.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LeadSubmissionResponse'
              examples:
                upstream:
                  value:
                    success: false
                    error: 'Network error: ECONNRESET'

  /api/become-dealer-submit:
    post:
      tags: [forms]
      summary: Submit a Become Dealer lead
      description: |
        Validates and forwards a Become Dealer form submission to the TVS Lead
        Submission API.
      operationId: submitBecomeDealer
      parameters:
        - in: cookie
          name: country
          schema: { type: string }
          required: false
        - in: cookie
          name: langCode
          schema: { type: string }
          required: false
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BecomeDealerNextPayload'
            examples:
              italy:
                summary: Italy request
                value:
                  firstName: Marco
                  lastName: Rossi
                  role: Owner
                  email: marco@example.com
                  phone: '3331122334'
                  individualDialCode: 39
                  companyName: Rossi Motors
                  companyAddress: Via Roma 1
                  companyCity: Milano
                  companyZipCode: '20100'
                  companyProvince: MI
                  companyNation: Italy
                  companyPhone: '0212345678'
                  companyDialCode: 39
                  companyWebsite: https://rossi-motors.example.com
                  numberOfEmployees: '10-50'
                  yearsOfActivity: '5'
                  operateIn: 'Moto,Auto'
                  additionInformation: Looking to expand the showroom.
                  termsAndConditions: true
                  communicationConsent: true
                  mandatoryFields:
                    - firstName
                    - email
                    - phone
                    - companyName
                    - termsAndConditions
      responses:
        '200':
          description: Submission processed.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/LeadSubmissionResponse' }
        '400':
          description: Invalid input.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ApiError' }
        '500':
          description: Upstream failure.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/LeadSubmissionResponse' }

  /api/health:
    get:
      tags: [health]
      summary: Liveness/readiness probe
      operationId: healthCheck
      responses:
        '200':
          description: Pod is healthy.
          content:
            text/plain:
              schema: { type: string, example: OK }

  /health_check/data_source:
    get:
      tags: [health]
      summary: Backend (Liferay) reachability probe
      description: |
        Calls `${API_BASE_URL}/health_check/data_source` with a 10-second timeout.
      operationId: dataSourceHealth
      responses:
        '200':
          description: Backend reachable.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, example: OK }
        '500':
          description: API_BASE_URL is not configured.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ApiError' }
        '503':
          description: Backend unreachable, timed out, or returned an error.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/ApiError' }
              examples:
                timeout:
                  value: { error: 'Health check timeout' }
                upstream_5xx:
                  value: { error: 'Health check failed with status: 502' }

  /sitemap.xml:
    get:
      tags: [seo]
      summary: Country sitemap
      description: |
        Returns the sitemap configured in Liferay under the `SITEMAP` page
        structure (`SEO_PAGES_STRUCTURE` → `SeoData`). Per-country.
      operationId: getSitemap
      responses:
        '200':
          description: Sitemap XML.
          content:
            application/xml:
              schema: { type: string }

  /robots.txt:
    get:
      tags: [seo]
      summary: Country robots policy
      description: |
        Returns the `robots.txt` configured in Liferay under the `ROBOTS` page
        structure (`SEO_PAGES_STRUCTURE` → `SeoData`).
      operationId: getRobots
      responses:
        '200':
          description: Robots policy.
          content:
            text/plain:
              schema: { type: string }

components:
  schemas:

    ApiError:
      type: object
      properties:
        error: { type: string, description: Error message }
      required: [error]

    LeadSubmissionResponse:
      type: object
      description: Envelope returned by lead submission endpoints.
      properties:
        success: { type: boolean }
        apiStatus:
          type: integer
          description: HTTP status from the upstream Lead API.
        apiData:
          type: object
          additionalProperties: true
          description: Raw upstream response body.
        error:
          type: string
          description: Present when `success` is false.

    ContactUsInputs:
      type: object
      required:
        - firstName
        - lastName
        - email
        - phone
        - city
        - typeRequested
        - message
        - termsAndConditions
        - communicationConsent
      properties:
        firstName: { type: string }
        lastName: { type: string }
        email: { type: string, format: email }
        phone: { type: string }
        city: { type: string, description: City code from CMS list (e.g. VLT). }
        typeRequested: { type: string, description: Enquiry type code from CMS list. }
        message: { type: string }
        termsAndConditions: { type: boolean }
        communicationConsent: { type: boolean }

    ContactUsNextPayload:
      allOf:
        - $ref: '#/components/schemas/ContactUsInputs'
        - type: object
          required: [dialCode, mandatoryFields]
          properties:
            dialCode:
              type: integer
              description: International dial code from intl-tel-input (e.g. 356).
            mandatoryFields:
              type: array
              items: { type: string }
              description: Names of fields the client treated as mandatory.

    BecomeDealerInputs:
      type: object
      required:
        - firstName
        - lastName
        - role
        - email
        - phone
        - companyName
        - companyAddress
        - companyCity
        - companyZipCode
        - companyProvince
        - companyNation
        - companyPhone
        - companyWebsite
        - numberOfEmployees
        - yearsOfActivity
        - operateIn
        - additionInformation
        - termsAndConditions
        - communicationConsent
      properties:
        firstName: { type: string }
        lastName: { type: string }
        role: { type: string }
        email: { type: string, format: email }
        phone: { type: string }
        companyName: { type: string }
        companyAddress: { type: string }
        companyCity: { type: string }
        companyZipCode: { type: string }
        companyProvince: { type: string }
        companyNation: { type: string }
        companyPhone: { type: string }
        companyWebsite: { type: string }
        numberOfEmployees: { type: string }
        yearsOfActivity: { type: string }
        operateIn:
          type: string
          description: Comma-separated list of operating segments (e.g. "Moto,Auto").
        additionInformation: { type: string }
        termsAndConditions: { type: boolean }
        communicationConsent: { type: boolean }

    BecomeDealerNextPayload:
      allOf:
        - $ref: '#/components/schemas/BecomeDealerInputs'
        - type: object
          required: [individualDialCode, companyDialCode, mandatoryFields]
          properties:
            individualDialCode: { type: integer }
            companyDialCode: { type: integer }
            mandatoryFields:
              type: array
              items: { type: string }

  securitySchemes:
    # No security schemes are applied to inbound endpoints.
    sameOriginOnly:
      type: apiKey
      in: header
      name: Origin
      description: |
        Inbound endpoints are not authenticated. They are expected to be
        called from the same origin as the website. WAF / Application Gateway
        is responsible for edge-level controls.
```

---

## 3. Inbound API Details

### 3.1 `POST /api/contact-submit`

#### Authentication
None at the application layer. Edge protection (Azure Application Gateway) enforces TLS, optionally WAF. Same-origin invocation is expected.

#### Headers

| Header | Required | Notes |
| --- | --- | --- |
| `Content-Type: application/json` | yes | Body is JSON. |
| `Cookie: country=<lc>; langCode=<lc>; fullLangCode=<lc>` | optional | Set by middleware. |

#### Validation rules

- The body must be valid JSON or the handler responds `400 Invalid input`.
- Field-level validation is performed on the **client** (`utilFuctions.validateAllFields`) using the `FieldMap<T>` derived from CMS:
  - `mandatory: true` → empty value triggers `errorMsgs[0]`.
  - Each entry in `validationRegex[]` is applied; failure picks an indexed error message (`errorMsgs[i+1]` if mandatory else `errorMsgs[i]`).
  - Regexes are authored per country in Liferay (`FormFieldRegex`) and are split by `,(?= ?\/)` so commas inside regex literals are preserved.
- The server currently trusts the client for required-field enforcement; `mandatoryFields` is informational.

#### Sample request

```http
POST /api/contact-submit HTTP/1.1
Host: malta.tvsmotor.com
Content-Type: application/json
Cookie: country=malta; langCode=en; fullLangCode=en_US

{
  "firstName": "Alice",
  "lastName": "Mizzi",
  "email": "alice@example.com",
  "phone": "99001122",
  "city": "VLT",
  "typeRequested": "SALES",
  "message": "I would like a brochure for the Apache RTR.",
  "termsAndConditions": true,
  "communicationConsent": true,
  "dialCode": 356,
  "mandatoryFields": ["firstName","email","phone","city","termsAndConditions"]
}
```

#### Sample success response

```json
{
  "success": true,
  "apiStatus": 200,
  "apiData": {
    "lead_id": 1234567,
    "message": "Lead created"
  }
}
```

#### Sample error responses

```json
HTTP/1.1 400
{ "error": "Invalid input" }
```

```json
HTTP/1.1 500
{ "success": false, "error": "Network error: ECONNRESET" }
```

#### Upstream payload mapping

```jsonc
{
  "customer_name": "Alice Mizzi",
  "mobile_number": "99001122",
  "email_id": "alice@example.com",
  "enquiry_date": "2026-05-28 10:23:45.123",
  "city": "VLT",
  "language_code": "EN",
  "country_code": "MT",
  "source_id": 2,
  "brand_code": 0,
  "customer_voice": "I would like a brochure for the Apache RTR.",
  "extra_attributes": [
    { "attribute_name": "first_name", "attribute_value": "Alice", "attribute_description": "Customer first name" },
    { "attribute_name": "last_name",  "attribute_value": "Mizzi", "attribute_description": "Customer last name"  },
    { "attribute_name": "phone_country_code", "attribute_value": 356, "attribute_description": "Dial code of selected country" },
    { "attribute_name": "request_type", "attribute_value": "SALES", "attribute_description": "Type of request" },
    { "attribute_name": "city_code", "attribute_value": "VLT", "attribute_description": "Selected city code" }
  ],
  "additional_details": {
    "enquiry_type": "Contact Us Enquiry",
    "marketing_consent": 1,
    "user_consent": 1
  }
}
```

---

### 3.2 `POST /api/become-dealer-submit`

#### Authentication
None at the application layer.

#### Headers
Same as Contact Us.

#### Validation rules
Same engine as Contact Us; field set is from `BecomeDealerInputs`.

> Implementation note: at present this handler hard-codes `country_code: 'IT'` in the upstream payload. See LLD §17 (Open Questions) — should be derived from the `country` cookie like Contact Us.

#### Sample request

```http
POST /api/become-dealer-submit HTTP/1.1
Host: italy.tvsmotor.com
Content-Type: application/json
Cookie: country=italy; langCode=it

{
  "firstName": "Marco", "lastName": "Rossi",
  "role": "Owner",
  "email": "marco@example.com", "phone": "3331122334", "individualDialCode": 39,
  "companyName": "Rossi Motors",
  "companyAddress": "Via Roma 1", "companyCity": "Milano",
  "companyZipCode": "20100", "companyProvince": "MI", "companyNation": "Italy",
  "companyPhone": "0212345678", "companyDialCode": 39,
  "companyWebsite": "https://rossi-motors.example.com",
  "numberOfEmployees": "10-50", "yearsOfActivity": "5",
  "operateIn": "Moto,Auto",
  "additionInformation": "Looking to expand the showroom.",
  "termsAndConditions": true, "communicationConsent": true,
  "mandatoryFields": ["firstName","email","phone","companyName","termsAndConditions"]
}
```

#### Sample success response

```json
{ "success": true, "apiStatus": 200, "apiData": { "lead_id": 7654321 } }
```

#### Upstream payload mapping (key fields)

| Upstream field | Source |
| --- | --- |
| `customer_name` | `firstName + " " + lastName` |
| `mobile_number` | `phone` |
| `email_id` | `email` |
| `customer_voice` | `additionInformation` |
| `country_code` | `'IT'` (current implementation) |
| `language_code` | `langCode` (uppercased) |
| `additional_details.enquiry_type` | `Dealer Enquiry` |
| `extra_attributes` | name, role, dial codes, full company block, segment list, employees, years active |

---

### 3.3 `GET /api/health`

- **Auth:** none.
- **Response:** `200 OK` with body `OK` (`text/plain`).
- **Use:** Kubernetes readiness/liveness probes.

```http
GET /api/health HTTP/1.1
Host: malta.tvsmotor.com
```

```
HTTP/1.1 200 OK
Content-Type: text/plain

OK
```

---

### 3.4 `GET /health_check/data_source`

- **Auth:** none.
- **Behavior:** Calls `${API_BASE_URL}/health_check/data_source` with `signal: AbortSignal.timeout(10000)`.
- **Status codes:**
  - `200` → backend reachable.
  - `500` → `API_BASE_URL` not configured.
  - `503` → backend returned non-2xx, timed out, or threw.

```http
GET /health_check/data_source HTTP/1.1
```

```json
HTTP/1.1 200 OK
{ "status": "OK" }
```

```json
HTTP/1.1 503 Service Unavailable
{ "error": "Health check timeout" }
```

---

### 3.5 `GET /sitemap.xml`

- **Auth:** none.
- **Source:** Liferay page-structure entry `SITEMAP` → child `SEO_PAGES_STRUCTURE` → field `SeoData`.
- **Response:** raw XML, `200 OK`.
- Logs an `error` entry if the structure is missing.

```http
GET /sitemap.xml HTTP/1.1
Host: malta.tvsmotor.com
```

---

### 3.6 `GET /robots.txt`

- **Auth:** none.
- **Source:** Liferay page-structure entry `ROBOTS` → `SEO_PAGES_STRUCTURE` → field `SeoData`.
- **Response:** plain text robots policy, `200 OK`.

---

## 4. Outbound API Dependencies

### 4.1 Liferay OAuth2

```http
POST /o/oauth2/token HTTP/1.1
Host: <API_BASE_URL host>
Content-Type: application/x-www-form-urlencoded

client_id=<LIFERAY_CLIENT_ID>&client_secret=<LIFERAY_CLIENT_SECRET>&grant_type=client_credentials
```

Response:
```json
{ "access_token": "<jwt>", "token_type": "Bearer", "expires_in": 3600 }
```

### 4.2 Liferay Headless Delivery

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/o/headless-delivery/v1.0/content-structures/{id}/structured-contents?fields=id,key,contentFields,friendlyUrlPath,id,title,name` | GET | Structured content for a structure. |
| `/o/headless-delivery/v1.0/navigation-menus/{id}?fields=id,navigationMenuItems.link,navigationMenuItems.name` | GET | Footer/header navigation menu items. |
| `/o/headless-delivery/v1.0/sites/{siteId}/site-pages/{friendlyUrl}?fields=pageSettings.seoSettings,title,uuid` | GET | Page SEO settings. |

All calls include:
- `Authorization: Bearer <access_token>`
- `Accept-Language: <fullLangCode>` (e.g. `en-US`)
- `Site-Id: <LIFERAY_SITE_ID_<COUNTRY>>` (when set)

### 4.3 Liferay Headless Admin List Type

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/o/headless-admin-list-type/v1.0/list-type-definitions/{id}` | GET | List type by ID. |
| `/o/headless-admin-list-type/v1.0/list-type-definitions/by-external-reference-code/{erc}?fields=listTypeEntries.key,listTypeEntries.name,listTypeEntries.name_i18n` | GET | List type by ERC (used to populate form options). |

### 4.4 Liferay TVS catalog (custom)

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/o/tvs/getProducts?searchCategory={cat}` | GET | Product list for a category. |
| `/o/tvs/getAllProductsCategories` | GET | All product categories. |
| `/o/tvs/product-options/batch?productIds={ids}` | GET | Product options for multiple products. |
| `/o/tvs/product-options/{id}/options` | GET | Product options for a single product. |
| `/o/tvs/getProductAttachments/{id}` | GET | Brochures and other attachments. |
| `/o/tvs/webcontent/{siteId}/{id}` | GET | Single web content by ID. |

### 4.5 TVS Lead Submission API

```http
POST <TVS_LEAD_URL_<COUNTRY>> HTTP/1.1
Authorization: Bearer <TVS_LEAD_TOKEN>
CountryCode: <ALPHA2_CODE_<COUNTRY>>
Content-Type: application/json

{ ... mapped payload ... }
```

Response: opaque to this service. The `apiStatus` and `apiData` fields are forwarded as-is in the inbound response envelope.

---

## 5. Error Reference

| HTTP | Where | When | Body shape |
| --- | --- | --- | --- |
| 200 | Inbound forms | Lead submission processed (check `success`). | `LeadSubmissionResponse` |
| 200 | `/api/health` | Pod healthy. | `OK` (text) |
| 200 | `/health_check/data_source` | Backend reachable. | `{ status: 'OK' }` |
| 200 | `/sitemap.xml`, `/robots.txt` | SEO data resolved. | XML / text |
| 400 | Inbound forms | Body missing or malformed. | `{ error: 'Invalid input' }` |
| 500 | `/api/contact-submit`, `/api/become-dealer-submit` | Network/transport error reaching Lead API. | `{ success: false, error: '<reason>' }` |
| 500 | `/health_check/data_source` | `API_BASE_URL` not configured. | `{ error: 'API_BASE_URL not configured' }` |
| 503 | `/health_check/data_source` | Upstream timeout / non-2xx / network error. | `{ error: '<reason>' }` |

The application does not return `401`/`403` on inbound endpoints — they are public.

---

## 6. Validation Rules (Authoritative Reference)

Validation is metadata-driven. The CMS provides per-country `FormField` records with:

```ts
{
  label: string;
  name: string;             // matches the form's input name
  options: { key: string; name: string }[];
  placeholder: string;
  validationRegex: string[]; // 0..N regex patterns
  errorMsgs: string[];       // semicolon-separated message list
  mandatory: boolean;
}
```

Algorithm (`getFieldError`):

1. If `mandatory && !value` → return `errorMsgs[0]`.
2. Else for each `regex` at index `i`:
   - Resolve message: when `mandatory` use `errorMsgs[i + 1]`, else `errorMsgs[i]`.
   - If `regex.test(value) === false` → return that message.
3. Return `''` (valid).

Sample regex catalogue (typical):

| Field | Regex | Message |
| --- | --- | --- |
| `email` | `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$` | `Please enter a valid email` |
| `phone` | `^[0-9 ]{6,15}$` | `Please enter a valid phone number` |
| `companyZipCode` | `^[0-9]{4,10}$` | `Please enter a valid ZIP` |

Actual regexes are authored per country in Liferay; this table is illustrative only.

---

## 7. Rate Limits

The Next.js application does not enforce HTTP rate limits. Operators rely on:

- Azure Application Gateway and any WAF rules in front of it.
- Liferay's quotas / load balancer policies for outbound calls.
- Lead API's own throttling (responses are surfaced unchanged).

If rate limiting is required at the application layer in the future, candidates include `next.js/middleware` with a token bucket against Redis or AppGw rate-limit rules.

---

## 8. Environment Configuration Used by APIs

| Variable | Used by | Purpose |
| --- | --- | --- |
| `API_BASE_URL`, `API_BASE_URL_<COUNTRY>` | Liferay client, `/health_check/data_source` | Base URL for Liferay calls. |
| `LIFERAY_CLIENT_ID`, `LIFERAY_CLIENT_SECRET` | `getAdminToken` | OAuth2 client credentials. |
| `LIFERAY_SITE_ID_<COUNTRY>` | Liferay client | `Site-Id` header. |
| `TVS_LEAD_URL_<COUNTRY>` | `leadSubmission` | Lead API URL. |
| `TVS_LEAD_TOKEN` | `leadSubmission` | Lead API bearer token. |
| `ALPHA2_CODE_<COUNTRY>` | `leadSubmission` | `CountryCode` header. |
| `ALLOWED_ROUTES_<COUNTRY>` | Middleware | Inbound page allow-list (does not affect API endpoints in `/api/*`). |
| `DEFAULT_LANGUAGE_<COUNTRY>` | Middleware | `/` → `/<lang>` redirect. |
| `FULL_LANG_CODES_<COUNTRY>` | Middleware, Liferay client | Locale resolution. |

> Per-country routing for inbound endpoints uses cookies set by `proxy.ts`; no path prefix is required.

---

## 9. Known Limitations & Open Items

- Server-side enforcement of `mandatoryFields` is not yet implemented — the route trusts the client's validation.
- `become-dealer-submit` currently sends `country_code: 'IT'` regardless of the cookie.
- No retries or circuit breakers around outbound calls.
- No application-level rate limiting; relies on edge.
- Form route handlers `console.log` the incoming payloads — review for PII redaction before production roll-outs in regulated regions.

---

## 10. Curl Cookbook

```bash
# Contact Us
curl -X POST https://malta.tvsmotor.com/api/contact-submit \
  -H "Content-Type: application/json" \
  -b "country=malta; langCode=en; fullLangCode=en_US" \
  -d '{
    "firstName":"Alice","lastName":"Mizzi",
    "email":"alice@example.com","phone":"99001122",
    "city":"VLT","typeRequested":"SALES",
    "message":"Brochure please",
    "termsAndConditions":true,"communicationConsent":true,
    "dialCode":356,
    "mandatoryFields":["firstName","email","phone","city","termsAndConditions"]
  }'

# Become a Dealer
curl -X POST https://italy.tvsmotor.com/api/become-dealer-submit \
  -H "Content-Type: application/json" \
  -b "country=italy; langCode=it" \
  -d '{ ...payload as in §3.2... }'

# Health
curl https://malta.tvsmotor.com/api/health
curl https://malta.tvsmotor.com/health_check/data_source
curl https://malta.tvsmotor.com/sitemap.xml
curl https://malta.tvsmotor.com/robots.txt
```

---

## 11. Postman / OpenAPI

The YAML in §2 can be saved as `openapi.yaml` and imported directly into Postman, Swagger Editor, or Stoplight. To generate a client SDK:

```bash
npx @openapitools/openapi-generator-cli generate \
  -i docs/openapi.yaml -g typescript-fetch -o sdk/
```

(Apply environment-specific `servers[].url` before generating.)

---

End of API specification.

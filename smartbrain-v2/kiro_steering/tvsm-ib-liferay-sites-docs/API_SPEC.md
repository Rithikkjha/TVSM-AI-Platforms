# API Specification — TVS-Website-Nepal

**Document Type:** API Specification (OpenAPI-aligned)
**Repository:** `TVS-Website-Nepal`
**Audience:** Integration partners, frontend developers, vendor engineers
**Last Reviewed:** May 2026

> No tokens, secrets, or internal credentials are embedded. Production hostnames (origins) are listed only because they are already public and are required for any integration partner to know which domains can call the APIs (CORS allowlist).

---

## 0. Service Identity & Dependency Map

> This section provides the dependency-mapping view: who this service is, who calls it (inbound), and what it calls (outbound). Detailed per-endpoint reference continues from §5. Fields marked _TBD_ must be filled by the owning team before publishing.

### 0.1 Service Identity

| Field | Value |
|-------|-------|
| Service Name | `TVS-Website-Nepal` (Liferay DXP international websites + forms platform) |
| Repo | `github.com/tvsmotorcompany/TVS-Website-Nepal` |
| Team | Digital & AI (D&AI) Engineering — International Websites |
| Tech Lead | _TBD_ |
| Deployment | Azure Kubernetes Service (AKS); container `liferay/dxp:2023.q4.0`; Azure Container Registry; CI/CD via Azure DevOps (`azure-pipelines/`) |
| Base URL (prod) | Per market, e.g. `https://nepal.tvsmotor.com`, `https://mexico.tvsmotor.com` (full list in §2 / §3.4) |
| Base URL (UAT) | `https://uat-<market>.tvsmotor.net` |
| Runtime | Liferay DXP 7.4 (`dxp-7.4-u62`), JAX-RS Whiteboard on Tomcat `:8080` |

### 0.2 Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | _TBD_ | _TBD_ |
| Tech Lead | _TBD_ | _TBD_ |
| Dev Team | D&AI Engineering — International Websites | Slack: `#tvs-website-nepal-eng` |
| Platform / DevOps | _TBD (D&AI Engineering)_ | Slack: `#tvs-website-nepal-ops` |
| On-call | Rotational | PagerDuty/Opsgenie schedule: _TBD_ |
| Vendor (Liferay) | Liferay DXP (commercial subscription) | _TBD_ |
| Issue Tracker | Atlassian Jira project `D2C` | https://tvsmotorcompany.atlassian.net |

### 0.3 Inbound — API Endpoints + Who Calls Them

Endpoints this service exposes. Full parameter/response detail is in §5–§6. All are reachable under `/o/<appBase>/...` on each market host.

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/o/tvs/maps`, `/o/tvs/map`, `/o/tvs/dealers` | Guest + geo token | Dealer-locator / reverse-geo / autocomplete | Market website frontends (dealer locator) |
| GET | `/o/tvs/loc`, `/o/tvs/liferay` | Guest | Issue geo / Liferay OAuth tokens | Frontend + server-internal |
| GET | `/o/tvs/addressFields`, `/o/tvs/liferayDealers`, `/o/tvs/getChannel` | Guest | Address metadata, dealer master, channel id | Market website frontends |
| GET | `/o/tvs/getAllProductsCategories`, `/o/tvs/getProducts`, `/o/tvs/getProductDetails/{id}`, `/o/tvs/getProduct/{id}`, `/o/tvs/getProductImages/{id}`, `/o/tvs/getProductSpecs/{id}` | Guest | Product catalog / PDP composition | Market website frontends (PLP/PDP) |
| PATCH | `/o/tvs/updateSkuPrice/{skuId}` | Guest at HTTP layer — **admin, gate upstream** | Update SKU price (audited) | Admin/ops tooling (must be gated by gateway/VPN) |
| GET/POST | `/o/tvs/language/{key}`, `/o/tvs/language/keys` | Guest | Language-key lookup (single/bulk) | Market website frontends |
| GET | `/o/tvs/webcontent/{groupId}/{articleId}` | Guest | Web content as JSON | Market website frontends |
| GET | `/o/tvs/product-options/{productId}/options`, `/o/tvs/product-options/batch` | Guest | Product options + custom attrs | Market website frontends (PDP/exchange forms) |
| POST | `/o/tvs/form/*` (20 form endpoints — see §5.2) | Guest + CORS allowlist + `X-Azure-ClientIP`, rate-limited | Lead/enquiry/OTP/partner form intake | Market website frontends (browser); Azure Front Door injects `X-Azure-ClientIP` |
| GET | `/o/list/cities`, `/o/list/dealers` | Guest | LATAM city/dealer reference (LCS-backed) | LATAM market frontends |

> **Auth note:** all endpoints are anonymous at the HTTP layer (`auth.verifier.guest.allowed=true`, `liferay.access.control.disable=true`). `Forms.Rest` adds a CORS allowlist (§3.3) and per-IP rate limiting (§4). There is no JWT/API-key for callers; the platform authenticates its own **outbound** calls (§0.4 / §9).

### 0.4 Outbound — Who This Service Calls

Systems this service depends on. Full detail in §9.

| Target | Method | Endpoint / Path | Purpose |
|--------|--------|-----------------|---------|
| Azure Identity (AAD) | POST | `${azure.endpoint}` (client-credentials) | Acquire bearer token for LCS calls (`TokenUtil` → `AzureTokenInfo`) |
| LCS (Lead Capture System) | POST | `${<region>.lcs.url}` + form path token (see §9.2) | Forward every form submission (leads, feedback, partner, OTP) |
| LCS OTP (`tvsotpify`) | POST | `/tvsotpify/v1/GenerateOtp`, `/VerifyOtp`, `/SendLeadAcknowledgement` | OTP generate/verify + lead acknowledgement |
| Dealer locator (`ib_api.latlong.in`) | GET | `/location_details`, `/autocomplete.json`, `/brands/{brand}/search.json` | Geo lookup / autocomplete / nearby dealers |
| Liferay Headless Commerce | GET/PATCH | `/o/headless-commerce-admin-catalog/*`, `/o/headless-commerce-delivery-catalog/*`, `/o/c/locations`, `/o/c/dealerns`, `/o/oauth2/token` | Catalog, SKU, images, address/dealer objects, OAuth |
| Plivo | POST | Plivo Java SDK (v5.18) | SMS delivery on OTP path |

### 0.5 Events & Messaging

**Not applicable in the current architecture.** This platform is **synchronous HTTPS only** — form submissions are forwarded to LCS in-request; there is no Azure Service Bus, Kafka, or event topic published or consumed by these modules today.

- Publishes to: _none_
- Subscribes to: _none_

> **Roadmap (from LLD §error-handling):** an async queue + retry layer for LCS forwarding is noted as future work. If/when added, document the queue/topic and event shapes here.

### 0.6 External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| LCS (Lead Capture System) | Lead/CRM intake | Persist all form submissions (leads, feedback, partner, service) | Azure-issued bearer (client credentials) |
| Azure AD / Identity | Identity | OAuth2 token issuance for LCS (and dealer locator where configured) | Client credentials (`<region>.azure.id/secret/resource`) |
| Plivo | SMS gateway | OTP + lead-acknowledgement SMS | API key/secret |
| `ib_api.latlong.in` | Dealer locator / geo API | Reverse-geo, autocomplete, nearby dealers | Client-credentials token (`IbCredentials` via `TokenUtil`) |
| Liferay Headless Commerce | Internal platform API | Product catalog, SKU pricing, images, dealer/location objects | Liferay OAuth2 (per `Company-Id`) |

### 0.7 Data & Storage

This repo **does not own a relational schema**; all data is managed by Liferay and its Commerce engine (see LLD §data-storage).

| Store | Type | Purpose |
|-------|------|---------|
| Liferay portal DB | MySQL / Oracle (prod/UAT), HSQLDB (local) | Portal + Commerce tables (`User_`, `JournalArticle`, `CommerceCatalog`, `CPDefinition`, `CPInstance`, `CommercePrice*`, Expando*, etc.) — managed by Liferay upgrades, no custom DDL |
| Liferay Commerce catalog | Within portal DB | Products, SKUs, prices, options |
| Expando tables | Within portal DB | Product custom fields consumed by renderer modules |
| Elasticsearch 7 | Search index | Liferay search backend (remote in UAT/prod, embedded local); no custom mappings authored here |
| Form submission PII | _Not persisted locally_ | Forwarded to LCS; only ephemeral in logs — review GDPR/data-residency before adding fields |

---

## 1. Document Map

| Section | Contents |
|---------|----------|
| §0 | Service identity, ownership, inbound/outbound dependency map, events, integrations, data storage |
| §2 | Server URLs and global conventions |
| §3 | Authentication, headers, CORS |
| §4 | Rate limiting |
| §5 | Endpoint catalog (grouped by JAX-RS application) |
| §6 | Detailed reference per endpoint |
| §7 | Common error envelope and HTTP status code table |
| §8 | Validation rules (server-side, authoritative) |
| §9 | External APIs the platform calls (outbound dependencies) |
| §10 | Sample requests and responses |
| §11 | OpenAPI 3.0 skeleton (YAML) |

---

## 2. Servers and Global Conventions

The platform exposes three JAX-RS applications via Liferay's JAX-RS Whiteboard. All endpoints are reachable under `/o/<applicationBase>/...` on the public website host of each market.

| JAX-RS Application | Source | Application Base | Public path prefix |
|--------------------|--------|------------------|--------------------|
| `Tvs.Rest` | `modules/Controller` (`TvsControllerApplication`) | `/tvs` | `/o/tvs/...` |
| `Forms.Rest` | `modules/FormsDetails` (`FormsDetailsApplication`) | `/tvs/form` | `/o/tvs/form/...` |
| `TvsLatam.Rest` | `modules/LatamApis` (`LatamApisApplication`) | `/list` | `/o/list/...` |

**Server URLs (public, per market):**

```
https://nepal.tvsmotor.com           # Production — Nepal
https://mexico.tvsmotor.com          # Production — Mexico
https://colombia.tvsmotor.com        # Production — Colombia
https://germany.tvsmotor.com         # Production — Germany
https://france.tvsmotor.com          # Production — France
https://italy.tvsmotor.com           # Production — Italy
https://turkey.tvsmotor.com          # Production — Turkey
https://saudi.tvsmotor.com           # Production — Saudi Arabia
... (full list in §3.4)
https://uat-<market>.tvsmotor.net    # UAT mirror, e.g. uat-nepal.tvsmotor.net
```

The full set of recognized origins lives in `modules/FormsDetails/src/main/resources/allowed-origins.txt`.

**Conventions:**

| Aspect | Value |
|--------|-------|
| Content type (request) | `application/json; charset=utf-8` for all POST endpoints |
| Content type (response) | `application/json; charset=utf-8` |
| Character set | UTF-8 throughout |
| Body style | JSON object; arrays only for `/o/tvs/language/keys` |
| Date / time | ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`) — used in finance & campaign forms |
| `null` | Acceptable for optional fields; omit preferred |

---

## 3. Authentication, Headers, CORS

### 3.1 Authentication

The endpoints are **public to anonymous users** at the HTTP layer:

- `auth.verifier.guest.allowed=true` and `liferay.access.control.disable=true` are set on each Application class.
- There is no API-key, OAuth, or JWT requirement for callers (the website's own browser).
- **Server-side, the platform itself authenticates outbound calls** to LCS, dealer-locator, and Liferay headless commerce APIs (see §9). That auth is opaque to the client.

If you are a backend partner calling these endpoints from outside a browser, you do not need a token — but you do need to be on the CORS allowlist or to be exempt from CORS (server-to-server).

### 3.2 Standard headers

| Header | Required | Used by | Purpose |
|--------|----------|---------|---------|
| `Content-Type: application/json` | yes (POST) | All POST endpoints | Body parser |
| `Accept-Language` | optional | `Tvs.Rest` (language, web content, product options); `Forms.Rest` OTP endpoints | Language selection (`en-US`, `es-ES`, `de-DE`, `tr-TR`, etc.) |
| `Site-Id` | conditional | Most `Tvs.Rest` and `Forms.Rest` endpoints | Liferay site ID; falls back to `44180` if omitted |
| `Company-Id` | conditional | `Tvs.Rest` catalog endpoints | Liferay company ID; falls back to `20097` if omitted |
| `Channel-Id` | only for `getProductImages` | `/o/tvs/getProductImages/{id}` | Liferay Commerce channel id |
| `Country-Code` | optional | `Forms.Rest` partner endpoints | Overrides country derived from `Site-Id` |
| `X-Azure-ClientIP` | server-injected | `Forms.Rest` rate limiter | Set by Azure Front Door / WAF; required for POSTs |
| `Origin` | (browser sets) | `Forms.Rest` CORS filter | Validated against allowlist |

### 3.3 CORS

Implemented in `lcsforms.application.CustomCorsFilter`:

- Allowed origins are loaded from `allowed-origins.txt` (verbatim host match after stripping `http(s)://`).
- Allowed methods: `POST`, `OPTIONS`.
- Allowed request headers: `Site-Id`, `Country-Code`, `Accept-Language`, `Content-Type`.
- `Access-Control-Allow-Credentials: true` is returned.
- Requests with a missing `Origin` are rejected with `403 Forbidden: Origin header missing`.
- Origins not in the allowlist are rejected with `403 Forbidden: Invalid Origin`.

### 3.4 CORS allowlist (production + UAT)

Production hosts (`*.tvsmotor.com`):

```
mexico, ib-cms, germany, guatemala, colombia, honduras, europe, france, haiti,
nicaragua, paraguay, uruguay, italy, turkey, ib-cms-me, www.tvsmotor-italia.com,
tvsmotor-italia.com, turkiye, partner-ib-cms, partner, saudi, georgia,
azerbaijan, russia, lebanon, tech, tech-cms, bangladesh, nepal
```

UAT hosts (`uat-*.tvsmotor.net`): same set plus `uat-ib-cms`, `uat-techbytes`, `uat-techbytes-cms`, `uat-partner`, `uat-partner-ib-cms`.

> If your integration is rejected with `403 Forbidden: Invalid Origin`, your domain isn't in `allowed-origins.txt`. Adding a domain requires a code change + redeploy.

---

## 4. Rate Limiting

Implemented in `lcsforms.application.RateLimitFilter` and applies to **all POST methods on `Forms.Rest`** (i.e. every `/o/tvs/form/*` endpoint).

| Parameter | Value |
|-----------|-------|
| Window | 5 minutes (`WINDOW_SIZE_MS = 300_000`) |
| Max requests per window | 20 (`MAX_REQUESTS = 20`) |
| Bucket key | `<X-Azure-ClientIP>|<request path>` |
| Tracker | In-memory `ConcurrentHashMap` per JVM (per pod) |
| Map cap | 5000 entries; if exceeded → `503 Server busy` |
| Cleanup | Background scheduler every 60 s |

**Responses:**

| Condition | HTTP | Body |
|-----------|------|------|
| Missing/blank `X-Azure-ClientIP` | `403` | `{"error":"Access denied. Invalid request source."}` |
| Map saturated | `503` | `{"error":"Server busy. Please try again later."}` |
| Quota exceeded | `429` | `{"error":"Too many requests. Please try again later."}` plus `Retry-After: 60` |

Rate limiting is **per pod**. Across N replicas, the effective limit is approximately N × 20 per 5 minutes for the same client + path. Plan accordingly for synthetic monitoring.

`Tvs.Rest` (`/o/tvs/...` excluding `/form`) and `TvsLatam.Rest` (`/o/list/...`) are **not rate-limited at the application layer** today.

---

## 5. Endpoint Catalog

### 5.1 `Tvs.Rest` — `/o/tvs/...` (Controller module)

| # | Method | Path | Auth headers | Purpose |
|---|--------|------|--------------|---------|
| 1 | GET | `/o/tvs/maps` | `Site-Id` | Reverse-geo dealer/location by lat/long |
| 2 | GET | `/o/tvs/map` | `Site-Id` | Autocomplete by zip / query string |
| 3 | GET | `/o/tvs/dealers` | `Site-Id` | Find nearby dealers (lat/long, optional limit) |
| 4 | GET | `/o/tvs/loc` | `Site-Id` | Issue a dealer-locator (geo) bearer token |
| 5 | GET | `/o/tvs/liferay` | `Company-Id` | Issue a Liferay OAuth token (server-only consumption) |
| 6 | GET | `/o/tvs/addressFields` | `Site-Id`, `Company-Id` | Address-field metadata for the country |
| 7 | GET | `/o/tvs/liferayDealers` | `Site-Id`, `Company-Id` | Dealer master from Liferay headless object endpoint |
| 8 | GET | `/o/tvs/getChannel` | `Site-Id` | Return Commerce channel id for the site |
| 9 | GET | `/o/tvs/getAllProductsCategories` | `Site-Id`, `Company-Id` | List unique categories across all products |
| 10 | GET | `/o/tvs/getProducts` | `Site-Id`, `Company-Id` | Product catalog (optionally filtered by category) |
| 11 | GET | `/o/tvs/getProductDetails/{productId}` | `Site-Id`, `Company-Id` | Aggregated PDP payload (single product) |
| 12 | GET | `/o/tvs/getProduct/{id}` | `Company-Id` | Raw single product |
| 13 | GET | `/o/tvs/getProductImages/{id}` | `Channel-Id`, `Company-Id` | Images for a product |
| 14 | GET | `/o/tvs/getProductSpecs/{id}` | `Company-Id` | Product specifications |
| 15 | PATCH | `/o/tvs/updateSkuPrice/{skuId}` | `Company-Id` | Update price/promoPrice on a SKU (audited) |
| 16 | GET | `/o/tvs/language/{key}` | `Accept-Language` | Single language-key lookup |
| 17 | POST | `/o/tvs/language/keys` | `Accept-Language` | Bulk language-key lookup |
| 18 | GET | `/o/tvs/webcontent/{groupId}/{articleId}` | `Accept-Language` | Web content article as JSON |
| 19 | GET | `/o/tvs/product-options/{productId}/options` | `Accept-Language` | Product options + values + custom attrs |
| 20 | GET | `/o/tvs/product-options/batch` | `Accept-Language` | Product options for multiple product IDs |

### 5.2 `Forms.Rest` — `/o/tvs/form/...` (FormsDetails module)

All endpoints are POST, JSON body, JSON response, rate-limited (§4), CORS-checked (§3.3). `Site-Id` header is expected; `Country-Code` may override.

| # | Path | Request POJO | Response POJO |
|---|------|--------------|---------------|
| 1 | `/o/tvs/form/owners-group` | `OwnersGroupRequest` | `OwnersGroupResponse` |
| 2 | `/o/tvs/form/sale-institutional` | `InstitutionalSaleRequest` | `InstitutionalResponse` |
| 3 | `/o/tvs/form/vehicle-feedback` | `FeedbackVehicleRequest` | `FeedbackResponse` |
| 4 | `/o/tvs/form/dealer-feedback` | `FeedbackDealerRequest` | `FeedbackResponse` |
| 5 | `/o/tvs/form/service-feedback` | `FeedbackServiceRequest` | `FeedbackResponse` |
| 6 | `/o/tvs/form/vehicle-customer` | `CustomerVehicleRequest` | `CustomerEnquiryResponse` |
| 7 | `/o/tvs/form/general-customer` | `CustomerGeneralRequest` | `CustomerEnquiryResponse` |
| 8 | `/o/tvs/form/nudge-request` | `CustomerVehicleRequest` | `CustomerEnquiryResponse` |
| 9 | `/o/tvs/form/website-feedback` | `WebsiteFeedbackRequest` | `WebsiteFeedbackResponse` |
| 10 | `/o/tvs/form/usersright-request` | `UsersRightRequest` | `UsersRightResponse` |
| 11 | `/o/tvs/form/potentialdealer-request` | `PotentialDealerRequest` | `PotentialDealerResponse` |
| 12 | `/o/tvs/form/campaign-request` | `CampaignRequest` | `CampaignResponse` |
| 13 | `/o/tvs/form/service-request` | `ServiceFormRequest` | `ServiceFormResponse` |
| 14 | `/o/tvs/form/save-partner-feedback` | `PartnerFeedbackRequest` | `PartnerResponse` |
| 15 | `/o/tvs/form/register-partner-interest` | `PartnerInterestRequest` | `PartnerResponse` |
| 16 | `/o/tvs/form/lms` | `LmsRequestBody` | `LmsResponseBody` |
| 17 | `/o/tvs/form/getOtp` | `OtpDto` | `OtpResponse` |
| 18 | `/o/tvs/form/verifyOtp` | `OtpDto` | `OtpResponse` |
| 19 | `/o/tvs/form/send-success-text-message` | `OtpDto` | `OtpResponse` |
| 20 | `/o/tvs/form/form-token` | (no body) | `200 OK` (empty) |

### 5.3 `TvsLatam.Rest` — `/o/list/...` (LatamApis module)

| # | Method | Path | Auth headers | Purpose |
|---|--------|------|--------------|---------|
| 1 | GET | `/o/list/cities` | `Site-Id`, `?search=` | List cities for a country (LCS-backed) |
| 2 | GET | `/o/list/dealers` | `Site-Id`, `?cityId=` | List dealers in a city (LCS-backed) |

---

## 6. Endpoint Reference

### 6.1 `Tvs.Rest` (Controller)

#### 6.1.1 `GET /o/tvs/maps` — Reverse-geo lookup

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getLatLong()` |
| Backed by | External: `https://ib_api.latlong.in/location_details` |
| Query params | `lat` (float, required), `longi` (float, required), `accessToken` (string, required) |
| Headers | `Site-Id` (optional, default `44180`) |
| Response | Pass-through JSON from the dealer-locator API |
| Errors | `200` with `{"error":"Internal Server Error"}` on IO failure (the platform does not currently propagate non-200 here) |

#### 6.1.2 `GET /o/tvs/map` — Autocomplete by zip / text

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getByZipCode()` |
| Backed by | External: `https://ib_api.latlong.in/autocomplete.json` |
| Query params | `queryString` (string, required), `accessToken` (string, required) |
| Headers | `Site-Id` |
| Response | Pass-through JSON |

#### 6.1.3 `GET /o/tvs/dealers` — Nearby dealers

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getNearbyDealers()` |
| Backed by | External: `https://ib_api.latlong.in/brands/{brand}/search.json` |
| Query params | `lat` (float, required), `longi` (float, required), `accessToken` (string, required), `limit` (long, optional, default 5) |
| Headers | `Site-Id` |
| Response | Pass-through JSON; list of dealer objects |

#### 6.1.4 `GET /o/tvs/loc` — Issue dealer-locator token

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getTokenForGeo()` |
| Headers | `Site-Id` |
| Response | JSON serialization of `AuthResponseGeo` (`accessToken`, `expiresIn`, `tokenType`) |
| Notes | Token is required as the `accessToken` query parameter for endpoints 6.1.1 / 6.1.2 / 6.1.3. |

#### 6.1.5 `GET /o/tvs/liferay` — Liferay OAuth token

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getTokenForLiferay()` |
| Headers | `Company-Id` (default `20097`) |
| Response | The bearer token string |
| Notes | Cached per company ID; refreshed on expiry. Used internally; do not consume from external clients. |

#### 6.1.6 `GET /o/tvs/addressFields`

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getAddressFields()` |
| Backed by | Liferay headless object endpoint `/o/c/locations/scopes/{siteId}` |
| Query params | `queryString` (optional) |
| Headers | `Site-Id`, `Company-Id` |
| Response | JSON array of address-field objects; "OTHER" province appended last if present |

#### 6.1.7 `GET /o/tvs/liferayDealers`

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getDealersFromLiferay()` |
| Backed by | Liferay headless object endpoint `/o/c/dealerns/scopes/{siteId}?search={cityReference}` |
| Query params | `cityReference` (string) |
| Headers | `Site-Id`, `Company-Id` |
| Response | `{ "stores": [ ... ] }` with each store enriched with extracted `*_i18n` translation maps |

#### 6.1.8 `GET /o/tvs/getChannel` — Commerce channel id

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getChannelId()` |
| Headers | `Site-Id` |
| Response | A long integer (channel id) |

#### 6.1.9 `GET /o/tvs/getAllProductsCategories`

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getAllProductsCategories()` |
| Headers | `Site-Id`, `Company-Id` |
| Response | `CategoriesResponse` — list of unique category items each with translations |

#### 6.1.10 `GET /o/tvs/getProducts`

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getProducts()` |
| Backed by | Liferay headless commerce delivery + per-product detail composition |
| Query params | `searchCategory` (string, optional), `pageSize` (int, optional, default 20) |
| Headers | `Site-Id`, `Company-Id` |
| Response | JSON array of `Product` objects, each augmented with `currencySymbol`, `customFields.CurrencyUnit`, `customFields.CurrencyFormat` |

#### 6.1.11 `GET /o/tvs/getProductDetails/{productId}`

| Aspect | Value |
|--------|-------|
| Source | `TvsControllerApplication.getProductDetailsAsync()` |
| Path params | `productId` (long) |
| Headers | `Site-Id`, `Company-Id` |
| Response | A composed `Product` object: name, urls, primary image, price/cost/promoPrice, sku code, custom fields, specs, tags, categories, images list, skus list, `threeSixty` flag |

#### 6.1.12 `GET /o/tvs/getProduct/{id}` — Raw single product

#### 6.1.13 `GET /o/tvs/getProductImages/{id}`

`Channel-Id` header required. Returns `ImagesResponse` with `src` rewritten to a host-relative path.

#### 6.1.14 `GET /o/tvs/getProductSpecs/{id}`

Returns nested map keyed by specification group → option category → values. Composes three Liferay catalog endpoints under the hood.

#### 6.1.15 `PATCH /o/tvs/updateSkuPrice/{skuId}`

| Aspect | Value |
|--------|-------|
| Path params | `skuId` (long) |
| Headers | `Company-Id` |
| Request body | `{ "userId": <long>, "userName": "<string>", "price": <number>, "promoPrice": <number> }` |
| Response | Pass-through from Liferay headless commerce; status mirrors upstream |
| Notes | Audited via `SkuPriceHelperService.auditSkuPriceUpdate()`. Although unauthenticated at the HTTP layer (per current configuration), this should be treated as **administrative** and protected by an upstream authorization layer (gateway / VPN / admin role). |

#### 6.1.16 `GET /o/tvs/language/{key}`

| Aspect | Value |
|--------|-------|
| Path params | `key` (string) |
| Headers | `Accept-Language` (e.g. `en-US`, `es-ES`, `tr-TR`) |
| Response | `{ "key": "<key>", "value": "<localized value>" }` |
| Errors | `500` with `{"error":"<message>"}` on lookup failure |

#### 6.1.17 `POST /o/tvs/language/keys`

| Aspect | Value |
|--------|-------|
| Headers | `Accept-Language`, `Content-Type: application/json` |
| Request body | JSON array of strings, e.g. `["form.firstName","form.lastName"]` |
| Response | JSON object `{ "<key1>": "<value1>", ... }` |

#### 6.1.18 `GET /o/tvs/webcontent/{groupId}/{articleId}`

Returns `{ articleId, title, description, content }` or `404` with `{"error":"Web content not found"}`.

#### 6.1.19 `GET /o/tvs/product-options/{productId}/options`

| Aspect | Value |
|--------|-------|
| Source | `ProductOptionsResource.getProductOptionsWithCustomFields()` |
| Headers | `Accept-Language` |
| Response | JSON array of `{ id, key, name, productOptionValues: [{ id, key, name, priority, ...customAttrs }] }` |

#### 6.1.20 `GET /o/tvs/product-options/batch`

| Aspect | Value |
|--------|-------|
| Query params | `productIds` (comma-separated longs, **required**) |
| Headers | `Accept-Language` |
| Errors | `400` with `{"error":"productIds parameter is required"}` |
| Response | Map of `{ "<productId>": [...options...] }` |

### 6.2 `Forms.Rest` (FormsDetails) — common envelope

Each form endpoint:

1. Accepts a JSON body matching the per-form POJO (see §5.2).
2. Reads `Site-Id` (required for country resolution) and optionally `Country-Code`.
3. Validates a small set of **required fields server-side** (see §8) and returns `400` with the standard envelope on failure.
4. On success, delegates to `FormsDetailsService` which serializes the request, acquires an Azure bearer token, POSTs to the LCS endpoint named in `FormConstants` (see §9), and returns the LCS response wrapped in the platform envelope.

**Standard response envelope** (`ResponseWithCode` is the common element):

```jsonc
{
  "data": { /* response-specific payload, or null on failure */ },
  "responseStatus": {
    "code": 200,            // mirrors upstream where possible
    "message": "Success",
    "status": "Success"     // or "Failure"
  }
}
```

### 6.3 Per-form summary

| Form endpoint | Required fields (server-side) | Envelope class |
|---------------|--------------------------------|----------------|
| `/owners-group` | `customerName`, `customerMobileNumber`, `ownersGroup`, `dealerId` | `OwnersGroupResponse` |
| `/sale-institutional` | `customerName`, `customerMobileNumber` | `InstitutionalResponse` |
| `/vehicle-feedback` | `customerName`, `customerMobileNumber` | `FeedbackResponse` |
| `/dealer-feedback` | `customerName`, `customerMobileNumber` | `FeedbackResponse` |
| `/service-feedback` | `customerName`, `customerMobileNumber` | `FeedbackResponse` |
| `/vehicle-customer` | `customerName`, `customerMobileNumber` | `CustomerEnquiryResponse` |
| `/general-customer` | `customerName`, `customerMobileNumber` | `CustomerEnquiryResponse` |
| `/nudge-request` | `customerName`, `customerMobileNumber`, `vehicleName` | `CustomerEnquiryResponse` |
| `/website-feedback` | `websiteRating` | `WebsiteFeedbackResponse` |
| `/usersright-request` | `data.isValid()` (compound validation) | `UsersRightResponse` |
| `/potentialdealer-request` | LCS-side validated; no platform-level required fields | `PotentialDealerResponse` |
| `/campaign-request` | LCS-side validated | `CampaignResponse` |
| `/service-request` | LCS-side validated | `ServiceFormResponse` |
| `/save-partner-feedback` | LCS-side validated | `PartnerResponse` |
| `/register-partner-interest` | LCS-side validated | `PartnerResponse` |
| `/lms` | LMS-side validated by `LmsRequestValidator` | `LmsResponseBody` |
| `/getOtp` | `mobileNumber` | `OtpResponse` |
| `/verifyOtp` | `mobileNumber`, `otp` | `OtpResponse` |
| `/send-success-text-message` | `mobileNumber` | `OtpResponse` |
| `/form-token` | n/a | `200 OK` (empty) |

> **Note on the `/form-token` endpoint:** the platform method returns `200` with no body. Token issuance for downstream LCS calls happens server-side inside `FormsDetailsService`, not via this endpoint. The endpoint exists as a hook for future client-token flows and as a CORS preflight target.

### 6.4 `TvsLatam.Rest` (LatamApis)

#### 6.4.1 `GET /o/list/cities`

| Aspect | Value |
|--------|-------|
| Source | `LatamApisApplication.getLatamCities()` → `LatamApisService.showLatamCities()` |
| Backed by | LCS endpoint `${lcs.url}GetCityList/{search}/EN` |
| Query params | `search` (string, used as path segment in upstream) |
| Headers | `Site-Id` |
| Response | `LatamCities` JSON |
| Errors | `500` with `{"error":"Failed to retrieve city list"}` |

#### 6.4.2 `GET /o/list/dealers`

| Aspect | Value |
|--------|-------|
| Source | `LatamApisApplication.getLatamDealers()` → `LatamApisService.showLatamDealers()` |
| Backed by | LCS endpoint `${lcs.url}GetDealerListByCity/{cityId}/EN` |
| Query params | `cityId` (string) |
| Headers | `Site-Id` |
| Response | `LatamDealers` JSON |
| Errors | `500` with `{"error":"An error occurred while retrieving the dealer list"}` |

---

## 7. Common Errors

### 7.1 HTTP status codes

| HTTP | When |
|------|------|
| `200 OK` | Success path |
| `204 No Content` | `PATCH /updateSkuPrice` upstream success without body |
| `400 Bad Request` | Server-side required-field validation failure (Forms.Rest); missing `productIds` (`product-options/batch`) |
| `403 Forbidden` | CORS rejection (missing/invalid `Origin`); rate-limit `X-Azure-ClientIP` missing |
| `404 Not Found` | Web content article not found |
| `429 Too Many Requests` | Rate limit exceeded; `Retry-After: 60` header |
| `500 Internal Server Error` | Unhandled exception, IO failure, upstream parse failure |
| `503 Service Unavailable` | Rate-limiter map saturated |

### 7.2 Error envelopes by kind

| Origin | Envelope |
|--------|----------|
| Forms validation (4xx) | `{ "data": null, "responseStatus": { "code": 400, "message": "Failure", "status": "Failure" } }` |
| Tvs.Rest exception path | `{"error":"Internal Server Error"}` |
| Tvs.Rest dealer-locator failure | `{"error":"Could not retrieve data"}` |
| `language/{key}` failure | `{"error":"<exception message>"}` |
| `product-options/batch` missing param | `{"error":"productIds parameter is required"}` |
| Rate-limit denial | `{"error":"Too many requests. Please try again later."}` |
| CORS denial | `Forbidden: Origin header missing` or `Forbidden: Invalid Origin` (text body) |
| LatamApis upstream failure | `{"error":"Failed to retrieve city list"}` / `{"error":"An error occurred while retrieving the dealer list"}` |

> The error envelopes are **not uniform** across applications. `Forms.Rest` uses the `responseStatus`-wrapped object; `Tvs.Rest` and `TvsLatam.Rest` use a flat `{ "error": "<msg>" }` shape. Plan client-side handling for both.

---

## 8. Validation Rules (Server-Side, Authoritative)

Server-side validation is intentionally **minimal and per-endpoint**; the LCS upstream performs richer validation. The platform enforces the bare minimum to avoid forwarding obviously malformed payloads.

| Form | Rule | Error |
|------|------|-------|
| `/owners-group` | `customerName != null` AND `customerMobileNumber != null` AND `ownersGroup != null` AND `dealerId != null` | `400`, envelope as in §7.2 |
| `/sale-institutional`, `/vehicle-feedback`, `/dealer-feedback`, `/service-feedback`, `/vehicle-customer`, `/general-customer` | `customerName != null` AND `customerMobileNumber != null` | `400` |
| `/nudge-request` | `customerName != null` AND `customerMobileNumber != null` AND `vehicleName != null` | `400` |
| `/website-feedback` | `websiteRating != null` | `400` |
| `/usersright-request` | `data.isValid()` (defined in `UsersRightRequest`) | `400` |
| `/lms` | `LmsRequestValidator.validate()` (richer rules) | `400` |
| `/getOtp`, `/verifyOtp`, `/send-success-text-message` | Validated within `LmsFormsService.otp()` (mobile format, country code derived from `Site-Id`) | depends |
| `/o/tvs/product-options/batch` | `productIds` non-empty | `400` with text body |
| All `/o/tvs/form/*` | Origin in CORS allowlist | `403` |
| All `/o/tvs/form/*` | `X-Azure-ClientIP` non-empty | `403` |
| All `/o/tvs/form/*` | Rate quota not exceeded | `429` |

**Client-side mirror** lives in `themes/<theme>/src/js/common.js` as `FORM_VALIDATION` rules: name/email/mobile/zip regexes per country, OTP cooldown timer, error message localization. The browser layer is **for UX only** — server-side rules are authoritative.

---

## 9. External APIs the Platform Calls (Outbound Dependencies)

These are **not exposed to integration partners**. They are listed so that vendors understand the platform's external surface and the failure modes that can result.

### 9.1 Dealer locator (`ib_api.latlong.in`)

Used by `IbLatLongService`. Endpoints called:

| Caller method | Upstream URL pattern |
|---------------|----------------------|
| `getLatLong` | `https://ib_api.latlong.in/location_details?location={lat},{long}&access_token={token}&country={cc}` |
| `getByZipCode` | `https://ib_api.latlong.in/autocomplete.json?query={q}&access_token={token}&country={cc}` |
| `getNearbyDealers` | `https://ib_api.latlong.in/brands/{brand}/search.json?lat={lat}&long={long}&access_token={token}&country={cc}&limit={limit}` |

Auth: client-credentials token via `TokenUtil` (see `IbCredentials`).

### 9.2 LCS lead intake

Used by `FormsDetailsService` for every form endpoint. Upstream paths (defined in `FormConstants`):

| Form endpoint | Upstream LCS path token |
|---------------|--------------------------|
| `/owners-group` | `saveOG` |
| `/sale-institutional` | `savevehiclesale` |
| `/vehicle-feedback` | `savevehiclefeedback` |
| `/dealer-feedback` | `SaveDealerFeedback` |
| `/service-feedback` | `saveservicefeedback` |
| `/vehicle-customer` | `savecustomervehicleenquiry` |
| `/general-customer` | `savegeneralenquiry` |
| `/nudge-request` | (reuses `savecustomervehicleenquiry`) |
| `/website-feedback` | `customerwebsitefeedback` |
| `/usersright-request` | `saveusersrightrequest` |
| `/potentialdealer-request` | `savepotentialdealerdetails` |
| `/campaign-request` | `submitcampaignenquiry` |
| `/service-request` | `submitserviceenquiry` |
| `/finance` (legacy module) | `savecustomerfinanceoption` |
| `/save-partner-feedback` | `savepartnerfeedback` |
| `/register-partner-interest` | `registerpartnerinterest` |
| `/getOtp` | `/tvsotpify/v1/GenerateOtp` |
| `/verifyOtp` | `/tvsotpify/v1/VerifyOtp` |
| `/send-success-text-message` | `/tvsotpify/v1/SendLeadAcknowledgement` |
| Misc | `callme` |

Auth: Azure-issued bearer (client-credentials) acquired by `TokenUtil` and cached in `AzureTokenInfo`.

### 9.3 Liferay headless commerce

Used by `Tvs.Rest` for catalog lookups. Endpoints touched:

```
/o/headless-commerce-admin-catalog/v1.0/products/{id}
/o/headless-commerce-admin-catalog/v1.0/products/{id}/categories
/o/headless-commerce-admin-catalog/v1.0/products/{id}/productSpecifications
/o/headless-commerce-admin-catalog/v1.0/specifications
/o/headless-commerce-admin-catalog/v1.0/optionCategories
/o/headless-commerce-admin-catalog/v1.0/skus/{skuId}
/o/headless-commerce-delivery-catalog/v1.0/channels/{channelId}/products
/o/headless-commerce-delivery-catalog/v1.0/channels/{channelId}/products/{id}/images
/o/c/locations/scopes/{siteId}
/o/c/dealerns/scopes/{siteId}
/o/oauth2/token
```

Auth: Liferay OAuth2 token, refreshed per `Company-Id`.

### 9.4 Plivo SMS (OTP path)

Used by `LmsFormsService` (Plivo Java SDK 5.18). Auth via API key.

### 9.5 Azure identity

Token issuer for LCS (and, where configured, for the dealer locator). Endpoint configured via `azure.endpoint` portal property; client/secret/resource via `<region>.azure.id`, `<region>.azure.secret`, `<region>.azure.resource`.

---

## 10. Sample Requests & Responses

### 10.1 Vehicle inquiry (`POST /o/tvs/form/vehicle-customer`)

**Request:**

```http
POST /o/tvs/form/vehicle-customer HTTP/1.1
Host: nepal.tvsmotor.com
Content-Type: application/json
Site-Id: 44180
Accept-Language: en-US
Origin: https://nepal.tvsmotor.com

{
  "customerName": "Maria Lopez",
  "customerMobileNumber": "+5215512345678",
  "customerEmail": "maria@example.com",
  "vehicleName": "Apache RTR 160",
  "city": "Mexico City",
  "state": "CDMX",
  "consent": { "marketing": true, "tnc": true },
  "campaign": {
    "utmSource": "google",
    "utmMedium": "cpc",
    "utmCampaign": "apache_q3",
    "formId": "pdp-test-ride",
    "pageUrl": "https://mexico.tvsmotor.com/products/apache-rtr-160"
  }
}
```

**Success response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: https://nepal.tvsmotor.com
Access-Control-Allow-Credentials: true

{
  "data": {
    "leadId": "LCS-2026-00123456",
    "enquiryReference": "ENQ-2026-00789012"
  },
  "responseStatus": { "code": 200, "message": "Success", "status": "Success" }
}
```

**Validation failure (missing `customerName`):**

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "data": null,
  "responseStatus": { "code": 400, "message": "Failure", "status": "Failure" }
}
```

**Rate-limit response:**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{ "error": "Too many requests. Please try again later." }
```

### 10.2 Nearby dealers (`GET /o/tvs/dealers`)

```http
GET /o/tvs/dealers?lat=27.7172&longi=85.3240&limit=5&accessToken=eyJ... HTTP/1.1
Host: nepal.tvsmotor.com
Site-Id: 44180
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "dealerId": "NPL-001",
    "name": "TVS Showroom Kathmandu",
    "lat": 27.7172,
    "long": 85.3240,
    "distanceKm": 0.4,
    "phone": "+977-1-...",
    "address": "..."
  },
  ...
]
```

### 10.3 Bulk language keys (`POST /o/tvs/language/keys`)

```http
POST /o/tvs/language/keys HTTP/1.1
Host: mexico.tvsmotor.com
Content-Type: application/json
Accept-Language: es-ES

["form.firstName","form.lastName","form.submit"]
```

```json
{
  "form.firstName": "Nombre",
  "form.lastName": "Apellido",
  "form.submit": "Enviar"
}
```

### 10.4 LATAM cities (`GET /o/list/cities`)

```http
GET /o/list/cities?search=mex HTTP/1.1
Host: mexico.tvsmotor.com
Site-Id: 44180
```

```json
{
  "cities": [
    { "id": "MX-CDMX", "name": "Ciudad de México", "stateCode": "CDMX" },
    { "id": "MX-MEX",  "name": "Estado de México", "stateCode": "MEX" }
  ]
}
```

### 10.5 OTP send (`POST /o/tvs/form/getOtp`)

```http
POST /o/tvs/form/getOtp HTTP/1.1
Host: nepal.tvsmotor.com
Content-Type: application/json
Site-Id: 44180
Accept-Language: en-US

{ "mobileNumber": "+9779812345678", "countryCode": "NP" }
```

```json
{
  "data": { "transactionId": "OTP-2026-...-1A2B" },
  "responseStatus": { "code": 200, "message": "OTP sent", "status": "Success" }
}
```

### 10.6 OTP verify (`POST /o/tvs/form/verifyOtp`)

```http
POST /o/tvs/form/verifyOtp HTTP/1.1
Content-Type: application/json
Site-Id: 44180

{ "mobileNumber": "+9779812345678", "otp": "654321" }
```

```json
{
  "data": { "verified": true, "verificationToken": "VRF-..." },
  "responseStatus": { "code": 200, "message": "OTP verified", "status": "Success" }
}
```

---

## 11. OpenAPI 3.0 Skeleton

A trimmed OpenAPI document that integration partners can paste into Swagger UI or import into Postman. **Schemas are simplified** — exhaustive shapes live in the per-form POJOs. Use this as a starting frame and extend from `lcsforms.pojos.*` and `com.tvs.pojos.*`.

```yaml
openapi: 3.0.3
info:
  title: TVS-Website-Nepal Public APIs
  version: "1.0.0"
  description: >
    JAX-RS endpoints exposed by the TVS-Website-Nepal Liferay DXP platform.
    Three application bases: /o/tvs (catalog/geo/language/web content),
    /o/tvs/form (forms intake), /o/list (LATAM city/dealer reference).
servers:
  - url: https://nepal.tvsmotor.com
  - url: https://mexico.tvsmotor.com
  - url: https://uat-nepal.tvsmotor.net

components:
  parameters:
    SiteId:
      name: Site-Id
      in: header
      schema: { type: string, default: "44180" }
    CompanyId:
      name: Company-Id
      in: header
      schema: { type: string, default: "20097" }
    AcceptLanguage:
      name: Accept-Language
      in: header
      schema: { type: string, example: "en-US" }
    CountryCode:
      name: Country-Code
      in: header
      schema: { type: string, example: "NP" }
    ChannelId:
      name: Channel-Id
      in: header
      required: true
      schema: { type: integer, format: int64 }
  schemas:
    ResponseWithCode:
      type: object
      properties:
        code:    { type: integer, example: 200 }
        message: { type: string,  example: "Success" }
        status:  { type: string,  enum: [Success, Failure] }
    FormEnvelope:
      type: object
      required: [responseStatus]
      properties:
        data:
          nullable: true
          type: object
          additionalProperties: true
        responseStatus:
          $ref: '#/components/schemas/ResponseWithCode'
    Dealer:
      type: object
      properties:
        dealerId:    { type: string }
        name:        { type: string }
        lat:         { type: number, format: float }
        long:        { type: number, format: float }
        distanceKm:  { type: number, format: float }
        phone:       { type: string }
        address:     { type: string }
    OtpRequest:
      type: object
      required: [mobileNumber]
      properties:
        mobileNumber: { type: string }
        otp:          { type: string, description: "Required for verifyOtp" }
        countryCode:  { type: string }
    CustomerVehicleRequest:
      type: object
      required: [customerName, customerMobileNumber]
      properties:
        customerName:         { type: string }
        customerMobileNumber: { type: string }
        customerEmail:        { type: string, format: email }
        vehicleName:          { type: string }
        city:                 { type: string }
        state:                { type: string }
        consent:
          type: object
          properties:
            marketing: { type: boolean }
            tnc:       { type: boolean }
        campaign:
          type: object
          properties:
            utmSource:   { type: string }
            utmMedium:   { type: string }
            utmCampaign: { type: string }
            formId:      { type: string }
            pageUrl:     { type: string, format: uri }
  responses:
    BadRequest:
      description: Validation failure
      content:
        application/json:
          schema: { $ref: '#/components/schemas/FormEnvelope' }
    RateLimited:
      description: Too many requests in 5-minute window
      headers:
        Retry-After:
          schema: { type: integer, example: 60 }
      content:
        application/json:
          schema:
            type: object
            properties: { error: { type: string } }

paths:

  /o/tvs/maps:
    get:
      summary: Reverse-geo lookup (lat/long → location details)
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - { name: lat,         in: query, required: true, schema: { type: number, format: float } }
        - { name: longi,       in: query, required: true, schema: { type: number, format: float } }
        - { name: accessToken, in: query, required: true, schema: { type: string } }
      responses:
        "200":
          description: Pass-through dealer-locator API response

  /o/tvs/map:
    get:
      summary: Autocomplete by zip / text
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - { name: queryString, in: query, required: true, schema: { type: string } }
        - { name: accessToken, in: query, required: true, schema: { type: string } }
      responses: { "200": { description: OK } }

  /o/tvs/dealers:
    get:
      summary: Nearby dealers
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - { name: lat,         in: query, required: true, schema: { type: number, format: float } }
        - { name: longi,       in: query, required: true, schema: { type: number, format: float } }
        - { name: accessToken, in: query, required: true, schema: { type: string } }
        - { name: limit,       in: query, required: false, schema: { type: integer, default: 5 } }
      responses:
        "200":
          description: Dealer list
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Dealer' }

  /o/tvs/loc:
    get:
      summary: Issue dealer-locator (geo) bearer token
      parameters: [ { $ref: '#/components/parameters/SiteId' } ]
      responses: { "200": { description: AuthResponseGeo JSON } }

  /o/tvs/getProducts:
    get:
      summary: Product list with currency-augmented details
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - $ref: '#/components/parameters/CompanyId'
        - { name: searchCategory, in: query, schema: { type: string } }
        - { name: pageSize,       in: query, schema: { type: integer, default: 20 } }
      responses: { "200": { description: OK } }

  /o/tvs/getProductDetails/{productId}:
    get:
      summary: Composed PDP payload
      parameters:
        - { name: productId, in: path, required: true, schema: { type: integer, format: int64 } }
        - $ref: '#/components/parameters/SiteId'
        - $ref: '#/components/parameters/CompanyId'
      responses: { "200": { description: OK } }

  /o/tvs/getProductImages/{id}:
    get:
      parameters:
        - { name: id, in: path, required: true, schema: { type: integer, format: int64 } }
        - $ref: '#/components/parameters/ChannelId'
        - $ref: '#/components/parameters/CompanyId'
      responses: { "200": { description: OK } }

  /o/tvs/updateSkuPrice/{skuId}:
    patch:
      summary: Update SKU price (audited)
      parameters:
        - { name: skuId, in: path, required: true, schema: { type: integer, format: int64 } }
        - $ref: '#/components/parameters/CompanyId'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [price, promoPrice]
              properties:
                userId:     { type: integer, format: int64 }
                userName:   { type: string }
                price:      { type: number }
                promoPrice: { type: number }
      responses: { "200": { description: Pass-through Liferay status } }

  /o/tvs/language/{key}:
    get:
      parameters:
        - { name: key, in: path, required: true, schema: { type: string } }
        - $ref: '#/components/parameters/AcceptLanguage'
      responses: { "200": { description: OK } }

  /o/tvs/language/keys:
    post:
      parameters: [ { $ref: '#/components/parameters/AcceptLanguage' } ]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              items: { type: string }
      responses: { "200": { description: Map of key → value } }

  /o/tvs/product-options/{productId}/options:
    get:
      parameters:
        - { name: productId, in: path, required: true, schema: { type: integer, format: int64 } }
        - $ref: '#/components/parameters/AcceptLanguage'
      responses: { "200": { description: OK } }

  /o/tvs/product-options/batch:
    get:
      parameters:
        - { name: productIds, in: query, required: true, schema: { type: string, example: "101,102,103" } }
        - $ref: '#/components/parameters/AcceptLanguage'
      responses:
        "200": { description: OK }
        "400": { description: productIds parameter required }

  /o/tvs/form/vehicle-customer:
    post:
      summary: Capture vehicle inquiry lead
      parameters:
        - $ref: '#/components/parameters/SiteId'
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CustomerVehicleRequest' }
      responses:
        "200": { description: Lead captured, content: { application/json: { schema: { $ref: '#/components/schemas/FormEnvelope' } } } }
        "400": { $ref: '#/components/responses/BadRequest' }
        "403": { description: CORS or rate-limit-IP missing }
        "429": { $ref: '#/components/responses/RateLimited' }

  /o/tvs/form/getOtp:
    post:
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - $ref: '#/components/parameters/AcceptLanguage'
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/OtpRequest' }
      responses:
        "200": { description: OTP sent }
        "429": { $ref: '#/components/responses/RateLimited' }

  /o/tvs/form/verifyOtp:
    post:
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - $ref: '#/components/parameters/AcceptLanguage'
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/OtpRequest' }
      responses:
        "200": { description: OTP verification result }

  /o/list/cities:
    get:
      summary: LATAM city list
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - { name: search, in: query, required: true, schema: { type: string } }
      responses:
        "200": { description: OK }
        "500": { description: Upstream LCS failure }

  /o/list/dealers:
    get:
      summary: LATAM dealers in city
      parameters:
        - $ref: '#/components/parameters/SiteId'
        - { name: cityId, in: query, required: true, schema: { type: string } }
      responses:
        "200": { description: OK }
        "500": { description: Upstream LCS failure }
```

> **Extending this spec:** for full POJO-level schemas, generate from `lcsforms.pojos.*` and `com.tvs.pojos.*` using a Java-to-OpenAPI generator (e.g. `swagger-core` annotations or `springdoc`). The fields are stable per release but are best read from source until annotation-driven generation is added.

---

## 12. Open Items / Known Gaps

1. **Heterogeneous error envelopes** between `Forms.Rest` and `Tvs.Rest`. Worth normalizing in a future revision.
2. **Per-pod rate limit** scales with replicas. Consider a shared (Redis) limiter once replicas > 1.
3. **`/form-token` is a no-op stub** today. Either remove or wire it to actually issue a short-lived client token.
4. **`/updateSkuPrice` is unauthenticated at the application layer.** Production must place an auth gate (gateway / VPN / network policy) in front of this path.
5. **Validation is minimal at the platform.** LCS performs the heavy lift. If LCS errors aren't propagated cleanly, clients see opaque 500s.
6. **Sample payloads for each LCS form** could be exhaustively drawn from each `*Request` POJO. Current samples cover the main flows; vendors should consult the POJO source for full field set per form.

---

## Appendix — File-level cheat sheet

| Concern | File |
|---------|------|
| Endpoint paths (`Tvs.Rest`) | `modules/Controller/src/main/java/com/tvs/controller/application/TvsControllerApplication.java` |
| Endpoint paths (`Forms.Rest`) | `modules/FormsDetails/src/main/java/lcsforms/application/FormsDetailsApplication.java` |
| Endpoint paths (`TvsLatam.Rest`) | `modules/LatamApis/src/main/java/LatamApis/application/LatamApisApplication.java` |
| LCS upstream path constants | `modules/FormsDetails/src/main/java/lcsforms/application/FormConstants.java` |
| Validation error strings | `modules/FormsDetails/src/main/java/lcsforms/application/ErrorConstants.java` |
| Constants (paths, defaults) | `modules/Controller/src/main/java/com/tvs/controller/application/Constants.java` |
| Rate-limit filter | `modules/FormsDetails/src/main/java/lcsforms/application/RateLimitFilter.java` |
| CORS filter | `modules/FormsDetails/src/main/java/lcsforms/application/CustomCorsFilter.java` |
| CORS allowlist | `modules/FormsDetails/src/main/resources/allowed-origins.txt` |
| Dealer locator client | `modules/Controller/src/main/java/com/tvs/controller/application/IbLatLongService.java` |
| LATAM service | `modules/LatamApis/src/main/java/LatamApis/application/LatamApisService.java` |
| Forms POJO root | `modules/FormsDetails/src/main/java/lcsforms/pojos/` |
| Catalog POJO root | `modules/Controller/src/main/java/com/tvs/pojos/` |

---

*End of API Specification. Next document in this series: `README.md`.*

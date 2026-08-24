# API Specification — TVS Holdings Limited Website

> Reference for engineering vendors integrating with, monitoring, or migrating the public site at `https://www.tvsholdings.com`.
> Companion documents: `docs/HLD.md`, `docs/LLD.md`, `docs/hlddoc.md`.

| | |
|---|---|
| Repository | <https://github.com/D2C-Website/TVS-Holdings> |
| Production URL | <https://www.tvsholdings.com> |
| Hosting | Azure Blob Storage (static website) + fronting Azure Front Door / Azure CDN |

---

## 1. Scope and Reality Check

This repository is a **static HTML website hosted on Azure Blob Storage** (the *static website* feature on the `$web` container) and fronted by **Azure Front Door** or **Azure CDN**. It exposes **no first-party APIs**:

- No REST / GraphQL / RPC endpoints.
- No back-end controllers.
- No JSON, XML, or form-encoded request bodies are ever processed.
- No authentication, sessions, tokens, or CSRF surfaces are exercised by application code.

What it *does* expose, from an HTTP-protocol perspective, is a set of **read-only static-resource "endpoints"** plus the redirect rules and security headers configured on the **fronting service rule engine** (Azure Front Door / Azure CDN). The OpenAPI specification below treats those as the API surface so that monitoring, smoke tests, CDN configuration, and migration validation have a contract to point at.

The repository also contains a legacy `web.config` from the previous IIS deployment. **Azure Blob Storage does not interpret `web.config`**; the rules it described must be (and are assumed to be) reproduced on the fronting service. References to `web.config` in this document are therefore historical context, not active configuration.

A small companion section (§9) documents the **third-party endpoints** the browser fetches and the **out-of-band channels** (email, registrar, exchange portals) that compliance workflows rely on.

> Throughout this document, "endpoint" means an addressable URL pattern returned by Azure Blob Storage via the fronting service. There is no business API here; do not confuse this with a transactional integration contract.

---

## 2. OpenAPI 3.1 Specification

The following YAML block is intended to be valid OpenAPI 3.1 and to round-trip through Swagger UI / Redoc / Postman. Drop it into a file named `openapi.yaml` if you want to render it.

```yaml
openapi: 3.1.0
info:
  title: TVS Holdings Limited - Public Website
  description: |
    Read-only static content surface for https://www.tvsholdings.com.
    There are no first-party transactional APIs. This document describes the
    HTTP-protocol contract returned by Azure Blob Storage (`$web` container)
    via a fronting Azure Front Door / Azure CDN profile that owns redirects,
    security headers, and caching. Use it for monitoring, link checking, and
    as a contract for any CDN or migration target.
  version: "1.0.0"
  contact:
    name: TVS Holdings - Company Secretariat
    email: corpsec@tvsholdings.com
  license:
    name: All rights reserved
    identifier: LicenseRef-Proprietary

servers:
  - url: https://www.tvsholdings.com
    description: Production (canonical)
  - url: https://tvsholdings.com
    description: Apex (always 301-redirected to the www server)
  - url: http://www.tvsholdings.com
    description: HTTP variant (always 301-redirected to HTTPS)

tags:
  - name: pages
    description: Curated HTML index and content pages
  - name: documents
    description: Investor / regulatory PDF artefacts
  - name: assets
    description: Stylesheets, scripts, images, legacy media
  - name: meta
    description: Domain-validation, search-engine-verification, and similar
  - name: redirects
    description: Canonicalisation rules enforced by the fronting Azure Front Door / Azure CDN rule engine

paths:

  # -------- Canonicalisation --------

  /:
    get:
      tags: [pages]
      summary: Site root - resolves to the default document
      description: |
        The Azure Storage account's static-website *index document* setting
        resolves `/` to `Profile.htm`. `AccessRestricted.html` is configured
        as the *error document* fallback if `Profile.htm` is missing.
      operationId: getRoot
      security: []
      responses:
        "200":
          description: Profile.htm rendered as the landing page
          headers:
            Strict-Transport-Security: { $ref: "#/components/headers/HSTS" }
            X-Frame-Options:           { $ref: "#/components/headers/XFO" }
            X-Content-Type-Options:    { $ref: "#/components/headers/XCTO" }
            X-XSS-Protection:          { $ref: "#/components/headers/XXSS" }
            Cache-Control:             { $ref: "#/components/headers/CC" }
            Content-Type:              { schema: { type: string, example: "text/html; charset=iso-8859-1" } }
          content:
            text/html:
              example: "<!DOCTYPE html ...>"

  # -------- Pages (representative; not exhaustive) --------

  /Profile.htm:
    get:
      tags: [pages]
      summary: About us / Profile (default document)
      operationId: getProfilePage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Reports.htm:
    get:
      tags: [pages]
      summary: Investors - Reports index
      description: |
        Index of annual returns, related-party transactions, and quarterly
        financial-result PDFs. Each list entry is hand-coded as `<li><a href="...">`.
      operationId: getReportsPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Information.htm:
    get:
      tags: [pages]
      summary: Investors - Information index (board notices, debenture trustees, credit ratings)
      operationId: getInformationPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Announcement.htm:
    get:
      tags: [pages]
      summary: Investors - Announcements (AGM notices, voting results, newspaper ads)
      operationId: getAnnouncementPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Disclosures.htm:
    get:
      tags: [pages]
      summary: Investors - Disclosures
      operationId: getDisclosuresPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /RBIDisclosures.htm:
    get:
      tags: [pages]
      summary: Investors - Disclosures under RBI Regulations
      operationId: getRbiDisclosuresPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /StockExchange.htm:
    get:
      tags: [pages]
      summary: Investors - NSE / BSE intimations index
      operationId: getStockExchangePage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Corporate.htm:
    get:
      tags: [pages]
      summary: Investors - Corporate governance reports
      operationId: getCorporatePage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /PostalBallot.htm:
    get:
      tags: [pages]
      summary: Investors - Postal ballot
      operationId: getPostalBallotPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /PostalBallotResults.htm:
    get:
      tags: [pages]
      summary: Investors - Postal ballot results
      operationId: getPostalBallotResultsPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Contact.htm:
    get:
      tags: [pages]
      summary: Contact us (registered office + investor grievance email)
      operationId: getContactPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /ContactInformation.htm:
    get:
      tags: [pages]
      summary: Investors - Contact information
      operationId: getContactInformationPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /BoardofDirectors.htm:
    get:
      tags: [pages]
      summary: About - Board of Directors
      operationId: getBoardOfDirectorsPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Sitemap.htm:
    get:
      tags: [pages]
      summary: Hand-maintained sitemap
      operationId: getSitemapPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Disclaimer.htm:
    get:
      tags: [pages]
      summary: Legal - Disclaimer
      operationId: getDisclaimerPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Home.htm:
    get:
      tags: [pages]
      summary: Language selector splash (English / Japanese / German / Korean)
      operationId: getHomePage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  /AccessRestricted.html:
    get:
      tags: [pages]
      summary: Implicit fallback default document if Profile.htm is unavailable
      operationId: getAccessRestrictedPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  # -------- Generic page pattern (catches any other root .htm) --------

  /{page}.htm:
    parameters:
      - name: page
        in: path
        required: true
        description: Root-level page name (e.g. Profile, Reports, Information, Quality)
        schema:
          type: string
          pattern: "^[A-Za-z0-9 _-]+$"
    get:
      tags: [pages]
      summary: Any root-level static HTML page
      operationId: getStaticHtmlPage
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }
        "404": { $ref: "#/components/responses/NotFound" }

  # -------- Investor PDFs (data store) --------

  /Investor/TVSH/{year}/{section}/{filename}:
    parameters:
      - name: year
        in: path
        required: true
        description: Calendar year of publication
        schema:
          type: integer
          minimum: 2023
          example: 2025
      - name: section
        in: path
        required: true
        description: Logical section of the disclosure
        schema:
          type: string
          enum:
            - Announcements
            - Corporate
            - Disclosures
            - Informations
            - RBIDisclosures
            - Reports
            - StockExchange
      - name: filename
        in: path
        required: true
        description: PDF filename (URL-encode spaces as %20)
        schema:
          type: string
          pattern: "^[A-Za-z0-9 _,()%-.]+\\.(pdf|PDF)$"
          example: Quarter_Ended_30th_Sep_2025.pdf
    get:
      tags: [documents]
      summary: Versioned investor document under the post-rebrand store
      operationId: getInvestorTvshDocument
      security: []
      responses:
        "200": { $ref: "#/components/responses/PdfDocument" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Reports/{filename}:
    parameters:
      - name: filename
        in: path
        required: true
        schema:
          type: string
          pattern: "^[A-Za-z0-9 _,()%-.]+\\.(pdf|PDF)$"
    get:
      tags: [documents]
      summary: Legacy reports store (pre-rebrand artefacts)
      operationId: getLegacyReportsDocument
      security: []
      responses:
        "200": { $ref: "#/components/responses/PdfDocument" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Web files/{filename}:
    parameters:
      - name: filename
        in: path
        required: true
        schema:
          type: string
    get:
      tags: [documents]
      summary: Pre-2018 financial results and supporting files
      operationId: getWebFilesDocument
      security: []
      responses:
        "200": { $ref: "#/components/responses/PdfDocument" }
        "404": { $ref: "#/components/responses/NotFound" }

  /Announcements/NewspaperPublication/{year}/{filename}:
    parameters:
      - name: year
        in: path
        required: true
        schema:
          type: integer
          minimum: 2022
      - name: filename
        in: path
        required: true
        schema:
          type: string
          pattern: "^[A-Za-z0-9 _,()%-.]+\\.(pdf|PDF|jpg|JPG)$"
    get:
      tags: [documents]
      summary: Newspaper publication PDFs / images for quarterly results
      operationId: getNewspaperPublication
      security: []
      responses:
        "200": { $ref: "#/components/responses/BinaryDocument" }
        "404": { $ref: "#/components/responses/NotFound" }

  /StockExchangeIntimation{yearSuffix}/{filename}:
    parameters:
      - name: yearSuffix
        in: path
        required: true
        description: Year segment (e.g. "-2022" or "2023" — folder names are inconsistent)
        schema:
          type: string
          enum: ["-2022", "2023"]
      - name: filename
        in: path
        required: true
        schema:
          type: string
    get:
      tags: [documents]
      summary: Year-wise NSE / BSE intimations (legacy folders)
      operationId: getStockExchangeIntimation
      security: []
      responses:
        "200": { $ref: "#/components/responses/BinaryDocument" }
        "404": { $ref: "#/components/responses/NotFound" }

  /NCDDisclosures/{year}/{filename}:
    parameters:
      - name: year
        in: path
        required: true
        schema:
          type: integer
      - name: filename
        in: path
        required: true
        schema:
          type: string
    get:
      tags: [documents]
      summary: Non-Convertible Debenture disclosures
      operationId: getNcdDisclosure
      security: []
      responses:
        "200": { $ref: "#/components/responses/PdfDocument" }
        "404": { $ref: "#/components/responses/NotFound" }

  # -------- Static assets --------

  /jquery-3.5.1.min.js:
    get:
      tags: [assets]
      summary: Vendored jQuery 3.5.1 (production build)
      operationId: getJquery
      security: []
      responses:
        "200":
          description: JavaScript
          headers:
            Cache-Control: { $ref: "#/components/headers/CC" }
          content:
            application/javascript: {}

  /ddaccordion.js:
    get:
      tags: [assets]
      summary: DynamicDrive accordion script (used by index.htm only)
      operationId: getDdaccordion
      security: []
      responses:
        "200":
          description: JavaScript
          content:
            application/javascript: {}

  /pngfix.js:
    get:
      tags: [assets]
      summary: Legacy IE6 PNG-transparency shim (loaded only in conditional comments)
      operationId: getPngfix
      security: []
      responses:
        "200":
          description: JavaScript
          content:
            application/javascript: {}

  /thumbnailviewer2.js:
    get:
      tags: [assets]
      summary: Thumbnail viewer used on legacy gallery pages
      operationId: getThumbnailViewer
      security: []
      responses:
        "200":
          description: JavaScript
          content:
            application/javascript: {}

  /layout.css:
    get:
      tags: [assets]
      summary: Primary layout stylesheet
      operationId: getLayoutCss
      security: []
      responses:
        "200": { description: CSS, content: { "text/css": {} } }

  /generalTVSH.css:
    get:
      tags: [assets]
      summary: TVSH-branded global styles
      operationId: getGeneralTvshCss
      security: []
      responses:
        "200": { description: CSS, content: { "text/css": {} } }

  /stylesheet.css:
    get:
      tags: [assets]
      summary: Legacy text styles (contenttext, submenutext, etc.)
      operationId: getStylesheetCss
      security: []
      responses:
        "200": { description: CSS, content: { "text/css": {} } }

  /images/{filename}:
    parameters:
      - name: filename
        in: path
        required: true
        schema:
          type: string
          pattern: "^[A-Za-z0-9 _-]+\\.(jpg|JPG|jpeg|png|PNG|gif|GIF|svg)$"
    get:
      tags: [assets]
      summary: Site images (banners, icons, logos, backgrounds)
      operationId: getImage
      security: []
      responses:
        "200":
          description: Image
          content:
            image/jpeg: {}
            image/png: {}
            image/gif: {}
        "404": { $ref: "#/components/responses/NotFound" }

  # -------- Domain validation / SEO --------

  /google451a3e51028a5485.html:
    get:
      tags: [meta]
      summary: Google Search Console domain verification
      description: |
        Must remain at the document root. Removal will break Search Console
        ownership and can affect indexing visibility.
      operationId: getGoogleVerification
      security: []
      responses:
        "200": { $ref: "#/components/responses/HtmlPage" }

components:

  responses:

    HtmlPage:
      description: Static HTML page
      headers:
        Strict-Transport-Security: { $ref: "#/components/headers/HSTS" }
        X-Frame-Options:           { $ref: "#/components/headers/XFO" }
        X-Content-Type-Options:    { $ref: "#/components/headers/XCTO" }
        X-XSS-Protection:          { $ref: "#/components/headers/XXSS" }
        Cache-Control:             { $ref: "#/components/headers/CC" }
        Content-Type:
          schema: { type: string, example: "text/html; charset=iso-8859-1" }
      content:
        text/html:
          schema:
            type: string
            description: HTML document body (no schema beyond raw HTML)

    PdfDocument:
      description: PDF artefact
      headers:
        Cache-Control: { $ref: "#/components/headers/CC" }
        Content-Type:
          schema: { type: string, example: "application/pdf" }
      content:
        application/pdf:
          schema:
            type: string
            format: binary

    BinaryDocument:
      description: Binary artefact (PDF, JPG)
      content:
        application/pdf:
          schema: { type: string, format: binary }
        image/jpeg:
          schema: { type: string, format: binary }

    NotFound:
      description: |
        Resource not found. The most common operational cause is linkrot: an
        index page (.htm) references a PDF blob that has been moved or renamed.
        The body is the storage account's *error document* (typically
        `AccessRestricted.html`); it is not customised by the repository.
      content:
        text/html:
          example: "<html><body>... AccessRestricted.html ...</body></html>"

    PermanentRedirect:
      description: 301 Moved Permanently to canonical URL
      headers:
        Location:
          schema: { type: string, example: "https://www.tvsholdings.com/Profile.htm" }
        Strict-Transport-Security: { $ref: "#/components/headers/HSTS" }

    MethodNotAllowed:
      description: |
        405 returned by the fronting service if a deny rule for OPTIONS / TRACE
        is configured. (The legacy IIS web.config deny-list is not active under
        Azure Blob Storage; this rule must be expressed on the fronting profile
        if the previous behaviour is required.)
      headers:
        Allow:
          schema: { type: string, example: "GET, HEAD" }

  headers:

    HSTS:
      description: HTTP Strict Transport Security
      schema: { type: string, example: "max-age=86400" }

    XFO:
      description: X-Frame-Options (clickjacking defence)
      schema: { type: string, example: "SAMEORIGIN" }

    XCTO:
      description: X-Content-Type-Options
      schema: { type: string, example: "nosniff" }

    XXSS:
      description: Legacy XSS-auditor hint
      schema: { type: string, example: "1; mode=block" }

    CC:
      description: Cache control - intentionally no-store at origin
      schema:
        type: string
        example: "private, no-cache, no-store, must-revalidate, max-age=0, no-transform"

  securitySchemes: {}

security: []
```

---

## 3. Authentication & Authorization

| Area | Status |
|---|---|
| End-user authentication | **None.** All endpoints are public, anonymous, read-only. |
| Authorization | None at the application layer. No role concept, no scopes, no tokens. |
| Cookies | The legacy `web.config` declared `<httpCookies httpOnlyCookies="true" requireSSL="true" />` and `<sessionState timeout="20" />` as defensive defaults — these are inert under Azure Blob Storage. The application never sets cookies. |
| API keys | None issued, none validated. |
| Editor / deploy access | Out-of-band: CI/CD service principal (or workload identity) scoped to the storage account `$web` container and the fronting profile (for cache purges). Owned by the hosting platform; not part of this contract. |

`security: []` at the OpenAPI root is therefore literal: no credentials are required for any endpoint.

---

## 4. Request Methods

The site is a strict read surface.

| Method | Allowed? | Notes |
|---|---|---|
| `GET` | yes | Primary access pattern |
| `HEAD` | yes | Implicit; useful for monitors / CDN origin-shield |
| `POST`, `PUT`, `PATCH`, `DELETE` | "allowed" by Azure Blob Storage's static-website endpoint to be received, but no resource handles them — the response is `405` for static blobs, or `404` if the path doesn't exist | Do not use |
| `OPTIONS` | denied (recommended): configure a deny rule on the fronting service if the previous IIS deny-list behaviour is required | Otherwise, behaviour is platform-default |
| `TRACE` | denied (recommended): same as `OPTIONS` | Otherwise, behaviour is platform-default |

---

## 5. Request & Response Payloads

### 5.1 Request payloads

There are **no request bodies on any endpoint**. The site does not accept JSON, XML, multipart, or form-encoded input.

Headers used by the static-file handler:

| Request header | Purpose |
|---|---|
| `Host` | Used by the fronting service to evaluate the apex→www redirect rule |
| `If-None-Match` / `If-Modified-Since` | Standard conditional GET; revalidations return `304` |
| `Accept-Encoding` | The fronting service may serve `gzip` / `br` if compression is enabled at the edge |
| `User-Agent` | Logged at the fronting service; used by GA4 client-side |
| `Referer` | Logged at the fronting service; used by GA4 client-side |

> Note: Two legacy localised pages (`SCL-*/IPPPage3.htm`) contain `<form ... action="">`. The empty `action` posts back to the same URL, which is a static page; the submission is silently ignored. These forms are **inert** and not part of the API contract.

### 5.2 Response payloads

| Tag | Content-Type | Schema |
|---|---|---|
| `pages` | `text/html; charset=iso-8859-1` | Raw HTML; no JSON contract |
| `documents` | `application/pdf` (occasionally `image/jpeg` for newspaper publications) | Binary |
| `assets` | `application/javascript`, `text/css`, `image/*` | Binary / text |
| `meta` | `text/html` or `text/plain` | Token strings for DCV / verification |

All responses include the standard security headers documented in §6.

---

## 6. Standard Response Headers

These headers are set by the **fronting Azure Front Door / Azure CDN rule engine**. The values shown reflect the previous IIS defaults; vendors must verify the equivalent rules on the active fronting profile.

```
Strict-Transport-Security: max-age=86400      (recommended: 31536000; includeSubDomains; preload)
X-Content-Type-Options:    nosniff
X-Frame-Options:           SAMEORIGIN
X-XSS-Protection:          1; mode=block
Cache-Control:             per content type at the edge
                           (HTML short, PDF/image long; configured on the rule engine)
Access-Control-Allow-Origin: https://www.tvsholdings.com
```

Recommended `Content-Security-Policy` to add on the fronting service (was drafted but commented out in the legacy `web.config`):

```
Content-Security-Policy:   default-src 'self';
                           script-src 'self' 'unsafe-inline' https://www.googletagmanager.com;
                           img-src 'self' data:;
                           style-src 'self' 'unsafe-inline';
                           connect-src 'self' https://www.google-analytics.com https://www.googletagmanager.com;
```

Headers that should **not** appear in responses (Front Door / CDN does not emit them by default; verify):

```
Server
X-Powered-By
X-AspNet-Version
X-AspNetMvc-Version
X-Robots-Tag
```

---

## 7. Error Responses

Because there is no application code, all errors come from the storage origin or the fronting service.

| HTTP status | Cause | Body | Recovery |
|---|---|---|---|
| `301` | Apex → www, or HTTP → HTTPS | empty | Follow `Location:` |
| `304` | Conditional GET unchanged | empty | Use cached copy |
| `404` | Missing blob (linkrot is the most common cause) | Storage account *error document* (typically `AccessRestricted.html`) | Upload the missing blob or fix the link in the parent `.htm`; purge the fronting cache |
| `405` | `OPTIONS` or `TRACE` request — only if a deny rule is configured on the fronting profile | Front Door / CDN default | By design (recommended) |
| `5xx` | Origin host failure (storage account unavailable) or fronting service fault | Front Door / CDN error page | Operations to investigate the storage account and the fronting profile |

Error bodies are not customised. There is **no JSON error envelope**.

> If a CDN is fronted, the CDN's error pages may apply for upstream failures. Coordinate with the CDN team to ensure user-facing 404 pages are still recognisable.

---

## 8. Validation Rules

This is a static site, so "validation" lives in three layers.

### 8.1 Edge validation (fronting service rule engine + storage account)

| Rule | Limit | Source |
|---|---|---|
| Method allow-list | Recommended: deny `OPTIONS` and `TRACE` via a fronting rule | Azure Front Door / Azure CDN rule engine |
| URL / query-string limits | Platform defaults; tighten via the rule engine if a stricter cap is required | Azure Front Door / Azure CDN |
| Body size cap | Origin is read-only; the fronting service may have its own cap | Azure Front Door / Azure CDN |
| Extension allow-list | All extensions allowed; the repo simply contains no executable types | Azure Blob Storage (no filter) |
| WAF (recommended) | OWASP managed rule set + bot protection | Azure Front Door WAF policy |

> The legacy IIS `<requestFiltering>` block (max URL 2048, max query 1024, max body 1 GiB, deny `OPTIONS`/`TRACE`) is **not** active under Azure Blob Storage. Re-implement the equivalents on the fronting profile.

### 8.2 Path-shape validation (informational, enforced by blob existence)

| Resource | Pattern |
|---|---|
| Page | `/{Page}.htm` where `{Page}` matches `^[A-Za-z0-9 _-]+$` |
| TVSH document | `/Investor/TVSH/{YYYY}/{Section}/{Filename}` where `{YYYY}` ≥ 2023 and `{Section}` ∈ {Announcements, Corporate, Disclosures, Informations, RBIDisclosures, Reports, StockExchange} |
| Image | `/images/{Filename}` matching `^[A-Za-z0-9 _-]+\.(jpg|jpeg|png|gif|svg)$` |

> These are **conventions**, not server-enforced regex rules. Azure Blob Storage will serve any matching blob regardless of pattern.

### 8.3 Editorial validation (pre-deploy checklist)

See `docs/LLD.md` §9.2. The single most important rule: **before merging an HTML edit that adds a new PDF link, confirm the PDF exists at the linked path on staging.** Most production 404s are linkrot.

---

## 9. External API / Endpoint Dependencies

The site does not call APIs server-to-server. Browsers, however, fetch a small set of third-party endpoints, and several out-of-band channels are referenced from rendered content. Both are documented here for completeness.

### 9.1 Third-party scripts loaded by the browser

| Endpoint | Method | Purpose | Auth | Data sent | Failure mode |
|---|---|---|---|---|---|
| `https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL` | GET (script) | Load Google Analytics 4 collector | None (public) | None (it is the script payload) | Page renders normally; only analytics is missed |
| `https://www.googletagmanager.com/gtag/js?id=UA-120525446-1` | GET (script) | Load deprecated Universal Analytics (still on legacy pages) | None (public) | None | Will eventually 404 / no-op |
| `https://www.google-analytics.com/g/collect?...` | GET (beacon) | GA4 page-view event | None (public) | URL, referrer, anon client ID | Same as above |
| `https://www.googletagmanager.com/gtm.js?id=...` | GET (script, if added in future) | GTM container | None | None | Page renders normally |

Recommended CSP whitelist (when CSP is enabled): `script-src 'self' https://www.googletagmanager.com; connect-src 'self' https://www.google-analytics.com https://www.googletagmanager.com;`

### 9.2 Out-of-band channels referenced from page content

These are **not API integrations** — they are emails and external portals that compliance workflows depend on. Listed here so monitoring tools don't false-alarm if they detect the references.

| Channel | Where referenced | Used for |
|---|---|---|
| `mailto:einward@integratedindia.in` | `Contact.htm`, others | Investor grievance handling (Registrar — Integrated Registry Management Services) |
| `mailto:corpsec@tvsholdings.com` | `Contact.htm`, others | Company secretariat |
| `https://www.nseindia.com/companytracker/cmtracker.jsp?symbol=SUNCLAYTON` | Legacy investor pages | NSE stock tracker (deep link) |
| `http://www.sclapd.com/` | Legacy SCL pages | External "Login" portal (separate system) |
| `http://www.sclftp.com/shareholders/login.aspx?Company=SCL` | Currently commented out | Legacy shareholder login |
| Beacon Trusteeship address | `Information.htm` | Debenture trustee contact |
| Catalyst Trusteeship address | `Information.htm` | Debenture trustee contact |

### 9.3 Domain-validation endpoints (must remain reachable)

| Endpoint | Used by | Why |
|---|---|---|
| `https://www.tvsholdings.com/google451a3e51028a5485.html` | Google Search Console | Domain ownership |

If a CDN or auth proxy is added, these paths must bypass any access controls.

---

## 10. Rate Limits

There are **no application-level rate limits** — the site has no app code that could enforce them. Rate limiting, if needed, is the responsibility of the fronting layer.

### 10.1 Today

| Layer | Limit | Source |
|---|---|---|
| Fronting service (Front Door / CDN) | Platform defaults — deny `OPTIONS`/`TRACE` if rule configured | Rule engine on the fronting profile |
| Storage origin | Per-storage-account request limits per Azure SLA | Azure Storage |
| Crawl rate | Unrestricted | `robots_dummy.txt` is a placeholder; there is no active `robots.txt` |

### 10.2 Recommended (when fronting with a CDN or WAF)

| Limit | Suggested value | Rationale |
|---|---|---|
| Per-IP requests | 60 req / 10 s, 600 req / minute | Adequate for human users; bot abuse should trip well before legitimate traffic |
| Per-IP PDF download burst | 10 PDFs / minute | PDFs are large; investor traffic does not burst that aggressively |
| Geo block-list | None initially | Investor traffic is global |
| User-Agent block-list | Common scraper/bot UAs | Standard WAF rule set |

These are **suggestions**; this repository does not implement them.

---

## 11. Sample Requests & Responses

> All examples use real paths from the repository. Replace the host with a staging URL when testing changes.

### 11.1 Site root → 200

```bash
curl -sS -i 'https://www.tvsholdings.com/'
```

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=iso-8859-1
Strict-Transport-Security: max-age=86400
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0, no-transform
Access-Control-Allow-Origin: https://www.tvsholdings.com

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ...>
<html ...>
  <head><title>Profile</title> ... </head>
  <body>
    <div class="logo"> ... </div>
    <div class="menu"> ... </div>
    ...
  </body>
</html>
```

### 11.2 Apex host → 301

```bash
curl -sS -I 'http://tvsholdings.com/Reports.htm'
```

```http
HTTP/1.1 301 Moved Permanently
Location: https://www.tvsholdings.com/Reports.htm
```

### 11.3 HTTP → HTTPS → 301

```bash
curl -sS -I 'http://www.tvsholdings.com/Reports.htm'
```

```http
HTTP/1.1 301 Moved Permanently
Location: https://www.tvsholdings.com/Reports.htm
```

### 11.4 PDF download → 200

```bash
curl -sS -OJ 'https://www.tvsholdings.com/Investor/TVSH/2025/Reports/Quarter_Ended_30th_Sep_2025.pdf'
```

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: <bytes>
Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0, no-transform
```

### 11.5 PDF missing → 404 (linkrot scenario)

```bash
curl -sS -i 'https://www.tvsholdings.com/Investor/TVSH/2099/Reports/Does_Not_Exist.pdf'
```

```http
HTTP/1.1 404 Not Found
Content-Type: text/html
... AccessRestricted.html (storage account error document) ...
```

### 11.6 OPTIONS denied → 405

```bash
curl -sS -i -X OPTIONS 'https://www.tvsholdings.com/Profile.htm'
```

```http
HTTP/1.1 405 Method Not Allowed
Allow: GET, HEAD
```

### 11.7 Conditional GET → 304

```bash
curl -sS -i \
  -H 'If-Modified-Since: Mon, 01 Jan 2024 00:00:00 GMT' \
  'https://www.tvsholdings.com/layout.css'
```

```http
HTTP/1.1 304 Not Modified
Cache-Control: private, no-cache, no-store, must-revalidate, max-age=0, no-transform
```

### 11.8 Google Search Console verification → 200

```bash
curl -sS -i 'https://www.tvsholdings.com/google451a3e51028a5485.html'
```

```http
HTTP/1.1 200 OK
Content-Type: text/html
```

### 11.9 GA4 beacon (third-party, illustrative)

The site does not call this server-to-server. The browser does, after `gtag.js` initialises:

```http
GET /g/collect?v=2&tid=G-DPMX50C7QL&cid=...&dl=https%3A%2F%2Fwww.tvsholdings.com%2FProfile.htm HTTP/1.1
Host: www.google-analytics.com
```

```http
HTTP/1.1 204 No Content
```

---

## 12. Idempotency, Concurrency, Caching

| Concern | Behaviour |
|---|---|
| Idempotency | All routes are `GET`-only and idempotent. No write surface exists. |
| Concurrency | Blob reads are concurrent-safe; Azure Storage handles request multiplexing. |
| Cache | The fronting service should set per-content-type cache TTLs (HTML short, PDF/image long). ETag / `Last-Modified` are emitted by Azure Storage and used for `304` revalidation. The legacy `Cache-Control: no-store` from `web.config` is inert. |
| CDN caching | Recommended per-content-type cache policy on the fronting profile: `public, max-age=86400` for `*.pdf` and `/images/*`, `public, max-age=60` for `*.htm`. Cache invalidation on deploy is mandatory (`az afd endpoint purge`). |

---

## 13. Versioning

The site does not version the API in URLs (and does not need to). What it *does* version is the **content**:

- Annual / quarterly artefacts are placed in year-stamped folders under `Investor/TVSH/<YYYY>/`.
- Filenames embed the period (e.g. `Quarter_Ended_30th_Sep_2025.pdf`).
- Once a URL is published in a stock-exchange filing, **it must not be changed**. Treat every published path as a permanent contract.

---

## 14. Test Plan (suggested smoke set)

A vendor taking over operations can stand up a synthetic monitor with the following probes. Each is a single `GET`, no auth required.

| # | Probe | Expected | Frequency |
|---|---|---|---|
| 1 | `https://www.tvsholdings.com/` | `200`, `Content-Type: text/html`, body contains `TVS Holdings Limited` | 1 min |
| 2 | `https://tvsholdings.com/` (apex) | `301` to `https://www.tvsholdings.com/` | 5 min |
| 3 | `http://www.tvsholdings.com/` | `301` to `https://www.tvsholdings.com/` | 5 min |
| 4 | `https://www.tvsholdings.com/Reports.htm` | `200`, body contains `Quarterly Reports` | 5 min |
| 5 | `https://www.tvsholdings.com/Information.htm` | `200`, body contains `Notice of Board Meetings` | 5 min |
| 6 | `https://www.tvsholdings.com/Announcement.htm` | `200`, body contains `AGM Voting Results` | 5 min |
| 7 | `https://www.tvsholdings.com/Disclosures.htm` | `200` | 15 min |
| 8 | `https://www.tvsholdings.com/StockExchange.htm` | `200` | 15 min |
| 9 | `https://www.tvsholdings.com/google451a3e51028a5485.html` | `200` | daily |
| 10 | TLS certificate expiry on `www.tvsholdings.com` | > 30 days | daily |
| 11 | Crawl all `<a href="*.pdf">` links from `Reports.htm`, `Information.htm`, `Announcement.htm`, `Disclosures.htm`, `RBIDisclosures.htm`, `StockExchange.htm`, `Corporate.htm`, `PostalBallot.htm`, `Information.htm` and assert `200` | All `200` | weekly |

---

## 15. Out of Scope / Intentionally Omitted

This document does **not** cover:
- Deployment credentials, Azure connection strings, SAS tokens, service-principal client IDs / secrets, CI/CD pipeline secrets.
- Storage account names, resource-group names, subscription IDs, fronting-profile resource IDs, or any other Azure resource identifiers.
- Internal IPs, monitoring tool URLs, or alerting destinations.
- Third-party contract terms (Google, CRISIL, Integrated Registry, BSE, NSE, debenture trustees).
- Any custom or commented-out endpoints (`IPPPage1.htm`, `Sundaram-Clayton-Record Date-09-final.pdf`, etc.) that exist as static content but are not currently linked from any active page. Treat them as archived assets, not endpoints.

Vendors needing any of the above must request them through the company-secretariat handover process.

---

*This API spec is a fair description of the protocol surface a consumer or monitor must integrate with. It is not a description of business APIs because none exist; if a future requirement (newsletter, query form, e-IPO interface) introduces real APIs, that will need its own design and contract document.*

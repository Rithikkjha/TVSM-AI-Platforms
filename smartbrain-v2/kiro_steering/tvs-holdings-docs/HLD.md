# High Level Design — TVS Holdings Limited Website

> Architecture document for external engineering partners.
> Template reference: *D2C — High Level Design Template* (Confluence page 4209508450).
> Scope: the public corporate / investor-relations website served at `https://www.tvsholdings.com`, captured in this repository.

| | |
|---|---|
| Repository | <https://github.com/D2C-Website/TVS-Holdings> |
| Production URL | <https://www.tvsholdings.com> |
| Hosting | Azure Blob Storage (static website) + fronting Azure Front Door / Azure CDN |

---

## 1. Overview

The repository contains the **public-facing static website** of TVS Holdings Limited (formerly Sundaram-Clayton Limited, "SCL"). The site exists to (a) project corporate identity and (b) discharge the company's statutory **investor-relations and disclosure obligations** as a Reserve Bank of India registered Core Investment Company (CIC).

What we are building (and have already built):
- A pure HTML / CSS / JavaScript site delivered from **Azure Blob Storage** (static website feature).
- A fronting **Azure Front Door** or **Azure CDN** profile that owns the custom domain, HTTPS termination, redirect rules, security headers, caching, and (optionally) WAF.
- An organised document store of statutory PDFs (annual reports, quarterly results, AGM notices, RBI/NCD disclosures, postal-ballot packs, governance policies) linked from curated landing pages.
- A small set of cross-cutting concerns that **were** enforced through `web.config` on the previous IIS deployment (HTTPS redirect, apex-to-www redirect, response-header policy, default document). On Azure Blob Storage, those rules are not interpreted; they live on the fronting service rule engine. The `web.config` file is retained in the repo as a historical reference and a porting checklist, **not** as live configuration.

What we are **not** building: there is no application server, database, API, or user account system in this codebase.

---

## 2. Tier Classification

**Tier 2 — Business Critical, not Life-or-Death.**

Justification:
- The site is the official channel for SEBI / RBI / Companies-Act mandated disclosures. Extended unavailability would create a **regulatory and reputational** issue, but no live transactions or revenue stream depend on it.
- Investor grievances and statutory filings already have **out-of-band channels** (registrar email, direct NSE/BSE filings) that continue to function during a site outage.
- There is no real-time SLA contract with end users. Read-only static content with no personalisation.

Implication for SLOs:
- Target availability **≥ 99.5% monthly**, RTO ≤ 4 h, RPO ≤ 24 h (content is recoverable from source control / backups).

---

## 3. Background

| Driver | Detail |
|---|---|
| Brand transition | The site now carries the **TVS Holdings** identity after the rebrand from Sundaram-Clayton Limited. Legacy SCL pages are retained for SEO and historical access. |
| Regulatory trigger | RBI Certificate of Registration as a Core Investment Company (CIC) created an ongoing obligation to publish RBI / NBFC / NCD disclosures, surfaced through `RBIDisclosures.htm` and `Disclosures.htm`. |
| Tech-debt observations | (a) Mixed Google Analytics IDs (GA4 `G-DPMX50C7QL` on current pages, legacy UA `UA-120525446-1` on older ones). (b) Adobe Flash assets (`.swf`, `.fla`) that no longer render on modern browsers. (c) No build pipeline; pages duplicate header/footer markup so changes ripple by hand. (d) `<base href="https://www.tvsholdings.com" />` on some pages prevents local previewing. (e) Right-click "disable" scripts that add UX friction without security value. |
| Operating model | Compliance / Secretarial team owns content; engineering owns Azure infrastructure (storage account, fronting profile, deploy pipeline). |

---

## 4. Requirements

### 4.1 Functional
- Serve corporate-information pages (About us, Board of Directors, Profile, Group structure, Contact).
- Serve investor-relations indices (Reports, Information, Announcements, Disclosures, RBI Disclosures, Stock Exchange Intimations, Postal Ballot, Corporate Governance).
- Serve PDF artefacts linked from the indices (annual returns, quarterly results, AGM notices, voting results, RPT statements, board-meeting notices, credit ratings, statutory policies).
- Provide multilingual mirror sites (Japanese, German, Korean) accessible from `Home.htm`.
- Provide standard legal pages (Disclaimer, Terms, Sitemap, Access Restricted).
- Honour search-engine validation requirements (Google Search Console verification file).

### 4.2 Non-Functional

| Category | Requirement |
|---|---|
| Availability | ≥ 99.5% monthly; planned maintenance windows allowed off-hours |
| Performance | Time-to-first-byte ≤ 500 ms from India region; full landing-page render ≤ 3 s on broadband |
| Security | HTTPS-only; HSTS; security response headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection); strip `Server` / `X-Powered-By` / `X-AspNet-Version`; no PII collection or storage |
| Compliance | All SEBI/RBI mandated disclosures must be retrievable via stable URLs; URLs visible in stock-exchange filings should not break |
| Accessibility | Compatible with mainstream desktop and mobile browsers; legacy IE-only behaviours (Flash, ActiveX) are out of scope |
| Auditability | Source control of every HTML and PDF change; deploy logs retained ≥ 90 days |
| Privacy | Only third-party data collector is Google Analytics (GA4); no first-party cookies set by application code |
| Localisation | English primary; static mirrors for ja, de, ko |
| Hostability | Deployable to Azure Blob Storage (`$web` container) fronted by Azure Front Door or Azure CDN. The redirect / header rules previously expressed in `web.config` must be reproduced on the fronting service. |

---

## 5. Current Architecture (HLD)

The site is in steady state on Azure Blob Storage with a fronting CDN/Front Door layer. The legacy `web.config` is retained in source for reference but is not interpreted by the storage account.

```
                        ┌───────────────────────────────────────────────┐
                        │                  End User                     │
                        │           (browser: desktop / mobile)         │
                        └───────────────────────────────────────────────┘
                                            │
                  HTTPS GET https://www.tvsholdings.com/<path>
                                            │
                                            ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │   [EDGE]  Azure Front Door  /  Azure CDN                               │
        │                                                                        │
        │   Routing / rule engine (configured in Azure portal or IaC,            │
        │   not in this repo):                                                   │
        │     • Custom domain + TLS termination (Azure-managed cert)             │
        │     • Redirect: tvsholdings.com → www.tvsholdings.com (301)            │
        │     • Redirect: HTTP             → HTTPS              (301)            │
        │     • Cache policy per content type (HTML short, PDF/image long)       │
        │     • Optional WAF policy                                              │
        │                                                                        │
        │   Recommended response headers (set on the rule engine):               │
        │     Strict-Transport-Security:    max-age=31536000; includeSubDomains  │
        │     X-Content-Type-Options:       nosniff                              │
        │     X-Frame-Options:              SAMEORIGIN                           │
        │     X-XSS-Protection:             1; mode=block                        │
        │     Content-Security-Policy:      <whitelist googletagmanager.com>     │
        │                                                                        │
        │   Note: anything that the legacy web.config in the repo claims to do   │
        │   is ONLY active here if it has been replicated as a rule.             │
        └────────────────────────────────────────────────────────────────────────┘
                                            │
                              (cache miss → fetch from origin)
                                            │
                                            ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │   [ORIGIN]  Azure Storage Account — Static Website                     │
        │                                                                        │
        │   Container: $web   (anonymous public read for GETs)                   │
        │   Index document: Profile.htm                                          │
        │   Error document: AccessRestricted.html  (recommended)                 │
        │                                                                        │
        │   Blob layout (mirrors source repo):                                   │
        │     Pages   : *.htm, *.html                                            │
        │     Styles  : layout.css, generalTVSH.css, stylesheet                  │
        │     Scripts : jquery-3.5.1.min.js, ddaccordion.js,                     │
        │               pngfix.js, thumbnailviewer2.js                           │
        │     Media   : images/*.{jpg,png,gif}, *.swf (legacy)                   │
        │     Docs    : Investor/, Reports/, Web files/,                         │
        │               Announcements/, NCDDisclosures/,                         │
        │               StockExchangeIntimation*/                                │
        │     SEO     : google451a3e51028a5485.html                              │
        │                                                                        │
        │   web.config: present in $web only as a leftover — NOT processed       │
        │   by Blob Storage (recommend removing from the deploy set).            │
        └────────────────────────────────────────────────────────────────────────┘

   Browser also calls (in parallel, third party):

     ── https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL  (GA4)
     ── https://www.googletagmanager.com/gtag/js?id=UA-120525446-1 (legacy UA, on older pages)

   Outbound links the user may follow (no server-to-server calls):

     ── https://www.nseindia.com/...                    (stock tracker)
     ── https://www.sclapd.com/                          (legacy login, separate system)
     ── mailto:einward@integratedindia.in                (investor grievance)
     ── mailto:corpsec@tvsholdings.com                   (company secretariat)
```

### 5.1 Major components (and their responsibilities)

> Dependency services that are **owned by other parties** (not by this repo) are flagged as **[EXTERNAL]**.

| # | Component | Type | Owner | Responsibility |
|---|---|---|---|---|
| 1 | **Azure Front Door / Azure CDN** | Edge (Azure) | Engineering | Custom domain, HTTPS termination, redirects, security headers, caching, WAF |
| 2 | **Azure Storage Account — Static Website (`$web`)** | Origin (Azure) | Engineering | Anonymous public GETs of all blobs (HTML, CSS, JS, images, PDFs) |
| 3 | HTML page set (~150 root pages) | Content | Compliance + Engineering | Curated investor and corporate views |
| 4 | PDF document store under `Investor/`, `Reports/`, `Announcements/`, `NCDDisclosures/`, `StockExchangeIntimation*/`, `Web files/` | Content | Compliance / Secretarial | Statutory and regulatory artefacts |
| 5 | jQuery 3.5.1 + DynamicDrive scripts (`ddaccordion.js`, `thumbnailviewer2.js`) + `pngfix.js` | Vendored JS | Engineering | DOM helpers, accordion menus, thumbnail viewer, IE6 PNG shim |
| 6 | Localised mirror sites under `SCL-Japan/`, `SCL-German/`, `SCL-Korean/` | Content | Compliance | Multilingual mirrors of legacy SCL content |
| 7 | Manual upload by an authorised engineer | Operational process | Engineering | Uploads the repo (or just the changed blobs) to `$web` via the Azure portal or `az storage blob upload` / `azcopy`. **There is no CI/CD pipeline.** Any cache purge on the fronting service is also a manual step. |
| 8 | **[EXTERNAL] Google Tag Manager / GA4** | Analytics SaaS | Google | Page-view, session, and source attribution telemetry |
| 9 | **[EXTERNAL] Google Search Console** | SEO SaaS | Google | Domain ownership and indexing visibility (verification file at site root) |
| 10 | **[EXTERNAL] Integrated Registry Management Services (RTA)** | Registrar | Integrated | Investor grievance handling, share-transfer support — referenced via email only |
| 11 | **[EXTERNAL] Beacon Trusteeship / Catalyst Trusteeship** | Debenture trustees | Trustees | NCD trusteeship — referenced via address/email only |
| 12 | **[EXTERNAL] CRISIL** | Credit rating | CRISIL | Credit-rating documents linked as PDFs |
| 13 | **[EXTERNAL] NSE / BSE** | Stock exchanges | Exchanges | Statutory filings are uploaded directly to exchanges; the site mirrors PDFs and deep-links the stock tracker |

### 5.2 Pros

- **Zero application-layer attack surface.** No app server, no DB, no auth → no SQL injection, no auth-bypass, no business-logic vulnerabilities to defend against.
- **Serverless origin.** Azure Blob Storage has Microsoft-managed durability (LRS / ZRS / GRS depending on configuration) and no host to patch.
- **Built-in global edge** when fronted by Azure Front Door / CDN — low TTFB worldwide.
- **Stable URLs.** Filings already lodged with NSE/BSE that reference this site continue to resolve.
- **Editorial autonomy.** Compliance team can publish without an engineering release; CI/CD turnaround is minutes.

### 5.3 Cons

- **No CMS / templating.** Header, footer and navigation markup is duplicated across ~150 pages; site-wide cosmetic changes are tedious.
- **No build pipeline (today).** No linting, no link-checking, no automated accessibility scan, no minification.
- **Configuration is split** between the storage account (index/error doc) and the fronting service (redirects, headers, cache, WAF). Two places to look when debugging.
- **The legacy `web.config` is misleading** if read at face value — Blob Storage does not interpret it.
- **Mixed analytics IDs** (GA4 + legacy UA) — telemetry is fragmented.
- **`<base href="...">`** on some pages breaks local previewing.
- **Legacy assets** (Flash `.swf`, `.fla`, IE-targeted `pngfix.js`, right-click disablers) add weight without benefit.
- **Linkrot risk.** PDF paths are hand-typed inside the HTML; renaming a blob silently breaks dozens of links.

---

## 6. Proposed Architecture (HLD)

Same as section 5 (this site is in steady state). For onboarding purposes we additionally recommend the following non-breaking improvements; each is optional and self-contained:

| Improvement | Rationale | Effort | Risk |
|---|---|---|---|
| Confirm the fronting layer is **Azure Front Door** (not just storage CDN endpoint) and enable WAF | DDoS / OWASP coverage; consistent rule engine | Low | Low |
| Promote HSTS to `max-age=31536000; includeSubDomains; preload` after a soak period | Closes downgrade-attack window | Low | Low (only after testing) |
| Enable a tightened Content-Security-Policy on the fronting layer | Mitigates XSS and third-party script risk | Low | Medium (must whitelist `googletagmanager.com`) |
| Enable storage account **soft delete**, **versioning**, and **change feed** | Cheap, non-breaking safety net for accidental overwrites / deletes | Low | Low |
| Enable storage account **diagnostic settings → Log Analytics** | Server-side request logs (not available client-side from GA4) | Low | Low |
| Use **GRS or RA-GRS** replication on the storage account, or run the storage account **paired across two regions** | DR posture for the origin | Low–Medium | Low |
| Retire UA `UA-120525446-1` references | Removes deprecated analytics endpoint | Low | Low |
| Remove Flash assets (`*.swf`, `*.fla`) and the IE6 `pngfix.js` | Reduces footprint, removes legacy code paths | Low | Low |
| Delete `web.config` from the deploy set after porting any remaining rules | Avoids confusion + avoids serving it as plain text | Low | Low |
| Introduce a static-site generator (or even a shared header/footer include) | Eliminates duplicated chrome across pages | Medium | Medium |
| Add an automated link-checker in CI | Detects broken PDF links before publish | Low | Low |

> Dependency services that we do **not** propose to take ownership of (kept **[EXTERNAL]** in any future diagram): Google Analytics, Google Search Console, NSE/BSE, the Registrar (Integrated), the Debenture Trustees, and the CRISIL portal.

---

## 7. Data Flow / Sequence Diagrams

### 7.1 Visitor read path (the primary user flow)

```
 User    Browser           Front Door / CDN          Storage ($web)         GA4
  │        │                       │                      │                  │
  │ type   │                       │                      │                  │
  │ URL    │                       │                      │                  │
  ├───────▶│                       │                      │                  │
  │        │ (1) GET https://tvsholdings.com/                                 │
  │        ├──────────────────────▶│                      │                  │
  │        │ ◀── 301 → https://www.tvsholdings.com/  (redirect rule) ────────│
  │        │                       │                      │                  │
  │        │ (2) GET https://www.tvsholdings.com/                            │
  │        ├──────────────────────▶│  cache miss          │                  │
  │        │                       ├─────────────────────▶│                  │
  │        │                       │ ◀── Profile.htm      │                  │
  │        │ ◀── 200 + sec headers │ (index document)     │                  │
  │        │                       │                      │                  │
  │        │ (3) parses HTML, fetches CSS/JS/images in parallel              │
  │        ├──────────────────────▶│ (mostly cache hits)  │                  │
  │        │ ◀── 200 (assets) ─────│                      │                  │
  │        │                       │                      │                  │
  │        │ (4) loads gtag.js                                                │
  │        ├────────────────────────────────────────────────────────────────▶│
  │        │ ◀── 200 (gtag.js) ──────────────────────────────────────────────│
  │        │ (5) page_view beacon ────────────────────────────────────────── │
  │        │                       │                      │                  │
  │ click  │                       │                      │                  │
  │ PDF    │ (6) GET /Investor/TVSH/2025/Reports/Quarter_Ended_30th_Sep_2025.pdf
  ├───────▶├──────────────────────▶│  cache miss          │                  │
  │        │                       ├─────────────────────▶│                  │
  │        │ ◀── 200 application/pdf  ◀───────────────────│                  │
  │ open   │                       │                      │                  │
  │◀───────│                       │                      │                  │
```

**Failure / fallback paths**
- If the storage origin is unreachable, the fronting service returns its configured upstream-error page. Edit that page on the fronting profile if a custom message is required.
- If `gtag.js` is blocked or fails, the page renders normally; only analytics is impacted.
- If a blob is missing (`404`), the response is the storage account's error document (typically `AccessRestricted.html`). Editorial fix is to upload the missing blob or correct the link in the parent `.htm`.
- If a redirect or security header is missing in production, the issue is in the **fronting service rule engine**, not in the legacy `web.config`.
- TLS failure with an Azure-managed cert is rare; if domain validation is pending, complete it in the fronting profile.

### 7.2 Editorial publish path

```
 Compliance       Local edits          Source control          Authorised             Azure
   editor         (HTML + PDF)         (GitHub)                  engineer             ($web + Front Door)
     │                │                    │                       │                       │
     │ produce PDF    │                    │                       │                       │
     ├───────────────▶│                    │                       │                       │
     │ edit Reports.htm                    │                       │                       │
     │ / Information.htm / Announcement.htm│                       │                       │
     ├───────────────▶│                    │                       │                       │
     │                │ commit + PR review │                       │                       │
     │                ├───────────────────▶│ merge to main         │                       │
     │                │                    ├──────────────────────▶│                       │
     │                │                    │                       │ MANUAL upload via     │
     │                │                    │                       │ Azure portal /        │
     │                │                    │                       │ az / azcopy           │
     │                │                    │                       ├──────────────────────▶│ (1) upload
     │                │                    │                       │                       │
     │                │                    │                       │ (optional) MANUAL     │
     │                │                    │                       │ cache purge in portal │
     │                │                    │                       ├──────────────────────▶│ (2) cache purge
     │                │                    │                       │                       │
     │ verify on prod │                    │                       │                       │ live
     │◀────────────────────────────────────────────────────────────────────────────────────│
```

> There is no CI/CD pipeline. Every step on the right of the diagram is hand-driven by an authorised engineer.

### 7.3 Apex-to-www and HTTP-to-HTTPS canonicalisation

```
 Client                            Front Door / Azure CDN
   │                                       │
   │ GET http://tvsholdings.com/  ────────▶│ rule "apex-to-www" matches Host=tvsholdings.com
   │ ◀────── 301 https://www.tvsholdings.com/  ─────────────────────────────────────────│
   │ GET http://www.tvsholdings.com/  ────▶│ rule "http-to-https" matches scheme=http
   │ ◀────── 301 https://www.tvsholdings.com/  ─────────────────────────────────────────│
   │ GET https://www.tvsholdings.com/ ─────▶│ cache lookup → origin Profile.htm (index doc)
   │ ◀────── 200 + security headers  ─────│
```

---

## 8. Database Interactions

**None.** The repository contains no database. There is no DB driver, no connection string, no ORM, no SQL, no NoSQL client. The only persistent store is Azure Blob Storage (`$web` container), which holds:

- Curated HTML pages (the index pages such as `Reports.htm`, `Information.htm`, `Announcement.htm`).
- A blob hierarchy of PDFs treated as the "data store" for disclosures.

Implication: there is **no transactional data layer**. Source control is the system of record; the storage account is a deploy target. Recommended Azure-native safety nets are blob **soft delete**, **versioning**, and (for DR) **GRS / RA-GRS** replication.

---

## 9. API Integrations

The site does not call or expose any APIs server-to-server. The only **third-party endpoint** loaded is the Google Tag Manager script:

| Endpoint | Method | Purpose | Auth |
|---|---|---|---|
| `https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL` | Browser GET | Load GA4 collector | None (public) |
| `https://www.googletagmanager.com/gtag/js?id=UA-120525446-1` | Browser GET | Legacy UA (still on older pages) | None (public) |
| `https://www.google-analytics.com/g/collect?...` | Browser GET (initiated by gtag) | Beacon page-view events | None (public) |

There are **no first-party APIs** in this codebase.

There is no automated CI/CD pipeline; deploys are manual blob uploads to the `$web` container performed by an authorised engineer using the Azure portal, `az` CLI, or `azcopy`. Those Azure REST calls are control-plane and not part of the runtime contract.

Outbound hyperlinks to NSE India, the SCL APD portal, and `mailto:` addresses are **navigation only** — the browser performs a top-level navigation; the site does not negotiate with these systems.

---

## 10. Authentication / Authorization Flow

**There is no end-user authentication or authorization in this site.** All content is public and read-only.

Where the codebase mentions "Login":
- The legacy SCL pages link to `http://www.sclapd.com/` and `http://www.sclftp.com/shareholders/login.aspx` (the latter is currently commented out in the active markup). Both are **separate systems on different domains** and not part of this repository.

Editor-side auth (deployment):
- There is no CI/CD pipeline today. Deploys are performed **manually** by an authorised engineer using their own Azure identity, via the Azure portal, `az login` + `az storage blob upload`, `azcopy login` + `azcopy`, or Azure Storage Explorer.
- Access to the storage account is controlled by **Azure RBAC**. Recommended minimum: grant the `Storage Blob Data Contributor` role on the `$web` container (not on the entire storage account, and not on the entire subscription).
- For ad-hoc deploys, a SAS token with limited scope and short TTL can be issued in lieu of full sign-in — the SAS must never be committed to this repository.

---

## 11. External Systems

Already enumerated in §5.1 ("Major components"). Re-listed here as a single reference for partner teams:

| External system | Interaction style | Owned by |
|---|---|---|
| Google Tag Manager / GA4 | Browser-loaded `<script>` | Google |
| Google Search Console | Static verification file at `/google451a3e51028a5485.html` | Google |
| NSE India (stock tracker) | Outbound hyperlink (user-initiated) | NSE |
| BSE / NSE filings | The site hosts copies of PDFs that are also filed directly with the exchanges; no API call | Exchanges |
| Integrated Registry Management Services (RTA) | Email reference (`einward@integratedindia.in`) | Integrated |
| Beacon Trusteeship / Catalyst Trusteeship (Debenture trustees) | Address / email reference | Trustees |
| CRISIL | PDFs hosted on this site link to CRISIL ratings | CRISIL |
| Legacy SCL APD portal (`sclapd.com`) | Outbound hyperlink (legacy pages only) | Separate SCL system |

---

## 12. Infrastructure Dependencies

| Layer | Dependency | Notes |
|---|---|---|
| Edge | **Azure Front Door** or **Azure CDN** | Owns the custom domain, HTTPS termination, redirect rules, security headers, caching, and (recommended) WAF. All redirect / header behaviour lives here. |
| Origin | **Azure Storage Account** with the **static website** feature enabled, container `$web` | Anonymous public read for blobs. Recommended: enable soft-delete, versioning, change-feed; use RA-GRS or GRS replication. |
| TLS | Azure-managed certificate on the fronting service | If domain validation is pending, complete it in the Front Door / CDN profile. |
| DNS | `tvsholdings.com` apex + `www` resolves to the Front Door / CDN endpoint | Both names must be registered on the fronting profile; the apex → www redirect itself is performed by Front Door / CDN, not by DNS. |
| Storage class | Standard (Hot) tier for `$web` | PDFs and HTML are read-frequently; Hot is the right default. |
| Runtime | None | No Node, no .NET application code, no Python, no Java. |
| Client runtime | jQuery 3.5.1 + DynamicDrive scripts (vendored) | No package manager; no automated update path. |
| Observability | Google Analytics 4 (browser-side) + (recommended) **Azure Storage diagnostic logs → Log Analytics** + **Front Door access logs** | Server-side request visibility currently relies on Azure logs being enabled on the fronting service and the storage account. |
| Source control | **GitHub** — `https://github.com/D2C-Website/TVS-Holdings` | System of record for HTML and PDF content. |
| CI/CD | **None today.** Deploys are manual uploads to `$web` by an authorised engineer (Azure portal, `az` CLI, or `azcopy`). No automated pipeline, no service-principal-driven release job. | Recommended (future): a GitHub Actions workflow on `main` that runs `az storage blob upload-batch` and (optionally) `az afd endpoint purge`. |
| Domain validation | `google451a3e51028a5485.html` | Must remain reachable at the public site root through the fronting service. |

---

## 13. Deployment & Rollout Plan

### 13.1 Steady-state deployment

- Source of truth is the GitHub repository <https://github.com/D2C-Website/TVS-Holdings>.
- **Deployment is manual.** There is no CI/CD pipeline. After a change is merged to `main`, an authorised engineer pulls the latest code locally and uploads the changed blobs to the storage account's `$web` container.
- The engineer authenticates with their own Azure identity (no shared service principal, no committed credentials) and uses one of:
  - **Azure portal** — *Storage browser* → `$web` → drag-drop the changed file(s).
  - **Azure CLI** — `az login` then `az storage blob upload` / `az storage blob upload-batch --auth-mode login`.
  - **AzCopy** — `azcopy login` then `azcopy copy` / `azcopy sync`.
  - **Azure Storage Explorer** (desktop client).
- A deploy is a copy of the changed `.htm` and `.pdf` blobs only. Whole-tree syncs are also possible but not required for incremental edits.
- The legacy `web.config` is included in the source tree but does not need to be re-uploaded — it is inert under Blob Storage and (recommended) should be excluded from the deploy set.
- If a fronting Azure Front Door / Azure CDN profile is in use and edge caching is enabled, the engineer manually purges the affected paths in the Azure portal after upload (or waits for the configured TTL to expire).
- Validation after deploy: spot-check the affected page in production, confirm the new PDF resolves, confirm `www` and HTTPS redirects still apply (these are enforced by the fronting service).

### 13.2 Rollout pattern (recommended for any non-trivial change)

| Stage | Description |
|---|---|
| Pre-flight | Open the page locally; if it has `<base href="https://www.tvsholdings.com" />`, preview against a staging mirror instead. Run a link-checker against the changed page. |
| Stage / pre-prod | Upload to a non-production storage account (or a separate `$web` container behind a non-production Front Door endpoint); verify with the compliance owner. |
| Production | Upload during a low-traffic window. Manually purge the fronting cache for the affected paths if edge caching is enabled. |
| Verification | Open the index page (e.g. `Reports.htm`) and the linked PDF in a fresh browser. Verify GA4 receives the page-view in real-time view. |

### 13.3 Rollback / hotfix
- Static deployments are **trivially reversible**. Roll back by re-running the deploy job from the previous commit on `main`.
- For a single-page emergency fix (e.g., a broken disclosure link), upload the corrected blob directly to `$web` via `az storage blob upload`, then purge the fronting cache; back-port the change to source control.
- If **soft delete** is enabled on the storage account (recommended), recently overwritten or deleted blobs can be restored via `az storage blob undelete` for the configured retention window. If **versioning** is enabled, the previous version can be promoted explicitly.
- For a fronting-service regression (wrong redirect / header rule), restore the previous version of the rule engine configuration in the Azure portal or re-apply IaC.
- No data migration is ever required.

### 13.4 Feature flags
- Not applicable — the site has no runtime feature toggles. "Phased rollout" is achieved by publishing PDFs to year-folders that aren't yet linked, then editing the parent `.htm` to expose them on the cut-over date.

---

## 14. Metrics to be Tracked

### 14.1 Availability & performance (infra-tier, must be added by hosting team)

| Metric | Source | Alarm |
|---|---|---|
| HTTP 5xx rate | Front Door / CDN access logs (Log Analytics) | > 1% over 5 min |
| HTTP 4xx rate (esp. 404 on PDFs) | Front Door / CDN logs | > 5% over 15 min — likely linkrot |
| TTFB (P50, P95) | Front Door / CDN metrics | P95 > 1 s for 10 min |
| HTTPS handshake errors | Front Door / CDN | > 0.1% sustained |
| Storage account availability + transactions | Azure Monitor (`Availability`, `Transactions`, `SuccessE2ELatency`) | Per Azure SLA |
| Cache-hit ratio at edge | Front Door / CDN metrics | < 80% triggers cache-policy review |
| Certificate expiry | Front Door / external monitor | Alarm 30 days before expiry |
| DNS resolution for `tvsholdings.com` / `www.tvsholdings.com` | External monitor | Any failure |

### 14.2 Content quality (editorial-tier)

| Metric | Source | Alarm |
|---|---|---|
| Broken-link count | Scheduled link-checker | > 0 (open ticket) |
| Pages still referencing deprecated UA `UA-120525446-1` | grep over repo | Track to zero |
| Pages still embedding Flash assets | grep over repo | Track to zero |
| `web.config` still uploaded to `$web` | Storage inventory | Track to zero (it is inert) |

### 14.3 Engagement (analytics-tier)

| Metric | Source |
|---|---|
| Page views per investor index page | GA4 (`G-DPMX50C7QL`) |
| Top exit links (PDF downloads) | GA4 enhanced measurement |
| Geo / device / browser breakdown | GA4 |

---

## 15. Data Analytics / Data Engineering Metrics / Tables

**Data lake integration: not enabled** for this repository.

- No first-party data is collected by the site.
- All telemetry resides in Google Analytics. If long-term retention beyond GA4's standard horizon is required, the BigQuery export from GA4 can be enabled — that pipeline would live outside this repository and is not part of the site's HLD.
- Server-side request logs from the storage account and the fronting service can be sent to **Azure Log Analytics** for retention and ad-hoc Kusto queries. That wiring is infra-owned and not part of this repo.

---

## 16. Alternatives Considered

### Option A — Migrate to a CMS (e.g., WordPress)
- **Pros:** Editorial UX, role-based publishing, plugins for SEO and accessibility, shared templates eliminate duplicated chrome.
- **Cons:** Introduces an application server, a database, an authentication boundary, and a much larger attack surface. Drives up Tier classification effectively to Tier 2-strict because a CMS compromise can deface investor disclosures. Migration risk includes URL changes that would break filings already lodged with NSE/BSE.
- **Verdict:** Rejected for now. Disproportionate to a read-only disclosure site.

### Option B — Move to a static-site generator + Git-based publishing (Jekyll / Hugo / Eleventy)
- **Pros:** Eliminates header/footer duplication via templates, enables a build-time link checker, supports preview environments, retains zero-runtime hosting (output still uploads to `$web`).
- **Cons:** Requires editorial team to learn Markdown / a publishing tool, or requires engineering to mediate every change.
- **Verdict:** Reasonable medium-term option; should be revisited when the next major content refresh is scheduled.

### Option C — Azure Static Web Apps instead of Blob Storage + Front Door
- **Pros:** Azure Static Web Apps has built-in routing rules (`staticwebapp.config.json`), automatic HTTPS, GitHub Actions integration, and per-environment preview URLs out of the box.
- **Cons:** Migration would require re-pointing the custom domain and re-validating every NSE/BSE-published URL. The current Blob + Front Door pattern already satisfies the requirements.
- **Verdict:** Worth considering at the next major refresh, alongside Option B.

### Option D — Keep Blob + Front Door + tighten the rule engine (current recommendation, see §6)
- **Pros:** Zero migration risk; addresses the highest-impact gaps (HSTS, CSP, soft-delete, versioning, log shipping).
- **Cons:** Does not solve duplicated-chrome editorial pain.
- **Verdict:** Proposed near-term path.

---

## 17. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Storage account region outage — full site outage | Low | High (regulatory visibility) | Use **GRS / RA-GRS** replication; document failover runbook; rely on Front Door's global edge to absorb short blips |
| R2 | TLS certificate expires | Low | High | Use **Azure-managed cert** on the fronting service (auto-renews) |
| R3 | Linkrot — a renamed PDF blob breaks dozens of investor links | Medium | Medium | Add CI link-checker; standardise on `Investor/TVSH/<YYYY>/<Section>/` naming |
| R4 | Editor unintentionally edits `web.config` expecting it to apply, but Blob Storage does not interpret it | Medium | Medium | Strongly recommend deleting `web.config` from the deploy set; document clearly that redirects/headers live on the fronting service |
| R5 | `web.config` is reachable as plain text from `$web` (anyone can `curl` it) | Medium | Low–Medium | Block the path with a fronting rule, or — preferred — exclude it from the deploy set entirely |
| R6 | Deprecated GA UA endpoint silently stops accepting hits | High (already deprecated) | Low | Remove all references to `UA-120525446-1` |
| R7 | Flash assets fail to render → broken visual elements on a few legacy pages | High (already happening) | Low | Remove `.swf` / `.fla` references; replace banners with images or HTML5 |
| R8 | `<base href="...">` causes a partner editor to deploy a draft that points all relative links at production | Medium | Medium | Document the gotcha; remove `<base>` tags from pages that don't truly need them |
| R9 | Defacement via compromised CI/CD service principal | Low | High | Out-of-repo: scope the SP to `$web` only, enforce workload-identity / MFA on humans, audit Azure activity logs, enable storage account **immutability policies** for compliance-sensitive blobs |
| R10 | Cache-purge missed after a deploy → users see stale content | Medium | Medium | Make cache-purge a mandatory step in the deploy job; alarm on deploy duration anomalies |
| R11 | Search-engine deindexing if the storage account's *index document* is changed away from `Profile.htm` | Low | Medium | Treat the static-website settings (index/error doc) and the fronting redirect rules as protected configuration |
| R12 | Blob soft-delete / versioning not enabled, accidental delete is unrecoverable | Medium (default-off on older accounts) | High | Enable soft-delete + blob versioning on the storage account |

---

## 18. Scalability and Resiliency Considerations

### 18.1 Scalability
- The workload is **read-only static assets**; throughput is bounded by Front Door / CDN edge capacity, which scales transparently. Azure Blob Storage has very high request limits per storage account; investor traffic, including filing-day spikes, is well within them.
- **Horizontal scale is built-in** at the edge by Front Door / CDN. Page HTML should be edge-cached for short TTLs (e.g., 60 s) and PDFs / images for longer (e.g., 1 day) once the cache policy is configured on the fronting service rule engine.
- **No vertical scale lever exists** — and none is needed.

### 18.2 Resiliency
- **No stateful tier** to worry about — recovery is purely re-uploading the repo to `$web` from source control.
- **Origin durability** is handled by Azure Storage SLA. Recommended: **GRS** or **RA-GRS** for cross-region redundancy.
- **Edge durability** is handled by Front Door's global POPs.
- **Disaster recovery** RTO ≤ 4 h is realistic via the documented rebuild runbook: provision a new storage account, enable static-website, upload from GitHub, point the fronting profile at the new origin, validate.
- **Accidental delete / overwrite** recovery is via blob soft-delete + versioning (recommended).
- **DDoS** absorption is provided by Front Door (basic) and Front Door Premium / WAF (advanced).

### 18.3 What does **not** scale gracefully
- **Editorial throughput.** Because every page duplicates the navigation chrome, a site-wide nav change is a 150-file find-and-replace. This is not a runtime problem but is the single biggest scalability constraint on the editorial side. Mitigation: adopt a static-site generator (Option B above).

---

## 19. Appendix

### 19.1 Glossary

| Term | Meaning |
|---|---|
| AGM | Annual General Meeting |
| BSE | Bombay Stock Exchange |
| CDN | Content Delivery Network |
| CIC | Core Investment Company (an RBI-registered NBFC category) |
| CSP | Content-Security-Policy header |
| DCV | Domain Control Validation (used by certificate authorities) |
| GA4 | Google Analytics 4 (the current generation of Google Analytics) |
| HSTS | HTTP Strict Transport Security |
| IEPF | Investor Education and Protection Fund (statutory fund for unclaimed dividends) |
| IIS | Internet Information Services (Microsoft's web server — the previous hosting platform; not used today) |
| LRS / ZRS / GRS / RA-GRS | Azure Storage replication options: Local / Zone / Geo / Read-Access Geo |
| NBFC | Non-Banking Financial Company |
| NCD | Non-Convertible Debenture |
| NSE | National Stock Exchange of India |
| RBI | Reserve Bank of India |
| RPO | Recovery Point Objective |
| RPT | Related-Party Transaction |
| RTA | Registrar and Transfer Agent (in this site, Integrated Registry Management Services) |
| RTO | Recovery Time Objective |
| SCL | Sundaram-Clayton Limited (legacy company name) |
| SE | Stock Exchange |
| SPOF | Single Point of Failure |
| TLS | Transport Layer Security |
| TVSH | TVS Holdings Limited (current company name) |
| UA | Universal Analytics (Google's previous-generation analytics, deprecated) |

### 19.2 Repository conventions (for partner editors)

- **New disclosure PDF:** place under `Investor/TVSH/<YYYY>/<Section>/` (one of `Announcements`, `Corporate`, `Disclosures`, `Informations`, `RBIDisclosures`, `Reports`, `StockExchange`).
- **Linking the new PDF:** edit the corresponding root-level `.htm` (`Reports.htm`, `Information.htm`, `Announcement.htm`, `Disclosures.htm`, `RBIDisclosures.htm`, `StockExchange.htm`, `Corporate.htm`, `PostalBallot.htm`, `ContactInformation.htm`).
- **Newspaper publication:** mirror the PDF in `Announcements/NewspaperPublication/<YYYY>/`.
- **Localised content:** apply changes in `SCL-Japan/`, `SCL-German/`, `SCL-Korean/` mirrors only when the corresponding language stakeholder approves; these are not auto-synced from English.

### 19.3 Files that must remain at the document root after any migration

- `Profile.htm` (storage account *index document*)
- `AccessRestricted.html` (storage account *error document*, recommended)
- `google451a3e51028a5485.html` (Search Console verification)
- `robots_dummy.txt` (rename to `robots.txt` if and when search-engine indexing policy is finalised)

### 19.4 Out-of-scope / intentionally omitted

This document avoids specifying:
- Deployment credentials, Azure subscription IDs, storage account names, resource-group names, service-principal client IDs / secrets, SAS tokens.
- Internal hostnames, IPs, jump-box endpoints, or VPN ranges.
- The internal email distribution list for compliance approvals.
- Registrar API keys or any inbound credential to external systems.
- Any pricing, SLA terms, or commercial contracts with vendors (Google, CRISIL, Integrated, BSE, NSE, trustees).

Partners requiring any of the above must request them through the company-secretariat handover process.

---

*Authored for external engineering partners. Any deviation from this design — particularly to the storage account static-website settings, the fronting service rule engine, the index/error document, or the SEO/SSL verification blobs at the site root — must be reviewed by the engineering owner before deployment.*

# High Level Code Document — TVS Holdings Limited Website

> Vendor onboarding reference for the public-facing corporate / investor-relations website hosted at `https://www.tvsholdings.com`.

| | |
|---|---|
| Repository | <https://github.com/D2C-Website/TVS-Holdings> |
| Production URL | <https://www.tvsholdings.com> |
| Hosting | Azure Blob Storage (static website) + fronting Azure Front Door / Azure CDN |

---

## 1. Application Overview

The repository is a **static, multi-page corporate website** for **TVS Holdings Limited** (formerly *Sundaram-Clayton Limited*, "SCL"), a Reserve Bank of India registered Core Investment Company (CIC). It serves as the public corporate identity and statutory **investor-relations portal** for the listed entity.

| Attribute | Value |
|---|---|
| Application type | Static HTML website |
| Primary purpose | Corporate identity + statutory investor disclosures |
| Hosting platform | **Azure Blob Storage — static website feature** (`$web` container) |
| Fronting service (typical) | Azure Front Door / Azure CDN — terminates the custom domain, applies HTTPS, redirects, security headers, and caching |
| Server-side runtime | None — Blob Storage serves blobs; the fronting CDN/Front Door applies routing rules |
| Public URL | `https://www.tvsholdings.com` |
| Default landing page | `Profile.htm` (English) — set as the *index document* on the storage account, **not** by `web.config`; `Home.htm` exists as a legacy language picker |
| Content strategy | HTML pages link to versioned PDF/JPG artefacts stored as blobs |
| Languages | English (primary), Japanese, German, Korean — under `SCL-Japan/`, `SCL-German/`, `SCL-Korean/` blob prefixes |

There is **no application server code, database, or build pipeline** in the repository. All dynamic-looking sections (e.g. quarterly results, board notices) are implemented as hand-curated HTML pages that link to PDF files committed to the repo.

> **Heads-up on `web.config`.** The repository still ships `web.config` from the previous IIS-era hosting. **Azure Blob Storage does not process `web.config`** — its rewrite rules, headers, default document, and request filtering are inert in the current deployment. Anything that document claims is "enforced by IIS" is, in this hosting model, either configured on the fronting service (Front Door / CDN rule engine) or simply not happening and needs to be re-verified.

---

## 2. Major Modules / Components

The site is logically (not physically) organised into the following content modules. Each module is a set of root-level `.htm` pages that share the common stylesheet and navigation chrome.

| Module | Representative pages | Purpose |
|---|---|---|
| Public landing / About | `Profile.htm`, `Home.htm`, `Milestones.htm`, `FactSheet.htm`, `Global.htm`, `TVSGroup.htm`, `BoardofDirectors.htm` | Corporate profile, leadership, group structure |
| Investors — Reports | `Reports.htm` | Annual reports, quarterly financial results, related-party transactions |
| Investors — Information | `Information.htm` | Board-meeting notices, credit ratings, debenture-trustee details, IDs terms |
| Investors — Disclosures | `Disclosures.htm`, `RBIDisclosures.htm`, `NCDDisclosures/` | Regulatory disclosures including RBI / NBFC / NCD disclosures |
| Investors — Stock Exchange | `StockExchange.htm`, `Stockexchange/`, `StockExchange2021/`, `StockExchangeIntimation-2022/`, `StockExchangeIntimation2023/` | Year-wise NSE/BSE intimations |
| Investors — Announcements | `Announcement.htm`, `Announcements/`, `TranscriptAGM/`, `Advertisement/` | AGM notices, postal ballots, voting results, newspaper ads |
| Investors — Governance | `Corporate.htm`, `SecretarialCompliance.htm`, `Annualsecreterialcomplaince/` | Corporate governance reports, secretarial audit |
| Postal Ballot | `PostalBallot.htm`, `PostalBallotResults.htm` | Postal-ballot notices and outcomes |
| Contact / Sitemap / Legal | `Contact.htm`, `ContactInformation.htm`, `Sitemap.htm`, `Disclaimer.htm`, `terms.htm`, `AccessRestricted.html` | Static footer / legal pages |
| Localised microsites | `SCL-Japan/`, `SCL-German/`, `SCL-Korean/` | Multilingual mirrors of legacy SCL content |
| Legacy SCL pages | `aboutscl.htm`, `oldsclhome.htm`, `Plants.htm`, `Diecasting.htm`, `Machining.htm`, `Quality.htm`, `Environment.htm`, `Customers.htm`, `Careers.htm` | Historic manufacturing-era content retained for SEO / archive |
| Static assets | `images/`, `*.css`, `*.js`, `*.swf`, `*.gif` | Branding, layout, animations |
| PDF document store | `Investor/`, `Reports/`, `Web files/`, `Bin/`, `NCDDisclosures/`, `Announcements/` | All linked binary disclosures |

---

## 3. Folder Structure Explanation

```
TVS-Holdings/
├── .git/                            # Version control
│
├── *.htm / *.html                   # ~150 root-level pages (each is a self-contained view)
├── *.css                            # generalTVSH.css, layout.css, stylesheet.css, general*.css
├── *.js                             # jquery-3.5.1.min.js, ddaccordion.js, pngfix.js, thumbnailviewer2.js
├── *.swf / *.fla                    # Legacy Flash animations (banners, taglines)
├── web.config                       # ⚠ IIS-era leftover; NOT processed by Azure Blob Storage
├── google451a3e51028a5485.html      # Google Search Console site verification
├── robots_dummy.txt                 # Robots placeholder
│
├── images/                          # Banners, icons, logos, backgrounds
│
├── Investor/                        # Master document store for investor disclosures
│   ├── TVSH/                        # Post-rebrand (TVS Holdings) artefacts, organised by year
│   │   ├── 2023/ 2024/ 2025/ 2026/  # Each year has subfolders:
│   │   │   ├── Announcements/
│   │   │   ├── Corporate/
│   │   │   ├── Disclosures/
│   │   │   ├── Informations/
│   │   │   ├── RBIDisclosures/
│   │   │   ├── Reports/
│   │   │   └── StockExchange/
│   │   ├── Disclosures/  Information/
│   │   └── *.pdf                    # Standing policies (CSR, Whistle-blower, RPT, etc.)
│   ├── Notice/<YYYY>/               # Board-meeting notices grouped by year
│   ├── PostalBallot/                # Active postal-ballot package
│   ├── 2014PostalBallot/ ... 2022PostalBallot/  # Archived ballots
│   ├── CompositeScheme/             # Scheme-of-arrangement documents
│   ├── Register/                    # Statutory registers
│   ├── SCL_IEPF_2_ PDF FILES/       # Investor Education & Protection Fund records
│   ├── 16042020/                    # One-off publication date folder
│   └── *.pdf                        # Loose investor PDFs from the SCL era
│
├── Reports/                         # Quarterly financial-result PDFs (older naming)
├── Web files/                       # Pre-2018 financial results & supporting HTML/PDFs
├── Bin/                             # Older binary disclosures
│
├── Announcements/                   # AGM notices and newspaper publications
│   ├── 2021/ 2022/ 2023/
│   ├── NewspaperPublication/<YYYY>/
│   └── TVSH/
├── Advertisement/                   # Vernacular newspaper PDFs
├── TranscriptAGM/                   # AGM transcript PDFs
├── NCDDisclosures/<YYYY>/           # Non-Convertible Debenture disclosures
│
├── Stockexchange/                   # SE intimations (legacy)
├── StockExchange2021/               # SE intimations 2021
├── StockExchangeIntimation-2022/    # SE intimations 2022 (incl. Part II)
├── StockExchangeIntimation2023/     # SE intimations 2023
├── Stock Exchange Intimation - 2021/
├── may112021/                       # Date-stamped event folder (HTML + supporting files)
│
├── Annualsecreterialcomplaince/     # Annual secretarial-compliance certificates
│
├── SCL-Japan/  SCL-German/  SCL-Korean/   # Localised mirror sites (each contains its own
│                                          # images/ Information_files/ Web files/ tree)
│
├── *_files/                         # Auto-saved sidecars from MS Word "Save as HTML" exports
│                                    # (Doc1_files, Information_files, JQMinfo_files,
│                                    #  June 2010_files, Mar2008_files, Sep2009_files, ...)
│
└── docs/                            # This documentation folder
    └── hlddoc.md                    # High-level document (this file)
```

### Naming conventions observed

- Quarterly results: `Quarter Ended <DD MonthYYYY>.pdf` or `Quarterended<DDMMYYYY>.pdf`
- Annual return: `AnnualReturn<YYYY>.pdf`
- Board-meeting notice: `Notice of Board Meeting - <Month>.pdf`
- Year folders use 4-digit calendar year (`2023`, `2024`, ...). After the rebrand, files moved into `Investor/TVSH/<YYYY>/<Section>/`.

---

## 4. Core Business Workflows

These are the **content workflows** the site supports — there is no transactional / runtime workflow.

### 4.1 Investor disclosure publication
1. Compliance team produces a PDF (financial result, board-meeting notice, RPT, etc.).
2. PDF is placed under the relevant year folder, e.g. `Investor/TVSH/<YYYY>/<Section>/`.
3. The corresponding listing page (`Reports.htm`, `Information.htm`, `Announcement.htm`, etc.) is edited to add a new `<li><a href="...">` link.
4. Files are uploaded **manually** to the storage account's `$web` container — there is no CI/CD pipeline. An authorised engineer uploads via the **Azure portal** (`Storage browser` → `$web` → drag-drop), or via `az storage blob upload` / `azcopy` / Azure Storage Explorer with their own Azure identity. If a fronting CDN / Front Door cache is in use, purge the affected paths in the portal afterwards.

### 4.2 Annual General Meeting (AGM) cycle
- Notice published — added to `Announcement.htm` under the year heading and stored in `Investor/TVSH/<YYYY>/Announcements/`.
- Newspaper advertisement (English + Tamil) — stored in `Announcements/<YYYY>/` or `Investor/TVSH/<YYYY>/Announcements/`.
- AGM transcript — stored under `TranscriptAGM/`.
- Voting results — added to `Announcement.htm` under "AGM Voting Results".

### 4.3 Quarterly financial-result publication
- Audited / unaudited PDF dropped in `Investor/TVSH/<YYYY>/Reports/` (or `Reports/` / `Web files/` for legacy).
- Newspaper publication (English + Tamil) added under `Announcements/NewspaperPublication/<YYYY>/`.
- `Reports.htm` updated with the new entry at the top of the "Quarterly Reports" list.

### 4.4 Stock-exchange (NSE / BSE) intimations
- Each intimation is saved as a PDF under `StockExchangeIntimation<YYYY>/` and surfaced from `StockExchange.htm`.

### 4.5 RBI / NBFC / NCD disclosures
- The CIC-registration status drives ongoing RBI disclosures, surfaced from `RBIDisclosures.htm` and `Disclosures.htm`, with sources under `Investor/TVSH/<YYYY>/RBIDisclosures/` and `NCDDisclosures/<YYYY>/`.

### 4.6 Postal ballot
- Each ballot has its own folder (`Investor/2022PostalBallot/`, etc.). `PostalBallot.htm` and `PostalBallotResults.htm` link the active and historical packs.

### 4.7 Investor-grievance routing (out-of-band)
- The site does not collect data. Grievances are routed by email to the registrar (`einward@integratedindia.in`) and the company secretariat (`corpsec@tvsholdings.com`) per `Contact.htm`.

---

## 5. Key Services / Classes

This is a static site, so there are no backend classes. The notable client-side components are:

| Component | File(s) | Role |
|---|---|---|
| jQuery 3.5.1 | `jquery-3.5.1.js`, `jquery-3.5.1.min.js` | DOM manipulation library used by accordion / menu scripts |
| `ddaccordion.init` | `ddaccordion.js` (vendored from DynamicDrive) | Collapsible accordion menu on `index.htm` |
| `thumbnailviewer2.js` | Root | Image thumbnail / preview viewer (DynamicDrive) |
| `pngfix.js` | Root | Legacy IE6 PNG-transparency shim, conditionally loaded via `<!--[if lt IE 7]>` |
| Right-click disabler | Inline in most pages | Trivial `oncontextmenu` override that displays an alert (cosmetic, not a security control) |
| `gtag()` Google Analytics loader | Inline in most pages | Google Analytics 4 with measurement ID `G-DPMX50C7QL`; some legacy pages still reference Universal Analytics ID `UA-120525446-1` |
| Language picker | `Home.htm` | Four buttons that route to English / 日本語 / Deutsch / 한국의 micro-sites |
| Fronting CDN routing rules (Front Door / Azure CDN) | Configured in the Azure portal / IaC, **not** in this repo | (a) HTTP → HTTPS redirect, (b) `tvsholdings.com` → `www.tvsholdings.com` redirect, (c) custom domain + TLS termination, (d) cache policy, (e) optional WAF |
| Fronting CDN security headers | Configured in the Front Door / CDN rule engine | Sets HSTS, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, cache-control; suppresses fingerprinting headers |
| Default-document mapping | Storage account static-website setting (Azure portal / `az storage blob service-properties update --static-website`) | Pins `Profile.htm` as the index document and (recommended) `AccessRestricted.html` as the error document |
| **[Inert] `web.config`** | Repo root | Was the IIS source of redirects and headers in the previous deployment. **Azure Blob Storage does not interpret `web.config`** — it is served as a static text blob. Recommend either deleting it or moving it out of the deploy set. |
| Domain ownership | `google451a3e51028a5485.html` | Google Search Console verification |

---

## 6. External Integrations

| Integration | Where referenced | Purpose |
|---|---|---|
| Google Analytics (GA4) | `gtag.js` script blocks across most pages — measurement ID `G-DPMX50C7QL` | Site traffic analytics |
| Google Universal Analytics (legacy) | Older pages reference `UA-120525446-1` | Legacy analytics — should be retired with GA4 migration |
| Google Search Console | `google451a3e51028a5485.html` | Domain verification |
| NSE India | Outbound link `http://www.nseindia.com/companytracker/cmtracker.jsp?symbol=SUNCLAYTON` (legacy pages) | Live stock tracker (deep link, no API call) |
| BSE / NSE filings | Linked PDFs only | Statutory filings are uploaded directly to the exchanges; the site mirrors the PDFs |
| Integrated Registry (Registrar & Transfer Agent) | Email `einward@integratedindia.in` (`Contact.htm`) | Investor-grievance handling |
| Beacon Trusteeship / Catalyst Trusteeship | Listed in `Information.htm` | Debenture trustees for NCD holders |
| CRISIL | `Investor/SCL Crisil.pdf`, `Investor/CRISIL_Credit_Rating.pdf`, `Investor/Rating Rationale.pdf` | Credit-rating documents |
| SCL APD portal (legacy) | Outbound link `http://www.sclapd.com/` from older pages | Legacy login (Customer / Supplier) — external system, not part of this repo |
| SCL FTP (legacy, commented out) | `http://www.sclftp.com/shareholders/login.aspx?Company=SCL` | Legacy shareholder login — currently commented out in markup |
| Pixel Studios | Footer credit on `index.htm` | Original site designer |

> The `.asp` URLs referenced in legacy pages (`uploadlogin.asp`, `supplierlogin.asp`, `pgDisplayFiles1.asp`) point to **external sister applications**, not files served from this repository.

---

## 7. Major Dependencies

| Dependency | Version / Source | Notes |
|---|---|---|
| jQuery | 3.5.1 (vendored) | Sole runtime JS framework |
| DynamicDrive `ddaccordion` | Vendored | Accordion menus |
| DynamicDrive `thumbnailviewer2` | Vendored | Image hover viewer |
| `pngfix.js` | Vendored | IE6 PNG transparency shim |
| Adobe Flash assets (`*.swf`, `*.fla`) | Legacy | `home_fla.swf`, `tagline.swf`, `arrowanimation.swf` — Flash is end-of-life in browsers; these will not render on modern clients |
| Azure Blob Storage (static website) | Hosted in Azure subscription | Origin for all `.htm`, `.css`, `.js`, image, and PDF blobs |
| Azure Front Door / Azure CDN | Hosted in Azure subscription | Custom domain, HTTPS, redirects, security headers, caching, optional WAF |
| TLS certificate | Azure-managed cert | HTTPS termination on the fronting service |

There is **no `package.json`, `composer.json`, `pom.xml`, `requirements.txt`, or any other dependency manifest**. The site has no build step.

---

## 8. Runtime Architecture

```
                        ┌───────────────────────────────────────────────┐
                        │       Browser (HTTPS, modern browsers)        │
                        └───────────────────────────────────────────────┘
                                            │
                       (1) HTTP/1.1 GET https://www.tvsholdings.com/...
                                            │
                                            ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │             Azure Front Door / Azure CDN (fronting service)            │
        │                                                                        │
        │   Routing / rule engine (configured outside this repo):                │
        │     (a) Redirect tvsholdings.com → www.tvsholdings.com (301)           │
        │     (b) Redirect HTTP → HTTPS (301)                                    │
        │     (c) Custom-domain TLS termination (Azure-managed cert)              │
        │     (d) Security response headers:                                     │
        │           Strict-Transport-Security, X-Frame-Options=SAMEORIGIN,       │
        │           X-Content-Type-Options=nosniff, X-XSS-Protection=1;mode=block│
        │     (e) Cache policy per content type (HTML short, PDF/image long)     │
        │     (f) Optional WAF rules                                             │
        │                                                                        │
        │   Note: any redirect/header in the legacy web.config is NOT applied    │
        │   here automatically — it must be expressed as a rule on this layer.   │
        └────────────────────────────────────────────────────────────────────────┘
                                            │
                       (2) cache miss → fetch from origin
                                            │
                                            ▼
        ┌────────────────────────────────────────────────────────────────────────┐
        │           Azure Storage Account — Static Website ($web container)      │
        │                                                                        │
        │   Index document: Profile.htm                                          │
        │   Error document: AccessRestricted.html (recommended)                  │
        │                                                                        │
        │   Serves blobs:                                                        │
        │     *.htm / *.html / *.css / *.js / *.pdf / images/*                   │
        │                                                                        │
        │   Does NOT process: web.config (served as plain text if uploaded),     │
        │   <rewrite>, <httpProtocol>, <requestFiltering>, <sessionState>        │
        └────────────────────────────────────────────────────────────────────────┘

   Browser, in parallel, fetches:
     • https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL   (analytics)
     • Outbound clicks to NSE India / external SCL portals (no server-to-server calls)
```

Key points:
- **Stateless** — each request is a blob fetch; the origin performs no application logic.
- **No databases**, no message queues, no workers, no scheduled jobs.
- **No authentication or authorisation** is implemented in this codebase. References to "Login" point to external systems on other domains.
- **All redirect / security-header / canonicalisation behaviour lives on the fronting service**, not in the storage account or in this repo. Verify on the fronting profile when something looks wrong.

---

## 9. Important Entry Points

| Entry point | Purpose |
|---|---|
| `Profile.htm` | **Primary landing page.** Set as the storage account's *index document*. Serves the English "About us / Profile" view with the global header, top nav (Home / About us / Investors / Contact us), left sidebar, and footer. |
| `Home.htm` | **Language selector splash screen.** Four buttons routing to English (`Profile.htm`), Japanese (`SCL-Japan/Profile.htm`), German (`SCL-German/Profile.htm`), Korean (`SCL-Korean/Profile.htm`). |
| `index.htm` | Legacy SCL homepage (older "Sundaram-Clayton Limited" template, retains accordion menu). Not the active default document. |
| `Reports.htm` | Top of the Investor-relations tree — annual returns, RPT, quarterly results. |
| `Information.htm` | Board-meeting notices, debenture trustees, credit ratings, IDs terms. |
| `Announcement.htm` | AGM notices, voting results, newspaper advertisements, disclosures timeline. |
| `Disclosures.htm` / `RBIDisclosures.htm` | Statutory and RBI/CIC disclosures. |
| `StockExchange.htm` | NSE / BSE intimation index. |
| `Corporate.htm` | Corporate governance reports. |
| `PostalBallot.htm` / `PostalBallotResults.htm` | Postal-ballot lifecycle. |
| `Contact.htm`, `ContactInformation.htm` | Registered office, investor-grievance email. |
| `Sitemap.htm` | Hand-maintained sitemap. |
| `Disclaimer.htm`, `terms.htm`, `AccessRestricted.html` | Legal / restricted-content stubs. (`AccessRestricted.html` is also typically configured as the storage account's *error document*.) |
| `web.config` | ⚠ **IIS-era leftover.** Azure Blob Storage does not process `web.config` — its rewrite rules, headers, and default-document mapping are inert. Recommend deleting from the deploy set, or moving it to `legacy/`, after porting any required rules into the fronting service rule engine. |
| `google451a3e51028a5485.html` | Google Search Console domain-ownership verification (must remain at root). |

---

## 10. High-Level Data Flow

There is no application data flow in the conventional sense — only **content publication** (write-once by editors) and **document delivery** (read-only by visitors).

### 10.1 Content publication flow (editorial)

```
   ┌────────────────┐    ┌───────────────────┐    ┌──────────────────────┐
   │ Compliance /   │    │ Editor commits    │    │ Authorised engineer  │
   │ Secretarial    │──▶ │ root .htm page +  │──▶ │ MANUALLY uploads to  │
   │ team produces  │    │ drops PDF in      │    │ Azure Storage $web   │
   │ disclosure PDF │    │ Investor/TVSH/... │    │ (portal / az / azcopy)│
   └────────────────┘    └───────────────────┘    └──────────────────────┘
                                                            │
                                                            ▼
                                                  ┌──────────────────────┐
                                                  │ (Optional) manual    │
                                                  │ Front Door / CDN     │
                                                  │ cache purge if used  │
                                                  └──────────────────────┘
                                                            │
                                                            ▼
                                                  ┌──────────────────────┐
                                                  │ Public site reflects │
                                                  │ new disclosure       │
                                                  └──────────────────────┘
```

There is **no CI/CD pipeline today** — every deploy is a hand-driven blob upload by an authorised engineer.

### 10.2 Visitor read flow

```
   ┌─────────┐    1. GET https://www.tvsholdings.com/        ┌──────────────────┐    ┌──────────────────┐
   │ Browser │ ────────────────────────────────────────────▶ │  Front Door /    │ ─▶ │ Storage Account  │
   │         │                                                │  Azure CDN       │    │ ($web container) │
   │         │                                                │  - apex→www      │    │ index = Profile  │
   │         │                                                │  - HTTP→HTTPS    │    │                  │
   │         │                                                │  - sec headers   │    │                  │
   │         │                                                │  - cache         │    │                  │
   │         │  ◀── 200 Profile.htm + headers ─────────────── │                  │ ◀─ │                  │
   │         │                                                └──────────────────┘    └──────────────────┘
   │         │    2. GET /generalTVSH.css, /jquery-3.5.1.min.js, /images/*.jpg
   │         │  ◀── 200 (assets, mostly cache hits) ────────
   │         │
   │         │    3. GET https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL
   │         │  ────────────────────────────────────────────▶ Google Analytics
   │         │
   │         │    4. (user clicks an investor PDF link)
   │         │       GET /Investor/TVSH/2025/Reports/Quarter_Ended_30th_Sep_2025.pdf
   │         │  ◀── 200 application/pdf ─────────────────── (cache hit at edge, miss → origin)
   └─────────┘
```

### 10.3 What the application does *not* do

- No user input is collected. There are no `<form>` submissions, no APIs, no AJAX endpoints, no cookies set by application code.
- No PII, financial data, or shareholder data is stored in the codebase.
- No authentication. The "Login" links in legacy templates point to external systems on other domains.

---

## Appendix A — Notable Observations for Vendor Onboarding

1. **No build step, no package manager.** Edits to `.htm` files are reflected after deployment (and cache purge).
2. **Legacy assets coexist with current content.** Files such as `*.swf`, `*.fla`, `pngfix.js`, `Plants27072019.htm`, `Society24072019.htm`, and many `*Old.htm` / `*_bak.htm` are historical snapshots. Treat them as archive, not active code.
3. **Many `*_files/` folders** (e.g. `Doc1_files/`, `Information_files/`, `JQMinfo_files/`, `June 2010_files/`, `Mar2008_files/`, `Sep2009_files/`) are MS-Word "Save as Web Page" sidecars and should be considered binary content owned by their parent `.htm`.
4. **Mixed analytics IDs.** Live pages mostly use GA4 `G-DPMX50C7QL`; some legacy pages still embed UA `UA-120525446-1`. Consolidate when next refactoring.
5. **Some pages set `<base href="https://www.tvsholdings.com" />`** — this can break local previews because relative links resolve against the production hostname instead of the local file system.
6. **Right-click "disable" scripts** present on many pages provide no real security and cause UX friction — they can be removed without functional impact.
7. **`web.config` is inert** under Azure Blob Storage. All redirect / security-header / canonicalisation behaviour lives on the fronting service (Azure Front Door / Azure CDN) rule engine. Any platform migration must reproduce those rules at the new edge.
8. **Content-Security-Policy is drafted but commented out** in `web.config` (and therefore not active anyway). Implement it as a `Content-Security-Policy` response header on the fronting service.
9. **HSTS is conservatively low** (the inert `web.config` declared `max-age=86400`). Whatever value the fronting service emits is what is actually applied; production hardening would extend this to one year with `includeSubDomains; preload`.
10. **Document inventory is large** (PDF library across `Investor/`, `Reports/`, `Web files/`, `Announcements/`, etc.). Vendors taking over content management should prefer the newer `Investor/TVSH/<YYYY>/<Section>/` convention.

## Appendix B — Quick "where do I edit X?" map

| To change… | Edit… |
|---|---|
| Top-level navigation labels | The `<ul class="solidblockmenu">` block inside each `.htm` page (it is duplicated; there is no shared template) |
| Footer copyright | Repeated `&copy; Copyright TVS Holdings Limited 2023…` in every page |
| Default landing page | Storage account → static-website settings → *Index document* |
| Error / fallback page | Storage account → static-website settings → *Error document* |
| Apex→www and HTTP→HTTPS redirects | Front Door / Azure CDN rule engine (do **not** edit `web.config` — it is inert) |
| Security response headers (HSTS, X-Frame-Options, CSP, etc.) | Front Door / Azure CDN rule engine |
| Cache policy per content type | Front Door / Azure CDN rule engine |
| WAF rules | Front Door WAF policy |
| Add a new quarterly result | Drop PDF under `Investor/TVSH/<YYYY>/Reports/` and add `<li>` to `Reports.htm` |
| Add a new board-meeting notice | Drop PDF under `Investor/TVSH/<YYYY>/Informations/` and add link to `Information.htm` |
| Add a new SE intimation | Drop PDF under `Investor/TVSH/<YYYY>/StockExchange/` and add link to `StockExchange.htm` |
| Replace analytics ID | Search/replace `G-DPMX50C7QL` (and `UA-120525446-1` on legacy pages) |
| Update registered-office or grievance email | `Contact.htm`, `ContactInformation.htm` |

---

*Document generated for vendor onboarding. Sensitive operational details (Azure subscription IDs, storage account names, service-principal credentials, internal email distribution lists, registrar API keys, etc.) are intentionally excluded — request these separately through the company-secretariat handover process.*

# TVS Holdings Limited — Public Website

The static corporate and investor-relations website served at **<https://www.tvsholdings.com>**.

| | |
|---|---|
| Repository | <https://github.com/D2C-Website/TVS-Holdings> |
| Production URL | <https://www.tvsholdings.com> |
| Hosting | Azure Blob Storage (static website) + fronting Azure Front Door / Azure CDN |

> Companion docs (in this folder): [`hlddoc.md`](./hlddoc.md) (code walkthrough), [`HLD.md`](./HLD.md) (architecture), [`LLD.md`](./LLD.md) (implementation), [`API_SPEC.md`](./API_SPEC.md) (HTTP contract).

---

## 1. Overview

This repository is the source for the public website of **TVS Holdings Limited** (formerly Sundaram-Clayton Limited), a Reserve Bank of India registered Core Investment Company (CIC). The site discharges statutory **investor-relations and disclosure** obligations and presents corporate identity content.

| Property | Value |
|---|---|
| Type | Static HTML / CSS / JavaScript website |
| Hosting | **Azure Blob Storage — static website feature** (`$web` container) |
| Fronting service (recommended / typical) | **Azure Front Door** or **Azure CDN** for custom domain, HTTPS, redirects, security headers, WAF |
| Build step | None |
| Database | None |
| Authentication | None (read-only public site) |
| Default landing page | `Profile.htm` (English) — set on the storage account, not in `web.config` |
| Languages | English (primary); Japanese, German, Korean mirrors |

What the repo contains:
- ~150 root-level `.htm` pages (each self-contained — no template engine).
- A versioned PDF document store under `Investor/`, `Reports/`, `Announcements/`, `NCDDisclosures/`, `StockExchangeIntimation*/`.
- Vendored JS/CSS (jQuery 3.5.1, DynamicDrive accordion, layout / brand / legacy stylesheets).
- A legacy `web.config` from the previous IIS deployment. **Azure Blob Storage does not process `web.config`** — its rewrite rules, headers, default-document mapping, and request filtering are inert in the current hosting model. It is retained for reference until it is either deleted or its policies are migrated into the fronting service.

---

## 2. Setup

### Prerequisites
- **Git** for source control.
- **A modern browser** (Chrome / Edge / Firefox / Safari) for previewing.
- One of the following local servers (any will do for static preview):
  - **Python 3** (`python3 -m http.server`) — works cross-platform.
  - **Node** (`npx http-server`) — works cross-platform.
  - **VS Code Live Server** extension.
- **Azure CLI** (`az`) and / or **AzCopy** if you will deploy.
- *(optional)* A markdown viewer or VS Code to read the `docs/` files.

### Clone
```bash
git clone https://github.com/D2C-Website/TVS-Holdings.git
cd TVS-Holdings
```

There is **nothing to install** — no `npm install`, no `pip install`, no Maven, no Gradle. The repo is ready to serve.

---

## 3. Local Development

### 3.1 Quick preview (any OS)

```bash
# from the repo root
python3 -m http.server 8080
# then open http://localhost:8080/Profile.htm
```

or

```bash
npx http-server -p 8080 .
# then open http://localhost:8080/Profile.htm
```

### 3.2 Editing pages

- **Open the `.htm` file directly** in your editor; save and refresh the browser.
- Some pages declare `<base href="https://www.tvsholdings.com" />`. When this is present, **all relative links resolve against the production host**, not your local file system. To preview such a page locally, temporarily comment the `<base>` tag — and revert before committing.
- Header/footer/navigation markup is **duplicated** across pages. There is no shared layout. Site-wide cosmetic changes are find-and-replace operations across many files.
- Local preview will **not** apply the production redirects (apex→www, HTTP→HTTPS) or security headers — those are enforced by the fronting service in production, not by anything in this repo.

### 3.3 Adding a new investor PDF

Cheat sheet (full version in [`LLD.md`](./LLD.md) §17.1):

| Content type | Place file at | Then edit |
|---|---|---|
| Quarterly result | `Investor/TVSH/<YYYY>/Reports/Quarter_Ended_<...>.pdf` | `Reports.htm` |
| Annual report / return | `Investor/TVSH/<YYYY>/Reports/AnnualReturn<YYYY>.pdf` | `Reports.htm` |
| Board-meeting notice | `Investor/TVSH/<YYYY>/Informations/Notice_of_BoardMeeting_<Mon>_<YY>.pdf` | `Information.htm` |
| AGM / voting / newspaper ad | `Investor/TVSH/<YYYY>/Announcements/...` | `Announcement.htm` |
| RBI / NCD disclosure | `Investor/TVSH/<YYYY>/RBIDisclosures/...` or `NCDDisclosures/<YYYY>/...` | `RBIDisclosures.htm` / `Disclosures.htm` |
| Stock-exchange intimation | `Investor/TVSH/<YYYY>/StockExchange/...` (or legacy folders) | `StockExchange.htm` |
| Postal-ballot pack | `Investor/PostalBallot/...` | `PostalBallot.htm` / `PostalBallotResults.htm` |
| Corporate-governance report | `Investor/TVSH/<YYYY>/Corporate/...` | `Corporate.htm` |

Once a URL is published in a stock-exchange filing, **never change it.** Treat every published path as a permanent contract — including the blob name in `$web`.

---

## 4. Environment Variables

**None for the runtime.** This is a static site.

There are also no `.env` files, no application secrets, no API keys, no connection strings in the repository. Configuration that does exist lives entirely in:

| Surface | Where it lives | Owns |
|---|---|---|
| Hosting (origin) | Storage account static-website settings | Index document (`Profile.htm`), error document (e.g. `AccessRestricted.html`) |
| Custom domain, HTTPS, redirects, security headers, caching, WAF | Azure Front Door / Azure CDN routing rules and rule engine | apex→www, HTTP→HTTPS, HSTS, X-Frame-Options, etc. |
| Analytics measurement IDs | inline in each `.htm` `<head>` | GA4 `G-DPMX50C7QL` (and legacy UA `UA-120525446-1` on older pages) |
| Search-engine ownership | `google451a3e51028a5485.html` | Google Search Console |
| **Inert** in current hosting | `web.config` | Was IIS rewrite + headers + default document; **not processed by Azure Blob Storage** |

Deploy-time configuration (storage account name, container, subscription, service-principal credentials) is held by infra and **not** committed to this repo.

---

## 5. Build

**No build step.** Files are deployed as-is to the `$web` container.

If you want to *validate* the repo before committing, the recommended (optional) checks are:

```bash
# 1. Find broken internal links
npx broken-link-checker https://staging.tvsholdings.com -ro

# 2. Lint HTML
npx htmlhint "**/*.htm"

# 3. Spot remaining references to deprecated analytics
grep -rIn "UA-120525446-1" --include="*.htm"

# 4. Find pages that still embed Flash assets
grep -rIn "\.swf" --include="*.htm"

# 5. Confirm web.config has not been edited (it is inert under Azure Blob Storage)
git diff --name-only HEAD~1 HEAD | grep -i 'web.config' && echo "Note: web.config is not processed by Blob Storage."
```

None of these are wired into CI today; they are suggestions for a vendor adopting the repo.

---

## 6. Deployment

> Deployment credentials, subscription details, and the Azure resource identities (storage account name, resource group, etc.) are infrastructure-tier and intentionally **not** part of this repository. Request them through the engineering owner / company-secretariat handover.

### 6.1 Hosting topology (current)

```
       Browser
          │
          ▼
  Azure Front Door / Azure CDN     ← custom domain, HTTPS, apex→www, HTTP→HTTPS,
   (rule engine + WAF)               security headers, caching, optional WAF
          │
          ▼
  Azure Storage Account
   └── $web container               ← origin: static website feature
        ├── Profile.htm             (index document)
        ├── AccessRestricted.html   (error document)
        ├── Reports.htm  Information.htm  Announcement.htm  ...
        ├── images/  Investor/  Reports/  Announcements/  ...
        ├── jquery-3.5.1.min.js  layout.css  ...
        └── google451a3e51028a5485.html
```

### 6.2 What gets deployed
- All `.htm` and `.html` files at the repo root and inside `SCL-*/`.
- `images/`, the three CSS files, and the vendored JS files.
- All folders under `Investor/`, `Reports/`, `Announcements/`, `NCDDisclosures/`, `StockExchangeIntimation*/`, etc.
- `google451a3e51028a5485.html` (Google Search Console verification).
- **Not** load-bearing: `web.config` (IIS-era leftover; Blob Storage ignores it). Recommend excluding from upload.

### 6.3 Deploy flow (manual upload — there is no CI/CD pipeline)

Deployment today is a **manual upload** by an authorised engineer. There is **no CI/CD pipeline**, no automated cache-purge step, and no service-principal-driven release job. Pick whichever option below your team is using.

**Option A — Azure Portal (point-and-click)**
1. Navigate to the storage account in the Azure Portal.
2. Open *Storage browser* → *Blob containers* → `$web`.
3. Drag the changed file(s) (or the whole folder) into the matching path under `$web`.
4. Confirm overwrite when prompted.

**Option B — Azure CLI**
```bash
# Authenticate as your own Azure identity (no service principal needed)
az login

# Upload only the changed files (preserving folder structure)
az storage blob upload-batch \
  --account-name <storageAccount> \
  --auth-mode login \
  --destination '$web' \
  --source . \
  --overwrite true

# Or upload one specific file
az storage blob upload \
  --account-name <storageAccount> \
  --auth-mode login \
  --container-name '$web' \
  --file Investor/TVSH/2026/Reports/Quarter_Ended_30th_June_2026.pdf \
  --name Investor/TVSH/2026/Reports/Quarter_Ended_30th_June_2026.pdf \
  --overwrite
```

**Option C — AzCopy (`azcopy sync`)**
```bash
# Authenticated to Azure (e.g. via `azcopy login`)
azcopy sync \
  "." \
  "https://<storageAccount>.blob.core.windows.net/\$web" \
  --recursive \
  --delete-destination=false
```

> If a fronting Azure Front Door / Azure CDN profile is in front of the storage account and edge caching is enabled, the new content may not be visible immediately. Either wait for the configured TTL to expire, or have an Azure-portal-authorised engineer manually purge the cache for the affected paths (Front Door / CDN profile → *Endpoints* / *Domains* → *Purge*).

### 6.4 Post-deploy verification

Run from any machine on the public internet:

```bash
# Page renders
curl -sS -I https://www.tvsholdings.com/Profile.htm   # expect 200

# Apex-to-www redirect (enforced at the fronting service)
curl -sS -I https://tvsholdings.com/                  # expect 301 → https://www.tvsholdings.com/

# HTTP-to-HTTPS redirect (enforced at the fronting service)
curl -sS -I http://www.tvsholdings.com/               # expect 301 → https

# Security headers (enforced at the fronting service)
curl -sS -I https://www.tvsholdings.com/Profile.htm   # expect HSTS, X-Frame-Options, etc.

# A new PDF link
curl -sS -I 'https://www.tvsholdings.com/Investor/TVSH/2026/Reports/<file>.pdf'  # expect 200
```

If any redirect or header is missing in production, the issue is in the **fronting service rule engine** (Azure portal), not in this repo. The `web.config` in the repo will not fix it.

### 6.5 Rollback

Static deployments are trivially reversible. Rollback options:

1. **Re-upload the previous version of the file** from your local Git checkout (`git checkout <previous-commit> -- <path>` then re-upload that path to `$web`).
2. **Restore from blob soft delete or versioning**, if enabled on the storage account: `az storage blob undelete ...` (soft delete) or promote a previous version (versioning).
3. **For a single-PDF emergency**, simply upload the corrected file via the Azure Portal.

After rollback, manually purge the fronting cache for the affected paths if edge caching is configured.

No data migration is ever required.

> **Recommendation:** Enable **soft delete** and **blob versioning** on the storage account so an accidentally overwritten or deleted blob can be recovered without a re-upload from Git. This is one click in the Azure portal.

---

## 7. Testing

There is **no automated test suite** in the repo today. Testing is currently a manual smoke check, plus optional tooling for vendors to add.

### 7.1 Manual smoke checklist (after every deploy)

- [ ] `https://www.tvsholdings.com/` resolves to the Profile page (200).
- [ ] `https://tvsholdings.com/` 301-redirects to `https://www.tvsholdings.com/`.
- [ ] `http://www.tvsholdings.com/` 301-redirects to HTTPS.
- [ ] The page you edited renders correctly in Chrome and Firefox.
- [ ] Any new PDF link opens (HTTP 200, not 404).
- [ ] Security headers present (`HSTS`, `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`).
- [ ] If a fronting CDN / Front Door is in use and the change is not visible, manually purge the cache for the affected paths in the Azure portal.
- [ ] GA4 real-time dashboard shows the test hit (measurement ID `G-DPMX50C7QL`).

### 7.2 Recommended synthetic monitors

A vendor taking over operations should add the probe set documented in [`API_SPEC.md`](./API_SPEC.md) §14.

### 7.3 Recommended pre-commit checks (not yet wired)

```bash
# Internal-link integrity against staging
npx broken-link-checker https://staging.tvsholdings.com -ro

# HTML lint
npx htmlhint "**/*.htm"

# Confirm no new <base href="..."> sneaks in on a page that didn't have one
git diff --diff-filter=AM | grep -E "^\+.*<base href"
```

---

## 8. Folder Structure

```text
TVS-Holdings/
├── docs/                            # supplementary engineering documentation
│   ├── README.md                    # this file (onboarding quickstart)
│   ├── hlddoc.md                    # code walkthrough / vendor onboarding
│   ├── HLD.md                       # architecture (high-level design)
│   ├── LLD.md                       # implementation (low-level design)
│   └── API_SPEC.md                  # HTTP-protocol contract / OpenAPI
│
├── web.config                       # ⚠ IIS-era leftover, NOT processed by Azure Blob Storage
├── google451a3e51028a5485.html      # Google Search Console verification (must stay at site root)
├── robots_dummy.txt                 # placeholder; not active
│
├── *.htm / *.html                   # ~150 self-contained pages
├── *.css                            # layout.css, generalTVSH.css, stylesheet.css, ...
├── *.js                             # jquery-3.5.1.min.js, ddaccordion.js, pngfix.js, thumbnailviewer2.js
├── *.swf / *.fla                    # legacy Flash (do not render in modern browsers)
│
├── images/                          # brand banners, icons, backgrounds
│
├── Investor/                        # primary investor-document store
│   ├── TVSH/                        # post-rebrand artefacts, by year
│   │   └── <YYYY>/
│   │       ├── Announcements/
│   │       ├── Corporate/
│   │       ├── Disclosures/
│   │       ├── Informations/
│   │       ├── RBIDisclosures/
│   │       ├── Reports/
│   │       └── StockExchange/
│   ├── Notice/<YYYY>/               # board-meeting notices (older convention)
│   ├── PostalBallot/                # active postal-ballot pack
│   ├── <YYYY>PostalBallot/          # archived ballots
│   └── *.pdf                        # loose legacy artefacts
│
├── Reports/                         # legacy financial-result PDFs (pre-rebrand)
├── Web files/                       # pre-2018 financial results & supporting files
├── Bin/                             # older binary disclosures
│
├── Announcements/                   # AGM notices and newspaper publications
│   └── NewspaperPublication/<YYYY>/
├── Advertisement/                   # vernacular newspaper PDFs
├── TranscriptAGM/                   # AGM transcript PDFs
├── NCDDisclosures/<YYYY>/           # Non-Convertible Debenture disclosures
│
├── Stockexchange/                   # SE intimations (legacy)
├── StockExchange2021/               # SE intimations 2021
├── StockExchangeIntimation-2022/    # SE intimations 2022
├── StockExchangeIntimation2023/     # SE intimations 2023
│
├── Annualsecreterialcomplaince/     # annual secretarial-compliance certificates
│
├── SCL-Japan/                       # localised mirror sites
├── SCL-German/                      # (each contains its own images/, Web files/, ...)
├── SCL-Korean/
│
└── *_files/                         # MS-Word "Save as HTML" sidecars (treat as binary)
```

Files / blobs that **must remain at the site root**:

```
Profile.htm                                 (storage-account index document)
AccessRestricted.html                       (storage-account error document — recommended)
google451a3e51028a5485.html                 (Search Console verification)
```

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Local preview loads but all images / CSS are missing | The page declares `<base href="https://www.tvsholdings.com" />`, so relative paths resolve against production | Temporarily comment the `<base>` tag; revert before committing |
| New PDF link returns 404 in production | Linkrot, **or the fronting cache still holds the old 404 from before the upload** | (a) Verify the blob exists in `$web` with the exact name and casing the link uses, (b) purge the fronting cache for the path |
| Apex (`tvsholdings.com`) does not redirect to `www` | Fronting service (Front Door / CDN) rule is missing or misconfigured — Blob Storage cannot do redirects on its own | Fix the rule in the fronting profile; do **not** edit `web.config` (it is inert) |
| HTTPS redirect not applied | Same root cause — the redirect is the fronting service's job | Fix the rule in the fronting profile |
| Security headers (HSTS, X-Frame-Options) missing | Same root cause — Azure Blob Storage does not emit them | Configure them in the fronting service rule engine |
| HTTPS shows a certificate error | Azure-managed cert not yet issued / domain not validated | Complete domain validation in Front Door / CDN |
| `web.config` was edited and the site behaviour did not change | **Blob Storage does not process `web.config`** — it is served as plain text | Configure the corresponding rule in the fronting service instead |
| `web.config` is reachable as plain text from the public site | It is just another blob in `$web` | Either delete it, or block the path via a fronting rule, or move it out of the deploy set |
| Change deployed but production still shows the old content | Fronting CDN cache still serving the previous response | Purge the cache for the affected paths |
| GA4 not receiving hits | Wrong measurement ID, ad-blocker, or `gtag.js` not loaded | Confirm `G-DPMX50C7QL` is in the page; check the Network panel for `googletagmanager.com/gtag/js` |
| Some pages still load `UA-120525446-1` | Legacy analytics ID never removed | `grep -rIn "UA-120525446-1" --include="*.htm"` and clean up |
| Site renders but Flash banners / animations are missing | Modern browsers do not run Flash; `.swf` / `.fla` files do not render | Replace with HTML5 / images or remove the `<object>` / `<embed>` references |
| Right-click shows an "alert" popup | The legacy right-click "disable" inline script | Cosmetic; safe to remove from the page (provides no real protection) |
| `OPTIONS` / `TRACE` requests return strange responses | Behaviour depends on the fronting service; Blob Storage allows them by default | Configure a deny rule in the fronting service if the previous IIS deny-list behaviour is required |
| Search Console verification stops working | Verification blob at root was not deployed, or fronting service is gating it | Ensure `google451a3e51028a5485.html` is uploaded to `$web` and that no fronting rule blocks anonymous public GETs |
| The page I am editing has duplicated header/footer that does not match the rest of the site | There is no shared template — chrome is hand-copied across ~150 pages | Use a representative current page as the source of truth |

When in doubt, prefer **adding new files** (year folder + new `<li>`) over modifying existing ones, and never change the storage-account index/error-document settings or the fronting service rule engine without engineering owner review.

---

## 10. Maintainers & Contact

> Update the placeholders below during onboarding handover.

| Role | Name | Contact |
|---|---|---|
| Engineering owner | _<add name>_ | _<add email>_ |
| Compliance / Secretarial owner | _<add name>_ | `corpsec@tvsholdings.com` |
| Hosting / Infrastructure (Azure) | _<add team>_ | _<add channel>_ |
| Registrar (RTA) | Integrated Registry Management Services | `einward@integratedindia.in` |
| Investor grievance (public) | Company Secretariat | `corpsec@tvsholdings.com` |
| TLS / domain | _<add team>_ (Azure-managed cert) | _<add channel>_ |
| Analytics | _<add owner>_ | GA4 measurement ID `G-DPMX50C7QL` |

For incidents during business hours, route to the engineering owner. After hours, route to the hosting team's on-call.

---

## License & Confidentiality

© TVS Holdings Limited. All rights reserved.

This repository contains public-facing content. Do **not** commit:
- Deployment credentials, Azure connection strings, SAS tokens, or service-principal secrets.
- Storage account names, resource-group names, subscription IDs, or other Azure resource identifiers.
- Internal hostnames, IPs, or VPN endpoints.
- Investor PII (the site does not collect any; it must not start to via this repo).
- Vendor contract terms.

When in doubt, ask the engineering owner before merging.

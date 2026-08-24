# Low Level Design — TVS Holdings Limited Website

> Implementation reference for new engineering vendors taking over the public corporate / investor-relations website at `https://www.tvsholdings.com`.
> Template reference: *D2C — Low Level Design Template* (Confluence page 4209606912).
> Companion documents: `docs/HLD.md` (architecture), `docs/hlddoc.md` (code walkthrough).

| | |
|---|---|
| Repository | <https://github.com/D2C-Website/TVS-Holdings> |
| Production URL | <https://www.tvsholdings.com> |
| Hosting | Azure Blob Storage (static website) + fronting Azure Front Door / Azure CDN |

---

## 1. Overview

This repository implements a **static HTML website** hosted on **Azure Blob Storage** (the *static website* feature on the `$web` container) and fronted by **Azure Front Door** or **Azure CDN**. Its job is to publish curated investor-relations content (annual reports, quarterly results, AGM notices, RBI / NCD disclosures, corporate-governance policies) and present the corporate identity of TVS Holdings Limited (formerly Sundaram-Clayton Limited).

The "implementation" is therefore a combination of:
- ~150 hand-curated `.htm` pages (each a self-contained view, no shared template engine).
- A folder hierarchy of PDF artefacts under `Investor/`, `Reports/`, `Announcements/`, `Web files/`, `NCDDisclosures/`, `StockExchangeIntimation*/`, etc.
- Three CSS files (`layout.css`, `generalTVSH.css`, `stylesheet.css`).
- Vendored JavaScript (jQuery 3.5.1, DynamicDrive `ddaccordion.js`, `thumbnailviewer2.js`, `pngfix.js`).
- A legacy `web.config` retained from the previous IIS deployment. **Azure Blob Storage does not interpret `web.config`** — its rewrite rules, response headers, default document, and request filtering are inert. The redirect / header / canonicalisation behaviour the file *describes* is now expressed on the **fronting service rule engine** (Azure Front Door / Azure CDN).

There is **no application code, no database, no ORM, no API**, and **no authentication**. Anything that looks dynamic on the site is the result of an editor manually placing a PDF in `$web` and editing the parent `.htm`.

---

## 2. High Level Design — Quick Recap

Reference: [`docs/HLD.md`](./HLD.md) in this repository.

Key properties relevant for the LLD:

| Property | Value |
|---|---|
| Tier | 2 (Business critical, not life-or-death) |
| Origin | Azure Blob Storage — static website (`$web` container) |
| Edge | Azure Front Door / Azure CDN (custom domain, HTTPS, redirects, headers, cache, WAF) |
| Default document | `Profile.htm` (set on the storage account, not in `web.config`) |
| Canonical host | `https://www.tvsholdings.com` |
| Auth | None (read-only public site) |
| Database | None |
| First-party APIs | None |
| Third-party scripts | Google Analytics (GA4 `G-DPMX50C7QL`; legacy UA `UA-120525446-1` on older pages) |

---

## 3. Assumptions

System-level and editorial assumptions baked into this design.

- **Origin is Azure Blob Storage with the *static website* feature enabled** on the `$web` container. The container is anonymous public-read for GETs.
- **Edge is Azure Front Door or Azure CDN.** Custom domain, HTTPS termination, apex→www redirect, HTTP→HTTPS redirect, security response headers, cache policy, and (recommended) WAF all live on the fronting service rule engine — **not** in `web.config`.
- **`web.config` is inert.** It is retained in the repo as a historical reference; Azure Blob Storage does not interpret it. Recommended to exclude it from the deploy set.
- **TLS is terminated at the fronting service.** The site assumes HTTPS is the only inbound protocol on port 443; HTTP requests are 301-redirected by the fronting service.
- **Editors deploy via the existing CI/CD pipeline** (typically `az storage blob upload-batch` or `azcopy sync`, followed by an `az afd endpoint purge`). Specific tooling, subscription IDs, storage account names, and credentials are infra-tier and intentionally not specified here.
- **Source control is the system of record** at <https://github.com/D2C-Website/TVS-Holdings>. No content is generated at runtime.
- **The browser is a "modern" browser.** IE-only assets (Flash, `pngfix.js`) are vestigial and may be removed at the next refactor without behavioural impact.
- **Legacy SCL outbound URLs (`sclapd.com`, `sclftp.com`)** point to systems on other domains that are not part of this repository or this design.
- **Year folders** under `Investor/TVSH/<YYYY>/` use the calendar year, not the financial year.

---

## 4. Components — Detailed Module Breakdown

The site has logical modules even though the directory layout is flat. Each module is the union of (a) one or more index `.htm` pages, (b) the PDF folder it indexes, and (c) any shared chrome.

### 4.1 Module map

| # | Module | Index pages (root) | PDF storage path(s) | Edited by |
|---|---|---|---|---|
| M1 | Public landing & About | `Profile.htm`, `Home.htm`, `Milestones.htm`, `FactSheet.htm`, `Global.htm`, `TVSGroup.htm`, `BoardofDirectors.htm`, `Society.htm`, `Vision.htm` | `images/` | Compliance + Engineering |
| M2 | Investors — Reports | `Reports.htm` | `Investor/TVSH/<YYYY>/Reports/`, `Reports/`, `Web files/` | Compliance |
| M3 | Investors — Information | `Information.htm` | `Investor/TVSH/<YYYY>/Informations/`, `Investor/Notice/<YYYY>/` | Compliance |
| M4 | Investors — Announcements | `Announcement.htm`, `Announcement1.htm`, `Announcement_1.htm` | `Investor/TVSH/<YYYY>/Announcements/`, `Announcements/<YYYY>/`, `Announcements/NewspaperPublication/<YYYY>/`, `TranscriptAGM/`, `Advertisement/` | Compliance |
| M5 | Investors — Disclosures | `Disclosures.htm`, `RBIDisclosures.htm` | `Investor/TVSH/<YYYY>/Disclosures/`, `Investor/TVSH/<YYYY>/RBIDisclosures/`, `NCDDisclosures/<YYYY>/` | Compliance |
| M6 | Investors — Stock Exchange | `StockExchange.htm` | `StockExchangeIntimation-2022/`, `StockExchangeIntimation2023/`, `Stock Exchange Intimation - 2021/`, `StockExchange2021/`, `Investor/TVSH/<YYYY>/StockExchange/` | Compliance |
| M7 | Investors — Corporate Governance | `Corporate.htm`, `SecretarialCompliance.htm`, `SecreterialComplaince.htm` | `Investor/TVSH/<YYYY>/Corporate/`, `Annualsecreterialcomplaince/` | Compliance |
| M8 | Investors — Postal Ballot | `PostalBallot.htm`, `PostalBallotResults.htm` | `Investor/PostalBallot/`, `Investor/<YYYY>PostalBallot/` | Compliance |
| M9 | Investors — Contact info | `Contact.htm`, `ContactInformation.htm` | n/a | Engineering (rare) |
| M10 | Legacy SCL pages | `aboutscl.htm`, `oldsclhome.htm`, `index.htm`, `sclhome.htm`, `Plants.htm`, `Diecasting.htm`, `Machining.htm`, `Quality.htm`, `Environment.htm`, `Customers.htm`, `Careers.htm`, `Design.htm`, `Tools.htm`, `Inspection.htm` | `images/`, `Web files/` | Frozen (archive) |
| M11 | Localised mirrors | `SCL-Japan/Profile.htm`, `SCL-German/Profile.htm`, `SCL-Korean/Profile.htm` | `SCL-<lang>/Web files/`, `SCL-<lang>/Information_files/` | Compliance (per-language) |
| M12 | Legal / footer | `Disclaimer.htm`, `terms.htm`, `terms20803.htm`, `Sitemap.htm`, `AccessRestricted.html` | n/a | Engineering |
| M13 | Configuration & SEO | `google451a3e51028a5485.html`, `robots_dummy.txt` (and the inert legacy `web.config`) | n/a | Engineering only |
| M14 | Vendored assets | `jquery-3.5.1.min.js`, `jquery-3.5.1.js`, `ddaccordion.js`, `thumbnailviewer2.js`, `pngfix.js`, three CSS files | n/a | Engineering only |

### 4.2 Page anatomy (the de-facto "template")

Every active `.htm` page in M1–M9 follows this shape. The header/footer is **duplicated by hand** because there is no template engine.

```
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" ...>
<html>
  <head>
    <title>...</title>
    <base href="https://www.tvsholdings.com" />          (1) optional, present on most pages
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"/>
    <meta http-equiv="imagetoolbar" content="no"/>
    <meta name="keywords"|"Title"|"Description" ... />
    <link href="layout.css" rel="stylesheet" type="text/css" />
    <link href="generalTVSH.css" rel="stylesheet" type="text/css" />
    <!--[if lt IE 7]>
      <script defer type="text/javascript" src="pngfix.js"></script>
    <![endif]-->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){ dataLayer.push(arguments); }
      gtag('js', new Date());
      gtag('config', 'G-DPMX50C7QL');
    </script>
  </head>
  <body>
    <div class="logo"> ... brand bar ... </div>
    <div class="menu">                                   (2) top nav
      <ul class="solidblockmenu">
        <li><a href="Profile.htm">Home</a></li>
        <li><a href="Profile.htm" class="current">About us</a></li>
        <li><a href="Reports.htm">Investors</a></li>
        <li><a href="Contact.htm">Contact us</a></li>
      </ul>
    </div>
    <div class="content">                                (3) two-column layout
      <table>
        <tr>
          <td width="178">                               (3a) left submenu
            <table class="...">
              <tr><td><a href="Reports.htm">Reports</a></td></tr>
              <tr><td><a href="Disclosures.htm">Disclosures</a></td></tr>
              ... ~10 rows ...
            </table>
          </td>
          <td>                                           (3b) main column
            <h1>Reports</h1>
            <ul>
              <li><a href="Investor/TVSH/2025/Reports/...">Quarter Ended 30th Sep 2025</a></li>
              ...
            </ul>
          </td>
        </tr>
      </table>
    </div>
    <hr/>
    <div class="footer">© Copyright TVS Holdings Limited 2023. ...</div>
    <script>
      // right-click "disable" boilerplate
      var message = "Sorry !! right click disabled on images";
      ...
      document.oncontextmenu = new Function("alert(message);return false");
    </script>
  </body>
</html>
```

The numbered annotations are the only places content meaningfully changes between pages.

---

## 5. API Design

**No first-party APIs exist.** This section documents the **only request / response contracts** the system actually serves: blobs returned by Azure Blob Storage with redirects, security headers, and caching applied by the fronting Azure Front Door / Azure CDN rule engine.

### 5.1 "Endpoints" (URL → fronting service / origin behaviour)

| URL pattern | Method | Behaviour | Status code | Body | Notes |
|---|---|---|---|---|---|
| `http://tvsholdings.com/<anything>` | GET | Front Door / CDN rule **"apex-to-www"** matches `Host=tvsholdings.com` | `301 Moved Permanently` | empty | `Location: https://www.tvsholdings.com/<anything>` |
| `http://www.tvsholdings.com/<anything>` | GET | Front Door / CDN rule **"http-to-https"** matches `scheme=http` | `301 Moved Permanently` | empty | `Location: https://www.tvsholdings.com/<anything>` |
| `https://www.tvsholdings.com/` | GET | Storage account *index document* setting resolves `/` → `Profile.htm` | `200 OK` | HTML | `Content-Type: text/html` |
| `https://www.tvsholdings.com/<page>.htm` | GET | Cache lookup at edge → blob fetch from `$web` on miss | `200` if blob exists, `404` otherwise | HTML | |
| `https://www.tvsholdings.com/<path>/<file>.pdf` | GET | Cache lookup at edge → blob fetch from `$web` on miss | `200` / `404` | PDF | `Content-Type: application/pdf` |
| `https://www.tvsholdings.com/images/<file>` | GET | Cache lookup at edge → blob fetch from `$web` on miss | `200` / `404` | image bytes | |
| `https://www.tvsholdings.com/google451a3e51028a5485.html` | GET | Blob fetch from `$web` | `200` | HTML | Google Search Console verification |
| `OPTIONS` / `TRACE` requests | * | Behaviour depends on the fronting service rule engine; Blob Storage allows them by default. The previous IIS deny-list (`405`) must be reproduced as an explicit rule on the fronting profile if required. | `405` (if rule configured) or origin default | empty | |
| URL longer than the fronting service's configured limit | any | Rejected by the fronting service | `4xx` | empty | Limits are platform-defined; tighten in the rule engine if a stricter cap is needed |
| Request body | any | Origin is read-only and ignores bodies; the fronting service may have its own size cap | `4xx` if the fronting cap is hit | | The legacy `web.config` `requestLimits` block is **not** active |

### 5.2 Standard response headers

These headers are **set on every response by the fronting Azure Front Door / Azure CDN rule engine** (the values shown were the previous IIS defaults from the now-inert `web.config`; vendors must verify the equivalent rules on the fronting profile):

```
Strict-Transport-Security: max-age=86400      (recommended: 31536000; includeSubDomains; preload)
X-Content-Type-Options:    nosniff
X-Frame-Options:           SAMEORIGIN
X-XSS-Protection:          1; mode=block
Cache-Control:             per-content-type   (HTML short, PDF/image long; configured at edge)
Access-Control-Allow-Origin: https://www.tvsholdings.com
```

Headers that should **not** appear in responses (Front Door / CDN does not emit them by default; if the storage account is queried directly, it will set its own `Server` header):

```
Server
X-Powered-By
X-AspNet-Version
X-AspNetMvc-Version
X-Robots-Tag
```

### 5.3 Idempotency

- All routes are idempotent `GET`s. There is no state mutation. There are no cookies, sessions, tokens, CSRF surfaces, or write APIs.

### 5.4 Status codes the site can return

| Code | When |
|---|---|
| `200 OK` | Blob served (cache hit at edge or origin fetch) |
| `301 Moved Permanently` | Apex→www, HTTP→HTTPS (both enforced by the fronting service) |
| `304 Not Modified` | Conditional GET (If-Modified-Since / If-None-Match) |
| `404 Not Found` | Missing blob (most common operational error — usually linkrot) — body is the storage account's *error document* (typically `AccessRestricted.html`) |
| `405 Method Not Allowed` | If the fronting service is configured to deny `OPTIONS` / `TRACE` |
| `5xx` | Fronting service or storage origin failure (no app code can produce these) |

### 5.5 Third-party endpoints called by the browser

These are not first-party APIs but are part of the request/response lifecycle:

| Endpoint | Initiator | Auth | Failure mode |
|---|---|---|---|
| `https://www.googletagmanager.com/gtag/js?id=G-DPMX50C7QL` | `<script async>` in page head | None (public) | If blocked, page renders fine; only analytics is lost |
| `https://www.google-analytics.com/g/collect` | gtag at runtime | None (public) | Same as above |

---

## 6. Data Model / Schema Changes

There is **no database**. The "data model" is entirely the file system layout. Below is the canonical schema vendors must respect when adding content.

### 6.1 PDF storage convention (post-rebrand)

```
Investor/TVSH/<YYYY>/<Section>/<Filename>.pdf
```

Where `<Section>` is one of:

| Section | Meaning | Linked from |
|---|---|---|
| `Announcements` | AGM notices, voting results, newspaper ads, postal-ballot intimations | `Announcement.htm` |
| `Corporate` | Corporate-governance reports, committee compositions | `Corporate.htm` |
| `Disclosures` | SEBI / SE intimations, related-party disclosures | `Disclosures.htm` |
| `Informations` | Board-meeting notices, debenture-trustee details, IDs terms | `Information.htm` |
| `RBIDisclosures` | RBI / CIC / NBFC disclosures | `RBIDisclosures.htm` |
| `Reports` | Annual returns, quarterly financial results, RPT statements | `Reports.htm` |
| `StockExchange` | NSE / BSE intimations | `StockExchange.htm` |

### 6.2 Filename conventions

| Artefact | Pattern (newer) | Examples |
|---|---|---|
| Quarterly result | `Quarter_Ended_<NNth>_<Mon>_<YYYY>.pdf` or `Quarter ended <DD MonthYYYY>.pdf` | `Quarter_Ended_30th_Sep_2025.pdf`, `Quarter ended 31st March 2026.pdf` |
| Annual return | `AnnualReturn<YYYY>.pdf` or `DraftAnnualReturn_<YYYY-YY>.pdf` | `AnnualReturn2024.pdf`, `DraftAnnualReturn_2024-25.pdf` |
| Annual report | `AnnualReport<YYYY>.pdf` | `AnnualReport2025.pdf` |
| Notice of board meeting | `Notice_of_BoardMeeting_<Mon>_<YY>.pdf` | `Notice_of_BoardMeeting_July_25.pdf` |
| Voting results | `AGM_VotingResults_<YYYY>.pdf` | `AGM_VotingResults_2025.pdf` |
| AGM notice | `<NNth>AGMNoticein<Lang>.pdf` | `62ndAGMNoticeinEnglish.pdf`, `62ndAGMNoticeinTamil.pdf` |
| Newspaper advertisement | `EnglishVCfacility.pdf`, `TamilVCfacility.pdf`, `Email_ID_updation_for_AGM_<Lang>.pdf` | |
| RPT (related-party transactions) | `HalfYear_ended_<DD_MM_YYYY>.pdf` | `HalfYear_ended_30_09_2024.pdf` |

### 6.3 Index-page schema (the "data" inside `.htm`)

Every entry in an investor index has the same five fields encoded inline as HTML:

| Field | HTML location | Required | Notes |
|---|---|---|---|
| Bullet image | `<img src="images/newbullet.jpg" .../>` | yes | Visual marker; pick the size used elsewhere in that section (18×18, 14×14, 10×10, 6×6) |
| Title | text inside `<a>` | yes | User-visible label |
| URL | `<a href="...">` | yes | Use forward slashes; URL-encode spaces |
| Target | `target="_blank"` | optional | Always set for PDFs and external links |
| Inline style | `style="color:#081156"` or `#083D6F` | yes | Brand colour inline because there is no per-link CSS class |

### 6.4 Data flexibility

- Adding a new year folder is non-breaking — it does not require any code change beyond the parent `.htm` edit.
- Renaming a folder **breaks every page that links to PDFs inside it**. Vendors must run a link-checker before merging such a change.
- The historic `Investor/`, `Reports/`, `Web files/`, `Bin/`, `Announcements/<YYYY>/` paths are still referenced from older list items and must not be moved.

### 6.5 ER-style diagram (file-system relations)

```
                     +-------------------+
                     |   Index page      |   (e.g. Reports.htm)
                     +-------------------+
                              | 1 .. N
                              |
                              v
                     +-------------------+
                     |  Anchor entry     |   <li><a href="..."> in HTML
                     |  (title + href)   |
                     +-------------------+
                              | 1 .. 1
                              |
                              v
                     +-------------------+
                     |  PDF artefact     |
                     |  (file on disk)   |
                     +-------------------+
                              | N .. 1
                              |
                              v
                     +-------------------+
                     |  Year folder      |   Investor/TVSH/<YYYY>/<Section>/
                     +-------------------+
```

---

## 7. Class & Interface Design

The codebase has **no classes** (no `class` keyword in any first-party file). What it does have are:
- A set of vendored JS objects with public methods.
- A set of inline JS handlers repeated in every page.
- A set of CSS classes that act as the contract between HTML and styles.

This section documents those interfaces.

### 7.1 Vendored JS — `ddaccordion` (DynamicDrive accordion)

Loaded only on `index.htm`.

```js
// Public surface
ddaccordion.init({
  headerclass:        "silverheader",   // CSS class that marks accordion headers
  contentclass:       "submenu",        // CSS class that marks the collapsible body
  revealtype:         "click" | "mouseover",
  collapseprev:       true | false,     // collapse the previously open panel?
  defaultexpanded:    [<int>, ...],     // indices of headers to open by default
  onemustopen:        true | false,
  animatedefault:     true | false,
  persiststate:       true | false,     // uses cookie for browser-session persistence
  toggleclass:        ["<closed>", "<open>"],
  togglehtml:         ["<position>", "<closed-html>", "<open-html>"],
  animatespeed:       "fast" | "normal" | "slow",
  oninit(headers, expandedIndices)      { ... },
  onopenclose(header, index, state, isUserActivated) { ... },
});

ddaccordion.expandone(headerclass, index);
ddaccordion.collapseone(headerclass, index);
ddaccordion.expandall(headerclass);
ddaccordion.collapseall(headerclass);
```

Implementation detail: the script binds a custom `evt_accordion` jQuery event on each header, so `expandall` / `collapseall` work by triggering that event on every visible / hidden content panel.

### 7.2 Vendored JS — `pngfix.js` (legacy IE PNG transparency)

Loaded only via:

```html
<!--[if lt IE 7]>
  <script defer type="text/javascript" src="pngfix.js"></script>
<![endif]-->
```

Algorithm (paraphrased from the script):
1. Read `navigator.appVersion`; if MSIE ≥ 5.5 and `document.body.filters` is supported, continue. Otherwise no-op.
2. Iterate `document.images`. For any image whose URL ends in `.PNG` (case-insensitive), replace its `outerHTML` with a `<span>` whose CSS uses `DXImageTransform.Microsoft.AlphaImageLoader` to render the image.
3. The replacement preserves `id`, `class`, `title` (or `alt`), inline style, alignment, and an inherited cursor pointer when the image lives inside an anchor.

Vendors maintaining the site can safely **remove** this script and the conditional comment after confirming there are no IE6 clients (modern reality: there aren't).

### 7.3 Vendored JS — `thumbnailviewer2.js`

Used on a few pages (legacy SCL galleries) for hover-preview thumbnails. Its public surface is `<a class="...">` markup picked up at `DOMContentLoaded`. It is not used by current investor-relations pages.

### 7.4 jQuery 3.5.1

The repository ships both `jquery-3.5.1.js` (debug) and `jquery-3.5.1.min.js` (production). Production pages reference the minified file. jQuery is a dependency of `ddaccordion` only; current investor-relations pages do not write jQuery code.

### 7.5 Inline scripts present in every active page

#### 7.5.1 Google Analytics initialisation

```js
window.dataLayer = window.dataLayer || [];
function gtag(){ dataLayer.push(arguments); }
gtag('js', new Date());
gtag('config', 'G-DPMX50C7QL');     // GA4 measurement ID
// older pages may instead call: gtag('config', 'UA-120525446-1');
```

Contract:
- `dataLayer` is a global push-only queue consumed by `https://www.googletagmanager.com/gtag/js`.
- `gtag` is the standard Google-recommended wrapper.
- Side effect: triggers a `page_view` beacon shortly after page load.

#### 7.5.2 Right-click "disable" boilerplate

```js
var message = "Sorry !! right click disabled on images";
function clickIE4(){ if (event.button == 2){ alert(message); return false; } }
function clickNS4(e){ if (document.layers || document.getElementById && !document.all){
  if (e.which == 2 || e.which == 3){ alert(message); return false; }
} }
if (document.layers){
  document.captureEvents(Event.MOUSEDOWN);
  document.onmousedown = clickNS4;
} else if (document.all && !document.getElementById){
  document.onmousedown = clickIE4;
}
document.oncontextmenu = new Function("alert(message); return false");
```

Contract: hijacks the `contextmenu` event and shows an `alert`. Provides **no** real protection (anyone can still save the page or its assets via dev tools). Vendors are recommended to remove it; documented here because it is duplicated across pages and may be unfamiliar to new editors.

#### 7.5.3 Language selector (only on `Home.htm`)

```html
<input type="button" value="English"  onclick="location.href='Profile.htm'" />
<input type="button" value="日本語"    onclick="location.href='SCL-Japan/Profile.htm'" />
<input type="button" value="Deutsch"  onclick="location.href='SCL-German/Profile.htm'" />
<input type="button" value="한국의"   onclick="location.href='SCL-Korean/Profile.htm'" />
```

### 7.6 CSS module map

| Class | Defined in | Owner of | Used in |
|---|---|---|---|
| `.logo` | `layout.css` | Top brand bar | All M1–M9 pages |
| `.menu`, `.solidblockmenu`, `.solidblockmenu li`, `.solidblockmenu .current` | `layout.css` | Top navigation | All M1–M9 pages |
| `.content` | `layout.css` | Two-column main area | All M1–M9 pages |
| `.footer` | `layout.css` | Footer bar | All M1–M9 pages |
| `.applemenu`, `.silverheader`, `.submenu`, `.selected` | `layout.css` + `index.htm` `<style>` | Accordion menu chrome | `index.htm` only |
| `.arrowlistmenu`, `.headerbar` | `layout.css` | Older sidebar list | Legacy SCL pages |
| `.contenttext`, `.submenutext`, `.milestone` | `stylesheet.css` | Body text sizing/colour | Most M2–M9 pages |
| `.globe` | `generalTVSH.css` | Splash globe positioning | `Home.htm` |

### 7.7 Hosting configuration interface

Configuration that affects request handling lives in **two places**, neither of which is in this repository:

1. The **storage account** (origin) — index document, error document, optional CORS rules, soft-delete, versioning, replication.
2. The **fronting service** (Azure Front Door / Azure CDN) — custom domain, HTTPS, redirects, security headers, cache policy, optional WAF.

The legacy `web.config` in the repo describes what the previous IIS deployment did. It is **not** interpreted by Azure Blob Storage and serves only as a porting reference.

#### 7.7.1 Storage account static-website settings

| Setting | Value | Notes |
|---|---|---|
| Static-website feature | enabled | `az storage blob service-properties update --account-name <sa> --static-website --index-document Profile.htm --404-document AccessRestricted.html` |
| Index document | `Profile.htm` | A `GET /` request resolves to this blob |
| Error document (404) | `AccessRestricted.html` (recommended) | Returned for any blob 404 |
| Container | `$web` | Anonymous public read for GETs |

Engineering must not change the index / error document without coordinating with SEO and any external systems referencing the canonical URL.

#### 7.7.2 Fronting service rule engine (Azure Front Door / Azure CDN)

The redirects, security headers, and cache policy that the previous IIS deployment expressed in `web.config` are now (or must be) expressed as rules on the fronting profile. Examples below — actual rule names depend on the Azure resource model in use:

- **Redirect rule "apex-to-www"** — match `Host = tvsholdings.com` → 301 `https://www.tvsholdings.com{path}`.
- **Redirect rule "http-to-https"** — match `Protocol = HTTP` → 301 `https://{host}{path}`.
- **Response-header rule** — append `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Content-Security-Policy`.
- **Cache-policy rule** — `*.htm` → short TTL (e.g. 60 s); `*.pdf`, `*.jpg`, `*.png`, `*.css`, `*.js` → long TTL (e.g. 1 day).
- **WAF policy** (recommended) — managed OWASP rule set + bot protection.

Rule **ordering matters** the same way it did under IIS: the apex→www redirect must run before the HTTP→HTTPS redirect to avoid double-redirect chains.

#### 7.7.3 Legacy `web.config` (inert reference)

Below is the content of the historical `web.config`, retained only as documentation of what the previous IIS deployment enforced. **Azure Blob Storage does not interpret this file.**

```xml
<rule name="Redirect to www" enabled="true" stopProcessing="true">
  <match url=".*" />
  <conditions>
    <add input="{HTTP_HOST}" pattern="^tvsholdings.com$" />
  </conditions>
  <action type="Redirect" url="https://www.tvsholdings.com/{R:0}" redirectType="Permanent" />
</rule>

<rule name="http into https" patternSyntax="Wildcard" stopProcessing="true">
  <match url="*" ignoreCase="false" />
  <conditions logicalGrouping="MatchAny">
    <add input="{HTTPS}" pattern="off" />
  </conditions>
  <action type="Redirect" url="https://www.tvsholdings.com/{R:1}" redirectType="Permanent" />
</rule>
```

The `<httpProtocol><customHeaders>` block in the file describes the original header policy (HSTS, X-Frame-Options, etc.) and the `<requestFiltering>` block describes URL/body limits and the `OPTIONS`/`TRACE` deny-list. **None of these are active under Blob Storage** — they must be re-implemented on the fronting service if their behaviour is required.

Recommendation: delete `web.config` from the deploy set after the fronting rules have been verified, to remove the file from the public site root and avoid editor confusion.

Already enumerated in §5.1, §5.2.

---

## 8. UI Changes

This section is the contract for editorial changes — i.e., the recurring "UI change" the site supports.

### 8.1 Add a new quarterly result

1. Place the PDF at `Investor/TVSH/<YYYY>/Reports/Quarter_Ended_<NN>_<Mon>_<YYYY>.pdf` (follow §6.2 naming).
2. Open `Reports.htm`. Inside the "Quarterly Reports" `<ul>` block, **prepend** a new `<li>`:

   ```html
   <li class="contenttext">
     <a href="Investor/TVSH/2026/Reports/Quarter_Ended_30th_June_2026.pdf"
        target="_blank"
        style="color:#081156">Quarter Ended 30th June 2026</a>
   </li>
   ```

3. Verify the path resolves with the live server's case-sensitivity rules.
4. Deploy `Reports.htm` and the PDF together.

### 8.2 Add a new board-meeting notice

1. Drop the PDF at `Investor/TVSH/<YYYY>/Informations/Notice_of_BoardMeeting_<Month>_<YY>.pdf`.
2. In `Information.htm`, locate the year heading inside the "Notice of Board Meetings" block and add a new line under it:

   ```html
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
   <img alt="" src="images/newbullet.jpg" height="10" width="10">
   <a href="Investor/TVSH/2026/Informations/Notice_of_BoardMeeting_June_26.pdf"
      target="_blank" style="color:#081156">Notice of Board Meeting - June</a>
   <br/><br/>
   ```

3. The bullet image height/width pattern is already established (10×10 for sub-items, 18×18 for section headers). Match it.

### 8.3 Site-wide chrome change (e.g. update the footer year)

Because there is no template engine, this is a **find-and-replace across every `.htm`**.

Recommended workflow:
1. Identify the literal to change (e.g. `&copy; Copyright TVS Holdings Limited 2023`).
2. Run a repository-wide replace.
3. Do **not** edit pages inside `SCL-Japan/`, `SCL-German/`, `SCL-Korean/` unless their language stakeholders have approved.
4. Spot-check three representative pages (one Profile/About, one Investor index, one legacy) before committing.

### 8.4 Update analytics measurement ID

1. Search-replace `G-DPMX50C7QL` (and `UA-120525446-1` on legacy pages).
2. Confirm in browser dev tools that the network beacon to `googletagmanager.com` carries the new ID.
3. Verify in GA4 real-time view that hits arrive.

### 8.5 Localised mirror updates

The three localised microsites (`SCL-Japan/`, `SCL-German/`, `SCL-Korean/`) are hand-translated mirrors. They share the visual style but **not** the latest content. Engineering must not auto-sync English content into these folders; only translate and merge changes that the language stakeholder has approved.

---

## 9. Validation Logic

There is **no application-level validation** because the site has no input forms. Validation in this codebase is split across three layers:

### 9.1 Edge-level validation (fronting service rule engine + storage account)

| Rule | Source | Effect |
|---|---|---|
| Method allow-list (recommended: deny `OPTIONS`, `TRACE`) | Front Door / CDN rule engine | `405` on denied verbs. The legacy `web.config` deny-list is **not** active under Blob Storage. |
| URL / query-string limits | Front Door / CDN platform defaults; tighten via rule engine if needed | Reject overlong URLs |
| Body size cap | Front Door / CDN platform defaults | Origin is read-only and ignores bodies |
| File-extension allow-list | None — all blob extensions are served | The repo simply contains no executable types |
| WAF rules (recommended) | Front Door WAF policy | Managed OWASP rule set + bot protection |

### 9.2 Editorial validation (manual / pre-deploy)

This is the most important "validation" the site has. New vendors should adopt this checklist before every deploy:

| Check | How |
|---|---|
| The PDF actually exists at the path written into the `.htm` | Verify on a staging mirror |
| The PDF opens in a fresh browser session (no cached version) | Ctrl-Shift-N |
| The new `<li>` renders without breaking the surrounding markup | Visual diff |
| No new occurrence of `UA-120525446-1` was introduced | grep |
| No new `<base href="...">` tag was added on a page that doesn't already have one | grep |
| The deploy candidate does not include drafts under any committed `2025`, `2026`, … folders that were meant to stay private until publication day | code review |

### 9.3 Browser-level validation

- Modern browsers reject mixed-content (HTTP) sub-resources because of HSTS. Editors must keep all hyperlinks and asset URLs on `https://`.
- The default `Cache-Control` policy on the fronting service should be **per content type**: short TTL (e.g. 60 s) for HTML so disclosure updates surface quickly, longer TTL (e.g. 1 day) for PDFs / images. Cache invalidation on deploy is handled by the CI/CD job (`az afd endpoint purge`).

---

## 10. Error Handling & Retries

There is no application code that can throw, so error handling is entirely at the protocol and infrastructure layers.

### 10.1 Error categories

| Layer | Error | Surfaced as | Vendor action |
|---|---|---|---|
| Storage origin | `404 Not Found` (missing blob) | Storage account *error document* (typically `AccessRestricted.html`) | Upload the missing blob or fix the link in the parent `.htm`; purge the fronting cache for the path |
| Fronting service | Edge cache hit on a stale 404 | Same body the origin returned at the time of the cache miss | Purge the fronting cache for the affected paths after fixing the origin |
| Fronting service | `405` on `OPTIONS` / `TRACE` | Front Door / CDN default | Expected by design if the deny rule is configured |
| Fronting service | `5xx` (origin unreachable, edge fault) | Front Door / CDN error page | Operations to investigate the storage account and the fronting profile |
| TLS | Handshake failure | Browser shows browser-native error | If using Azure-managed certs: complete domain validation in the fronting profile |
| Browser | GA4 / gtag.js blocked or fails | Page renders fine, no analytics | Acceptable; no user-visible error |
| Browser | Right-click handler `alert()` | UX friction | Recommended to remove |
| Editorial | Wrong PDF deployed | Visible-but-wrong content | Roll back: re-run the deploy job from the previous commit, or `az storage blob upload` the correct file and purge cache |
| Editorial | Linkrot after blob rename | `404` on PDF clicks | Restore the blob name **or** update every reference, then purge cache |

### 10.2 Retry semantics

- Browsers retry transparent network errors per their own policy. The site itself has no retry logic.
- There is no async work, no message queue, no scheduled job. There is nothing for the site to "retry."

### 10.3 Timeouts

- Front Door / CDN default origin timeouts apply (typically tens of seconds). Tighten or relax via the fronting profile if needed.
- The legacy `web.config` declared `<sessionState timeout="20" />` — this is **inert** under Blob Storage. The application has no sessions anyway.

### 10.4 Fallback mechanism

- If the canonical *index document* `Profile.htm` is missing, the storage account falls back to the configured *error document* (typically `AccessRestricted.html`).
- There is no other fallback. Any 404 surfaces the storage account's error document.

---

## 11. Security and Compliance

### 11.1 Encryption

| Data | Mode | Notes |
|---|---|---|
| In transit | TLS 1.2+ enforced via 301 redirect on the fronting service | Cert: Azure-managed |
| At rest (origin blobs) | Azure Storage Service Encryption (AES-256, Microsoft-managed keys) — on by default | Customer-managed keys can be enabled if required |
| At rest (build artefacts) | None — no compiled artefacts | |

### 11.2 Authentication / Authorization

Already covered in HLD: **none** for end users. Editor-side auth is the deploy-account credential and is infrastructure-tier.

### 11.3 PII / GDPR

- The site collects no PII directly — there are no forms.
- Google Analytics (GA4) collects standard analytics signals client-side. Treat GA4's privacy disclosures as the privacy boundary; document them in any cookie/privacy notice attached to the site.
- The investor-grievance email addresses (`einward@integratedindia.in`, `corpsec@tvsholdings.com`) are public on `Contact.htm` by design; they are not "PII leakage" but the official disclosed channels.

### 11.4 Token management

- Not applicable. No tokens are issued, stored, or validated anywhere in this codebase.

### 11.5 Header policy (defence in depth)

> All values below must be configured on the **fronting service rule engine** (Azure Front Door / Azure CDN). The legacy `web.config` is inert.

| Header | Value | Rationale |
|---|---|---|
| `Strict-Transport-Security` | recommended `max-age=31536000; includeSubDomains; preload` (legacy was `max-age=86400`) | Force HTTPS |
| `X-Frame-Options` | `SAMEORIGIN` | Defends against clickjacking |
| `X-Content-Type-Options` | `nosniff` | Defends against MIME-confusion |
| `X-XSS-Protection` | `1; mode=block` | Legacy browser XSS auditor |
| `Cache-Control` | per content type at the edge: `public, max-age=60` for HTML, `public, max-age=86400` for PDFs / images | Disclosures stay fresh; static assets stay cheap |
| `Access-Control-Allow-Origin` | `https://www.tvsholdings.com` | Tightens CORS; the site has no API, but this is a defensive default |
| `Content-Security-Policy` | recommended: `default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; img-src 'self' data:; style-src 'self' 'unsafe-inline'; connect-src 'self' https://www.google-analytics.com https://www.googletagmanager.com;` | Mitigates XSS and limits third-party reach |
| Suppress origin fingerprint | Front Door / CDN does not emit `X-AspNet-Version` / `X-Powered-By`; ensure the fronting service is not adding any custom `Server` header | Reduces fingerprinting |

---

## 12. RBAC (Role-Based Access Control)

There are no end-user roles in the application. The only operationally meaningful roles are:

| Role | Permission scope | System where enforced |
|---|---|---|
| Public visitor | Read all `https://www.tvsholdings.com/*` content | Storage account `$web` (anonymous public read; no auth check) |
| Editor (Compliance / Secretarial) | Add / replace blobs under `Investor/...`; edit any `.htm` *except* the storage-account static-website settings or fronting rules | Out-of-repo: CI/CD job permissions |
| Engineer | All editor permissions plus storage-account static-website settings, fronting rule engine, JS/CSS, redirect rules, security headers | Out-of-repo: Azure RBAC + code-review gate |
| Operations | Manage Azure resources, reissue TLS, manage DNS | Azure portal / Azure RBAC |
| Security | Headers / CSP review, SAS / SP rotation, WAF rules | Out-of-repo: Azure RBAC |

The CI/CD pipeline authenticates as a **service principal** (or workload identity) scoped to the storage account and the fronting profile (for cache purges). Credentials are held in the CI/CD secret store; they are never committed to this repository.

---

## 13. Configuration Rules & Feature Flags

### 13.1 Configuration surfaces

| Surface | Where it lives | Owns |
|---|---|---|
| URL canonicalisation (apex→www, HTTP→HTTPS) | Azure Front Door / Azure CDN rule engine | Redirects |
| Default document | Storage account → static-website settings → *Index document* | `Profile.htm` |
| Error document | Storage account → static-website settings → *Error document* | `AccessRestricted.html` (recommended) |
| Response headers (HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, CSP, CORS) | Azure Front Door / Azure CDN rule engine | Security headers |
| Cache policy (per content type) | Azure Front Door / Azure CDN rule engine | TTLs |
| WAF policy (recommended) | Azure Front Door WAF | OWASP / bot |
| TLS certificate | Azure-managed cert on the fronting service | HTTPS |
| Storage durability | Storage account replication setting (LRS / ZRS / GRS / RA-GRS) | Origin redundancy |
| Soft delete + versioning + change feed (recommended) | Storage account blob service properties | Recoverability |
| Diagnostic logs (recommended) | Storage account + fronting service → Log Analytics | Server-side observability |
| Analytics ID | Inline in every page `<head>` | `G-DPMX50C7QL` (and legacy `UA-120525446-1`) |
| Domain ownership | `google451a3e51028a5485.html` | Google Search Console |
| Robots | `robots_dummy.txt` | Currently not active; rename to `robots.txt` once policy is finalised |
| **Inert** | `web.config` (in repo only) | Was IIS rewrite + headers + default document; **not interpreted by Blob Storage** |

### 13.2 Configuration rules

- **The fronting service rule engine is critical-path.** Any change must be peer-reviewed and tested on a non-production fronting profile. Recover from a bad change by restoring the previous rule version (or re-applying IaC).
- **Storage-account static-website settings are critical-path.** The *index document* (`Profile.htm`) must not change without coordinating with SEO and external systems referencing the canonical URL.
- **Rewrite-rule order is significant.** Apex→www must precede HTTP→HTTPS to avoid double redirects.
- **Cache policy should be per content type** at the edge: HTML short (e.g. 60 s), PDFs / images longer (e.g. 1 day). Cache invalidation on deploy is mandatory; the CI/CD job should always run `az afd endpoint purge` after upload.
- **HSTS lifetime** — recommended `max-age=31536000; includeSubDomains; preload` once all sub-resources are confirmed HTTPS. The legacy `web.config` value of `max-age=86400` is not active.
- **`web.config` is inert.** Editing it has no effect in production. Vendors must change the corresponding rule on the fronting service or storage account instead.

### 13.3 Feature flags

The site has no runtime feature toggles. "Phased rollout" is achieved by:
- Placing draft PDFs in a year folder that no `.htm` references yet.
- Editing the parent `.htm` to expose them on cut-over day.
- Reverting the `.htm` change to "hide" again.

---

## 14. Dependencies

### 14.1 Internal (in this repository)

| Dependency | Used by | Guarantee |
|---|---|---|
| `layout.css`, `generalTVSH.css`, `stylesheet.css` | All M1–M9 pages | Must remain at root and keep their current class names |
| `images/` | All pages, all chrome | Stable image filenames are part of the contract |
| `jquery-3.5.1.min.js` | `index.htm` (and `ddaccordion`) | Pinned version |
| `ddaccordion.js` | `index.htm` accordion menu | Pinned vendored copy |
| `pngfix.js` | Conditional comment in many pages | Inert on modern browsers |
| `thumbnailviewer2.js` | Legacy galleries | Inert on current investor pages |

### 14.2 External (third-party)

| Dependency | Contract | Failure mode |
|---|---|---|
| Google Tag Manager (`googletagmanager.com/gtag/js`) | Public script load | Page renders fine if blocked |
| Google Analytics (`google-analytics.com/g/collect`) | Beacon endpoint | Same |
| Google Search Console verification | Static file at root | Site indexing affected if file removed |
| NSE / BSE | User-clickable outbound links only | Links may rot; not our SLO |
| Registrar (Integrated) | `mailto:` reference only | Out of band |
| Debenture trustees (Beacon, Catalyst) | Address/email reference only | Out of band |
| CRISIL | PDFs hosted on this site | Out of band |

### 14.3 Infrastructure

| Layer | Dependency | Guarantee required |
|---|---|---|
| Edge | **Azure Front Door** or **Azure CDN** | Custom domain, HTTPS, redirects, security headers, cache policy, WAF |
| Origin | **Azure Storage Account** with the *static website* feature enabled, container `$web` | Anonymous public read for blobs |
| TLS | Cert chain valid for `www.tvsholdings.com` and `tvsholdings.com` | Azure-managed cert |
| DNS | A / CNAME for both apex and `www` resolving to the fronting endpoint | Both must be registered on the fronting profile so that the apex→www redirect itself runs there |
| CI/CD | Pipeline (e.g. GitHub Actions / Azure DevOps) authenticated as a service principal scoped to the storage account and the fronting profile | `az storage blob upload-batch` / `azcopy sync` + `az afd endpoint purge` |
| Source control | GitHub — <https://github.com/D2C-Website/TVS-Holdings> | System of record |

---

## 15. Trade-offs & Alternatives Considered

| Decision | Trade-off taken | Alternative considered | Why current choice |
|---|---|---|---|
| Static HTML on Azure Blob Storage + Front Door / CDN | Editor-friendly markup duplication; no application risk; Azure-native ops | CMS (WordPress, Drupal) | CMS introduces auth, DB, and a much larger attack surface for a read-only site |
| Hand-edited templates | Duplicate chrome across 150 pages | Static-site generator (Hugo / Eleventy / Jekyll) | SSG would be a strict improvement; deferred until the next major content refresh |
| Per-content-type cache policy (recommended) at edge | Disclosures stay fresh (short TTL on HTML); PDFs / images cache for hours | All-`no-store` (legacy IIS approach) | Edge caching is the entire point of fronting with Front Door / CDN |
| HSTS recommended `max-age=31536000` | Long lockdown; takes ~1 year to roll back | `max-age=86400` (legacy) | Tighten after a soak period |
| CSP recommended on the fronting service | Inline scripts (`gtag`, right-click) make a strict CSP harder to author | No CSP | Enable as a follow-up; can start permissive and tighten |
| Right-click "disable" inline JS | Provides no real protection; adds an `alert` modal | Remove | Recommended to remove on next pass |
| Vendored jQuery 3.5.1 | Not on the latest 3.x; but it's only used by the legacy accordion | Upgrade or drop entirely | Drop when the accordion menu is retired or modernised |
| Mixed GA4 + UA pages | Fragmented telemetry; UA is deprecated | Unify on GA4 | Plan to remove all `UA-120525446-1` references |
| Flash assets retained | Unrendered on modern browsers; harmless but wasteful | Delete | Plan to delete |
| `web.config` retained in source | Inert under Blob Storage; possibly serves as plain text from `$web` | Delete from the deploy set | Recommended to remove from `$web` once the fronting rules are confirmed |

---

## 16. Open Questions

These should be resolved during onboarding with the company secretariat / engineering owner:

1. **Robots policy.** `robots_dummy.txt` is present but the site has no active `robots.txt`. Should investor PDFs be allowed in search engines? If yes, what about archived / superseded ones?
2. **Fronting service confirmation.** Is the fronting service Azure Front Door, Azure CDN, or both? Which redirect / header rules are currently configured?
3. **CSP rollout.** What is the appetite for enabling a CSP on the fronting service? Are there pages embedding third-party widgets that the draft would break?
4. **Localised mirrors.** Are `SCL-Japan/`, `SCL-German/`, `SCL-Korean/` actively maintained, or can they be archived behind a `legacy/` prefix?
5. **Flash retirement.** Confirmation to delete `*.swf`, `*.fla`, and the IE6 `pngfix.js` references on next refactor.
6. **Default-document fallback.** Is the current `AccessRestricted.html` content still appropriate as the storage account *error document*?
7. **HSTS lengthening.** Is there an objection to extending HSTS to one year with `includeSubDomains; preload` after a 30-day soak?
8. **Form-based interactions.** Will any future requirement (newsletter sign-up, investor query form) be added? If so, that breaks the "no first-party API / no DB" assumption and would need its own design document.
9. **Deployment tooling.** Confirm the active CI/CD pipeline (GitHub Actions / Azure DevOps / other) and which service principal it authenticates as. Vendors need this documented separately, with credentials managed by the security/infra team.
10. **Outbound link audit.** Older legacy pages still link to `sclapd.com` and (commented out) `sclftp.com`. Should those references be removed entirely from currently-served pages?
11. **`web.config` cleanup.** Should `web.config` be removed from the deploy set / `$web` container (recommended) or retained as a historical reference?
12. **Storage account hardening.** Confirm soft delete, blob versioning, and replication tier (LRS / ZRS / GRS / RA-GRS).

---

## 17. Appendix — Quick Reference

### 17.1 Where to add new content (cheatsheet)

| Content type | Drop file at | Then edit |
|---|---|---|
| Quarterly result | `Investor/TVSH/<YYYY>/Reports/Quarter_Ended_<...>.pdf` | `Reports.htm` |
| Annual return / report | `Investor/TVSH/<YYYY>/Reports/AnnualReturn<YYYY>.pdf` or `Investor/TVSH/<YYYY>/AnnualReport<YYYY>.pdf` | `Reports.htm` |
| Board-meeting notice | `Investor/TVSH/<YYYY>/Informations/Notice_of_BoardMeeting_<Mon>_<YY>.pdf` | `Information.htm` |
| AGM notice / voting | `Investor/TVSH/<YYYY>/Announcements/...` | `Announcement.htm` |
| Newspaper publication | `Announcements/NewspaperPublication/<YYYY>/...` | `Announcement.htm` |
| RBI / NCD disclosure | `Investor/TVSH/<YYYY>/RBIDisclosures/...` or `NCDDisclosures/<YYYY>/...` | `RBIDisclosures.htm` or `Disclosures.htm` |
| Stock-exchange intimation | `StockExchangeIntimation<YYYY>/...` or `Investor/TVSH/<YYYY>/StockExchange/...` | `StockExchange.htm` |
| Postal-ballot pack | `Investor/PostalBallot/...` | `PostalBallot.htm` / `PostalBallotResults.htm` |
| Corporate-governance report | `Investor/TVSH/<YYYY>/Corporate/...` | `Corporate.htm` |

### 17.2 Files that **must not** move

```
Profile.htm                                 (default document)
AccessRestricted.html                       (default-document fallback)
web.config                                  (rewrite + headers)
google451a3e51028a5485.html                 (Search Console verification)
```

### 17.3 Glossary

See §19.1 of `docs/HLD.md`.

### 17.4 Out-of-scope

Deployment credentials, internal hostnames, IPs, registrar API keys, vendor contract terms — all intentionally omitted. Request through the company-secretariat handover process.

---

*This LLD is meant to give a new vendor enough operational detail to maintain and extend the site without surprises. When in doubt, prefer adding new files (year folder + new `<li>`) over changing existing ones, and never change `web.config` or the default-document mapping without engineering owner review.*

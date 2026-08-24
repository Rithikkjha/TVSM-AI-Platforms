# TVS Apache RR310 — Built to Order (BTO) 3D Configurator

A browser-based 3D motorcycle configurator that lets customers personalize the TVS Apache RR310 — selecting kits, colors, alloy wheels, and race numbers — then place an order directly from the TVS Motor website.

## Application Overview

- **What:** Interactive 3D configurator with real-time material swapping, pricing, AR viewing, and order placement
- **Tech:** A-Frame 1.4.0 (WebGL/Three.js), vanilla JavaScript, static HTML/CSS
- **Hosting:** Embedded as `<iframe>` on `tvsmotor.com/tvs-apache/rr-310/built-to-order/book-online`
- **Build:** No bundler — static file deployment (no npm, webpack, or build step)

---

## Setup Instructions

### Prerequisites

- A modern web browser with WebGL 2.0 support (Chrome 90+, Firefox 88+, Safari 15+, Edge 90+)
- A local HTTP server (the app uses `fetch()` and requires HTTPS/HTTP origins)
- Git

### Clone

```bash
git clone <repository-url>
cd rr310-configurator-experience-v1
```

### Install a Local Server

Pick any static file server:

```bash
# Option 1: Python
python3 -m http.server 8080

# Option 2: Node.js (npx, no install needed)
npx serve .

# Option 3: VS Code Live Server extension
# Right-click index_preprod.html → "Open with Live Server"
```

---

## Local Development

1. **Open the pre-production entry point:**
   ```
   http://localhost:8080/index_preprod.html
   ```

2. **Disable devtools protection (for debugging):**
   Comment out or remove the devtools detection `<script>` block at the top of `index_preprod.html` (lines 12–83).

3. **Enable console logging:**
   In `avataarrenderer_preprod.js`, the IIFE at line 1 suppresses console on non-localhost. Develop on `localhost` to keep logs active.

4. **Key files to edit:**

   | File | Purpose |
   |------|---------|
   | `configmaster_tvs_preprod_new.js` | Product config, pricing, icons, variants |
   | `avataarrenderer_preprod.js` | 3D engine, interactions, API integration |
   | `index_preprod.css` | Styling and responsive layout |
   | `index_preprod.html` | DOM structure, script loading |

5. **Version bump:** After changes, increment the `?v=` query param on script tags in the HTML to bust browser cache.

---

## Environment Variables

This is a static client-side app — there are no `.env` files or server-side environment variables. Configuration is managed via:

| Config Point | Location | Description |
|--------------|----------|-------------|
| API Endpoints | `configmaster_tvs_preprod_new.js` → `AllAPIs`, `redirectCheckOut`, `_chunksApi` | Backend URLs |
| Analytics ID | `index.html` inline `<script>` | Google Analytics `G-9QYYD82JSC` |
| GTM Container | `index.html` inline `<script>` | Google Tag Manager `GTM-KD53L7` |
| Debug Flag | `index.html` → `const debugFlag = true` | Controls analytics init |
| A-Frame CDN | `<script src="...">` in HTML `<head>` | Framework source URL |
| Asset Paths | `configmaster_tvs_preprod_new.js` → `glbs`, `cubemapForImageBasedLighting` | 3D models, textures |

### Environment Switching

| Environment | Entry Point | API Base |
|-------------|-------------|----------|
| Production | `index.html` | `https://www.tvsmotor.com` |
| UAT | `index_preprod.html` | `https://uat-www.tvsmotor.net` |
| Local | `index_preprod.html` | `localhost` (API calls will fail without proxy) |

---

## Build Instructions

There is **no build step**. The application deploys as static files.

### Minification (Manual)

When preparing for production:

1. Minify `configmaster_tvs_preprod_new.js` → `configmaster_tvs_preprod.min.js`
2. Minify `avataarrenderer_preprod.js` → `avataarrenderer_preprod.min.js`
3. Update `index.html` to reference `.min.js` files
4. Increment `?v=` query parameter on script tags

Recommended tools: [terser](https://terser.org/), [uglify-js](https://github.com/mishoo/UglifyJS), or any online JS minifier.

```bash
# Example with terser
npx terser configmaster_tvs_preprod_new.js -o configmaster_tvs_preprod.min.js -c -m
npx terser avataarrenderer_preprod.js -o avataarrenderer_preprod.min.js -c -m
```

---

## Deployment

This project is deployed to **Azure Blob Storage** (static website hosting). Deployment to both UAT and Production is done **manually** by uploading files directly to the respective blob containers.

### Blob Storage Environments

| Environment | Blob Container | Served Via |
|-------------|---------------|------------|
| UAT / Pre-prod | UAT storage account | `https://uat-www.tvsmotor.net` / `https://dev-bto.tvsmotor.net` |
| Production | Production storage account | `https://bto.tvsmotor.com` |

### Deployment Steps

1. **Prepare files:**
   - Minify JS (see [Build Instructions](#build-instructions))
   - Bump `?v=` query string on script tags in HTML
   - Verify `index.html` points to `.min.js` files and correct API URLs

2. **Upload to Azure Blob Storage:**
   - Open **Azure Portal** → Storage Account → Containers → `$web` (or relevant container)
   - Upload all changed files (use drag-and-drop, Azure Storage Explorer, or `az storage blob upload-batch`)
   - Maintain the same folder structure as the repository

   ```bash
   # Example using Azure CLI
   az storage blob upload-batch \
     --account-name <storage-account> \
     --destination '$web' \
     --source . \
     --overwrite
   ```

3. **Purge CDN cache (if Azure CDN is in front):**
   ```bash
   az cdn endpoint purge \
     --resource-group <rg-name> \
     --profile-name <cdn-profile> \
     --name <endpoint-name> \
     --content-paths "/*"
   ```

4. **Verify deployment:**
   - Open UAT/prod URL in browser
   - Confirm 3D model loads, icons render, pricing displays correctly
   - Test on mobile for AR functionality

### Deployment Checklist

- [ ] `debugFlag` set to `false` in production `index.html`
- [ ] Script tags point to `.min.js` files
- [ ] Query string version bumped (`?v=10`)
- [ ] Console suppression IIFE active (production domain check)
- [ ] DevTools detection script included
- [ ] API endpoints point to production URLs (not UAT)
- [ ] GLB model chunks accessible via production Azure Blob API
- [ ] All files uploaded to correct blob container
- [ ] CORS configured on blob storage to allow `tvsmotor.com` origin
- [ ] Test on Chrome, Safari, Firefox, and mobile (Android/iOS)

### Rollback

Re-upload the previous version of files to the blob container. No database migrations — purely file-based rollback. Keep previous versioned files in a tagged git commit for quick recovery.

---

## Testing

### Manual Testing Checklist

| Feature | Steps |
|---------|-------|
| 3D Model Load | Open page → model renders within 5s |
| Kit Selection | Click Kit → Dynamic/Pro → materials swap |
| Color Change | Click Color → Red/Grey/Blue → body texture updates |
| Wheel Color | Select alloy color → wheel meshes update |
| Race Number | Open number picker → scroll digits → apply |
| Price Update | Change config → price reflects correct total |
| AR (Mobile) | Tap AR icon → model-viewer launches |
| AR (Desktop) | Tap AR icon → QR code appears |
| Save Config | Login → save → reload → config persists |
| Place Order | Buy Now → accept T&C → redirect to payment |
| Responsive | Test on 375px, 768px, 1440px widths |

### Browser Compatibility

| Browser | Min Version | Status |
|---------|-------------|--------|
| Chrome | 90+ | ✅ Primary |
| Safari | 15+ | ✅ Supported |
| Firefox | 88+ | ✅ Supported |
| Edge | 90+ | ✅ Supported |
| Samsung Internet | 14+ | ✅ Supported |
| iOS Safari | 15+ | ✅ AR supported |

> **Note:** No automated test suite exists. Testing is manual.

---

## Folder Structure

```
rr310-configurator-experience-v1/
├── index.html                          # Production entry point
├── index_preprod.html                  # UAT/dev entry point
├── index_preprod.css                   # Stylesheet
├── configmaster_tvs_preprod_new.js     # Product config schema (source)
├── configmaster_tvs_preprod.min.js     # Product config (minified, production)
├── avataarrenderer_preprod.js          # 3D engine (source)
├── avataarrenderer_preprod.min.js      # 3D engine (minified, production)
├── aframe-1.4.0.min.js                # A-Frame framework (local copy)
├── *.glb                               # 3D model files (multiple variants)
├── ShadowCatcher_Ground_Plane_draco.glb
│
├── preprodAssets/                      # UI assets
│   ├── hdri/                           # Environment cubemap (IBL)
│   ├── Textures/                       # Material swap textures
│   ├── global menu/                    # Navigation icons
│   ├── kit/                            # Kit selector images
│   ├── color/                          # Color swatch images
│   ├── feature/                        # Feature callout images
│   ├── race number/                    # Number picker assets
│   ├── price_summary/                  # Order flow assets
│   ├── save functionality/             # Save config UI
│   ├── videos/                         # Feature videos
│   ├── audios/                         # Audio narrations
│   └── userflow/                       # Onboarding overlays
│
├── common/                             # Shared assets (AR instructions, loaders)
├── _0x7f3d2a1e/                        # Split GLB binary chunks
├── docs/                               # Documentation
│   ├── hlc.md                          # High Level Code Document
│   ├── hld.md                          # High Level Design
│   ├── lld.md                          # Low Level Design
│   └── api-specification.md            # API Reference
│
├── cancellationpolicy.html             # Legal pages
├── disclaimer.html
└── privacypolicy.html
```

---

## Common Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| 3D model doesn't load | CORS error on chunk API | Run on localhost or configure proxy for `uat-www.tvsmotor.net` |
| Black screen on load | WebGL not supported | Use a modern browser; check GPU drivers |
| Icons don't appear | `configmaster` not loaded first | Verify script order in HTML `<head>` |
| "Developer tools detected" overlay | DevTools protection active | Comment out the detection script block for development |
| Console is empty | Production console suppression | Develop on `localhost` to bypass suppression |
| AR button does nothing | Not on mobile / Model Viewer not loaded | Test on physical Android/iOS device |
| API calls fail locally | CORS + no auth token | Use browser CORS extension or proxy; pass `?userId=test` |
| Price shows NaN | Missing `priceAPI` field in config | Check `ConfigurationDetails[N].priceAPI` has all fields |
| Model loads but no textures | Texture path 404 | Verify `preprodAssets/Textures/` paths match schema |
| Page freezes on load | DevTools detection loop | Close devtools or remove detection script |

---

## Documentation

Detailed documentation is in the `docs/` folder:

- **[High Level Code Document](docs/hlc.md)** — Module overview, folder structure, workflows
- **[High Level Design](docs/hld.md)** — Architecture, deployment, integrations
- **[Low Level Design](docs/lld.md)** — Implementation details, algorithms, data models
- **[API Specification](docs/api-specification.md)** — Endpoint reference with OpenAPI spec

---

## Maintainers

| Role | Name | Contact |
|------|------|---------|
| Product Owner | *[Name]* | *[email]* |
| Tech Lead | *[Name]* | *[email]* |
| Frontend Engineer | *[Name]* | *[email]* |
| 3D/WebGL Engineer | *[Name]* | *[email]* |
| DevOps/Deployment | *[Name]* | *[email]* |

### Support Channels

- **Slack:** *#rr310-bto-configurator*
- **Jira Board:** *[Project URL]*
- **Confluence Space:** *[Documentation URL]*

---

## Version

**Current:** v1.0.16  
**Last Updated:** June 2026

# TVS Apache RTR 310 - 3D Vehicle Configurator

A Direct-to-Consumer (D2C) web application for the TVS Apache RTR 310 motorcycle featuring an interactive 3D configurator built with React 19 and Babylon.js.

---

## Application Overview

This application allows users to:
- Explore the TVS Apache RTR 310 in real-time 3D (rotate, zoom, pan)
- Change vehicle colors (Fiery Red, Fury Yellow, Arsenal Black, Sepang Blue)
- Select BTO (Built-to-Order) accessory kits (Dynamic / Dynamic Pro)
- View feature details via interactive 3D hotspots
- Register/login using OTP-based authentication
- Place orders with payment gateway integration

**Tech Stack:** React 19 · Babylon.js 8 · TypeScript · Zustand · Vite · SCSS

---

## Setup Instructions

### Prerequisites

- **Node.js** >= 18.x
- **npm** >= 9.x (or yarn/pnpm)
- Modern browser with WebGL2 support

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd RTR310

# Install dependencies
npm install
```

---

## Local Development

### Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (default Vite port).

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | TypeScript check + Vite production build |
| `npm run lint` | Run ESLint |
| `npm run preview` | Preview production build locally |

### Development Proxy

In development mode, Vite proxies API calls to bypass CORS:
- `/api/*` → TVS backend API
- `/blob-proxy/*` → Azure Blob Storage

Configure proxy rules in `vite.config.ts` if needed.

---

## Environment Variables

Environment variables are prefixed with `VITE_` (Vite convention) and configured per environment:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_ENV` | Environment name | `local`, `dev`, `uat`, `production` |
| `VITE_API_BASE_URL` | TVS Motor Web API base URL | `https://uat-www.tvsmotor.net/api` |
| `VITE_LOGIN_URL` | TVS Connect auth API base URL | `https://uat-tvsconnectapi.tvsmotor.net/api` |
| `VITE_BLOB_SAS_ENDPOINT` | Blob SAS token API path | `/api/BlobSas/GetRes?t=rtr310` |

### Environment Files

| File | Purpose |
|------|---------|
| `.env` | Local development (default) |
| `.env.development` | Development environment |
| `.env.uat` | UAT/Staging environment |
| `.env.production` | Production environment |

To use a specific environment:
```bash
# Vite uses the mode flag to select env file
npx vite --mode uat        # Uses .env.uat
npx vite --mode production # Uses .env.production
```

---

## Build Instructions

### Production Build

```bash
npm run build
```

This runs:
1. `tsc -b` — TypeScript compilation and type checking
2. `vite build` — Optimized production bundle

Output is generated in the `dist/` directory.

### Build Output

```
dist/
├── index.html          # Entry HTML
├── assets/
│   ├── index-[hash].js # Main JS bundle
│   ├── index-[hash].css# Compiled styles
│   └── [asset files]   # Images, fonts, textures
```

---

## Deployment Steps

### Azure Blob Storage (Static Website) — Manual Upload

The application is deployed to **Azure Blob Storage** with Static Website hosting enabled. Deployment is done manually (no CI/CD pipeline).

#### Step-by-Step Deployment

1. **Build the application for the target environment:**
   ```bash
   # UAT build
   npx vite build --mode uat

   # Production build
   npx vite build --mode production
   ```

2. **Upload `dist/` contents to Azure Blob Storage `$web` container:**

   **Option A — Azure Portal:**
   - Go to Azure Portal → Storage Account → Containers → `$web`
   - Delete existing files (or overwrite)
   - Upload all files from the local `dist/` folder maintaining folder structure

   **Option B — Azure Storage Explorer:**
   - Open Azure Storage Explorer
   - Navigate to the storage account → Blob Containers → `$web`
   - Delete old content and upload the new `dist/` folder contents

   **Option C — Azure CLI:**
   ```bash
   az storage blob upload-batch \
     --account-name <storage-account-name> \
     --destination '$web' \
     --source ./dist \
     --overwrite
   ```

3. **Verify deployment:**
   - Access the Static Website URL: `https://<account>.z13.web.core.windows.net`
   - Confirm 3D model loads and APIs respond

#### Azure Static Website Configuration
- **Index document:** `index.html`
- **Error document:** `index.html` (for SPA hash routing fallback)
- **Container:** `$web` (auto-created when static website is enabled)

### Post-Deployment Checklist
- [ ] Verify CORS configuration on TVS APIs for the deployment domain
- [ ] Ensure Azure Blob Storage CORS allows the deployment domain
- [ ] Confirm environment variables in build point to correct API endpoints
- [ ] Test OTP flow with correct `LOGIN_URL`
- [ ] Verify 3D model loading (SAS tokens accessible from deployed domain)
- [ ] Check that `index.html` is set as both index and error document

---

## Testing Instructions

### Manual Testing

Currently, the project does not have an automated test suite. Testing is performed manually:

1. **3D Scene**: Verify model loads, camera controls work, color changes apply
2. **Authentication**: Test OTP request/verify for login and registration
3. **Configuration**: Select kits, change colors, verify price updates
4. **Order Flow**: Place order, verify payment redirect
5. **Security**: Open DevTools to verify blocking overlay appears

### Linting

```bash
npm run lint
```

---

## Folder Structure

```
RTR310/
├── public/                     # Static public assets
│   ├── fonts/gilroy/          # Gilroy font files
│   └── plugins/situ-design/   # SITU design plugin
├── src/
│   ├── assets/                # App assets (images, textures, env maps)
│   ├── babylon/               # 3D engine (scene, camera, hotspots)
│   ├── components/            # Reusable UI components
│   │   ├── BtoPopup/         # BTO kit selection popup
│   │   ├── Callouts/         # Feature callout panel
│   │   ├── Colors/           # Color picker component
│   │   ├── ConfirmOrder/     # Order confirmation modal
│   │   ├── Footer/           # Bottom navigation bar
│   │   ├── header/           # Top bar (price, expand)
│   │   ├── PlaceOrder/       # Order summary panel
│   │   └── Toast/            # Toast notification system
│   ├── config/                # Environment config accessor
│   ├── constants/             # App configuration constants
│   │   └── hotspotConfig/    # 3D hotspot definitions
│   ├── context/               # React contexts (Scene, Camera)
│   ├── hooks/                 # Zustand stores & custom hooks
│   ├── pages/                 # Route-level pages (SignIn, SignUp)
│   ├── route/                 # React Router config
│   ├── services/              # API service layer (Axios)
│   ├── styles/                # Global SCSS styles
│   └── utils/                 # Utilities (security, model loader)
├── docs/                       # Project documentation
├── .env.*                      # Environment configs
├── package.json               # Dependencies & scripts
├── tsconfig.json              # TypeScript config
├── vite.config.*              # Vite build config
└── eslint.config.js           # ESLint config
```

---

## Common Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 3D model won't load | CORS blocking blob storage | Configure Vite proxy for `/blob-proxy` |
| Blank screen on load | DevTools open (security block) | Close DevTools and refresh |
| "Access Blocked" overlay | Security check triggered | Close all dev tools, refresh page |
| API 401 errors | Expired token | Logout and re-login |
| OTP not received | Wrong environment API | Check `.env` file's `VITE_LOGIN_URL` |
| Colors not changing | Texture files missing | Verify `src/assets/models/textures/` has all color JPGs |
| Build fails | TypeScript errors | Run `npx tsc --noEmit` to see errors |
| Price shows fallback | API unreachable | Check `VITE_API_BASE_URL` connectivity |
| Vite proxy not working | Wrong config | Ensure `vite.config.ts` has correct proxy targets |

### Known Limitations
- DevTools detection may trigger false positives on some screen sizes
- 3D model requires ~2-5MB download (chunked)
- OTP timer is 90 seconds (no configurable option)
- Prices currently filtered for "Delhi" state only

---

## Maintainer / Contact

| Role | Contact |
|------|---------|
| Project Owner | [TVS Motor Company] |
| Development Team | [Team Contact Placeholder] |
| Technical Lead | [Tech Lead Placeholder] |
| Repository | [Repository URL Placeholder] |

---

## License

Proprietary - TVS Motor Company. All rights reserved.

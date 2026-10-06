# TVS PlanIQ — Setup & Deployment Guide

## Overview

TVS PlanIQ is a FastAPI application with a static frontend. It uses:
- **Azure OpenAI (gpt-4o-mini)** for LLM inference (primary)
- **Ollama** as optional local fallback
- **SharePoint** for data persistence (Excel files via Microsoft Graph API)
- **Azure AD SSO** for authentication in production

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.11+ |
| Docker | For containerized deployment |
| Azure OpenAI | Endpoint + API key + gpt-4o-mini deployment |
| SharePoint | Site with Graph API access (App Registration with Files.ReadWrite.All) |
| Azure AD App Registration | For SSO (optional in dev, required in prod) |

---

## 1. Local Development Setup

### Clone and install dependencies

```bash
cd estimation-tool
pip install -r requirements.txt
```

### Configure environment

Copy `.env.example` to `.env.dev` and fill in your credentials:

```bash
cp .env.example .env.dev
```

Required variables:
```
DEV_MODE=true
SSO_SECRET=<any-32-char-string>

# Azure OpenAI (primary LLM)
AZURE_OPENAI_KEY=<your-azure-openai-key>
AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
AZURE_OPENAI_DEPLOYMENT_GPT4O=gpt-4o-mini

# SharePoint persistence
SHAREPOINT_TENANT_ID=<azure-ad-tenant-id>
SHAREPOINT_CLIENT_ID=<app-registration-client-id>
SHAREPOINT_CLIENT_SECRET=<app-registration-secret>
SHAREPOINT_SITE_URL=<sharepoint-site-url>
SHAREPOINT_DRIVE_ID=<document-library-drive-id>
```

### Run locally

```bash
set -a && source .env.dev && set +a
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

### Optional: Run Ollama (local LLM fallback)

```bash
# In a separate terminal
OLLAMA_NUM_PARALLEL=2 ollama serve
ollama pull gemma3:4b
```

---

## 2. Production Deployment (Docker)

### Build the image

```bash
docker build -f Dockerfile.app -t tvs-planiq:latest .
```

### Configure production environment

Edit `.env.prod` with production credentials:

```
DEV_MODE=false
SSO_SECRET=<strong-production-secret-32-chars-min>

# Azure OpenAI
AZURE_OPENAI_KEY=<production-azure-key>
AZURE_OPENAI_ENDPOINT=<production-azure-endpoint>
AZURE_OPENAI_DEPLOYMENT_GPT4O=gpt-4o-mini

# SharePoint
SHAREPOINT_TENANT_ID=<prod-tenant-id>
SHAREPOINT_CLIENT_ID=<prod-client-id>
SHAREPOINT_CLIENT_SECRET=<prod-client-secret>
SHAREPOINT_SITE_URL=<prod-sharepoint-site-url>
SHAREPOINT_DRIVE_ID=<prod-drive-id>
```

### Run the container

```bash
docker run -d \
  --name tvs-planiq \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env.prod \
  tvs-planiq:latest
```

### Verify deployment

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","devMode":"false"}
```

---

## 3. SharePoint Setup

The app auto-creates its folder structure on first startup. Required permissions for the App Registration:

| Permission | Type | Purpose |
|-----------|------|---------|
| Sites.ReadWrite.All | Application | Read/write SharePoint files |
| Files.ReadWrite.All | Application | Manage Excel workbooks |

### Folder structure created automatically:

```
Document Library Root/
├── Estimations/
│   ├── EstimationIndex.xlsx
│   ├── Estimations/          (monthly data files)
│   └── Audit/                (monthly audit logs)
├── PrdCheck/
│   ├── Audit/                (PRD check audit logs)
│   └── Templates/            (uploaded doc templates)
└── MPCP_FY2026_27/           (financial year folder)
    ├── MPCPTracker.xlsx      (all MPCP data: MPs, CPs, Projects, etc.)
    ├── Audit/                (MPCP audit logs)
    └── Exports/              (generated reports)
```

### How to get the Drive ID:

1. Go to SharePoint site → Document Library
2. Use Graph Explorer: `GET https://graph.microsoft.com/v1.0/sites/{site-id}/drives`
3. Copy the `id` of the document library drive

---

## 4. Azure AD SSO Setup (Production)

In production (`DEV_MODE=false`), the app validates JWT tokens from Azure AD.

### App Registration setup:

1. Register an app in Azure AD
2. Add redirect URI: `https://your-domain.com`
3. Enable ID tokens
4. Add users/groups to the app

### Environment variables for SSO:

```
SSO_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
SSO_AUDIENCE=<app-registration-client-id>
SSO_JWKS_URL=https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys
```

### Dev mode bypass:

When `DEV_MODE=true`, authentication is bypassed with a demo token. Any request with `Authorization: Bearer demo-token` is accepted as "Suraj Ray / Admin".

---

## 5. User Management

### Adding users (Admin only):

1. Navigate to Settings → Users in the UI
2. Add users by corporate email
3. Assign role: `Admin`, `User`, or `Partner`

> Re-adding a previously removed user reactivates their existing row (and updates the role) rather than creating a duplicate, so logins keep working.

### Roles & access control:

- Only registered (allowlisted) users can access the tool. Unknown/inactive emails are denied at login.
- **Admin** — manage users, upload templates, edit system/SLM config; full access to all modules including Budget; full create/edit/delete on the MPCP hierarchy.
- **User** — run estimations, check PRDs, and act as a **full contributor** in the MPCP Tracker: create, edit, and delete MPs/CPs/Projects and update tracking data. Full Budget access.
- **Partner** — same MPCP contributor access as User (create/edit/delete hierarchy + tracking), **except Budget** data, which is hidden and blocked (403). Intended for external delivery partners.

MPCP Tracker permission summary:

| Action | Admin | User | Partner |
|--------|:-----:|:----:|:-------:|
| View hierarchy / tracking data | ✅ | ✅ | ✅ |
| Create / edit / delete MP, CP, Project | ✅ | ✅ | ✅ |
| Update RAG, Process Track, Milestones, Tasks, Dependencies | ✅ | ✅ | ✅ |
| View / edit Budget | ✅ | ✅ | ❌ (403) |
| Manage users / templates / system config | ✅ | ❌ | ❌ |

> User-management, template, and system/SLM config endpoints remain **Admin-only** (`require_admin`). MPCP hierarchy and tracking endpoints are open to any authenticated role; Budget is gated by `require_budget_access` (Partner denied).

---

## 6. Health & Monitoring

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic health check (returns status + devMode) |
| `GET /api/estimations/jobs` | Active estimation jobs |

### Docker health check:

The container has a built-in health check (every 30s). Docker will restart it if unhealthy after 3 consecutive failures.

---

## 7. Key Configuration Files

| File | Purpose |
|------|---------|
| `config/doc_templates.json` | PRD/BRD/HLD template sections for completeness checking |
| `config/estimation_catalog.json` | Work item catalog for effort estimation |
| `config/estimation_blueprint.md` | Estimation methodology reference |
| `config/system_dependencies.json` | System dependency graph |

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid authentication token" | Check `DEV_MODE` is `true` for local dev, or configure SSO properly for prod |
| SharePoint initialization failed | Verify tenant ID, client ID, secret, site URL, and drive ID are correct |
| Azure OpenAI timeout | Check endpoint URL ends with `/`, verify API key, check deployment name |
| Empty estimation results | Ensure documents are uploaded (BRD + PRD minimum for Tier 1) |
| MPCP data lost on restart | In dev without SharePoint connection, data is in-memory only. Connect SharePoint for persistence |

---

## 9. Updating & Redeployment

```bash
# Pull latest code
git pull

# Rebuild image
docker build -f Dockerfile.app -t tvs-planiq:latest .

# Restart container
docker stop tvs-planiq && docker rm tvs-planiq
docker run -d --name tvs-planiq --restart unless-stopped -p 8000:8000 --env-file .env.prod tvs-planiq:latest
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│              TVS PlanIQ                      │
├─────────────────────────────────────────────┤
│  Frontend: Static HTML/JS (served by FastAPI)│
│  Backend:  FastAPI (Python 3.11)            │
│  LLM:     Azure OpenAI (primary)           │
│            Ollama (fallback, optional)       │
│  Storage:  SharePoint (Excel via Graph API) │
│  Auth:     Azure AD SSO (prod)             │
│            Demo token bypass (dev)           │
└─────────────────────────────────────────────┘
```

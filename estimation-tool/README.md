# Project Estimation Tool

A self-service web application that leverages an embedded Small Language Model (SLM) to generate effort estimations from business and technical documents (BRD, PRD, HLD). Produces per-discipline effort breakdowns, cost projections, timeline calculations, confidence scores, and scope coverage analysis.

## Features

- **Document-based estimation**: Upload BRD, PRD, HLD documents to generate comprehensive project estimates
- **Multi-discipline breakdown**: Per-discipline effort in person-days/months with team composition
- **Confidence scoring**: 5-factor composite confidence score with actionable recommendations
- **Scope coverage analysis**: Maps PRD items against base templates, identifies gaps
- **Cost projection**: Configurable rate card-based cost calculations
- **Timeline calculation**: Calendar duration with scenario modeling
- **Vendor comparison**: Compare vendor proposals against internal estimates
- **Build vs Buy evaluation**: Multi-criteria scoring for build/buy/partner decisions
- **PRD completeness checker**: Validates document readiness against org templates
- **MPCP Project Tracker**: Full-lifecycle project tracking (MP → CP → Project → Milestones → Tasks) with auto-RAG detection, 3W1H accountability, budget ledger, dependencies, Gantt charts, and Excel exports
- **Re-estimation**: Track changes with before/after comparison and full audit trail
- **Admin panel**: User management, SLM configuration, rate card settings, template management
- **Zero external API calls**: All inference runs locally via Ollama (gemma3:4b)

## Architecture

```
┌─────────────────────────────────────┐
│  Frontend (HTML/JS SPA)             │
├─────────────────────────────────────┤
│  FastAPI Backend                    │
│  ├── Auth Middleware (SSO + Allow)  │
│  ├── Rate Limiter (10 req/min)     │
│  ├── Error Handler                  │
│  ├── Estimation Engine              │
│  ├── MPCP Tracker (48+ APIs)        │
│  ├── Build vs Buy Evaluator         │
│  ├── PRD Completeness Checker       │
│  ├── Vendor Comparator              │
│  └── Audit Service                  │
├─────────────────────────────────────┤
│  Ollama (gemma3:4b) ← local SLM    │
├─────────────────────────────────────┤
│  SharePoint (Excel via Graph API)   │
│  └── ProjectTracker/{FY}/           │
│       MPCPTracker.xlsx (12 sheets)  │
└─────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed locally (or use Docker)
- SharePoint site with Microsoft Graph API access (service account credentials)
- Corporate SSO provider (Azure AD / compatible OIDC)

## Quick Start (Local Development)

### 1. Install dependencies

```bash
cd estimation-tool
pip install -r requirements.txt
```

### 2. Start Ollama and pull the model

```bash
ollama serve &
ollama pull qwen3:4b
```

### 3. Set environment variables

```bash
export SHAREPOINT_TENANT_ID="your-tenant-id"
export SHAREPOINT_CLIENT_ID="your-client-id"
export SHAREPOINT_CLIENT_SECRET="your-client-secret"
export SHAREPOINT_SITE_ID="your-site-id"
export SHAREPOINT_DRIVE_ID="your-drive-id"
export SSO_SECRET="dev-secret"
export OLLAMA_HOST="http://localhost:11434"
export SLM_MODEL_NAME="qwen3:4b"
```

Or create a `.env` file with these values.

### 4. Run the application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open the UI

Navigate to [http://localhost:8000](http://localhost:8000)

## Docker Deployment

### Option A: All-in-one (bundled Ollama)

Build and run with Ollama bundled inside the container:

```bash
docker build -t estimation-tool .
docker run -p 8000:8000 \
  -e SHAREPOINT_TENANT_ID="..." \
  -e SHAREPOINT_CLIENT_ID="..." \
  -e SHAREPOINT_CLIENT_SECRET="..." \
  -e SHAREPOINT_SITE_ID="..." \
  -e SHAREPOINT_DRIVE_ID="..." \
  -e SSO_SECRET="dev-secret" \
  estimation-tool
```

> Note: First run will pull the qwen3:4b model (~2.5GB).

### Option B: Docker Compose (recommended for production)

Uses separate containers for the app and Ollama:

```bash
# Create .env file with your credentials
cp .env.example .env
# Edit .env with your values

# Start services
docker-compose up -d

# Pull the model (first time only)
docker exec estimation-tool-ollama ollama pull qwen3:4b

# Check status
docker-compose ps
docker-compose logs -f app
```

### Azure VM Deployment

1. **Provision Azure VM**: Standard_D4s_v3 or higher (4 vCPU, 16GB RAM recommended for SLM)
2. **Install Docker**: Follow [Docker install docs](https://docs.docker.com/engine/install/)
3. **Clone repository** and copy to VM
4. **Configure environment**:
   - Set SharePoint credentials in `.env`
   - Configure SSO settings for your Azure AD tenant
5. **Start services**:
   ```bash
   docker-compose up -d
   docker exec estimation-tool-ollama ollama pull qwen3:4b
   ```
6. **Configure reverse proxy** (nginx/Caddy) for HTTPS
7. **Set up monitoring**: Use health endpoints `/health` and `/health/detailed`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/estimations | Generate new estimation |
| GET | /api/estimations | List estimations (dashboard) |
| GET | /api/estimations/:id | Get estimation detail |
| POST | /api/estimations/:id/re-estimate | Re-estimate existing project |
| POST | /api/estimations/:id/vendor-compare | Compare vendor proposals |
| POST | /api/estimations/:id/scenarios | Model team scenarios |
| GET | /api/estimations/:id/audit | Get audit history |
| GET | /api/estimations/:id/export/pdf | Export as PDF |
| GET | /api/estimations/:id/export/json | Export as JSON |
| GET | /api/admin/users | List users (Admin) |
| POST | /api/admin/users | Add user (Admin) |
| DELETE | /api/admin/users/:id | Remove user (Admin) |
| GET | /api/admin/config | Get system config |
| PUT | /api/admin/config | Update config (Admin) |
| GET | /api/admin/templates | List templates |
| POST | /api/admin/templates | Create template (Admin) |
| DELETE | /api/admin/templates/:id | Delete template (Admin) |
| GET | /health | Health check |
| GET | /health/detailed | Detailed health check |

## Configuration

### SharePoint Files

The application uses the following Excel files on SharePoint:

- **Users.xlsx**: User allowlist with roles
- **Config.xlsx**: SLM and rate card configuration
- **Templates.xlsx**: Base estimation templates
- **EstimationIndex.xlsx**: Lightweight dashboard index
- **Estimations_YYYY-MM.xlsx**: Monthly estimation data (auto-created)
- **AuditLog_YYYY-MM.xlsx**: Monthly audit logs (auto-created)

### Rate Limiting

- Default: 10 requests per minute per user
- Returns HTTP 429 with Retry-After header when exceeded
- Configure via `RateLimiterMiddleware` parameters in `main.py`

### SLM Configuration

- Default model: `qwen3:4b`
- Context window: 8192 tokens
- Configurable via Admin panel or `Config.xlsx`

## Development

### Run tests

```bash
cd estimation-tool
python -m pytest tests/ -v
```

### Project structure

```
estimation-tool/
├── app/
│   ├── middleware/     # Auth, rate limiter, error handler
│   ├── models/         # Pydantic schemas
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   └── utils/          # Shared utilities
├── static/             # Frontend SPA (index.html)
├── tests/              # Unit and property tests
├── main.py             # FastAPI application entry point
├── requirements.txt    # Python dependencies
├── Dockerfile          # All-in-one container
├── Dockerfile.app      # App-only container (for docker-compose)
└── docker-compose.yml  # Multi-service deployment
```

## License

Internal use only. All rights reserved.

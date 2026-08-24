# TVSM AI Platform

Monorepo for the two internal AI apps deployed on the UAT VM
(`tazsmrtbrnvmuat01` / 10.44.59.200), fronted by nginx on a single hostname.

## Layout

```
tvsm-ai-platform/
├── smartbrain-v2/      Engineering Memory Graph — REST API, chatbot UI, MCP server
│                        (FastAPI on :8000; Neo4j + Qdrant via docker compose)
├── estimation-tool/    PlanIQ — project estimation tool (FastAPI on :9000, Azure OpenAI)
├── deploy/
│   └── nginx/          Reverse-proxy config (TLS + path routing)
└── .gitignore
```

## Public routing (single DNS name)

`smartbrain.tvsmotor.net` (→ 10.44.59.200), path-based via nginx:

| URL | Backend |
|---|---|
| `/brain/chatbot` | SmartBrain UI (`127.0.0.1:8000`) |
| `/brain/mcp` | SmartBrain MCP (Streamable HTTP) |
| `/brain/v1/...` | SmartBrain REST API |
| `/planiq/` | PlanIQ / Estimation (`127.0.0.1:9000`) |

## Run (on the VM)

**SmartBrain** (from `smartbrain-v2/`, venv active; infra via `./start.sh infra`):
```
uvicorn api.app:app --host 0.0.0.0 --port 8000 --root-path /brain
```

**PlanIQ / Estimation** (from `estimation-tool/`, Azure OpenAI, no Ollama):
```
docker compose up --build -d      # app on :9000, add --root-path /planiq to the CMD
```

**nginx** (TLS + routing):
```
sudo cp deploy/nginx/tvsm-platform.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/tvsm-platform.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

## Notes

- `data/` (Neo4j + Qdrant + BM25 state) is **not** in git — it's large binary
  runtime state. Re-ingest with `python -m ingestion.run_sync --clean` or restore
  a copy separately.
- `.env` files are gitignored (they hold Azure/SharePoint secrets). Use the
  committed `.env.example` as a template.
- The apps run behind a `/brain` and `/planiq` path prefix, so each is started
  with a matching `--root-path`. In the SmartBrain chatbot UI settings, set the
  **API Base URL** to `/brain` so its API calls resolve correctly.

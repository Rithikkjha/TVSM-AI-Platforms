# Engineering Memory Graph (V1)

A microservices knowledge graph that captures how engineering systems connect — services,
teams, code, tickets, and documentation — and exposes this knowledge through a REST
Query API and a natural language chatbot interface grounded in the graph.

The platform is MCP-first: ingestion is driven by Model Context Protocol servers, and graph
extraction combines deterministic parsing (for structured data) with LLM-backed extraction
(for unstructured text).

## Scope (V1 Pilot)

- Ingestion from GitHub, Jira, and Confluence via MCP servers.
- Scale: 10–20 repositories, 1–2 Jira projects, 1–2 Confluence spaces.
- Query API (REST, 4 endpoints): `services/{name}`, `services/{name}/impact`, `search`, `ask`.
- Web UI: search, service detail, NL chatbot.
- Internal/VPN-only pilot, single shared API key.

See [`.kiro/specs/engineering-memory-graph/`](./.kiro/specs/engineering-memory-graph/) for the
full requirements, design, and implementation plan.

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |Layer 1: Data Sources
"We pull knowledge from 4 places:

GitHub — 42 repos from our org. We get repo metadata, the last 30 PRs per repo, contributors, and CODEOWNERS files. This tells us what services exist and who works on them.

Jira — 11 projects (CCP, CBS). We get tickets and epics. This tells us what work is planned, in progress, or done — linked to which service.

Confluence — 3 spaces of wiki documentation. Architecture pages, API contracts, runbooks. The LLM reads these pages and tries to extract which services are mentioned — creating 'documented_in' links.

Kiro Steering — this is the richest source. We opened each of our 42 repos in Kiro and asked it to analyze the full codebase. It generated 3 files per service: product context (what it does), code structure (how it's organized), and tech stack (what it uses, what it depends on). This gives us structured, code-derived knowledge that doesn't exist anywhere else."

Layer 2: Ingestion Pipeline
"An ingestion script pulls from each source, extracts structured entities (services, tickets, pages, PRs), and writes them idempotently into two stores. Idempotent means — if you run it twice, nothing duplicates. It checks a content hash and only updates what actually changed."

Layer 3: Two Databases (the brain)
"Neo4j — a graph database. Think of it as a map. Nodes are things (services, teams, tickets, docs). Edges are relationships (this service DEPENDS_ON that service, this ticket is LINKED_TO that service, this person is LOCATED_IN that team). It knows structure — who connects to whom.

Qdrant — a vector database. Every piece of text (steering content, Confluence pages, ticket descriptions) gets converted into a 1536-dimensional number array using Azure OpenAI's embedding model. When you ask a question, your question gets embedded too, and Qdrant finds the most similar content by mathematical distance. It knows meaning — it can find 'payment processing' even if the doc says 'financial transaction handling'.

Together: Qdrant finds relevant stuff by meaning. Neo4j adds context by traversing connections. The LLM synthesizes it all into a coherent answer."

Layer 4: Consumer Surfaces
"Three ways to access the same brain:

MCP Server — 4 tools available in Kiro/Claude. The AI calls them automatically when you ask about services. This is for developers.

Chatbot UI — web browser at localhost:8000/ui. Type a question, get an answer. This is for anyone — PMs, architects, new joiners who don't use the IDE.

REST API — programmatic endpoints. For scripts, CI/CD pipelines, or custom integrations. Same data, HTTP interface."
| API framework | FastAPI |
| Graph database | Neo4j 5.x (Community for dev, AuraDB for prod) |
| Vector store | Azure AI Search (prod) / Qdrant (dev) |
| LLM / embeddings | Azure OpenAI (GPT-4o, text-embedding-3-large) |
| MCP runtime | Model Context Protocol SDK (Python) |
| Container orchestration | Docker Compose (dev), AKS (prod) |
| Property-based testing | Hypothesis |
| Unit testing | pytest |

## Repository Layout

```
src/
  config/            # Pydantic settings + MCP server registry loader
    settings.py      # All app settings from environment variables
    mcp_registry.py  # YAML config loader for MCP servers
    mcp_servers.yaml # MCP server registry (GitHub, Jira, Confluence)
  ingestion/         # MCP Orchestrator + periodic sync scheduler
    orchestrator.py  # Coordinates MCP server calls + routes to extraction
    scheduler.py     # Periodic full re-sync (default: every 6 hours)
    github_client.py # GitHub MCP integration
    jira_client.py   # Jira MCP integration
    confluence_client.py # Confluence MCP integration
    run_sync.py      # Manual sync entry point
    steering_ingest.py # Steering file ingestion
    generate_steering.py # Auto-generate steering docs from graph
    retry.py         # Exponential backoff retry logic
  extraction/        # Deterministic + LLM extraction, embeddings, write coordinator
    deterministic.py # Structured data extraction (repos, PRs, tickets)
    llm_extractor.py # LLM-backed extraction for unstructured text
    embeddings.py    # Azure OpenAI text-embedding-3-large (3072 dims)
    writer.py        # Idempotent write coordinator (source_id + text_hash)
  models/            # Graph schema, Neo4j + vector store adapters
    schema.py        # Node labels, relationship types, validation
    graph_store.py   # Async Neo4j driver wrapper (upsert, soft-delete)
    vector_store.py  # Azure AI Search / Qdrant abstraction
    setup_neo4j.py   # Schema setup (constraints, indexes)
  query/             # FastAPI app, REST endpoints, GraphRAG pipeline
    app.py           # Main FastAPI application + middleware
    services.py      # GET /v1/services/{name} and /impact endpoints
    search.py        # GET /v1/search endpoint
    ask.py           # POST /v1/ask — GraphRAG pipeline
    freshness.py     # Staleness detection + freshness summary
    graph_queries.py # Reusable Neo4j query helpers
    schemas.py       # Pydantic response models
  webhooks/          # Webhook receivers + signature verification
    adapter.py       # POST /webhooks/github, /jira, /confluence
ui/                  # Web UI (plain HTML/JS SPA)
  index.html         # Main page
  app.js             # Application logic (chat, search, service detail)
  api.js             # API client (fetch wrapper with X-API-Key)
  markdown.js        # Markdown-to-HTML renderer with GFM tables
  style.css          # Styles
tests/
  unit/              # Fast unit tests
  properties/        # Hypothesis property-based tests
  integration/       # End-to-end tests against real Neo4j / vector store
```

## Getting Started

### Prerequisites

- Python 3.11 or newer
- Docker 24+ and Docker Compose v2 (for local Neo4j + Qdrant)
- Azure OpenAI API access (for LLM and embeddings)

### Environment Setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Fill in the required values in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `NEO4J_URI` | Yes (has default) | Neo4j Bolt URI (`bolt://neo4j:7687` for Docker) |
| `NEO4J_USER` | Yes (has default) | Neo4j username (`neo4j`) |
| `NEO4J_PASSWORD` | Yes (has default) | Neo4j password (`neo4jpassword`) |
| `AZURE_OPENAI_KEY` | Yes | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O` | Yes (has default) | GPT-4o deployment name |
| `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` | Yes (has default) | Embedding model deployment name |
| `QDRANT_URL` | Yes (has default) | Qdrant URL (`http://qdrant:6333` for Docker) |
| `GITHUB_TOKEN` | For ingestion | GitHub personal access token or App token |
| `JIRA_TOKEN` | For ingestion | Atlassian API token for Jira |
| `JIRA_EMAIL` | For ingestion | Atlassian account email |
| `JIRA_URL` | For ingestion | Jira instance URL |
| `CONFLUENCE_TOKEN` | For ingestion | Atlassian API token for Confluence |
| `CONFLUENCE_URL` | For ingestion | Confluence instance URL |
| `API_KEY` | Yes (has default) | API key for Query API auth (`dev-api-key`) |
| `MCP_SERVERS_CONFIG_PATH` | Yes (has default) | Path to MCP server registry YAML |

### Install (editable, with dev extras)

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Verify the package imports:

```bash
python -c "import src"
```

### Running the Service (Docker Compose)

Start all services (Neo4j, Qdrant, FastAPI API):

```bash
docker compose up --build -d
```

Then import the pre-built graph data (so you don't need to run ingestion):

```bash
./seed/import.sh
```

This brings up:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | FastAPI application |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Chatbot UI** | http://localhost:8000/ui/ | Web-based chat + search interface |
| **Neo4j Browser** | http://localhost:7474 | Graph database admin UI |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector store admin UI |

### Credentials (Development)

| Service | Username / Header | Password / Value |
|---------|-------------------|------------------|
| Query API | `X-API-Key` header | `dev-api-key` |
| Neo4j | `neo4j` | `neo4jpassword` |
| Qdrant | — | No auth required |

### Using the Chatbot UI

1. Open http://localhost:8000/ui/
2. Click the **Settings** icon (gear) in the sidebar
3. Enter API Key: `dev-api-key`
4. Leave Base URL as `/` (default)
5. Click **Save**
6. Start asking questions about your engineering systems

### API Endpoints

All endpoints (except `/v1/health`) require the `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/health` | Health check (no auth) — Neo4j, vector store status, freshness |
| `GET` | `/v1/services/{name}` | Service detail with owners, deps, tickets, docs |
| `GET` | `/v1/services/{name}/impact` | Transitive dependency set (up to 2 hops) |
| `GET` | `/v1/search?q=&type=&limit=` | Vector + full-text search across entities |
| `POST` | `/v1/ask` | Natural language question → GraphRAG answer with citations |
| `POST` | `/webhooks/github` | GitHub webhook receiver |
| `POST` | `/webhooks/jira` | Jira webhook receiver |
| `POST` | `/webhooks/confluence` | Confluence webhook receiver |

### Example API Calls

```bash
# Health check (no auth)
curl http://localhost:8000/v1/health

# Get service details
curl -H "X-API-Key: dev-api-key" http://localhost:8000/v1/services/payments-service

# Impact analysis
curl -H "X-API-Key: dev-api-key" http://localhost:8000/v1/services/payments-service/impact

# Search
curl -H "X-API-Key: dev-api-key" "http://localhost:8000/v1/search?q=payment+retry&limit=5"

# Ask a natural language question
curl -X POST http://localhost:8000/v1/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key" \
  -d '{"question": "What services depend on the payments service?"}'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Source Systems                             │
│   GitHub (10-20 repos)  │  Jira (1-2 projects)  │  Confluence   │
└──────────┬──────────────┴───────────┬───────────┴───────┬───────┘
           │ webhooks                  │ webhooks           │ webhooks
           ▼                           ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ingestion Layer                              │
│  Webhook_Adapter → MCP_Orchestrator → Graph_Extraction_Engine    │
│  (signature verify)  (retry + schedule)  (deterministic + LLM)   │
└──────────────────────────┬──────────────────────┬───────────────┘
                           │                      │
                           ▼                      ▼
┌──────────────────────────────────┐  ┌───────────────────────────┐
│         Neo4j (Graph DB)          │  │   Qdrant / Azure AI Search │
│  Services, Teams, Repos, PRs,     │  │   (Vector Embeddings)      │
│  Tickets, Epics, Confluence Pages │  │   3072-dim, cosine         │
└──────────────────┬───────────────┘  └───────────────┬───────────┘
                   │                                    │
                   ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Query Layer                                │
│  FastAPI: /services, /impact, /search, /ask (GraphRAG)           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Consumer Surfaces                            │
│          Web UI (Chat + Search)  │  IDE MCP Server (optional)    │
└─────────────────────────────────────────────────────────────────┘
```

## Graph Schema

### Entity Types (Node Labels)

| Entity | Key Properties |
|--------|---------------|
| `Service` | `source_id`, `name`, `description` |
| `Repository` | `source_id`, `name`, `url`, `default_branch`, `language` |
| `Team` | `source_id`, `name` |
| `Person` | `source_id`, `name`, `email`, `github_username`, `jira_username` |
| `Epic` | `source_id`, `key`, `title`, `status` |
| `Ticket` | `source_id`, `key`, `title`, `status`, `priority`, `description` |
| `PR` | `source_id`, `number`, `title`, `state`, `author`, `description` |
| `ConfluencePage` | `source_id`, `title`, `space_key`, `url`, `content_summary` |

### Relationship Types

| Relationship | Direction | Meaning |
|---|---|---|
| `OWNED_BY` | Service/Repo → Team | Ownership |
| `DEPENDS_ON` | Service → Service | Runtime or build dependency |
| `CONTAINS` | Repository → Service | Repo hosts service code |
| `LINKED_TO` | Ticket/Epic → Service | Work item linked to service |
| `MODIFIES` | PR → Repository | PR changes files in repo |
| `DOCUMENTED_IN` | Service → ConfluencePage | Documentation link |
| `LOCATED_IN` | Person → Team | Team membership |

## Data Ingestion

### Real-time Path

Source system webhook → Webhook_Adapter (signature verification) → MCP_Orchestrator → Graph_Extraction_Engine → Neo4j + Vector Store

### Batch Path

Scheduler (every 6 hours) → MCP_Orchestrator → full re-sync of all registered MCP servers → idempotent graph updates

### Idempotency

Every entity has a `source_id` (e.g., `github:repo:payments-service`) and `text_hash` (SHA-256 of source content). On re-ingestion, if the hash matches the existing entity, the write is skipped.

## Running Tests

```bash
pytest                 # run all tests
pytest -m unit         # fast unit tests only
pytest -m property     # Hypothesis property tests
pytest -m integration  # integration tests (require local stack running)
```

## Linting and Type Checking

```bash
ruff check src tests   # linting
mypy src               # type checking
```

## Configuration

### MCP Server Registry

The MCP server registry is defined in `src/config/mcp_servers.yaml`. It specifies which data sources to connect to:

```yaml
servers:
  - name: github
    type: "@modelcontextprotocol/server-github"
    config:
      org: "your-org"
      repos: ["service-a", "service-b"]
      token_env: "GITHUB_TOKEN"
  - name: jira
    type: "mcp-atlassian"
    config:
      instance: "your-org.atlassian.net"
      projects: ["ENG"]
      token_env: "JIRA_TOKEN"
  - name: confluence
    type: "mcp-atlassian"
    config:
      instance: "your-org.atlassian.net"
      spaces: ["ENG"]
      token_env: "CONFLUENCE_TOKEN"
```

### Tunable Parameters

| Setting | Default | Description |
|---------|---------|-------------|
| `STALENESS_THRESHOLD_HOURS` | 24 | Hours before entity is marked stale |
| `FULL_SYNC_INTERVAL_HOURS` | 6 | Hours between full re-syncs |
| `LLM_CONTEXT_TOKEN_BUDGET` | 8000 | Max tokens for LLM context window |
| `VECTOR_SEARCH_TOP_K` | 10 | Number of vector search results |
| `GRAPH_EXPANSION_HOPS` | 2 | Hops for graph neighborhood expansion |
| `LOG_LEVEL` | INFO | Application log level |

## Troubleshooting

### Importing seed data manually

If `./seed/import.sh` fails, you can import manually:

```bash
# Neo4j: decompress and import
gunzip -k seed/neo4j-seed.cypher.gz
docker cp seed/neo4j-seed.cypher emg-neo4j:/var/lib/neo4j/import/seed.cypher
docker exec emg-neo4j cypher-shell -u neo4j -p neo4jpassword --file /var/lib/neo4j/import/seed.cypher

# Qdrant: decompress and restore
gunzip -k seed/qdrant-snapshot.snapshot.gz
curl -X DELETE "http://localhost:6333/collections/memory_graph_entities"
curl -X POST "http://localhost:6333/collections/memory_graph_entities/snapshots/upload" \
  -F "snapshot=@seed/qdrant-snapshot.snapshot"
```

### Services won't start

```bash
# Remove old containers and restart
docker compose down
docker rm -f emg-neo4j emg-qdrant emg-api 2>/dev/null
docker compose up --build
```

### Neo4j healthcheck failing

Neo4j takes 30–60 seconds to start. The API container waits for the healthcheck to pass before starting. If it keeps failing:

```bash
# Check Neo4j logs
docker logs emg-neo4j

# Verify Neo4j is accessible
docker exec emg-neo4j cypher-shell -u neo4j -p neo4jpassword "RETURN 1"
```

### API returning 401

Ensure you're passing the API key header:

```bash
curl -H "X-API-Key: dev-api-key" http://localhost:8000/v1/services/my-service
```

### /v1/ask returning 503

The `/ask` endpoint requires Azure OpenAI credentials. Ensure `AZURE_OPENAI_KEY` and `AZURE_OPENAI_ENDPOINT` are set in your `.env` file with valid values.

### Chatbot UI not loading

The UI is served from the `ui/` directory mounted into the container. Ensure the `ui/` directory exists and contains `index.html`, `app.js`, `api.js`, `markdown.js`, and `style.css`.

## License

Proprietary — internal use only.

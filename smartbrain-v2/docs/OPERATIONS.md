# SmartBrain V2 — Operations Guide

How to start, stop, ingest data, update data, and query the system.

---

## Prerequisites

- Python 3.11+
- Docker + Docker Compose
- `.env` file with Azure OpenAI creds, Jira/Confluence tokens (copy from `.env.example`)

---

## 1. Starting the System

All commands run from the `smartbrain-v2/` directory.

### Start infrastructure (Neo4j + Qdrant)

```bash
./start.sh infra
```

This spins up:
- Neo4j on `localhost:7475` (browser) / `localhost:7688` (bolt)
- Qdrant on `localhost:6335` (REST) / `localhost:6336` (gRPC)

Data is stored in `./data/` (persists across restarts).

### Start the REST API

```bash
./start.sh api
```

Runs FastAPI on `localhost:8001`. Endpoints: `/v1/ask`, `/v1/search`, `/v1/services/{name}`.

### Start the MCP server (for Kiro integration)

```bash
./start.sh mcp
```

The MCP server exposes `ask_question`, `search_graph`, `get_service_info`, `get_impact` tools.

### Start everything at once

```bash
./start.sh
```

Starts infra, then API + MCP in parallel.

---

## 2. Ingesting Data (First Time)

When your Neo4j and Qdrant are empty and you want to populate them from scratch.

### Full clean ingest (recommended for first setup)

```bash
python -m ingestion.run_sync --clean
```

**What this does:**
1. Reads all 126 steering files from `kiro_steering/` directory
2. Fetches pages from configured Confluence spaces
3. Fetches tickets from configured Jira projects
4. Chunks each item into 200-500 token pieces (semantic splitting at headings)
5. Embeds each chunk (Azure OpenAI text-embedding-3-small)
6. Checks for near-duplicates (cosine > 0.95 → marks as duplicate)
7. Writes everything to: Neo4j (Service nodes, Chunk nodes, edges) + Qdrant (vectors) + BM25 index
8. Runs deterministic relationship extraction (DOCUMENTED_IN, OWNED_BY, etc.)
9. Runs LLM relationship extraction (DEPENDS_ON between services, LINKED_TO from tickets)
10. Prints a per-source report at the end

### Phase control — skip to a specific phase

If Phase 1 already completed (data is in Neo4j/Qdrant), you can skip directly to Phase 2 or 3:

```bash
# Skip to Phase 2 (deterministic edges) + Phase 3 (LLM enrichment)
python -m ingestion.run_sync --clean --phase 2

# Skip directly to Phase 3 (LLM enrichment only)
python -m ingestion.run_sync --clean --phase 3
```

When starting from Phase 2 or 3, the pipeline rebuilds the Known_Entity_Set by:
- Reading service names from `kiro_steering/` on disk
- Fetching ticket keys from Jira API

No re-embedding, no re-writing to Qdrant/BM25. Just rebuilds the in-memory state needed for LLM extraction.

### Source filtering — ingest only what changed

If you only updated steering files and don't want to re-fetch Confluence/Jira:

```bash
# Only ingest steering files (skip confluence + jira entirely)
python -m ingestion.run_sync --clean --source steering

# Only re-ingest Jira tickets
python -m ingestion.run_sync --clean --source jira

# Only re-ingest Confluence pages
python -m ingestion.run_sync --clean --source confluence
```

When `--source steering` is used:
- Phase 1 only processes steering files (fast, no API calls to Atlassian)
- Phase 3 only runs LLM on steering docs (no Jira tickets sent to GPT-4o)

### LLM ticket limit

By default, only the **100 most recent Jira tickets** are sent through GPT-4o for relationship extraction. **All steering docs always go through LLM** (no limit on steering — they're the highest signal source). The limit only affects Jira.

```bash
# Default: 100 tickets through LLM (all remain searchable)
python -m ingestion.run_sync --clean

# Send 200 tickets through LLM
python -m ingestion.run_sync --clean --llm-ticket-limit 200

# Skip Jira LLM extraction entirely (only steering gets LLM edges)
python -m ingestion.run_sync --clean --llm-ticket-limit 0

# Send ALL tickets through LLM (expensive, slow)
python -m ingestion.run_sync --clean --llm-ticket-limit 99999
```

### Examples — common scenarios

```bash
# First time setup (everything from scratch)
python -m ingestion.run_sync --clean

# Phase 1 was interrupted, restart it
python -m ingestion.run_sync --clean
# (idempotent — already-written data is skipped via MERGE)

# Phase 1 done, run Phase 2+3 with limit
python -m ingestion.run_sync --clean --phase 2

# Only re-run LLM extraction (e.g., after fixing a prompt)
python -m ingestion.run_sync --clean --phase 3 --llm-ticket-limit 50

# Full run with debug logs visible
python -m ingestion.run_sync --clean --verbose
```

**Progress bar:** By default, only a clean cumulative progress bar is displayed:

```
🚀 Clean ingest starting — 716 items to process (steering + confluence + jira)

[  5/716]   0.7%  steering: Catalog-Scheduler/tech — 6 chunks ✓  (ETA 90m40s)
[ 47/716]   6.6%  confluence: DEV/Onboarding Guide — 3 chunks ✓  (ETA 78m12s)
[130/716]  18.2%  jira: ACV2-1234: Fix payment timeout — 2 chunks ✓  (ETA 55m08s)
  └─ steering done: 42 items, 312 chunks total [45.2s elapsed]
  └─ confluence done: 85 items, 210 chunks total [120.8s elapsed]
  └─ jira done: 589 items, 602 chunks total [480.1s elapsed]

✅ Phase 1 complete: 716/716 items processed in 480.1s

🧠 Phase 3: LLM enrichment — 226 items to extract
  ℹ Limiting Jira LLM extraction to 100 tickets (of 8453 total). All tickets remain searchable.
[ 1/226]   0.4%  llm/steering: booking-crud-services — 4 edges
[127/226]  56.2%  llm/jira: CCP4-350 — 2 edges
```

**Verbose mode:** To see full debug logs (httpx, neo4j, embedding calls):

```bash
python -m ingestion.run_sync --clean --verbose
```

### Pipeline phases explained

| Phase | What it does | Duration | Costs $ |
|---|---|---|---|
| **Phase 1** | Chunk + embed + write to Qdrant, BM25, Neo4j (nodes + structural edges) | ~30-60 min | Embedding API (~$0.01) |
| **Phase 2** | Count deterministic edges (future: rule-based extraction) | Seconds | Free |
| **Phase 3** | GPT-4o reads docs → creates DEPENDS_ON / LINKED_TO edges in Neo4j | ~10-40 min | GPT-4o tokens (~$2-5) |

**When to use:** First time setup, or when you want to blow away everything and rebuild from scratch.

**Requirements:** Neo4j + Qdrant running, `.env` with Azure OpenAI key.

---

## 3. Updating Data

### Scenario: You added/changed steering files

If you edited files in `kiro_steering/booking-crud-services/tech.md` or added a new repo folder:

```bash
python -m ingestion.run_sync --clean
```

The pipeline is **idempotent** — unchanged files are skipped (via text_hash comparison), only changed/new files are re-processed. So re-running `--clean` is safe and only does work for what changed.

### Scenario: You want to pull fresh data from Jira/Confluence

```bash
python -m ingestion.run_sync
```

(Without `--clean`) This runs the incremental per-source sync:
- Fetches latest tickets from Jira (configured projects)
- Fetches latest pages from Confluence (configured spaces)
- Fetches latest PRs from GitHub (configured repos)
- Upserts everything into Neo4j + vector store

**Idempotent:** Unchanged content is skipped. Changed content is updated in-place.

### Scenario: You have existing V1 data in Neo4j and want to add V2 chunks

```bash
python -m scripts.backfill_chunks
```

**What this does:**
1. Looks in Neo4j for all existing steering doc entities (source_id starting with "steering:")
2. For each one, reads the corresponding file from `kiro_steering/`
3. Runs the V2 chunker on it → produces 200-500 token chunks
4. Embeds each chunk, checks dedup, writes chunk vectors + BM25 + graph nodes

**When to use:** You already have the V1 whole-document vectors in the DB and want to add the new chunked vectors alongside them. The `retrieval_mode=chunk` setting (default) then uses the chunks for queries.

**Options:**
```bash
python -m scripts.backfill_chunks --steering-dir kiro_steering  # explicit dir
python -m scripts.backfill_chunks --verbose                      # debug logging
```

---

## 4. Querying

Once data is ingested, you can query via:

### MCP (from Kiro IDE)

The MCP tools auto-route through the V2 pipeline:
- `ask_question("How does booking cancellation work?")` → hybrid retrieval + re-ranking + citations
- `search_graph("payment service")` → BM25 + dense fused search

### REST API

```bash
# Ask a question
curl http://localhost:8001/v1/ask -d '{"question": "What services depend on tvsm-auth?"}' -H "Content-Type: application/json"

# Search
curl "http://localhost:8001/v1/search?q=booking+cancellation&limit=5"
```

### What the V2 pipeline does on each query

```
Question
  → Check result cache (hit? return instantly)
  → Check embedding cache (hit? skip embedding API call)
  → Embed the question (Azure OpenAI)
  → Hybrid search: dense vectors + BM25 keywords → fuse via RRF → top-30
  → Re-rank with cross-encoder → top-5 most relevant chunks
  → Expand graph neighborhood (1-2 hops from parent docs)
  → Build [ref:N] annotated context
  → Call GPT-4o with context + question
  → Map citations to structured objects
  → Cache the result (1h) and embedding (24h)
  → Return answer + citations
```

---

## 5. Configuration

Key settings in `.env` (or environment variables):

| Variable | Default | What it controls |
|---|---|---|
| `RETRIEVAL_MODE` | `chunk` | `chunk` = V2 pipeline, `document` = legacy V1 dense-only |
| `CHUNK_MIN_TOKENS` | `200` | Minimum chunk size |
| `CHUNK_MAX_TOKENS` | `500` | Maximum chunk size |
| `HYBRID_TOP_N` | `30` | How many candidates hybrid retrieval returns |
| `RERANK_TOP_K` | `5` | How many chunks the re-ranker selects for the LLM |
| `RRF_K` | `60` | RRF fusion constant |
| `DEDUP_COSINE_THRESHOLD` | `0.95` | Cosine similarity threshold for near-duplicate detection |
| `CACHE_BACKEND` | `memory` | `memory` (dev) or `redis` (prod) |
| `EMBEDDING_CACHE_TTL_SECONDS` | `86400` | Embedding cache TTL (24 hours) |
| `RESULT_CACHE_TTL_SECONDS` | `3600` | Result cache TTL (1 hour) |
| `HOT_CACHE_CAPACITY` | `500` | Max entries in the hot-embeddings LRU |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder model |
| `RERANK_TIMEOUT_MS` | `500` | Max time for re-ranking before fallback |

---

## 6. Troubleshooting

### "No results found" on queries
- Check data was ingested: `python -m ingestion.run_sync --clean`
- Check Neo4j has nodes: browse `http://localhost:7475` → run `MATCH (n) RETURN count(n)`
- Check `.env` has valid `AZURE_OPENAI_KEY` and `AZURE_OPENAI_ENDPOINT`

### Embedding errors
- Azure OpenAI rate limit → the pipeline retries 3x with backoff
- Invalid key → check `AZURE_OPENAI_KEY` in `.env`

### Stale answers (cached)
- Result cache TTL is 1h. Re-ingesting data auto-invalidates relevant caches.
- To force-clear: restart the process (in-memory cache resets)

### Docker port conflicts
- If tvsm-brain's containers are running on the default ports, smartbrain-v2 uses different ports (7475/7688/6335/8001) to avoid conflicts

---

## 7. Command Cheat Sheet

```bash
# === SETUP ===
./start.sh infra                              # Start Neo4j + Qdrant

# === FULL INGESTION (all 3 phases) ===
python -m ingestion.run_sync --clean          # Full pipeline (Phase 1→2→3), progress bar only
python -m ingestion.run_sync --clean -v       # Full pipeline with debug logs

# === SOURCE FILTERING (only ingest what changed) ===
python -m ingestion.run_sync --clean --source steering     # Steering only (no Jira/Confluence API calls)
python -m ingestion.run_sync --clean --source jira         # Jira only
python -m ingestion.run_sync --clean --source confluence   # Confluence only

# === PHASE CONTROL (skip completed phases) ===
python -m ingestion.run_sync --clean --phase 2      # Phase 2+3 only (skip ingestion)
python -m ingestion.run_sync --clean --phase 3      # Phase 3 only (LLM enrichment)

# === LLM TICKET LIMIT (steering always runs full, only Jira is capped) ===
python -m ingestion.run_sync --clean --llm-ticket-limit 200   # 200 Jira tickets through GPT-4o
python -m ingestion.run_sync --clean --llm-ticket-limit 0     # Steering LLM only, skip Jira LLM

# === COMBOS ===
python -m ingestion.run_sync --clean --source steering --phase 3   # Re-run LLM on steering only
python -m ingestion.run_sync --clean --phase 3 --llm-ticket-limit 50  # Phase 3, 50 Jira tickets

# === DAILY USE ===
./start.sh                                    # Start everything
python -m ingestion.run_sync                  # Pull latest from Jira/Confluence/GitHub

# === AFTER EDITING STEERING FILES ===
python -m ingestion.run_sync --clean --source steering   # Fast: only re-ingest steering

# === LOAD DEPENDENCY GRAPH ===
python -m ingestion.load_dependency_graph                 # Load service deps JSON into Neo4j
python -m ingestion.load_dependency_graph --dry-run       # Preview without writing
python -m ingestion.load_dependency_graph --json path.json # Custom JSON path

# === SERVICES ===
./start.sh api                                # REST API only (port 8001)
./start.sh mcp                                # MCP server only (stdio)
./start.sh bench                              # Run benchmark suite
```

---

## 8. Webhook Pipeline — Automatic Steering Updates from PRs

When a PR is pushed or merged on GitHub, the webhook pipeline automatically:
1. Receives the webhook event
2. Extracts the PR diff (changed files)
3. Sends the diff to GPT-4o which decides: "Does this code change warrant a steering file update?"
4. If yes → writes the updated steering files to `kiro_steering/{repo}/`
5. Triggers re-ingestion for the affected repo

### Setup

1. Start the webhook server:
```bash
./start.sh webhook    # Runs on port 8002
```

2. Configure your GitHub repo webhook:
   - URL: `https://your-server:8002/webhooks/steering`
   - Content type: `application/json`
   - Secret: set to match `STEERING_WEBHOOK_SECRET` in your `.env`
   - Events: Pull requests

3. Set environment variable:
```bash
STEERING_WEBHOOK_SECRET=your-shared-secret-here
```

### What happens on each PR event

| PR Action | What the pipeline does |
|---|---|
| PR opened/updated | Analyzes diff, may update steering files |
| PR merged | Analyzes diff, updates steering if needed, triggers re-ingest |
| PR closed (not merged) | Ignored |

### Response format

```json
{
  "status": "updated",
  "repo": "booking-crud-services",
  "updated_files": ["tech", "structure"],
  "reasoning": "PR adds a new Redis dependency and restructures the payment module",
  "ingestion": {"files_processed": 2, "files_skipped": 1, "chunks_created": 8}
}
```

### Files

| File | What it does |
|---|---|
| `webhook_pipeline/router.py` | FastAPI endpoint + HMAC validation + orchestration |
| `webhook_pipeline/diff_extractor.py` | Fetches PR changed files from GitHub API |
| `webhook_pipeline/llm_analyzer.py` | GPT-4o prompt that decides if/what to update |
| `webhook_pipeline/steering_writer.py` | Atomic file writer (tempfile + rename) |
| `webhook_pipeline/app.py` | Standalone FastAPI app for the webhook server |
| `shared/reingest.py` | Shared utility that triggers V2 re-ingestion |

---

## 9. Metadata Scanner — Generate Steering from GitHub Repos

Pulls repository metadata from the GitHub API (languages, contributors, README, build manifests, file tree) and generates/updates steering files.

### Usage

```bash
# Scan a single repo
python -m metadata_scanner.run --repo booking-crud-services

# Scan all configured repos (from config/mcp_servers.yaml)
python -m metadata_scanner.run --all

# Use LLM-enhanced generation (GPT-4o improves the prose)
python -m metadata_scanner.run --all --llm

# Verbose logging
python -m metadata_scanner.run --all --verbose
```

### What it does

For each repo:
1. Fetches from GitHub API (parallel calls): repo info, languages, contributors, recent commits, file tree, CODEOWNERS, README, package.json/pom.xml
2. Generates three steering files:
   - `product.md` — purpose, contributors, code owners
   - `structure.md` — directory tree, key modules, recent activity
   - `tech.md` — languages, build dependencies, config
3. Writes to `kiro_steering/{repo}/`
4. Triggers re-ingestion (chunks + embeds + writes to graph)

### Modes

| Mode | Flag | Description |
|---|---|---|
| Deterministic | (default) | Fills templates with factual metadata — fast, no API cost |
| LLM-enhanced | `--llm` | GPT-4o rewrites each file for better readability — slower, costs tokens |

### Files

| File | What it does |
|---|---|
| `metadata_scanner/run.py` | CLI entry point (argparse, orchestrates the flow) |
| `metadata_scanner/github_metadata.py` | GitHub API client (parallel fetches, error-resilient) |
| `metadata_scanner/steering_generator.py` | Renders product/structure/tech from metadata |

### Prerequisites

- `GITHUB_TOKEN` set in `.env` (needs repo read access)
- `config/mcp_servers.yaml` has repos listed under the github server config (for `--all`)

---

## 10. Complete Command Cheat Sheet

```bash
# === INFRASTRUCTURE ===
./start.sh infra                              # Start Neo4j + Qdrant
./start.sh                                    # Start everything (infra + API + MCP)
./start.sh webhook                            # Start webhook server (port 8002)

# === INGESTION — FULL PIPELINE ===
python -m ingestion.run_sync --clean          # All 3 phases (progress bar only)
python -m ingestion.run_sync --clean -v       # All 3 phases (with debug logs)

# === INGESTION — PHASE CONTROL ===
python -m ingestion.run_sync --clean --phase 2      # Skip Phase 1, run Phase 2→3
python -m ingestion.run_sync --clean --phase 3      # Skip Phase 1+2, run Phase 3 only

# === INGESTION — LLM TICKET LIMIT ===
python -m ingestion.run_sync --clean --llm-ticket-limit 200   # 200 tickets to GPT-4o
python -m ingestion.run_sync --clean --llm-ticket-limit 0     # No Jira LLM (steering only)
python -m ingestion.run_sync --clean --phase 3 --llm-ticket-limit 50  # Combo: Phase 3 + 50 limit

# === INGESTION — INCREMENTAL SYNC ===
python -m ingestion.run_sync                  # Incremental sync (live fetch all sources)

# === STANDALONE PHASE 3 (alternative) ===
python -m ingestion.run_phase3                # Phase 3 standalone (default: 100 tickets)
python -m ingestion.run_phase3 --limit 50     # 50 tickets through LLM
python -m ingestion.run_phase3 --limit 0      # Steering only

# === METADATA SCANNER ===
python -m metadata_scanner.run --all          # Scan all repos, generate steering
python -m metadata_scanner.run --repo X       # Scan one repo
python -m metadata_scanner.run --all --llm    # LLM-enhanced generation

# === AFTER EDITING STEERING FILES ===
python -m ingestion.run_sync --clean          # Re-ingest (idempotent, skips unchanged)

# === MIGRATE V1 → V2 ===
python -m scripts.backfill_chunks             # Re-chunk existing V1 docs

# === DEPENDENCY GRAPH ===
python -m ingestion.load_dependency_graph                 # Load deps JSON → Neo4j edges
python -m ingestion.load_dependency_graph --dry-run       # Preview only (no writes)

# === SERVICES ===
./start.sh api                                # REST API (port 8001)
./start.sh mcp                                # MCP server (stdio)
./start.sh webhook                            # Webhook server (port 8002)
./start.sh bench                              # Run benchmarks
```

---

## 11. Project Structure Reference

```
smartbrain-v2/
├── config/                  Settings, MCP registry
├── ingestion/               Data ingestion (clients, steering, orchestrator)
├── processing/              Chunking, embeddings, dedup, extraction
├── storage/                 Neo4j graph + vector stores
├── retrieval/               Hybrid search, re-ranking, caching, citations
├── mcp_server/              MCP tools (ask, search, impact, service_info)
├── api/                     FastAPI REST app
├── webhook_pipeline/        PR webhook → LLM → steering update → re-ingest
├── metadata_scanner/        GitHub API → steering file generation
├── shared/                  Utilities shared across pipelines (reingest)
├── scripts/                 One-off scripts (backfill, seed)
├── kiro_steering/           Steering files (input data, 42 repos × 3 files)
├── docs/                    Documentation
├── tests/                   Test suite
├── data/                    Neo4j + Qdrant persistent data (gitignored)
├── start.sh                 Unified entry point
├── docker-compose.yml       Infrastructure containers
└── .env                     Credentials (not committed)
```

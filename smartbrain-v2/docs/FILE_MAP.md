# SmartBrain V2 — File Map

Every file in the project and what it does.

---

## config/

| File | What it does |
|---|---|
| `settings.py` | All app config loaded from env vars / `.env`. Pydantic-settings model with Neo4j, Azure OpenAI, vector store, RAG tunables, webhook secret, steering dir path. |
| `mcp_servers.yaml` | Defines which GitHub repos, Jira projects, and Confluence spaces to connect to. Read by the ingestion pipeline and metadata scanner. |
| `mcp_registry.py` | Parses `mcp_servers.yaml` into typed Python objects (MCPRegistry, MCPServerConfig). |

---

## ingestion/

| File | What it does |
|---|---|
| `clean_ingest.py` | **The main V2 ingestion orchestrator.** Three-phase pipeline: materialize entities+chunks → deterministic extraction → LLM enrichment. Handles all 3 sources (steering, Confluence, Jira). |
| `run_sync.py` | CLI entry point. `--clean` → runs CleanIngestOrchestrator. Without flag → runs per-source incremental sync. |
| `orchestrator.py` | Legacy MCPOrchestrator for per-source fan-out (GitHub/Jira/Confluence). Used by incremental sync. |
| `scheduler.py` | Periodic background scheduler (triggers full_sync every N hours). |
| `retry.py` | Retry decorator with exponential backoff for API calls. |
| `webhook_adapter.py` | Old V1 webhook handler (generic entity extraction). Kept for reference; new webhook is in `webhook_pipeline/`. |
| `report.py` | IngestionReport dataclass — per-source/per-stage counts for observability. |
| `clients/github_client.py` | Async HTTP client for GitHub REST API (repos, PRs, files). |
| `clients/confluence_client.py` | Async HTTP client for Confluence REST API (pages by space, with pagination). |
| `clients/jira_client.py` | Async HTTP client for Jira REST API (issues by project, with JQL). |
| `steering/kiro_steering_ingest.py` | Reads `kiro_steering/` dir and writes steering entities to graph. Used by clean_ingest and shared/reingest. |
| `steering/steering_batch_update.py` | Batch update steering files across all repos. |
| `steering/steering_updater.py` | Single-repo steering updater (fetch + regenerate + write). |
| `steering/steering_ingest.py` | Original V1 steering ingestion script. |
| `steering/generate_steering.py` | V1 steering file generation from manifests. |
| `steering/extract_edges.py` | Extracts service dependency edges from steering file prose (regex-based). |

---

## processing/

### processing/chunking/

| File | What it does |
|---|---|
| `models.py` | Core data models: `SourceType` enum, `ChunkMetadata` dataclass, `Chunk` dataclass. |
| `base.py` | `Chunker` protocol, `get_chunker()` dispatch, `SourceDocument` input type, `make_chunk()` and `build_chunks()` helpers. |
| `tokenizer.py` | `count_tokens()`, `split_oversized()`, `merge_undersized()` — shared token math for all chunkers. |
| `markdown_chunker.py` | Splits steering files (markdown) at H1-H4 headings, prepends ancestor heading path. |
| `confluence_chunker.py` | Normalizes Confluence HTML to headings, then reuses the markdown chunker's split logic. |
| `jira_chunker.py` | Splits Jira tickets at field boundaries (summary, description, acceptance criteria, comments). |

### processing/deduplication/

| File | What it does |
|---|---|
| `dedup_service.py` | Near-duplicate detection. Compares chunk vectors by cosine similarity (>0.95 = duplicate). Authority ranking: Confluence > steering > Jira. |

### processing/embeddings/

| File | What it does |
|---|---|
| `service.py` | `EmbeddingService` — async wrapper around Azure OpenAI text-embedding-3-large. Token-aware truncation. Batch + single embedding. |

### processing/extraction/

| File | What it does |
|---|---|
| `deterministic.py` | Maps structured source data (PR fields, ticket fields, repo metadata) directly to graph entities/relationships. No LLM. |
| `llm_extractor.py` | GPT-4o-based extraction of DEPENDS_ON and DOCUMENTED_IN/LINKED_TO edges from Confluence, PRs, steering files, and Jira tickets. Grounded against known-entity whitelist. |
| `writer.py` | `GraphWriter` — coordinates idempotent writes to Neo4j + vector store. Maps `source` → `provenance`, adds `confidence` for LLM edges. |

---

## storage/

### storage/graph/

| File | What it does |
|---|---|
| `schema.py` | Neo4j schema definition: entity types (Service, Ticket, Chunk, etc.), relationship types, valid tuples, required properties, constraints. |
| `graph_store.py` | Async Neo4j driver wrapper. CRUD for entities + relationships. `get_relationships_by_provenance()` for filtered edge queries. |
| `setup_neo4j.py` | Creates Neo4j constraints and indexes on first run. |

### storage/vector/

| File | What it does |
|---|---|
| `vector_store.py` | `VectorStore` ABC with two backends: `AzureAISearchVectorStore` (prod) and `QdrantVectorStore` (dev). Stores chunk vectors with metadata. |
| `sparse_index.py` | `SparseIndex` ABC with two backends: `LocalBM25Index` (dev, rank_bm25) and `AzureSearchSparseIndex` (prod, native BM25). For keyword search. |

---

## retrieval/

### retrieval/search/

| File | What it does |
|---|---|
| `rrf.py` | Pure Reciprocal Rank Fusion function — merges dense + BM25 rankings into one. |
| `hybrid_retriever.py` | `HybridRetriever` — runs dense + sparse in parallel, fuses via RRF, returns `ScoredChunk`s. |
| `ask_pipeline.py` | **The V2 query entry point.** Full pipeline: cache → embed → hybrid → rerank → graph expand → cite → LLM → cache write. |
| `semantic_search.py` | FastAPI search endpoint (`/v1/search`). Routes through HybridRetriever when mode=chunk. |
| `graph_queries.py` | Cypher queries for graph neighborhood expansion (1-2 hops). |
| `freshness.py` | Staleness detection for entities (hours since last update). |
| `services.py` | `/v1/services/{name}` endpoint — detailed service info with deps, docs, tickets. |

### retrieval/reranking/

| File | What it does |
|---|---|
| `cross_encoder.py` | `CrossEncoderReranker` — scores (query, chunk) pairs with ms-marco-MiniLM. Fallback to hybrid top-k on failure. |

### retrieval/cache/

| File | What it does |
|---|---|
| `backends.py` | `CacheBackend` ABC + `InMemoryTTLBackend` (dev) + `RedisBackend` (prod). Byte-level key-value with TTL. |
| `query_cache.py` | `EmbeddingCache` (24h) + `ResultCache` (1h) built on top of CacheBackend. SHA-256 keyed. |
| `hot_embeddings.py` | `HotEmbeddingsCache` — LRU (500 entries) for frequently accessed entity vectors. Sub-ms lookups. |

### retrieval/citations/

| File | What it does |
|---|---|
| `citation_engine.py` | `[ref:N]` citation system: `format_context()` assigns markers, `parse_refs()` extracts them, `map_citations()` filters to used refs. |

---

## webhook_pipeline/

| File | What it does |
|---|---|
| `app.py` | Standalone FastAPI app for the webhook server (port 8002). |
| `router.py` | `POST /webhooks/steering` endpoint — HMAC validation → diff extract → LLM analyze → write → re-ingest. |
| `diff_extractor.py` | Fetches PR changed files from GitHub API. Returns `DiffResult` with file paths and patches. |
| `llm_analyzer.py` | Calls GPT-4o to decide if a PR diff requires steering updates. Prompt design + JSON parsing. |
| `steering_writer.py` | Writes steering files atomically (tempfile + os.replace). Shared by webhook and metadata scanner. |
| `README.md` | Usage docs for the webhook pipeline. |

---

## metadata_scanner/

| File | What it does |
|---|---|
| `run.py` | CLI entry: `python -m metadata_scanner.run --repo X` or `--all`. Orchestrates fetch → generate → ingest. |
| `github_metadata.py` | `MetadataFetcher` — parallel GitHub API calls for repo info, languages, contributors, commits, tree, manifests. |
| `steering_generator.py` | `SteeringGenerator` — renders product/structure/tech from metadata. Deterministic or LLM-enhanced modes. |
| `README.md` | Usage docs for the metadata scanner. |

---

## shared/

| File | What it does |
|---|---|
| `reingest.py` | `trigger_reingest(repo_name, file_types)` — re-ingests specific steering files into the graph. Used by both webhook and scanner. Idempotent via text_hash. |

---

## mcp_server/

| File | What it does |
|---|---|
| `server.py` | MCP protocol server entry point. Registers all tools. |
| `tools/ask.py` | `ask_question` tool — delegates to the V2 ask pipeline. |
| `tools/search.py` | `search_graph` tool — hybrid search via HybridRetriever. |
| `tools/impact.py` | `get_impact` tool — blast radius analysis (2-hop graph traversal). |
| `tools/service_info.py` | `get_service_info` tool — detailed service info from the graph. |

---

## api/

| File | What it does |
|---|---|
| `app.py` | FastAPI application with all REST endpoints mounted. Includes the webhook router for unified deployments. |
| `schemas.py` | Pydantic response/request models for the REST API. |

---

## scripts/

| File | What it does |
|---|---|
| `backfill_chunks.py` | Re-chunks existing steering entities in Neo4j through the V2 pipeline. For V1→V2 migration. |
| `backfill_embeddings.py` | Regenerates embeddings for entities missing vectors. |
| `cleanup_old_steering.py` | Removes stale/orphaned steering nodes from the graph. |
| `seed_import.sh` | Imports a Neo4j seed dump (cypher) into a fresh database. |

---

## analysis/

| File | What it does |
|---|---|
| `scanner.py` | Full static analysis: clones repos, runs language extractors, outputs YAML manifests. |
| `steering_generator.py` | V1 steering file renderer from manifests (kept for reference; metadata_scanner/ is the V2 version). |
| `github_fetcher.py` | V1 GitHub file fetcher (used by scanner). |
| `clone_repos.py` | Clones configured repos to a local temp dir for analysis. |
| `collect_steering.py` | Collects generated steering files into the kiro_steering/ folder. |
| `extractors/base.py` | Base class for language-specific code extractors. |
| `extractors/common.py` | Common extraction logic (git activity, key modules). |
| `extractors/node_nestjs.py` | NestJS/Node.js project extractor. |
| `extractors/java_spring.py` | Java/Spring Boot project extractor. |
| `extractors/dotnet.py` | .NET/C# project extractor. |
| `models/manifest.py` | ServiceManifest data model (output of the scanner). |

---

## Root files

| File | What it does |
|---|---|
| `start.sh` | Unified startup script. Commands: infra, api, mcp, webhook, ingest, bench, all. |
| `docker-compose.yml` | Neo4j + Qdrant + API containers. Ports: 7475/7688/6335/8001. |
| `Dockerfile` | Container image for the API service. |
| `pyproject.toml` | Python project config (dependencies, build, pytest, ruff, mypy). |
| `.env` | Credentials and configuration (not committed). |
| `.env.example` | Template showing all available env vars. |
| `.gitignore` | Ignores data/, .env, __pycache__, etc. |
| `.python-version` | Pins Python 3.11. |
| `README.md` | Project overview and quick start. |

---

## Data directories (gitignored, runtime)

| Directory | What it contains |
|---|---|
| `kiro_steering/` | 42 repos × 3 steering files (product/structure/tech). Input for ingestion. |
| `generated_steering/` | V1 generated steering output (kept for reference). |
| `data/` | Neo4j database + Qdrant vectors + BM25 index (persisted across restarts). |
| `steering-lite/` | Lightweight steering MCP server + benchmarks (self-contained). |
| `ui/` | Simple chatbot HTML/JS UI. |

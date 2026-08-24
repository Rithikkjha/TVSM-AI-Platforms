# Engineering Memory Graph — MCP Server

An MCP (Model Context Protocol) server that exposes the engineering knowledge graph to AI assistants like Kiro, Claude Desktop, and Cursor.

## What It Does

This MCP server gives AI assistants direct access to your organization's engineering knowledge:

- **42 services** with code-derived steering (tech stack, structure, product context)
- **Service dependencies** (who calls whom, service bus topics)
- **Jira tickets and epics** linked to services
- **Confluence documentation** linked to services
- **GitHub repos, PRs, and contributors**

All queryable through 4 tools via natural language or structured lookups.

---

## Tools

| Tool | What it does | Example |
|------|-------------|---------|
| `ask_question` | Natural language Q&A (GraphRAG) | "What services depend on tvsm-auth?" |
| `search_graph` | Semantic vector search | "Find services related to payments" |
| `get_service_info` | Detailed service lookup | Get deps, owners, tickets, docs for a service |
| `get_impact` | Blast radius analysis | "What breaks if notification-service goes down?" |

---

## How It Works (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│  AI Assistant (Kiro / Claude Desktop / Cursor)               │
│  Sends tool calls via MCP protocol (stdio JSON-RPC)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  src/mcp_server/server.py (FastMCP)                          │
│                                                              │
│  Registers 4 tools:                                          │
│  ├── ask_question      → tools/ask.py                        │
│  ├── search_graph      → tools/search.py                     │
│  ├── get_service_info  → tools/service_info.py               │
│  └── get_impact        → tools/impact.py                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Shared Query Layer (src/query/, src/models/, src/extraction/)│
│                                                              │
│  ├── Neo4j (graph DB)     — service nodes, relationships     │
│  ├── Qdrant (vector DB)   — semantic embeddings (1536-dim)   │
│  └── Azure OpenAI         — embeddings + LLM (GPT-4o)        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow for `ask_question`

```
Question: "What tech stack does booking-service use?"
    │
    ├─1─▶ Azure OpenAI: embed question → 1536-dim vector
    │
    ├─2─▶ Qdrant: vector search → finds steering:booking-crud-services:tech
    │
    ├─3─▶ Neo4j: expand graph neighborhood (1-2 hops)
    │     → finds related services, deps, tickets, docs
    │
    ├─4─▶ Assemble context (entities + neighbors, token budget)
    │
    ├─5─▶ Azure OpenAI GPT-4o: system prompt + context + question
    │
    └─6─▶ Return grounded answer with citations
```

### Data Flow for `search_graph`

```
Query: "payment processing"
    │
    ├─1─▶ Azure OpenAI: embed query → 1536-dim vector
    │
    └─2─▶ Qdrant: cosine similarity search → top-K results
         → returns source_ids + scores
```

### Data Flow for `get_service_info`

```
Name: "booking-crud-services"
    │
    └───▶ Neo4j Cypher queries:
          ├── MATCH (s:Service {name: $name})
          ├── (s)-[:OWNED_BY]->(t:Team)
          ├── (s)-[:DEPENDS_ON]->(upstream:Service)
          ├── (downstream:Service)-[:DEPENDS_ON]->(s)
          ├── (ticket:Ticket)-[:LINKED_TO]->(s)
          └── (s)-[:DOCUMENTED_IN]->(doc:ConfluencePage)
```

### Data Flow for `get_impact`

```
Name: "tvsm-auth"
    │
    └───▶ Neo4j BFS traversal (up to 2 hops):
          MATCH path = (affected:Service)-[:DEPENDS_ON*1..2]->(s:Service {name: $name})
          → returns all affected services + their linked tickets/epics
```

---

## Folder Structure

```
src/mcp_server/
├── __init__.py              ← Package docs + architecture overview
├── server.py                ← FastMCP server (entry point, tool registrations)
├── README.md                ← This file
└── tools/
    ├── __init__.py          ← Package docs
    ├── ask.py               ← ask_question implementation (GraphRAG pipeline)
    ├── search.py            ← search_graph implementation (vector search)
    ├── service_info.py      ← get_service_info implementation (Neo4j traversal)
    └── impact.py            ← get_impact implementation (BFS blast radius)
```

**Shared modules used by the tools:**

```
src/config/settings.py       ← All env vars (Neo4j, Azure OpenAI, Qdrant)
src/models/graph_store.py    ← Neo4j async driver wrapper
src/models/vector_store.py   ← Qdrant client (vector upsert/search/delete)
src/extraction/embeddings.py ← Azure OpenAI embedding generation
src/query/graph_queries.py   ← Reusable Cypher query helpers
src/query/freshness.py       ← Staleness detection
```

---

## Configuration

### Prerequisites

- Docker running with `docker compose up -d` (Neo4j + Qdrant)
- `.env` file with Azure OpenAI credentials (same as the REST API)
- Python 3.11+ with project installed (`pip install -e ".[dev]"`)

### Kiro Configuration

Add to `.kiro/settings/mcp.json` (workspace level) or `~/.kiro/settings/mcp.json` (user level):

```json
{
  "mcpServers": {
    "engineering-memory-graph": {
      "command": "python3.11",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/tvsm-brain",
      "env": {
        "PYTHONPATH": "/path/to/tvsm-brain"
      },
      "disabled": false,
      "autoApprove": [
        "ask_question",
        "search_graph",
        "get_service_info",
        "get_impact"
      ]
    }
  }
}
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "engineering-memory-graph": {
      "command": "python3.11",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/tvsm-brain"
    }
  }
}
```

---

## Testing

### Quick test (stdio mode)

```bash
cd /path/to/tvsm-brain
python3.11 -m src.mcp_server.server
```

The server will start and wait for MCP protocol messages on stdin. Press Ctrl+C to stop.

### Test with MCP inspector

```bash
npx @modelcontextprotocol/inspector python3.11 -m src.mcp_server.server
```

This opens a web UI where you can call tools interactively.

---

## How the Knowledge Graph Was Built

```
1. GitHub API → repos, PRs, contributors → Neo4j + Qdrant
2. Jira API → tickets, epics → Neo4j + Qdrant
3. Confluence API → wiki pages → Neo4j + Qdrant
4. Kiro → generated .kiro/steering/ (product.md, structure.md, tech.md) per repo
5. collect_steering → gathered into kiro_steering/{repo}/
6. kiro_steering_ingest → 3 nodes per service in Neo4j + 3 embeddings in Qdrant
```

Total: ~42 services × 3 steering files + Confluence pages + Jira tickets + GitHub PRs = rich, searchable knowledge graph.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEO4J_URI` | Yes | `bolt://localhost:7687` (Docker) |
| `NEO4J_USER` | Yes | `neo4j` |
| `NEO4J_PASSWORD` | Yes | `neo4jpassword` |
| `AZURE_OPENAI_KEY` | Yes | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O` | Yes | GPT-4o deployment name |
| `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` | Yes | Embedding model deployment |
| `AZURE_OPENAI_API_VERSION` | Yes | API version (e.g. `2025-01-01-preview`) |
| `QDRANT_URL` | Yes | `http://localhost:6333` (Docker) |
| `EMBEDDING_DIMENSION` | No | `1536` (default, matches text-embedding-3-small) |

# Steering Lite - Lightweight MCP Server + Evaluation Bench

A zero-infra MCP server that serves raw steering files directly to AI assistants.
No Neo4j, no Qdrant, no Azure OpenAI needed. The calling LLM (Kiro/Claude) does
all the reasoning itself using the raw markdown content.

## Folder Structure

```
steering-lite/
├── README.md                    ← This file
├── global_steering/             ← Combined steering (master docs)
│   ├── index.md                 ← Service index (names, one-liners, categories)
│   ├── services/                ← Per-service merged steering (product+structure+tech)
│   │   ├── booking-crud-services.md
│   │   ├── tvsm-auth.md
│   │   ├── notification-service.md
│   │   └── ...
│   └── dependencies.md          ← Cross-service dependency map
├── mcp_server/                  ← Lightweight MCP server (no DB, no LLM)
│   ├── __init__.py
│   └── server.py                ← FastMCP with file-serving tools
├── bench/                       ← SWE Bench for evaluation
│   ├── questions.yaml           ← 30 test questions (easy/medium/hard)
│   ├── run_bench.py             ← Runner that tests both MCP servers
│   └── results/                 ← Evaluation results
└── scripts/
    └── build_global_steering.py ← Generates global_steering/ from kiro_steering/
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  AI Assistant (Kiro / Claude)                            │
│  ↕ MCP protocol (stdio)                                 │
├─────────────────────────────────────────────────────────┤
│  steering-lite/mcp_server/server.py                      │
│  Tools:                                                  │
│  ├── list_services()        → returns service index      │
│  ├── get_service(name)      → returns full merged .md    │
│  ├── get_dependencies()     → returns dependency map     │
│  └── search_services(query) → keyword search across all  │
├─────────────────────────────────────────────────────────┤
│  steering-lite/global_steering/ (just files on disk)     │
│  No Neo4j. No Qdrant. No Azure OpenAI. Just markdown.    │
└─────────────────────────────────────────────────────────┘
```

## Comparison: Full Brain vs Steering Lite

| | Full Brain (src/mcp_server/) | Steering Lite |
|---|---|---|
| Infra | Docker + Neo4j + Qdrant + Azure OpenAI | Nothing |
| Cost per query | ~$0.01-0.05 | $0 |
| Setup | 5 min | 0 min (just add MCP config) |
| Dependency traversal | ✅ (graph BFS) | ⚠️ (from dependencies.md) |
| Semantic search | ✅ (vector similarity) | ⚠️ (keyword only) |
| Works offline | ❌ | ✅ |
| Jira/Confluence data | ✅ | ❌ |
| Scales to 100+ services | ✅ | ⚠️ (context window) |

## Usage

```bash
# Build global steering from kiro_steering/
python steering-lite/scripts/build_global_steering.py

# Run the lightweight MCP server
python -m steering-lite.mcp_server.server

# Run the benchmark
python steering-lite/bench/run_bench.py
```

## MCP Config (Kiro)

```json
{
  "mcpServers": {
    "steering-lite": {
      "command": "python3.11",
      "args": ["-m", "steering-lite.mcp_server.server"],
      "cwd": "/path/to/tvsm-brain",
      "disabled": false,
      "autoApprove": ["list_services", "get_service", "get_dependencies", "search_services"]
    }
  }
}
```

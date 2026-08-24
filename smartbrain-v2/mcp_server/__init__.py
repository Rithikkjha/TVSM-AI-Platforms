"""MCP Server for the Engineering Memory Graph.

This package exposes the knowledge graph as a Model Context Protocol server,
allowing AI assistants (Kiro, Claude, etc.) to query service information,
search the graph, and ask natural language questions — all through MCP tools.

Architecture:
    src/mcp_server/
    ├── __init__.py          ← This file (package marker)
    ├── server.py            ← FastMCP server definition + tool registrations
    ├── tools/
    │   ├── __init__.py
    │   ├── ask.py           ← ask_question tool (GraphRAG NL query)
    │   ├── search.py        ← search_graph tool (semantic vector search)
    │   ├── service_info.py  ← get_service_info tool (service detail)
    │   └── impact.py        ← get_impact tool (blast radius analysis)
    └── README.md            ← How to configure and use this MCP server

How it works:
    The MCP server wraps the same query layer used by the REST API (FastAPI).
    It connects to Neo4j (graph) and Qdrant (vectors) directly, and calls
    Azure OpenAI for embeddings and LLM answers.

    ┌─────────────────────────────────────────────────┐
    │  AI Assistant (Kiro / Claude / etc.)             │
    │  ↕ MCP protocol (stdio or SSE)                  │
    ├─────────────────────────────────────────────────┤
    │  src/mcp_server/server.py (FastMCP)             │
    │  ├── ask_question()     → GraphRAG pipeline     │
    │  ├── search_graph()     → Vector similarity     │
    │  ├── get_service_info() → Neo4j traversal       │
    │  └── get_impact()       → BFS dependency graph  │
    ├─────────────────────────────────────────────────┤
    │  src/query/             (shared query layer)     │
    │  src/extraction/        (embeddings)             │
    │  src/models/            (Neo4j + Qdrant stores)  │
    └─────────────────────────────────────────────────┘

Running:
    # stdio mode (for IDE integration like Kiro)
    python -m src.mcp_server.server

    # Or via the mcp CLI
    mcp run src/mcp_server/server.py
"""

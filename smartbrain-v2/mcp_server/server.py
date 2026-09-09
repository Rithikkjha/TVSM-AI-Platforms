"""Engineering Memory Graph — MCP Server.

This is the main entry point for the MCP server. It exposes the knowledge
graph through 4 tools that AI assistants can call:

Tools:
    1. ask_question      — Natural language Q&A (GraphRAG pipeline)
    2. search_graph      — Semantic vector search across all entities
    3. get_service_info  — Detailed service info (deps, owners, docs, tickets)
    4. get_impact        — Blast radius analysis (what breaks if X goes down)

Running:
    # stdio mode (for IDE integration — Kiro, Claude Desktop, etc.)
    python -m src.mcp_server.server

    # The server communicates over stdin/stdout using the MCP protocol.
    # Configure it in your IDE's mcp.json (see README.md for examples).

Architecture:
    This server is a thin MCP wrapper around the existing query layer.
    It reuses the same Neo4j, Qdrant, and Azure OpenAI connections that
    the REST API uses. No data duplication — same brain, different interface.

    ┌──────────────────────────────────────────────────────────┐
    │  IDE (Kiro / Claude Desktop / Cursor)                     │
    │  ↕ stdio (JSON-RPC over MCP protocol)                    │
    ├──────────────────────────────────────────────────────────┤
    │  THIS FILE — FastMCP server                               │
    │  Registers 4 tools, delegates to src/mcp_server/tools/    │
    ├──────────────────────────────────────────────────────────┤
    │  src/query/          — Graph queries (Cypher)              │
    │  src/extraction/     — Embedding generation               │
    │  src/models/         — Neo4j driver + Qdrant client        │
    │  src/config/         — Settings from .env                  │
    └──────────────────────────────────────────────────────────┘

Environment:
    Requires the same .env as the REST API:
    - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    - AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT
    - AZURE_OPENAI_DEPLOYMENT_GPT4O, AZURE_OPENAI_DEPLOYMENT_EMBEDDING
    - QDRANT_URL
"""

from __future__ import annotations

import logging
import os
import sys

# Ensure the project root is on sys.path so `src.*` imports work
# when running as `python -m src.mcp_server.server` from the project root.
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Load .env before any settings are read
from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Import tool implementations
from mcp_server.tools.ask import ask_question as _ask_question
from mcp_server.tools.impact import get_impact as _get_impact
from mcp_server.tools.search import search_graph as _search_graph
from mcp_server.tools.service_info import get_service_info as _get_service_info

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,  # MCP uses stdout for protocol; logs go to stderr
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Server definition
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Engineering Memory Graph",
    instructions=(
        "Knowledge graph of engineering systems — services, dependencies, "
        "teams, tickets, and documentation. Ask questions, search, get "
        "service details, or analyze blast radius."
    ),
    # Stateless Streamable HTTP (2026-07-28 spec): no persistent sessions,
    # so the server can be mounted into the FastAPI app and survives restarts.
    stateless_http=True,
    # Behind nginx the Host header is the public domain (smartbrain.tvsmotor.net),
    # which the Streamable HTTP transport rejects by default via DNS-rebinding
    # protection ("Invalid Host header"). nginx is the trusted front door and MCP
    # clients (Kiro/Claude) are not browsers, so we disable that check. To keep it
    # enabled instead, set allowed_hosts/allowed_origins to the public domain.
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


# ---------------------------------------------------------------------------
# Tool registrations — NEW PRIMITIVE TOOLS (Cerebras-style)
# ---------------------------------------------------------------------------


@mcp.tool()
async def ask_question(question: str) -> str:
    """Ask a natural language question about the engineering systems.

    Uses GraphRAG (vector search + graph traversal + LLM) to answer
    questions grounded in real data from GitHub, Jira, Confluence,
    and code-derived steering files.

    Examples:
        - "What services depend on tvsm-auth?"
        - "How does the booking flow work?"
        - "What tech stack does notification-service use?"
        - "Who works on the payment system?"
        - "What's the architecture of the Parts Catalogue?"

    Args:
        question: Your question about the engineering systems.

    Returns:
        A detailed answer with citations to source entities.
    """
    import json
    result = await _ask_question(question)
    if result.get("error"):
        return f"Error: {result['error']}"
    if result.get("answer"):
        return result["answer"]
    return result.get("message", "No answer available.")


@mcp.tool()
async def search(query: str, repo_filter: str = "", doc_type: str = "", limit: int = 5) -> str:
    """Search the knowledge base for relevant chunks. Returns raw evidence (no LLM synthesis).

    Use this to retrieve specific information from a service's documentation.
    Call multiple times with different repo_filter values to gather context
    from multiple services before synthesizing an answer yourself.

    Examples:
        - query="database connection", repo_filter="booking-crud-services"
        - query="payment gateway integration", repo_filter="payment-service"
        - query="authentication middleware" (no filter — searches all)

    Args:
        query: What you're looking for (natural language).
        repo_filter: Optional — scope to one service's docs only.
        doc_type: Optional — filter by type: tech, product, structure, confluence, jira.
        limit: Number of chunks to return (1-10, default 5).

    Returns:
        List of relevant text chunks with scores and source references.
    """
    import json
    from retrieval.search.primitives import search as _search

    chunks = await _search(
        query=query,
        repo_filter=repo_filter.strip() or None,
        doc_type=doc_type.strip() or None,
        limit=min(limit, 10),
    )
    return json.dumps({"chunks": chunks, "count": len(chunks)}, indent=2)


@mcp.tool()
async def get_service_chain(service: str, direction: str = "downstream", hops: int = 2) -> str:
    """Get the dependency chain from a service via graph traversal.

    Use this to understand what services are connected before doing
    targeted searches on each one.

    Examples:
        - service="booking-crud-services", direction="downstream"
          → what booking depends on
        - service="tvsm-auth", direction="upstream"
          → what depends on auth
        - service="payment-service", direction="both"
          → full picture

    Args:
        service: The service name to start from.
        direction: "downstream" (what it depends on), "upstream" (what depends on it), "both".
        hops: Max traversal depth (1-3, default 2).

    Returns:
        Ordered list of connected services with relationship type and hop distance.
    """
    import json
    from retrieval.search.primitives import get_service_chain as _get_chain

    chain = await _get_chain(service=service, direction=direction, hops=min(hops, 3))
    return json.dumps({"root": service, "direction": direction, "chain": chain, "count": len(chain)}, indent=2)


@mcp.tool()
async def get_service_info(name: str) -> str:
    """Get detailed information about a specific service.

    Returns the service's properties, owners, upstream/downstream
    dependencies, linked Jira tickets, and documentation (Confluence
    pages + steering files).

    Examples:
        - name="booking-crud-services"
        - name="tvsm-auth"
        - name="notification-service"

    Args:
        name: The service name (case-sensitive, as it appears in the graph).

    Returns:
        Detailed service information including deps, owners, tickets, and docs.
    """
    import json
    result = await _get_service_info(name)
    if result.get("error"):
        return f"Error: {result.get('message', result['error'])}"
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def get_impact(name: str) -> str:
    """Analyze the blast radius if a service goes down or changes.

    Traverses the dependency graph (up to 2 hops) to find all services
    that depend on the given service, plus any linked epics and tickets
    that would be affected.

    Examples:
        - name="tvsm-auth" → shows all services that use auth
        - name="Payment-Service" → shows what breaks if payments fail
        - name="notification-service" → shows who depends on notifications

    Args:
        name: The service name to analyze impact for.

    Returns:
        List of affected services (with hop distance), linked epics, and tickets.
    """
    import json
    result = await _get_impact(name)
    if result.get("error"):
        return f"Error: {result.get('message', result['error'])}"
    return json.dumps(result, indent=2, default=str)


# ---------------------------------------------------------------------------
# OLD TOOLS — commented out to avoid confusing Kiro
# These are superseded by the primitives above (search + get_service_chain)
# ---------------------------------------------------------------------------

# @mcp.tool()
# async def search_graph(query: str, entity_type: str = "", limit: int = 10) -> str:
#     """Search the knowledge graph using semantic similarity.
#     REPLACED BY: search() — which supports repo_filter and returns chunks.
#     """
#     import json
#     etype = entity_type.strip() if entity_type else None
#     if etype == "":
#         etype = None
#     result = await _search_graph(query, entity_type=etype, limit=limit)
#     if result.get("error"):
#         return f"Error: {result['error']}"
#     return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Engineering Memory Graph MCP Server (stdio mode)")
    mcp.run()

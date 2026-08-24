"""Steering Lite MCP Server — zero-infra knowledge serving.

A lightweight MCP server that serves engineering knowledge directly from
markdown files. No Neo4j, no Qdrant, no Azure OpenAI, no Docker needed.
The calling LLM (Kiro/Claude) does all the reasoning itself.

Tools:
    1. list_services    — Returns the service index (names + one-liners)
    2. get_service      — Returns full steering content for one service
    3. get_dependencies — Returns the cross-service dependency map
    4. search_services  — Keyword search across all service files

Running:
    python -m steering-lite.mcp_server.server

Architecture:
    ┌─────────────────────────────────────────────────┐
    │  AI Assistant (Kiro / Claude)                     │
    │  Does ALL the reasoning over raw content         │
    │  ↕ MCP protocol (stdio)                         │
    ├─────────────────────────────────────────────────┤
    │  This server (FastMCP)                           │
    │  Just reads files and returns content            │
    │  No LLM, no DB, no embeddings                   │
    ├─────────────────────────────────────────────────┤
    │  steering-lite/global_steering/ (markdown files)  │
    │  ├── index.md                                    │
    │  ├── dependencies.md                             │
    │  └── services/*.md                               │
    └─────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Ensure project root is on path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GLOBAL_STEERING_DIR = Path(_project_root) / "steering-lite" / "global_steering"
SERVICES_DIR = GLOBAL_STEERING_DIR / "services"

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Steering Lite",
    instructions=(
        "Lightweight engineering knowledge server. Serves raw steering docs "
        "for 42+ microservices. No database needed — just file reads. "
        "Use list_services to discover services, get_service for details, "
        "get_dependencies for cross-service relationships, and search_services "
        "to find services by keyword."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_services() -> str:
    """List all known services with one-line summaries.

    Returns the service index — names, summaries, and file links
    for all 42+ services in the engineering org.

    Use this first to discover what services exist before diving into details.

    Returns:
        Markdown table with service names and one-line descriptions.
    """
    index_path = GLOBAL_STEERING_DIR / "index.md"
    if not index_path.exists():
        return "Error: index.md not found. Run build_global_steering.py first."
    return index_path.read_text(encoding="utf-8")


@mcp.tool()
async def get_service(name: str) -> str:
    """Get complete steering documentation for a specific service.

    Returns the FULL content — product context, code structure, tech stack,
    API endpoints, dependencies, configuration, and deployment info.
    Nothing is summarized or truncated.

    Examples:
        - name="booking-crud-services"
        - name="tvsm-auth"
        - name="notification-service"

    Args:
        name: Service name (case-sensitive, must match the file name).

    Returns:
        Full markdown content of the service's steering documentation.
    """
    if not name or not name.strip():
        return "Error: Service name must not be empty."

    service_path = SERVICES_DIR / f"{name}.md"
    if not service_path.exists():
        # Try case-insensitive match
        available = [f.stem for f in SERVICES_DIR.glob("*.md")]
        matches = [s for s in available if s.lower() == name.lower()]
        if matches:
            service_path = SERVICES_DIR / f"{matches[0]}.md"
        else:
            # Fuzzy suggestion
            close = [s for s in available if name.lower() in s.lower()]
            suggestion = f" Did you mean: {', '.join(close[:5])}?" if close else ""
            return f"Error: Service '{name}' not found.{suggestion}\nAvailable: {', '.join(available[:10])}..."

    return service_path.read_text(encoding="utf-8")


@mcp.tool()
async def get_dependencies() -> str:
    """Get the cross-service dependency map.

    Shows which services call which other services (HTTP calls),
    and the Service Bus topology (who publishes/subscribes to what topics).

    Use this to understand how services are connected and what the
    blast radius of a change might be.

    Returns:
        Markdown document with dependency tables and topology.
    """
    deps_path = GLOBAL_STEERING_DIR / "dependencies.md"
    if not deps_path.exists():
        return "Error: dependencies.md not found. Run build_global_steering.py first."
    return deps_path.read_text(encoding="utf-8")


@mcp.tool()
async def search_services(query: str) -> str:
    """Search across all service documentation by keyword.

    Performs a case-insensitive keyword search across all service files.
    Returns matching service names and the lines containing the match.

    Useful when you don't know the exact service name but know a keyword
    like "payment", "booking", "auth", "notification", etc.

    Examples:
        - query="payment" → finds PaymentService, booking-crud-services (payment integration)
        - query="NestJS" → finds all NestJS services
        - query="MongoDB" → finds services using MongoDB

    Args:
        query: Keyword to search for (case-insensitive).

    Returns:
        List of matching services with relevant lines.
    """
    if not query or not query.strip():
        return "Error: Query must not be empty."

    query_lower = query.lower().strip()
    results: list[str] = []

    if not SERVICES_DIR.exists():
        return "Error: services/ directory not found. Run build_global_steering.py first."

    for service_file in sorted(SERVICES_DIR.glob("*.md")):
        content = service_file.read_text(encoding="utf-8")
        if query_lower in content.lower():
            # Extract matching lines (up to 5 per service)
            matching_lines = []
            for line in content.split("\n"):
                if query_lower in line.lower() and line.strip():
                    matching_lines.append(f"  - {line.strip()[:100]}")
                    if len(matching_lines) >= 5:
                        break

            results.append(f"### {service_file.stem}\n" + "\n".join(matching_lines))

    if not results:
        return f"No services found matching '{query}'."

    header = f"# Search Results for '{query}'\n\nFound in {len(results)} service(s):\n\n"
    return header + "\n\n".join(results)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting Steering Lite MCP Server (stdio mode)")
    mcp.run()

"""FastAPI application for the Engineering Memory Graph Query API.

This module defines the main FastAPI application instance that hosts all V1
endpoints. It sets up CORS middleware, API key authentication, error handling,
and includes routers for webhooks and query endpoints.

The app is importable as ``src.query.app:app`` for use with uvicorn.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles

from config.settings import get_settings
from retrieval.search.ask_pipeline import router as ask_router
from retrieval.search.freshness import get_freshness_summary
from retrieval.search.semantic_search import router as search_router
from retrieval.search.services import router as services_router

# MCP server (stateless Streamable HTTP) — mounted at /mcp on this same app.
from mcp_server.server import mcp

logger = logging.getLogger(__name__)

# Serve the Streamable HTTP handler at the mount root so the public path is
# exactly /mcp (not /mcp/mcp). Must be set before building the sub-app.
mcp.settings.streamable_http_path = "/"
mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan: run the MCP stateless session manager alongside the API."""
    logger.info("Application starting")
    async with mcp.session_manager.run():
        yield
    logger.info("Application shutting down")


# ---------------------------------------------------------------------------
# API Key Authentication
# ---------------------------------------------------------------------------


async def verify_api_key(
    x_api_key: str | None = Header(default=None),
) -> str:
    """FastAPI dependency that validates the X-API-Key header.

    Compares the provided key against ``settings.api_key``. Returns the
    key value on success (useful for logging). Raises 401 if missing or
    invalid.
    """
    settings = get_settings()
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Invalid or missing API key"},
        )
    return x_api_key


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Engineering Memory Graph API",
    version="1.0.0",
    description=(
        "V1 pilot API for querying the engineering memory graph — "
        "a knowledge graph built from GitHub, Jira, and Confluence data."
    ),
    lifespan=lifespan,
)

# CORS middleware — allow all origins for V1 internal pilot
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions.

    Returns a structured 500 response so consumers always get JSON,
    even on unexpected failures.
    """
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# V1 query router — API key required on all routes except /v1/health
v1_router = APIRouter(prefix="/v1", tags=["v1"])


@v1_router.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint (unauthenticated).

    Returns expanded status including Neo4j connectivity, vector store
    connectivity, last sync timestamp, and freshness summary.
    """
    from neo4j import AsyncGraphDatabase as _AsyncGraphDatabase

    settings = get_settings()

    # --- Neo4j connectivity check ---
    neo4j_status = "disconnected"
    freshness: dict[str, Any] | None = None
    driver = None
    try:
        driver = _AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with driver.session() as session:
            await session.run("RETURN 1")
        neo4j_status = "connected"

        # Freshness summary (only if Neo4j is up)
        freshness = await get_freshness_summary(driver)
    except Exception:
        logger.warning("Neo4j health check failed")
    finally:
        if driver is not None:
            await driver.close()

    # --- Vector store connectivity check ---
    vector_status = "disconnected"
    try:
        if settings.azure_search_endpoint and settings.azure_search_key:
            # Azure AI Search — attempt to construct client
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient

            SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name="memory_graph_entities",
                credential=AzureKeyCredential(settings.azure_search_key),
            )
            vector_status = "connected"
        elif settings.qdrant_url:
            # Qdrant local — check if URL is configured
            vector_status = "connected"
    except Exception:
        logger.warning("Vector store health check failed")

    # --- Last sync (placeholder for V1) ---
    last_sync: str | None = None

    return {
        "status": "ok",
        "neo4j": neo4j_status,
        "vector_store": vector_status,
        "last_sync": last_sync,
        "freshness": freshness,
    }


# Authenticated V1 router for query endpoints
v1_authenticated_router = APIRouter(
    prefix="/v1",
    tags=["v1"],
    dependencies=[Depends(verify_api_key)],
)


# Placeholder authenticated endpoint for testing — will be replaced by real
# query endpoints in subsequent tasks.
@v1_authenticated_router.get("/services")
async def list_services() -> dict[str, Any]:
    """Placeholder for the services listing endpoint."""
    return {"services": []}


# Include routers
app.include_router(v1_router)
v1_authenticated_router.include_router(services_router)
v1_authenticated_router.include_router(search_router)
v1_authenticated_router.include_router(ask_router)
app.include_router(v1_authenticated_router)


# ---------------------------------------------------------------------------
# Primitive API endpoints (no LLM, for programmatic / MCP HTTP access)
# ---------------------------------------------------------------------------


@app.post("/v1/search", dependencies=[Depends(verify_api_key)])
async def primitive_search_endpoint(body: dict[str, Any]) -> dict[str, Any]:
    """POST /v1/search — Raw hybrid search primitive (no LLM synthesis).

    Returns reranked chunks matching the query. Supports filtering by
    service (repo_filter) and doc_type.

    Body:
        {
            "query": "booking cancellation refund",
            "repo_filter": "payment-service",  // optional
            "doc_type": "tech",                // optional
            "limit": 5                         // optional, default 5
        }
    """
    from retrieval.search.primitives import search

    query = body.get("query", "")
    if not query:
        return {"error": "bad_request", "message": "query is required"}

    chunks = await search(
        query=query,
        repo_filter=body.get("repo_filter"),
        doc_type=body.get("doc_type"),
        limit=body.get("limit", 5),
    )
    return {"chunks": chunks, "count": len(chunks)}


@app.get("/v1/graph/chain", dependencies=[Depends(verify_api_key)])
async def graph_chain_endpoint(
    service: str = Query(..., description="Service name"),
    direction: str = Query(default="downstream", description="downstream|upstream|both"),
    hops: int = Query(default=2, description="Max traversal depth"),
) -> dict[str, Any]:
    """GET /v1/graph/chain — Service dependency chain from graph.

    Returns the ordered dependency chain for a service.
    No LLM involved — direct Neo4j traversal.
    """
    from retrieval.search.primitives import get_service_chain

    chain = await get_service_chain(service=service, direction=direction, hops=hops)
    return {
        "root": service,
        "direction": direction,
        "hops": hops,
        "chain": chain,
        "count": len(chain),
    }


# ---------------------------------------------------------------------------
# MCP server — stateless Streamable HTTP, mounted at /mcp
# ---------------------------------------------------------------------------

# Clients (Kiro/Claude) connect to  http://<host>:8000/mcp
app.mount("/mcp", mcp_app, name="mcp")


# ---------------------------------------------------------------------------
# Static file serving — Web UI at /chatbot
# ---------------------------------------------------------------------------

app.mount("/chatbot", StaticFiles(directory="ui", html=True), name="chatbot")


# ---------------------------------------------------------------------------
# Steering Update Webhook
# ---------------------------------------------------------------------------


@app.post("/webhooks/steering-update")
async def steering_update_webhook(body: dict[str, Any]) -> JSONResponse:
    """Receive a steering update trigger from GitHub Actions.

    Expected body:
        {"repo": "booking-crud-services", "pr_number": 42}

    Runs the full pipeline: filter → classify → patch → save → ingest.
    Returns the result summary.
    """
    import asyncio
    from ingestion.steering.steering_updater import update_steering_from_pr

    repo = body.get("repo", "")
    pr_number = body.get("pr_number", 0)
    org = body.get("org", "TVSM-CS")

    if not repo or not pr_number:
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": "repo and pr_number are required"},
        )

    try:
        result = await update_steering_from_pr(org, repo, pr_number)
        return JSONResponse(status_code=200, content=result)
    except Exception as exc:
        logger.error("Steering update failed for %s PR #%d: %s", repo, pr_number, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": str(exc)},
        )


@app.post("/v1/steering/batch-update")
async def steering_batch_update_api(
    body: dict[str, Any] | None = None,
    _key: str = Depends(verify_api_key),
) -> JSONResponse:
    """Trigger a batch steering update across all repos (or a single repo).

    Scans for recently merged PRs, filters for meaningful changes,
    patches steering files, and updates the knowledge graph.

    Optional body:
        {
            "days": 7,          // look back N days (default: 7)
            "max_prs": 2,       // max PRs per repo (default: 2)
            "repo": null,       // single repo filter (default: all repos)
            "dry_run": false    // filter only, don't patch (default: false)
        }

    After completion, MCP tools immediately serve the updated data.
    Audit log written to logs/steering_update_audit.jsonl.
    """
    from ingestion.steering.steering_batch_update import run_batch_update

    if body is None:
        body = {}

    days = body.get("days", 7)
    max_prs = body.get("max_prs", 2)
    repo_filter = body.get("repo", None)
    dry_run = body.get("dry_run", False)

    try:
        result = await run_batch_update(
            days=days,
            max_prs=max_prs,
            repo_filter=repo_filter,
            dry_run=dry_run,
        )
        return JSONResponse(status_code=200, content=result)
    except Exception as exc:
        logger.error("Batch steering update failed: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": str(exc)},
        )


# Startup / shutdown are handled by the `lifespan` context above (which also
# runs the MCP stateless session manager).

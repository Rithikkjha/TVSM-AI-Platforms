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

from config.settings import get_settings
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles

# MCP server (stateless Streamable HTTP) — mounted at /mcp on this same app.
from mcp_server.server import mcp
from retrieval.search.ask_pipeline import router as ask_router
from retrieval.search.freshness import get_freshness_summary
from retrieval.search.semantic_search import router as search_router
from retrieval.search.services import router as services_router
from starlette.middleware.sessions import SessionMiddleware

from api.auth import ChatbotLoginGateMiddleware, require_login
from api.auth import router as auth_router

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
    invalid. Skipped entirely unless ``settings.require_api_key`` is True.
    """
    settings = get_settings()
    if not settings.require_api_key:
        return x_api_key or ""
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Invalid or missing API key"},
        )
    return x_api_key


# ---------------------------------------------------------------------------
# SSO / login fail-fast configuration check
# ---------------------------------------------------------------------------


def _check_login_config() -> None:
    """Fail fast at startup if login is required but misconfigured.

    When ``require_login`` is True we need the Azure app-registration values
    and a session secret. Booting without them would produce an endless
    redirect loop or an insecure (unsigned) session, so raise a clear error
    naming the missing env var(s) instead.
    """
    settings = get_settings()
    if not settings.require_login:
        return

    missing: list[str] = []
    if not settings.azure_tenant_id:
        missing.append("AZURE_TENANT_ID")
    if not settings.azure_client_id:
        missing.append("AZURE_CLIENT_ID")
    if not settings.azure_client_secret:
        missing.append("AZURE_CLIENT_SECRET")
    if not settings.session_secret:
        missing.append("SESSION_SECRET")

    if missing:
        raise RuntimeError(
            "Login is required (REQUIRE_LOGIN defaults ON) but these env vars "
            f"are missing/empty: {', '.join(missing)}. Set them in .env, or set "
            "REQUIRE_LOGIN=false to disable login (not recommended for prod)."
        )


_check_login_config()


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

# Chatbot UI login gate. Added BEFORE SessionMiddleware so that
# SessionMiddleware wraps it (Starlette runs the LAST-added middleware
# outermost) and request.session is populated when the gate runs.
app.add_middleware(ChatbotLoginGateMiddleware)

# Session middleware — signs the login session cookie with SESSION_SECRET.
# Required for the SSO auth-code flow (stores PKCE/state + the user dict).
# https_only + same_site=lax are safe behind the TLS-terminating nginx proxy.
# The secret may be empty only when login is disabled (fail-fast above would
# have raised otherwise); fall back to the api_key so SessionMiddleware still
# has a non-empty key for the login-disabled case.
_session_secret = get_settings().session_secret or get_settings().api_key
app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret,
    https_only=True,
    same_site="lax",
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


# Authenticated V1 router for query endpoints.
# Two independent gates: SSO login (require_login) and the legacy X-API-Key
# (verify_api_key). With defaults, login is required and the API key is not.
v1_authenticated_router = APIRouter(
    prefix="/v1",
    tags=["v1"],
    dependencies=[Depends(require_login), Depends(verify_api_key)],
)


# Include routers
app.include_router(auth_router)  # /auth/login, /auth/callback, /auth/logout, /auth/me
app.include_router(v1_router)
v1_authenticated_router.include_router(services_router)
v1_authenticated_router.include_router(search_router)
v1_authenticated_router.include_router(ask_router)
app.include_router(v1_authenticated_router)


# ---------------------------------------------------------------------------
# Primitive API endpoints (no LLM, for programmatic / MCP HTTP access)
# ---------------------------------------------------------------------------


@app.post("/v1/search", dependencies=[Depends(require_login), Depends(verify_api_key)])
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


@app.get("/v1/graph/chain", dependencies=[Depends(require_login), Depends(verify_api_key)])
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


# Startup / shutdown are handled by the `lifespan` context above (which also
# runs the MCP stateless session manager).

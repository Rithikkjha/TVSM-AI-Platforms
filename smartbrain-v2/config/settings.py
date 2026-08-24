"""Application settings loaded from environment variables.

Uses `pydantic-settings` so that every field is sourced from the process
environment (or a local `.env` file for development). Use `get_settings()`
to obtain a cached singleton instance instead of constructing `Settings()`
directly in application code.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed container for all application configuration.

    All fields are populated from environment variables (case-insensitive)
    or from a `.env` file at the project root. Defaults are chosen so that
    `Settings()` is constructible in a fresh environment — secrets default
    to empty strings and should be overridden in real deployments.
    """

    # --- Neo4j ------------------------------------------------------------
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4jpassword"

    # --- Azure OpenAI (LLM + embeddings) ---------------------------------
    azure_openai_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment_gpt4o: str = "gpt-4o"
    azure_openai_deployment_embedding: str = "text-embedding-3-large"
    azure_openai_api_version: str = "2024-06-01"

    # --- Vector store -----------------------------------------------------
    # Azure AI Search is used in prod; leave blank for local dev and rely
    # on Qdrant instead.
    azure_search_endpoint: str | None = None
    azure_search_key: str | None = None
    qdrant_url: str = "http://qdrant:6333"

    # --- Source integrations ---------------------------------------------
    github_token: str = ""
    jira_token: str = ""
    jira_email: str = ""
    jira_url: str = ""
    confluence_token: str = ""
    confluence_url: str = ""

    # --- Query API --------------------------------------------------------
    api_key: str = "dev-api-key"
    api_version_prefix: str = "/v1"

    # --- MCP registry -----------------------------------------------------
    mcp_servers_config_path: str = "config/mcp_servers.yaml"

    # --- Misc tunables ----------------------------------------------------
    staleness_threshold_hours: int = 24
    full_sync_interval_hours: int = 6
    llm_context_token_budget: int = 8000
    vector_search_top_k: int = 10
    graph_expansion_hops: int = 2
    log_level: str = "INFO"

    # --- Automated Steering Pipeline ----------------------------------------
    steering_webhook_secret: str = ""
    kiro_steering_dir: str = "kiro_steering"

    # --- V2 RAG pipeline tunables ----------------------------------------
    # Chunking: target 200-500 token chunks (Req 1.4).
    chunk_min_tokens: int = 200
    chunk_max_tokens: int = 500
    # Hybrid retrieval + RRF fusion (Req 3.3, 3.4).
    hybrid_top_n: int = 30
    rrf_k: int = 60
    # Cross-encoder re-ranking (Req 4.1, 4.2, 4.3).
    rerank_top_k: int = 5
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_timeout_ms: int = 500
    # Deduplication near-duplicate cosine threshold (Req 5.2).
    dedup_cosine_threshold: float = 0.95
    # Layered caching TTLs and hot-embedding capacity (Req 7.5, 7.6, 8.1).
    embedding_cache_ttl_seconds: int = 86400
    result_cache_ttl_seconds: int = 3600
    hot_cache_capacity: int = 500
    # Cache backend: "memory" (dev default) or "redis" (Req 7.x).
    cache_backend: str = "memory"
    # Retrieval cutover flag: "chunk" (default) or "document" (migration).
    retrieval_mode: str = "chunk"

    # Ask pipeline mode: "monolithic" (V2 pipeline) or "orchestrated" (routed).
    # Controls the default behavior of POST /v1/ask when no mode is specified.
    default_ask_mode: str = "monolithic"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached `Settings` instance.

    The `lru_cache` decorator makes this effectively a singleton: the first
    call constructs `Settings` (reading env vars and the `.env` file),
    and subsequent calls return the same object. Tests that need to force
    a re-read can call `get_settings.cache_clear()`.
    """

    return Settings()

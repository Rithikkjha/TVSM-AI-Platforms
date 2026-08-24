"""Retrieval primitives — low-level building blocks shared by all strategies.

These functions are the "atoms" of retrieval. They do ONE thing each, have no
LLM calls, and return raw data. Used by:

- The orchestrated pipeline strategies (structural, single_service, flow)
- MCP primitive tools (search, get_service_chain)
- The /v1/search and /v1/graph/chain API endpoints

Design principle (from Cerebras): Build good primitives, let the orchestrator
(agent or server-side) be smart.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from neo4j import AsyncGraphDatabase

from config.settings import Settings, get_settings
from processing.embeddings.service import EmbeddingService
from retrieval.reranking.cross_encoder import CrossEncoderReranker
from retrieval.search.hybrid_retriever import HybridRetriever, ScoredChunk
from storage.vector.sparse_index import LocalBM25Index
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Primitive: search
# ---------------------------------------------------------------------------


async def search(
    query: str,
    repo_filter: str | None = None,
    doc_type: str | None = None,
    limit: int = 5,
    rerank: bool = True,
) -> list[dict[str, Any]]:
    """Hybrid search + optional rerank. Returns raw chunks (no LLM).

    This is the core retrieval primitive. It embeds the query, runs hybrid
    retrieval (dense + BM25 + RRF), optionally reranks, and returns the top
    chunks as plain dicts.

    Args:
        query: The search query text.
        repo_filter: If set, only return chunks from this service/repo.
        doc_type: If set, only return chunks of this type (tech/product/structure/confluence/jira).
        limit: Maximum number of chunks to return (default 5).
        rerank: Whether to apply cross-encoder reranking (default True).

    Returns:
        List of chunk dicts with keys: chunk_id, text, score, section_title,
        repo_name, doc_type, source_ref, parent_source_id, chunk_index.
    """
    settings = get_settings()

    # Build filters dict
    filters: dict[str, str] | None = None
    if repo_filter or doc_type:
        filters = {}
        if repo_filter:
            filters["repo_name"] = repo_filter
        if doc_type:
            filters["doc_type"] = doc_type

    # Embed the query
    embedding_service = EmbeddingService(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        deployment_name=settings.azure_openai_deployment_embedding,
        api_version=settings.azure_openai_api_version,
    )
    try:
        query_vector = await embedding_service.generate_embedding(query)
    finally:
        await embedding_service.close()

    # Hybrid retrieval
    vector_store = get_vector_store(settings)
    sparse_index = LocalBM25Index()
    retriever = HybridRetriever(
        vector_store=vector_store,
        sparse_index=sparse_index,
        rrf_k=settings.rrf_k,
        top_n=settings.hybrid_top_n,
    )

    candidates = await retriever.retrieve(
        query=query,
        query_vector=query_vector,
        filters=filters,
        top_n=settings.hybrid_top_n if rerank else limit,
    )

    if not candidates:
        return []

    # Optional reranking
    if rerank and len(candidates) > limit:
        reranker = CrossEncoderReranker(settings)
        try:
            top_chunks = await reranker.rerank(
                query=query,
                candidates=candidates,
                top_k=limit,
            )
        except Exception as exc:
            logger.warning("Reranker failed in primitive search, using top-%d: %s", limit, exc)
            top_chunks = candidates[:limit]
    else:
        top_chunks = candidates[:limit]

    # Convert to plain dicts
    # Hydrate text from Neo4j since vector store doesn't carry chunk text
    hydrated_chunks = await _hydrate_chunk_text(top_chunks)

    return hydrated_chunks


async def _hydrate_chunk_text(chunks: list[ScoredChunk]) -> list[dict[str, Any]]:
    """Fetch actual text content from Neo4j for chunks.

    The vector store and BM25 index don't store full text — only the embedding
    and metadata. The actual content lives in Neo4j on the parent document nodes
    (as content_summary) or on chunk nodes directly.

    This mirrors what ask_pipeline.py does in step 7.
    """
    if not chunks:
        return []

    settings = get_settings()

    try:
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

        results = []
        async with driver.session() as session:
            for chunk in chunks:
                text = ""
                # Try fetching from chunk node first
                chunk_result = await session.run(
                    "MATCH (n {source_id: $sid}) RETURN n.text AS text, n.content_summary AS content",
                    sid=chunk.chunk_id,
                )
                record = await chunk_result.single()
                if record:
                    text = record.get("text") or record.get("content") or ""

                # If chunk node has no text, try the parent document
                if not text and chunk.parent_source_id:
                    parent_result = await session.run(
                        "MATCH (n {source_id: $sid}) RETURN n.content_summary AS content, n.text AS text",
                        sid=chunk.parent_source_id,
                    )
                    parent_record = await parent_result.single()
                    if parent_record:
                        text = parent_record.get("content") or parent_record.get("text") or ""
                        # If we got the full parent doc, try to extract relevant section
                        if text and chunk.section_title:
                            section_text = _extract_section(text, chunk.section_title)
                            if section_text:
                                text = section_text

                results.append({
                    "chunk_id": chunk.chunk_id,
                    "text": text[:3000],  # Cap at ~750 tokens
                    "display_text": text[:3000],
                    "score": round(chunk.score, 4),
                    "section_title": chunk.section_title,
                    "repo_name": chunk.repo_name,
                    "doc_type": chunk.doc_type,
                    "source_ref": chunk.source_ref,
                    "parent_source_id": chunk.parent_source_id,
                    "chunk_index": chunk.chunk_index,
                })

        await driver.close()
        return results

    except Exception as exc:
        logger.warning("Neo4j text hydration failed, returning without text: %s", exc)
        # Fallback: return chunks without text
        return [
            {
                "chunk_id": c.chunk_id,
                "text": c.text or c.display_text or "",
                "display_text": c.display_text or c.text or "",
                "score": round(c.score, 4),
                "section_title": c.section_title,
                "repo_name": c.repo_name,
                "doc_type": c.doc_type,
                "source_ref": c.source_ref,
                "parent_source_id": c.parent_source_id,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]


def _extract_section(full_text: str, section_title: str) -> str:
    """Extract a section from a full document by heading match."""
    import re

    # Try to find the section heading
    pattern = rf"^#+\s*{re.escape(section_title)}\s*$"
    lines = full_text.split("\n")

    start_idx = None
    for i, line in enumerate(lines):
        if re.match(pattern, line, re.IGNORECASE):
            start_idx = i
            break

    if start_idx is None:
        # Try simpler match
        for i, line in enumerate(lines):
            if section_title.lower() in line.lower() and line.strip().startswith("#"):
                start_idx = i
                break

    if start_idx is None:
        return ""

    # Find next heading of same or higher level
    heading_level = len(lines[start_idx]) - len(lines[start_idx].lstrip("#"))
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip().startswith("#"):
            current_level = len(lines[i]) - len(lines[i].lstrip("#"))
            if current_level <= heading_level:
                end_idx = i
                break

    return "\n".join(lines[start_idx:end_idx]).strip()


# ---------------------------------------------------------------------------
# Primitive: get_service_chain
# ---------------------------------------------------------------------------


async def get_service_chain(
    service: str,
    direction: str = "downstream",
    hops: int = 2,
) -> list[dict[str, Any]]:
    """Get the dependency chain from a service via graph traversal.

    Args:
        service: The service name to start from.
        direction: "downstream" (what this service depends on),
                   "upstream" (what depends on this service),
                   "both" (both directions).
        hops: Maximum traversal depth (default 2).

    Returns:
        List of dicts with keys: name, relationship_type, hop_distance, source_id.
        Ordered by hop distance ascending.
    """
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    results: list[dict[str, Any]] = []

    try:
        async with driver.session() as session:
            if direction in ("downstream", "both"):
                # Services this service depends ON
                cypher = (
                    "MATCH path = (s:Service {name: $name})-[:DEPENDS_ON*1.."
                    + str(hops)
                    + "]->(t:Service) "
                    "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
                    "WITH t, min(length(path)) AS hop_dist "
                    "RETURN t.name AS name, t.source_id AS source_id, "
                    "hop_dist, 'depends_on' AS relationship"
                )
                result = await session.run(cypher, name=service)
                records = [record async for record in result]
                for r in records:
                    results.append({
                        "name": r["name"],
                        "source_id": r["source_id"],
                        "relationship_type": "DEPENDS_ON",
                        "direction": "downstream",
                        "hop_distance": r["hop_dist"],
                    })

            if direction in ("upstream", "both"):
                # Services that depend ON this service
                cypher = (
                    "MATCH path = (t:Service)-[:DEPENDS_ON*1.."
                    + str(hops)
                    + "]->(s:Service {name: $name}) "
                    "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
                    "WITH t, min(length(path)) AS hop_dist "
                    "RETURN t.name AS name, t.source_id AS source_id, "
                    "hop_dist, 'depended_on_by' AS relationship"
                )
                result = await session.run(cypher, name=service)
                records = [record async for record in result]
                for r in records:
                    results.append({
                        "name": r["name"],
                        "source_id": r["source_id"],
                        "relationship_type": "DEPENDED_ON_BY",
                        "direction": "upstream",
                        "hop_distance": r["hop_dist"],
                    })
    finally:
        await driver.close()

    # Sort by hop distance
    results.sort(key=lambda x: x["hop_distance"])
    return results


# ---------------------------------------------------------------------------
# Primitive: get_known_services
# ---------------------------------------------------------------------------


async def get_known_services() -> list[str]:
    """Fetch all known service names from the graph.

    Used by the query classifier to detect service mentions in questions.
    Results are cached in-memory after first call (services rarely change mid-request).
    """
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        async with driver.session() as session:
            result = await session.run(
                "MATCH (s:Service) WHERE s.deleted_at IS NULL RETURN s.name AS name"
            )
            records = [record async for record in result]
            return [r["name"] for r in records if r["name"]]
    finally:
        await driver.close()

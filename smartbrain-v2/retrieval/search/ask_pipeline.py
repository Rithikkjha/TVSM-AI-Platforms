"""V2 RAG query pipeline — the ``ask_question`` entry point.

Implements the full V2 query flow:

1. Result cache check — SHA-256 of query → cached answer on hit.
2. Embedding cache check — cached query vector on hit.
3. Embed query — call EmbeddingService; write to embedding cache.
4. Hybrid retrieval — HybridRetriever (dense + BM25, RRF top-30).
5. Cross-encoder re-ranking — Reranker → top-5 ScoredChunks.
6. Graph expansion — 1-2 hops from parent_source_id values.
7. Citation context assembly — citation_engine.format_context.
8. LLM call — GPT-4o with [ref:N] system prompt + graph context.
9. Citation mapping — citation_engine.map_citations.
10. Cache write — embedding (24h) + result (1h).
11. Return — answer text + mapped citations list.

Graceful degradation:
- Cache backend down → treat as miss.
- Reranker fails → use hybrid top-5.
- Sparse index unavailable → dense-only (handled by HybridRetriever).

The public entry point ``ask_question(question)`` is backward-compatible with
the MCP tool and the FastAPI router.

Requirements: 4.4, 6.2, 7.1–7.6.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from fastapi import Query
from fastapi.routing import APIRouter
from openai import AsyncAzureOpenAI

from config.settings import Settings, get_settings
from processing.embeddings.service import EmbeddingError, EmbeddingService
from retrieval.cache.query_cache import EmbeddingCache, ResultCache, build_query_caches
from retrieval.citations.citation_engine import Citation, format_context, map_citations
from retrieval.reranking.cross_encoder import CrossEncoderReranker
from retrieval.search.hybrid_retriever import HybridRetriever, ScoredChunk
from storage.vector.sparse_index import LocalBM25Index
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# V2 LLM System Prompt — instructs [ref:N] citation usage (Req 6.2)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the Engineering Memory Graph Assistant. You have deep knowledge of this organization's engineering systems from the provided context.

CRITICAL RULES:

1. DETAILED ANSWERS: When asked about a service, provide ALL information from the context — full description, tech stack, endpoints, dependencies, configuration, deployment. Do NOT summarize aggressively. Include every detail available.

2. FORMATTING — MAKE ANSWERS SCANNABLE:
   - Use proper markdown section headings (## Overview, ## Tech Stack, ## API Endpoints, ## Architecture, ## Dependencies, ## Configuration, ## Deployment) when the context has those sections.
   - Render API endpoint lists as GFM pipe tables with columns Method / Endpoint / Description.
   - MANDATORY: Whenever you list TWO OR MORE entities that share the same attributes render them as a GFM pipe table.
   - Render tech stack / dependencies / env-var lists as bullet points with bolded labels.
   - Use fenced code blocks with language hints for configuration snippets.
   - Keep paragraphs short (2-3 sentences). Prefer bullets over prose when listing items.
   - Bold the **key terms** (service names, file names, protocols) to aid skimming.
   - IMPORTANT: Use bullet points (-) for lists, NOT numbered lists (1. 2. 3.). Numbered lists break rendering.

3. NEVER FABRICATE: Do not make up services, dependencies, endpoints, or flows that are not explicitly stated in the context. Base every claim on actual text from the provided context.

4. When asked what a service does or for its design/details, provide the FULL content from the context, REFORMATTED for readability. Preserve every fact; reorganize the presentation.

5. GROUNDING: If the retrieved context does not contain enough information to answer the question precisely, say so plainly. Do not hallucinate. It's better to say "not in the ingested data" than to guess.

6. Cite sources using [ref:N] markers that correspond to the numbered context chunks provided.
"""


# ---------------------------------------------------------------------------
# Graph expansion (reused from existing pipeline logic)
# ---------------------------------------------------------------------------


async def _expand_graph_neighborhood(
    parent_source_ids: set[str],
    hops: int = 2,
) -> str:
    """Expand graph neighborhood from parent document source_ids.

    Fetches 1-2 hop neighbors for each unique parent_source_id among the
    re-ranked chunks, assembles them into a concise text block for the LLM.
    Returns an empty string if Neo4j is unavailable or no neighbors found.
    """
    if not parent_source_ids:
        return ""

    try:
        from neo4j import AsyncGraphDatabase
        from retrieval.search import graph_queries

        settings = get_settings()
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    except Exception as exc:
        logger.warning("Neo4j driver creation failed for graph expansion: %s", exc)
        return ""

    neighbor_blocks: list[str] = []
    try:
        seen_ids: set[str] = set()
        for source_id in parent_source_ids:
            try:
                neighbors = await graph_queries.get_entity_neighborhood(
                    driver, source_id, hops=hops
                )
                for neighbor in neighbors:
                    nid = neighbor.get("source_id", "")
                    if nid and nid not in seen_ids:
                        seen_ids.add(nid)
                        name = neighbor.get("name") or neighbor.get("title") or ""
                        desc = neighbor.get("description") or ""
                        if name:
                            block = f"- {name}"
                            if desc:
                                block += f": {desc[:200]}"
                            neighbor_blocks.append(block)
            except Exception as exc:
                logger.debug("Graph expansion failed for %s: %s", source_id, exc)
                continue
    finally:
        await driver.close()

    if not neighbor_blocks:
        return ""
    return "Related entities from graph neighborhood:\n" + "\n".join(
        neighbor_blocks[:20]
    )


# ---------------------------------------------------------------------------
# Component factories (lazy construction from settings)
# ---------------------------------------------------------------------------


def _get_embedding_service(settings: Settings) -> EmbeddingService:
    """Construct an EmbeddingService from settings."""
    return EmbeddingService(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        deployment_name=settings.azure_openai_deployment_embedding,
        api_version=settings.azure_openai_api_version,
    )


def _get_hybrid_retriever(settings: Settings) -> HybridRetriever:
    """Construct a HybridRetriever wired to the configured backends."""
    vector_store = get_vector_store(settings)
    sparse_index = LocalBM25Index()
    return HybridRetriever(
        vector_store=vector_store,
        sparse_index=sparse_index,
        rrf_k=settings.rrf_k,
        top_n=settings.hybrid_top_n,
    )


def _get_reranker(settings: Settings) -> CrossEncoderReranker:
    """Construct a CrossEncoderReranker from settings."""
    return CrossEncoderReranker(settings)


def _get_llm_client(settings: Settings) -> AsyncAzureOpenAI:
    """Create an Azure OpenAI client for LLM chat completion."""
    import httpx
    http_client = httpx.AsyncClient(verify=False, timeout=60.0)
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=http_client,
    )


# ---------------------------------------------------------------------------
# Main V2 pipeline entry point
# ---------------------------------------------------------------------------


async def ask_question(question: str) -> dict[str, Any]:
    """Answer a question using the V2 RAG pipeline.

    Pipeline flow:
    1. Result cache check (SHA-256 of query).
    2. Embedding cache check.
    3. Embed query (on cache miss).
    4. Hybrid retrieval (dense + BM25, RRF -> top-30).
    5. Cross-encoder re-ranking -> top-5.
    6. Graph expansion from parent_source_ids (1-2 hops).
    7. Citation context assembly ([ref:N] markers).
    8. LLM call (GPT-4o with updated system prompt).
    9. Citation mapping (filter to used refs only).
    10. Cache write (embedding 24h, result 1h).
    11. Return answer + citations.

    Args:
        question: The user's natural language question.

    Returns:
        A dict with keys:
        - "answer": str — the LLM-generated answer text.
        - "citations": list[dict] — mapped citation objects.
    """
    settings = get_settings()

    # Build caches (graceful: backend down → misses)
    try:
        embedding_cache, result_cache = build_query_caches(settings)
    except Exception as exc:
        logger.warning("Cache backend initialization failed: %s", exc)
        embedding_cache = None
        result_cache = None

    # ------------------------------------------------------------------
    # Step 1: Result cache check
    # ------------------------------------------------------------------
    query_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()

    if result_cache is not None:
        try:
            cached_result = await result_cache.get(question)
            if cached_result is not None:
                logger.info("Result cache hit for query hash %s", query_hash[:12])
                return cached_result
        except Exception as exc:
            logger.warning("Result cache read failed (treating as miss): %s", exc)

    # ------------------------------------------------------------------
    # Step 2: Embedding cache check
    # ------------------------------------------------------------------
    query_vector: list[float] | None = None

    if embedding_cache is not None:
        try:
            query_vector = await embedding_cache.get(question)
            if query_vector is not None:
                logger.info("Embedding cache hit for query hash %s", query_hash[:12])
        except Exception as exc:
            logger.warning("Embedding cache read failed (treating as miss): %s", exc)

    # ------------------------------------------------------------------
    # Step 3: Embed query (on cache miss)
    # ------------------------------------------------------------------
    if query_vector is None:
        embedding_service = _get_embedding_service(settings)
        try:
            query_vector = await embedding_service.generate_embedding(question)
        except EmbeddingError as exc:
            logger.error("Embedding generation failed: %s", exc)
            return {
                "answer": "I'm temporarily unable to process your question. "
                "The embedding service is unavailable.",
                "citations": [],
            }
        finally:
            await embedding_service.close()

        # Write embedding to cache on success
        if embedding_cache is not None:
            try:
                await embedding_cache.set(question, query_vector)
            except Exception as exc:
                logger.warning("Embedding cache write failed: %s", exc)

    # ------------------------------------------------------------------
    # Step 4: Hybrid retrieval → top-30 ScoredChunks
    # ------------------------------------------------------------------
    retriever = _get_hybrid_retriever(settings)
    try:
        candidates: list[ScoredChunk] = await retriever.retrieve(
            query=question,
            query_vector=query_vector,
            filters=None,
            top_n=settings.hybrid_top_n,
        )
    except Exception as exc:
        logger.error("Hybrid retrieval failed: %s", exc)
        return {
            "answer": "I'm temporarily unable to search the knowledge base.",
            "citations": [],
        }

    if not candidates:
        return {
            "answer": "I don't have enough information in the knowledge base "
            "to answer this question. Try asking about a specific "
            "service that has been ingested.",
            "citations": [],
        }

    # ------------------------------------------------------------------
    # Step 5: Cross-encoder re-ranking → top-5
    # ------------------------------------------------------------------
    reranker = _get_reranker(settings)
    try:
        top_chunks: list[ScoredChunk] = await reranker.rerank(
            query=question,
            candidates=candidates,
            top_k=settings.rerank_top_k,
        )
    except Exception as exc:
        # Graceful degradation: use hybrid top-5 (Req 4.4)
        logger.warning("Reranker failed, falling back to hybrid top-%d: %s",
                       settings.rerank_top_k, exc)
        top_chunks = candidates[: settings.rerank_top_k]

    # ------------------------------------------------------------------
    # Step 6: Graph expansion from parent_source_ids
    # ------------------------------------------------------------------
    parent_ids: set[str] = set()
    for chunk in top_chunks:
        if chunk.parent_source_id:
            parent_ids.add(chunk.parent_source_id)

    graph_context = await _expand_graph_neighborhood(
        parent_ids, hops=settings.graph_expansion_hops
    )

    # ------------------------------------------------------------------
    # Step 6.5: Graph gap re-retrieval (Option 2)
    # If the graph surfaced related services whose chunks we don't have,
    # and those services have a chunk relevant to THIS question, add it.
    # See docs/GRAPH_GAP_RETRIEVAL.md for full explanation.
    # ------------------------------------------------------------------
    covered_services = {
        chunk.repo_name for chunk in top_chunks if chunk.repo_name
    }
    uncovered_services: list[str] = []
    for neighbor in (graph_context or "").split("\n"):
        # Graph context lines look like "- service-name: description"
        if neighbor.startswith("- "):
            svc_name = neighbor[2:].split(":")[0].strip()
            if svc_name and svc_name not in covered_services:
                uncovered_services.append(svc_name)

    # Cap at 3 to bound latency
    graph_gap_max = 3
    graph_gap_threshold = 0.7
    for svc in uncovered_services[:graph_gap_max]:
        try:
            gap_hits = await retriever._vector_store.search(
                query_vector=query_vector,
                entity_type="Chunk",
                limit=1,
                filters={"repo_name": svc},
                exclude_duplicates=True,
            )
            if gap_hits and gap_hits[0].score > graph_gap_threshold:
                hit = gap_hits[0]
                from retrieval.search.hybrid_retriever import ScoredChunk
                top_chunks.append(ScoredChunk(
                    chunk_id=hit.source_id,
                    score=hit.score,
                    text="",
                    display_text="",
                    section_title=hit.section_title,
                    repo_name=hit.repo_name,
                    doc_type=hit.doc_type,
                    parent_source_id=hit.parent_source_id,
                    chunk_index=hit.chunk_index,
                    source_ref=hit.source_ref,
                ))
        except Exception as exc:
            logger.debug("Graph gap re-retrieval failed for %s: %s", svc, exc)

    # ------------------------------------------------------------------
    # Step 7: Context assembly — fetch FULL parent documents from Neo4j
    # instead of just chunk snippets (matches V1 approach for better answers)
    # ------------------------------------------------------------------
    # Collect unique parent source IDs from top chunks
    parent_ids_ordered: list[str] = []
    seen_parents: set[str] = set()
    for chunk in top_chunks:
        pid = chunk.parent_source_id or chunk.chunk_id.rsplit("#chunk:", 1)[0] if "#chunk:" in (chunk.chunk_id or "") else chunk.chunk_id
        if pid and pid not in seen_parents:
            seen_parents.add(pid)
            parent_ids_ordered.append(pid)

    # Fetch full entity content from Neo4j for each parent
    context_blocks: list[str] = []
    citations_list: list[Citation] = []
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with driver.session() as session:
            for ref_idx, parent_id in enumerate(parent_ids_ordered[:10], start=1):
                result = await session.run(
                    "MATCH (n {source_id: $sid}) RETURN properties(n) AS props",
                    sid=parent_id,
                )
                record = await result.single()
                if record:
                    props = record["props"]
                    # Format entity like V1 does — include ALL properties
                    name = props.get("name") or props.get("title") or parent_id
                    lines = [f"[ref:{ref_idx}] Entity: {name} (source: {parent_id})"]
                    # Include content_summary (full doc text) if available
                    content = props.get("content_summary") or props.get("text") or ""
                    if content:
                        lines.append(content[:12000])  # Cap at ~3000 tokens
                    else:
                        # Fallback: include all properties
                        for key, value in props.items():
                            if key in ("source_id", "text_hash", "deleted_at", "created_at", "embedding"):
                                continue
                            if value is not None and value != "" and str(value).strip():
                                lines.append(f"- {key}: {str(value)[:500]}")
                    block = "\n".join(lines)
                    context_blocks.append(block)
                    citations_list.append(Citation(
                        ref=ref_idx,
                        source_id=parent_id,
                        section_title=props.get("section_title") or props.get("doc_type") or "",
                        url=None,
                        source_ref=props.get("repo_name") or "",
                        line_range=None,
                    ))
        await driver.close()
    except Exception as exc:
        logger.warning("Parent doc fetch failed, falling back to chunk text: %s", exc)
        # Fallback to chunk-based context
        from retrieval.citations.citation_engine import format_context
        context_text_fallback, citations_list = format_context(top_chunks)
        context_blocks = [context_text_fallback]

    context_text = "\n\n".join(context_blocks)

    # ------------------------------------------------------------------
    # Step 8: LLM call with [ref:N] system prompt
    # ------------------------------------------------------------------
    # Build the user message with chunk context + graph context
    user_parts: list[str] = [
        "## Retrieved Context\n",
        context_text,
    ]
    if graph_context:
        user_parts.append(f"\n\n## Graph Neighborhood\n{graph_context}")
    user_parts.append(f"\n\n## Question\n{question}")

    user_message = "\n".join(user_parts)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    llm_client = _get_llm_client(settings)
    try:
        completion = await llm_client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=messages,
            temperature=0.1,
        )
        answer_text = completion.choices[0].message.content or ""
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return {
            "answer": "The LLM service is temporarily unavailable. "
            "Please try again shortly.",
            "citations": [],
        }
    finally:
        await llm_client.close()

    # ------------------------------------------------------------------
    # Step 9: Citation mapping — filter to only used refs
    # ------------------------------------------------------------------
    mapped_citations: list[Citation] = map_citations(answer_text, citations_list)

    # ------------------------------------------------------------------
    # Step 10: Cache write — embedding (24h) + result (1h)
    # ------------------------------------------------------------------
    result_payload: dict[str, Any] = {
        "answer": answer_text,
        "citations": [
            {
                "ref": c.ref,
                "source_id": c.source_id,
                "section_title": c.section_title,
                "url": c.url,
                "source_ref": c.source_ref,
                "line_range": c.line_range,
            }
            for c in mapped_citations
        ],
    }

    # Write embedding cache (may already be cached from step 2 hit, but
    # set is idempotent)
    if embedding_cache is not None:
        try:
            await embedding_cache.set(question, query_vector)
        except Exception as exc:
            logger.warning("Embedding cache write failed: %s", exc)

    # Write result cache
    if result_cache is not None:
        try:
            await result_cache.set(question, None, result_payload)
        except Exception as exc:
            logger.warning("Result cache write failed: %s", exc)

    # ------------------------------------------------------------------
    # Step 11: Return
    # ------------------------------------------------------------------
    return result_payload


# ---------------------------------------------------------------------------
# FastAPI Router
# ---------------------------------------------------------------------------

router = APIRouter()


@router.post("/ask")
async def ask_endpoint(body: dict[str, Any]) -> dict[str, Any]:
    """POST /v1/ask — Ask a natural language question.

    Supports a `mode` parameter:
    - "monolithic": existing V2 pipeline (embed → hybrid → rerank → LLM)
    - "orchestrated": classify → route → strategy-specific retrieval → LLM

    Default mode is controlled by settings.default_ask_mode.
    """
    question = body.get("question", "")
    if not question:
        return {"error": "bad_request", "message": "question is required"}

    mode = body.get("mode", get_settings().default_ask_mode)

    if mode == "orchestrated":
        from retrieval.search.orchestrated_pipeline import ask_orchestrated
        return await ask_orchestrated(question)

    return await ask_question(question)


@router.get("/ask")
async def ask_get_endpoint(
    q: str = Query(..., description="Question text"),
    mode: str = Query(default="", description="Pipeline mode: monolithic or orchestrated"),
) -> dict[str, Any]:
    """GET /v1/ask?q=...&mode=... — Ask a natural language question."""
    effective_mode = mode or get_settings().default_ask_mode

    if effective_mode == "orchestrated":
        from retrieval.search.orchestrated_pipeline import ask_orchestrated
        return await ask_orchestrated(q)

    return await ask_question(q)

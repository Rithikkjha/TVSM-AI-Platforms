"""FastAPI router for the search endpoint.

Implements GET /v1/search which performs vector similarity search
using the embedding service and vector store.

When ``settings.retrieval_mode == "chunk"`` (the V2 default), the search is
routed through the :class:`~retrieval.search.hybrid_retriever.HybridRetriever`
which fuses dense vector search and BM25 keyword search via RRF, providing
better recall for exact-term queries. When ``retrieval_mode == "document"``
(the legacy fallback), the existing direct dense-only search path is preserved
so the cutover can be rolled back without code changes.

Requirements: 3.2, 3.3
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from config.settings import get_settings
from processing.embeddings.service import EmbeddingError, EmbeddingService
from retrieval.search.hybrid_retriever import HybridRetriever
from storage.vector.sparse_index import LocalBM25Index
from storage.vector.vector_store import VectorStore, get_vector_store
from api.schemas import SearchHit, SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_embedding_service() -> EmbeddingService:
    """Lazily create an EmbeddingService from settings.

    This helper exists so tests can mock it without needing real
    Azure OpenAI credentials.
    """
    settings = get_settings()
    return EmbeddingService(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        deployment_name=settings.azure_openai_deployment_embedding,
        api_version=settings.azure_openai_api_version,
    )


def _get_vector_store() -> VectorStore:
    """Lazily create a VectorStore from settings.

    This helper exists so tests can mock it without needing real
    vector store infrastructure.
    """
    settings = get_settings()
    return get_vector_store(settings)


def _get_hybrid_retriever(vector_store: VectorStore) -> HybridRetriever:
    """Construct a HybridRetriever wired to the given vector store.

    Uses a :class:`LocalBM25Index` for the sparse leg and reads RRF/top-n
    tunables from settings.
    """
    settings = get_settings()
    sparse_index = LocalBM25Index()
    return HybridRetriever(
        vector_store=vector_store,
        sparse_index=sparse_index,
        rrf_k=settings.rrf_k,
        top_n=settings.hybrid_top_n,
    )


@router.get("/search")
async def search(
    q: str = Query(default="", description="Search query string"),
    type: str | None = Query(default=None, description="Filter by entity type"),
    limit: int = Query(default=10, description="Number of results (max 50)"),
) -> JSONResponse:
    """Search for entities using vector similarity.

    Embeds the query text and performs vector similarity search.
    Returns scored results with entity metadata.

    - Empty query → 400
    - Embedding failure → 200 with empty results (logged warning)
    - Limit capped at 50

    When ``retrieval_mode == "chunk"``, routes through the HybridRetriever
    (dense + BM25 fused via RRF) for improved recall on exact-term queries.
    When ``retrieval_mode == "document"``, uses direct dense vector search
    (legacy behavior).
    """
    # Validate query
    if not q or not q.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": "Query parameter 'q' is required and must not be empty"},
        )

    # Cap limit at 50
    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 1

    settings = get_settings()

    # Get services
    embedding_service = _get_embedding_service()
    vector_store = _get_vector_store()

    try:
        # Embed the query
        query_vector = await embedding_service.generate_embedding(q)

        if settings.retrieval_mode == "chunk":
            # V2 path: hybrid retrieval (dense + BM25, fused via RRF)
            retriever = _get_hybrid_retriever(vector_store)
            scored_chunks = await retriever.retrieve(
                query=q,
                query_vector=query_vector,
                top_n=limit,
            )

            # Map ScoredChunks to the existing SearchHit response format
            results = [
                SearchHit(
                    source_id=chunk.chunk_id,
                    entity_type=chunk.doc_type or "Chunk",
                    name=None,
                    title=None,
                    score=chunk.score,
                )
                for chunk in scored_chunks
            ]
        else:
            # Legacy path (retrieval_mode == "document"): direct dense search
            hits = await vector_store.search(
                query_vector=query_vector,
                entity_type=type,
                limit=limit,
            )

            results = [
                SearchHit(
                    source_id=hit.source_id,
                    entity_type=hit.entity_type,
                    name=None,
                    title=None,
                    score=hit.score,
                )
                for hit in hits
            ]

        response = SearchResponse(
            query=q,
            results=results,
            total=len(results),
        )

        return JSONResponse(status_code=200, content=response.model_dump())

    except EmbeddingError as exc:
        logger.warning("Embedding generation failed for search query '%s': %s", q, exc)
        # Fall back to empty results
        response = SearchResponse(
            query=q,
            results=[],
            total=0,
        )
        return JSONResponse(status_code=200, content=response.model_dump())

    finally:
        await embedding_service.close()
        await vector_store.close()

"""search_graph tool — semantic vector search across the knowledge graph.

Embeds the query text and finds the most similar entities in the vector store.
Returns scored results with entity metadata.

When ``settings.retrieval_mode == "chunk"`` (V2 default), routes through the
:class:`~retrieval.search.hybrid_retriever.HybridRetriever` for fused
dense + BM25 retrieval. When ``retrieval_mode == "document"``, preserves the
legacy direct dense vector search.

Use cases:
- "Find services related to payments"
- "Search for booking-related tickets"
- "What docs mention authentication?"
"""

from __future__ import annotations

from typing import Any

from config.settings import get_settings
from processing.embeddings.service import EmbeddingError, EmbeddingService
from retrieval.search.hybrid_retriever import HybridRetriever
from storage.vector.sparse_index import LocalBM25Index
from storage.vector.vector_store import get_vector_store


async def search_graph(query: str, entity_type: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Perform semantic vector search across the knowledge graph.

    Args:
        query: Natural language search query.
        entity_type: Optional filter (Service, Ticket, ConfluencePage, PR, Epic).
        limit: Max results to return (1-50, default 10).

    Returns:
        Dict with query, results list, and total count.
    """
    import asyncio

    if not query or not query.strip():
        return {"error": "Query must not be empty"}

    # Normalize empty/whitespace entity_type to None
    if entity_type is not None and not entity_type.strip():
        entity_type = None

    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 1

    settings = get_settings()

    embedding_service = EmbeddingService(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        deployment_name=settings.azure_openai_deployment_embedding,
        api_version=settings.azure_openai_api_version,
    )
    vector_store = get_vector_store(settings)

    # Retry up to 3 times with backoff for rate limiting
    last_error = None
    for attempt in range(3):
        try:
            query_vector = await embedding_service.generate_embedding(query)

            if settings.retrieval_mode == "chunk":
                # V2 path: hybrid retrieval (dense + BM25, fused via RRF)
                sparse_index = LocalBM25Index()
                retriever = HybridRetriever(
                    vector_store=vector_store,
                    sparse_index=sparse_index,
                    rrf_k=settings.rrf_k,
                    top_n=settings.hybrid_top_n,
                )
                scored_chunks = await retriever.retrieve(
                    query=query,
                    query_vector=query_vector,
                    top_n=limit,
                )

                results = [
                    {
                        "source_id": chunk.chunk_id,
                        "entity_type": chunk.doc_type or "Chunk",
                        "score": round(chunk.score, 4),
                    }
                    for chunk in scored_chunks
                ]
            else:
                # Legacy path (retrieval_mode == "document"): direct dense search
                hits = await vector_store.search(
                    query_vector=query_vector,
                    entity_type=entity_type,
                    limit=limit,
                )

                results = [
                    {
                        "source_id": hit.source_id,
                        "entity_type": hit.entity_type,
                        "score": round(hit.score, 4),
                    }
                    for hit in hits
                ]

            return {"query": query, "results": results, "total": len(results)}

        except EmbeddingError as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s backoff
                continue
            break
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            break
        finally:
            if attempt == 2 or last_error is None:
                await embedding_service.close()
                await vector_store.close()

    await embedding_service.close()
    await vector_store.close()
    return {"error": f"Search failed after 3 attempts: {last_error}"}

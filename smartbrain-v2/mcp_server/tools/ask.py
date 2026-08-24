"""ask_question tool — natural language Q&A over the knowledge graph (GraphRAG).

Delegates to the V2 RAG pipeline which handles:
- Result/embedding caching
- Hybrid retrieval (dense + BM25, RRF fusion)
- Cross-encoder re-ranking
- Graph expansion
- Structured [ref:N] citations
- LLM call (GPT-4o)

Use cases:
- "What services depend on tvsm-auth?"
- "How does the booking flow work?"
- "What tech stack does notification-service use?"
- "Who works on the payment system?"

Requirements: 6.2.
"""

from __future__ import annotations

from typing import Any

from retrieval.search.ask_pipeline import ask_question as v2_ask_question


async def ask_question(question: str) -> dict[str, Any]:
    """Answer a natural language question using the V2 RAG pipeline.

    Args:
        question: Natural language question about the engineering systems.

    Returns:
        Dict with 'answer' text and 'citations' list.
    """
    return await v2_ask_question(question)

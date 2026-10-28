"""Strict scope gate for the ask/chat pipeline.

The chatbot must answer ONLY from the TVS engineering knowledge base. Two
mechanisms live here and are shared by both ask pipelines (monolithic
``ask_question`` and the ``orchestrated`` router) so behaviour is identical
regardless of ``DEFAULT_ASK_MODE``:

1. **Meta-intent allow-list** (:func:`match_meta_intent`) — a *tiny*, explicit
   guard that gives greetings ("hi", "hello") and capability questions ("what
   can you do", "help", "who are you") a canned, retrieval-free scope reply
   with no citations. It is deliberately strict (anchored, short-phrase only)
   so it never swallows a real question like "who are the subscribers of ...".

2. **Relevance gate** (:func:`max_dense_cosine`) — before synthesising an
   answer, each pipeline checks whether ANY retrieved chunk clears
   ``settings.min_retrieval_score``. The score gated on is the **dense cosine
   similarity** from Qdrant (``VectorSearchHit.score``), which is the
   semantically meaningful, query-comparable score. The hybrid retriever's
   ``ScoredChunk.score`` is an RRF *fusion* score (~1/(k+rank)) that is NOT
   comparable across queries, so it must not be used for an absolute threshold.
   If nothing clears the threshold the pipeline returns :data:`REFUSAL` with
   no citations and never calls the synthesis LLM.

Empirical score separation (text-embedding-3-small, 1536-dim, cosine):
    in-domain top cosine  ~0.63-0.71
    out-of-domain top     ~0.19 ("who invented the bulb") - 0.31 ("what is 2+2")
A default ``MIN_RETRIEVAL_SCORE`` of 0.40 sits in the gap: it passes in-domain
and rejects out-of-domain / trivia.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

__all__ = ["REFUSAL", "META_REPLY", "match_meta_intent", "max_dense_cosine"]


# ---------------------------------------------------------------------------
# Canned replies (no LLM, no citations)
# ---------------------------------------------------------------------------

#: Returned when no retrieved chunk clears the relevance threshold.
REFUSAL = (
    "I can only answer questions about TVS engineering systems (services, "
    "APIs, dependencies, data flows, Jira/Confluence). I don't have anything "
    "relevant to that."
)

#: Returned for greeting / capability (meta) questions — no retrieval needed.
META_REPLY = (
    "Hi! I'm the TVS Engineering Memory Graph assistant. I answer questions "
    "grounded in the TVS engineering knowledge base — services, APIs, "
    "dependencies, data flows, and Jira/Confluence docs. Ask me things like "
    "\"what does booking-crud-services depend on\" or \"what endpoints does "
    "tvsmbe-location expose\"."
)


# ---------------------------------------------------------------------------
# Meta-intent allow-list
# ---------------------------------------------------------------------------

# Deliberately narrow: match only very short / explicit greeting or capability
# phrasings so real questions are never swallowed. Anchored with ^...$ and
# limited to a handful of patterns.
_META_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Greetings: "hi", "hello", "hey", "yo", "hi there", "good morning", ...
    re.compile(r"^(hi|hello|hey|yo|hiya|howdy)(\s+there)?[.!]*$"),
    re.compile(r"^good\s+(morning|afternoon|evening)[.!]*$"),
    re.compile(r"^greetings[.!]*$"),
    # Capability / identity: "what can you do", "help", "who are you", ...
    re.compile(r"^help[.!?]*$"),
    re.compile(r"^what\s+can\s+you\s+do[.!?]*$"),
    re.compile(r"^what\s+do\s+you\s+do[.!?]*$"),
    re.compile(r"^who\s+are\s+you[.!?]*$"),
    re.compile(r"^what\s+are\s+you[.!?]*$"),
)


def match_meta_intent(question: str) -> bool:
    """Return ``True`` when ``question`` is a greeting or capability question.

    Matches only short, explicit phrasings (anchored patterns). Anything with
    extra substance — e.g. "who are you going to notify when X fails" — falls
    through to normal retrieval + the relevance gate.
    """
    if not question:
        return False
    q = question.strip().lower()
    # Hard length guard so a long sentence can never match a meta pattern.
    if len(q.split()) > 5:
        return False
    return any(pattern.match(q) for pattern in _META_PATTERNS)


# ---------------------------------------------------------------------------
# Relevance gate — dense cosine similarity
# ---------------------------------------------------------------------------


async def max_dense_cosine(
    query_vector: list[float],
    *,
    filters: dict | None = None,
) -> float:
    """Return the highest dense cosine similarity for ``query_vector``.

    Runs a small dense-only vector search (``Chunk`` entities) against the
    configured vector store and returns the top hit's cosine score, or ``0.0``
    when nothing is found or the store is unavailable (fail-closed: an
    unavailable store yields 0.0 so the caller refuses rather than free-wheels).

    This is intentionally a cheap, dense-only probe (not the full hybrid /
    rerank path) so the gate adds negligible latency and gates on the one
    score that is comparable across queries.
    """
    from config.settings import get_settings
    from storage.vector.vector_store import get_vector_store

    settings = get_settings()
    try:
        vector_store = get_vector_store(settings)
        hits = await vector_store.search(
            query_vector,
            entity_type="Chunk",
            limit=5,
            filters=filters,
            exclude_duplicates=True,
        )
    except Exception as exc:  # noqa: BLE001 - gate must fail closed on any error
        logger.warning("Relevance gate dense probe failed (treating as 0.0): %s", exc)
        return 0.0

    if not hits:
        return 0.0
    return max(float(h.score) for h in hits)

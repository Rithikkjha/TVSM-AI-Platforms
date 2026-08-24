"""Query classifier — routes questions to the optimal retrieval strategy.

Classifies incoming questions into one of four types using keyword heuristics
(no LLM call, ~0ms). Falls back to "general" for anything ambiguous.

Query types:
- structural: Graph-only questions about dependencies, ownership, impact.
- single_service: Questions about a specific known service.
- cross_service_flow: End-to-end flow questions spanning multiple services.
- general: Everything else (falls through to monolithic pipeline).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from retrieval.search.service_aliases import resolve_service


class QueryType(str, Enum):
    """The classification result."""

    STRUCTURAL = "structural"
    SINGLE_SERVICE = "single_service"
    CROSS_SERVICE_FLOW = "cross_service_flow"
    GENERAL = "general"


@dataclass
class ClassificationResult:
    """Result of query classification."""

    query_type: QueryType
    extracted_service: str | None = None
    confidence: str = "heuristic"


# Patterns that signal structural/graph questions
_STRUCTURAL_PATTERNS = [
    r"\bwhat\s+(services?\s+)?depends?\s+on\b",
    r"\bwho\s+owns?\b",
    r"\bwho\s+is\s+the\s+owner\b",
    r"\bblast\s+radius\b",
    r"\bimpact\s+(of|if)\b",
    r"\bwhat\s+(is|are)\s+the\s+dependenc(y|ies)\b",
    r"\bupstream\b.*\bservices?\b",
    r"\bdownstream\b.*\bservices?\b",
    r"\bwhat\s+services?\s+use\b",
    r"\bwhat\s+services?\s+call\b",
]

# Patterns that signal cross-service flow questions
_FLOW_PATTERNS = [
    r"\bend\s*to\s*end\b",
    r"\be2e\b",
    r"\bflow\b",
    r"\bjourney\b",
    r"\bstep\s+by\s+step\b",
    r"\bacross\s+services?\b",
    r"\bhow\s+does\s+.+\s+work\s+.*(end|across|between)\b",
    r"\bsequence\b.*\bservices?\b",
    r"\bwhat\s+happens\s+when\b.*\b(after|then|next)\b",
]

# Patterns that signal a single-service question
_SINGLE_SERVICE_PATTERNS = [
    r"\btell\s+me\s+about\b",
    r"\bwhat\s+is\b",
    r"\bdescribe\b",
    r"\bexplain\b.*\bservice\b",
    r"\btech\s+stack\b",
    r"\bapi\s+endpoints?\b",
    r"\barchitecture\s+of\b",
    r"\bdetails?\s+(of|about|for)\b",
    r"\boverview\s+(of|for)\b",
]


def classify_query(
    question: str,
    known_services: list[str] | None = None,
) -> ClassificationResult:
    """Classify a question into a query type.

    Args:
        question: The user's natural language question.
        known_services: Optional list of known service names for matching.
            If not provided, service extraction is skipped (still classifies type).

    Returns:
        A ClassificationResult with the detected type and extracted service name.
    """
    q_lower = question.lower().strip()

    # Extract mentioned service name (if any)
    extracted_service = _extract_service_name(q_lower, known_services or [])

    # Check structural first (highest priority — cheapest to answer)
    for pattern in _STRUCTURAL_PATTERNS:
        if re.search(pattern, q_lower):
            return ClassificationResult(
                query_type=QueryType.STRUCTURAL,
                extracted_service=extracted_service,
            )

    # Check cross-service flow
    for pattern in _FLOW_PATTERNS:
        if re.search(pattern, q_lower):
            return ClassificationResult(
                query_type=QueryType.CROSS_SERVICE_FLOW,
                extracted_service=extracted_service,
            )

    # Check single-service (only if we detected a specific service)
    if extracted_service:
        for pattern in _SINGLE_SERVICE_PATTERNS:
            if re.search(pattern, q_lower):
                return ClassificationResult(
                    query_type=QueryType.SINGLE_SERVICE,
                    extracted_service=extracted_service,
                )

        # If a known service is mentioned but no flow/structural signals,
        # still treat as single_service
        word_count = len(q_lower.split())
        if word_count <= 8:
            # Short question mentioning a service → single_service
            return ClassificationResult(
                query_type=QueryType.SINGLE_SERVICE,
                extracted_service=extracted_service,
            )

    # Default: general (monolithic pipeline)
    return ClassificationResult(
        query_type=QueryType.GENERAL,
        extracted_service=extracted_service,
    )


def _extract_service_name(
    q_lower: str,
    known_services: list[str],
) -> str | None:
    """Extract a known service name from the question text.

    Resolution order:
    1. Alias-aware resolution via the dependency graph — maps human names,
       folder names, and nicknames ("booking service", "PaymentService",
       "tvsm-auth") back to the canonical service name Neo4j stores. Uses
       word-boundary + longest-match so short acronyms don't over-fire.
    2. Fallback: direct longest substring match against known_services (covers
       services present in the graph but absent from the alias file).
    """
    # 1. Alias-aware resolution (handles the friendly-name → canonical mapping)
    resolved = resolve_service(q_lower, known_services)
    if resolved:
        return resolved

    if not known_services:
        return None

    # 2. Fallback: direct longest-match against known service names
    candidates = sorted(known_services, key=len, reverse=True)
    for svc in candidates:
        if svc.lower() in q_lower:
            return svc

    return None

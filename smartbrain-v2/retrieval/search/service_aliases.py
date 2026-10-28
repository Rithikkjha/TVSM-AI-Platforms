"""Service alias resolution.

Source of truth is the repo_docs registry: ``repo_docs/registry/aliases.yaml``
merged with ``repo_docs/config/aliases.manual.yaml`` (see
:mod:`retrieval.search.entity_linker`). Neo4j ``Service`` nodes are keyed by
``service:<service_id>`` with ``name = service_id`` (loaded by
``ingestion/repo_docs_ingest/graph_loader.py``), so any alias the user types is
mapped back to that service_id.

Matching uses word boundaries and longest-first, so short acronyms ("mdp") don't
fire on substrings and "booking service" beats "booking". For ambiguous aliases
this single-answer API returns the best-ranked candidate; use
``entity_linker.resolve`` to get every candidate.
"""

from __future__ import annotations

import logging

from retrieval.search.entity_linker import get_index, resolve

logger = logging.getLogger(__name__)


def resolve_service(
    text: str,
    known_services: list[str] | None = None,
    graph_path: str | None = None,
) -> str | None:
    """Resolve a service mention in free text to a canonical service_id.

    Args:
        text: Free text to search (any case).
        known_services: Service names present in the graph. When given, only a
            candidate that is in this list is returned (falls back to a raw
            longest match against the list).
        graph_path: Optional repo_docs root override (kept for compatibility).

    Returns:
        The service_id, or ``None`` if nothing matched.
    """
    q = (text or "").strip()
    if not q:
        return None
    idx = get_index(graph_path) if graph_path else get_index()
    known_lower = {s.lower(): s for s in (known_services or [])}
    for cand in resolve(q, idx)["services"]:
        if not known_services or cand["id"].lower() in known_lower:
            return known_lower.get(cand["id"].lower(), cand["id"])
    if known_services:
        ql = q.lower()
        for svc in sorted(known_services, key=len, reverse=True):
            if svc.lower() in ql:
                return svc
    return None

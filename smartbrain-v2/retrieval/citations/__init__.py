"""Structured citation assembly and mapping for RAG Pipeline V2.

Exposes the :class:`Citation` dataclass and the pure ``format_context`` /
``parse_refs`` / ``map_citations`` functions that implement the ``[ref:N]``
citation grammar used to ground LLM answers in specific document sections.
"""

from __future__ import annotations

from retrieval.citations.citation_engine import (
    Citation,
    format_context,
    map_citations,
    parse_refs,
)

__all__ = ["Citation", "format_context", "parse_refs", "map_citations"]

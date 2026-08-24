"""Structured citation engine for RAG Pipeline V2.

Implements the ``[ref:N]`` citation grammar that lets the LLM cite specific
retrieved chunks and lets the pipeline map those markers back to structured
:class:`Citation` objects. The engine has three responsibilities:

- :func:`format_context` assigns ``[ref:1]`` .. ``[ref:N]`` markers to the
  re-ranked chunks *in order*, builds an annotated context text (each block
  prefixed with its marker and carrying the chunk's display text), and returns
  the parallel list of :class:`Citation` objects (Req 6.1, 6.4).
- :func:`parse_refs` extracts the integer ref numbers from LLM output text, in
  order of first appearance, de-duplicated (Req 6.3).
- :func:`map_citations` returns only the citations whose ref actually appears
  in the LLM output, dropping any ``[ref:N]`` marker that has no corresponding
  provided chunk (Req 6.5).

Round-trip contract (Req 6.6 / Property 10): for any list of chunks,
``parse_refs(format_context(chunks)[0])`` returns exactly ``[1, 2, ..., N]``
and the ``i``-th citation maps back to the ``i``-th chunk's ``section_title``
and ``source_ref``.

Subset contract (Property 11): ``map_citations`` always returns a subset of the
provided citations — never a marker without a backing chunk.

Duck typing
-----------
To keep this module free of a runtime import on
``retrieval.search.hybrid_retriever`` (which may not exist yet and would
create an import cycle), ``format_context`` accepts any structurally-compatible
object: it must expose a ``chunk_id`` attribute, some text attribute
(``display_text`` preferred, then ``text``), and a ``metadata`` object carrying
``section_title`` / ``source_ref`` (and optionally ``parent_source_id``). The
``ScoredChunk`` produced by the hybrid retriever satisfies this shape.

The functions are pure and deterministic: they perform no I/O.

Requirements: 6.1, 6.3, 6.4, 6.5
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime import
    from collections.abc import Iterable, Sequence

__all__ = ["Citation", "format_context", "parse_refs", "map_citations"]


# Marker grammar: ``[ref:` <int> `]``. Captures the integer ref number.
_REF_PATTERN = re.compile(r"\[ref:(\d+)\]")


@dataclass(frozen=True)
class Citation:
    """A structured citation backing a single ``[ref:N]`` marker.

    Attributes:
        ref: The 1-based marker number ``N`` in ``[ref:N]``.
        source_id: Stable identifier of the cited chunk (its ``chunk_id``).
        section_title: Nearest preceding heading or structured field name,
            copied from the chunk's metadata (Req 6.4).
        url: A clickable link for the source. Derived from ``source_ref`` when
            it looks like a URL; otherwise equal to ``source_ref``.
        source_ref: Source-type-specific reference (file path | page URL |
            ticket key) copied from the chunk's metadata (Req 6.4).
        line_range: Optional ``(start, end)`` line span within the source.
    """

    ref: int
    source_id: str
    section_title: str
    url: str
    source_ref: str
    line_range: tuple[int, int] | None = None


def _get_text(chunk: Any) -> str:
    """Return the chunk's display text, preferring ``display_text``.

    Falls back to ``text`` and finally to an empty string so a malformed chunk
    never crashes context assembly.
    """

    text = getattr(chunk, "display_text", None)
    if text is None:
        text = getattr(chunk, "text", None)
    return text if isinstance(text, str) else ""


def _get_meta_field(chunk: Any, field: str, default: str = "") -> str:
    """Read ``field`` from the chunk's ``metadata``, tolerating absence.

    Handles both attribute-style metadata (e.g. ``ChunkMetadata``) and
    mapping-style metadata (a plain ``dict``).
    """

    metadata = getattr(chunk, "metadata", None)
    if metadata is None:
        return default

    if isinstance(metadata, dict):
        value = metadata.get(field, default)
    else:
        value = getattr(metadata, field, default)

    return value if isinstance(value, str) else default


def _derive_url(source_ref: str) -> str:
    """Derive a clickable URL from ``source_ref``.

    A ``source_ref`` that is already an HTTP(S) URL (e.g. a Confluence page
    link) is used verbatim. Otherwise (file path, ticket key) there is no
    distinct URL, so the ``source_ref`` itself is returned.
    """

    lowered = source_ref.lower()
    if lowered.startswith(("http://", "https://")):
        return source_ref
    return source_ref


def format_context(chunks: "Sequence[Any] | Iterable[Any]") -> tuple[str, list[Citation]]:
    """Assign ``[ref:N]`` markers to chunks and build the annotated context.

    Chunks are numbered ``[ref:1]`` .. ``[ref:N]`` in the order provided. Each
    context block is prefixed with its marker and carries the chunk's display
    text; the parallel citation list derives its fields from each chunk's
    metadata (Req 6.1, 6.4).

    Args:
        chunks: An ordered collection of ``ScoredChunk``-like objects. Each
            must expose ``chunk_id``, a text attribute (``display_text`` or
            ``text``), and a ``metadata`` object with ``section_title`` and
            ``source_ref``.

    Returns:
        A ``(context_text, citations)`` tuple. ``context_text`` is the newline
        separated, marker-prefixed blocks; ``citations`` is the parallel list
        where ``citations[i].ref == i + 1``.
    """

    blocks: list[str] = []
    citations: list[Citation] = []

    for index, chunk in enumerate(chunks):
        ref = index + 1

        chunk_id = getattr(chunk, "chunk_id", "")
        source_id = chunk_id if isinstance(chunk_id, str) else str(chunk_id)
        section_title = _get_meta_field(chunk, "section_title")
        source_ref = _get_meta_field(chunk, "source_ref")
        text = _get_text(chunk)

        citations.append(
            Citation(
                ref=ref,
                source_id=source_id,
                section_title=section_title,
                url=_derive_url(source_ref),
                source_ref=source_ref,
                line_range=None,
            )
        )

        # Each block is prefixed with its marker so parse_refs can recover the
        # full 1..N sequence from the assembled context text (round-trip).
        blocks.append(f"[ref:{ref}] {text}".rstrip())

    context_text = "\n\n".join(blocks)
    return context_text, citations


def parse_refs(llm_output: str) -> list[int]:
    """Extract ``[ref:N]`` integer markers from LLM text.

    Args:
        llm_output: The raw text emitted by the LLM.

    Returns:
        The ref numbers in order of first appearance, de-duplicated. Returns an
        empty list when no markers are present.
    """

    seen: set[int] = set()
    ordered: list[int] = []

    for match in _REF_PATTERN.finditer(llm_output):
        ref = int(match.group(1))
        if ref in seen:
            continue
        seen.add(ref)
        ordered.append(ref)

    return ordered


def map_citations(llm_output: str, citations: list[Citation]) -> list[Citation]:
    """Return only the citations whose ref appears in the LLM output.

    Any ``[ref:N]`` marker in the output that has no corresponding provided
    citation is silently dropped (Req 6.5), so the result is always a subset of
    ``citations`` (Property 11). The returned citations preserve their original
    relative order.

    Args:
        llm_output: The raw text emitted by the LLM.
        citations: The citations produced by :func:`format_context`.

    Returns:
        The subset of ``citations`` referenced by the output, in the original
        citation order.
    """

    used_refs = set(parse_refs(llm_output))
    return [citation for citation in citations if citation.ref in used_refs]

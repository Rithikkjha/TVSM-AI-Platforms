"""Chunker protocol, dispatch, and shared derivation helpers.

This module is the shared plumbing layer that ties the source-type-aware
chunkers together. It defines:

* :class:`SourceDocument` — the normalized input every chunker consumes.
* :class:`Chunker` — the :class:`~typing.Protocol` each concrete chunker
  implements (``chunk(doc) -> list[Chunk]``).
* :func:`get_chunker` — the :class:`SourceType`-keyed dispatch that returns
  the concrete chunker for a source document.
* Shared derivation helpers (:func:`make_chunk`, :func:`build_chunks`) that
  every concrete chunker uses to construct :class:`Chunk` objects with a
  stable ``chunk_id`` and a fully-populated :class:`ChunkMetadata`, and to
  assign sequential 0-based ``chunk_index`` values.

The concrete chunkers (``markdown_chunker.py``, ``confluence_chunker.py``,
``jira_chunker.py``) are implemented in separate tasks. To keep ``base.py``
importable before those modules exist, :func:`get_chunker` resolves them via
a **lazy import** of a ``SourceType → module:class`` mapping and raises a
clear error only if a chunker is actually requested before its module is
available.

See the design document, section "Components and Interfaces > 1. Chunking",
for the authoritative interface shapes. Requirements: 2.1, 2.10, 2.11.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from processing.chunking.models import Chunk, ChunkMetadata, SourceType

__all__ = [
    "SourceDocument",
    "Chunker",
    "get_chunker",
    "make_chunk",
    "build_chunks",
]


# ---------------------------------------------------------------------------
# Chunker input
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceDocument:
    """Normalized input consumed by every :class:`Chunker`.

    A ``SourceDocument`` carries the raw content plus the metadata every
    chunker needs to derive :class:`ChunkMetadata` for the chunks it
    produces. The content shape is deliberately flexible so a single type
    serves all source types:

    * **Markdown / Confluence** documents populate :attr:`text` (the markdown
      body, or the HTML storage content the Confluence chunker normalizes
      first) and leave :attr:`fields` as ``None``.
    * **Jira** tickets populate :attr:`fields` (an ordered mapping of field
      name → field text, e.g. ``{"Summary": ..., "Description": ...}``) and
      leave :attr:`text` as ``None``.

    Attributes:
        source_type: Origin category used to select the concrete chunker.
        parent_source_id: ``source_id`` of the full-document entity these
            chunks are derived from; becomes
            :attr:`ChunkMetadata.parent_source_id` (Req 2.11).
        repo_name: Repository the document belongs to.
        source_ref: Source-type-specific origin reference — file path
            (steering), page URL (Confluence), or ticket key (Jira).
        doc_type: Document type discriminator
            (``product`` | ``structure`` | ``tech`` | ``confluence`` | ``jira``).
        text: Raw body for markdown/Confluence documents; ``None`` for Jira.
        fields: Ordered field-name → field-text mapping for Jira tickets;
            ``None`` for markdown/Confluence.
        title: Optional document title / top-level heading context (for
            example the Confluence page title or the ticket key) that a
            chunker may use when deriving prepended context. Does not affect
            dispatch.
    """

    source_type: SourceType
    parent_source_id: str
    repo_name: str
    source_ref: str
    doc_type: str
    text: str | None = None
    fields: dict[str, str] | None = None
    title: str | None = None


# ---------------------------------------------------------------------------
# Chunker protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Chunker(Protocol):
    """Splits one :class:`SourceDocument` into ordered, metadata-bearing chunks."""

    def chunk(self, doc: SourceDocument) -> list[Chunk]:
        """Split one document into ordered, metadata-bearing chunks.

        Implementations return chunks in document order with sequential,
        0-based :attr:`ChunkMetadata.chunk_index` values (Req 2.10).
        """
        ...


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

#: Maps each :class:`SourceType` to the ``"module:ClassName"`` of the concrete
#: chunker that handles it. Resolved lazily by :func:`get_chunker` so this
#: module imports cleanly before the concrete chunker modules exist.
_CHUNKER_REGISTRY: dict[SourceType, str] = {
    SourceType.STEERING_FILE: "processing.chunking.markdown_chunker:MarkdownChunker",
    SourceType.CONFLUENCE_PAGE: "processing.chunking.confluence_chunker:ConfluenceChunker",
    SourceType.JIRA_TICKET: "processing.chunking.jira_chunker:JiraChunker",
}


def get_chunker(source_type: SourceType) -> Chunker:
    """Return the :class:`Chunker` registered for ``source_type``.

    The concrete chunker class is resolved and instantiated lazily: its
    module is imported only when this function is called, so importing
    :mod:`processing.chunking.base` never hard-fails just because a concrete
    chunker module has not been implemented yet.

    Args:
        source_type: The source category to dispatch on.

    Returns:
        A freshly constructed instance of the concrete chunker for
        ``source_type``.

    Raises:
        ValueError: If ``source_type`` has no registered chunker.
        ImportError: If the registered chunker module or class cannot be
            imported (for example, before the concrete chunker task has been
            implemented). The message names the missing target.
    """

    target = _CHUNKER_REGISTRY.get(source_type)
    if target is None:
        raise ValueError(f"No chunker registered for source_type {source_type!r}")

    module_path, _, class_name = target.partition(":")
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ImportError(
            f"Chunker module {module_path!r} for source_type {source_type!r} "
            f"is not available yet: {exc}"
        ) from exc

    try:
        chunker_cls = getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(
            f"Chunker class {class_name!r} not found in module {module_path!r} "
            f"for source_type {source_type!r}"
        ) from exc

    return chunker_cls()


# ---------------------------------------------------------------------------
# Shared derivation helpers
# ---------------------------------------------------------------------------


def make_chunk(
    *,
    parent_source_id: str,
    chunk_index: int,
    display_text: str,
    original_segment: str,
    section_title: str,
    repo_name: str,
    source_ref: str,
    doc_type: str,
) -> Chunk:
    """Build a single :class:`Chunk` with a stable id and full metadata.

    The ``chunk_id`` is derived deterministically as
    ``f"{parent_source_id}#chunk:{chunk_index}"`` and the accompanying
    :class:`ChunkMetadata` is populated from the supplied fields (Req 2.1).

    Args:
        parent_source_id: ``source_id`` of the parent document entity
            (Req 2.11).
        chunk_index: 0-based sequential position within the parent document
            (Req 2.10).
        display_text: Context-prepended text used for embedding / re-ranking.
        original_segment: Raw source text for lossless round-trip reassembly.
        section_title: Nearest preceding heading or structured field name.
        repo_name: Repository the parent document belongs to.
        source_ref: File path | page URL | ticket key.
        doc_type: Document type discriminator.

    Returns:
        A fully-constructed :class:`Chunk`.
    """

    metadata = ChunkMetadata(
        section_title=section_title,
        parent_source_id=parent_source_id,
        repo_name=repo_name,
        chunk_index=chunk_index,
        source_ref=source_ref,
        doc_type=doc_type,
    )
    return Chunk(
        chunk_id=f"{parent_source_id}#chunk:{chunk_index}",
        display_text=display_text,
        original_segment=original_segment,
        metadata=metadata,
    )


def build_chunks(
    doc: SourceDocument,
    segments: list[tuple[str, str, str]],
) -> list[Chunk]:
    """Build an ordered list of chunks with sequential 0-based indices.

    This is the shared assembly step every concrete chunker funnels its
    final segments through: it assigns ``chunk_index`` values 0, 1, 2, …
    (Req 2.10) and copies the shared metadata (``parent_source_id``,
    ``repo_name``, ``source_ref``, ``doc_type``) from ``doc`` onto each
    chunk (Req 2.1, 2.11).

    Args:
        doc: The source document supplying shared metadata.
        segments: Ordered ``(display_text, original_segment, section_title)``
            triples, one per chunk, in document order.

    Returns:
        Chunks in the same order as ``segments`` with sequential indices.
    """

    return [
        make_chunk(
            parent_source_id=doc.parent_source_id,
            chunk_index=index,
            display_text=display_text,
            original_segment=original_segment,
            section_title=section_title,
            repo_name=doc.repo_name,
            source_ref=doc.source_ref,
            doc_type=doc.doc_type,
        )
        for index, (display_text, original_segment, section_title) in enumerate(
            segments
        )
    ]

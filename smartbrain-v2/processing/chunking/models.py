"""Chunk domain models for RAG Pipeline V2.

Defines the first-class ``Chunk`` entity produced by the source-type-aware
chunkers, along with its structured ``ChunkMetadata`` and the ``SourceType``
enumeration used to dispatch to the correct chunker.

See the design document, section "Components and Interfaces > 2. Chunk
metadata", for the authoritative field shapes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = ["SourceType", "ChunkMetadata", "Chunk"]


class SourceType(StrEnum):
    """Origin category of a source document.

    The value is the stable string persisted in metadata and used to select
    the appropriate chunker during ingestion.
    """

    STEERING_FILE = "steering"
    CONFLUENCE_PAGE = "confluence"
    JIRA_TICKET = "jira"


@dataclass(frozen=True)
class ChunkMetadata:
    """Structured metadata attached to every chunk.

    Attributes:
        section_title: Nearest preceding heading (markdown/Confluence) or the
            structured field name (Jira).
        parent_source_id: ``source_id`` of the full-document entity this chunk
            was derived from.
        repo_name: Repository the parent document belongs to.
        chunk_index: 0-based sequential position of the chunk within its
            parent document.
        source_ref: Source-type-specific reference locating the origin content
            (file path | page URL | ticket key).
        doc_type: Document type discriminator
            (``product`` | ``structure`` | ``tech`` | ``confluence`` | ``jira``).
    """

    section_title: str
    parent_source_id: str
    repo_name: str
    chunk_index: int
    source_ref: str
    doc_type: str


@dataclass(frozen=True)
class Chunk:
    """A semantically coherent, metadata-bearing text segment.

    Attributes:
        chunk_id: Stable identifier formatted as
            ``f"{parent_source_id}#chunk:{chunk_index}"``.
        display_text: Context-prepended text used for embedding and re-ranking.
        original_segment: Raw source text used for lossless round-trip
            reassembly.
        metadata: The associated :class:`ChunkMetadata`.
    """

    chunk_id: str
    display_text: str
    original_segment: str
    metadata: ChunkMetadata

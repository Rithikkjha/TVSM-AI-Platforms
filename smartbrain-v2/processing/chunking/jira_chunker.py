"""Field-boundary chunker for Jira tickets.

This module implements :class:`JiraChunker`, the concrete
:class:`~processing.chunking.base.Chunker` for :class:`SourceType.JIRA_TICKET`
documents. Unlike the markdown/Confluence chunkers — which recover structure
from heading prose — Jira input is *already* structured: a
:class:`~processing.chunking.base.SourceDocument` for a ticket carries its
content in ``doc.fields``, an **ordered** mapping of field name → field text
(for example ``{"Summary": ..., "Description": ...,
"Acceptance Criteria": ..., "Comment 1": ..., "Comment 2": ...}``).

Chunking strategy (design §1, Req 1.3):

* Each structured field — summary, description, acceptance criteria, and
  *each* comment — is treated as its own logical section.
* ``section_title`` is the field's structured name (Req 2.6). Enumerated
  comment fields (``"Comment 1"``, ``"Comment 2"``) collapse to the generic
  ``"Comment"`` title so the metadata matches the shape called out in the
  requirement's examples; the *display* prefix still carries the original
  field name so distinct comments stay distinguishable.
* Each field's ``display_text`` is prefixed with ``"{TICKET-KEY} — {Field
  Name}"`` (Req 1.8) while ``original_segment`` retains the **raw** field text
  with no prefix, preserving the round-trip contract (Req 1.9).
* ``doc_type`` is ``"jira"`` (Req 2.4) and ``source_ref`` is the ticket key
  (Req 2.9), both supplied on the incoming ``doc`` and copied through by
  :func:`~processing.chunking.base.build_chunks`.

**Size normalization.** Each field is independently run through
:func:`~processing.chunking.tokenizer.split_oversized` so no resulting chunk
exceeds 500 tokens (Req 1.4/1.5). We deliberately **do not** apply
cross-field :func:`~processing.chunking.tokenizer.merge_undersized`: because
every field is its own section with its own ``section_title``, merging two
different fields (e.g. Summary + Description) into one chunk would erase that
per-field title distinction. Keeping fields as distinct chunks is the more
useful behaviour for structured Jira content, and an undersized final field
simply remains its own (small) chunk — the same outcome the shared tokenizer
already permits for a trailing undersized section.

**Round-trip (Req 1.9).** Concatenating every chunk's ``original_segment`` in
``chunk_index`` order reproduces the concatenation of the field texts in field
order. Fields that fit within the token budget are emitted verbatim as a
single segment; only oversized fields are subdivided (via the shared
tokenizer's paragraph/sentence cascade).
"""

from __future__ import annotations

import re

from processing.chunking.base import SourceDocument, build_chunks
from processing.chunking.models import Chunk
from processing.chunking.tokenizer import DEFAULT_MAX_TOKENS, split_oversized

__all__ = ["JiraChunker"]


#: Em dash used to join the ticket key and field name in the display prefix
#: (Req 1.8): ``"{TICKET-KEY} — {Field Name}"``.
_PREFIX_SEPARATOR = " — "

#: Matches an enumerated comment field name such as ``"Comment 1"`` or
#: ``"comment 12"`` (case-insensitive) so its ``section_title`` collapses to
#: the generic ``"Comment"`` (Req 2.6).
_COMMENT_FIELD_RE = re.compile(r"^\s*comment\b\s*\d*\s*$", re.IGNORECASE)

#: Canonical section title for any comment field.
_COMMENT_SECTION_TITLE = "Comment"


class JiraChunker:
    """Split a structured Jira ticket into ordered, per-field chunks.

    Implements the :class:`~processing.chunking.base.Chunker` protocol.
    Registered for :class:`SourceType.JIRA_TICKET` via
    :func:`~processing.chunking.base.get_chunker`
    (``"processing.chunking.jira_chunker:JiraChunker"``).
    """

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        """Create a chunker.

        Args:
            max_tokens: Upper token bound per chunk; oversized fields are
                split to respect it (Req 1.4/1.5). Defaults to the shared
                :data:`~processing.chunking.tokenizer.DEFAULT_MAX_TOKENS`.
        """

        self._max_tokens = max_tokens

    def chunk(self, doc: SourceDocument) -> list[Chunk]:
        """Split ``doc`` into ordered, metadata-bearing per-field chunks.

        Args:
            doc: The Jira source document. Its ``fields`` attribute supplies
                the ordered field-name → field-text mapping; ``source_ref``
                (or ``title``) supplies the ticket key.

        Returns:
            Chunks in field order with sequential 0-based ``chunk_index``
            values. Empty (falsy) field texts are skipped so no empty chunk
            is produced. Returns ``[]`` when the document carries no fields.
        """

        fields = doc.fields
        if not fields:
            return []

        ticket_key = self._ticket_key(doc)

        segments: list[tuple[str, str, str]] = []
        for field_name, field_text in fields.items():
            if not field_text:
                # Skip empty/None fields: they contribute nothing to the
                # round-trip concatenation and would only add empty chunks.
                continue

            section_title = self._section_title(field_name)
            prefix = self._display_prefix(ticket_key, field_name)

            # Split only oversized fields; each piece keeps the raw text as
            # its original_segment (no prefix) for the round-trip contract.
            for piece in split_oversized(field_text, self._max_tokens):
                display_text = f"{prefix}\n\n{piece}"
                segments.append((display_text, piece, section_title))

        return build_chunks(doc, segments)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _ticket_key(doc: SourceDocument) -> str:
        """Resolve the ticket key from the document.

        Prefers ``doc.title`` (the caller-provided ticket key context) and
        falls back to ``doc.source_ref``, which is defined to be the ticket
        key for Jira tickets (Req 2.9). Returns an empty string if neither is
        set, so the prefix still forms a valid ``" — {Field}"`` string.
        """

        return doc.title or doc.source_ref or ""

    @staticmethod
    def _section_title(field_name: str) -> str:
        """Derive the ``section_title`` for a field (Req 2.6).

        Enumerated comment fields (``"Comment 1"``, ``"Comment 2"``, …)
        collapse to the generic ``"Comment"``; every other field keeps its
        name verbatim.
        """

        if _COMMENT_FIELD_RE.match(field_name):
            return _COMMENT_SECTION_TITLE
        return field_name

    @staticmethod
    def _display_prefix(ticket_key: str, field_name: str) -> str:
        """Build the ``"{TICKET-KEY} — {Field Name}"`` display prefix (Req 1.8).

        Uses the *original* field name (not the collapsed section title) so
        distinct comments remain distinguishable in the embedded text.
        """

        return f"{ticket_key}{_PREFIX_SEPARATOR}{field_name}"

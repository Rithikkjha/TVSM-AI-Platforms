"""Confluence page chunker (Req 1.2, 1.7, 2.3, 2.5, 2.8).

``ConfluenceChunker`` turns a Confluence page :class:`SourceDocument` (whose
``doc.text`` is Confluence HTML storage content) into an ordered list of
:class:`Chunk` objects using the *same* heading-aware splitting strategy as
:mod:`processing.chunking.markdown_chunker`.

The strategy, per the design (section "Components and Interfaces > 1.
Chunking"):

1. **HTML normalization.** Confluence storage-format HTML is parsed with
   :mod:`html.parser` (stdlib) to produce a lightweight structural model:
   ``<h1>``–``<h4>`` tags become ATX-style heading lines (``# Title`` …
   ``#### Title``), and all other block-level text (``<p>``, ``<div>``,
   ``<li>``, ``<td>``, ``<pre>``, naked text) becomes plain-text paragraphs.
   Inline HTML entities and nested tags are reduced to their text content.
2. **Heading-split + ancestor-prepend + size-normalization.** The normalized
   text is processed through the *exact* same pipeline that
   :class:`~processing.chunking.markdown_chunker.MarkdownChunker` uses:
   heading partition → oversized-section split → undersized-section merge →
   context-prepend segment assembly. This is achieved by delegating to an
   internal ``MarkdownChunker`` instance configured with matching token bounds.
3. **Metadata.** ``doc_type="confluence"`` (Req 2.3) and ``source_ref`` from
   ``doc.source_ref`` (page URL, Req 2.8) are passed through unmodified by
   the shared :func:`~processing.chunking.base.build_chunks` helper.

**Round-trip contract (Req 1.9).** Because the normalized text is constructed
deterministically from the HTML source, and the markdown chunker maintains
exact-substring ``original_segment`` values over that normalized text, the
round-trip holds over the *normalized* representation. The raw HTML is not
preserved verbatim in ``original_segment`` — the normalization step is lossy
with respect to HTML formatting but preserves all textual content.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

from processing.chunking.base import SourceDocument, build_chunks
from processing.chunking.markdown_chunker import MarkdownChunker
from processing.chunking.models import Chunk
from processing.chunking.tokenizer import DEFAULT_MAX_TOKENS, DEFAULT_MIN_TOKENS

__all__ = ["ConfluenceChunker"]


# ---------------------------------------------------------------------------
# HTML → normalized text conversion
# ---------------------------------------------------------------------------

#: Heading tags that map to ATX heading levels.
_HEADING_TAGS: dict[str, int] = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}

#: Block-level tags whose content starts a new paragraph.
_BLOCK_TAGS: frozenset[str] = frozenset(
    {
        "p",
        "div",
        "li",
        "td",
        "th",
        "tr",
        "blockquote",
        "pre",
        "section",
        "article",
        "header",
        "footer",
        "figcaption",
        "dt",
        "dd",
    }
)

#: Tags that produce a line break but no paragraph separation.
_BREAK_TAGS: frozenset[str] = frozenset({"br", "hr"})

#: Tags that should be completely ignored (no text contribution).
_SKIP_TAGS: frozenset[str] = frozenset(
    {"script", "style", "head", "meta", "link", "noscript"}
)

#: Collapse runs of blank lines to at most two newlines (one blank line).
_BLANK_COLLAPSE_RE = re.compile(r"\n{3,}")

#: Collapse multiple spaces/tabs on a single line.
_SPACE_COLLAPSE_RE = re.compile(r"[ \t]{2,}")


class _HTMLToTextParser(HTMLParser):
    """Lightweight Confluence HTML storage → normalized text converter.

    Extracts heading tags (h1–h4) as ATX-style markdown heading lines and
    all other text content as plain paragraphs separated by blank lines.
    The output is suitable for feeding directly into :class:`MarkdownChunker`.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._in_heading: int = 0  # current heading level (0 = not in heading)
        self._heading_text: list[str] = []
        self._skip_depth: int = 0  # depth counter for skipped tags

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()

        if tag_lower in _SKIP_TAGS:
            self._skip_depth += 1
            return

        if self._skip_depth > 0:
            return

        if tag_lower in _HEADING_TAGS:
            # Flush any pending text before the heading.
            self._in_heading = _HEADING_TAGS[tag_lower]
            self._heading_text = []
            return

        if tag_lower in _BLOCK_TAGS:
            self._parts.append("\n\n")
            return

        if tag_lower in _BREAK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()

        if tag_lower in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return

        if self._skip_depth > 0:
            return

        if tag_lower in _HEADING_TAGS and self._in_heading > 0:
            # Emit the heading as an ATX line.
            title = " ".join(self._heading_text).strip()
            if title:
                prefix = "#" * self._in_heading
                self._parts.append(f"\n\n{prefix} {title}\n\n")
            self._in_heading = 0
            self._heading_text = []
            return

        if tag_lower in _BLOCK_TAGS:
            self._parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return

        if self._in_heading > 0:
            self._heading_text.append(data)
        else:
            self._parts.append(data)

    def get_text(self) -> str:
        """Return the normalized text suitable for heading-aware chunking."""
        raw = "".join(self._parts)
        # Collapse excessive blank lines.
        text = _BLANK_COLLAPSE_RE.sub("\n\n", raw)
        # Collapse inline whitespace runs.
        text = _SPACE_COLLAPSE_RE.sub(" ", text)
        return text.strip()


def _normalize_html(html: str) -> str:
    """Convert Confluence HTML storage content to normalized heading/paragraph text."""
    parser = _HTMLToTextParser()
    parser.feed(html)
    return parser.get_text()


# ---------------------------------------------------------------------------
# ConfluenceChunker
# ---------------------------------------------------------------------------


class ConfluenceChunker:
    """Split a Confluence page into metadata-bearing chunks.

    Implements the :class:`~processing.chunking.base.Chunker` protocol and is
    resolved by :func:`~processing.chunking.base.get_chunker` for
    :attr:`~processing.chunking.models.SourceType.CONFLUENCE_PAGE`.

    The HTML storage content is first normalized to a heading/paragraph text
    model, then processed through the same heading-split + ancestor-prepend +
    split/merge pipeline that
    :class:`~processing.chunking.markdown_chunker.MarkdownChunker` uses.
    """

    def __init__(
        self,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        min_tokens: int = DEFAULT_MIN_TOKENS,
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        if min_tokens <= 0:
            raise ValueError("min_tokens must be a positive integer")
        self._max_tokens = max_tokens
        self._min_tokens = min_tokens
        # Reuse the markdown chunker for the core splitting logic.
        self._md_chunker = MarkdownChunker(
            max_tokens=max_tokens, min_tokens=min_tokens
        )

    def chunk(self, doc: SourceDocument) -> list[Chunk]:
        """Split ``doc`` into ordered chunks.

        The ``doc.text`` field is expected to contain Confluence HTML storage
        content. It is normalized to a heading/paragraph text model, then
        chunked using the markdown heading-split pipeline.

        Returns an empty list for a document with no body text. Chunks carry
        sequential 0-based ``chunk_index`` values.
        """
        html_content = doc.text
        if not html_content:
            return []

        # Step 1: Normalize HTML to heading/paragraph text.
        normalized_text = _normalize_html(html_content)
        if not normalized_text:
            return []

        # Step 2: Create a proxy document with normalized text for the
        # markdown chunker's internal partition/split/merge pipeline.
        # We delegate to the markdown chunker's internal methods directly
        # rather than calling chunk() so we keep the original doc's metadata.
        text = normalized_text
        spans = self._md_chunker._partition(text)
        leaves = self._md_chunker._split_oversized_spans(text, spans)
        merged = self._md_chunker._merge_undersized_spans(text, leaves)

        segments: list[tuple[str, str, str]] = [
            self._md_chunker._to_segment(text, span) for span in merged
        ]

        # Step 3: Build chunks with the original doc's metadata (doc_type,
        # source_ref, parent_source_id, repo_name all flow through).
        return build_chunks(doc, segments)

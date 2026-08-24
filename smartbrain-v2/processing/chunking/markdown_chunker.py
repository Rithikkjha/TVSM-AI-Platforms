"""Heading-aware chunker for steering-file markdown (Req 1.1, 1.7, 2.2, 2.5, 2.7).

``MarkdownChunker`` turns a steering-file :class:`SourceDocument` (product /
structure / tech markdown) into an ordered list of :class:`Chunk` objects.

The strategy, per the design (section "Components and Interfaces > 1.
Chunking"):

1. **Heading split (Req 1.1).** The markdown body is partitioned at H1–H4
   heading boundaries into raw sections. Headings inside fenced code blocks
   (```` ``` ```` / ``~~~``) are ignored so code samples do not fracture a
   section.
2. **Size normalization (Req 1.4–1.6).** Oversized raw sections are split at
   paragraph/sentence boundaries via
   :func:`processing.chunking.tokenizer.split_oversized`; adjacent undersized
   pieces from the same document are then merged up to the minimum, mirroring
   :func:`processing.chunking.tokenizer.merge_undersized`. Both use the shared
   :func:`processing.chunking.tokenizer.count_tokens` so the 200–500-token
   target holds.
3. **Context prepend (Req 1.7).** Each chunk's ``display_text`` prepends the
   ancestor heading path (e.g. ``"# Tech Stack > ## Dependencies"``) followed
   by a blank line and the section body.
4. **Metadata (Req 2.2, 2.5, 2.7).** ``section_title`` is the nearest
   preceding heading; ``doc_type`` (product/structure/tech) and ``source_ref``
   (file path) are copied from the document by
   :func:`processing.chunking.base.build_chunks`.

**Round-trip contract (Req 1.9).** ``original_segment`` is always an *exact
substring* of ``doc.text``. Because size normalization is performed over
character *offset spans* — never over the whitespace-normalized text the
tokenizer emits — the raw sections form a lossless, contiguous partition of the
body. Concatenating every chunk's ``original_segment`` in ``chunk_index`` order
therefore reproduces ``doc.text`` exactly. The prepended ancestor path lives
only in ``display_text`` and is excluded from reassembly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from processing.chunking.base import SourceDocument, build_chunks
from processing.chunking.models import Chunk
from processing.chunking.tokenizer import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MIN_TOKENS,
    count_tokens,
    split_oversized,
)

__all__ = ["MarkdownChunker"]


#: Matches an ATX heading of level 1–4 (``#``–``####``) with at least one
#: non-space character in the title. Level 5–6 headings are treated as body
#: text (Req 1.1 scopes the split to H1–H4).
_HEADING_RE = re.compile(r"^(#{1,4})[ \t]+(\S.*?)[ \t]*$")

#: Matches the fence marker that opens or closes a fenced code block.
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


@dataclass
class _Span:
    """A contiguous ``[start, end)`` slice of the document body.

    ``heading_line`` is the exact heading line that opens the span (or ``None``
    for pre-heading preamble and for continuation pieces produced by an
    oversized-section split). ``title`` is the nearest preceding heading text
    (Req 2.5) and ``path`` is the ancestor heading stack, each element already
    formatted as ``"<hashes> <title>"`` for the Req 1.7 context prefix.
    """

    start: int
    end: int
    heading_line: str | None
    title: str
    path: list[str]


class MarkdownChunker:
    """Split a steering-file markdown document into metadata-bearing chunks.

    Implements the :class:`processing.chunking.base.Chunker` protocol and is
    resolved by :func:`processing.chunking.base.get_chunker` for
    :attr:`~processing.chunking.models.SourceType.STEERING_FILE`.
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

    # -- public API --------------------------------------------------------

    def chunk(self, doc: SourceDocument) -> list[Chunk]:
        """Split ``doc`` into ordered chunks (see module docstring).

        Returns an empty list for a document with no body text. Chunks carry
        sequential 0-based ``chunk_index`` values assigned by
        :func:`processing.chunking.base.build_chunks`.
        """

        text = doc.text
        if not text:
            return []

        spans = self._partition(text)
        leaves = self._split_oversized_spans(text, spans)
        merged = self._merge_undersized_spans(text, leaves)

        segments: list[tuple[str, str, str]] = [
            self._to_segment(text, span) for span in merged
        ]
        return build_chunks(doc, segments)

    # -- heading partition (Req 1.1) --------------------------------------

    def _partition(self, text: str) -> list[_Span]:
        """Partition ``text`` into contiguous heading-bounded spans.

        The returned spans tile ``text`` with no gaps or overlaps: an optional
        preamble span covers any content before the first heading, then one
        span per H1–H4 heading runs to the next heading (or end of document).
        """

        lines = text.splitlines(keepends=True)
        offsets: list[int] = []
        cursor = 0
        for line in lines:
            offsets.append(cursor)
            cursor += len(line)

        headings: list[tuple[int, int, str, str]] = []  # (offset, level, title, line)
        in_fence = False
        for index, line in enumerate(lines):
            if _FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            stripped = line.rstrip("\r\n")
            match = _HEADING_RE.match(stripped)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append((offsets[index], level, title, stripped))

        if not headings:
            return [_Span(0, len(text), None, "", [])]

        spans: list[_Span] = []

        first_start = headings[0][0]
        if first_start > 0:
            # Pre-heading preamble: no nearest preceding heading yet.
            spans.append(_Span(0, first_start, None, "", []))

        stack: list[tuple[int, str]] = []  # (level, "<hashes> <title>")
        for pos, (start, level, title, line) in enumerate(headings):
            end = headings[pos + 1][0] if pos + 1 < len(headings) else len(text)
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, f"{'#' * level} {title}"))
            path = [element for _, element in stack]
            spans.append(_Span(start, end, line, title, path))

        return spans

    # -- oversized split (Req 1.5) ----------------------------------------

    def _split_oversized_spans(
        self, text: str, spans: list[_Span]
    ) -> list[_Span]:
        """Split any span exceeding ``max_tokens`` into offset-exact pieces.

        The tokenizer's :func:`split_oversized` decides the split points
        (paragraph → sentence → hard token boundary). Its whitespace-normalized
        output is then re-aligned back onto the original character offsets so
        the pieces remain exact substrings (round-trip, Req 1.9).
        """

        leaves: list[_Span] = []
        for span in spans:
            segment_text = text[span.start : span.end]
            if count_tokens(segment_text) <= self._max_tokens:
                leaves.append(span)
                continue

            pieces = split_oversized(segment_text, self._max_tokens)
            for offset, (piece_start, piece_end) in enumerate(
                _align_pieces(segment_text, pieces)
            ):
                leaves.append(
                    _Span(
                        span.start + piece_start,
                        span.start + piece_end,
                        # Only the first piece retains the heading line; later
                        # pieces are continuations with no leading heading.
                        span.heading_line if offset == 0 else None,
                        span.title,
                        span.path,
                    )
                )
        return leaves

    # -- undersized merge (Req 1.6) ---------------------------------------

    def _merge_undersized_spans(
        self, text: str, leaves: list[_Span]
    ) -> list[_Span]:
        """Merge adjacent undersized spans up to ``min_tokens``.

        Mirrors :func:`processing.chunking.tokenizer.merge_undersized`: because
        every span originates from the same document, adjacent spans are always
        eligible to merge. Merged spans are contiguous, so extending the buffer
        to the next span's ``end`` keeps ``original_segment`` an exact
        substring. The final span may remain below the minimum when nothing
        follows it.
        """

        if not leaves:
            return []

        merged: list[_Span] = []
        buffer = leaves[0]
        buffer_tokens = count_tokens(text[buffer.start : buffer.end])

        for leaf in leaves[1:]:
            if buffer_tokens >= self._min_tokens:
                merged.append(buffer)
                buffer = leaf
                buffer_tokens = count_tokens(text[leaf.start : leaf.end])
                continue

            # Buffer undersized: absorb the next contiguous span, keeping the
            # buffer's heading context (its nearest preceding heading).
            buffer = _Span(
                buffer.start,
                leaf.end,
                buffer.heading_line,
                buffer.title,
                buffer.path,
            )
            buffer_tokens = count_tokens(text[buffer.start : buffer.end])

        merged.append(buffer)
        return merged

    # -- segment assembly (Req 1.7, 2.5) ----------------------------------

    def _to_segment(self, text: str, span: _Span) -> tuple[str, str, str]:
        """Build the ``(display_text, original_segment, section_title)`` triple.

        ``original_segment`` is the exact span slice (round-trip). ``display_text``
        prepends the ancestor heading path (Req 1.7); the section's own heading
        line is dropped from the body to avoid duplicating it under the path.
        """

        original = text[span.start : span.end]

        body = original
        if span.heading_line is not None:
            newline = original.find("\n")
            body = "" if newline == -1 else original[newline + 1 :]

        content = body.strip()
        prefix = " > ".join(span.path)

        if prefix:
            display_text = f"{prefix}\n\n{content}" if content else prefix
        else:
            display_text = content or original

        return display_text, original, span.title


def _align_pieces(
    segment_text: str, pieces: list[str]
) -> list[tuple[int, int]]:
    """Map tokenizer split ``pieces`` back onto exact offsets in ``segment_text``.

    :func:`split_oversized` preserves the order of all non-whitespace characters
    and only normalizes whitespace at split/join points. Walking ``segment_text``
    and consuming, per piece, the same count of non-whitespace characters lets
    us recover contiguous ``[start, end)`` spans that tile ``segment_text``
    exactly. Whitespace at a boundary is attached to the following piece; the
    final piece extends to the end so all trailing whitespace is retained.
    """

    spans: list[tuple[int, int]] = []
    local = 0
    length = len(segment_text)
    last = len(pieces) - 1

    for index, piece in enumerate(pieces):
        if index == last:
            spans.append((local, length))
            local = length
            break

        target = sum(1 for char in piece if not char.isspace())
        cursor = local
        seen = 0
        while cursor < length and seen < target:
            if not segment_text[cursor].isspace():
                seen += 1
            cursor += 1
        spans.append((local, cursor))
        local = cursor

    return spans

"""Token counting and size-normalization utilities for chunking.

This module is the shared token layer used by all source-type-aware
chunkers (steering / Confluence / Jira). It is intentionally
**self-contained** — it operates on plain strings or a small internal
:class:`Section` value and does not depend on the richer ``Chunk`` /
``ChunkMetadata`` domain models (those wire tokenizer output into chunks
in later steps).

It provides three pieces of behaviour required by the chunker
(Requirements 1.4–1.6):

* :func:`count_tokens` — token count via :mod:`tiktoken` using the
  ``cl100k_base`` encoding (the encoding used by
  ``text-embedding-3-large`` in :mod:`processing.embeddings.service`),
  with a character-based heuristic fallback (``len // 4``) when
  :mod:`tiktoken` is unavailable or raises.
* :func:`split_oversized` — split a section that exceeds ``max_tokens``
  at paragraph boundaries first, then sentence boundaries, then — as a
  last resort — a hard token-boundary split (Req 1.5).
* :func:`merge_undersized` — merge adjacent sections from the *same*
  source document until each reaches ``min_tokens``; the final chunk may
  remain below the minimum when there is nothing left to merge (Req 1.6).

The default bounds (200 / 500 tokens) mirror ``chunk_min_tokens`` /
``chunk_max_tokens`` in :mod:`config.settings` and the design's
200–500-token chunk-sizing target.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Encoding used by ``text-embedding-3-large``. Kept identical to the
#: embedding service so token counts here match what the embedding API
#: eventually sees.
_ENCODING_NAME: str = "cl100k_base"

#: Approximate character-to-token ratio for the char-based fallback. Four
#: chars per token is the commonly cited heuristic for English text with
#: OpenAI BPE tokenizers (matches ``processing.embeddings.service``).
_CHARS_PER_TOKEN_FALLBACK: int = 4

#: Default upper bound on tokens per chunk (Req 1.4/1.5).
DEFAULT_MAX_TOKENS: int = 500

#: Default lower bound on tokens per chunk (Req 1.4/1.6).
DEFAULT_MIN_TOKENS: int = 200

#: Splits text into paragraphs on one-or-more blank lines.
_PARAGRAPH_RE = re.compile(r"\n\s*\n")

#: Sentence terminator followed by whitespace. Deliberately simple: the
#: goal is a reasonable secondary split point, not linguistically perfect
#: sentence segmentation.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


# ---------------------------------------------------------------------------
# Lightweight section value
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Section:
    """A raw text segment awaiting size normalization.

    ``source_id`` groups sections by their originating document so
    :func:`merge_undersized` only ever merges adjacent sections that came
    from the *same* source (Req 1.6). ``title`` is optional context (for
    example the nearest heading) carried through splits and merges for the
    convenience of downstream chunkers; it does not affect token math.
    """

    text: str
    source_id: str | None = None
    title: str | None = None


# A section-like input accepted by the split/merge helpers.
SectionLike = str | Section


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------


def count_tokens(text: str) -> int:
    """Return the number of tokens in ``text``.

    Uses :mod:`tiktoken` with the ``cl100k_base`` encoding when available.
    If :mod:`tiktoken` cannot be imported or raises during encoding, falls
    back to a ``len(text) // _CHARS_PER_TOKEN_FALLBACK`` heuristic and logs
    a warning once per failure.

    An empty string counts as zero tokens.
    """

    if not text:
        return 0

    encoding = _get_encoding()
    if encoding is not None:
        try:
            return len(encoding.encode(text))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "tiktoken encode failed (%s); using char-based token estimate",
                exc,
            )

    return _fallback_token_count(text)


def _fallback_token_count(text: str) -> int:
    """Character-heuristic token estimate used when tiktoken is unusable."""

    return len(text) // _CHARS_PER_TOKEN_FALLBACK


# Module-level cache for the encoding object. ``False`` means "we tried and
# it isn't available"; ``None`` means "not yet attempted".
_ENCODING_CACHE: object | None | bool = None


def _get_encoding():  # type: ignore[no-untyped-def]
    """Load and memoize the tiktoken encoding, or ``None`` if unavailable."""

    global _ENCODING_CACHE
    if _ENCODING_CACHE is False:
        return None
    if _ENCODING_CACHE is not None:
        return _ENCODING_CACHE

    try:
        import tiktoken  # local import to keep import cost lazy
    except ImportError:
        logger.warning(
            "tiktoken unavailable; token counts use a char-based heuristic"
        )
        _ENCODING_CACHE = False
        return None

    try:
        _ENCODING_CACHE = tiktoken.get_encoding(_ENCODING_NAME)
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning(
            "failed to load tiktoken encoding %r (%s); using char heuristic",
            _ENCODING_NAME,
            exc,
        )
        _ENCODING_CACHE = False
        return None

    return _ENCODING_CACHE


# ---------------------------------------------------------------------------
# Section <-> text helpers
# ---------------------------------------------------------------------------


def _as_text(section: SectionLike) -> str:
    """Return the raw text of a string- or :class:`Section`-typed input."""

    if isinstance(section, Section):
        return section.text
    return section


def _source_id(section: SectionLike) -> str | None:
    """Return the grouping source id, or ``None`` for plain strings."""

    if isinstance(section, Section):
        return section.source_id
    return None


def _rebuild(template: SectionLike, text: str) -> SectionLike:
    """Return a value of the same shape as ``template`` carrying ``text``."""

    if isinstance(template, Section):
        return replace(template, text=text)
    return text


def _merge_two(left: SectionLike, right: SectionLike) -> SectionLike:
    """Concatenate two section-like values, preserving the left's shape."""

    merged_text = f"{_as_text(left)}\n\n{_as_text(right)}"
    if isinstance(left, Section):
        return replace(left, text=merged_text)
    if isinstance(right, Section):
        return replace(right, text=merged_text)
    return merged_text


# ---------------------------------------------------------------------------
# Oversized-section splitting (Req 1.5)
# ---------------------------------------------------------------------------


def split_oversized(
    section: SectionLike,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[SectionLike]:
    """Split ``section`` so no returned piece exceeds ``max_tokens`` tokens.

    The split cascade favours the most semantically coherent boundary
    available (Req 1.5):

    1. **Paragraphs** — greedily pack paragraphs (blank-line separated)
       into pieces up to ``max_tokens``.
    2. **Sentences** — any single paragraph still over budget is packed
       from its sentences.
    3. **Hard token split** — any single sentence still over budget is
       cut on token boundaries as a last resort.

    A section already within budget is returned unchanged as a
    single-element list. The returned pieces preserve the input's shape:
    ``str`` in → ``list[str]`` out; :class:`Section` in →
    ``list[Section]`` out (each carrying the original's ``source_id`` /
    ``title``).

    Args:
        section: The section (string or :class:`Section`) to split.
        max_tokens: Maximum tokens per returned piece. Must be positive.

    Returns:
        Ordered list of section-like pieces, each within ``max_tokens``
        (except where a single indivisible token run forces otherwise).

    Raises:
        ValueError: If ``max_tokens`` is not positive.
    """

    if max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer")

    text = _as_text(section)
    if count_tokens(text) <= max_tokens:
        return [section]

    pieces = _split_text(text, max_tokens)
    return [_rebuild(section, piece) for piece in pieces]


def _split_text(text: str, max_tokens: int) -> list[str]:
    """Split raw ``text`` into <= ``max_tokens`` pieces, paragraphs first."""

    paragraphs = [p for p in _PARAGRAPH_RE.split(text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    return _pack(paragraphs, max_tokens, "\n\n", _split_paragraph)


def _split_paragraph(paragraph: str, max_tokens: int) -> list[str]:
    """Split an oversized paragraph into <= ``max_tokens`` pieces by sentence."""

    sentences = [s for s in _SENTENCE_RE.split(paragraph) if s.strip()]
    if not sentences:
        sentences = [paragraph]
    return _pack(sentences, max_tokens, " ", _hard_token_split)


def _pack(
    units: list[str],
    max_tokens: int,
    joiner: str,
    fallback_splitter,  # type: ignore[no-untyped-def]
) -> list[str]:
    """Greedily pack ``units`` into pieces of at most ``max_tokens`` tokens.

    A unit that on its own exceeds ``max_tokens`` flushes the current
    buffer and is handed to ``fallback_splitter`` (the next-finer split
    strategy). Adjacent units are joined with ``joiner``.
    """

    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = count_tokens(unit)

        if unit_tokens > max_tokens:
            if current:
                pieces.append(joiner.join(current))
                current, current_tokens = [], 0
            pieces.extend(fallback_splitter(unit, max_tokens))
            continue

        if current and current_tokens + unit_tokens > max_tokens:
            pieces.append(joiner.join(current))
            current, current_tokens = [], 0

        current.append(unit)
        current_tokens += unit_tokens

    if current:
        pieces.append(joiner.join(current))

    return pieces


def _hard_token_split(text: str, max_tokens: int) -> list[str]:
    """Last-resort split on token boundaries when no softer boundary fits."""

    encoding = _get_encoding()
    if encoding is not None:
        try:
            tokens = encoding.encode(text)
            if len(tokens) <= max_tokens:
                return [text]
            return [
                encoding.decode(tokens[i : i + max_tokens])
                for i in range(0, len(tokens), max_tokens)
            ]
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "tiktoken hard-split failed (%s); using char-based split", exc
            )

    return _hard_char_split(text, max_tokens)


def _hard_char_split(text: str, max_tokens: int) -> list[str]:
    """Character-based hard split used when tiktoken is unusable."""

    char_budget = max(1, max_tokens * _CHARS_PER_TOKEN_FALLBACK)
    if len(text) <= char_budget:
        return [text]
    return [text[i : i + char_budget] for i in range(0, len(text), char_budget)]


# ---------------------------------------------------------------------------
# Undersized-section merging (Req 1.6)
# ---------------------------------------------------------------------------


def merge_undersized(
    sections: list[SectionLike],
    min_tokens: int = DEFAULT_MIN_TOKENS,
) -> list[SectionLike]:
    """Merge adjacent same-document sections up to ``min_tokens`` tokens.

    Sections are processed in order. Consecutive sections that share the
    same ``source_id`` are merged (joined with a blank line) until the
    accumulated buffer reaches ``min_tokens``, at which point it is
    emitted and a fresh buffer begins. Sections from a different source
    document are never merged across the boundary.

    The **final** emitted section may fall below ``min_tokens`` when there
    is no further same-document content to merge it with (Req 1.6). Plain
    strings are all treated as belonging to one document (their
    ``source_id`` is ``None``).

    Args:
        sections: Ordered section-like values to normalize.
        min_tokens: Lower token bound each non-terminal chunk should reach.
            Must be positive.

    Returns:
        Ordered list of merged section-like values. Input shape is
        preserved (strings merge into strings, :class:`Section`s into
        :class:`Section`s).

    Raises:
        ValueError: If ``min_tokens`` is not positive.
    """

    if min_tokens <= 0:
        raise ValueError("min_tokens must be a positive integer")
    if not sections:
        return []

    result: list[SectionLike] = []
    buffer: SectionLike = sections[0]
    buffer_tokens = count_tokens(_as_text(buffer))

    for section in sections[1:]:
        section_tokens = count_tokens(_as_text(section))

        # Buffer already satisfies the minimum: emit it and start fresh.
        if buffer_tokens >= min_tokens:
            result.append(buffer)
            buffer, buffer_tokens = section, section_tokens
            continue

        # Buffer is undersized. Merge only if same source document.
        if _source_id(buffer) == _source_id(section):
            buffer = _merge_two(buffer, section)
            buffer_tokens = count_tokens(_as_text(buffer))
        else:
            # Nothing left to merge from this document; emit as-is.
            result.append(buffer)
            buffer, buffer_tokens = section, section_tokens

    result.append(buffer)
    return result


__all__ = [
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MIN_TOKENS",
    "Section",
    "SectionLike",
    "count_tokens",
    "merge_undersized",
    "split_oversized",
]

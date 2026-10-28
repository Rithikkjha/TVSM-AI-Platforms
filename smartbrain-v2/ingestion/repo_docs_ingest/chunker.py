"""RepoDocChunker: front-matter + H2/H3-aware chunking of the repo_docs md files.

* Front matter (``service_id, doc_type, last_reviewed, aliases``) is parsed and dropped.
* Split at ``## ``. A section over ``max_tokens`` is split at ``### `` (one endpoint per
  chunk in API_SPEC); anything still too large goes through ``split_oversized``.
* Small pieces are merged ONLY within the same H2 (never across sections).
* Each chunk's ``display_text`` (embedded + BM25-indexed) is prefixed with
  ``[<service_id> | aka <aliases> | <domain>] <DOC_TYPE> › <H2> › <H3>`` and the summary.
* API_SPEC endpoint chunks (``### `` under ``## Endpoints``) get the request /
  response schema bodies they reference inlined from the doc's ``## Schemas``
  section (when not already tabled), up to ``endpoint_max_tokens``; beyond that
  only top-level fields are kept and a ``Full schema: <Name> (see Schemas)`` line
  is added. The ``## Schemas`` chunks themselves are unchanged.
Headings inside fenced code blocks are ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

from processing.chunking.models import Chunk, ChunkMetadata
from processing.chunking.tokenizer import count_tokens, split_oversized

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
MAX_ALIASES_IN_PREFIX = 5
ENDPOINT_MAX_TOKENS = 800
_REF_LINE_RE = re.compile(r"^(?:Request body|Response `[^`]*`): `([^`]+)`")
_ROW_TYPE_RE = re.compile(r"^\|[^|]*\|([^|]*)\|", re.M)
_TYPE_SPLIT_RE = re.compile(r"[^\w<>.]+")


@dataclass
class _Piece:
    h2: str
    h3: list[str]
    text: str


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            try:
                meta = yaml.safe_load(text[4:end]) or {}
            except yaml.YAMLError:
                meta = {}
            body = text[end + 4 :].lstrip("\n")
            return (meta if isinstance(meta, dict) else {}), body
    return {}, text


def _split_headings(lines: list[str], marker: str) -> list[tuple[str | None, list[str]]]:
    """Split ``lines`` at headings starting with ``marker`` (outside code fences)."""

    blocks: list[tuple[str | None, list[str]]] = [(None, [])]
    in_fence = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        if not in_fence and line.startswith(marker) and not line.startswith(marker + "#"):
            blocks.append((line[len(marker) :].strip(), [line]))
        else:
            blocks[-1][1].append(line)
    return blocks


def _schemas(lines: list[str]) -> dict[str, str]:
    """``name -> body`` (without the ``### `` heading) of the ``## Schemas`` section."""

    for h2, block in _split_headings(lines, "## "):
        if h2 == "Schemas":
            return {
                h3: "\n".join(sub[1:]).strip()
                for h3, sub in _split_headings(block, "### ")
                if h3
            }
    return {}


def _types_in_tables(text: str, names: dict[str, str]) -> list[str]:
    out: list[str] = []
    for m in _ROW_TYPE_RE.finditer(text):
        cell = m.group(1).replace("\\|", " ").strip()
        for tok in [cell, *_TYPE_SPLIT_RE.split(cell)]:
            if tok in names and tok not in out:
                out.append(tok)
    return out


def _truncate_table(body: str, budget: int) -> str:
    """Keep leading lines of ``body`` within ``budget`` tokens."""

    kept: list[str] = []
    for line in body.split("\n"):
        if count_tokens("\n".join([*kept, line])) > budget:
            break
        kept.append(line)
    return "\n".join(kept)


def inline_schemas(block: str, schemas: dict[str, str], max_tokens: int = ENDPOINT_MAX_TOKENS) -> str:
    """Append the schemas ``block`` references but does not already table."""

    lines = block.split("\n")
    direct: list[str] = []
    tabled: set[str] = set()
    for i, line in enumerate(lines):
        m = _REF_LINE_RE.match(line)
        if not m or m.group(1) not in schemas:
            continue
        name = m.group(1)
        if any(ln.startswith("| Field |") for ln in lines[i + 1 : i + 3]):
            tabled.add(name)
        elif name not in direct:
            direct.append(name)
    direct = [n for n in direct if n not in tabled]
    nested = [
        n
        for n in _types_in_tables(block + "\n" + "\n".join(schemas[d] for d in direct), schemas)
        if n not in direct and n not in tabled
    ]
    if not direct and not nested:
        return block

    def section(name: str, body: str) -> str:
        return f"#### Schema {name}\n{body}"

    full = "\n\n".join([block, *(section(n, schemas[n]) for n in direct + nested)])
    if count_tokens(full) <= max_tokens:
        return full
    # Over budget: top-level (direct) schemas only, truncated to fit; pointers for the rest.
    parts = [block]
    pointers: list[str] = []
    for n in direct:
        footer = "\n".join(f"Full schema: {x} (see Schemas)" for x in [*pointers, n, *nested])
        room = max_tokens - count_tokens("\n\n".join([*parts, footer])) - 8
        body = schemas[n] if count_tokens(section(n, schemas[n])) <= room else _truncate_table(schemas[n], room)
        if body.count("\n| ") < 2:  # not even a header + one field row fits
            pointers.append(n)
            continue
        parts.append(section(n, body))
        if body != schemas[n]:
            pointers.append(n)
    pointers += nested
    if pointers:
        parts.append("\n".join(f"Full schema: {x} (see Schemas)" for x in pointers))
    return "\n\n".join(parts)


class RepoDocChunker:
    def __init__(self, min_tokens: int = 200, max_tokens: int = 500) -> None:
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens

    def _pieces(self, body: str, doc_type: str | None = None) -> list[_Piece]:
        lines = body.split("\n")
        pieces: list[_Piece] = []
        schemas = _schemas(lines) if doc_type == "API_SPEC" else {}
        for h2, block in _split_headings(lines, "## "):
            text = "\n".join(block).strip()
            if not text:
                continue
            if h2 is None:
                # Preamble: drop a bare H1 title line.
                rest = [ln for ln in block if not ln.startswith("# ")]
                text = "\n".join(rest).strip()
                if not text:
                    continue
                h2 = "Introduction"
            if h2 == "Endpoints" and schemas:
                section_pieces = self._endpoint_pieces(h2, block, schemas)
                if section_pieces is not None:
                    pieces.extend(self._merge_within(section_pieces))
                    continue
            if count_tokens(text) <= self.max_tokens:
                section_pieces = [_Piece(h2, [], text)]
            else:
                section_pieces = []
                for h3, sub in _split_headings(block, "### "):
                    sub_text = "\n".join(sub).strip()
                    if not sub_text:
                        continue
                    for part in split_oversized(sub_text, self.max_tokens):
                        section_pieces.append(_Piece(h2, [h3] if h3 else [], str(part)))
            pieces.extend(self._merge_within(section_pieces))
        return pieces

    def _endpoint_pieces(self, h2: str, block: list[str], schemas: dict[str, str]) -> list[_Piece] | None:
        """One piece per ``### `` endpoint with schemas inlined; ``None`` if nothing to inline."""

        subs = [(h3, "\n".join(sub).strip()) for h3, sub in _split_headings(block, "### ")]
        enriched = [
            (h3, inline_schemas(t, schemas) if h3 and count_tokens(t) <= ENDPOINT_MAX_TOKENS else t)
            for h3, t in subs
            if t
        ]
        if all(e == t for (_, e), (_, t) in zip(enriched, [s for s in subs if s[1]], strict=True)):
            return None
        out: list[_Piece] = []
        for (h3, text), (_, orig) in zip(enriched, [s for s in subs if s[1]], strict=True):
            limit = ENDPOINT_MAX_TOKENS if text != orig else self.max_tokens
            for part in split_oversized(text, limit):
                out.append(_Piece(h2, [h3] if h3 else [], str(part)))
        return out

    def _merge_within(self, pieces: list[_Piece]) -> list[_Piece]:
        """Merge adjacent undersized pieces of ONE H2 section."""

        out: list[_Piece] = []
        for p in pieces:
            if out:
                last = out[-1]
                lt = count_tokens(last.text)
                if lt < self.min_tokens and lt + count_tokens(p.text) <= self.max_tokens:
                    last.text = f"{last.text}\n\n{p.text}"
                    last.h3 = last.h3 + [h for h in p.h3 if h not in last.h3]
                    continue
            out.append(_Piece(p.h2, list(p.h3), p.text))
        return out

    def chunk(
        self,
        text: str,
        *,
        service_id: str,
        doc_type: str,
        source_ref: str,
        aliases: list[str] | None = None,
        domain: str | None = None,
        summary: str | None = None,
    ) -> list[tuple[Chunk, str]]:
        """Return ``[(Chunk, section)]`` for one md file."""

        _, body = parse_front_matter(text)
        parent = f"repodoc:{service_id}:{doc_type}"
        aka = ", ".join((aliases or [])[:MAX_ALIASES_IN_PREFIX])
        head = f"[{service_id}" + (f" | aka {aka}" if aka else "") + f" | {domain or 'unknown'}]"
        out: list[tuple[Chunk, str]] = []
        for i, piece in enumerate(self._pieces(body, doc_type)):
            h3 = ", ".join(piece.h3[:3]) + (" …" if len(piece.h3) > 3 else "")
            section = piece.h2 + (f" › {h3}" if h3 else "")
            prefix = f"{head} {doc_type} › {section}\n" + (f"{summary}\n" if summary else "") + "\n"
            out.append(
                (
                    Chunk(
                        chunk_id=f"{parent}#chunk:{i}",
                        display_text=prefix + piece.text,
                        original_segment=piece.text,
                        metadata=ChunkMetadata(
                            section_title=section,
                            parent_source_id=parent,
                            repo_name=service_id,
                            chunk_index=i,
                            source_ref=source_ref,
                            doc_type=doc_type,
                        ),
                    ),
                    piece.h2,
                )
            )
        return out

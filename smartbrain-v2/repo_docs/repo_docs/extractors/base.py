"""Phase-2 extractor contract (docs/EXTRACTORS.md#contract-repo_docsextractorsbasepy)."""
from __future__ import annotations

import posixpath
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..classify import classify, status_for
from ..config_classify import redact_line
from .config_index import ConfigIndex

SNIPPET_MAX = 200


@dataclass(frozen=True)
class Evidence:
    file: str      # path relative to repo root (ledgered, non-skipped)
    line: int      # 1-based, <= ledger lines
    snippet: str   # the source line, trimmed, <=200 chars, redacted

    def to_dict(self) -> dict:
        return {"file": self.file, "line": self.line, "snippet": self.snippet}


@dataclass
class InventoryItem:
    id: str
    kind: str
    subproject: str
    attributes: dict
    evidence: list[Evidence]
    source: str = "code"
    extractor_id: str = ""
    extractor_version: str = ""
    confidence: str = "high"
    evidence_count: int | None = None

    def to_dict(self) -> dict:
        ev = sorted(set(self.evidence), key=lambda e: (e.file, e.line, e.snippet))
        total = self.evidence_count if self.evidence_count is not None else len(ev)
        return {
            "id": self.id, "kind": self.kind, "subproject": self.subproject,
            "attributes": self.attributes,
            "evidence": [e.to_dict() for e in ev[:25]], "evidence_count": max(total, len(ev)),
            "source": self.source,
            "extractor": {"id": self.extractor_id, "version": self.extractor_version},
            "confidence": self.confidence,
        }


@dataclass
class FileTouch:
    parse: str                 # "full" | "partial"
    error: str | None = None   # redacted parse error -> file stays pending


@dataclass
class ExtractResult:
    items: list[InventoryItem] = field(default_factory=list)
    touched: dict[str, FileTouch] = field(default_factory=dict)

    def touch(self, path: str, parse: str, error: str | None = None) -> None:
        """Record that ``path`` was opened; a worse result never gets upgraded."""
        prev = self.touched.get(path)
        if prev is not None:
            if prev.parse == "partial":
                parse = "partial"
            error = prev.error or error
        self.touched[path] = FileTouch(parse, error)


class Extractor(ABC):
    """See EXTRACTORS.md. ``stacks == ()`` -> shared extractor (always applies, runs once per repo
    with ``subproject=None`` and attributes items through ``ctx.subproject_of``)."""
    id: str = ""
    stacks: tuple[str, ...] = ()
    extractor_version: str = "0.1.0"
    status: str = "implemented"

    def applies_to(self, meta: dict, subproject: str | None = None) -> bool:
        if not self.stacks:
            return True
        stacks = {s["stack"] for s in meta.get("stacks") or []
                  if subproject is None or s.get("subproject") == subproject}
        return bool(stacks & set(self.stacks))

    @abstractmethod
    def extract(self, ctx: "RepoContext", subproject: str | None) -> ExtractResult: ...


def _count_lines(data: bytes) -> int:
    n = data.count(b"\n")
    if data and not data.endswith(b"\n"):
        n += 1
    return n


class RepoContext:
    """Read-only view of one repo for extractors: clone files, ledger, meta, config index,
    external-systems registry and per-language symbol caches."""

    def __init__(self, org: str, repo: str, clone_dir: Path | None, ledger: dict, meta: dict,
                 registry: list | None = None, internal_patterns: list | tuple = (),
                 reader: Callable[[str], bytes | None] | None = None):
        self.org, self.repo = org, repo
        self.clone_dir = Path(clone_dir) if clone_dir else None
        self.ledger = ledger
        self.meta = meta or {}
        self.registry = list(registry or [])
        self.internal_patterns = list(internal_patterns or [])
        self._reader = reader
        self.ledger_index: dict[str, dict] = {f["path"]: f for f in ledger.get("files") or []}
        self.entries = [f for f in ledger.get("files") or []
                        if f.get("status") in ("pending", "extracted", "scanned")]
        subs = {s.get("subproject") or "." for s in self.meta.get("stacks") or []}
        self.subprojects = sorted(subs)
        self._subs_deep = sorted((s for s in subs if s != "."), key=lambda s: (-s.count("/"), s))
        self._text: dict[str, str | None] = {}
        self._lines: dict[str, list[str]] = {}
        self._syntax: dict[str, object] = {}
        self.config = ConfigIndex()
        self.symbols: dict = {}     # per-language symbol indexes (filled by language modules)
        self.hints: dict = {}       # cross-extractor hints (e.g. generated api specs)

    # ---- layout --------------------------------------------------------------------------
    def subproject_of(self, path: str) -> str:
        """Deepest ``meta.stacks[].subproject`` containing ``path`` (D-P5), else ``.``."""
        for s in self._subs_deep:
            if path.startswith(s + "/"):
                return s
        return "."

    def files(self, subproject: str | None = None,
              predicate: Callable[[dict], bool] | None = None) -> list[dict]:
        """Non-skipped ledger entries (path order), optionally of one subproject."""
        out = []
        for e in self.entries:
            if subproject is not None and self.subproject_of(e["path"]) != subproject:
                continue
            if predicate is None or predicate(e):
                out.append(e)
        return out

    def paths(self, subproject: str | None = None,
              predicate: Callable[[dict], bool] | None = None) -> list[str]:
        return [e["path"] for e in self.files(subproject, predicate)]

    # ---- reading -------------------------------------------------------------------------
    def read_bytes(self, path: str) -> bytes | None:
        if self._reader is not None:
            return self._reader(path)
        if self.clone_dir is None:
            return None
        p = self.clone_dir / path
        try:
            if p.is_symlink() or not p.is_file():
                return None
            return p.read_bytes()
        except OSError:
            return None

    def read_text(self, path: str) -> str | None:
        if path not in self._text:
            data = self.read_bytes(path)
            t = None if data is None else data.decode("utf-8", "replace")
            if t is not None and t.startswith("\ufeff"):
                t = t[1:]
            self._text[path] = t
        return self._text[path]

    def lines(self, path: str) -> list[str]:
        if path not in self._lines:
            t = self.read_text(path)
            self._lines[path] = [] if t is None else [ln.rstrip("\r") for ln in t.split("\n")]
        return self._lines[path]

    def line(self, path: str, n: int) -> str | None:
        ls = self.lines(path)
        return ls[n - 1] if 1 <= n <= len(ls) else None

    def evidence(self, path: str, line: int) -> Evidence:
        raw = self.line(path, line) or ""
        return Evidence(path, line, redact_line(raw).strip()[:SNIPPET_MAX])

    def evidence_masked(self, path: str, line: int, value) -> Evidence:
        """Evidence for a value the classifier marked secret: when the (redacted) line still
        contains the value (its secret-ness came from the full key path, not the line), the
        snippet is cut before the value so it stays a substring of the redacted line."""
        ev = self.evidence(path, line)
        if not isinstance(value, str):
            value = None if value is None else str(value)
        v = (value or "").strip()
        if len(v) < 2 or v not in ev.snippet:
            return ev
        cut = ev.snippet[: ev.snippet.index(v)].rstrip(" \"'=:")
        if not cut:
            cut = ev.snippet[:1] if ev.snippet[:1] in "-\"'[{" else ""
        return Evidence(path, line, cut or "")

    def syntax(self, path: str):
        """tree-sitter parse of a source file (cached), or None for non-source languages."""
        from . import syntax as _syntax
        if path not in self._syntax:
            lang = _syntax.lang_for_path(path)
            txt = self.read_text(path) if lang else None
            self._syntax[path] = _syntax.parse(txt, lang) if txt is not None else None
        return self._syntax[path]

    # ---- external-systems hints ----------------------------------------------------------
    def note_sdk_symbol(self, name: str, path: str, line: int) -> None:
        """Record a declared/imported symbol for the external-systems matcher when it matches a
        registry ``sdk_symbols`` pattern (``hints["sdk_symbols"]``: {symbol: [Evidence]})."""
        import fnmatch
        if not name or not any(fnmatch.fnmatchcase(name, p) for s in self.registry
                               for p in s.get("sdk_symbols") or []):
            return
        evs = self.hints.setdefault("sdk_symbols", {}).setdefault(name, [])
        ev = self.evidence(path, line)
        if ev not in evs:
            evs.append(ev)

    # ---- tests ---------------------------------------------------------------------------
    @classmethod
    def for_test(cls, files: dict[str, str | bytes], stacks: list[tuple[str, str]] = (),
                 repo: str = "fixture", org: str = "TEST-ORG", registry: list | None = None,
                 internal_patterns: list | tuple = (), max_file_bytes: int = 1_000_000
                 ) -> "RepoContext":
        """In-memory context: ledger entries classified with ``classify.classify``."""
        blobs = {p: (c.encode() if isinstance(c, str) else c) for p, c in files.items()}
        entries = []
        for p in sorted(blobs):
            data = blobs[p]
            klass, lang = classify(p, "100644", len(data), data[:8192], max_file_bytes)
            st = status_for(klass)
            entries.append({"path": p, "class": klass, "language": lang, "size": len(data),
                            "lines": _count_lines(data) if st == "pending" else None,
                            "status": st})
        meta = {"repo": repo, "org": org,
                "stacks": [{"stack": s, "subproject": sub, "evidence": []} for s, sub in stacks],
                "stack_ids": sorted({s for s, _ in stacks})}
        ledger = {"files": entries, "generated_at": "2025-01-01T00:00:00Z"}
        return cls(org, repo, None, ledger, meta, registry, internal_patterns,
                   reader=lambda p: blobs.get(p))


def basename(path: str) -> str:
    return posixpath.basename(path)

"""Entity linking over the repo_docs registry: text -> services / topics / endpoints.

Sources (read-only, cached per process):

* ``repo_docs/registry/aliases.yaml`` merged with ``repo_docs/config/aliases.manual.yaml``
  (a manual alias maps ONLY to the listed services) plus the ``ambiguous`` map;
* ``repo_docs/registry/messaging.json`` topic names and raw names;
* endpoint ``METHOD path`` from ``repo_docs/output/<org>/*/service.yaml``.

Matching is case-insensitive, word-boundary, longest-first (one alternation regex),
so "booking service" wins over "booking" at the same position. Ambiguous aliases
return ALL candidate services, flagged ``ambiguous: True``.

Also used by the ingest-side alias linker (``ingestion/repo_docs_ingest/alias_linker.py``).
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

#: smartbrain-v2/repo_docs (retrieval/search/entity_linker.py -> parents[2]).
REPO_DOCS_ROOT = Path(__file__).resolve().parents[2] / "repo_docs"
DEFAULT_ORG = os.environ.get("REPO_DOCS_ORG", "TVS-CS")

CONF_RANK = {"manual": 4, "high": 3, "medium": 2, "low": 1}
_METHOD_PATH_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[^\s`'\"?,)]*)", re.I)
_PATH_RE = re.compile(r"(?<![\w/])(/[A-Za-z0-9_{}:.\-]+(?:/[A-Za-z0-9_{}:.\-]+)*)")
_PARAM_RE = re.compile(r"\{[^}]*\}|(?<=/):[A-Za-z_][A-Za-z0-9_]*")


def normalize_path(path: str | None) -> str:
    if not path:
        return ""
    return _PARAM_RE.sub("{}", path.strip()).rstrip("/") or "/"


def alias_entries(aliases: dict[str, Any], manual: dict[str, Any], known: set[str]) -> dict[str, dict[str, Any]]:
    """``alias_lower -> {"text", "services": {sid: confidence}, "ambiguous": bool}``.

    The canonical service_id / repo name are high-confidence aliases of their own
    service; ``ambiguous`` entries add low-confidence candidates; manual entries
    replace whatever was derived for that alias.
    """

    out: dict[str, dict[str, Any]] = {}

    def add(text: str, sid: str, conf: str) -> None:
        key = text.strip().lower()
        if not key or sid not in known:
            return
        entry = out.setdefault(key, {"text": text.strip(), "services": {}, "ambiguous": False})
        prev = entry["services"].get(sid)
        if prev is None or CONF_RANK.get(conf, 0) > CONF_RANK.get(prev, 0):
            entry["services"][sid] = conf

    for sid, svc in (aliases.get("services") or {}).items():
        add(sid, sid, "high")
        if svc.get("canonical"):
            add(svc["canonical"], sid, "high")
        if svc.get("repo"):
            add(svc["repo"], sid, "high")
        for al in svc.get("aliases") or []:
            add(al.get("alias") or "", sid, al.get("confidence") or "low")
    for sid in known:
        add(sid, sid, "high")
    for text, sids in (aliases.get("ambiguous") or {}).items():
        for sid in sids or []:
            add(text, sid, "low")
    for text, sids in (manual or {}).items():
        if not isinstance(sids, list):
            continue
        valid = [s for s in sids if s in known]
        if valid:
            out[str(text).strip().lower()] = {
                "text": str(text).strip(),
                "services": {s: "manual" for s in valid},
                "ambiguous": len(valid) > 1,
            }
    for entry in out.values():
        entry["ambiguous"] = len(entry["services"]) > 1
    return out


def compile_terms(terms: list[str]) -> re.Pattern[str]:
    ordered = sorted(set(terms), key=lambda t: (-len(t), t))
    return re.compile(r"(?<!\w)(" + "|".join(re.escape(t) for t in ordered) + r")(?!\w)")


@dataclass
class EntityIndex:
    known: set[str]
    aliases: dict[str, dict[str, Any]]
    canonical: dict[str, str]  # lowered service_id / repo -> service_id
    topics: dict[str, dict[str, Any]] = field(default_factory=dict)  # lowered name -> topic info
    endpoints: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)
    paths: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    _alias_re: re.Pattern[str] | None = None
    _topic_re: re.Pattern[str] | None = None

    def __post_init__(self) -> None:
        if self.aliases:
            self._alias_re = compile_terms(list(self.aliases))
        if self.topics:
            self._topic_re = re.compile(
                r"(?<![\w.])("
                + "|".join(re.escape(t) for t in sorted(self.topics, key=lambda t: (-len(t), t)))
                + r")(?![\w])"
            )

    def find_terms(self, text: str) -> Counter[str]:
        """Count alias-term occurrences (longest match wins at each position)."""

        if not text or self._alias_re is None:
            return Counter()
        return Counter(m.group(1) for m in self._alias_re.finditer(text.lower()))


def build_index(root: Path = REPO_DOCS_ROOT, org: str = DEFAULT_ORG) -> EntityIndex:
    out_dir = root / "output" / org
    services: list[dict[str, Any]] = []
    if out_dir.exists():
        for d in sorted(out_dir.iterdir()):
            f = d / "service.yaml"
            if f.is_file():
                services.append(yaml.safe_load(f.read_text(encoding="utf-8")) or {})
    known = {s["service_id"] for s in services if s.get("service_id")}

    def _y(p: Path) -> Any:
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None

    alias_doc = _y(root / "registry" / "aliases.yaml") or {}
    manual = _y(root / "config" / "aliases.manual.yaml") or {}
    entries = alias_entries(alias_doc, manual, known)
    canonical = {sid.lower(): sid for sid in known}
    for sid, svc in (alias_doc.get("services") or {}).items():
        if sid in known and svc.get("repo"):
            canonical[str(svc["repo"]).lower()] = sid

    topics: dict[str, dict[str, Any]] = {}
    mpath = root / "registry" / "messaging.json"
    if mpath.exists():
        for ent in json.loads(mpath.read_text(encoding="utf-8")).get("entities", []):
            name = ent.get("name")
            if not name:
                continue
            info = {
                "name": name,
                "broker": ent.get("broker"),
                "source_id": f"topic:{ent.get('broker')}:{name}",
                "publishers": sorted({p.get("service_id") for p in ent.get("publishers") or [] if p.get("service_id")}),
                "subscribers": sorted({p.get("service_id") for p in ent.get("subscribers") or [] if p.get("service_id")}),
            }
            for n in [name, *(ent.get("raw_names") or [])]:
                topics.setdefault(str(n).lower(), info)

    endpoints: dict[tuple[str, str], list[dict[str, Any]]] = {}
    paths: dict[str, list[dict[str, Any]]] = {}
    for svc in services:
        for item in svc.get("inbound") or []:
            method, path = (item.get("method") or "").upper(), item.get("path")
            if not (method and path):
                continue
            info = {"service": svc["service_id"], "method": method, "path": path}
            endpoints.setdefault((method, normalize_path(path)), []).append(info)
            paths.setdefault(normalize_path(path), []).append(info)
    return EntityIndex(known=known, aliases=entries, canonical=canonical, topics=topics, endpoints=endpoints, paths=paths)


@lru_cache(maxsize=4)
def get_index(root: str | None = None, org: str | None = None) -> EntityIndex:
    return build_index(Path(root) if root else REPO_DOCS_ROOT, org or DEFAULT_ORG)


def resolve(text: str, index: EntityIndex | None = None) -> dict[str, list[dict[str, Any]]]:
    """Resolve every service / topic / endpoint mentioned in ``text``.

    Returns ``{"services": [{id, confidence, term, ambiguous, candidates}],
    "topics": [...], "endpoints": [...]}``. Services are ordered by confidence,
    then by match length. Ambiguous aliases contribute every candidate.
    """

    idx = index or get_index()
    services: dict[str, dict[str, Any]] = {}
    for term, _count in idx.find_terms(text).items():
        entry = idx.aliases[term]
        cands = sorted(entry["services"])
        for sid, conf in entry["services"].items():
            if term in idx.canonical and idx.canonical[term] == sid:
                conf = "high"
            cur = services.get(sid)
            cand = {
                "id": sid,
                "confidence": conf,
                "term": term,
                "ambiguous": entry["ambiguous"],
                "candidates": cands if entry["ambiguous"] else [sid],
            }
            better = cur is None or (
                (not cand["ambiguous"], CONF_RANK.get(conf, 0), len(term))
                > (not cur["ambiguous"], CONF_RANK.get(cur["confidence"], 0), len(cur["term"]))
            )
            if better:
                services[sid] = cand
    ordered = sorted(
        services.values(),
        key=lambda c: (c["ambiguous"], -CONF_RANK.get(c["confidence"], 0), -len(c["term"]), c["id"]),
    )

    topics: list[dict[str, Any]] = []
    if idx._topic_re is not None and text:
        seen: set[str] = set()
        for m in idx._topic_re.finditer(text.lower()):
            info = idx.topics[m.group(1)]
            if info["source_id"] not in seen:
                seen.add(info["source_id"])
                topics.append({**info, "term": m.group(1)})

    endpoints: list[dict[str, Any]] = []
    for m in _METHOD_PATH_RE.finditer(text or ""):
        for info in idx.endpoints.get((m.group(1).upper(), normalize_path(m.group(2))), []):
            if info not in endpoints:
                endpoints.append(info)
    if not endpoints:
        for m in _PATH_RE.finditer(text or ""):
            for info in idx.paths.get(normalize_path(m.group(1)), []):
                if info not in endpoints:
                    endpoints.append(info)
    return {"services": ordered, "topics": topics, "endpoints": endpoints}


def resolve_name(name: str, index: EntityIndex | None = None) -> tuple[str | None, list[str]]:
    """Resolve a tool argument (service id, repo name, alias, or free text).

    Returns ``(service_id or None, candidates)``. ``candidates`` has more than one
    entry when the name is ambiguous; then ``service_id`` is ``None``.
    """

    idx = index or get_index()
    q = (name or "").strip()
    if not q:
        return None, []
    low = q.lower()
    if low in idx.canonical:
        return idx.canonical[low], [idx.canonical[low]]
    if low.startswith("service:") and low[8:] in idx.canonical:
        return idx.canonical[low[8:]], [idx.canonical[low[8:]]]
    entry = idx.aliases.get(low)
    if entry:
        cands = sorted(entry["services"], key=lambda s: (-CONF_RANK.get(entry["services"][s], 0), s))
        return (cands[0], cands) if len(cands) == 1 else (None, cands)
    found = resolve(q, idx)["services"]
    if not found:
        return None, []
    best = found[0]
    if best["ambiguous"]:
        return None, best["candidates"]
    return best["id"], [best["id"]]

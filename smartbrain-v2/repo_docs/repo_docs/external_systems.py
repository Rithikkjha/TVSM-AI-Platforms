"""External-systems registry (registry/external_systems.yaml) + matcher.

Hosts of ``outbound_http`` / ``frontend_api_call`` base URLs and of URL-valued ``config_key`` items,
dependency names and SDK symbols (``ctx.hints["sdk_symbols"]``: {symbol: [Evidence]}) are
fnmatch-ed against the registry. A hit emits one ``external_system`` item per (system,
subproject) and sets ``target_hint: external:<name>`` on matching calls.
"""
from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path

import yaml

from . import paths
from .extractors.base import RepoContext
from .inventory_schema import make_item

MATCHER_ID = ("external_systems", "0.1.0")   # orchestrator step, versioned with PHASE_VERSION
CALL_KINDS = ("outbound_http", "frontend_api_call")


def load_registry(path: Path | None = None) -> tuple[list[dict], str, bytes]:
    """(systems, sha1 hex of the file bytes, bytes). Missing file -> no systems."""
    path = path or paths.external_systems_path()
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        data = b""
    systems = []
    if data:
        doc = yaml.safe_load(data.decode("utf-8")) or {}
        for s in doc.get("systems") or []:
            if isinstance(s, dict) and s.get("name"):
                systems.append({"name": str(s["name"]), "category": s.get("category") or "other",
                                "hosts": [str(h).lower() for h in s.get("hosts") or []],
                                "packages": [str(p).lower() for p in s.get("packages") or []],
                                "sdk_symbols": [str(x) for x in s.get("sdk_symbols") or []]})
    return systems, hashlib.sha1(data).hexdigest(), data


def _host(url: str) -> str | None:
    if not isinstance(url, str) or "://" not in url:
        return None
    h = url.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0]
    return h.rsplit("@", 1)[-1].split(":", 1)[0].lower() or None


def _match_host(host: str, systems: list[dict]):
    for s in systems:
        for pat in s["hosts"]:
            if fnmatch.fnmatchcase(host, pat):
                return s, pat
    return None


def match(ctx: RepoContext, items: list) -> list:
    """Return new external_system items; sets ``target_hint`` on matching call items in place."""
    systems = ctx.registry
    if not systems:
        return []
    found: dict[tuple[str, str], list] = {}   # (system, subproject) -> [(matched_by, match, item)]
    for it in items:
        a = it.attributes
        hosts = []
        if it.kind in CALL_KINDS:
            hosts = [_host(v) for v in sorted((a.get("base_url_values") or {}).values())]
        elif it.kind == "config_key" and a.get("value_kind") == "url":
            hosts = [_host(v) for v in sorted((a.get("values") or {}).values())]
        for h in hosts:
            hit = _match_host(h, systems) if h else None
            if hit:
                s, _pat = hit
                found.setdefault((s["name"], it.subproject), []).append(("host", h, it))
                if it.kind in CALL_KINDS and not a.get("target_hint"):
                    a["target_hint"] = f"external:{s['name']}"
                break
        if it.kind == "dependency":
            name = str(a.get("name") or "").lower()
            for s in systems:
                if any(fnmatch.fnmatchcase(name, p) for p in s["packages"]):
                    found.setdefault((s["name"], it.subproject), []).append(("package", name, it))
                    break
    for sym, evs in sorted((ctx.hints.get("sdk_symbols") or {}).items()):
        for s in systems:
            if any(fnmatch.fnmatchcase(sym, p) for p in s["sdk_symbols"]) and evs:
                sub = ctx.subproject_of(evs[0].file)
                found.setdefault((s["name"], sub), []).append(("sdk-symbol", sym, evs))
                break
    by_name = {s["name"]: s for s in systems}
    out = []
    for (name, sub), hits in sorted(found.items()):
        hits = sorted(hits, key=lambda h: (h[0], h[1], h[2].id if hasattr(h[2], "id") else ""))
        by, what, first = hits[0]
        evidence = []
        for _, _, src in hits:
            evidence += list(src.evidence) if hasattr(src, "evidence") else list(src)
        attrs = {"name": name, "matched_by": by, "match": what,
                 "category": by_name[name]["category"],
                 "from_item": first.id if hasattr(first, "id") else None}
        out.append(make_item("external_system", sub, name, attrs, evidence, MATCHER_ID))
    return out

"""Service alias resolution.

The dependency graph (`kiro_steering/_dependencies/service_dependency_graph.json`)
is the source of truth for how services are named. Each service has a canonical
key (e.g. ``common-backend-booking-service``) and a list of ``aliases`` — the
human names, folder names, and nicknames people actually use ("booking service",
"Booking CRUD Services", "PaymentService", "tvsm-auth", etc.).

Neo4j ``Service`` nodes are MERGE'd by the canonical key (see
``ingestion/load_dependency_graph.py``), so to route a question we must map any
alias the user types back to that canonical key.

Design notes:
- Matching uses word boundaries so short acronyms ("UMS", "MDP", "LS") don't
  fire on substrings of unrelated words.
- When multiple aliases match, the longest wins (so "booking service" beats a
  hypothetical "booking").
- IB vs domestic disambiguation is handled by the alias lists themselves:
  "booking service" is an alias only of the domestic service; the IB variant
  carries "booking-ib" / "Booking CRUD Services IB". No special-casing needed.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Repo root: retrieval/search/service_aliases.py -> parents[2] == smartbrain-v2/
_DEFAULT_GRAPH_PATH = (
    Path(__file__).resolve().parents[2]
    / "kiro_steering"
    / "_dependencies"
    / "service_dependency_graph.json"
)


@lru_cache(maxsize=1)
def _load_alias_map(graph_path: str | None = None) -> dict[str, str]:
    """Build a lowercased ``alias -> canonical service name`` map.

    Includes the canonical key itself as a self-alias. Cached after first load
    (the dependency graph is static for the lifetime of the process).
    """
    path = Path(graph_path) if graph_path else _DEFAULT_GRAPH_PATH
    alias_map: dict[str, str] = {}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load service alias map from %s: %s", path, exc)
        return alias_map

    services = data.get("services", {})
    for canonical, svc_data in services.items():
        # Canonical key maps to itself.
        alias_map[canonical.lower()] = canonical
        for alias in svc_data.get("aliases", []):
            if not alias:
                continue
            key = alias.strip().lower()
            # Don't let a shared/duplicate alias clobber a more specific mapping.
            alias_map.setdefault(key, canonical)

    return alias_map


def _term_present(term: str, text: str) -> bool:
    """True if ``term`` appears in ``text`` with word boundaries on both ends."""
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


def resolve_service(
    text: str,
    known_services: list[str] | None = None,
    graph_path: str | None = None,
) -> str | None:
    """Resolve a service mention in free text to a canonical service name.

    Args:
        text: The (already lowercased or mixed-case) text to search.
        known_services: Canonical service names present in the graph. When a
            resolved canonical name is NOT in this list, we fall back to any
            alias form that *is* known, so routing still hits a real node.
        graph_path: Optional override for the dependency-graph JSON path.

    Returns:
        The canonical service name, or ``None`` if nothing matched.
    """
    q = text.lower().strip()
    if not q:
        return None

    alias_map = _load_alias_map(graph_path)
    known_lower = {s.lower(): s for s in (known_services or [])}

    # Collect every alias/canonical term that appears in the text, longest first.
    matches: list[tuple[int, str, str]] = []  # (length, matched_term, canonical)
    for term, canonical in alias_map.items():
        if _term_present(term, q):
            matches.append((len(term), term, canonical))

    # Also consider raw known_services that may not be in the alias map at all.
    for svc_lower, svc in known_lower.items():
        if svc_lower not in alias_map and _term_present(svc_lower, q):
            matches.append((len(svc_lower), svc_lower, svc))

    if not matches:
        return None

    matches.sort(key=lambda m: m[0], reverse=True)
    _, _, canonical = matches[0]

    if not known_services:
        return canonical

    # Prefer the canonical name if the graph actually has it.
    if canonical.lower() in known_lower:
        return known_lower[canonical.lower()]

    # Otherwise, fall back to an alias form that exists as a known service.
    for _, term, canon in matches:
        if canon == canonical and term in known_lower:
            return known_lower[term]

    # Last resort: return the canonical name even if not in known_services
    # (the downstream query may still match on the node's `aliases` property).
    return canonical

"""Canonical service_id derivation (lowercase kebab) and collision handling.

``repo`` is always the exact GitHub name; ``service_id`` is the canonical id used in docs/graph.
"""

from __future__ import annotations

import hashlib
import re


class NamingError(ValueError):
    pass


_CAMEL_1 = re.compile(r"([a-z0-9])([A-Z])")
_CAMEL_2 = re.compile(r"([A-Z]+)([A-Z][a-z])")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def service_id_for(repo: str) -> str:
    s = _CAMEL_1.sub(r"\1-\2", repo)
    s = _CAMEL_2.sub(r"\1-\2", s)
    s = s.lower()
    s = _NON_ALNUM.sub("-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _hash6(repo: str) -> str:
    return hashlib.sha1(repo.encode("utf-8")).hexdigest()[:6]


def assign_service_ids(
    names: list[str], overrides: dict[str, str] | None = None
) -> tuple[dict[str, str], set[str]]:
    """Return ({repo: service_id}, {repos that collided}).

    Overrides are applied first and must be unique. Among repos sharing a base id, the repo whose
    ``name.lower()`` already equals the base keeps it; all others get ``<base>-<sha1(repo)[:6]>``.
    """
    overrides = dict(overrides or {})
    seen_override: dict[str, str] = {}
    for repo, sid in overrides.items():
        if sid in seen_override:
            raise NamingError(
                f"service_id_overrides: {repo!r} and {seen_override[sid]!r} both map to {sid!r}"
            )
        seen_override[sid] = repo

    base: dict[str, str] = {}
    for n in names:
        base[n] = overrides[n] if n in overrides else service_id_for(n)

    groups: dict[str, list[str]] = {}
    for n, b in base.items():
        groups.setdefault(b, []).append(n)

    result: dict[str, str] = {}
    collided: set[str] = set()
    for b, members in groups.items():
        if len(members) == 1:
            result[members[0]] = b
            continue
        overridden = [m for m in members if m in overrides]
        if len(overridden) > 1:
            raise NamingError(f"service_id_overrides collide on {b!r}: {sorted(overridden)}")
        keeper = overridden[0] if overridden else next(
            (m for m in sorted(members) if m.lower() == b), None
        )
        for m in members:
            collided.add(m)
            result[m] = b if m == keeper else f"{b}-{_hash6(m)}"
    if len(set(result.values())) != len(result):
        raise NamingError("service_id assignment produced duplicates")
    return result, collided

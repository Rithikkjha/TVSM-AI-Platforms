"""Extractor registry (id-keyed, fixed order; docs/EXTRACTORS.md#extractor-ids).

Order: shared.config, shared.manifests, shared.infra, shared.contracts, shared.sql, then stack
extractors alphabetical by id. Planned stubs never run; their stacks (and any detected stack
without an implemented extractor) are reported by ``missing_extractors``.
"""
from __future__ import annotations

from .base import Extractor
from .dotnet_aspnet import DotnetAspnetExtractor
from .java_spring import JavaSpring
from .node_backend import NodeBackendExtractor
from .node_frontend import NodeFrontendExtractor
from .shared_config import SharedConfig
from .shared_contracts import SharedContracts
from .shared_infra import SharedInfra
from .shared_manifests import SharedManifests
from .shared_sql import SharedSql
from .stubs import PLANNED_STACKS, STUBS

SHARED: tuple[type[Extractor], ...] = (SharedConfig, SharedManifests, SharedInfra,
                                       SharedContracts, SharedSql)
STACK_EXTRACTORS: tuple[type[Extractor], ...] = (DotnetAspnetExtractor, JavaSpring,
                                                 NodeBackendExtractor, NodeFrontendExtractor)

REGISTRY: dict[str, type[Extractor]] = {}
for _cls in SHARED:
    REGISTRY[_cls.id] = _cls
for _id in sorted([c.id for c in STACK_EXTRACTORS] + list(STUBS)):
    REGISTRY[_id] = next((c for c in STACK_EXTRACTORS if c.id == _id), None) or STUBS[_id]

_INSTANCES: dict[str, Extractor] = {}


def get_extractor(ext_id: str) -> Extractor:
    if ext_id not in REGISTRY:
        raise KeyError(f"no extractor registered with id {ext_id!r}")
    if ext_id not in _INSTANCES:
        _INSTANCES[ext_id] = REGISTRY[ext_id]()
    return _INSTANCES[ext_id]


def implemented() -> list[Extractor]:
    return [get_extractor(i) for i in REGISTRY if REGISTRY[i].status == "implemented"]


def planned_ids() -> list[str]:
    return [i for i, c in REGISTRY.items() if c.status == "planned"]


def applicable(meta: dict) -> list[tuple[Extractor, str | None]]:
    """[(extractor, subproject)] in registry order. Shared extractors run once (subproject None);
    stack extractors once per subproject they apply to (D-P6)."""
    out: list[tuple[Extractor, str | None]] = []
    subs = sorted({s.get("subproject") or "." for s in meta.get("stacks") or []})
    for ex in implemented():
        if not ex.stacks:
            out.append((ex, None))
            continue
        for sub in subs:
            if ex.applies_to(meta, sub):
                out.append((ex, sub))
    return out


def missing_extractors(meta: dict) -> list[str]:
    """Detected stacks with no implemented extractor."""
    covered = set()
    for ex in implemented():
        covered |= set(ex.stacks)
    return sorted({s["stack"] for s in meta.get("stacks") or []} - covered)


__all__ = ["REGISTRY", "SHARED", "STACK_EXTRACTORS", "PLANNED_STACKS", "get_extractor",
           "implemented", "planned_ids", "applicable", "missing_extractors"]

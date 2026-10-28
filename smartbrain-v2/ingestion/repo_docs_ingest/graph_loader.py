"""Deterministic Neo4j load of the repo_docs registry (Phase 8 step 2).

Inputs (all under ``repo_docs/``):

* ``output/<org>/*/service.yaml`` — services, endpoints, schemas, data stores, config keys;
* ``registry/edges.json`` — http / event / shared_db / owns_schema / library / tests edges;
* ``registry/flows.json`` — end-to-end flows;
* ``registry/messaging.json`` — topics/queues with publishers and subscribers;
* ``registry/aliases.yaml`` (+ ``config/aliases.manual.yaml``) — aliases and the ambiguous map;
* ``registry/external_systems.yaml`` — third-party systems.

:func:`build_graph` is pure (files in, :class:`GraphPlan` out) so it is unit
tested on fixtures. :func:`load_graph` writes the plan with ``UNWIND … MERGE``
through the neo4j async driver (not ``GraphWriter``: that is locked to the
``EntityType`` enum and would embed every endpoint).

Every node carries ``source_id``, ``origin='repo_docs'`` and ``ingest_run``.
Every relationship carries ``source``, ``confidence``, ``evidence`` (JSON
string), ``edge_id``, ``origin='repo_docs'`` and ``ingest_run``. A load is a
full idempotent rebuild of the ``origin='repo_docs'`` graph scope: everything is
MERGEd with the new ``ingest_run``, then graph nodes/relationships of an older
run are deleted. Links written by the alias linker are left alone.

``DEPENDS_ON`` rollup keeps the existing convention "A depends on B = A calls
B": http and shared_db edges keep their direction; for event edges (publisher ->
subscriber) the subscriber depends on the publisher.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import yaml

from retrieval.search.entity_linker import alias_entries
from ingestion.repo_docs_ingest.common import (
    ORIGIN,
    OrgPaths,
    run_cypher,
    stable_id,
    to_json,
    unwind_write,
)

logger = logging.getLogger(__name__)

#: Labels owned by the graph loader (ServiceDoc/Chunk belong to the docs loader).
GRAPH_LABELS: tuple[str, ...] = (
    "Service",
    "Endpoint",
    "Topic",
    "Schema",
    "DataStore",
    "ExternalSystem",
    "ConfigKey",
    "Flow",
    "Alias",
    "Domain",
)

#: Relationship types owned by the graph loader.
GRAPH_REL_TYPES: tuple[str, ...] = (
    "EXPOSES",
    "CALLS",
    "CALLS_ENDPOINT",
    "PUBLISHES",
    "SUBSCRIBES",
    "READS",
    "WRITES",
    "SHARES_DB",
    "DEPENDS_ON_LIBRARY",
    "OWNS_SCHEMA",
    "REQUEST",
    "RESPONDS",
    "USES_CONFIG",
    "PART_OF_FLOW",
    "ALSO_KNOWN_AS",
    "IN_DOMAIN",
    "DEPENDS_ON",
)

_CONF_RANK = {"manual": 4, "high": 3, "medium": 2, "low": 1}
_ROLLUP_KINDS = ("http", "event", "shared_db")
_VIA_ENDPOINT_RE = re.compile(r"^([A-Z]+) (/\S*)$")
_TO_ITEM_RE = re.compile(r"^inbound_http:(.*?):([A-Z]+):(/.*)$")
_PARAM_RE = re.compile(r"\{[^}]*\}|(?<=/):[A-Za-z_][A-Za-z0-9_]*")


def normalize_path(path: str | None) -> str:
    """``/a/{id}/b`` and ``/a/:id/b`` -> ``/a/{}/b``; trailing slash dropped."""

    if not path:
        return ""
    norm = _PARAM_RE.sub("{}", path.strip())
    return norm.rstrip("/") or "/"


def _max_conf(values: list[str | None]) -> str:
    best = max((v for v in values if v), key=lambda v: _CONF_RANK.get(v, 0), default="medium")
    return best


def _service_sid(service_id: str) -> str:
    return f"service:{service_id}"


@dataclass
class GraphPlan:
    """Nodes and relationships to write, keyed for MERGE."""

    nodes: dict[str, dict[str, dict[str, Any]]] = field(default_factory=lambda: defaultdict(dict))
    rels: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def node(self, label: str, source_id: str, **props: Any) -> str:
        existing = self.nodes[label].get(source_id)
        clean = {k: v for k, v in props.items() if v is not None}
        if existing is None:
            self.nodes[label][source_id] = {"source_id": source_id, **clean}
        else:
            for k, v in clean.items():
                existing.setdefault(k, v)
        return source_id

    def rel(
        self,
        rel_type: str,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        *,
        edge_id: str | None = None,
        source: str = "code",
        confidence: str = "high",
        evidence: Any = None,
        **props: Any,
    ) -> None:
        eid = edge_id or stable_id(rel_type, from_id, to_id, *sorted(f"{k}={v}" for k, v in props.items()))
        clean = {k: v for k, v in props.items() if v is not None}
        self.rels.append(
            {
                "type": rel_type,
                "from_label": from_label,
                "from": from_id,
                "to_label": to_label,
                "to": to_id,
                "props": {
                    **clean,
                    "edge_id": eid,
                    "source": source or "code",
                    "confidence": confidence or "medium",
                    "evidence": to_json(evidence if evidence is not None else []),
                },
            }
        )

    def counts(self) -> dict[str, Any]:
        by_rel: dict[str, int] = defaultdict(int)
        for r in self.rels:
            by_rel[r["type"]] += 1
        return {
            "nodes": {label: len(v) for label, v in sorted(self.nodes.items())},
            "relationships": dict(sorted(by_rel.items())),
        }


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------


def load_inputs(paths: OrgPaths) -> dict[str, Any]:
    services = [yaml.safe_load((d / "service.yaml").read_text(encoding="utf-8")) for d in paths.service_dirs()]
    reg = paths.registry_dir

    def _json(name: str) -> dict[str, Any]:
        p = reg / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def _yaml(p: Any) -> Any:
        return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None

    return {
        "services": services,
        "edges": _json("edges.json").get("edges", []),
        "flows": _json("flows.json").get("flows", []),
        "messaging": _json("messaging.json").get("entities", []),
        "aliases": _yaml(reg / "aliases.yaml") or {},
        "manual_aliases": _yaml(paths.manual_aliases) or {},
        "external_systems": (_yaml(reg / "external_systems.yaml") or {}).get("systems", []),
    }


# ---------------------------------------------------------------------------
# Plan building (pure)
# ---------------------------------------------------------------------------


def build_graph(inputs: dict[str, Any]) -> GraphPlan:
    plan = GraphPlan()
    services: list[dict[str, Any]] = inputs["services"]
    known = {s["service_id"] for s in services}
    endpoint_index: dict[str, dict[tuple[str, str], list[str]]] = defaultdict(lambda: defaultdict(list))

    ext_meta = {s["name"]: s for s in inputs.get("external_systems") or []}

    def external(name_ref: str) -> str:
        name = name_ref.split(":", 1)[1] if name_ref.startswith("external:") else name_ref
        meta = ext_meta.get(name, {})
        return plan.node("ExternalSystem", f"external:{name}", name=name, category=meta.get("category"))

    for meta in ext_meta.values():
        external(meta["name"])

    for svc in services:
        _add_service(plan, svc, endpoint_index)

    for edge in inputs.get("edges") or []:
        _add_edge(plan, edge, known, endpoint_index, external)

    _add_rollup(plan, inputs.get("edges") or [], known)
    _add_messaging(plan, inputs.get("messaging") or [], known)
    _add_flows(plan, inputs.get("flows") or [], known)
    _add_aliases(plan, inputs.get("aliases") or {}, inputs.get("manual_aliases") or {}, known)
    return plan


def _add_service(plan: GraphPlan, svc: dict[str, Any], endpoint_index: dict) -> None:
    sid = svc["service_id"]
    s_node = _service_sid(sid)
    repo = svc.get("repo") or {}
    plan.node(
        "Service",
        s_node,
        name=sid,
        service_id=sid,
        display_name=svc.get("name") or sid,
        type=svc.get("type"),
        summary=svc.get("summary"),
        # ``description`` is what the existing graph-expansion code prints.
        description=svc.get("summary"),
        aliases=list(svc.get("aliases") or []),
        domain=svc.get("domain"),
        repo_url=repo.get("url"),
        default_branch=repo.get("default_branch"),
        languages=list((svc.get("tech_stack") or {}).get("languages") or []),
        frameworks=list((svc.get("tech_stack") or {}).get("frameworks") or []),
    )

    if svc.get("domain"):
        d = plan.node("Domain", f"domain:{svc['domain']}", name=svc["domain"])
        plan.rel("IN_DOMAIN", "Service", s_node, "Domain", d, source="inferred", confidence="medium")

    schemas: dict[str, Any] = svc.get("schemas") or {}
    for name, schema in sorted(schemas.items()):
        schema = schema or {}
        plan.node(
            "Schema",
            f"schema:{sid}:{name}",
            name=name,
            service_id=sid,
            defined_in=schema.get("defined_in"),
            fields=to_json(schema.get("fields") or []),
            enum=to_json(schema["enum"]) if schema.get("enum") else None,
            schema_source=schema.get("source"),
        )

    used: set[str] = set()
    for item in svc.get("inbound") or []:
        kind = item.get("kind") or "http"
        method = (item.get("method") or "").upper() or None
        path = item.get("path")
        if kind == "http" and method and path:
            key = f"endpoint:{sid}:{method} {path}"
        else:
            key = f"endpoint:{sid}:{kind.upper()} {item.get('id') or item.get('handler')}"
        if key in used:
            key = f"{key}#{item.get('id')}"
        used.add(key)
        plan.node(
            "Endpoint",
            key,
            service_id=sid,
            inbound_id=item.get("id"),
            kind=kind,
            method=method,
            path=path,
            path_normalized=normalize_path(path) if path else None,
            auth=item.get("auth"),
            handler=item.get("handler"),
            trigger=item.get("trigger"),
            schedule=item.get("schedule"),
            callers=list(item.get("callers") or []),
            params=to_json(item.get("params") or []),
            request=item.get("request"),
            responses=to_json(item.get("responses") or []),
        )
        evidence = [{"handler": item.get("handler")}] if item.get("handler") else []
        plan.rel("EXPOSES", "Service", s_node, "Endpoint", key, source=item.get("source") or "code", evidence=evidence)
        if method and path:
            endpoint_index[sid][(method, normalize_path(path))].append(key)
        req = item.get("request")
        if req and req in schemas:
            plan.rel("REQUEST", "Endpoint", key, "Schema", f"schema:{sid}:{req}", source=item.get("source") or "code")
        for resp in item.get("responses") or []:
            sch = (resp or {}).get("schema")
            if sch and sch in schemas:
                plan.rel(
                    "RESPONDS",
                    "Endpoint",
                    key,
                    "Schema",
                    f"schema:{sid}:{sch}",
                    source=item.get("source") or "code",
                    status=resp.get("status"),
                    when=resp.get("when"),
                )

    for store in svc.get("data_stores") or []:
        stype = store.get("type") or "other"
        sname = store.get("name") or "_"
        ds = plan.node(
            "DataStore",
            f"datastore:{sid}:{stype}:{sname}",
            name=sname,
            type=stype,
            service_id=sid,
            owned=store.get("owned"),
            owner_service=store.get("owner_service"),
            key_entities=[str(e) for e in store.get("key_entities") or []],
        )
        access = (store.get("access") or "").lower()
        reads = access in ("read", "read-write", "both")
        writes = access in ("write", "read-write", "both")
        src = store.get("source") or "code"
        if writes:
            plan.rel("WRITES", "Service", s_node, "DataStore", ds, source=src, access=access)
        if reads:
            plan.rel("READS", "Service", s_node, "DataStore", ds, source=src, access=access)
        if not (reads or writes):
            # Access not determinable from code: keep the store attached, flagged.
            plan.rel("READS", "Service", s_node, "DataStore", ds, source=src, confidence="low", access="unknown")

    for cfg in svc.get("config") or []:
        name = cfg.get("name")
        if not name:
            continue
        # Names only — service.yaml never carries values, and none are copied here.
        ck = plan.node(
            "ConfigKey",
            f"config:{sid}:{name}",
            name=name,
            service_id=sid,
            secret=bool(cfg.get("secret")),
            required=cfg.get("required"),
            provided_by=cfg.get("provided_by"),
            purpose=cfg.get("purpose"),
        )
        plan.rel("USES_CONFIG", "Service", s_node, "ConfigKey", ck)


def _resolve_endpoints(edge: dict[str, Any], endpoint_index: dict) -> list[str]:
    target = edge.get("to")
    items = [edge.get("to_item")] + list(edge.get("to_items_alt") or [])
    found: list[str] = []
    for item in items:
        m = _TO_ITEM_RE.match(item or "")
        if not m:
            continue
        for key in endpoint_index.get(target, {}).get((m.group(2), normalize_path(m.group(3))), []):
            if key not in found:
                found.append(key)
        if found:
            break
    return found


def _add_edge(plan: GraphPlan, edge: dict[str, Any], known: set[str], endpoint_index: dict, external) -> None:  # type: ignore[no-untyped-def]
    kind = edge.get("kind")
    src, dst = edge.get("from"), edge.get("to") or ""
    if src not in known:
        plan.warnings.append(f"edge {edge.get('id')}: unknown from {src}")
        return
    common = {
        "edge_id": edge.get("id"),
        "source": edge.get("source") or "code",
        "confidence": edge.get("confidence") or "medium",
        "evidence": edge.get("evidence") or [],
    }
    a = _service_sid(src)

    def target() -> tuple[str, str] | None:
        if dst.startswith("external:"):
            return "ExternalSystem", external(dst)
        if dst in known:
            return "Service", _service_sid(dst)
        plan.warnings.append(f"edge {edge.get('id')}: unknown to {dst}")
        return None

    via = edge.get("via")
    if kind in ("http", "grpc", "soap", "tests"):
        t = target()
        if t is None:
            return
        m = _VIA_ENDPOINT_RE.match(via or "")
        plan.rel(
            "CALLS",
            "Service",
            a,
            t[0],
            t[1],
            **common,
            kind=kind,
            via=via,
            endpoint=via if m else None,
            caller_type=edge.get("caller_type"),
            criticality=edge.get("criticality"),
            match=edge.get("match"),
            from_item=edge.get("from_item"),
            to_item=edge.get("to_item"),
        )
        if t[0] == "Service":
            for ep in _resolve_endpoints(edge, endpoint_index):
                plan.rel(
                    "CALLS_ENDPOINT",
                    "Service",
                    a,
                    "Endpoint",
                    ep,
                    **{**common, "edge_id": stable_id(edge.get("id"), ep)},
                    kind=kind,
                    via=via,
                    registry_edge_id=edge.get("id"),
                )
    elif kind == "shared_db":
        t = target()
        if t is not None:
            plan.rel("SHARES_DB", "Service", a, t[0], t[1], **common, via=via, match=edge.get("match"))
    elif kind == "owns_schema":
        table = dst.split(":", 1)[1] if dst.startswith("table:") else dst
        tnode = plan.node("Schema", f"table:{table}", name=table, schema_kind="table")
        plan.rel("OWNS_SCHEMA", "Service", a, "Schema", tnode, **common, via=via)
    elif kind == "library_dependency":
        t = target()
        if t is not None:
            package = via.split(":", 1)[1] if via and via.startswith("package:") else via
            plan.rel("DEPENDS_ON_LIBRARY", "Service", a, t[0], t[1], **common, package=package, via=via)
    elif kind == "event":
        # Represented by PUBLISHES/SUBSCRIBES (messaging.json) and the DEPENDS_ON rollup.
        return
    else:
        plan.warnings.append(f"edge {edge.get('id')}: unhandled kind {kind}")


def _add_rollup(plan: GraphPlan, edges: list[dict[str, Any]], known: set[str]) -> None:
    pairs: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        kind = edge.get("kind")
        if kind not in _ROLLUP_KINDS:
            continue
        src, dst = edge.get("from"), edge.get("to")
        if src not in known or dst not in known:
            continue
        # A depends on B = A calls B. Events: subscriber (to) depends on publisher (from).
        dependent, dependency = (dst, src) if kind == "event" else (src, dst)
        if dependent == dependency:
            continue
        pairs[(dependent, dependency)].append(edge)
    for (dependent, dependency), group in sorted(pairs.items()):
        kinds = sorted({e["kind"] for e in group})
        evidence = [ev for e in group for ev in (e.get("evidence") or [])][:5]
        plan.rel(
            "DEPENDS_ON",
            "Service",
            _service_sid(dependent),
            "Service",
            _service_sid(dependency),
            edge_id=stable_id("DEPENDS_ON", dependent, dependency),
            source="registry",
            confidence=_max_conf([e.get("confidence") for e in group]),
            evidence=evidence,
            kinds=kinds,
            dependency_type=",".join(kinds),
            edge_ids=sorted(e["id"] for e in group if e.get("id")),
            vias=sorted({e.get("via") for e in group if e.get("via")})[:20],
        )


def _add_messaging(plan: GraphPlan, entities: list[dict[str, Any]], known: set[str]) -> None:
    for ent in entities:
        broker = ent.get("broker") or "unknown"
        name = ent.get("name")
        if not name:
            continue
        sid = f"topic:{broker}:{name}"
        if sid in plan.nodes["Topic"] and plan.nodes["Topic"][sid].get("key") != ent.get("key"):
            sid = f"topic:{broker}:{ent.get('entity_type')}:{name}"
        plan.node(
            "Topic",
            sid,
            name=name,
            key=ent.get("key"),
            broker=broker,
            entity_type=ent.get("entity_type"),
            raw_names=list(ent.get("raw_names") or []),
            flags=list(ent.get("flags") or []),
        )
        for direction, rel_type in (("publishers", "PUBLISHES"), ("subscribers", "SUBSCRIBES")):
            for member in ent.get(direction) or []:
                svc = member.get("service_id")
                if svc not in known:
                    plan.warnings.append(f"topic {name}: unknown {direction[:-1]} {svc}")
                    continue
                plan.rel(
                    rel_type,
                    "Service",
                    _service_sid(svc),
                    "Topic",
                    sid,
                    edge_id=stable_id(rel_type, svc, ent.get("key"), member.get("item_id")),
                    evidence=[{"item_id": member.get("item_id"), "repo": member.get("repo")}],
                    item_id=member.get("item_id"),
                    namespace=member.get("namespace"),
                    subscription=member.get("subscription") if rel_type == "SUBSCRIBES" else None,
                    filter=member.get("filter") if rel_type == "SUBSCRIBES" else None,
                    message_types=list(member.get("message_types") or []),
                    raw_names=list(member.get("raw_names") or []),
                )


def _add_flows(plan: GraphPlan, flows: list[dict[str, Any]], known: set[str]) -> None:
    for flow in flows:
        fid = flow.get("flow_id")
        if not fid:
            continue
        fnode = plan.node(
            "Flow",
            f"flow:{fid}",
            flow_id=fid,
            name=flow.get("name"),
            entry=flow.get("entry"),
            terminal=flow.get("terminal"),
            length=flow.get("length"),
            confidence=flow.get("confidence"),
            truncated=flow.get("truncated"),
            entry_types=list(flow.get("entry_types") or []),
            triggers=list(flow.get("triggers") or []),
            services=list(flow.get("services") or []),
            steps=to_json(flow.get("steps") or []),
        )
        first_step: dict[str, int] = {}
        for step in flow.get("steps") or []:
            for member in (step.get("from"), step.get("to")):
                if member and member not in first_step:
                    first_step[member] = step.get("n") or 0
        for member in flow.get("services") or []:
            if member not in known:
                continue
            role = "entry" if member == flow.get("entry") else (
                "terminal" if member == flow.get("terminal") else "participant"
            )
            plan.rel(
                "PART_OF_FLOW",
                "Service",
                _service_sid(member),
                "Flow",
                fnode,
                source="code",
                confidence=flow.get("confidence") or "medium",
                role=role,
                step_n=first_step.get(member),
            )


def _add_aliases(plan: GraphPlan, aliases: dict[str, Any], manual: dict[str, Any], known: set[str]) -> None:
    for key, entry in sorted(alias_entries(aliases, manual, known).items()):
        anode = plan.node("Alias", f"alias:{key}", text=entry["text"], name=key, ambiguous=entry["ambiguous"])
        for sid, conf in sorted(entry["services"].items()):
            plan.rel(
                "ALSO_KNOWN_AS",
                "Alias",
                anode,
                "Service",
                _service_sid(sid),
                source="manual" if conf == "manual" else "code",
                confidence=conf,
                ambiguous=entry["ambiguous"],
            )


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


async def load_graph(driver: Any, plan: GraphPlan, run_id: str) -> dict[str, Any]:
    """MERGE the plan, then delete graph-scope leftovers of older runs."""

    async with driver.session() as session:
        for label, nodes in sorted(plan.nodes.items()):
            rows = [
                {"source_id": sid, "props": {**props, "origin": ORIGIN, "ingest_run": run_id}}
                for sid, props in sorted(nodes.items())
            ]
            await unwind_write(
                session,
                f"MERGE (n:{label} {{source_id: row.source_id}}) SET n = row.props, n.updated_at = datetime()",
                rows,
            )

        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for r in plan.rels:
            groups[(r["type"], r["from_label"], r["to_label"])].append(
                {"from": r["from"], "to": r["to"], "props": {**r["props"], "origin": ORIGIN, "ingest_run": run_id}}
            )
        written = 0
        for (rel_type, fl, tl), rows in sorted(groups.items()):
            for i in range(0, len(rows), 500):
                result = await session.run(
                    f"UNWIND $rows AS row "
                    f"MATCH (a:{fl} {{source_id: row.from}}) MATCH (b:{tl} {{source_id: row.to}}) "
                    f"MERGE (a)-[r:{rel_type} {{edge_id: row.props.edge_id}}]->(b) SET r = row.props "
                    f"RETURN count(r) AS n",
                    rows=rows[i : i + 500],
                )
                written += (await result.single())["n"]

        stale_rels = (
            await run_cypher(
                session,
                "MATCH ()-[r]->() WHERE r.origin = $origin AND r.ingest_run <> $run AND type(r) IN $types "
                "DELETE r RETURN count(r) AS n",
                origin=ORIGIN,
                run=run_id,
                types=list(GRAPH_REL_TYPES),
            )
        )[0]["n"]
        stale_nodes = (
            await run_cypher(
                session,
                "MATCH (n) WHERE n.origin = $origin AND n.ingest_run <> $run "
                "AND any(l IN labels(n) WHERE l IN $labels) DETACH DELETE n RETURN count(n) AS n",
                origin=ORIGIN,
                run=run_id,
                labels=list(GRAPH_LABELS),
            )
        )[0]["n"]
    return {
        "relationships_planned": len(plan.rels),
        "relationships_written": written,
        "stale_relationships_deleted": stale_rels,
        "stale_nodes_deleted": stale_nodes,
    }


async def graph_counts(driver: Any) -> dict[str, Any]:
    async with driver.session() as session:
        nodes = await run_cypher(
            session,
            "MATCH (n) WHERE n.origin = $origin UNWIND labels(n) AS l RETURN l, count(*) AS n ORDER BY l",
            origin=ORIGIN,
        )
        rels = await run_cypher(
            session,
            "MATCH ()-[r]->() WHERE r.origin = $origin RETURN type(r) AS t, count(*) AS n ORDER BY t",
            origin=ORIGIN,
        )
    return {"nodes": {r["l"]: r["n"] for r in nodes}, "relationships": {r["t"]: r["n"] for r in rels}}

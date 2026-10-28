"""End-to-end flow building (repo_docs/flows.py): paths, cycles, depth cap, exclusions, determinism."""
from __future__ import annotations

import json
from types import SimpleNamespace

from repo_docs import flows as fl
from repo_docs import paths
from repo_docs.phase6_verify import headings, split_front_matter

TYPES = {"ui": "frontend", "a": "service", "b": "service", "c": "service", "d": "service",
         "e": "service", "f": "service", "g": "service", "lib": "library", "t": "test-suite"}


def E(frm, to, kind="http", via=None, conf="high", **kw):
    via = via or (f"GET /{to}" if kind == "http" else f"azure-service-bus:topic:{to}-events")
    return {"id": f"{frm}>{to}:{kind}:{via}", "from": frm, "to": to, "kind": kind, "via": via,
            "confidence": conf, "criticality": "hard" if kind == "http" else "async",
            "caller_type": "frontend" if frm == "ui" else "service",
            "from_item": kw.get("from_item"), "to_item": kw.get("to_item"),
            "evidence": [{"repo": frm, "file": "src/x.ts", "line": 1, "snippet": "s"}]}


def seqs(flows):
    return sorted(tuple(f["services"]) for f in flows)


def test_simple_paths_and_maximal_only():
    edges = [E("ui", "a"), E("a", "b"), E("a", "c"), E("b", "external:pay")]
    out = fl.build_flows(edges, {}, TYPES)
    assert seqs(out) == [("ui", "a", "b", "external:pay"), ("ui", "a", "c")]
    f = next(f for f in out if f["terminal"] == "c")
    assert f["flow_id"] == "ui--c" and f["entry_types"] == ["frontend"]
    assert [s["mode"] for s in f["steps"]] == ["sync", "sync"]
    ext = next(f for f in out if f["terminal"] == "external:pay")
    assert ext["flow_id"] == "ui--external-pay"


def test_cycle_avoidance():
    edges = [E("ui", "a"), E("a", "b"), E("b", "a"), E("b", "c")]
    out = fl.build_flows(edges, {}, TYPES)
    assert seqs(out) == [("ui", "a", "b", "c")]
    for f in out:
        assert len(set(f["services"])) == len(f["services"])


def test_cycle_only_component_is_covered():
    out = fl.build_flows([E("a", "b"), E("b", "a")], {}, TYPES)
    assert {s for f in out for s in f["services"]} == {"a", "b"}
    assert all(f["entry_types"] == ["uncovered"] for f in out)


def test_depth_cap():
    chain = ["ui", "a", "b", "c", "d", "e", "f", "g"]
    edges = [E(x, y) for x, y in zip(chain, chain[1:])]
    out = [f for f in fl.build_flows(edges, {}, TYPES) if f["entry"] == "ui"]
    assert len(out) == 1 and out[0]["length"] == fl.MAX_DEPTH and out[0]["truncated"] is True
    assert out[0]["services"] == chain[:fl.MAX_DEPTH + 1]
    assert fl.build_flows(edges, {}, TYPES, max_depth=2)[0]["length"] == 2


def test_exclusion_rules():
    items = {"a": {"outbound_http:script": {"kind": "outbound_http", "attributes": {"role": "script"}}}}
    edges = [E("ui", "a"),
             E("a", "a"),                                       # self-loop
             E("a", "b", kind="owns_schema", via="table:x"),
             E("a", "lib", kind="library_dependency", via="artifact:lib"),
             E("a", "c", kind="shared_db", via="db"),
             E("a", "d", kind="tests", via="t"),
             {**E("t", "a"), "caller_type": "test-suite"},
             E("a", "e", from_item="outbound_http:script"),     # role=script caller
             E("a", "lib")]                                     # library service
    out = fl.build_flows(edges, items, TYPES)
    assert seqs(out) == [("ui", "a")]


def test_event_publisher_entry_and_payload_schema():
    items = {"b": {"messaging:pub": {"kind": "messaging", "attributes": {"payload": "OrderEvent"}}},
             "e": {"inbound_http:x": {"kind": "inbound_http",
                                      "attributes": {"request": "CReq", "responses": [{"schema": "CRes"},
                                                                                       {"schema": "string"}]}}}}
    edges = [E("ui", "a"), E("a", "b"),
             E("b", "c", kind="event", via="azure-service-bus:topic:orders", from_item="messaging:pub"),
             E("b", "d", to_item=None), E("c", "e", to_item="inbound_http:x")]
    out = fl.build_flows(edges, items, TYPES)
    pub = [f for f in out if "event_publisher" in f["entry_types"]]
    assert [f["services"] for f in pub] == [["b", "c", "e"]]
    step = pub[0]["steps"][0]
    assert step["mode"] == "async" and step["via"] == "topic:orders" and step["topics"] == ["orders"]
    assert step["data"] == ["OrderEvent"]
    assert pub[0]["steps"][1]["data"] == ["CReq", "CRes"]  # generic names dropped


def test_collision_suffix_and_min_confidence():
    edges = [E("ui", "a"), E("ui", "b", conf="medium"), E("a", "c"), E("b", "c")]
    out = fl.build_flows(edges, {}, TYPES)
    ids = sorted(f["flow_id"] for f in out)
    assert len(ids) == 2 and all(i.startswith("ui--c-") and len(i) == len("ui--c-") + 6 for i in ids)
    assert {f["confidence"] for f in out} == {"high", "medium"}


def test_aggregated_hop_and_dedup():
    edges = [E("ui", "a", via="GET /x"), E("ui", "a", via="POST /y", conf="medium")]
    out = fl.build_flows(edges, {}, TYPES, scheduled={"ui": ["job"]})
    assert len(out) == 1
    s = out[0]["steps"][0]
    assert s["vias"] == ["GET /x", "POST /y"] and s["confidence"] == "high" and len(s["edges"]) == 2
    assert out[0]["entry_types"] == ["frontend", "scheduled"]


def _setup(tmp_path):
    paths.set_root(tmp_path)
    reg = paths.registry_dir()
    edges = [E("ui", "a"), E("a", "b"), E("b", "external:pay"), E("a", "c"),
             E("c", "d", kind="event", via="kafka:kafka-topic:cp.order")]
    paths.atomic_write_json(reg / "edges.json", {"schema_version": 1, "edges": edges})
    svcs = {s: {"repo_type": TYPES.get(s, "service"), "data_stores": ["mongo:_:x"] if s == "a" else []}
            for s in ("ui", "a", "b", "c", "d", "lonely")}
    paths.atomic_write_json(reg / "O" / "services.json", {"services": svcs})
    for s in svcs:
        paths.atomic_write_json(paths.runs_dir("O", s) / "inventory.json",
                                {"service_id": s, "items": []})
        paths.output_dir("O", s).mkdir(parents=True)
    (paths.output_dir("O", "a") / "DATA_FLOWS.md").write_text(
        "---\nservice_id: a\ndoc_type: data_flows\nlast_reviewed: 2024-01-02\nflows: []\n---\n"
        "# a\n## Flow Index\nold\n## Flow: old\nx\n## Notes\nkeep me\n", encoding="utf-8")


def _org(name="O"):
    return SimpleNamespace(name=name)


def test_run_determinism_and_render(tmp_path):
    _setup(tmp_path)
    org = _org()
    res = fl.run(org)
    first = (paths.registry_dir() / "flows.json").read_bytes()
    md1 = {s: (paths.output_dir("O", s) / "DATA_FLOWS.md").read_bytes() for s in ("a", "lonely")}
    fl.run(org)
    assert (paths.registry_dir() / "flows.json").read_bytes() == first
    assert {s: (paths.output_dir("O", s) / "DATA_FLOWS.md").read_bytes() for s in md1} == md1
    assert res["flows"] == 3 and "lonely" in res["services_without_flow"]
    doc = json.loads(first)
    assert [f["flow_id"] for f in doc["flows"]] == sorted(f["flow_id"] for f in doc["flows"])

    fm, body = split_front_matter(md1["a"].decode())
    assert str(fm["last_reviewed"]) == "2024-01-02" and fm["flows"]
    hs = headings(body)
    assert hs[0] == "Flow Index" and hs[-1] == "Notes" and "Flow: old" not in hs
    assert [h for h in hs if h.startswith("Flow: ")] == [f"Flow: {i}" for i in fm["flows"]]
    text = md1["a"].decode()
    assert "a->>b: GET /b" in text and "c--)d: kafka-topic:cp.order" in text
    assert "| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |" in text
    assert "`ui/src/x.ts:1`" in text and "keep me" in text and "a: mongo:x" in text

    fm2, body2 = split_front_matter(md1["lonely"].decode())
    assert fm2["flows"] == [] and "N/A" in body2 and "Direct neighbours in registry/edges.json: none." in body2

    sy = fl.service_yaml_flows(doc["flows"], "a")
    assert [f["flow_id"] for f in sy] == fm["flows"]
    assert {f["role"] for f in sy} == {"participant"}


def test_service_cap():
    edges = [E("ui", f"s{i}") for i in range(30)]
    types = {**TYPES, **{f"s{i}": "service" for i in range(30)}}
    out = fl.build_flows(edges, {}, types)
    sel, total = fl.select_for_service(out, "ui")
    assert total == 30 and len(sel) == fl.SERVICE_CAP

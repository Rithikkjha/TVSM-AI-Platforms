"""Phase 5 generate mapping + phase 6 verify gate (deterministic, synthetic data)."""
import yaml

from repo_docs import paths
from repo_docs import phase5_generate as g
from repo_docs import phase6_verify as v


def _it(kind, iid, source="code", **attrs):
    return {"kind": kind, "id": iid, "source": source, "attributes": attrs}


INV = {"service_id": "svc-a", "repo": "svc-a", "head_sha": "x", "items": [
    _it("inbound_http", "inbound_http:.:POST:/api/x", source="contract", method="POST",
        path="/api/x/{id}", auth="bearer-jwt", params=[{"name": "id", "in": "path",
                                                        "type": "string", "required": True}],
        request="XReq", responses=[{"status": 200, "schema": "XRes", "when": None}],
        handler="XController.Post"),
    _it("outbound_http", "outbound_http:.:GET:config:b.url:/api/b", method="GET",
        path_template="/api/b", base_url_source="config:b.url", role="runtime"),
    _it("outbound_http", "outbound_http:.:GET:unknown:/api/z", method="GET",
        path_template="/api/z", base_url_source="unknown", role="runtime"),
    _it("messaging", "messaging:.:publish:sb:x-events", direction="publish", entity="x-events",
        entity_type="topic", broker="azure-service-bus", name_from="literal",
        published_by="src/Pub.cs:10"),
    _it("config_key", "config_key:.:b.url", name="b.url", canonical="b.url", secret=False,
        provided_by="app-settings", required=None, values={"default": "https://b.example"}),
    _it("config_key", "config_key:.:db.password", name="Db:Password", canonical="db.password",
        secret=True, provided_by="unknown"),
    _it("data_access", "data_access:.:mssql:env:DB", store_type="mssql", database="_",
        name_from="env:DB", operation="both", entities=[{"name": "Order"}]),
    _it("schema", "schema:.:Color", name="Color", defined_in="src/Color.cs:1",
        enum_values=["RED", "BLUE"], fields=[]),
]}
EDGES = [
    {"from": "svc-c", "to": "svc-a", "kind": "http", "via": "POST /api/x", "source": "code",
     "from_item": "o", "to_item": "inbound_http:.:POST:/api/x", "criticality": "hard"},
    {"from": "svc-a", "to": "svc-b", "kind": "http", "via": "GET /api/b", "source": "inferred",
     "from_item": "outbound_http:.:GET:config:b.url:/api/b", "criticality": "soft"},
    {"from": "svc-a", "to": "svc-d", "kind": "event", "via": "azure-service-bus:topic:x-events",
     "source": "code", "from_item": "messaging:.:publish:sb:x-events", "to_item": "m",
     "criticality": "async"},
]


def _doc():
    return g.build_service_yaml(INV, {"repo_type": {"template_type": "backend-api"},
                                      "html_url": "https://github.com/o/svc-a",
                                      "default_branch": "main", "language": "C#"},
                                g.Registry(EDGES, {}))


def test_generate_mapping():
    d = _doc()
    assert d["type"] == "backend-api" and d["summary"] is None and d["ownership"]["team"] is None
    ib = d["inbound"][0]
    assert ib["id"] == "post-api-x" and ib["callers"] == ["svc-c"] and ib["source"] == "code"
    tgt = {o["path"]: o for o in d["outbound"]}
    assert tgt["/api/b"]["target"] == "svc-b" and tgt["/api/b"]["criticality"] == "soft"
    assert tgt["/api/b"]["source"] == "inferred"
    assert tgt["/api/z"]["target"] is None and tgt["/api/z"]["criticality"] is None
    assert d["events"]["publishes"][0]["consumers"] == ["svc-d"]
    assert d["flows"][0]["flow_id"] == "event-x-events"
    assert d["flows"][0]["steps"][0] == {"from": "svc-a", "to": "svc-d", "via": "topic:x-events",
                                         "data": None, "source": "code"}
    cfg = {c["name"]: c for c in d["config"]}
    assert cfg["b.url"]["points_to"] == "svc-b" and cfg["Db:Password"]["secret"] is True
    assert cfg["Db:Password"]["provided_by"] is None
    assert d["data_stores"][0]["name"] == "env:DB" and d["data_stores"][0]["access"] == "read-write"
    assert d["schemas"]["Color"]["type"] == "enum[RED,BLUE]"
    text = g.dump_yaml(d)
    assert "https://b.example" not in text  # config values never written
    assert g.dump_yaml(_doc()) == text      # deterministic


def test_flow_id_shared_across_participants():
    reg = g.Registry(EDGES, {})
    inv_d = {"service_id": "svc-d", "repo": "svc-d", "items": [
        _it("messaging", "m", direction="subscribe", entity="x-events", entity_type="topic")]}
    d = g.build_service_yaml(inv_d, {}, reg)
    assert d["events"]["subscribes"][0]["producers"] == ["svc-a"]
    assert d["flows"][0]["flow_id"] == _doc()["flows"][0]["flow_id"]
    assert d["flows"][0]["role"] == "consumer"


def test_write_output_keeps_md(tmp_path):
    paths.set_root(tmp_path)
    out = g.write_output("O", "svc-a", "a: 1\n")
    (out / "OVERVIEW.md").write_text("keep")
    g.write_output("O", "svc-a", "a: 2\n")
    assert (out / "OVERVIEW.md").read_text() == "keep"
    assert (out / "service.yaml").read_text() == "a: 2\n"
    assert not (tmp_path / "output" / "O" / "svc-a.partial").exists()


def _write_docs(out, spec, mention=""):
    for name, s in spec.items():
        fm = f"---\nservice_id: svc-a\ndoc_type: {s['doc_type']}\nlast_reviewed: 2026-01-01\n---\n"
        body = "".join(f"## {h}\nN/A — not determinable from code\n" for h in s["headings"])
        (out / name).write_text(fm + body + mention)


def test_verify_pass_and_fail(tmp_path):
    spec = v.template_spec()
    paths.set_root(tmp_path)
    rd = paths.runs_dir("O", "svc-a")
    rd.mkdir(parents=True)
    paths.atomic_write_json(rd / "inventory.json", INV)
    out = g.write_output("O", "svc-a", g.dump_yaml(_doc()))
    _write_docs(out, spec)
    cov = v.verify_repo("O", "svc-a", [], spec)
    assert cov["result"] == "fail"
    assert "inbound_http:.:POST:/api/x" in cov["gaps"]["items_missing_in_docs"]
    mention = "/api/x/{id} /api/z x-events svc-b env:DB\n"
    _write_docs(out, spec, mention)
    cov = v.verify_repo("O", "svc-a", [], spec)
    assert cov["result"] == "pass", cov["gaps"]
    assert (rd / "coverage-report.md").read_text().startswith("# Coverage report")
    # heading removed + secret value -> fail
    api = out / "API_SPEC.md"
    api.write_text(api.read_text().replace("## Schemas\n", "") + 'password="hunter2xyz"\n')
    cov = v.verify_repo("O", "svc-a", [], spec)
    assert any("Schemas" in x for x in cov["gaps"]["template_violations"])
    assert cov["gaps"]["secret_hits"]


def test_line_has_secret():
    ok = ["  secret: true", "- name: AppSettings:BRIDGE_AUTH_TOKEN", 'password="${DB_PWD}"',
          "Password=***;", "| `Jwt:Key` | secret | key-vault |", "https://x.example/a?sig=***"]
    bad = ['"password": "hunter2xyz"', "Server=x;Password=abc;", "https://u:p@host/db",
           "eyJhbGciOiJIUzI1.eyJzdWIiOiIx.abc", "ghp_" + "a" * 30]
    assert not [x for x in ok if v.line_has_secret(x)]
    assert all(v.line_has_secret(x) for x in bad)


def test_front_matter_and_headings():
    fm, body = v.split_front_matter("---\nservice_id: a\n---\n## A\n```\n## not\n```\n## B\n")
    assert fm == {"service_id": "a"} and v.headings(body) == ["A", "B"]
    assert v._in_order(["A", "B"], ["B", "A"]) == ["B"]
    assert yaml.safe_load(g.dump_yaml({"x": None})) == {"x": None}

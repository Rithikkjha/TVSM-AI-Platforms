"""Phase 4 resolve: path/topic normalization, route matching and org-level resolution."""
import json

import pytest

from repo_docs import phase4_resolve as p4


@pytest.mark.parametrize("raw,want", [
    ("/API//Bookings/", "/api/bookings"),
    ("/a/{id}", "/a/{}"), ("/a/{id:int}", "/a/{}"), ("/a/:id/b", "/a/{}/b"),
    ("/x/${y}", "/x/{}"), ("/a/[id]", "/a/{}"), ("/a/<id>", "/a/{}"), ("/a/*", "/a/{}"),
    ("/x?q=1#frag", "/x"), ("", "/"), ("/", "/"),
])
def test_norm_path(raw, want):
    assert p4.norm_path(raw) == want


@pytest.mark.parametrize("raw,want", [
    ("dev.cp-booking", "cp-booking"), ("prod.booking", "booking"), ("uat.booking", "booking"),
    ("local.mdp.dealer_data", "mdp.dealer_data"), ("SIT.Orders", "orders"), ("qa.x", "x"),
    ("orders-dev", "orders"), ("orders_uat", "orders"), ("notifications-status-update",
                                                         "notifications-status-update"),
    ("devices", "devices"), ("dev", "dev"), (None, None),
])
def test_norm_topic(raw, want):
    assert p4.norm_topic(raw) == want


def test_placeholders_and_namespaces():
    assert p4.is_placeholder("xxx") and p4.is_placeholder("dev.xxxx") and not p4.is_placeholder("xx")
    assert p4.norm_namespace("xxxx") is None and p4.norm_namespace(None) is None
    assert p4.norm_namespace("nmazcmnasbdev01-uks") == p4.norm_namespace("nmazcmnasbuat01-uks")


def _route(sid, method, path):
    n = p4.norm_path(path)
    return {"sid": sid, "item_id": f"inbound_http:.:{method}:{n}", "method": method, "path": n,
            "segs": p4.segs(n), "item": {}}


def test_match_unique_full_and_suffix():
    routes = [_route("a", "GET", "/api/bookings/{id}"), _route("b", "GET", "/catalogs"),
              _route("c", "POST", "/api/bookings/{id}")]
    v, top = p4.pick(p4.match_routes(["/api/bookings/{}"], "GET", routes))
    assert v == "edge" and top[0][2]["sid"] == "a" and top[0][0] == 2
    # gateway prefix: route is a suffix of the full path
    v, top = p4.pick(p4.match_routes(["/booking-svc/api/bookings/{}"], "GET", routes))
    assert v == "edge" and top[0][2]["sid"] == "a" and top[0][0] == 1
    # unknown method = wildcard -> both a and c -> candidates
    assert p4.pick(p4.match_routes(["/api/bookings/{}"], None, routes))[0] == "candidates"


def test_match_rejects_param_only_and_call_param_vs_literal_suffix():
    routes = [_route("q", "GET", "/{shortCode}"), _route("p", "GET", "/on-road-prices/models/{id}")]
    assert p4.match_routes(["/fish"], "GET", routes) == []
    assert p4.match_routes(["/price-components/{}/models/{}"], "GET", routes) == []


def test_match_multiple_services_are_candidates():
    routes = [_route("a", "DELETE", "/cache/clear"), _route("b", "DELETE", "/cache/clear")]
    v, top = p4.pick(p4.match_routes(["/cache/clear"], "DELETE", routes))
    assert v == "candidates" and {t[2]["sid"] for t in top} == {"a", "b"}


def _item(kind, iid, attrs, file="f.x", source="code"):
    return {"kind": kind, "id": iid, "attributes": attrs, "source": source, "confidence": "high",
            "evidence": [{"file": file, "line": 1, "snippet": "x"}]}


def _call(kind, method, src, path, values=None, role="runtime"):
    return _item(kind, f"{kind}:.:{method}:{src}:{path}", {
        "method": method, "base_url_source": src, "base_url_values": values or {},
        "path_template": path, "role": role, "request": None, "response": None})


def _msg(direction, entity, ns=None, role="runtime", values=None):
    return _item("messaging", f"messaging:.:{direction}:asb:{entity}", {
        "direction": direction, "broker": "azure-service-bus", "entity_type": "topic",
        "entity": entity, "namespace": ns, "resolved_values": values or {}, "role": role,
        "message_types": [], "subscription": None, "filter": None, "name_from": "literal"})


def _repo(name, rtype, items):
    return {"repo": name, "sid": name, "repo_type": rtype, "items": items, "head_sha": "x"}


def test_resolve_org_end_to_end(root):
    inb = _item("inbound_http", "inbound_http:.:GET:/api/v1/bookings/{}",
                {"method": "GET", "path": "/api/v1/bookings/{id}", "responses": [], "request": None})
    twin = _item("inbound_http", "inbound_http:.:GET:/api/v1/bookings/{id}#c",
                 {"method": "GET", "path": "/api/v1/bookings/{id}", "responses": [], "request": None},
                 source="contract")
    repos = {
        "svc": _repo("svc", "service", [inb, twin, _msg("publish", "dev.booking"),
                                        _item("artifact", "artifact:.:maven:g:lib",
                                              {"ecosystem": "maven", "name": "g:lib", "version": "1"})]),
        "fe": _repo("fe", "frontend", [
            _call("frontend_api_call", "GET", "env:API", "/v1/bookings/{}",
                  {"prod": "https://api.example.org/booking"}),
            _call("frontend_api_call", "GET", "env:API", "/nothing/here"),
            _call("frontend_api_call", "GET", "unknown", "/zzz")]),
        "tst": _repo("tst", "test-suite", [_call("outbound_http", "GET", "literal", "/api/v1/bookings/1")]),
        "sub": _repo("sub", "service", [_msg("subscribe", "uat.booking"), _msg("subscribe", "xxxx"),
                                        _msg("subscribe", "dev.other", role="script"),
                                        _item("dependency", "dependency:.:maven:g:lib",
                                              {"ecosystem": "maven", "name": "g:lib", "version": "2",
                                               "internal": True, "internal_repo": None, "kind": "package"})]),
    }
    out = p4.resolve_org("ORG", repos)
    edges = out["edges"]["edges"]
    http = [e for e in edges if e["kind"] == "http"]
    assert len(http) == 1 and http[0]["from"] == "fe" and http[0]["to"] == "svc"
    assert http[0]["caller_type"] == "frontend" and http[0]["to_item"] == inb["id"]  # contract twin ignored
    tests = [e for e in edges if e["kind"] == "tests"]
    assert len(tests) == 1 and tests[0]["caller_type"] == "test-suite"
    ev = [e for e in edges if e["kind"] == "event"]
    assert len(ev) == 1 and ev[0]["from"] == "svc" and ev[0]["to"] == "sub" and ev[0]["confidence"] == "medium"
    lib = [e for e in edges if e["kind"] == "library_dependency"]
    assert len(lib) == 1 and lib[0]["to"] == "svc"
    reasons = {(u["repo"], u["reason"]) for u in out["unresolved"]["items"]}
    assert ("fe", "no_route_match") in reasons and ("fe", "no_base_url") in reasons
    assert ("sub", "placeholder_name") in reasons and ("sub", "script_only") in reasons
    callers = out["services"]["services"]["svc"]["inbound_callers"][inb["id"]]
    assert {c["service_id"] for c in callers} == {"fe", "tst"}
    assert out["services"]["services"]["svc"]["event_consumers"] == {
        "messaging:.:publish:asb:dev.booking": ["sub"]}
    assert out["services"]["services"]["fe"]["config_points_to"] == {"API": ["svc"]}
    ent = out["messaging"]["entities"][0]
    assert ent["name"] == "booking" and ent["raw_names"] == ["dev.booking", "uat.booking"]
    # deterministic
    assert json.dumps(p4.resolve_org("ORG", repos), sort_keys=True) == json.dumps(out, sort_keys=True)


def test_namespace_disagreement_blocks_edge(root):
    repos = {"a": _repo("a", "service", [_msg("publish", "t", ns="ns-one")]),
             "b": _repo("b", "service", [_msg("subscribe", "t", ns="ns-two")])}
    out = p4.resolve_org("ORG", repos)
    assert not [e for e in out["edges"]["edges"] if e["kind"] == "event"]


def test_mixed_segment_keeps_literal_stem():
    assert p4.norm_path("/v2/catalogs{}") == "/v2/catalogs"
    assert p4.norm_path("/v1/catalogs/assemblies${q}") == "/v1/catalogs/assemblies"


def test_suffix_tier_requires_evidence():
    routes = [_route("ccp", "GET", "/catalogs/{id}"), _route("mdp", "GET", "/mdp/v1/product/mna/v2/{sapPartNo}"),
              _route("n", "POST", "/api/v1/notification/email"), _route("d", "GET", "/dealer/{id}/branches")]
    # route param absorbing a call literal with only 1 shared literal -> no match
    assert p4.match_routes(["/v2/catalogs/labour"], "GET", routes) == []
    assert p4.match_routes(["/v2/catalogs"], "GET", routes) == []
    # shared literal last segment, no absorption -> kept
    assert p4.pick(p4.match_routes(["/email"], "POST", routes))[1][0][2]["sid"] == "n"
    assert p4.pick(p4.match_routes(["/branches"], "GET", routes))[1][0][2]["sid"] == "d"
    assert p4.match_routes(["/email"], "POST", routes, allow_suffix=False) == []


def test_norm_namespace_anchored():
    assert p4.norm_namespace("devices") == "devices"
    assert p4.norm_namespace("contest-bus") == "contest-bus"
    assert p4.norm_namespace("bus-dev") == "bus"

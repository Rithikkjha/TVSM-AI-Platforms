"""java.spring Phase 3 Part A over trimmed reproductions of TVS-CS files (tests/fixtures/java/,
source cited per file): helper inlining with arguments, multi-hop wrappers, builder locals,
no-base / absolute uri, @Bean / Lombok client binding, MongoTemplate / OpenSearch / NebulaGraph
data access, @Value param propagation for Service Bus helpers, client-factory suppression.
All hosts are *.example.test and every secret is fake; tests assert none reaches the output."""
from __future__ import annotations

import json
from pathlib import Path

from repo_docs import gaps, phase2_extract as p2
from repo_docs.extractors import java_symbols as js
from repo_docs.extractors import syntax as sx
from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.java_spring import JavaSpring

FIX = Path(__file__).parent / "fixtures" / "java"
BFF = "bff-service/src/main/java/com/tvsm/bff/"
ING = "src/main/java/org/com/graph/"
PCS = "src/main/java/org/com/graph/"


def fx(name: str) -> dict[str, str]:
    root = FIX / name
    return {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*"))
            if p.is_file()}


def _run(files, stacks=(("java", "."),)):
    ctx = RepoContext.for_test(files, list(stacks))
    res = p2.run(ctx)
    assert p2.validate(ctx, res["items"]) == []
    return ctx, res


def _items(res, kind=None):
    return {i.id: i for i in res["items"] if kind is None or i.kind == kind}


def _touch(res, path):
    return next(t for x, _v, t, _n in res["touches"][path] if x == "java.spring")


def _line(text, needle, start=1):
    return next(i for i, ln in enumerate(text.split("\n"), 1) if i >= start and needle in ln)


def _dump(res) -> str:
    return json.dumps([i.to_dict() for i in res["items"]], sort_keys=True)


def _method(idx, path, name, nparams):
    for jt in idx.files[path].types:
        for m in jt.methods:
            if m.name == name and len(m.params) == nparams:
                return jt, m
    raise AssertionError(name)


def _local_value(idx, jt, m, local):
    scope = idx.method_scope(jt, m)
    return idx.resolve_expr(scope.locals[local][0], scope)


# ---- 1. java_symbols: helper inlining with args, UriComponentsBuilder locals ---------------
CPS = [("java", "bff-service"), ("java", "tvs-cps-app")]
UTIL = BFF + "util/ApiPassthroughUtil.java"


def test_helper_with_args_and_uri_builder_local_resolve_to_params():
    ctx = RepoContext.for_test(fx("cps-bff"), CPS)
    idx = js.index(ctx)
    expect = (js.Seg("param", "1"), js.Seg("lit", "/"), js.Seg("param", "2"))
    jt, m = _method(idx, UTIL, "postMethodCall", 7)
    vs = _local_value(idx, jt, m, "fullUrl")  # builder.build().toUriString(), builder = helper
    assert (vs.kind, vs.segs) == ("param", expect)
    jt, m = _method(idx, UTIL, "put", 5)
    vs = _local_value(idx, jt, m, "fullUrl")  # buildSafeUrl(baseUrl, endpoint)
    assert (vs.kind, vs.segs) == ("param", expect)


# ---- 2. java_http: wrapper chains, multi-param substitution --------------------------------
def test_wrapper_chain_through_private_helper_resolves_base_and_path():
    files = fx("cps-bff")
    _c, res = _run(files, CPS)
    out = _items(res, "outbound_http")
    util = files[UTIL]
    post_line = _line(util, "restTemplate.exchange(fullUrl, HttpMethod.POST, entity, MAP_TYPE_REF)")
    get_line = _line(util, "restTemplate.exchange(fullUrl, HttpMethod.GET")
    inv = out["outbound_http:bff-service:POST:config:bff.inventory-service.base-url:"
              "/system/api/v1/inventory/analytics/list"]
    a = inv.attributes
    assert a["client"] == "resttemplate" and inv.confidence == "medium"
    assert a["via_wrapper"] == f"{UTIL}:{post_line}"
    assert a["base_url_values"] == {"default": "https://inventory.example.test/norton-cps-app"}
    assert a["response"] is not None and a["request"] is not None
    ev = {(e.file, e.line) for e in inv.evidence}
    assert (UTIL, post_line) in ev
    assert any(f.endswith("InventoryAnalyticsBFFController.java") for f, _ in ev)
    lst = out["outbound_http:bff-service:GET:config:bff.appointment-service.base-url:"
              "/system/api/v1/appointments/list"]
    assert lst.attributes["via_wrapper"] == f"{UTIL}:{get_line}"
    assert "outbound_http:bff-service:POST:config:bff.appointment-service.base-url:" \
           "/api/v1/appointments/create" in out
    assert _touch(res, UTIL).parse == "full"
    assert _touch(res, BFF + "client/AppointmentClient.java").parse == "full"


# ---- 3. client_base: builder locals, mutate, no-base sentinel, bean / Lombok binding --------
def test_webclient_builder_local_and_mutate_chain_keep_the_base():
    _c, res = _run(fx("cps-bff"), CPS)
    out = _items(res, "outbound_http")
    lead = [i for i in out.values() if i.attributes["base_url_source"] == "config:lead.api.url"]
    paths = {(i.attributes["method"], i.attributes["path_template"]): i.attributes["client"]
             for i in lead}
    assert paths[("POST", "/lead-service/api/v2/lead")] == "webclient"
    # mutate().build() WebClient + RestTemplate URL to the same endpoint merge into one item
    assert paths[("POST", "/lead-service/api/v2/leads/all")] == ["resttemplate", "webclient"]
    booking = out["outbound_http:bff-service:POST:config:bff.booking-service.base-url:"
                  "/booking-service/v2/bookings/search"]
    assert booking.attributes["request"] == "BookingSearchRequestDto"
    assert not [i for i in out.values() if i.attributes["base_url_source"] == "unknown"]


ING_STACKS = [("java", ".")]


def test_restclient_bean_binding_no_base_and_absolute_uri():
    _c, res = _run(fx("parts-ingestion"), ING_STACKS)
    out = list(_items(res, "outbound_http").values())

    def one(file, **want):
        hit = [i for i in out if any(e.file.endswith(file) for e in i.evidence)
               and all(i.attributes[k] == v for k, v in want.items())]
        assert len(hit) == 1, (file, want, [i.id for i in out])
        return hit[0]
    mdp = one("MdpEnrichmentService.java", method="GET")
    assert mdp.attributes["base_url_source"] == "config:catalogue.api.mdp.baseUrl"
    assert mdp.attributes["headers"] == ["x-tenant-id"]
    price = one("PriceApiService.java", method="GET")
    assert price.attributes["base_url_source"] == "config:catalogue.api.price.baseUrl"
    # uri(baseUrl) on a client whose base is that key: the base is used once, not twice
    assert price.attributes["path_template"] == "/"
    assert price.attributes["base_url_values"] == {"default": "https://price.example.test/api"}
    token = one("ApiClientConfig.java", method="POST")
    assert token.attributes["base_url_source"] == "config:catalogue.api.mdp.tokenUrl"
    # "token" is a secret-like key word: the classifier keeps the key, never the value
    assert token.attributes["base_url_values"] == {}
    norton = one("IngestionApiClientService.java", method="GET")  # Lombok @Bean binding
    assert norton.attributes["base_url_source"] == "config:catalogue.api.norton.baseUrl"
    assert "fakeMdpSecret0123456789" not in _dump(res)
    assert "client_secret=" not in _dump(res)


# ---- 4. data access: MongoTemplate / OpenSearch / NebulaGraph -------------------------------
def test_mongo_template_location_and_qrcode():
    _c, res = _run(fx("location"))
    [da] = [i for i in res["items"] if i.kind == "data_access"]
    a = da.attributes
    assert (a["store_type"], a["orm"]) == ("mongo", "mongo-template")
    assert a["collections"] == ["dealership_location"]
    assert a["host"] == "cluster0.example.test" and a["database"] == "locationdb"
    assert [(e["name"], e["operation"]) for e in a["entities"]] == [("DealershipLocation", "both")]
    assert "fakeMongoPw0rd" not in _dump(res)
    svc = "src/main/java/com/tvsmotor/location_master/service/DealershipLocationService.java"
    assert _touch(res, svc).parse == "full"
    _c, res = _run(fx("qrcode"))
    [da] = [i for i in res["items"] if i.kind == "data_access"]
    a = da.attributes
    assert {"qr_redirect_events", "sequences", "qr_codes"} <= set(a["collections"])
    assert a["operation"] == "both"
    assert [(e["name"], e["operation"]) for e in a["entities"]] == [("QrCode", "read")]


def test_opensearch_indices_from_code_defaults_and_nebula_space():
    files = fx("parts-catalogue")
    _c, res = _run(files)
    da = {i.attributes["store_type"]: i for i in res["items"] if i.kind == "data_access"}
    os_ = da["opensearch"].attributes
    assert os_["orm"] == "opensearch-client"
    assert os_["collections"] == ["parts_catalogue", "parts_hierarchies"]
    rows = {e["name"]: e["operation"] for e in os_["entities"]}
    assert rows == {"parts_catalogue": "both", "parts_hierarchies": "read"}
    assert os_["name_from"] == "config:opensearch.host" and os_["host"] is None
    assert da["opensearch"].confidence == "medium"  # code-default index names
    cfg = PCS + "config/OpenSearchConfig.java"
    assert any(e.file == cfg for e in da["opensearch"].evidence)
    assert _touch(res, PCS + "repository/opensearch/HierarchyDataRepository.java").parse == "full"
    assert _touch(res, PCS + "repository/opensearch/BrandCatalogueRepository.java").parse == \
        "partial"  # brandCataloguesIndex: no config value, no code default
    neb = da["nebula"].attributes
    assert neb["orm"] == "nebula-client" and neb["database"] == "parts_catalogue_graph"
    assert neb["name_from"] == "config:nebula.space"
    assert {e["name"]: e["operation"] for e in neb["entities"]} == {"part": "read"}
    assert _touch(res, PCS + "repository/nebula/PartRepository.java").parse == "full"
    assert _touch(res, PCS + "repository/nebula/NebulaGraphRepository.java").parse == "full"
    dump = _dump(res)
    assert "fakeNebulaPw0rd" not in dump and "fakeOsPw0rd" not in dump


# ---- 5. messaging: @Value params of @Bean methods -> private helper -------------------------
def test_service_bus_helper_entity_from_bean_value_params():
    files = fx("notification-dispatcher")
    _c, res = _run(files)
    subs = [i for i in res["items"] if i.kind == "messaging"]
    named = [i for i in subs if i.attributes["entity"] == "local.notifications"]
    assert len(named) == 1
    a = named[0].attributes
    assert a["direction"] == "subscribe"
    assert a["name_from"] == "config:spring.jms.servicebus.topic.notifications"
    assert a["namespace"] == "fake-ns"
    assert a["subscription"] == ["email-notifications", "highpriority-notifications"]
    assert named[0].confidence == "medium"
    cfg = "src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java"
    text = files[cfg]
    lines = {e.line for e in named[0].evidence if e.file == cfg}
    for needle in ("ForHighPriorityNotifications", "ForEmailNotifications"):
        call = _line(text, "return createServiceBusProcessorClient(", _line(text, needle))
        assert call in lines
    orphan = [i for i in subs if any(e.file.endswith("OrphanServiceBusHelper.java")
                                     for e in i.evidence)]
    assert len(orphan) == 1 and orphan[0].attributes["name_from"] == "unknown"
    assert "fakeSbKey0123456789abcdef=" not in _dump(res)


# ---- 7. client factory / holder / interface suppression -------------------------------------
def _gaps(files, stacks):
    ctx, res = _run(files, stacks)
    led = p2.recompute_ledger(ctx, ctx.ledger, res["touches"])
    return gaps.build(ctx, res["items"], led, res["touches"], res["repo_type"]["value"])


def test_client_factory_holder_interface_are_not_silent_client_files():
    doc = _gaps(fx("cps-bff"), CPS)
    silent = {g["file"] for g in doc["gaps"] if g["type"] == "silent_client_file"}
    assert BFF + "config/Config.java" not in silent
    assert doc["summary"]["suppressed"].get("client-factory") == 1
    assert f"{BFF}config/Config.java (client-factory)" in doc["summary"]["suppressed_paths"]
    doc = _gaps(fx("parts-ingestion"), ING_STACKS)
    sup = doc["summary"]["suppressed_paths"]
    assert f"{ING}service/strategy/NortonClientStrategy.java (client-holder)" in sup
    assert f"{ING}service/strategy/IClientStrategy.java (client-interface)" in sup


UNRESOLVED_HOLDER = """package a;
import org.springframework.web.client.RestTemplate;
public class Caller {
    private final RestTemplate restTemplate;
    public Caller(RestTemplate r) { this.restTemplate = r; }
    public String call(String u) { return restTemplate.getForObject(pick(u), String.class); }
}
"""


def test_client_with_an_unresolvable_call_is_still_reported():
    p = "src/main/java/a/Caller.java"
    doc = _gaps({p: UNRESOLVED_HOLDER}, [("java", ".")])
    listed = {(g["type"], g["file"]) for g in doc["gaps"]}
    assert ("partial_parse", p) in listed or ("silent_client_file", p) in listed
    assert doc["summary"]["suppressed"] == {}


# ---- 6. determinism + version ------------------------------------------------------------------
def test_phase3a_deterministic_twice():
    for name, stacks in (("cps-bff", CPS), ("parts-ingestion", ING_STACKS),
                         ("location", ING_STACKS), ("qrcode", ING_STACKS),
                         ("parts-catalogue", ING_STACKS), ("notification-dispatcher",
                                                           ING_STACKS)):
        files = fx(name)
        a, b = _run(files, stacks)[1], _run(files, stacks)[1]
        assert _dump(a) == _dump(b), name
        ta = json.dumps({p: [(x, t.parse, t.error) for x, _v, t, _n in tl]
                         for p, tl in sorted(a["touches"].items())}, sort_keys=True)
        tb = json.dumps({p: [(x, t.parse, t.error) for x, _v, t, _n in tl]
                         for p, tl in sorted(b["touches"].items())}, sort_keys=True)
        assert ta == tb, name
    assert JavaSpring.extractor_version == sx.versioned("0.2.0", "java")

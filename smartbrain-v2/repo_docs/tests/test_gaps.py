"""gaps.json builder (repo_docs/gaps.py): every gap type, summary, pending invariant, determinism."""
from __future__ import annotations

import json

from repo_docs import gaps, phase2_extract as p2
from repo_docs.extractors.base import RepoContext

CTRL = """package a;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
@RestController
@RequestMapping("/api")
public class OrderController {
    private RestTemplate restTemplate;
    @PostMapping("/orders")
    public void create(String raw) {
        restTemplate.postForObject(baseUrl + "/pricing/quote", raw, String.class);
    }
}
"""
CFG = """package a;
import org.springframework.web.client.RestTemplate;
public class HttpConfig {
    public RestTemplate restTemplate() { return new RestTemplate(); }
}
"""
SB = """package a;
import com.azure.messaging.servicebus.*;
public class Publisher {
    public ServiceBusSenderClient sender(String cs) {
        return new ServiceBusClientBuilder().connectionString(cs).sender()
                .topicName(topicFor(cs)).buildClient();
    }
}
"""
BROKEN = "package a;\npublic class Broken { int x = ; }\n"
FILES = {"pom.xml": "<project><artifactId>a</artifactId></project>\n",
         "src/main/java/a/OrderController.java": CTRL,
         "src/main/java/a/HttpConfig.java": CFG,
         "src/main/java/a/Publisher.java": SB,
         "src/main/java/a/Broken.java": BROKEN,
         "scripts/seed.py": "print('seed')\n",
         "src/test/java/a/OrderControllerTest.java": "class OrderControllerTest {}\n"}


def _build(files=FILES, stacks=(("java", "."),)):
    ctx = RepoContext.for_test(files, list(stacks))
    res = p2.run(ctx)
    assert p2.validate(ctx, res["items"]) == []
    led = p2.recompute_ledger(ctx, ctx.ledger, res["touches"])
    return gaps.build(ctx, res["items"], led, res["touches"], res["repo_type"]["value"],
                      "h" * 40, "v1"), res


def _of(doc, typ):
    return [g for g in doc["gaps"] if g["type"] == typ]


def test_every_gap_type_and_summary():
    doc, res = _build()
    assert doc["head_sha"] == "h" * 40 and doc["version"] == "v1"
    assert doc["gaps_version"] == gaps.GAPS_VERSION
    ctrl = "src/main/java/a/OrderController.java"
    [ub] = _of(doc, "unresolved_base_url")
    assert ub["file"] == ctrl and ub["item"].startswith("outbound_http:.:POST:_:")
    [ue] = _of(doc, "unresolved_entity")
    assert ue["file"] == "src/main/java/a/Publisher.java" and ue["item"].startswith("messaging:")
    assert [g["item"] for g in _of(doc, "missing_payload")] == [ue["item"]]
    ms = _of(doc, "missing_schema")
    assert {g["reason"] for g in ms} == {"POST /api/orders: no request schema",
                                        "POST /api/orders: no response schema"}
    pp = {g["file"]: g["reason"] for g in _of(doc, "partial_parse")}
    assert pp["src/main/java/a/Broken.java"].startswith("java.spring: parse error: tree-sitter")
    assert "unresolved" in pp[ctrl]
    [sc] = _of(doc, "silent_client_file")
    assert sc["file"] == "src/main/java/a/HttpConfig.java" and sc["line"] == 2
    assert "RestTemplate" in sc["reason"]
    assert [g["file"] for g in _of(doc, "untouched_source")] == ["scripts/seed.py"]
    unknown = _of(doc, "unknown_repo_type")
    assert len(unknown) == (1 if res["repo_type"]["value"] == "unknown" else 0)
    by = doc["summary"]["by_type"]
    assert set(by) == set(gaps.TYPES)
    for t in gaps.TYPES:
        assert by[t] == len(_of(doc, t))
    assert doc["summary"]["total"] == len(doc["gaps"])
    order = [gaps._order(g) for g in doc["gaps"]]
    assert order == sorted(order)
    for g in doc["gaps"]:
        assert set(g) == {"type", "file", "line", "reason", "item"}
        assert len(g["reason"]) <= gaps.REASON_MAX


def test_untouched_source_is_not_capped():
    files = {f"scripts/s{i}.py": "x = 1\n" for i in range(250)}
    doc, _ = _build(files, ())
    assert len(_of(doc, "untouched_source")) == 250
    assert doc["summary"]["by_type"]["untouched_source"] == 250
    assert doc["summary"]["total"] == len(doc["gaps"])


def test_every_pending_file_is_listed_once():
    files = {**FILES, "docs/notes.md": "# notes\n",
             "src/main/resources/routing.json": "{\"a\": 1}\n"}
    doc, _ = _build(files)
    ctx = RepoContext.for_test(files, [("java", ".")])
    led = p2.recompute_ledger(ctx, ctx.ledger, p2.run(ctx)["touches"])
    pending = sorted(f["path"] for f in led["files"] if f["status"] == "pending")
    file_types = ("partial_parse", "untouched_source", "untouched_file")
    listed = sorted(g["file"] for g in doc["gaps"] if g["type"] in file_types)
    assert listed == pending
    uf = {g["file"]: g["reason"] for g in _of(doc, "untouched_file")}
    assert uf["docs/notes.md"].startswith("docs file left pending")
    assert "src/main/resources/routing.json" in uf


def test_script_tree_messaging_is_not_runtime():
    sub = """package a;
import com.azure.spring.messaging.servicebus.implementation.core.annotation.ServiceBusListener;
public class DealerConsumer {
    @ServiceBusListener(destination = "dev.dealer", group = "g")
    public void on(String m) {}
}
"""
    files = {"pom.xml": FILES["pom.xml"],
             "script/java/service_bus/DealerConsumer.java": sub,
             "src/main/java/a/RealConsumer.java": sub.replace("DealerConsumer", "RealConsumer")
                                                    .replace("dev.dealer", "dev.real")}
    ctx = RepoContext.for_test(files, [("java", ".")])
    res = p2.run(ctx)
    roles = {it.attributes["entity"]: it.attributes["role"] for it in res["items"]
             if it.kind == "messaging"}
    assert roles == {"dev.dealer": "script", "dev.real": "runtime"}


def test_clean_repo_has_no_item_or_file_gaps():
    files = {"pom.xml": "<project><artifactId>a</artifactId></project>\n",
             "src/main/java/a/Util.java": "package a;\npublic class Util { int f() { return 1; } }\n"}
    doc, _ = _build(files)
    assert [g["type"] for g in doc["gaps"]] in ([], ["unknown_repo_type"])


def test_deterministic_in_process():
    a, _ = _build()
    b, _ = _build()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

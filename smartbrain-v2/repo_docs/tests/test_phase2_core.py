"""Phase-2 orchestrator: schema, validation, failure isolation, ledger recompute, staleness, CLI."""
from __future__ import annotations

import json
import os

import pytest

from conftest import FAKE_TOKEN
from phase2_helpers import make_ledgered_repo
from repo_docs import paths, phase1_ledger as p1, phase2_extract as p2
from repo_docs.cli import main
from repo_docs.extractors import registry as reg
from repo_docs.extractors.base import Evidence, ExtractResult, RepoContext
from repo_docs.inventory_schema import (DICT_ATTRS, KINDS, LIST_ATTRS, SchemaError, make_item,
                                        validate_item)
from repo_docs.state import StateStore

FAKE_PW = "fakeP4ssw0rdValue"
FILES = {
    "appsettings.json": '{\n  "ServiceBusSettings": {"TopicName": "booking-events"},\n'
                        f'  "Db": {{"Password": "{FAKE_PW}"}}\n}}\n',
    "src/App.cs": "class App {}\n",
}


@pytest.fixture
def store(root):
    return StateStore()


def _inv(name="alpha"):
    return paths.read_json(paths.runs_dir("TEST-ORG", name) / "inventory.json")


def _ledger(name="alpha"):
    return paths.read_json(paths.runs_dir("TEST-ORG", name) / "ledger.json")


def test_every_kind_has_exactly_the_schema_keys():
    ex = ("t.x", "0.1.0")
    for kind, keys in KINDS.items():
        it = make_item(kind, ".", "k", {}, [Evidence("f", 1, "x")], ex)
        assert set(it.attributes) == set(keys)
        for k in LIST_ATTRS[kind]:
            assert it.attributes[k] == []
        for k in DICT_ATTRS[kind]:
            assert it.attributes[k] == {}
    assert "context_path_by_env" in KINDS["inbound_http"]
    with pytest.raises(SchemaError):
        make_item("config_key", ".", "k", {"bogus": 1}, [], ex)
    with pytest.raises(SchemaError):
        make_item("nope", ".", "k", {}, [], ex)


def test_validate_item_rules():
    ctx = RepoContext.for_test({"a.txt": "hello world\n", "node_modules/x.js": "x\n"})
    ex = ("t.x", "0.1.0")
    good = make_item("config_key", ".", "k", {}, [ctx.evidence("a.txt", 1)], ex)
    assert validate_item(good, ctx.ledger_index, ctx.line) == []
    for ev, msg in [(Evidence("a.txt", 1, "not there"), "substring"),
                    (Evidence("a.txt", 5, "hello"), "out of range"),
                    (Evidence("node_modules/x.js", 1, "x"), "skipped"),
                    (Evidence("missing.txt", 1, "x"), "not in ledger")]:
        bad = make_item("config_key", ".", "k", {}, [ev], ex)
        errs = validate_item(bad, ctx.ledger_index, ctx.line)
        assert errs and msg in errs[0]
    noev = make_item("config_key", ".", "k", {}, [], ex)
    assert any("no evidence" in e for e in validate_item(noev, ctx.ledger_index, ctx.line))


def test_extract_end_to_end_and_fresh(root, org_cfg, store):
    head = make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    res = p2.extract_all(org_cfg, store)
    assert res["results"] == {"alpha": "done"}
    inv = _inv()
    assert inv["head_sha"] == head and inv["version"].startswith(p2.PHASE_VERSION + "+")
    ids = [i["id"] for i in inv["items"]]
    assert "config_key:.:servicebussettings.topicname" in ids
    topic = next(i for i in inv["items"] if i["id"] == "config_key:.:servicebussettings.topicname")
    assert topic["attributes"]["values"] == {"default": "booking-events"}
    pw = next(i for i in inv["items"] if i["id"] == "config_key:.:db.password")
    assert pw["attributes"]["secret"] and pw["attributes"]["values"] == {}
    led = {f["path"]: f for f in _ledger()["files"]}
    assert led["appsettings.json"]["status"] == "extracted"
    assert led["appsettings.json"]["extractors"][0]["id"] == "shared.config"
    assert led["src/App.cs"]["status"] == "pending" and "extractors" not in led["src/App.cs"]
    ph = store.phase("TEST-ORG", "alpha", "extract")
    assert ph["status"] == "done" and ph["input_sha"] == head
    assert ph["missing_extractors"] == []  # no csproj -> no dotnet stack detected
    assert ph["registry_hash"] and ph["ledger_generated_at"] == _ledger()["generated_at"]
    assert set(ph["counts"]) >= {"items", "files_extracted", "files_partial", "files_untouched",
                                 "file_errors", "files_failed", "by_kind"}
    meta = paths.read_json(paths.runs_dir("TEST-ORG", "alpha") / "meta.json")
    assert meta["extract"]["version"] == inv["version"] and "repo_type" in meta
    for f in ("inventory.json", "ledger.json", "meta.json"):
        assert FAKE_PW not in (paths.runs_dir("TEST-ORG", "alpha") / f).read_text()
    assert FAKE_PW not in paths.state_path().read_text()
    assert p2.extract_all(org_cfg, store)["results"] == {"alpha": "fresh"}
    before = (paths.runs_dir("TEST-ORG", "alpha") / "inventory.json").read_bytes()
    assert p2.extract_all(org_cfg, store, force=True)["results"] == {"alpha": "done"}
    assert (paths.runs_dir("TEST-ORG", "alpha") / "inventory.json").read_bytes() == before


def test_validation_failure_fails_repo_and_keeps_previous(root, org_cfg, store, monkeypatch):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    assert p2.extract_one(org_cfg, store, "alpha") == "done"
    before = (paths.runs_dir("TEST-ORG", "alpha") / "inventory.json").read_bytes()
    led_before = (paths.runs_dir("TEST-ORG", "alpha") / "ledger.json").read_bytes()
    ex = reg.get_extractor("shared.sql")

    def bad(ctx, sub):
        r = ExtractResult()
        r.items.append(make_item("config_key", ".", "zz", {}, [Evidence("src/App.cs", 1,
                                                                        "invented")], ex))
        return r

    monkeypatch.setattr(ex, "extract", bad)
    assert p2.extract_one(org_cfg, store, "alpha", force=True) == "failed"
    ph = store.phase("TEST-ORG", "alpha", "extract")
    assert ph["status"] == "failed" and "invalid item" in ph["error"]
    assert (paths.runs_dir("TEST-ORG", "alpha") / "inventory.json").read_bytes() == before
    assert (paths.runs_dir("TEST-ORG", "alpha") / "ledger.json").read_bytes() == led_before


def test_extractor_exception_isolates_repo(root, org_cfg, store, monkeypatch, caplog):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    make_ledgered_repo(root, org_cfg, store, "beta", {"x.sql": "CREATE TABLE t (a int);\n"})
    saved = list(__import__("repo_docs.secrets", fromlist=["x"]).SecretFilter._secrets)
    from repo_docs.secrets import SecretFilter
    SecretFilter.register(FAKE_TOKEN)
    ex = reg.get_extractor("shared.sql")
    real = type(ex).extract

    def boom(ctx, sub):
        if ctx.repo == "beta":
            raise RuntimeError(f"bug {FAKE_TOKEN}")
        return real(ex, ctx, sub)

    monkeypatch.setattr(ex, "extract", boom)
    try:
        res = p2.extract_all(org_cfg, store, workers=1)
    finally:
        SecretFilter._secrets[:] = saved
    assert res["results"] == {"alpha": "done", "beta": "failed"} and res["failed"] == ["beta"]
    err = store.phase("TEST-ORG", "beta", "extract")["error"]
    assert "RuntimeError" in err and FAKE_TOKEN not in err and FAKE_TOKEN not in caplog.text
    assert not (paths.runs_dir("TEST-ORG", "beta") / "inventory.json").exists()


def test_parse_error_goes_to_errors_and_file_stays_pending(root, org_cfg, store):
    make_ledgered_repo(root, org_cfg, store, "alpha", {"appsettings.json": '{"a": \n',
                                                       "src/x.cs": "class X {}\n"})
    assert p2.extract_one(org_cfg, store, "alpha") == "done"
    inv = _inv()
    assert inv["errors"] and inv["errors"][0]["file"] == "appsettings.json"
    assert inv["errors"][0]["extractor"] == "shared.config"
    f = {x["path"]: x for x in _ledger()["files"]}["appsettings.json"]
    assert f["status"] == "pending" and f["extractors"][0]["parse"] == "partial"
    assert "error" in f["extractors"][0]
    assert store.phase("TEST-ORG", "alpha", "extract")["counts"]["file_errors"] == 1


def test_failed_missing_is_preserved(root, org_cfg, store):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    os.remove(paths.clone_dir("TEST-ORG", "alpha") / "src/App.cs")
    assert p1.ledger_one(org_cfg, store, "alpha") == "done"
    assert p2.extract_one(org_cfg, store, "alpha") == "done"
    f = {x["path"]: x for x in _ledger()["files"]}
    assert f["src/App.cs"]["status"] == "failed:missing"
    assert store.phase("TEST-ORG", "alpha", "extract")["counts"]["files_failed"] == 1


def test_zero_extractor_repo_gives_valid_empty_inventory(root, org_cfg, store):
    make_ledgered_repo(root, org_cfg, store, "alpha", {"src/Main.kt": "fun main() {}\n"})
    before = [f["status"] for f in _ledger()["files"]]
    assert p2.extract_one(org_cfg, store, "alpha") == "done"
    assert _inv()["items"] == [] and _inv()["errors"] == []
    assert [f["status"] for f in _ledger()["files"]] == before


def test_status_stale_after_ledger_rebuild_and_registry_edit(root, org_cfg, store, monkeypatch,
                                                            capsys):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    assert main(["extract", "--org", "TEST-ORG"]) == 0
    capsys.readouterr()
    assert main(["status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["TEST-ORG"]["phases"]["extract"] == {"done": 1}
    monkeypatch.setattr(paths, "utcnow", lambda: "2099-01-01T00:00:00Z")
    assert main(["ledger", "--org", "TEST-ORG", "--force"]) == 0
    capsys.readouterr()
    assert main(["status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["TEST-ORG"]["phases"]["extract"] == {"stale": 1}
    assert main(["extract", "--org", "TEST-ORG"]) == 0
    capsys.readouterr()
    paths.external_systems_path().parent.mkdir(parents=True, exist_ok=True)
    paths.external_systems_path().write_text("schema_version: 1\nsystems: []\n")
    assert main(["status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["TEST-ORG"]["phases"]["extract"] == {"stale": 1}


def test_cli_extract_exit_codes_and_log(root, org_cfg, store, monkeypatch, capsys):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    assert main(["extract", "--org", "TEST-ORG"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["TEST-ORG"]["counts"] == {"done": 1}
    assert list(paths.logs_dir("TEST-ORG").glob("extract-*.log"))
    ex = reg.get_extractor("shared.config")
    monkeypatch.setattr(ex, "extract", lambda ctx, sub: (_ for _ in ()).throw(ValueError("x")))
    assert main(["extract", "--org", "TEST-ORG", "--force"]) == 1
    assert json.loads(capsys.readouterr().out)["TEST-ORG"]["failed"] == ["alpha"]
    assert main(["extract", "--org", "TEST-ORG", "--repo", "nope"]) == 2


def test_extract_refuses_without_fresh_ledger(root, org_cfg, store):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    store.upsert_repo("TEST-ORG", "alpha", {"head_sha": "0" * 40})
    assert p2.extract_all(org_cfg, store)["results"] == {"alpha": "no-ledger"}
    assert p2.extract_one(org_cfg, store, "alpha") == "failed"


def test_composite_version_changes_with_registry():
    meta = {"stacks": []}
    a = p2.current_version(meta, b"")
    b = p2.current_version(meta, b"schema_version: 1\n")
    assert a != b and a.startswith(p2.PHASE_VERSION + "+") and len(a.split("+")[1]) == 12


def test_merge_code_beats_contract_and_runtime_beats_tests_target():
    ev = [Evidence("f", 1, "x")]
    code = make_item("inbound_http", ".", "POST:/b", {
        "method": "POST", "handler": "BookingsController.create", "request": "BookingDto",
        "responses": [{"status": 202, "schema": "Booking", "when": None, "from": "code"}]},
        ev, ("java.spring", "1"))
    contract = make_item("inbound_http", ".", "POST:/b", {
        "method": "POST", "handler": None, "request": "CreateBooking", "contract_file": "o.yaml",
        "responses": [{"status": 202, "schema": "Booking", "when": "accepted",
                       "from": "contract"},
                      {"status": 400, "schema": None, "when": "bad", "from": "contract"}]},
        [Evidence("o.yaml", 3, "post:")], ("shared.contracts", "1"), source="contract")
    [m] = p2.merge_items([contract, code])
    a = m.attributes
    assert a["handler"] == "BookingsController.create" and a["request"] == "BookingDto"
    assert a["contract_file"] == "o.yaml" and m.confidence == "high"
    assert m.extractor_id == "java.spring" and m.source == "code"
    assert a["responses"] == [{"status": 202, "schema": "Booking", "when": "accepted",
                               "from": "code"},
                              {"status": 400, "schema": None, "when": "bad",
                               "from": "contract"}]
    rt = make_item("outbound_http", ".", "GET:x:/", {"role": "runtime", "response": "A"}, ev,
                   ("java.spring", "1"))
    tt = make_item("outbound_http", ".", "GET:x:/", {"role": "tests_target", "response": "B"},
                   ev, ("java.spring", "1"))
    [o] = p2.merge_items([tt, rt])
    assert o.attributes["role"] == "runtime" and o.attributes["response"] == "A"
    a1 = make_item("outbound_http", ".", "GET:y:/", {"response": "A"}, ev, ("java.spring", "1"))
    a2 = make_item("outbound_http", ".", "GET:y:/", {"response": "B"}, ev, ("java.spring", "1"))
    [c] = p2.merge_items([a1, a2])
    assert c.attributes["response"] == ["A", "B"] and c.confidence == "medium"


def test_gaps_json_written_and_missing_gaps_is_stale(root, org_cfg, store):
    make_ledgered_repo(root, org_cfg, store, "alpha", FILES)
    assert p2.extract_all(org_cfg, store)["results"] == {"alpha": "done"}
    gp = paths.runs_dir("TEST-ORG", "alpha") / "gaps.json"
    doc = paths.read_json(gp)
    assert doc["version"] == _inv()["version"] and doc["head_sha"] == _inv()["head_sha"]
    assert doc["summary"]["by_type"]["untouched_source"] == 1     # src/App.cs, no dotnet stack
    assert store.phase("TEST-ORG", "alpha", "extract")["gaps"] == doc["summary"]["by_type"]
    assert FAKE_PW not in gp.read_text()
    before = gp.read_bytes()
    assert p2.extract_all(org_cfg, store)["results"] == {"alpha": "fresh"}
    gp.unlink()
    assert p2.extract_all(org_cfg, store)["results"] == {"alpha": "done"}
    assert gp.read_bytes() == before

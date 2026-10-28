"""Deterministic service aliases (repo_docs.aliases) + generate wiring."""
from pathlib import Path

import yaml

from repo_docs import aliases as al
from repo_docs import paths
from repo_docs import phase5_generate as g


def test_split_ident_camel_snake_kebab_dotted():
    assert al.split_ident("BookingServiceClient") == ["booking", "service", "client"]
    assert al.split_ident("BOOKING_SERVICE_URL") == ["booking", "service", "url"]
    assert al.split_ident("bff.booking-service.base-url") == ["bff", "booking", "service", "base", "url"]
    assert al.split_ident("MDPServiceClient") == ["mdp", "service", "client"]
    assert al.split_ident("BS2.0Backend_Integration") == ["bs2.0", "backend", "integration"]


def test_key_words_strips_url_suffix_and_prefixes():
    assert al.key_words("BOOKING_SERVICE_URL") == ["booking", "service"]
    assert al.key_words("bookingService.api.base-url") == ["booking", "service"]
    assert al.key_words("bff.booking-service.base-url") == ["booking", "service"]
    assert al.key_words("REACT_APP_BOOKING_API_URL") == ["booking"]
    assert al.key_words("ums.base.url") == ["ums"]
    assert al.key_words("spring.datasource.username") == []  # not URL-shaped


def test_class_words():
    assert al.class_words("BookingServiceClient") == (["booking"], "medium")
    assert al.class_words("NotificationGateway") == (["notification"], "medium")
    assert al.class_words("UMSService") == (["ums"], "low")
    assert al.class_words("OkHttpService") is None
    assert al.class_words("dataService") is None


def test_name_variants_suffix_stripping():
    v = al.name_variants(["booking", "crud", "services"])
    for want in ("booking crud services", "booking crud service", "booking service", "booking"):
        assert want in v
    assert "booking crud" not in v
    v = al.name_variants(["catalog", "microservice", "backend", "for", "frontend", "layer"])
    assert "catalog" in v and "catalog microservice bff" not in v
    v = al.name_variants(["tvs", "cps", "billing"])
    assert "cps billing" in v and "billing" in v


def test_junk_filter():
    for junk in ("service", "api", "be", "backend app", "xxx", "xxxx topic", "tvsm", "readme",
                 "ab", "${artifactid}", "cd pipeline"):
        assert al.is_junk(junk), junk
    for ok in ("booking", "mdp", "booking service", "auth ninja"):
        assert not al.is_junk(ok), ok


def _inv(sid, repo, items=()):
    return {"service_id": sid, "repo": repo, "items": list(items)}


def _out(iid, base, file):
    return {"kind": "outbound_http", "id": iid, "evidence": [{"file": file, "line": 7}],
            "attributes": {"base_url_source": base, "client": "webclient"}}


def _collect():
    invs = {"booking-crud-services": _inv("booking-crud-services", "booking-crud-services"),
            "appointment-booking-service": _inv("appointment-booking-service",
                                                "appointment-booking-service"),
            "caller": _inv("caller", "Caller", [
                _out("o1", "config:bff.booking-service.base-url", "src/BookingServiceClient.java"),
                _out("o2", "env:APPOINTMENT_BOOKING_URL", "src/BookingGateway.java")])}
    edges = [{"id": "1", "kind": "http", "from": "caller", "to": "booking-crud-services",
              "from_items": ["o1"], "caller_type": "service"},
             {"id": "2", "kind": "http", "from": "caller", "to": "appointment-booking-service",
              "from_items": ["o2"], "caller_type": "service"}]
    return al.collect("ORG", invs, edges, {}, {}), invs


def test_collect_caller_sources_and_ambiguity():
    col, invs = _collect()
    b = col.data["booking-crud-services"]
    assert b["booking crud services"]["confidence"] == "high"  # spaced repo name
    assert b["booking service"]["confidence"] == "medium"  # caller key beats derived (low)
    assert any(s["type"] == "caller_config" and s["repo"] == "Caller" and s["line"] == 7
               for s in b["booking service"]["sources"])
    assert any(s["type"] == "caller_client" for s in b["booking"]["sources"])
    merged = al.merge(col.data, {}, invs)
    amb = al.ambiguous_map(merged)
    assert amb["booking"] == ["appointment-booking-service", "booking-crud-services"]


def test_manual_override_precedence(tmp_path):
    col, invs = _collect()
    mp = tmp_path / "aliases.manual.yaml"
    mp.write_text("bs: [booking-crud-services]\nbooking: booking-crud-services\n"
                  "x1: [no-such-service]\n", encoding="utf-8")
    merged = al.merge(col.data, al.load_manual(mp), invs)
    assert merged["booking-crud-services"]["bs"]["confidence"] == "manual"
    assert merged["booking-crud-services"]["booking"]["confidence"] == "manual"
    assert "booking" not in merged["appointment-booking-service"]  # manual wins
    assert "booking" not in al.ambiguous_map(merged)
    assert all("x1" not in m for m in merged.values())
    doc = al.build_doc("ORG", merged, {})
    assert al.ranked(doc["services"]["booking-crud-services"], 2)[0] in ("bs", "booking")


def test_determinism():
    a = al.dump(al.build_doc("ORG", al.merge(_collect()[0].data, {}, _collect()[1]), {}))
    b = al.dump(al.build_doc("ORG", al.merge(_collect()[0].data, {}, _collect()[1]), {}))
    assert a == b


def test_run_writes_registry_and_manual_template(tmp_path, monkeypatch):
    paths.set_root(tmp_path)
    try:
        class Store:
            def repos(self, org):
                return {"booking-crud-services": {}}
        rd = paths.runs_dir("ORG", "booking-crud-services")
        paths.atomic_write_json(rd / "inventory.json",
                                _inv("booking-crud-services", "booking-crud-services"))
        clone = paths.clone_dir("ORG", "booking-crud-services")
        clone.mkdir(parents=True)
        (clone / "README.md").write_text("# Booking Service\n\nThe **Booking Service** does x\n")
        res = al.run("ORG", Store())
        assert res["services"] == 1
        assert (tmp_path / "config" / "aliases.manual.yaml").read_text().startswith("# User-owned")
        doc = yaml.safe_load(al.aliases_path().read_text())
        rows = doc["services"]["booking-crud-services"]["aliases"]
        bs = next(r for r in rows if r["alias"] == "booking service")
        assert {"type": "readme_h1", "repo": "booking-crud-services", "file": "README.md",
                "line": 1} in bs["sources"]
        # manual template is never overwritten
        mp = tmp_path / "config" / "aliases.manual.yaml"
        mp.write_text("bs: [booking-crud-services]\n")
        al.run("ORG", Store())
        assert mp.read_text() == "bs: [booking-crud-services]\n"
        assert al.load_registry()["booking-crud-services"]["aliases"][0]["alias"] == "bs"
    finally:
        paths.set_root(paths.DEFAULT_ROOT)


def test_refresh_overview_idempotent():
    text = ("---\nservice_id: s\ndoc_type: overview\naliases:\n  - old\nlast_reviewed: 2026-01-01\n"
            "---\n# s — Overview\n## Purpose\nBody text.\n## Users and Consumers\nx\n")
    once = g.refresh_overview(text, ["booking service", "bs"], "Does bookings.")
    twice = g.refresh_overview(once, ["booking service", "bs"], "Does bookings.")
    assert once == twice
    fm = yaml.safe_load(once.split("---")[1])
    assert fm["aliases"] == ["booking service", "bs"] and fm["last_reviewed"]
    assert ("## Purpose\nSummary: Does bookings.\nAlso known as: booking service, bs\nBody text."
            in once)
    assert "## Users and Consumers" in once and "old" not in once


def test_build_service_yaml_uses_aliases_and_summaries():
    reg = g.Registry([], {}, [], aliases={"svc-a": {"aliases": [
        {"alias": "svc-a", "confidence": "high"}, {"alias": "svc a", "confidence": "high"},
        {"alias": "a svc", "confidence": "medium"}]}},
        summaries={"svc-a": {"summary": "Does A.", "domain": "booking"}})
    doc = g.build_service_yaml({"service_id": "svc-a", "repo": "svc-a", "items": []}, {}, reg)
    assert doc["aliases"] == ["svc a", "a svc"]
    assert doc["summary"] == "Does A." and doc["domain"] == "booking"

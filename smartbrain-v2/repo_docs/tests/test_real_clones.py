"""Smoke tests over the real TVS-CS clones (skipped when the clone or its phase-1 outputs are
absent). Read-only: the clone and runs/ ledger+meta are only read, results stay in memory
(``phase2_extract.run`` writes nothing)."""
from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

from repo_docs import phase2_extract as p2
from repo_docs.extractors.base import RepoContext

RD = Path(__file__).resolve().parents[1]


def _ctx(repo: str) -> RepoContext:
    run = RD / "runs" / "TVS-CS" / repo
    return RepoContext("TVS-CS", repo, RD / "repos" / "TVS-CS" / repo,
                       json.loads((run / "ledger.json").read_text()),
                       json.loads((run / "meta.json").read_text()), [], [])


def _available(repo: str) -> bool:
    run = RD / "runs" / "TVS-CS" / repo
    return (RD / "repos" / "TVS-CS" / repo).is_dir() and (run / "ledger.json").is_file() \
        and (run / "meta.json").is_file()


@pytest.mark.skipif(not _available("master-data-platform"),
                    reason="master-data-platform clone / ledger absent")
def test_master_data_platform_real_clone():
    ctx = _ctx("master-data-platform")
    res = p2.run(ctx)
    items = res["items"]
    assert p2.validate(ctx, items) == []
    inbound = [i for i in items if i.kind == "inbound_http"]
    assert inbound and all(i.attributes["path"].startswith("/mdp/") for i in inbound)
    key = "config:spring.jms.servicebus.topic.dealerData.name"
    msgs = {i.id: i.attributes for i in items if i.kind == "messaging"}
    pub = msgs[f"messaging:.:publish:azure-service-bus:{key}"]
    sub = msgs[f"messaging:.:subscribe:azure-service-bus:{key}"]
    assert pub["name_from"] == key and sub["name_from"] == key
    assert pub["entity"] and pub["entity"] == sub["entity"]
    assert sub["subscription"]
    by_kind = collections.Counter(i.kind for i in items if i.extractor_id == "java.spring")
    assert by_kind["inbound_http"] >= 60 and by_kind["messaging"] >= 9


def _real(repo: str):
    ctx = _ctx(repo)
    res = p2.run(ctx)
    assert p2.validate(ctx, res["items"]) == []
    return res["items"]


# ---- Phase 3 Part A ---------------------------------------------------------------------------
@pytest.mark.skipif(not _available("notification-dispatcher-service"),
                    reason="notification-dispatcher-service clone / ledger absent")
def test_notification_dispatcher_service_bus_helper_entity():
    msgs = [i.attributes for i in _real("notification-dispatcher-service")
            if i.kind == "messaging"]
    assert any(a["direction"] == "subscribe" and a["entity"] == "local.notifications"
               for a in msgs)


@pytest.mark.skipif(not _available("Parts-Catalogue-Service"),
                    reason="Parts-Catalogue-Service clone / ledger absent")
def test_parts_catalogue_opensearch_and_nebula_stores():
    da = {i.attributes["store_type"]: i.attributes for i in _real("Parts-Catalogue-Service")
          if i.kind == "data_access"}
    assert "parts_hierarchies" in da["opensearch"]["collections"]
    assert da["nebula"]["entities"]


@pytest.mark.skipif(not _available("tvsmbe-location"), reason="tvsmbe-location clone absent")
def test_location_mongo_template_collection():
    da = [i.attributes for i in _real("tvsmbe-location")
          if i.kind == "data_access" and i.attributes["store_type"] == "mongo"]
    assert len(da) == 1 and "dealership_location" in da[0]["collections"]


@pytest.mark.skipif(not _available("Parts-Catalogue-Ingestion-Service"),
                    reason="Parts-Catalogue-Ingestion-Service clone / ledger absent")
def test_parts_ingestion_restclient_bases():
    out = [i.attributes for i in _real("Parts-Catalogue-Ingestion-Service")
           if i.kind == "outbound_http"]
    known = [a for a in out if a["base_url_source"] != "unknown"]
    assert len(known) >= 4
    assert any(a["base_url_source"] == "config:catalogue.api.mdp.baseUrl" for a in known)

"""Read-only smoke tests of node.backend / node.frontend on the real TVS-CS clones (FEAT-004).
Skipped when the clones / phase-1 ledgers are absent. Nothing is written."""
from __future__ import annotations

import json

import pytest

from repo_docs import paths
from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.node_backend import NodeBackendExtractor
from repo_docs.extractors.node_frontend import NodeFrontendExtractor
from repo_docs.extractors.shared_config import SharedConfig
from repo_docs.extractors.shared_infra import SharedInfra
from repo_docs.inventory_schema import validate_item
from repo_docs.phase2_extract import merge_items

ROOT = paths.DEFAULT_ROOT
ORG = "TVS-CS"


def _ctx(repo: str) -> RepoContext:
    rd = ROOT / "runs" / ORG / repo
    clone = ROOT / "repos" / ORG / repo
    if not (rd / "ledger.json").is_file() or not (rd / "meta.json").is_file() or \
            not clone.is_dir():
        pytest.skip(f"{repo} clone/ledger not present")
    ledger = json.loads((rd / "ledger.json").read_text())
    meta = json.loads((rd / "meta.json").read_text())
    return RepoContext(ORG, repo, clone, ledger, meta, [])


def _items(repo: str) -> dict:
    ctx = _ctx(repo)
    SharedConfig().extract(ctx, None)
    SharedInfra().extract(ctx, None)
    items = []
    for ex in (NodeBackendExtractor(), NodeFrontendExtractor()):
        for sub in ctx.subprojects:
            if ex.applies_to(ctx.meta, sub):
                items += ex.extract(ctx, sub).items
    items = merge_items(items)
    assert [p for it in items for p in validate_item(it, ctx.ledger_index, ctx.line)] == []
    return {it.id: it for it in items}


def test_price_bff_inbound_and_outbound():
    items = _items("Price-Microservice-Backend-for-Frontend-Layer")
    inb = items["inbound_http:.:GET:/regions/{}/states"].attributes
    assert inb["path"] == "/regions/{country}/states" and inb["framework"] == "express"
    out = items["outbound_http:.:GET:env:PRICE_MICROSERVICE_BASE_URL:/regions/{}/states"]
    assert out.attributes["via_wrapper"] == "src/rest/http/http.ts:10"
    assert out.attributes["path_template"] == "/regions/{}/states"


def test_location_frontend_dealer_countries():
    items = _items("location-frontend")
    it = items["frontend_api_call:.:GET:env:REACT_APP_DEALER_BASE_URL:/api/v1/user-x/{}/countries"]
    a = it.attributes
    assert a["ui_framework"] == "react" and a["base_url_kind"] == "dotenv"
    assert set(a["base_url_values"]) == {"dev", "uat", "prod"}
    assert all("?" not in v for v in a["base_url_values"].values())

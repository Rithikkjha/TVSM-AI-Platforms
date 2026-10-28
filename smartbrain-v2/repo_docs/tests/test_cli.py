from __future__ import annotations

import json

import pytest

from repo_docs import paths
from repo_docs.cli import PLANNED, main
from repo_docs.extractors import registry as reg


def test_status_empty(root, capsys):
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "TEST-ORG" in out and "discover --org TEST-ORG" in out
    assert main(["status", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["TEST-ORG"]["repo_count"] == 0
    assert "ingest" in data["TEST-ORG"]["phases"]


@pytest.mark.parametrize("cmd", list(PLANNED))
def test_stub_commands_exit_2(root, cmd, capsys):
    assert main([cmd, "--org", "TEST-ORG"]) == 2
    assert "planned" in capsys.readouterr().err
    assert not paths.state_path().exists()


def test_extract_is_implemented():
    assert "extract" not in PLANNED and "ingest" in PLANNED and "eval" in PLANNED


def test_unknown_org_and_repo(root, capsys):
    assert main(["status", "--org", "UNKNOWN"]) == 2
    assert "unknown org" in capsys.readouterr().err
    assert main(["ledger", "--org", "TEST-ORG", "--repo", "nope"]) == 2


def test_registry_order_and_planned_stubs():
    ids = list(reg.REGISTRY)
    assert ids[:5] == ["shared.config", "shared.manifests", "shared.infra", "shared.contracts",
                       "shared.sql"]
    assert ids[5:] == sorted(ids[5:])
    planned = {f"{s}.planned" for s in ("android", "react-native", "vue", "python", "ios", "dart",
                                        "flutter", "php")}
    assert set(reg.planned_ids()) == planned
    for i in planned:
        ex = reg.get_extractor(i)
        assert ex.status == "planned" and ex.applies_to({"stacks": [
            {"stack": ex.stacks[0], "subproject": "."}]}, ".")
        with pytest.raises(NotImplementedError):
            ex.extract(None, ".")
    meta = {"stacks": [{"stack": "vue", "subproject": "web"}, {"stack": "java", "subproject": "."}]}
    assert [(e.id, s) for e, s in reg.applicable(meta)] == \
        [(c.id, None) for c in reg.SHARED] + [("java.spring", ".")]
    assert reg.missing_extractors(meta) == ["vue"]


def test_registry_multi_stack_dispatch():
    """D-P6: java/node/.NET extractors coexist; each (extractor, subproject) runs once."""
    assert [c.id for c in reg.STACK_EXTRACTORS] == ["dotnet.aspnet", "java.spring", "node.backend",
                                                    "node.frontend"]
    meta = {"stacks": [{"stack": "java", "subproject": "."},
                       {"stack": "node", "subproject": "api"}, {"stack": "nest", "subproject": "api"},
                       {"stack": "node", "subproject": "web"}, {"stack": "react", "subproject": "web"},
                       {"stack": "nextjs", "subproject": "web"},
                       {"stack": "node", "subproject": "jobs"},
                       {"stack": "dotnet", "subproject": "svc"}]}
    assert [(e.id, s) for e, s in reg.applicable(meta)] == \
        [(c.id, None) for c in reg.SHARED] + [
            ("dotnet.aspnet", "svc"), ("java.spring", "."), ("node.backend", "api"),
            ("node.backend", "jobs"), ("node.frontend", "web")]
    assert reg.missing_extractors(meta) == []

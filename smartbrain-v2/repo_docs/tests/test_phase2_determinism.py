"""Cross-process determinism (plan item 7): one multi-stack repo (java + node backend + react +
dotnet subprojects) extracted in two interpreters with different PYTHONHASHSEED gives
byte-identical inventory items, errors, ledger statuses and gaps.json."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from test_dotnet_aspnet import PAY
from test_java_spring import MDP
from test_node_backend import load

ROOT = Path(__file__).resolve().parents[1]
CHILD = r"""
import json, sys
from repo_docs import gaps, phase2_extract as p2
from repo_docs.extractors.base import RepoContext
spec = json.loads(open(sys.argv[1]).read())
ctx = RepoContext.for_test(spec["files"], [tuple(s) for s in spec["stacks"]])
res = p2.run(ctx)
assert p2.validate(ctx, res["items"]) == []
led = p2.recompute_ledger(ctx, ctx.ledger, res["touches"])
doc = {"items": [i.to_dict() for i in res["items"]], "errors": res["errors"],
       "repo_type": res["repo_type"]["value"],
       "ledger": [(f["path"], f["status"], f.get("extractors")) for f in led["files"]],
       "gaps": gaps.build(ctx, res["items"], led, res["touches"], res["repo_type"]["value"])}
sys.stdout.write(json.dumps(doc, sort_keys=True, ensure_ascii=False))
"""


def _spec() -> dict:
    files = {f"mdp/{k}": v for k, v in MDP.items()}
    files.update({f"pay/{k}": v for k, v in PAY.items()})
    files.update({f"web/{k}": v for k, v in load("location-frontend").items()})
    files["api/package.json"] = '{"name": "api", "dependencies": {"express": "4"}}\n'
    files["api/src/app.js"] = ("const express = require('express');\nconst app = express();\n"
                               "app.get('/health', (req, res) => res.send('ok'));\n")
    stacks = [("java", "mdp"), ("dotnet", "pay"), ("node", "api"), ("express", "api"),
              ("node", "web"), ("react", "web")]
    return {"files": files, "stacks": stacks}


def _run(spec_path: Path, seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed,
           "PYTHONPATH": os.pathsep.join([str(ROOT), os.environ.get("PYTHONPATH", "")])}
    out = subprocess.run([sys.executable, "-c", CHILD, str(spec_path)], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-2000:]
    return out.stdout


def test_extract_and_gaps_identical_across_hash_seeds(tmp_path):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(_spec()))
    a = _run(spec, "1")
    b = _run(spec, "2")
    assert a == b
    doc = json.loads(a)
    kinds = {i["kind"] for i in doc["items"]}
    assert {"inbound_http", "messaging", "frontend_api_call", "data_access"} <= kinds
    extractors = {i["extractor"]["id"] for i in doc["items"]}
    assert {"java.spring", "dotnet.aspnet", "node.backend", "node.frontend"} <= extractors

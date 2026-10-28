"""CLI: python -m repo_docs <command> [--org ORG] [--repo NAME ...] [--force] [--workers N]."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

from . import paths, phase0_discover_clone as p0, phase1_ledger as p1, phase2_extract as p2
from . import aliases as paliases, flows as pflows, phase4_resolve as p4, phase5_generate as p5, phase6_verify as p6
from .config import ConfigError, OrgConfig, load_config
from .github_client import GitHubClient, GitHubError
from .naming import NamingError
from .secrets import SecretFilter, TokenError, load_token, secret_forms
from .selfcheck import scan_for_secret
from .state import StateStore

log = logging.getLogger("repo_docs")

PLANNED = {"llm-scan": "Phase 3", "review": "Phase 7", "ingest": "Phase 8", "eval": "Evaluation"}
EXTRACT_VERSION = "per-repo"  # composite, computed per repo from meta + registry (phase2_extract)
PHASE_ORDER = [("clone", "clone", p0.PHASE_VERSION), ("ledger", "ledger", p1.PHASE_VERSION),
               ("extract", "extract", EXTRACT_VERSION), ("llm_scan", "llm-scan", None),
               ("resolve", "resolve", p4.PHASE_VERSION), ("generate", "generate", p5.PHASE_VERSION),
               ("verify", "verify", p6.PHASE_VERSION), ("review", "review", None), ("ingest", "ingest", None)]
VERSIONS = {"clone": p0.PHASE_VERSION, "ledger": p1.PHASE_VERSION, "extract": p2.PHASE_VERSION,
            "resolve": p4.PHASE_VERSION, "generate": p5.PHASE_VERSION,
            "verify": p6.PHASE_VERSION}


def _setup_logging(cmd: str, orgs: list[str], verbose: bool) -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    for h in list(root.handlers):
        root.removeHandler(h)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    sh.addFilter(SecretFilter())
    root.addHandler(sh)
    if cmd in ("discover", "clone", "ledger", "extract", "resolve", "selfcheck"):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for org in orgs:
            d = paths.logs_dir(org)
            d.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(d / f"{cmd}-{ts}.log", encoding="utf-8")
            fh.setFormatter(fmt)
            fh.addFilter(SecretFilter())
            root.addHandler(fh)


def _token(org: OrgConfig) -> str:
    token = load_token(org.token_env_file, org.token_key)
    SecretFilter.register(token)
    return token


def _check_repos(store: StateStore, org: OrgConfig, repos: list[str] | None) -> None:
    if not repos:
        return
    known = store.repos(org.name)
    unknown = [r for r in repos if r not in known]
    if unknown:
        raise ConfigError(f"repo(s) not registered for {org.name}: {unknown} (run discover?)")


def cmd_status(orgs: list[OrgConfig], store: StateStore, as_json: bool) -> int:
    data = store.get()
    report = {}
    reg_bytes = p2.registry_bytes()
    for org in orgs:
        o = data["orgs"].get(org.name, {})
        repos = o.get("repos", {})
        extract_inputs = {name: p2.status_inputs(org.name, name, reg_bytes) for name in repos}

        def eff(name: str, r: dict, key: str, ver) -> str:
            if ver is EXTRACT_VERSION:
                ev, lga = extract_inputs[name]
                return StateStore.effective_from(r, key, ev, ledger_generated_at=lga)
            return StateStore.effective_from(r, key, ver)

        phases = {}
        for key, _, ver in PHASE_ORDER:
            counts: dict[str, int] = {}
            for name, r in repos.items():
                st = eff(name, r, key, ver)
                counts[st] = counts.get(st, 0) + 1
            phases[key] = counts
        failed = {
            f"{name}:{key}": ((r.get("phases") or {}).get(key) or {}).get("error", "").splitlines()[0][:200]
            if ((r.get("phases") or {}).get(key) or {}).get("error") else ""
            for name, r in sorted(repos.items()) for key, _, ver in PHASE_ORDER
            if eff(name, r, key, ver) == "failed"
        }
        nxt = None
        if not repos:
            nxt = f"discover --org {org.name}"
        else:
            for key, cmd, ver in PHASE_ORDER:
                c = phases[key]
                if any(c.get(s) for s in ("pending", "failed", "stale", "running")):
                    if cmd not in PLANNED:
                        nxt = f"{cmd} --org {org.name}"
                    else:
                        nxt = f"{cmd} --org {org.name}  ({PLANNED[cmd]} planned: implement first, see docs/PIPELINE.md)"
                    break
        report[org.name] = {
            "discovered_at": o.get("discovered_at"), "api_repo_count": o.get("api_repo_count"),
            "repo_count": len(repos), "allowlist_missing": o.get("allowlist_missing", []),
            "service_id_collisions": {n: repos[n].get("service_id")
                                      for n in o.get("service_id_collisions", []) if n in repos},
            "phases": phases, "failed": failed, "next": nxt,
        }
    if as_json:
        print(json.dumps(report, indent=2))
        return 0
    for name, r in report.items():
        print(f"== {name}: {r['repo_count']} repos registered"
              f" (api: {r['api_repo_count']}, discovered_at: {r['discovered_at']})")
        if r["allowlist_missing"]:
            print(f"   allowlist_missing: {r['allowlist_missing']}")
        if r["service_id_collisions"]:
            print(f"   service_id collisions: {r['service_id_collisions']}")
        for key, _, ver in PHASE_ORDER:
            c = r["phases"][key]
            tag = "" if ver else " (planned)"
            print(f"   {key:<9}{tag:<10} " + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))
        for k, err in r["failed"].items():
            print(f"   FAILED {k}: {err}")
        print(f"   next: {r['next'] or 'nothing pending for implemented phases'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m repo_docs",
                                 description="GitHub repos -> standardized service docs pipeline")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status", help="per-org/per-phase progress + next command")
    s.add_argument("--org")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("discover", help="phase 0a: list org repos, register in-scope repos")
    s.add_argument("--org")
    for name, helptxt in (("clone", "phase 0b: shallow clone/refresh + stack detection"),
                          ("ledger", "phase 1: file ledger"),
                          ("extract", "phase 2: deterministic extraction -> inventory.json")):
        s = sub.add_parser(name, help=helptxt)
        s.add_argument("--org")
        s.add_argument("--repo", action="append", help="exact GitHub repo name (repeatable)")
        s.add_argument("--force", action="store_true")
        s.add_argument("--workers", type=int)
    s = sub.add_parser("resolve", help="phase 4: cross-repo resolution -> registry/")
    s.add_argument("--org")
    s = sub.add_parser("flows", help="end-to-end flows -> registry/flows.json + DATA_FLOWS.md")
    s.add_argument("--org")
    s = sub.add_parser("aliases", help="service nicknames -> registry/aliases.yaml (+ manual)")
    s.add_argument("--org")
    for name, helptxt in (("generate", "phase 5: deterministic service.yaml -> output/"),
                          ("verify", "phase 6: coverage gate -> runs/<org>/<repo>/coverage-report.md")):
        s = sub.add_parser(name, help=helptxt)
        s.add_argument("--org")
        s.add_argument("--repo", action="append", help="exact GitHub repo name (repeatable)")
        s.add_argument("--force", action="store_true")
    s = sub.add_parser("selfcheck", help="scan repo_docs + clone .git/config for the token")
    s.add_argument("--org")
    for name, n in PLANNED.items():
        s = sub.add_parser(name, help=f"{n} (planned)")
        s.add_argument("--org")
        s.add_argument("--repo", action="append")
        s.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd in PLANNED:
        print(f"{args.cmd}: planned ({PLANNED[args.cmd]}) — see docs/PIPELINE.md",
              file=sys.stderr)
        return 2

    try:
        cfg = load_config()
        orgs = [cfg.org(args.org)] if args.org else cfg.enabled_orgs()
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    _setup_logging(args.cmd, [o.name for o in orgs], args.verbose)
    store = StateStore()

    if args.cmd == "status":
        return cmd_status(orgs, store, args.json)

    rc = 0
    try:
        for org in orgs:
            if args.cmd == "discover":
                token = _token(org)
                client = GitHubClient(token, org.api_base, org.max_retries)
                res = p0.discover(org, store, client)
                log.info("discover %s: %s", org.name, res)
                print(json.dumps({org.name: res}, indent=2))
                if res["allowlist_missing"]:
                    rc = max(rc, 1)
            elif args.cmd == "clone":
                _check_repos(store, org, args.repo)
                if not store.repos(org.name):
                    raise ConfigError(f"no repos registered for {org.name}; run discover first")
                token = _token(org)
                res = p0.clone_all(org, store, token, args.repo, args.force, args.workers)
                print(json.dumps({org.name: {"counts": res["counts"],
                                             "failed": res["failed"]}}, indent=2))
                if res["failed"]:
                    rc = max(rc, 1)
            elif args.cmd == "ledger":
                _check_repos(store, org, args.repo)
                res = p1.ledger_all(org, store, args.repo, args.force, args.workers)
                print(json.dumps({org.name: {"counts": res["counts"],
                                             "failed": res["failed"]}}, indent=2))
                if res["failed"]:
                    rc = max(rc, 1)
            elif args.cmd == "extract":
                _check_repos(store, org, args.repo)
                res = p2.extract_all(org, store, args.repo, args.force, args.workers)
                print(json.dumps({org.name: {"counts": res["counts"],
                                             "failed": res["failed"]}}, indent=2))
                if res["failed"]:
                    rc = max(rc, 1)
            elif args.cmd == "resolve":
                res = p4.run(org, store)
                log.info("resolve %s: %s", org.name, res)
                print(json.dumps({org.name: res}, indent=2))
                if res["failed"]:
                    rc = max(rc, 1)
            elif args.cmd == "flows":
                res = pflows.run(org)
                log.info("flows %s: %s", org.name, {k: v for k, v in res.items()
                                                    if k != "services_without_flow"})
                print(json.dumps({org.name: res}, indent=2))
            elif args.cmd == "aliases":
                res = paliases.run(org, store)
                log.info("aliases %s: %s", org.name, res)
                print(json.dumps({org.name: res}, indent=2))
            elif args.cmd == "generate":
                _check_repos(store, org, args.repo)
                res = p5.run(org, store, args.repo)
                print(json.dumps({org.name: res}, indent=2))
                if res["failed"]:
                    rc = max(rc, 1)
            elif args.cmd == "verify":
                _check_repos(store, org, args.repo)
                res = p6.run(org, store, args.repo, secret_forms(_token(org)))
                print(json.dumps({org.name: {"pass": len(res["pass"]), "fail": res["fail"]}},
                                 indent=2))
                if res["fail"]:
                    rc = max(rc, 1)
            elif args.cmd == "selfcheck":
                token = _token(org)
                hits = scan_for_secret(token)
                print(f"secret-scan [{org.name}]: {len(hits)} files contain the token")
                for h in hits:
                    print(f"   {h}")
                if hits:
                    rc = 1
    except (ConfigError, NamingError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except (TokenError, GitHubError) as e:
        log.error("%s", e)
        return 1
    return rc

"""Phase 4 — cross-repo resolution (docs/PIPELINE.md#phase-4--cross-repo-resolution).

Reads every ``runs/<org>/<repo>/inventory.json`` (+ ``llm_notes.json`` items) and writes the
deterministic registry files of docs/SCHEMAS.md#registry-files-planned. D2: no APIM/gateway configs;
targets come only from config/env values, infra service/ingress/compose/app-service names and
inbound-route path matching. No timestamps in registry files; everything sorted.
"""
from __future__ import annotations
import fnmatch
import hashlib
import logging
import re
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse

import yaml

from . import paths, pathnorm
from .config import OrgConfig
from .state import StateStore

log = logging.getLogger(__name__)
PHASE_VERSION = "0.1.0"
SKIP_LLM_KINDS = {"purpose", "flow_step"}


def merge_llm_items(items: list[dict], notes: dict) -> list[dict]:
    """Append llm_notes items; a phase-2 item named by an llm item's ``corroborates`` is replaced
    by it (the llm item restates it with the name resolved), so it is not counted twice."""
    extra = [i for i in notes.get("items", []) if i.get("kind") not in SKIP_LLM_KINDS]
    replaced = {i.get("corroborates") for i in extra} - {None}
    return [i for i in items if i["id"] not in replaced] + extra
ENV_TOKENS = ("local", "dev", "develop", "uat", "qa", "prod", "prd", "sit", "stg", "staging", "test",
              "preprod", "perf")
_ENV_ALT = "|".join(ENV_TOKENS)
_ENV_PREFIX = re.compile(rf"^(?:{_ENV_ALT})[._-]", re.I)
_ENV_SUFFIX = re.compile(rf"[._-](?:{_ENV_ALT})$", re.I)
_PLACEHOLDER = re.compile(r"^x{3,}$", re.I)
_IP = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_WRITE_OPS = ("write", "both")


# ---------------------------------------------------------------------------------------------
# normalization helpers (unit-tested)

def norm_path(p: str | None) -> str:
    """Comparison form: lowercase literals, collapse //, strip trailing / + query/fragment, every
    parameter form ({id}, {id:int}, :id, ${x}, [id], <id>, *) -> {}."""
    k = pathnorm.match_key(p or "/")
    segs = []
    for s in k.split("/"):
        if not s:
            continue
        if s in ("*", "**") or re.fullmatch(r"<[^<>/]+>", s):
            s = "{}"
        elif "{}" in s and s.strip("{}"):
            # mixed segment (``catalogs{}`` = literal + interpolated query/suffix): keep the
            # literal stem; anything still holding a hole stays a non-wildcard literal
            s = re.sub(r"(?:\{\})+$", "", s)
        elif "{}" in s:
            s = "{}"
        segs.append(s)
    return "/" + "/".join(segs)


def segs(p: str) -> list[str]:
    return [s for s in p.split("/") if s]


def join_path(prefix: str, path: str) -> str:
    return norm_path((prefix or "").rstrip("/") + "/" + (path or "").lstrip("/"))


def norm_topic(name: str | None) -> str | None:
    """Strip environment prefixes/suffixes (``dev.``, ``uat-``, ``-dev``, ``_uat`` …), lowercase."""
    if not name:
        return None
    n = name.strip().lower()
    prev = None
    while prev != n:
        prev = n
        n = _ENV_PREFIX.sub("", n, count=1) or n
        n = _ENV_SUFFIX.sub("", n, count=1) or n
    return n


def is_placeholder(name: str | None) -> bool:
    return bool(name) and bool(_PLACEHOLDER.match(norm_topic(name) or ""))


def norm_namespace(ns: str | None) -> str | None:
    """Namespace comparison form; placeholders -> unknown; env tokens removed so the same
    namespace family across envs (``…asbdev01`` / ``…asbuat01``) compares equal."""
    if not ns or is_placeholder(ns):
        return None
    n = ns.lower().split(".")[0]
    # env token anchored to a token boundary, or followed by digits (``asbdev01``)
    return re.sub(rf"(?:(?:^|(?<=[._-]))(?:{_ENV_ALT})(?=[._-]|$)|(?:{_ENV_ALT})\d+)", "", n).strip("._-") or n


def suffix_ok(a: list[str], b: list[str], lit: int) -> bool:
    """Suffix-tier evidence bar: >=2 shared literals, or a shared literal last segment with no
    route parameter absorbing a call literal."""
    if lit >= 2:
        return True
    if not a or a[-1] == "{}" or a[-1] != b[-1]:
        return False
    return not any(y == "{}" and x != "{}" for x, y in zip(a, b))


def seg_match(a: list[str], b: list[str], strict_call: bool = False) -> tuple[bool, int]:
    """Segment-wise equality of call ``a`` vs route ``b``; ``{}`` on either side matches any
    segment -> (ok, literal hits). ``strict_call`` (suffix tier): a call parameter may only match a
    route parameter, never a route literal."""
    if len(a) != len(b):
        return False, 0
    lit = 0
    for x, y in zip(a, b):
        if x == "{}" and y != "{}" and strict_call:
            return False, 0
        if x == "{}" or y == "{}":
            continue
        if x != y:
            return False, 0
        lit += 1
    return True, lit


def match_routes(call_paths: list[str], method: str | None, routes: list[dict],
                 allow_suffix: bool = True) -> list[tuple[int, int, dict]]:
    # suffix tier only applies when the base path is unknown (caller passes allow_suffix)
    """All matching routes as (tier, literal_hits, route); tier 2 = full path, 1 = suffix."""
    out: dict[str, tuple[int, int, dict]] = {}
    m = (method or "").upper()
    for cp in call_paths:
        cs = segs(cp)
        for r in routes:
            if m and m not in ("ANY", "*") and r["method"] not in (m, "ANY", "*", None):
                continue
            rs = r["segs"]
            ok, lit = seg_match(cs, rs)
            tier = 2
            if (not ok or lit == 0) and allow_suffix and cs and rs and len(cs) != len(rs):
                n = min(len(cs), len(rs))
                ok, lit = seg_match(cs[-n:], rs[-n:], strict_call=True)
                ok = ok and suffix_ok(cs[-n:], rs[-n:], lit)
                tier = 1
            if not ok or lit == 0:  # at least one shared literal segment, always
                continue
            key = r["sid"] + "|" + r["item_id"]
            cand = (tier, lit, r)
            if key not in out or (cand[0], cand[1]) > (out[key][0], out[key][1]):
                out[key] = cand
    return sorted(out.values(), key=lambda t: (-t[0], -t[1], t[2]["sid"], t[2]["item_id"]))


def pick(matches: list[tuple[int, int, dict]]) -> tuple[str, list]:
    """('edge'|'candidates'|'none', top-tier matches)."""
    if not matches:
        return "none", []
    best = (matches[0][0], matches[0][1])
    top = [m for m in matches if (m[0], m[1]) == best]
    if len({m[2]["sid"] for m in top}) == 1:
        return "edge", top
    return "candidates", top


def _values(v: Any) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v if x]
    return [str(v)] if v else []


def host_and_prefix(value: str) -> tuple[str | None, str | None]:
    base, path, _ = pathnorm.split_url(value)
    if base and "://" in base:
        h = urlparse(base).hostname
        return (h.lower() if h else None), (norm_path(path) if path else "/")
    if value.startswith("/"):
        return None, norm_path(value)
    h = value.split("/", 1)[0].split(":", 1)[0].strip().lower()
    rest = value[len(value.split("/", 1)[0]):]
    return (h or None), norm_path(rest) if rest else "/"


def _domain(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _local_host(h: str) -> bool:
    return h in ("localhost", "0.0.0.0", "127.0.0.1") or bool(_IP.match(h)) or "." not in h


_CONF_RANK = {"low": 0, "medium": 1, "high": 2}


def _src(*items: dict) -> str:
    """Edge source: ``code`` only when every contributing item is code-proven."""
    srcs = {(i.get("source") or "code") for i in items}
    return "code" if srcs == {"code"} else sorted(srcs - {"code"})[0]


def _conf(base: str, *items: dict) -> str:
    """Cap ``base`` by the weakest contributing item's confidence."""
    return min([base] + [i.get("confidence") or "high" for i in items], key=lambda c: _CONF_RANK.get(c, 2))


def edge_id(frm: str, to: str, kind: str, via: str) -> str:
    return hashlib.sha1(f"{frm}|{to}|{kind}|{via}".encode()).hexdigest()


def _ev(repo: str, item: dict, n: int = 3) -> list[dict]:
    return [{"repo": repo, "file": e["file"], "line": e["line"], "snippet": e["snippet"]}
            for e in (item.get("evidence") or [])[:n]]


# ---------------------------------------------------------------------------------------------
# loading

def load_org(org: str) -> tuple[dict[str, dict], dict[str, str]]:
    """{repo: {meta, items}} and {repo: error} for malformed inventories."""
    repos: dict[str, dict] = {}
    failed: dict[str, str] = {}
    base = paths.runs_dir(org)
    if not base.exists():
        return repos, failed
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        inv_p = d / "inventory.json"
        if not inv_p.exists():
            continue
        try:
            meta = paths.read_json(d / "meta.json", {}) or {}
            inv = paths.read_json(inv_p)
            items = list(inv["items"])
            notes = paths.read_json(d / "llm_notes.json")
            if notes:
                items = merge_llm_items(items, notes)
            for i in items:
                i["kind"], i["id"], i["attributes"]  # shape check
        except Exception as e:  # noqa: BLE001 - one bad repo must not stop the org
            failed[d.name] = f"{type(e).__name__}: {e}"
            continue
        sid = inv.get("service_id") or meta.get("service_id") or d.name
        repos[d.name] = {"repo": d.name, "sid": sid, "repo_type": inv.get("repo_type")
                         or meta.get("repo_type") or "unknown", "items": items,
                         "head_sha": inv.get("head_sha")}
    return repos, failed


def _load_externals() -> list[dict]:
    p = paths.external_systems_path()
    if not p.exists():
        return []
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("systems") or []


# ---------------------------------------------------------------------------------------------
# resolution

def build_host_index(repos: dict[str, dict]) -> dict[str, list[dict]]:
    """host -> [{sid, from, env, path_prefix}] from infra items (k8s service/ingress, compose,
    App Service names in pipelines)."""
    idx: dict[str, list[dict]] = defaultdict(list)

    def add(h: str | None, sid: str, frm: str, env: str = "default", prefix: str | None = None):
        if not h or "$(" in h or "{" in h:
            return
        rec = {"sid": sid, "from": frm, "env": env}
        if prefix:
            rec["path_prefix"] = prefix
        if rec not in idx[h.lower()]:
            idx[h.lower()].append(rec)

    for r in repos.values():
        sid = r["sid"]
        for it in r["items"]:
            if it["kind"] != "infra":
                continue
            a = it["attributes"]
            k, name, ns = a.get("infra_kind"), a.get("name"), a.get("namespace")
            if k == "k8s-service" and name:
                add(name, sid, "k8s-service")
                if ns:
                    add(f"{name}.{ns}", sid, "k8s-service")
                    add(f"{name}.{ns}.svc.cluster.local", sid, "k8s-service")
            elif k == "compose-service" and name:
                add(name, sid, "compose-service")
            elif k == "k8s-ingress":
                for h in a.get("hosts") or []:
                    for p in a.get("paths") or [{"path": "/"}]:
                        add(h, sid, "k8s-ingress", prefix=norm_path(p.get("path") or "/"))
            for t in a.get("deploy_targets") or []:
                key, _, val = str(t).partition("=")
                if key.lower() in ("webappname", "appname", "functionappname") and val:
                    add(f"{val}.azurewebsites.net", sid, "app-service")
    return {h: sorted(v, key=lambda x: (x["sid"], x["from"], x.get("path_prefix") or ""))
            for h, v in sorted(idx.items())}


def _host_service(hosts: list[str], prefixes: list[str], hidx: dict) -> str | None:
    """A unique service for the call's hosts (longest ingress path prefix wins); hosts shared by
    several services never decide alone."""
    found: set[str] = set()
    for h in hosts:
        recs = hidx.get(h) or []
        if not recs:
            continue
        sids = {x["sid"] for x in recs}
        if len(sids) == 1:
            found |= sids
            continue
        best, blen = None, -1
        for x in recs:
            pp = x.get("path_prefix")
            if pp and any(p == pp or p.startswith(pp.rstrip("/") + "/") for p in prefixes):
                if len(pp) > blen:
                    best, blen = x["sid"], len(pp)
        if best:
            found.add(best)
    return found.pop() if len(found) == 1 else None


def _routes(repos: dict[str, dict]) -> list[dict]:
    routes = []
    for r in repos.values():
        code_keys = set()
        inb = [i for i in r["items"] if i["kind"] == "inbound_http"]
        for i in inb:
            if i.get("source") != "contract":
                a = i["attributes"]
                code_keys.add(((a.get("method") or "").upper(), norm_path(a.get("path"))))
        for i in inb:
            a = i["attributes"]
            key = ((a.get("method") or "").upper(), norm_path(a.get("path")))
            if i.get("source") == "contract" and key in code_keys:
                continue  # contract-only item with a code twin
            routes.append({"sid": r["sid"], "repo": r["repo"], "item_id": i["id"], "method": key[0],
                           "path": key[1], "segs": segs(key[1]), "item": i})
    return sorted(routes, key=lambda x: (x["sid"], x["item_id"]))


def resolve_org(org: OrgConfig | str, repos: dict[str, dict] | None = None) -> dict[str, Any]:
    org_name = org if isinstance(org, str) else org.name
    patterns = [] if isinstance(org, str) else list(org.internal_package_patterns)
    failed: dict[str, str] = {}
    if repos is None:
        repos, failed = load_org(org_name)
    externals = _load_externals()
    hidx = build_host_index(repos)
    routes = _routes(repos)
    by_sid = {r["sid"]: r for r in repos.values()}
    edges: dict[str, dict] = {}
    candidates, unresolved, ext_cands = [], [], defaultdict(list)
    mismatches = []

    def add_edge(e: dict) -> dict:
        e["id"] = edge_id(e["from"], e["to"], e["kind"], e["via"])
        if e["id"] in edges:
            old = edges[e["id"]]
            fi = sorted(set(old.get("from_items", [old["from_item"]]) + [e["from_item"]]))
            old["from_items"] = fi
            old["from_item"] = fi[0]
            seen = {(x["repo"], x["file"], x["line"]) for x in old["evidence"]}
            old["evidence"] += [x for x in e["evidence"] if (x["repo"], x["file"], x["line"]) not in seen]
            old["evidence"] = sorted(old["evidence"], key=lambda x: (x["repo"], x["file"], x["line"]))[:25]
            if e["confidence"] == "high":
                old["confidence"] = "high"
            return old
        e["from_items"] = [e["from_item"]]
        e["evidence"] = sorted(e["evidence"], key=lambda x: (x["repo"], x["file"], x["line"]))[:25]
        edges[e["id"]] = e
        return e

    # ---- external_system items (phase 2 registry matches) ---------------------------------
    ext_from: set[tuple[str, str]] = set()
    for r in repos.values():
        for it in r["items"]:
            if it["kind"] != "external_system":
                continue
            a = it["attributes"]
            if a.get("from_item"):
                ext_from.add((r["repo"], a["from_item"]))
            mb = a.get("matched_by")
            add_edge({"from": r["sid"], "to": f"external:{a['name']}",
                      "kind": "library_dependency" if mb == "package" else "http",
                      "via": f"{mb}:{a.get('match')}", "from_item": a.get("from_item") or it["id"],
                      "to_item": None, "match": {"host": "host", "package": "artifact"}.get(mb, mb),
                      "caller_type": "service", "criticality": "hard", "source": it.get("source", "code"),
                      "confidence": it.get("confidence", "medium"), "evidence": _ev(r["repo"], it)})

    def ext_by_host(h: str) -> str | None:
        for s in externals:
            if any(fnmatch.fnmatch(h, p.lower()) for p in s.get("hosts") or []):
                return s["name"]
        return None

    # ---- (a)+(b) HTTP ---------------------------------------------------------------------
    pending_unmatched = []
    resolved_hosts: set[str] = set()
    for r in sorted(repos.values(), key=lambda x: x["repo"]):
        for it in r["items"]:
            if it["kind"] not in ("outbound_http", "frontend_api_call"):
                continue
            a = it["attributes"]
            ref = (r["repo"], it["id"])
            method = (a.get("method") or "").upper() or None
            call_path = norm_path(a.get("path_template"))
            hosts, prefixes = [], []
            for v in sorted(a.get("base_url_values") or {}):
                for val in _values(a["base_url_values"][v]):
                    h, p = host_and_prefix(val)
                    if h and h not in hosts:
                        hosts.append(h)
                    if p and p not in prefixes:
                        prefixes.append(p)
            hosts.sort()
            prefixes.sort()
            is_test = r["repo_type"] == "test-suite" or a.get("role") == "tests_target"
            ctype = "test-suite" if is_test else (
                "frontend" if it["kind"] == "frontend_api_call" or r["repo_type"] == "frontend" else "service")
            kind = "tests" if is_test else "http"
            if ref in ext_from:
                continue  # already an external edge
            ext = next((x for x in (ext_by_host(h) for h in hosts) if x), None)
            if ext:
                add_edge({"from": r["sid"], "to": f"external:{ext}", "kind": kind,
                          "via": f"{method or 'ANY'} {call_path}", "from_item": it["id"], "to_item": None,
                          "match": "host", "caller_type": ctype, "criticality": "hard",
                          "source": it.get("source", "code"), "confidence": "high",
                          "evidence": _ev(r["repo"], it)})
                continue
            full = sorted({join_path(p, call_path) for p in prefixes}) or [call_path]
            if call_path not in full:
                full.append(call_path)
            host_sid = _host_service(hosts, prefixes, hidx)
            pool = [x for x in routes if x["sid"] == host_sid] if host_sid else routes
            dynamic = not [s for s in segs(call_path) if s != "{}"]
            # D2: no gateway configs, so a known base-URL path (``/norton/otp/api``) may still be
            # rewritten by an unseen gateway -> treat the effective path as unknown and allow the
            # (evidence-gated, see suffix_ok) suffix tier
            matches = [] if dynamic and not prefixes else match_routes(full, method, pool)
            if dynamic:  # "/" or all-param path: never suffix-guess
                matches = [m for m in matches if m[0] == 2 and m[1] > 0]
            verdict, top = pick(matches)
            via = f"{method or 'ANY'} {call_path}"
            if verdict == "edge":
                tier, lit, rt = top[0]
                conf = "high" if host_sid or (tier == 2 and prefixes) else "medium"
                mlabel = "host+path" if host_sid else ("path-unique" if tier == 2 else "path-suffix")
                e = add_edge({"from": r["sid"], "to": rt["sid"], "kind": kind,
                              "via": f"{rt['method'] or 'ANY'} {rt['item']['attributes'].get('path')}",
                              "from_item": it["id"], "to_item": rt["item_id"], "match": mlabel,
                              "caller_type": ctype, "criticality": "hard",
                              "source": it.get("source", "code"), "confidence": conf,
                              "evidence": _ev(r["repo"], it) + _ev(rt["repo"], rt["item"], 1)})
                if len(top) > 1:
                    e["to_items_alt"] = sorted({m[2]["item_id"] for m in top[1:]})
                resolved_hosts.update(hosts)
                if kind == "http":
                    _contract(e, it, r, rt, by_sid, mismatches)
            elif verdict == "candidates":
                candidates.append({"repo": r["repo"], "item_id": it["id"], "call": via,
                                   "caller_type": ctype,
                                   "candidates": [{"service_id": m[2]["sid"], "item_id": m[2]["item_id"],
                                                   "score": m[0] * 100 + m[1],
                                                   "reason": "full-path" if m[0] == 2 else "suffix"}
                                                  for m in top]})
                resolved_hosts.update(hosts)
            elif host_sid:
                add_edge({"from": r["sid"], "to": host_sid, "kind": kind, "via": via,
                          "from_item": it["id"], "to_item": None, "match": "host", "caller_type": ctype,
                          "criticality": "hard", "source": it.get("source", "code"),
                          "confidence": "medium", "evidence": _ev(r["repo"], it)})
                resolved_hosts.update(hosts)
            else:
                pending_unmatched.append((r, it, hosts, via, dynamic, ctype))

    internal_domains = {_domain(h) for h in resolved_hosts | set(hidx) if not _local_host(h)}
    for r, it, hosts, via, dynamic, ctype in pending_unmatched:
        a = it["attributes"]
        third = [h for h in hosts if not _local_host(h) and _domain(h) not in internal_domains]
        if third and ctype != "test-suite" and len(third) == len(hosts):
            for h in third:
                ext_cands[("host", h)].append({"repo": r["repo"], "item_id": it["id"]})
            continue
        if (a.get("base_url_source") or "unknown") == "unknown":
            reason = "no_base_url"
        elif dynamic:
            reason = "dynamic_url"
        elif hosts and not any(h in hidx for h in hosts) and not any(
                _domain(h) in internal_domains for h in hosts if not _local_host(h)) and third:
            reason = "unknown_host"
        else:
            reason = "no_route_match"
        unresolved.append({"repo": r["repo"], "item_id": it["id"], "kind": it["kind"],
                           "target": f"{a.get('base_url_source')} {via}", "hosts": hosts,
                           "caller_type": ctype, "reason": reason})

    # ---- (c) messaging --------------------------------------------------------------------
    messaging = _messaging(repos, add_edge, unresolved)

    # ---- (d) shared DB + owns_schema ------------------------------------------------------
    stores = _shared_db(repos, add_edge)

    # ---- (e) libraries --------------------------------------------------------------------
    drift = _libraries(repos, patterns, externals, add_edge, unresolved, ext_cands, candidates)

    # ---- (f) back-fill + services ---------------------------------------------------------
    services = _services(org_name, repos, hidx, edges, messaging, stores)

    edge_list = sorted(edges.values(), key=lambda e: (e["kind"], e["from"], e["to"], e["via"], e["id"]))
    for e in edge_list:
        e["from_items"] = sorted(set(e["from_items"]))
    out = {
        "services": {"schema_version": 1, "org": org_name, "services": services,
                     "host_index": hidx, "data_stores": stores},
        "edges": {"schema_version": 1, "edges": edge_list, "library_drift": drift},
        "candidates": {"schema_version": 1, "items": sorted(candidates, key=lambda x: (x["repo"], x["item_id"]))},
        "unresolved": {"schema_version": 1, "items": sorted(unresolved, key=lambda x: (x["repo"], x["item_id"]))},
        "messaging": {"schema_version": 1, "entities": messaging},
        "contract_mismatches": {"schema_version": 1,
                                "items": sorted(mismatches, key=lambda x: (x["edge_id"], x["direction"],
                                                                           x["caller_schema"] or ""))},
        "external_candidates": {"schema_version": 1, "items": [
            {"kind": k, "value": v, "used_by": sorted(u, key=lambda x: (x["repo"], x["item_id"]))}
            for (k, v), u in sorted(ext_cands.items())]},
        "failed": failed,
    }
    return out


def _schema(repo: dict, name: str | None) -> dict | None:
    if isinstance(name, list):
        name = name[0] if len(name) == 1 else None
    if not name or not isinstance(name, str):
        return None
    base = re.sub(r"^(List|Array|Set|IEnumerable|Page|Optional|Mono|Flux|Promise)<(.+)>$", r"\2", name)
    base = base.rstrip("[]")
    for it in repo["items"]:
        if it["kind"] == "schema" and it["attributes"].get("name") in (name, base):
            return it
    return None


def _contract(edge: dict, call: dict, caller: dict, rt: dict, by_sid: dict, out: list) -> None:
    """(g) field-by-field DTO diff, only when both sides' schemas are known."""
    callee = by_sid.get(rt["sid"])
    if not callee:
        return
    ca, ra = call["attributes"], rt["item"]["attributes"]
    resp = next((x.get("schema") for x in ra.get("responses") or []
                 if x.get("schema") and str(x.get("status", "")).startswith("2")), None)
    for direction, cs, ss in (("request", ca.get("request"), ra.get("request")),
                              ("response", ca.get("response"), resp)):
        c, s = _schema(caller, cs), _schema(callee, ss)
        if not c or not s:
            continue
        cf = {(f.get("json_name") or f["name"]): f for f in c["attributes"].get("fields") or []}
        sf = {(f.get("json_name") or f["name"]): f for f in s["attributes"].get("fields") or []}
        diffs = []
        lc = {k.lower(): k for k in sf}
        for k in sorted(cf):
            if k in sf:
                continue
            if k.lower() in lc:
                diffs.append({"field": k, "issue": "name_case", "caller": k, "callee": lc[k.lower()],
                              "severity": "info"})
            else:
                diffs.append({"field": k, "issue": "extra", "caller": k, "callee": None,
                              "severity": "info" if direction == "request" else "warn"})
        if direction == "request":
            clc = {k.lower() for k in cf}
            for k in sorted(sf):
                if sf[k].get("required") and k not in cf and k.lower() not in clc:
                    diffs.append({"field": k, "issue": "missing_required", "caller": None, "callee": k,
                                  "severity": "error"})
        if diffs:
            out.append({"edge_id": edge["id"], "direction": direction,
                        "caller_schema": c["attributes"].get("name"),
                        "callee_schema": s["attributes"].get("name"), "diffs": diffs})


def _msg_names(a: dict) -> list[str]:
    names = []
    for v in [a.get("entity")] + [x for k in sorted(a.get("resolved_values") or {})
                                  for x in _values(a["resolved_values"][k])]:
        if v and v not in names:
            names.append(v)
    return names


def _family(a: dict) -> str:
    t = a.get("entity_type") or "topic"
    return {"subscription": "topic"}.get(t, t)


def _messaging(repos: dict, add_edge, unresolved: list) -> list[dict]:
    ents: dict[tuple, dict] = {}
    for r in sorted(repos.values(), key=lambda x: x["repo"]):
        for it in r["items"]:
            if it["kind"] != "messaging":
                continue
            a = it["attributes"]
            raw = _msg_names(a)
            if a.get("role") == "script":
                unresolved.append({"repo": r["repo"], "item_id": it["id"], "kind": "messaging",
                                   "target": ",".join(raw) or None, "reason": "script_only"})
                continue
            normed = sorted({norm_topic(n) for n in raw if n})
            if not normed:
                unresolved.append({"repo": r["repo"], "item_id": it["id"], "kind": "messaging",
                                   "target": a.get("name_from"), "reason": "unknown_entity"})
                continue
            if all(is_placeholder(n) for n in normed):
                unresolved.append({"repo": r["repo"], "item_id": it["id"], "kind": "messaging",
                                   "target": ",".join(raw), "reason": "placeholder_name"})
                continue
            for n in normed:
                if is_placeholder(n):
                    continue
                key = (a.get("broker") or "_", _family(a), n)
                e = ents.setdefault(key, {"publishers": [], "subscribers": []})
                rec = {"service_id": r["sid"], "repo": r["repo"], "item_id": it["id"],
                       "raw_names": raw, "namespace": a.get("namespace"),
                       "message_types": sorted(a.get("message_types") or []), "item": it}
                if a.get("direction") == "publish":
                    e["publishers"].append(rec)
                else:
                    sub = a.get("subscription")
                    rec.update({"subscription": sub if not isinstance(sub, list) else sorted(sub),
                                "filter": a.get("filter")})
                    e["subscribers"].append(rec)
    out = []
    for (broker, fam, name), e in sorted(ents.items()):
        flags = []
        nss = {norm_namespace(x["namespace"]) for x in e["publishers"] + e["subscribers"]}
        if None in nss:
            flags.append("namespace_unknown")
        if not e["subscribers"]:
            flags.append("no_subscribers")
        if not e["publishers"]:
            flags.append("no_publishers")
        ptypes = {t for p in e["publishers"] for t in p["message_types"]}
        links = []
        for p in e["publishers"]:
            for s in e["subscribers"]:
                pn, sn = norm_namespace(p["namespace"]), norm_namespace(s["namespace"])
                if pn and sn and pn != sn:
                    continue
                if s["message_types"] and ptypes and not set(s["message_types"]) & ptypes:
                    if "message_type_unmatched" not in flags:
                        flags.append("message_type_unmatched")
                both = bool(pn and sn)
                ed = add_edge({"from": p["service_id"], "to": s["service_id"], "kind": "event",
                               "via": f"{broker}:{fam}:{name}", "from_item": p["item_id"],
                               "to_item": s["item_id"], "match": "entity+namespace" if both else "entity",
                               "caller_type": "service", "criticality": "async",
                               "source": _src(p["item"], s["item"]),
                               "confidence": _conf("high" if both else "medium", p["item"], s["item"]),
                               "evidence": _ev(p["repo"], p["item"], 2) + _ev(s["repo"], s["item"], 2)})
                links.append(ed["id"])
        if e["publishers"] and e["subscribers"] and not links:
            flags.append("namespace_mismatch")
        strip = lambda xs: [{k: v for k, v in x.items() if k != "item"} for x in  # noqa: E731
                            sorted(xs, key=lambda x: (x["service_id"], x["item_id"]))]
        out.append({"key": f"{broker}:{fam}:{name}", "broker": broker, "entity_type": fam, "name": name,
                    "raw_names": sorted({n for x in e["publishers"] + e["subscribers"] for n in x["raw_names"]}),
                    "publishers": strip(e["publishers"]), "subscribers": strip(e["subscribers"]),
                    "edges": sorted(set(links)), "flags": sorted(flags)})
    return out


def _shared_db(repos: dict, add_edge) -> dict:
    stores: dict[str, dict] = {}
    for r in sorted(repos.values(), key=lambda x: x["repo"]):
        for it in r["items"]:
            if it["kind"] != "data_access":
                continue
            a = it["attributes"]
            skey = f"{a.get('store_type') or 'other'}:{(a.get('host') or '_').lower()}:{(a.get('database') or '_').lower()}"
            s = stores.setdefault(skey, {"tables": {}, "services": []})
            if r["sid"] not in s["services"]:
                s["services"].append(r["sid"])
            for ent in a.get("entities") or []:
                tname = (ent.get("table") or ent.get("name") or "").lower()
                if not tname:
                    continue
                t = s["tables"].setdefault(tname, {"writers": {}, "readers": {}})
                op = ent.get("operation") or a.get("operation")
                (t["writers"] if op in _WRITE_OPS else t["readers"]).setdefault(r["sid"], (r["repo"], it))
            if a.get("owns_schema") or r["repo_type"] == "db-migration":
                for td in a.get("tables_ddl") or []:
                    tn = ".".join(x for x in (td.get("schema"), td.get("name")) if x).lower()
                    add_edge({"from": r["sid"], "to": f"table:{tn}", "kind": "owns_schema", "via": tn,
                              "from_item": it["id"], "to_item": None, "match": "table",
                              "caller_type": "service", "criticality": "hard", "source": _src(it),
                              "confidence": _conf("high", it), "evidence": _ev(r["repo"], it, 1)})
    out = {}
    for skey in sorted(stores):
        s = stores[skey]
        tables = {}
        for tn in sorted(s["tables"]):
            t = s["tables"][tn]
            ws = sorted(t["writers"])
            tables[tn] = {"writers": ws, "readers": sorted(set(t["readers"]) - set(ws))}
            if len(ws) >= 2:
                for i, a in enumerate(ws):
                    for b in ws[i + 1:]:
                        (ra, ia), (rb, ib) = t["writers"][a], t["writers"][b]
                        add_edge({"from": a, "to": b, "kind": "shared_db", "via": f"{skey}/{tn}",
                                  "from_item": ia["id"], "to_item": ib["id"], "match": "table",
                                  "caller_type": "service", "criticality": "hard",
                                  "source": _src(ia, ib),
                                  "confidence": _conf("high" if not skey.endswith(":_:_") else "medium",
                                                      ia, ib),
                                  "evidence": _ev(ra, ia, 1) + _ev(rb, ib, 1),
                                  "readers": tables[tn]["readers"]})
        out[skey] = {"services": sorted(s["services"]), "tables": tables}
    return out


def _libraries(repos: dict, patterns: list[str], externals: list[dict], add_edge, unresolved: list,
               ext_cands: dict, candidates: list | None = None) -> dict:
    arts: dict[tuple[str, str], str] = {}
    publishers: dict[tuple[str, str], list[str]] = defaultdict(list)
    own: dict[str, set[str]] = defaultdict(set)
    for r in sorted(repos.values(), key=lambda x: x["repo"]):
        for it in r["items"]:
            if it["kind"] == "artifact":
                a = it["attributes"]
                arts.setdefault((a.get("ecosystem"), a.get("name")), r["repo"])
                publishers[(a.get("ecosystem"), a.get("name"))].append(r["repo"])
                own[r["repo"]] |= {str(a.get("name")).lower(), str(a.get("name")).split(":")[-1].lower()}
    for (eco, n), rps in sorted(publishers.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        libs = sorted({rp for rp in rps if repos[rp]["repo_type"] == "library"})
        if len(set(rps)) > 1:
            if len(libs) == 1:
                arts[(eco, n)] = libs[0]  # the single library repo is the publisher of record
            else:
                arts.pop((eco, n), None)  # ambiguous publisher: no edge, report instead
            if candidates is not None:
                candidates.append({"repo": sorted(set(rps))[0], "item_id": f"artifact:{eco}:{n}",
                                   "kind": "artifact_collision", "artifact": f"{eco}:{n}",
                                   "candidates": [{"service_id": repos[rp]["sid"], "repo": rp}
                                                  for rp in sorted(set(rps))]})
    used: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for r in sorted(repos.values(), key=lambda x: x["repo"]):
        for it in r["items"]:
            if it["kind"] != "dependency":
                continue
            a = it["attributes"]
            name = a.get("name") or ""
            target = arts.get((a.get("ecosystem"), name))
            if not target and patterns and any(fnmatch.fnmatch(name, p) for p in patterns):
                libs = sorted({rp for (eco, n), rp in arts.items() if repos[rp]["repo_type"] == "library"
                               and n.split(":")[-1] == name.split(":")[-1]})
                target = libs[0] if len(libs) == 1 else None
            if target and target != r["repo"]:
                tsid = repos[target]["sid"]
                add_edge({"from": r["sid"], "to": tsid, "kind": "library_dependency", "via": name,
                          "from_item": it["id"], "to_item": None, "match": "artifact",
                          "caller_type": "service", "criticality": "hard", "source": _src(it),
                          "confidence": _conf("high", it), "evidence": _ev(r["repo"], it, 1),
                          "version": a.get("version")})
                used[name][str(a.get("version"))].append(r["sid"])
                continue
            if not a.get("internal") or target == r["repo"]:
                continue
            if (a.get("internal_repo") == r["repo"] or a.get("kind") in ("module", "project-reference")
                    or name.lower() in own[r["repo"]] or name.split(":")[-1].lower() in own[r["repo"]]):
                continue  # intra-repo module
            unresolved.append({"repo": r["repo"], "item_id": it["id"], "kind": "dependency",
                               "target": name, "reason": "no_artifact_match"})
    return {n: {v: sorted(set(s)) for v, s in sorted(vs.items())}
            for n, vs in sorted(used.items()) if len(vs) > 1}


def _services(org: str, repos: dict, hidx: dict, edges: dict, messaging: list, stores: dict) -> dict:
    hosts_by: dict[str, list] = defaultdict(list)
    for h, recs in hidx.items():
        for x in recs:
            hosts_by[x["sid"]].append({"host": h, **{k: v for k, v in x.items() if k != "sid"}})
    callers: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    points_to: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    item_by = {(r["sid"], i["id"]): i for r in repos.values() for i in r["items"]}
    for e in edges.values():
        if e["kind"] in ("http", "tests") and e.get("to_item"):
            callers[e["to"]][e["to_item"]].append({"service_id": e["from"], "caller_type": e["caller_type"],
                                                   "edge_id": e["id"], "kind": e["kind"]})
        if e["kind"] in ("http", "tests") and not e["to"].startswith(("external:", "table:")):
            for fi in e["from_items"]:
                it = item_by.get((e["from"], fi))
                src = (it or {}).get("attributes", {}).get("base_url_source") or ""
                if src.startswith(("config:", "env:")):
                    k = src.split(":", 1)[1]
                    if e["to"] not in points_to[e["from"]][k]:
                        points_to[e["from"]][k].append(e["to"])
    consumers: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    producers: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for ent in messaging:
        for p in ent["publishers"]:
            for s in ent["subscribers"]:
                if edge_id(p["service_id"], s["service_id"], "event", ent["key"]) not in ent["edges"]:
                    continue
                c = consumers[p["service_id"]][p["item_id"]]
                if s["service_id"] not in c:
                    c.append(s["service_id"])
                pr = producers[s["service_id"]][s["item_id"]]
                if p["service_id"] not in pr:
                    pr.append(p["service_id"])
    out = {}
    cps_owner = next((r["sid"] for r in repos.values() if r["repo_type"] == "db-migration"
                      and r["repo"].upper().startswith("TVS-CPS")), None)
    owned_tables = {e["via"].split(".")[-1] for e in edges.values()
                    if e["kind"] == "owns_schema" and e["from"] == cps_owner}
    for r in sorted(repos.values(), key=lambda x: x["sid"]):
        sid, its = r["sid"], r["items"]
        a_of = lambda k: [i["attributes"] for i in its if i["kind"] == k]  # noqa: E731
        base_urls = sorted({v for i in its if i["kind"] == "infra"
                            for v in (i["attributes"].get("hosts") or [])})
        ownership = []
        if cps_owner and sid != cps_owner and r["repo"].upper().startswith("TVS-CPS"):
            for a in a_of("data_access"):
                for ent in a.get("entities") or []:
                    t = (ent.get("table") or "").lower()
                    if t and t in owned_tables:
                        ownership.append({"table": t, "owned": False, "owner_service": cps_owner})
        out[sid] = {
            "repo": r["repo"], "repo_type": r["repo_type"], "aliases": sorted({r["repo"]} - {sid}),
            "hosts": hosts_by.get(sid, []), "base_urls": base_urls,
            "config_keys": sorted({a.get("canonical") or a.get("name") for a in a_of("config_key")}),
            "inbound_routes": len(a_of("inbound_http")),
            "topics_published": sorted({e["name"] for e in messaging for p in e["publishers"]
                                        if p["service_id"] == sid}),
            "topics_consumed": sorted({e["name"] for e in messaging for p in e["subscribers"]
                                       if p["service_id"] == sid}),
            "data_stores": sorted(k for k, v in stores.items() if sid in v["services"]),
            "artifacts": sorted({a.get("name") for a in a_of("artifact") if a.get("name")}),
            "inbound_callers": {k: sorted(v, key=lambda x: (x["service_id"], x["edge_id"]))
                                for k, v in sorted(callers.get(sid, {}).items())},
            "event_consumers": {k: sorted(v) for k, v in sorted(consumers.get(sid, {}).items())},
            "event_producers": {k: sorted(v) for k, v in sorted(producers.get(sid, {}).items())},
            "config_points_to": {k: sorted(v) for k, v in sorted(points_to.get(sid, {}).items())},
            "table_ownership": sorted(ownership, key=lambda x: x["table"]),
        }
    return out


# ---------------------------------------------------------------------------------------------

FILES = {"edges": "edges.json", "candidates": "candidates.json", "unresolved": "unresolved.json",
         "messaging": "messaging.json", "contract_mismatches": "contract_mismatches.json",
         "external_candidates": "external_candidates.json"}


def inputs_sha(org: str) -> str:
    h = hashlib.sha1()
    base = paths.runs_dir(org)
    for p in sorted(base.glob("*/inventory.json")) + sorted(base.glob("*/llm_notes.json")):
        h.update(str(p.relative_to(base)).encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def run(org: OrgConfig, store: StateStore) -> dict[str, Any]:
    res = resolve_org(org)
    reg = paths.registry_dir()
    paths.atomic_write_json(reg / org.name / "services.json", res["services"], sort_keys=True)
    for k, f in FILES.items():
        paths.atomic_write_json(reg / f, res[k], sort_keys=True)
    sha = inputs_sha(org.name)
    now = paths.utcnow()
    for repo, info in sorted(store.repos(org.name).items()):
        if repo in res["failed"]:
            store.set_phase(org.name, repo, "resolve", status="failed", error=res["failed"][repo],
                            version=PHASE_VERSION, finished_at=now)
        elif (paths.runs_dir(org.name, repo) / "inventory.json").exists():
            store.set_phase(org.name, repo, "resolve", status="done", version=PHASE_VERSION,
                            input_sha=info.get("head_sha"), inventories_sha=sha, finished_at=now,
                            error=None)
    counts: dict[str, int] = defaultdict(int)
    for e in res["edges"]["edges"]:
        counts[e["kind"]] += 1
    return {"edges": dict(sorted(counts.items())), "candidates": len(res["candidates"]["items"]),
            "unresolved": len(res["unresolved"]["items"]),
            "external_candidates": len(res["external_candidates"]["items"]),
            "messaging_entities": len(res["messaging"]["entities"]),
            "contract_mismatches": len(res["contract_mismatches"]["items"]), "failed": res["failed"]}

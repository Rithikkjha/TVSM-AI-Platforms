"""repo_type classification (docs/EXTRACTORS.md#repo_type-classification).

Ordered rules 1-9, first match wins; every fired rule is recorded with evidence. Applied to the
whole repo and to every subproject. No name-based special cases except the documented
``bff`` / ``portal`` template_type suffixes.
"""
from __future__ import annotations

import posixpath
import re

from .extractors.base import RepoContext
from .extractors.shared_sql import FLYWAY

TEST_DEPS = ("testng", "rest-assured", "karate", "cucumber", "selenium", "playwright", "cypress")
UI_STACKS = {"react", "nextjs", "angular", "vue"}
MOBILE_STACKS = {"android", "ios", "react-native", "dart", "flutter"}
FUNCTION_DEPS = ("microsoft.azure.functions.worker", "microsoft.net.sdk.functions",
                 "microsoft.azure.webjobs", "@azure/functions")
_START_SCRIPT = re.compile(r'^\s*"start"\s*:')
_ENTRY = [
    ("java", re.compile(r"@SpringBootApplication\b|\bSpringApplication\.run\s*\(")),
    ("csharp", re.compile(r"\bWebApplication\.Create(Builder|SlimBuilder)?\s*\(|"
                          r"\bHost\.Create(DefaultBuilder|ApplicationBuilder)\s*\(|"
                          r"\bCreateHostBuilder\s*\(|\.UseStartup<")),
    ("typescript", re.compile(r"\bNestFactory\.create\s*\(|\b(app|server)\.listen\s*\(")),
    ("javascript", re.compile(r"\bNestFactory\.create\s*\(|\b(app|server)\.listen\s*\(")),
]
_FUNCTION_ATTR = re.compile(r"\[(Function|FunctionName)\s*\(")
TEMPLATE_TYPE = {"service": "backend-api", "frontend": "frontend-web", "function-app": "function",
                 "scheduler": "worker", "library": "library", "mobile": "mobile-app",
                 "test-suite": None, "db-migration": None, "unknown": None}


def _is_migration(path: str) -> bool:
    name = posixpath.basename(path)
    low = path.lower()
    return name.lower().endswith(".sql") and (
        bool(FLYWAY.match(name)) or "/migration" in "/" + low or "migrations/" in low
        or "changelog" in low or "/ddl/" in "/" + low)


def _entrypoints(ctx: RepoContext, files: list[dict]) -> list:
    """Runnable-app signals: Spring Boot main, ASP.NET/Generic host builders, NestFactory /
    ``app.listen``, a package.json ``start`` script. Maven archetype templates are not app code."""
    hits = []
    for e in files:
        if "archetype-resources/" in e["path"]:
            continue
        if posixpath.basename(e["path"]) == "package.json":
            for i, ln in enumerate(ctx.lines(e["path"]), 1):
                if _START_SCRIPT.match(ln):
                    hits.append(ctx.evidence(e["path"], i))
                    break
            continue
        if e.get("class") != "source":
            continue
        for lang, rx in _ENTRY:
            if e.get("language") != lang:
                continue
            for i, ln in enumerate(ctx.lines(e["path"]), 1):
                if rx.search(ln):
                    hits.append(ctx.evidence(e["path"], i))
                    break
        if len(hits) >= 5:
            break
    return hits


def _first_line(ctx: RepoContext, path: str, rx: re.Pattern | None = None):
    if rx is not None:
        for i, ln in enumerate(ctx.lines(path), 1):
            if rx.search(ln):
                return ctx.evidence(path, i)
    return ctx.evidence(path, 1)


def _classify(ctx: RepoContext, files: list[dict], items: list, stacks: set[str]
              ) -> tuple[str, list[str], list]:
    by_kind: dict[str, list] = {}
    for it in items:
        by_kind.setdefault(it.kind, []).append(it)
    inbound = by_kind.get("inbound_http", [])
    subscribes = [m for m in by_kind.get("messaging", [])
                  if m.attributes.get("direction") == "subscribe"]
    source = [e for e in files if e.get("class") == "source"]
    entry = _entrypoints(ctx, files)
    ui_app = bool(stacks & UI_STACKS)
    hosts = [e["path"] for e in files if posixpath.basename(e["path"]) == "host.json"]
    fdeps = [d for d in by_kind.get("dependency", [])
             if str(d.attributes.get("name")).lower().startswith(FUNCTION_DEPS)]
    func_host = bool(hosts) and (bool(fdeps) or any(
        e.get("language") == "csharp" and _FUNCTION_ATTR.search(ctx.read_text(e["path"]) or "")
        for e in source))
    if func_host:  # a Functions host is a runnable app
        entry = entry + [_first_line(ctx, hosts[0])]
    # 1 db-migration
    migs = [e["path"] for e in source if _is_migration(e["path"])]
    if migs and len(migs) * 2 >= len(source) and not inbound:
        return "db-migration", [f"sql_migrations={len(migs)}/{len(source)} source files",
                                "inbound_http=0"], [_first_line(ctx, p) for p in migs[:3]]
    # 2 test-suite
    test_deps = [d for d in by_kind.get("dependency", [])
                 if any(t in str(d.attributes.get("name")).lower() for t in TEST_DEPS)]
    tests = [e for e in files if e.get("class") == "test"]
    if test_deps and not entry and not ui_app:
        return "test-suite", ["test-framework dependency", "no app entrypoint"], \
            [d.evidence[0] for d in test_deps[:3]]
    if files and len(tests) * 2 >= len(files) and not entry and not ui_app:
        return "test-suite", [f"test files={len(tests)}/{len(files)}"], \
            [_first_line(ctx, e["path"]) for e in tests[:3]]
    # 3 library
    boot = ctx.hints.get("boot_repackage", set())
    arts = [a for a in by_kind.get("artifact", [])
            if not (a.attributes.get("ecosystem") == "maven"
                    and (a.attributes.get("packaging") == "pom" or a.evidence[0].file in boot))]
    if arts and not entry and not ui_app:
        return "library", ["publishes artifact", "no app entrypoint"], \
            [a.evidence[0] for a in arts[:3]]
    # 4 function-app
    if func_host:
        ev = [_first_line(ctx, hosts[0])] + [d.evidence[0] for d in fdeps[:2]]
        return "function-app", ["host.json", "functions worker"], ev
    # 5 mobile
    if stacks & MOBILE_STACKS:
        return "mobile", [f"stack={sorted(stacks & MOBILE_STACKS)[0]}"], []
    # 6 frontend
    backend_inbound = [i for i in inbound if i.source == "code"
                       and i.attributes.get("framework") != "next-api"]
    if ui_app and not backend_inbound:
        return "frontend", [f"stack={sorted(stacks & UI_STACKS)[0]}", "no backend inbound_http"], []
    # 7 scheduler
    jobs = by_kind.get("scheduled_job", [])
    if jobs and not inbound and not subscribes:
        return "scheduler", ["scheduled_job>0", "no inbound_http/subscribe"], \
            [j.evidence[0] for j in jobs[:3]]
    # 8 service
    if inbound or subscribes:
        rules = (["inbound_http>0"] if inbound else []) + (["subscribe>0"] if subscribes else [])
        return "service", rules, [i.evidence[0] for i in (inbound + subscribes)[:3]]
    return "unknown", [], []


def template_type(value: str, repo: str) -> str | None:
    low = repo.lower()
    if value == "service" and ("bff" in low or "backend-for-frontend" in low):
        return "bff"
    if value == "frontend" and "portal" in low:
        return "portal"
    return TEMPLATE_TYPE.get(value)


def classify_repo(ctx: RepoContext, items: list) -> dict:
    """``meta.repo_type`` block."""
    stacks_all = {s["stack"] for s in ctx.meta.get("stacks") or []}
    value, rules, ev = _classify(ctx, ctx.files(), items, stacks_all)
    subs = {}
    for sub in ctx.subprojects:
        sstacks = {s["stack"] for s in ctx.meta.get("stacks") or []
                   if (s.get("subproject") or ".") == sub}
        sv, _, _ = _classify(ctx, ctx.files(sub), [i for i in items if i.subproject == sub],
                             sstacks)
        subs[sub] = sv
    ev = sorted(set(ev), key=lambda e: (e.file, e.line))[:5]
    return {"value": value, "template_type": template_type(value, ctx.repo),
            "rules_fired": rules, "evidence": [e.to_dict() for e in ev], "subprojects": subs}

"""node.frontend: React / Next.js / Angular / plain-JS portals (FEAT-004, docs/EXTRACTORS.md).

- ``frontend_api_call`` for every resolved HTTP call (axios/fetch/axios instances/Angular
  ``HttpClient``/one-level wrappers, shared with node.backend through ``node_common``) with
  ``ui_framework``, ``runtime`` (``server`` for Next route handlers, ``pages/api``, server
  components/pages without ``'use client'``, ``getServerSideProps`` files, build scripts) and
  ``base_url_kind`` (``dotenv`` for ``process.env``/``import.meta.env`` vars incl. NEXT_PUBLIC_/
  REACT_APP_/VITE_, ``environment-ts``/``config-js``/``runtime-config-json`` for config-file keys,
  ``next-config`` for vars only defined in ``next.config.*``).
- Next.js API routes (``app/**/route.(ts|js)`` exported verbs, ``pages/api/**``) -> ``inbound_http``
  ``framework: next-api`` with ``basePath`` from ``next.config.*``.
- TS request/response types -> ``schema``; ``process.env`` reads -> ``config_key`` (names only).
"""
from __future__ import annotations

import posixpath
import re

from .. import pathnorm
from ..inventory_schema import make_item
from . import node_common as nc
from . import syntax
from .base import ExtractResult, Extractor, RepoContext

VERBS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
_SERVER_PATH = re.compile(r"(^|/)(pages/api/|src/server/|server/|scripts/)|(^|/)middleware\.[cm]?[jt]s$"
                          r"|(^|/)[^/]*\.config\.[cm]?[jt]s$|(^|/)next\.config\.")
_APP_FILE = re.compile(r"(^|/)app/(.*/)?(page|layout|route|template|default|loading|not-found)"
                       r"\.[cm]?[jt]sx?$")
_NEXT_CONFIG = re.compile(r"(^|/)next\.config\.[cm]?[jt]s$")


def _ui_framework(stacks: set[str]) -> str:
    for s in ("nextjs", "angular", "react"):
        if s in stacks:
            return s
    return "plain-js"


class NodeFrontendExtractor(Extractor):
    id = "node.frontend"
    stacks = ("react", "nextjs", "angular")
    extractor_version = nc.VERSION

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        proj = nc.project(ctx)
        paths = proj.paths_in(subproject)
        if not paths:
            return res
        stacks = {s["stack"] for s in ctx.meta.get("stacks") or []
                  if (s.get("subproject") or ".") == (subproject or ".")}
        ui = _ui_framework(stacks)
        unresolved: set[str] = set()
        types: list[str] = []
        http = ctx.symbols.get("node.http")
        if http is None:
            http = ctx.symbols["node.http"] = nc.HttpModel(proj)
            http.build(proj.paths_in(None))
        calls, unr = http.calls(paths)
        unresolved |= unr
        for c in calls:
            extra = {"ui_framework": ui, "runtime": self._runtime(ctx, c.mod.path, ui),
                     "base_url_kind": self._base_kind(ctx, c.url, subproject)}
            it = nc.call_item(ctx, self, c, "frontend_api_call", extra)
            if it is None:
                unresolved.add(c.mod.path)
                continue
            res.items.append(it)
            types += nc.type_names(c.response) + nc.type_names(c.request)
        next_cfg = [p for p in paths if _NEXT_CONFIG.search(p)]
        if "nextjs" in stacks or next_cfg:
            res.items += self._next_routes(ctx, proj, paths, subproject, next_cfg, unresolved,
                                           types)
        res.items += nc.config_reads(ctx, proj, paths, self)
        if types:
            res.items += nc.schema_items(ctx, proj, sorted(set(types)), subproject or ".", self)
        tsconf = [p for p in proj.tsconfig_paths() if ctx.subproject_of(p) == (subproject or ".")]
        nc.note_sdk_symbols(ctx, proj, paths)
        nc.touch_files(ctx, res, proj, paths, unresolved, extra=tsconf)
        return res

    # ---- attributes ----------------------------------------------------------------------
    @staticmethod
    def _runtime(ctx, path: str, ui: str) -> str:
        if _SERVER_PATH.search(path):
            return "server"
        if ui != "nextjs":
            return "browser"
        text = ctx.read_text(path) or ""
        head = text.lstrip()[:40]
        if re.match(r"""['"]use client['"]""", head):
            return "browser"
        if re.match(r"""['"]use server['"]""", head) or "getServerSideProps" in text or \
                "getStaticProps" in text:
            return "server"
        if _APP_FILE.search(path):
            return "server"
        return "browser"

    @staticmethod
    def _base_kind(ctx, url: nc.SV, subproject) -> str | None:
        p0 = url.parts[0] if url.parts else None
        if isinstance(p0, nc.Env):
            defs = ctx.config.env_defs(p0.name, subproject) or ctx.config.defs(p0.name, subproject)
            files = [d.file for d in defs]
            if files and all(_NEXT_CONFIG.search(f) for f in files):
                return "next-config"
            return "dotenv"
        if isinstance(p0, nc.Cfg):
            files = [d.file for d in ctx.config.defs(p0.key, subproject)]
            for f in files:
                b = posixpath.basename(f)
                if b.startswith("environment"):
                    return "environment-ts"
                if b == "config.js":
                    return "config-js"
                if b == "config.json":
                    return "runtime-config-json"
            return None
        return None

    # ---- Next.js API routes --------------------------------------------------------------
    def _base_path(self, ctx, proj, next_cfg, subproject):
        ev = proj.evaluator
        for p in next_cfg:
            m = proj.module(p)
            if m is None:
                continue
            for n in syntax.walk(m.root):
                if n.type == "pair" and syntax.text(n.child_by_field_name("key")) == "basePath":
                    v = ev.eval(m, n.child_by_field_name("value"))
                    lit = nc.literal_of(v)
                    if lit is not None:
                        return lit, {}, (p, syntax.line(n))
                    if isinstance(v, nc.SV) and len(v.parts) == 1 and isinstance(
                            v.parts[0], (nc.Env, nc.Cfg)):
                        p0 = v.parts[0]
                        nm = p0.name if isinstance(p0, nc.Env) else p0.key
                        vals = dict(ctx.config.public_values(nm, subproject))
                        if isinstance(p0, nc.Env) and p0.default and "code-default" not in vals:
                            vals["code-default"] = p0.default
                        return None, vals, (p, syntax.line(n))
                    return None, {}, (p, syntax.line(n))
        return None, {}, None

    def _next_routes(self, ctx, proj, paths, subproject, next_cfg, unresolved, types) -> list:
        base, base_vals, base_ev = self._base_path(ctx, proj, next_cfg, subproject)
        out = []
        sub = subproject or "."
        for p in paths:
            rel = p[len(sub) + 1:] if sub != "." and p.startswith(sub + "/") else p
            ma = re.match(r"^(?:src/)?app/(?:(.*)/)?route\.[cm]?[jt]sx?$", rel)
            mp = re.match(r"^(?:src/)?pages/api/(.*)\.[cm]?[jt]sx?$", rel)
            if not ma and not mp:
                continue
            m = proj.module(p)
            if m is None:
                continue
            if ma:
                route = self._route_from(ma.group(1) or "")
                methods = []
                for name in VERBS:
                    if name in m.exports:
                        d = m.decls.get(name)
                        methods.append((name, syntax.line(d) if d is not None else 1))
            else:
                segs = mp.group(1)
                if segs == "index" or segs.endswith("/index"):
                    segs = segs[: -len("index")].rstrip("/")
                route = pathnorm.join("/api", self._route_from(segs))
                dline = syntax.line(m.default) if m.default is not None else 1
                text = ctx.read_text(p) or ""
                found = sorted(set(re.findall(r"""method\s*[!=]==?\s*['"]([A-Z]+)['"]""", text))
                               | set(re.findall(r"""case\s+['"]([A-Z]+)['"]\s*:""", text)))
                found = [x for x in found if x in VERBS]
                methods = [(x, dline) for x in found] or [(None, dline)]
                if not found:
                    unresolved.add(p)
            full = pathnorm.join(base, route) if base else route
            for meth, line in methods:
                ev_list = [ctx.evidence(p, line)]
                if base and base_ev:
                    ev_list.append(ctx.evidence(*base_ev))
                attrs = {"method": meth, "path": pathnorm.display_path(full),
                         "path_raw": rel, "path_params_normalized": pathnorm.normalize(full),
                         "handler": f"{p}#{meth or 'default'}", "framework": "next-api",
                         "params": [{"name": n, "in": "path", "type": "string", "required": True}
                                    for n in re.findall(r"\{(\w+)\}",
                                                        pathnorm.display_path(full))],
                         "context_path_by_env": base_vals if not base else {}}
                out.append(make_item("inbound_http", ctx.subproject_of(p), None, attrs, ev_list,
                                     self, "high" if meth and (base or not base_ev) else
                                     "medium"))
        return out

    @staticmethod
    def _route_from(segs: str) -> str:
        out = []
        for s in segs.split("/"):
            if not s or (s.startswith("(") and s.endswith(")")) or s.startswith("@"):
                continue
            mm = re.fullmatch(r"\[\[?(?:\.\.\.)?([A-Za-z_]\w*)\]\]?", s)
            out.append("{" + mm.group(1) + "}" if mm else s)
        return "/" + "/".join(out)

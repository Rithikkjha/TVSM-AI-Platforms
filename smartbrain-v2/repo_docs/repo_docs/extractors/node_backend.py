"""node.backend: Express / Nest / plain Node services (FEAT-004, docs/EXTRACTORS.md).

Applies (D-P6) to subprojects with ``express``/``nest`` stacks, or ``node`` without a frontend stack
(``react``/``nextjs``/``angular``; e.g. Catalog-Scheduler). Emits inbound_http (Express app/router
verbs + ``app.use`` mount prefixes across one import hop; Nest ``@Controller`` x ``@Get``… with
``setGlobalPrefix``/URI versioning/``RouterModule``; Azure Functions ``app.http``), schema,
outbound_http (axios/fetch/got/Nest HttpService, axios instances, one-level wrappers), messaging
(``@azure/service-bus`` senders/receivers with entity names resolved through ``process.env``/
``.env``/``ConfigService``/one constructor-or-method parameter hop; Nest ``@EventPattern``/
``@MessagePattern``), data_access (TypeORM/Mongoose/mongodb/Prisma/redis/pg/mysql2/mssql/
Sequelize/knex), scheduled_job (node-cron/cron/``@Cron``/``@Interval``/agenda/Functions
``app.timer``), config_key reads and ``SwaggerModule.setup`` api_contract.
Test files are not opened (D-P4: node test files only mock HTTP clients).
"""
from __future__ import annotations

import posixpath
import re

from .. import config_classify as cc
from .. import pathnorm
from ..inventory_schema import make_item
from . import node_common as nc
from . import syntax
from .base import ExtractResult, Extractor, RepoContext
from .shared_manifests import generated_contract_item

FRONTEND_STACKS = frozenset({"react", "nextjs", "angular"})
EXPRESS_VERBS = ("get", "post", "put", "patch", "delete", "all", "options", "head")
NEST_VERBS = {"Get": "GET", "Post": "POST", "Put": "PUT", "Patch": "PATCH", "Delete": "DELETE",
              "All": None, "Options": "OPTIONS", "Head": "HEAD"}
NEST_RESP = {"ApiOkResponse": 200, "ApiCreatedResponse": 201, "ApiAcceptedResponse": 202,
             "ApiNoContentResponse": 204, "ApiMovedPermanentlyResponse": 301,
             "ApiBadRequestResponse": 400, "ApiUnauthorizedResponse": 401,
             "ApiForbiddenResponse": 403, "ApiNotFoundResponse": 404,
             "ApiMethodNotAllowedResponse": 405, "ApiConflictResponse": 409,
             "ApiUnprocessableEntityResponse": 422, "ApiTooManyRequestsResponse": 429,
             "ApiInternalServerErrorResponse": 500, "ApiBadGatewayResponse": 502,
             "ApiServiceUnavailableResponse": 503, "ApiGatewayTimeoutResponse": 504}
HTTP_STATUS = {"CONTINUE": 100, "OK": 200, "CREATED": 201, "ACCEPTED": 202, "NO_CONTENT": 204,
               "PARTIAL_CONTENT": 206, "MOVED_PERMANENTLY": 301, "FOUND": 302,
               "NOT_MODIFIED": 304, "BAD_REQUEST": 400, "UNAUTHORIZED": 401,
               "PAYMENT_REQUIRED": 402, "FORBIDDEN": 403, "NOT_FOUND": 404,
               "METHOD_NOT_ALLOWED": 405, "NOT_ACCEPTABLE": 406, "REQUEST_TIMEOUT": 408,
               "CONFLICT": 409, "GONE": 410, "PRECONDITION_FAILED": 412,
               "PAYLOAD_TOO_LARGE": 413, "UNSUPPORTED_MEDIA_TYPE": 415,
               "UNPROCESSABLE_ENTITY": 422, "TOO_MANY_REQUESTS": 429,
               "INTERNAL_SERVER_ERROR": 500, "NOT_IMPLEMENTED": 501, "BAD_GATEWAY": 502,
               "SERVICE_UNAVAILABLE": 503, "GATEWAY_TIMEOUT": 504}
PUBLIC_DECOS = ("Public", "SkipAuth", "AllowAnonymous", "IsPublic", "NoAuth")
AUTH_MW = re.compile(r"auth|jwt|token|verify|guard|passport|protect|authorize", re.I)
SB_PUBLISH = ("createSender",)
SB_SUBSCRIBE = ("createReceiver", "acceptNextSession", "acceptSession")
DB_TYPES = {"mssql": "mssql", "postgres": "postgres", "postgresql": "postgres",
            "mysql": "mysql", "mariadb": "mysql", "mongodb": "mongo", "sqlite": "sqlite",
            "better-sqlite3": "sqlite", "oracle": "oracle", "cockroachdb": "postgres",
            "sqlserver": "mssql", "cosmosdb": "cosmos"}
_CRON_RE = re.compile(r"^[0-9*/,\-?LW# A-Za-z]{5,80}$")


def _sub_stacks(meta: dict, subproject: str | None) -> set[str]:
    return {s["stack"] for s in meta.get("stacks") or []
            if subproject is None or (s.get("subproject") or ".") == subproject}


def _status(v) -> int | None:
    lit = nc.literal_of(v)
    if lit and lit.isdigit():
        return int(lit)
    return None


class NodeBackendExtractor(Extractor):
    id = "node.backend"
    stacks = ("node", "express", "nest")
    extractor_version = nc.VERSION

    def applies_to(self, meta: dict, subproject: str | None = None) -> bool:
        st = _sub_stacks(meta, subproject)
        if st & {"express", "nest"}:
            return True
        return "node" in st and not st & FRONTEND_STACKS

    # ---- main ----------------------------------------------------------------------------
    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        proj = nc.project(ctx)
        paths = proj.paths_in(subproject)
        if not paths:
            return res
        unresolved: set[str] = set()
        types: list[str] = []
        res.items += self._express(ctx, proj, paths, unresolved)
        res.items += self._nest(ctx, proj, paths, unresolved, types)
        res.items += self._functions_http(ctx, proj, paths)
        http = ctx.symbols.get("node.http")
        if http is None:
            http = ctx.symbols["node.http"] = nc.HttpModel(proj)
            http.build(proj.paths_in(None))
        calls, unr = http.calls(paths)
        unresolved |= unr
        for c in calls:
            it = nc.call_item(ctx, self, c, "outbound_http")
            if it is None:
                unresolved.add(c.mod.path)
                continue
            res.items.append(it)
            types += nc.type_names(c.response) + nc.type_names(c.request)
        res.items += self._messaging(ctx, proj, paths, unresolved)
        res.items += self._data(ctx, proj, paths, subproject, unresolved)
        res.items += self._scheduled(ctx, proj, paths, unresolved)
        res.items += self._swagger(ctx, proj, paths)
        res.items += nc.config_reads(ctx, proj, paths, self)
        if types:
            res.items += nc.schema_items(ctx, proj, sorted(set(types)), subproject or ".", self)
        prisma = [p for p in ctx.paths(subproject) if posixpath.basename(p) == "schema.prisma"]
        for p in prisma:
            it = self._prisma(ctx, p)
            if it is not None:
                res.items.append(it)
        tsconf = [p for p in proj.tsconfig_paths() if ctx.subproject_of(p) == (subproject or ".")]
        nc.note_sdk_symbols(ctx, proj, paths)
        nc.touch_files(ctx, res, proj, paths, unresolved, extra=tsconf + prisma)
        return res

    # ---- Express -------------------------------------------------------------------------
    def _express(self, ctx, proj, paths, unresolved) -> list:
        ev = proj.evaluator
        routes, mounts = [], {}
        for p in paths:
            txt = ctx.read_text(p) or ""
            if not re.search(r"\.(get|post|put|patch|delete|all|use|route|options|head)\s*\(", txt):
                continue
            if "express" not in txt and "Router" not in txt and "app" not in txt:
                continue
            m = proj.module(p)
            if m is None:
                continue
            for n in syntax.walk(m.root):
                if n.type != "call_expression":
                    continue
                fn = nc.unwrap(n.child_by_field_name("function"))
                if fn is None or fn.type != "member_expression":
                    continue
                prop = syntax.text(fn.child_by_field_name("property"))
                obj = nc.unwrap(fn.child_by_field_name("object"))
                if prop in EXPRESS_VERBS:
                    args = nc.args_of(n)
                    if obj is not None and obj.type == "call_expression" and \
                            nc.callee_name(obj) == "route":
                        ofn = nc.unwrap(obj.child_by_field_name("function"))
                        if ofn is None or ofn.type != "member_expression":
                            continue
                        rv = ev.eval(m, ofn.child_by_field_name("object"))
                        oargs = nc.args_of(obj)
                        path_node = oargs[0] if oargs else None
                        handlers = args
                        line_nodes = [obj, n]
                    else:
                        rv = ev.eval(m, obj)
                        path_node = args[0] if args else None
                        handlers = args[1:]
                        line_nodes = [n]
                    if not isinstance(rv, nc.Router) or path_node is None or not handlers:
                        continue
                    pv = nc.literal_of(ev.eval(m, path_node))
                    if pv is None:
                        unresolved.add(p)
                        continue
                    routes.append((rv, prop, pv, m, line_nodes, handlers))
                elif prop == "use":
                    rv = ev.eval(m, obj)
                    if not isinstance(rv, nc.Router):
                        continue
                    args = nc.args_of(n)
                    prefix, rest = "", args
                    if args:
                        first = ev.eval(m, args[0])
                        lit = nc.literal_of(first)
                        if lit is not None:
                            prefix, rest = lit, args[1:]
                        elif isinstance(first, nc.SV):
                            unresolved.add(p)
                            continue
                    for a in rest:
                        av = ev.eval(m, a)
                        if isinstance(av, nc.Router) and av != rv:
                            mounts.setdefault(av, []).append((rv, prefix, p, syntax.line(n)))
        out = []
        for rv, verb, pv, m, line_nodes, handlers in routes:
            for prefix, mount_ev, ok in self._prefixes(rv, mounts, 0, ()):
                if not ok:
                    unresolved.add(m.path)
                full = pathnorm.join(prefix, pv) if prefix or pv not in ("", "/") else "/"
                if pv in ("*", "/*"):
                    full = pathnorm.join(prefix, "{*}")
                method = None if verb == "all" else verb.upper()
                params = [{"name": nm, "in": "path", "type": "string", "required": True}
                          for nm in re.findall(r"\{(\w+)\}", pathnorm.display_path(full))]
                params += self._express_query(handlers[-1])
                mws = [syntax.text(h) for h in handlers[:-1] if h.type in ("identifier",
                                                                           "member_expression",
                                                                           "call_expression")]
                auth_mw = [w for w in mws if AUTH_MW.search(w)]
                attrs = {"method": method, "path": pathnorm.display_path(full), "path_raw": pv,
                         "path_params_normalized": pathnorm.normalize(full),
                         "handler": self._handler(m, handlers[-1]), "framework": "express",
                         "params": params, "auth": "unknown" if auth_mw else None,
                         "auth_raw": ", ".join(auth_mw)[:200] if auth_mw else None}
                ev_list = [ctx.evidence(m.path, syntax.line(x)) for x in line_nodes]
                ev_list += [ctx.evidence(f, ln) for f, ln in mount_ev]
                conf = "medium" if (not ok or auth_mw) else "high"
                out.append(make_item("inbound_http", ctx.subproject_of(m.path), None, attrs,
                                     ev_list, self, conf))
        return out

    def _prefixes(self, r, mounts, depth, mount_ev):
        """[(prefix, mount evidence [(file, line)], resolved)] for a router."""
        if r.app:
            return [("", list(mount_ev), True)]
        ms = mounts.get(r)
        if not ms or depth > 6:
            return [("", list(mount_ev), False)]
        out = []
        for parent, pre, f, ln in ms:
            for pp, evs, ok in self._prefixes(parent, mounts, depth + 1, mount_ev + ((f, ln),)):
                out.append((pathnorm.join(pp, pre) if pp or pre else "", evs, ok))
        return out

    @staticmethod
    def _handler(m, h) -> str:
        h = nc.unwrap(h)
        if h.type in ("identifier", "member_expression"):
            return syntax.text(h)
        if h.type in ("arrow_function", "function_expression", "function"):
            body = h.child_by_field_name("body")
            calls = []
            if body is not None and body.type == "call_expression":
                calls = [body]
            elif body is not None:
                sts = [c for c in syntax.named_children(body) if c.type != "comment"]
                if len(sts) == 1 and sts[0].type == "expression_statement":
                    e = nc.unwrap(syntax.named_children(sts[0])[0])
                    if e is not None and e.type == "call_expression":
                        calls = [e]
            if calls:
                return syntax.text(nc.unwrap(calls[0].child_by_field_name("function")))[:120]
        return f"{m.path}:{syntax.line(h)}"

    @staticmethod
    def _express_query(h) -> list:
        h = nc.unwrap(h)
        if h is None or h.type not in ("arrow_function", "function_expression", "function"):
            return []
        ps = syntax.params_of(h, "ts")
        if not ps:
            return []
        req = re.sub(r"[:\s].*$", "", ps[0].name)
        body = syntax.text(h.child_by_field_name("body"))
        names = re.findall(rf"\b{re.escape(req)}\.query\.(\w+)", body)
        for m in re.finditer(rf"\{{([^{{}}]*)\}}\s*=\s*{re.escape(req)}\.query\b", body):
            names += [x.split(":")[0].split("=")[0].strip() for x in m.group(1).split(",")]
        out, seen = [], set()
        for nm in names:
            if nm and re.fullmatch(r"\w+", nm) and nm not in seen:
                seen.add(nm)
                out.append({"name": nm, "in": "query", "type": "string", "required": False})
        return out

    # ---- Nest ----------------------------------------------------------------------------
    def _nest_globals(self, ctx, proj, paths):
        ev = proj.evaluator
        g = {"prefix": None, "prefix_ev": None, "exclude": [], "uri": False, "default_ver": None,
             "module_prefix": {}, "ctrl_module": {}, "app_guard": None, "app_guard_ev": None}
        for p in paths:
            txt = ctx.read_text(p) or ""
            if not any(k in txt for k in ("setGlobalPrefix", "enableVersioning", "RouterModule",
                                          "@Module", "APP_GUARD")):
                continue
            m = proj.module(p)
            if m is None:
                continue
            for n in syntax.walk(m.root):
                if n.type == "call_expression":
                    name = nc.callee_name(n)
                    args = nc.args_of(n)
                    if name == "setGlobalPrefix" and args:
                        lit = nc.literal_of(ev.eval(m, args[0]))
                        if lit is not None:
                            g["prefix"], g["prefix_ev"] = lit, (p, syntax.line(n))
                        if len(args) > 1 and args[1].type == "object":
                            for pair in syntax.named_children(args[1]):
                                if pair.type == "pair" and syntax.text(
                                        pair.child_by_field_name("key")) == "exclude":
                                    arr = pair.child_by_field_name("value")
                                    for el in syntax.named_children(arr) if arr is not None else []:
                                        v = ev.eval(m, el)
                                        if isinstance(v, nc.Obj):
                                            v = ev._obj_member(v, "path")
                                        lit2 = nc.literal_of(v)
                                        if lit2 is not None:
                                            g["exclude"].append(pathnorm.match_key(lit2))
                    elif name == "enableVersioning":
                        t = syntax.text(n)
                        if "URI" in t or not args:
                            g["uri"] = True
                            if args:
                                o = ev.eval(m, args[0])
                                if isinstance(o, nc.Obj):
                                    g["default_ver"] = nc.literal_of(
                                        ev._obj_member(o, "defaultVersion"))
                    elif name in ("register", "forRoutes") and "RouterModule" in syntax.text(
                            n.child_by_field_name("function")) and args:
                        self._router_module(m, ev, args[0], "", g)
                elif n.type == "decorator" and syntax.text(n).startswith("@Module"):
                    ann = syntax.annotation_of(n, m.lang)
                    a = nc.decorator_args(ann)
                    cls = n.parent
                    while cls is not None and cls.type not in ("class_declaration",
                                                               "export_statement"):
                        cls = cls.parent
                    if cls is not None and cls.type == "export_statement":
                        cls = cls.child_by_field_name("declaration")
                    cname = syntax.text(cls.child_by_field_name("name")) if cls is not None else ""
                    if a and a[0].type == "object":
                        for pair in syntax.named_children(a[0]):
                            if pair.type != "pair":
                                continue
                            k = syntax.text(pair.child_by_field_name("key"))
                            val = pair.child_by_field_name("value")
                            if k == "controllers" and val is not None:
                                for el in syntax.named_children(val):
                                    g["ctrl_module"][syntax.text(el)] = cname
                            if k == "providers" and val is not None:
                                for el in syntax.named_children(val):
                                    if el.type == "object" and "APP_GUARD" in syntax.text(el):
                                        uc = next((syntax.text(pp.child_by_field_name("value"))
                                                   for pp in syntax.named_children(el)
                                                   if pp.type == "pair" and syntax.text(
                                                       pp.child_by_field_name("key")) in (
                                                       "useClass", "useExisting")), None)
                                        if uc:
                                            g["app_guard"] = uc
                                            g["app_guard_ev"] = (p, syntax.line(el))
        return g

    def _router_module(self, m, ev, arr, prefix, g, depth=0):
        if arr is None or arr.type != "array" or depth > 4:
            return
        for el in syntax.named_children(arr):
            if el.type != "object":
                continue
            o = nc.Obj(m, el)
            pth = nc.literal_of(ev._obj_member(o, "path")) or ""
            full = pathnorm.join(prefix, pth) if prefix or pth else ""
            for pair in syntax.named_children(el):
                if pair.type != "pair":
                    continue
                k = syntax.text(pair.child_by_field_name("key"))
                if k == "module":
                    g["module_prefix"][syntax.text(pair.child_by_field_name("value"))] = full
                elif k == "children":
                    self._router_module(m, ev, pair.child_by_field_name("value"), full, g,
                                        depth + 1)

    def _paths_from(self, m, ev, nodes) -> list[str] | None:
        """Decorator path args -> list of literal paths ([''] when none); None if unresolved."""
        if not nodes:
            return [""]
        a = nodes[0]
        if a.type == "array":
            out = []
            for el in syntax.named_children(a):
                lit = nc.literal_of(ev.eval(m, el))
                if lit is None:
                    return None
                out.append(lit)
            return out or [""]
        v = ev.eval(m, a)
        if isinstance(v, nc.Obj):
            pv = ev._obj_member(v, "path")
            if isinstance(pv, nc.Unknown):
                return [""]
            v = pv
        lit = nc.literal_of(v)
        return [lit] if lit is not None else None

    def _nest(self, ctx, proj, paths, unresolved, types) -> list:
        ev = proj.evaluator
        g = None
        out = []
        for p in paths:
            txt = ctx.read_text(p) or ""
            if "@Controller" not in txt and "Pattern(" not in txt:
                continue
            m = proj.module(p)
            if m is None:
                continue
            if g is None:
                g = self._nest_globals(ctx, proj, paths)
            for td in syntax.type_decls(m.parsed):
                if td.kind != "class":
                    continue
                anns = {a.name: a for a in td.annotations}
                ctrl = anns.get("Controller")
                for md in syntax.methods(td, m.lang):
                    out += self._nest_messaging(ctx, m, ev, td, md)
                if ctrl is None:
                    continue
                cargs = nc.decorator_args(ctrl)
                cpaths = self._paths_from(m, ev, cargs)
                cver = None
                if cargs:
                    cv = ev.eval(m, cargs[0])
                    if isinstance(cv, nc.Obj):
                        cver = nc.literal_of(ev._obj_member(cv, "version"))
                if "Version" in anns:
                    va = nc.decorator_args(anns["Version"])
                    cver = nc.literal_of(ev.eval(m, va[0])) if va else cver
                if cpaths is None:
                    unresolved.add(p)
                    continue
                cguards = self._guards(anns)
                cpublic = any(n in anns for n in PUBLIC_DECOS)
                mod_prefix = g["module_prefix"].get(g["ctrl_module"].get(td.name, ""), "")
                for md in syntax.methods(td, m.lang):
                    manns = {a.name: a for a in md.annotations}
                    verb = next((a for a in md.annotations if a.name in NEST_VERBS), None)
                    if verb is None:
                        continue
                    mpaths = self._paths_from(m, ev, nc.decorator_args(verb))
                    if mpaths is None:
                        unresolved.add(p)
                        continue
                    ver = cver
                    if "Version" in manns:
                        va = nc.decorator_args(manns["Version"])
                        ver = nc.literal_of(ev.eval(m, va[0])) if va else ver
                    ver = ver or g["default_ver"]
                    for cp in cpaths:
                        for mp in mpaths:
                            out.append(self._nest_item(ctx, m, ev, td, md, ctrl, verb, cp, mp,
                                                       ver, mod_prefix, g, cguards, cpublic,
                                                       manns, types))
        return out

    @staticmethod
    def _guards(anns) -> list[str]:
        ug = anns.get("UseGuards")
        if ug is None:
            return []
        return [syntax.text(a) for a in nc.decorator_args(ug)]

    def _nest_item(self, ctx, m, ev, td, md, ctrl, verb, cp, mp, ver, mod_prefix, g, cguards,
                   cpublic, manns, types):
        local = pathnorm.join(pathnorm.join(mod_prefix, cp), mp)
        evid = [ctx.evidence(m.path, verb.line), ctx.evidence(m.path, ctrl.line)]
        full = local
        if g["uri"] and ver:
            full = pathnorm.join("v" + str(ver).lstrip("v"), full)
        if g["prefix"] and pathnorm.match_key(local) not in g["exclude"]:
            full = pathnorm.join(g["prefix"], full)
            evid.append(ctx.evidence(*g["prefix_ev"]))
        method = NEST_VERBS[verb.name]
        params, request = [], None
        for prm in md.params:
            pan = {a.name: a for a in prm.annotations}
            pty = nc.norm_type(prm.type)
            for dn, where in (("Param", "path"), ("Query", "query"), ("Body", "body"),
                              ("Headers", "header")):
                if dn not in pan:
                    continue
                a = nc.decorator_args(pan[dn])
                nm = nc.literal_of(ev.eval(m, a[0])) if a else None
                if dn == "Body":
                    if nm is None:
                        request = nc.unwrap_type(prm.type)
                        types += nc.type_names(prm.type)
                    params.append({"name": nm or prm.name, "in": "body", "type": pty,
                                   "required": not prm.optional})
                elif nm is None:
                    params.append({"name": prm.name, "in": where, "type": pty or "object",
                                   "required": where == "path" or not prm.optional})
                    if where == "query":
                        types += nc.type_names(prm.type)
                else:
                    params.append({"name": nm, "in": where, "type": pty or "string",
                                   "required": where == "path" or not prm.optional})
        declared = {x["name"] for x in params if x["in"] == "path"}
        for nm in re.findall(r"\{(\w+)\}", pathnorm.display_path(full)):
            if nm not in declared:
                params.append({"name": nm, "in": "path", "type": "string", "required": True})
        responses, http_code = [], None
        if "HttpCode" in manns:
            a = nc.decorator_args(manns["HttpCode"])
            http_code = self._status_of(m, ev, a[0]) if a else None
        for a in md.annotations:
            if a.name == "ApiResponse" or a.name in NEST_RESP:
                st = NEST_RESP.get(a.name)
                schema, when = None, None
                da = nc.decorator_args(a)
                if da and da[0].type == "object":
                    for pair in syntax.named_children(da[0]):
                        if pair.type != "pair":
                            continue
                        k = syntax.text(pair.child_by_field_name("key"))
                        val = pair.child_by_field_name("value")
                        if k == "status":
                            st = self._status_of(m, ev, val)
                        elif k == "type" and val is not None:
                            schema = (syntax.text(syntax.named_children(val)[0]) + "[]"
                                      if val.type == "array" and syntax.named_children(val)
                                      else syntax.text(val))
                        elif k == "description":
                            when = nc.literal_of(ev.eval(m, val))
                if schema:
                    types += nc.type_names(schema)
                responses.append({"status": st, "schema": schema, "when": when,
                                  "from": "annotation"})
        ok = http_code or (201 if method == "POST" else 200)
        if not any(r["status"] == ok for r in responses):
            rt = nc.unwrap_type(md.return_type)
            schema = rt if rt and nc.type_names(rt) else None
            if schema:
                types += nc.type_names(schema)
            responses.append({"status": ok, "schema": schema, "when": None,
                              "from": "return-type" if schema else "default"})
        responses.sort(key=lambda r: (r["status"] is None, r["status"] or 0))
        mguards = self._guards(manns)
        guards = mguards or cguards
        public = cpublic or any(n in manns for n in PUBLIC_DECOS)
        medium = False
        if public:
            auth, auth_raw, allow = "none", "@Public()", True
            medium = True
        elif guards:
            auth, auth_raw, allow = f"guard:{guards[0]}", "@UseGuards(" + ", ".join(guards) + ")", \
                None
        elif g["app_guard"]:
            auth, auth_raw, allow = f"guard:{g['app_guard']}", f"APP_GUARD {g['app_guard']}", None
            evid.append(ctx.evidence(*g["app_guard_ev"]))
            medium = True
        elif "ApiBearerAuth" in manns or any(a.name == "ApiBearerAuth" for a in td.annotations):
            auth, auth_raw, allow = "bearer-jwt", "@ApiBearerAuth()", None
            medium = True
        else:
            auth, auth_raw, allow = None, None, None
        deprecated = None
        op = manns.get("ApiOperation")
        if op is not None and re.search(r"deprecated\s*:\s*true", syntax.text(op.node)):
            deprecated = True
        attrs = {"method": method, "path": pathnorm.display_path(full),
                 "path_raw": pathnorm.join(cp, mp),
                 "path_params_normalized": pathnorm.normalize(full),
                 "handler": f"{td.name}.{md.name}", "framework": "nest", "params": params,
                 "request": request, "responses": responses, "auth": auth, "auth_raw": auth_raw,
                 "allow_anonymous": allow, "deprecated": deprecated}
        return make_item("inbound_http", ctx.subproject_of(m.path), None, attrs, evid, self,
                         "medium" if medium else "high")

    @staticmethod
    def _status_of(m, ev, node) -> int | None:
        if node is None:
            return None
        t = syntax.text(node)
        mm = re.fullmatch(r"HttpStatus\.(\w+)", t)
        if mm:
            return HTTP_STATUS.get(mm.group(1))
        return _status(ev.eval(m, node))

    def _nest_messaging(self, ctx, m, ev, td, md) -> list:
        out = []
        for a in md.annotations:
            if a.name not in ("EventPattern", "MessagePattern"):
                continue
            da = nc.decorator_args(a)
            v = ev.eval(m, da[0]) if da else nc.UNKNOWN
            attrs = self._entity_attrs(ctx, v, ctx.subproject_of(m.path))
            attrs.update({"direction": "subscribe", "broker": None,
                          "handler": f"{m.path}:{a.line}", "trigger": "message-pattern",
                          "library": "@nestjs/microservices"})
            out.append(make_item("messaging", ctx.subproject_of(m.path),
                                 self._msg_key(attrs, m.path, a.line), attrs,
                                 [ctx.evidence(m.path, a.line)], self,
                                 "high" if attrs["name_from"] == "literal" else "medium"))
        return out

    # ---- Azure Functions (node programming model v4) -------------------------------------
    def _functions_http(self, ctx, proj, paths) -> list:
        ev = proj.evaluator
        out = []
        prefix = "api"
        for hp in ctx.paths(None, lambda e: posixpath.basename(e["path"]) == "host.json"):
            from . import configfmt
            r = configfmt.parse_jsonc(ctx.read_text(hp) or "")
            rp = (((r.data or {}).get("extensions") or {}).get("http") or {}).get("routePrefix") \
                if isinstance(r.data, dict) else None
            if isinstance(rp, str):
                prefix = rp
        for p in paths:
            txt = ctx.read_text(p) or ""
            if "@azure/functions" not in txt or ".http(" not in txt:
                continue
            m = proj.module(p)
            if m is None:
                continue
            for n in syntax.walk(m.root):
                if n.type != "call_expression" or nc.callee_name(n) != "http":
                    continue
                fn = nc.unwrap(n.child_by_field_name("function"))
                ov = ev.eval(m, fn.child_by_field_name("object")) if fn.type == \
                    "member_expression" else None
                if not (isinstance(ov, nc.Lib) and ov.pkg == "@azure/functions"):
                    continue
                args = nc.args_of(n)
                name = nc.literal_of(ev.eval(m, args[0])) if args else None
                if not name or len(args) < 2:
                    continue
                o = ev.eval(m, args[1])
                route = nc.literal_of(ev._obj_member(o, "route")) if isinstance(o, nc.Obj) else None
                methods_node = None
                if isinstance(o, nc.Obj):
                    for pair in syntax.named_children(o.node):
                        if pair.type == "pair" and syntax.text(
                                pair.child_by_field_name("key")) == "methods":
                            methods_node = pair.child_by_field_name("value")
                methods = [nc.literal_of(ev.eval(m, x)) for x in syntax.named_children(
                    methods_node)] if methods_node is not None else [None]
                full = pathnorm.join(prefix, route if route is not None else name)
                for meth in methods:
                    attrs = {"method": meth.upper() if meth else None,
                             "path": pathnorm.display_path(full), "path_raw": route or name,
                             "path_params_normalized": pathnorm.normalize(full),
                             "handler": f"{p}:{syntax.line(n)}", "framework": "azure-functions"}
                    out.append(make_item("inbound_http", ctx.subproject_of(p), None, attrs,
                                         [ctx.evidence(p, syntax.line(n))], self, "medium"))
        return out

    # ---- messaging -----------------------------------------------------------------------
    def _entity_attrs(self, ctx, v, sub) -> dict:
        a = {"entity": None, "name_from": "unknown", "name_key": None, "resolved_values": {}}
        s = v if isinstance(v, nc.SV) else None
        if s is None:
            return a
        lit = s.literal()
        if lit:
            a.update(entity=lit, name_from="literal")
            return a
        if len(s.parts) == 1:
            p0 = s.parts[0]
            if isinstance(p0, (nc.Env, nc.Cfg)):
                nm = p0.name if isinstance(p0, nc.Env) else p0.key
                vals = ctx.config.public_values(nm, sub)
                if not vals and isinstance(p0, nc.Env) and p0.default:
                    c = cc.classify(nm, p0.default)
                    if c.record_value is not None and not c.secret:
                        vals = {"code-default": c.record_value}
                ent = vals.get("default") or (next(iter(vals.values())) if len(vals) == 1
                                               else None)
                a.update(entity=ent, name_from=(f"env:{nm}" if isinstance(p0, nc.Env)
                                                else f"config:{nm}"),
                         name_key=nm, resolved_values=dict(sorted(vals.items())))
            elif isinstance(p0, nc.Key):
                a.update(name_key=p0.name)
        return a

    @staticmethod
    def _msg_key(attrs, file, line) -> str:
        nf = attrs["name_from"]
        ref = attrs["entity"] if nf == "literal" else nf
        if nf == "unknown":
            ref = f"unknown:{attrs['name_key']}" if attrs["name_key"] else f"unknown@{file}:{line}"
        return f"{attrs['direction']}:{attrs['broker'] or '_'}:{ref or '_'}"

    def _hop(self, ctx, proj, m, node):
        """[(value, extra evidence)] for an entity argument, following one constructor / method
        parameter hop when the value is a parameter (``this.topicName`` set from a ctor param)."""
        ev = proj.evaluator
        v = ev.eval(m, node)
        prm = None
        if isinstance(v, nc.Param):
            prm = v
        elif isinstance(v, nc.SV) and len(v.parts) == 1 and isinstance(v.parts[0], nc.Param):
            prm = v.parts[0]
        if prm is None:
            return [(v, [])]
        fpath, fkey = prm.owner
        fm = proj.module(fpath)
        fn = next((x for x in syntax.walk(fm.root) if nc.key_of(x) == fkey), None) if fm else None
        if fn is None or fn.type != "method_definition":
            return [(nc.UNKNOWN, [])]
        cls = nc.enclosing_class(fn)
        if cls is None:
            return [(nc.UNKNOWN, [])]
        cname = syntax.text(cls.child_by_field_name("name"))
        mname = nc._member_name(fn)
        params = nc.fn_params(fn, fm.lang)
        if prm.name not in params:
            return [(nc.UNKNOWN, [])]
        idx = params.index(prm.name)
        out = []
        for p2 in proj.paths_in(None):
            txt = ctx.read_text(p2) or ""
            if mname == "constructor":
                if f"new {cname}" not in txt:
                    continue
            elif mname not in txt or (cname not in txt and p2 != fpath):
                continue
            m2 = proj.module(p2)
            if m2 is None:
                continue
            for n in syntax.walk(m2.root):
                site = None
                if mname == "constructor" and n.type == "new_expression" and syntax.text(
                        n.child_by_field_name("constructor")) == cname:
                    site = n
                elif mname != "constructor" and n.type == "call_expression":
                    f = nc.unwrap(n.child_by_field_name("function"))
                    if f is None or f.type != "member_expression" or syntax.text(
                            f.child_by_field_name("property")) != mname:
                        continue
                    o = syntax.text(f.child_by_field_name("object"))
                    c2 = nc.enclosing_class(n)
                    if o in ("this", "super") and c2 is not None and (
                            nc.key_of(c2) == nc.key_of(cls) and p2 == fpath
                            or re.search(rf"\bextends\s+{re.escape(cname)}\b", syntax.text(c2))):
                        if nc.key_of(c2) == nc.key_of(cls) and p2 == fpath:
                            continue    # internal re-call; not a configuration site
                        site = n
                if site is None:
                    continue
                a = nc.args_of(site)
                if idx >= len(a):
                    continue
                v2 = ev.eval(m2, a[idx])
                if isinstance(v2, nc.Param) or (isinstance(v2, nc.SV) and any(
                        isinstance(x, nc.Param) for x in v2.parts)):
                    v2 = nc.UNKNOWN
                out.append((v2, [ctx.evidence(p2, syntax.line(site))]))
        return out or [(nc.UNKNOWN, [])]

    def _messaging(self, ctx, proj, paths, unresolved) -> list:
        out = []
        for p in paths:
            txt = ctx.read_text(p) or ""
            if not any(k in txt for k in SB_PUBLISH + SB_SUBSCRIBE):
                continue
            m = proj.module(p)
            if m is None or m.imports_pkg("@azure/service-bus") is None:
                continue
            for n in syntax.walk(m.root):
                if n.type != "call_expression":
                    continue
                name = nc.callee_name(n)
                if name not in SB_PUBLISH + SB_SUBSCRIBE:
                    continue
                args = nc.args_of(n)
                if not args or args[0].type == "object":
                    continue
                direction = "publish" if name in SB_PUBLISH else "subscribe"
                sub_node = args[1] if direction == "subscribe" and len(args) > 1 and \
                    args[1].type != "object" else None
                line = syntax.line(n)
                for v, extra in self._hop(ctx, proj, m, args[0]):
                    attrs = self._entity_attrs(ctx, v, ctx.subproject_of(p))
                    subscription = None
                    if sub_node is not None:
                        sv_list = self._hop(ctx, proj, m, sub_node)
                        sv_ = sv_list[0][0] if len(sv_list) == 1 else None
                        if extra and len(sv_list) > 1:
                            # pick the site that matches this entity's evidence
                            sv_ = next((x for x, e in sv_list if e == extra), sv_)
                        sa = self._entity_attrs(ctx, sv_, ctx.subproject_of(p))
                        subscription = sa["entity"] or (
                            f"{sa['name_from']}" if sa["name_from"] != "unknown" else
                            (f"unknown:{sa['name_key']}" if sa["name_key"] else None))
                    hint = (attrs["name_key"] or syntax.text(args[0])).lower()
                    etype = "topic" if sub_node is not None or "topic" in hint else \
                        "queue" if "queue" in hint or name == "createReceiver" else None
                    attrs.update({"direction": direction, "broker": "azure-service-bus",
                                  "entity_type": etype, "subscription": subscription,
                                  "library": "@azure/service-bus",
                                  "trigger": "processor" if direction == "subscribe" else None})
                    attrs["published_by" if direction == "publish" else "handler"] = f"{p}:{line}"
                    if attrs["name_from"] == "unknown" and not attrs["name_key"]:
                        unresolved.add(p)
                    conf = "high" if attrs["name_from"] == "literal" and not extra else "medium"
                    if attrs["name_from"].startswith("env:") and not extra and \
                            attrs["entity"] is not None:
                        conf = "high"
                    out.append(make_item("messaging", ctx.subproject_of(p),
                                         self._msg_key(attrs, p, line), attrs,
                                         [ctx.evidence(p, line)] + extra, self, conf))
        return out

    # ---- data access ---------------------------------------------------------------------
    def _store_ref(self, ctx, ev, m, node, sub) -> dict:
        """name_from/host/database for a connection-ish value (never the value itself)."""
        v = ev.eval(m, node) if node is not None else None
        out = {"name_from": None, "host": None, "database": None}
        if isinstance(v, nc.Obj):
            for k in ("url", "uri", "host", "connectionString"):
                r = self._store_ref(ctx, ev, m, self._pair_node(v.node, k), sub)
                if r["name_from"] or r["host"]:
                    return r
            return out
        if isinstance(v, nc.SV) and v.parts:
            refs = [x for x in v.parts if isinstance(x, (nc.Env, nc.Cfg))]
            if len(v.parts) == 1:
                p0 = v.parts[0]
            else:   # composed URL: prefer the host / url / connection part
                p0 = next((x for x in refs if re.search(
                    r"HOST|URL|URI|CONNECTION|SERVER", getattr(x, "name", "") or
                    getattr(x, "key", ""), re.I)), None)
            nm = None
            if isinstance(p0, nc.Env):
                nm, out["name_from"] = p0.name, f"env:{p0.name}"
            elif isinstance(p0, nc.Cfg):
                nm, out["name_from"] = p0.key, f"config:{p0.key}"
            if nm:
                raw = ctx.config.resolve("${" + nm + "}", "default", sub).value
                ident = cc.parse_store_identity(raw) if raw else None
                if ident:
                    out["host"], out["database"] = ident.get("host"), ident.get("database")
        return out

    @staticmethod
    def _pair_node(obj, key):
        for pair in syntax.named_children(obj):
            if pair.type == "pair" and syntax.text(pair.child_by_field_name("key")).strip(
                    "'\"") == key:
                return pair.child_by_field_name("value")
        return None

    def _data(self, ctx, proj, paths, subproject, unresolved) -> list:
        ev = proj.evaluator
        stores: dict[tuple, dict] = {}

        def store(st, orm, ref, line_ev, conf="high"):
            k = (st, ref.get("name_from") or ref.get("host") or "_", orm)
            s = stores.setdefault(k, {"attrs": {"store_type": st, "orm": orm, "entities": [],
                                                "collections": [], "host": ref.get("host"),
                                                "database": ref.get("database"),
                                                "name_from": ref.get("name_from")},
                                      "ev": [], "conf": conf})
            s["ev"].append(line_ev)
            return s

        pk = {"typeorm": "typeorm", "@nestjs/typeorm": "typeorm", "mongoose": "mongoose",
              "@nestjs/mongoose": "mongoose", "mongodb": None, "redis": "redis-client",
              "ioredis": "redis-client", "pg": "pg", "mysql2": "mysql2", "mssql": None,
              "sequelize": "sequelize", "knex": "knex"}
        st_of = {"mongoose": "mongo", "@nestjs/mongoose": "mongo", "mongodb": "mongo",
                 "redis": "redis", "ioredis": "redis", "pg": "postgres", "mysql2": "mysql",
                 "mssql": "mssql"}
        typeorm_entities, typeorm_cfg = [], []
        mongo_cols: dict[str, list] = {}
        import_only: dict[str, tuple] = {}
        any_mongodb = False
        for p in paths:
            m = proj.module(p)
            if m is None:
                continue
            pkgs = {s for s in m.pkgs if s in pk}
            if "mongodb" in pkgs:
                any_mongodb = True
            if not pkgs and ".collection(" not in (ctx.read_text(p) or ""):
                continue
            for spec in sorted(pkgs):
                if spec in st_of and spec not in ("mongoose", "@nestjs/mongoose", "mongodb"):
                    import_only.setdefault(st_of[spec], (pk[spec], ctx.evidence(p, m.pkgs[spec])))
            if pkgs & {"typeorm", "@nestjs/typeorm"}:
                for td in syntax.type_decls(m.parsed):
                    ent = next((a for a in td.annotations if a.name == "Entity"), None)
                    if ent is None:
                        continue
                    da = nc.decorator_args(ent)
                    table = schema = None
                    if da:
                        v = ev.eval(m, da[0])
                        if isinstance(v, nc.Obj):
                            table = nc.literal_of(ev._obj_member(v, "name"))
                            schema = nc.literal_of(ev._obj_member(v, "schema"))
                        else:
                            table = nc.literal_of(v)
                    typeorm_entities.append(({"name": td.name, "table": table, "schema": schema,
                                              "defined_in": f"{p}:{td.line}", "operation": None},
                                             ctx.evidence(p, ent.line)))
                for n in syntax.walk(m.root):
                    if n.type == "pair" and syntax.text(n.child_by_field_name("key")) == "type":
                        lit = nc.literal_of(ev.eval(m, n.child_by_field_name("value")))
                        if lit in DB_TYPES and n.parent is not None:
                            typeorm_cfg.append((DB_TYPES[lit], self._store_ref(
                                ctx, ev, m, n.parent, subproject), ctx.evidence(p, syntax.line(n))))
            mongoose = bool(pkgs & {"mongoose", "@nestjs/mongoose"})
            for n in syntax.walk(m.root):
                if n.type != "call_expression":
                    continue
                cn = nc.callee_name(n)
                args = nc.args_of(n)
                if mongoose and cn == "model" and args:
                    lit = nc.literal_of(ev.eval(m, args[0]))
                    if lit:
                        mongo_cols.setdefault("mongoose", []).append(
                            (lit, ctx.evidence(p, syntax.line(n))))
                    else:
                        unresolved.add(p)
                elif mongoose and cn in ("connect", "createConnection") and args and \
                        "mongoose" in syntax.text(n.child_by_field_name("function")):
                    store("mongo", "mongoose", self._store_ref(ctx, ev, m, args[0], subproject),
                          ctx.evidence(p, syntax.line(n)))
                elif cn == "collection" and args:
                    lit = nc.literal_of(ev.eval(m, args[0]))
                    if lit:
                        mongo_cols.setdefault("driver", []).append(
                            (lit, ctx.evidence(p, syntax.line(n))))
                elif "mongodb" in pkgs and cn in ("MongoClient", "connect") and args and \
                        "MongoClient" in syntax.text(n):
                    store("mongo", None, self._store_ref(ctx, ev, m, args[0], subproject),
                          ctx.evidence(p, syntax.line(n)))
            for n in syntax.walk(m.root):
                if n.type == "new_expression":
                    cn = syntax.text(n.child_by_field_name("constructor"))
                    args = nc.args_of(n)
                    if cn == "MongoClient" and "mongodb" in pkgs and args:
                        store("mongo", None, self._store_ref(ctx, ev, m, args[0], subproject),
                              ctx.evidence(p, syntax.line(n)))
                    elif cn in ("Redis",) and "ioredis" in pkgs:
                        store("redis", "redis-client",
                              self._store_ref(ctx, ev, m, args[0] if args else None, subproject),
                              ctx.evidence(p, syntax.line(n)))
                    elif cn == "Sequelize" and "sequelize" in pkgs:
                        dial = None
                        for a in args:
                            if a.type == "object":
                                dial = nc.literal_of(ev.eval(m, self._pair_node(a, "dialect")))
                        store(DB_TYPES.get(dial or "", "other"), "sequelize", {},
                              ctx.evidence(p, syntax.line(n)), "medium")
                elif n.type == "call_expression" and nc.callee_name(n) == "createClient" and \
                        "redis" in pkgs:
                    a = nc.args_of(n)
                    store("redis", "redis-client",
                          self._store_ref(ctx, ev, m, a[0] if a else None, subproject),
                          ctx.evidence(p, syntax.line(n)))
        if typeorm_entities or typeorm_cfg:
            cfgs = typeorm_cfg or [("other", {}, None)]
            for st, ref, line_ev in cfgs:
                s = store(st, "typeorm", ref, line_ev or typeorm_entities[0][1],
                          "high" if typeorm_cfg else "medium")
                s["attrs"]["entities"] = sorted([e for e, _ in typeorm_entities],
                                                key=lambda e: (e["name"], e["defined_in"]))
                s["ev"] += [x for _, x in typeorm_entities]
        for orm_kind, cols in sorted(mongo_cols.items()):
            if orm_kind == "driver" and not any_mongodb:
                continue
            orm = "mongoose" if orm_kind == "mongoose" else None
            cands = [k for k in stores if k[0] == "mongo" and k[2] == orm]
            if cands:
                s = stores[cands[0]]
            else:
                s = store("mongo", orm, {}, cols[0][1], "medium")
            s["attrs"]["collections"] = sorted(set(s["attrs"]["collections"]) | {c for c, _ in cols})
            s["ev"] += [e for _, e in cols]
        for st, (orm, line_ev) in sorted(import_only.items()):
            if not any(k[0] == st for k in stores):
                store(st, orm, {}, line_ev, "medium")
        out = []
        for k in sorted(stores, key=lambda x: (x[0], x[1], x[2] or "")):
            s = stores[k]
            a = s["attrs"]
            sub = ctx.subproject_of(s["ev"][0].file)
            out.append(make_item("data_access", sub, None, a, s["ev"], self, s["conf"]))
        return out

    def _prisma(self, ctx, path):
        text = ctx.read_text(path)
        if not text:
            return None
        lines = text.split("\n")
        st, ref, ev_lines, entities = None, {}, [], []
        cur, cur_line, block = None, None, None
        for i, ln in enumerate(lines, 1):
            s = ln.strip()
            mm = re.match(r"^(datasource|model|generator|enum)\s+(\w+)\s*\{", s)
            if mm:
                block, cur, cur_line = mm.group(1), mm.group(2), i
                if block == "model":
                    entities.append({"name": cur, "table": None, "schema": None,
                                     "defined_in": f"{path}:{i}", "operation": None})
                    ev_lines.append(i)
                continue
            if s == "}":
                block = None
                continue
            if block == "datasource":
                pm = re.match(r'^provider\s*=\s*"(\w+)"', s)
                if pm:
                    st = DB_TYPES.get(pm.group(1), "other")
                    ev_lines.append(i)
                um = re.match(r'^url\s*=\s*env\("(\w+)"\)', s)
                if um:
                    ref = {"name_from": f"env:{um.group(1)}"}
            elif block == "model":
                mp = re.match(r'^@@map\("([^"]+)"\)', s)
                if mp and entities:
                    entities[-1]["table"] = mp.group(1)
                sp = re.match(r'^@@schema\("([^"]+)"\)', s)
                if sp and entities:
                    entities[-1]["schema"] = sp.group(1)
        if st is None and not entities:
            return None
        attrs = {"store_type": st or "other", "orm": "prisma", "entities": entities,
                 "name_from": ref.get("name_from")}
        return make_item("data_access", ctx.subproject_of(path), None, attrs,
                         [ctx.evidence(path, i) for i in ev_lines], self)

    # ---- schedulers ----------------------------------------------------------------------
    def _expr_attrs(self, ctx, v, sub) -> dict:
        a = {"expression": None, "expression_from": None, "resolved_values": {}}
        if not isinstance(v, nc.SV):
            return a
        lit = v.literal()
        if lit is not None:
            a.update(expression=lit, expression_from="literal")
            return a
        if len(v.parts) == 1 and isinstance(v.parts[0], (nc.Env, nc.Cfg)):
            p0 = v.parts[0]
            nm = p0.name if isinstance(p0, nc.Env) else p0.key
            a["expression_from"] = f"env:{nm}" if isinstance(p0, nc.Env) else f"config:{nm}"
            vals = {}
            if not cc.key_is_secret(nm):
                for env in ctx.config.resolved_envs(nm, sub) or []:
                    r = ctx.config.resolve("${" + nm + "}", env, sub)
                    if r.value and _CRON_RE.match(r.value) and not cc.value_is_secret(r.value):
                        vals[env] = r.value
                for env in ctx.config.envs(nm, sub):
                    if env not in vals:
                        r = ctx.config.resolve("${" + nm + "}", env, sub)
                        if r.value and _CRON_RE.match(r.value) and not cc.value_is_secret(r.value):
                            vals[env] = r.value
            a["resolved_values"] = dict(sorted(vals.items()))
            a["expression"] = vals.get("default") or (next(iter(vals.values()))
                                                      if len(vals) == 1 else None)
        return a

    def _scheduled(self, ctx, proj, paths, unresolved) -> list:
        ev = proj.evaluator
        out = []
        for p in paths:
            txt = ctx.read_text(p) or ""
            if not re.search(r"schedule|@Cron|@Interval|CronJob|\.timer\(|\.every\(", txt):
                continue
            m = proj.module(p)
            if m is None:
                continue
            sub = ctx.subproject_of(p)
            for n in syntax.walk(m.root):
                item = None
                if n.type == "call_expression":
                    cn = nc.callee_name(n)
                    fn = nc.unwrap(n.child_by_field_name("function"))
                    obj = fn.child_by_field_name("object") if fn is not None and \
                        fn.type == "member_expression" else None
                    ov = ev.eval(m, obj) if obj is not None and cn in (
                        "schedule", "timer", "every") else None
                    args = nc.args_of(n)
                    if cn == "schedule" and isinstance(ov, nc.Lib) and ov.pkg == "node-cron" \
                            and args:
                        a = self._expr_attrs(ctx, ev.eval(m, args[0]), sub)
                        a.update(trigger_type="node-cron", handler=f"{p}:{syntax.line(n)}")
                        item = a
                    elif cn == "timer" and isinstance(ov, nc.Lib) and \
                            ov.pkg == "@azure/functions" and len(args) > 1:
                        o = ev.eval(m, args[1])
                        sched = ev._obj_member(o, "schedule") if isinstance(o, nc.Obj) else None
                        a = self._expr_attrs(ctx, sched, sub)
                        a.update(trigger_type="timer-trigger", handler=f"{p}:{syntax.line(n)}",
                                 name=nc.literal_of(ev.eval(m, args[0])))
                        item = a
                    elif cn == "every" and m.imports_pkg("agenda") is not None and args:
                        a = self._expr_attrs(ctx, ev.eval(m, args[0]), sub)
                        a.update(trigger_type="agenda", handler=f"{p}:{syntax.line(n)}",
                                 name=nc.literal_of(ev.eval(m, args[1])) if len(args) > 1 else None)
                        item = a
                elif n.type == "new_expression" and syntax.text(
                        n.child_by_field_name("constructor")) == "CronJob" and \
                        m.imports_pkg("cron") is not None:
                    args = nc.args_of(n)
                    if args and args[0].type != "object":
                        a = self._expr_attrs(ctx, ev.eval(m, args[0]), sub)
                        a.update(trigger_type="cron", handler=f"{p}:{syntax.line(n)}")
                        item = a
                elif n.type == "decorator":
                    t = syntax.text(n)
                    if t.startswith("@Cron(") or t.startswith("@Interval("):
                        ann = syntax.annotation_of(n, m.lang)
                        da = nc.decorator_args(ann)
                        meth = n.next_named_sibling
                        while meth is not None and meth.type == "decorator":
                            meth = meth.next_named_sibling
                        cls = nc.enclosing_class(n)
                        hname = (syntax.text(cls.child_by_field_name("name")) + "." +
                                 nc._member_name(meth)) if cls is not None and meth is not None \
                            else None
                        if ann.name == "Cron" and da:
                            raw = syntax.text(da[0])
                            v = ev.eval(m, da[0])
                            a = self._expr_attrs(ctx, v, sub)
                            if a["expression_from"] is None and raw.startswith("CronExpression."):
                                a.update(expression=raw, expression_from="literal")
                            tz = None
                            if len(da) > 1 and da[1].type == "object":
                                tz = nc.literal_of(ev.eval(m, self._pair_node(da[1], "timeZone")))
                            a.update(trigger_type="cron", timezone=tz)
                        elif ann.name == "Interval" and da:
                            a = self._expr_attrs(ctx, ev.eval(m, da[-1]), sub)
                            a.update(trigger_type="interval")
                        else:
                            continue
                        a.update(handler=f"{p}:{syntax.line(n)}", name=hname)
                        item = a
                if item is None:
                    continue
                if item.get("expression_from") is None:
                    unresolved.add(p)
                out.append(make_item("scheduled_job", sub, None, item,
                                     [ctx.evidence(p, int(item["handler"].rsplit(":", 1)[1]))],
                                     self, "high" if item.get("expression") else "medium"))
        return out

    # ---- swagger -------------------------------------------------------------------------
    def _swagger(self, ctx, proj, paths) -> list:
        ev = proj.evaluator
        out = []
        for p in paths:
            if "SwaggerModule" not in (ctx.read_text(p) or ""):
                continue
            m = proj.module(p)
            if m is None:
                continue
            for n in syntax.walk(m.root):
                if n.type == "call_expression" and syntax.text(
                        n.child_by_field_name("function")).replace(" ", "") == "SwaggerModule.setup":
                    a = nc.args_of(n)
                    lit = nc.literal_of(ev.eval(m, a[0])) if a else None
                    out.append(generated_contract_item(ctx, self, "nestjs-swagger",
                                                       pathnorm.display_path(lit) if lit else None,
                                                       p, syntax.line(n)))
        return out

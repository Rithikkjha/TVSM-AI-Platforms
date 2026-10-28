"""``dotnet.aspnet`` extractor (docs/EXTRACTORS.md): ASP.NET Core controllers + minimal APIs,
Azure Functions (isolated worker / in-process) triggers, HttpClient / IHttpClientFactory / Refit /
RestSharp / Flurl outbound calls, Azure Service Bus SDK + MassTransit messaging, EF Core / Dapper /
ADO.NET data access, ``IConfiguration`` / ``IOptions<T>`` / environment reads, hosted services /
Hangfire / Quartz / TimerTrigger jobs, Swashbuckle generated specs, and schemas for every type the
items reference.

Source files are parsed with tree-sitter (``syntax.py``); values are folded by
``dotnet_symbols.Resolver`` (constants, config keys, env vars, one assignment hop). A file is
``parse: full`` only when its tree has no error nodes and every construct found was resolved.
Test-class files are opened only for outbound calls (``role: tests_target``, D-P4).
"""
from __future__ import annotations

import posixpath
import re

from .. import config_classify as cc
from .. import pathnorm
from ..inventory_schema import make_item
from . import configfmt
from . import syntax as sx
from .base import ExtractResult, Extractor, RepoContext
from .dotnet_symbols import (LANG, CsFile, CsIndex, Resolver, Scope, Seg, Val, arg_expr,
                             arg_name, call_parts, get_index, scope_for)
from .dotnet_types import (is_nullable, is_simple, is_value_type, norm_type, schema_refs,
                           split_generic)
from .shared_manifests import generated_contract_item

VERBS = {"HttpGet": "GET", "HttpPost": "POST", "HttpPut": "PUT", "HttpPatch": "PATCH",
         "HttpDelete": "DELETE", "HttpHead": "HEAD", "HttpOptions": "OPTIONS"}
MAP_VERBS = {"MapGet": "GET", "MapPost": "POST", "MapPut": "PUT", "MapDelete": "DELETE",
             "MapPatch": "PATCH", "MapMethods": None}
HTTP_CALLS = {"GetAsync": "GET", "GetStringAsync": "GET", "GetStreamAsync": "GET",
              "GetByteArrayAsync": "GET", "GetFromJsonAsync": "GET", "PostAsync": "POST",
              "PostAsJsonAsync": "POST", "PutAsync": "PUT", "PutAsJsonAsync": "PUT",
              "PatchAsync": "PATCH", "PatchAsJsonAsync": "PATCH", "DeleteAsync": "DELETE",
              "DeleteFromJsonAsync": "DELETE", "SendAsync": None, "Send": None}
RETURN_STATUS = {"Ok": 200, "Created": 201, "CreatedAtAction": 201, "CreatedAtRoute": 201,
                 "Accepted": 202, "AcceptedAtAction": 202, "AcceptedAtRoute": 202,
                 "NoContent": 204, "BadRequest": 400, "ValidationProblem": 400,
                 "Unauthorized": 401, "Forbid": 403, "NotFound": 404, "Conflict": 409,
                 "UnprocessableEntity": 422, "Problem": 500}
HTTP_STATUS_NAMES = {"OK": 200, "Created": 201, "Accepted": 202, "NoContent": 204,
                     "MovedPermanently": 301, "Found": 302, "NotModified": 304,
                     "BadRequest": 400, "Unauthorized": 401, "Forbidden": 403, "NotFound": 404,
                     "MethodNotAllowed": 405, "Conflict": 409, "Gone": 410,
                     "UnprocessableEntity": 422, "TooManyRequests": 429,
                     "InternalServerError": 500, "NotImplemented": 501, "BadGateway": 502,
                     "ServiceUnavailable": 503, "GatewayTimeout": 504}
PARAM_SOURCES = {"FromRoute": "path", "FromQuery": "query", "FromHeader": "header",
                 "FromBody": "body", "FromForm": "form"}
SKIP_PARAM_TYPES = {"CancellationToken", "HttpContext", "HttpRequest", "HttpResponse",
                    "ClaimsPrincipal", "FunctionContext", "ILogger", "HttpRequestData"}
EF_STORES = {"UseSqlServer": "mssql", "UseAzureSql": "mssql", "UseNpgsql": "postgres",
             "UseMySql": "mysql", "UseMySQL": "mysql", "UseOracle": "oracle",
             "UseSqlite": "sqlite", "UseCosmos": "cosmos", "UseInMemoryDatabase": "other"}
ADO_STORES = {"SqlConnection": "mssql", "NpgsqlConnection": "postgres",
              "MySqlConnection": "mysql", "OracleConnection": "oracle",
              "SqliteConnection": "sqlite"}
DAPPER = {"Query", "QueryAsync", "QueryFirst", "QueryFirstAsync", "QueryFirstOrDefault",
          "QueryFirstOrDefaultAsync", "QuerySingle", "QuerySingleAsync", "QuerySingleOrDefault",
          "QuerySingleOrDefaultAsync", "QueryMultiple", "QueryMultipleAsync", "Execute",
          "ExecuteAsync", "ExecuteScalar", "ExecuteScalarAsync", "ExecuteReader",
          "ExecuteReaderAsync"}
EF_RAW = {"FromSqlRaw", "FromSqlInterpolated", "FromSql", "ExecuteSqlRaw", "ExecuteSqlRawAsync",
          "ExecuteSqlInterpolated", "ExecuteSqlInterpolatedAsync", "SqlQueryRaw", "SqlQuery"}
SB_LIB = "Azure.Messaging.ServiceBus"
_SQL_TABLE = re.compile(r"(?i)\b(FROM|JOIN|INTO|UPDATE|DELETE\s+FROM|MERGE\s+INTO)\s+"
                        r"([\[\]\w.\"]+)")
_SP = re.compile(r"(?i)^\s*(?:EXEC(?:UTE)?\s+)([\[\]\w.]+)")
_TOKEN = re.compile(r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")
_FUNC_PLACEHOLDER = re.compile(r"^%([A-Za-z0-9_.:\-]+)%$")
_CONSTRAINT_TYPES = {"int": "integer", "long": "integer", "bool": "boolean",
                     "datetime": "datetime", "decimal": "number", "double": "number",
                     "float": "number", "guid": "uuid"}
_DTO_BODY_TYPES = {"object", "string", "JObject", "JsonElement", "dynamic", "JToken"}


def _route_tokens(template: str) -> list[tuple[str, bool, str | None]]:
    """``{id:int}`` / ``{x?}`` / ``{**slug}`` / ``{p=1}`` -> [(name, optional, type)]."""
    out = []
    for m in _TOKEN.finditer(template or ""):
        inner = m.group(1).lstrip("*")
        nm = re.match(r"[A-Za-z_]\w*", inner)
        if not nm:
            continue
        rest = inner[nm.end():]
        optional = "?" in rest.split("(")[0] or "=" in rest
        ctype = None
        if rest.startswith(":"):
            c = re.match(r":([A-Za-z]+)", rest)
            ctype = _CONSTRAINT_TYPES.get(c.group(1).lower(), "string") if c else None
        out.append((nm.group(0), optional, ctype))
    return out


def _status(v) -> int | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    name = getattr(v, "name", None) or (v if isinstance(v, str) else None)
    if not name:
        return None
    m = re.search(r"Status(\d{3})", name)
    if m:
        return int(m.group(1))
    if re.fullmatch(r"\d{3}", name):
        return int(name)
    return HTTP_STATUS_NAMES.get(name.split(".")[-1])


class DotnetAspnetExtractor(Extractor):
    id = "dotnet.aspnet"
    stacks = ("dotnet",)
    extractor_version = sx.versioned("0.1.1", "csharp")
    status = "implemented"

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        run = _Run(self, ctx, get_index(ctx), subproject)
        for e in ctx.files(subproject, lambda e: e["path"].endswith(".cs")):
            run.file(e, res)
        run.finish(res)
        # declared top-level type names for the external-systems matcher (sdk_symbols)
        mine = {cf.path for cf in run._sub_files()}
        for _name, cands in sorted(run.idx.types.items()):
            for p, td in cands:
                if p in mine and td.outer is None:
                    ctx.note_sdk_symbol(td.name, p, td.line)
        return res


class _Run:
    def __init__(self, ex: Extractor, ctx: RepoContext, idx: CsIndex, sub: str | None):
        self.ex, self.ctx, self.idx, self.sub = ex, ctx, idx, sub
        self.res = Resolver(idx, ctx)
        self.items: list = []
        self.schema_refs: list[tuple[str, str, int]] = []   # (type text, file, line)
        self.stores: dict[str, object] = {}
        self.pending_sps: list[tuple[dict, object]] = []
        self.reads: dict[tuple[str, str], list] = {}
        self.enums = {n for n, cands in idx.types.items() if any(td.kind == "enum"
                                                                  for _, td in cands)}
        self.path_base = self._path_base()
        self.route_prefix = self._route_prefix()
        self.unresolved: list[str] = []
        self.cf: CsFile | None = None

    # ---- helpers ---------------------------------------------------------------------------
    def ev(self, path: str, line: int):
        return self.ctx.evidence(path, line)

    def sub_of(self, path: str) -> str:
        return self.ctx.subproject_of(path)

    def item(self, kind, path, attrs, lines, confidence="high", key=None):
        evs = [self.ev(p, ln) for p, ln in sorted(set(lines))]
        it = make_item(kind, self.sub_of(path), key, attrs, evs, self.ex, confidence)
        self.items.append(it)
        return it

    def miss(self, why: str) -> None:
        self.unresolved.append(why)

    def _sub_files(self):
        return [cf for p, cf in self.idx.files.items()
                if (self.sub is None or self.sub_of(p) == self.sub) and not cf.is_test]

    def _path_base(self) -> tuple[str, int, str] | None:
        for cf in self._sub_files():
            if "UsePathBase" not in cf.text:
                continue
            for inv in sx.find_all(cf.parsed.root, "invocation_expression"):
                _, nm, _, args = call_parts(inv)
                if nm == "UsePathBase" and args:
                    v = self.res.resolve(arg_expr(args[0]), scope_for(cf, inv))
                    if v.is_literal:
                        return v.text, sx.line(inv), cf.path
        return None

    def _route_prefix(self) -> str:
        hosts = [p for p in self.ctx.paths() if posixpath.basename(p) == "host.json"]
        hosts.sort(key=lambda p: (self.sub_of(p) != self.sub, p))
        for h in hosts:
            r = configfmt.parse_jsonc(self.ctx.read_text(h) or "")
            data = r.data if r.ok and isinstance(r.data, dict) else {}
            http = ((data.get("extensions") or {}).get("http") or {}) if isinstance(
                data.get("extensions"), dict) else {}
            if isinstance(http, dict) and isinstance(http.get("routePrefix"), str):
                return http["routePrefix"]
            return "api"
        return "api"

    def ann_str(self, a, *names, pos=0, td=None) -> str | None:
        v = a.args.get(*names, pos=pos)
        if v is None:
            return None
        if isinstance(v, str):
            return v

        def lookup(name):
            c = self.idx.const(name, td)
            return sx.value_of(c[0], LANG) if c is not None else None
        s, unresolved = sx.resolve_value(v, lookup)
        if unresolved or s is None:
            self.miss(f"attribute value {a.name}")
            return None
        return s

    def config_values(self, key: str) -> dict:
        return self.ctx.config.public_values(key, self.sub)

    def schedule_values(self, key: str) -> dict:
        """{env: cron/interval expression} for a schedule setting. Schedules are classifier
        rule 6 (``hidden``) values, so they are recorded only when neither the key nor the value
        is secret-like and the value has the shape of a cron / TimeSpan expression."""
        out = dict(self.config_values(key))
        if cc.key_is_secret(key):
            return out
        for env in self.ctx.config.resolved_envs(key, self.sub):
            v = self.ctx.config.resolve_key(key, env, self.sub).value
            if isinstance(v, str) and not cc.value_is_secret(v) and \
                    re.fullmatch(r"[0-9*/,?LW#A-Z\- ]{1,60}|\d{1,2}:\d{2}:\d{2}", v.strip()) and \
                    (len(v.split()) in (5, 6, 7) or ":" in v):
                out.setdefault(env, v.strip())
        return out

    def raw_value(self, kind: str, key: str):
        """Raw (never written) value of a config key / env var, for identity parsing only."""
        if kind == "config":
            r = self.ctx.config.resolve_key(key, "default", self.sub)
            return r.value
        if kind == "env":
            ds = self.ctx.config.env_defs(key, self.sub) or self.ctx.config.defs(key, self.sub)
            for d in ds:
                if d.env == "default" or len(ds) == 1:
                    return self.ctx.config.resolve(d.value, "default", self.sub).value
        return None

    # ---- per file --------------------------------------------------------------------------
    def file(self, e: dict, res: ExtractResult) -> None:
        path = e["path"]
        cf = self.idx.files.get(path)
        if cf is None:
            res.touch(path, "partial", "not parsed")
            return
        self.cf = cf
        self.unresolved = []
        self.invs = sx.find_all(cf.parsed.root, "invocation_expression")
        self.creations = sx.find_all(cf.parsed.root, ("object_creation_expression",
                                                      "implicit_object_creation_expression"))
        err = f"tree-sitter: {cf.parsed.errors} error nodes" if cf.parsed.has_error else None
        if cf.is_test:
            self.outbound(cf, "tests_target")
            res.touch(path, "partial", err)
            return
        self.controllers(cf)
        self.minimal_apis(cf)
        self.functions(cf)
        if "ServiceBus" in cf.text:
            self.servicebus(cf)
        if "MassTransit" in cf.text:
            self.masstransit(cf)
        self.outbound(cf, "runtime")
        if "Refit" in cf.text:
            self.refit(cf)
        if "RestSharp" in cf.text or "RestRequest" in cf.text:
            self.restsharp(cf)
        if "Flurl" in cf.text:
            self.flurl(cf)
        self.data_access(cf)
        self.config_reads(cf)
        self.scheduled(cf)
        self.contracts(cf)
        res.touch(path, "partial" if (err or self.unresolved) else "full", err)

    # ---- inbound: controllers --------------------------------------------------------------
    def _auth(self, anns, td=None) -> tuple[str | None, str | None, bool | None]:
        for a in anns:
            if a.name == "AllowAnonymous":
                return "none", sx.text(a.node), True
        for a in anns:
            if a.name != "Authorize":
                continue
            roles = self.ann_str(a, "Roles", pos=None, td=td)
            policy = self.ann_str(a, "Policy", pos=0, td=td)
            schemes = self.ann_str(a, "AuthenticationSchemes", pos=None, td=td) or ""
            if roles:
                auth = "roles:" + ",".join(r.strip() for r in roles.split(","))
            elif policy:
                auth = f"policy:{policy}"
            elif re.search(r"(?i)bearer|jwt", schemes):
                auth = "bearer-jwt"
            elif re.search(r"(?i)basic", schemes):
                auth = "basic"
            elif re.search(r"(?i)api.?key", schemes):
                auth = "api-key"
            else:
                auth = self.idx.auth_default or "unknown"
            return auth, sx.text(a.node), None
        return None, None, None

    def controllers(self, cf: CsFile) -> None:
        for td in cf.types:
            if td.kind != "class":
                continue
            names = {a.name for a in td.annotations}
            bases = {split_generic(b)[0] for b in td.extends}
            if not ("ApiController" in names or "Route" in names or td.name.endswith("Controller")
                    or bases & {"Controller", "ControllerBase"}):
                continue
            api = "ApiController" in names
            ctrl = re.sub(r"Controller$", "", td.name)
            area = next((self.ann_str(a, "areaName", pos=0, td=td) for a in td.annotations
                         if a.name == "Area"), None)
            cls_routes = [(t, a.line) for a in td.annotations if a.name == "Route"
                          for t in [self.ann_str(a, "template", "Template", pos=0, td=td)]
                          if t is not None]
            cls_auth = self._auth(td.annotations, td)
            cls_dep = "Obsolete" in names
            for m in sx.methods(td, LANG):
                if m.kind != "method":
                    continue
                mnames = {a.name for a in m.annotations}
                if "NonAction" in mnames or not (mnames & (set(VERBS) | {"Route",
                                                                          "AcceptVerbs"})):
                    continue
                self._action(cf, td, m, api, ctrl, area, cls_routes, cls_auth,
                             cls_dep or "Obsolete" in mnames)

    def _action(self, cf, td, m, api, ctrl, area, cls_routes, cls_auth, deprecated) -> None:
        combos: list[tuple[str | None, str | None, list[int]]] = []
        routes = [(self.ann_str(a, "template", "Template", pos=0, td=td), a.line)
                  for a in m.annotations if a.name == "Route"]
        routes = [r for r in routes if r[0] is not None]
        verbs = []
        for a in m.annotations:
            if a.name in VERBS:
                verbs.append((VERBS[a.name], self.ann_str(a, "template", "Template", pos=0, td=td)
                              if (a.args.positional or a.args.named.get("template")
                                  or a.args.named.get("Template")) else None, a.line))
            elif a.name == "AcceptVerbs":
                for v in a.args.positional:
                    if isinstance(v, str):
                        verbs.append((v.upper(), self.ann_str(a, "Route", pos=None, td=td),
                                      a.line))
        if verbs:
            for verb, t, ln in verbs:
                if t is not None:
                    combos.append((verb, t, [ln]))
                elif routes:
                    combos += [(verb, rt, [ln, rl]) for rt, rl in routes]
                else:
                    combos.append((verb, None, [ln]))
        else:
            combos = [(None, rt, [rl]) for rt, rl in routes]
        auth, auth_raw, anon = self._auth(m.annotations, td)
        if auth is None:
            auth, auth_raw, anon = cls_auth
        responses, resp_medium = self._responses(cf, td, m)
        for verb, tmpl, lines in combos:
            if tmpl is not None and (tmpl.startswith("/") or tmpl.startswith("~/")):
                paths = [(tmpl.lstrip("~"), [])]
            elif cls_routes:
                paths = [(pathnorm.join(ct, tmpl or ""), [cl]) for ct, cl in cls_routes]
            else:
                paths = [(tmpl or "", [])]
            for raw, extra in paths:
                raw = re.sub(r"(?i)\[controller\]", ctrl, raw)
                raw = re.sub(r"(?i)\[action\]", re.sub(r"Async$", "", m.name), raw)
                if area is not None:
                    raw = re.sub(r"(?i)\[area\]", area, raw)
                ev_lines = [(cf.path, ln) for ln in lines + extra]
                if self.path_base:
                    raw = pathnorm.join(self.path_base[0], raw)
                    ev_lines.append((self.path_base[2], self.path_base[1]))
                raw = raw if raw.startswith("/") else "/" + raw
                params, request, req_medium = self._params(cf, td, m, raw, api)
                path = pathnorm.display_path(raw)
                attrs = {"method": verb, "path": path, "path_raw": raw,
                         "path_params_normalized": pathnorm.normalize(path),
                         "handler": f"{td.name}.{m.name}", "framework": "aspnet-core",
                         "params": params, "request": request, "responses": responses,
                         "auth": auth, "auth_raw": auth_raw, "allow_anonymous": anon,
                         "deprecated": True if deprecated else None, "contract_file": None,
                         "context_path_by_env": {}}
                conf = "medium" if (req_medium or resp_medium) else "high"
                self.item("inbound_http", cf.path, attrs, ev_lines, conf)

    def _params(self, cf, td, m, raw, api) -> tuple[list, str | None, bool]:
        tokens = _route_tokens(raw)
        tok = {n.lower(): (n, opt, ty) for n, opt, ty in tokens}
        out, request, medium, seen = [], None, False, set()
        for p in m.params:
            names = {a.name for a in p.annotations}
            ptype = (p.type or "").strip()
            base = split_generic(ptype.rstrip("?"))[0]
            if "FromServices" in names or base in SKIP_PARAM_TYPES or "FromKeyedServices" in names:
                continue
            src = next((PARAM_SOURCES[a.name] for a in p.annotations if a.name in PARAM_SOURCES),
                       None)
            nm = p.name
            for a in p.annotations:
                if a.name in PARAM_SOURCES:
                    alias = self.ann_str(a, "Name", pos=None, td=td)
                    nm = alias or nm
            if src is None:
                if base in ("IFormFile", "IFormFileCollection"):
                    src = "form"
                elif nm.lower() in tok:
                    src = "path"
                elif is_simple(ptype, self.enums):
                    src = "query"
                else:
                    src = "body" if api else "query"
            ty = norm_type(ptype)
            if src == "path":
                t = tok.get(nm.lower())
                ty = ty or (t[2] if t else None) or "string"
                required = not (t[1] if t else False)
                seen.add(nm.lower())
            else:
                required = not (p.optional or is_nullable(ptype))
            out.append({"name": nm, "in": src, "type": ty, "required": required})
            if src == "body":
                refs = schema_refs(ptype)
                if base in _DTO_BODY_TYPES and m.body is not None:
                    found = sorted({g for inv in sx.find_all(m.body, "invocation_expression")
                                    for _, n2, gs, _ in [call_parts(inv)]
                                    if n2 in ("DeserializeObject", "Deserialize") and gs
                                    for g in gs[:1]})
                    if len(found) == 1:
                        request, medium = norm_type(found[0]), True
                        self.schema_refs.append((found[0], cf.path, m.line))
                else:
                    request = ty if refs else (ty if ty not in (None, "object") else None)
                    for r in refs:
                        self.schema_refs.append((r, cf.path, p.line))
        for n, opt, ctype in tokens:
            if n.lower() not in seen:
                out.append({"name": n, "in": "path", "type": ctype or "string",
                            "required": not opt})
        return out, request, medium

    def _responses(self, cf, td, m) -> tuple[list, bool]:
        out: dict[int, dict] = {}
        for a in m.annotations:
            if a.name not in ("ProducesResponseType", "SwaggerResponse", "ProducesDefaultResponseType"):
                continue
            status, schema = None, None
            g = re.search(r"<\s*([\w.<>\[\], ]+)\s*>$", a.full_name)
            if g:
                schema = g.group(1)
            for v in list(a.args.positional) + [a.args.named.get(k) for k in
                                                 ("statusCode", "StatusCode", "type", "Type")]:
                if isinstance(v, sx.TypeRef):
                    schema = v.name
                elif status is None and _status(v) is not None:
                    status = _status(v)
            if status is None:
                continue
            desc = a.args.get("description", "Description")
            if not isinstance(desc, str):
                desc = next((x for x in a.args.positional[1:] if isinstance(x, str)), None)
            out.setdefault(status, {"status": status, "schema": norm_type(schema) if schema
                                    else None, "when": desc, "from": "annotation"})
            if schema:
                self.schema_refs += [(r, cf.path, a.line) for r in schema_refs(schema)]
        rt = (m.return_type or "").strip()
        name, args = split_generic(rt)
        while name in ("Task", "ValueTask") and args:
            rt = args[0]
            name, args = split_generic(rt)
        inner = None
        if name == "ActionResult" and args:
            inner = args[0]
        elif name not in ("IActionResult", "ActionResult", "IResult", "void", "Task",
                          "ValueTask", "HttpResponseMessage") and norm_type(rt):
            inner = rt
        if inner and 200 not in out:
            out[200] = {"status": 200, "schema": norm_type(inner), "when": None,
                        "from": "return-type"}
            self.schema_refs += [(r, cf.path, m.line) for r in schema_refs(inner)]
        from_return = False
        rets = [c for c in m.node.children if c.type == "arrow_expression_clause"]
        if m.body is not None:
            rets += sx.find_all(m.body, "return_statement")
        if rets:
            for ret in rets:
                kids = sx.named_children(ret)
                if not kids or kids[0].type != "invocation_expression":
                    continue
                recv, nm, _, args2 = call_parts(kids[0])
                if recv is not None and sx.text(recv) not in ("this", "base", "Results",
                                                              "TypedResults"):
                    continue
                status = RETURN_STATUS.get(nm)
                if nm == "StatusCode" and args2:
                    status = _status(sx.value_of(arg_expr(args2[0]), LANG))
                if status is None or status in out:
                    continue
                schema = None
                for a2 in args2:
                    ex = arg_expr(a2)
                    if ex is not None and ex.type == "object_creation_expression":
                        schema = sx.text(ex.child_by_field_name("type"))
                if schema:
                    self.schema_refs += [(r, cf.path, sx.line(ret)) for r in schema_refs(schema)]
                out[status] = {"status": status, "schema": norm_type(schema) if schema else None,
                               "when": None, "from": "return"}
                from_return = True
        resp = [out[k] for k in sorted(out)]
        only_return = from_return and all(r["from"] == "return" for r in resp)
        return resp, only_return

    # ---- inbound: minimal APIs -------------------------------------------------------------
    def _group_prefix(self, recv, scope, depth=0) -> tuple[str, list[int], str | None]:
        if recv is None or depth > 3:
            return "", [], None
        auth = None
        node = recv
        if node.type == "identifier":
            init = self.res._local(sx.text(node), scope)
            if init is None:
                return "", [], None
            node = init
        lines: list[int] = []
        while node is not None and node.type == "invocation_expression":
            r2, nm, _, args = call_parts(node)
            if nm == "MapGroup" and args:
                v = self.res.resolve(arg_expr(args[0]), scope)
                pre, l2, a2 = self._group_prefix(r2, scope, depth + 1)
                return pathnorm.join(pre, v.text or ""), l2 + [sx.line(node)], auth or a2
            if nm == "RequireAuthorization":
                auth = self._policy_auth(args, scope)
            elif nm == "AllowAnonymous":
                auth = "none"
            node = r2
        return "", lines, auth

    def _policy_auth(self, args, scope) -> str:
        if args:
            v = self.res.resolve(arg_expr(args[0]), scope)
            if v.is_literal:
                return f"policy:{v.text}"
        return self.idx.auth_default or "unknown"

    def minimal_apis(self, cf: CsFile) -> None:
        if "Map" not in cf.text:
            return
        for inv in self.invs:
            recv, name, _, args = call_parts(inv)
            if name not in MAP_VERBS or recv is None or len(args) < 2:
                continue
            scope = scope_for(cf, inv)
            tv = self.res.resolve(arg_expr(args[0]), scope)
            if not tv.is_literal:
                self.miss("minimal api route")
                continue
            verbs = [MAP_VERBS[name]]
            handler_arg = args[1]
            if name == "MapMethods":
                mv = sx.value_of(arg_expr(args[1]), LANG)
                verbs = [x.upper() for x in mv if isinstance(x, str)] if isinstance(mv, list) \
                    else [None]
                handler_arg = args[2] if len(args) > 2 else None
            prefix, plines, gauth = self._group_prefix(recv, scope)
            raw = pathnorm.join(prefix, tv.text)
            if self.path_base:
                raw = pathnorm.join(self.path_base[0], raw)
            auth = None
            cur = inv
            while cur.parent is not None and cur.parent.type == "member_access_expression" and \
                    cur.parent.parent is not None and \
                    cur.parent.parent.type == "invocation_expression":
                _, nm2, _, a2 = call_parts(cur.parent.parent)
                if nm2 == "RequireAuthorization":
                    auth = self._policy_auth(a2, scope)
                elif nm2 == "AllowAnonymous":
                    auth = "none"
                cur = cur.parent.parent
            auth = auth or gauth
            hx = arg_expr(handler_arg)
            handler = f"{cf.path}:{sx.line(hx)}" if hx is not None and hx.type in (
                "lambda_expression", "anonymous_method_expression") else (sx.text(hx) if hx
                                                                           is not None else None)
            tokens = _route_tokens(raw)
            tok = {n.lower(): (n, o, t) for n, o, t in tokens}
            params, request, seen = [], None, set()
            if hx is not None and hx.type == "lambda_expression":
                for p in sx.params_of(hx, LANG):
                    names = {a.name for a in p.annotations}
                    base = split_generic((p.type or "").rstrip("?"))[0]
                    if "FromServices" in names or base in SKIP_PARAM_TYPES or not p.type or \
                            re.match(r"^I[A-Z]", base):
                        continue
                    src = next((PARAM_SOURCES[a.name] for a in p.annotations
                                if a.name in PARAM_SOURCES), None)
                    if src is None:
                        src = "path" if p.name.lower() in tok else (
                            "query" if is_simple(p.type, self.enums) else "body")
                    if src == "path":
                        seen.add(p.name.lower())
                    params.append({"name": p.name, "in": src, "type": norm_type(p.type),
                                   "required": not (p.optional or is_nullable(p.type))
                                   if src != "path" else True})
                    if src == "body":
                        request = norm_type(p.type)
                        self.schema_refs += [(r, cf.path, sx.line(inv))
                                             for r in schema_refs(p.type)]
            for n, opt, ctype in tokens:
                if n.lower() not in seen:
                    params.append({"name": n, "in": "path", "type": ctype or "string",
                                   "required": not opt})
            path = pathnorm.display_path(raw)
            for verb in verbs:
                attrs = {"method": verb, "path": path, "path_raw": raw,
                         "path_params_normalized": pathnorm.normalize(path), "handler": handler,
                         "framework": "aspnet-minimal", "params": params, "request": request,
                         "responses": [], "auth": auth, "auth_raw": None,
                         "allow_anonymous": True if auth == "none" else None, "deprecated": None,
                         "contract_file": None, "context_path_by_env": {}}
                lines = [(cf.path, sx.line(inv))] + [(cf.path, ln) for ln in plines]
                if self.path_base:
                    lines.append((self.path_base[2], self.path_base[1]))
                self.item("inbound_http", cf.path, attrs, lines)

    # ---- Azure Functions -------------------------------------------------------------------
    def functions(self, cf: CsFile) -> None:
        if "Function" not in cf.text:
            return
        for td in cf.types:
            for m in sx.methods(td, LANG):
                fa = next((a for a in m.annotations if a.name in ("Function", "FunctionName")),
                          None)
                if fa is None:
                    continue
                fname = self.ann_str(fa, "name", pos=0, td=td) or m.name
                for p in m.params:
                    for a in p.annotations:
                        self._trigger(cf, td, m, fa, fname, p, a)
                for a in m.annotations:
                    if a.name in ("ServiceBusOutput", "ServiceBus"):
                        self._sb_binding(cf, td, m, fa, a, "publish", None)

    def _trigger(self, cf, td, m, fa, fname, p, a) -> None:
        lines = [(cf.path, fa.line), (cf.path, a.line)]
        if a.name == "HttpTrigger":
            pos = list(a.args.positional)
            level = pos[0] if pos and isinstance(pos[0], sx.Ref) else a.args.named.get(
                "AuthLevel")
            methods = [x.upper() for x in pos if isinstance(x, str)] or [None]
            route = self.ann_str(a, "Route", pos=None, td=td)
            route = fname if route is None else route
            raw = pathnorm.join(self.route_prefix, route)
            lvl = getattr(level, "name", "") or ""
            auth = ("none" if lvl.endswith("Anonymous") else
                    "api-key" if re.search(r"(Function|Admin|System)$", lvl) else
                    "unknown" if lvl else None)
            params = [{"name": n, "in": "path", "type": t or "string", "required": not o}
                      for n, o, t in _route_tokens(raw)]
            request = None
            if m.body is not None:
                found = sorted({g for inv in sx.find_all(m.body, "invocation_expression")
                                for _, n2, gs, _ in [call_parts(inv)]
                                if n2 in ("ReadFromJsonAsync", "ReadAsAsync") and gs
                                for g in gs[:1]})
                if len(found) == 1:
                    request = norm_type(found[0])
                    self.schema_refs.append((found[0], cf.path, a.line))
            path = pathnorm.display_path(raw)
            for verb in methods:
                attrs = {"method": verb, "path": path, "path_raw": raw,
                         "path_params_normalized": pathnorm.normalize(path),
                         "handler": f"{td.name}.{m.name}", "framework": "azure-functions",
                         "params": params, "request": request, "responses": [],
                         "auth": auth, "auth_raw": lvl or None,
                         "allow_anonymous": True if auth == "none" else None, "deprecated": None,
                         "contract_file": None, "context_path_by_env": {}}
                self.item("inbound_http", cf.path, attrs, lines)
        elif a.name in ("ServiceBusTrigger", "ServiceBus"):
            self._sb_binding(cf, td, m, fa, a, "subscribe", p)
        elif a.name in ("QueueTrigger", "EventHubTrigger", "EventGridTrigger", "KafkaTrigger",
                        "RabbitMQTrigger"):
            broker = {"QueueTrigger": "storage-queue", "EventHubTrigger": "event-hub",
                      "EventGridTrigger": "event-grid", "KafkaTrigger": "kafka",
                      "RabbitMQTrigger": "rabbitmq"}[a.name]
            etype = {"storage-queue": "queue", "event-hub": "event-hub", "kafka": "kafka-topic",
                     "rabbitmq": "queue", "event-grid": None}[broker]
            first = a.args.get("queueName", "eventHubName", "QueueName", "EventHubName",
                               "topic", "Topic", pos=0) if a.name != "EventGridTrigger" else None
            if a.name == "KafkaTrigger":
                first = a.args.get("topic", "Topic", pos=1)
            self._msg(cf, "subscribe", broker, self._name_val(first), etype, lines,
                      handler=f"{cf.path}:{a.line}", trigger="function-trigger",
                      library="Microsoft.Azure.Functions.Worker", payload=p.type,
                      allow_none=a.name == "EventGridTrigger")
        elif a.name == "TimerTrigger":
            sched = a.args.get("schedule", "Schedule", pos=0)
            expr, efrom, rv = None, None, {}
            if isinstance(sched, str):
                mm = _FUNC_PLACEHOLDER.match(sched)
                if mm:
                    efrom = f"config:{mm.group(1)}"
                    rv = self.schedule_values(mm.group(1))
                    expr = rv.get("default") or (next(iter(rv.values())) if len(set(
                        rv.values())) == 1 else None)
                else:
                    expr, efrom = sched, "literal"
            attrs = {"trigger_type": "timer-trigger", "expression": expr,
                     "expression_from": efrom, "resolved_values": rv, "timezone": None,
                     "handler": f"{cf.path}:{a.line}", "name": fname}
            if expr is None:
                self.miss("timer schedule")
            self.item("scheduled_job", cf.path, attrs, lines,
                      "high" if expr is not None and efrom == "literal" else "medium")

    def _name_val(self, v):
        """Attribute value -> ('literal', text) / ('config', key) / ('unknown', None)."""
        if isinstance(v, str):
            mm = _FUNC_PLACEHOLDER.match(v)
            if mm:
                return ("config", mm.group(1))
            if "%" in v:
                return ("unknown", None)
            return ("literal", v)
        if v is None:
            return None
        if isinstance(v, sx.Ref):
            c = self.idx.const(v.name, None)
            if c is not None:
                s, un = sx.resolve_value(sx.value_of(c[0], LANG), lambda n: (
                    sx.value_of(self.idx.const(n)[0], LANG) if self.idx.const(n) else None))
                if s is not None and not un:
                    return self._name_val(s)
        return ("unknown", None)

    def _sb_binding(self, cf, td, m, fa, a, direction, p) -> None:
        pos = list(a.args.positional)
        first = a.args.get("queueOrTopicName", "QueueName", "TopicName", pos=0)
        second = a.args.get("subscriptionName", "SubscriptionName", pos=1)
        nv = self._name_val(first)
        sv = self._name_val(second) if (second is not None and isinstance(second, (str, sx.Ref))
                                        and not isinstance(second, bool)) else None
        sub_name = None
        if sv is not None:
            if sv[0] == "literal":
                sub_name = sv[1]
            elif sv[0] == "config":
                vals = self.config_values(sv[1])
                sub_name = vals.get("default") or (next(iter(vals.values())) if len(
                    set(vals.values())) == 1 else f"config:{sv[1]}")
        etype = "topic" if sub_name or a.args.get("TopicName") is not None else "queue"
        props = {}
        if a.args.get("IsSessionsEnabled") is True:
            props["session_id"] = "sessions-enabled"
        err = {}
        if m.body is not None and "DeadLetterMessageAsync" in sx.text(m.body):
            err["dead_letter"] = True
        lines = [(cf.path, fa.line), (cf.path, a.line)]
        self._msg(cf, direction, "azure-service-bus", nv, etype, lines,
                  handler=f"{cf.path}:{a.line}" if direction == "subscribe" else None,
                  published_by=f"{cf.path}:{a.line}" if direction == "publish" else None,
                  trigger="function-trigger" if direction == "subscribe" else None,
                  library="Microsoft.Azure.Functions.Worker.Extensions.ServiceBus",
                  subscription=sub_name, properties=props, error_handling=err,
                  payload=p.type if p is not None else None)

    def _msg(self, cf, direction, broker, nv, etype, lines, handler=None, published_by=None,
             trigger=None, library=None, subscription=None, properties=None, error_handling=None,
             payload=None, namespace=None, message_types=None, allow_none=False,
             medium=False) -> None:
        """messaging item; ``nv`` = (kind, key/text) from ``_name_val`` / ``_val_name``."""
        entity, name_from, name_key, rv = None, None, None, {}
        kind, key = nv if nv else (None, None)
        if kind == "literal" and key and not cc.value_is_secret(key):
            entity, name_from = key, "literal"
        elif kind in ("config", "env"):
            name_from, name_key = f"{kind}:{key}", key
            rv = self.config_values(key)
            entity = rv.get("default") or (next(iter(rv.values())) if len(set(rv.values())) == 1
                                           else None)
        elif not allow_none:
            name_from = "unknown"
            self.miss("dynamic entity name")
        if etype is None and name_key:
            low = name_key.lower()
            etype = "topic" if "topic" in low else "queue" if "queue" in low else None
        pl = norm_type(payload) if payload and split_generic(payload.rstrip("?"))[0] not in (
            "ServiceBusReceivedMessage", "ServiceBusMessage", "string", "byte[]", "BinaryData",
            "Message", "EventGridEvent", "CloudEvent", "QueueMessage", "EventData") else None
        if pl and payload:
            self.schema_refs += [(r, cf.path, lines[-1][1]) for r in schema_refs(payload)]
        attrs = {"direction": direction, "broker": broker, "entity": entity,
                 "entity_type": etype, "namespace": namespace, "name_from": name_from,
                 "name_key": name_key, "resolved_values": rv, "subscription": subscription,
                 "filter": None, "message_types": sorted(set(message_types or [])),
                 "payload": pl, "properties": properties or {}, "published_by": published_by,
                 "handler": handler, "trigger": trigger, "error_handling": error_handling or {},
                 "library": library}
        conf = "medium" if (medium or (entity is None and not allow_none)) else "high"
        self.item("messaging", cf.path, attrs, lines, conf)

    # ---- Service Bus SDK -------------------------------------------------------------------
    def _val_name(self, v: Val):
        kind, key, rest = v.source()
        if kind == "literal" and "{}" not in (v.text or ""):
            return ("literal", v.text)
        if kind in ("config", "env") and rest == "":
            return (kind, key)
        return ("unknown", key if kind == "param" else None)

    def _namespace(self, cf, td) -> str | None:
        node = td.node if td is not None else cf.parsed.root
        for c in sx.find_all(node, ("object_creation_expression",
                                    "implicit_object_creation_expression")):
            ty = sx.text(c.child_by_field_name("type"))
            if c.type == "implicit_object_creation_expression":
                vd = c.parent
                holder = vd.parent if vd is not None else None
                ty = sx.text(holder.child_by_field_name("type")) if holder is not None and \
                    holder.type == "variable_declaration" else ""
            if not ty.endswith("ServiceBusClient"):
                continue
            al = c.child_by_field_name("arguments") or next(
                (x for x in c.children if x.type == "argument_list"), None)
            args = sx.named_children(al) if al is not None else []
            if not args:
                continue
            v = self.res.resolve(arg_expr(args[0]), scope_for(cf, c))
            kind, key, _ = v.source()
            raw = v.text if kind == "literal" else self.raw_value(kind, key) if key else None
            if not raw:
                continue
            ident = cc.parse_store_identity(raw)
            if ident and ident.get("namespace"):
                return ident["namespace"]
            mm = re.search(r"(?:sb://)?([A-Za-z0-9-]+)\.servicebus\.windows\.net", raw)
            if mm:
                return mm.group(1)
        return None

    def _error_handling(self, td_node) -> dict:
        t = sx.text(td_node) if td_node is not None else ""
        out = {}
        mm = re.search(r"MaxDeliveryCount\s*=\s*(\d+)", t)
        if mm:
            out["max_delivery"] = int(mm.group(1))
        if "DeadLetterMessageAsync" in t:
            out["dead_letter"] = True
        if re.search(r"ServiceBusRetryOptions|RetryOptions\s*=", t):
            out["retry"] = True
        return out

    def servicebus(self, cf: CsFile) -> None:
        for inv in self.invs:
            recv, name, _, args = call_parts(inv)
            if name not in ("CreateSender", "CreateProcessor", "CreateSessionProcessor",
                            "CreateReceiver", "AcceptNextSessionAsync", "AcceptSessionAsync"):
                continue
            if recv is None:
                continue
            scope = scope_for(cf, inv)
            vals = []
            for a in args:
                ex = arg_expr(a)
                if ex is None:
                    continue
                ty = self.res.local_type(sx.text(ex), scope)[0] if ex.type == "identifier" \
                    else None
                if "Options" in sx.text(ex) or (ty and "Options" in ty) or arg_name(a):
                    continue
                vals.append(self.res.resolve(ex, scope))
            if not vals:
                continue
            td = scope.td
            ns = self._namespace(cf, td)
            lines = [(cf.path, sx.line(inv))] + [ln for v in vals for ln in v.lines
                                                 if ln[0] == cf.path]
            nv = self._val_name(vals[0])
            if name == "CreateSender":
                etype = None
                if nv[0] == "unknown" and nv[1]:
                    low = nv[1].lower()
                    etype = "topic" if "topic" in low else "queue" if "queue" in low else None
                mtypes, props = self._message_details(scope)
                self._msg(cf, "publish", "azure-service-bus", nv, etype, lines,
                          published_by=f"{cf.path}:{sx.line(inv)}", library=SB_LIB,
                          namespace=ns, message_types=mtypes, properties=props)
                continue
            subscription, etype = None, "queue"
            if len(vals) >= 2:
                etype = "topic"
                sn = self._val_name(vals[1])
                if sn[0] == "literal":
                    subscription = sn[1]
                elif sn[0] in ("config", "env"):
                    sv = self.config_values(sn[1])
                    subscription = sv.get("default") or (next(iter(sv.values())) if len(
                        set(sv.values())) == 1 else f"{sn[0]}:{sn[1]}")
                else:
                    self.miss("dynamic subscription")
            handler = self._handler(cf, td, inv) or f"{cf.path}:{sx.line(inv)}"
            props = {"session_id": "session-processor"} if "Session" in name else {}
            self._msg(cf, "subscribe", "azure-service-bus", nv, etype, lines, handler=handler,
                      trigger="processor" if "Processor" in name else "poll", library=SB_LIB,
                      subscription=subscription, namespace=ns, properties=props,
                      error_handling=self._error_handling(td.node if td else None))

    def _handler(self, cf, td, inv) -> str | None:
        """``proc.ProcessMessageAsync += H`` in the same type -> ``file:line`` of H."""
        target = None
        par = inv.parent
        while par is not None and par.type not in ("variable_declarator", "assignment_expression",
                                                   "expression_statement", "block"):
            par = par.parent
        if par is not None and par.type == "variable_declarator":
            nm = par.child_by_field_name("name") or next(
                (x for x in par.children if x.type == "identifier"), None)
            target = sx.text(nm) if nm is not None else None
        elif par is not None and par.type == "assignment_expression":
            target = sx.text(par.child_by_field_name("left")).replace("this.", "")
        node = td.node if td is not None else cf.parsed.root
        hits = []
        for n in sx.find_all(node, "assignment_expression"):
            left = sx.text(n.child_by_field_name("left"))
            if sx.text(n.child_by_field_name("operator")) != "+=" or \
                    not left.endswith(".ProcessMessageAsync"):
                continue
            recv = left.rsplit(".", 1)[0].replace("this.", "")
            if target is not None and recv != target:
                continue
            hits.append(n)
        if not hits:
            return None
        rhs = hits[0].child_by_field_name("right")
        if rhs is not None and rhs.type == "identifier" and td is not None:
            for m in sx.methods(td, LANG):
                if m.name == sx.text(rhs):
                    nm = m.node.child_by_field_name("name")
                    return f"{cf.path}:{sx.line(nm)}"
        return f"{cf.path}:{sx.line(hits[0])}"

    def _message_details(self, scope: Scope) -> tuple[list, dict]:
        mtypes, props = [], {}
        if scope.body is None or scope.body.type == "compilation_unit":
            return mtypes, props
        for n in sx.find_all(scope.body, "assignment_expression"):
            left = sx.text(n.child_by_field_name("left"))
            right = n.child_by_field_name("right")
            leaf = left.split(".")[-1]
            if leaf == "Subject":
                v = self.res.resolve(right, scope)
                if v.is_literal:
                    mtypes.append(v.text)
            elif leaf in ("SessionId", "CorrelationId", "PartitionKey"):
                key = {"SessionId": "session_id", "CorrelationId": "correlation_id",
                       "PartitionKey": "partition_key"}[leaf]
                props[key] = sx.text(right)[:80]
        for n in sx.find_all(scope.body, ("element_access_expression", "invocation_expression")):
            t = sx.text(n)
            if "ApplicationProperties" not in t:
                continue
            mm = re.match(r'.*ApplicationProperties\s*(?:\[\s*"(\w+)"\s*\]|\.Add\(\s*"(\w+)")', t,
                          re.S)
            if mm:
                pn = mm.group(1) or mm.group(2)
                props.setdefault("app_properties", [])
                if pn not in props["app_properties"]:
                    props["app_properties"].append(pn)
                par = n.parent
                if mm.group(1) and par is not None and par.type == "assignment_expression" and \
                        pn.lower() in ("type", "eventtype", "messagetype"):
                    v = self.res.resolve(par.child_by_field_name("right"), scope)
                    if v.is_literal:
                        mtypes.append(v.text)
        if "app_properties" in props:
            props["app_properties"] = sorted(props["app_properties"])
        return mtypes, props

    def masstransit(self, cf: CsFile) -> None:
        broker = ("rabbitmq" if "UsingRabbitMq" in cf.text else "azure-service-bus")
        for inv in self.invs:
            recv, name, gargs, args = call_parts(inv)
            scope = scope_for(cf, inv)
            lines = [(cf.path, sx.line(inv))]
            if name == "ReceiveEndpoint" and args:
                v = self.res.resolve(arg_expr(args[0]), scope)
                consumers = sorted({g for n in sx.find_all(inv, "invocation_expression")
                                    for _, n2, gs, _ in [call_parts(n)]
                                    if n2 in ("Consumer", "ConfigureConsumer") for g in gs[:1]})
                self._msg(cf, "subscribe", broker, self._val_name(v), "queue", lines,
                          handler=f"{cf.path}:{sx.line(inv)}", trigger="processor",
                          library="MassTransit", message_types=consumers)
            elif name == "SubscriptionEndpoint" and args:
                strs = [self.res.resolve(arg_expr(a), scope) for a in args
                        if arg_expr(a) is not None and arg_expr(a).type != "lambda_expression"]
                if gargs:
                    self._msg(cf, "subscribe", broker, None, "topic", lines,
                              handler=f"{cf.path}:{sx.line(inv)}", trigger="processor",
                              library="MassTransit", message_types=gargs[:1], medium=True,
                              subscription=strs[0].text if strs and strs[0].is_literal else None)
                elif len(strs) >= 2:
                    self._msg(cf, "subscribe", broker, self._val_name(strs[1]), "topic", lines,
                              handler=f"{cf.path}:{sx.line(inv)}", trigger="processor",
                              library="MassTransit",
                              subscription=strs[0].text if strs[0].is_literal else None)
            elif name in ("Publish", "Send") and recv is not None:
                ty = self.res.member_type(sx.text(recv), scope) or ""
                if not re.search(r"IPublishEndpoint|IBus\b|ISendEndpoint", ty):
                    continue
                mt = gargs[:1]
                if not mt and args:
                    ex = arg_expr(args[0])
                    if ex is not None and ex.type == "object_creation_expression":
                        mt = [sx.text(ex.child_by_field_name("type"))]
                self._msg(cf, "publish", broker, None, "topic" if name == "Publish" else "queue",
                          lines, published_by=f"{cf.path}:{sx.line(inv)}", library="MassTransit",
                          message_types=mt, medium=True)

    # ---- outbound HTTP ---------------------------------------------------------------------
    def _client_of(self, recv, scope: Scope, cf: CsFile, depth=0):
        """(client, client_name, base Val | None, base line | None) or None."""
        if recv is None or depth > 3:
            return None
        t = recv.type
        if t in ("object_creation_expression", "implicit_object_creation_expression"):
            ty = sx.text(recv.child_by_field_name("type"))
            if t == "implicit_object_creation_expression" or ty.endswith("HttpClient"):
                base = self._base_assign(recv, None, scope, cf)
                return ("httpclient", None) + base
            return None
        if t == "invocation_expression":
            _, nm, _, args = call_parts(recv)
            if nm == "CreateClient":
                cname = None
                if args:
                    v = self.res.resolve(arg_expr(args[0]), scope)
                    cname = v.text if v.is_literal else None
                reg = self.idx.named_clients.get(cname or "")
                return ("ihttpclientfactory", cname, reg.base if reg else None,
                        (reg.path, reg.line) if reg else None)
            return None
        if t in ("identifier", "member_access_expression"):
            name = sx.text(recv).replace("this.", "")
            if "." in name:
                return None
            ty, init = self.res.local_type(name, scope)
            if init is not None and init.type in ("object_creation_expression",
                                                  "implicit_object_creation_expression",
                                                  "invocation_expression"):
                if init.type == "implicit_object_creation_expression" and not (
                        ty or "").endswith("HttpClient"):
                    return None
                got = self._client_of(init, scope, cf, depth + 1)
                if got is not None:
                    if got[2] is None:
                        b = self._base_assign(None, name, scope, cf)
                        got = got[:2] + b
                    return got
            if init is None and scope.body is not None:
                # using (var client = new HttpClient()) / using var c = factory.CreateClient()
                loc = self.res._local(name, scope)
                if loc is not None and loc.type in ("object_creation_expression",
                                                    "invocation_expression"):
                    return self._client_of(loc, scope, cf, depth + 1)
            if ty and re.search(r"\bHttpClient\b", ty) and "Factory" not in ty:
                b = self._base_assign(None, name, scope, cf)
                if b[0] is not None:
                    return ("httpclient", None) + b
                if scope.td is not None:
                    for key in [scope.td.name] + [split_generic(x)[0] for x in scope.td.extends]:
                        reg = self.idx.typed_clients.get(key)
                        if reg is not None:
                            return ("ihttpclientfactory", reg.name, reg.base,
                                    (reg.path, reg.line))
                return ("httpclient", None, None, None)
        return None

    def _base_assign(self, init, name, scope: Scope, cf: CsFile) -> tuple:
        """BaseAddress from an object initializer or ``x.BaseAddress = new Uri(..)``."""
        nodes = [init] if init is not None else []
        if name is not None:
            nodes.append(scope.td.node if scope.td is not None else cf.parsed.root)
        for node in nodes:
            for n in sx.find_all(node, "assignment_expression"):
                left = sx.text(n.child_by_field_name("left")).replace("this.", "")
                if init is not None and node is init and left == "BaseAddress":
                    pass
                elif name is not None and left == f"{name}.BaseAddress":
                    pass
                else:
                    continue
                rhs = n.child_by_field_name("right")
                return self.res.resolve(rhs, scope_for(cf, rhs)), (cf.path, sx.line(n))
        return None, None

    def _type_of_arg(self, ex, scope) -> str | None:
        if ex is None:
            return None
        if ex.type == "object_creation_expression":
            return sx.text(ex.child_by_field_name("type"))
        if ex.type == "identifier":
            ty, init = self.res.local_type(sx.text(ex), scope)
            if ty:
                return ty
            if init is not None and init.type == "object_creation_expression":
                return sx.text(init.child_by_field_name("type"))
        return None

    def _single_generic(self, body, names) -> str | None:
        if body is None or body.type == "compilation_unit":
            return None
        found = sorted({g for inv in sx.find_all(body, "invocation_expression")
                        for _, n2, gs, _ in [call_parts(inv)] if n2 in names and gs
                        for g in gs[:1]})
        return found[0] if len(found) == 1 else None

    def _headers(self, scope: Scope, client_name: str | None) -> list[str]:
        out = set()
        if scope.body is None or scope.body.type == "compilation_unit":
            return []
        for inv in sx.find_all(scope.body, "invocation_expression"):
            recv, nm, _, args = call_parts(inv)
            if nm in ("Add", "TryAddWithoutValidation") and recv is not None and \
                    re.search(r"(DefaultRequestHeaders|\.Headers)$", sx.text(recv)) and args:
                v = self.res.resolve(arg_expr(args[0]), scope)
                if v.is_literal and re.fullmatch(r"[A-Za-z0-9-]{1,80}", v.text or ""):
                    out.add(v.text)
        for n in sx.find_all(scope.body, "assignment_expression"):
            if sx.text(n.child_by_field_name("left")).endswith("DefaultRequestHeaders.Authorization"):
                out.add("Authorization")
        return sorted(out)

    def _request_message(self, ex, scope) -> tuple[str | None, object | None, int | None]:
        """HttpRequestMessage -> (method, url node, line)."""
        node = ex
        if ex is not None and ex.type == "identifier":
            _, init = self.res.local_type(sx.text(ex), scope)
            node = init or self.res._local(sx.text(ex), scope)
        if node is None or node.type not in ("object_creation_expression",
                                             "implicit_object_creation_expression"):
            return None, None, None
        al = node.child_by_field_name("arguments")
        args = [arg_expr(a) for a in sx.named_children(al)] if al is not None else []
        method, url = None, None
        if args:
            mt = sx.text(args[0])
            mm = re.match(r"(?:System\.Net\.Http\.)?HttpMethod\.(\w+)$", mt)
            if mm:
                method = mm.group(1).upper()
            else:
                mm = re.match(r'new\s+HttpMethod\(\s*"(\w+)"\s*\)', mt)
                method = mm.group(1).upper() if mm else None
            url = args[1] if len(args) > 1 else None
        for n in sx.find_all(node, "assignment_expression"):
            left = sx.text(n.child_by_field_name("left")).split(".")[-1]
            rhs = n.child_by_field_name("right")
            if left == "Method":
                mm = re.match(r"HttpMethod\.(\w+)$", sx.text(rhs))
                method = mm.group(1).upper() if mm else method
            elif left == "RequestUri":
                url = rhs
        if ex is not None and ex.type == "identifier" and method is None and scope.body:
            for n in sx.find_all(scope.body, "assignment_expression"):
                if sx.text(n.child_by_field_name("left")) == f"{sx.text(ex)}.Method":
                    mm = re.match(r"HttpMethod\.(\w+)$", sx.text(n.child_by_field_name("right")))
                    method = mm.group(1).upper() if mm else method
        return method, url, sx.line(node)

    def outbound(self, cf: CsFile, role: str) -> None:
        wrappers = []
        for inv in self.invs:
            recv, name, gargs, args = call_parts(inv)
            if name not in HTTP_CALLS or recv is None or not args:
                continue
            scope = scope_for(cf, inv)
            client = self._client_of(recv, scope, cf)
            if client is None:
                continue
            kind, cname, base, base_ln = client
            method = HTTP_CALLS[name]
            url_node = arg_expr(args[0])
            extra = []
            if method is None:
                method, url_node, rl = self._request_message(arg_expr(args[0]), scope)
                if rl:
                    extra.append((cf.path, rl))
            if url_node is None:
                self.miss("http url")
                continue
            uv = self.res.resolve(url_node, scope)
            request = response = None
            if name.endswith("AsJsonAsync") and len(args) > 1:
                request = gargs[0] if gargs else self._type_of_arg(arg_expr(args[1]), scope)
            if name == "GetFromJsonAsync" and gargs:
                response = gargs[0]
            response = response or self._single_generic(scope.body, ("ReadFromJsonAsync",
                                                                     "ReadAsAsync"))
            spec = {"method": method, "client": kind, "client_name": cname, "request": request,
                    "response": response, "headers": self._headers(scope, cname), "role": role}
            lines = [(cf.path, sx.line(inv))] + extra + [ln for ln in uv.lines
                                                         if ln[0] == cf.path]
            if base_ln and base_ln[0] == cf.path:
                lines.append(base_ln)
            src = uv.source()
            if src[0] == "param":
                pidx = self._param_index(scope, src[1])
                if pidx is not None:
                    wrappers.append((scope, pidx, uv, spec, lines, base, sx.line(inv)))
                    continue
            self._emit_call("outbound_http", cf, uv, base, spec, lines)
        for scope, pidx, uv, spec, lines, base, ln in wrappers:
            self._follow_wrapper(cf, scope, pidx, uv, spec, lines, base, ln, "outbound_http")

    def _param_index(self, scope: Scope, name: str) -> int | None:
        node = scope.body
        if node is None or node.type not in ("method_declaration", "local_function_statement"):
            return None
        for i, p in enumerate(sx.params_of(node, LANG)):
            if p.name == name:
                return i
        return None

    def _follow_wrapper(self, cf, scope, pidx, uv, spec, lines, base, http_line, kind) -> None:
        mname = sx.text(scope.body.child_by_field_name("name"))
        hit = False
        for inv in self.invs:
            recv, name, _, args = call_parts(inv)
            if name != mname or (recv is not None and sx.text(recv) not in ("this",)) or \
                    len(args) <= pidx:
                continue
            csc = scope_for(cf, inv)
            av = self.res.resolve(arg_expr(args[pidx]), csc)
            # substitute the parameter segment by the call-site value
            segs, done = [], False
            for s in uv.segs:
                if s.kind == "param" and not done:
                    segs += list(av.segs)
                    done = True
                else:
                    segs.append(s)
            nv = Val(tuple(segs), av.lines)
            if nv.source()[0] in ("param", "unknown"):
                continue
            hit = True
            s2 = dict(spec, via_wrapper=f"{cf.path}:{http_line}")
            self._emit_call(kind, cf, nv, base, s2, lines + [(cf.path, sx.line(inv))],
                            medium=True)
        if not hit:
            self.miss("http url via parameter")

    def _emit_call(self, kind, cf, uv: Val, base: Val | None, spec: dict, lines,
                   medium=False) -> None:
        src, key, rest = uv.source()
        base_src, base_vals, target, path_text = None, {}, None, None
        if src == "literal":
            full = rest
            b = pathnorm.split_url(full)[0] if re.match(r"^[a-z][a-z0-9+.-]*://", full, re.I) \
                else None
            if b:
                c = cc.classify("base_url", b)
                base_src = "literal"
                base_vals = {"default": c.record_value} if c.record_value and not c.secret else {}
                target = b.split("://")[-1].split("/")[0].split(":")[0]
                path_text = full[len(b):] if full.startswith(b) else pathnorm.split_url(full)[1]
            else:
                path_text = full
        elif src in ("config", "env"):
            base_src = f"{src}:{key}"
            base_vals = self.config_values(key)
            path_text = rest
        else:
            self.miss("http url")
            return
        if base_src is None:
            if base is not None:
                bsrc, bkey, brest = base.source()
                if bsrc == "literal":
                    b2, _p2, _ = pathnorm.split_url(brest)
                    if b2:
                        c = cc.classify("base_url", b2)
                        base_src = "literal"
                        base_vals = {"default": c.record_value} if c.record_value and \
                            not c.secret else {}
                        target = b2.split("://")[-1].split("/")[0].split(":")[0]
                        path_text = pathnorm.join(brest[len(b2):], path_text or "")
                elif bsrc in ("config", "env"):
                    base_src = f"{bsrc}:{bkey}"
                    base_vals = self.config_values(bkey)
                    path_text = pathnorm.join(brest, path_text or "")
            if base_src is None:
                base_src = "unknown"
                medium = True
                self.miss("relative url without base address")
        path, query = _split_path(path_text or "/")
        attrs = {"method": spec.get("method"), "client": spec.get("client"),
                 "client_name": spec.get("client_name"), "base_url_source": base_src,
                 "base_url_values": base_vals, "path_template": pathnorm.normalize(path),
                 "path_raw": path_text, "query_params": sorted(set(query)),
                 "headers": spec.get("headers") or [],
                 "request": norm_type(spec.get("request")), "response":
                     norm_type(spec.get("response")), "via_wrapper": spec.get("via_wrapper"),
                 "role": spec.get("role") or "runtime", "target_hint": target}
        for t in (spec.get("request"), spec.get("response")):
            self.schema_refs += [(r, cf.path, lines[0][1]) for r in schema_refs(t)]
        if not spec.get("method"):
            medium = True
        self.item(kind, cf.path, attrs, lines, "medium" if medium else "high")

    def refit(self, cf: CsFile) -> None:
        for td in cf.types:
            if td.kind != "interface":
                continue
            reg = self.idx.refit_bases.get(td.name)
            for m in sx.methods(td, LANG):
                a = next((x for x in m.annotations if x.name in ("Get", "Post", "Put", "Delete",
                                                                  "Patch", "Head")), None)
                if a is None:
                    continue
                path = self.ann_str(a, "path", pos=0, td=td) or ""
                body = next((p.type for p in m.params
                             if any(x.name == "Body" for x in p.annotations)), None)
                spec = {"method": a.name.upper(), "client": "refit", "client_name": td.name,
                        "request": body, "response": m.return_type, "headers": [],
                        "role": "runtime"}
                lines = [(cf.path, a.line)]
                if reg is not None and reg.path == cf.path:
                    lines.append((reg.path, reg.line))
                self._emit_call("outbound_http", cf, Val((sx_seg("lit", path),)),
                                reg.base if reg else None, spec, lines)

    def restsharp(self, cf: CsFile) -> None:
        for c in self.creations:
            ty = sx.text(c.child_by_field_name("type"))
            if ty != "RestRequest":
                continue
            scope = scope_for(cf, c)
            al = c.child_by_field_name("arguments")
            args = [arg_expr(a) for a in sx.named_children(al)] if al is not None else []
            if not args:
                self.miss("RestRequest without resource")
                continue
            uv = self.res.resolve(args[0], scope)
            method = None
            for a in args[1:]:
                mm = re.match(r"Method\.(\w+)$", sx.text(a))
                if mm:
                    method = mm.group(1).upper()
            response = None
            body = scope.body if scope.body is not None else cf.parsed.root
            for inv in sx.find_all(body, "invocation_expression"):
                _, nm, gs, _ = call_parts(inv)
                mm = re.match(r"(?:Execute)?(Get|Post|Put|Delete|Patch)(?:Async)?$", nm)
                if mm and method is None:
                    method = mm.group(1).upper()
                if nm.startswith(("Execute", "Get", "Post", "Put", "Delete", "Patch")) and gs:
                    response = response or gs[0]
            base, base_ln = None, None
            for node in ([scope.body] if scope.body is not None else []) + (
                    [scope.td.node] if scope.td is not None else []):
                for c2 in sx.find_all(node, "object_creation_expression"):
                    t2 = sx.text(c2.child_by_field_name("type"))
                    if t2 not in ("RestClient", "RestClientOptions"):
                        continue
                    al2 = c2.child_by_field_name("arguments")
                    a2 = [arg_expr(a) for a in sx.named_children(al2)] if al2 is not None else []
                    if a2 and a2[0] is not None and a2[0].type != "object_creation_expression":
                        base, base_ln = self.res.resolve(a2[0], scope_for(cf, c2)), sx.line(c2)
                    else:
                        rhs = next((n.child_by_field_name("right")
                                    for n in sx.find_all(c2, "assignment_expression")
                                    if sx.text(n.child_by_field_name("left")) == "BaseUrl"), None)
                        if rhs is not None:
                            base, base_ln = self.res.resolve(rhs, scope_for(cf, rhs)), sx.line(c2)
                    if base is not None:
                        break
                if base is not None:
                    break
            spec = {"method": method, "client": "restsharp", "client_name": None,
                    "request": None, "response": response, "headers": [], "role": "runtime"}
            lines = [(cf.path, sx.line(c))] + ([(cf.path, base_ln)] if base_ln else [])
            if uv.source()[0] in ("param", "unknown"):
                self.miss("RestRequest resource")
                continue
            self._emit_call("outbound_http", cf, uv, base, spec, lines)

    def flurl(self, cf: CsFile) -> None:
        verbs = {"GetAsync": "GET", "GetJsonAsync": "GET", "GetStringAsync": "GET",
                 "PostJsonAsync": "POST", "PostAsync": "POST", "PostUrlEncodedAsync": "POST",
                 "PutJsonAsync": "PUT", "PutAsync": "PUT", "PatchJsonAsync": "PATCH",
                 "DeleteAsync": "DELETE"}
        for inv in self.invs:
            recv, name, gargs, args = call_parts(inv)
            if name not in verbs or recv is None:
                continue
            chain, node = [], recv
            while node is not None and node.type == "invocation_expression":
                r2, n2, _, a2 = call_parts(node)
                chain.append((n2, a2, node))
                node = r2
            flurly = any(n in ("AppendPathSegment", "AppendPathSegments", "SetQueryParam",
                               "SetQueryParams", "WithHeader", "WithOAuthBearerToken",
                               "WithBasicAuth", "WithTimeout") for n, _, _ in chain)
            if not flurly and not (node is not None and node.type in (
                    "string_literal", "interpolated_string_expression")):
                continue
            scope = scope_for(cf, inv)
            root = self.res.resolve(node, scope)
            segs = list(root.segs)
            for n, a2, _ in reversed(chain):
                if n in ("AppendPathSegment", "AppendPathSegments"):
                    for a in a2:
                        segs.append(sx_seg("lit", "/"))
                        segs += list(self.res.resolve(arg_expr(a), scope).segs)
            spec = {"method": verbs[name], "client": "flurl", "client_name": None,
                    "request": None, "response": gargs[0] if gargs else None, "headers": [],
                    "role": "runtime"}
            self._emit_call("outbound_http", cf, Val(tuple(segs), root.lines), None, spec,
                            [(cf.path, sx.line(inv))], medium=True)

    # ---- data access -----------------------------------------------------------------------
    def _conn_source(self, ex, scope) -> tuple[str | None, str | None, str | None]:
        """Connection-string expression -> (name_from, host, database); never the value."""
        if ex is None:
            return None, None, None
        v = self.res.resolve(ex, scope)
        src, key, rest = v.source()
        raw = None
        if src == "literal":
            mm = re.match(r"(?i)^\s*name\s*=\s*(?:ConnectionStrings:)?([\w.:-]+)\s*$", v.text or "")
            if mm:
                key, src, rest = f"ConnectionStrings:{mm.group(1)}", "config", ""
            else:
                raw = v.text
        if src in ("config", "env") and rest == "":
            raw = self.raw_value(src, key)
            ident = cc.parse_store_identity(raw) if raw else None
            return f"{src}:{key}", (ident or {}).get("host"), (ident or {}).get("database")
        if raw:
            ident = cc.parse_store_identity(raw)
            return None, (ident or {}).get("host"), (ident or {}).get("database")
        self.miss("connection string source")
        return None, None, None

    def _entities(self, ctx_name: str) -> list[dict]:
        hit = self.idx.dbcontexts.get(ctx_name.split(".")[-1])
        if hit is None:
            return []
        path, td = hit
        out = []
        for f in sx.fields(td, LANG):
            name, args = split_generic(f.type or "")
            if name != "DbSet" or not args:
                continue
            ent = args[0].split(".")[-1]
            tab = self.idx.entity_tables.get(ent)
            decl = self.idx.type_decl(ent)
            out.append({"name": ent, "table": tab[0] if tab else f.name,
                        "schema": tab[1] if tab else None,
                        "defined_in": f"{decl[0]}:{decl[1].line}" if decl else f"{path}:{f.line}",
                        "operation": None})
        return sorted(out, key=lambda e: e["name"])

    def _store(self, cf, store_type, name_from, host, db, orm, entities, lines, sps=(),
               medium=False) -> None:
        attrs = {"store_type": store_type, "host": host, "database": db, "name_from": name_from,
                 "orm": orm, "entities": entities, "collections": [],
                 "stored_procedures": list(sps), "operation": None, "owns_schema": None,
                 "routines": [], "tables_ddl": []}
        evs = [self.ev(p, ln) for p, ln in sorted(set(lines))]
        it = make_item("data_access", self.sub_of(cf.path), None, attrs, evs, self.ex,
                       "medium" if medium else "high")
        prev = self.stores.get(it.id)
        if prev is None:
            self.stores[it.id] = it
            return
        pa = prev.attributes
        if pa["orm"] != orm and orm == "ef-core":
            pa["orm"] = orm
        for k in ("entities", "stored_procedures"):
            seen = {repr(sorted(x.items())) for x in pa[k]}
            pa[k] = sorted(pa[k] + [x for x in attrs[k] if repr(sorted(x.items())) not in seen],
                           key=lambda x: (x.get("name") or "", repr(sorted(x.items()))))
        pa["host"] = pa["host"] or host
        pa["database"] = pa["database"] or db
        prev.evidence = sorted(set(prev.evidence) | set(evs), key=lambda e: (e.file, e.line))
        if medium:
            prev.confidence = "medium"

    def data_access(self, cf: CsFile) -> None:
        for inv in self.invs:
            recv, name, gargs, args = call_parts(inv)
            if name in ("AddDbContext", "AddDbContextFactory", "AddDbContextPool",
                        "AddPooledDbContextFactory") and gargs:
                use = None
                for n in sx.find_all(inv, "invocation_expression"):
                    _, n2, _, a2 = call_parts(n)
                    if n2 in EF_STORES:
                        use = (n2, a2, n)
                        break
                if use is None:
                    self.miss("DbContext provider")
                    continue
                scope = scope_for(cf, use[2])
                nf, host, db = self._conn_source(arg_expr(use[1][0]) if use[1] else None, scope)
                lines = [(cf.path, sx.line(inv)), (cf.path, sx.line(use[2]))]
                self._store(cf, EF_STORES[use[0]], nf, host, db, "ef-core",
                            self._entities(gargs[-1]), lines)
            elif name in EF_STORES and recv is not None:
                m = enclosing_method(inv)
                if m is None or sx.text(m.child_by_field_name("name")) != "OnConfiguring":
                    continue
                scope = scope_for(cf, inv)
                nf, host, db = self._conn_source(arg_expr(args[0]) if args else None, scope)
                ctx_name = scope.td.name if scope.td is not None else ""
                self._store(cf, EF_STORES[name], nf, host, db, "ef-core",
                            self._entities(ctx_name), [(cf.path, sx.line(inv))])
            elif name in EF_RAW and args:
                v = self.res.resolve(arg_expr(args[0]), scope_for(cf, inv))
                mm = _SP.match(v.segs[0].text) if v.segs and v.segs[0].kind == "lit" else None
                if mm:
                    self.pending_sps.append(({"name": mm.group(1).strip("[]"),
                                              "evidence": f"{cf.path}:{sx.line(inv)}"},
                                             (cf, sx.line(inv))))
            elif name in DAPPER and args and "Dapper" in cf.text:
                self._dapper(cf, inv, recv, name, args)
        for c in self.creations:
            ty = sx.text(c.child_by_field_name("type"))
            if ty not in ADO_STORES:
                continue
            al = c.child_by_field_name("arguments")
            args = [arg_expr(a) for a in sx.named_children(al)] if al is not None else []
            if not args:
                continue
            nf, host, db = self._conn_source(args[0], scope_for(cf, c))
            if nf is None and host is None:
                continue
            sps = []
            for c2 in self.creations:
                if sx.text(c2.child_by_field_name("type")) not in ("SqlCommand", "NpgsqlCommand"):
                    continue
                al2 = c2.child_by_field_name("arguments")
                a2 = [arg_expr(a) for a in sx.named_children(al2)] if al2 is not None else []
                body = enclosing_method(c2)
                if a2 and body is not None and "StoredProcedure" in sx.text(body):
                    v = self.res.resolve(a2[0], scope_for(cf, c2))
                    if v.is_literal and re.fullmatch(r"[\w.\[\]]+", v.text or ""):
                        sps.append({"name": v.text.strip("[]"),
                                    "evidence": f"{cf.path}:{sx.line(c2)}"})
            self._store(cf, ADO_STORES[ty], nf, host, db,
                        "dapper" if "using Dapper" in cf.text else "ado", [],
                        [(cf.path, sx.line(c))], sps)

    def _dapper(self, cf, inv, recv, name, args) -> None:
        scope = scope_for(cf, inv)
        v = self.res.resolve(arg_expr(args[0]), scope)
        if not v.is_literal:
            self.miss("dapper sql")
            return
        sql = v.text or ""
        is_sp = any("StoredProcedure" in sx.text(a) for a in args[1:])
        conn_type, conn_arg = None, None
        body = scope.body if scope.body is not None else cf.parsed.root
        for c in sx.find_all(body, "object_creation_expression"):
            t = sx.text(c.child_by_field_name("type"))
            if t in ADO_STORES:
                al = c.child_by_field_name("arguments")
                a2 = [arg_expr(a) for a in sx.named_children(al)] if al is not None else []
                conn_type, conn_arg = t, (a2[0] if a2 else None)
        nf, host, db = self._conn_source(conn_arg, scope) if conn_arg is not None else (
            None, None, None)
        store = ADO_STORES.get(conn_type or "", "other")
        lines = [(cf.path, sx.line(inv))]
        if is_sp:
            self._store(cf, store, nf, host, db, "dapper", [], lines,
                        [{"name": sql.strip().strip("[]"),
                          "evidence": f"{cf.path}:{sx.line(inv)}"}], medium=True)
            return
        op = "write" if re.match(r"(?i)\s*(INSERT|UPDATE|DELETE|MERGE)", sql) else "read"
        ents = [{"name": t.strip('[]"'), "table": t.strip('[]"').split(".")[-1].strip('[]"'),
                 "schema": t.strip('[]"').split(".")[0].strip('[]"') if "." in t else None,
                 "defined_in": f"{cf.path}:{sx.line(inv)}", "operation": op}
                for _, t in _SQL_TABLE.findall(sql)]
        sp = _SP.match(sql)
        self._store(cf, store, nf, host, db, "dapper", ents, lines,
                    [{"name": sp.group(1).strip("[]"), "evidence": f"{cf.path}:{sx.line(inv)}"}]
                    if sp else [], medium=True)

    # ---- config reads ----------------------------------------------------------------------
    def _cfg_key(self, node, scope) -> tuple[str, str] | None:
        """(key, api) for a configuration read expression, else None."""
        t = node.type
        if t == "element_access_expression":
            # Resolver only yields a config key for configuration receivers / sections
            v = self.res.resolve(node, scope)
            if v.single is not None and v.single.kind == "config":
                return v.single.text, "IConfiguration[]"
            return None
        if t == "invocation_expression":
            recv, nm, _, args = call_parts(node)
            if nm in ("GetSection", "GetRequiredSection", "GetValue", "GetConnectionString") \
                    and args and recv is not None:
                v = self.res.resolve(node, scope)
                if v.single is not None and v.single.kind in ("config", "section"):
                    return v.single.text, nm
            if nm == "GetEnvironmentVariable" and args:
                v = self.res.resolve(node, scope)
                if v.single is not None and v.single.kind == "env":
                    return v.single.text, "Environment.GetEnvironmentVariable"
                self.miss("dynamic env var name")
        if t == "member_access_expression":
            v = self.res.resolve(node, scope)
            if v.single is not None and v.single.kind == "config" and \
                    sx.text(node).count(".Value.") + sx.text(node).count(".CurrentValue.") > 0:
                return v.single.text, "IOptions"
        return None

    def config_reads(self, cf: CsFile) -> None:
        if not re.search(r"GetSection|GetValue|GetConnectionString|GetEnvironmentVariable|"
                         r"\[\s*\"|\.Value\.", cf.text):
            return
        for n in sx.walk(cf.parsed.root):
            if n.type not in ("element_access_expression", "invocation_expression",
                              "member_access_expression"):
                continue
            par = n.parent
            if n.type == "member_access_expression" and par is not None and \
                    par.type == "member_access_expression":
                continue
            # an outer node continues the chain: let it record the full key
            if par is not None and par.type == "element_access_expression" and \
                    par.child_by_field_name("expression") == n:
                continue
            if par is not None and par.type == "member_access_expression" and \
                    par.parent is not None and par.parent.type == "invocation_expression" and \
                    sx.text(par.child_by_field_name("name")).split("<")[0] in (
                        "GetSection", "GetValue", "GetConnectionString", "GetRequiredSection"):
                continue
            if n.type == "invocation_expression" and call_parts(n)[1] not in (
                    "GetSection", "GetRequiredSection", "GetValue", "GetConnectionString",
                    "GetEnvironmentVariable"):
                continue
            scope = scope_for(cf, n)
            got = self._cfg_key(n, scope)
            if got is None:
                continue
            key, api = got
            self.reads.setdefault((self.sub_of(cf.path), key), []).append(
                (cf.path, sx.line(n), api))

    # ---- scheduled jobs --------------------------------------------------------------------
    def scheduled(self, cf: CsFile) -> None:
        for td in cf.types:
            if td.kind != "class":
                continue
            bases = {split_generic(b)[0] for b in td.extends}
            if bases & {"BackgroundService", "IHostedService"}:
                ms = [m for m in sx.methods(td, LANG) if m.name in ("ExecuteAsync", "StartAsync")]
                m = ms[0] if ms else None
                ln = sx.line(m.node.child_by_field_name("name")) if m else sx.line(
                    td.node.child_by_field_name("name"))
                expr = None
                if m is not None and m.body is not None:
                    mm = re.search(r"(?:PeriodicTimer|Task\.Delay)\s*\(\s*(TimeSpan\.\w+\([^()]*\)|"
                                   r"\d+)", sx.text(m.body))
                    expr = mm.group(1) if mm else None
                attrs = {"trigger_type": "hosted-service", "expression": expr,
                         "expression_from": "literal" if expr else None, "resolved_values": {},
                         "timezone": None, "handler": f"{cf.path}:{ln}", "name": td.name}
                self.item("scheduled_job", cf.path, attrs, [(cf.path, ln)], "medium")
        if "RecurringJob" in cf.text or "WithCronSchedule" in cf.text:
            for inv in self.invs:
                recv, nm, gargs, args = call_parts(inv)
                scope = scope_for(cf, inv)
                if nm == "AddOrUpdate" and recv is not None and "RecurringJob" in sx.text(recv) \
                        or (nm == "AddOrUpdate" and recv is not None and re.search(
                            r"(?i)recurring", sx.text(recv))):
                    vals = [arg_expr(a) for a in args]
                    jid = self.res.resolve(vals[0], scope) if vals else None
                    cron = vals[-1] if vals else None
                    for v in vals[1:]:
                        if v is not None and (v.type in ("string_literal",) or
                                              sx.text(v).startswith("Cron.")):
                            cron = v
                    cv = self.res.resolve(cron, scope) if cron is not None else None
                    expr = cv.text if cv is not None and cv.is_literal else (
                        sx.text(cron) if cron is not None and sx.text(cron).startswith("Cron.")
                        else None)
                    if expr is None:
                        self.miss("hangfire cron")
                    attrs = {"trigger_type": "hangfire", "expression": expr,
                             "expression_from": "literal" if expr else None,
                             "resolved_values": {}, "timezone": None,
                             "handler": f"{cf.path}:{sx.line(inv)}",
                             "name": jid.text if jid is not None and jid.is_literal else None}
                    self.item("scheduled_job", cf.path, attrs, [(cf.path, sx.line(inv))])
                elif nm == "WithCronSchedule" and args:
                    cv = self.res.resolve(arg_expr(args[0]), scope)
                    src, key, _ = cv.source()
                    rv = self.schedule_values(key) if src in ("config", "env") else {}
                    expr = cv.text if cv.is_literal else (rv.get("default") if rv else None)
                    if expr is None:
                        self.miss("quartz cron")
                    attrs = {"trigger_type": "quartz", "expression": expr,
                             "expression_from": "literal" if cv.is_literal else (
                                 f"{src}:{key}" if key else None),
                             "resolved_values": rv, "timezone": None,
                             "handler": f"{cf.path}:{sx.line(inv)}", "name": None}
                    self.item("scheduled_job", cf.path, attrs, [(cf.path, sx.line(inv))],
                              "high" if cv.is_literal else "medium")

    # ---- generated contracts ---------------------------------------------------------------
    def contracts(self, cf: CsFile) -> None:
        if "AddSwaggerGen" not in cf.text and "UseSwagger" not in cf.text:
            return
        docs = "/swagger/v1/swagger.json"
        first = None
        for inv in self.invs:
            _, nm, _, args = call_parts(inv)
            if nm in ("AddSwaggerGen", "UseSwagger") and first is None:
                first = inv
            if nm == "SwaggerEndpoint" and args:
                v = self.res.resolve(arg_expr(args[0]), scope_for(cf, inv))
                if v.is_literal and (v.text or "").startswith("/") and "{}" not in v.text:
                    docs = v.text
        if first is not None:
            self.items.append(generated_contract_item(self.ctx, self.ex, "swashbuckle", docs,
                                                      cf.path, sx.line(first)))

    # ---- finish: schemas, config reads, stored procs ---------------------------------------
    def finish(self, res: ExtractResult) -> None:
        efs = [it for it in self.stores.values() if it.attributes["orm"] == "ef-core"]
        for sp, (cf, ln) in self.pending_sps:
            if len(efs) == 1:
                pa = efs[0].attributes
                if sp not in pa["stored_procedures"]:
                    pa["stored_procedures"] = sorted(pa["stored_procedures"] + [sp],
                                                     key=lambda x: (x["name"], x["evidence"]))
                efs[0].evidence = sorted(set(efs[0].evidence) | {self.ev(cf.path, ln)},
                                         key=lambda e: (e.file, e.line))
            else:
                res.touch(cf.path, "partial")
        self.items += list(self.stores.values())
        for (sub, key), reads in sorted(self.reads.items()):
            reads = sorted(set(reads))
            attrs = {"name": key, "canonical": cc.canonical_key(key)[0],
                     "reads": [{"file": f, "line": ln, "api": api} for f, ln, api in reads],
                     "defined_in": [], "values": {}, "value_kind": None, "secret": None,
                     "kv_ref": None, "ref": None, "provided_by": None, "required": None}
            evs = [self.ev(f, ln) for f, ln, _ in reads]
            self.items.append(make_item("config_key", sub, attrs["canonical"], attrs, evs,
                                        self.ex))
        self._schemas()
        res.items.extend(self.items)

    def _schemas(self) -> None:
        done: set[str] = set()
        queue = sorted(set(self.schema_refs))
        while queue:
            name, ref_file, ref_line = queue.pop(0)
            if name in done:
                continue
            done.add(name)
            hit = self.idx.type_decl(name, self.sub_of(ref_file), self.ctx)
            if hit is None:
                attrs = {"name": name, "defined_in": None, "language": "csharp",
                         "schema_kind": None, "fields": [], "enum_values": [], "type_params": [],
                         "extends": None, "resolved": False}
                self.items.append(make_item("schema", self.sub_of(ref_file), name, attrs,
                                            [self.ev(ref_file, ref_line)], self.ex))
                continue
            path, td = hit
            attrs, nested = self._schema_attrs(path, td)
            ln = sx.line(td.node.child_by_field_name("name") or td.node)
            self.items.append(make_item("schema", self.sub_of(path), name, attrs,
                                        [self.ev(path, ln)], self.ex))
            for r in nested:
                if r not in done:
                    queue.append((r, path, ln))

    def _schema_attrs(self, path, td) -> tuple[dict, list[str]]:
        nested: list[str] = []
        fields_out = []
        enum_values = []
        if td.kind == "enum":
            enum_values = [n if v is None else f"{n}={v}" for n, v, _ in sx.enum_members(td, LANG)]
        else:
            members = [(p.name, p.type, p.annotations, [], None) for p in td.params] if \
                td.kind == "record" else []
            for f in sx.fields(td, LANG):
                mods = set(f.modifiers)
                if "static" in mods or "const" in mods:
                    continue
                if td.kind != "interface" and "public" not in mods:
                    continue
                default = sx.text(f.value)[:80] if f.value is not None else None
                members.append((f.name, f.type, f.annotations, f.modifiers, default))
            for name, ty, anns, mods, default in members:
                an = {a.name: a for a in anns}
                if "JsonIgnore" in an:
                    continue
                jn = None
                for k in ("JsonPropertyName", "JsonProperty"):
                    if k in an:
                        v = an[k].args.get("PropertyName", "propertyName", pos=0)
                        jn = v if isinstance(v, str) else None
                val = {}
                for a in anns:
                    if a.name == "StringLength":
                        val["max_length"] = a.args.get("maximumLength", pos=0)
                        if a.args.get("MinimumLength") is not None:
                            val["min_length"] = a.args.get("MinimumLength")
                    elif a.name == "MaxLength":
                        val["max_length"] = a.args.get("length", pos=0)
                    elif a.name == "MinLength":
                        val["min_length"] = a.args.get("length", pos=0)
                    elif a.name == "Range":
                        val["min"] = a.args.get("minimum", pos=0)
                        val["max"] = a.args.get("maximum", pos=1)
                    elif a.name == "RegularExpression":
                        val["pattern"] = a.args.get("pattern", pos=0)
                    elif a.name in ("EmailAddress", "Phone", "Url", "CreditCard"):
                        val["format"] = a.name.lower()
                val = {k: v for k, v in val.items() if isinstance(v, (str, int, float))}
                required = bool("required" in mods or "Required" in an or
                                is_value_type(ty, self.enums))
                fields_out.append({"name": name, "json_name": jn, "type": norm_type(ty),
                                   "required": required, "nullable": is_nullable(ty),
                                   "validation": val or None,
                                   "default": default if default not in ("default!", "null!")
                                   else None})
                nested += schema_refs(ty)
        ext = next((split_generic(b)[0] for b in td.extends
                    if not re.match(r"^I[A-Z]", split_generic(b)[0])), None)
        if ext:
            nested.append(ext)
        kind = {"struct": "class"}.get(td.kind, td.kind)
        attrs = {"name": td.name, "defined_in": f"{path}:{sx.line(td.node.child_by_field_name('name') or td.node)}",
                 "language": "csharp", "schema_kind": kind, "fields": fields_out,
                 "enum_values": enum_values, "type_params": td.type_params, "extends": ext,
                 "resolved": True}
        return attrs, sorted(set(nested))


def _split_path(text: str) -> tuple[str, list[str]]:
    """Relative path text (holes as ``{}``) -> (path with leading ``/``, query names)."""
    if re.match(r"^[a-z][a-z0-9+.-]*://", text, re.I):
        _b, path, query = pathnorm.split_url(text)
        return path, query
    path, _, q = text.split("#", 1)[0].partition("?")
    query = [p.split("=", 1)[0] for p in q.split("&") if p.split("=", 1)[0]] if q else []
    path = re.sub(r"/{2,}", "/", path if path.startswith("/") else "/" + path)
    return path, query


def sx_seg(kind: str, text: str) -> Seg:
    return Seg(kind, text)


def enclosing_method(node):
    cur = node.parent
    while cur is not None:
        if cur.type in ("method_declaration", "constructor_declaration",
                        "local_function_statement"):
            return cur
        cur = cur.parent
    return None

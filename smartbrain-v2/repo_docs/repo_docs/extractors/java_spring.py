"""java.spring: Spring MVC/WebFlux/JAX-RS inbound, schemas, outbound HTTP, messaging, data access,
scheduled jobs and config reads for ``*.java`` files (plan.md item 4, docs/EXTRACTORS.md).

Built on tree-sitter trees (syntax.py) and the repo-wide symbol index (java_symbols.py). Files
whose tree has errors are extracted from clean subtrees and marked ``partial``; so are files with
an unresolved route/URL/entity, a wrapper of a wrapper or an unsupported client. Test-class files
only yield ``outbound_http`` with ``role: tests_target`` (D-P4).
"""
from __future__ import annotations

import re

from .. import config_classify as cc
from .. import pathnorm
from ..inventory_schema import make_item
from . import java_data as jd
from . import java_inbound as ji
from . import java_symbols as js
from . import syntax as sx
from .base import ExtractResult, Extractor, RepoContext
from .java_http import Call, HttpScanner, is_no_base
from .java_messaging import Msg, MessagingScanner
from .java_types import SchemaCollector, TypeNorm, parse_type

# constructs no rule covers yet -> file partial (phase 3)
UNSUPPORTED = re.compile(
    r"\bRetrofit\b|\bRouterFunctions\b|\bjava\.net\.http\b|\bHttpURLConnection\b|"
    r"\bAmqpTemplate\b|@SqsListener\b|\bEventHub(Producer|Consumer)\w*Client\b|"
    r"\bServiceBusAdministrationClient\b|\bSqlSessionTemplate\b|\borg\.apache\.ibatis\b|"
    r"\bElasticsearch\w*\b|\bCosmos\w*Client\b|"
    r"\bBlob(Service|Container)Client\b|\bWebSocket\w*\b|\bGrpc\w*\b")
# client / driver packages no extractor rule covers: importing one leaves the file partial even
# when a type name above does not match (allowlist gate instead of growing the denylist)
UNSUPPORTED_IMPORTS = re.compile(
    r"^\s*import\s+(?:static\s+)?(?:org\.elasticsearch|"
    r"co\.elastic\.clients|org\.neo4j|com\.datastax|org\.apache\.cassandra|com\.azure\.cosmos|"
    r"com\.azure\.storage|com\.azure\.messaging\.eventhubs|com\.azure\.data|"
    r"software\.amazon\.awssdk|com\.amazonaws|com\.google\.cloud|io\.grpc|org\.apache\.ibatis|"
    r"org\.mybatis|com\.mongodb|org\.apache\.solr|io\.nats|com\.rabbitmq|org\.apache\.pulsar|"
    r"org\.apache\.http\.nio|org\.asynchttpclient|retrofit2|com\.couchbase|"
    r"io\.lettuce|redis\.clients\.jedis|org\.redisson)\.", re.M)
CLIENT_TYPE = re.compile(r"\b(RestTemplate|WebClient|RestClient|OkHttpClient|"
                         r"CloseableHttpClient|HttpClient)\b")
INTERCEPTORS = frozenset({"ClientHttpRequestInterceptor", "ExchangeFilterFunction",
                          "Interceptor"})
EXCHANGES = {"GetExchange": "GET", "PostExchange": "POST", "PutExchange": "PUT",
             "PatchExchange": "PATCH", "DeleteExchange": "DELETE", "HttpExchange": None}


def _is_java(e: dict) -> bool:
    return e["path"].endswith(".java")


class _State:
    def __init__(self, ctx, sub):
        self.ctx, self.sub = ctx, sub
        self.items: list = []
        self.partial: dict[str, str | None] = {}   # path -> error (None = unresolved construct)
        self.msgs: list = []                         # (Msg, path, jt, item)
        self.sends: list = []                        # (bean, path, line, jt)
        self.config_reads: dict = {}                 # canonical -> [(key, default, path, line, api)]
        self.repo_ops: list = []
        self.jdbc: list = []                         # (sql, path, line)
        self.procs: list = []                        # (name, path, line)
        self.redis: list = []                        # (path, line)
        self.entities: list = []      # (jt, 'sql'|'mongo', table, schema, collection, line)
        self.mongo_ops: list = []     # (entity JType | None, collection | None, op, path, line)
        self.os_sites: list = []      # (names, key, code_default, op, path, line)
        self.neb_rows: list = []      # (name, op, path, line)
        self.neb_space: list = []     # (names, key, code_default, path, line)
        self.neb_ev: list = []        # (path, line) statement sites without a tag/edge
        self.store_beans: list = []   # (store kind, path, line)
        self.prefix: dict = {}        # webflux flag -> context_prefix(...)

    def unresolved(self, path: str) -> None:
        self.partial.setdefault(path, None)


class JavaSpring(Extractor):
    id = "java.spring"
    stacks = ("java",)
    extractor_version = sx.versioned("0.2.0", "java")

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        sub = subproject or "."
        res = ExtractResult()
        idx = js.index(ctx)
        tn = TypeNorm(idx)
        http = ctx.symbols.setdefault("java.http", HttpScanner(idx))
        msc = MessagingScanner(ctx, idx)
        st = _State(ctx, sub)
        schemas = SchemaCollector(ctx, idx, tn, self, sub)
        sb_jms = any("servicebus" in k for k in ctx.config.keys())
        repos = jd.repositories(idx)
        files = ctx.files(sub, _is_java)
        sec = ji.Security()
        for e in files:
            jf = idx.files.get(e["path"])
            if jf is None or e.get("class") == "test":
                continue
            for jt in jf.types:
                for m in jt.methods:
                    sec.collect(idx, jt, m)
        for p in sec.unresolved:
            st.unresolved(p)
        for e in files:
            path = e["path"]
            jf = idx.files.get(path)
            if jf is None:
                res.touch(path, "partial", "unreadable")
                continue
            if jf.parsed.has_error:
                st.partial[path] = f"tree-sitter: {jf.parsed.errors} error nodes"
            is_test = e.get("class") == "test"
            text = ctx.read_text(path) or ""
            if not is_test and (UNSUPPORTED.search(text) or UNSUPPORTED_IMPORTS.search(text)):
                st.unresolved(path)
            has_calls = False
            for jt in jf.types:
                if not is_test:
                    self._inbound(ctx, idx, tn, jt, st, sec, schemas)
                    self._interface_client(ctx, idx, tn, jt, st, schemas)
                    self._type_level(ctx, idx, jt, st)
                for m in jt.methods:
                    mcalls = http.calls(jt, m) + http.wrapper_calls(jt, m)
                    if mcalls:
                        has_calls = True
                    for c in mcalls:
                        if c.is_wrapper():
                            # a registered wrapper body is resolved at its call sites; a
                            # param-derived URL beyond the wrapper depth limit stays partial
                            if (jt.fqn, m.name, len(m.params)) not in http.wrappers():
                                st.unresolved(path)
                            continue
                        self._outbound(ctx, tn, c, jf, jt, st, schemas,
                                       "tests_target" if is_test else "runtime")
                    if is_test:
                        continue
                    for msg in msc.expand_param_msgs(
                            jt, m, msc.method_msgs(jt, m, sub, sb_jms), sub) + \
                            msc.listener_msgs(jt, m, sb_jms):
                        self._messaging(ctx, tn, msg, jf, jt, st, schemas)
                    for bean, line in msc.send_sites(jt, m):
                        st.sends.append((bean, path, line, jt))
                    self._scheduled(ctx, idx, jt, m, st)
                    self._method_config(idx, jt, m, st)
                    self._store_sites(ctx, idx, jt, m, st)
                    data = jd.scan_method(idx, jt, m, repos)
                    st.repo_ops += data["repo_ops"]
                    st.jdbc += [(s, path, ln) for s, ln in data["jdbc"]]
                    st.procs += [(n, path, ln) for n, ln in data["procs"]]
                    for vs, ln, job in data["quartz"]:
                        self._quartz(ctx, vs, ln, job, jf, jt, m, st)
            if not is_test and not has_calls:
                why = self._silent_ok(idx, jf)
                if why:
                    ctx.hints.setdefault("silent_ok", {})[path] = why
        self._link_sends(ctx, tn, msc, st, schemas)
        self._data_items(ctx, idx, repos, st)
        self._config_items(ctx, st)
        st.items += schemas.run()
        res.items = st.items
        for e in files:
            path = e["path"]
            if path in st.partial:
                res.touch(path, "partial", st.partial[path])
            elif path in idx.files:
                res.touch(path, "full")
        return res

    # ---- client factory / holder / interface / interceptor files (D8) --------------------
    @staticmethod
    def _silent_ok(idx, jf) -> str | None:
        """Why a file that mentions an HTTP client but has no call site is expected to yield no
        outbound item: every type in it is a client factory (``@Configuration`` with a
        ``@Bean`` returning a client), a client holder (constructors / getters only, with a
        client-typed field), an interface, or a client interceptor. Mixed files -> None."""
        reasons = []
        for jt in jf.types:
            d = jt.decl
            anns = {a.name for a in d.annotations}
            exts = {js.simple_type(e) for e in d.extends}
            if d.kind == "interface":
                reasons.append("client-interface")
            elif exts & INTERCEPTORS:
                reasons.append("client-interceptor")
            elif anns & {"Configuration", "AutoConfiguration"} and any(
                    any(a.name == "Bean" for a in m.annotations)
                    and CLIENT_TYPE.search(m.return_type or "") for m in jt.methods):
                reasons.append("client-factory")
            elif any(CLIENT_TYPE.search(f.type or "") for f in jt.fields.values()) and all(
                    m.kind == "constructor" or (not m.params and re.match(r"(get|is)[A-Z]",
                                                                          m.name))
                    for m in jt.methods):
                reasons.append("client-holder")
            else:
                return None
        return reasons[0] if reasons else None

    # ---- inbound -------------------------------------------------------------------------
    def _inbound(self, ctx, idx, tn, jt, st: _State, sec, schemas) -> None:
        d = jt.decl
        if d.kind != "class":
            return
        canns = {a.name: a for a in d.annotations}
        if "FeignClient" in canns or "HttpExchange" in canns:
            return
        jaxrs = "Path" in canns
        if not (jaxrs or "RestController" in canns or "Controller" in canns
                or "RequestMapping" in canns):
            return
        path = jt.jfile.path
        scope = idx.type_scope(jt)
        sub = st.sub
        if jaxrs:
            cann = canns["Path"]
            cvals = [cann.args.get("value", pos=0)]
            app = self._application_path(ctx, idx, sub)
        else:
            cann = canns.get("RequestMapping")
            cvals = ji.as_list(cann.args.get("value", "path", pos=0)) if cann else []
            app = ""
        cvals = cvals or [""]
        cpaths = [ji.route_text(ctx, idx, sub, v, scope) for v in cvals]
        if any(p is None for p in cpaths):
            st.unresolved(path)
            return
        craw = sx.text(cann.node.child_by_field_name("arguments")) if cann is not None and \
            cann.node.child_by_field_name("arguments") is not None else ""
        cauth = ji.auth_from(d.annotations)
        for m in jt.methods:
            maps = []
            if jaxrs:
                verbs = [a.name for a in m.annotations if a.name in ji.JAXRS_VERBS]
                mp = next((a for a in m.annotations if a.name == "Path"), None)
                if not verbs and mp is None:
                    continue
                maps.append((verbs or [None], [mp.args.get("value", pos=0)] if mp else [""],
                             mp or next(a for a in m.annotations if a.name in ji.JAXRS_VERBS)))
            else:
                for a in m.annotations:
                    if a.name not in ji.MAPPINGS:
                        continue
                    verb = ji.MAPPINGS[a.name]
                    if verb:
                        verbs = [verb]
                    else:
                        verbs = [v.name.rsplit(".", 1)[-1] if isinstance(v, sx.Ref) else None
                                 for v in ji.as_list(a.args.get("method"))] or [None]
                    maps.append((verbs, ji.as_list(a.args.get("value", "path", pos=0)) or [""],
                                 a))
            if not maps:
                continue
            webflux = ji.is_webflux(m)
            if webflux not in st.prefix:
                st.prefix[webflux] = ji.context_prefix(ctx, sub, webflux)
            prefix, by_env, differ = st.prefix[webflux]
            params, request, req_text = ji.params_of(tn, m, jt.jfile, jt, jaxrs)
            responses, resp_texts = ji.responses_of(tn, m, jt.jfile, jt, d.annotations)
            mauth = ji.auth_from(m.annotations)
            auth, auth_raw, anon = mauth if mauth[0] else cauth
            for verbs, mvals, ann in maps:
                for mv in mvals:
                    mpath = ji.route_text(ctx, idx, sub, mv, scope)
                    if mpath is None:
                        st.unresolved(path)
                        continue
                    for cp in cpaths:
                        rel = pathnorm.join(pathnorm.join(app, cp), mpath)
                        full = pathnorm.join(prefix, rel) if prefix else rel
                        medium = differ
                        a_auth, a_raw, a_anon = auth, auth_raw, anon
                        if a_auth is None and sec.rules:
                            a_auth, a_anon, raw = sec.match(pathnorm.display_path(rel))
                            if a_auth is not None:
                                a_raw = f"SecurityFilterChain: {raw}"
                                medium = True
                        for verb in verbs:
                            araw = sx.text(ann.node.child_by_field_name("arguments")) \
                                if ann.node.child_by_field_name("arguments") is not None else ""
                            attrs = {
                                "method": verb, "path": pathnorm.display_path(full),
                                "path_raw": " + ".join(x for x in (craw, araw) if x)[:200] or None,
                                "path_params_normalized": pathnorm.normalize(full),
                                "handler": f"{d.qualified}.{m.name}",
                                "framework": "jax-rs" if jaxrs else (
                                    "spring-webflux" if webflux else "spring-mvc"),
                                "params": params, "request": request, "responses": responses,
                                "auth": a_auth, "auth_raw": a_raw, "allow_anonymous": a_anon,
                                "deprecated": any(a.name == "Deprecated"
                                                  for a in m.annotations + d.annotations),
                                "contract_file": None, "context_path_by_env": by_env}
                            ev = [ctx.evidence(path, ann.line)]
                            if cann is not None:
                                ev.append(ctx.evidence(path, cann.line))
                            st.items.append(make_item("inbound_http", sub, None, attrs, ev, self,
                                                      "medium" if medium else "high"))
            ev0 = ctx.evidence(path, maps[0][2].line)
            if req_text:
                schemas.add(req_text, jt.jfile, jt, ev0)
            for t in resp_texts:
                schemas.add(t, jt.jfile, jt, ev0)

    def _application_path(self, ctx, idx, sub) -> str:
        for jt in idx.types.values():
            if ctx.subproject_of(jt.jfile.path) != sub:
                continue
            a = next((a for a in jt.decl.annotations if a.name == "ApplicationPath"), None)
            if a is not None:
                v = ji.route_text(ctx, idx, sub, a.args.get("value", pos=0), idx.type_scope(jt))
                return v or ""
        return ""

    # ---- outbound ------------------------------------------------------------------------
    def _split(self, ctx, sub, vs: js.ValueSource):
        """(base_url_source, base_url_values, path, query, ok) for a URL value source."""
        if vs is None:
            return "unknown", {}, "", [], False
        if vs.kind == "literal":
            base, path, q = pathnorm.split_url(vs.value or "")
            if base and "://" in base:
                c = cc.classify("url", base)
                vals = {"default": c.record_value} if c.record_value and not c.secret else {}
                return "literal", vals, path, q + vs.query, True
            return "unknown", {}, path, q + vs.query, False
        if vs.kind in ("config", "env"):
            _b, path, q = pathnorm.split_url(vs.value or "")
            vals = ctx.config.public_values(vs.key, sub)
            if not vals and vs.default:
                c = cc.classify(vs.key, vs.default)
                if c.record_value and not c.secret:
                    vals = {"default": c.record_value}
            return f"{vs.kind}:{vs.key}", vals, path, q + vs.query, True
        if vs.kind == "unknown":
            _b, path, q = pathnorm.split_url(vs.value or "")
            return "unknown", {}, path, q + vs.query, False
        return "unknown", {}, "", [], False

    @staticmethod
    def _absolute_uri(ctx, sub, c: Call) -> bool:
        """WebClient/RestClient ``uri(x)`` replaces the base when the client has no base URL,
        or ``x`` is an absolute literal, the base's own key, or a config key whose value is an
        absolute URL."""
        p, b = c.path, c.base
        if is_no_base(b):
            return True
        if p.kind == "literal":
            return "://" in (p.value or "")
        if p.kind not in ("config", "env") or p.prefix:
            return False
        if b is not None and b.kind == p.kind and b.key == p.key and not b.prefix:
            return True
        if p.kind == "config":
            vals = ctx.config.public_values(p.key, sub)
            distinct = sorted(set(vals.values()))
            v = vals.get("default") or (distinct[0] if len(distinct) == 1 else "")
            return bool(re.match(r"https?://", v or ""))
        return False

    def _outbound(self, ctx, tn, c: Call, jf, jt, st: _State, schemas, role: str) -> None:
        path = jf.path
        sub = st.sub
        if c.url is not None:
            vs = c.url
        elif c.path is not None and self._absolute_uri(ctx, sub, c):
            vs = c.path  # uri(...) is the whole URL: no base, or an absolute literal/config
        else:
            base_segs = list(c.base.segs) if c.base is not None else [js.Seg("unknown", "base")]
            path_segs = list(c.path.segs) if c.path is not None else []
            vs = js.source_of(base_segs + path_segs, c.path.query if c.path is not None else [])
        src, vals, upath, query, ok = self._split(ctx, sub, vs)
        literal_part = re.sub(r"\{[^}]*\}|/", "", upath or "")
        if not ok:
            st.unresolved(path)
            if not literal_part:
                return
        medium = (not ok) or bool(c.via_wrapper) or c.method is None or \
            (c.method or "").startswith("param:")
        meth = c.method if c.method and not c.method.startswith("param:") else None
        attrs = {
            "method": meth, "client": c.client, "client_name": c.client_name,
            "base_url_source": src, "base_url_values": vals,
            "path_template": pathnorm.normalize(upath or "/"),
            "path_raw": re.sub(r"\s+", " ", c.raw)[:200] or None,
            "query_params": sorted(set(query)), "headers": sorted(set(c.headers)),
            "request": tn.norm(c.request, jf, jt) if c.request else None,
            "response": tn.norm(c.response, jf, jt) if c.response else None,
            "via_wrapper": c.via_wrapper, "role": role,
            "target_hint": c.client_name if c.client == "feign" and src == "unknown" else None}
        ev = [ctx.evidence(path, ln) for ln in sorted(set(c.lines or [c.line]))]
        ev += [ctx.evidence(f, ln) for f, ln in c.extra_evidence]
        # the innermost HTTP call of a wrapper chain is evidence too (runtime items only: a test
        # calling the wrapper must not point gaps / docs at the production helper)
        if role == "runtime" and c.wrapper_file and c.wrapper_line and (
                c.wrapper_file != path or c.wrapper_line not in (c.lines or [c.line])):
            ev.append(ctx.evidence(c.wrapper_file, c.wrapper_line))
        st.items.append(make_item("outbound_http", sub, None, attrs, ev, self,
                                  "medium" if medium else "high"))
        if role == "runtime":
            if c.request:
                schemas.add(c.request, jf, jt, ev[0])
            if c.response:
                schemas.add(c.response, jf, jt, ev[0])

    def _interface_client(self, ctx, idx, tn, jt, st: _State, schemas) -> None:
        d = jt.decl
        if d.kind != "interface":
            return
        canns = {a.name: a for a in d.annotations}
        feign = canns.get("FeignClient")
        hx = canns.get("HttpExchange")
        if feign is None and hx is None:
            return
        scope = idx.type_scope(jt)
        if feign is not None:
            name = feign.args.get("name", "value", pos=0)
            name = name if isinstance(name, str) else None
            url = feign.args.get("url")
            base = list(idx.resolve_value(url, scope).segs) if url else [js.Seg("unknown", "feign")]
            pre = ji.route_text(ctx, idx, st.sub, feign.args.get("path"), scope)
            client, cline = "feign", feign.line
        else:
            name = None
            u = hx.args.get("url", "value", pos=0)
            vs = idx.resolve_value(u, scope) if u else None
            if vs is not None and vs.kind == "literal" and "://" in (vs.value or ""):
                base, pre = list(vs.segs), ""
            else:
                base = [js.Seg("unknown", "http-exchange")]
                pre = ji.route_text(ctx, idx, st.sub, u, scope) if u else ""
            client, cline = "restclient", hx.line
        if pre is None:
            st.unresolved(jt.jfile.path)
            return
        table = ji.MAPPINGS if feign is not None else EXCHANGES
        for m in jt.methods:
            for a in m.annotations:
                if a.name not in table:
                    continue
                verb = table[a.name]
                if verb is None:
                    mv = a.args.get("method")
                    mv = mv[0] if isinstance(mv, list) and mv else mv
                    verb = mv.name.rsplit(".", 1)[-1] if isinstance(mv, sx.Ref) else (
                        mv if isinstance(mv, str) else None)
                for v in ji.as_list(a.args.get("value", "path", "url", pos=0)) or [""]:
                    mpath = ji.route_text(ctx, idx, st.sub, v, scope)
                    if mpath is None:
                        st.unresolved(jt.jfile.path)
                        continue
                    full = pathnorm.join(pre, mpath)
                    vs = js.source_of(base + [js.Seg("lit", full)])
                    _params, _req, req_text = ji.params_of(tn, m, jt.jfile, jt, False)
                    c = Call(client, verb, vs, None, None, sx.text(a.node)[:200], req_text,
                             m.return_type if js.simple_type(m.return_type) not in (
                                 "void", "Void") else None, a.line, [a.line, cline],
                             client_name=name)
                    self._outbound(ctx, tn, c, jt.jfile, jt, st, schemas, "runtime")

    # ---- messaging -----------------------------------------------------------------------
    def _messaging(self, ctx, tn, msg: Msg, jf, jt, st: _State, schemas) -> None:
        sub, path = st.sub, jf.path
        entity, name_from, name_key, resolved, medium = None, "unknown", None, {}, False
        vs = msg.name
        if vs is not None and vs.kind == "literal" and not vs.holes:
            entity, name_from = vs.value, "literal"
        elif vs is not None and vs.kind in ("config", "env") and not vs.value and not vs.prefix:
            name_key, name_from = vs.key, f"{vs.kind}:{vs.key}"
            resolved = ctx.config.public_values(vs.key, sub)
            if not resolved and vs.default:
                c = cc.classify(vs.key, vs.default)
                if c.record_value and not c.secret:
                    resolved = {"default": c.record_value}
            distinct = sorted(set(resolved.values()))
            entity = resolved.get("default") or (distinct[0] if len(distinct) == 1 else None)
            medium = entity is None or len(distinct) > 1
        else:
            medium = True
            st.unresolved(path)
        subscription = None
        if msg.subscription is not None:
            s = msg.subscription
            if s.kind == "literal" and not s.holes:
                subscription = s.value
            elif s.kind in ("config", "env") and not s.value:
                pv = ctx.config.public_values(s.key, sub)
                subscription = pv.get("default") or (next(iter(pv.values())) if len(
                    set(pv.values())) == 1 else None)
                if subscription is None:
                    medium = True
        broker = msg.broker
        if broker == "stream":
            keys = " ".join(ctx.config.keys())
            broker = "azure-service-bus" if "servicebus" in keys else (
                "kafka" if "kafka" in keys else "other")
        eh = dict(msg.error_handling)
        if "deadLetter(" in (ctx.read_text(path) or ""):
            eh["dead_letter"] = True
        for ent in ctx.hints.get("servicebus_entities") or []:
            if entity and ent.get("name") == entity:
                if ent.get("max_delivery") is not None:
                    eh["max_delivery"] = ent["max_delivery"]
                if ent.get("dead_letter") is not None:
                    eh.setdefault("dead_letter", ent["dead_letter"])
        where = f"{path}:{msg.handler_line or msg.line}"
        attrs = {
            "direction": msg.direction, "broker": broker, "entity": entity,
            "entity_type": msg.entity_type, "namespace": msg.namespace, "name_from": name_from,
            "name_key": name_key, "resolved_values": resolved, "subscription": subscription,
            "filter": None, "message_types": [],
            "payload": tn.norm(msg.payload, jf, jt) if msg.payload else None,
            "properties": dict(msg.properties),
            "published_by": f"{path}:{msg.line}" if msg.direction == "publish" else None,
            "handler": where if msg.direction == "subscribe" else None,
            "trigger": msg.trigger, "error_handling": eh, "library": msg.library}
        ev = [ctx.evidence(path, ln) for ln in sorted(set(msg.lines or [msg.line]))]
        item = make_item("messaging", sub, None, attrs, ev, self, "medium" if medium else "high")
        if msg.payload:
            schemas.add(msg.payload, jf, jt, ev[0])
        st.items.append(item)
        st.msgs.append((msg, path, jt, item))

    def _link_sends(self, ctx, tn, msc: MessagingScanner, st: _State, schemas) -> None:
        senders = [(m, it) for m, _p, _jt, it in st.msgs
                   if m.direction == "publish" and m.library == "azure-messaging-servicebus"]
        if not senders:
            return
        details: dict = {}
        for bean, path, line, jt in sorted(st.sends, key=lambda s: (s[1], s[2])):
            hit = [it for m, it in senders if bean and bean in m.beans]
            if not hit and len(senders) == 1:
                hit = [senders[0][1]]
            if not hit:
                st.unresolved(path)
                continue
            it = hit[0]
            if jt.fqn not in details:
                details[jt.fqn] = msc.message_details(jt)
            types, props, lines, payloads = details[jt.fqn]
            a = it.attributes
            pl = sorted({tn.norm(t, jt.jfile, jt) for t, _ln in payloads} - {None})
            if len(pl) == 1 and a.get("payload") in (None, pl[0]):
                a["payload"] = pl[0]
                for t, ln in payloads[:1]:
                    pev = ctx.evidence(jt.jfile.path, ln)
                    it.evidence.append(pev)
                    schemas.add(t, jt.jfile, jt, pev)
            if not a.get("_linked"):
                a["published_by"] = f"{path}:{line}"
            a["_linked"] = True
            a["message_types"] = sorted(set(a["message_types"]) | set(types))
            for k, v in props.items():
                if k == "app_properties":
                    a["properties"][k] = sorted(set(a["properties"].get(k, [])) | set(v))
                else:
                    a["properties"].setdefault(k, v)
            it.evidence.append(ctx.evidence(path, line))
            it.evidence += [ctx.evidence(jt.jfile.path, ln) for ln in lines[:5]]
        for _m, it in senders:
            it.attributes.pop("_linked", None)

    # ---- scheduled -----------------------------------------------------------------------
    def _scheduled(self, ctx, idx, jt, m, st: _State) -> None:
        path = jt.jfile.path
        scope = idx.method_scope(jt, m)
        anns = [a for a in m.annotations if a.name == "Scheduled"]
        for a in m.annotations:
            if a.name == "Schedules":
                anns += [x for x in ji.as_list(a.args.get("value", pos=0))
                         if isinstance(x, sx.Annotation)]
        for a in anns:
            for attr, trig in (("cron", "cron"), ("fixedRate", "fixed-rate"),
                               ("fixedRateString", "fixed-rate"), ("fixedDelay", "fixed-delay"),
                               ("fixedDelayString", "fixed-delay")):
                v = a.args.named.get(attr)
                if v is None:
                    continue
                expr, frm, rv = self._expr(ctx, idx, v, scope, st.sub)
                if expr is None and frm == "unknown":
                    st.unresolved(path)
                zone = a.args.get("zone")
                zone = idx.resolve_value(zone, scope).value if zone is not None else None
                attrs = {"trigger_type": trig, "expression": expr, "expression_from": frm,
                         "resolved_values": rv, "timezone": zone,
                         "handler": f"{path}:{a.line}", "name": f"{jt.decl.qualified}.{m.name}"}
                st.items.append(make_item("scheduled_job", st.sub, None, attrs,
                                          [ctx.evidence(path, a.line)], self,
                                          "high" if frm != "unknown" else "medium"))
                break

    def _expr(self, ctx, idx, v, scope, sub):
        if isinstance(v, int):
            return str(v), "literal", {}
        vs = idx.resolve_value(v, scope)
        if vs.kind == "literal" and not vs.holes:
            return vs.value, "literal", {}
        if vs.kind in ("config", "env") and not vs.value and not vs.prefix:
            rv = jd.public_expr_values(ctx, vs.key, sub)
            dflt = vs.default if vs.default and jd.CRON_LIKE.match(vs.default) else None
            return rv.get("default") or dflt, f"{vs.kind}:{vs.key}", rv
        return None, "unknown", {}

    def _quartz(self, ctx, vs, line, job, jf, jt, m, st: _State) -> None:
        expr, frm, rv = None, "unknown", {}
        if vs.kind == "literal" and not vs.holes:
            expr, frm = vs.value, "literal"
        elif vs.kind in ("config", "env") and not vs.value:
            rv = jd.public_expr_values(ctx, vs.key, st.sub)
            expr, frm = rv.get("default"), f"{vs.kind}:{vs.key}"
        else:
            st.unresolved(jf.path)
        attrs = {"trigger_type": "quartz", "expression": expr, "expression_from": frm,
                 "resolved_values": rv, "timezone": None, "handler": f"{jf.path}:{line}",
                 "name": job or f"{jt.decl.qualified}.{m.name}"}
        st.items.append(make_item("scheduled_job", st.sub, None, attrs,
                                  [ctx.evidence(jf.path, line)], self, "medium"))

    # ---- config reads + type-level data --------------------------------------------------
    def _read(self, st: _State, key: str, default, path: str, line: int, api: str) -> None:
        canon, _ = cc.canonical_key(key)
        if canon:
            st.config_reads.setdefault(canon, []).append((key, default, path, line, api))

    def _type_level(self, ctx, idx, jt, st: _State) -> None:
        path = jt.jfile.path
        for f in jt.fields.values():
            for a in f.annotations:
                if a.name == "Value":
                    for k, d in js.placeholder_keys(a.args.get("value", pos=0)):
                        self._read(st, k, d, path, a.line, "@Value")
            if js.simple_type(f.type) in jd.REDIS_TYPES:
                st.redis.append((path, f.line))
        if jt.props_prefix is not None:
            cp = next(a for a in jt.decl.annotations if a.name == "ConfigurationProperties")
            for f in jt.fields.values():
                if "static" in f.modifiers:
                    continue
                key = f"{jt.props_prefix}.{f.name}" if jt.props_prefix else f.name
                self._read(st, key, None, path, f.line if f.line else cp.line,
                           "@ConfigurationProperties")
        canns = {a.name: a for a in jt.decl.annotations}
        if "Entity" in canns:
            t = canns.get("Table")
            st.entities.append((jt, "sql", t.args.get("name") if t else None,
                                t.args.get("schema") if t else None, None,
                                canns["Entity"].line))
        if "Document" in canns:
            a = canns["Document"]
            coll = a.args.get("collection", "value", pos=0)
            st.entities.append((jt, "mongo", None, None, coll if isinstance(coll, str) else None,
                                a.line))
        # sdk symbols for the external-systems matcher (declared top-level types)
        if jt.outer_fqn is None:
            ctx.note_sdk_symbol(jt.decl.name, path, jt.decl.line)

    def _method_config(self, idx, jt, m, st: _State) -> None:
        path = jt.jfile.path
        for p in m.params:
            for a in p.annotations:
                if a.name == "Value":
                    for k, d in js.placeholder_keys(a.args.get("value", pos=0)):
                        self._read(st, k, d, path, a.line, "@Value")
        if m.body is None:
            return
        for n in idx.nodes(m, "method_invocation"):
            name = sx.text(n.child_by_field_name("name"))
            obj = sx.text(n.child_by_field_name("object"))
            al = n.child_by_field_name("arguments")
            args = sx.named_children(al) if al is not None else []
            if not args:
                continue
            v = sx.decode_string(args[0], "java")
            if not isinstance(v, str):
                continue
            ln = sx.line(n.child_by_field_name("name"))
            if obj == "System" and name == "getenv":
                self._read(st, v, None, path, ln, "System.getenv")
            elif name in ("getProperty", "getRequiredProperty") and "env" in obj.lower():
                self._read(st, v, None, path, ln, "Environment.getProperty")

    def _config_items(self, ctx, st: _State) -> None:
        for canon, reads in sorted(st.config_reads.items()):
            defs = sorted([d for d in ctx.config.defs(reads[0][0], st.sub)
                           if d.subproject == st.sub], key=lambda d: (d.file, d.line))
            name = defs[0].name if defs else sorted(r[0] for r in reads)[0]
            attrs = {"name": name, "canonical": canon,
                     "reads": sorted({(p, ln, api) for _k, _d, p, ln, api in reads}),
                     "defined_in": [], "values": {}, "value_kind": None,
                     "secret": None if defs else cc.key_is_secret(name), "kv_ref": None,
                     "ref": None, "provided_by": None,
                     "required": True if all(d is None for _k, d, *_ in reads) else None}
            attrs["reads"] = [{"file": p, "line": ln, "api": api} for p, ln, api in attrs["reads"]]
            ev = [ctx.evidence(p, ln) for _k, _d, p, ln, _a in reads]
            st.items.append(make_item("config_key", st.sub, canon, attrs, ev, self))

    # ---- data access ---------------------------------------------------------------------
    BEAN_STORES = {"OpenSearchClient": "opensearch", "OpenSearchAsyncClient": "opensearch",
                   "SessionPool": "nebula", "NebulaPool": "nebula", "MongoClient": "mongo",
                   "MongoTemplate": "mongo", "ReactiveMongoTemplate": "mongo"}

    def _store_sites(self, ctx, idx, jt, m, st: _State) -> None:
        """MongoTemplate / OpenSearch / NebulaGraph sites of one method into ``st``."""
        path, sub = jt.jfile.path, st.sub
        if any(a.name == "Bean" for a in m.annotations):
            kind = self.BEAN_STORES.get(js.simple_type(m.return_type))
            if kind:
                st.store_beans.append((kind, path, m.line))
        res = jd.store_sites(idx, jt, m)
        if res["unresolved"]:
            st.unresolved(path)
        for et, coll, op, line in res["mongo"]:
            st.mongo_ops.append((et, coll, op, path, line))
        for vs, op, line in res["opensearch"]:
            names, key, dflt = jd.name_values(ctx, idx, vs, sub)
            if not names:
                # index name not resolvable (env-provided / runtime): file stays partial; a
                # known config key still evidences the store
                st.unresolved(path)
                if vs.kind in ("config", "env") and not vs.prefix and not vs.value:
                    key = vs.key
                if not key:
                    continue
            st.os_sites.append((names, key, dflt, op, path, line))
        for kind, vs, line in res["nebula"]:
            if kind == "space":
                names, key, dflt = jd.name_values(ctx, idx, vs, sub)
                if key is None and vs.kind in ("config", "env") and not vs.prefix:
                    key = vs.key
                if names or key:
                    st.neb_space.append((names, key, dflt, path, line))
                continue
            verb, op, names, space_key = jd.ngql(vs)
            if verb is None:
                st.unresolved(path)
                continue
            if verb == "USE":
                if space_key:
                    vals, k, dflt = jd.name_values(
                        ctx, idx, js.source_of([js.Seg("config", space_key)]), sub)
                    st.neb_space.append((vals, k, dflt, path, line))
                elif names:
                    st.neb_space.append((names, None, False, path, line))
                else:
                    st.unresolved(path)
                continue
            if jd.ngql_name_hole(vs):
                st.unresolved(path)
            for nm in names:
                st.neb_rows.append((nm, op, path, line))
            if not names and op:
                st.neb_ev.append((op, path, line))

    @staticmethod
    def _opensearch_host(ctx, idx, sub, keys):
        """({host, database}, name_from key) of an OpenSearch store: the ``host``/``hosts``/
        ``uris`` field of the properties class whose index fields were read. The host comes
        from config public values only, never from a code default."""
        for pre in sorted({k.rsplit(".", 1)[0] for k in keys if "." in k}):
            for jt in idx.types.values():
                if jt.props_prefix != pre:
                    continue
                for fld in ("host", "hosts", "uris"):
                    if idx.find_field(jt, fld) is None:
                        continue
                    hk = f"{pre}.{fld}"
                    hv = ctx.config.public_values(hk, sub).get("default")
                    c = cc.classify("host", hv) if hv else None
                    host = c.record_value if c is not None and not c.secret else None
                    return {"host": host, "database": None}, hk
        return None, None

    def _data_items(self, ctx, idx, repos: dict, st: _State) -> None:
        sub = st.sub
        mine = [r for r in repos.values() if ctx.subproject_of(r.jt.jfile.path) == sub]
        used = {fqn for fqn, _op, _ln in st.repo_ops}
        for r in repos.values():
            if r.jt.fqn in used and r not in mine:
                mine.append(r)
        ops_by_repo: dict = {}
        for fqn, op, _ln in st.repo_ops:
            ops_by_repo.setdefault(fqn, []).append(op)
        stores: dict[str, dict] = {}

        def store(kind):
            return stores.setdefault(kind, {"rows": {}, "ev": [], "procs": [], "medium": False,
                                            "repos": False, "jdbc": False, "colls": [],
                                            "ops": [], "template": False, "keys": [],
                                            "spaces": []})

        def add_row(s, name, table, schema, defined_in, op):
            key = (name, table, schema)
            row = s["rows"].get(key)
            if row is None:
                s["rows"][key] = {"name": name, "table": table, "schema": schema,
                                  "defined_in": defined_in, "operation": op}
            else:
                row["operation"] = jd.rollup([row["operation"], op])
                row["defined_in"] = row["defined_in"] or defined_in
        ent_ops: dict = {}
        for r in mine:
            ops = ops_by_repo.get(r.jt.fqn) or r.declared
            if r.entity:
                et = idx.resolve_type(r.entity, r.jt.jfile, r.jt)
                ent_ops.setdefault(et.fqn if et else r.entity, []).append(jd.rollup(ops))
        for et, _coll, op, _f, _ln in st.mongo_ops:
            if et is not None:
                ent_ops.setdefault(et.fqn, []).append(op)
        for jt, kind, table, schema, coll, line in st.entities:
            s = store(kind)
            add_row(s, jt.decl.name, table if isinstance(table, str) else None,
                    schema if isinstance(schema, str) else None,
                    f"{jt.jfile.path}:{jt.decl.line}", jd.rollup(ent_ops.get(jt.fqn, [])))
            if coll:
                s["colls"].append(coll)
            s["ev"].append(ctx.evidence(jt.jfile.path, line))
        for r in mine:
            s = store(r.store)
            s["repos"] = True
            et = idx.resolve_type(r.entity, r.jt.jfile, r.jt) if r.entity else None
            if r.entity and not any(row["name"] == js.simple_type(r.entity)
                                    for row in s["rows"].values()):
                add_row(s, js.simple_type(r.entity), None, None,
                        f"{et.jfile.path}:{et.decl.line}" if et else None,
                        jd.rollup(ent_ops.get(et.fqn if et else r.entity, [])))
            s["ev"].append(ctx.evidence(r.jt.jfile.path, r.jt.decl.line))
            for sch, t, op, f, ln in r.tables:
                add_row(s, t, t, sch, f"{f}:{ln}", op)
                s["ev"].append(ctx.evidence(f, ln))
                s["medium"] = True
            for nm, f, ln in r.procs:
                s["procs"].append({"name": nm, "evidence": f"{f}:{ln}"})
                s["ev"].append(ctx.evidence(f, ln))
        for sql, f, ln in st.jdbc:
            s = store("sql")
            s["jdbc"] = True
            s["medium"] = True
            for sch, t in jd.sql_tables(sql):
                add_row(s, t, t, sch, f"{f}:{ln}", jd.sql_op(sql))
            s["ev"].append(ctx.evidence(f, ln))
        for nm, f, ln in st.procs:
            s = store("sql")
            s["procs"].append({"name": nm, "evidence": f"{f}:{ln}"})
            s["ev"].append(ctx.evidence(f, ln))
        for f, ln in st.redis:
            s = store("redis")
            s["medium"] = True
            s["ev"].append(ctx.evidence(f, ln))
        for et, coll, op, f, ln in st.mongo_ops:
            s = store("mongo")
            s["template"] = True
            if et is not None:
                doc = next((a for a in et.decl.annotations if a.name == "Document"), None)
                dc = doc.args.get("collection", "value", pos=0) if doc is not None else None
                if not any(row["name"] == et.decl.name for row in s["rows"].values()):
                    add_row(s, et.decl.name, None, None, f"{et.jfile.path}:{et.decl.line}",
                            jd.rollup(ent_ops.get(et.fqn, [])))
                if isinstance(dc, str):
                    s["colls"].append(dc)
            if coll:
                s["colls"].append(coll)
            s["ops"].append(op)
            s["ev"].append(ctx.evidence(f, ln))
        for names, key, dflt, op, f, ln in st.os_sites:
            s = store("opensearch")
            for nm in names:
                add_row(s, nm, nm, None, f"{f}:{ln}", op)
                s["colls"].append(nm)
            if not names:
                s["ops"].append(op)
            s["medium"] = s["medium"] or dflt or len(names) != 1
            if key:
                s["keys"].append(key)
            s["ev"].append(ctx.evidence(f, ln))
        for nm, op, f, ln in st.neb_rows:
            s = store("nebula")
            add_row(s, nm, nm, None, f"{f}:{ln}", op)
            s["ev"].append(ctx.evidence(f, ln))
        for op, f, ln in st.neb_ev:
            s = store("nebula")
            s["ops"].append(op)
            s["ev"].append(ctx.evidence(f, ln))
        for names, key, dflt, f, ln in st.neb_space:
            s = store("nebula")
            s["spaces"].append((tuple(names), key, dflt))
            s["ev"].append(ctx.evidence(f, ln))
        for kind, f, ln in st.store_beans:  # config bean of a store the subproject uses
            if kind in stores and stores[kind]["ev"]:
                stores[kind]["ev"].append(ctx.evidence(f, ln))
        for kind in sorted(stores):
            s = stores[kind]
            if not s["ev"]:
                continue
            if kind == "sql":
                ident, key, _raw = jd.store_identity(ctx, sub, ("spring.datasource.url",
                                                                "spring.datasource.jdbc-url",
                                                                "spring.r2dbc.url"))
                if key is None:
                    ident, key, _raw = jd.datasource_fallback(ctx, sub)
                st_type = (ident or {}).get("store_type") or jd.guess_sql_store(ctx, sub)
                orm = "spring-data" if s["repos"] else ("jpa" if s["rows"] and not s["jdbc"]
                                                       else "jdbctemplate")
            elif kind == "mongo":
                ident, key, _raw = jd.store_identity(ctx, sub, ("spring.data.mongodb.uri",))
                st_type = "mongo"
                orm = "mongo-template" if s["template"] and not s["repos"] else "spring-data"
                if ident is None:
                    for hk in ("spring.data.mongodb.host",):
                        if [d for d in ctx.config.defs(hk, sub) if d.subproject == sub]:
                            key = hk
            elif kind == "opensearch":
                st_type, orm = "opensearch", "opensearch-client"
                ident, key = self._opensearch_host(ctx, idx, sub, s["keys"])
            elif kind == "nebula":
                st_type, orm = "nebula", "nebula-client"
                s["medium"] = True
                names = sorted({n for ns, _k, _d in s["spaces"] for n in ns})
                keys = sorted({k for _n, k, _d in s["spaces"] if k})
                ident = {"host": None, "database": names[0] if len(names) == 1 else None}
                key = keys[0] if len(keys) == 1 else None
            else:
                ident, key, _raw = jd.store_identity(ctx, sub, ("spring.data.redis.url",
                                                                "spring.redis.url"))
                st_type, orm = "redis", "redis-client"
                if ident is None:
                    for hk in ("spring.data.redis.host", "spring.redis.host"):
                        if [d for d in ctx.config.defs(hk, sub) if d.subproject == sub]:
                            key = hk
                            hv = ctx.config.public_values(hk, sub).get("default")
                            ident = {"store_type": "redis", "host": hv, "database": None}
                            break
            rows = sorted(s["rows"].values(), key=lambda r: (r["name"], r["table"] or "",
                                                             r["schema"] or ""))
            attrs = {"store_type": st_type, "host": (ident or {}).get("host"),
                     "database": (ident or {}).get("database"),
                     "name_from": f"config:{key}" if key else None, "orm": orm,
                     "entities": rows, "collections": sorted(set(s["colls"])),
                     "stored_procedures": sorted(s["procs"], key=lambda p: (p["name"],
                                                                            p["evidence"])),
                     "operation": jd.rollup([r["operation"] for r in rows] + s["ops"]),
                     "owns_schema": None, "routines": [], "tables_ddl": []}
            st.items.append(make_item("data_access", sub, None, attrs, s["ev"], self,
                                      "medium" if s["medium"] else "high"))


__all__ = ["JavaSpring", "parse_type"]

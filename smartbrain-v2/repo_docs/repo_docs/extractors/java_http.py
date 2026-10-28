"""Outbound HTTP call detection for java.spring (docs/EXTRACTORS.md#outbound_http).

RestTemplate, WebClient / RestClient (``.baseUrl`` from builder chains, fields, ``@Bean`` methods or a
same-class factory method), OkHttp ``Request.Builder``, Apache ``HttpGet/HttpPost``; one-level
wrapper following (a same-repo method whose HTTP call takes its URL from a parameter).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import java_symbols as js
from . import syntax as sx

VERBS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
# name -> (method, url idx, request idx, response idx); method None = from the HttpMethod arg
REST_TEMPLATE = {
    "getForObject": ("GET", 0, None, 1), "getForEntity": ("GET", 0, None, 1),
    "postForObject": ("POST", 0, 1, 2), "postForEntity": ("POST", 0, 1, 2),
    "postForLocation": ("POST", 0, 1, None), "put": ("PUT", 0, 1, None),
    "patchForObject": ("PATCH", 0, 1, 2), "delete": ("DELETE", 0, None, None),
    "headForHeaders": ("HEAD", 0, None, None), "optionsForAllow": ("OPTIONS", 0, None, None),
    "exchange": (None, 0, 2, 3), "execute": (None, 0, None, None),
}
APACHE = {"HttpGet": "GET", "HttpPost": "POST", "HttpPut": "PUT", "HttpDelete": "DELETE",
          "HttpPatch": "PATCH", "HttpHead": "HEAD", "HttpOptions": "OPTIONS"}
OKHTTP_VERBS = {"get": "GET", "post": "POST", "put": "PUT", "delete": "DELETE",
                "patch": "PATCH", "head": "HEAD"}


@dataclass
class Call:
    client: str
    method: str | None                 # GET.. / None unknown / "param:<i>" (wrapper)
    url: js.ValueSource | None         # full URL (template/okhttp/apache/wrapper)
    base: js.ValueSource | None        # web/rest client base URL (None = unknown)
    path: js.ValueSource | None        # web/rest client uri(...)
    raw: str
    request: str | None
    response: str | None
    line: int
    lines: list = field(default_factory=list)
    response_param: int | None = None
    headers: list = field(default_factory=list)
    via_wrapper: str | None = None
    client_name: str | None = None
    request_param: int | None = None
    wrapper_file: str | None = None    # innermost HTTP call (via_wrapper) file / line
    wrapper_line: int | None = None
    wrapper_depth: int = 0
    extra_evidence: list = field(default_factory=list)  # (file, line) outside the call file

    def is_wrapper(self) -> bool:
        src = self.url if self.url is not None else self.path
        return src is not None and src.kind == "param"


@dataclass
class Wrapper:
    owner: str
    name: str
    nparams: int
    url_index: int
    call: Call                          # innermost HTTP call
    file: str                           # innermost HTTP call's file
    method_param: int | None
    response_param: int | None
    request_param: int | None = None
    depth: int = 1                      # 1 = the method holds the HTTP call itself
    segs: tuple = ()                    # innermost URL segments in this method's params
    query: list = field(default_factory=list)


GENERIC_TYPES = frozenset({"Object", "?"})
# "no base URL" (a builder chain without baseUrl): distinct from None = "base unknown"
NO_BASE = js.ValueSource("literal", "", segs=())


def is_no_base(vs) -> bool:
    return vs is not None and vs.kind == "literal" and not vs.segs and not vs.value


def _concrete(ty: str | None) -> str | None:
    """Drop ``Object`` / ``T`` / single-letter generics: they say nothing about the payload."""
    if not ty:
        return None
    s = js.strip_generics(ty)
    if s in GENERIC_TYPES or (len(s) == 1 and s.isupper()):
        return None
    return ty


def _args(node) -> list:
    al = node.child_by_field_name("arguments")
    return sx.named_children(al) if al is not None else []


def _name(node) -> str:
    return sx.text(node.child_by_field_name("name"))


MOCK_STUBS = frozenset({"when", "verify", "given", "then", "doReturn", "doThrow", "doAnswer",
                        "doNothing", "thenReturn", "willReturn"})


def _in_mock_stub(node) -> bool:
    """True when ``node`` sits inside the arguments of a Mockito/BDDMockito stub or verify call
    (``when(client.get())``): those are test doubles, not call sites."""
    p = node.parent
    while p is not None:
        if p.type == "argument_list" and p.parent is not None and \
                p.parent.type == "method_invocation" and _name(p.parent) in MOCK_STUBS:
            return True
        if p.type in ("method_declaration", "constructor_declaration", "lambda_expression"):
            return False
        p = p.parent
    return False


def _nline(node) -> int:
    n = node.child_by_field_name("name")
    return sx.line(n if n is not None else node)


def class_type(node) -> str | None:
    """``Foo.class`` -> ``Foo``; ``new ParameterizedTypeReference<List<Foo>>(){}`` -> ``List<Foo>``."""
    if node is None:
        return None
    if node.type == "class_literal":
        kids = sx.named_children(node)
        return sx.text(kids[0]) if kids else None
    if node.type == "object_creation_expression":
        ty = sx.text(node.child_by_field_name("type"))
        if ty.startswith("ParameterizedTypeReference<"):
            return ty[len("ParameterizedTypeReference<"):-1]
    return None


class HttpScanner:
    def __init__(self, idx: js.JavaIndex):
        self.idx = idx
        self._memo: dict = {}
        self._wrappers: dict | None = None

    # ---- helpers -------------------------------------------------------------------------
    def _http_method(self, node, scope) -> str | None:
        if node is None:
            return None
        t = sx.text(node)
        last = t.rsplit(".", 1)[-1]
        if last in VERBS and ("HttpMethod" in t or "RequestMethod" in t or t == last):
            return last
        if node.type == "identifier" and t in scope.params:
            return f"param:{scope.params[t][0]}"
        vs = self.idx.resolve_expr(node, scope)
        if vs.kind == "literal" and (vs.value or "").upper() in VERBS:
            return vs.value.upper()
        return None

    def _req_type(self, node, scope) -> str | None:
        """Type of a request body argument (HttpEntity unwrapped)."""
        if node is None:
            return None
        if node.type == "object_creation_expression":
            ty = sx.text(node.child_by_field_name("type"))
            if js.simple_type(ty) in ("HttpEntity", "RequestEntity"):
                a = _args(node)
                if "<" in ty and not ty.endswith("<>"):
                    return ty[ty.index("<") + 1:-1]
                return self._req_type(a[0], scope) if a else None
            return ty
        if node.type == "identifier":
            nm = sx.text(node)
            vals = scope.locals.get(nm) or []
            ty = self.idx.type_of(node, scope)
            if ty and js.simple_type(ty) in ("HttpEntity", "RequestEntity"):
                if "<" in ty and not ty.endswith("<>"):
                    inner = ty[ty.index("<") + 1:-1]
                    if inner not in ("?", "Object"):
                        return inner
                if len(vals) == 1 and vals[0] is not None:
                    return self._req_type(vals[0], scope)
                return None
            if ty:
                return ty
            if len(vals) == 1 and vals[0] is not None:
                return self._req_type(vals[0], scope)
        if node.type == "null_literal":
            return None
        return self.idx.type_of(node, scope)

    def _resp(self, node, scope) -> tuple[str | None, int | None]:
        ct = class_type(node)
        if ct:
            return ct, None
        if node is not None and node.type == "identifier" and sx.text(node) in scope.params:
            return None, scope.params[sx.text(node)][0]
        if node is not None and node.type == "identifier" and sx.text(node) not in scope.locals:
            # static final ParameterizedTypeReference<X> MAP_TYPE_REF = new ...<X>() {}
            hit = self.idx.find_field(scope.jtype, sx.text(node)) if scope.jtype else None
            if hit is not None and hit[1].value is not None and \
                    {"static", "final"} <= set(hit[1].modifiers):
                ct = class_type(hit[1].value)
                if ct:
                    return ct, None
        return None, None

    # ---- per method ----------------------------------------------------------------------
    def calls(self, jt: js.JType, m: sx.MethodDecl) -> list[Call]:
        key = (jt.fqn, m.line, m.name)
        if key in self._memo:
            return self._memo[key]
        out: list[Call] = []
        if m.body is not None:
            scope = self.idx.method_scope(jt, m)
            for n in self.idx.nodes(m, "*"):
                c = None
                if n.type in ("method_invocation", "object_creation_expression") and \
                        _in_mock_stub(n):
                    continue
                if n.type == "method_invocation":
                    c = self._rest_template(n, scope) or self._web_client(n, scope)
                elif n.type == "object_creation_expression":
                    c = self._okhttp(n, scope) or self._apache(n, scope)
                if c is not None:
                    out.append(c)
        self._memo[key] = out
        return out

    def _rest_template(self, n, scope) -> Call | None:
        name = _name(n)
        if name not in REST_TEMPLATE:
            return None
        obj = n.child_by_field_name("object")
        if obj is None:
            return None
        ty = js.simple_type(self.idx.type_of(obj, scope) or "")
        if not (ty in ("RestTemplate", "RestOperations", "TestRestTemplate")
                or "resttemplate" in sx.text(obj).lower()):
            return None
        meth, ui, ri, pi = REST_TEMPLATE[name]
        args = _args(n)
        if len(args) <= ui:
            return None
        if meth is None:
            if len(args) < 2:
                return None
            meth = self._http_method(args[1], scope)
        url = self.idx.resolve_expr(args[ui], scope)
        req = self._req_type(args[ri], scope) if ri is not None and len(args) > ri else None
        resp, rparam = self._resp(args[pi], scope) if pi is not None and len(args) > pi \
            else (None, None)
        return Call("resttemplate", meth, url, None, None, sx.text(args[ui]), req, resp,
                    _nline(n), [_nline(n)], rparam,
                    request_param=self._req_param(args[ri], scope)
                    if ri is not None and len(args) > ri else None)

    def _req_param(self, node, scope) -> int | None:
        """Index of the method parameter a request body comes from (``new HttpEntity<>(p, h)``,
        directly or through a local), for wrapper call sites."""
        for _ in range(2):
            if node is None:
                return None
            if node.type == "identifier":
                nm = sx.text(node)
                if nm in scope.params:
                    return scope.params[nm][0]
                vals = scope.locals.get(nm) or []
                node = vals[0] if len(vals) == 1 else None
                continue
            if node.type == "object_creation_expression" and js.simple_type(sx.text(
                    node.child_by_field_name("type"))) in ("HttpEntity", "RequestEntity"):
                a = _args(node)
                if a and a[0].type == "identifier" and sx.text(a[0]) in scope.params:
                    return scope.params[sx.text(a[0])][0]
            return None
        return None

    # ---- WebClient / RestClient ----------------------------------------------------------
    def client_base(self, node, scope, depth: int = 0):
        """(client, base ValueSource | None, [(file, line)] of the baseUrl) when ``node``
        evaluates to a WebClient / RestClient, else None."""
        if node is None or depth > 4:
            return None
        t = node.type
        if t in ("identifier", "field_access"):
            nm = sx.text(node)
            nm = nm[5:] if nm.startswith("this.") else nm
            ty = js.simple_type(self.idx.type_of(node, scope) or "")
            client = {"WebClient": "webclient", "RestClient": "restclient"}.get(ty)
            vals = scope.locals.get(nm) if t == "identifier" else None
            if vals:
                if len(vals) == 1 and vals[0] is not None:
                    r = self.client_base(vals[0], scope, depth + 1)
                    if r:
                        return r
                return (client, None, []) if client else None
            if t == "identifier" and nm in scope.params:
                # a parameter shadows a same-named field (ctor `this.c = c`): bind it through
                # its @Qualifier / name to a @Bean, else the repo's only @Bean of that type
                if not client:
                    return None
                return self._bean_base(client, ty, self.idx.qualifier_of(node, scope), depth) \
                    or (client, None, [])
            hit = self.idx.find_field(scope.jtype, nm) if scope.jtype is not None else None
            if hit is not None:
                fjt, f = hit
                val = f.value if f.value is not None else fjt.ctor_values.get(f.name)
                if val is not None:
                    sc = self.idx.type_scope(fjt)
                    ctor = next((mm for mm in fjt.methods if mm.kind == "constructor"
                                 and mm.node.start_byte <= val.start_byte < mm.node.end_byte),
                                None)
                    if ctor is not None:
                        sc = self.idx.method_scope(fjt, ctor)
                    r = self.client_base(val, sc, depth + 1)
                    if r:
                        return r
                else:
                    bound = self.idx.lombok_binding(fjt, f.name)
                    if bound is not None:
                        r = self.client_base(bound[0], bound[1], depth + 1)
                        if r:
                            return r
            if client:
                bean = self.idx.qualifier_of(node, scope)
                b = self.idx.beans.get(bean) if bean else None
                if b is not None:
                    r = self._from_method(b[1], b[0], depth)
                    if r:
                        return r
                return client, None, []
            return None
        if t == "method_invocation":
            chain = js.invocation_chain(node)
            root = chain[0][0]
            names = [c[1] for c in chain[1:]]
            rt = sx.text(root) if root is not None else ""
            client = None
            if rt in ("WebClient", "RestClient"):
                client = rt.lower()
            elif root is not None and root.type in ("identifier", "field_access"):
                ty = self.idx.type_of(root, scope) or ""
                if "WebClient" in ty:
                    client = "webclient"
                elif "RestClient" in ty:
                    client = "restclient"
            if client is None and root is None and len(chain) >= 2 and scope.jtype is not None:
                first = chain[1]
                m = next((mm for tt in self.idx.outer_chain(scope.jtype) for mm in tt.methods
                          if mm.name == first[1] and len(mm.params) == len(first[2])), None)
                if m is not None:
                    owner = next(tt for tt in self.idx.outer_chain(scope.jtype)
                                 if m in tt.methods)
                    return self._from_method(owner, m, depth + 1)
                return None
            if client is None:
                return None
            found = None
            for cn, nm, args in chain[1:]:
                if nm in ("baseUrl", "create") and args:  # a later baseUrl wins
                    found = (client, self.idx.resolve_expr(args[0], scope),
                             [(scope.jfile.path, _nline(cn))])
            if found is not None:
                return found
            if root is not None and root.type == "identifier" and \
                    rt not in ("WebClient", "RestClient"):
                # WebClient.Builder builder = WebClient.builder().baseUrl(x)...; builder.build()
                vals = scope.locals.get(sx.text(root)) or []
                if len(vals) == 1 and vals[0] is not None:
                    r = self.client_base(vals[0], scope, depth + 1)
                    if r is not None:
                        return r[0] or client, r[1], r[2]
                elif sx.text(root) in scope.params or vals:
                    return client, None, []
                else:
                    r = self.client_base(root, scope, depth + 1)
                    return r if r is not None else (client, None, [])
            if "builder" in names or ("create" in names and rt in ("WebClient", "RestClient")):
                # a builder chain without baseUrl(...): "no base", uri(...) is the full URL
                return client, NO_BASE, []
            if "mutate" in names:
                return client, None, []
            return None
        return None

    def _bean_base(self, client, ty, bean, depth):
        """Base of the @Bean a client parameter is bound to: by @Qualifier / name (when that
        bean returns the same client type), else the repo's only @Bean returning that type."""
        b = self.idx.beans.get(bean) if bean else None
        if b is not None and js.simple_type(b[0].return_type) != ty:
            b = None
        if b is None:
            cands = self.idx.beans_of_type(ty)
            b = cands[0] if len(cands) == 1 else None
        if b is None:
            return None
        return self._from_method(b[1], b[0], depth)

    def _from_method(self, jt, m, depth):
        if m.body is None:
            return None
        rets = [r for r in sx.walk(m.body) if r.type == "return_statement"]
        if len(rets) != 1 or not sx.named_children(rets[0]):
            return None
        return self.client_base(sx.named_children(rets[0])[0], self.idx.method_scope(jt, m),
                                depth + 1)

    def _web_client(self, n, scope) -> Call | None:
        name = _name(n)
        args = _args(n)
        if name.upper() in VERBS and not args:
            meth = name.upper()
        elif name == "method" and len(args) == 1:
            meth = self._http_method(args[0], scope)
        else:
            return None
        base = self.client_base(n.child_by_field_name("object"), scope)
        if base is None:
            return None
        client, base_vs, where = base
        path, req, resp, headers, raw = None, None, None, [], ""
        # baseUrl(...) lines: same file -> call lines, another file (@Bean) -> extra evidence
        lines = [ln for f, ln in where if f == scope.jfile.path] + [_nline(n)]
        extra = sorted({(f, ln) for f, ln in where if f != scope.jfile.path})
        cur = n
        while cur.parent is not None and cur.parent.type == "method_invocation" and \
                cur.parent.child_by_field_name("object") == cur:
            cur = cur.parent
            nm, a = _name(cur), _args(cur)
            if nm == "uri" and a:
                raw = sx.text(a[0])
                lines.append(_nline(cur))
                if a[0].type == "lambda_expression":
                    body = a[0].child_by_field_name("body")
                    inv = next((x for x in sx.walk(body) if x.type == "method_invocation"), None) \
                        if body is not None else None
                    if inv is not None:
                        segs, q = self.idx._uri_builder(js.invocation_chain(inv), scope,
                                                        js.MAX_DEPTH, frozenset())
                        path = js.source_of(segs, q)
                else:
                    path = self.idx.resolve_expr(a[0], scope)
            elif nm in ("bodyToMono", "toEntity", "body") and a and class_type(a[-1]):
                if nm == "body" and len(a) == 2:
                    req = class_type(a[1])
                elif nm == "body" and client == "webclient":
                    req = class_type(a[0])
                else:
                    resp = class_type(a[0])
            elif nm in ("bodyToFlux", "toEntityList") and a and class_type(a[0]):
                resp = f"List<{class_type(a[0])}>"
            elif nm in ("bodyValue", "body", "syncBody") and a:
                inner = a[0]
                if inner.type == "method_invocation" and _name(inner) == "fromValue":
                    ia = _args(inner)
                    inner = ia[0] if ia else None
                req = self._req_type(inner, scope)
            elif nm == "header" and a:
                h = sx.decode_string(a[0], "java")
                if isinstance(h, str):
                    headers.append(h)
        return Call(client, meth, None, base_vs, path, raw, req, resp, _nline(n),
                    sorted(set(lines)), headers=headers, extra_evidence=extra)

    # ---- OkHttp / Apache -----------------------------------------------------------------
    def _okhttp(self, n, scope) -> Call | None:
        ty = sx.text(n.child_by_field_name("type"))
        if not (ty.endswith("Request.Builder") or (ty == "Builder" and any(
                "okhttp3" in v for v in scope.jfile.imports.values()))):
            return None
        url, meth, lines, headers, raw = None, None, [sx.line(n)], [], ""
        cur = n
        while cur.parent is not None and cur.parent.type == "method_invocation" and \
                cur.parent.child_by_field_name("object") == cur:
            cur = cur.parent
            nm, a = _name(cur), _args(cur)
            if nm == "url" and a:
                url = self.idx.resolve_expr(a[0], scope)
                raw = sx.text(a[0])
                lines.append(_nline(cur))
            elif nm in OKHTTP_VERBS:
                meth = OKHTTP_VERBS[nm]
                lines.append(_nline(cur))
            elif nm == "method" and a:
                meth = self._http_method(a[0], scope)
            elif nm in ("header", "addHeader") and a:
                h = sx.decode_string(a[0], "java")
                if isinstance(h, str):
                    headers.append(h)
        if url is None:
            return None
        if meth is None:
            var = cur.parent.child_by_field_name("name") \
                if cur.parent is not None and cur.parent.type == "variable_declarator" else None
            if var is not None and scope.method is not None and scope.method.body is not None:
                vn = sx.text(var)
                for x in sx.walk(scope.method.body):
                    if x.type == "method_invocation" and \
                            sx.text(x.child_by_field_name("object")) == vn and \
                            _name(x) in OKHTTP_VERBS:
                        meth = OKHTTP_VERBS[_name(x)]
                        break
            meth = meth or "GET"
        return Call("okhttp", meth, url, None, None, raw, None, None, sx.line(n),
                    sorted(set(lines)), headers=headers)

    def _apache(self, n, scope) -> Call | None:
        ty = js.simple_type(sx.text(n.child_by_field_name("type")))
        if ty not in APACHE:
            return None
        a = _args(n)
        if not a:
            return None
        return Call("apache-httpclient", APACHE[ty], self.idx.resolve_expr(a[0], scope), None,
                    None, sx.text(a[0]), None, None, sx.line(n), [sx.line(n)])

    # ---- wrappers ------------------------------------------------------------------------
    MAX_WRAPPER_DEPTH = 3

    def wrappers(self) -> dict:
        """(owner fqn, method, nparams) -> Wrapper, repo-wide. Round 1: methods whose own HTTP
        call takes its URL from a parameter. Rounds 2..3: methods whose call of a registered
        wrapper still has a parameter-derived URL (public -> private helper -> exchange).
        Bounded, source order, setdefault: deterministic."""
        if self._wrappers is not None:
            return self._wrappers
        out: dict = {}
        for jt in self.idx.types.values():
            for m in jt.methods:
                for c in self.calls(jt, m):
                    if not c.is_wrapper():
                        continue
                    src = c.url if c.url is not None else c.path
                    mp = int(c.method[6:]) if c.method and c.method.startswith("param:") else None
                    out.setdefault((jt.fqn, m.name, len(m.params)),
                                   Wrapper(jt.fqn, m.name, len(m.params), int(src.key), c,
                                           jt.jfile.path, mp, c.response_param,
                                           c.request_param, 1, tuple(src.segs),
                                           list(src.query)))
        for depth in range(2, self.MAX_WRAPPER_DEPTH + 1):
            added: dict = {}
            for jt in self.idx.types.values():
                for m in jt.methods:
                    k = (jt.fqn, m.name, len(m.params))
                    if k in out or k in added:
                        continue
                    for c, w in self._wrapper_calls(jt, m, out):
                        if not c.is_wrapper():
                            continue
                        src = c.url if c.url is not None else c.path
                        mp = int(c.method[6:]) if c.method and c.method.startswith("param:") \
                            else None
                        added.setdefault(k, Wrapper(
                            jt.fqn, m.name, len(m.params), int(src.key), w.call, w.file, mp,
                            c.response_param, c.request_param, w.depth + 1, tuple(src.segs),
                            list(src.query)))
            if not added:
                break
            out.update(added)
        self._wrappers = out
        return out

    def wrapper_calls(self, jt: js.JType, m: sx.MethodDecl) -> list[Call]:
        """Call sites in ``m`` of a registered wrapper (resolved at the call site, medium)."""
        return [c for c, _w in self._wrapper_calls(jt, m, self.wrappers())]

    def _wrapper_calls(self, jt: js.JType, m: sx.MethodDecl, ws: dict) -> list[tuple]:
        if not ws or m.body is None:
            return []
        names = self._memo.get(("wnames", id(ws), len(ws)))
        if names is None:
            names = {w.name for w in ws.values()}
            self._memo[("wnames", id(ws), len(ws))] = names
        nodes = [n for n in self.idx.nodes(m, "method_invocation")
                 if _name(n) in names and not _in_mock_stub(n)]
        if not nodes:
            return []
        scope = self.idx.method_scope(jt, m)
        out = []
        for n in nodes:
            args = _args(n)
            obj = n.child_by_field_name("object")
            if obj is None or obj.type == "this":
                owners = [t.fqn for t in self.idx.outer_chain(jt)]
                owners += [s.fqn for s in self.idx.supertypes(jt)]
            else:
                ty = self.idx.type_of(obj, scope)
                t = self.idx.resolve_type(ty, scope.jfile, jt) if ty else None
                owners = [t.fqn] if t is not None else []
            w = next((ws.get((o, _name(n), len(args))) for o in owners
                      if (o, _name(n), len(args)) in ws), None)
            if w is None or (w.owner == jt.fqn and w.name == m.name
                             and w.nparams == len(m.params)):
                continue
            inner = w.call
            # substitute every parameter segment of the innermost URL with the call-site value
            segs, query = [], list(w.query)
            for s in w.segs:
                if s.kind == "param" and s.text.isdigit() and int(s.text) < len(args):
                    v = self.idx.resolve_expr(args[int(s.text)], scope)
                    segs += list(v.segs) or [js.Seg("unknown", sx.text(args[int(s.text)])[:80])]
                    query += [q for q in v.query if q not in query]
                else:
                    segs.append(s)
            url = js.source_of(segs, query)
            meth = inner.method if w.method_param is None else None
            if w.method_param is not None and w.method_param < len(args):
                meth = self._http_method(args[w.method_param], scope)
            resp, rparam = inner.response, None
            if w.response_param is not None and w.response_param < len(args):
                rt, rparam = self._resp(args[w.response_param], scope)
                resp = rt or (None if rparam is not None else resp)
            req, qparam = _concrete(inner.request), None
            if w.request_param is not None and w.request_param < len(args):
                a = args[w.request_param]
                if a.type == "identifier" and sx.text(a) in scope.params:
                    qparam = scope.params[sx.text(a)][0]
                req = _concrete(self._req_type(a, scope)) or (None if qparam is not None
                                                              else req)
            raw = " + ".join(sx.text(args[int(s.text)]) for s in w.segs
                             if s.kind == "param" and s.text.isdigit()
                             and int(s.text) < len(args))
            c = Call(inner.client, meth, url if inner.url is not None else None, inner.base,
                     url if inner.url is None else None, raw, req, resp, _nline(n), [_nline(n)],
                     rparam, via_wrapper=f"{w.file}:{inner.line}", headers=list(inner.headers),
                     request_param=qparam, wrapper_file=w.file, wrapper_line=inner.line,
                     wrapper_depth=w.depth)
            out.append((c, w))
        return out

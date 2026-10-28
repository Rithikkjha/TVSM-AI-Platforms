"""Inbound HTTP for java.spring (plan.md 'Route combination rules', docs/EXTRACTORS.md#inbound_http).

Spring MVC/WebFlux: class ``@RequestMapping`` x method ``@Get/Post/Put/Patch/DeleteMapping`` /
``@RequestMapping(method=...)`` (cartesian over arrays; a method path starting with ``/`` is still
relative), values from constants or ``${k:default}`` placeholders (config index ``default`` env, else
the literal default), then ``server.servlet.context-path`` + ``spring.mvc.servlet.path`` (WebFlux:
``spring.webflux.base-path``) of the subproject's config. JAX-RS ``@ApplicationPath`` / ``@Path``.
"""
from __future__ import annotations

import re

from .. import pathnorm
from . import java_symbols as js
from . import syntax as sx
from .java_types import parse_type

MAPPINGS = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
            "PatchMapping": "PATCH", "DeleteMapping": "DELETE", "RequestMapping": None}
JAXRS_VERBS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
HTTP_STATUS = {
    "CONTINUE": 100, "OK": 200, "CREATED": 201, "ACCEPTED": 202, "NO_CONTENT": 204,
    "PARTIAL_CONTENT": 206, "MOVED_PERMANENTLY": 301, "FOUND": 302, "SEE_OTHER": 303,
    "NOT_MODIFIED": 304, "TEMPORARY_REDIRECT": 307, "PERMANENT_REDIRECT": 308,
    "BAD_REQUEST": 400, "UNAUTHORIZED": 401, "PAYMENT_REQUIRED": 402, "FORBIDDEN": 403,
    "NOT_FOUND": 404, "METHOD_NOT_ALLOWED": 405, "NOT_ACCEPTABLE": 406, "REQUEST_TIMEOUT": 408,
    "CONFLICT": 409, "GONE": 410, "PRECONDITION_FAILED": 412, "PAYLOAD_TOO_LARGE": 413,
    "UNSUPPORTED_MEDIA_TYPE": 415, "UNPROCESSABLE_ENTITY": 422, "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500, "NOT_IMPLEMENTED": 501, "BAD_GATEWAY": 502,
    "SERVICE_UNAVAILABLE": 503, "GATEWAY_TIMEOUT": 504}
PARAM_ANN = {"PathVariable": "path", "RequestParam": "query", "RequestHeader": "header",
             "CookieValue": "cookie", "RequestBody": "body", "RequestPart": "form",
             "ModelAttribute": "query", "PathParam": "path", "QueryParam": "query",
             "HeaderParam": "header", "FormParam": "form", "CookieParam": "cookie"}
JAXRS_CONTEXT = {"Context", "Suspended", "BeanParam"}


def as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def status_of(v) -> int | None:
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    if isinstance(v, sx.Ref):
        return HTTP_STATUS.get(v.name.rsplit(".", 1)[-1])
    return None


def route_text(ctx, idx: js.JavaIndex, sub: str, v, scope) -> str | None:
    """Resolve a mapping value to a route string, or None when any part is unresolved."""
    if v is None or v == "":
        return ""
    vs = idx.resolve_value(v, scope)
    out = []
    for s in vs.segs:
        if s.kind == "lit":
            out.append(s.text)
        elif s.kind in ("config", "env"):
            r = ctx.config.resolve("${" + s.text + "}", "default", sub)
            val = r.value
            if val is None and s.default is not None:
                val = ctx.config.resolve(s.default, "default", sub).value
                val = s.default if val is None else val
            if val is None:
                return None
            out.append(val)
        else:
            return None
    return "".join(out)


def context_prefix(ctx, sub: str, webflux: bool) -> tuple[str, dict, bool]:
    """(default prefix, {env: prefix}, envs differ) from the subproject's application* config."""
    keys = ("spring.webflux.base-path",) if webflux else ("server.servlet.context-path",
                                                          "spring.mvc.servlet.path")
    per_key = []
    for key in keys:
        if not [d for d in ctx.config.defs(key, sub) if d.subproject == sub]:
            continue
        per_key.append(ctx.config.public_values(key, sub))
    if not per_key:
        return "", {}, False
    envs = sorted({e for pv in per_key for e in pv})
    by_env = {}
    for e in envs:
        p = ""
        for pv in per_key:
            v = pv.get(e, pv.get("default", ""))
            p = pathnorm.join(p, v) if v and v != "/" else p
        by_env[e] = p or "/"
    vals = set(by_env.values())
    if "default" in by_env:
        dflt = by_env["default"]
    elif len(vals) == 1:
        dflt = next(iter(vals))
    else:
        dflt = "/"
    return ("" if dflt == "/" else dflt), by_env, len(vals) > 1 or (
        bool(by_env) and "default" not in by_env and len(vals) != 1)


def _ann_raw(a) -> str:
    return re.sub(r"\s+", " ", sx.text(a.node))[:200]


def auth_from(anns) -> tuple[str | None, str | None, bool | None]:
    for a in anns:
        if a.name == "PreAuthorize":
            expr = a.args.get("value", pos=0)
            expr = expr if isinstance(expr, str) else ""
            roles = []
            for m in re.finditer(r"has(?:Any)?(?:Role|Authority)\s*\(([^)]*)\)", expr):
                roles += re.findall(r"['\"]([^'\"]+)['\"]", m.group(1))
            if roles:
                return "roles:" + ",".join(sorted(set(roles))), _ann_raw(a), None
            if "permitAll" in expr:
                return "none", _ann_raw(a), True
            return "unknown", _ann_raw(a), None
        if a.name in ("Secured", "RolesAllowed"):
            vals = [x for x in as_list(a.args.get("value", pos=0)) if isinstance(x, str)]
            return ("roles:" + ",".join(sorted(set(vals))) if vals else "unknown"), _ann_raw(a), None
        if a.name in ("PermitAll", "AnonymousAllowed"):
            return "none", _ann_raw(a), True
        if a.name == "DenyAll":
            return "unknown", _ann_raw(a), None
    return None, None, None


class Security:
    """SecurityFilterChain rules of one subproject (path-matched -> medium)."""

    def __init__(self):
        self.rules: list = []      # (order, regex, verdict, raw)
        self.jwt = False
        self.basic = False
        self.unresolved: set = set()

    @staticmethod
    def _regex(p: str) -> str:
        out, i = "", 0
        while i < len(p):
            if p.startswith("/**", i):
                out += "(/.*)?"
                i += 3
            elif p.startswith("**", i):
                out += ".*"
                i += 2
            elif p[i] == "*":
                out += "[^/]*"
                i += 1
            elif p[i] == "{":
                j = p.find("}", i)
                out += "[^/]+"
                i = j + 1 if j > 0 else len(p)
            else:
                out += re.escape(p[i])
                i += 1
        return "^" + out + "/?$"

    def collect(self, idx: js.JavaIndex, jt: js.JType, m) -> bool:
        rt = js.simple_type(m.return_type)
        if rt != "SecurityFilterChain" and not (
                m.name == "configure" and any(js.simple_type(p.type) == "HttpSecurity"
                                              for p in m.params)):
            return False
        if m.body is None:
            return True
        scope = idx.method_scope(jt, m)
        for n in sx.walk(m.body):
            if n.type != "method_invocation":
                continue
            nm_node = n.child_by_field_name("name")
            name = sx.text(nm_node)
            al = n.child_by_field_name("arguments")
            args = sx.named_children(al) if al is not None else []
            if name in ("oauth2ResourceServer", "jwt"):
                self.jwt = True
            elif name in ("addFilterBefore", "addFilterAfter", "addFilterAt", "addFilter") and \
                    any("jwt" in sx.text(x).lower() or "token" in sx.text(x).lower()
                        for x in args[:1]):
                self.jwt = True
            elif name == "httpBasic":
                self.basic = True
            if name not in ("requestMatchers", "antMatchers", "mvcMatchers", "anyRequest",
                            "regexMatchers"):
                continue
            pats = []
            if name == "anyRequest":
                pats = ["/**"]
            else:
                for x in args:
                    if "HttpMethod" in sx.text(x):
                        continue
                    vs = idx.resolve_expr(x, scope)
                    if vs.kind == "literal" and not vs.holes:
                        pats.append(vs.value)
                    else:
                        self.unresolved.add(jt.jfile.path)
            parent = n.parent
            verdict = None
            if parent is not None and parent.type == "method_invocation" and \
                    parent.child_by_field_name("object") == n:
                vn = sx.text(parent.child_by_field_name("name"))
                pal = parent.child_by_field_name("arguments")
                pargs = sx.named_children(pal) if pal is not None else []
                if vn == "permitAll":
                    verdict = "none"
                elif vn in ("authenticated", "fullyAuthenticated"):
                    verdict = "auth"
                elif vn in ("hasRole", "hasAnyRole", "hasAuthority", "hasAnyAuthority"):
                    roles = [sx.decode_string(x, "java") for x in pargs]
                    roles = [r for r in roles if isinstance(r, str)]
                    verdict = "roles:" + ",".join(sorted(set(roles))) if roles else "unknown"
                else:
                    verdict = "unknown"
            for p in pats:
                self.rules.append((nm_node.start_byte, jt.jfile.path, self._regex(p), verdict,
                                   p))
        self.rules.sort(key=lambda r: (r[1], r[0]))
        return True

    def match(self, path: str) -> tuple[str | None, bool | None, str | None]:
        probe = re.sub(r"\{[^}]*\}", "x", path)
        for _o, _f, rx, verdict, raw in self.rules:
            if verdict is None:
                continue
            if re.match(rx, probe):
                if verdict == "auth":
                    return ("bearer-jwt" if self.jwt else "basic" if self.basic else "unknown"), \
                        None, raw
                return verdict, (True if verdict == "none" else None), raw
        return None, None, None


def params_of(tn, m, jf, jt, jaxrs: bool) -> tuple[list, str | None, str | None]:
    """(params, request schema, request type text)."""
    out, request, req_text = [], None, None
    for p in m.params:
        ann = next((a for a in p.annotations if a.name in PARAM_ANN), None)
        tree = parse_type(p.type)
        optional = js.simple_type(tree[0]) == "Optional"
        ptype = tn.norm(p.type, jf, jt)
        if ann is None:
            if jaxrs and not any(a.name in JAXRS_CONTEXT for a in p.annotations) and \
                    request is None:
                request, req_text = ptype, p.type
                out.append({"name": p.name, "in": "body", "type": ptype, "required": True})
            continue
            # Spring: unannotated simple params are request params; left to phase 3
        where = PARAM_ANN[ann.name]
        nm = ann.args.get("value", "name", pos=0)
        nm = nm if isinstance(nm, str) and nm else p.name
        req = ann.args.get("required")
        if req is None:
            req = not optional and ann.args.get("defaultValue") is None
            if ann.name == "ModelAttribute":
                req = False
        out.append({"name": nm, "in": where, "type": ptype, "required": bool(req)})
        if where == "body":
            request, req_text = ptype, p.type
    return out, request, req_text


def responses_of(tn, m, jf, jt, class_anns) -> tuple[list, list]:
    """(responses, response type texts for schemas)."""
    rs = {}
    texts = []
    st = next((a for a in m.annotations if a.name == "ResponseStatus"), None) or \
        next((a for a in class_anns if a.name == "ResponseStatus"), None)
    status = status_of(st.args.get("value", "code", pos=0)) if st is not None else None
    rt = m.return_type
    schema = tn.norm(rt, jf, jt) if rt else None
    if rt and js.simple_type(rt) not in ("void", "Void"):
        if schema == "any":
            schema = None
        rs[status or 200] = {"status": status or 200, "schema": schema, "when": None,
                             "from": "return-type"}
        texts.append(rt)
    elif status is not None:
        rs[status] = {"status": status, "schema": None, "when": None, "from": "annotation"}
    else:
        rs[200] = {"status": 200, "schema": None, "when": None, "from": "default"}
    api = []
    for a in m.annotations:
        if a.name == "ApiResponse":
            api.append(a)
        elif a.name == "ApiResponses":
            api += [x for x in as_list(a.args.get("value", pos=0)) if isinstance(x, sx.Annotation)]
    for a in api:
        code = status_of(a.args.get("responseCode", "code", pos=0))
        if code is None:
            continue
        desc = a.args.get("description", "message")
        sch = None
        for c in as_list(a.args.get("content")):
            if not isinstance(c, sx.Annotation):
                continue
            s = c.args.get("schema")
            arr = c.args.get("array")
            if isinstance(arr, sx.Annotation) and isinstance(arr.args.get("schema"), sx.Annotation):
                impl = arr.args.get("schema").args.get("implementation")
                if isinstance(impl, sx.TypeRef):
                    sch = f"List<{impl.name}>"
            elif isinstance(s, sx.Annotation):
                impl = s.args.get("implementation")
                if isinstance(impl, sx.TypeRef):
                    sch = impl.name
        prev = rs.get(code)
        entry = {"status": code,
                 "schema": tn.norm(sch, jf, jt) if sch else (prev or {}).get("schema"),
                 "when": desc if isinstance(desc, str) else None, "from": "annotation"}
        if sch:
            texts.append(sch)
        rs[code] = entry
    return [rs[k] for k in sorted(rs)], texts


def is_webflux(m) -> bool:
    rt = js.simple_type(m.return_type)
    return rt in ("Mono", "Flux") or any(js.simple_type(p.type) == "ServerWebExchange"
                                         for p in m.params)

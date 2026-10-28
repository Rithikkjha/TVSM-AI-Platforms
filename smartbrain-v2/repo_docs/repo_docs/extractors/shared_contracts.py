"""shared.contracts: API contract files -> ``api_contract`` + contract-sourced ``inbound_http`` /
``schema`` items (``source: contract``).

Files are content-sniffed: any ledgered JSON/YAML whose top level has ``openapi`` / ``swagger`` /
``asyncapi`` or a Postman ``info._postman_id`` is a contract, whatever its ledger class. OpenAPI 2/3
and WSDL are parsed fully; Postman, proto, GraphQL, AsyncAPI and RAML are recorded with
``parse: partial`` (phase 3 reads them). Generated specs (Swashbuckle / springdoc /
``@nestjs/swagger``) use ``shared_manifests.generated_contract_item`` (hook for stack extractors).
"""
from __future__ import annotations

import json
import posixpath
import re

from .. import pathnorm
from ..inventory_schema import make_item
from . import configfmt
from .base import ExtractResult, Extractor, RepoContext
from .shared_manifests import generated_contract_item  # noqa: F401  (re-exported hook)

HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
_SNIFF_YAML = re.compile(r"^(openapi|swagger|asyncapi)\s*:", re.M)
_SNIFF_JSON = re.compile(r'"(openapi|swagger|asyncapi|_postman_id)"\s*:')


def _kind(ctx: RepoContext, entry: dict) -> str | None:
    path = entry["path"]
    name = posixpath.basename(path).lower()
    if name.endswith(".proto"):
        return "proto"
    if name.endswith((".graphql", ".graphqls", ".gql")):
        return "graphql"
    if name.endswith(".wsdl"):
        return "wsdl"
    if name.endswith(".raml"):
        return "raml"
    if name.endswith((".json", ".yaml", ".yml")):
        if entry.get("class") not in ("api_contract", "config", "docs", "other", "test", "infra"):
            return None
        head = (ctx.read_text(path) or "")[:4096]
        if name.endswith(".json"):
            m = _SNIFF_JSON.search(head)
            return ("postman" if m.group(1) == "_postman_id" else "openapi-json") if m else None
        m = _SNIFF_YAML.search(head)
        return "openapi-yaml" if m else None
    if entry.get("class") == "api_contract":
        return "other"
    return None


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _type(s) -> str:
    if not isinstance(s, dict):
        return "any"
    if "$ref" in s:
        return _ref_name(s["$ref"])
    if s.get("enum"):
        return "enum[" + ",".join(str(x) for x in s["enum"]) + "]"
    for key in ("allOf", "oneOf", "anyOf"):
        if isinstance(s.get(key), list) and len(s[key]) == 1:
            return _type(s[key][0])
    t = s.get("type")
    f = s.get("format")
    if t == "array":
        return _type(s.get("items")) + "[]"
    if t == "string":
        return {"date": "date", "date-time": "datetime", "uuid": "uuid", "binary": "binary",
                "byte": "binary"}.get(f, "string")
    if t in ("integer", "number", "boolean"):
        return t
    if t == "object" or "properties" in s:
        ap = s.get("additionalProperties")
        if isinstance(ap, dict):
            return f"map<string,{_type(ap)}>"
        return "object"
    return "any"


def _validation(s: dict) -> str | None:
    parts = [f"{k}={s[k]}" for k in ("minLength", "maxLength", "minimum", "maximum", "pattern",
                                     "minItems", "maxItems") if k in s]
    if s.get("format") == "email":
        parts.append("email")
    return ";".join(parts) or None


def _auth(sec, schemes: dict) -> tuple[str | None, str | None]:
    if sec is None:
        return None, None
    if sec == []:
        return "none", "[]"
    names = [n for req in sec if isinstance(req, dict) for n in req]
    raw = json.dumps(sorted(set(names)))
    for n in names:
        sc = schemes.get(n) or {}
        t = str(sc.get("type", "")).lower()
        if t == "http" and str(sc.get("scheme", "")).lower() == "bearer" or t in ("oauth2",
                                                                                  "openidconnect"):
            return "bearer-jwt", raw
        if t == "http" and str(sc.get("scheme", "")).lower() == "basic" or t == "basic":
            return "basic", raw
        if t == "apikey":
            return "api-key", raw
    return "unknown", raw


class SharedContracts(Extractor):
    id = "shared.contracts"
    stacks = ()
    extractor_version = "0.1.1"

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        for entry in ctx.files(subproject):
            kind = _kind(ctx, entry)
            if kind is None:
                continue
            path = entry["path"]
            text = ctx.read_text(path) or ""
            if kind in ("openapi-json", "postman"):
                r = configfmt.parse_jsonc(text)
                if not r.ok or not isinstance(r.data, dict):
                    res.touch(path, "partial", r.error)
                    continue
                lines = {p: ln for p, _, ln in r.entries}
                if kind == "postman":
                    self._postman(ctx, path, r.data, lines, res)
                else:
                    self._spec(ctx, path, r.data, lines, res)
            elif kind == "openapi-yaml":
                docs, ok, err = configfmt.yaml_with_lines(text)
                if not ok or not docs or not isinstance(docs[0].data, dict):
                    res.touch(path, "partial", err or "empty YAML")
                    continue
                self._spec(ctx, path, docs[0].data, {p: ln for p, _, ln in docs[0].entries}, res)
            elif kind == "wsdl":
                self._wsdl(ctx, path, text, res)
            elif kind == "proto":
                self._proto(ctx, path, res)
            elif kind == "graphql":
                self._graphql(ctx, path, res)
            elif kind == "raml":
                self._contract(ctx, res, path, 1, "raml", None, None, None)
                res.touch(path, "partial")
            else:
                res.touch(path, "partial")
        return res

    def _contract(self, ctx, res, path, line, fmt, ops, title, version):
        attrs = {"format": fmt, "file": path, "generator": None, "generated": False,
                 "docs_path": None, "operations": ops,
                 "title": str(title) if title is not None else None,
                 "version": str(version) if version is not None else None}
        res.items.append(make_item("api_contract", ctx.subproject_of(path), path, attrs,
                                   [ctx.evidence(path, line)], self, source="contract"))

    # ---- OpenAPI / AsyncAPI ----------------------------------------------------------------
    def _spec(self, ctx, path, data, lines, res):
        top = next((k for k in ("openapi", "swagger", "asyncapi") if k in data), None)
        info = data.get("info") if isinstance(data.get("info"), dict) else {}
        if top == "asyncapi":
            chans = data.get("channels") if isinstance(data.get("channels"), dict) else {}
            self._contract(ctx, res, path, lines.get(("asyncapi",), 1), "asyncapi", len(chans),
                           info.get("title"), info.get("version"))
            res.touch(path, "partial")
            return
        v3 = top == "openapi"
        fmt = "openapi-3" if v3 else "openapi-2"
        prefix = ""
        if v3:
            servers = data.get("servers") or []
            if servers and isinstance(servers[0], dict) and isinstance(servers[0].get("url"), str):
                _, sp, _ = pathnorm.split_url(servers[0]["url"])
                prefix = sp if sp not in ("", "/") else ""
        else:
            prefix = data.get("basePath") if isinstance(data.get("basePath"), str) else ""
        comps = data.get("components") if isinstance(data.get("components"), dict) else {}
        schemes = comps.get("securitySchemes") if v3 else data.get("securityDefinitions")
        schemes = schemes if isinstance(schemes, dict) else {}
        shared_params = (comps.get("parameters") if v3 else data.get("parameters")) or {}
        paths_ = data.get("paths") if isinstance(data.get("paths"), dict) else {}
        sub = ctx.subproject_of(path)
        ops = 0
        partial = False

        def deref(p):
            if isinstance(p, dict) and "$ref" in p:
                return shared_params.get(_ref_name(p["$ref"])) or {}
            return p if isinstance(p, dict) else {}

        for rp in paths_:
            item = paths_[rp] if isinstance(paths_[rp], dict) else {}
            common = [deref(p) for p in item.get("parameters") or []]
            for m in HTTP_METHODS:
                op = item.get(m)
                if not isinstance(op, dict):
                    continue
                ops += 1
                full = pathnorm.join(prefix, str(rp))
                params, request = [], None
                for p in common + [deref(x) for x in op.get("parameters") or []]:
                    if not p.get("name"):
                        continue
                    if p.get("in") == "body":
                        request = _type(p.get("schema"))
                        continue
                    ptype = _type(p.get("schema")) if v3 or "schema" in p else _type(p)
                    params.append({"name": str(p["name"]), "in": p.get("in"), "type": ptype,
                                   "required": bool(p.get("required", p.get("in") == "path"))})
                rb = op.get("requestBody")
                if v3 and isinstance(rb, dict):
                    if "$ref" in rb:
                        request = _ref_name(rb["$ref"])
                    else:
                        for ct in sorted(rb.get("content") or {}):
                            request = _type((rb["content"][ct] or {}).get("schema"))
                            break
                responses = []
                for code, r in sorted((op.get("responses") or {}).items(), key=lambda kv: str(kv[0])):
                    r = r if isinstance(r, dict) else {}
                    schema = None
                    if v3:
                        for ct in sorted(r.get("content") or {}):
                            sch = (r["content"][ct] or {}).get("schema")
                            schema = _type(sch) if sch else None
                            break
                    elif r.get("schema"):
                        schema = _type(r["schema"])
                    status = int(code) if str(code).isdigit() else str(code)
                    responses.append({"status": status, "schema": schema,
                                      "when": r.get("description"), "from": "contract"})
                auth, auth_raw = _auth(op.get("security", data.get("security")), schemes)
                attrs = {"method": m.upper(), "path": pathnorm.display_path(full),
                         "path_raw": str(rp), "path_params_normalized": pathnorm.normalize(full),
                         # operationId is not a code handler (it would conflict on merge)
                         "handler": None, "framework": None,
                         "params": params, "request": request, "responses": responses,
                         "auth": auth, "auth_raw": auth_raw, "allow_anonymous": None,
                         "deprecated": bool(op.get("deprecated", False)), "contract_file": path,
                         "context_path_by_env": {}}
                ln = lines.get(("paths", rp, m)) or lines.get(("paths", rp), 1)
                res.items.append(make_item("inbound_http", sub, None, attrs,
                                           [ctx.evidence(path, ln)], self, source="contract"))
        schemas = (comps.get("schemas") if v3 else data.get("definitions")) or {}
        for name in schemas if isinstance(schemas, dict) else []:
            s = schemas[name] if isinstance(schemas[name], dict) else {}
            base = ("components", "schemas", name) if v3 else ("definitions", name)
            ln = lines.get(base, 1)
            req = set(s.get("required") or [])
            fields, extends = [], None
            props = dict(s.get("properties") or {})
            for part in s.get("allOf") or []:
                if isinstance(part, dict) and "$ref" in part:
                    extends = _ref_name(part["$ref"])
                elif isinstance(part, dict):
                    props.update(part.get("properties") or {})
                    req |= set(part.get("required") or [])
            for fname, fs in props.items():
                fs = fs if isinstance(fs, dict) else {}
                fields.append({"name": str(fname), "json_name": str(fname), "type": _type(fs),
                               "required": fname in req, "nullable": fs.get("nullable"),
                               "validation": _validation(fs), "default": fs.get("default")})
            attrs = {"name": str(name), "defined_in": f"{path}:{ln}", "language": None,
                     "schema_kind": "contract", "fields": fields,
                     "enum_values": [str(x) for x in s.get("enum") or []], "type_params": [],
                     "extends": extends, "resolved": True}
            res.items.append(make_item("schema", sub, str(name), attrs, [ctx.evidence(path, ln)],
                                       self, source="contract"))
        self._contract(ctx, res, path, lines.get((top,), 1), fmt, ops, info.get("title"),
                       info.get("version"))
        res.touch(path, "partial" if partial else "full")

    # ---- Postman ---------------------------------------------------------------------------
    def _postman(self, ctx, path, data, lines, res):
        info = data.get("info") if isinstance(data.get("info"), dict) else {}
        n = 0

        def walk(items, p):
            nonlocal n
            for i, it in enumerate(items or []):
                if not isinstance(it, dict):
                    continue
                if isinstance(it.get("item"), list):
                    walk(it["item"], p + (i, "item"))
                    continue
                req = it.get("request")
                if not isinstance(req, dict):
                    continue
                url = req.get("url")
                raw = url.get("raw") if isinstance(url, dict) else url
                if not isinstance(raw, str):
                    continue
                n += 1
                m = re.match(r"^\{\{[^}]+\}\}", raw)
                rest = raw[m.end():] if m else raw
                base, pth, query = pathnorm.split_url(rest)
                attrs = {"method": str(req.get("method") or "GET").upper(), "client": None,
                         "client_name": info.get("name"),
                         "base_url_source": "literal" if base and not m else "unknown",
                         "base_url_values": {"default": base} if base and not m else {},
                         "path_template": pathnorm.normalize(pth), "path_raw": raw,
                         "query_params": query, "role": "tests_target"}
                ln = lines.get(p + (i, "request")) or lines.get(p + (i,), 1)
                res.items.append(make_item("outbound_http", ctx.subproject_of(path), None, attrs,
                                           [ctx.evidence(path, ln)], self, "medium",
                                           source="contract"))

        walk(data.get("item"), ("item",))
        self._contract(ctx, res, path, lines.get(("info",), 1), "postman", n, info.get("name"),
                       None)
        res.touch(path, "partial")

    # ---- WSDL / proto / GraphQL ------------------------------------------------------------
    def _wsdl(self, ctx, path, text, res):
        doc = configfmt.xml_with_lines(text)
        ops = 0
        if doc.root is not None:
            for pt in doc.root.iter("portType"):
                ops += len(pt.findall("operation"))
        self._contract(ctx, res, path, 1, "wsdl", ops,
                       doc.root.get("name") if doc.root is not None else None, None)
        res.touch(path, "full" if doc.ok else "partial", doc.error)

    def _proto(self, ctx, path, res):
        lines = ctx.lines(path)
        pkg, svc, ops = "", None, 0
        for i, ln in enumerate(lines, 1):
            m = re.match(r"^\s*package\s+([\w.]+)\s*;", ln)
            if m:
                pkg = m.group(1)
            m = re.match(r"^\s*service\s+(\w+)", ln)
            if m:
                svc = m.group(1)
            m = re.match(r"^\s*rpc\s+(\w+)\s*\(\s*(?:stream\s+)?([\w.]+)\s*\)\s*returns\s*\(\s*"
                         r"(?:stream\s+)?([\w.]+)", ln)
            if m and svc:
                ops += 1
                full = f"/{pkg + '.' if pkg else ''}{svc}/{m.group(1)}"
                attrs = {"method": "POST", "path": full, "path_raw": full,
                         "path_params_normalized": full, "handler": f"{svc}.{m.group(1)}",
                         "framework": "grpc", "request": m.group(2),
                         "responses": [{"status": 200, "schema": m.group(3), "when": None,
                                        "from": "contract"}], "contract_file": path}
                res.items.append(make_item("inbound_http", ctx.subproject_of(path), None, attrs,
                                           [ctx.evidence(path, i)], self, source="contract"))
        self._contract(ctx, res, path, 1, "proto", ops, svc, None)
        res.touch(path, "partial")

    def _graphql(self, ctx, path, res):
        text = ctx.read_text(path) or ""
        ops = 0
        for m in re.finditer(r"\btype\s+(Query|Mutation|Subscription)\s*\{([^}]*)\}", text):
            ops += len(re.findall(r"^\s*\w+\s*[(:]", m.group(2), re.M))
        self._contract(ctx, res, path, 1, "graphql", ops, None, None)
        res.touch(path, "partial")

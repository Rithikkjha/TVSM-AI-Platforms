"""Data access + scheduled jobs for java.spring (docs/EXTRACTORS.md#data_access, #scheduled_job).

JPA ``@Entity``/``@Table``, Mongo ``@Document``, Spring Data repositories (read/write rollup from
call sites, else declared methods), ``@Query(nativeQuery = true)`` tables, JdbcTemplate SQL literals,
``@Procedure`` / ``SimpleJdbcCall.withProcedureName``, RedisTemplate (medium). Store identity from
``spring.datasource.url`` / ``spring.data.mongodb.uri`` via ``parse_store_identity`` (host/db only).
"""
from __future__ import annotations

import re

from .. import config_classify as cc
from . import java_symbols as js
from . import syntax as sx

REPO_BASES = {"JpaRepository": "sql", "CrudRepository": "sql", "PagingAndSortingRepository": "sql",
              "ListCrudRepository": "sql", "ListPagingAndSortingRepository": "sql",
              "R2dbcRepository": "sql", "ReactiveCrudRepository": "sql",
              "MongoRepository": "mongo", "ReactiveMongoRepository": "mongo"}
READ = ("find", "get", "count", "exists", "read", "query", "search", "stream", "load", "fetch")
WRITE = ("save", "delete", "remove", "insert", "update", "persist", "merge", "flush", "create",
         "upsert", "truncate")
JDBC_TYPES = ("JdbcTemplate", "NamedParameterJdbcTemplate", "JdbcClient")
REDIS_TYPES = ("RedisTemplate", "StringRedisTemplate", "ReactiveRedisTemplate",
               "ReactiveStringRedisTemplate")
_TABLES = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE|MERGE\s+INTO)\s+([A-Za-z_][\w$]*(?:\.[A-Za-z_]"
                     r"[\w$]*)?)", re.I)
_SQL_KW = {"select", "set", "where", "lateral", "unnest", "dual", "values"}
CRON_LIKE = re.compile(r"^[0-9*/?,LW#A-Za-z\- ]+$")


def op_of(method_name: str) -> str | None:
    low = method_name.lower()
    if low.startswith(WRITE):
        return "write"
    if low.startswith(READ):
        return "read"
    return None


def rollup(ops) -> str | None:
    s = {o for o in ops if o}
    if not s:
        return None
    if "both" in s or s == {"read", "write"}:
        return "both"
    return s.pop()


def sql_tables(sql: str) -> list[tuple[str | None, str]]:
    out = []
    for m in _TABLES.finditer(sql or ""):
        q = m.group(1)
        if q.lower() in _SQL_KW:
            continue
        parts = q.split(".")
        t = (parts[0], parts[1]) if len(parts) == 2 else (None, parts[0])
        if t not in out:
            out.append(t)
    return out


def sql_op(sql: str) -> str | None:
    s = (sql or "").lstrip().upper()
    if s.startswith(("SELECT", "WITH")):
        return "read"
    if s.startswith(("INSERT", "UPDATE", "DELETE", "MERGE", "TRUNCATE")):
        return "write"
    return None


def store_identity(ctx, sub: str, keys: tuple[str, ...]) -> tuple[dict | None, str | None, str]:
    """(identity {store_type, host, database}, name_from key, raw prefix) from the subproject's
    config. Raw values stay in memory; host/database go through the classifier."""
    for key in keys:
        defs = [d for d in ctx.config.defs(key, sub) if d.subproject == sub]
        if not defs:
            continue
        raw = ctx.config.resolve_key(key, "default", sub).value
        ident = cc.parse_store_identity(raw) if raw else None
        if ident is None:
            ident = cc.parse_store_identity(str(defs[0].value or ""))
            if ident is not None:
                ident = {"store_type": ident["store_type"], "host": None, "database": None}
        if ident is not None:
            host = ident.get("host")
            if host and ("${" in host or cc.classify("host", host).record_value is None):
                host = None
            db = ident.get("database")
            if db and ("${" in db or cc.classify("database", db).record_value is None):
                db = None
            return {"store_type": ident["store_type"], "host": host, "database": db}, key, \
                str(defs[0].value or "")
        return None, key, str(defs[0].value or "")
    return None, None, ""


_DS_URL = re.compile(r"(^|\.)datasource(\.[a-z0-9_]+)*\.(jdbc|r2dbc)?url$")


def datasource_fallback(ctx, sub: str) -> tuple[dict | None, str | None, str]:
    """Store identity when the subproject has no standard datasource key: the single
    ``*.datasource[.*].url`` property defined anywhere in the repo (e.g. a multi-module app whose
    modules share the app module's custom multitenant datasource). Ambiguous -> nothing."""
    keys = sorted({k for k in ctx.config.keys() if _DS_URL.search(k)
                   and any(d.source == "property" for d in ctx.config.defs(k))})
    if len(keys) != 1:
        return None, None, ""
    key = keys[0]
    defs = ctx.config.defs(key, sub)
    name = defs[0].name
    raw = ctx.config.resolve_key(name, "default", defs[0].subproject).value
    ident = cc.parse_store_identity(raw) if raw else None
    if ident is None:
        return None, name, str(defs[0].value or "")
    host, db = ident.get("host"), ident.get("database")
    if host and ("${" in host or cc.classify("host", host).record_value is None):
        host = None
    if db and ("${" in db or cc.classify("database", db).record_value is None):
        db = None
    return {"store_type": ident["store_type"], "host": host, "database": db}, name, \
        str(defs[0].value or "")


def guess_sql_store(ctx, sub: str) -> str:
    for key in ("spring.jpa.database", "spring.datasource.driver-class-name",
                "spring.jpa.properties.hibernate.dialect", "spring.jpa.database-platform"):
        defs = [d for d in ctx.config.defs(key, sub) if d.subproject == sub]
        v = str(ctx.config.resolve_key(key, "default", sub).value or
                (defs[0].value if defs else "") or "").lower()
        for needle, st in (("postgres", "postgres"), ("sqlserver", "mssql"), ("mysql", "mysql"),
                           ("mariadb", "mysql"), ("oracle", "oracle"), ("h2", "other")):
            if needle in v:
                return st
    return "other"


def public_expr_values(ctx, key: str, sub: str) -> dict:
    """Per-env values of a schedule expression key. Cron/number/duration-shaped values are not
    secret (and the classifier would hide them as rule 6), so they are recorded when neither the
    key chain nor the value is secret-like."""
    out = {}
    for env in ctx.config.resolved_envs(key, sub):
        r = ctx.config.resolve_key(key, env, sub)
        v = r.value
        if not v or any(cc.key_is_secret(k) for k in r.chain) or cc.value_is_secret(v):
            continue
        if CRON_LIKE.match(v) and len(v) <= 120:
            out[env] = v
    return out


NAME_SHAPE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def props_default(idx: js.JavaIndex, key: str) -> str | None:
    """Literal string initializer (code default) of the ``@ConfigurationProperties`` field a
    ``prefix.field`` key reads (the specific field only; supertypes included)."""
    if not key or "." not in key:
        return None
    pre, prop = key.rsplit(".", 1)
    hits = []
    for jt in idx.types.values():
        if jt.props_prefix != pre:
            continue
        hit = idx.find_field(jt, prop)
        if hit is None or hit[1].value is None or "static" in hit[1].modifiers:
            continue
        v = sx.decode_string(hit[1].value, "java")
        if isinstance(v, str):
            hits.append(v)
    return hits[0] if len(set(hits)) == 1 else None


def public_name_values(ctx, idx: js.JavaIndex, key: str, sub: str) -> dict:
    """Per-env values of a store object name key (OpenSearch index, Nebula space). The
    classifier hides ``*Index`` / ``space`` keys (rule 6) although they are plain names, so a
    value is recorded when no key in the resolution chain is secret-like, the value is not
    secret-like and it is name-shaped. Config values first; when the key is defined nowhere in
    the repo, the properties field's literal initializer under pseudo-env ``code-default``."""
    if cc.key_is_secret(key):
        return {}
    if ctx.config.defs(key):
        out = {}
        for env in ctx.config.resolved_envs(key, sub):
            r = ctx.config.resolve_key(key, env, sub)
            v = r.value
            if not v or any(cc.key_is_secret(k) for k in r.chain) or cc.value_is_secret(v):
                continue
            if NAME_SHAPE.match(v):
                out[env] = v
        return out
    v = props_default(idx, key)
    if v and NAME_SHAPE.match(v) and not cc.value_is_secret(v):
        return {"code-default": v}
    return {}


def name_values(ctx, idx, vs: js.ValueSource, sub: str) -> tuple[list[str], str | None, bool]:
    """(names, config key, code_default) for a store object name expression."""
    if vs.kind == "literal" and not vs.holes and NAME_SHAPE.match(vs.value or "") and \
            not cc.value_is_secret(vs.value):
        return [vs.value], None, False
    if vs.kind in ("config", "env") and not vs.value and not vs.prefix:
        vals = public_name_values(ctx, idx, vs.key, sub)
        return sorted(set(vals.values())), vs.key, "code-default" in vals
    return [], None, False


# ---- MongoTemplate / OpenSearch / NebulaGraph ---------------------------------------------
MONGO_TYPES = ("MongoTemplate", "ReactiveMongoTemplate", "MongoOperations",
               "ReactiveMongoOperations")
_MONGO_WRITE_EXACT = ("findAndModify", "findAndRemove", "findAllAndRemove", "findAndReplace",
                      "bulkOps")


def mongo_op(name: str) -> str | None:
    if name in _MONGO_WRITE_EXACT or name.startswith(("insert", "save", "update", "upsert",
                                                       "remove", "replace")):
        return "write"
    if name.startswith(("find", "count", "exists", "aggregate", "stream", "query",
                        "estimatedCount", "scroll", "distinct")):
        return "read"
    return None


OS_TYPES = ("OpenSearchClient", "OpenSearchAsyncClient")
OS_READ = ("search", "scroll", "count", "get", "mget", "msearch", "exists", "existsSource",
           "getSource", "explain", "termvectors", "mtermvectors", "searchTemplate")
OS_WRITE = ("index", "bulk", "update", "delete", "deleteByQuery", "updateByQuery", "create",
            "refresh", "putMapping", "reindex", "putSettings", "flush", "forcemerge")
NEBULA_TYPES = ("SessionPool", "Session", "NebulaPool")
NEBULA_EXEC = ("execute", "executeJson", "executeWithParameter", "executeJsonWithParameter")
NGQL_READ = ("MATCH", "FETCH", "GO", "LOOKUP", "FIND", "GET", "SHOW", "DESCRIBE", "DESC")
NGQL_WRITE = ("INSERT", "UPSERT", "UPDATE", "DELETE")
_NGQL_NAMES = re.compile(r"(?::|\bON\s+|\bVERTEX\s+|\bEDGE\s+)`?([A-Za-z_]\w*)`?")
_NGQL_KW = frozenset({"ON", "SET", "WHERE", "YIELD", "RETURN", "AS", "OVER", "FROM", "TO",
                      "VALUES", "WITH", "AND", "OR", "NOT", "IN", "IS", "NULL", "WHEN",
                      "VERTEX", "EDGE", "TAG", "IF", "EXISTS"})
_NGQL_HOLE = re.compile(r"(?::|\bON\s+|\bVERTEX\s+|\bEDGE\s+)`?\{\}")


def _imports_nebula(jf) -> bool:
    return any(v.startswith("com.vesoft.nebula") for v in jf.import_lines)


def _recv_type(idx, obj, scope) -> str:
    """Simple type of an invocation receiver; for a chain (``client.indices()``) its root."""
    while obj is not None and obj.type == "method_invocation":
        obj = obj.child_by_field_name("object")
    return js.simple_type(idx.type_of(obj, scope) or "") if obj is not None else ""


def _has_field_of(idx, jt, types) -> bool:
    seen, todo = set(), [jt]
    while todo:
        t = todo.pop()
        if t is None or t.fqn in seen:
            continue
        seen.add(t.fqn)
        if any(js.simple_type(f.type) in types for f in t.fields.values()):
            return True
        todo += idx.supertypes(t)
    return False


SINK_ROUNDS = 5


def _wrapper_sites(idx, jt, m, scope, wrappers: dict) -> list:
    """(invocation, arg index, op) of calls in ``m`` to a registered sink wrapper."""
    if not wrappers:
        return []
    names = {k[1] for k in wrappers}
    out = []
    for n in idx.nodes(m, "method_invocation"):
        name = sx.text(n.child_by_field_name("name"))
        if name not in names:
            continue
        obj = n.child_by_field_name("object")
        al = n.child_by_field_name("arguments")
        nargs = len(sx.named_children(al)) if al is not None else 0
        if obj is None or obj.type == "this":
            owners = [t.fqn for t in idx.outer_chain(jt)] + _all_supers(idx, jt)
        else:
            ty = idx.type_of(obj, scope)
            t = idx.resolve_type(ty, scope.jfile, jt) if ty else None
            owners = [t.fqn] if t is not None else []
        k = next(((o, name, nargs) for o in owners if (o, name, nargs) in wrappers), None)
        if k is not None and k != (jt.fqn, m.name, len(m.params)):
            out.append((n, wrappers[k][0], wrappers[k][1]))
    return out


def sink_wrappers(idx: js.JavaIndex, kind: str, direct) -> dict:
    """(owner fqn, method, nparams) -> (param index, op): methods passing a parameter to a
    store sink (``direct(idx, jt, m, scope)`` -> [(invocation, arg index, op)]: a Nebula
    ``execute*(query)``, an OpenSearch ``.index(name)``) in round 1, or to such a method in
    rounds 2..SINK_ROUNDS (overload ladders like ``execute/4 -> /5 -> /6``). Bounded, source
    order, setdefault: deterministic."""
    key = ("sink_wrappers", kind)
    got = idx._memo.get(key)
    if got is not None:
        return got
    out: dict = {}
    for rnd in range(SINK_ROUNDS):
        added = {}
        for jt in idx.types.values():
            for m in jt.methods:
                k = (jt.fqn, m.name, len(m.params))
                if k in out or k in added or m.body is None:
                    continue
                scope = idx.method_scope(jt, m)
                calls = direct(idx, jt, m, scope) if rnd == 0 else \
                    _wrapper_sites(idx, jt, m, scope, out)
                for n, qi, op in calls:
                    args = sx.named_children(n.child_by_field_name("arguments"))
                    a = args[qi] if qi < len(args) else None
                    if a is not None and a.type == "identifier" and sx.text(a) in scope.params:
                        added.setdefault(k, (scope.params[sx.text(a)][0], op))
        if not added:
            break
        out.update(added)
    idx._memo[key] = out
    return out


def _nebula_direct(idx, jt, m, scope) -> list:
    if not _imports_nebula(jt.jfile):
        return []
    out = []
    for n in idx.nodes(m, "method_invocation"):
        obj = n.child_by_field_name("object")
        al = n.child_by_field_name("arguments")
        if obj is None or al is None or not sx.named_children(al):
            continue
        if sx.text(n.child_by_field_name("name")) in NEBULA_EXEC and \
                _recv_type(idx, obj, scope) in NEBULA_TYPES:
            out.append((n, 0, None))
    return out


def _os_direct(idx, jt, m, scope) -> list:
    if not (_has_field_of(idx, jt, OS_TYPES)
            or any(js.simple_type(p.type) in OS_TYPES for p in m.params)):
        return []
    ops, sites = [], []
    for n in idx.nodes(m, "method_invocation"):
        name = sx.text(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        if obj is None:
            continue
        if _recv_type(idx, obj, scope) in OS_TYPES:
            ops.append("read" if name in OS_READ else ("write" if name in OS_WRITE else None))
        elif name == "index" and _os_index_site(idx, n, scope):
            sites.append(n)
    return [(n, 0, _os_op(idx, n, scope, ops)) for n in sites]


def _all_supers(idx, jt) -> list[str]:
    out, todo = [], list(idx.supertypes(jt))
    while todo and len(out) < 16:
        s = todo.pop(0)
        if s.fqn not in out:
            out.append(s.fqn)
            todo += idx.supertypes(s)
    return out


def _lambda_param_root(node) -> bool:
    """True when ``node`` (identifier) is a parameter of an enclosing lambda."""
    nm = sx.text(node)
    p = node.parent
    while p is not None and p.type not in ("method_declaration", "constructor_declaration"):
        if p.type == "lambda_expression":
            ps = p.child_by_field_name("parameters")
            if ps is not None and nm in [sx.text(x) for x in sx.walk(ps)
                                         if x.type == "identifier"]:
                return True
        p = p.parent
    return False


def _os_index_site(idx, n, scope) -> bool:
    """``x.index(name)`` that names an OpenSearch index: on a lambda parameter of a request
    builder lambda or on a ``*Request.Builder`` local / creation (not a DTO builder)."""
    al = n.child_by_field_name("arguments")
    args = sx.named_children(al) if al is not None else []
    if len(args) != 1 or args[0].type in ("lambda_expression", "true", "false",
                                          "decimal_integer_literal"):
        return False
    if args[0].type == "method_invocation" and \
            sx.text(args[0].child_by_field_name("name")) == "of":
        return False
    root = js.invocation_chain(n)[0][0]
    if root is None:
        return False
    if root.type == "identifier":
        if js.simple_type(idx.type_of(root, scope) or "") in OS_TYPES:
            return False
        if _lambda_param_root(root):
            return True
        ty = idx.type_of(root, scope) or ""
        return bool(re.search(r"Request(\.Builder)?$", js.strip_generics(ty)))
    if root.type == "object_creation_expression":
        ty = js.strip_generics(sx.text(root.child_by_field_name("type")))
        return bool(re.search(r"Request\.Builder$", ty))
    return False


def _os_op(idx, n, scope, method_ops) -> str | None:
    p = n.parent
    while p is not None and p.type not in ("method_declaration", "constructor_declaration"):
        if p.type == "method_invocation":
            nm = sx.text(p.child_by_field_name("name"))
            if _recv_type(idx, p.child_by_field_name("object"), scope) in OS_TYPES:
                return "read" if nm in OS_READ else ("write" if nm in OS_WRITE else None)
        p = p.parent
    return rollup(method_ops)


def store_sites(idx: js.JavaIndex, jt: js.JType, m: sx.MethodDecl) -> dict:
    """MongoTemplate / OpenSearch / Nebula sites of one method:
    ``mongo``: (entity JType | None, collection | None, op, line);
    ``opensearch``: (name ValueSource, op, line); ``nebula``: (kind, ValueSource, line) with kind
    ``stmt`` or ``space``; ``unresolved``: True when a site of interest could not be settled."""
    res = {"mongo": [], "opensearch": [], "nebula": [], "unresolved": False}
    if m.body is None:
        return res
    scope = idx.method_scope(jt, m)
    mine = (jt.fqn, m.name, len(m.params))
    for n in idx.nodes(m, "method_invocation"):
        obj = n.child_by_field_name("object")
        if obj is None:
            continue
        if js.simple_type(idx.type_of(obj, scope) or "") not in MONGO_TYPES:
            continue
        name = sx.text(n.child_by_field_name("name"))
        al = n.child_by_field_name("arguments")
        args = sx.named_children(al) if al is not None else []
        line = sx.line(n.child_by_field_name("name"))
        op = mongo_op(name)
        ents, colls = [], []
        for a in args:
            if a.type == "class_literal":
                kids = sx.named_children(a)
                et = idx.resolve_type(sx.text(kids[0]), scope.jfile, jt) if kids else None
                if et is not None:  # in-repo document class (not Document / Map)
                    ents.append(et)
            elif a.type in ("string_literal", "identifier", "field_access", "binary_expression"):
                vs = idx.resolve_expr(a, scope)
                if vs.kind == "literal" and not vs.holes and NAME_SHAPE.match(vs.value or ""):
                    colls.append(vs.value)
        if op is None or not (ents or colls):
            res["unresolved"] = True
            continue
        for et in ents or [None]:
            res["mongo"].append((et, colls[0] if colls else None, op, line))
    sinks = (("opensearch", _os_direct), ("nebula", _nebula_direct))
    for kind, direct in sinks:
        wrappers = sink_wrappers(idx, kind, direct)
        for n, qi, op in direct(idx, jt, m, scope) + _wrapper_sites(idx, jt, m, scope, wrappers):
            args = sx.named_children(n.child_by_field_name("arguments"))
            a = args[qi] if qi < len(args) else None
            if a is None:
                continue
            line = sx.line(n.child_by_field_name("name"))
            vs = idx.resolve_expr(a, scope)
            if vs.kind == "param" and mine in wrappers:
                continue  # wrapper body: resolved at its call sites
            if kind == "opensearch":
                res["opensearch"].append((vs, op, line))
            else:
                res["nebula"].append(("stmt", vs, line))
    if _imports_nebula(jt.jfile):
        for n in idx.nodes(m, "object_creation_expression"):
            if js.simple_type(sx.text(n.child_by_field_name("type"))) == "SessionPoolConfig":
                args = sx.named_children(n.child_by_field_name("arguments"))
                if len(args) >= 2:
                    res["nebula"].append(("space", idx.resolve_expr(args[1], scope),
                                          sx.line(n)))
    return res


def ngql(vs: js.ValueSource) -> tuple[str | None, str | None, list[str], str | None]:
    """(verb, op, tag/edge names, space key) of a resolved nGQL statement; verb None when the
    statement text does not start with a literal."""
    segs = list(vs.segs)
    if not segs or segs[0].kind != "lit":
        return None, None, [], None
    text = "".join(s.text if s.kind == "lit" else "{}" for s in segs)
    words = text.strip().split(None, 1)
    verb = words[0].upper().rstrip(";") if words else ""
    if verb == "USE":
        key = next((s.text for s in segs[1:] if s.kind in ("config", "env")), None)
        if key is None:
            rest = (words[1] if len(words) > 1 else "").strip().rstrip(";").strip("`")
            return "USE", None, [rest] if NAME_SHAPE.match(rest) else [], None
        return "USE", None, [], key
    op = "read" if verb in NGQL_READ else ("write" if verb in NGQL_WRITE else None)
    names = []
    for mm in _NGQL_NAMES.finditer(text):
        nm = mm.group(1)
        if nm.upper() not in _NGQL_KW and nm not in names:
            names.append(nm)
    return verb, op, names, None


def ngql_name_hole(vs: js.ValueSource) -> bool:
    """True when a tag/edge position of the statement is a runtime value (``MATCH (v:%s)``)."""
    text = "".join(s.text if s.kind == "lit" else "{}" for s in vs.segs)
    return bool(_NGQL_HOLE.search(text))


class Repo:
    def __init__(self, jt: js.JType, entity: str | None, store: str):
        self.jt, self.entity, self.store = jt, entity, store
        self.ops: list[str] = []          # call-site ops
        self.declared: list[str] = []     # declared method ops
        self.lines: list[tuple[str, int]] = [(jt.jfile.path, jt.decl.line)]
        self.tables: list[tuple] = []     # (schema, table, op, file, line)
        self.procs: list[tuple] = []      # (name, file, line)


def repositories(idx: js.JavaIndex) -> dict[str, Repo]:
    """Spring Data repository interfaces (fqn -> Repo), repo-wide."""
    out = idx._memo.get("repositories")
    if out is not None:
        return out
    out = {}
    for jt in idx.types.values():
        if jt.decl.kind != "interface":
            continue
        for ext in jt.decl.extends:
            base = js.simple_type(ext)
            if base not in REPO_BASES:
                continue
            m = re.search(r"<\s*([\w.]+)", ext)
            r = Repo(jt, m.group(1) if m else None, REPO_BASES[base])
            for md in jt.methods:
                q = next((a for a in md.annotations if a.name == "Query"), None)
                mod = any(a.name == "Modifying" for a in md.annotations)
                proc = next((a for a in md.annotations if a.name == "Procedure"), None)
                op = "write" if mod else op_of(md.name)
                if q is not None:
                    sql = q.args.get("value", pos=0)
                    if q.args.get("nativeQuery") is True and isinstance(sql, str):
                        sop = sql_op(sql) or op
                        for sch, t in sql_tables(sql):
                            r.tables.append((sch, t, sop, jt.jfile.path, q.line))
                        op = sop or op
                    elif isinstance(sql, str):
                        op = sql_op(sql) or op
                if proc is not None:
                    nm = proc.args.get("procedureName", "value", "name", pos=0)
                    if isinstance(nm, str):
                        r.procs.append((nm, jt.jfile.path, proc.line))
                if op:
                    r.declared.append(op)
            out[jt.fqn] = r
            break
    idx._memo["repositories"] = out
    return out


def scan_method(idx: js.JavaIndex, jt: js.JType, m: sx.MethodDecl, repos: dict) -> dict:
    """Repository call ops, JdbcTemplate SQL, procedures, Quartz cron calls in one method."""
    res = {"repo_ops": [], "jdbc": [], "procs": [], "quartz": []}
    if m.body is None:
        return res
    scope = idx.method_scope(jt, m)
    for n in idx.nodes(m, "method_invocation"):
        name = sx.text(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        al = n.child_by_field_name("arguments")
        args = sx.named_children(al) if al is not None else []
        line = sx.line(n.child_by_field_name("name"))
        if obj is not None and repos:
            ty = idx.type_of(obj, scope)
            t = idx.resolve_type(ty, scope.jfile, jt) if ty else None
            if t is not None and t.fqn in repos:
                op = op_of(name)
                if op:
                    res["repo_ops"].append((t.fqn, op, line))
                continue
        if obj is not None and js.simple_type(idx.type_of(obj, scope) or "") in JDBC_TYPES and args:
            vs = idx.resolve_expr(args[0], scope)
            if vs.kind == "literal":
                res["jdbc"].append((vs.value, line))
        elif name == "withProcedureName" and args:
            vs = idx.resolve_expr(args[0], scope)
            if vs.kind == "literal" and not vs.holes:
                res["procs"].append((vs.value, line))
        elif name == "cronSchedule" and args and sx.text(obj) == "CronScheduleBuilder":
            job = None
            for x in sx.walk(m.body):
                if x.type == "method_invocation" and \
                        sx.text(x.child_by_field_name("name")) == "newJob":
                    xa = x.child_by_field_name("arguments")
                    ka = sx.named_children(xa) if xa is not None else []
                    if ka and ka[0].type == "class_literal":
                        job = sx.text(sx.named_children(ka[0])[0])
                    break
            res["quartz"].append((idx.resolve_expr(args[0], scope), line, job))
    return res

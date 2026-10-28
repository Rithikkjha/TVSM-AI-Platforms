"""shared.sql: ``*.sql`` DDL / DML / PL/pgSQL -> one ``data_access`` item per subproject.

A statement splitter aware of quotes, comments and dollar-quoted (``$$`` / ``$tag$``) bodies feeds a
recognizer for CREATE/ALTER TABLE (columns), CREATE VIEW, CREATE [OR REPLACE] FUNCTION/PROCEDURE,
INSERT/UPDATE/DELETE (entities) and other known statements. A file is ``full`` only when every
statement is recognized. ``owns_schema`` is set by the orchestrator when the repo is a db-migration
repo. Flyway ``V<n>__*.sql`` files are listed in ``ctx.hints["flyway_files"]``.
"""
from __future__ import annotations

import posixpath
import re

from ..inventory_schema import make_item
from .base import ExtractResult, Extractor, RepoContext

FLYWAY = re.compile(r"^[VRU]\d+(?:[._]\d+)*__.+\.sql$", re.I)
_KNOWN = re.compile(
    r"^(CREATE\s+(UNIQUE\s+)?INDEX|CREATE\s+(SCHEMA|SEQUENCE|EXTENSION|TYPE|TRIGGER|DOMAIN|ROLE|"
    r"USER|DATABASE)|DROP\s|ALTER\s+(SEQUENCE|INDEX|SCHEMA|VIEW|FUNCTION|TYPE|DATABASE|ROLE|USER)|"
    r"COMMENT\s+ON|GRANT\s|REVOKE\s|SET\s|BEGIN|COMMIT|ROLLBACK|START\s+TRANSACTION|DO\s|"
    r"TRUNCATE\s|SELECT\s|WITH\s|USE\s|GO$|EXEC(UTE)?\s|CALL\s|ANALYZE|VACUUM|REFRESH\s|"
    r"DECLARE\s|IF\s|PRINT\s|MERGE\s|COPY\s|LOCK\s|SAVEPOINT|RELEASE)", re.I)
_IDENT = r'(?:"[^"]+"|\[[^\]]+\]|`[^`]+`|[A-Za-z_][\w$]*)'
_QNAME = rf"({_IDENT}(?:\s*\.\s*{_IDENT})?)"
_CREATE_TABLE = re.compile(rf"^CREATE\s+(?:(?:GLOBAL\s+|LOCAL\s+)?(?:TEMP|TEMPORARY|UNLOGGED)\s+)?"
                           rf"TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{_QNAME}\s*\((.*)\)", re.I | re.S)
_ALTER_TABLE = re.compile(rf"^ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?{_QNAME}\s+(.*)$",
                          re.I | re.S)
_VIEW = re.compile(rf"^CREATE\s+(?:OR\s+REPLACE\s+)?(?:MATERIALIZED\s+)?VIEW\s+"
                   rf"(?:IF\s+NOT\s+EXISTS\s+)?{_QNAME}", re.I)
_ROUTINE = re.compile(rf"^CREATE\s+(?:OR\s+REPLACE\s+|OR\s+ALTER\s+)?(FUNCTION|PROCEDURE|PROC)\s+"
                      rf"{_QNAME}", re.I)
_DML = re.compile(rf"^(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(?:ONLY\s+)?{_QNAME}", re.I)
_CONSTRAINT = re.compile(r"^(CONSTRAINT|PRIMARY\s+KEY|FOREIGN\s+KEY|UNIQUE|CHECK|EXCLUDE|INDEX|KEY)"
                         r"\b", re.I)


def _unq(s: str) -> str:
    return re.sub(r'^["\[`]|["\]`]$', "", s.strip())


def _split_name(q: str) -> tuple[str | None, str]:
    parts = [_unq(p) for p in re.split(r"\s*\.\s*", q.strip())]
    return (parts[0], parts[1]) if len(parts) == 2 else (None, parts[0])


def split_statements(text: str) -> list[tuple[str, int]]:
    """[(statement without comments, start line)] split on ``;`` outside quotes/comments/$$."""
    out = []
    buf: list[str] = []
    i, n, line = 0, len(text), 1
    start_line = None
    dollar = None
    while i < n:
        c = text[i]
        if dollar:
            if text.startswith(dollar, i):
                buf.append(dollar)
                i += len(dollar)
                dollar = None
                continue
            if c == "\n":
                line += 1
            buf.append(c)
            i += 1
            continue
        if c == "-" and text.startswith("--", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            line += text.count("\n", i, j)
            buf.append(" ")
            i = j
            continue
        if c in "'\"":
            j = i + 1
            while j < n:
                if text[j] == c:
                    if j + 1 < n and text[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            seg = text[i:j + 1]
            if start_line is None:
                start_line = line
            line += seg.count("\n")
            buf.append(seg)
            i = j + 1
            continue
        if c == "$":
            m = re.match(r"\$[A-Za-z_]*\$", text[i:i + 64])
            if m:
                dollar = m.group(0)
                if start_line is None:
                    start_line = line
                buf.append(dollar)
                i += len(dollar)
                continue
        if c == ";":
            stmt = "".join(buf).strip()
            if stmt:
                out.append((stmt, start_line or line))
            buf, start_line = [], None
            i += 1
            continue
        if c == "\n":
            line += 1
        if not c.isspace() and start_line is None:
            start_line = line
        buf.append(c)
        i += 1
    stmt = "".join(buf).strip()
    if stmt:
        out.append((stmt, start_line or line))
    return out


def _columns(body: str) -> list[dict]:
    cols, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            cols.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    cols.append("".join(cur))
    out = []
    for c in cols:
        c = c.strip()
        if not c or _CONSTRAINT.match(c):
            continue
        m = re.match(rf"^({_IDENT})\s+(.+)$", c, re.S)
        if not m:
            continue
        rest = m.group(2)
        typ = re.split(r"\s+(?:NOT\s+NULL|NULL|DEFAULT|PRIMARY|REFERENCES|UNIQUE|CHECK|"
                       r"CONSTRAINT|GENERATED|COLLATE|IDENTITY)\b", rest, 1, flags=re.I)[0]
        out.append({"name": _unq(m.group(1)), "type": re.sub(r"\s+", " ", typ.strip()),
                    "nullable": not re.search(r"\bNOT\s+NULL\b|\bPRIMARY\s+KEY\b", rest, re.I)})
    return out


def _dialect(text: str) -> str:
    if re.search(r"plpgsql|\$\$|\bSERIAL\b|::\w|\bJSONB\b|ALTER\s+COLUMN\s+\S+\s+TYPE\b", text,
                 re.I):
        return "postgres"
    if re.search(r"\bNVARCHAR\b|^\s*GO\s*$|\[dbo\]|\bIDENTITY\s*\(", text, re.I | re.M):
        return "mssql"
    if re.search(r"\bAUTO_INCREMENT\b|\bENGINE\s*=", text, re.I):
        return "mysql"
    return "other"


class SharedSql(Extractor):
    id = "shared.sql"
    stacks = ()
    extractor_version = "0.1.0"

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        per_sub: dict[str, dict] = {}
        for path in ctx.paths(subproject, lambda e: e["path"].lower().endswith(".sql")):
            text = ctx.read_text(path)
            if text is None:
                res.touch(path, "partial", "unreadable")
                continue
            sub = ctx.subproject_of(path)
            acc = per_sub.setdefault(sub, {"tables": {}, "routines": {}, "entities": {},
                                           "evidence": [], "dialects": set()})
            if FLYWAY.match(posixpath.basename(path)):
                ctx.hints.setdefault("flyway_files", []).append(path)
            acc["dialects"].add(_dialect(text))
            unknown = 0
            for stmt, ln in split_statements(text):
                s = stmt.lstrip("( \t\n")
                m = _CREATE_TABLE.match(s)
                if m:
                    schema, name = _split_name(m.group(1))
                    t = acc["tables"].setdefault((schema, name), {"name": name, "schema": schema,
                                                                  "columns": {}})
                    for col in _columns(m.group(2)):
                        t["columns"][col["name"]] = col
                    acc["evidence"].append((path, ln))
                    continue
                m = _ALTER_TABLE.match(s)
                if m:
                    schema, name = _split_name(m.group(1))
                    t = acc["tables"].setdefault((schema, name), {"name": name, "schema": schema,
                                                                  "columns": {}})
                    for am in re.finditer(rf"\bADD\s+(?:COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?"
                                          rf"({_IDENT})\s+([^,]+)", m.group(2), re.I):
                        if _CONSTRAINT.match(am.group(1)):
                            continue
                        col = _columns(f"{am.group(1)} {am.group(2)}")
                        if col:
                            t["columns"][col[0]["name"]] = col[0]
                    for am in re.finditer(rf"\bALTER\s+COLUMN\s+({_IDENT})\s+(?:SET\s+DATA\s+)?"
                                          rf"TYPE\s+([^,]+)", m.group(2), re.I):
                        cname = _unq(am.group(1))
                        prev = t["columns"].get(cname, {"name": cname, "nullable": None})
                        t["columns"][cname] = dict(prev, type=re.sub(r"\s+", " ",
                                                                     am.group(2).strip()))
                    acc["evidence"].append((path, ln))
                    continue
                m = _VIEW.match(s)
                if m:
                    schema, name = _split_name(m.group(1))
                    acc["tables"].setdefault((schema, name), {"name": name, "schema": schema,
                                                              "columns": {}, "view": True})
                    acc["evidence"].append((path, ln))
                    continue
                m = _ROUTINE.match(s)
                if m:
                    schema, name = _split_name(m.group(2))
                    lang = re.search(r"\bLANGUAGE\s+'?(\w+)", s, re.I)
                    kind = m.group(1).lower()
                    acc["routines"][(schema, name)] = {
                        "name": name, "schema": schema,
                        "kind": "procedure" if kind == "proc" else kind,
                        "language": lang.group(1).lower() if lang else None,
                        "defined_in": f"{path}:{ln}"}
                    acc["evidence"].append((path, ln))
                    continue
                m = _DML.match(s)
                if m:
                    schema, name = _split_name(m.group(2))
                    acc["entities"].setdefault((schema, name), {
                        "name": name, "table": name, "schema": schema,
                        "defined_in": f"{path}:{ln}", "operation": "write"})
                    acc["evidence"].append((path, ln))
                    continue
                if not _KNOWN.match(s):
                    unknown += 1
            res.touch(path, "partial" if unknown else "full")
        for sub, acc in sorted(per_sub.items()):
            if not acc["evidence"] and not acc["entities"]:
                continue
            dialects = sorted(acc["dialects"] - {"other"})
            store = dialects[0] if len(dialects) == 1 else "other"
            tables = []
            for (_s, _n), t in sorted(acc["tables"].items(), key=lambda kv: (kv[0][0] or "",
                                                                             kv[0][1])):
                entry = {"name": t["name"], "schema": t["schema"],
                         "columns": [t["columns"][c] for c in sorted(t["columns"])]}
                if t.get("view"):
                    entry["view"] = True
                tables.append(entry)
            ents = [acc["entities"][k] for k in sorted(acc["entities"],
                                                        key=lambda k: (k[0] or "", k[1]))]
            ev_src = acc["evidence"] or [(e["defined_in"].rsplit(":", 1)[0],
                                          int(e["defined_in"].rsplit(":", 1)[1])) for e in ents]
            attrs = {"store_type": store, "host": None, "database": None, "name_from": None,
                     "orm": None, "entities": ents, "collections": [], "stored_procedures": [],
                     "operation": "write" if ents or tables else None, "owns_schema": None,
                     "routines": [acc["routines"][k] for k in sorted(
                         acc["routines"], key=lambda k: (k[0] or "", k[1]))],
                     "tables_ddl": tables}
            res.items.append(make_item("data_access", sub, None, attrs,
                                       [ctx.evidence(f, ln) for f, ln in ev_src], self,
                                       "high" if store != "other" else "medium"))
        return res

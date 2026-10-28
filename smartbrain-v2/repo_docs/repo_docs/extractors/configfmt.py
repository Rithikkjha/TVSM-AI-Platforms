"""Structured-file parsers with 1-based line numbers (stdlib + PyYAML only).

Each parser returns a result with ``ok`` / ``error`` so callers set ledger ``parse`` to
``full`` (ok) or ``partial`` (error; whatever was recovered is still returned).
Values returned here are RAW: callers must pass them through ``config_classify`` before writing.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from xml.parsers import expat

import yaml

Path_ = tuple  # key path: tuple of str (mapping keys) / int (sequence indexes)


@dataclass
class Entries:
    """Flat (key, value, line) list. For JSON/YAML ``key`` is a path tuple."""
    entries: list = field(default_factory=list)
    ok: bool = True
    error: str | None = None
    data: object = None


# ---- .properties ---------------------------------------------------------------------------
_PROP_ESC = {"t": "\t", "n": "\n", "r": "\r", "f": "\f"}


def _prop_unescape(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            nx = s[i + 1]
            if nx == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", s[i + 2:i + 6] or ""):
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
                continue
            out.append(_PROP_ESC.get(nx, nx))
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def parse_properties(text: str) -> Entries:
    """Java .properties: continuations, ``=`` / ``:`` / whitespace separators, ``#``/``!`` comments,
    unicode escapes. Entries: (key, value, line_of_key)."""
    res = Entries()
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\r")
        start = i + 1
        stripped = raw.lstrip()
        i += 1
        if not stripped or stripped[0] in "#!":
            continue
        logical = stripped
        while _odd_backslashes(logical) and i < len(lines):
            logical = logical[:-1] + lines[i].rstrip("\r").lstrip()
            i += 1
        # split key / value at first unescaped separator
        k_end, j = None, 0
        while j < len(logical):
            c = logical[j]
            if c == "\\":
                j += 2
                continue
            if c in "=:" or c in " \t\f":
                k_end = j
                break
            j += 1
        if k_end is None:
            key, value = logical, ""
        else:
            key = logical[:k_end]
            rest = logical[k_end:].lstrip(" \t\f")
            if rest[:1] in ("=", ":") and logical[k_end] in " \t\f":
                rest = rest[1:].lstrip(" \t\f")
            elif logical[k_end] in "=:":
                rest = logical[k_end + 1:].lstrip(" \t\f")
            value = rest
        res.entries.append((_prop_unescape(key), _prop_unescape(value), start))
    return res


def _odd_backslashes(s: str) -> bool:
    n = len(s) - len(s.rstrip("\\"))
    return n % 2 == 1


# ---- .env ----------------------------------------------------------------------------------
_ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_.\-]*)\s*=\s?(.*)$")


def parse_dotenv(text: str) -> Entries:
    """dotenv: ``export``, single/double quotes (double: \\n escapes, multi-line), inline
    `` #`` comments for unquoted values. Lines that are not assignments make the result partial."""
    res = Entries()
    lines = text.split("\n")
    i = 0
    bad = []
    while i < len(lines):
        raw = lines[i].rstrip("\r")
        ln = i + 1
        i += 1
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = _ENV_LINE.match(raw)
        if not m:
            bad.append(ln)
            continue
        key, val = m.group(1), m.group(2).strip()
        if val[:1] in ("'", '"'):
            q = val[0]
            body = val[1:]
            while q not in _unescaped(body, q) and i < len(lines):
                body += "\n" + lines[i].rstrip("\r")
                i += 1
            end = _find_quote(body, q)
            if end < 0:
                bad.append(ln)
                val = body
            else:
                val = body[:end]
            if q == '"':
                val = val.replace("\\n", "\n").replace('\\"', '"')
        else:
            val = re.split(r"\s+#", val, 1)[0].strip()
        res.entries.append((key, val, ln))
    if bad:
        res.ok = False
        res.error = f"dotenv: unparsable line(s) {bad[:5]}"
    return res


def _find_quote(s: str, q: str) -> int:
    i = 0
    while i < len(s):
        if s[i] == "\\" and q == '"':
            i += 2
            continue
        if s[i] == q:
            return i
        i += 1
    return -1


def _unescaped(s: str, q: str) -> str:
    return q if _find_quote(s, q) >= 0 else ""


# ---- JSON / JSONC --------------------------------------------------------------------------
def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments outside strings and trailing commas (newlines preserved)."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.extend("\n" if ch == "\n" else " " for ch in text[i:j])
            i = j
            continue
        out.append(c)
        i += 1
    s = "".join(out)
    # trailing commas: replace the comma (keep length / newlines)
    return re.sub(r",(\s*[}\]])", lambda m: " " + m.group(1), s)


class _JsonLines:
    """Minimal scanner over valid JSON mapping each value path to the line of its key/value."""

    def __init__(self, s: str):
        self.s, self.i, self.line = s, 0, 1
        self.out: list = []

    def ws(self):
        s = self.s
        while self.i < len(s) and s[self.i] in " \t\r\n":
            if s[self.i] == "\n":
                self.line += 1
            self.i += 1

    def string(self) -> str:
        start = self.i
        self.i += 1
        s = self.s
        while s[self.i] != '"':
            if s[self.i] == "\\":
                self.i += 1
            self.i += 1
        self.i += 1
        return json.loads(s[start:self.i])

    def value(self, path: tuple, line: int):
        self.ws()
        c = self.s[self.i]
        if c == "{":
            self.i += 1
            self.out.append((path, {}, line)) if path else None
            self.ws()
            if self.s[self.i] == "}":
                self.i += 1
                return
            while True:
                self.ws()
                kl = self.line
                key = self.string()
                self.ws()
                self.i += 1  # ':'
                self.value(path + (key,), kl)
                self.ws()
                if self.s[self.i] == ",":
                    self.i += 1
                    continue
                self.i += 1  # '}'
                return
        if c == "[":
            self.i += 1
            self.out.append((path, [], line)) if path else None
            self.ws()
            if self.s[self.i] == "]":
                self.i += 1
                return
            idx = 0
            while True:
                self.ws()
                self.value(path + (idx,), self.line)
                idx += 1
                self.ws()
                if self.s[self.i] == ",":
                    self.i += 1
                    continue
                self.i += 1
                return
        if c == '"':
            self.out.append((path, self.string(), line))
            return
        m = re.compile(r"-?\d+(\.\d+)?([eE][+-]?\d+)?|true|false|null").match(self.s, self.i)
        self.i = m.end()
        self.out.append((path, json.loads(m.group(0)), line))


def parse_jsonc(text: str) -> Entries:
    """JSON with comments / trailing commas. Entries: (path tuple, scalar or {}/[] marker, line)."""
    res = Entries()
    stripped = strip_jsonc(text.lstrip("\ufeff"))
    try:
        res.data = json.loads(stripped)
    except ValueError as e:
        res.ok, res.error = False, f"JSONDecodeError: {e}"
        return res
    sc = _JsonLines(stripped)
    sc.value((), 1)
    res.entries = sc.out
    return res


# ---- YAML ----------------------------------------------------------------------------------
@dataclass
class YamlDoc:
    data: object
    entries: list          # (path tuple, scalar / {} / [] marker, line)
    profile: str | None    # Spring profile of this document
    start_line: int


def _yaml_walk(node, path: tuple, out: list, loader) -> object:
    if isinstance(node, yaml.MappingNode):
        d = {}
        for k, v in node.value:
            if isinstance(k, yaml.ScalarNode):
                key = loader.construct_object(k, deep=True)
            else:
                key = str(loader.construct_object(k, deep=True))
            if k.tag == "tag:yaml.org,2002:merge":
                continue
            key = str(key) if not isinstance(key, str) else key
            out.append((path + (key,), {} if isinstance(v, yaml.MappingNode) else
                        [] if isinstance(v, yaml.SequenceNode) else None, k.start_mark.line + 1))
            idx = len(out) - 1
            val = _yaml_walk(v, path + (key,), out, loader)
            if not isinstance(v, (yaml.MappingNode, yaml.SequenceNode)):
                out[idx] = (path + (key,), val, k.start_mark.line + 1)
            d[key] = val
        return d
    if isinstance(node, yaml.SequenceNode):
        lst = []
        for i, v in enumerate(node.value):
            if not isinstance(v, (yaml.MappingNode, yaml.SequenceNode)):
                val = loader.construct_object(v, deep=True)
                out.append((path + (i,), val, v.start_mark.line + 1))
            else:
                out.append((path + (i,), {} if isinstance(v, yaml.MappingNode) else [],
                            v.start_mark.line + 1))
                val = _yaml_walk(v, path + (i,), out, loader)
            lst.append(val)
        return lst
    return loader.construct_object(node, deep=True)


def _spring_profile(data) -> str | None:
    if not isinstance(data, dict):
        return None
    sp = data.get("spring")
    if isinstance(sp, dict):
        cfg = sp.get("config")
        if isinstance(cfg, dict):
            act = cfg.get("activate")
            if isinstance(act, dict) and act.get("on-profile"):
                return str(act["on-profile"])
        prof = sp.get("profiles")
        if isinstance(prof, str):
            return prof
    for k in ("spring.config.activate.on-profile", "spring.profiles"):
        if isinstance(data.get(k), str):
            return data[k]
    return None


def yaml_with_lines(text: str) -> tuple[list[YamlDoc], bool, str | None]:
    """All documents of a YAML stream with per-key lines. Returns (docs, ok, error)."""
    docs: list[YamlDoc] = []
    try:
        loader = yaml.SafeLoader(text.lstrip("\ufeff"))
        try:
            while loader.check_node():
                node = loader.get_node()
                if node is None:
                    continue
                out: list = []
                data = _yaml_walk(node, (), out, loader)
                docs.append(YamlDoc(data, out, _spring_profile(data), node.start_mark.line + 1))
        finally:
            loader.dispose()
    except yaml.YAMLError as e:
        msg = str(e).splitlines()
        where = ""
        mark = getattr(e, "problem_mark", None)
        if mark is not None:
            where = f" (line {mark.line + 1})"
        prob = getattr(e, "problem", None) or (msg[0] if msg else "")
        return docs, False, f"YAMLError: {prob}{where}"
    except Exception as e:  # constructor errors on unknown tags etc.
        return docs, False, f"{type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}"
    return docs, True, None


def flatten_key(path: tuple, sep: str = ".") -> str:
    return sep.join(str(p) if not isinstance(p, int) else f"[{p}]" for p in path).replace(
        sep + "[", "[")


# ---- XML -----------------------------------------------------------------------------------
@dataclass
class XmlDoc:
    root: ET.Element | None
    lines: dict  # id(element) -> line
    ok: bool
    error: str | None

    def line(self, el) -> int:
        return self.lines.get(id(el), 1)


def _local(tag: str) -> str:
    return tag.rsplit(":", 1)[-1]


def xml_with_lines(text: str) -> XmlDoc:
    """ElementTree with namespace prefixes stripped and the start line of every element."""
    tb = ET.TreeBuilder()
    lines: dict = {}
    keep: list = []
    p = expat.ParserCreate()

    def start(name, attrs):
        el = tb.start(_local(name), {_local(k): v for k, v in attrs.items()})
        lines[id(el)] = p.CurrentLineNumber
        keep.append(el)

    p.StartElementHandler = start
    p.EndElementHandler = lambda name: tb.end(_local(name))
    p.CharacterDataHandler = tb.data
    try:
        p.Parse(text.lstrip("\ufeff").encode("utf-8"), True)
        root = tb.close()
        return XmlDoc(root, lines, True, None)
    except (expat.ExpatError, AssertionError, IndexError) as e:
        return XmlDoc(keep[0] if keep else None, lines, False, f"XMLError: {e}")


def xml_text(el, child: str) -> str | None:
    c = el.find(child) if el is not None else None
    return c.text.strip() if c is not None and c.text and c.text.strip() else None


# ---- Dockerfile ----------------------------------------------------------------------------
DOCKER_INSTR = {"FROM", "ARG", "ENV", "EXPOSE", "ENTRYPOINT", "CMD", "RUN", "COPY", "ADD",
                "WORKDIR", "USER", "LABEL", "VOLUME", "HEALTHCHECK", "SHELL", "STOPSIGNAL",
                "ONBUILD", "MAINTAINER"}


def parse_dockerfile(text: str) -> Entries:
    """(INSTRUCTION, args, first_line) with ``\\`` continuations joined, comments skipped."""
    res = Entries()
    lines = text.split("\n")
    i, bad = 0, []
    while i < len(lines):
        raw = lines[i].rstrip("\r")
        ln = i + 1
        i += 1
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        logical = s
        cont = logical.endswith("\\")
        while cont and i < len(lines):
            logical = logical.rstrip("\\").rstrip() if logical.endswith("\\") else logical
            nxt = lines[i].rstrip("\r").strip()
            i += 1
            if nxt.startswith("#") or not nxt:
                continue  # comment / blank lines inside a continuation are skipped
            logical += " " + nxt
            cont = nxt.endswith("\\")
        logical = logical.rstrip("\\").rstrip()
        parts = logical.split(None, 1)
        instr = parts[0].upper()
        if instr not in DOCKER_INSTR:
            bad.append(ln)
            continue
        res.entries.append((instr, parts[1].strip() if len(parts) > 1 else "", ln))
    if bad:
        res.ok, res.error = False, f"Dockerfile: unknown instruction at line(s) {bad[:5]}"
    return res


def docker_kv(args: str) -> list[tuple[str, str]]:
    """ENV/ARG/LABEL argument pairs: ``K=V K2="v 2"`` or legacy ``K V``."""
    args = args.strip()
    if not args:
        return []
    if "=" not in args.split(None, 1)[0]:
        parts = args.split(None, 1)
        return [(parts[0], parts[1] if len(parts) > 1 else "")]
    out = []
    for m in re.finditer(r"""([A-Za-z_][\w.\-]*)(?:=("(?:[^"\\]|\\.)*"|'[^']*'|\S*))?""", args):
        v = m.group(2) or ""
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out.append((m.group(1), v))
    return out

"""URL / route path normalization shared by every extractor (keys) and phase 4 (matching).

Param forms: ``{x}``, ``{x:int}``, ``{x:regex(\\d{3})}`` (nested braces), ``{x?}``, ``{*x}``,
``{**x}``, ``{x=default}``, ``:x``, ``[x]``, ``[...x]``, ``[[...x]]``, ``${expr}``, ``{0}``,
``%s``/``%d``, concatenation holes ``{}``.

- ``display_path``: every param -> ``{name}`` (``{}`` when there is no name)
- ``normalize``: every param -> ``{}``
- ``match_key``: normalize + lowercase literal segments + no trailing ``/``
All three ensure a leading ``/``, collapse ``//``, strip ``~/`` and drop query/fragment.
"""
from __future__ import annotations

import re

_SCHEME = re.compile(r"^([a-z][a-z0-9+.\-]*://[^/?#]*)(.*)$", re.I)
_IDENT_TAIL = re.compile(r"([A-Za-z_$][\w$]*)\s*(?:\)|\]|\?)?\s*$")
_FMT = re.compile(r"%[sdif]")


def _param_name(inner: str) -> str:
    """Name of a ``{...}`` route param (constraint/default/optional/catch-all stripped)."""
    s = inner.strip()
    s = s.lstrip("*")
    s = re.split(r"[:=]", s, 1)[0]
    s = s.rstrip("?").strip()
    return s if re.fullmatch(r"[A-Za-z_][\w.\-]*|\d+", s) else ""


def _expr_name(expr: str) -> str:
    """Name for a ``${expr}`` hole: the last identifier (``this.a.id`` -> ``id``)."""
    e = expr.strip()
    m = _IDENT_TAIL.search(e)
    if m and re.fullmatch(r"[\w$.\s?!]+(\(\))?", e):
        return m.group(1)
    return ""


def _scan(p: str) -> list[tuple[str, str]]:
    """Tokens: ('lit', text) | ('param', name). Handles nested braces and ``${}``."""
    toks: list[tuple[str, str]] = []
    buf = []
    i, n = 0, len(p)
    while i < n:
        c = p[i]
        if c == "$" and i + 1 < n and p[i + 1] == "{" or c == "{":
            start = i + (2 if c == "$" else 1)
            depth, j = 1, start
            while j < n and depth:
                if p[j] == "{":
                    depth += 1
                elif p[j] == "}":
                    depth -= 1
                j += 1
            if depth:  # unbalanced -> literal
                buf.append(c)
                i += 1
                continue
            inner = p[start:j - 1]
            if buf:
                toks.append(("lit", "".join(buf)))
                buf = []
            toks.append(("param", _expr_name(inner) if c == "$" else _param_name(inner)))
            i = j
            continue
        if c == "%" and _FMT.match(p, i):
            if buf:
                toks.append(("lit", "".join(buf)))
                buf = []
            toks.append(("param", ""))
            i += 2
            continue
        buf.append(c)
        i += 1
    if buf:
        toks.append(("lit", "".join(buf)))
    return toks


def _strip_query(p: str) -> str:
    # only split on ?/# outside braces
    depth = 0
    for i, c in enumerate(p):
        if c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif c in "?#" and depth == 0:
            return p[:i]
    return p


def split_url(s: str) -> tuple[str | None, str, list[str]]:
    """(base or None, path, query param names). ``https://h:1/a?b=1`` -> ('https://h:1', '/a', ['b']).
    A leading hole (``${base}/x``, ``{}/x``) is returned as base."""
    s = (s or "").strip()
    base = None
    m = _SCHEME.match(s)
    if m:
        base, s = m.group(1), m.group(2)
    else:
        m2 = re.match(r"^(\$\{[^{}]*\}|\{\})(?=/|$)", s)
        if m2:
            base, s = m2.group(1), s[m2.end():]
    path = _strip_query(s)
    rest = s[len(path):]
    query: list[str] = []
    if rest.startswith("?"):
        q = rest[1:].split("#", 1)[0]
        for part in q.split("&"):
            name = part.split("=", 1)[0].strip()
            if name and name not in query:
                query.append(name)
    return base, path, query


def _segments(p: str, keep_names: bool) -> str:
    p = (p or "").strip()
    m = _SCHEME.match(p)
    if m:
        p = m.group(2)
    p = _strip_query(p)
    if p.startswith("~/"):
        p = p[1:]
    out = []
    for kind, val in _scan(p):
        if kind == "param":
            out.append("{" + (val if keep_names else "") + "}")
        else:
            out.append(val)
    s = "".join(out)
    segs = []
    for seg in s.split("/"):
        if seg == "":
            continue
        mm = re.fullmatch(r":([A-Za-z_]\w*)\??(?:\(.*\))?", seg)
        if mm:
            seg = "{" + (mm.group(1) if keep_names else "") + "}"
        else:
            mm = re.fullmatch(r"\[\[?(?:\.\.\.)?([A-Za-z_]\w*)\]\]?", seg)
            if mm:
                seg = "{" + (mm.group(1) if keep_names else "") + "}"
        segs.append(seg)
    return "/" + "/".join(segs)


def display_path(p: str) -> str:
    return _segments(p, keep_names=True)


def normalize(p: str) -> str:
    return _segments(p, keep_names=False)


def match_key(p: str) -> str:
    n = normalize(p)
    segs = [s if "{}" in s else s.lower() for s in n.split("/")]
    out = "/".join(segs)
    return out if out == "/" else out.rstrip("/") or "/"


def join(a: str | None, b: str | None) -> str:
    """Route join: strip trailing '/' of a, '/' before b unless empty, leading '/', no '//'."""
    a = (a or "").rstrip("/")
    b = (b or "").strip()
    s = a + ("/" + b.lstrip("/") if b else "")
    s = re.sub(r"/{2,}", "/", s)
    return s if s.startswith("/") else "/" + s

"""inventory.json item kinds (docs/SCHEMAS.md#item-kinds-and-attributes) + item validation.

``KINDS`` holds the attribute keys of every kind, copied 1:1 from the SCHEMAS table. Every item
carries every key of its kind (``[]`` for list attributes, ``{}`` for dict attributes, else
``None`` when unknown).
"""
from __future__ import annotations

import json
from typing import Callable

from . import pathnorm
from .config_classify import redact_line
from .extractors.base import Evidence, InventoryItem
from .secrets import SecretFilter

_OUTBOUND = ("method", "client", "client_name", "base_url_source", "base_url_values",
             "path_template", "path_raw", "query_params", "headers", "request", "response",
             "via_wrapper", "role", "target_hint")

KINDS: dict[str, tuple[str, ...]] = {
    "inbound_http": ("method", "path", "path_raw", "path_params_normalized", "handler",
                     "framework", "params", "request", "responses", "auth", "auth_raw",
                     "allow_anonymous", "deprecated", "contract_file", "context_path_by_env"),
    "schema": ("name", "defined_in", "language", "schema_kind", "fields", "enum_values",
               "type_params", "extends", "resolved"),
    "outbound_http": _OUTBOUND,
    "frontend_api_call": _OUTBOUND + ("ui_framework", "runtime", "base_url_kind"),
    "messaging": ("direction", "broker", "entity", "entity_type", "namespace", "name_from",
                  "name_key", "resolved_values", "subscription", "filter", "message_types",
                  "payload", "properties", "published_by", "handler", "trigger",
                  "error_handling", "library", "role"),
    "data_access": ("store_type", "host", "database", "name_from", "orm", "entities",
                    "collections", "stored_procedures", "operation", "owns_schema", "routines",
                    "tables_ddl"),
    "config_key": ("name", "canonical", "reads", "defined_in", "values", "value_kind", "secret",
                   "kv_ref", "ref", "provided_by", "required"),
    "scheduled_job": ("trigger_type", "expression", "expression_from", "resolved_values",
                      "timezone", "handler", "name"),
    "external_system": ("name", "matched_by", "match", "category", "from_item"),
    "dependency": ("ecosystem", "name", "version", "version_from", "scope", "manifest",
                   "internal", "internal_repo", "kind"),
    "artifact": ("ecosystem", "name", "version", "packaging"),
    "infra": ("infra_kind", "name", "namespace", "image", "base_images", "ports", "env", "hosts",
              "paths", "configmap_refs", "secret_refs", "variables", "variable_groups",
              "environments", "deploy_targets", "servicebus_entities"),
    "api_contract": ("format", "file", "generator", "generated", "docs_path", "operations",
                     "title", "version"),
}

_OUT_LISTS = frozenset({"query_params", "headers"})
LIST_ATTRS: dict[str, frozenset] = {
    "inbound_http": frozenset({"params", "responses"}),
    "schema": frozenset({"fields", "enum_values", "type_params"}),
    "outbound_http": _OUT_LISTS,
    "frontend_api_call": _OUT_LISTS,
    "messaging": frozenset({"message_types"}),
    "data_access": frozenset({"entities", "collections", "stored_procedures", "routines",
                              "tables_ddl"}),
    "config_key": frozenset({"reads", "defined_in"}),
    "scheduled_job": frozenset(),
    "external_system": frozenset(),
    "dependency": frozenset(),
    "artifact": frozenset(),
    "infra": frozenset({"base_images", "ports", "env", "hosts", "paths", "configmap_refs",
                        "secret_refs", "variables", "variable_groups", "environments",
                        "deploy_targets", "servicebus_entities"}),
    "api_contract": frozenset(),
}
DICT_ATTRS: dict[str, frozenset] = {
    "inbound_http": frozenset({"context_path_by_env"}),
    "schema": frozenset(),
    "outbound_http": frozenset({"base_url_values"}),
    "frontend_api_call": frozenset({"base_url_values"}),
    "messaging": frozenset({"resolved_values", "properties", "error_handling"}),
    "data_access": frozenset(),
    "config_key": frozenset({"values"}),
    "scheduled_job": frozenset({"resolved_values"}),
    "external_system": frozenset(),
    "dependency": frozenset(),
    "artifact": frozenset(),
    "infra": frozenset(),
    "api_contract": frozenset(),
}

SOURCES = ("code", "contract")
CONFIDENCES = ("high", "medium")
EVIDENCE_CAP = 25


def _ref(v) -> str:
    return v if v not in (None, "") else "_"


def _messaging_key(a: dict) -> str:
    nf = a.get("name_from")
    ref = a.get("entity") if nf in (None, "literal") else nf
    if nf == "unknown" and a.get("name_key"):
        ref = f"unknown:{a['name_key']}"   # keep distinct dynamic entities apart (FEAT-004)
    return f"{a.get('direction')}:{a.get('broker')}:{_ref(ref)}"


def _http_key(a: dict) -> str:
    return f"{a.get('method') or 'ANY'}:{pathnorm.normalize(a.get('path') or '/')}"


def _call_key(a: dict) -> str:
    src = a.get("base_url_source")
    if src in (None, "unknown"):
        base = "_"
    elif src == "literal":
        vals = a.get("base_url_values") or {}
        url = vals.get("default") or next(iter(sorted(vals.values())), None) if vals else None
        base = _ref((pathnorm.split_url(url)[0] or "").split("://")[-1] if url else None)
    else:
        base = src
    return f"{a.get('method') or 'ANY'}:{base}:{pathnorm.normalize(a.get('path_template') or '/')}"


KIND_KEY: dict[str, Callable[[dict], str]] = {
    "inbound_http": _http_key,
    "schema": lambda a: str(a.get("name")),
    "outbound_http": _call_key,
    "frontend_api_call": _call_key,
    "messaging": _messaging_key,
    "data_access": lambda a: f"{a.get('store_type')}:{_ref(a.get('name_from') or a.get('host'))}",
    "config_key": lambda a: str(a.get("canonical")),
    "scheduled_job": lambda a: str(a.get("handler")),
    "external_system": lambda a: str(a.get("name")),
    "dependency": lambda a: f"{a.get('ecosystem')}:{a.get('name')}",
    "artifact": lambda a: f"{a.get('ecosystem')}:{a.get('name')}",
    "infra": lambda a: f"{a.get('infra_kind')}:{a.get('name')}",
    "api_contract": lambda a: str(a.get("file") or a.get("generator")),
}


class SchemaError(ValueError):
    pass


def default_attrs(kind: str) -> dict:
    return {k: ([] if k in LIST_ATTRS[kind] else {} if k in DICT_ATTRS[kind] else None)
            for k in KINDS[kind]}


def make_id(kind: str, subproject: str | None, key: str) -> str:
    return f"{kind}:{subproject or '.'}:{key}"


def make_item(kind: str, subproject: str | None, key: str | None, attrs: dict,
              evidence: list[Evidence], extractor, confidence: str = "high",
              source: str = "code") -> InventoryItem:
    """Build an item with every attribute key of ``kind`` present. Unknown keys -> SchemaError.
    ``key`` None -> computed by ``KIND_KEY[kind]``. ``extractor`` is an Extractor (id/version) or
    an ``(id, version)`` tuple."""
    if kind not in KINDS:
        raise SchemaError(f"unknown kind {kind!r}")
    unknown = sorted(set(attrs) - set(KINDS[kind]))
    if unknown:
        raise SchemaError(f"{kind}: unknown attribute(s) {unknown}")
    full = default_attrs(kind)
    full.update(attrs)
    if key is None:
        key = KIND_KEY[kind](full)
    if isinstance(extractor, tuple):
        ex_id, ex_ver = extractor
    else:
        ex_id, ex_ver = extractor.id, extractor.extractor_version
    return InventoryItem(id=make_id(kind, subproject, key), kind=kind,
                         subproject=subproject or ".", attributes=full,
                         evidence=list(evidence), source=source, extractor_id=ex_id,
                         extractor_version=ex_ver, confidence=confidence)


def validate_item(item: InventoryItem, ledger_index: dict,
                  line_reader: Callable[[str, int], str | None]) -> list[str]:
    """SCHEMAS evidence + shape rules. Returns a list of problems (empty = valid)."""
    errs: list[str] = []
    if item.kind not in KINDS:
        return [f"{item.id}: unknown kind {item.kind!r}"]
    keys = set(item.attributes)
    want = set(KINDS[item.kind])
    if keys != want:
        errs.append(f"{item.id}: attribute keys differ (missing {sorted(want - keys)}, "
                    f"extra {sorted(keys - want)})")
    if not item.id.startswith(f"{item.kind}:{item.subproject}:"):
        errs.append(f"{item.id}: id does not match kind/subproject")
    if item.source not in SOURCES:
        errs.append(f"{item.id}: invalid source {item.source!r}")
    if item.confidence not in CONFIDENCES:
        errs.append(f"{item.id}: invalid confidence {item.confidence!r}")
    if not item.extractor_id:
        errs.append(f"{item.id}: missing extractor id")
    if not item.evidence:
        errs.append(f"{item.id}: no evidence")
    for ev in item.evidence:
        ent = ledger_index.get(ev.file)
        where = f"{item.id}: evidence {ev.file}:{ev.line}"
        if ent is None:
            errs.append(f"{where}: file not in ledger")
            continue
        st = ent.get("status") or ""
        if st.startswith("skipped:") or st.startswith("failed:"):
            errs.append(f"{where}: file is {st}")
            continue
        lines = ent.get("lines")
        if not isinstance(ev.line, int) or lines is None or not 1 <= ev.line <= lines:
            errs.append(f"{where}: line out of range (lines={lines})")
            continue
        raw = line_reader(ev.file, ev.line)
        if raw is None:
            errs.append(f"{where}: line unreadable")
            continue
        red = redact_line(raw).strip()
        if len(ev.snippet) > 200 or ev.snippet not in red:
            errs.append(f"{where}: snippet is not a substring of the redacted line")
    blob = json.dumps(item.to_dict(), ensure_ascii=False)
    for s in SecretFilter.secrets():
        if s and s in blob:
            errs.append(f"{item.id}: contains a registered secret")
            break
    return errs

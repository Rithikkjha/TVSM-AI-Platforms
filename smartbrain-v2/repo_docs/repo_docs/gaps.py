"""gaps.json: what Phase 2 could not settle, the input of the Phase 3 gap-fill agent
(docs/SCHEMAS.md#runsorgrepogapsjson, docs/PIPELINE.md#phase-3--targeted-gap-fill-planned).

Built by ``extract`` from the same in-memory results that produce inventory.json and the
recomputed ledger; deterministic (sorted, no timestamps). Each entry: ``type``, ``file``,
``line`` (when known), ``reason``, ``item`` (related item id or null). Never contains values,
only paths, ids and short reasons.
"""
from __future__ import annotations

import posixpath
import re

GAPS_VERSION = "0.1.2"
REASON_MAX = 200

TYPES = ("unresolved_base_url", "unresolved_entity", "missing_payload", "missing_schema",
         "partial_parse", "silent_client_file", "untouched_source", "untouched_file",
         "unknown_repo_type")
CALL_KINDS = ("outbound_http", "frontend_api_call")
BODY_METHODS = ("POST", "PUT", "PATCH")

# client/SDK usage per language -> item kinds that should have come out of the file
_NODE_PKG = r"""(?:from\s+|require\(\s*|import\s*\(\s*)['"](?:{pkgs})(?:/[^'"]*)?['"]"""


def _node(pkgs: list[str]) -> re.Pattern:
    return re.compile(_NODE_PKG.format(pkgs="|".join(re.escape(p) for p in pkgs)))


CLIENT_RULES: dict[str, tuple[tuple[str, re.Pattern, tuple[str, ...]], ...]] = {
    "java": (
        ("http client", re.compile(
            r"\b(RestTemplate|WebClient|RestClient|OkHttpClient|CloseableHttpClient|"
            r"HttpURLConnection|Retrofit)\b|@FeignClient\b|\bjava\.net\.http\b"), CALL_KINDS),
        ("messaging SDK", re.compile(
            r"\b(ServiceBus(Sender|Processor|Receiver)\w*Client|ServiceBusClientBuilder|"
            r"ServiceBusTemplate|JmsTemplate|KafkaTemplate|RabbitTemplate|AmqpTemplate|"
            r"StreamBridge|EventHub(Producer|Consumer)\w*Client)\b|"
            r"@(JmsListener|KafkaListener|RabbitListener|ServiceBusListener)\b"), ("messaging",)),
        ("data store client", re.compile(
            r"\b(JdbcTemplate|NamedParameterJdbcTemplate|DriverManager|EntityManager|"
            r"(Reactive)?MongoTemplate|MongoClient|RedisTemplate|StringRedisTemplate|Jedis|"
            r"RedissonClient|OpenSearchClient|RestHighLevelClient|ElasticsearchClient|"
            r"SessionPool|CosmosClient|BlobServiceClient|BlobContainerClient|SqlSession)\b|"
            r"\bimport\s+(org\.opensearch|com\.vesoft\.nebula|org\.neo4j|com\.datastax)\."),
         ("data_access",)),
    ),
    "csharp": (
        ("http client", re.compile(
            r"\b(HttpClient|IHttpClientFactory|RestClient|RestRequest|FlurlClient|"
            r"RestService)\b|\.(GetJsonAsync|PostJsonAsync)\b"), CALL_KINDS),
        ("messaging SDK", re.compile(
            r"\b(ServiceBusClient|ServiceBusSender|ServiceBusProcessor|ServiceBusReceiver|"
            r"ServiceBusTrigger|QueueClient|TopicClient|IBus|IPublishEndpoint|"
            r"EventHubProducerClient|EventHubTrigger|QueueTrigger)\b"), ("messaging",)),
        ("data store client", re.compile(
            r"\b(DbContext|SqlConnection|NpgsqlConnection|MySqlConnection|OracleConnection|"
            r"IDbConnection|MongoClient|CosmosClient|BlobServiceClient|BlobContainerClient|"
            r"ConnectionMultiplexer|ElasticClient)\b"), ("data_access",)),
    ),
    "node": (
        ("http client", _node(["axios", "got", "node-fetch", "cross-fetch", "isomorphic-fetch",
                               "superagent", "ky", "undici", "@nestjs/axios"]), CALL_KINDS),
        ("messaging SDK", _node(["@azure/service-bus", "kafkajs", "amqplib",
                                 "amqp-connection-manager", "bull", "bullmq",
                                 "@nestjs/microservices", "@azure/event-hubs"]), ("messaging",)),
        ("data store client", _node(["typeorm", "@nestjs/typeorm", "@prisma/client", "sequelize",
                                     "sequelize-typescript", "mongoose", "@nestjs/mongoose",
                                     "mongodb", "pg", "mysql2", "mysql", "mssql", "redis",
                                     "ioredis", "knex", "@azure/cosmos", "@azure/storage-blob",
                                     "@elastic/elasticsearch",
                                     "@opensearch-project/opensearch"]), ("data_access",)),
    ),
}
_LANG_RULES = {"java": "java", "csharp": "csharp", "javascript": "node", "typescript": "node"}


def _reason(s: str) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:REASON_MAX]


def _entry(typ: str, file: str | None, line: int | None, reason: str,
           item: str | None = None) -> dict:
    return {"type": typ, "file": file, "line": line, "reason": _reason(reason), "item": item}


def _where(it) -> tuple[str | None, int | None]:
    ev = sorted(it.evidence, key=lambda e: (e.file, e.line))
    return (ev[0].file, ev[0].line) if ev else (None, None)


def _item_gaps(items: list) -> list[dict]:
    out = []
    for it in items:
        a = it.attributes
        f, ln = _where(it)
        if it.kind in CALL_KINDS and a.get("base_url_source") in (None, "unknown"):
            out.append(_entry("unresolved_base_url", f, ln,
                              f"{a.get('method') or 'ANY'} {a.get('path_template') or '/'}: "
                              "base URL source unknown", it.id))
        elif it.kind == "messaging":
            nf = a.get("name_from")
            if nf in (None, "unknown") or (a.get("entity") is None
                                            and not a.get("resolved_values")):
                out.append(_entry("unresolved_entity", f, ln,
                                  f"{a.get('direction')} {a.get('broker') or 'unknown broker'}: "
                                  f"entity name not resolved (name_from {nf or 'none'})", it.id))
            if a.get("payload") is None:
                out.append(_entry("missing_payload", f, ln,
                                  f"{a.get('direction')} {a.get('entity') or nf or '?'}: "
                                  "payload type not resolved", it.id))
        elif it.kind == "inbound_http":
            m = a.get("method")
            route = f"{m or 'ANY'} {a.get('path') or '/'}"
            if m in BODY_METHODS and not a.get("request"):
                out.append(_entry("missing_schema", f, ln, f"{route}: no request schema", it.id))
            rs = a.get("responses") or []
            if not any(isinstance(r, dict) and r.get("schema") for r in rs):
                out.append(_entry("missing_schema", f, ln, f"{route}: no response schema",
                                  it.id))
    return out


def _file_gaps(ctx, items: list, ledger: dict, touches: dict,
               suppressed: dict | None = None) -> list[dict]:
    """Per-file gaps. Invariant: every ``pending`` ledger path is listed by exactly one of
    ``partial_parse`` / ``untouched_source`` / ``untouched_file``. An ``http client``
    ``silent_client_file`` is not listed for paths an extractor marked as client factory /
    holder / interface / interceptor (``ctx.hints["silent_ok"]``); those go to ``suppressed``
    ({path: reason})."""
    silent_ok = (getattr(ctx, "hints", None) or {}).get("silent_ok") or {}
    kinds_by_file: dict[str, set] = {}
    for it in items:
        for e in it.evidence:
            kinds_by_file.setdefault(e.file, set()).add(it.kind)
    out, untouched, unlisted = [], [], []
    for f in ledger.get("files") or []:
        st = f.get("status") or ""
        path = f["path"]
        if st.startswith(("skipped:", "failed:")):
            continue
        tl = touches.get(path) or []
        partial = [(ex_id, t) for ex_id, _v, t, _n in sorted(tl, key=lambda x: x[0])
                   if t.parse == "partial"]
        if partial and st == "pending":
            ex_id, t = next(((x, t) for x, t in partial if t.error), partial[0])
            why = f"parse error: {t.error}" if t.error else "unresolved or unsupported construct"
            out.append(_entry("partial_parse", path, None, f"{ex_id}: {why}"))
        elif st == "pending":
            if f.get("class") == "source" and not tl:
                untouched.append(path)
            else:
                unlisted.append((path, f.get("class") or "other", bool(tl)))
        if f.get("class") != "source" or not tl:
            continue
        rules = CLIENT_RULES.get(_LANG_RULES.get(f.get("language") or "", ""), ())
        if not rules:
            continue
        text = ctx.read_text(path) or ""
        have = kinds_by_file.get(path, set())
        for label, rx, kinds in rules:
            m = rx.search(text)
            if m and not have & set(kinds) and label == "http client" and path in silent_ok:
                if suppressed is not None:
                    suppressed[path] = silent_ok[path]
                continue
            if m and not have & set(kinds):
                ln = text.count("\n", 0, m.start()) + 1
                out.append(_entry("silent_client_file", path, ln,
                                  f"uses a {label} ({m.group(0).strip()[:60]}) but yielded no "
                                  f"{'/'.join(kinds)} item"))
    for path in sorted(untouched):
        ext = posixpath.splitext(path)[1] or posixpath.basename(path)
        out.append(_entry("untouched_source", path, None,
                          f"no extractor opened this {ext} source file"))
    for path, cls, touched in sorted(unlisted):
        why = "opened but not settled by any extractor" if touched else "no extractor opened it"
        out.append(_entry("untouched_file", path, None, f"{cls} file left pending: {why}"))
    return out


def _order(e: dict) -> tuple:
    return (TYPES.index(e["type"]), e["file"] or "", e["line"] or 0, e["item"] or "",
            e["reason"])


def build(ctx, items: list, ledger: dict, touches: dict, repo_type: str | None,
          head_sha: str | None = None, version: str | None = None) -> dict:
    """gaps.json document for one repo. ``ledger`` is the recomputed ledger; ``touches`` the
    per-file extractor touches from ``phase2_extract.run``."""
    gaps = _item_gaps(items)
    suppressed: dict = {}
    gaps += _file_gaps(ctx, items, ledger, touches, suppressed)
    if repo_type in (None, "unknown"):
        gaps.append(_entry("unknown_repo_type", None, None,
                           "no repo_type rule matched the repo's items and layout"))
    uniq = {}
    for e in gaps:
        uniq.setdefault(tuple(sorted((k, str(v)) for k, v in e.items())), e)
    gaps = sorted(uniq.values(), key=_order)
    by_type = {t: 0 for t in TYPES}
    for e in gaps:
        by_type[e["type"]] += 1
    return {
        "schema_version": 1, "org": ctx.org, "repo": ctx.repo, "head_sha": head_sha,
        "gaps_version": GAPS_VERSION, "version": version, "repo_type": repo_type,
        "summary": {"total": sum(by_type.values()), "by_type": by_type,
                    "suppressed": {r: sum(1 for v in suppressed.values() if v == r)
                                   for r in sorted(set(suppressed.values()))},
                    "suppressed_paths": [f"{p} ({suppressed[p]})" for p in sorted(suppressed)]},
        "gaps": gaps,
    }

"""Config value classifier (docs/SCHEMAS.md#config-value-classifier).

Every config value, ENV/ARG value, pipeline variable and evidence snippet goes through this module
before anything is written. Rules, first match wins:

1. placeholder value (``${X}``, ``${X:default}``, ``#{X}#``, ``$(X)``, ``%X%``, ``__X__``, ``{{X}}``)
   -> ``reference`` (a literal default is classified again by rules 2-6)
2. Key Vault reference -> secret, ``kv_ref`` only
3. secret-like key name -> secret, name only
4. secret-like value -> secret, name only
5. allowed value kind (url/host/path/topic/queue/entity/db-name) -> value recorded
6. anything else -> ``hidden``, name only
"""
from __future__ import annotations

import math
import posixpath
import re
from dataclasses import dataclass

from .secrets import SecretFilter, redact

SECRET_WORDS = frozenset({
    "password", "passwd", "pwd", "secret", "secrets", "token", "tokens", "key", "keys", "apikey",
    "credential", "credentials", "cert", "certificate", "pfx", "sas", "signature", "salt",
    "private",
})
SECRET_SUBSTRINGS = ("connectionstring", "connstr", "connection_string", "connection-string")
ENTITY_WORDS = ("topic", "queue", "subscription", "entity", "exchange", "eventhub", "binding",
                "destination")
DB_WORDS = ("database", "dbname", "db_name", "catalog", "schema")
URL_SCHEMES = ("http", "https", "sb", "amqp", "amqps", "ws", "wss", "grpc")

# ---- placeholders (rule 1) ----------------------------------------------------------------
_PH_FULL = [
    re.compile(r"^\$\{([^{}:]+?)(?::(.*))?\}$", re.S),
    re.compile(r"^#\{([^{}]+)\}#$"),
    re.compile(r"^\$\(([^()]+)\)$"),
    re.compile(r"^%([A-Za-z0-9_.:\-]+)%$"),
    re.compile(r"^__([A-Za-z0-9_.\-]+?)__$"),
    re.compile(r"^\{\{\s*([^{}]+?)\s*\}\}$"),
]
PLACEHOLDER_ANY = re.compile(
    r"\$\{[^{}]+\}|#\{[^{}]+\}#|\$\([A-Za-z0-9_.\-]+\)|\{\{[^{}]+\}\}")

# ---- secret-shaped values (rule 4) ---------------------------------------------------------
_KV_SECRET_URI = re.compile(
    r"@Microsoft\.KeyVault\(\s*SecretUri\s*=\s*https://([A-Za-z0-9-]+)\.vault\.azure\.net/secrets/"
    r"([A-Za-z0-9-]+)", re.I)
_KV_NAMES = re.compile(
    r"@Microsoft\.KeyVault\(\s*VaultName\s*=\s*([A-Za-z0-9-]+)\s*;\s*SecretName\s*=\s*([A-Za-z0-9-]+)",
    re.I)
_CONN_SECRET = re.compile(r"(?:^|;)\s*(password|pwd|accountkey|sharedaccesskey|user id)\s*=", re.I)
_USERINFO = re.compile(r"\b[a-z][a-z0-9+.\-]*://[^/\s@:]+(?::[^/\s@]*)?@", re.I)
_JWT = re.compile(r"eyJ[A-Za-z0-9_\-]{5,}\.[A-Za-z0-9_\-]{5,}\.[A-Za-z0-9_\-]*")
_PEM = re.compile(r"-----BEGIN [A-Z0-9 ]+-----")
_AKIA = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_GHP = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}")
_SAS = re.compile(r"(?:^|[?&;])sig=[^&\s;]+", re.I)

_HOST = re.compile(
    r"^(?:localhost|(?:\d{1,3}\.){3}\d{1,3}|(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,62})\.)+"
    r"[A-Za-z][A-Za-z0-9-]*)(?::\d{1,5})?$")
_ENTITY_VALUE = re.compile(r"^[A-Za-z0-9._/\-]{1,260}$")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]{0,127}$")


@dataclass
class Classified:
    value_kind: str                      # url|host|path|topic|queue|entity|db-name|hidden|reference
    secret: bool
    record_value: str | None             # value safe to write (rule 5 only)
    ref: str | None = None               # placeholder target (rule 1)
    kv_ref: str | None = None            # "<vault>/<name>" (rule 2)
    provided_by: str = "unknown"
    rule: int = 6
    default: "Classified | None" = None  # classification of a literal placeholder default


# ---- helpers ------------------------------------------------------------------------------
def split_words(key: str) -> list[str]:
    """camel/snake/kebab/dot/colon/``__`` split, lower-cased."""
    if not key:
        return []
    parts = re.split(r"[.:_\-/\\\s\[\]]+", key)
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        p = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", p)
        p = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", p)
        out.extend(w.lower() for w in p.split() if w)
    return out


def key_is_secret(key: str) -> bool:
    if not key:
        return False
    low = key.lower()
    if any(s in low for s in SECRET_SUBSTRINGS):
        return True
    if re.match(r"^connectionstrings(:|\.|__)", low):
        return True
    return bool(set(split_words(key)) & SECRET_WORDS)


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


_QUALIFIED = re.compile(r"^[A-Za-z_$][\w$-]*(?:\.[A-Za-z_$][\w$-]*)+(?::\d{1,5})?$")
_CONN_FORM = re.compile(r"(?:^|;)\s*(server|data source|host|endpoint|accountendpoint|accountname|"
                        r"initial catalog|database)\s*=", re.I)


def _looks_url_or_path(v: str) -> bool:
    """URLs, paths, host names and dotted qualified identifiers (class names) are not
    entropy-checked."""
    return (bool(re.match(r"^[a-z][a-z0-9+.\-]*://", v, re.I)) or v.startswith("/") or "/" in v
            or bool(_QUALIFIED.match(v)))


def value_is_secret(value: str) -> bool:
    if not value:
        return False
    v = value.strip()
    if _CONN_SECRET.search(v) and ";" in v or re.match(r"^\s*(password|pwd)\s*=", v, re.I):
        return True
    if ";" in v and _CONN_FORM.search(v):  # connection strings are never stored
        return True
    if _USERINFO.search(v) or _JWT.search(v) or _PEM.search(v) or _AKIA.search(v):
        return True
    if _GHP.search(v) or _SAS.search(v):
        return True
    if len(v) >= 24 and " " not in v and not _looks_url_or_path(v) and _entropy(v) >= 4.0:
        return True
    return False


def _kv_ref(value: str) -> str | None:
    m = _KV_SECRET_URI.search(value) or _KV_NAMES.search(value)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def strip_query(url: str) -> str:
    return url.split("#", 1)[0].split("?", 1)[0]


def provided_by_for_file(file: str | None) -> str:
    if not file:
        return "unknown"
    name = posixpath.basename(file)
    if name.startswith(".env") or name.endswith(".env"):
        return "env-file"
    if (name.startswith("appsettings") or name.startswith("application")
            or name.startswith("bootstrap") or name in ("local.settings.json", "host.json")
            or name.lower() in ("web.config", "app.config")):
        return "app-settings"
    return "unknown"


def _allowed_kind(key: str, v: str) -> str | None:
    low_key = (key or "").lower()
    m = re.match(r"^([a-z][a-z0-9+.\-]*)://", v, re.I)
    if m:
        return "url" if m.group(1).lower() in URL_SCHEMES and not _USERINFO.search(v) else None
    if v.startswith("/") and " " not in v:
        return "path"
    for w in ENTITY_WORDS:
        if w in low_key and _ENTITY_VALUE.match(v):
            if w == "topic":
                return "topic"
            if w == "queue":
                return "queue"
            return "entity"
    if any(w in low_key for w in DB_WORDS) and _IDENT.match(v):
        return "db-name"
    if _HOST.match(v):
        return "host"
    return None


def _placeholder(value: str) -> tuple[str, str | None] | None:
    for rx in _PH_FULL:
        m = rx.match(value)
        if m:
            name = m.group(1).strip()
            default = m.group(2) if rx is _PH_FULL[0] else None
            return name, default
    return None


def classify(key: str, value, *, file: str | None = None) -> Classified:
    """Classify one config ``key = value`` pair. Never returns a secret in ``record_value``."""
    pb = provided_by_for_file(file)
    if value is None or isinstance(value, (dict, list)):
        return Classified("hidden", key_is_secret(key), None, provided_by=pb, rule=6)
    if isinstance(value, bool):
        value = "true" if value else "false"
    v = str(value).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    # rule 1: whole value is a placeholder
    ph = _placeholder(v)
    if ph:
        name, default = ph
        dflt = classify(key, default, file=file) if default not in (None, "") else None
        return Classified("reference", key_is_secret(key) or bool(dflt and dflt.secret), None,
                          ref=name, provided_by=pb, rule=1, default=dflt)
    # rule 2: Key Vault reference
    kv = _kv_ref(v)
    if kv:
        return Classified("hidden", True, None, kv_ref=kv, provided_by="key-vault", rule=2)
    # rule 3: secret-like key name
    if key_is_secret(key):
        return Classified("hidden", True, None, provided_by=pb, rule=3)
    # embedded placeholders: classify the template with the holes neutralized
    ref = None
    m = PLACEHOLDER_ANY.search(v)
    if m:
        inner = re.sub(r"^\$\{|^#\{|^\$\(|^\{\{|\}#$|\}$|\)$|\}\}$", "", m.group(0))
        ref = inner.split(":", 1)[0].strip()
        probe = PLACEHOLDER_ANY.sub("x", v)
    else:
        probe = v
    # rule 4: secret-like value
    if value_is_secret(probe):
        return Classified("hidden", True, None, provided_by=pb, rule=4)
    if not probe:
        return Classified("hidden", False, None, ref=ref, provided_by=pb, rule=6)
    # rule 5: allowed value kinds
    kind = _allowed_kind(key, probe)
    if kind:
        rec = strip_query(v) if kind == "url" else v
        if ref is not None:
            return Classified("reference", False, rec, ref=ref, provided_by=pb, rule=5)
        return Classified(kind, False, rec, provided_by=pb, rule=5)
    return Classified("reference" if ref else "hidden", False, None, ref=ref, provided_by=pb,
                      rule=6)


# ---- store identity ------------------------------------------------------------------------
def _kv_pairs(value: str) -> dict[str, str]:
    out = {}
    for part in value.split(";"):
        k, sep, v = part.partition("=")
        if sep:
            out[k.strip().lower()] = v.strip()
    return out


def parse_store_identity(value: str | None) -> dict | None:
    """{store_type, host, database[, namespace]} parsed from a connection string / URL.
    The connection string itself is never returned."""
    if not value or not isinstance(value, str):
        return None
    v = value.strip()
    m = re.search(r"Endpoint\s*=\s*sb://([A-Za-z0-9.-]+?)(?:\.servicebus\.windows\.net)?/?(?:;|$)",
                  v, re.I)
    if m:
        ns = m.group(1).split(".")[0]
        return {"store_type": "azure-service-bus", "host": f"{ns}.servicebus.windows.net",
                "database": None, "namespace": ns}
    m = re.match(r"^jdbc:(postgresql|mysql|mariadb|sqlserver|oracle(?::thin)?)(?::@|://)"
                 r"(?:[^@/]*@)?([^/:;?]+)(?::\d+)?(?:[/:]([A-Za-z0-9_\-.]+))?(.*)$", v, re.I)
    if m:
        st = {"postgresql": "postgres", "mysql": "mysql", "mariadb": "mysql",
              "sqlserver": "mssql"}.get(m.group(1).lower(), "oracle")
        db = m.group(3)
        if st == "mssql":
            dm = re.search(r"database(?:name)?\s*=\s*([^;]+)", m.group(4) or "", re.I)
            db = dm.group(1).strip() if dm else None
        return {"store_type": st, "host": m.group(2), "database": db}
    m = re.match(r"^(mongodb(?:\+srv)?|redis|rediss|postgres(?:ql)?|mysql)://(?:[^@/]*@)?"
                 r"([^/:,?]+)(?::\d+)?(?:,[^/]*)?(?:/([A-Za-z0-9_\-.]+))?", v, re.I)
    if m:
        st = {"mongodb": "mongo", "mongodb+srv": "mongo", "redis": "redis", "rediss": "redis",
              "postgres": "postgres", "postgresql": "postgres", "mysql": "mysql"}[m.group(1).lower()]
        return {"store_type": st, "host": m.group(2), "database": m.group(3)}
    if ";" in v and "=" in v:
        kv = _kv_pairs(v)
        if "accountendpoint" in kv:
            host = re.sub(r"^https?://", "", kv["accountendpoint"]).split("/")[0].split(":")[0]
            return {"store_type": "cosmos", "host": host, "database": kv.get("database")}
        if "accountname" in kv or "blobendpoint" in kv:
            host = (f"{kv['accountname']}.blob.core.windows.net" if "accountname" in kv else
                    re.sub(r"^https?://", "", kv["blobendpoint"]).split("/")[0])
            return {"store_type": "blob", "host": host, "database": None}
        host = (kv.get("server") or kv.get("data source") or kv.get("host") or kv.get("address")
                or kv.get("addr"))
        db = kv.get("database") or kv.get("initial catalog")
        if host or db:
            st = "mssql"
            if "host" in kv or kv.get("port") == "5432":
                st = "postgres"
            elif kv.get("port") == "3306" or "uid" in kv and "server" in kv and "sslmode" in kv:
                st = "mysql"
            if host:
                host = re.sub(r"^tcp:", "", host, flags=re.I).split(",")[0].strip()
            return {"store_type": st, "host": host or None, "database": db}
    return None


# ---- env name from file name ---------------------------------------------------------------
def env_from_filename(path: str) -> str:
    name = posixpath.basename(path)
    if name == "local.settings.json":
        return "local"
    m = re.match(r"^appsettings\.(.+)\.json$", name, re.I)
    if m:
        return m.group(1)
    m = re.match(r"^(?:application|bootstrap)-(.+)\.(?:properties|ya?ml)$", name)
    if m:
        return m.group(1)
    if name == ".env":
        return "default"
    m = re.match(r"^\.env\.(.+)$", name)
    if m:
        return m.group(1)
    m = re.match(r"^environment\.(.+)\.ts$", name)
    if m:
        return m.group(1)
    m = re.match(r"^values-(.+)\.ya?ml$", name)
    if m:
        return m.group(1)
    return "default"


# ---- key normalization ---------------------------------------------------------------------
_ENV_STYLE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")


def canonical_key(key: str) -> tuple[str, bool]:
    """(canonical, needed_env_rule). Lowercase; ':' and '__' -> '.'; '-' dropped inside segments
    (Spring relaxed binding); env-style A_B_C -> a.b.c (flag True: joins on it are medium)."""
    k = (key or "").strip()
    if _ENV_STYLE.match(k) and "__" not in k:
        return k.lower().replace("_", "."), True
    k = k.replace("__", ".").replace(":", ".")
    segs = [s.replace("-", "").lower() for s in k.split(".")]
    return ".".join(s for s in segs if s != ""), False


# ---- snippet redaction ---------------------------------------------------------------------
_KV_JSON = re.compile(r'"([^"\\]{1,200})"\s*:\s*"((?:[^"\\]|\\.)*)"')
_KV_QUOTED = re.compile(r"""([A-Za-z_][\w.\-:\[\]]*)\s*[:=]\s*(["'])((?:(?!\2).){0,2000}?)\2""")
_KV_LINE = re.compile(r"^(\s*(?:export\s+|-\s+)?)([A-Za-z_][\w.\-:\[\]]*)(\s*[=:]\s*)(.+?)(\s*)$")
_QUOTED = re.compile(r"""(["'`])((?:(?!\1)[^\\]|\\.){24,}?)\1""")
_SHAPES = [_JWT, _PEM, _AKIA, _GHP]
_KV_BARE = re.compile(r"(?<![\w.\-])([A-Za-z_][\w.\-]*)=([^\s\"'`;&,)]+)")


def _secret_hit(key: str, value: str) -> bool:
    c = classify(key, value)
    return c.secret and c.value_kind != "reference" and c.rule in (2, 3, 4) and bool(value)


def _mask_conn(value: str) -> str:
    return re.sub(r"(?i)\b(password|pwd|accountkey|sharedaccesskey|user id|sig)\s*=\s*[^;&\s\"']*",
                  lambda m: m.group(1) + "=***", value)


_URL_QUERY = re.compile(r"(\bhttps?://[^\s?#\"'`]+\?)([^\s#\"'`]+)", re.I)
_QUERY_VAL = re.compile(r"(^|&)([^=&]+)=([^&]*)")


def _mask_qv(m) -> str:
    v = m.group(3)
    if not v or v == "***" or v.startswith(("$", "{", ":", "%")):
        return m.group(0)   # empty, already masked, or a template hole / placeholder
    return f"{m.group(1)}{m.group(2)}=***"


def redact_line(line: str) -> str:
    """Mask secret values in one line (rule 2/3/4 hits in k=v / k: v / "k": "v" / k="v" forms and
    secret-shaped literals anywhere), then redact registered tokens."""
    if not line:
        return redact(line, SecretFilter.secrets())
    out = line

    def json_sub(m):
        if not _secret_hit(m.group(1), m.group(2)):
            return m.group(0)
        s = m.group(0)
        return s[: m.start(2) - m.start(0)] + "***" + s[m.end(2) - m.start(0):]

    out = _KV_JSON.sub(json_sub, out)

    def quoted_sub(m):
        if _secret_hit(m.group(1), m.group(3)):
            return m.group(0)[: m.start(3) - m.start(0)] + "***" + m.group(2)
        return m.group(0)

    out = _KV_QUOTED.sub(quoted_sub, out)
    m = _KV_LINE.match(out)
    if m:
        val = m.group(4)
        code_like = val.rstrip().endswith((";", "{", ",", "(")) or "(" in val or val.startswith(
            ("\"", "'", "`", "new ", "this.", "{", "["))
        cut = re.split(r"\s+#", val, 1)[0]
        if not code_like and "***" not in val and _secret_hit(m.group(2), cut):
            out = m.group(1) + m.group(2) + m.group(3) + "***" + val[len(cut):] + m.group(5)
    # unquoted KEY=value pairs anywhere on the line (Dockerfile ENV, CLI args, compose lists)
    def bare_sub(mm):
        if mm.group(2) != "***" and _secret_hit(mm.group(1), mm.group(2)):
            return mm.group(1) + "=***"
        return mm.group(0)

    out = _KV_BARE.sub(bare_sub, out)
    # secret-shaped literals anywhere
    for rx in _SHAPES:
        out = rx.sub("***", out)
    out = _USERINFO.sub(lambda mm: re.sub(r"//[^@]*@", "//***@", mm.group(0)), out)
    # literal query values of absolute URLs (APIM subscription keys are often passed this way)
    out = _URL_QUERY.sub(lambda mm: mm.group(1) + _QUERY_VAL.sub(_mask_qv, mm.group(2)), out)
    if _CONN_SECRET.search(out) or _SAS.search(out):
        out = _mask_conn(out)

    def ent_sub(mm):
        body = mm.group(2)
        if " " not in body and not _looks_url_or_path(body) and _entropy(body) >= 4.0:
            return mm.group(1) + "***" + mm.group(1)
        return mm.group(0)

    out = _QUOTED.sub(ent_sub, out)
    return redact(out, SecretFilter.secrets())

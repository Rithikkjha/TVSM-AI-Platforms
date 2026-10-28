"""Config value classifier (docs/SCHEMAS.md#config-value-classifier). All secret values are fake."""
from __future__ import annotations

import pytest

from repo_docs import config_classify as cc
from repo_docs.secrets import SecretFilter

FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmYWtlIn0.ZmFrZXNpZ25hdHVyZQ"
FAKE_HIGH_ENTROPY = "q8Zr2LmX9vT4kP7wN1sB6yH3cJ5dF0gA"


@pytest.mark.parametrize("value,ref", [
    ("${DATABASE_HOST_URL}", "DATABASE_HOST_URL"),
    ("${api.base:/api/v1}", "api.base"),
    ("#{Token}#", "Token"),
    ("$(BuildId)", "BuildId"),
    ("%TopicName%", "TopicName"),
    ("__Endpoint__", "Endpoint"),
    ("{{ .Values.url }}", ".Values.url"),
])
def test_rule1_placeholders(value, ref):
    c = cc.classify("some.key", value)
    assert c.value_kind == "reference" and c.ref == ref and c.rule == 1
    assert c.record_value is None


def test_rule1_default_is_reclassified():
    c = cc.classify("api.base", "${API_BASE:/api/v1}")
    assert c.default is not None and c.default.value_kind == "path"
    c = cc.classify("x", "${X:Password=fake;Server=s}")
    assert c.secret  # literal default is secret-like


@pytest.mark.parametrize("value,kv", [
    ("@Microsoft.KeyVault(SecretUri=https://my-vault.vault.azure.net/secrets/db-pass/)",
     "my-vault/db-pass"),
    ("@Microsoft.KeyVault(VaultName=my-vault;SecretName=sb-conn)", "my-vault/sb-conn"),
])
def test_rule2_key_vault(value, kv):
    c = cc.classify("Whatever", value)
    assert c.secret and c.kv_ref == kv and c.provided_by == "key-vault" and c.record_value is None


@pytest.mark.parametrize("key", [
    "spring.datasource.password", "DATABASE_PASSWORD", "db-pwd", "clientSecret", "API_KEY",
    "apiKey", "authToken", "jwt.signing.keys", "tls.cert", "certificate.path", "my.pfx",
    "sas", "webhook.signature", "hash.salt", "private.data", "credentials", "AccountKey",
    "SERVICE_BUS_DEALER_DATA_CONNECTION_STRING", "spring.jms.servicebus.connection-string",
    "ConnectionStrings:Default", "connStr", "NEXT_PUBLIC_FIREBASE_API_KEY",
])
def test_rule3_secret_key_names(key):
    c = cc.classify(key, "https://example.invalid/x")
    assert c.secret and c.record_value is None and c.rule == 3


@pytest.mark.parametrize("key", ["keyspace", "monkey", "tokenizer", "keyboard", "turkey.count",
                                 "cassandra.keyspace", "tokenizerModel"])
def test_rule3_near_misses(key):
    c = cc.classify(key, "plain")
    assert not c.secret


@pytest.mark.parametrize("value", [
    "Server=db.example.invalid;Database=x;User ID=fake;Password=fakepass",
    "Endpoint=sb://ns.servicebus.windows.net/;SharedAccessKeyName=n;SharedAccessKey=fakeKey=",
    "DefaultEndpointsProtocol=https;AccountName=acct;AccountKey=ZmFrZQ==",
    "postgres://fakeuser:fakepass@db.example.invalid:5432/app",
    FAKE_JWT,
    "-----BEGIN PRIVATE KEY-----",
    "AKIAABCDEFGHIJKLMNOP",
    "ghp_FAKEtoken1234567890abcdef",
    "github_pat_FAKE1234567890abcdefghij",
    "https://acct.blob.core.windows.net/c?sv=2020&sig=fakesig",
    FAKE_HIGH_ENTROPY,
])
def test_rule4_secret_values(value):
    c = cc.classify("innocent.name", value)
    assert c.secret and c.record_value is None and c.rule == 4


@pytest.mark.parametrize("value", [
    "org.springframework.boot.autoconfigure.security.SecurityAutoConfiguration",
    "eventhub-ns01-dev.servicebus.windows.net:9093",
])
def test_rule4_entropy_ignores_hosts_and_class_names(value):
    assert not cc.classify("spring.autoconfigure.exclude", value).secret


@pytest.mark.parametrize("key,value,kind,recorded", [
    ("NEXT_PUBLIC_API_BASE_URL", "https://api.example.invalid/v1?code=abc#frag", "url",
     "https://api.example.invalid/v1"),
    ("broker", "amqps://bus.example.invalid", "url", "amqps://bus.example.invalid"),
    ("redis.host", "cache.example.invalid:6380", "host", "cache.example.invalid:6380"),
    ("server.servlet.context-path", "/mdp", "path", "/mdp"),
    ("SERVICE_BUS_DEALER_DATA_TOPIC_NAME", "local.mdp.dealer_data", "topic",
     "local.mdp.dealer_data"),
    ("orders.queue", "orders-q", "queue", "orders-q"),
    ("app.subscription", "sub-1", "entity", "sub-1"),
    ("DATABASE_NAME", "masterdata", "db-name", "masterdata"),
])
def test_rule5_allowed_kinds(key, value, kind, recorded):
    c = cc.classify(key, value)
    assert not c.secret and c.value_kind == kind and c.record_value == recorded and c.rule == 5


@pytest.mark.parametrize("key,value", [("logging.level.root", "INFO"), ("server.port", "8080"),
                                       ("feature.enabled", True), ("x.topic", "has space")])
def test_rule6_hidden(key, value):
    c = cc.classify(key, value)
    assert c.value_kind == "hidden" and c.record_value is None and not c.secret


def test_split_words():
    assert cc.split_words("NEXT_PUBLIC_FIREBASE_API_KEY") == ["next", "public", "firebase",
                                                              "api", "key"]
    assert cc.split_words("ConnectionStrings:DefaultConnection") == [
        "connection", "strings", "default", "connection"]
    assert cc.split_words("spring.jms.servicebus.connection-string") [-2:] == ["connection",
                                                                              "string"]
    assert cc.split_words("clientSecretValue__x") == ["client", "secret", "value", "x"]


def test_parse_store_identity_never_returns_the_string():
    v = "Server=tcp:sql.example.invalid,1433;Initial Catalog=jobcard;User ID=u;Password=fakepw"
    sid = cc.parse_store_identity(v)
    assert sid == {"store_type": "mssql", "host": "sql.example.invalid", "database": "jobcard"}
    assert cc.parse_store_identity("jdbc:postgresql://pg.example.invalid:5432/cps?ssl=true") == {
        "store_type": "postgres", "host": "pg.example.invalid", "database": "cps"}
    assert cc.parse_store_identity("mongodb+srv://u:fakepw@cluster0.example.invalid/booking") == {
        "store_type": "mongo", "host": "cluster0.example.invalid", "database": "booking"}
    sb = cc.parse_store_identity("Endpoint=sb://tvsm-dev.servicebus.windows.net/;"
                                 "SharedAccessKeyName=RootManageSharedAccessKey;"
                                 "SharedAccessKey=fakeKey=")
    assert sb["namespace"] == "tvsm-dev" and "fakeKey" not in str(sb)


@pytest.mark.parametrize("path,env", [
    ("src/appsettings.Development.json", "Development"),
    ("src/main/resources/application-uat.properties", "uat"),
    ("application-prod.yml", "prod"), (".env.prod", "prod"), (".env", "default"),
    ("src/environments/environment.prod.ts", "prod"), ("local.settings.json", "local"),
    ("helm/values-dev.yaml", "dev"), ("appsettings.json", "default"),
    ("application.properties", "default"),
])
def test_env_from_filename(path, env):
    assert cc.env_from_filename(path) == env


def test_canonical_key():
    assert cc.canonical_key("booking.base-url") == ("booking.baseurl", False)
    assert cc.canonical_key("booking.baseUrl") == ("booking.baseurl", False)
    assert cc.canonical_key("ServiceBusSettings:TopicName") == ("servicebussettings.topicname",
                                                                False)
    assert cc.canonical_key("Logging__LogLevel__Default") == ("logging.loglevel.default", False)
    assert cc.canonical_key("SERVICE_BUS_TOPIC") == ("service.bus.topic", True)


# redact_line: master-data-platform .env / properties / appsettings style lines (fake values)
@pytest.mark.parametrize("line,secret", [
    ("SERVICE_BUS_DEALER_DATA_CONNECTION_STRING=Endpoint=sb://ns.servicebus.windows.net/;"
     "SharedAccessKeyName=n;SharedAccessKey=fakeSAK123=", "fakeSAK123"),
    ("DATABASE_PASSWORD=fakeDbPass99", "fakeDbPass99"),
    ("export AZURE_B2C_CLIENT_SECRET='fakeClientSecret'", "fakeClientSecret"),
    ('    "DefaultConnection": "Server=s;Database=d;User ID=u;Password=fakePw1"', "fakePw1"),
    ('    "AppDb": "Server=s;Database=d;Trusted_Connection=True"', "Trusted_Connection"),
    ("spring.datasource.password: fakeYamlPw", "fakeYamlPw"),
    ('const apiKey = "fakeApiKeyValue";', "fakeApiKeyValue"),
    ("ENV DB_PASSWORD=fakeDockerPw", "fakeDockerPw"),
    (f"Authorization: Bearer {FAKE_JWT}", FAKE_JWT),
    ("url = postgres://fakeuser:fakepass@db.example.invalid/app", "fakepass"),
    (f'token: "{FAKE_HIGH_ENTROPY}"', FAKE_HIGH_ENTROPY),
])
def test_redact_line_masks(line, secret):
    out = cc.redact_line(line)
    assert secret not in out and "***" in out


def test_redact_line_masks_url_query_values():
    # location-frontend .env style (fake value): APIM subscription key passed as a query param
    out = cc.redact_line("REACT_APP_DEALER_BASE_URL=https://h.example/p?subscription=abc123&x=")
    assert "abc123" not in out and out.endswith("?subscription=***&x=")
    # template holes in code stay readable
    line = "fetch(`https://h.example/p?id=${id}`)"
    assert cc.redact_line(line) == line


def test_redact_line_keeps_safe_values_and_registered_tokens():
    assert cc.redact_line("SERVICE_BUS_DEALER_DATA_TOPIC_NAME=local.mdp.dealer_data") == \
        "SERVICE_BUS_DEALER_DATA_TOPIC_NAME=local.mdp.dealer_data"
    assert cc.redact_line('[HttpGet("fetch/{frameNo}")]') == '[HttpGet("fetch/{frameNo}")]'
    saved = list(SecretFilter._secrets)
    try:
        SecretFilter.register("plainFakeRegistered")
        assert "plainFakeRegistered" not in cc.redact_line("x = plainFakeRegistered")
    finally:
        SecretFilter._secrets[:] = saved

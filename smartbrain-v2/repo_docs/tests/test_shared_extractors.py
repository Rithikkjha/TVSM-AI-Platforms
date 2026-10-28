"""Shared extractors over trimmed reproductions of TVS-CS files (sources cited per fixture).
Every secret value here is fake; tests assert they never reach inventory bytes."""
from __future__ import annotations

import json

from phase2_helpers import make_ledgered_repo
from repo_docs import paths, phase2_extract as p2
from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.shared_config import SharedConfig
from repo_docs.extractors.shared_contracts import SharedContracts
from repo_docs.extractors.shared_infra import SharedInfra
from repo_docs.extractors.shared_manifests import SharedManifests
from repo_docs.extractors.shared_sql import SharedSql, split_statements
from repo_docs.state import StateStore

FAKE_SB = "fakeSharedAccessKey0123456789="
FAKE_DB_PW = "fakeDbPassw0rd"
FAKE_B2C = "fakeB2cClientSecret"

# master-data-platform src/main/resources/application.properties (+ -uat, .env, Dockerfile)
MDP = {
    "pom.xml": "<project><groupId>com.tvsm</groupId><artifactId>mdp</artifactId>"
               "<version>1.0</version></project>\n",
    "src/main/resources/application.properties": (
        "spring.profiles.active=${ACTIVE_ENVIRONMENT}\n"
        "spring.application.name=mdp\n"
        "server.servlet.context-path=/${spring.application.name}\n"
        "spring.datasource.password=${DATABASE_PASSWORD}\n"
        "spring.jms.servicebus.topic.dealerData.name=${SERVICE_BUS_DEALER_DATA_TOPIC_NAME}\n"
        "spring.jms.servicebus.topic.dealerData.connection-string="
        "${SERVICE_BUS_DEALER_DATA_CONNECTION_STRING}\n"
        f"azure.b2c.client.secret={FAKE_B2C}\n"),
    "src/main/resources/application-uat.properties": "server.port=9090\n",
    ".env": (f"DATABASE_PASSWORD={FAKE_DB_PW}\n"
             "SERVICE_BUS_DEALER_DATA_CONNECTION_STRING=Endpoint=sb://mdp-ns.servicebus.windows"
             f".net/;SharedAccessKeyName=root;SharedAccessKey={FAKE_SB}\n"
             "SERVICE_BUS_DEALER_DATA_TOPIC_NAME=local.mdp.dealer_data\n"),
    "Dockerfile": ("FROM maven:3.9.16-amazoncorretto-17 AS build\nRUN mvn package\n"
                   "FROM amazoncorretto:17.0.20\nENV TZ Asia/Kolkata\n"
                   f"ENV DB_PASSWORD={FAKE_DB_PW}\nEXPOSE 8080\n"
                   'ENTRYPOINT ["java", "-jar", "/usr/local/lib/mdp.jar"]\n'),
    # master-data-platform cd-pipeline.yaml (trimmed)
    "cd-pipeline.yaml": ("trigger: none\nparameters:\n  - name: environments\n    type: object\n"
                         "    default:\n      - name: 'dev'\n      - name: 'uat'\n"
                         "variables:\n  - group: mdp-vars\n  - name: serviceName\n    value: mdp\n"
                         "stages:\n  - stage: Deploy\n    jobs:\n      - deployment: D\n"
                         "        environment: mdp-uat\n"),
}


def _run(ex, files, stacks=()):
    ctx = RepoContext.for_test(files, list(stacks))
    return ctx, ex.extract(ctx, None)


def _by_id(res):
    return {i.id: i for i in res.items}


def _assert_no_secret(items, *secrets):
    blob = json.dumps([i.to_dict() for i in items])
    for s in secrets:
        assert s not in blob


def test_shared_config_master_data_platform():
    ctx, res = _run(SharedConfig(), MDP, [("java", ".")])
    items = _by_id(res)
    cp = items["config_key:.:server.servlet.contextpath"].attributes
    assert cp["value_kind"] == "reference" and cp["ref"] == "spring.application.name"
    assert cp["values"] == {"default": "/${spring.application.name}"}
    # placeholder chain resolution through the index: property -> property / env var
    assert ctx.config.resolve_key("server.servlet.context-path").value == "/mdp"
    topic = "spring.jms.servicebus.topic.dealerData.name"
    assert ctx.config.public_values(topic) == {"default": "local.mdp.dealer_data"}
    assert ctx.config.public_values("spring.jms.servicebus.topic.dealerData.connection-string") \
        == {}
    env_topic = items["config_key:.:service.bus.dealer.data.topic.name"].attributes
    assert env_topic["values"] == {"default": "local.mdp.dealer_data"}
    assert env_topic["value_kind"] == "topic" and env_topic["provided_by"] == "env-file"
    conn = items["config_key:.:service.bus.dealer.data.connection.string"].attributes
    assert conn["secret"] and conn["values"] == {}
    b2c = items["config_key:.:azure.b2c.client.secret"]
    assert b2c.attributes["secret"] and FAKE_B2C not in b2c.evidence[0].snippet
    port = items["config_key:.:server.port"].attributes
    assert port["defined_in"] == [{"file": "src/main/resources/application-uat.properties",
                                   "env": "uat"}]
    _assert_no_secret(res.items, FAKE_SB, FAKE_DB_PW, FAKE_B2C)
    assert res.touched[".env"].parse == "full"
    assert res.touched["src/main/resources/application.properties"].parse == "full"


def test_config_resolution_is_cycle_safe():
    ctx, _ = _run(SharedConfig(), {"application.properties": "a=${b}\nb=${a}\nc=${d:x}\n"})
    r = ctx.config.resolve_key("a")
    assert r.value is None and r.unresolved
    assert ctx.config.resolve_key("c").value == "x"


def test_shared_config_appsettings_and_host_json():
    # BS2.0Backend_Integration appsettings.json + appsettings.Development.json;
    # PaymentService host.json (has a // comment)
    files = {
        "appsettings.json": ('{\n  "ServiceBusSettings": {\n    "TopicName": "bs2-topic",\n'
                             '    "ConnectionString": "Endpoint=sb://bs2.servicebus.windows.net/;'
                             f'SharedAccessKeyName=x;SharedAccessKey={FAKE_SB}"\n  }},\n'
                             '  "ConnectionStrings": {"Default": "Server=s;Database=d;'
                             'Trusted_Connection=True"}\n}\n'),
        "appsettings.Development.json": '{"ServiceBusSettings": {"TopicName": "bs2-dev"}}\n',
        "host.json": '{\n    "version": "2.0",\n    // Pipeline test - no functional change\n'
                     '    "logging": {"logLevel": {"default": "Information"}}\n}\n',
        "local.settings.json": '{"Values": {"TopicName": "cpg-juspay"}}\n',
    }
    ctx, res = _run(SharedConfig(), files, [("dotnet", ".")])
    items = _by_id(res)
    t = items["config_key:.:servicebussettings.topicname"].attributes
    assert t["values"] == {"default": "bs2-topic", "Development": "bs2-dev"}
    assert items["config_key:.:connectionstrings.default"].attributes["secret"]
    assert items["config_key:.:servicebussettings.connectionstring"].attributes["secret"]
    assert res.touched["host.json"].parse == "full"
    assert "config_key:.:version" in items
    assert ctx.config.env_defs("TopicName")[0].env == "local"
    _assert_no_secret(res.items, FAKE_SB, "Trusted_Connection")


def test_shared_manifests_pom_modules_parent_props():
    # TVS-CPS-BACKEND root pom.xml: <modules> + spring-boot parent 3.5.x
    pom = """<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.5.3</version>
  </parent>
  <groupId>com.tvsm</groupId>
  <artifactId>tvs-cps-backend</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <properties><lib.version>2.1</lib.version></properties>
  <modules>
    <module>bff-service</module>
    <module>appointment-service</module>
  </modules>
  <dependencies>
    <dependency><groupId>com.acme</groupId><artifactId>lib</artifactId><version>${lib.version}</version></dependency>
    <dependency><groupId>org.springdoc</groupId><artifactId>springdoc-openapi-starter-webmvc-ui</artifactId></dependency>
    <dependency><groupId>org.testng</groupId><artifactId>testng</artifactId><version>${missing}</version><scope>test</scope></dependency>
  </dependencies>
</project>
"""
    mod = ("<project><parent><groupId>com.tvsm</groupId><artifactId>tvs-cps-backend</artifactId>"
           "<version>1.0.0</version></parent><artifactId>bff-service</artifactId>\n"
           "<dependencies><dependency><groupId>com.tvsm</groupId>"
           "<artifactId>appointment-service</artifactId></dependency></dependencies>"
           "<build><plugins><plugin><artifactId>spring-boot-maven-plugin</artifactId></plugin>"
           "</plugins></build></project>\n")
    ctx, res = _run(SharedManifests(), {"pom.xml": pom, "bff-service/pom.xml": mod,
                                        "appointment-service/pom.xml":
                                            "<project><groupId>com.tvsm</groupId>"
                                            "<artifactId>appointment-service</artifactId>"
                                            "</project>\n"},
                    [("java", "."), ("java", "bff-service"), ("java", "appointment-service")])
    items = _by_id(res)
    parent = items["dependency:.:maven:org.springframework.boot:spring-boot-starter-parent"]
    assert parent.attributes["kind"] == "parent" and parent.attributes["version"] == "3.5.3"
    assert parent.evidence[0].line == 3
    assert items["dependency:.:maven:bff-service"].attributes["kind"] == "module"
    lib = items["dependency:.:maven:com.acme:lib"].attributes
    assert lib["version"] == "2.1" and lib["version_from"] == "property:lib.version"
    internal = items["dependency:bff-service:maven:com.tvsm:appointment-service"].attributes
    assert internal["internal"] is True
    art = items["artifact:.:maven:com.tvsm:tvs-cps-backend"].attributes
    assert art["packaging"] == "pom" and art["version"] == "1.0.0"
    assert "api_contract:.:springdoc" in items
    assert items["api_contract:.:springdoc"].attributes["docs_path"] == "/v3/api-docs"
    assert res.touched["pom.xml"].parse == "partial"  # ${missing} unresolved
    assert res.touched["bff-service/pom.xml"].parse == "full"
    assert ctx.hints["boot_repackage"] == {"bff-service/pom.xml"}


def test_shared_manifests_csproj_package_json_toml_gradle():
    # job-card-service src/Jobcard.API/Jobcard.API.csproj PackageReferences
    csproj = ('<Project Sdk="Microsoft.NET.Sdk.Web">\n  <ItemGroup>\n'
              '    <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" '
              'Version="9.0.0" />\n    <PackageReference Include="Swashbuckle.AspNetCore" '
              'Version="6.5.0" />\n    <PackageReference Include="Central.Pkg" />\n'
              '    <ProjectReference Include="..\\Jobcard.Domain\\Jobcard.Domain.csproj" />\n'
              '  </ItemGroup>\n</Project>\n')
    props = ('<Project><ItemGroup><PackageVersion Include="Central.Pkg" Version="1.2.3"/>'
             '</ItemGroup></Project>\n')
    pkg = ('{\n  "name": "@tvs/ui-lib",\n  "version": "1.0.0",\n  "main": "dist/index.js",\n'
           '  "dependencies": {\n    "axios": "^1.6.0",\n    "@react-google-maps/api": "^2.19.3"\n'
           '  },\n  "devDependencies": {"jest": "29"},\n  "workspaces": ["packages/*"]\n}\n')
    toml = ('[versions]\nboot = "3.5.3"\n[libraries]\nboot-web = { module = '
            '"org.springframework.boot:spring-boot-starter-web", version.ref = "boot" }\n')
    gradle = "dependencies {\n  implementation 'com.squareup.okhttp3:okhttp:4.12.0'\n}\n"
    files = {"Directory.Packages.props": props, "src/Api/Api.csproj": csproj,
             "web/package.json": pkg, "gradle/libs.versions.toml": toml, "app/build.gradle": gradle}
    ctx = RepoContext.for_test(files, [("dotnet", "src/Api"), ("node", "web"), ("java", "app")],
                               internal_patterns=["@tvs/*"])
    res = SharedManifests().extract(ctx, None)
    items = _by_id(res)
    ef = items["dependency:src/Api:nuget:Microsoft.EntityFrameworkCore.SqlServer"].attributes
    assert ef["version"] == "9.0.0" and ef["scope"] == "compile"
    assert items["dependency:src/Api:nuget:Central.Pkg"].attributes["version_from"] == "central"
    assert items["dependency:src/Api:nuget:Jobcard.Domain"].attributes["kind"] == \
        "project-reference"
    assert items["api_contract:src/Api:swashbuckle"].attributes["docs_path"] == \
        "/swagger/v1/swagger.json"
    ax = items["dependency:web:npm:axios"]
    assert ax.attributes["scope"] == "runtime" and ax.evidence[0].line == 6
    assert items["dependency:web:npm:jest"].attributes["scope"] == "dev"
    assert items["dependency:web:npm:packages/*"].attributes["kind"] == "module"
    assert items["artifact:web:npm:@tvs/ui-lib"].attributes["version"] == "1.0.0"
    boot = items["dependency:.:gradle:org.springframework.boot:spring-boot-starter-web"]
    assert boot.attributes["version"] == "3.5.3"
    assert items["dependency:app:gradle:com.squareup.okhttp3:okhttp"].confidence == "medium"
    assert res.touched["app/build.gradle"].parse == "partial"
    assert all(res.touched[p].parse == "full" for p in
               ("Directory.Packages.props", "src/Api/Api.csproj", "web/package.json",
                "gradle/libs.versions.toml"))


def test_shared_infra_dockerfile_compose_pipeline_k8s():
    # FormBuilder docker-compose.yml; master-data-platform Dockerfile + cd-pipeline.yaml
    files = dict(MDP)
    files["docker-compose.yml"] = ("version: '3.8'\nservices:\n  app:\n    build:\n"
                                   "      context: .\n    image: formbuilder:latest\n"
                                   "    ports:\n      - '3000:3000'\n    environment:\n"
                                   "      - NODE_ENV=production\n"
                                   f"      - DB_PASSWORD={FAKE_DB_PW}\n")
    files["k8s/deploy.yaml"] = ("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: mdp\n"
                                "  namespace: tvsm\nspec:\n  template:\n    spec:\n"
                                "      containers:\n        - name: c\n          image: mdp:1\n"
                                "          ports:\n            - containerPort: 8080\n"
                                "          env:\n            - name: API_URL\n"
                                "              value: https://api.example.invalid/x\n"
                                "            - name: SB_CONN\n              valueFrom:\n"
                                "                secretKeyRef:\n                  name: sb-secret\n"
                                "                  key: conn\n---\napiVersion: batch/v1\n"
                                "kind: CronJob\nmetadata:\n  name: import\nspec:\n"
                                "  schedule: '0 2 * * *'\n")
    ctx, res = _run(SharedInfra(), files, [("java", ".")])
    items = _by_id(res)
    df = items["infra:.:dockerfile:Dockerfile"].attributes
    assert df["base_images"] == ["maven:3.9.16-amazoncorretto-17", "amazoncorretto:17.0.20"]
    assert df["ports"] == ["8080"]
    assert {e["name"] for e in df["env"]} == {"TZ", "DB_PASSWORD"}
    assert all("value" not in e for e in df["env"] if e["name"] == "DB_PASSWORD")
    svc = items["infra:.:compose-service:app"].attributes
    assert svc["image"] == "formbuilder:latest" and svc["ports"] == ["3000:3000"]
    pipe = items["infra:.:azure-pipeline:cd-pipeline.yaml"].attributes
    assert pipe["variable_groups"] == ["mdp-vars"]
    assert pipe["environments"] == ["dev", "mdp-uat", "uat"]
    assert pipe["variables"] == [{"name": "serviceName", "secret": False}]
    dep = items["infra:.:k8s-deployment:mdp"].attributes
    assert dep["namespace"] == "tvsm" and dep["secret_refs"] == ["sb-secret"]
    assert dep["env"] == [{"name": "API_URL", "from": "k8s",
                           "value": "https://api.example.invalid/x"}]
    job = [i for i in res.items if i.kind == "scheduled_job"][0]
    assert job.attributes["expression"] == "0 2 * * *"
    assert ctx.config.env_defs("API_URL")[0].provided_by == "k8s-configmap"
    assert res.touched["Dockerfile"].parse == "full"
    assert res.touched["docker-compose.yml"].parse == "full"
    _assert_no_secret(res.items, FAKE_DB_PW)


def test_shared_infra_iac_servicebus():
    tf = ('resource "azurerm_servicebus_subscription" "s" {\n  name = "booking-sub"\n'
          '  max_delivery_count = 10\n  dead_lettering_on_message_expiration = true\n}\n')
    ctx, res = _run(SharedInfra(), {"infra/main.tf": tf})
    ent = _by_id(res)["infra:.:terraform:infra/main.tf"].attributes["servicebus_entities"]
    assert ent == [{"name": "booking-sub", "type": "subscription", "max_delivery": 10,
                    "dead_letter": True}]
    assert res.touched["infra/main.tf"].parse == "partial"
    assert ctx.hints["servicebus_entities"][0]["name"] == "booking-sub"


OPENAPI = """openapi: 3.0.1
info:
  title: Booking Service
  version: '1.0'
servers:
  - url: http://uat-ingress.example.invalid
paths:
  /bookings/{bookingId}:
    get:
      operationId: BookingsController_getBooking
      parameters:
        - name: bookingId
          in: path
          required: true
          schema:
            type: string
        - name: clientId
          in: header
          required: true
          schema:
            type: string
      responses:
        '200':
          description: ok
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Booking'
components:
  schemas:
    Booking:
      type: object
      required: [id]
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
          enum: [OPEN, CLOSED]
"""
SWAGGER = ('{\n  "openapi": "3.0.0",\n  "paths": {\n    "/bookings": {\n      "post": {\n'
           '        "requestBody": {"content": {"application/json": {"schema": '
           '{"$ref": "#/components/schemas/CreateBookingRequestDto"}}}},\n'
           '        "responses": {"202": {"description": "created"}}\n      }\n    }\n  },\n'
           '  "info": {"title": "b", "version": "1"}\n}\n')


def test_shared_contracts_openapi_yaml_and_json():
    # booking-crud-services "Booking Service.openapi.yaml" + swagger.json
    files = {"Booking Service.openapi.yaml": OPENAPI, "swagger.json": SWAGGER,
             "config/other.yaml": "a: 1\n"}
    ctx, res = _run(SharedContracts(), files)
    items = _by_id(res)
    get = items["inbound_http:.:GET:/bookings/{}"]
    assert get.source == "contract" and get.evidence[0].line == 9
    a = get.attributes
    assert a["path"] == "/bookings/{bookingId}" and a["handler"] is None
    assert {p["name"]: p["in"] for p in a["params"]} == {"bookingId": "path", "clientId": "header"}
    assert a["responses"] == [{"status": 200, "schema": "Booking", "when": "ok",
                               "from": "contract"}]
    assert items["inbound_http:.:POST:/bookings"].attributes["request"] == \
        "CreateBookingRequestDto"
    sch = items["schema:.:Booking"].attributes
    assert [(f["name"], f["type"], f["required"]) for f in sch["fields"]] == [
        ("id", "uuid", True), ("status", "enum[OPEN,CLOSED]", False)]
    c = items["api_contract:.:Booking Service.openapi.yaml"].attributes
    assert c["format"] == "openapi-3" and c["operations"] == 1 and c["title"] == "Booking Service"
    assert res.touched["Booking Service.openapi.yaml"].parse == "full"
    assert res.touched["swagger.json"].parse == "full"
    assert "config/other.yaml" not in res.touched


def test_shared_contracts_postman_proto():
    pm = ('{\n  "info": {"_postman_id": "x", "name": "Booking tests"},\n  "item": [\n'
          '    {"name": "get", "request": {"method": "GET", "url": {"raw": '
          '"{{baseUrl}}/api/bookings/123?x=1"}}}\n  ]\n}\n')
    proto = ('syntax = "proto3";\npackage booking;\nservice BookingService {\n'
             '  rpc GetBooking (GetReq) returns (Booking);\n}\n')
    ctx, res = _run(SharedContracts(), {"tests/b.postman_collection.json": pm,
                                        "proto/b.proto": proto})
    out = [i for i in res.items if i.kind == "outbound_http"][0]
    assert out.attributes["role"] == "tests_target"
    assert out.attributes["path_template"] == "/api/bookings/123"
    assert out.attributes["query_params"] == ["x"]
    g = _by_id(res)["inbound_http:.:POST:/booking.BookingService/GetBooking"]
    assert g.attributes["framework"] == "grpc" and g.attributes["request"] == "GetReq"


def test_shared_sql_flyway_ddl():
    # TVS-CPS-DB-MIGRATION src/main/resources/db/migration/cps-backend/V100__increase_column_length.sql
    v100 = ("ALTER TABLE appointment\n    ALTER COLUMN remark TYPE VARCHAR(500),\n"
            "    ALTER COLUMN reason TYPE VARCHAR(500);\n"
            "ALTER TABLE claim_catalog_mapping\n    ALTER COLUMN remark TYPE VARCHAR(500);\n")
    v1 = ("-- comment; with semicolon\nCREATE TABLE IF NOT EXISTS cps.appointment (\n"
          "  id BIGSERIAL PRIMARY KEY,\n  remark VARCHAR(100) NOT NULL,\n  reason TEXT,\n"
          "  CONSTRAINT x UNIQUE (remark)\n);\n"
          "CREATE OR REPLACE FUNCTION f() RETURNS trigger AS $$\nBEGIN\n  x := 'a;b';\n"
          "  RETURN NEW;\nEND;\n$$ LANGUAGE plpgsql;\nINSERT INTO cps.appointment (remark) "
          "VALUES ('x');\n")
    base = "src/main/resources/db/migration/cps-backend/"
    ctx, res = _run(SharedSql(), {base + "V100__increase_column_length.sql": v100,
                                  base + "V1__init.sql": v1, base + "weird.sql": "FROBNICATE;\n"})
    it = [i for i in res.items if i.kind == "data_access"][0]
    a = it.attributes
    assert a["store_type"] == "postgres"
    tables = {(t["schema"], t["name"]): t for t in a["tables_ddl"]}
    cols = {c["name"]: c for c in tables[("cps", "appointment")]["columns"]}
    assert cols["remark"]["type"] == "VARCHAR(100)" and cols["remark"]["nullable"] is False
    assert {c["name"]: c["type"] for c in tables[(None, "appointment")]["columns"]} == {
        "reason": "VARCHAR(500)", "remark": "VARCHAR(500)"}
    assert a["routines"][0]["name"] == "f" and a["routines"][0]["language"] == "plpgsql"
    assert a["entities"][0]["operation"] == "write"
    assert res.touched[base + "V100__increase_column_length.sql"].parse == "full"
    assert res.touched[base + "V1__init.sql"].parse == "full"
    assert res.touched[base + "weird.sql"].parse == "partial"
    assert len(ctx.hints["flyway_files"]) == 2
    stmts = split_statements(v1)
    assert stmts[0][1] == 2 and "$$" in stmts[1][0] and "'a;b'" in stmts[1][0]


def test_structured_fixture_files_end_extracted_and_secrets_absent(root, org_cfg):
    store = StateStore()
    files = dict(MDP)
    files["Booking Service.openapi.yaml"] = OPENAPI
    files["db/migration/V100__x.sql"] = "ALTER TABLE a ALTER COLUMN b TYPE TEXT;\n"
    files["package.json"] = '{"name": "x", "private": true, "dependencies": {"axios": "1"}}\n'
    files["appsettings.json"] = '{"A": {"TopicName": "t"}}\n'
    files["src/main/java/App.java"] = "class App {}\n"
    make_ledgered_repo(root, org_cfg, store, "alpha", files)
    assert p2.extract_one(org_cfg, store, "alpha") == "done"
    led = {f["path"]: f for f in paths.read_json(paths.runs_dir("TEST-ORG", "alpha") /
                                                 "ledger.json")["files"]}
    for p in ("src/main/resources/application.properties", "appsettings.json", "pom.xml",
              "package.json", "Booking Service.openapi.yaml", "Dockerfile",
              "db/migration/V100__x.sql", ".env", "cd-pipeline.yaml"):
        assert led[p]["status"] == "extracted", p
    # source files are opened by the stack extractor (java.spring since FEAT-003)
    assert [x["id"] for x in led["src/main/java/App.java"]["extractors"]] == ["java.spring"]
    for name in ("inventory.json", "ledger.json", "meta.json"):
        data = (paths.runs_dir("TEST-ORG", "alpha") / name).read_text()
        for s in (FAKE_SB, FAKE_DB_PW, FAKE_B2C):
            assert s not in data, (name, s)
    st = paths.state_path().read_text()
    assert all(s not in st for s in (FAKE_SB, FAKE_DB_PW, FAKE_B2C))


def test_external_systems_match(root):
    from repo_docs import external_systems as es
    reg = paths.external_systems_path()
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text("schema_version: 1\nsystems:\n  - name: google-maps\n    category: maps\n"
                   "    hosts: ['maps.googleapis.com']\n    packages: ['@react-google-maps/*']\n")
    systems, h, data = es.load_registry()
    assert systems[0]["name"] == "google-maps" and len(h) == 40
    files = {"package.json": '{"dependencies": {"@react-google-maps/api": "2"}}\n',
             ".env.dev": "REACT_APP_GOOGLE_MAP_API_BASE_URL=https://maps.googleapis.com/maps/api\n"}
    ctx = RepoContext.for_test(files, [("react", ".")], registry=systems)
    items = SharedConfig().extract(ctx, None).items + SharedManifests().extract(ctx, None).items
    ext = es.match(ctx, items)
    assert [e.id for e in ext] == ["external_system:.:google-maps"]
    a = ext[0].attributes
    assert a["category"] == "maps" and a["matched_by"] in ("host", "package")
    assert len(ext[0].evidence) == 2

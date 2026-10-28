"""repo_type rules over small fixtures modelled on TVS-CS repos (sources cited per test)."""
from __future__ import annotations

from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.registry import SHARED
from repo_docs.phase2_extract import merge_items
from repo_docs.repo_type import classify_repo, template_type


def _classify(files, stacks, repo="fixture"):
    ctx = RepoContext.for_test(files, stacks, repo=repo)
    items = []
    for cls in SHARED:
        items += cls().extract(ctx, None).items
    return classify_repo(ctx, merge_items(items))


def test_db_migration():
    # TVS-CPS-DB-MIGRATION: a few java runner classes + many Flyway files
    files = {"pom.xml": "<project><groupId>g</groupId><artifactId>m</artifactId></project>\n",
             "src/main/java/MigrationRunner.java":
                 "class MigrationRunner { public static void main(String[] a) {} }\n"}
    for i in range(3):
        files[f"src/main/resources/db/migration/V10{i}__x.sql"] = "ALTER TABLE a ADD COLUMN b INT;\n"
    rt = _classify(files, [("java", ".")])
    assert rt["value"] == "db-migration" and rt["template_type"] is None
    assert rt["evidence"] and rt["rules_fired"][0].startswith("sql_migrations=")


def test_test_suite():
    # Core-Commerce-Platform-API-Service-Testng: testng + rest-assured, no app entrypoint
    pom = ("<project><groupId>g</groupId><artifactId>t</artifactId><dependencies>\n"
           "<dependency><groupId>org.testng</groupId><artifactId>testng</artifactId></dependency>\n"
           "</dependencies></project>\n")
    rt = _classify({"pom.xml": pom, "src/main/java/Base.java": "class Base {}\n"},
                   [("java", ".")])
    assert rt["value"] == "test-suite"


def test_library_vs_boot_service():
    # TVS-CPS-BE-BASE-FRAMEWORK: jar modules without boot repackage; archetype Application.java
    files = {"core/pom.xml": "<project><groupId>com.tvsm</groupId><artifactId>tvsm-be-core"
                             "</artifactId><packaging>jar</packaging></project>\n",
             "archetype/src/main/resources/archetype-resources/src/main/java/Application.java":
                 "@SpringBootApplication\nclass Application {}\n",
             "core/src/main/java/Util.java": "class Util {}\n"}
    rt = _classify(files, [("java", "core")])
    assert rt["value"] == "library" and rt["template_type"] == "library"
    files["core/src/main/java/App.java"] = "@SpringBootApplication\nclass App {}\n"
    assert _classify(files, [("java", "core")])["value"] != "library"


def test_function_app():
    # PaymentService: host.json + Functions worker package; Catalog-Scheduler: @azure/functions
    cs = ('<Project><ItemGroup><PackageReference Include="Microsoft.Azure.Functions.Worker" '
          'Version="1.0" /></ItemGroup></Project>\n')
    rt = _classify({"host.json": '{"version": "2.0"}\n', "PaymentService.csproj": cs,
                    "Functions/JusPayWebhooks.cs": "class J {}\n"}, [("dotnet", ".")])
    assert rt["value"] == "function-app" and rt["template_type"] == "function"
    pkg = '{"name": "catalog-scheduler", "main": "src/functions/*.js", ' \
          '"dependencies": {"@azure/functions": "4"}}\n'
    rt = _classify({"host.json": "{}\n", "package.json": pkg,
                    "src/functions/job.js": "module.exports = 1;\n"}, [("node", ".")])
    assert rt["value"] == "function-app"


def test_frontend_and_portal_suffix():
    # TVS-CPS-PORTAL (nextjs), location-frontend (react)
    pkg = '{"name": "portal", "private": true, "dependencies": {"next": "15"}}\n'
    rt = _classify({"package.json": pkg, "src/app/page.tsx": "export default 1;\n"},
                   [("nextjs", "."), ("node", ".")], repo="TVS-CPS-PORTAL")
    assert rt["value"] == "frontend" and rt["template_type"] == "portal"
    assert rt["subprojects"] == {".": "frontend"}


def test_service_from_contract_inbound_and_bff_suffix():
    spec = ("openapi: 3.0.1\ninfo: {title: t, version: '1'}\npaths:\n  /x:\n    get:\n"
            "      responses: {'200': {description: ok}}\n")
    rt = _classify({"openapi.yaml": spec, "src/main.ts": "x\n"}, [("node", ".")],
                   repo="Price-Microservice-Backend-for-Frontend-Layer")
    assert rt["value"] == "service" and rt["rules_fired"] == ["inbound_http>0"]
    assert rt["template_type"] == "bff"


def test_unknown_and_mapping():
    assert _classify({"README.md": "# r\n"}, [])["value"] == "unknown"
    assert template_type("scheduler", "x") == "worker"
    assert template_type("mobile", "x") == "mobile-app"
    assert template_type("test-suite", "x") is None

from __future__ import annotations

import pytest

from repo_docs.classify import classify, status_for

M = 1_000_000
F = "100644"


@pytest.mark.parametrize("path,mode,size,head,cls,lang", [
    ("sub", "160000", None, b"", "submodule", "unknown"),
    ("link.js", "120000", 10, b"", "symlink", "javascript"),
    ("web/node_modules/x/index.js", F, 10, b"x", "vendor", "javascript"),
    ("vendor/lib.php", F, 10, b"x", "vendor", "php"),
    ("ios/Pods/A/a.m", F, 10, b"x", "vendor", "objc"),
    ("packages/Newtonsoft.Json.13.0.1/lib/a.xml", F, 10, b"x", "vendor", "xml"),
    ("src/Web/wwwroot/lib/jquery/jquery.js", F, 10, b"x", "vendor", "javascript"),
    ("packages/core/src/index.ts", F, 10, b"x", "source", "typescript"),
    ("src/Api/bin/Debug/net6.0/Api.dll", F, 10, b"x", "generated", "unknown"),
    ("src/Api/obj/project.assets.json", F, 10, b"{}", "generated", "json"),
    ("dist/main.js", F, 10, b"x", "generated", "javascript"),
    ("src/Data/Migrations/20200101_Init.Designer.cs", F, 10, b"x", "generated", "csharp"),
    ("src/Data/Migrations/AppDbContextModelSnapshot.cs", F, 10, b"x", "generated", "csharp"),
    ("bin/www", F, 10, b"x", "other", "unknown"),
    ("package-lock.json", F, 10, b"{}", "lockfile", "json"),
    ("ios/Podfile.lock", F, 10, b"x", "lockfile", "unknown"),
    ("src/app.min.js", F, 10, b"x", "minified", "javascript"),
    ("src/app.js.map", F, 10, b"x", "minified", "unknown"),
    ("img/logo.png", F, 10, b"\x89PNG", "binary", "unknown"),
    ("data/blob.xyz", F, 10, b"ab\x00cd", "binary", "unknown"),
    ("src/assets/icon.svg", F, 10, b"<svg", "asset", "svg"),
    ("src/assets/fonts/readme.woff3", F, 10, b"x", "asset", "unknown"),
    ("src/big.cs", F, M + 1, b"x", "large", "csharp"),
    ("docs/openapi.yaml", F, 10, b"openapi: 3", "api_contract", "yaml"),
    ("swagger.json", F, 10, b"{}", "api_contract", "json"),
    ("proto/booking.proto", F, 10, b"x", "api_contract", "proto"),
    ("api/My.postman_collection.json", F, 10, b"{}", "api_contract", "json"),
    ("Dockerfile", F, 10, b"FROM x", "infra", "dockerfile"),
    ("Dockerfile.prod", F, 10, b"FROM x", "infra", "dockerfile"),
    ("docker-compose.yml", F, 10, b"x", "infra", "yaml"),
    (".github/workflows/ci.yml", F, 10, b"on: push", "infra", "yaml"),
    ("azure-pipelines.yml", F, 10, b"x", "infra", "yaml"),
    ("k8s/deploy.yaml", F, 10, b"x", "infra", "yaml"),
    ("svc.yaml", F, 10, b"apiVersion: v1\nkind: Service\n", "infra", "yaml"),
    ("infra/main.bicep", F, 10, b"x", "infra", "bicep"),
    ("main.tf", F, 10, b"x", "infra", "hcl"),
    ("helm/chart/values.yaml", F, 10, b"x", "infra", "yaml"),
    ("Foo.csproj", F, 10, b"<Project", "build_manifest", "xml"),
    ("Foo.sln", F, 10, b"x", "build_manifest", "sln"),
    ("pom.xml", F, 10, b"<project", "build_manifest", "xml"),
    ("web/package.json", F, 10, b"{}", "build_manifest", "json"),
    ("requirements-dev.txt", F, 10, b"x", "build_manifest", "text"),
    ("tsconfig.app.json", F, 10, b"{}", "build_manifest", "json"),
    ("src/test/java/a/FooTest.java", F, 10, b"x", "test", "java"),
    ("src/app/foo.spec.ts", F, 10, b"x", "test", "typescript"),
    ("Api.Tests/FooTests.cs", F, 10, b"x", "test", "csharp"),
    ("tests/test_x.py", F, 10, b"x", "test", "python"),
    ("README.md", F, 10, b"# x", "docs", "markdown"),
    ("docs/guide.rst", F, 10, b"x", "docs", "rst"),
    ("LICENSE", F, 10, b"x", "docs", "unknown"),
    ("appsettings.Production.json", F, 10, b"{}", "config", "json"),
    ("web.config", F, 10, b"<x", "config", "xml"),
    ("src/main/resources/application-dev.yml", F, 10, b"x", "config", "yaml"),
    (".env", F, 10, b"A=1", "config", "dotenv"),
    ("src/environments/environment.prod.ts", F, 10, b"x", "config", "typescript"),
    ("Controllers/X.cs", F, 10, b"x", "source", "csharp"),
    ("src/main/java/a/App.java", F, 10, b"x", "source", "java"),
    ("lib/main.dart", F, 10, b"x", "source", "dart"),
    ("db/schema.sql", F, 10, b"x", "source", "sql"),
    ("Views/Home/Index.cshtml", F, 10, b"x", "source", "razor"),
    ("weird.qqq", F, 10, b"x", "other", "unknown"),
])
def test_classify_table(path, mode, size, head, cls, lang):
    assert classify(path, mode, size, head, M) == (cls, lang)


def test_status_mapping():
    for c in ("source", "config", "infra", "api_contract", "docs", "test", "build_manifest",
              "other"):
        assert status_for(c) == "pending"
    for c in ("vendor", "generated", "binary", "lockfile", "minified", "asset", "large",
              "symlink", "submodule"):
        assert status_for(c) == f"skipped:{c}"

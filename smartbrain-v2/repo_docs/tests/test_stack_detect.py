from __future__ import annotations

import json

from repo_docs.stack_detect import detect_stacks, stack_ids


def _detect(files: dict[str, str]):
    return detect_stacks(list(files), lambda p: files.get(p))


def _pairs(hits):
    return {(h.stack, h.subproject) for h in hits}


def test_dotnet_sln_and_csproj():
    hits = _detect({"X.sln": "", "src/Api/Api.csproj": "", "src/Core/Core.csproj": ""})
    assert _pairs(hits) == {("dotnet", "src/Api"), ("dotnet", "src/Core")}
    assert _pairs(_detect({"Legacy.sln": ""})) == {("dotnet", ".")}


def test_java_and_android():
    assert _pairs(_detect({"pom.xml": ""})) == {("java", ".")}
    hits = _detect({"app/build.gradle": "apply plugin: 'com.android.application'",
                    "app/src/main/AndroidManifest.xml": ""})
    assert _pairs(hits) == {("java", "app"), ("android", "app")}


def test_node_frameworks():
    def pkg(deps):
        return json.dumps({"dependencies": deps})
    cases = {
        "angular": {"@angular/core": "17"}, "nextjs": {"next": "14", "react": "18"},
        "react": {"react": "18"}, "react-native": {"react-native": "0.7", "react": "18"},
        "nest": {"@nestjs/core": "10"}, "express": {"express": "4"}, "vue": {"vue": "3"},
    }
    for stack, deps in cases.items():
        ids = stack_ids(_detect({"package.json": pkg(deps)}))
        assert stack in ids and "node" in ids, stack
    ids = stack_ids(_detect({"package.json": pkg({"next": "14", "react": "18"})}))
    assert "react" not in ids
    assert "angular" in stack_ids(_detect({"package.json": "{}", "angular.json": "{}"}))


def test_monorepo_three_subprojects():
    hits = _detect({
        "api/Api.csproj": "",
        "web/package.json": json.dumps({"dependencies": {"@angular/core": "16"}}),
        "web/angular.json": "{}",
        "mobile/pubspec.yaml": "name: app\ndependencies:\n  flutter:\n    sdk: flutter\n",
    })
    assert {("dotnet", "api"), ("angular", "web"), ("node", "web"), ("dart", "mobile"),
            ("flutter", "mobile")} <= _pairs(hits)


def test_ignores_vendor_package_json():
    assert _detect({"node_modules/x/package.json": "{}"}) == []


def test_ios_python_php_empty():
    assert ("ios", ".") in _pairs(_detect({"App.xcodeproj/project.pbxproj": ""}))
    assert ("ios", "ios") in _pairs(_detect({"ios/Podfile": ""}))
    assert _pairs(_detect({"pyproject.toml": ""})) == {("python", ".")}
    assert _pairs(_detect({"composer.json": "{}"})) == {("php", ".")}
    assert _detect({}) == []
    assert stack_ids([]) == []

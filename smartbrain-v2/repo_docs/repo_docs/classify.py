"""Phase-1 file classification. ``classify()`` is pure: ordered rules, first match wins."""

from __future__ import annotations

import fnmatch
import posixpath
import re

PENDING_CLASSES = (
    "source", "config", "infra", "api_contract", "docs", "test", "build_manifest", "other",
)
SKIP_CLASSES = (
    "vendor", "generated", "binary", "lockfile", "minified", "asset", "large", "symlink",
    "submodule",
)
CLASSES = PENDING_CLASSES + SKIP_CLASSES

VENDOR_DIRS = {"node_modules", "vendor", "bower_components", "Pods", ".git",
               "jspm_packages", ".yarn", "Carthage", "third_party", "thirdparty"}
# NuGet restore folder: packages/<Id>.<version>/...  (plain packages/ = monorepo workspaces, kept)
_NUGET_PKG = re.compile(r"(^|/)packages/[^/]+?\.\d+(\.\d+)+[^/]*/")
# .NET build output: bin/Debug|Release/... (plain bin/ e.g. node bin/www is kept)
_DOTNET_BIN = re.compile(r"(^|/)bin/(Debug|Release|x64|x86)/")
GENERATED_DIRS = {"obj", "dist", "build", "target", "out", ".next", "coverage",
                  "generated", ".angular", ".nuxt", ".dart_tool", ".gradle", "__pycache__",
                  ".terraform", "DerivedData"}
GENERATED_GLOBS = ("*.g.cs", "*.g.i.cs", "*.Designer.cs", "*.designer.cs", "*.pb.go", "*_pb2.py",
                   "*_pb2_grpc.py", "*.generated.cs", "*.g.dart", "*.freezed.dart",
                   "*ModelSnapshot.cs")
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "packages.lock.json",
             "Podfile.lock", "pubspec.lock", "composer.lock", "poetry.lock", "Pipfile.lock",
             "gradle.lockfile", "Cargo.lock", "go.sum", "npm-shrinkwrap.json", "bun.lockb",
             "Gemfile.lock", "Package.resolved", "uv.lock"}
MINIFIED_GLOBS = ("*.min.js", "*.min.css", "*.map", "*.min.mjs", "*-min.js", "*.bundle.js")
BINARY_EXT = {"png", "jpg", "jpeg", "gif", "ico", "webp", "bmp", "tif", "tiff", "pdf", "zip",
              "gz", "tgz", "tar", "rar", "7z", "jar", "war", "ear", "dll", "exe", "so", "dylib",
              "class", "woff", "woff2", "ttf", "eot", "otf", "mp4", "mp3", "wav", "mov", "avi",
              "keystore", "jks", "p12", "pfx", "apk", "ipa", "aar", "nupkg", "snk", "pdb",
              "xlsx", "xls", "docx", "doc", "pptx", "ppt", "psd", "ai", "sketch", "heic",
              "db", "sqlite", "bin", "dat", "pyc", "o", "a", "lib", "cer", "der", "crt"}
ASSET_DIRS = ("assets", "static", "public", "wwwroot", "images", "img", "fonts", "icons")
CODE_EXT = {"cs", "java", "kt", "kts", "ts", "tsx", "js", "jsx", "mjs", "cjs", "py", "dart",
            "swift", "m", "mm", "h", "php", "go", "rb", "rs", "sql", "sh", "bash", "ps1",
            "psm1", "bat", "cmd", "html", "htm", "cshtml", "razor", "vue", "scss", "sass",
            "css", "less", "xaml", "gradle", "groovy", "scala", "c", "cpp", "hpp", "vb", "fs",
            "aspx", "ascx", "asax", "master", "ashx", "asmx", "svc", "jsp", "ejs", "hbs",
            "pug", "twig", "plsql", "pls", "pks", "pkb", "r", "lua", "pl"}
LANG_BY_EXT = {
    "cs": "csharp", "java": "java", "kt": "kotlin", "kts": "kotlin", "ts": "typescript",
    "tsx": "typescript", "js": "javascript", "jsx": "javascript", "mjs": "javascript",
    "cjs": "javascript", "py": "python", "dart": "dart", "swift": "swift", "m": "objc",
    "mm": "objc", "h": "c", "php": "php", "go": "go", "rb": "ruby", "rs": "rust", "sql": "sql",
    "plsql": "sql", "pls": "sql", "pks": "sql", "pkb": "sql",
    "sh": "shell", "bash": "shell", "ps1": "powershell", "psm1": "powershell", "bat": "batch",
    "cmd": "batch", "html": "html", "htm": "html", "cshtml": "razor", "razor": "razor",
    "vue": "vue", "scss": "scss", "sass": "scss", "css": "css", "less": "less", "xaml": "xaml",
    "gradle": "groovy", "groovy": "groovy", "scala": "scala", "c": "c", "cpp": "cpp",
    "hpp": "cpp", "vb": "vbnet", "fs": "fsharp", "aspx": "aspnet", "ascx": "aspnet",
    "asax": "aspnet", "master": "aspnet", "ashx": "aspnet", "asmx": "aspnet", "svc": "aspnet",
    "jsp": "jsp", "yaml": "yaml", "yml": "yaml", "json": "json", "xml": "xml",
    "csproj": "xml", "fsproj": "xml", "vbproj": "xml", "props": "xml", "targets": "xml",
    "config": "xml", "plist": "xml", "wsdl": "xml", "xsd": "xml", "resx": "xml",
    "md": "markdown", "rst": "rst", "adoc": "asciidoc", "txt": "text", "tf": "hcl",
    "tfvars": "hcl", "hcl": "hcl", "bicep": "bicep", "proto": "proto", "graphql": "graphql",
    "gql": "graphql", "properties": "properties", "ini": "ini", "toml": "toml", "conf": "conf",
    "env": "dotenv", "svg": "svg", "sln": "sln", "ejs": "html", "hbs": "html", "pug": "html",
    "raml": "raml", "r": "r", "lua": "lua", "pl": "perl", "csv": "csv",
}
LANG_BY_NAME = {"Dockerfile": "dockerfile", "Jenkinsfile": "groovy", "Makefile": "make",
                "Podfile": "ruby", "Gemfile": "ruby", "Procfile": "procfile"}

BUILD_MANIFEST_NAMES = {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
                        "settings.gradle.kts", "package.json", "pubspec.yaml", "Podfile",
                        "Package.swift", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
                        "composer.json", "Directory.Build.props", "Directory.Build.targets",
                        "Directory.Packages.props", "nuget.config", "NuGet.Config",
                        "NuGet.config", "global.json", "gradle.properties", "angular.json",
                        "go.mod", "Cargo.toml", "Gemfile", "Makefile", "packages.config",
                        "lerna.json", "nx.json", "workspace.json", "turbo.json",
                        "pnpm-workspace.yaml", "gradle-wrapper.properties", "mvnw",
                        "gradlew", "mvnw.cmd", "gradlew.bat", "webpack.config.js",
                        "vite.config.ts", "vite.config.js", "next.config.js",
                        "next.config.mjs", "next.config.ts", "babel.config.js",
                        ".babelrc", "metro.config.js", "proxy.conf.json", "karma.conf.js",
                        "jest.config.js", "jest.config.ts", "dotnet-tools.json"}
BUILD_MANIFEST_GLOBS = ("*.csproj", "*.sln", "*.fsproj", "*.vbproj", "*.sqlproj",
                        "requirements*.txt", "tsconfig*.json", "*.nuspec", "*.podspec")
API_CONTRACT_GLOBS = ("openapi*.json", "openapi*.yaml", "openapi*.yml", "swagger*.json",
                      "swagger*.yaml", "swagger*.yml", "*.proto", "*.graphql", "*.gql",
                      "*.wsdl", "*.postman_collection.json", "*postman_collection*.json",
                      "*.raml", "asyncapi*.json", "asyncapi*.yaml", "asyncapi*.yml",
                      "*.openapi.json", "*.openapi.yaml", "*.swagger.json", "*.http")
INFRA_NAME_GLOBS = ("Dockerfile*", "*.Dockerfile", "*.dockerfile", "docker-compose*.yml",
                    "docker-compose*.yaml", "compose*.yml", "compose*.yaml", ".dockerignore",
                    "*.tf", "*.tfvars", "*.bicep", "*.bicepparam", "azure-pipelines*.yml",
                    "azure-pipelines*.yaml", "Jenkinsfile*", ".gitlab-ci.yml",
                    "bitbucket-pipelines.yml", "Chart.yaml", "nginx*.conf", "Procfile",
                    "buildspec*.yml", "buildspec*.yaml", "appspec.yml", "cloudbuild*.yaml",
                    "skaffold*.yaml", "kustomization.yaml", "serverless*.yml", "*.azcli",
                    "template.yaml", "app.yaml", "vercel.json", "netlify.toml",
                    "firebase.json", "web.config.transform")
INFRA_DIRS = {"helm", "charts", "k8s", "kubernetes", "manifests", "deploy", "deployment",
              "deployments", ".azure", "pipelines", ".pipelines", "terraform", "infra",
              "infrastructure", "bicep", "arm", ".circleci", "ci", ".devops", "devops"}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "e2e", "integration-tests",
             "testing", "UnitTests", "IntegrationTests", "androidTest", "cypress"}
TEST_NAME_GLOBS = ("*.spec.*", "*.test.*", "*Tests.cs", "*Test.cs", "*Test.java",
                   "*Tests.java", "*IT.java", "*_test.py", "test_*.py", "*_test.dart",
                   "*Test.kt", "*Tests.swift", "*_test.go", "*.Tests.csproj")
DOC_EXT = {"md", "rst", "adoc", "txt", "markdown"}
DOC_NAMES = ("README*", "CHANGELOG*", "LICENSE*", "CONTRIBUTING*", "NOTICE*", "AUTHORS*",
             "CODEOWNERS", "SECURITY*", "HISTORY*")
CONFIG_NAME_GLOBS = ("appsettings*.json", "web.config", "Web.config", "app.config",
                     "App.config", "*.properties", "application*.yml", "application*.yaml",
                     "bootstrap*.yml", "bootstrap*.yaml", ".env*", "*.env", "*.ini",
                     "*.toml", "*.conf", "*.cfg", "*.xml", "host.json", "local.settings.json",
                     "*.plist", "environment*.ts", ".eslintrc*", ".editorconfig",
                     ".prettierrc*", ".gitignore", ".gitattributes", ".npmrc", ".nvmrc",
                     ".browserslistrc", "launchSettings.json", "*.config", "*.yml", "*.yaml",
                     "*.json", "*.json5", ".htaccess", "*.settings", "*.runsettings",
                     "*.ruleset", ".stylelintrc*", "*.xcconfig", "*.entitlements",
                     "*.pubxml", "*.resx", "*.props", "*.targets", "*.xsd", "*.jsonc",
                     ".flutter-plugins*", ".metadata", ".prettierignore", ".eslintignore",
                     ".dockerignore", ".gcloudignore", "*.iml", ".tool-versions")
CONFIG_DIRS = {"config", "configs", "conf", "settings", "environments", "properties"}
K8S_HINT = (b"apiVersion:", b"kind:")


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name.lstrip(".") else ""


def _any(name: str, globs) -> bool:
    return any(fnmatch.fnmatchcase(name, g) for g in globs)


def language_for(path: str) -> str:
    name = posixpath.basename(path)
    if name in LANG_BY_NAME:
        return LANG_BY_NAME[name]
    if name.startswith("Dockerfile") or name.endswith(".Dockerfile"):
        return "dockerfile"
    if name.startswith(".env"):
        return "dotenv"
    return LANG_BY_EXT.get(_ext(name), "unknown")


def status_for(cls: str) -> str:
    return "pending" if cls in PENDING_CLASSES else f"skipped:{cls}"


def classify(
    path: str, mode: str, size: int | None, head: bytes | None, max_file_bytes: int
) -> tuple[str, str]:
    """Return (class, language) for one tracked file."""
    lang = language_for(path)
    name = posixpath.basename(path)
    dirs = path.split("/")[:-1]
    dirset = set(dirs)
    lower_dirs = {d.lower() for d in dirs}
    ext = _ext(name)
    head = head or b""

    if mode == "160000":
        return "submodule", "unknown"
    if mode == "120000":
        return "symlink", lang
    if dirset & VENDOR_DIRS or _NUGET_PKG.search(path) or "wwwroot/lib/" in path:
        return "vendor", lang
    if dirset & GENERATED_DIRS or _any(name, GENERATED_GLOBS) or _DOTNET_BIN.search(path):
        return "generated", lang
    if "Migrations" in dirset and name.endswith(".Designer.cs"):
        return "generated", lang
    if name in LOCKFILES:
        return "lockfile", lang
    if _any(name, MINIFIED_GLOBS):
        return "minified", lang
    if ext in BINARY_EXT or b"\x00" in head:
        return "binary", lang
    in_asset_dir = bool(lower_dirs & set(ASSET_DIRS)) or "wwwroot/lib" in path
    if ext == "svg" or (in_asset_dir and ext not in CODE_EXT and not _config_like(name, ext)):
        return "asset", lang
    if size is not None and size > max_file_bytes:
        return "large", lang
    if _any(name, API_CONTRACT_GLOBS):
        return "api_contract", lang
    if _is_infra(path, name, ext, dirs, lower_dirs, head):
        return "infra", lang
    if name in BUILD_MANIFEST_NAMES or _any(name, BUILD_MANIFEST_GLOBS):
        return "build_manifest", lang
    if _is_test(path, name, dirset):
        return "test", lang
    if ext in DOC_EXT or _any(name, DOC_NAMES) or ("docs" in lower_dirs and ext in DOC_EXT):
        return "docs", lang
    if _any(name, CONFIG_NAME_GLOBS) or (lower_dirs & CONFIG_DIRS and ext not in CODE_EXT):
        return "config", lang
    if ext in CODE_EXT:
        return "source", lang
    return "other", lang


def _config_like(name: str, ext: str) -> bool:
    return ext in {"json", "yml", "yaml", "xml", "config", "toml", "ini", "properties", "txt",
                   "md", "webmanifest"} or name.startswith(".")


def _is_infra(path, name, ext, dirs, lower_dirs, head) -> bool:
    if _any(name, INFRA_NAME_GLOBS):
        return True
    if path.startswith(".github/workflows/") or path.startswith(".github/actions/"):
        return True
    if ext in ("yml", "yaml"):
        if lower_dirs & INFRA_DIRS:
            return True
        if name.startswith("values") and ("helm" in lower_dirs or "charts" in lower_dirs):
            return True
        if all(h in head for h in K8S_HINT):
            return True
    if lower_dirs & {"helm", "charts", "terraform"} and ext in ("tpl", "tf", "json", "yaml"):
        return True
    return False


def _is_test(path, name, dirset) -> bool:
    if dirset & TEST_DIRS or "src/test/" in path:
        return True
    if any(d.endswith(".Tests") or d.endswith(".Test") or d.endswith("Tests")
           or d.endswith(".UnitTests") or d.endswith(".IntegrationTests") for d in dirset):
        return True
    return _any(name, TEST_NAME_GLOBS)

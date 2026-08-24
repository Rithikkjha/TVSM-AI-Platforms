"""Static analysis scanner — orchestrates the full scan pipeline.

For each repo:
1. Fetch file tree via GitHub API
2. Detect language
3. Fetch relevant source files
4. Run extractors (endpoints, HTTP calls, service bus, databases)
5. Run common extractor (ownership, README, git activity, modules)
6. Assemble into ServiceManifest
7. Write to YAML

Usage:
    python -m src.analysis.scanner --repo booking-crud-services
    python -m src.analysis.scanner --org TVSM-CS
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from analysis.extractors.common import CommonExtractor
from analysis.extractors.node_nestjs import NodeNestJSExtractor
from analysis.github_fetcher import GitHubFetcher
from analysis.models.manifest import ServiceManifest
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Files we always fetch regardless of language
_COMMON_FILES = [
    "README.md",
    "readme.md",
    "CODEOWNERS",
    ".github/CODEOWNERS",
    "Dockerfile",
    ".env.example",
    ".env.sample",
    "docker-compose.yml",
    "docker-compose.yaml",
]

# Language-specific files to fetch
_LANGUAGE_FILES: dict[str, list[str]] = {
    "node": [
        "package.json",
        "tsconfig.json",
        "nest-cli.json",
        ".env.example",
        "swagger.json",
        "openapi.json",
        "openapi.yaml",
        "src/shared/constants/constants.ts",
        "src/constants/constants.ts",
        "src/common/constants.ts",
        "src/config/constants.ts",
    ],
    "java": [
        "pom.xml",
        "build.gradle",
        "src/main/resources/application.properties",
        "src/main/resources/application.yml",
        "src/main/resources/application.yaml",
    ],
    "dotnet": [
        "appsettings.json",
        "appsettings.Development.json",
        "web.config",
    ],
}

# Known services list (loaded from mcp_servers.yaml)
_KNOWN_SERVICES: list[str] = []


def _detect_language(tree_paths: list[str]) -> str:
    """Detect primary language from file tree."""
    has_pom = "pom.xml" in tree_paths
    has_gradle = "build.gradle" in tree_paths
    has_package_json = "package.json" in tree_paths
    has_csproj = any(p.endswith(".csproj") for p in tree_paths)
    has_pyproject = "pyproject.toml" in tree_paths

    if has_pom or has_gradle:
        return "java"
    if has_package_json:
        return "node"
    if has_csproj:
        return "dotnet"
    if has_pyproject:
        return "python"
    return "unknown"


def _get_source_files_to_fetch(tree: list[dict[str, Any]], language: str) -> list[str]:
    """Determine which source files to fetch for analysis.

    We don't fetch ALL files — just the ones likely to contain
    endpoints, HTTP calls, service bus patterns, and config.
    """
    paths_to_fetch: list[str] = []

    # Key directories by language
    key_patterns: dict[str, list[str]] = {
        "node": [
            r"src/.*\.(ts|js)$",
            r"app/.*\.(ts|js)$",
            r"lib/.*\.(ts|js)$",
            r"routes?/.*\.(ts|js)$",
            r"controllers?/.*\.(ts|js)$",
            r"services?/.*\.(ts|js)$",
            r"modules?/.*\.(ts|js)$",
            r"events?/.*\.(ts|js)$",
            r"middleware/.*\.(ts|js)$",
            r"config/.*\.(ts|js|json)$",
            r"database/.*\.(ts|js)$",
            r"entities?/.*\.(ts|js)$",
            r"models?/.*\.(ts|js)$",
            r"listener/.*\.(ts|js)$",
            r"publisher/.*\.(ts|js)$",
            r"cloud-conductor/.*\.(ts|js)$",
        ],
        "java": [
            r"src/main/java/.*\.(java|kt)$",
            r"src/main/resources/.*\.(properties|yml|yaml|xml)$",
        ],
        "dotnet": [
            r".*Controllers?/.*\.cs$",
            r".*Services?/.*\.cs$",
            r".*Handlers?/.*\.cs$",
            r".*Clients?/.*\.cs$",
            r".*Hubs?/.*\.cs$",
            r".*Models?/.*\.cs$",
            r".*\.csproj$",
            r".*appsettings.*\.json$",
            r".*web\.config$",
            r"Startup\.cs$",
            r"Program\.cs$",
        ],
    }

    patterns = key_patterns.get(language, [r"src/.*"])

    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item.get("path", "")
        size = item.get("size", 0)

        # Skip very large files (>100KB) and test files
        if size > 100_000:
            continue
        if "test" in path.lower() or "spec" in path.lower() or "__test__" in path:
            continue
        if "node_modules" in path or "dist/" in path or "build/" in path:
            continue

        for pattern in patterns:
            if re.search(pattern, path):
                paths_to_fetch.append(path)
                break

    # Cap at 100 files to avoid rate limiting
    if len(paths_to_fetch) > 100:
        # Prioritize: controllers/routes first, then services, then others
        priority_keywords = ["controller", "route", "service", "event", "middleware", "config",
                             "servicebus", "service_bus", "topic", "queue", "listener", "publisher",
                             "consumer", "receiver", "notifier", "dispatcher", "client",
                             "integration", "lead", "payment", "auth", "entity", "entities",
                             "database", "model"]
        scored = []
        for p in paths_to_fetch:
            score = sum(1 for kw in priority_keywords if kw in p.lower())
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        paths_to_fetch = [p for _, p in scored[:100]]

    return paths_to_fetch


def _extract_framework(files: dict[str, str], language: str) -> str:
    """Detect framework and version from build files."""
    if language == "node":
        pkg_content = files.get("package.json")
        if pkg_content:
            try:
                import json
                pkg = json.loads(pkg_content)
                deps = pkg.get("dependencies", {})
                if "@nestjs/core" in deps:
                    version = deps["@nestjs/core"].lstrip("^~")
                    return f"nestjs@{version}"
                if "express" in deps:
                    version = deps["express"].lstrip("^~")
                    return f"express@{version}"
                if "fastify" in deps:
                    version = deps["fastify"].lstrip("^~")
                    return f"fastify@{version}"
            except Exception:
                pass
    elif language == "java":
        pom = files.get("pom.xml", "")
        if "spring-boot" in pom:
            match = re.search(r"<spring-boot\.version>([^<]+)", pom)
            if match:
                return f"spring-boot@{match.group(1)}"
            match = re.search(r"spring-boot-starter-parent.*?<version>([^<]+)", pom, re.DOTALL)
            if match:
                return f"spring-boot@{match.group(1)}"
            return "spring-boot"
    return ""


async def scan_repo(
    fetcher: GitHubFetcher,
    repo_name: str,
    known_services: list[str],
    branch: str | None = None,
) -> ServiceManifest:
    """Run the full static analysis pipeline on a single repo.

    Steps:
    1. Get file tree
    2. Detect language
    3. Fetch source files + common files
    4. Run language-specific extractor
    5. Run common extractor
    6. Assemble manifest
    """
    logger.info("=" * 60)
    logger.info("Scanning: %s", repo_name)
    logger.info("=" * 60)

    # Step 1: Get file tree
    logger.info("[1/6] Fetching file tree...")
    tree = await fetcher.get_tree(repo_name, branch)
    if not tree:
        logger.warning("Empty tree for %s — repo may be empty or inaccessible", repo_name)
        return ServiceManifest(name=repo_name)

    tree_paths = [item.get("path", "") for item in tree]
    directory_tree = fetcher.get_directory_tree_display(tree, max_depth=2)

    # Step 2: Detect language
    language = _detect_language(tree_paths)
    logger.info("[2/6] Detected language: %s", language)

    # Step 3: Fetch files
    logger.info("[3/6] Fetching source files...")
    # Common files
    common_file_paths = [f for f in _COMMON_FILES if f in tree_paths]
    # Language-specific config files
    lang_files = _LANGUAGE_FILES.get(language, [])
    lang_file_paths = [f for f in lang_files if f in tree_paths]
    # Source files for analysis
    source_file_paths = _get_source_files_to_fetch(tree, language)

    all_paths = list(set(common_file_paths + lang_file_paths + source_file_paths))
    logger.info("  Fetching %d files (%d source, %d config/common)...",
                len(all_paths), len(source_file_paths), len(common_file_paths + lang_file_paths))

    files = await fetcher.get_file_batch(repo_name, all_paths)
    logger.info("  Got %d files successfully", len(files))

    # Step 4: Run language-specific extractor
    logger.info("[4/6] Running %s extractor...", language)
    endpoints = []
    http_calls = []
    publishes = []
    subscribes = []
    build_deps = []
    databases = []

    if language == "node":
        extractor = NodeNestJSExtractor(known_services)
        endpoints = await extractor.extract_endpoints(files)
        http_calls = await extractor.extract_http_calls(files)
        publishes, subscribes = await extractor.extract_service_bus(files)
        build_deps = await extractor.extract_build_deps(files)
        databases = await extractor.extract_databases(files)
    elif language == "java":
        from analysis.extractors.java_spring import JavaSpringExtractor
        extractor = JavaSpringExtractor(known_services)
        endpoints = await extractor.extract_endpoints(files)
        http_calls = await extractor.extract_http_calls(files)
        publishes, subscribes = await extractor.extract_service_bus(files)
        build_deps = await extractor.extract_build_deps(files)
        databases = await extractor.extract_databases(files)
    elif language == "dotnet":
        from analysis.extractors.dotnet import DotNetExtractor
        extractor = DotNetExtractor(known_services)
        endpoints = await extractor.extract_endpoints(files)
        http_calls = await extractor.extract_http_calls(files)
        publishes, subscribes = await extractor.extract_service_bus(files)
        build_deps = await extractor.extract_build_deps(files)
        databases = await extractor.extract_databases(files)
    # TODO: Add Python extractor
    else:
        logger.info("  No extractor for language '%s' yet — skipping code analysis", language)

    logger.info("  Found: %d endpoints, %d HTTP calls, %d pub topics, %d sub topics, %d databases",
                len(endpoints), len(http_calls), len(publishes), len(subscribes), len(databases))

    # Step 4b: Parse swagger.json/openapi.json if available (overrides regex-extracted endpoints)
    swagger = files.get("swagger.json") or files.get("openapi.json")
    if swagger:
        try:
            import json as _json
            spec = _json.loads(swagger)
            swagger_endpoints = []
            for path, methods in spec.get("paths", {}).items():
                for method, details in methods.items():
                    if method.lower() in ("get", "post", "put", "delete", "patch"):
                        from analysis.models.manifest import Endpoint as _Ep
                        swagger_endpoints.append(_Ep(
                            method=method.upper(),
                            path=path,
                            description=details.get("summary", ""),
                            file="swagger.json",
                        ))
            if swagger_endpoints:
                logger.info("  Swagger/OpenAPI found: %d endpoints (overriding regex results)", len(swagger_endpoints))
                endpoints = swagger_endpoints
        except Exception as exc:
            logger.warning("  Failed to parse swagger.json: %s", exc)

    # Step 4c: Extract entity/model schemas
    entity_fields: list[dict] = []
    for file_path, content in files.items():
        if "entit" not in file_path.lower() and "model" not in file_path.lower():
            continue
        if "test" in file_path.lower() or "spec" in file_path.lower():
            continue
        if "index" in file_path.split("/")[-1]:
            continue
        # Extract class name and @Column fields
        import re as _re
        class_match = _re.search(r"(?:export\s+)?class\s+(\w+)", content)
        if not class_match:
            continue
        entity_name = class_match.group(1)
        columns = _re.findall(r"@(?:Column|PrimaryColumn|CreateDateColumn)\([^)]*\)\s*\n\s*(\w+)", content)
        if columns:
            entity_fields.append({
                "name": entity_name,
                "fields": columns[:15],  # limit to 15 key fields
                "file": file_path,
            })

    # Step 5: Run common extractor
    logger.info("[5/6] Running common extractor...")
    common = CommonExtractor()

    # Purpose from README
    readme = files.get("README.md") or files.get("readme.md") or ""
    purpose = common.extract_purpose(readme)

    # Ownership
    codeowners = files.get("CODEOWNERS") or files.get(".github/CODEOWNERS")
    owner_team, contacts = common.extract_ownership(codeowners)
    if not contacts:
        contributors = await fetcher.get_contributors(repo_name)
        contacts = common.extract_ownership_from_contributors(contributors)

    # Git activity
    commits = await fetcher.get_commits(repo_name, per_page=100)
    git_activity = common.extract_git_activity(commits)

    # Env vars
    env_content = files.get(".env.example") or files.get(".env.sample")
    env_vars = common.extract_env_vars(env_content)

    # Key modules
    key_modules = common.extract_key_modules(files, language)

    # Domain keywords
    domain_keywords = common.extract_domain_keywords(files, language)

    # Framework
    framework = _extract_framework(files, language)

    # Config files found
    config_files = [p for p in files.keys() if any(
        k in p.lower() for k in ["config", ".env", "application.", "appsettings", "web.config"]
    )]

    # Step 6: Assemble manifest
    logger.info("[6/6] Assembling manifest...")
    from analysis.models.manifest import Dependencies

    manifest = ServiceManifest(
        name=repo_name,
        language=language,
        framework=framework,
        owner_team=owner_team,
        contacts=contacts,
        purpose=purpose,
        domain_keywords=domain_keywords,
        directory_tree=directory_tree,
        key_modules=key_modules,
        git_activity=git_activity,
        api_base_path=_detect_base_path(endpoints),
        endpoints=endpoints,
        dependencies=Dependencies(
            http_calls=http_calls,
            service_bus_publishes=publishes,
            service_bus_subscribes=subscribes,
            build=build_deps,
            databases=databases,
        ),
        env_vars=env_vars,
        config_files=config_files,
    )

    logger.info("✅ Scan complete for %s", repo_name)
    return manifest


def _detect_base_path(endpoints: list) -> str:
    """Try to detect a common base path from all endpoints."""
    if not endpoints:
        return ""
    paths = [e.path for e in endpoints]
    if len(paths) < 2:
        return ""
    # Find common prefix
    prefix = paths[0]
    for path in paths[1:]:
        while not path.startswith(prefix):
            prefix = prefix.rsplit("/", 1)[0]
            if "/" not in prefix:
                return ""
    return prefix if prefix and prefix != "/" else ""


def save_manifest(manifest: ServiceManifest, output_dir: Path) -> Path:
    """Save a manifest to YAML file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{manifest.name}.service-manifest.yaml"

    # Convert to dict and write YAML
    data = manifest.model_dump(exclude_none=True, exclude_defaults=False)

    # Add header comment
    yaml_content = (
        f"# Auto-generated by tvsm-brain static analyzer\n"
        f"# Scanned: {manifest.scanned_at}\n"
        f"# Review status: {manifest.review_status}\n"
        f"# -----------------------------------------------\n\n"
    )
    yaml_content += yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    output_path.write_text(yaml_content, encoding="utf-8")
    return output_path


async def run_scan(
    repos: list[str],
    output_dir: str = "manifests",
    branch: str | None = None,
) -> None:
    """Run the scanner on a list of repos."""
    settings = get_settings()

    # Load known services from mcp_servers.yaml
    from config.mcp_registry import load_mcp_registry
    registry = load_mcp_registry(settings.mcp_servers_config_path)
    github_config = next((s for s in registry.servers if s.name == "github"), None)
    known_services = github_config.config.get("repos", []) if github_config else []

    org = github_config.config.get("org", "TVSM-CS") if github_config else "TVSM-CS"

    fetcher = GitHubFetcher(token=settings.github_token, org=org)
    output_path = Path(output_dir)

    results: list[tuple[str, str]] = []  # (repo, status)

    try:
        for idx, repo in enumerate(repos, 1):
            logger.info("\n[%d/%d] Processing %s...", idx, len(repos), repo)
            try:
                manifest = await scan_repo(fetcher, repo, known_services, branch)
                saved_path = save_manifest(manifest, output_path)
                results.append((repo, f"✅ saved to {saved_path}"))
            except Exception as exc:
                logger.error("Failed to scan %s: %s", repo, exc)
                results.append((repo, f"❌ failed: {exc}"))
    finally:
        await fetcher.close()

    # Print summary
    print("\n" + "=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    for repo, status in results:
        print(f"  {repo}: {status}")
    print(f"\nManifests written to: {output_path.resolve()}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for the scanner."""
    import argparse

    parser = argparse.ArgumentParser(description="Static analysis scanner for TVSM-CS repos")
    parser.add_argument("--repo", type=str, help="Scan a single repo")
    parser.add_argument("--repos", type=str, nargs="+", help="Scan multiple repos")
    parser.add_argument("--org", type=str, help="Scan all repos in the org (from mcp_servers.yaml)")
    parser.add_argument("--output", type=str, default="manifests", help="Output directory")
    parser.add_argument("--branch", type=str, default=None, help="Branch to scan (default: repo's default)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Determine which repos to scan
    if args.repo:
        repos = [args.repo]
    elif args.repos:
        repos = args.repos
    elif args.org:
        # Load all repos from config
        settings = get_settings()
        from config.mcp_registry import load_mcp_registry
        registry = load_mcp_registry(settings.mcp_servers_config_path)
        github_config = next((s for s in registry.servers if s.name == "github"), None)
        repos = github_config.config.get("repos", []) if github_config else []
    else:
        parser.error("Specify --repo, --repos, or --org")
        return

    logger.info("Scanning %d repo(s)...", len(repos))
    asyncio.run(run_scan(repos, output_dir=args.output, branch=args.branch))


if __name__ == "__main__":
    main()

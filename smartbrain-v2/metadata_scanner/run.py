"""CLI entry point for the Metadata Scanner.

Usage:
    python -m metadata_scanner.run --repo booking-crud-services
    python -m metadata_scanner.run --all
    python -m metadata_scanner.run --all --llm
    python -m metadata_scanner.run --all --llm --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import yaml

from config.settings import get_settings
from metadata_scanner.github_metadata import MetadataFetcher
from metadata_scanner.steering_generator import SteeringGenerator
from shared.reingest import trigger_reingest

logger = logging.getLogger(__name__)


async def run_scan(repos: list[str], use_llm: bool = False) -> dict:
    """Execute the metadata scan pipeline for given repos.

    For each repo: fetch metadata → generate steering → trigger re-ingest.
    Errors are isolated per-repo so one failure doesn't stop the batch.
    """
    settings = get_settings()
    fetcher = MetadataFetcher(token=settings.github_token)
    generator = SteeringGenerator(use_llm=use_llm)

    results: list[dict] = []
    for repo in repos:
        try:
            logger.info("Processing: %s", repo)

            # Step 1: Fetch metadata
            metadata = await fetcher.fetch(repo)
            logger.info("  Fetched metadata: %d languages, %d files",
                       len(metadata.languages), len(metadata.file_tree))

            # Step 2: Generate steering files
            files = await generator.generate(repo, metadata)
            logger.info("  Generated %d steering files", len(files))

            # Step 3: Trigger re-ingestion
            ingest = await trigger_reingest(repo, ["product", "structure", "tech"])
            logger.info(
                "  Ingestion: %d processed, %d skipped, %d created",
                ingest.files_processed,
                ingest.files_skipped,
                ingest.chunks_created,
            )

            results.append({
                "repo": repo,
                "status": "ok",
                "files": len(files),
                "ingestion": {
                    "files_processed": ingest.files_processed,
                    "files_skipped": ingest.files_skipped,
                    "chunks_created": ingest.chunks_created,
                    "error": ingest.error,
                },
            })
        except Exception as exc:
            logger.error("Failed to process %s: %s", repo, exc)
            results.append({"repo": repo, "status": "error", "error": str(exc)})

    await fetcher.close()
    return {"repos_processed": len(results), "results": results}


def _resolve_repos(args: argparse.Namespace) -> list[str]:
    """Resolve the list of repos to scan from CLI args."""
    if args.repo:
        return [args.repo]

    if args.all:
        # Read repos from config/mcp_servers.yaml
        config_path = Path("config/mcp_servers.yaml")
        if not config_path.exists():
            logger.error("Config file not found: %s", config_path)
            sys.exit(1)

        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        servers = config.get("servers", [])
        github_server = next(
            (s for s in servers if s.get("name") == "github"), None
        )
        if github_server is None:
            logger.error("No 'github' server found in %s", config_path)
            sys.exit(1)

        repos = github_server.get("config", {}).get("repos", [])
        if not repos:
            logger.error("No repos configured in github server config")
            sys.exit(1)

        return repos

    logger.error("Specify --repo <name> or --all")
    sys.exit(1)


def _print_summary(result: dict) -> None:
    """Print a human-readable summary of the scan results."""
    print("\n" + "=" * 60)
    print("Metadata Scanner — Summary")
    print("=" * 60)
    print(f"Repos processed: {result['repos_processed']}")
    print()

    ok_count = sum(1 for r in result["results"] if r["status"] == "ok")
    err_count = sum(1 for r in result["results"] if r["status"] == "error")
    print(f"  ✅ Successful: {ok_count}")
    print(f"  ❌ Failed: {err_count}")
    print()

    if err_count > 0:
        print("Failures:")
        for r in result["results"]:
            if r["status"] == "error":
                print(f"  - {r['repo']}: {r.get('error', 'unknown')}")
    print("=" * 60)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Metadata Scanner — generate steering files from GitHub metadata"
    )
    parser.add_argument("--repo", type=str, help="Scan a single repo")
    parser.add_argument("--all", action="store_true", help="Scan all configured repos")
    parser.add_argument("--llm", action="store_true", help="Use LLM-enhanced generation")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    repos = _resolve_repos(args)
    logger.info("Scanning %d repos (llm=%s)", len(repos), args.llm)

    result = asyncio.run(run_scan(repos, use_llm=args.llm))
    _print_summary(result)


if __name__ == "__main__":
    main()


__all__ = [
    "main",
    "run_scan",
]

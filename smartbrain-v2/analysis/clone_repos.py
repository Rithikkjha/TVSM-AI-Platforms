"""Clone all repos from mcp_servers.yaml using the GitHub token.

Usage:
    python -m src.analysis.clone_repos
    python -m src.analysis.clone_repos --output ~/kiro-batch
    python -m src.analysis.clone_repos --only tvsm-auth booking-crud-services

After running:
    1. Open each cloned repo in Kiro
    2. Ask Kiro to generate .kiro/steering/ files
    3. Run collect_steering.py to gather them all
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_repos(config_path: str) -> tuple[str, list[str]]:
    """Load org and repo list from mcp_servers.yaml."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    github = next((s for s in config["servers"] if s["name"] == "github"), None)
    if not github:
        raise ValueError("No github server in mcp_servers.yaml")

    org = github["config"]["org"]
    repos = github["config"]["repos"]
    return org, repos


def clone_repo(token: str, org: str, repo: str, dest: Path) -> tuple[bool, str]:
    """Clone a single repo. Returns (success, message)."""
    target = dest / repo

    if target.exists():
        # Check if it's a valid git repo
        if (target / ".git").exists():
            return True, "already cloned (skipped)"
        else:
            shutil.rmtree(target)

    # Use token in URL — works with x-access-token format
    url = f"https://x-access-token:{token}@github.com/{org}/{repo}.git"

    try:
        result = subprocess.run(
            ["git", "clone", url, str(target)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True, "cloned"
        else:
            err = result.stderr.strip().split("\n")[-1]
            # Don't leak token in error message
            err = err.replace(token, "***")
            return False, f"failed: {err}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as exc:
        return False, f"error: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Clone all configured repos for Kiro batch processing")
    parser.add_argument(
        "--output",
        default=str(Path.home() / "kiro-batch"),
        help="Where to clone repos (default: ~/kiro-batch)",
    )
    parser.add_argument(
        "--config",
        default="src/config/mcp_servers.yaml",
        help="Path to mcp_servers.yaml",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only clone specific repos (by name)",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Env var name for GitHub token",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    # Load token from .env if not in environment
    token = os.environ.get(args.token_env, "")
    if not token:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith(f"{args.token_env}="):
                    token = line.split("=", 1)[1].strip()
                    break

    if not token:
        logger.error("No GitHub token found in env var %s or .env file", args.token_env)
        return

    # Load repo list
    org, all_repos = load_repos(args.config)
    repos = [r for r in all_repos if not args.only or r in args.only]

    if not repos:
        logger.error("No repos to clone")
        return

    output_dir = Path(args.output).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Cloning %d repos from %s to %s", len(repos), org, output_dir)
    logger.info("=" * 60)

    results: list[tuple[str, str]] = []
    success_count = 0
    fail_count = 0

    for idx, repo in enumerate(repos, 1):
        logger.info("[%d/%d] Cloning %s...", idx, len(repos), repo)
        success, message = clone_repo(token, org, repo, output_dir)
        results.append((repo, message))
        if success:
            success_count += 1
            logger.info("  ✅ %s", message)
        else:
            fail_count += 1
            logger.warning("  ❌ %s", message)

    # Summary
    print("")
    print("=" * 60)
    print("CLONE SUMMARY")
    print("=" * 60)
    print(f"  Total: {len(repos)}")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"\nRepos cloned to: {output_dir}")
    print("\nNext steps:")
    print("  1. Open each repo in Kiro")
    print("  2. Ask Kiro to generate .kiro/steering/ files")
    print("  3. Run: python -m src.analysis.collect_steering")
    print("=" * 60)

    if fail_count > 0:
        print("\nFailed repos:")
        for repo, msg in results:
            if "failed" in msg or "error" in msg or "timeout" in msg:
                print(f"  - {repo}: {msg}")


if __name__ == "__main__":
    main()

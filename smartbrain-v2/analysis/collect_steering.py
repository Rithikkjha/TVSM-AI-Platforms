"""Collect .kiro/steering/ files from cloned repos and copy them centrally.

Usage:
    python -m src.analysis.collect_steering
    python -m src.analysis.collect_steering --input ~/kiro-batch --output kiro_steering

After Kiro generates .kiro/steering/{product,structure,tech}.md in each cloned repo,
this script gathers them into tvsm-brain/kiro_steering/{repo-name}/ for ingestion.
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def collect_for_repo(repo_dir: Path, output_dir: Path) -> tuple[bool, str]:
    """Copy .kiro/steering/ files from a single cloned repo. Returns (found, message)."""
    repo_name = repo_dir.name
    steering_src = repo_dir / ".kiro" / "steering"

    if not steering_src.exists():
        return False, "no .kiro/steering/ folder"

    md_files = list(steering_src.glob("*.md"))
    if not md_files:
        return False, ".kiro/steering/ exists but no .md files"

    # Copy to output
    dest = output_dir / repo_name
    dest.mkdir(parents=True, exist_ok=True)

    copied = []
    for md in md_files:
        shutil.copy2(md, dest / md.name)
        copied.append(md.name)

    return True, f"collected {len(copied)} files: {', '.join(copied)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Kiro-generated steering files from cloned repos")
    parser.add_argument(
        "--input",
        default=str(Path.home() / "kiro-batch"),
        help="Where repos were cloned (default: ~/kiro-batch)",
    )
    parser.add_argument(
        "--output",
        default="kiro_steering",
        help="Where to put collected steering files (default: kiro_steering/)",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    input_dir = Path(args.input).expanduser()
    output_dir = Path(args.output).expanduser()

    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all cloned repos (folders with .git)
    repos = sorted([p for p in input_dir.iterdir() if p.is_dir() and (p / ".git").exists()])

    if not repos:
        logger.error("No cloned repos found in %s", input_dir)
        return

    logger.info("=" * 60)
    logger.info("Collecting Kiro steering from %d repos", len(repos))
    logger.info("=" * 60)

    found_count = 0
    missing_count = 0
    results: list[tuple[str, str, bool]] = []

    for repo_dir in repos:
        repo_name = repo_dir.name
        found, message = collect_for_repo(repo_dir, output_dir)
        results.append((repo_name, message, found))
        if found:
            found_count += 1
            logger.info("  ✅ %s — %s", repo_name, message)
        else:
            missing_count += 1
            logger.info("  ⏭️  %s — %s", repo_name, message)

    # Summary
    print("")
    print("=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)
    print(f"  Total repos: {len(repos)}")
    print(f"  ✅ Steering collected: {found_count}")
    print(f"  ⏭️  Steering missing: {missing_count}")
    print(f"\nOutput: {output_dir.resolve()}")
    print("=" * 60)

    if missing_count > 0:
        print("\nRepos still needing Kiro steering:")
        for name, msg, found in results:
            if not found:
                print(f"  - {name}")


if __name__ == "__main__":
    main()

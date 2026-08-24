"""Build the global steering files from kiro_steering/.

This script:
1. Merges product.md + structure.md + tech.md into one file per service (zero data loss)
2. Builds index.md with LLM-generated one-line summaries per service
3. Builds dependencies.md — a cross-service dependency map extracted from tech.md files

Usage:
    python steering-lite/scripts/build_global_steering.py
    python steering-lite/scripts/build_global_steering.py --skip-llm  (no index summaries, just raw)

Output:
    steering-lite/global_steering/
    ├── index.md
    ├── dependencies.md
    └── services/
        ├── booking-crud-services.md
        └── ...
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Paths
KIRO_STEERING_DIR = Path("kiro_steering")
OUTPUT_DIR = Path("steering-lite/global_steering")
SERVICES_DIR = OUTPUT_DIR / "services"


# ---------------------------------------------------------------------------
# Step 1: Merge per-service files (no LLM, zero data loss)
# ---------------------------------------------------------------------------


def build_service_files() -> list[dict[str, str]]:
    """Merge product + structure + tech into one file per service.

    Returns list of {name, path, product_content} for index building.
    """
    SERVICES_DIR.mkdir(parents=True, exist_ok=True)

    repos = sorted([
        d for d in KIRO_STEERING_DIR.iterdir()
        if d.is_dir() and any(d.glob("*.md"))
    ])

    services_meta: list[dict[str, str]] = []

    for repo_dir in repos:
        repo_name = repo_dir.name

        # Read each file (preserve full content)
        product = _read_if_exists(repo_dir / "product.md")
        structure = _read_if_exists(repo_dir / "structure.md")
        tech = _read_if_exists(repo_dir / "tech.md")

        # Build merged file
        sections = [f"# {repo_name}\n"]

        if product:
            sections.append("## Product Context\n")
            sections.append(product.strip())
            sections.append("")

        if structure:
            sections.append("## Code Structure\n")
            sections.append(structure.strip())
            sections.append("")

        if tech:
            sections.append("## Tech Stack & Dependencies\n")
            sections.append(tech.strip())
            sections.append("")

        merged_content = "\n\n".join(sections)

        # Write
        out_path = SERVICES_DIR / f"{repo_name}.md"
        out_path.write_text(merged_content, encoding="utf-8")

        services_meta.append({
            "name": repo_name,
            "path": f"services/{repo_name}.md",
            "product_content": product or "",
            "tech_content": tech or "",
        })

        logger.info("  ✅ %s", repo_name)

    return services_meta


# ---------------------------------------------------------------------------
# Step 2: Build index.md (LLM for one-liners, or fallback)
# ---------------------------------------------------------------------------


async def build_index(services_meta: list[dict[str, str]], use_llm: bool = True) -> None:
    """Build index.md with a one-liner per service."""

    summaries: list[dict[str, str]] = []

    if use_llm:
        summaries = await _generate_summaries_with_llm(services_meta)
    else:
        # Fallback: extract first sentence from product.md
        for svc in services_meta:
            first_line = _extract_first_sentence(svc["product_content"])
            summaries.append({"name": svc["name"], "summary": first_line})

    # Build the index markdown
    lines = [
        "# Service Index",
        "",
        f"Total services: {len(summaries)}",
        "",
        "| # | Service | Summary |",
        "|---|---------|---------|",
    ]

    for idx, s in enumerate(summaries, 1):
        lines.append(f"| {idx} | [{s['name']}](services/{s['name']}.md) | {s['summary']} |")

    lines.append("")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")
    logger.info("  ✅ index.md (%d services)", len(summaries))


async def _generate_summaries_with_llm(services_meta: list[dict[str, str]]) -> list[dict[str, str]]:
    """Use LLM to generate one-line summaries for each service."""
    from dotenv import load_dotenv
    load_dotenv()

    import httpx
    from openai import AsyncAzureOpenAI
    from src.config.settings import get_settings

    settings = get_settings()
    custom_http_client = httpx.AsyncClient(verify=False)
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=custom_http_client,
    )

    # Batch all services into one prompt (cheaper than 42 individual calls)
    service_list = "\n".join(
        f"- {svc['name']}: {svc['product_content'][:500]}"
        for svc in services_meta
    )

    prompt = f"""For each service below, write a ONE-LINE summary (max 15 words) describing what it does.
Return ONLY a list in this exact format, one per line:
service-name: summary here

Services:
{service_list}"""

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=3000,
        )
        raw = response.choices[0].message.content or ""

        # Parse response
        summaries = []
        result_map: dict[str, str] = {}
        for line in raw.strip().split("\n"):
            if ":" in line:
                name, summary = line.split(":", 1)
                result_map[name.strip().lstrip("- ")] = summary.strip()

        for svc in services_meta:
            summary = result_map.get(svc["name"], _extract_first_sentence(svc["product_content"]))
            summaries.append({"name": svc["name"], "summary": summary})

        return summaries
    except Exception as exc:
        logger.warning("LLM index generation failed: %s — using fallback", exc)
        return [
            {"name": svc["name"], "summary": _extract_first_sentence(svc["product_content"])}
            for svc in services_meta
        ]
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Step 3: Build dependencies.md (parse tech.md files, optionally LLM)
# ---------------------------------------------------------------------------


async def build_dependencies(services_meta: list[dict[str, str]], use_llm: bool = True) -> None:
    """Build dependencies.md — cross-service dependency map."""

    # Parse dependencies from tech.md files deterministically
    all_deps: list[dict[str, str]] = []
    for svc in services_meta:
        tech = svc["tech_content"]
        deps = _parse_dependencies_from_tech(svc["name"], tech)
        all_deps.extend(deps)

    if use_llm and all_deps:
        # Use LLM to clean up and format a nice dependency map
        dep_text = "\n".join(
            f"- {d['source']} → {d['target']} ({d['type']}: {d['detail']})"
            for d in all_deps
        )
        await _build_dependencies_with_llm(dep_text, all_deps)
    else:
        # Deterministic fallback
        _build_dependencies_deterministic(all_deps)

    logger.info("  ✅ dependencies.md (%d dependency edges)", len(all_deps))


def _parse_dependencies_from_tech(service_name: str, tech_content: str) -> list[dict[str, str]]:
    """Extract dependency info from a tech.md file by parsing markdown tables."""
    deps: list[dict[str, str]] = []

    if not tech_content:
        return deps

    # Look for HTTP call tables (Target Service | URL | ...)
    # and Service Bus tables (Topic | ...)
    lines = tech_content.split("\n")

    in_http_table = False
    in_publishes_table = False
    in_subscribes_table = False

    for line in lines:
        lower = line.lower()

        # Detect table sections
        if "http" in lower and "call" in lower:
            in_http_table = True
            in_publishes_table = False
            in_subscribes_table = False
            continue
        elif "publish" in lower:
            in_publishes_table = True
            in_http_table = False
            in_subscribes_table = False
            continue
        elif "subscri" in lower:
            in_subscribes_table = True
            in_http_table = False
            in_publishes_table = False
            continue
        elif line.startswith("##"):
            in_http_table = False
            in_publishes_table = False
            in_subscribes_table = False
            continue

        # Parse table rows
        if "|" not in line or line.strip().startswith("|---"):
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells or len(cells) < 2:
            continue

        if in_http_table and len(cells) >= 2:
            target = cells[0].strip("`").strip()
            if target and target.lower() not in ("target service", "---", ""):
                deps.append({
                    "source": service_name,
                    "target": target,
                    "type": "HTTP",
                    "detail": cells[1] if len(cells) > 1 else "",
                })

        elif in_publishes_table and len(cells) >= 1:
            topic = cells[0].strip("`").strip()
            if topic and topic.lower() not in ("topic", "---", ""):
                deps.append({
                    "source": service_name,
                    "target": f"topic:{topic}",
                    "type": "publishes",
                    "detail": topic,
                })

        elif in_subscribes_table and len(cells) >= 1:
            topic = cells[0].strip("`").strip()
            if topic and topic.lower() not in ("topic", "---", ""):
                deps.append({
                    "source": f"topic:{topic}",
                    "target": service_name,
                    "type": "subscribes",
                    "detail": topic,
                })

    return deps


async def _build_dependencies_with_llm(dep_text: str, all_deps: list[dict[str, str]]) -> None:
    """Use LLM to format a clean dependency map."""
    from dotenv import load_dotenv
    load_dotenv()

    import httpx
    from openai import AsyncAzureOpenAI
    from src.config.settings import get_settings

    settings = get_settings()
    custom_http_client = httpx.AsyncClient(verify=False)
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=custom_http_client,
    )

    prompt = f"""You are given a list of service dependencies extracted from code analysis.
Build a clean, well-organized markdown document showing:

1. A summary table of all HTTP service-to-service calls
2. A Service Bus topology (who publishes what, who subscribes to what)
3. A "most depended upon" ranking (services with the most incoming deps)

Keep it factual. Only include what's in the data below. Format as clean markdown with tables.

Dependencies found:
{dep_text}"""

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4000,
        )
        content = response.choices[0].message.content or ""
        header = "# Cross-Service Dependencies\n\n*Auto-generated from tech.md analysis*\n\n"
        (OUTPUT_DIR / "dependencies.md").write_text(header + content, encoding="utf-8")
    except Exception as exc:
        logger.warning("LLM dependency map failed: %s — using deterministic", exc)
        _build_dependencies_deterministic(all_deps)
    finally:
        await client.close()


def _build_dependencies_deterministic(all_deps: list[dict[str, str]]) -> None:
    """Build dependencies.md without LLM — just structured tables."""
    lines = [
        "# Cross-Service Dependencies",
        "",
        "*Auto-generated from tech.md analysis*",
        "",
    ]

    # HTTP calls
    http_deps = [d for d in all_deps if d["type"] == "HTTP"]
    if http_deps:
        lines.append("## HTTP Service-to-Service Calls")
        lines.append("")
        lines.append("| Source | Target | Detail |")
        lines.append("|--------|--------|--------|")
        for d in http_deps:
            lines.append(f"| {d['source']} | {d['target']} | {d['detail']} |")
        lines.append("")

    # Service Bus publishes
    pub_deps = [d for d in all_deps if d["type"] == "publishes"]
    if pub_deps:
        lines.append("## Service Bus — Publishers")
        lines.append("")
        lines.append("| Service | Publishes Topic |")
        lines.append("|---------|----------------|")
        for d in pub_deps:
            lines.append(f"| {d['source']} | {d['detail']} |")
        lines.append("")

    # Service Bus subscribes
    sub_deps = [d for d in all_deps if d["type"] == "subscribes"]
    if sub_deps:
        lines.append("## Service Bus — Subscribers")
        lines.append("")
        lines.append("| Subscribes Topic | Service |")
        lines.append("|-----------------|---------|")
        for d in sub_deps:
            lines.append(f"| {d['detail']} | {d['target']} |")
        lines.append("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "dependencies.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_if_exists(path: Path) -> str:
    """Read file content or return empty string."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _extract_first_sentence(text: str) -> str:
    """Extract first meaningful sentence from markdown text."""
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---") or line.startswith("*"):
            continue
        if line.startswith("-"):
            line = line.lstrip("- ")
        # Truncate to ~80 chars
        if len(line) > 80:
            line = line[:77] + "..."
        return line
    return "No description available"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main_async(skip_llm: bool = False) -> None:
    """Run the full build pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Building Global Steering")
    logger.info("=" * 60)

    if not KIRO_STEERING_DIR.exists():
        logger.error("kiro_steering/ directory not found!")
        return

    # Step 1: Merge per-service files
    logger.info("")
    logger.info("Step 1: Merging per-service files...")
    services_meta = build_service_files()
    logger.info("  Merged %d services", len(services_meta))

    # Step 2: Build index
    logger.info("")
    logger.info("Step 2: Building index.md...")
    await build_index(services_meta, use_llm=not skip_llm)

    # Step 3: Build dependencies
    logger.info("")
    logger.info("Step 3: Building dependencies.md...")
    await build_dependencies(services_meta, use_llm=not skip_llm)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Done! Output: %s", OUTPUT_DIR.resolve())
    logger.info("=" * 60)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Build global steering from kiro_steering/")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM calls (deterministic only)")
    args = parser.parse_args()

    asyncio.run(main_async(skip_llm=args.skip_llm))


if __name__ == "__main__":
    main()

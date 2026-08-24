"""Generate enriched steering files from manifests.

Two modes:
1. Deterministic (no LLM) — renders manifest data directly to markdown
2. LLM-enhanced — passes static facts to GPT for human-friendly prose

The LLM CANNOT hallucinate dependencies because it only sees what
the static scanner actually found. It can only rephrase and summarize.

Usage:
    python -m src.analysis.steering_generator --input manifests/ --output generated_steering/
    python -m src.analysis.steering_generator --input manifests/ --output generated_steering/ --llm
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import yaml
from openai import AsyncAzureOpenAI

from analysis.models.manifest import ServiceManifest
from config.settings import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Deterministic rendering (no LLM)
# ---------------------------------------------------------------------------


def render_steering_deterministic(manifest: ServiceManifest) -> str:
    """Render a steering file purely from manifest data. Zero LLM, zero hallucination."""

    sections: list[str] = []

    # Header
    sections.append(f"# {manifest.name}\n")
    sections.append("*Auto-generated from static code analysis*\n")

    # Service Overview
    sections.append("## Service Overview")
    sections.append(f"- **Language:** {manifest.language} ({manifest.framework})" if manifest.framework else f"- **Language:** {manifest.language}")
    if manifest.owner_team:
        contacts_str = ", ".join(manifest.contacts[:3]) if manifest.contacts else ""
        sections.append(f"- **Owner:** {manifest.owner_team}" + (f" ({contacts_str})" if contacts_str else ""))
    elif manifest.contacts:
        sections.append(f"- **Contacts:** {', '.join(manifest.contacts[:5])}")
    if manifest.purpose:
        sections.append(f"- **Purpose:** {manifest.purpose}")
    if manifest.domain_keywords:
        sections.append(f"- **Domain:** {', '.join(manifest.domain_keywords[:10])}")
    sections.append("")

    # Code Structure
    if manifest.directory_tree:
        sections.append("## Code Structure")
        sections.append("```")
        # Show full tree (already filtered by github_fetcher)
        sections.append(manifest.directory_tree)
        sections.append("```")
        sections.append("")

    # Key Modules
    if manifest.key_modules:
        sections.append("## Key Modules")
        sections.append("| File | Purpose |")
        sections.append("|---|---|")
        for mod in manifest.key_modules:
            sections.append(f"| {mod.file} | {mod.purpose} |")
        sections.append("")

    # API Endpoints
    if manifest.endpoints:
        sections.append("## API Endpoints")
        sections.append("| Method | Path | Description | File |")
        sections.append("|--------|------|-------------|------|")
        for ep in manifest.endpoints:
            sections.append(f"| {ep.method} | {ep.path} | {ep.description} | {ep.file} |")
        sections.append("")

    # Dependencies
    has_deps = (
        manifest.dependencies.http_calls
        or manifest.dependencies.service_bus_publishes
        or manifest.dependencies.service_bus_subscribes
    )
    if has_deps:
        sections.append("## Dependencies (Outbound)")

        if manifest.dependencies.http_calls:
            sections.append("### HTTP Calls")
            sections.append("| Target Service | URL/Variable | Confidence | File |")
            sections.append("|---|---|---|---|")
            for dep in manifest.dependencies.http_calls:
                conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(dep.confidence, "⚪")
                # Extract URL/variable from evidence (format: "file:line — variable — code")
                parts = dep.evidence.split(" — ")
                url_var = parts[1] if len(parts) > 1 else ""
                file_ref = parts[0] if parts else dep.evidence
                sections.append(f"| {dep.target_service} | `{url_var}` | {conf_icon} {dep.confidence} | {file_ref} |")
            sections.append("")

        if manifest.dependencies.service_bus_publishes:
            sections.append("### Service Bus — Publishes")
            sections.append("| Topic | Confidence | File |")
            sections.append("|---|---|---|")
            for pub in manifest.dependencies.service_bus_publishes:
                conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(pub.confidence, "⚪")
                sections.append(f"| {pub.topic} | {conf_icon} {pub.confidence} | {pub.evidence} |")
            sections.append("")

        if manifest.dependencies.service_bus_subscribes:
            sections.append("### Service Bus — Subscribes")
            sections.append("| Topic | Source Service | Confidence | File |")
            sections.append("|---|---|---|---|")
            for sub in manifest.dependencies.service_bus_subscribes:
                conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(sub.confidence, "⚪")
                sections.append(f"| {sub.topic} | {sub.source_service} | {conf_icon} {sub.confidence} | {sub.evidence} |")
            sections.append("")

    # Databases
    if manifest.dependencies.databases:
        sections.append("## Databases")
        sections.append("| Type | Name | File |")
        sections.append("|---|---|---|")
        for db in manifest.dependencies.databases:
            sections.append(f"| {db.type} | {db.name} | {db.evidence} |")
        sections.append("")

    # Recent Activity
    if manifest.git_activity.last_commit_date:
        sections.append("## Recent Activity")
        ga = manifest.git_activity
        sections.append(f"- **Last commit:** {ga.last_commit_date} by {ga.last_commit_author} — \"{ga.last_commit_message}\"")
        if ga.active_contributors_30d:
            sections.append(f"- **Active contributors (30d):** {', '.join(ga.active_contributors_30d)}")
        sections.append(f"- **Commit frequency:** {ga.commit_frequency}")
        sections.append("")

    # Configuration
    if manifest.env_vars:
        sections.append("## Configuration")
        sections.append(f"**Required env vars:** {', '.join(manifest.env_vars)}")
        sections.append("")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# LLM-enhanced rendering
# ---------------------------------------------------------------------------

_LLM_STEERING_PROMPT = """You are writing a concise, accurate steering file for a microservice.
You are given VERIFIED FACTS from static code analysis. Your job is to:

1. Write a clear, human-friendly summary in the "Service Overview" section
2. Keep ALL the structured data (endpoints, dependencies, service bus, databases) EXACTLY as provided — do not add, remove, or modify any entries
3. Add brief contextual notes where helpful (e.g., "This service is the central booking hub that other services depend on for...")
4. Keep confidence levels and file references exactly as given

RULES:
- Do NOT invent dependencies, endpoints, or topics that aren't in the data
- Do NOT remove any entries from the tables
- You MAY rephrase the "purpose" into better prose
- You MAY add a brief "Architecture Notes" section if the code structure suggests patterns
- Keep it concise — this is a reference doc, not an essay

Output format: Markdown, same structure as the input but with improved prose."""


async def render_steering_with_llm(
    manifest: ServiceManifest,
    deterministic_md: str,
) -> str:
    """Enhance the deterministic steering file with LLM prose.

    The LLM receives the static facts and can only rephrase/summarize —
    it cannot add dependencies or endpoints that aren't in the data.
    """
    settings = get_settings()

    if not settings.azure_openai_key or not settings.azure_openai_endpoint:
        logger.warning("No Azure OpenAI credentials — falling back to deterministic output")
        return deterministic_md

    import httpx as _httpx
    custom_http_client = _httpx.AsyncClient(verify=False)

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        timeout=60.0,
        http_client=custom_http_client,
    )

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=[
                {"role": "system", "content": _LLM_STEERING_PROMPT},
                {"role": "user", "content": f"Here is the static analysis output for {manifest.name}. Enhance it:\n\n{deterministic_md}"},
            ],
            temperature=0.1,
            max_tokens=4000,
            timeout=60.0,
        )
        result = response.choices[0].message.content
        if result:
            return result
        return deterministic_md
    except Exception as exc:
        logger.error("LLM steering generation failed for %s: %s", manifest.name, exc)
        return deterministic_md
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


async def generate_steering_from_manifests(
    input_dir: str = "manifests",
    output_dir: str = "generated_steering",
    use_llm: bool = False,
) -> None:
    """Read all manifests and generate/update steering files."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    manifest_files = sorted(input_path.glob("*.service-manifest.yaml"))
    if not manifest_files:
        logger.error("No manifest files found in %s", input_path)
        return

    logger.info("Generating steering files from %d manifests (LLM: %s)", len(manifest_files), use_llm)

    for idx, mf in enumerate(manifest_files, 1):
        repo_name = mf.stem.replace(".service-manifest", "")
        logger.info("[%d/%d] Generating steering for: %s", idx, len(manifest_files), repo_name)

        try:
            # Load manifest
            raw = yaml.safe_load(mf.read_text(encoding="utf-8"))
            manifest = ServiceManifest.model_validate(raw)

            # Step 1: Deterministic render
            deterministic_md = render_steering_deterministic(manifest)

            # Step 2: Optional LLM enhancement
            if use_llm:
                final_md = await render_steering_with_llm(manifest, deterministic_md)
            else:
                final_md = deterministic_md

            # Save
            out_file = output_path / f"{repo_name}.md"
            out_file.write_text(final_md, encoding="utf-8")
            logger.info("  ✅ Saved: %s", out_file)

        except Exception as exc:
            logger.error("  ❌ Failed for %s: %s", repo_name, exc)

    logger.info("\nDone! Steering files written to: %s", output_path.resolve())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate steering files from manifests")
    parser.add_argument("--input", type=str, default="manifests", help="Manifests directory")
    parser.add_argument("--output", type=str, default="generated_steering", help="Output directory")
    parser.add_argument("--llm", action="store_true", help="Use LLM to enhance prose (costs tokens)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    asyncio.run(generate_steering_from_manifests(
        input_dir=args.input,
        output_dir=args.output,
        use_llm=args.llm,
    ))


if __name__ == "__main__":
    main()

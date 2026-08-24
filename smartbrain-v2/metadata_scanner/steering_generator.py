"""Steering file generation from repository metadata.

Supports two modes:
- Deterministic: renders templates populated with metadata facts
- LLM-enhanced: passes facts to GPT-4o for human-friendly prose
"""

from __future__ import annotations

import logging

from openai import AsyncAzureOpenAI

from config.settings import get_settings
from metadata_scanner.github_metadata import RepoMetadata
from webhook_pipeline.llm_analyzer import SteeringUpdate
from webhook_pipeline.steering_writer import write_steering_files

logger = logging.getLogger(__name__)


class SteeringGenerator:
    """Generate steering files from repository metadata.

    Two modes:
    - Deterministic: renders templates populated with metadata facts.
    - LLM-enhanced: passes facts to GPT-4o for human-friendly prose.
    """

    def __init__(self, use_llm: bool = False) -> None:
        self._use_llm = use_llm

    async def generate(self, repo_name: str, metadata: RepoMetadata) -> list[str]:
        """Generate 3 steering files and write to kiro_steering/{repo}/.

        Returns list of file paths written.
        """
        product_md = self._render_product(metadata)
        structure_md = self._render_structure(metadata)
        tech_md = self._render_tech(metadata)

        if self._use_llm:
            product_md = await self._enhance_with_llm(repo_name, "product", product_md)
            structure_md = await self._enhance_with_llm(repo_name, "structure", structure_md)
            tech_md = await self._enhance_with_llm(repo_name, "tech", tech_md)

        updates = [
            SteeringUpdate(file_type="product", content=product_md),
            SteeringUpdate(file_type="structure", content=structure_md),
            SteeringUpdate(file_type="tech", content=tech_md),
        ]
        return write_steering_files(repo_name, updates)

    def _render_product(self, metadata: RepoMetadata) -> str:
        """Deterministic product.md template."""
        lines = [
            f"# {metadata.name} — Product Context",
            "",
            "## Purpose",
            "",
        ]

        if metadata.readme:
            # Extract first paragraph from README as purpose
            readme_lines = metadata.readme.strip().split("\n")
            # Skip title line if it starts with #
            content_lines = [
                ln for ln in readme_lines if not ln.startswith("#") and ln.strip()
            ]
            purpose = " ".join(content_lines[:3]).strip()
            if purpose:
                lines.append(purpose)
            else:
                lines.append(f"Service: {metadata.name}")
        else:
            lines.append(f"Service: {metadata.name}")

        lines.extend(["", "## Contributors", ""])
        if metadata.contributors:
            for contributor in metadata.contributors[:5]:
                login = contributor.get("login", "unknown")
                contributions = contributor.get("contributions", 0)
                lines.append(f"- {login} ({contributions} contributions)")
        else:
            lines.append("- (no contributor data available)")

        if metadata.codeowners:
            lines.extend(["", "## Code Owners", "", f"```\n{metadata.codeowners}\n```"])

        lines.append("")
        return "\n".join(lines)

    def _render_structure(self, metadata: RepoMetadata) -> str:
        """Deterministic structure.md template."""
        lines = [
            f"# {metadata.name} — Code Structure",
            "",
            "## Directory Tree",
            "",
            "```",
        ]

        # Show top-level directories and key files
        seen_dirs: set[str] = set()
        for path in sorted(metadata.file_tree[:100]):
            parts = path.split("/")
            if len(parts) == 1:
                lines.append(path)
            elif parts[0] not in seen_dirs:
                seen_dirs.add(parts[0])
                lines.append(f"{parts[0]}/")

        if len(metadata.file_tree) > 100:
            lines.append(f"... ({len(metadata.file_tree)} total files)")

        lines.extend(["```", "", "## Key Modules", ""])

        # Identify key directories from tree
        top_dirs = sorted(
            {p.split("/")[0] for p in metadata.file_tree if "/" in p}
        )
        for d in top_dirs[:15]:
            lines.append(f"- `{d}/`")

        lines.extend(["", "## Recent Activity", ""])
        if metadata.recent_commits:
            for commit in metadata.recent_commits[:5]:
                msg = commit.get("commit", {}).get("message", "").split("\n")[0]
                sha = commit.get("sha", "")[:7]
                lines.append(f"- `{sha}` {msg}")
        else:
            lines.append("- (no recent commits)")

        lines.append("")
        return "\n".join(lines)

    def _render_tech(self, metadata: RepoMetadata) -> str:
        """Deterministic tech.md template."""
        lines = [
            f"# {metadata.name} — Tech Stack",
            "",
            "## Languages",
            "",
        ]

        if metadata.languages:
            total_bytes = sum(metadata.languages.values())
            for lang, bytes_count in sorted(
                metadata.languages.items(), key=lambda x: -x[1]
            ):
                pct = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                lines.append(f"- {lang}: {pct:.1f}%")
        else:
            lines.append("- (no language data available)")

        lines.extend(["", "## Build & Dependencies", ""])

        if metadata.build_manifest:
            for filename, content in metadata.build_manifest.items():
                lines.append(f"### {filename}")
                lines.append("")
                # Truncate large manifests
                truncated = content[:2000]
                if len(content) > 2000:
                    truncated += "\n... (truncated)"
                lines.append(f"```\n{truncated}\n```")
                lines.append("")
        else:
            lines.append("- (no build manifest found)")

        lines.extend(["", "## Configuration", ""])
        lines.append(f"- Default branch: `{metadata.default_branch}`")

        lines.append("")
        return "\n".join(lines)

    async def _enhance_with_llm(
        self, repo_name: str, file_type: str, content: str
    ) -> str:
        """Enhance a deterministic steering file with GPT-4o."""
        settings = get_settings()

        prompt = (
            f"Improve this {file_type}.md steering file for the '{repo_name}' "
            f"repository. Make it more readable and well-structured while "
            f"preserving ALL factual content. Return only the improved markdown.\n\n"
            f"{content}"
        )

        try:
            client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
            )
            response = await client.chat.completions.create(
                model=settings.azure_openai_deployment_gpt4o,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical documentation writer. "
                        "Improve the given steering file while preserving all facts.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=4000,
                timeout=60.0,
            )
            await client.close()
            return response.choices[0].message.content or content
        except Exception as exc:
            logger.warning(
                "LLM enhancement failed for %s/%s.md: %s", repo_name, file_type, exc
            )
            return content


__all__ = [
    "SteeringGenerator",
]

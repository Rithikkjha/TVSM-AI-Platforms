"""GPT-4o diff analysis for steering file updates.

Calls Azure OpenAI to determine whether a PR diff requires updates to
the repository's steering files (product.md, structure.md, tech.md).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from config.settings import get_settings
from webhook_pipeline.diff_extractor import ChangedFile, DiffResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class SteeringUpdate(BaseModel):
    """A single steering file update recommended by the LLM."""

    file_type: str  # "product", "structure", or "tech"
    content: str  # complete updated markdown


class AnalysisResult(BaseModel):
    """LLM analysis output indicating whether steering files need updates."""

    needs_update: bool
    reasoning: str
    updates: list[SteeringUpdate] = []
    error: str | None = None

    @property
    def has_changes(self) -> bool:
        """True when the LLM recommends at least one file update."""
        return self.needs_update and len(self.updates) > 0

    @property
    def updated_file_types(self) -> list[str]:
        """List of file types that have updates."""
        return [u.file_type for u in self.updates]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an engineering knowledge graph maintainer.
You analyze code diffs to determine if service steering documentation needs updating.

Steering files document a service's:
- product.md: purpose, domain, user stories, business context
- structure.md: code layout, key modules, directory tree, architecture patterns
- tech.md: tech stack, dependencies, APIs, databases, deployment config

Rules:
1. Only recommend updates when the diff MATERIALLY changes the service's architecture,
   dependencies, API surface, or purpose.
2. Minor refactors, test additions, and formatting changes do NOT warrant updates.
3. When updates are needed, provide the COMPLETE updated file content (not a patch).
4. Preserve all existing factual content — only ADD or MODIFY based on the diff.
"""

USER_PROMPT_TEMPLATE = """Repository: {repo_name}

## Current Steering Files

### product.md
{current_product_md}

### structure.md
{current_structure_md}

### tech.md
{current_tech_md}

## PR Diff (changed files)
{diff_content}

## Instructions
Analyze this diff and determine which (if any) steering files need updating.

Respond in this exact JSON format:
{{
  "needs_update": true/false,
  "reasoning": "brief explanation of why updates are/aren't needed",
  "updates": [
    {{
      "file_type": "product|structure|tech",
      "content": "complete updated markdown content"
    }}
  ]
}}
"""


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------


def _load_current_steering(steering_dir: Path) -> dict[str, str]:
    """Load existing steering files from disk for the prompt context."""
    files: dict[str, str] = {}
    for file_type in ("product", "structure", "tech"):
        md_file = steering_dir / f"{file_type}.md"
        if md_file.exists():
            files[file_type] = md_file.read_text(encoding="utf-8")
        else:
            files[file_type] = "(not yet created)"
    return files


def _format_diff_for_prompt(
    changed_files: list[ChangedFile], max_tokens: int = 6000
) -> str:
    """Format changed files into a string suitable for the LLM prompt.

    Truncates at approximately ``max_tokens`` (estimated at 4 chars/token)
    to stay within context budget.
    """
    char_budget = max_tokens * 4
    parts: list[str] = []
    total_chars = 0

    for f in changed_files:
        entry = f"### {f.path} ({f.status})\n```diff\n{f.patch}\n```\n"
        if total_chars + len(entry) > char_budget:
            parts.append(f"\n... (truncated — {len(changed_files) - len(parts)} more files)")
            break
        parts.append(entry)
        total_chars += len(entry)

    return "\n".join(parts) if parts else "(no diff content available)"


async def analyze_diff(diff_result: DiffResult, repo_name: str) -> AnalysisResult:
    """Call GPT-4o to analyze the diff and determine steering updates.

    Args:
        diff_result: Extracted PR diff data.
        repo_name: Repository name for prompt context.

    Returns:
        An :class:`AnalysisResult` with the LLM's recommendation.
    """
    settings = get_settings()
    steering_dir = Path(settings.kiro_steering_dir) / repo_name

    # Load current steering files
    current_files = _load_current_steering(steering_dir)

    # Build diff content (truncate to ~6000 tokens)
    diff_content = _format_diff_for_prompt(diff_result.changed_files, max_tokens=6000)

    # Call Azure OpenAI
    try:
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_key,
            api_version=settings.azure_openai_api_version,
        )
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        repo_name=repo_name,
                        current_product_md=current_files.get("product", ""),
                        current_structure_md=current_files.get("structure", ""),
                        current_tech_md=current_files.get("tech", ""),
                        diff_content=diff_content,
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=8000,
            response_format={"type": "json_object"},
            timeout=60.0,
        )
        await client.close()
        return _parse_llm_response(response)
    except Exception as exc:
        logger.exception("LLM analysis failed for %s", repo_name)
        return AnalysisResult(
            needs_update=False,
            reasoning="",
            updates=[],
            error=f"LLM analysis failed: {exc}",
        )


def _parse_llm_response(response: object) -> AnalysisResult:
    """Parse the Azure OpenAI chat response into an AnalysisResult."""
    try:
        content = response.choices[0].message.content  # type: ignore[union-attr]
        data = json.loads(content)
        updates = [
            SteeringUpdate(file_type=u["file_type"], content=u["content"])
            for u in data.get("updates", [])
        ]
        return AnalysisResult(
            needs_update=data.get("needs_update", False),
            reasoning=data.get("reasoning", ""),
            updates=updates,
        )
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Failed to parse LLM response: %s", exc)
        return AnalysisResult(
            needs_update=False,
            reasoning="",
            updates=[],
            error=f"Failed to parse LLM response: {exc}",
        )


__all__ = [
    "AnalysisResult",
    "SteeringUpdate",
    "analyze_diff",
]

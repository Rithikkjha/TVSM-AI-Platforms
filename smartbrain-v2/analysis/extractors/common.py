"""Common extractor — language-agnostic facts.

Handles:
- CODEOWNERS parsing → ownership
- Git activity (from commits API)
- README.md first paragraph → purpose
- Directory tree → code structure
- .env.example → env var names
- Dockerfile → ports, base image
- Key module docstrings → module descriptions
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from analysis.models.manifest import GitActivity, KeyModule

logger = logging.getLogger(__name__)


class CommonExtractor:
    """Extracts language-agnostic facts from a repository."""

    def extract_purpose(self, readme_content: str | None) -> str:
        """Extract the first meaningful paragraph from README as the service purpose."""
        if not readme_content:
            return ""

        lines = readme_content.split("\n")
        paragraph_lines: list[str] = []
        in_paragraph = False

        for line in lines:
            stripped = line.strip()
            # Skip headings, badges, empty lines, HTML tags at start
            if not in_paragraph:
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    continue
                if stripped.startswith("![") or stripped.startswith("[!["):
                    continue
                if stripped.startswith("<") and ("img" in stripped.lower() or "p>" in stripped.lower() or "div" in stripped.lower()):
                    continue
                if stripped.startswith("---") or stripped.startswith("==="):
                    continue
                if "badge" in stripped.lower() or "pipeline" in stripped.lower() or "build/status" in stripped.lower():
                    continue
                if stripped.startswith("|") and "---" in stripped:
                    continue
                # Must have actual text content (not just markup)
                clean = re.sub(r"<[^>]+>", "", stripped)  # strip HTML
                clean = re.sub(r"\[!\[.*?\]\(.*?\)\]", "", clean)  # strip badge markdown
                clean = clean.strip()
                if len(clean) < 10:
                    continue
                # Found start of first real paragraph
                in_paragraph = True

            if in_paragraph:
                if not stripped:
                    # End of paragraph
                    break
                if stripped.startswith("#"):
                    break
                if stripped.startswith("<") and ("img" in stripped.lower() or "/p>" in stripped.lower()):
                    continue
                # Strip HTML tags from content
                clean_line = re.sub(r"<[^>]+>", "", stripped).strip()
                if clean_line:
                    paragraph_lines.append(clean_line)

        purpose = " ".join(paragraph_lines)
        # Truncate if too long
        if len(purpose) > 500:
            purpose = purpose[:497] + "..."
        return purpose

    def extract_ownership(self, codeowners_content: str | None) -> tuple[str, list[str]]:
        """Parse CODEOWNERS file to extract team and contacts.

        Returns (team_name, [contact_emails_or_handles]).
        """
        if not codeowners_content:
            return "", []

        contacts: list[str] = []
        team = ""

        for line in codeowners_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # CODEOWNERS format: pattern @owner1 @owner2
            parts = line.split()
            for part in parts[1:]:  # skip the file pattern
                if part.startswith("@"):
                    owner = part.lstrip("@")
                    if "/" in owner:
                        # org/team-name format
                        team = owner.split("/")[-1]
                    else:
                        contacts.append(owner)

        return team, contacts

    def extract_ownership_from_contributors(
        self, contributors: list[dict[str, Any]]
    ) -> list[str]:
        """Fallback: extract top contributors as contacts."""
        contacts: list[str] = []
        for contrib in contributors[:5]:
            login = contrib.get("login", "")
            if login:
                contacts.append(login)
        return contacts

    def extract_git_activity(self, commits: list[dict[str, Any]]) -> GitActivity:
        """Extract git activity stats from commit history."""
        if not commits:
            return GitActivity()

        # Last commit
        last = commits[0]
        last_commit = last.get("commit", {})
        last_author = last.get("author", {}) or {}
        last_committer = last_commit.get("author", {}) or {}

        last_date = last_committer.get("date", "")[:10]
        last_author_name = last_author.get("login", "") or last_committer.get("name", "")
        last_message = last_commit.get("message", "").split("\n")[0][:100]

        # Active contributors in last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_authors: set[str] = set()
        recent_count = 0

        for commit in commits:
            commit_data = commit.get("commit", {})
            author_data = commit.get("author", {}) or {}
            date_str = commit_data.get("author", {}).get("date", "")

            try:
                commit_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if commit_date > thirty_days_ago:
                    recent_count += 1
                    login = author_data.get("login", "")
                    if login:
                        recent_authors.add(login)
            except (ValueError, TypeError):
                continue

        # Estimate frequency
        if recent_count > 0:
            weeks = 4.3  # ~30 days
            freq = f"~{int(recent_count / weeks)}/week"
        else:
            freq = "inactive"

        return GitActivity(
            last_commit_date=last_date,
            last_commit_author=last_author_name,
            last_commit_message=last_message,
            active_contributors_30d=sorted(recent_authors),
            commit_frequency=freq,
        )

    def extract_env_vars(self, env_example_content: str | None) -> list[str]:
        """Extract environment variable names from .env.example."""
        if not env_example_content:
            return []

        vars_found: list[str] = []
        for line in env_example_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^([A-Z][A-Z0-9_]+)\s*=", line)
            if match:
                vars_found.append(match.group(1))
        return vars_found

    def extract_key_modules(
        self, files: dict[str, str], language: str
    ) -> list[KeyModule]:
        """Extract key module descriptions from source file headers.

        Reads the first comment/docstring from files in key directories.
        """
        key_dirs = {
            "node": ["src/services/", "src/controllers/", "src/modules/", "src/routes/"],
            "java": ["src/main/java/", "src/main/kotlin/"],
            "dotnet": ["Controllers/", "Services/", "Handlers/"],
        }

        target_dirs = key_dirs.get(language, ["src/"])
        modules: list[KeyModule] = []

        for file_path, content in files.items():
            # Only look at files in key directories
            if not any(d in file_path for d in target_dirs):
                continue
            # Skip test files, index files
            if "test" in file_path.lower() or "spec" in file_path.lower():
                continue
            if file_path.endswith(("index.ts", "index.js", "__init__.py")):
                continue

            purpose = self._extract_file_purpose(content, language)
            if purpose:
                modules.append(KeyModule(file=file_path, purpose=purpose))

        # Limit to top 10 most interesting modules
        return modules[:10]

    def extract_domain_keywords(self, files: dict[str, str], language: str) -> list[str]:
        """Extract domain vocabulary from class/function/route names."""
        keywords: set[str] = set()

        for file_path, content in files.items():
            if "test" in file_path.lower() or "spec" in file_path.lower():
                continue
            if "node_modules" in file_path or "dist" in file_path:
                continue

            # Extract from class names, function names, route paths
            # CamelCase splitting
            camel_words = re.findall(r"[A-Z][a-z]+", content[:5000])
            for word in camel_words:
                w = word.lower()
                if len(w) > 3 and w not in _COMMON_WORDS:
                    keywords.add(w)

            # Route path segments
            route_segments = re.findall(r"/([a-z][\w-]+)", content[:5000])
            for seg in route_segments:
                if len(seg) > 3 and seg not in _COMMON_WORDS:
                    keywords.add(seg.lower())

        # Return top keywords by frequency (simplified: just return unique ones)
        return sorted(keywords)[:20]

    def _extract_file_purpose(self, content: str, language: str) -> str:
        """Extract the purpose/description from the first comment in a file."""
        lines = content.split("\n")[:15]  # Only look at first 15 lines

        if language == "node":
            # Look for JSDoc: /** ... */ or // description
            jsdoc_lines: list[str] = []
            in_jsdoc = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("/**"):
                    in_jsdoc = True
                    # Might have content on same line
                    after = stripped[3:].strip().rstrip("*/").strip()
                    if after:
                        jsdoc_lines.append(after)
                    continue
                if in_jsdoc:
                    if "*/" in stripped:
                        before = stripped.split("*/")[0].lstrip("* ").strip()
                        if before:
                            jsdoc_lines.append(before)
                        break
                    cleaned = stripped.lstrip("* ").strip()
                    if cleaned and not cleaned.startswith("@"):
                        jsdoc_lines.append(cleaned)

            if jsdoc_lines:
                return " ".join(jsdoc_lines)[:200]

            # Fallback: first // comment
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("//"):
                    comment = stripped[2:].strip()
                    if len(comment) > 10:
                        return comment[:200]

        elif language == "java":
            # Look for Javadoc
            jdoc_lines: list[str] = []
            in_jdoc = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("/**"):
                    in_jdoc = True
                    continue
                if in_jdoc:
                    if "*/" in stripped:
                        break
                    cleaned = stripped.lstrip("* ").strip()
                    if cleaned and not cleaned.startswith("@"):
                        jdoc_lines.append(cleaned)
            if jdoc_lines:
                return " ".join(jdoc_lines)[:200]

        return ""


# Common English words to exclude from domain keywords
_COMMON_WORDS = frozenset({
    "this", "that", "with", "from", "have", "been", "will", "would",
    "could", "should", "their", "there", "where", "when", "what",
    "which", "about", "after", "before", "between", "through",
    "string", "number", "boolean", "object", "array", "function",
    "return", "import", "export", "const", "class", "interface",
    "async", "await", "promise", "error", "response", "request",
    "module", "service", "controller", "model", "entity", "type",
    "index", "config", "utils", "helper", "common", "shared",
    "create", "update", "delete", "find", "list", "search",
    "true", "false", "null", "undefined", "void", "private",
    "public", "protected", "static", "abstract", "extends",
})

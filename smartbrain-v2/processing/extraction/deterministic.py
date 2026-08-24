"""Deterministic extraction for structured source data.

This module turns JSON payloads from GitHub, Jira, and Confluence MCP
servers into schema-valid :class:`ExtractedEntity` and
:class:`ExtractedRelationship` objects *without* calling any LLM.

The V1 design (see ``Graph_Extraction_Engine`` in the design doc)
mandates a two-tier extraction strategy:

* **Deterministic** (this module): direct field-to-schema mapping for
  anything structured — repository metadata, PR fields, ticket fields,
  CODEOWNERS files. Confidence is always ``"high"``.
* **LLM-backed** (``src/extraction/llm_extractor.py``): free-form text
  such as Confluence page bodies and PR descriptions.

All functions in this module are pure: no network I/O, no database
calls, no hidden global state. Given the same inputs (payload + an
optional injected ``now`` clock), they return the same
:class:`ExtractionResult`. That determinism is what makes Property 2
("Deterministic Extraction Correctness") testable and makes the
idempotency check in the write coordinator safe (Requirement 1.6,
Property 1).

The ``text_hash`` field on every produced entity is an SHA-256 of the
source payload, serialized with sorted JSON keys so semantically equal
payloads hash identically. The writer uses it to short-circuit
no-op writes when the source content hasn't changed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from storage.graph.schema import (
    EntityType,
    RelationshipType,
    is_valid_entity_type,
    is_valid_relationship,
    required_properties,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Confidence value assigned to every entity/relationship produced by
#: deterministic extraction. LLM extractors pick from a wider range
#: (``"high" | "medium" | "low"``); structured-field extraction is
#: always maximally confident (Requirement 1.9).
DETERMINISTIC_CONFIDENCE: str = "high"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractedEntity:
    """A schema-valid entity produced by an extractor.

    Instances are frozen so they can be safely passed across async
    boundaries and accumulated into result lists without worrying
    about in-place mutation. The ``properties`` dict itself is still
    mutable (Python can't deep-freeze dicts), but by convention
    extractors build it once and don't mutate it after construction.

    Validation happens in :meth:`__post_init__`:

    * ``label`` must be a known V1 entity type.
    * ``properties`` must include all fields required for that label
      (see :func:`~src.models.schema.required_properties`), plus a
      non-empty ``source_id`` and a ``text_hash``.
    """

    label: str
    properties: dict[str, Any]
    confidence: str = DETERMINISTIC_CONFIDENCE

    def __post_init__(self) -> None:
        if not is_valid_entity_type(self.label):
            raise ValueError(f"Unknown entity label: {self.label!r}")
        missing = required_properties(self.label) - self.properties.keys()
        if missing:
            raise ValueError(
                f"Entity {self.label!r} missing required properties: {sorted(missing)}"
            )
        source_id = self.properties.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("Entity must have a non-empty 'source_id' string")
        if "text_hash" not in self.properties:
            raise ValueError("Entity must have a 'text_hash' property")


@dataclass(frozen=True)
class ExtractedRelationship:
    """A schema-valid relationship produced by an extractor.

    The triple ``(source_label, rel_type, target_label)`` is validated
    against the V1 whitelist at construction time. Endpoints are
    identified by ``source_id`` values; the writer is responsible for
    confirming those entities exist in the graph before materializing
    the edge (Property 4: Referential Integrity).
    """

    source_label: str
    source_id: str
    target_label: str
    target_id: str
    rel_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: str = DETERMINISTIC_CONFIDENCE

    def __post_init__(self) -> None:
        if not is_valid_relationship(self.source_label, self.rel_type, self.target_label):
            raise ValueError(
                f"Invalid relationship triple: "
                f"({self.source_label!r})-[:{self.rel_type}]->({self.target_label!r})"
            )
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("Relationship source_id must be a non-empty string")
        if not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("Relationship target_id must be a non-empty string")


@dataclass
class ExtractionResult:
    """Aggregate output of a single extractor call.

    Extractors return zero-or-more entities and zero-or-more
    relationships in a single structure so the MCP orchestrator can
    treat all extraction outputs uniformly. The :meth:`merge` helper
    lets callers combine results from multiple extractors (e.g. the
    repository extractor plus a CODEOWNERS extractor on the same repo)
    before handing them off to the writer.
    """

    entities: list[ExtractedEntity] = field(default_factory=list)
    relationships: list[ExtractedRelationship] = field(default_factory=list)

    def merge(self, other: ExtractionResult) -> ExtractionResult:
        """Return a new result containing entities/relationships from both.

        The operation is non-mutating: neither ``self`` nor ``other``
        is modified. Order is preserved — entries from ``self`` come
        before entries from ``other``.
        """

        return ExtractionResult(
            entities=[*self.entities, *other.entities],
            relationships=[*self.relationships, *other.relationships],
        )


# ---------------------------------------------------------------------------
# Hashing + timestamp helpers
# ---------------------------------------------------------------------------


def compute_text_hash(content: str | dict[str, Any]) -> str:
    """Return a stable SHA-256 hex digest for ``content``.

    Strings are hashed as UTF-8 bytes. Dicts are first serialized with
    ``json.dumps(..., sort_keys=True, default=str)`` so that two dicts
    with the same entries in different insertion orders — or containing
    datetime values that round-trip through ``str()`` identically —
    produce the same hash.

    This hash is the second half of the idempotency key alongside
    ``source_id`` (Requirement 1.6): re-ingesting the same payload
    must yield the same hash so the writer can detect "no content
    change" and skip the write.
    """

    if isinstance(content, dict):
        serialized = json.dumps(content, sort_keys=True, default=str, ensure_ascii=False)
    else:
        serialized = content
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_now(now: datetime | None) -> str:
    """Return an ISO-8601 UTC timestamp.

    If ``now`` is provided, it's used verbatim (allowing tests and
    batch jobs to inject a deterministic clock). Otherwise the current
    UTC time is computed. Callers should prefer supplying the source
    system's own ``updated_at`` when available — ``_resolve_now`` is
    the fallback for payloads missing that field.
    """

    if now is None:
        now = datetime.now(UTC)
    return now.isoformat()


def _prefer_source_timestamp(source_value: Any, now: datetime | None) -> str:
    """Return ``source_value`` if it's a non-empty string, else ``_resolve_now(now)``."""

    if isinstance(source_value, str) and source_value:
        return source_value
    return _resolve_now(now)


# ---------------------------------------------------------------------------
# Extractor: Repository (GitHub)
# ---------------------------------------------------------------------------


def extract_repository(
    github_repo_data: dict[str, Any],
    now: datetime | None = None,
) -> ExtractionResult:
    """Extract Repository + Service entities from a GitHub repo payload.

    A GitHub repository is modelled as both a :class:`Repository`
    (source-system artifact) and a :class:`Service` (logical unit of
    ownership in the engineering graph), connected by a ``CONTAINS``
    edge. The Service's ``source_id`` uses the repo name so that PRs,
    tickets, and Confluence pages can reference the same service
    without knowing the numeric GitHub repo id.

    The payload is expected to carry at least ``id`` and ``name``;
    other fields (``full_name``, ``html_url``, ``default_branch``,
    ``language``, ``updated_at``) populate optional properties and
    fall back to sensible defaults when missing.
    """

    repo_id = github_repo_data["id"]
    name = github_repo_data["name"]
    url = github_repo_data.get("html_url", "")
    default_branch = github_repo_data.get("default_branch", "main")
    language = github_repo_data.get("language", "") or ""

    updated_at = _prefer_source_timestamp(github_repo_data.get("updated_at"), now)
    created_at = _prefer_source_timestamp(github_repo_data.get("created_at"), now) or updated_at
    if not created_at:
        created_at = updated_at

    text_hash = compute_text_hash(github_repo_data)
    repo_source_id = f"github:repo:{repo_id}"
    service_source_id = f"service:{name}"

    repo_entity = ExtractedEntity(
        label=EntityType.REPOSITORY.value,
        properties={
            "source_id": repo_source_id,
            "name": name,
            "url": url,
            "default_branch": default_branch,
            "language": language,
            "created_at": created_at,
            "updated_at": updated_at,
            "text_hash": text_hash,
        },
    )

    # The Service hash is derived only from the repo name so that later
    # Confluence/PR updates that rename fields inside the repo payload
    # don't churn the Service node.
    service_entity = ExtractedEntity(
        label=EntityType.SERVICE.value,
        properties={
            "source_id": service_source_id,
            "name": name,
            "created_at": created_at,
            "updated_at": updated_at,
            "text_hash": compute_text_hash({"service_name": name}),
        },
    )

    contains_rel = ExtractedRelationship(
        source_label=EntityType.REPOSITORY.value,
        source_id=repo_source_id,
        target_label=EntityType.SERVICE.value,
        target_id=service_source_id,
        rel_type=RelationshipType.CONTAINS.value,
        properties={"created_at": created_at},
    )

    return ExtractionResult(
        entities=[repo_entity, service_entity],
        relationships=[contains_rel],
    )


# ---------------------------------------------------------------------------
# Extractor: PR (GitHub)
# ---------------------------------------------------------------------------


def extract_pr(
    github_pr_data: dict[str, Any],
    repo_source_id: str,
    now: datetime | None = None,
) -> ExtractionResult:
    """Extract a PR entity, its author (Person), and a MODIFIES edge.

    The PR ``source_id`` embeds the repo identifier so that PR numbers
    from different repos don't collide. ``repo_source_id`` is the
    canonical id of the owning repository (produced by
    :func:`extract_repository`). If the PR payload includes a
    ``user.login``, a :class:`Person` entity is emitted for the author
    so downstream queries can join PRs to people.

    ``merged_at`` is included only when present on the payload — open
    PRs legitimately have no merge timestamp, and stamping a ``null``
    would conflict with Neo4j property semantics.
    """

    number = github_pr_data["number"]
    title = github_pr_data["title"]
    state = github_pr_data.get("state", "open")
    body = github_pr_data.get("body") or ""
    url = github_pr_data.get("html_url", "")

    user = github_pr_data.get("user") or {}
    author_login = user.get("login", "") if isinstance(user, dict) else ""

    updated_at = _prefer_source_timestamp(github_pr_data.get("updated_at"), now)
    created_at = _prefer_source_timestamp(github_pr_data.get("created_at"), now) or updated_at
    merged_at = github_pr_data.get("merged_at")

    text_hash = compute_text_hash(github_pr_data)

    # Strip the ``github:repo:`` prefix so the PR id reads as
    # ``github:pr:<repo-token>/<number>`` rather than double-prefixing.
    repo_token = repo_source_id.removeprefix("github:repo:")
    pr_source_id = f"github:pr:{repo_token}/{number}"

    pr_props: dict[str, Any] = {
        "source_id": pr_source_id,
        "number": number,
        "title": title,
        "state": state,
        "description": body,
        "url": url,
        "author": author_login,
        "created_at": created_at,
        "updated_at": updated_at,
        "text_hash": text_hash,
    }
    if isinstance(merged_at, str) and merged_at:
        pr_props["merged_at"] = merged_at

    entities: list[ExtractedEntity] = [
        ExtractedEntity(label=EntityType.PR.value, properties=pr_props)
    ]
    relationships: list[ExtractedRelationship] = [
        ExtractedRelationship(
            source_label=EntityType.PR.value,
            source_id=pr_source_id,
            target_label=EntityType.REPOSITORY.value,
            target_id=repo_source_id,
            rel_type=RelationshipType.MODIFIES.value,
            properties={"created_at": created_at},
        )
    ]

    if author_login:
        person_source_id = f"github:user:{author_login}"
        person_entity = ExtractedEntity(
            label=EntityType.PERSON.value,
            properties={
                "source_id": person_source_id,
                "name": user.get("name") or author_login,
                "github_username": author_login,
                "created_at": created_at,
                "updated_at": updated_at,
                "text_hash": compute_text_hash({"github_login": author_login}),
            },
        )
        entities.append(person_entity)

    return ExtractionResult(entities=entities, relationships=relationships)


# ---------------------------------------------------------------------------
# Extractor: Ticket (Jira)
# ---------------------------------------------------------------------------


def _flatten_adf(value: Any) -> str:
    """Flatten an Atlassian Document Format (ADF) node tree to plain text.

    Jira's REST API v3 returns ``description`` (and other rich-text
    fields) as ADF JSON rather than the plain-string representation
    used by API v2. Neo4j property values can only be primitives or
    homogeneous lists of primitives, so storing the dict verbatim
    raises a driver error. Flattening to a string preserves the
    paragraph text while discarding the structural metadata that
    the graph doesn't need.

    If ``value`` is already a string, it's returned unchanged. If
    it's ``None`` or an empty container, the empty string is
    returned. Unknown node shapes degrade to ``str(value)``.
    """

    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_adf(item) for item in value).strip()
    if isinstance(value, dict):
        # Leaf text node.
        text = value.get("text")
        if isinstance(text, str):
            return text
        content = value.get("content")
        if isinstance(content, list):
            return _flatten_adf(content)
        return ""
    return str(value)


def _extract_jira_issue(
    jira_issue_data: dict[str, Any],
    label: EntityType,
    now: datetime | None = None,
) -> ExtractionResult:
    """Shared body for :func:`extract_ticket` and :func:`extract_epic`.

    Epics and Tickets share almost all of Jira's issue shape; only
    the label differs at the graph level. Keeping the mapping in one
    place ensures both paths stay in lockstep as the Jira schema
    evolves.
    """

    key = jira_issue_data["key"]
    fields = jira_issue_data.get("fields") or {}
    title = fields.get("summary", "") or ""
    status_obj = fields.get("status") or {}
    status = status_obj.get("name", "") if isinstance(status_obj, dict) else ""
    priority_obj = fields.get("priority") or {}
    priority = priority_obj.get("name", "") if isinstance(priority_obj, dict) else ""
    # Jira v3 returns ADF JSON for rich-text fields; flatten to a plain
    # string so it's Neo4j-serializable.
    description = _flatten_adf(fields.get("description"))

    updated_at = _prefer_source_timestamp(fields.get("updated"), now)
    created_at = _prefer_source_timestamp(fields.get("created"), now) or updated_at

    text_hash = compute_text_hash(jira_issue_data)
    prefix = "jira:epic" if label is EntityType.EPIC else "jira:ticket"
    issue_source_id = f"{prefix}:{key}"

    issue_props: dict[str, Any] = {
        "source_id": issue_source_id,
        "key": key,
        "title": title,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "text_hash": text_hash,
    }
    # Priority isn't part of Epic's schema but keeping the field
    # doesn't hurt; the writer will pass it through.
    if priority:
        issue_props["priority"] = priority
    if description and label is EntityType.TICKET:
        issue_props["description"] = description

    entities: list[ExtractedEntity] = [
        ExtractedEntity(label=label.value, properties=issue_props)
    ]

    assignee = fields.get("assignee")
    if isinstance(assignee, dict) and assignee:
        account_id = assignee.get("accountId") or ""
        display_name = assignee.get("displayName") or ""
        email = assignee.get("emailAddress") or ""
        if account_id:
            person_source_id = f"jira:user:{account_id}"
            person_entity = ExtractedEntity(
                label=EntityType.PERSON.value,
                properties={
                    "source_id": person_source_id,
                    "name": display_name or account_id,
                    "email": email,
                    "jira_username": account_id,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "text_hash": compute_text_hash(
                        {"jira_account_id": account_id}
                    ),
                },
            )
            entities.append(person_entity)

    return ExtractionResult(entities=entities)


def extract_ticket(
    jira_issue_data: dict[str, Any],
    now: datetime | None = None,
) -> ExtractionResult:
    """Extract a Ticket entity (and assignee Person, if present).

    Deterministic extraction only uses explicit fields — it does not
    infer service links from the free-form description. The LLM
    extractor is responsible for that (``src/extraction/llm_extractor.py``).
    """

    return _extract_jira_issue(jira_issue_data, EntityType.TICKET, now=now)


def extract_epic(
    jira_epic_data: dict[str, Any],
    now: datetime | None = None,
) -> ExtractionResult:
    """Extract an Epic entity (and assignee Person, if present).

    The Epic shape mirrors :class:`Ticket`; the only graph-level
    difference is the label, which lets queries distinguish strategic
    work (Epics) from delivery tickets.
    """

    return _extract_jira_issue(jira_epic_data, EntityType.EPIC, now=now)


# ---------------------------------------------------------------------------
# Extractor: Confluence page metadata
# ---------------------------------------------------------------------------


def extract_confluence_page_metadata(
    page_data: dict[str, Any],
    now: datetime | None = None,
    base_url: str | None = None,
) -> ExtractionResult:
    """Extract a :class:`ConfluencePage` from a page metadata payload.

    Only the *metadata* (id, title, space key, URL) is extracted here
    — semantic analysis of the page body (service mentions,
    ownership claims) is explicitly deferred to the LLM extractor.

    Args:
        page_data: Raw page payload from Confluence REST API.
        now: Optional fallback timestamp when source timestamps are missing.
        base_url: Optional Confluence site base URL (e.g.
            ``https://foo.atlassian.net/wiki``). When provided, the
            ``webui`` relative link returned by Confluence is resolved
            to an absolute URL so it is safe to surface directly to
            users. When ``None``, the raw relative link is preserved
            for backward compatibility.
    """

    page_id = page_data["id"]
    title = page_data.get("title", "") or ""
    space = page_data.get("space") or {}
    space_key = space.get("key", "") if isinstance(space, dict) else ""
    links = page_data.get("_links") or {}
    webui = links.get("webui", "") if isinstance(links, dict) else ""
    # Resolve to absolute URL when base_url is supplied so downstream
    # consumers (LLM, UI) can hand the URL straight to a browser.
    if webui and base_url:
        url = f"{base_url.rstrip('/')}{webui}" if webui.startswith("/") else webui
    else:
        url = webui

    version = page_data.get("version") or {}
    version_when = version.get("when") if isinstance(version, dict) else None
    updated_at = _prefer_source_timestamp(version_when, now)
    created_at = _prefer_source_timestamp(page_data.get("created"), now) or updated_at

    text_hash = compute_text_hash(page_data)
    page_source_id = f"confluence:page:{page_id}"

    entity = ExtractedEntity(
        label=EntityType.CONFLUENCE_PAGE.value,
        properties={
            "source_id": page_source_id,
            "title": title,
            "space_key": space_key,
            "url": url,
            "created_at": created_at,
            "updated_at": updated_at,
            "text_hash": text_hash,
        },
    )

    return ExtractionResult(entities=[entity])


# ---------------------------------------------------------------------------
# Extractor: CODEOWNERS
# ---------------------------------------------------------------------------


def _parse_codeowners_lines(codeowners_text: str) -> list[str]:
    """Return the sorted set of unique ``@``-prefixed owners in the file.

    The parser handles:

    * Full-line comments (``# ...``) and inline comments (``foo # bar``).
    * Blank lines.
    * Mixed whitespace (tabs, multiple spaces).
    * Non-owner tokens on a line (e.g. file-pattern entries like
      ``*.md`` that show up before the owners).

    Owners are returned with the leading ``@`` stripped, deduplicated,
    and sorted for deterministic downstream output.
    """

    owners: set[str] = set()
    for raw_line in codeowners_text.splitlines():
        # Drop inline comments before tokenizing so "#" in a URL-style
        # owner would still tokenize correctly (CODEOWNERS doesn't
        # allow "#" in owners, so this is safe).
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        # First token is the file pattern; remaining tokens are owners.
        for token in tokens[1:]:
            if token.startswith("@") and len(token) > 1:
                owners.add(token.lstrip("@"))
    return sorted(owners)


def extract_codeowners(
    codeowners_text: str,
    repo_source_id: str,
    now: datetime | None = None,
) -> ExtractionResult:
    """Extract Team entities + OWNED_BY edges from a CODEOWNERS file.

    The extractor is conservative: every ``@``-prefixed owner becomes
    a :class:`Team` (the V1 schema only allows ``OWNED_BY`` to target
    Teams, and GitHub's ``@org/name`` team syntax is the intended
    pattern). Individual ``@username`` entries are still modelled as
    Teams of size one rather than dropped on the floor — doing so
    keeps the ownership graph complete for small repos that use
    personal ownership.

    A single file generally produces one OWNED_BY edge per unique
    owner; duplicate mentions across multiple path rules collapse.
    """

    if not isinstance(repo_source_id, str) or not repo_source_id:
        raise ValueError("extract_codeowners requires a non-empty repo_source_id")

    owners = _parse_codeowners_lines(codeowners_text)
    if not owners:
        return ExtractionResult()

    resolved_now = _resolve_now(now)

    entities: list[ExtractedEntity] = []
    relationships: list[ExtractedRelationship] = []

    for team_name in owners:
        team_source_id = f"team:{team_name}"
        team_entity = ExtractedEntity(
            label=EntityType.TEAM.value,
            properties={
                "source_id": team_source_id,
                "name": team_name,
                "created_at": resolved_now,
                "updated_at": resolved_now,
                "text_hash": compute_text_hash({"team_name": team_name}),
            },
        )
        entities.append(team_entity)

        relationships.append(
            ExtractedRelationship(
                source_label=EntityType.REPOSITORY.value,
                source_id=repo_source_id,
                target_label=EntityType.TEAM.value,
                target_id=team_source_id,
                rel_type=RelationshipType.OWNED_BY.value,
                properties={"created_at": resolved_now},
            )
        )

    return ExtractionResult(entities=entities, relationships=relationships)


__all__ = [
    "DETERMINISTIC_CONFIDENCE",
    "ExtractedEntity",
    "ExtractedRelationship",
    "ExtractionResult",
    "compute_text_hash",
    "extract_codeowners",
    "extract_confluence_page_metadata",
    "extract_epic",
    "extract_pr",
    "extract_repository",
    "extract_ticket",
]

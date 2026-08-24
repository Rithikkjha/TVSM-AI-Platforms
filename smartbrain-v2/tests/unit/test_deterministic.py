"""Unit tests for :mod:`src.extraction.deterministic`.

These tests pin down the deterministic extractor contract: the
shape/content of :class:`ExtractionResult` given representative
structured payloads from GitHub and Jira, the idempotency of
:func:`compute_text_hash`, and the CODEOWNERS parser's handling of
the syntactic corner cases the pilot is likely to encounter.

Property-based tests for the universal extractor invariants
(Property 2: Deterministic Extraction Correctness) live separately
under ``tests/properties/`` and are tracked as optional subtasks in
the spec.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from processing.extraction.deterministic import (
    DETERMINISTIC_CONFIDENCE,
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
    compute_text_hash,
    extract_codeowners,
    extract_confluence_page_metadata,
    extract_epic,
    extract_pr,
    extract_repository,
    extract_ticket,
)
from storage.graph.schema import EntityType, RelationshipType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXED_NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


def _entity_by_label(result: ExtractionResult, label: str) -> ExtractedEntity:
    """Return the first entity with ``label`` or fail the test."""

    for entity in result.entities:
        if entity.label == label:
            return entity
    pytest.fail(f"No entity with label {label!r} in result")


# ---------------------------------------------------------------------------
# compute_text_hash
# ---------------------------------------------------------------------------


def test_compute_text_hash_is_deterministic_for_strings() -> None:
    """Same string input produces the same hash across calls."""

    assert compute_text_hash("hello") == compute_text_hash("hello")


def test_compute_text_hash_differs_for_different_strings() -> None:
    assert compute_text_hash("hello") != compute_text_hash("hello!")


def test_compute_text_hash_is_deterministic_for_dicts() -> None:
    """Dicts with the same entries hash the same regardless of key order."""

    a: dict[str, Any] = {"name": "payments", "id": 1}
    b: dict[str, Any] = {"id": 1, "name": "payments"}
    assert compute_text_hash(a) == compute_text_hash(b)


def test_compute_text_hash_differs_for_different_dicts() -> None:
    assert compute_text_hash({"id": 1}) != compute_text_hash({"id": 2})


def test_compute_text_hash_returns_sha256_hex_length() -> None:
    """SHA-256 hex digests are always 64 chars."""

    assert len(compute_text_hash("x")) == 64


# ---------------------------------------------------------------------------
# ExtractionResult.merge
# ---------------------------------------------------------------------------


def test_extraction_result_merge_concatenates_entities_and_relationships() -> None:
    repo_result = extract_repository(
        {"id": 1, "name": "svc-a"},
        now=FIXED_NOW,
    )
    codeowners_result = extract_codeowners(
        "* @org/platform-team\n",
        repo_source_id="github:repo:1",
        now=FIXED_NOW,
    )
    merged = repo_result.merge(codeowners_result)

    assert len(merged.entities) == len(repo_result.entities) + len(codeowners_result.entities)
    assert len(merged.relationships) == len(repo_result.relationships) + len(
        codeowners_result.relationships
    )
    # Order: self's entries first, then other's.
    assert merged.entities[: len(repo_result.entities)] == repo_result.entities
    assert merged.relationships[: len(repo_result.relationships)] == repo_result.relationships


def test_extraction_result_merge_does_not_mutate_inputs() -> None:
    a = ExtractionResult(
        entities=[], relationships=[]
    )
    b = ExtractionResult(
        entities=[], relationships=[]
    )
    a_entities_before = list(a.entities)
    b_entities_before = list(b.entities)
    a.merge(b)
    assert a.entities == a_entities_before
    assert b.entities == b_entities_before


# ---------------------------------------------------------------------------
# extract_repository
# ---------------------------------------------------------------------------


def _sample_github_repo() -> dict[str, Any]:
    return {
        "id": 12345,
        "name": "payments-service",
        "full_name": "org/payments-service",
        "html_url": "https://github.com/org/payments-service",
        "default_branch": "main",
        "language": "Python",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-10T10:00:00Z",
    }


def test_extract_repository_produces_repository_and_service_and_contains_edge() -> None:
    result = extract_repository(_sample_github_repo(), now=FIXED_NOW)

    assert len(result.entities) == 2
    assert len(result.relationships) == 1

    repo = _entity_by_label(result, EntityType.REPOSITORY.value)
    svc = _entity_by_label(result, EntityType.SERVICE.value)
    rel = result.relationships[0]

    assert repo.properties["source_id"] == "github:repo:12345"
    assert repo.properties["name"] == "payments-service"
    assert repo.properties["url"] == "https://github.com/org/payments-service"
    assert repo.properties["default_branch"] == "main"
    assert repo.properties["language"] == "Python"
    assert repo.properties["updated_at"] == "2024-01-10T10:00:00Z"
    assert "text_hash" in repo.properties

    assert svc.properties["source_id"] == "service:payments-service"
    assert svc.properties["name"] == "payments-service"

    assert rel.rel_type == RelationshipType.CONTAINS.value
    assert rel.source_label == EntityType.REPOSITORY.value
    assert rel.target_label == EntityType.SERVICE.value
    assert rel.source_id == "github:repo:12345"
    assert rel.target_id == "service:payments-service"


def test_extract_repository_is_deterministic_across_invocations() -> None:
    payload = _sample_github_repo()
    r1 = extract_repository(payload, now=FIXED_NOW)
    r2 = extract_repository(payload, now=FIXED_NOW)

    assert [e.properties for e in r1.entities] == [e.properties for e in r2.entities]
    assert r1.relationships == r2.relationships


def test_extract_repository_all_entities_have_high_confidence() -> None:
    result = extract_repository(_sample_github_repo(), now=FIXED_NOW)
    for entity in result.entities:
        assert entity.confidence == DETERMINISTIC_CONFIDENCE


def test_extract_repository_falls_back_to_now_when_timestamps_missing() -> None:
    payload = {"id": 1, "name": "svc"}
    result = extract_repository(payload, now=FIXED_NOW)
    repo = _entity_by_label(result, EntityType.REPOSITORY.value)
    assert repo.properties["updated_at"] == FIXED_NOW.isoformat()


# ---------------------------------------------------------------------------
# extract_pr
# ---------------------------------------------------------------------------


def _sample_github_pr(merged: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "number": 42,
        "title": "Fix payment retry timeout",
        "state": "closed" if merged else "open",
        "body": "Adjusts retry backoff to 500ms.",
        "html_url": "https://github.com/org/payments-service/pull/42",
        "user": {"login": "alice", "name": "Alice Smith"},
        "created_at": "2024-01-05T09:00:00Z",
        "updated_at": "2024-01-06T11:00:00Z",
    }
    if merged:
        payload["merged_at"] = "2024-01-06T12:00:00Z"
    return payload


def test_extract_pr_with_merged_pr_includes_merged_at_and_person() -> None:
    result = extract_pr(
        _sample_github_pr(merged=True),
        repo_source_id="github:repo:12345",
        now=FIXED_NOW,
    )

    pr = _entity_by_label(result, EntityType.PR.value)
    person = _entity_by_label(result, EntityType.PERSON.value)

    assert pr.properties["source_id"] == "github:pr:12345/42"
    assert pr.properties["number"] == 42
    assert pr.properties["title"] == "Fix payment retry timeout"
    assert pr.properties["state"] == "closed"
    assert pr.properties["merged_at"] == "2024-01-06T12:00:00Z"
    assert pr.properties["author"] == "alice"

    assert person.properties["source_id"] == "github:user:alice"
    assert person.properties["github_username"] == "alice"
    assert person.properties["name"] == "Alice Smith"

    # MODIFIES edge from PR to repo
    assert len(result.relationships) == 1
    rel = result.relationships[0]
    assert rel.rel_type == RelationshipType.MODIFIES.value
    assert rel.source_id == "github:pr:12345/42"
    assert rel.target_id == "github:repo:12345"


def test_extract_pr_without_merged_at_omits_property() -> None:
    result = extract_pr(
        _sample_github_pr(merged=False),
        repo_source_id="github:repo:12345",
        now=FIXED_NOW,
    )
    pr = _entity_by_label(result, EntityType.PR.value)
    assert "merged_at" not in pr.properties
    assert pr.properties["state"] == "open"


def test_extract_pr_without_author_omits_person() -> None:
    payload = _sample_github_pr(merged=False)
    payload["user"] = None
    result = extract_pr(
        payload,
        repo_source_id="github:repo:12345",
        now=FIXED_NOW,
    )
    # Only the PR entity — no Person.
    assert [e.label for e in result.entities] == [EntityType.PR.value]


# ---------------------------------------------------------------------------
# extract_ticket
# ---------------------------------------------------------------------------


def _sample_jira_ticket(with_assignee: bool = True) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "summary": "Fix timeout on payment retry",
        "status": {"name": "In Progress"},
        "priority": {"name": "High"},
        "description": "Retries are hitting a 30s timeout...",
        "project": {"key": "ENG"},
        "created": "2024-01-03T08:00:00Z",
        "updated": "2024-01-12T14:00:00Z",
    }
    if with_assignee:
        fields["assignee"] = {
            "accountId": "acc-123",
            "displayName": "Bob Jones",
            "emailAddress": "bob@example.com",
        }
    return {"key": "ENG-1234", "fields": fields}


def test_extract_ticket_with_assignee_produces_ticket_and_person() -> None:
    result = extract_ticket(_sample_jira_ticket(with_assignee=True), now=FIXED_NOW)

    ticket = _entity_by_label(result, EntityType.TICKET.value)
    person = _entity_by_label(result, EntityType.PERSON.value)

    assert ticket.properties["source_id"] == "jira:ticket:ENG-1234"
    assert ticket.properties["key"] == "ENG-1234"
    assert ticket.properties["title"] == "Fix timeout on payment retry"
    assert ticket.properties["status"] == "In Progress"
    assert ticket.properties["priority"] == "High"
    assert ticket.properties["description"] == "Retries are hitting a 30s timeout..."
    assert ticket.properties["updated_at"] == "2024-01-12T14:00:00Z"

    assert person.properties["source_id"] == "jira:user:acc-123"
    assert person.properties["jira_username"] == "acc-123"
    assert person.properties["email"] == "bob@example.com"
    assert person.properties["name"] == "Bob Jones"


def test_extract_ticket_without_assignee_omits_person() -> None:
    result = extract_ticket(_sample_jira_ticket(with_assignee=False), now=FIXED_NOW)
    assert [e.label for e in result.entities] == [EntityType.TICKET.value]
    # No relationships for tickets via deterministic extraction.
    assert result.relationships == []


def test_extract_ticket_is_deterministic() -> None:
    payload = _sample_jira_ticket(with_assignee=True)
    r1 = extract_ticket(payload, now=FIXED_NOW)
    r2 = extract_ticket(payload, now=FIXED_NOW)
    assert [e.properties for e in r1.entities] == [e.properties for e in r2.entities]


# ---------------------------------------------------------------------------
# extract_epic
# ---------------------------------------------------------------------------


def test_extract_epic_produces_epic_entity_with_correct_source_id() -> None:
    payload = {
        "key": "ENG-100",
        "fields": {
            "summary": "Payment Platform Rewrite",
            "status": {"name": "In Progress"},
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-14T00:00:00Z",
        },
    }
    result = extract_epic(payload, now=FIXED_NOW)

    epic = _entity_by_label(result, EntityType.EPIC.value)
    assert epic.properties["source_id"] == "jira:epic:ENG-100"
    assert epic.properties["key"] == "ENG-100"
    assert epic.properties["title"] == "Payment Platform Rewrite"
    assert epic.properties["status"] == "In Progress"
    # Epic schema does not require ``description``; we omit it to
    # avoid carrying stale text across syncs.
    assert "description" not in epic.properties


# ---------------------------------------------------------------------------
# extract_confluence_page_metadata
# ---------------------------------------------------------------------------


def test_extract_confluence_page_metadata_produces_page_entity() -> None:
    payload = {
        "id": "98765",
        "title": "Payments Architecture",
        "space": {"key": "ENG"},
        "_links": {"webui": "/spaces/ENG/pages/98765"},
        "version": {"when": "2024-01-08T10:00:00Z"},
    }
    result = extract_confluence_page_metadata(payload, now=FIXED_NOW)

    assert len(result.entities) == 1
    assert result.relationships == []

    page = result.entities[0]
    assert page.label == EntityType.CONFLUENCE_PAGE.value
    assert page.properties["source_id"] == "confluence:page:98765"
    assert page.properties["title"] == "Payments Architecture"
    assert page.properties["space_key"] == "ENG"
    assert page.properties["url"] == "/spaces/ENG/pages/98765"
    assert page.properties["updated_at"] == "2024-01-08T10:00:00Z"


def test_extract_confluence_page_metadata_does_not_emit_service_links() -> None:
    """Deterministic extraction must not infer service mentions from page bodies."""

    payload = {
        "id": "1",
        "title": "Mentions payments-service and order-service",
        "body": {"storage": {"value": "<p>payments-service depends on order-service</p>"}},
    }
    result = extract_confluence_page_metadata(payload, now=FIXED_NOW)
    # Only the page entity; no service linking.
    assert [e.label for e in result.entities] == [EntityType.CONFLUENCE_PAGE.value]
    assert result.relationships == []


# ---------------------------------------------------------------------------
# extract_codeowners
# ---------------------------------------------------------------------------


def test_extract_codeowners_parses_org_team_syntax() -> None:
    text = """# Global owner
* @org/platform-team

# Service owner
/src/ @org/payments-team
"""
    result = extract_codeowners(text, repo_source_id="github:repo:12345", now=FIXED_NOW)

    team_names = sorted(e.properties["name"] for e in result.entities)
    assert team_names == ["org/payments-team", "org/platform-team"]

    # OWNED_BY edge per team, pointing from repo -> team.
    assert len(result.relationships) == 2
    for rel in result.relationships:
        assert rel.rel_type == RelationshipType.OWNED_BY.value
        assert rel.source_label == EntityType.REPOSITORY.value
        assert rel.target_label == EntityType.TEAM.value
        assert rel.source_id == "github:repo:12345"


def test_extract_codeowners_deduplicates_repeat_owners() -> None:
    text = """*.py @org/platform
*.md @org/platform
docs/ @org/docs-team
"""
    result = extract_codeowners(text, repo_source_id="github:repo:1", now=FIXED_NOW)
    team_names = sorted(e.properties["name"] for e in result.entities)
    assert team_names == ["org/docs-team", "org/platform"]
    assert len(result.relationships) == 2


def test_extract_codeowners_handles_inline_comments() -> None:
    text = "* @org/a # owners for everything\n"
    result = extract_codeowners(text, repo_source_id="github:repo:1", now=FIXED_NOW)
    team_names = [e.properties["name"] for e in result.entities]
    assert team_names == ["org/a"]


def test_extract_codeowners_handles_individual_usernames() -> None:
    """Personal ownership (``@alice``) is still modelled as a Team."""

    text = "* @alice @bob\n"
    result = extract_codeowners(text, repo_source_id="github:repo:1", now=FIXED_NOW)
    team_names = sorted(e.properties["name"] for e in result.entities)
    assert team_names == ["alice", "bob"]


def test_extract_codeowners_empty_file_returns_empty_result() -> None:
    result = extract_codeowners("\n# only comments\n\n", repo_source_id="github:repo:1")
    assert result.entities == []
    assert result.relationships == []


def test_extract_codeowners_requires_non_empty_repo_source_id() -> None:
    with pytest.raises(ValueError, match="repo_source_id"):
        extract_codeowners("* @org/a\n", repo_source_id="")


# ---------------------------------------------------------------------------
# Dataclass validation
# ---------------------------------------------------------------------------


def test_extracted_entity_rejects_unknown_label() -> None:
    with pytest.raises(ValueError, match="Unknown entity label"):
        ExtractedEntity(
            label="Widget",
            properties={
                "source_id": "x",
                "created_at": "t",
                "updated_at": "t",
                "text_hash": "h",
            },
        )


def test_extracted_entity_rejects_missing_required_property() -> None:
    with pytest.raises(ValueError, match="missing required properties"):
        ExtractedEntity(
            label=EntityType.SERVICE.value,
            properties={
                # Missing "name".
                "source_id": "service:x",
                "created_at": "t",
                "updated_at": "t",
                "text_hash": "h",
            },
        )


def test_extracted_entity_rejects_missing_text_hash() -> None:
    with pytest.raises(ValueError, match="text_hash"):
        ExtractedEntity(
            label=EntityType.SERVICE.value,
            properties={
                "source_id": "service:x",
                "name": "x",
                "created_at": "t",
                "updated_at": "t",
            },
        )


def test_extracted_relationship_rejects_invalid_triple() -> None:
    with pytest.raises(ValueError, match="Invalid relationship triple"):
        ExtractedRelationship(
            source_label=EntityType.SERVICE.value,
            source_id="service:x",
            target_label=EntityType.SERVICE.value,
            target_id="service:y",
            rel_type=RelationshipType.OWNED_BY.value,  # not allowed: Service-OWNED_BY-Service
        )

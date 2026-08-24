"""Unit tests for :mod:`src.extraction.writer`.

These tests exercise the write coordinator with mocked dependencies —
no Neo4j, no vector backend, no Azure OpenAI. The writer's contract
is about *decisions* (created/updated/skipped) and *routing* (which
store saw which call), which are easy to assert on with
``AsyncMock`` + ``MagicMock``.

Covered behaviours:

* CREATED decision for brand-new entities + full vector pipeline runs.
* SKIPPED decision when the stored ``text_hash`` matches.
* UPDATED decision when the stored ``text_hash`` differs.
* Non-text-bearing labels (Team, Repository, Person) skip embedding.
* Embedding failures are recorded but the entity still lands in Neo4j.
* Vector-store failures behave the same way.
* Relationship :class:`ReferentialIntegrityError` is logged and skipped
  without aborting the batch.
* Relationships that already exist resolve to SKIPPED.
* :class:`WriteResult` counters (created/updated/skipped).
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from processing.extraction.deterministic import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
)
from processing.embeddings.service import EmbeddingError
from processing.extraction.writer import (
    GraphWriter,
    WriteDecision,
    WriteResult,
    _extract_text_for_embedding,
)
from storage.graph.graph_store import ReferentialIntegrityError
from storage.graph.schema import EntityType, RelationshipType
from storage.vector.vector_store import EMBEDDING_DIMENSION

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vector() -> list[float]:
    """Return a canonical 3072-long vector for fake embedding responses."""

    return [0.1] * EMBEDDING_DIMENSION


def _make_writer() -> tuple[GraphWriter, MagicMock, MagicMock, MagicMock]:
    """Construct a :class:`GraphWriter` with fully-mocked dependencies.

    Returns the writer plus handles to the three mocks so tests can
    set return values and assert on calls. The graph-store mock has
    reasonable defaults: :meth:`get_entity` returns ``None`` (entity
    doesn't exist) and :meth:`get_relationships` returns an empty
    list (no edges yet).
    """

    graph_store = MagicMock(name="GraphStore")
    graph_store.get_entity = AsyncMock(return_value=None)
    graph_store.get_relationships = AsyncMock(return_value=[])
    graph_store.upsert_entity = AsyncMock(return_value={})
    graph_store.upsert_relationship = AsyncMock(return_value={})
    graph_store.close = AsyncMock()

    vector_store = MagicMock(name="VectorStore")
    vector_store.upsert_embedding = AsyncMock()
    vector_store.close = AsyncMock()

    embedding_service = MagicMock(name="EmbeddingService")
    embedding_service.generate_embedding = AsyncMock(return_value=_make_vector())
    embedding_service.close = AsyncMock()

    writer = GraphWriter(
        graph_store=graph_store,
        vector_store=vector_store,
        embedding_service=embedding_service,
    )
    return writer, graph_store, vector_store, embedding_service


def _ticket_entity(
    *,
    source_id: str = "jira:ticket:ENG-1",
    text_hash: str = "hash-1",
    description: str = "Investigate retry logic",
) -> ExtractedEntity:
    """Build a valid Ticket :class:`ExtractedEntity` for tests."""

    return ExtractedEntity(
        label=EntityType.TICKET.value,
        properties={
            "source_id": source_id,
            "key": "ENG-1",
            "title": "Fix payment retry",
            "description": description,
            "status": "In Progress",
            "created_at": "2024-12-01T10:00:00+00:00",
            "updated_at": "2024-12-01T11:00:00+00:00",
            "text_hash": text_hash,
        },
    )


def _team_entity(
    *,
    source_id: str = "team:platform",
    text_hash: str = "team-hash-1",
) -> ExtractedEntity:
    """Build a valid Team :class:`ExtractedEntity` (non-text-bearing)."""

    return ExtractedEntity(
        label=EntityType.TEAM.value,
        properties={
            "source_id": source_id,
            "name": "platform",
            "created_at": "2024-12-01T10:00:00+00:00",
            "updated_at": "2024-12-01T10:00:00+00:00",
            "text_hash": text_hash,
        },
    )


def _service_entity(
    *, source_id: str = "service:payments", text_hash: str = "svc-hash-1"
) -> ExtractedEntity:
    """Build a text-bearing Service :class:`ExtractedEntity`."""

    return ExtractedEntity(
        label=EntityType.SERVICE.value,
        properties={
            "source_id": source_id,
            "name": "payments",
            "description": "Handles payment processing",
            "created_at": "2024-12-01T10:00:00+00:00",
            "updated_at": "2024-12-01T10:00:00+00:00",
            "text_hash": text_hash,
        },
    )


def _repository_entity() -> ExtractedEntity:
    """Non-text-bearing Repository :class:`ExtractedEntity`."""

    return ExtractedEntity(
        label=EntityType.REPOSITORY.value,
        properties={
            "source_id": "github:repo:123",
            "name": "payments-service",
            "created_at": "2024-12-01T10:00:00+00:00",
            "updated_at": "2024-12-01T10:00:00+00:00",
            "text_hash": "repo-hash",
        },
    )


def _pr_entity() -> ExtractedEntity:
    """Text-bearing PR :class:`ExtractedEntity`."""

    return ExtractedEntity(
        label=EntityType.PR.value,
        properties={
            "source_id": "github:pr:123/42",
            "number": 42,
            "title": "Add idempotency key",
            "description": "Adds an idempotency key to the retry path.",
            "created_at": "2024-12-01T10:00:00+00:00",
            "updated_at": "2024-12-01T10:00:00+00:00",
            "text_hash": "pr-hash",
        },
    )


def _confluence_entity() -> ExtractedEntity:
    """Text-bearing ConfluencePage :class:`ExtractedEntity`."""

    return ExtractedEntity(
        label=EntityType.CONFLUENCE_PAGE.value,
        properties={
            "source_id": "confluence:page:1",
            "title": "Payment Retry Strategy",
            "space_key": "ENG",
            "created_at": "2024-12-01T10:00:00+00:00",
            "updated_at": "2024-12-01T10:00:00+00:00",
            "text_hash": "cf-hash",
        },
    )


# ---------------------------------------------------------------------------
# _extract_text_for_embedding
# ---------------------------------------------------------------------------


class TestExtractTextForEmbedding:
    def test_service_uses_name_and_description(self) -> None:
        svc = _service_entity()
        text = _extract_text_for_embedding(svc)
        assert text == "payments Handles payment processing"

    def test_ticket_uses_title_and_description(self) -> None:
        text = _extract_text_for_embedding(_ticket_entity())
        assert text == "Fix payment retry Investigate retry logic"

    def test_confluence_page_uses_title_and_space_key(self) -> None:
        text = _extract_text_for_embedding(_confluence_entity())
        assert text == "Payment Retry Strategy ENG"

    def test_pr_uses_title_and_description(self) -> None:
        text = _extract_text_for_embedding(_pr_entity())
        assert text == "Add idempotency key Adds an idempotency key to the retry path."

    def test_repository_returns_none(self) -> None:
        assert _extract_text_for_embedding(_repository_entity()) is None

    def test_team_returns_none(self) -> None:
        assert _extract_text_for_embedding(_team_entity()) is None

    def test_empty_pieces_return_none(self) -> None:
        # A text-bearing entity with only whitespace in its text fields
        # should be treated as "no text" so the writer doesn't emit a
        # degenerate embedding.
        entity = ExtractedEntity(
            label=EntityType.TICKET.value,
            properties={
                "source_id": "jira:ticket:ENG-2",
                "key": "ENG-2",
                "title": "",
                "description": "",
                "created_at": "2024-12-01T10:00:00+00:00",
                "updated_at": "2024-12-01T10:00:00+00:00",
                "text_hash": "h",
            },
        )
        assert _extract_text_for_embedding(entity) is None


# ---------------------------------------------------------------------------
# WriteResult counters
# ---------------------------------------------------------------------------


class TestWriteResultCounters:
    def test_counts_across_entities_and_relationships(self) -> None:
        result = WriteResult(
            entity_decisions={
                "a": WriteDecision.CREATED,
                "b": WriteDecision.UPDATED,
                "c": WriteDecision.SKIPPED,
                "d": WriteDecision.CREATED,
            },
            relationship_decisions={
                "a|REL|b": WriteDecision.CREATED,
                "b|REL|c": WriteDecision.SKIPPED,
            },
            embedding_failures=["a"],
        )
        assert result.created_count == 3
        assert result.updated_count == 1
        assert result.skipped_count == 2

    def test_empty_result_zero_counts(self) -> None:
        result = WriteResult()
        assert result.created_count == 0
        assert result.updated_count == 0
        assert result.skipped_count == 0


# ---------------------------------------------------------------------------
# GraphWriter.write — entity decisions
# ---------------------------------------------------------------------------


class TestWriteEntity:
    async def test_created_new_text_bearing_entity_runs_full_pipeline(self) -> None:
        """New Ticket → Neo4j upsert + embedding + vector-store upsert."""

        writer, graph, vector, embed = _make_writer()
        entity = _ticket_entity()

        result = await writer.write(ExtractionResult(entities=[entity]))

        assert result.entity_decisions == {entity.properties["source_id"]: WriteDecision.CREATED}
        assert result.embedding_failures == []
        graph.get_entity.assert_awaited_once_with(
            source_id=entity.properties["source_id"],
            label=EntityType.TICKET.value,
            include_deleted=True,
        )
        graph.upsert_entity.assert_awaited_once_with(
            EntityType.TICKET.value, entity.properties
        )
        embed.generate_embedding.assert_awaited_once()
        vector.upsert_embedding.assert_awaited_once()
        # Verify the VectorRecord carries through the right metadata.
        (call_record,), _ = vector.upsert_embedding.call_args
        assert call_record.source_id == entity.properties["source_id"]
        assert call_record.entity_type == EntityType.TICKET.value
        assert call_record.text_hash == entity.properties["text_hash"]
        assert call_record.created_at == entity.properties["updated_at"]
        assert len(call_record.vector) == EMBEDDING_DIMENSION

    async def test_skipped_when_text_hash_unchanged(self) -> None:
        """Existing row with matching hash → no Neo4j or vector traffic."""

        writer, graph, vector, embed = _make_writer()
        entity = _ticket_entity(text_hash="same-hash")
        graph.get_entity.return_value = {
            "label": EntityType.TICKET.value,
            "source_id": entity.properties["source_id"],
            "text_hash": "same-hash",
        }

        result = await writer.write(ExtractionResult(entities=[entity]))

        assert result.entity_decisions == {
            entity.properties["source_id"]: WriteDecision.SKIPPED
        }
        graph.upsert_entity.assert_not_awaited()
        embed.generate_embedding.assert_not_awaited()
        vector.upsert_embedding.assert_not_awaited()
        assert result.embedding_failures == []
        assert result.skipped_count == 1
        assert result.created_count == 0

    async def test_updated_when_text_hash_differs(self) -> None:
        """Existing row with different hash → Neo4j upsert + re-embed."""

        writer, graph, vector, embed = _make_writer()
        entity = _ticket_entity(text_hash="new-hash", description="fresh body")
        graph.get_entity.return_value = {
            "label": EntityType.TICKET.value,
            "source_id": entity.properties["source_id"],
            "text_hash": "old-hash",
        }

        result = await writer.write(ExtractionResult(entities=[entity]))

        assert result.entity_decisions == {
            entity.properties["source_id"]: WriteDecision.UPDATED
        }
        graph.upsert_entity.assert_awaited_once()
        embed.generate_embedding.assert_awaited_once()
        vector.upsert_embedding.assert_awaited_once()
        (rec,), _ = vector.upsert_embedding.call_args
        assert rec.text_hash == "new-hash"

    async def test_include_embeddings_false_skips_vector_pipeline(self) -> None:
        writer, graph, vector, embed = _make_writer()
        entity = _ticket_entity()

        result = await writer.write(
            ExtractionResult(entities=[entity]), include_embeddings=False
        )

        assert result.entity_decisions == {
            entity.properties["source_id"]: WriteDecision.CREATED
        }
        graph.upsert_entity.assert_awaited_once()
        embed.generate_embedding.assert_not_awaited()
        vector.upsert_embedding.assert_not_awaited()

    async def test_non_text_bearing_entity_skips_embedding(self) -> None:
        """Team/Repository writes land in Neo4j but not the vector store."""

        writer, graph, vector, embed = _make_writer()
        team = _team_entity()
        repo = _repository_entity()

        result = await writer.write(ExtractionResult(entities=[team, repo]))

        assert result.entity_decisions == {
            team.properties["source_id"]: WriteDecision.CREATED,
            repo.properties["source_id"]: WriteDecision.CREATED,
        }
        assert graph.upsert_entity.await_count == 2
        embed.generate_embedding.assert_not_awaited()
        vector.upsert_embedding.assert_not_awaited()
        assert result.embedding_failures == []

    async def test_embedding_failure_recorded_but_entity_still_written(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """EmbeddingError → entity still in Neo4j, source_id in failures list."""

        writer, graph, vector, embed = _make_writer()
        entity = _ticket_entity()
        embed.generate_embedding.side_effect = EmbeddingError("rate limited")

        with caplog.at_level(logging.WARNING, logger="src.extraction.writer"):
            result = await writer.write(ExtractionResult(entities=[entity]))

        assert result.entity_decisions == {
            entity.properties["source_id"]: WriteDecision.CREATED
        }
        assert result.embedding_failures == [entity.properties["source_id"]]
        graph.upsert_entity.assert_awaited_once()
        vector.upsert_embedding.assert_not_awaited()
        assert any(
            "Embedding generation failed" in rec.message for rec in caplog.records
        )

    async def test_vector_store_failure_recorded_but_entity_still_written(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Vector upsert exception → entity still in Neo4j, logged failure."""

        writer, graph, vector, embed = _make_writer()
        entity = _ticket_entity()
        vector.upsert_embedding.side_effect = RuntimeError("qdrant down")

        with caplog.at_level(logging.WARNING, logger="src.extraction.writer"):
            result = await writer.write(ExtractionResult(entities=[entity]))

        assert result.entity_decisions == {
            entity.properties["source_id"]: WriteDecision.CREATED
        }
        assert result.embedding_failures == [entity.properties["source_id"]]
        graph.upsert_entity.assert_awaited_once()
        embed.generate_embedding.assert_awaited_once()
        assert any(
            "Vector store upsert failed" in rec.message for rec in caplog.records
        )


# ---------------------------------------------------------------------------
# GraphWriter.write — relationship decisions
# ---------------------------------------------------------------------------


class TestWriteRelationship:
    def _rel(self) -> ExtractedRelationship:
        return ExtractedRelationship(
            source_label=EntityType.PR.value,
            source_id="github:pr:123/42",
            target_label=EntityType.REPOSITORY.value,
            target_id="github:repo:123",
            rel_type=RelationshipType.MODIFIES.value,
            properties={"created_at": "2024-12-01T10:00:00+00:00"},
        )

    async def test_created_when_relationship_is_new(self) -> None:
        writer, graph, _vector, _embed = _make_writer()
        rel = self._rel()

        result = await writer.write(ExtractionResult(relationships=[rel]))

        key = f"{rel.source_id}|{rel.rel_type}|{rel.target_id}"
        assert result.relationship_decisions == {key: WriteDecision.CREATED}
        graph.upsert_relationship.assert_awaited_once_with(
            source_id=rel.source_id,
            source_label=rel.source_label,
            target_id=rel.target_id,
            target_label=rel.target_label,
            rel_type=rel.rel_type,
            properties=rel.properties,
        )

    async def test_skipped_when_relationship_already_exists(self) -> None:
        writer, graph, _vector, _embed = _make_writer()
        rel = self._rel()
        graph.get_relationships.return_value = [
            {
                "rel_type": rel.rel_type,
                "properties": {},
                "direction": "outgoing",
                "neighbor": {
                    "label": rel.target_label,
                    "source_id": rel.target_id,
                },
            }
        ]

        result = await writer.write(ExtractionResult(relationships=[rel]))

        key = f"{rel.source_id}|{rel.rel_type}|{rel.target_id}"
        assert result.relationship_decisions == {key: WriteDecision.SKIPPED}
        graph.upsert_relationship.assert_not_awaited()

    async def test_referential_integrity_error_is_logged_and_skipped(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """ReferentialIntegrityError → warning logged, next rel still processed."""

        writer, graph, _vector, _embed = _make_writer()
        bad_rel = self._rel()
        good_rel = ExtractedRelationship(
            source_label=EntityType.SERVICE.value,
            source_id="service:a",
            target_label=EntityType.TEAM.value,
            target_id="team:platform",
            rel_type=RelationshipType.OWNED_BY.value,
        )

        # upsert_relationship succeeds for good_rel but fails for bad_rel.
        def _upsert_side_effect(**kwargs: Any) -> dict[str, Any]:
            if kwargs["source_id"] == bad_rel.source_id:
                raise ReferentialIntegrityError("missing endpoint")
            return {}

        graph.upsert_relationship.side_effect = _upsert_side_effect

        with caplog.at_level(logging.WARNING, logger="src.extraction.writer"):
            result = await writer.write(
                ExtractionResult(relationships=[bad_rel, good_rel])
            )

        # The bad relationship isn't recorded as CREATED.
        bad_key = f"{bad_rel.source_id}|{bad_rel.rel_type}|{bad_rel.target_id}"
        good_key = f"{good_rel.source_id}|{good_rel.rel_type}|{good_rel.target_id}"
        assert bad_key not in result.relationship_decisions
        assert result.relationship_decisions[good_key] == WriteDecision.CREATED

        # The second relationship still got its turn.
        assert graph.upsert_relationship.await_count == 2
        assert any(
            "Skipping relationship" in rec.message for rec in caplog.records
        )


# ---------------------------------------------------------------------------
# Mixed batches, close()
# ---------------------------------------------------------------------------


class TestBatchAndLifecycle:
    async def test_entities_written_before_relationships(self) -> None:
        """Entity upserts must precede relationship upserts.

        The writer order-of-ops matters for referential integrity:
        relationships are rejected by the graph store if either
        endpoint is missing, so all entities in the batch must land
        first.
        """

        writer, graph, _vector, _embed = _make_writer()
        call_order: list[str] = []

        async def _upsert_entity(*args: Any, **kwargs: Any) -> dict[str, Any]:
            call_order.append("entity")
            return {}

        async def _upsert_relationship(*args: Any, **kwargs: Any) -> dict[str, Any]:
            call_order.append("relationship")
            return {}

        graph.upsert_entity.side_effect = _upsert_entity
        graph.upsert_relationship.side_effect = _upsert_relationship

        entity = _service_entity()
        rel = ExtractedRelationship(
            source_label=EntityType.SERVICE.value,
            source_id=entity.properties["source_id"],
            target_label=EntityType.TEAM.value,
            target_id="team:platform",
            rel_type=RelationshipType.OWNED_BY.value,
        )

        await writer.write(
            ExtractionResult(entities=[entity], relationships=[rel]),
            include_embeddings=False,
        )

        assert call_order == ["entity", "relationship"]

    async def test_close_delegates_to_all_stores(self) -> None:
        writer, graph, vector, embed = _make_writer()
        await writer.close()
        graph.close.assert_awaited_once()
        vector.close.assert_awaited_once()
        embed.close.assert_awaited_once()

    async def test_async_context_manager_closes_on_exit(self) -> None:
        writer, graph, vector, embed = _make_writer()
        async with writer as w:
            assert w is writer
        graph.close.assert_awaited_once()
        vector.close.assert_awaited_once()
        embed.close.assert_awaited_once()

"""Unit tests for :mod:`src.models.graph_store`.

These tests exercise the GraphStore with a mocked ``neo4j`` async driver.
They cover schema validation, referential integrity checks, the Cypher
shapes emitted for each operation, and soft-delete / read filtering
semantics. No Neo4j instance is required.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from storage.graph.graph_store import (
    GraphStore,
    ReferentialIntegrityError,
    SchemaValidationError,
)

# ---------------------------------------------------------------------------
# Fake driver / session plumbing
# ---------------------------------------------------------------------------


class _FakeRecord(dict[str, Any]):
    """Dict that also supports ``record["key"]`` the way Neo4j records do."""


class _FakeResult:
    """Minimal async stand-in for ``neo4j.AsyncResult``.

    Stores a list of records and exposes ``single()`` (returns the first
    record or ``None``) and async iteration for multi-row results.
    """

    def __init__(self, records: list[_FakeRecord]) -> None:
        self._records = records

    async def single(self) -> _FakeRecord | None:
        return self._records[0] if self._records else None

    def __aiter__(self) -> Any:
        async def _gen() -> Any:
            for r in self._records:
                yield r

        return _gen()


class _FakeSession:
    """Records every ``run()`` call and returns queued ``_FakeResult`` objects.

    The test configures the queue via ``queue_results``; the session
    pops one result per ``run()`` in order. If fewer results are queued
    than runs are made, a default empty result is returned so failing
    tests surface as missing assertions rather than queue-exhaustion
    exceptions.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._results: list[_FakeResult] = []

    def queue_results(self, *results: _FakeResult) -> None:
        self._results.extend(results)

    async def run(self, cypher: str, **params: Any) -> _FakeResult:
        self.calls.append((cypher, params))
        if self._results:
            return self._results.pop(0)
        return _FakeResult([])

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


def _make_store_with_session() -> tuple[GraphStore, _FakeSession]:
    """Construct a GraphStore wired to a controllable fake session.

    Returns both the store and the session so tests can assert on
    queued queries and their parameters.
    """

    session = _FakeSession()
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()
    store = GraphStore(driver=driver)
    return store, session


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    """Constructor, connect, close, and async-context-manager behavior."""

    def test_requires_driver_or_connection_params(self) -> None:
        with pytest.raises(ValueError, match="driver"):
            GraphStore()

    @pytest.mark.asyncio
    async def test_injected_driver_is_not_closed_by_store(self) -> None:
        driver = MagicMock()
        driver.close = AsyncMock()
        store = GraphStore(driver=driver)
        await store.connect()  # no-op for injected drivers
        await store.close()
        driver.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_unconnected_store_raises_on_use(self) -> None:
        store = GraphStore(uri="bolt://x", user="u", password="p")
        with pytest.raises(RuntimeError, match="not connected"):
            await store.upsert_entity(
                "Service",
                {
                    "source_id": "s1",
                    "name": "svc",
                    "created_at": "t",
                    "updated_at": "t",
                },
            )


# ---------------------------------------------------------------------------
# upsert_entity
# ---------------------------------------------------------------------------


class TestUpsertEntity:
    @pytest.mark.asyncio
    async def test_rejects_unknown_label(self) -> None:
        store, _ = _make_store_with_session()
        with pytest.raises(SchemaValidationError, match="Unknown entity type"):
            await store.upsert_entity("Widget", {"source_id": "s1"})

    @pytest.mark.asyncio
    async def test_rejects_missing_source_id(self) -> None:
        store, _ = _make_store_with_session()
        with pytest.raises(SchemaValidationError, match="source_id"):
            await store.upsert_entity(
                "Service",
                {"name": "svc", "created_at": "t", "updated_at": "t"},
            )

    @pytest.mark.asyncio
    async def test_rejects_empty_source_id(self) -> None:
        store, _ = _make_store_with_session()
        with pytest.raises(SchemaValidationError, match="source_id"):
            await store.upsert_entity(
                "Service",
                {
                    "source_id": "",
                    "name": "svc",
                    "created_at": "t",
                    "updated_at": "t",
                },
            )

    @pytest.mark.asyncio
    async def test_rejects_missing_required_property(self) -> None:
        """Service requires ``name`` (in addition to common fields)."""

        store, _ = _make_store_with_session()
        with pytest.raises(SchemaValidationError, match="missing required properties"):
            await store.upsert_entity(
                "Service",
                {"source_id": "s1", "created_at": "t", "updated_at": "t"},
            )

    @pytest.mark.asyncio
    async def test_builds_merge_cypher_with_sanitized_props(self) -> None:
        """MERGE keys on source_id; managed keys are stripped from $props."""

        store, session = _make_store_with_session()
        returned_node = _FakeRecord(
            n={
                "source_id": "s1",
                "name": "svc",
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
            }
        )
        session.queue_results(_FakeResult([returned_node]))

        result = await store.upsert_entity(
            "Service",
            {
                "source_id": "s1",
                "name": "svc",
                "created_at": "stale-client-timestamp",
                "updated_at": "stale-client-timestamp",
                "deleted_at": "attempted-undelete",
                "description": "hello",
            },
        )

        assert result["label"] == "Service"
        assert result["source_id"] == "s1"
        assert len(session.calls) == 1
        cypher, params = session.calls[0]
        assert "MERGE (n:Service {source_id: $source_id})" in cypher
        assert "ON CREATE SET" in cypher
        assert "ON MATCH SET" in cypher
        assert "n.created_at = datetime()" in cypher
        assert "n.updated_at = datetime()" in cypher
        assert params["source_id"] == "s1"
        # Client-supplied managed props are stripped so the server-side
        # timestamps win.
        assert "created_at" not in params["props"]
        assert "updated_at" not in params["props"]
        assert "deleted_at" not in params["props"]
        assert params["props"]["name"] == "svc"
        assert params["props"]["description"] == "hello"


# ---------------------------------------------------------------------------
# upsert_relationship
# ---------------------------------------------------------------------------


class TestUpsertRelationship:
    @pytest.mark.asyncio
    async def test_rejects_invalid_triple(self) -> None:
        store, _ = _make_store_with_session()
        # Correct rel_type but wrong direction
        with pytest.raises(SchemaValidationError, match="Invalid relationship"):
            await store.upsert_relationship(
                source_id="t1",
                source_label="Team",
                target_id="s1",
                target_label="Service",
                rel_type="OWNED_BY",
            )

    @pytest.mark.asyncio
    async def test_rejects_when_source_missing(self) -> None:
        store, session = _make_store_with_session()
        # Existence preflight says source missing, target present
        session.queue_results(
            _FakeResult(
                [_FakeRecord(source_exists=False, target_exists=True)]
            )
        )
        with pytest.raises(ReferentialIntegrityError, match="Service:s1"):
            await store.upsert_relationship(
                source_id="s1",
                source_label="Service",
                target_id="t1",
                target_label="Team",
                rel_type="OWNED_BY",
            )

    @pytest.mark.asyncio
    async def test_rejects_when_target_missing(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(
            _FakeResult(
                [_FakeRecord(source_exists=True, target_exists=False)]
            )
        )
        with pytest.raises(ReferentialIntegrityError, match="Team:t1"):
            await store.upsert_relationship(
                source_id="s1",
                source_label="Service",
                target_id="t1",
                target_label="Team",
                rel_type="OWNED_BY",
            )

    @pytest.mark.asyncio
    async def test_creates_when_both_endpoints_exist(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(
            _FakeResult([_FakeRecord(source_exists=True, target_exists=True)]),
            _FakeResult(
                [_FakeRecord(rel_props={"created_at": "2024-01-01"})]
            ),
        )

        result = await store.upsert_relationship(
            source_id="s1",
            source_label="Service",
            target_id="t1",
            target_label="Team",
            rel_type="OWNED_BY",
        )

        assert result == {
            "source_id": "s1",
            "target_id": "t1",
            "rel_type": "OWNED_BY",
            "properties": {"created_at": "2024-01-01"},
        }
        # Two queries: existence check then MERGE.
        assert len(session.calls) == 2
        _preflight_cypher, _ = session.calls[0]
        merge_cypher, merge_params = session.calls[1]
        assert "MATCH (s:Service {source_id: $source_id})" in merge_cypher
        assert "MATCH (t:Team {source_id: $target_id})" in merge_cypher
        assert "MERGE (s)-[r:OWNED_BY]->(t)" in merge_cypher
        assert merge_params["source_id"] == "s1"
        assert merge_params["target_id"] == "t1"


# ---------------------------------------------------------------------------
# soft_delete_entity
# ---------------------------------------------------------------------------


class TestSoftDeleteEntity:
    @pytest.mark.asyncio
    async def test_rejects_unknown_label(self) -> None:
        store, _ = _make_store_with_session()
        with pytest.raises(SchemaValidationError):
            await store.soft_delete_entity("s1", "Widget")

    @pytest.mark.asyncio
    async def test_returns_true_when_entity_updated(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([_FakeRecord(updated=1)]))
        assert await store.soft_delete_entity("s1", "Service") is True
        cypher, params = session.calls[0]
        assert "MATCH (n:Service {source_id: $source_id})" in cypher
        assert "n.deleted_at IS NULL" in cypher
        assert "SET n.deleted_at = datetime()" in cypher
        assert params == {"source_id": "s1"}

    @pytest.mark.asyncio
    async def test_returns_false_when_no_entity_matches(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([_FakeRecord(updated=0)]))
        assert await store.soft_delete_entity("missing", "Service") is False


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------


class TestGetEntity:
    @pytest.mark.asyncio
    async def test_excludes_soft_deleted_by_default(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        result = await store.get_entity("s1", label="Service")

        assert result is None
        cypher, _ = session.calls[0]
        assert "n.deleted_at IS NULL" in cypher
        assert "MATCH (n:Service {source_id: $source_id})" in cypher

    @pytest.mark.asyncio
    async def test_include_deleted_drops_deleted_filter(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(
            _FakeResult(
                [
                    _FakeRecord(
                        n={"source_id": "s1", "deleted_at": "2024-01-02"},
                        node_labels=["Service"],
                    )
                ]
            )
        )

        result = await store.get_entity(
            "s1", label="Service", include_deleted=True
        )

        cypher, _ = session.calls[0]
        assert "n.deleted_at IS NULL" not in cypher
        assert result is not None
        assert result["label"] == "Service"
        assert result["deleted_at"] == "2024-01-02"

    @pytest.mark.asyncio
    async def test_omitting_label_uses_unfiltered_match(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(
            _FakeResult(
                [
                    _FakeRecord(
                        n={"source_id": "s1", "name": "svc"},
                        node_labels=["Service"],
                    )
                ]
            )
        )

        result = await store.get_entity("s1")

        cypher, _ = session.calls[0]
        # No label filter inside the parens
        assert "MATCH (n {source_id: $source_id})" in cypher
        assert result is not None
        assert result["label"] == "Service"


# ---------------------------------------------------------------------------
# get_relationships
# ---------------------------------------------------------------------------


class TestGetRelationships:
    @pytest.mark.asyncio
    async def test_outgoing_direction_uses_right_arrow(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships(
            source_id="s1",
            source_label="Service",
            direction="outgoing",
        )

        cypher, _ = session.calls[0]
        assert "(s:Service {source_id: $source_id})-[r]->(t)" in cypher

    @pytest.mark.asyncio
    async def test_incoming_direction_uses_left_arrow(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships(
            source_id="s1",
            source_label="Service",
            direction="incoming",
        )

        cypher, _ = session.calls[0]
        assert "(s:Service {source_id: $source_id})<-[r]-(t)" in cypher

    @pytest.mark.asyncio
    async def test_rejects_invalid_direction(self) -> None:
        store, _ = _make_store_with_session()
        with pytest.raises(ValueError, match="direction"):
            await store.get_relationships(
                source_id="s1",
                source_label="Service",
                direction="sideways",
            )

    @pytest.mark.asyncio
    async def test_filters_soft_deleted_neighbors(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships(
            source_id="s1",
            source_label="Service",
        )

        cypher, _ = session.calls[0]
        assert "t.deleted_at IS NULL" in cypher
        assert "s.deleted_at IS NULL" in cypher

    @pytest.mark.asyncio
    async def test_returns_neighbor_dicts(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(
            _FakeResult(
                [
                    _FakeRecord(
                        rel_type="OWNED_BY",
                        rel_props={"created_at": "2024-01-01"},
                        neighbor={"source_id": "t1", "name": "payments"},
                        neighbor_labels=["Team"],
                        dir="outgoing",
                    ),
                ]
            )
        )

        rels = await store.get_relationships(
            source_id="s1",
            source_label="Service",
            rel_type="OWNED_BY",
        )

        assert rels == [
            {
                "rel_type": "OWNED_BY",
                "properties": {"created_at": "2024-01-01"},
                "direction": "outgoing",
                "neighbor": {
                    "label": "Team",
                    "source_id": "t1",
                    "name": "payments",
                },
            }
        ]
        # rel_type filter is parameterized.
        _, params = session.calls[0]
        assert params["rel_type"] == "OWNED_BY"


# ---------------------------------------------------------------------------
# get_relationships_by_provenance
# ---------------------------------------------------------------------------


class TestGetRelationshipsByProvenance:
    @pytest.mark.asyncio
    async def test_filters_by_provenance_parameter(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships_by_provenance("llm:steering")

        cypher, params = session.calls[0]
        assert "MATCH (s)-[r]->(t)" in cypher
        assert "r.provenance = $provenance" in cypher
        assert params["provenance"] == "llm:steering"
        # No rel_type filter when not requested.
        assert "type(r) = $rel_type" not in cypher
        assert "rel_type" not in params

    @pytest.mark.asyncio
    async def test_applies_rel_type_filter_via_parameter(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships_by_provenance(
            "deterministic", rel_type="DEPENDS_ON"
        )

        cypher, params = session.calls[0]
        assert "type(r) = $rel_type" in cypher
        assert params["rel_type"] == "DEPENDS_ON"

    @pytest.mark.asyncio
    async def test_excludes_soft_deleted_endpoints(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships_by_provenance("llm:jira")

        cypher, _ = session.calls[0]
        assert "s.deleted_at IS NULL" in cypher
        assert "t.deleted_at IS NULL" in cypher

    @pytest.mark.asyncio
    async def test_limit_is_parameterized(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(_FakeResult([]))

        await store.get_relationships_by_provenance("llm:pr", limit=25)

        cypher, params = session.calls[0]
        assert "LIMIT $limit" in cypher
        assert params["limit"] == 25

    @pytest.mark.asyncio
    async def test_returns_edge_dicts(self) -> None:
        store, session = _make_store_with_session()
        session.queue_results(
            _FakeResult(
                [
                    _FakeRecord(
                        source="service:a",
                        target="service:b",
                        rel_type="DEPENDS_ON",
                        rel_props={
                            "provenance": "llm:steering",
                            "confidence": "high",
                        },
                    ),
                ]
            )
        )

        edges = await store.get_relationships_by_provenance("llm:steering")

        assert edges == [
            {
                "source": "service:a",
                "target": "service:b",
                "rel_type": "DEPENDS_ON",
                "properties": {
                    "provenance": "llm:steering",
                    "confidence": "high",
                },
            }
        ]

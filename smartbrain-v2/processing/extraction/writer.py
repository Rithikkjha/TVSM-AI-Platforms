"""Idempotent write coordinator for the Engineering Memory Graph.

:class:`GraphWriter` coordinates writes across the three storage
layers — Neo4j (entities + relationships), the vector store
(embeddings), and Azure OpenAI (embedding generation) — so that the
rest of the pipeline can hand off an :class:`ExtractionResult` and
trust that:

* Entities with unchanged ``text_hash`` are skipped (Requirement 1.6,
  Property 1: Idempotent Ingestion).
* Entities with changed ``text_hash`` are updated in Neo4j and have
  their embedding regenerated.
* Text-bearing entities (ConfluencePage, Ticket, PR, Service, Epic)
  always have a corresponding vector in the vector store after a
  successful write (Property 5: Vector Embedding Completeness).
* Non-text-bearing entities (Repository, Team, Person) are written
  to Neo4j without an embedding — there's no meaningful body text to
  embed for them in V1.
* Partial failures (embedding generation or vector-store write) are
  *logged and recorded*, not fatal. The entity is still present in
  Neo4j; the embedding will be retried on the next sync cycle
  (matches the "Vector store write failure" row in the design's
  Error Handling table).
* Relationship writes that fail referential integrity are logged and
  skipped without aborting the rest of the batch (matches the
  "Schema validation failure" row in the Error Handling table).

The writer is pure async and stateless — it holds no internal state
between :meth:`write` calls beyond the injected store handles. Two
concurrent calls are safe; per-entity decisions are independent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from types import TracebackType
from typing import Self

from processing.extraction.deterministic import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
)
from processing.embeddings.service import EmbeddingError, EmbeddingService
from storage.graph.graph_store import GraphStore, ReferentialIntegrityError
from storage.graph.schema import EntityType
from storage.vector.vector_store import VectorRecord, VectorStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class WriteDecision(StrEnum):
    """Outcome of a single entity or relationship write.

    Values are strings so they round-trip cleanly through structured
    logs and JSON observability payloads.
    """

    CREATED = "created"
    UPDATED = "updated"
    SKIPPED = "skipped"


@dataclass
class WriteResult:
    """Summary of a single :meth:`GraphWriter.write` invocation.

    Attributes:
        entity_decisions: Map from entity ``source_id`` to the write
            decision that was taken. Keyed on ``source_id`` so callers
            can correlate decisions back to their input entities.
        relationship_decisions: Map from a synthetic relationship key
            (``"{source_id}|{rel_type}|{target_id}"``) to the decision
            taken. Relationships don't carry a ``text_hash`` so their
            decisions are either ``CREATED`` (new edge) or ``SKIPPED``
            (already present).
        embedding_failures: ``source_id`` list of entities whose Neo4j
            write succeeded but whose embedding generation or
            vector-store write failed. These will be retried on the
            next sync cycle.
    """

    entity_decisions: dict[str, WriteDecision] = field(default_factory=dict)
    relationship_decisions: dict[str, WriteDecision] = field(default_factory=dict)
    embedding_failures: list[str] = field(default_factory=list)

    @property
    def created_count(self) -> int:
        """Total writes that materialized a new node or edge."""

        return sum(
            1
            for d in (*self.entity_decisions.values(), *self.relationship_decisions.values())
            if d is WriteDecision.CREATED
        )

    @property
    def updated_count(self) -> int:
        """Total writes that replaced an existing node's properties.

        Relationships don't support the ``UPDATED`` decision in V1, so
        this only counts entities.
        """

        return sum(
            1
            for d in (*self.entity_decisions.values(), *self.relationship_decisions.values())
            if d is WriteDecision.UPDATED
        )

    @property
    def skipped_count(self) -> int:
        """Total writes that were no-ops due to unchanged content."""

        return sum(
            1
            for d in (*self.entity_decisions.values(), *self.relationship_decisions.values())
            if d is WriteDecision.SKIPPED
        )


# ---------------------------------------------------------------------------
# Text-extraction helper
# ---------------------------------------------------------------------------


#: Labels that carry meaningful free-form text worth embedding. Kept as
#: a module constant so that callers (e.g. the full-sync path) can
#: quickly check whether an entity is text-bearing without constructing
#: a :class:`GraphWriter`.
_TEXT_BEARING_LABELS: frozenset[str] = frozenset(
    {
        EntityType.SERVICE.value,
        EntityType.TICKET.value,
        EntityType.EPIC.value,
        EntityType.PR.value,
        EntityType.CONFLUENCE_PAGE.value,
    }
)


def _extract_text_for_embedding(entity: ExtractedEntity) -> str | None:
    """Return the text to embed for ``entity``, or ``None`` if not text-bearing.

    The concatenation strategy is intentionally simple: join the
    label-specific identifier fields with the free-form body so that
    a single embedding captures both "what this thing is called" and
    "what it's about." Missing fields are tolerated (treated as empty
    string) so the helper never raises on a valid :class:`ExtractedEntity`.
    """

    label = entity.label
    if label not in _TEXT_BEARING_LABELS:
        return None

    props = entity.properties
    if label == EntityType.SERVICE.value:
        pieces = [props.get("name", ""), props.get("description", "")]
    elif label in {
        EntityType.TICKET.value,
        EntityType.EPIC.value,
        EntityType.PR.value,
    }:
        pieces = [props.get("title", ""), props.get("description", "")]
    elif label == EntityType.CONFLUENCE_PAGE.value:
        # Embed on title + space + full content so steering files,
        # key-file summaries and real Confluence pages are all
        # retrievable by their actual text, not just their title.
        pieces = [
            props.get("title", ""),
            props.get("space_key", ""),
            props.get("content_summary", ""),
        ]
    else:  # pragma: no cover - covered by the set check above
        return None

    text = " ".join(str(p) for p in pieces if p).strip()
    return text or None


# ---------------------------------------------------------------------------
# GraphWriter
# ---------------------------------------------------------------------------


class GraphWriter:
    """Coordinates idempotent writes to Neo4j and the vector store.

    All three dependencies are required — the writer doesn't support
    a "neo4j only" mode because the vector store and Neo4j must stay
    in sync for the query layer to work. A caller that genuinely
    wants to skip embeddings on a single call can pass
    ``include_embeddings=False`` to :meth:`write`.

    The writer is stateless; it is safe to call :meth:`write`
    concurrently from multiple tasks as long as the injected stores
    themselves are thread-/task-safe (they are, in both backends).
    """

    def __init__(
        self,
        graph_store: GraphStore,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
    ) -> None:
        self._graph_store = graph_store
        self._vector_store = vector_store
        self._embedding_service = embedding_service

    # -- public API ------------------------------------------------------

    async def write(
        self,
        extraction_result: ExtractionResult,
        include_embeddings: bool = True,
    ) -> WriteResult:
        """Apply an :class:`ExtractionResult` to Neo4j and the vector store.

        Ordering:

        1. Entities are processed first in the order supplied. This is
           the caller's responsibility — the writer does not reorder.
           Extractors are expected to emit "terminal" entities (those
           that are only endpoints, never sources) last so that any
           referenced relationships have their endpoints in the graph
           by the time step 2 runs.
        2. Relationships are processed after all entities, so that
           referential-integrity checks inside
           :meth:`GraphStore.upsert_relationship` see the full graph
           state produced by this batch.

        A failure in one entity or relationship never stops the batch:
        errors are logged and the loop continues. This matches the
        "single entity failure shouldn't stop batch" behaviour called
        out in the V1 design.
        """

        result = WriteResult()

        for entity in extraction_result.entities:
            try:
                await self._write_entity(entity, include_embeddings, result)
            except Exception as exc:  # pragma: no cover - defensive
                # Unexpected errors (schema violations, driver failures)
                # should not abort the batch — log and move on so
                # subsequent entities still get a shot at being
                # written.
                logger.error(
                    "Failed to write entity %s:%s — %s",
                    entity.label,
                    entity.properties.get("source_id"),
                    exc,
                )

        for relationship in extraction_result.relationships:
            try:
                await self._write_relationship(relationship, result)
            except ReferentialIntegrityError as exc:
                # Expected whenever an upstream extractor produced a
                # relationship whose endpoint got soft-deleted or
                # never existed. Log the specifics so operators can
                # diagnose, but don't fail the batch.
                logger.warning(
                    "Skipping relationship (%s:%s)-[:%s]->(%s:%s): %s",
                    relationship.source_label,
                    relationship.source_id,
                    relationship.rel_type,
                    relationship.target_label,
                    relationship.target_id,
                    exc,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(
                    "Failed to write relationship (%s)-[:%s]->(%s): %s",
                    relationship.source_id,
                    relationship.rel_type,
                    relationship.target_id,
                    exc,
                )

        logger.info(
            "Write complete: created=%d updated=%d skipped=%d embedding_failures=%d",
            result.created_count,
            result.updated_count,
            result.skipped_count,
            len(result.embedding_failures),
        )
        return result

    async def close(self) -> None:
        """Close all injected stores.

        Delegates to each dependency's ``close``. Each dependency's
        ``close`` is idempotent and only closes resources it owns, so
        this is safe to call even when the stores were constructed
        with externally-owned drivers/clients.
        """

        await self._graph_store.close()
        await self._vector_store.close()
        await self._embedding_service.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- internal --------------------------------------------------------

    async def _write_entity(
        self,
        entity: ExtractedEntity,
        include_embeddings: bool,
        result: WriteResult,
    ) -> None:
        """Write a single entity, recording the decision on ``result``.

        The decision is one of:

        * ``CREATED`` — no row with that ``source_id`` exists yet;
          upsert the node and (if text-bearing) generate a fresh
          embedding.
        * ``UPDATED`` — a row with that ``source_id`` exists but its
          stored ``text_hash`` differs from the incoming hash; upsert
          the node and regenerate the embedding.
        * ``SKIPPED`` — a row with that ``source_id`` and identical
          ``text_hash`` already exists; no Neo4j or vector-store
          traffic at all.
        """

        source_id = entity.properties["source_id"]
        text_hash = entity.properties["text_hash"]

        # Look up the existing entity — include soft-deleted rows so
        # that an identical re-ingestion of a soft-deleted record is
        # correctly reported as SKIPPED rather than re-created.
        existing = await self._graph_store.get_entity(
            source_id=source_id,
            label=entity.label,
            include_deleted=True,
        )

        if existing is None:
            decision = WriteDecision.CREATED
        elif existing.get("text_hash") == text_hash:
            result.entity_decisions[source_id] = WriteDecision.SKIPPED
            logger.debug(
                "Skipped entity %s:%s (text_hash unchanged)", entity.label, source_id
            )
            return
        else:
            decision = WriteDecision.UPDATED

        await self._graph_store.upsert_entity(entity.label, entity.properties)
        result.entity_decisions[source_id] = decision
        logger.debug(
            "%s entity %s:%s",
            decision.value.capitalize(),
            entity.label,
            source_id,
        )

        if include_embeddings:
            await self._maybe_embed(entity, text_hash, result)

    async def _maybe_embed(
        self,
        entity: ExtractedEntity,
        text_hash: str,
        result: WriteResult,
    ) -> None:
        """Generate + upsert an embedding for text-bearing entities.

        Failures in either the embedding API call or the vector-store
        upsert are caught, logged, and recorded in
        ``result.embedding_failures`` so the caller can surface a
        retry hint. The Neo4j row is left intact — the next sync
        cycle will retry the embedding step.
        """

        text = _extract_text_for_embedding(entity)
        if text is None:
            return

        source_id = entity.properties["source_id"]
        # Prefer ``updated_at`` (reflects the most recent sync) and
        # fall back to ``created_at`` so the vector always carries a
        # valid ISO timestamp — VectorRecord rejects an empty one.
        created_at = (
            entity.properties.get("updated_at")
            or entity.properties.get("created_at")
            or ""
        )

        try:
            vector = await self._embedding_service.generate_embedding(text)
        except EmbeddingError as exc:
            logger.warning(
                "Embedding generation failed for %s:%s — %s; entity written "
                "to Neo4j, vector will be retried on next sync",
                entity.label,
                source_id,
                exc,
            )
            result.embedding_failures.append(source_id)
            return
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Unexpected embedding error for %s:%s — %s", entity.label, source_id, exc
            )
            result.embedding_failures.append(source_id)
            return

        try:
            record = VectorRecord(
                source_id=source_id,
                entity_type=entity.label,
                text_hash=text_hash,
                vector=vector,
                created_at=created_at,
            )
            await self._vector_store.upsert_embedding(record)
        except Exception as exc:
            logger.warning(
                "Vector store upsert failed for %s:%s — %s; entity written "
                "to Neo4j, vector will be retried on next sync",
                entity.label,
                source_id,
                exc,
            )
            result.embedding_failures.append(source_id)

    async def _write_relationship(
        self,
        relationship: ExtractedRelationship,
        result: WriteResult,
    ) -> None:
        """Write a single relationship, recording the decision on ``result``.

        Relationships don't carry a ``text_hash`` (their content is
        defined by their endpoints and type), so the decision space
        is just ``CREATED`` vs ``SKIPPED``. The writer asks the graph
        store whether an identical edge already exists before calling
        :meth:`GraphStore.upsert_relationship` so that ``created_count``
        and ``skipped_count`` on the result are accurate.
        """

        key = (
            f"{relationship.source_id}|{relationship.rel_type}|{relationship.target_id}"
        )

        existing = await self._graph_store.get_relationships(
            source_id=relationship.source_id,
            source_label=relationship.source_label,
            rel_type=relationship.rel_type,
            direction="outgoing",
        )
        already_present = any(
            neighbor["neighbor"].get("source_id") == relationship.target_id
            for neighbor in existing
        )
        if already_present:
            result.relationship_decisions[key] = WriteDecision.SKIPPED
            logger.debug("Skipped relationship %s (already present)", key)
            return

        # Map extractor provenance/confidence onto the stored edge
        # properties (Req 11). Extractors tag their origin via a
        # ``source`` property (``"llm:confluence"``, ``"llm:pr"``,
        # ``"llm:steering"``, ``"llm:jira"``); deterministic extractors
        # may omit it. Rename ``source`` → ``provenance`` with a
        # ``"deterministic"`` default so no edge is ever written
        # without a provenance value (Req 11.1, 11.3, 11.6). Only
        # non-deterministic edges carry a ``confidence`` (Req 11.2);
        # deterministic edges are unconditionally trusted and carry
        # none.
        props = dict(relationship.properties)
        props["provenance"] = props.pop("source", "deterministic")
        if props["provenance"] != "deterministic":
            props.setdefault("confidence", relationship.confidence)

        await self._graph_store.upsert_relationship(
            source_id=relationship.source_id,
            source_label=relationship.source_label,
            target_id=relationship.target_id,
            target_label=relationship.target_label,
            rel_type=relationship.rel_type,
            properties=props,
        )
        result.relationship_decisions[key] = WriteDecision.CREATED
        logger.debug("Created relationship %s", key)


__all__ = [
    "GraphWriter",
    "WriteDecision",
    "WriteResult",
]

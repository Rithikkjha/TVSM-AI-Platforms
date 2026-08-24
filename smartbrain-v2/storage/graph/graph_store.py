"""Async Neo4j graph store abstraction for the Engineering Memory Graph.

This module wraps the official ``neo4j`` async driver with the V1 write
and read semantics described in the design document:

* Schema-first validation — every entity and relationship is validated
  against :mod:`src.models.schema` *before* any Cypher is sent to Neo4j
  (Requirements 2.3, 2.5, 5.2).
* Referential integrity — relationship writes are rejected if either
  endpoint is missing from the graph (Requirements 2.4, 2.6, 5.4).
* Soft delete — entities are marked with ``deleted_at`` rather than
  removed (Requirement 5.5), and read operations skip soft-deleted
  entities by default.

The store is dependency-injectable: callers can pass an existing
``AsyncDriver`` (useful in tests, or when sharing a driver across
modules) or let the store construct one from connection settings and
manage its lifecycle via an ``async with`` context manager.

Labels and relationship types are validated against the schema enum
before being interpolated into Cypher text. User-controlled values
(``source_id``, property dicts) always flow through Cypher parameters,
so the store is safe against Cypher injection.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

from neo4j import AsyncDriver, AsyncGraphDatabase

from storage.graph.schema import (
    is_valid_entity_type,
    is_valid_relationship,
    required_properties,
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SchemaValidationError(ValueError):
    """Raised when a write violates the V1 graph schema.

    Thrown for unknown entity labels, unknown relationship types,
    disallowed ``(source, rel, target)`` tuples, or payloads missing
    required properties. Inherits from :class:`ValueError` so callers
    can catch it as either.
    """


class ReferentialIntegrityError(ValueError):
    """Raised when a relationship write references a non-existent entity.

    Thrown when the source or target ``source_id`` cannot be matched
    in the graph (under the given label). The graph state is not
    modified before the exception is raised.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

#: Properties that the graph store manages on write. Callers may supply
#: them — they will simply be overridden by the store-side values — but
#: they are not *required* from the caller, because the store generates
#: them from Cypher ``datetime()`` calls.
_MANAGED_PROPERTIES: frozenset[str] = frozenset({"created_at", "updated_at", "deleted_at"})


def _sanitize_entity_properties(properties: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``properties`` with store-managed keys removed.

    The returned dict is safe to splat into ``SET n += $props`` without
    clobbering the ``created_at`` that the store maintains, and without
    accidentally resurrecting a soft-deleted entity by setting
    ``deleted_at = null``.
    """

    return {k: v for k, v in properties.items() if k not in _MANAGED_PROPERTIES}


def _validate_source_id(source_id: Any) -> str:
    """Return ``source_id`` if it's a non-empty string, else raise."""

    if not isinstance(source_id, str) or not source_id:
        raise SchemaValidationError("Entity must have a non-empty 'source_id' string")
    return source_id


# ---------------------------------------------------------------------------
# GraphStore
# ---------------------------------------------------------------------------


class GraphStore:
    """Async wrapper around the Neo4j driver for the V1 Memory_Graph.

    The store can be constructed in two modes:

    * **Connection mode** — pass ``uri``, ``user``, ``password``. The
      store creates and owns an :class:`~neo4j.AsyncDriver`, which must
      be initialized with :meth:`connect` and released with
      :meth:`close` (or via ``async with``).
    * **Injected-driver mode** — pass an existing ``driver``. The
      caller retains ownership; :meth:`close` becomes a no-op for the
      driver (the store will not close a driver it didn't create).
    """

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        *,
        driver: AsyncDriver | None = None,
    ) -> None:
        if driver is None and not (uri and user is not None and password is not None):
            raise ValueError(
                "GraphStore requires either an existing 'driver' or "
                "'uri'/'user'/'password' to construct one"
            )
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: AsyncDriver | None = driver
        self._owns_driver: bool = driver is None

    # -- lifecycle -------------------------------------------------------

    async def connect(self) -> None:
        """Initialize the Neo4j driver if one wasn't injected.

        Safe to call multiple times — subsequent calls are no-ops as long
        as the driver is already initialized.
        """

        if self._driver is None:
            assert self._uri is not None  # narrowed by constructor
            assert self._user is not None
            assert self._password is not None
            self._driver = AsyncGraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )

    async def close(self) -> None:
        """Close the driver if this store created it. No-op otherwise."""

        if self._driver is not None and self._owns_driver:
            await self._driver.close()
            self._driver = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- internal --------------------------------------------------------

    @property
    def _active_driver(self) -> AsyncDriver:
        """Return the live driver or raise if the store isn't connected."""

        if self._driver is None:
            raise RuntimeError(
                "GraphStore is not connected; call 'await store.connect()' "
                "or use it as an async context manager"
            )
        return self._driver

    # -- write operations -----------------------------------------------

    async def upsert_entity(self, label: str, properties: dict[str, Any]) -> dict[str, Any]:
        """Upsert an entity node keyed on ``source_id``.

        On create, the store sets ``created_at`` and ``updated_at`` to
        ``datetime()`` and applies all caller-supplied properties. On
        match, it updates ``updated_at`` and all caller-supplied
        properties while preserving the original ``created_at``.

        Args:
            label: Entity label (must appear in the V1 schema).
            properties: Property bag. Must contain ``source_id`` and any
                label-specific required fields from
                :func:`~src.models.schema.required_properties`.

        Returns:
            The resulting entity as ``{"label": ..., **properties}``.

        Raises:
            SchemaValidationError: If the label is unknown, the payload
                is missing ``source_id``, or any required field is
                absent.
        """

        if not is_valid_entity_type(label):
            raise SchemaValidationError(f"Unknown entity type: {label!r}")

        source_id = _validate_source_id(properties.get("source_id"))

        required = required_properties(label)
        caller_required = required - _MANAGED_PROPERTIES
        missing = sorted(caller_required - properties.keys())
        if missing:
            raise SchemaValidationError(
                f"Entity of type {label!r} is missing required properties: {missing}"
            )

        # Strip store-managed keys before sending to Cypher so that a
        # stale ``created_at`` in the payload can't override the
        # server-side timestamp (and so we never implicitly "un-delete"
        # via ``deleted_at = null``).
        sanitized = _sanitize_entity_properties(properties)

        # Label is safe to interpolate because it's validated above.
        cypher = (
            f"MERGE (n:{label} {{source_id: $source_id}}) "
            "ON CREATE SET n += $props, "
            "              n.created_at = datetime(), "
            "              n.updated_at = datetime() "
            "ON MATCH SET n += $props, "
            "             n.updated_at = datetime() "
            "RETURN n"
        )

        async with self._active_driver.session() as session:
            result = await session.run(
                cypher,
                source_id=source_id,
                props=sanitized,
            )
            record = await result.single()

        if record is None:  # pragma: no cover - MERGE should always return a row
            raise RuntimeError(f"MERGE returned no row for entity {label}:{source_id}")

        node_props = dict(record["n"])
        return {"label": label, **node_props}

    async def upsert_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upsert a relationship between two existing entities.

        Validates that the ``(source_label, rel_type, target_label)``
        tuple is in the V1 whitelist and that both endpoints exist
        before issuing the ``MERGE``.

        Args:
            source_id: ``source_id`` of the source entity.
            source_label: Label of the source entity.
            target_id: ``source_id`` of the target entity.
            target_label: Label of the target entity.
            rel_type: Relationship type.
            properties: Optional relationship properties.

        Returns:
            ``{"source_id", "target_id", "rel_type", "properties"}``.

        Raises:
            SchemaValidationError: If the triple is not in the schema
                whitelist.
            ReferentialIntegrityError: If either endpoint cannot be
                matched in the graph.
        """

        if not is_valid_relationship(source_label, rel_type, target_label):
            raise SchemaValidationError(
                f"Invalid relationship triple: "
                f"({source_label!r})-[:{rel_type}]->({target_label!r})"
            )

        _validate_source_id(source_id)
        _validate_source_id(target_id)

        props = _sanitize_entity_properties(properties or {})

        # Existence preflight. Running it in the same session keeps the
        # two operations on the same connection, but Neo4j doesn't
        # require them to be in one transaction for this check — a
        # concurrent delete between the two queries would simply cause
        # the MERGE to find 0 matches and no-op.
        driver = self._active_driver
        async with driver.session() as session:
            check = await session.run(
                (
                    f"OPTIONAL MATCH (s:{source_label} {{source_id: $source_id}}) "
                    f"OPTIONAL MATCH (t:{target_label} {{source_id: $target_id}}) "
                    "RETURN s IS NOT NULL AS source_exists, "
                    "       t IS NOT NULL AS target_exists"
                ),
                source_id=source_id,
                target_id=target_id,
            )
            row = await check.single()
            source_exists = bool(row and row["source_exists"])
            target_exists = bool(row and row["target_exists"])
            if not source_exists or not target_exists:
                missing: list[str] = []
                if not source_exists:
                    missing.append(f"{source_label}:{source_id}")
                if not target_exists:
                    missing.append(f"{target_label}:{target_id}")
                raise ReferentialIntegrityError(
                    "Cannot create relationship; missing endpoint(s): "
                    + ", ".join(missing)
                )

            merge_cypher = (
                f"MATCH (s:{source_label} {{source_id: $source_id}}) "
                f"MATCH (t:{target_label} {{source_id: $target_id}}) "
                f"MERGE (s)-[r:{rel_type}]->(t) "
                "ON CREATE SET r += $props, r.created_at = datetime() "
                "ON MATCH SET r += $props "
                "RETURN properties(r) AS rel_props"
            )
            result = await session.run(
                merge_cypher,
                source_id=source_id,
                target_id=target_id,
                props=props,
            )
            record = await result.single()

        rel_props = dict(record["rel_props"]) if record else {}
        return {
            "source_id": source_id,
            "target_id": target_id,
            "rel_type": rel_type,
            "properties": rel_props,
        }

    async def soft_delete_entity(self, source_id: str, label: str) -> bool:
        """Mark an entity as deleted by setting ``deleted_at``.

        Only affects entities that are not already soft-deleted — re-running
        on a soft-deleted entity returns ``False`` without changing the
        existing ``deleted_at`` value.

        Returns:
            ``True`` if an entity was updated, ``False`` if no matching
            live entity was found.
        """

        if not is_valid_entity_type(label):
            raise SchemaValidationError(f"Unknown entity type: {label!r}")
        _validate_source_id(source_id)

        cypher = (
            f"MATCH (n:{label} {{source_id: $source_id}}) "
            "WHERE n.deleted_at IS NULL "
            "SET n.deleted_at = datetime() "
            "RETURN count(n) AS updated"
        )
        async with self._active_driver.session() as session:
            result = await session.run(cypher, source_id=source_id)
            record = await result.single()

        updated = int(record["updated"]) if record else 0
        return updated > 0

    # -- read operations -------------------------------------------------

    async def get_entity(
        self,
        source_id: str,
        label: str | None = None,
        include_deleted: bool = False,
    ) -> dict[str, Any] | None:
        """Fetch an entity by ``source_id``.

        Args:
            source_id: The entity's ``source_id``.
            label: Optional label filter. If ``None``, the first entity
                matching ``source_id`` under any label is returned.
            include_deleted: When ``False`` (default), soft-deleted
                entities are excluded.

        Returns:
            ``{"label": ..., **properties}`` for the first matching
            entity, or ``None`` if none is found.
        """

        _validate_source_id(source_id)
        if label is not None and not is_valid_entity_type(label):
            raise SchemaValidationError(f"Unknown entity type: {label!r}")

        label_pattern = f":{label}" if label else ""
        deleted_clause = "" if include_deleted else " AND n.deleted_at IS NULL"

        cypher = (
            f"MATCH (n{label_pattern} {{source_id: $source_id}}) "
            f"WHERE 1=1{deleted_clause} "
            "RETURN n, labels(n) AS node_labels "
            "LIMIT 1"
        )
        async with self._active_driver.session() as session:
            result = await session.run(cypher, source_id=source_id)
            record = await result.single()

        if record is None:
            return None

        node_props = dict(record["n"])
        labels = list(record["node_labels"])
        # Prefer the filtered label when present; otherwise pick the
        # first returned label. V1 entities only carry one schema label
        # each, so this is deterministic.
        resolved_label = label if label is not None else (labels[0] if labels else "")
        return {"label": resolved_label, **node_props}

    async def get_relationships(
        self,
        source_id: str,
        source_label: str,
        rel_type: str | None = None,
        direction: str = "outgoing",
    ) -> list[dict[str, Any]]:
        """Return relationships incident to the given entity.

        Args:
            source_id: The entity's ``source_id``.
            source_label: The entity's label.
            rel_type: Optional relationship type filter.
            direction: ``"outgoing"`` (default), ``"incoming"``, or
                ``"both"``.

        Returns:
            A list of dicts with keys ``rel_type``, ``properties``,
            ``direction``, and ``neighbor`` (``{"label", **props}``).
            Soft-deleted neighbors are excluded.
        """

        if not is_valid_entity_type(source_label):
            raise SchemaValidationError(f"Unknown entity type: {source_label!r}")
        _validate_source_id(source_id)
        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError(
                f"direction must be 'outgoing', 'incoming', or 'both'; got {direction!r}"
            )

        # Arrow shape is injected as a literal — direction is validated
        # against a small enum set above, so it's safe.
        if direction == "outgoing":
            pattern = f"(s:{source_label} {{source_id: $source_id}})-[r]->(t)"
        elif direction == "incoming":
            pattern = f"(s:{source_label} {{source_id: $source_id}})<-[r]-(t)"
        else:
            pattern = f"(s:{source_label} {{source_id: $source_id}})-[r]-(t)"

        rel_filter = ""
        params: dict[str, Any] = {"source_id": source_id}
        if rel_type is not None:
            rel_filter = " AND type(r) = $rel_type"
            params["rel_type"] = rel_type

        # Include the direction per row so callers of ``direction="both"``
        # can tell outgoing from incoming without re-querying.
        cypher = (
            f"MATCH {pattern} "
            "WHERE t.deleted_at IS NULL "
            f"      AND s.deleted_at IS NULL{rel_filter} "
            "RETURN type(r) AS rel_type, "
            "       properties(r) AS rel_props, "
            "       t AS neighbor, "
            "       labels(t) AS neighbor_labels, "
            "       CASE WHEN startNode(r) = s THEN 'outgoing' ELSE 'incoming' END AS dir"
        )
        async with self._active_driver.session() as session:
            result = await session.run(cypher, **params)
            records = [record async for record in result]

        output: list[dict[str, Any]] = []
        for record in records:
            neighbor_props = dict(record["neighbor"])
            neighbor_labels = list(record["neighbor_labels"])
            neighbor_label = neighbor_labels[0] if neighbor_labels else ""
            output.append(
                {
                    "rel_type": record["rel_type"],
                    "properties": dict(record["rel_props"]),
                    "direction": record["dir"],
                    "neighbor": {"label": neighbor_label, **neighbor_props},
                }
            )
        return output

    async def get_relationships_by_provenance(
        self,
        provenance: str,
        rel_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return edges whose ``provenance`` property matches ``provenance``.

        A typed convenience wrapper for the "audit by provenance" query
        (Requirements 11.4, 11.5): every V2 edge carries exactly one
        ``provenance`` value (``deterministic``, ``llm:confluence``,
        ``llm:pr``, ``llm:steering``, or ``llm:jira``), and this method
        filters on it. When ``rel_type`` is supplied, results are further
        restricted to edges of that relationship type.

        Both the ``provenance`` filter and the optional ``rel_type`` filter
        are applied via Cypher parameters (never string-interpolated), so
        the method is safe against Cypher injection regardless of the
        caller-supplied values.

        Args:
            provenance: The provenance tag to match exactly (e.g.
                ``"llm:steering"``).
            rel_type: Optional relationship-type filter, applied via
                ``type(r) = $rel_type``.
            limit: Maximum number of edges to return.

        Returns:
            A list of dicts, one per matching edge, each with keys
            ``source`` (source entity's ``source_id``), ``target`` (target
            entity's ``source_id``), ``rel_type`` (the relationship type),
            and ``properties`` (the full relationship property bag,
            including ``provenance`` and any ``confidence``). Edges whose
            endpoints are soft-deleted are excluded.
        """

        rel_filter = ""
        params: dict[str, Any] = {"provenance": provenance, "limit": limit}
        if rel_type is not None:
            rel_filter = " AND type(r) = $rel_type"
            params["rel_type"] = rel_type

        cypher = (
            "MATCH (s)-[r]->(t) "
            "WHERE r.provenance = $provenance "
            "      AND s.deleted_at IS NULL "
            f"      AND t.deleted_at IS NULL{rel_filter} "
            "RETURN s.source_id AS source, "
            "       t.source_id AS target, "
            "       type(r) AS rel_type, "
            "       properties(r) AS rel_props "
            "LIMIT $limit"
        )
        async with self._active_driver.session() as session:
            result = await session.run(cypher, **params)
            records = [record async for record in result]

        return [
            {
                "source": record["source"],
                "target": record["target"],
                "rel_type": record["rel_type"],
                "properties": dict(record["rel_props"]),
            }
            for record in records
        ]


__all__ = [
    "GraphStore",
    "ReferentialIntegrityError",
    "SchemaValidationError",
]

"""V1 graph schema for the Engineering Memory Graph.

This module is a pure, side-effect-free declaration of the Neo4j schema:

* Node labels (entity types).
* Relationship types.
* Which ``(source_label, rel_type, target_label)`` tuples are valid
  according to the V1 design.
* Required properties per label.
* Canonical Neo4j constraint names (used by ``setup_neo4j.py`` and by
  any runtime schema assertions).

Importing this module does **not** talk to Neo4j; it only defines
constants and small pure helpers. Runtime code (extractors, graph
store, query layer) should validate payloads against these definitions
before issuing writes.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class EntityType(StrEnum):
    """Node labels used in the V1 Memory_Graph.

    Values match the literal Neo4j label strings (case-sensitive),
    so a :class:`EntityType` can be used directly anywhere a
    Cypher label string is expected.
    """

    SERVICE = "Service"
    REPOSITORY = "Repository"
    TEAM = "Team"
    PERSON = "Person"
    EPIC = "Epic"
    TICKET = "Ticket"
    PR = "PR"
    CONFLUENCE_PAGE = "ConfluencePage"
    CHUNK = "Chunk"


class RelationshipType(StrEnum):
    """Relationship types used in the V1 Memory_Graph.

    Values match the literal Neo4j relationship type strings and
    can be dropped directly into Cypher.
    """

    OWNED_BY = "OWNED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    CONTAINS = "CONTAINS"
    LINKED_TO = "LINKED_TO"
    MODIFIES = "MODIFIES"
    DOCUMENTED_IN = "DOCUMENTED_IN"
    LOCATED_IN = "LOCATED_IN"
    HAS_CHUNK = "HAS_CHUNK"
    DUPLICATE_OF = "DUPLICATE_OF"


# ---------------------------------------------------------------------------
# Required properties per label
# ---------------------------------------------------------------------------

#: Properties every entity type must carry, regardless of label. These are
#: the schema-invariant fields (see Requirement 2.3 and Property 3). Note
#: that ``text_hash`` and ``deleted_at`` are *managed* by the graph layer
#: on write/soft-delete and are therefore not part of the *incoming* payload
#: contract here.
COMMON_REQUIRED_PROPERTIES: Final[frozenset[str]] = frozenset(
    {"source_id", "created_at", "updated_at"}
)

#: Required properties for each label. The value includes
#: :data:`COMMON_REQUIRED_PROPERTIES` plus any label-specific minimums
#: drawn from the design doc's Data Models table.
REQUIRED_PROPERTIES: Final[dict[EntityType, frozenset[str]]] = {
    EntityType.SERVICE: COMMON_REQUIRED_PROPERTIES | {"name"},
    EntityType.REPOSITORY: COMMON_REQUIRED_PROPERTIES | {"name"},
    EntityType.TEAM: COMMON_REQUIRED_PROPERTIES | {"name"},
    # Person entities may come from multiple sources that don't all supply
    # name/email consistently; only the universal fields are mandated.
    EntityType.PERSON: COMMON_REQUIRED_PROPERTIES,
    EntityType.EPIC: COMMON_REQUIRED_PROPERTIES | {"key", "title"},
    EntityType.TICKET: COMMON_REQUIRED_PROPERTIES | {"key", "title"},
    EntityType.PR: COMMON_REQUIRED_PROPERTIES | {"number", "title"},
    EntityType.CONFLUENCE_PAGE: COMMON_REQUIRED_PROPERTIES | {"title"},
    # Chunk nodes carry the join-back key to their parent document plus the
    # ordering/typing metadata needed for chunk-based retrieval (see the
    # RAG Pipeline V2 design "Chunk node (graph)" data model).
    EntityType.CHUNK: COMMON_REQUIRED_PROPERTIES
    | {"parent_source_id", "chunk_index", "doc_type"},
}


# ---------------------------------------------------------------------------
# Valid (source_label, rel_type, target_label) tuples
# ---------------------------------------------------------------------------

#: The V1 relationship whitelist. Every entry is a directed
#: ``(source, relationship, target)`` tuple exactly matching the Data
#: Models section of the design document. Writes that don't match one of
#: these tuples are considered schema violations (Requirement 2.4).
VALID_RELATIONSHIPS: Final[frozenset[tuple[EntityType, RelationshipType, EntityType]]] = (
    frozenset(
        {
            (EntityType.SERVICE, RelationshipType.OWNED_BY, EntityType.TEAM),
            (EntityType.REPOSITORY, RelationshipType.OWNED_BY, EntityType.TEAM),
            (EntityType.SERVICE, RelationshipType.DEPENDS_ON, EntityType.SERVICE),
            (EntityType.REPOSITORY, RelationshipType.CONTAINS, EntityType.SERVICE),
            (EntityType.TICKET, RelationshipType.LINKED_TO, EntityType.SERVICE),
            (EntityType.EPIC, RelationshipType.LINKED_TO, EntityType.SERVICE),
            (EntityType.PR, RelationshipType.MODIFIES, EntityType.REPOSITORY),
            (EntityType.SERVICE, RelationshipType.DOCUMENTED_IN, EntityType.CONFLUENCE_PAGE),
            (EntityType.PERSON, RelationshipType.LOCATED_IN, EntityType.TEAM),
            # RAG Pipeline V2 chunk graph: a parent document (stored as a
            # ConfluencePage entity) owns its chunks, and near-duplicate
            # chunks point at their canonical counterpart.
            (EntityType.CONFLUENCE_PAGE, RelationshipType.HAS_CHUNK, EntityType.CHUNK),
            (EntityType.CHUNK, RelationshipType.DUPLICATE_OF, EntityType.CHUNK),
        }
    )
)


# ---------------------------------------------------------------------------
# Canonical constraint names (used by the setup script)
# ---------------------------------------------------------------------------

#: Canonical Neo4j constraint name per label, matching the design doc.
#: Kept here (rather than derived from ``EntityType.name``) so we don't
#: end up with ``confluencepage_unique`` instead of ``confluence_unique``.
UNIQUE_CONSTRAINT_NAMES: Final[dict[EntityType, str]] = {
    EntityType.SERVICE: "service_unique",
    EntityType.REPOSITORY: "repository_unique",
    EntityType.TEAM: "team_unique",
    EntityType.PERSON: "person_unique",
    EntityType.EPIC: "epic_unique",
    EntityType.TICKET: "ticket_unique",
    EntityType.PR: "pr_unique",
    EntityType.CONFLUENCE_PAGE: "confluence_unique",
    EntityType.CHUNK: "chunk_unique",
}


# ---------------------------------------------------------------------------
# Internal lookup sets (built once at import time)
# ---------------------------------------------------------------------------

_ENTITY_TYPE_VALUES: Final[frozenset[str]] = frozenset(e.value for e in EntityType)
_RELATIONSHIP_TYPE_VALUES: Final[frozenset[str]] = frozenset(r.value for r in RelationshipType)
_VALID_RELATIONSHIP_STRINGS: Final[frozenset[tuple[str, str, str]]] = frozenset(
    (s.value, r.value, t.value) for (s, r, t) in VALID_RELATIONSHIPS
)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def is_valid_entity_type(label: str) -> bool:
    """Return ``True`` if ``label`` is a known V1 entity type.

    Case-sensitive (labels match Neo4j conventions, e.g. ``"Service"``
    is valid but ``"service"`` is not).
    """

    return label in _ENTITY_TYPE_VALUES


def is_valid_relationship_type(rel_type: str) -> bool:
    """Return ``True`` if ``rel_type`` is a known V1 relationship type.

    Case-sensitive; Neo4j relationship types are conventionally
    ``UPPER_SNAKE_CASE``.
    """

    return rel_type in _RELATIONSHIP_TYPE_VALUES


def is_valid_relationship(source_label: str, rel_type: str, target_label: str) -> bool:
    """Return ``True`` if the ``(source, rel, target)`` tuple is allowed.

    The tuple is allowed iff it appears in :data:`VALID_RELATIONSHIPS`.
    Any combination outside the whitelist — including ones where each
    individual component is otherwise valid — returns ``False``.
    """

    return (source_label, rel_type, target_label) in _VALID_RELATIONSHIP_STRINGS


def required_properties(label: str | EntityType) -> frozenset[str]:
    """Return the set of required property names for a given label.

    Raises:
        ValueError: If ``label`` is not a known V1 entity type.
    """

    try:
        entity = label if isinstance(label, EntityType) else EntityType(label)
    except ValueError as exc:
        raise ValueError(f"Unknown entity type: {label!r}") from exc
    return REQUIRED_PROPERTIES[entity]


__all__ = [
    "COMMON_REQUIRED_PROPERTIES",
    "EntityType",
    "REQUIRED_PROPERTIES",
    "RelationshipType",
    "UNIQUE_CONSTRAINT_NAMES",
    "VALID_RELATIONSHIPS",
    "is_valid_entity_type",
    "is_valid_relationship",
    "is_valid_relationship_type",
    "required_properties",
]

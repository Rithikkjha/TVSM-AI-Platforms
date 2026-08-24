"""Unit tests for :mod:`src.models.schema`.

These tests pin down the V1 graph schema contract: which entity and
relationship types exist, which ``(source, rel, target)`` tuples are
valid, and that the validation helpers behave correctly.
"""

from __future__ import annotations

import pytest
from storage.graph.schema import (
    COMMON_REQUIRED_PROPERTIES,
    REQUIRED_PROPERTIES,
    UNIQUE_CONSTRAINT_NAMES,
    VALID_RELATIONSHIPS,
    EntityType,
    RelationshipType,
    is_valid_entity_type,
    is_valid_relationship,
    is_valid_relationship_type,
    required_properties,
)

# ---------------------------------------------------------------------------
# Entity types
# ---------------------------------------------------------------------------


def test_entity_type_contains_all_v1_labels() -> None:
    """Every V1 node label from the design doc must be enumerated."""

    expected = {
        "Service",
        "Repository",
        "Team",
        "Person",
        "Epic",
        "Ticket",
        "PR",
        "ConfluencePage",
    }
    assert {e.value for e in EntityType} == expected


def test_entity_type_values_match_neo4j_label_casing() -> None:
    """Enum values match the literal Cypher label strings (PascalCase)."""

    assert EntityType.SERVICE.value == "Service"
    assert EntityType.CONFLUENCE_PAGE.value == "ConfluencePage"
    assert EntityType.PR.value == "PR"


# ---------------------------------------------------------------------------
# Relationship types
# ---------------------------------------------------------------------------


def test_relationship_type_contains_all_v1_rel_types() -> None:
    """Every V1 relationship type from the design doc must be enumerated."""

    expected = {
        "OWNED_BY",
        "DEPENDS_ON",
        "CONTAINS",
        "LINKED_TO",
        "MODIFIES",
        "DOCUMENTED_IN",
        "LOCATED_IN",
    }
    assert {r.value for r in RelationshipType} == expected


# ---------------------------------------------------------------------------
# Valid relationship tuples
# ---------------------------------------------------------------------------


EXPECTED_VALID_TUPLES: set[tuple[EntityType, RelationshipType, EntityType]] = {
    (EntityType.SERVICE, RelationshipType.OWNED_BY, EntityType.TEAM),
    (EntityType.REPOSITORY, RelationshipType.OWNED_BY, EntityType.TEAM),
    (EntityType.SERVICE, RelationshipType.DEPENDS_ON, EntityType.SERVICE),
    (EntityType.REPOSITORY, RelationshipType.CONTAINS, EntityType.SERVICE),
    (EntityType.TICKET, RelationshipType.LINKED_TO, EntityType.SERVICE),
    (EntityType.EPIC, RelationshipType.LINKED_TO, EntityType.SERVICE),
    (EntityType.PR, RelationshipType.MODIFIES, EntityType.REPOSITORY),
    (EntityType.SERVICE, RelationshipType.DOCUMENTED_IN, EntityType.CONFLUENCE_PAGE),
    (EntityType.PERSON, RelationshipType.LOCATED_IN, EntityType.TEAM),
}


def test_valid_relationships_set_matches_design_doc() -> None:
    """The whitelist must exactly match the Data Models section."""

    assert set(VALID_RELATIONSHIPS) == EXPECTED_VALID_TUPLES


# ---------------------------------------------------------------------------
# Required properties
# ---------------------------------------------------------------------------


def test_common_required_properties_are_source_id_and_timestamps() -> None:
    """Every entity carries at least source_id, created_at, updated_at."""

    assert frozenset({"source_id", "created_at", "updated_at"}) == COMMON_REQUIRED_PROPERTIES


def test_required_properties_defined_for_every_entity_type() -> None:
    """Each enum member has a corresponding required-properties entry."""

    assert set(REQUIRED_PROPERTIES.keys()) == set(EntityType)


def test_required_properties_include_common_for_every_entity() -> None:
    """Every label's required set is a superset of the common required set."""

    for entity, props in REQUIRED_PROPERTIES.items():
        assert COMMON_REQUIRED_PROPERTIES.issubset(props), entity


def test_required_properties_labels_have_name_or_title() -> None:
    """Text-bearing entities advertise a sensible display field."""

    assert "name" in REQUIRED_PROPERTIES[EntityType.SERVICE]
    assert "name" in REQUIRED_PROPERTIES[EntityType.REPOSITORY]
    assert "name" in REQUIRED_PROPERTIES[EntityType.TEAM]
    assert "title" in REQUIRED_PROPERTIES[EntityType.EPIC]
    assert "title" in REQUIRED_PROPERTIES[EntityType.TICKET]
    assert "title" in REQUIRED_PROPERTIES[EntityType.PR]
    assert "title" in REQUIRED_PROPERTIES[EntityType.CONFLUENCE_PAGE]


def test_required_properties_helper_accepts_enum_and_string() -> None:
    """`required_properties` is symmetric over label and enum forms."""

    assert required_properties(EntityType.SERVICE) == REQUIRED_PROPERTIES[EntityType.SERVICE]
    assert required_properties("Service") == REQUIRED_PROPERTIES[EntityType.SERVICE]


def test_required_properties_helper_rejects_unknown_label() -> None:
    """`required_properties` raises ValueError for an unknown label."""

    with pytest.raises(ValueError, match="Unknown entity type"):
        required_properties("NotAType")


# ---------------------------------------------------------------------------
# Constraint names
# ---------------------------------------------------------------------------


def test_unique_constraint_names_defined_for_every_entity_type() -> None:
    """There is exactly one canonical constraint name per label."""

    assert set(UNIQUE_CONSTRAINT_NAMES.keys()) == set(EntityType)
    # Design doc uses `confluence_unique`, not `confluencepage_unique`.
    assert UNIQUE_CONSTRAINT_NAMES[EntityType.CONFLUENCE_PAGE] == "confluence_unique"
    assert UNIQUE_CONSTRAINT_NAMES[EntityType.PR] == "pr_unique"
    # Names are distinct so Neo4j accepts creating all eight.
    assert len(set(UNIQUE_CONSTRAINT_NAMES.values())) == len(EntityType)


# ---------------------------------------------------------------------------
# Helper: is_valid_entity_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label",
    [
        "Service",
        "Repository",
        "Team",
        "Person",
        "Epic",
        "Ticket",
        "PR",
        "ConfluencePage",
    ],
)
def test_is_valid_entity_type_accepts_known_labels(label: str) -> None:
    assert is_valid_entity_type(label) is True


@pytest.mark.parametrize(
    "label",
    [
        "",
        "service",  # lowercase not accepted
        "SERVICE",
        "Widget",
        "confluence_page",
    ],
)
def test_is_valid_entity_type_rejects_unknown_labels(label: str) -> None:
    assert is_valid_entity_type(label) is False


# ---------------------------------------------------------------------------
# Helper: is_valid_relationship_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "OWNED_BY",
        "DEPENDS_ON",
        "CONTAINS",
        "LINKED_TO",
        "MODIFIES",
        "DOCUMENTED_IN",
        "LOCATED_IN",
    ],
)
def test_is_valid_relationship_type_accepts_known_rels(rel: str) -> None:
    assert is_valid_relationship_type(rel) is True


@pytest.mark.parametrize(
    "rel",
    [
        "",
        "owned_by",  # lowercase not accepted
        "OWNS",
        "RELATED_TO",
    ],
)
def test_is_valid_relationship_type_rejects_unknown_rels(rel: str) -> None:
    assert is_valid_relationship_type(rel) is False


# ---------------------------------------------------------------------------
# Helper: is_valid_relationship
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "triple",
    [
        ("Service", "OWNED_BY", "Team"),
        ("Repository", "OWNED_BY", "Team"),
        ("Service", "DEPENDS_ON", "Service"),
        ("Repository", "CONTAINS", "Service"),
        ("Ticket", "LINKED_TO", "Service"),
        ("Epic", "LINKED_TO", "Service"),
        ("PR", "MODIFIES", "Repository"),
        ("Service", "DOCUMENTED_IN", "ConfluencePage"),
        ("Person", "LOCATED_IN", "Team"),
    ],
)
def test_is_valid_relationship_accepts_whitelisted_triples(
    triple: tuple[str, str, str],
) -> None:
    assert is_valid_relationship(*triple) is True


@pytest.mark.parametrize(
    "triple",
    [
        # Swapped direction
        ("Team", "OWNED_BY", "Service"),
        # Right direction but wrong endpoint types
        ("Person", "OWNED_BY", "Team"),
        ("Service", "DEPENDS_ON", "Team"),
        # Unknown label
        ("Widget", "OWNED_BY", "Team"),
        # Unknown relationship type
        ("Service", "OWNS", "Team"),
        # Empty strings
        ("", "", ""),
    ],
)
def test_is_valid_relationship_rejects_invalid_triples(
    triple: tuple[str, str, str],
) -> None:
    assert is_valid_relationship(*triple) is False


def test_is_valid_relationship_accepts_enum_values_via_str_enum() -> None:
    """EntityType / RelationshipType inherit from StrEnum so they
    equal their string values and can be passed directly."""

    assert is_valid_relationship(
        EntityType.SERVICE.value,
        RelationshipType.DEPENDS_ON.value,
        EntityType.SERVICE.value,
    )


# ---------------------------------------------------------------------------
# Import side-effect check
# ---------------------------------------------------------------------------


def test_schema_module_imports_without_side_effects() -> None:
    """Re-importing the module must not raise and must not require Neo4j."""

    # If this import had side effects (e.g. a driver connection) the
    # previous imports at the top of this file would already have raised.
    # We still assert the module is re-importable and exposes the
    # expected public API.
    import importlib

    import storage.graph.schema as schema_mod

    reloaded = importlib.reload(schema_mod)
    assert hasattr(reloaded, "EntityType")
    assert hasattr(reloaded, "RelationshipType")
    assert hasattr(reloaded, "VALID_RELATIONSHIPS")

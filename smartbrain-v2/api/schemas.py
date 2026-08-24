"""Pydantic response schemas for the Query API.

Defines the response models used by the V1 query endpoints. These models
ensure consistent JSON output shapes and provide automatic OpenAPI
documentation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EntityRef(BaseModel):
    """A lightweight reference to a related entity.

    Used in service query responses to represent owners, dependencies,
    tickets, and documents without returning the full entity payload.
    """

    source_id: str
    name: str | None = None
    title: str | None = None

    # Additional fields that vary by entity type
    key: str | None = None
    status: str | None = None
    priority: str | None = None
    url: str | None = None
    dependency_type: str | None = None


class ServiceResponse(BaseModel):
    """Response model for GET /v1/services/{name}.

    Contains the full service properties along with all related entities
    fetched via graph traversal.
    """

    service: dict[str, Any]
    owners: list[EntityRef]
    upstream_dependencies: list[EntityRef]
    downstream_dependents: list[EntityRef]
    linked_tickets: list[EntityRef]
    documents: list[EntityRef]
    staleness: str | None = None


class AffectedService(BaseModel):
    """A service affected by changes to the queried service.

    Used in impact analysis responses to represent services that
    transitively depend on the queried service.
    """

    source_id: str
    name: str
    hops: int  # 1 or 2


class ImpactResponse(BaseModel):
    """Response model for GET /v1/services/{name}/impact.

    Contains the transitive dependency set (up to 2 hops) with
    linked epics and tickets for all affected services.
    """

    service: str  # the queried service name
    max_hops: int  # always 2 for V1
    affected_services: list[AffectedService]
    linked_epics: list[EntityRef]
    linked_tickets: list[EntityRef]


class SearchHit(BaseModel):
    """A single scored result from the search endpoint.

    Represents an entity matched by vector similarity search.
    """

    source_id: str
    entity_type: str
    name: str | None = None
    title: str | None = None
    score: float


class SearchResponse(BaseModel):
    """Response model for GET /v1/search.

    Contains the original query, scored results, and total count.
    """

    query: str
    results: list[SearchHit]
    total: int


class ErrorResponse(BaseModel):
    """Standard error response body."""

    error: str
    message: str


# ---------------------------------------------------------------------------
# Ask endpoint schemas
# ---------------------------------------------------------------------------


class AskRequest(BaseModel):
    """Request body for POST /v1/ask."""

    question: str


class Citation(BaseModel):
    """A citation referencing a graph entity used to answer a question."""

    source_id: str
    entity_type: str
    name: str | None = None
    title: str | None = None


class AskResponse(BaseModel):
    """Response model for POST /v1/ask.

    When the graph has sufficient context, ``answer`` contains the LLM-generated
    response and ``citations`` lists the entities referenced. When context is
    insufficient, ``answer`` is None and ``message`` explains why.
    """

    answer: str | None = None
    message: str | None = None
    citations: list[Citation] = []

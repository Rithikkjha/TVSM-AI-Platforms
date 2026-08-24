"""Pydantic models for the .service-manifest.yaml schema."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Endpoint(BaseModel):
    """A single API endpoint exposed by the service."""

    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, PATCH)")
    path: str = Field(..., description="Route path (e.g., /api/v1/booking/:id)")
    description: str = Field(default="", description="What this endpoint does")
    file: str = Field(default="", description="Source file:line where defined")


class HttpDependency(BaseModel):
    """An outbound HTTP call to another service."""

    target_service: str = Field(..., description="Name of the service being called")
    purpose: str = Field(default="", description="Why this call is made")
    evidence: str = Field(default="", description="file:line + code snippet")
    confidence: Literal["high", "medium", "low"] = Field(default="low")


class ServiceBusPublish(BaseModel):
    """A topic this service publishes to."""

    topic: str = Field(..., description="Topic/queue name")
    evidence: str = Field(default="", description="file:line where publisher is defined")
    confidence: Literal["high", "medium", "low"] = Field(default="low")


class ServiceBusSubscribe(BaseModel):
    """A topic this service subscribes to."""

    topic: str = Field(..., description="Topic/queue name")
    source_service: str = Field(default="unknown", description="Which service publishes to this topic")
    evidence: str = Field(default="", description="file:line where listener is defined")
    confidence: Literal["high", "medium", "low"] = Field(default="low")


class BuildDependency(BaseModel):
    """A build-time dependency (npm package, maven artifact, nuget package)."""

    name: str
    version: str = ""
    type: str = Field(default="", description="npm, maven, nuget, pip")


class DatabaseConnection(BaseModel):
    """A database this service connects to."""

    type: str = Field(..., description="mongodb, mysql, postgres, redis, etc.")
    name: str = Field(default="", description="Database name if detectable")
    evidence: str = Field(default="", description="file:line where connection is configured")


class KeyModule(BaseModel):
    """A key source file with its purpose."""

    file: str = Field(..., description="Relative file path")
    purpose: str = Field(default="", description="What this module does (from docstring/comment)")


class GitActivity(BaseModel):
    """Recent git activity for the repo."""

    last_commit_date: str = ""
    last_commit_author: str = ""
    last_commit_message: str = ""
    active_contributors_30d: list[str] = Field(default_factory=list)
    commit_frequency: str = Field(default="", description="e.g., ~12/week")


class Dependencies(BaseModel):
    """All dependency types for a service."""

    http_calls: list[HttpDependency] = Field(default_factory=list)
    service_bus_publishes: list[ServiceBusPublish] = Field(default_factory=list)
    service_bus_subscribes: list[ServiceBusSubscribe] = Field(default_factory=list)
    build: list[BuildDependency] = Field(default_factory=list)
    databases: list[DatabaseConnection] = Field(default_factory=list)


class ServiceManifest(BaseModel):
    """Complete manifest for a single service/repo."""

    # Metadata
    scanned_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    review_status: str = "DRAFT"

    # Service identity
    name: str = Field(..., description="Repo/service name")
    language: str = Field(default="unknown", description="java, node, dotnet, python, unknown")
    framework: str = Field(default="", description="e.g., spring-boot@3.5, express@4.18, nestjs@11")
    owner_team: str = Field(default="", description="Team name from CODEOWNERS or git")
    contacts: list[str] = Field(default_factory=list, description="Email addresses")
    purpose: str = Field(default="", description="What this service does (from README)")
    domain_keywords: list[str] = Field(default_factory=list, description="Business domain terms")

    # Code context
    directory_tree: str = Field(default="", description="Top-level directory structure")
    key_modules: list[KeyModule] = Field(default_factory=list)
    git_activity: GitActivity = Field(default_factory=GitActivity)

    # API surface
    api_base_path: str = Field(default="", description="Common prefix for all endpoints")
    endpoints: list[Endpoint] = Field(default_factory=list)

    # Dependencies
    dependencies: Dependencies = Field(default_factory=Dependencies)

    # Configuration
    env_vars: list[str] = Field(default_factory=list, description="Required environment variables")
    config_files: list[str] = Field(default_factory=list, description="Config file paths found")

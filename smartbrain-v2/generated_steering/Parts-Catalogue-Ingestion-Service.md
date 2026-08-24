# Steering File: Parts-Catalogue-Ingestion-Service

*Auto-generated from repository analysis*

# Parts Catalogue Ingestion Service Overview

## Service Overview
- **Purpose**: The Parts Catalogue Ingestion Service is a Spring Boot microservice designed to ingest parts catalogue data from external APIs, transform it, and store it in a Nebula Graph database while also indexing it in OpenSearch for efficient search capabilities.
- **Key Responsibilities**:
  - Fetching parts catalogue data from external sources (e.g., Norton, TVS).
  - Transforming and persisting data into Nebula Graph.
  - Indexing data in OpenSearch for search and retrieval.
  - Supporting both manual and scheduled ingestion workflows.
  - Managing distributed locks to prevent concurrent ingestion conflicts.
  - Providing region-based configuration for multi-deployment scenarios.

## Tech Stack
- **Language and Version**: Java 21
- **Framework**: Spring Boot 3.5.8
- **Database**: 
  - Nebula Graph (3.8.4) for graph data storage.
  - OpenSearch (3.3.0) for search capabilities.
- **Key Libraries/Dependencies**:
  - Nebula Graph Client (3.8.4)
  - OpenSearch Client (3.3.0)
  - Resilience4j (2.2.0) for circuit breakers and retry logic.
  - Springdoc OpenAPI (2.8.14) for API documentation.
  - Lombok (1.18.42) for reducing boilerplate code.

## API Endpoints / Routes
- **IngestionController**:
  - **POST /ingest**: Triggers the ingestion process.
  - **GET /ingest/status**: Retrieves the status of the ingestion process.
- **RegionConfigurationController**:
  - **GET /regions**: Fetches the current region configurations.
  - **POST /regions**: Updates region configurations.

## Architecture
- **Code Organization**: The code is organized into a layered architecture:
  1. **Presentation Layer** (`controller/`): Handles HTTP requests and responses.
  2. **Business Layer** (`service/`): Contains business logic and orchestration.
  3. **Data Access Layer** (`repository/`): Manages database and search engine operations.
  4. **Domain Layer** (`model/`): Defines domain entities and value objects.
- **Key Design Patterns**:
  - Strategy Pattern for different data source implementations.
  - Factory Pattern for service instantiation based on data source type.
  - Observer Pattern for event-driven configuration updates.
- **Entry Point**: The main application class is `IngestionServiceApplication.java`.

## Dependencies (External Services)
- **External APIs**: 
  - Norton API
  - TVS API
- **Databases/Caches**:
  - Nebula Graph for storing catalogue data.
  - OpenSearch for indexing and searching catalogue data.

## Configuration
- **Key Environment Variables**:
  - `EXPOSED_PORT`
  - `NEBULA_HOSTS`
  - `NEBULA_PORT`
  - `NEBULA_SPACE`
  - `NEBULA_USERNAME`
  - `NEBULA_PASSWORD`
  - `ACD_TVS_URL`, `ACD_TVS_ENDPOINT`, `ACD_TVS_API_KEY`
  - `ACD_NORTON_URL`, `ACD_NORTON_ENDPOINT`, `ACD_NORTON_API_KEY`
  - `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD`
- **Configuration Files**:
  - `application.properties`: Main configuration file.
  - `application-dev.properties`: Development profile configuration.
  - `regions.yaml`: Region configuration file for multi-region setup.

## Deployment
- **Deployment Method**: The application is deployed using Docker.
- **Ports Exposed**: The application exposes port `2001`.
- **Health Check Endpoints**: Health checks are available via Spring Boot Actuator at `/actuator/health` and `/actuator/metrics`.

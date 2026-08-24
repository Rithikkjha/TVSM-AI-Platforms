# Steering File: Parts-Catalogue-Service

*Auto-generated from repository analysis*

# Parts Catalogue Service Overview

## Service Overview
- **Purpose**: The Parts Catalogue Service is a Spring Boot microservice designed to manage product catalogues, parts inventory, and their hierarchical relationships using graph databases. It provides efficient traversal of product hierarchies and advanced search capabilities.
- **Key Responsibilities**:
  - Manage product relationships and hierarchies using NebulaGraph.
  - Provide full-text search capabilities through OpenSearch.
  - Handle complex product data structures, including assemblies, kits, and variants.
  - Ensure data integrity with input validation and sanitization.
  - Implement resilience and fault tolerance in external service calls.
  - Expose a comprehensive RESTful API for product operations.

## Tech Stack
- **Language and Version**: Java 21
- **Framework**: Spring Boot 3.5.8
- **Database**: 
  - NebulaGraph (Graph database for product relationships)
  - OpenSearch (Distributed search engine for full-text search)
- **Message Queue / Event Bus**: Not determinable from available files
- **Key Libraries/Dependencies**:
  - Spring Boot Starter Web
  - Spring Data JPA
  - Spring Boot Actuator
  - NebulaGraph Client
  - OpenSearch Java Client
  - Resilience4j
  - Caffeine (Caching)
  - SpringDoc OpenAPI (API documentation)

## API Endpoints / Routes
### Entities APIs (`/api`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles` | Get vehicles by product ID |
| GET | `/api/models` | Get models by vehicle ID |
| GET | `/api/variants` | Get variants by model ID |
| GET | `/api/catalogues` | Get catalogues by variant ID |
| GET | `/api/kits` | Get kits by catalogue ID |
| GET | `/api/assemblies` | Get assemblies by kit ID |
| GET | `/api/parts` | Get parts by assembly ID |

### Search APIs (`/api/search`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search` | Search parts and their hierarchy with optional filters and pagination |

### Product Details APIs (`/api/products`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/kits-with-assemblies` | Get kits with assemblies by product name |

### Traversal APIs (`/api`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reverseHierarchy/part` | Get reverse hierarchy from part number or catalog SKU ID |

### Chart APIs (`/api/chart`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chart/product` | Get chart data for a product by name |
| GET | `/api/chart/vehicle` | Get chart data for a vehicle by name |
| GET | `/api/chart/model` | Get chart data for a model by name |

## Architecture
- **Code Organization**: The code is organized in a layered architecture:
  - **Controller Layer**: Handles HTTP requests and responses.
  - **Service Layer**: Contains business logic.
  - **Repository Layer**: Manages data access (to NebulaGraph and OpenSearch).
  - **Model/Entity Layer**: Defines data structures.
  - **Configuration Layer**: Contains external service configurations.
- **Key Design Patterns**: Layered architecture, Circuit Breaker pattern (via Resilience4j).
- **Entry Point**: The main application class is `ProductCatalogue.java`.

## Dependencies (External Services)
- **External Services**:
  - NebulaGraph (for graph-based queries)
  - OpenSearch (for search capabilities)
- **Databases/Caches**:
  - NebulaGraph (Graph database)
  - OpenSearch (Search engine)

## Configuration
- **Key Environment Variables**:
  - `NEBULA_HOSTS`
  - `NEBULA_PORT`
  - `NEBULA_SPACE`
  - `NEBULA_USERNAME`
  - `NEBULA_PASSWORD`
  - `OPENSEARCH_HOST`
  - `OPENSEARCH_PORT`
  - `OPENSEARCH_USERNAME`
  - `OPENSEARCH_PASSWORD`
- **Configuration Files**:
  - `src/main/resources/application.properties` (Main configuration file)

## Deployment
- **Deployment Method**: Docker (multi-stage build)
- **Ports Exposed**: 3001
- **Health Check Endpoints**: 
  - `http://localhost:3001/actuator/health`
  - Additional metrics available at `http://localhost:3001/actuator/metrics`

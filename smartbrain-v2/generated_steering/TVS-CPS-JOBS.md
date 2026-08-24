# Steering File: TVS-CPS-JOBS

*Auto-generated from repository analysis*

# TVSM-CPS-JOBS Repository Summary

## Service Overview
- **Purpose**: The TVSM-CPS-JOBS service is an Order Service built using Spring Boot, designed to manage orders within a multi-tenant architecture. It provides RESTful APIs for CRUD operations, pagination, sorting, and JWT-based security.
- **Key Responsibilities**:
  - Manage orders with support for multi-tenancy.
  - Provide secure access to APIs using JWT authentication.
  - Generate OpenAPI/Swagger documentation for API endpoints.
  - Integrate with PostgreSQL for data persistence.
  - Support health checks and monitoring via Spring Boot Actuator.

## Tech Stack
- **Language and Version**: Java 21 or higher
- **Framework**: Spring Boot
- **Database**: PostgreSQL
- **Message Queue / Event Bus**: Not determinable from available files
- **Key Libraries/Dependencies**:
  - Spring Boot Starters (Web, Data JPA, Validation, Actuator)
  - Lombok
  - MapStruct
  - Springdoc OpenAPI for Swagger documentation
  - PostgreSQL JDBC Driver

## API Endpoints / Routes
- **Not explicitly listed in the provided files**. However, the service exposes:
  - **Health Check**: `GET /api/health`
  - **Swagger UI**: `GET /swagger-ui.html`
  - **OpenAPI Specification**: `GET /api-docs`

## Architecture
- **Code Organization**: The code is organized into a standard Maven structure with separate directories for main application code (`src/main/java`), resources (`src/main/resources`), and test code (`src/test`).
- **Key Design Patterns Used**: Not explicitly mentioned, but likely includes MVC (Model-View-Controller) and Repository patterns due to the use of Spring Boot and JPA.
- **Entry Point(s)**: The main application entry point is defined in the `pom.xml` as `com.tvsm.jobs.TVSCPSJobsApplication`.

## Dependencies (External Services)
- **Other Services/APIs**: 
  - Integrates with various external APIs for order management and ERP synchronization (specific endpoints are defined in `application.yml`).
- **Databases/Caches**: 
  - Connects to a PostgreSQL database for data storage.

## Configuration
- **Key Environment Variables**: 
  - `JWT_PUBLIC_KEY_1`, `SERVICE_AUTH_TOKEN_CLIENT_ID`, `SERVICE_AUTH_TOKEN_CLIENT_SECRET`, `AZURE_STORAGE_CONNECTION_STRING`, etc.
- **Configuration Files**: 
  - Main configuration is in `src/main/resources/application.yml`, which includes settings for database, logging, security, and external service integrations.

## Deployment
- **How it's Deployed**: The service is deployed using Docker, as indicated by the presence of a `Dockerfile`.
- **Ports Exposed**: The application listens on port `8080`.
- **Health Check Endpoints**: The health check endpoint is available at `/api/health`.

This summary provides a structured overview of the TVSM-CPS-JOBS repository, detailing its purpose, technology stack, architecture, and deployment strategy based on the available files.

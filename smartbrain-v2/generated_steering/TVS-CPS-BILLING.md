# Steering File: TVS-CPS-BILLING

*Auto-generated from repository analysis*

# TVS-CPS-BILLING Repository Summary

## Service Overview
- **Purpose**: The TVS-CPS-BILLING service is a Spring Boot application designed to manage orders within a multi-tenant architecture. It provides RESTful APIs for CRUD operations, pagination, sorting, and JWT-based security.
- **Key Responsibilities**:
  - Manage order entities with support for multi-tenancy.
  - Provide secure access to APIs using JWT authentication.
  - Expose OpenAPI/Swagger documentation for API consumers.
  - Integrate with a PostgreSQL database for data persistence.

## Tech Stack
- **Language and Version**: Java 21 or higher
- **Framework**: Spring Boot
- **Database**: PostgreSQL
- **Key Libraries/Dependencies**:
  - Spring Boot Starters (Web, Data JPA, Validation, Actuator)
  - Lombok for reducing boilerplate code
  - MapStruct for DTO mapping
  - Springdoc OpenAPI for API documentation

## API Endpoints / Routes
- **Health Check**: 
  - **Method**: GET
  - **Path**: `/api/health`
  - **Description**: Returns the health status of the application.
- **Swagger UI**: 
  - **Method**: GET
  - **Path**: `/swagger-ui.html`
  - **Description**: Provides a user interface for exploring the API.
- **OpenAPI Specification**: 
  - **Method**: GET
  - **Path**: `/api-docs`
  - **Description**: Returns the OpenAPI documentation for the service.

## Architecture
- **Code Organization**: The code is organized into a standard Spring Boot structure with separate directories for main application code (`src/main/java`), resources (`src/main/resources`), and test code (`src/test/java`).
- **Key Design Patterns Used**: 
  - Multi-tenancy for data isolation.
  - Repository pattern for data access.
  - DTO pattern for data transfer.
- **Entry Point**: The main application entry point is defined in `com.tvsm.billing.TVSCPSBillingApplication`.

## Dependencies (External Services)
- **Database**: Connects to a PostgreSQL database for data storage.
- **Cloud Storage**: Optionally connects to Azure for cloud storage capabilities.

## Configuration
- **Key Environment Variables**:
  - `BIL_JWT_PUBLIC_KEY_1`: Public key for JWT validation.
  - `BIL_DB_USERNAME`: Database username.
  - `BIL_DB_PASSWORD`: Database password.
  - `INV_AZURE_STORAGE_CONNECTION_STRING`: Connection string for Azure storage.
- **Configuration Files**: The main configuration is located in `src/main/resources/application.yml`.

## Deployment
- **Deployment Method**: The application is deployed using Docker.
- **Ports Exposed**: The application listens on port `8081`.
- **Health Check Endpoint**: The health check can be accessed at `/api/health`.

This summary provides a structured overview of the TVS-CPS-BILLING service, detailing its purpose, technology stack, API endpoints, architecture, dependencies, configuration, and deployment strategy.

# Steering File: TVS-CPS-INVENTORY

*Auto-generated from repository analysis*

# TVSM-CPS-INVENTORY Repository Summary

## Service Overview
- **Purpose**: The TVSM-CPS-INVENTORY service is a Spring Boot application designed to manage inventory orders. It provides a RESTful API for CRUD operations, pagination, sorting, and multi-tenancy support.
- **Key Responsibilities**:
  - Manage inventory orders with tenant-specific data isolation.
  - Provide JWT-based authentication and authorization.
  - Expose OpenAPI/Swagger documentation for API consumers.
  - Integrate with a PostgreSQL database for data persistence.

## Tech Stack
- **Language and Version**: Java 21 or higher
- **Framework**: Spring Boot
- **Database**: PostgreSQL
- **Key Libraries/Dependencies**:
  - Spring Boot Starters (Web, Data JPA, Validation, Actuator)
  - Lombok for reduced boilerplate code
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
  - **Description**: Provides the OpenAPI documentation for the API.

## Architecture
- **Code Organization**: The code is organized into a standard Spring Boot structure with separate directories for main application code (`src/main/java`), resources (`src/main/resources`), and test code (`src/test/java`).
- **Key Design Patterns Used**: 
  - Multi-tenancy architecture for data isolation.
  - Repository pattern for data access.
  - DTO pattern for data transfer.
- **Entry Point**: The main application entry point is defined in `com.tvsm.inventory.TVSCPSInventoryApplication`.

## Dependencies (External Services)
- **Database**: Connects to a PostgreSQL database for data storage.
- **Cloud Storage**: Configured to use Azure for cloud storage capabilities.

## Configuration
- **Key Environment Variables**:
  - `INV_JWT_PUBLIC_KEY_1`: Public key for JWT validation.
  - `INV_DB_USERNAME`: Database username.
  - `INV_DB_PASSWORD`: Database password.
  - `INV_AZURE_STORAGE_CONNECTION_STRING`: Connection string for Azure storage.
- **Configuration Files**: The main configuration is located in `src/main/resources/application.yml`, which includes settings for database connections, logging, security, and API documentation.

## Deployment
- **Deployment Method**: The application is deployed using Docker, as indicated by the presence of a `Dockerfile`.
- **Ports Exposed**: The application listens on port `8099`.
- **Health Check Endpoints**: The health check endpoint is available at `/api/health`.

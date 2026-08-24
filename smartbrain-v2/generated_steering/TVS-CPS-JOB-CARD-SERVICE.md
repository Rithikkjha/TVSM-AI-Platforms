# Steering File: TVS-CPS-JOB-CARD-SERVICE

*Auto-generated from repository analysis*

# TVS-CPS-JOB-CARD-SERVICE Repository Summary

## Service Overview
- **Purpose**: The Job Card Service is a Spring Boot application designed to manage job cards within the TVSM domain. It provides RESTful APIs for CRUD operations, pagination, sorting, and multi-tenancy.
- **Key Responsibilities**:
  - Manage job cards with tenant-specific data isolation.
  - Provide JWT-based authentication and authorization.
  - Expose APIs with OpenAPI/Swagger documentation for easy integration and usage.
  - Support health checks and monitoring through Spring Boot Actuator.

## Tech Stack
- **Language and Version**: Java 21 or higher
- **Framework**: Spring Boot
- **Database**: PostgreSQL
- **Message Queue / Event Bus**: Azure Kafka
- **Key Libraries/Dependencies**:
  - Spring Boot Starters (Web, Data JPA, Validation, Actuator)
  - Lombok
  - MapStruct
  - Springdoc OpenAPI
  - Spring Kafka

## API Endpoints / Routes
- **Health Check**: 
  - **Method**: GET
  - **Path**: `/api/health`
  - **Description**: Returns the health status of the service.
- **Swagger UI**: 
  - **Method**: GET
  - **Path**: `/swagger-ui.html`
  - **Description**: Provides a user interface for exploring the API.
- **OpenAPI Specification**: 
  - **Method**: GET
  - **Path**: `/api-docs`
  - **Description**: Provides the OpenAPI documentation for the service.

## Architecture
- **Code Organization**: The code is organized into standard Spring Boot structure with separate directories for main application code (`src/main/java`), resources (`src/main/resources`), and test code (`src/test/java`).
- **Key Design Patterns Used**: 
  - Multi-tenancy for data isolation.
  - DTO mapping using MapStruct.
  - Dependency Injection via Spring Framework.
- **Entry Point(s)**: The main application entry point is defined in `com.tvsm.jobcard.Application`.

## Dependencies (External Services)
- **Databases/Caches**: 
  - Connects to a PostgreSQL database for data storage.
- **External Services**: 
  - Azure Kafka for messaging.
  - External customer search API.

## Configuration
- **Key Environment Variables**:
  - `DB_USERNAME`: Database username.
  - `DB_PASSWORD`: Database password.
  - `KAFKA_SSL_JC_PWD`: Kafka connection string password.
- **Configuration Files**: 
  - `src/main/resources/application.yml` for application configuration.

## Deployment
- **Deployment Method**: Docker
- **Ports Exposed**: 8080
- **Health Check Endpoints**: `/api/health` for health status.

This summary provides a structured overview of the Job Card Service, detailing its purpose, technology stack, API endpoints, architecture, dependencies, configuration, and deployment strategy.

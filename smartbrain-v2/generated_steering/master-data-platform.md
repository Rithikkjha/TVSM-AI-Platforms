# Steering File: master-data-platform

*Auto-generated from repository analysis*

# TVSM-CS/master-data-platform Repository Analysis

## Service Overview
- **Purpose**: The `master-data-platform` (MDP) is designed to manage and process master data related to dealers, vehicles, and other entities within the automotive domain.
- **Key Responsibilities**: 
  - Handling dealer data and related operations.
  - Integrating with external services for data synchronization.
  - Providing APIs for data access and manipulation.
  - Implementing soft-delete functionality for data integrity.

## Tech Stack
- **Language and Version**: Java 17
- **Framework**: Spring Boot 3.5.12
- **Database**: MySQL (version 8)
- **Message Queue / Event Bus**: Azure Service Bus
- **Key Libraries/Dependencies**:
  - Spring Data JPA
  - Lombok
  - Hibernate
  - MySQL Connector
  - Springdoc OpenAPI for API documentation
  - Redis for caching

## API Endpoints / Routes
- **Not determinable from available files**: The repository does not explicitly list API endpoints in the provided files. However, it mentions the use of Springdoc for API documentation, which suggests that endpoints may be generated dynamically based on the code.

## Architecture
- **Code Organization**: The code is organized into a standard Maven structure with directories for source code (`src/main/java`), resources, and scripts.
- **Key Design Patterns Used**: 
  - Service Layer pattern (as indicated by the README guidelines).
  - Repository pattern for data access.
- **Entry Point(s)**: The application is likely started from the main class annotated with `@SpringBootApplication`, which is not explicitly shown in the provided files.

## Dependencies (External Services)
- **External Services/APIs**: 
  - Azure Service Bus for messaging.
  - Notification service for sending alerts.
- **Databases/Caches**: 
  - MySQL for primary data storage.
  - Redis for caching.

## Configuration
- **Key Environment Variables**:
  - `ACTIVE_ENVIRONMENT`
  - `SERVICE_BUS_DEALER_DATA_CONNECTION_STRING`
  - `DATABASE_HOST_URL`
  - `REDIS_HOST_URL`
  - `NOTIFICATION_BASE_URL`
- **Configuration Files**: 
  - `application.properties` for application-specific configurations.
  - `.env` for environment variable declarations.

## Deployment
- **How it's Deployed**: The application is deployed using Docker, as indicated by the presence of a `Dockerfile`.
- **Ports Exposed**: The application exposes port `8080`.
- **Health Check Endpoints**: Not explicitly mentioned in the provided files, but typically, Spring Boot applications expose health check endpoints via Actuator.

This summary provides a structured overview of the `master-data-platform` repository, detailing its purpose, technology stack, architecture, and deployment strategies based on the available files.

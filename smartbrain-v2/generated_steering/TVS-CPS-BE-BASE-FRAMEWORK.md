# Steering File: TVS-CPS-BE-BASE-FRAMEWORK

*Auto-generated from repository analysis*

# TVSM Base Framework Repository Summary

## Service Overview
- **Purpose**: The TVSM Base Framework is designed to provide a comprehensive foundation for building enterprise-ready backend applications using Spring Boot. It aims to streamline the development process by offering reusable components and architectural patterns.
- **Key Responsibilities**: 
  - Provides a base framework for backend applications.
  - Supports multi-tenant architecture with dynamic data source routing.
  - Implements JWT authentication and global exception handling.
  - Facilitates rapid project bootstrapping through a Maven archetype.

## Tech Stack
- **Language and Version**: Java 21
- **Framework**: Spring Boot 3.5.4
- **Database**: PostgreSQL (via the PostgreSQL client)
- **Message Queue / Event Bus**: Not determinable from available files
- **Key Libraries/Dependencies**:
  - Spring Boot Starter Web
  - Spring Boot Starter Data JPA
  - Spring Boot Starter Validation
  - Spring Boot Starter Actuator
  - Lombok
  - MapStruct
  - Springdoc OpenAPI

## API Endpoints / Routes
- **Not explicitly defined in the repository**. However, the WireMock server setup allows for dynamic API stubs, including:
  - `POST /api/products`: Creates a product with a dynamic ID based on the request body.
  - `GET /api/parts-with-vehicles`: Retrieves parts with vehicles based on query parameters.
  - `GET /api/search`: Searches for parts based on query parameters.
  - `GET /api/parts/all`: Retrieves all parts based on query parameters.

## Architecture
- **Code Organization**: The project is organized into multiple modules:
  - `tvsm-be-core`: Contains the core framework library.
  - `tvsm-be-archetype`: A Maven archetype for generating new projects.
- **Key Design Patterns Used**: 
  - Dependency Injection (via Spring)
  - Aspect-Oriented Programming (AOP) for logging and monitoring
- **Entry Point(s)**: The main entry point is likely defined in the Spring Boot application class, which is not explicitly shown in the provided files.

## Dependencies (External Services)
- **Other Services/APIs**: Not determinable from available files.
- **Databases/Caches**: Connects to PostgreSQL for data storage.

## Configuration
- **Key Environment Variables**: Not explicitly listed in the provided files.
- **Configuration Files**: 
  - `application.yml`: Used for configuring the WireMock server and other application settings.

## Deployment
- **How it's Deployed**: The application is deployed using Docker, as indicated by the presence of a `Dockerfile`.
- **Ports Exposed**: The specific ports are not mentioned, but the WireMock server runs on a configurable port defined in `application.yml`.
- **Health Check Endpoints**: Not determinable from available files.

This summary provides a structured overview of the TVSM Base Framework repository, detailing its purpose, technology stack, architecture, and deployment strategies based on the available files.

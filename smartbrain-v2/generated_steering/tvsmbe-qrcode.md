# Steering File: tvsmbe-qrcode

*Auto-generated from repository analysis*

# TVSM-CS/tvsmbe-qrcode Repository Summary

## Service Overview
- **Purpose**: This service is designed to generate and manage QR codes, likely for use in various applications related to TVS Motor Company. It handles both public and administrative functionalities, including QR code generation, storage, and management.
- **Key Responsibilities**:
  - Generate QR codes based on user input.
  - Store and retrieve QR codes from a MongoDB database.
  - Provide public-facing endpoints for QR code access and redirection.
  - Enforce authentication for administrative operations.

## Tech Stack
- **Language and Version**: Java 21
- **Framework**: Spring Boot (version 3.3.3)
- **Database**: MongoDB (version 7)
- **Message Queue / Event Bus**: Not determinable from available files
- **Key Libraries/Dependencies**:
  - Spring Boot Starter Web
  - Spring Boot Starter Data MongoDB
  - Spring Boot Starter Validation
  - Azure Blob Storage SDK
  - Apache Batik for SVG to PNG conversion
  - ZXing for QR code generation
  - JSON Web Token (JWT) for authentication
  - Spring Security for cryptography
  - ModelMapper for object mapping
  - Lombok for reducing boilerplate code

## API Endpoints / Routes
- **Not explicitly defined in the provided files**. The service exposes public and admin endpoints, but specific routes are not detailed in the available files.

## Architecture
- **Code Organization**: The code is organized into a standard Spring Boot structure with separate directories for main application code (`src/main/java`) and resources (`src/main/resources`).
- **Key Design Patterns Used**: Not determinable from available files, but likely includes MVC (Model-View-Controller) given the use of Spring Boot.
- **Entry Point(s)**: The main entry point is likely the `@SpringBootApplication` annotated class in the `src/main/java` directory, which is not explicitly listed in the provided files.

## Dependencies (External Services)
- **Other Services/APIs**: 
  - MongoDB for data storage.
  - Azure Blob Storage for potential file storage (if enabled).
- **Databases/Caches**: 
  - Connects to a MongoDB instance for storing QR code data.

## Configuration
- **Key Environment Variables**:
  - `SPRING_PROFILES_ACTIVE`: Defines the active profile (public/admin).
  - `SERVER_PORT`: Port on which the service runs.
  - `MONGO_URI`: Connection string for MongoDB.
  - `TVSM_AUTH_ENABLED`: Enables or disables authentication.
  - `AZURE_STORAGE_ENABLED`: Enables or disables Azure Blob Storage integration.
- **Configuration Files**: 
  - `application.yml` for Spring Boot configuration.

## Deployment
- **How it's Deployed**: The service is deployed using Docker, with a `Dockerfile` and `docker-compose.yml` for managing services.
- **Ports Exposed**:
  - Public backend: 8085
  - Admin backend: 8084
  - MongoDB: 27017
- **Health Check Endpoints**: Not determinable from available files.

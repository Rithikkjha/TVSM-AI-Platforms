# Steering File: tvsm-auth

*Auto-generated from repository analysis*

# TVSM Authentication Service Summary

## Service Overview
- **Purpose**: The TVSM Authentication Service is designed to enable client web applications to authenticate users through the Azure Active Directory B2C tenant using the Microsoft identity platform. It serves as an authentication and authorization service for applications within the TVSM ecosystem.
- **Key Responsibilities**: 
  - User authentication and authorization via Azure AD B2C.
  - Management of user accounts and tokens.
  - Integration with various Azure services for enhanced functionality (e.g., Azure Storage, Azure Face API).

## Tech Stack
- **Language and Version**: Java 17
- **Framework**: Spring Boot 3.5.7
- **Database**: MySQL (version not specified, but uses JDBC URL format)
- **Message Queue / Event Bus**: Azure Service Bus
- **Key Libraries/Dependencies**:
  - Spring Boot Starter Web
  - Spring Boot Starter Security
  - Spring Boot Starter Data JPA
  - MySQL Connector/J
  - MSAL4J for Azure authentication
  - Microsoft Graph SDK
  - Azure SDKs for Blob Storage and Face API
  - Lombok for reducing boilerplate code

## API Endpoints / Routes
- **Not determinable from available files**: The repository does not explicitly list API endpoints or routes in the provided files. The service likely exposes endpoints for user authentication and management, but specific routes are not documented.

## Architecture
- **Code Organization**: The code is organized into a standard Spring Boot structure with a `src/main/java` directory for Java source files and `src/main/resources` for configuration files.
- **Key Design Patterns Used**: Common Spring patterns such as Dependency Injection and MVC (Model-View-Controller) are likely employed, though specific implementations are not detailed in the provided files.
- **Entry Point(s)**: The entry point for the application is typically the main application class annotated with `@SpringBootApplication`, which is not explicitly shown in the provided files.

## Dependencies (External Services)
- **Other Services/APIs**: 
  - Azure Active Directory B2C for user authentication.
  - Microsoft Graph API for user management.
  - Azure Storage for blob storage functionalities.
  - Azure Face API for facial recognition features.
  - Notification service for sending notifications.
  - Karza API for eKYC (electronic Know Your Customer) processes.
- **Databases/Caches**: 
  - MySQL database named "tvs_auth" for storing user data.

## Configuration
- **Key Environment Variables**:
  - `ACTIVE_ENVIRONMENT`: Specifies the active environment (e.g., local, production).
  - `DB_URI`, `DB_USERNAME`, `DB_PASSWORD`: Database connection details.
  - Azure AD B2C configuration variables (e.g., `B2C_TENANT_NAME`, `B2C_TENANT_ID`, etc.).
  - Various application-specific configurations (e.g., `AZURE_BLOB_CONNECTION`, `KARZA_API_BASE_URL`).
- **Configuration Files**: 
  - `application.properties` for Spring Boot configuration settings.

## Deployment
- **How it's Deployed**: The application is packaged and deployed using Docker. A multi-stage Dockerfile is provided for building and running the application.
- **Ports Exposed**: The application exposes port 8080.
- **Health Check Endpoints**: **Not determinable from available files**: The repository does not specify any health check endpoints in the provided files.

# Steering File: tvsm-marketplace-service

*Auto-generated from repository analysis*

# tvsm-marketplace-service Repository Summary

## Service Overview
- **Purpose**: The `tvsm-marketplace-service` is designed to interact with a marketplace, likely facilitating operations related to e-commerce transactions, such as managing product listings, processing orders, and handling notifications.
- **Key Responsibilities**: 
  - Interacting with external e-commerce platforms (e.g., Flipkart).
  - Managing vehicle price data and updates.
  - Handling notifications and updates related to bookings and pricing.
  - Integrating with Azure Service Bus for messaging.

## Tech Stack
- **Language and Version**: Java 17
- **Framework**: Spring Boot 3.5.7
- **Database**: MySQL (via `mysql-connector-j`)
- **Message Queue / Event Bus**: Azure Service Bus
- **Key Libraries/Dependencies**:
  - Spring Boot Starter Web
  - Spring Boot Starter Data JPA
  - Spring Retry
  - Azure Messaging Service Bus
  - Guava
  - Jackson Datatype (for JSON processing)
  - Lombok (for reducing boilerplate code)

## API Endpoints / Routes
- **Not determinable from available files**: The provided files do not explicitly list any API endpoints or routes.

## Architecture
- **Code Organization**: The code is organized into a standard Maven structure with a `src/main/java` directory for Java source files and a `src/main/resources` directory for configuration files.
- **Key Design Patterns Used**: Not explicitly mentioned in the provided files, but typical Spring Boot applications often utilize MVC (Model-View-Controller) and Dependency Injection patterns.
- **Entry Point(s)**: The entry point is likely defined in a main application class annotated with `@SpringBootApplication`, but this is not visible in the provided files.

## Dependencies (External Services)
- **Other Services/APIs**: 
  - Flipkart API for seller operations.
  - Azure Service Bus for messaging.
  - Various external services for notifications and bookings (e.g., Lead Service, Booking Service).
- **Databases/Caches**: 
  - MySQL database for persistent storage.

## Configuration
- **Key Environment Variables**: 
  - `ACTIVE_ENVIRONMENT`
  - `DATABASE_HOST_URL`
  - `DATABASE_NAME`
  - `DATABASE_USERNAME`
  - `DATABASE_PASSWORD`
  - `VEHICLE_PRICE_DATA_TOPIC_NAME`
  - `FLIPKART_SELLER_API_BASE_URL`
  - `FLIPKART_OAUTH_APPLICATION_ID`
  - `FLIPKART_OAUTH_APPLICATION_SECRET`
  - `B2C_TOKEN_URL`, `B2C_CLIENT_ID`, `B2C_CLIENT_SECRET`, etc.
- **Configuration Files**: 
  - `application.properties` contains various configurations for the application, including database connection details and service-specific settings.

## Deployment
- **How it's Deployed**: The service is deployed using Docker, as indicated by the presence of a `Dockerfile`.
- **Ports Exposed**: The application exposes port `8080`.
- **Health Check Endpoints**: Not determinable from available files; no specific health check endpoints are mentioned.

This summary provides a structured overview of the `tvsm-marketplace-service` repository based on the available files and their contents.

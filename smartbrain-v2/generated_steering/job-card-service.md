# Steering File: job-card-service

*Auto-generated from repository analysis*

# Job Card Service Repository Summary

## Service Overview
- **Purpose**: The Job Card Service is a software solution designed to manage the creation, tracking, and updating of job cards for vehicle services. It aims to streamline workflow, task allocation, and customer communication across multiple channels.
- **Key Responsibilities**: 
  - Creation and management of job cards (task or work orders).
  - Tracking job card status and updates.
  - Facilitating customer communication through various platforms (web, mobile, social media).

## Tech Stack
- **Language and Version**: C# (.NET 9.0)
- **Framework**: ASP.NET Core
- **Database**: Not explicitly mentioned, but a centralized database is implied for storing job card data and related information.
- **Message Queue / Event Bus**: Not determinable from available files.
- **Key Libraries/Dependencies**: 
  - Entity Framework (for database migrations and interactions).

## API Endpoints / Routes
- Not explicitly listed in the provided files. However, the service exposes an API for managing job cards, as indicated in the README and the structure of the `src/Jobcard.API` directory.

## Architecture
- **Code Organization**: The code is organized into a microservices architecture with separate modules for API, application logic, and potentially domain and infrastructure layers.
- **Key Design Patterns Used**: Microservices architecture, likely using patterns such as Repository and Service patterns for data access and business logic.
- **Entry Point(s)**: The entry point for the application is defined in `Program.cs` within the `src/Jobcard.API` directory.

## Dependencies (External Services)
- **Other Services/APIs**: Not determinable from available files.
- **Databases/Caches**: The service connects to a centralized database for job card data, customer information, and service history, but specific database technologies are not mentioned.

## Configuration
- **Key Environment Variables**:
  - `ASPNETCORE_URLS`: Configured to listen on port 8080.
  - `TZ`: Set to Asia/Kolkata for timezone.
- **Configuration Files**: 
  - `appsettings.json` in `src/Jobcard.API` for application settings.
  - `NuGet.Config` for package management.

## Deployment
- **How it's Deployed**: The service is deployed using Docker and Kubernetes.
- **Ports Exposed**: Port 8080 is exposed for the application.
- **Health Check Endpoints**: Not determinable from available files.

This summary provides a structured overview of the Job Card Service repository, detailing its purpose, technology stack, architecture, and deployment strategy based on the available files.

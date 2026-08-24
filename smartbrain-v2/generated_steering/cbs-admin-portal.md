# Steering File: cbs-admin-portal

*Auto-generated from repository analysis*

# TVS Lead Service Admin Portal - Repository Summary

## Service Overview
- **Purpose**: The TVS Lead Service Admin Portal is a full-stack internal application designed for managing Lead Service configurations. It provides a structured workflow for handling drafts, publishing changes, and maintaining audit logs and versioning.
- **Key Responsibilities**:
  - Manage dealer and source configurations.
  - Handle form configurations with a visual mapping interface.
  - Maintain audit logs for all changes.
  - Implement a secure authentication system with role-based access control.

## Tech Stack
- **Language and Version**: Java 17+ for backend, JavaScript (Node.js 18+) for frontend.
- **Framework**: 
  - Backend: Spring Boot
  - Frontend: React
- **Database**: 
  - Admin DB (for drafts, versions, audit logs)
  - LS DB (for production business tables)
- **Message Queue / Event Bus**: Not determinable from available files.
- **Key Libraries/Dependencies**: 
  - Maven for backend dependency management (indicated by `pom.xml`).
  - React libraries for frontend (indicated by `package.json`).

## API Endpoints / Routes
- **List of API Endpoints**:
  | Method | Path                          | Description                               |
  |--------|-------------------------------|-------------------------------------------|
  | POST   | `/api/auth/login`            | Authenticate user                         |
  | POST   | `/api/dealers/draft`         | Save dealer draft                         |
  | POST   | `/api/dealers/publish/{id}`  | Publish dealer to LS DB                   |
  | GET    | `/api/dealers`               | List all dealers                          |
  | GET    | `/api/dealers/drafts`        | List dealer drafts                        |
  | POST   | `/api/sources/draft`         | Save source draft                         |
  | POST   | `/api/sources/publish/{id}`  | Publish source to LS DB                   |
  | GET    | `/api/sources`               | List all sources                         |
  | POST   | `/api/form-config/draft`     | Save form config draft                   |
  | POST   | `/api/form-config/publish/{id}` | Publish form config                     |
  | GET    | `/api/form-config/metadata`   | Get field/form/product metadata          |
  | GET    | `/api/audit`                 | List audit logs (paginated)              |

## Architecture
- **Code Organization**: The code is organized into a modular monolith structure with separate packages for configuration, common utilities, audit logging, authentication, dealer management, source management, and form configuration.
- **Key Design Patterns Used**: Not explicitly mentioned, but the use of a draft-publish workflow suggests a Command pattern for handling operations.
- **Entry Point(s)**: The backend entry point is the Spring Boot application, typically found in the `main` method of the main application class.

## Dependencies (External Services)
- **Other Services/APIs**: Not determinable from available files.
- **Databases/Caches**: 
  - Admin DB for managing drafts and audit logs.
  - LS DB for production data, accessed through a controlled publish process.

## Configuration
- **Key Environment Variables**: Not determinable from available files.
- **Configuration Files**: 
  - `application.yml` for multi-datasource configuration in the backend.
  - SQL files for schema definitions.

## Deployment
- **How It's Deployed**: Not determinable from available files, but it can be run locally using Maven for the backend and npm for the frontend.
- **Ports Exposed**: 
  - Backend: `http://localhost:8080`
  - Frontend: `http://localhost:3000`
- **Health Check Endpoints**: Not determinable from available files.

This summary provides a structured overview of the TVS Lead Service Admin Portal repository, detailing its purpose, architecture, and key components based on the provided files.

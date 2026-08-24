# Steering File: bto_api

*Auto-generated from repository analysis*

# Repository Summary for TVSM-CS/bto_api

## Service Overview
- **Purpose**: This service is a backend API built using the NestJS framework, designed to provide functionalities related to booking and authentication, likely for a booking system.
- **Key Responsibilities**: 
  - User authentication and authorization.
  - Managing booking operations.
  - Providing an API for clients to interact with the booking system.
  - Exposing API documentation via Swagger.

## Tech Stack
- **Language and Version**: TypeScript (version not explicitly stated, but inferred from `tsconfig.json` and `package.json`).
- **Framework**: NestJS (version 10.0.0).
- **Database**: Prisma ORM is used, with a schema defined in `prisma/schema.prisma`.
- **Message Queue / Event Bus**: Not determinable from available files.
- **Key Libraries/Dependencies**:
  - `@nestjs/common`, `@nestjs/core`, `@nestjs/jwt`, `@nestjs/passport`, `@nestjs/swagger`
  - `@prisma/client`
  - `argon2` for password hashing
  - `class-transformer`, `class-validator` for data validation
  - `winston` for logging

## API Endpoints / Routes
- **Not explicitly listed in the provided files**, but the service exposes:
  - Authentication endpoints (likely in `src/auth/auth.controller.ts`).
  - Booking management endpoints (likely in `src/booking/booking.controller.ts`).
  - Report generation endpoints (likely in `src/report/report.controller.ts`).
- The service also provides Swagger documentation at `/api-doc`.

## Architecture
- **Code Organization**: The code is organized into modules (e.g., `auth`, `booking`, `report`, `prisma`), each containing its own controller, service, and DTOs.
- **Key Design Patterns Used**: 
  - Modular architecture for separation of concerns.
  - Dependency Injection via NestJS.
  - Use of DTOs for data validation and transformation.
- **Entry Point**: The application starts from `src/main.ts`, where the Nest application is bootstrapped.

## Dependencies (External Services)
- **Other Services/APIs**: Not determinable from available files.
- **Databases/Caches**: Connects to a database via Prisma, but specific database details are not provided in the files.

## Configuration
- **Key Environment Variables**:
  - `CORS_ALLOWED_ORIGINS`: Specifies allowed origins for CORS.
  - `PORT`: The port on which the application listens.
- **Configuration Files**: 
  - `.env` file is referenced for environment variables.
  - `prisma/schema.prisma` for database schema configuration.

## Deployment
- **How it's Deployed**: Not determinable from available files, but it can be inferred that it may be deployed using Node.js directly.
- **Ports Exposed**: The application listens on a port defined by the `PORT` environment variable.
- **Health Check Endpoints**: Not determinable from available files.

This summary provides a structured overview of the `bto_api` repository, detailing its purpose, technology stack, architecture, and configuration.

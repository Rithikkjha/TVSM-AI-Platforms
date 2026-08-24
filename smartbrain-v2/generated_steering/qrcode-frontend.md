# Steering File: qrcode-frontend

*Auto-generated from repository analysis*

# QR Code Frontend Service Summary

## Service Overview
- **Purpose**: This service is a frontend application for generating QR codes, built using React and TypeScript. It leverages Vite for development and build processes.
- **Key Responsibilities**: 
  - Provides a user interface for generating and managing QR codes.
  - Implements authentication and authorization features.
  - Displays analytics and library of generated QR codes.

## Tech Stack
- **Language and Version**: TypeScript (5.5.4)
- **Framework**: React (18.3.1) with Vite (5.4.10)
- **Database**: Not determinable from available files
- **Message Queue / Event Bus**: Not determinable from available files
- **Key Libraries/Dependencies**:
  - `@hookform/resolvers`: 3.9.0
  - `lucide-react`: 0.454.0
  - `react-hook-form`: 7.53.0
  - `zod`: 3.23.8

## API Endpoints / Routes
- Not determinable from available files. The service does not explicitly define API endpoints in the provided files.

## Architecture
- **Code Organization**: The code is organized into several directories:
  - `src`: Contains the main application code, including components, pages, and utilities.
  - `public`: Contains static assets like SVG files.
  - `auth`: Contains authentication-related components.
  - `components`: Contains reusable UI components.
  - `pages`: Contains different pages of the application.
- **Key Design Patterns Used**: Not explicitly mentioned, but likely follows component-based architecture typical in React applications.
- **Entry Point(s)**: The entry point is `src/main.tsx`, which initializes the React application.

## Dependencies (External Services)
- **Other Services/APIs**: The application is configured to connect to an API base URL defined by the environment variable `VITE_API_BASE`, which defaults to `http://localhost:8084`.
- **Databases/Caches**: Not determinable from available files.

## Configuration
- **Key Environment Variables**:
  - `VITE_API_BASE`: Base URL for API calls (default: `http://localhost:8084`).
  - `VITE_ENV`: Environment setting (default: `UAT`).
- **Configuration Files**: 
  - `vite.config.ts`: Configuration for Vite.
  - `nginx.conf`: Configuration for serving the application with Nginx.

## Deployment
- **How it's Deployed**: The application is deployed using Docker, with a multi-stage build process that compiles the application and serves it using Nginx.
- **Ports Exposed**: The application exposes port 80 internally and maps it to port 3000 externally.
- **Health Check Endpoints**: Not determinable from available files.

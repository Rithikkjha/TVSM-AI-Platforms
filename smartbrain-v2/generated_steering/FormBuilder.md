# Steering File: FormBuilder

*Auto-generated from repository analysis*

# TVSM-CS/FormBuilder Repository Analysis

## Service Overview
- **Purpose**: The application is a checklist form builder based on Survey JS, designed to facilitate the creation and management of checklist forms.
- **Domain**: Primarily focused on form management and user interaction through a web interface.
- **Key Responsibilities**: 
  - Provide a user-friendly interface for creating and managing forms.
  - Handle form submissions and data storage.
  - Support admin functionalities for managing templates and submissions.

## Tech Stack
- **Language and Version**: TypeScript
- **Framework**: Next.js (version 15.2.4)
- **Database**: Not determinable from available files
- **Message Queue / Event Bus**: Not determinable from available files
- **Key Libraries/Dependencies**:
  - React (version 19.0.0)
  - Axios (for HTTP requests)
  - Redux Toolkit (for state management)
  - Firebase (for backend services)
  - SurveyJS (for form building)

## API Endpoints / Routes
- **List of API Endpoints**:
  - `GET /api/generate-pdf`: Generates a PDF document.
  - `GET /api/get-env-config`: Retrieves environment configuration.
  - `GET /api/get-masterdata`: Fetches master data.
  - `GET /api/get-submission-data`: Retrieves submission data.
  - `POST /api/save-template-data`: Saves template data.
  - `POST /api/submission-approval`: Approves a submission.
  - `POST /api/submission-update`: Updates a submission.
  - `GET /api/templates`: Fetches available templates.

## Architecture
- **Code Organization**: The code is organized into modules such as `app`, `components`, `hooks`, `lib`, and `pages`, following a structure that separates concerns.
- **Key Design Patterns Used**: The application follows the Backend for Frontend (BFF) design pattern, which allows for a tailored API for the frontend.
- **Entry Point(s)**: The main entry point is defined in `next.config.ts`, with the application starting from the `pages` directory.

## Dependencies (External Services)
- **Other Services/APIs**: Not determinable from available files.
- **Databases/Caches**: Not determinable from available files.

## Configuration
- **Key Environment Variables**:
  - `NEXT_PUBLIC_REDIRECT_URI`: Used for redirecting after authentication.
  - `NODE_ENV`: Specifies the environment (e.g., production, uat).
- **Configuration Files**: 
  - `.development`, `.production`, `.uat`: Environment-specific configuration files.
  - `next.config.ts`: Configuration for Next.js.

## Deployment
- **How it's Deployed**: The application can be deployed using Docker, as indicated by the presence of a `Dockerfile` and `docker-compose.yml`.
- **Ports Exposed**: The application exposes port `3000`.
- **Health Check Endpoints**: Not determinable from available files.

This structured summary provides a comprehensive overview of the TVSM-CS/FormBuilder repository, detailing its purpose, technology stack, architecture, and deployment strategies.

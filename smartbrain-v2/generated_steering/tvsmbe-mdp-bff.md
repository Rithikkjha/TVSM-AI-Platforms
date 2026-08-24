# Steering File: tvsmbe-mdp-bff

*Auto-generated from repository analysis*

# TVSM-CS/tvsmbe-mdp-bff Repository Summary

## Service Overview
- **Purpose**: This service acts as a Backend for Frontend (BFF) for the MDP (Motor Dealer Platform), facilitating communication between clients and various MDP services.
- **Key Responsibilities**:
  - Acts as a BFF for MDP, handling requests from clients and servers.
  - Initiates communication with external services, such as single-interface and Knowlarity.

## Tech Stack
- **Language and Version**: Not determinable from available files.
- **Framework**: Not determinable from available files.
- **Database**: 
  - MySQL (hosted on Azure).
- **Message Queue / Event Bus**: Not determinable from available files.
- **Key Libraries/Dependencies**: 
  - Maven (indicated by `pom.xml` files in both inbound and outbound directories).

## API Endpoints / Routes
- Not determinable from available files. The README does not specify explicit API endpoints.

## Architecture
- **Code Organization**: 
  - The repository is structured into `inbound` and `outbound` directories, each containing their own source (`src`) and test (`test`) directories, along with configuration files.
- **Key Design Patterns Used**: Not determinable from available files.
- **Entry Point(s)**: Not determinable from available files.

## Dependencies (External Services)
- **External Services/APIs**:
  - Communicates with external services such as Knowlarity and single-interface.
- **Databases/Caches**:
  - Connects to a MySQL database hosted on Azure.

## Configuration
- **Key Environment Variables**:
  - `ACTIVE_ENVIRONMENT`
  - `DATABASE_HOST_URL`
  - `DATABASE_NAME`
  - `DATABASE_PASSWORD`
  - `DATABASE_USERNAME`
  - `KNOWLARITY_K_NUMBER_API_TOKEN`
  - `KNOWLARITY_K_NUMBER_API_URL`
  - `MDP_BASE_URL`
  - `MDP_BFF_EXTERNAL_CLIENTS`
  - `MDP_DEALER_DATA_TOPIC_NAME`
  - `MDP_GENERATE_AUTH_TOKEN_CLIENT_ID`
  - `MDP_GENERATE_AUTH_TOKEN_CLIENT_PASSWORD`
  - `SI_OUTLET_API_BASE_URL`
  - `SI_OUTLET_API_TOKEN`
  - `MDP_DEALER_DATA_TOPIC_CONNECTION_STRING`
  - `NOTIFICATION_BASE_URL`
  - `NOTIFICATION_GENERATE_B2C_TOKEN_API_URL`
  - `NOTIFICATION_APIM_SUBSCRIPTION_KEY`
  - `NOTIFICATION_GENERATE_B2C_TOKEN_CLIENT_ID`
  - `NOTIFICATION_GENERATE_B2C_TOKEN_CLIENT_SECRET`
  - `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL`
  - `AZURE_B2C_CLIENT_ID`
  - `AZURE_B2C_CLIENT_SECRET`
- **Configuration Files**: 
  - `.env` file contains environment variables.
  - `pom.xml` files in both `inbound` and `outbound` directories for Maven configuration.

## Deployment
- **Deployment Method**: 
  - Docker (indicated by the presence of `Dockerfile` in both `inbound` and `outbound` directories).
- **Ports Exposed**: Not determinable from available files.
- **Health Check Endpoints**: Not determinable from available files.

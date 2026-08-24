# tvsm-otp-service

*Auto-generated from static code analysis*

## Service Overview
- **Language:** Java (Spring Boot @ 3.5.7)
- **Contacts:** somashis-nath-tvsd-ai, Nithin-Devarakonda, Koyelnath, shekharbachu123, santhosh-tvsd
- **Purpose:** The OTP Service is a Spring Boot application designed to generate and verify One-Time Passwords (OTPs) across multiple communication channels. It offers a secure, scalable, and flexible OTP management solution, featuring multi-channel support, configurable policies, and integration with Azure Key Vault for encryption.
- **Domain:** actuator, added, additional, advice, algorithm, application, architecture, args, argument, artifact

## Code Structure
```
📁 .idea/
📄 .idea/.gitignore
📄 .idea/.name
📄 .idea/compiler.xml
📄 .idea/encodings.xml
📄 .idea/jarRepositories.xml
📄 .idea/misc.xml
📁 .vscode/
📄 .vscode/settings.json
📄 Dockerfile
📄 Dockerfile.build
📄 Jenkinsfile
📄 Jenkinsfile-sun
📄 Otp-Service.iml
📄 README.md
📁 azure-pipelines/
📄 azure-pipelines/ast-image-scan-otp-pipeline.yaml
📄 azure-pipelines/ast-otp-prod-pipeline.yaml
📄 azure-pipelines/ast-otp-uat-pipeline.yaml
📄 azure-pipelines/cd-pipeline.yaml
📄 azure-pipelines/ci-pipeline.yaml
📄 azure-pipelines/sonar.yaml
📄 build.sh
📄 cd-pipeline.yaml
📄 ci-otp-pipeline.yaml
📄 pom.xml
📁 src/
📁 src/main/
📁 src/main/java/
📁 src/main/resources/
📁 src/test/
📁 src/test/java/
📄 uk-cd-pipeline.yaml
📄 uk-cd-training-pipeline.yaml
```

## Key Modules
| File | Purpose |
|---|---|
| src/main/java/com/otp/exception/ConfigurationException.java | Exception thrown when OTP configuration fails. This exception encapsulates failures during OTP configuration from the JSON file. |

## API Endpoints
| Method | Path | Description | File |
|--------|------|-------------|------|
| POST | /api/generate | Endpoint for generating OTPs. | src/main/java/com/otp/controller/OtpController.java:39 |
| POST | /api/verify | Endpoint for verifying OTPs. | src/main/java/com/otp/controller/OtpController.java:65 |

## Dependencies (Outbound)
### HTTP Calls
| Target Service | URL/Variable | Confidence | File |
|---|---|---|---|
| unknown | `@Value("${spring.redis.host}")` | 🔴 low | src/main/java/com/otp/config/RedisConfig.java:16 |
| master-data-platform | `@Value("${spring.redis.database}")` | 🟡 medium | src/main/java/com/otp/config/RedisConfig.java:22 |

## Databases
| Type | Name | File |
|---|---|---|
| redis |  | pom.xml — redis dependency |

## Recent Activity
- **Last commit:** 2026-03-09 by Nithin-Devarakonda — "Merge pull request #46 from TVSM-CS/Nithin-Devarakonda-patch-10"
- **Commit frequency:** inactive

## Architecture Notes
The service is structured to support modular development, with clear separation of concerns between configuration, exception handling, and API endpoints. This design facilitates maintainability and scalability as the service evolves.
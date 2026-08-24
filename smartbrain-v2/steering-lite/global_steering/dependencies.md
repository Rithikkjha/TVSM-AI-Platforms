# Cross-Service Dependencies

*Auto-generated from tech.md analysis*

# Service Dependencies Documentation

## Summary of HTTP Service-to-Service Calls

| Source Service                  | Target Service                          | Description                                           |
|---------------------------------|----------------------------------------|-------------------------------------------------------|
| tvsm-marketplace-service         | Guava                                  | ImmutableSet, Lists.partition() for batch processing   |
| tvsm-marketplace-service         | Jackson + Joda/JSR-310                | JSON serialization with Java 8 time and Joda time support |
| tvsm-marketplace-service         | Commons Codec                          | SHA-1 hashing for Flipkart webhook signature verification |
| tvsm-marketplace-service         | SpringDoc OpenAPI                      | Auto-generated Swagger UI at `/marketplace/swagger-ui.html` |
| tvsm-marketplace-service         | Hibernate Envers                       | Automatic entity change history (audit tables with `_AUD` suffix) |
| tvsm-marketplace-service         | Spring Retry                           | Declarative retry with exponential backoff on Flipkart API calls |

## Service Bus Topology

### Publishers and Subscribers

| Publisher       | Topic                | Subscribers                          |
|-----------------|----------------------|--------------------------------------|
| tvsm-auth       | Builder              | -                                    |
| tvsm-auth       | Repository           | -                                    |
| tvsm-auth       | Filter Chain         | -                                    |
| tvsm-auth       | Retry                | -                                    |
| tvsm-auth       | Async                | -                                    |
| tvsm-auth       | Caching              | -                                    |
| tvsm-auth       | Scheduler            | -                                    |
| Azure Blob      | tvsm-auth            | -                                    |
| Azure Service Bus | tvsm-auth          | -                                    |
| MDP             | tvsm-auth            | -                                    |
| Karza (eKYC)    | tvsm-auth           | -                                    |
| Notification    | tvsm-auth            | -                                    |
| User Lifecycle   | tvsm-auth           | -                                    |
| Security        | tvsm-auth            | -                                    |
| Deployment      | PaymentService       | -                                    |

## Most Depended Upon Services

| Service            | Incoming Dependencies Count |
|--------------------|----------------------------|
| tvsm-auth          | 8                          |
| FormBuilder        | 7                          |
| tvsm-marketplace-service | 6                    |
| PaymentService     | 1                          |

This document summarizes the service dependencies extracted from code analysis, providing a clear overview of HTTP service calls, service bus topology, and the ranking of services based on their incoming dependencies.
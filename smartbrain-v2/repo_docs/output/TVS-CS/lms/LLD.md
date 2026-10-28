---
service_id: lms
doc_type: lld
last_reviewed: 2026-10-11
---

# lms — Low-Level Design

## Data Model
lms EF Core entities (inventory `data_access`; DDL not in repo):

| Entity | Table | Defined in |
|---|---|---|
| `AccountMaster` | `account_master` | `lms.config/Entities/AccountMaster.cs:9` |
| `AdditionalDetail` | `additional_details` | `lms.config/Entities/AdditionalDetail.cs:9` |
| `AdditionalDetailsLogMapping` | `additional_details_log_mapping` | `lms.config/Entities/AdditionalDetailsLogMapping.cs:9` |
| `BrandDetailLogMapping` | `brand_detail_log_mapping` | `lms.config/Entities/BrandDetailLogMapping.cs:9` |
| `BrandMaster` | `brand_master` | `lms.config/Entities/BrandMaster.cs:9` |
| `ClassifiedLead` | `classified_leads` | `lms.config/Entities/ClassifiedLead.cs:9` |
| `CommsBrandDetail` | `comms_brand_details` | `lms.config/Entities/CommsBrandDetail.cs:9` |
| `CountryMaster` | `country_master` | `lms.config/Entities/CountryMaster.cs:9` |
| `DealerContact` | `dealer_contacts` | `lms.config/Entities/DealerContact.cs:9` |
| `DealerFlag` | `dealer_flags` | `lms.config/Entities/DealerFlag.cs:9` |
| `DealerLocation` | `dealer_locations` | `lms.config/Entities/DealerLocation.cs:9` |
| `DealerMaster` | `dealer_master` | `lms.config/Entities/DealerMaster.cs:9` |
| `DealerMasterList` | `DealerMasterList` | `lms.config/Entities/DealerMasterList.cs:9` |
| `DealerMediationControl` | `dealer_mediation_controls` | `lms.config/Entities/DealerMediationControl.cs:9` |
| `DuplicateLead` | `duplicate_leads` | `lms.config/Entities/DuplicateLead.cs:9` |
| `EventConfigurator` | `event_configurator` | `lms.config/Entities/EventConfigurator.cs:9` |
| `FinanceDetail` | `finance_details` | `lms.config/Entities/FinanceDetail.cs:9` |
| `FormBrandMapping` | `form_brand_mapping` | `lms.config/Entities/FormBrandMapping.cs:9` |
| `FormConfiguration` | `FormConfigurations` | `lms.config/Entities/FormConfiguration.cs:9` |
| `FormMaster` | `form_master` | `lms.config/Entities/FormMaster.cs:9` |
| `LatlongPushLog` | `latlong_push_logs` | `lms.config/Entities/LatlongPushLog.cs:9` |
| `Lead` | `leads` | `lms.config/Entities/Lead.cs:9` |
| `LeadAcquisitionLog` | `lead_acquisition_logs` | `lms.config/Entities/LeadAcquisitionLog.cs:9` |
| `LeadBrandDetail` | `lead_brand_details` | `lms.config/Entities/LeadBrandDetail.cs:9` |
| `LeadCatalogueDetail` | `lead_catalogue_details` | `lms.config/Entities/LeadCatalogueDetail.cs:9` |
| `LeadComm` | `lead_comms` | `lms.config/Entities/LeadComm.cs:9` |
| `LeadEnquiryTag` | `lead_enquiry_tag` | `lms.config/Entities/LeadEnquiryTag.cs:9` |
| `LeadEventLog` | `lead_event_logs` | `lms.config/Entities/LeadEventLog.cs:9` |
| `LeadExtraAttribute` | `lead_extra_attributes` | `lms.config/Entities/LeadExtraAttribute.cs:9` |
| `LeadFlowConfiguration` | `lead_flow_configuration` | `lms.config/Entities/LeadFlowConfiguration.cs:9` |
| `LeadFollowup` | `lead_followups` | `lms.config/Entities/LeadFollowup.cs:9` |
| `LeadInvoiceDetail` | `lead_invoice_details` | `lms.config/Entities/LeadInvoiceDetail.cs:9` |
| `LeadLog` | `lead_logs` | `lms.config/Entities/LeadLog.cs:9` |
| `LeadLogResponse` | `lead_log_response` | `lms.config/Entities/LeadLogResponse.cs:9` |
| `LeadPushLog` | `lead_push_logs` | `lms.config/Entities/LeadPushLog.cs:9` |
| `LeadSource` | `lead_sources` | `lms.config/Entities/LeadSource.cs:9` |
| `LeadTestRide` | `lead_test_rides` | `lms.config/Entities/LeadTestRide.cs:9` |
| `LeadsCommsMapping` | `leads_comms_mapping` | `lms.config/Entities/LeadsCommsMapping.cs:9` |
| `MetaLog` | `meta_logs` | `lms.config/Entities/MetaLog.cs:9` |
| `ModelIdPartIdMaster` | `model_id_part_id_master` | `lms.config/Entities/ModelIdPartIdMaster.cs:9` |
| `PageMaster` | `page_master` | `lms.config/Entities/PageMaster.cs:9` |
| `PincodeMaster` | `pincode_master` | `lms.config/Entities/PincodeMaster.cs:9` |
| `ReferralCustomerDetail` | `referral_customer_details` | `lms.config/Entities/ReferralCustomerDetail.cs:9` |
| `StatusCode` | `status_codes` | `lms.config/Entities/StatusCode.cs:9` |
| `TestRideLogMapping` | `test_ride_log_mapping` | `lms.config/Entities/TestRideLogMapping.cs:9` |
| `WebhookLog` | `WebhookLog` | `lms.config/Entities/WebhookLog.cs:9` |

## State Machines
lms event-type enumerations found in code (no persisted status state machine evidenced):

| Field | Values |
|---|---|
| Lead event type (`EventType` property) | lead type values passed by `ProcessValidLeadService` / `ProcessInvalidLeadService`; `LEAD_PROCESS`, `PARTIAL_LEAD_PROCESS`, `UPDATE_LEAD_PROCESS` come from config keys of the same name (`leadLogs/Const/AppSettingsService.cs:25-27`) |

## Business Rules
lms rules shown by code:
- Lead source and lead-flow configuration are loaded per `source_id` before validation (`leadLogs/Services/LeadDelegate.cs:25-29`)
- Duplicate leads of type `dealer` are processed by `ProcessDuplicateLeadService` and still dispatched (`leadLogs/Services/LeadLogService.cs:84-90`, `ProcessDuplicateLeadService.cs:63`)
- Optional `countryCode` header selects the target country flow (`LeadAcquisitionController.cs:63`; DB keys `DOM_DB_CONN` / `SRILANKA_DB_CONN` in `AppSettingsService.cs`)

## Key Classes and Functions
lms key classes:

| Class / function | Role | Evidence |
|---|---|---|
| LeadDispatchService | Service Bus sender | `leadLogs/Services/LeadDispatchService.cs:21` |
| AddAzureClients | Key Vault | `leadLogs/Startup.cs:74-77` |
| LMSDbContext | SQL Server | `leadLogs/Startup.cs:67` |
| HttpClient | HTTP | `leadLogs/Services/WebhookService.cs:145` |

## Sequence Details
lms sequences: see DATA_FLOWS.md `Request Flows` (mermaid per flow, steps with file:line).

## Error Handling
lms: Controllers catch exceptions, log them and return `422 UnprocessableEntity` (e.g. `leadLogs/Controllers/LeadAcquisitionController.cs:71-74`); other status codes come from the service response object (`StatusCode(response.Status, response)`).

## Configuration Details
lms configuration keys (names only; full list in OVERVIEW.md): `DB_CONNECTION`, `LATLONG_3W_API_URL`, `LATLONG_COMMON_API_URL`, `LATLONG_EV_API_URL`, `LATLONG_RONIN_API_URL`, `LATLONG_RTR_API_URL`, `LATLONG_TOKEN_URL`, `OLD_LMS_URL`, `SERVICE_BUS_CONNECTION_STRING`, `TOPIC_NAME`.

## Edge Cases
lms edge cases evidenced in code:
- `LeadDispatchService.Dispatch` ignores its `topicName` argument and always uses the sender created for `TOPIC_NAME` (`leadLogs/Services/LeadDispatchService.cs:21,27`)
- `TOPIC_NAME`, `EVENT_SOURCE_VALUE`, `EVENT_TARGET_VALUE` are not in `appsettings*.json`; they must come from environment variables (`leadLogs/Const/AppSettingsService.cs:14,22-24`)

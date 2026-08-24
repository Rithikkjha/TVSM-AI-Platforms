# CentralisedAPI — Low Level Design

## API Endpoints Summary (401 Total)

| # | Controller | Route Prefix | API Count |
|---|-----------|--------------|-----------|
| 1 | JobCardController | JobCard/ | 107 |
| 2 | MasterController | Masters/ | 47 |
| 3 | SMRController | PartAPI/ | 29 |
| 4 | FRTModuleController | FRTModule/ | 21 |
| 5 | FRTMasterController | FRTMaster/ | 20 |
| 6 | PsfController | Psf/ | 19 |
| 7 | AttendanceController | Attendance/ | 17 |
| 8 | CustomerController | Customer/ | 16 |
| 9 | SalesController | Sales/ | 13 |
| 10 | ServiceReminderController | ServRem/ | 11 |
| 11 | InvoiceController | Invoice/ | 9 |
| 12 | PDIJobCardController | PDIJobCard/ | 9 |
| 13 | PickNDropController | PickNDrop/ | 9 |
| 14 | ServiceRequestController | ServReq/ | 9 |
| 15 | LoginController | Login/ | 8 |
| 16 | AMCController | AMC/ | 6 |
| 17 | FRTLabourController | FRTLabour/ | 6 |
| 18 | SelfJCController | SelfJobCard/ | 6 |
| 19 | AuditController | Audit/ | 4 |
| 20 | RepairRequestController | RepairRequest/ | 4 |
| 21 | SuperDMSController | SuperDMS/ | 4 |
| 22 | TVSConnectController | TVSConnect/ | 4 |
| 23 | App5SController | 5SApp/ | 3 |
| 24 | AuthenticationController | Authentication/ | 3 |
| 25 | DealerController | Login/ | 3 |
| 26 | IntegrityController | Integrity/ | 3 |
| 27 | PsfFeedBackController | Psf/ | 3 |
| 28 | PNDController | pnd/ | 2 |
| 29 | DashboardController | DashBoard/ | 1 |
| 30 | NotificationController | Notification/ | 1 |
| 31 | PartsController | Parts/ | 1 |
| 32 | PredictionController | Prediction/ | 1 |
| 33 | RegScannerController | RegScanner/ | 1 |
| 34 | TranscribeController | Transcribe/ | 1 |
| 35 | UsersController | Users/ | 1 |
| 36 | EnquiryController | Enquiry/ | 0 (commented out) |
| 37 | HomeController | (MVC) | 0 (not Web API) |
| 38 | ValuesController | (none) | 0 (commented out) |

**HTTP Method Distribution:** ~250 GET, ~145 POST, 1 PUT, 1 PATCH, 0 DELETE

---

## Top Controllers — Detailed API Listing

### JobCardController [RoutePrefix: JobCard/] — 107 APIs

Key endpoints (grouped by function):

**Customer/Vehicle Lookup:**
- GET IsMobileNumberExist, GET GetFrameDetails, GET ChkFrame, GET SearchJobCardDetails, GET SearchJobCardDetailsPagination, GET SearchJobCardDetailsbyFrameNo, GET SearchJobCardDetailsbyFrameNo_ForCSI

**Job Card CRUD:**
- POST SaveJobCardDetails, POST SaveAllJobCardDetails, POST CreateJobCard, GET PopulateJobCardDetailsAngular, POST UpdateJobCardDetails, GET GetJobCardandPSFDetailsBasedOnFrameNo, POST SaveJobcardStatus, POST CompleteJobCard, POST ValidateCompleteJobCard, GET ValidateIfJobCardCreationAllowed, GET CheckPendingJobCard, GET GetPendingJobCardListNew

**Complaints:**
- GET GetComplaint, POST AddComplaints, GET LoadComplaintsByGroupId, GET LoadComplaintsGroupAndComplaint, GET GetRankedComplaintGruopList, POST SaveFrameManufacturerAndComplaints

**Labour:**
- GET GetJobCardlabour, GET GetLabourDetailsApiNew, POST SaveJobCardLabour, POST DeleteJobCardLabour, GET LoadLabourApi, POST CreateAutoFRTLabour, POST SaveJobCardLabourEstimation

**Spare Parts:**
- GET GetJcardPartDetails, GET LoadPartNumbers, GET GetSelectedPartDetailsJobCard, GET CheckIssueMode, GET PopulateRackandBinDetailsJobCard, GET PopulateIssueSparePartDetailsById, GET GetDefaultIssueParts, GET GetStorageLocationApplicableForService_DIGI, POST SaveBulkIssueSparesToJobcard, POST SaveIssueSparesToJobcard, POST CalculateSpareTaxForJobCard, POST SaveAndUpdateIssueSparesForFrt

**Estimation:**
- GET PopulateJobCardEstimatedDetails, POST SaveJobcardEstimation, GET PopulateJobPartLabourEstimation, GET EstimatedCostPart, POST DeleteEstimateLabour, POST DeleteEstimateParts, POST SaveEstimationCost, POST SaveAndUpdateEstimationSparesForFrt

**Proforma Invoice:**
- POST SaveProformaInvoice (in JobCard context)

**WIP / Validation:**
- POST ValidateImage, GET GetWIPStatus

**Printing:**
- GET PrintJobcard, GET PrintCostEstimation_DIGI

**Checklists:**
- POST SaveAfterTrial, POST SaveBeforeTrial, POST SaveBeforeDelivery, GET GetStandardCheck, POST AddStandardChecks

**Insurance/AMC/VAS:**
- POST SaveInsurance, POST CreateJobCardAMC, GET GetJobCardAMC, GET loadCWIAMCTypeJobCardNew, GET GetValueAddedServicesDetails, GET GetVASDetailsByJobCardId, GET GetVASDetailsByJobCardIdModifyMode, POST SaveVASDetails

**PSF/DS:**
- POST SavePSFDSOTP, POST ResendSendDSClosure_OTP

**Warranty:**
- GET GetjcDetailsForWarrantyTagJobcard, GET GetFreeTextdetailsOfWarrantyTag, POST SaveWarrantyTagForJc, GET CheckIssueModeForSpares

**Pending Job Cards:**
- GET GetpendingjobcardDetails, GET GetPendingJobcardDetailsPagination, POST UpdatePendingJobcardStatus, GET GetDropDownDetailsForPendingJC, GET GetOrderDetailsForPendingJC, GET GetSparePOForJCPending, POST AddJCPendingSparePO, POST AddPendingJCPartsOrder, GET GetPendingJCPartsOrder

**Battery Claims:**
- GET GetBatteryClaimMasters, POST AddBatteryVendorPendingJC, GET GetBatteryVendorPendingJC

**Recall/Refit:**
- GET getRecallRefitStatus, POST updateRecallRefitRejectReason, POST updateRecallRefitParts, GET RecallRefitPartsWithJobCardId, GET RecallRefitParts

**Misc:**
- GET getLastJobServices, GET checkPartsAvailability, POST checkAndSendDelayNotification, POST updatePDT, POST SaveJobCardDetailsByCustomer, POST SavePartRequestDetails, POST UpdateCompActionStatus, GET CheckSMSSent, POST UpdateJobcardIDRangefromDMS, GET GetRevisitDetails, GET ECouponCodeValidate, POST checkOtp, GET getProbingSheetBasedOnComplaintid, GET GetNoOfJcCreatedForMonitoring, POST CheckEngineOilRecommendation, POST SaveOilRecommendationReason, GET CheckJobCardFlashingStatus, GET GetVehicleComprehensiveReport, GET GetHaritaInsuranceDetail, GET GetSeviceRequestDetails, GET GetComplaintsForSeviceRequest, POST SaveServiceRequestOptions, GET CheckMobileNoDuplicate

### MasterController [RoutePrefix: Masters/] — 47 APIs

- GET GetMasterDropDownDetails, GET GetHPSchemeByCompanyId, GET GetVehicleModelPartMasters
- GET GetCoreVehicleDetailsByFrameNo, POST CreateToken, POST CreateTokenByRF
- GET GetTokenAppointmentList, GET GetTknAppointRemarks, POST CancelToken, GET GetTokenCount
- GET GetJobCategoryDetails, GET GetLanguage, GET GetLiteralsForModule
- GET GetVehicleDetailsByRegnFrameNo, GET ECouponCodeValidate
- POST ResendOTP, POST UpdateRemarks
- GET GetVehicleServiceHistory, GET GetVehicleServiceHistory_DIGI, GET GetVehicleServiceHistoryByJobCardId
- GET GetPartDetailsbyPartNo, GET GetLabourDetails, GET LoadPMPMessage
- GET searchEmployee, POST saveEmployee, GET GetEmployeeDetailsByID
- GET GetIsCentralDigiDealer, POST SaveIsCentralDealer
- GET GetDigiHomeScreenMessage, GET GetIsWIPDealer, GET GetRelatedVehicles
- POST SaveDigiAppFeedback, GET GetNoOfUnallocatedJC
- GET GetMasterDataForLabor, GET GetServiceBulletin, GET GetNewsAnnouncement
- GET ValidateIfUpdateRequired, GET GetCompany
- GET FetchMasterDataForSuperDMS
- POST SendContactVerificationOTP, POST VerifyContactVerificationOTP
- POST UpdatePrimaryContactwithSecondary, GET GetGeoFencingDetails
- POST VerifyContactUpdateOTP, GET Details
- POST CreateTokenNew, GET CheckPremiumStatus

### LoginController [RoutePrefix: Login/] — 8 APIs

- GET GetDealerDetails, POST ValidateLogin, POST ResendOTP, POST VerifyOTP
- POST ValidateAuthToken, GET GetAccessToken, POST TestSendEmail, POST SaveEmployeeLoginDetails

### Other Controllers (Remaining 285 APIs)

**SMRController [PartAPI/] — 29 APIs:**
getCustomerByFrameNo, getFollowupDetails, saveEscalation, saveCallHistory, InsertFollowupSMR, SendSMS, GetFollowupMaster, getHighestCall, getEmployeePerformancePost, Getspecialreqforsmr, GetServiceReminderPost, UpdateFollowupAppointment, GetServiceReminderCountPost, InsertFollowup, getCentralizedAppVersion, GetSMRFAQs, GetDueForFollowUp, GetInFollowUp, GetCallAgain, GetNoShow, GetOpenAppointments, GetCallInfo, CreateFollowUp, CheckAppointmentStatus, CheckLeadStatus, GetFollowupHistory, GetDueForFollowUpCount, GetLeadDetails, +1 more

**FRTModuleController [FRTModule/] — 21 APIs:**
GetComplaintByJobCardId, GetComplaintById, SaveComplaint, ActionTaken, GetActionTakenById, SaveActionTaken, ActionTakenPart, GetActionTakenPartById, SaveActionTakenPart, ADDJobcardFRTDetails, UpdateFRTDetailsForJobCard, GetFRTDetail, GetAdditionalJobDetails, UpdateFRTAdditionalJobDetailsForJobCard, CheckIssueModeForSpares, generateAutoLaborPreview, CreateJobCard, CreateAutoFRTLabour, Estimation/GetFrtComplaint, Estimation/SaveFrtLabour, Estimation/AddFrtComplaints

**FRTMasterController [FRTMaster/] — 20 APIs:**
Symptom, Aggregate, SubAggregate (×2), Condition, Situation, Location, PhysicalObservation, Action, Variance, Part, SearchParts, GetFRTMasterDetail, UpdateFRTJobcardAction, GetFRTPeriodicMaintenanceandVehWashCost, GetStorageLocationandIssueModeList, CheckIfVehicleUnderWarranty, FetchFrtParts, FetchFRTVehicleVariant, FetchFRTMasterLabourDetails

**PsfController [Psf/] — 19 APIs:**
GetServiceAdvisorBranch, GetPSFRemarks, UpdatePSFRemark, GetAppointmentEmployees, GetMobJobTypes, CreateDIGICallLogs, GetPSFListForDMSPageLoad, CreatePSF, PopulatePSFDetails, ResendPsfDsOtp, UpdatePSFDsClosureStatus, getSalesPSFDetailsBasedonFrameNo, PopulatePSFDetails_3W, CreatePSF_3W, GetPsfMaster, Create2WPSF, SavewaybeoDetails, waybeointegration, GetWaybeoDealer

**AttendanceController [Attendance/] — 17 APIs:**
CreateAttendance, UpdateAttendance, AttendanceDashboard, AttendanceAdmin, SaveFaceCapture, getFaceCapture, AttendanceSummary, CreateAttendanceAdmin, DeleteAttendanceAdmin, GetHolidayAttendanceAdmin, GetWorkCategory, AttendanceEmpDashboard, EmployeeAttendanceList, GetAttendanceMasterAPI, SaveEmployeeForgotAttendance, SaveAttendanceNotCaptureReason, GetAttendanceNotCaptureDates

**CustomerController [Customer/] — 16 APIs:**
CreateCustomer, CreateCICInfo, GetCustomerinfoByMobileNo, GetCustomerDetailsByFrameNo, GetVehicleDetailsByFrameNo, CreateCustomerVehicle, getExistingCuswithmobileno, GetArea, updateCustMobileNo, CheckVehicleMappingWithMobileNoForAD, CheckVehicleMappingForAD, CheckVehicleMappingWithMobileNo, CreateIndividualCustMapVehicle, UpdateExistingIndividualCust, UpdateContactforCustomer, CreateMBOCustMapVehicle

**SalesController [Sales/] — 13 APIs:**
EnquirySearch, SalesDashboard, GetEnquiriesWithMobileNo_Digi, GetEnquiryDropdownValues_Digi, GetHPSchemeByCompanyId_Digi, GetModelColorByModelId_Digi, GetLikelyUserWithCustomerId_Digi, GetEnquiryDetailsByEnquiryNo, UpdateDMSEnquiryforvehicleinfo, UpdateDMSEnquiryforFollowupinfo, UpdateDMSEnquiry, GetCustomerDetails, GetCustomerVehicleEndUserDetailsBasedonContactNo

**ServiceReminderController [ServRem/] — 11 APIs:**
getEmployeeServRemPriority, CreateServRemainder, CloseAppointment, GetFrameBasedOnMobileNumber, UpdateSMRAppointment, PopulateServiceAppDetails, StaticServiceDropDownsList, LoadJobType, SaveServiceAppointmentDetails, SearchServiceAppointDetails, CreateServRemainderVoiceBot

**InvoiceController [Invoice/] — 9 APIs:**
GetJobCardDetailsByIdForProformaInvoice, SaveProformaInvoice, PrintJCProformaInvoices, LoadJobcardProformaInvoicedDetailsForViewMode, CalculateTaxDetails, GetPaymentMode, SaveInvoice, PrintJCInvoices, LoadJobcardInvoicedDetailsForViewMode

**PDIJobCardController [PDIJobCard/] — 9 APIs:**
getPDIVehicles, viewandModifybyJobcardId, MobGetCoreVehicleDetailsByFrameNo, SaveNewJobCard, getMobileJobType, UpdateJobcardCustomerSign, UpdateCompActionStatus, getVehicleCountforPDIDashboard, getVehicleDetailsforPDIDashboard

**PickNDropController [PickNDrop/] — 9 APIs:**
GenerateAuthToken, RedirectToRider, ValidateAuthToken, CreateAppointment, UpdateAppointment, Appointments, Distance, UpdateReference (PATCH), VerifyDealerEnabled

**ServiceRequestController [ServReq/] — 9 APIs:**
IsRepairRequestExists, GetPartNoDescriptionwithStock, GetRepairRequestList, SaveServiceRequest, GetDropDownListForServiceRequest, SapFundAvailable, GetMappedADs, GetRepairRequestListAMD, GetRepairRequestListAD

**AMCController [AMC/] — 6 APIs:**
GetAMCPickupDropSearch, GetCalculatedAMCAmount, CreateAMCPickupDrop, CloseAMCPND, GetServicePersons, ModifyAMCPND

**FRTLabourController [FRTLabour/] — 6 APIs:**
SearchManualFRTLabour (×2 overloads), CreateManualFRTLabour, UpdateManualFRTLabourStatus, CheckLabourIssueMode/{labourCode}/{issueModeId}, FetchPmlLabour

**SelfJCController [SelfJobCard/] — 6 APIs:**
GetVehicleList, CreateCustomerVehMappingandGetVehDetails, GetServiceCenters, GetVehicleDetail, CheckDealerSettings, ValidateKilometer

**AuditController [Audit/] — 4 APIs:**
ValidateLogin, GetDealers, GetMasterDropDown, ValidateAuditToken

**RepairRequestController [RepairRequest/] — 4 APIs:**
GetRepairRequests, GetServiceEmployees, GetRepairRequestById, SaveRepareRequest

**SuperDMSController [SuperDMS/] — 4 APIs:**
GenerateJWTForSuperDMS, ValidateLogin, GetDealers, GetMasterDropDown

**TVSConnectController [TVSConnect/] — 4 APIs:**
GetServiceReminderPost, GetSalesPSFQuestions, PostSalesPSF, CreatePSF

**AuthenticationController [Authentication/] — 3 APIs:**
Callback, ums/profileinfo, ums/logout

**App5SController [5SApp/] — 3 APIs:**
5SApp/getLocation, 5SApp/post5SData, 5SApp/getDetails

**DealerController [Login/] — 3 APIs:**
GetDealers, GetMasterDropDown, GetDealerBranchDetail

**IntegrityController [Integrity/] — 3 APIs:**
Verify, CheckPinning, CheckPinning2

**PsfFeedBackController [Psf/] — 3 APIs:**
GetPsfFeedbackCallLogs, GetPsfDSNotificationList, GetDsTrendPercentage

**PNDController [pnd/] — 2 APIs:**
PNDApprovalList, PostPNDEOWApproval

**Single-endpoint controllers (1 API each):**
DashboardController (getDigiDashboard), NotificationController (CreateFirebaseToken), PartsController (GetPartDetailsBasedoniRcode), PredictionController (GetHighRiskAndAMCRecommendation), RegScannerController (GetAccessToken), TranscribeController (MLTranscribeAudio), UsersController (Rider)

---

## Code Structure

```
CentralisedAPI/
├── EMSUI/                             (Main Web API Project - .NET Framework 4.8)
│   ├── Controllers/                   (38 API controllers with RoutePrefix attributes)
│   ├── Filters/                       (Auth filters: Authentication, BasicAuth, SuperDMS, HeaderToken, Audit, PnD, SJP)
│   ├── Helpers/                       (OtelHelper, HttpErrorMessageHelper)
│   ├── Webhook/                       (ApimTokenAcquisition, NotificationWebHookService, WipValidationService, P360EVWebhookService, FRTWebhookService, WhatsappWebhookService)
│   ├── MessageHandlers/               (APIKeyMessageHandler)
│   ├── Models/                        (View models, request/response DTOs)
│   ├── App_Start/                     (WebApiConfig, RouteConfig, FilterConfig, BundleConfig)
│   ├── Authentication.cs              (IAuthenticationFilter implementation - JWT + UMS dual auth)
│   ├── TokenManager.cs                (JWT generation/validation for all 6+ token types)
│   ├── CommonHost.cs                  (UMS header detection utilities)
│   ├── TokenValidation.cs             (Dealer ID validation from token claims)
│   ├── LogGeneration.cs               (File-based logging utility)
│   ├── MemoryCacheService.cs          (In-memory cache for UMS tokens)
│   ├── VaultManager.cs                (Azure Key Vault secret retrieval)
│   ├── Global.asax.cs                 (Application startup, TLS 1.2, OTel init)
│   └── Web.config                     (All configuration - connection strings, app settings)
├── EMS.BusinessLayer/                 (Business Logic - 46 classes)
│   ├── JobCardBL.cs                   (Job card CRUD, complaints, close)
│   ├── InvoiceBL.cs                   (Invoice generation, tax calculation)
│   ├── GSTTaxProcessor.cs             (GST tax engine)
│   ├── CentralTaxProcessor.cs         (Central tax rules post Oct 2021)
│   ├── MasterBL.cs                    (Master data operations)
│   ├── CustomerBL.cs                  (Customer management)
│   ├── SMRBL.cs                       (Service maintenance reminders)
│   ├── PsfBL.cs                       (Post-service feedback)
│   ├── AmcBL.cs                       (AMC management)
│   ├── FRTMasterBL.cs                 (FRT master data)
│   ├── FRTModuleBL.cs                 (FRT calculations)
│   ├── PredictionBL.cs                (CCE predictions)
│   ├── SMSTemplateBL.cs               (SMS template resolution)
│   ├── RegScannerBL.cs                (APIM config retrieval for token acquisition)
│   └── UMSAuthenticationBL.cs         (UMS token validation logic)
├── EMS.BusinessEntities/              (Data Objects - 186 classes)
│   ├── JobCard.cs, Customer.cs, etc.  (Domain entities / DTOs)
│   ├── RequestModel/                  (Request payload models)
│   ├── ResponseModel/                 (Response payload models)
│   └── Common.cs                      (Shared utility methods)
├── EMS.DataAccessLayer/               (Data Access - 49 classes)
│   ├── DALHelper.cs                   (Legacy SQL helper - SqlConnection/SqlCommand)
│   ├── DBFactoryHelper.cs             (Factory pattern SQL helper)
│   ├── SqlDataAccess.cs               (Generic SQL data access)
│   ├── ConstStoredProcedures.cs       (Stored procedure name constants)
│   ├── JobCardDAL.cs                  (Job card stored procedure calls)
│   ├── InvoiceDAL.cs                  (Invoice stored procedure calls)
│   ├── CustomerDAL.cs                 (Customer stored procedure calls)
│   └── Web References/               (SOAP service reference to SAP WCF)
└── packages/                          (NuGet packages folder)
```

---

## Database Schema

Data access uses ADO.NET stored procedures. Key tables (inferred from entities):

### Core Tables
| Table/Entity | Purpose |
|--------------|---------|
| Dealer | Dealer registration and profile |
| Branch | Dealer branches |
| Customer | Customer master |
| Vehicle | Vehicle registration (frame number, model, sale date) |
| JobCard | Job card header (status, dates, dealer, branch, technician) |
| JobCardComplaint | Complaints linked to job card |
| JobCardLabour | Labour items assigned to job card |
| JobCardSpares | Spare parts issued to job card |
| Invoice | Invoice header (proforma + final) |
| InvoiceDetail | Invoice line items |
| ServiceReminder | Upcoming service due records |
| PSF | Post-service feedback records |
| AMC | Annual maintenance contracts |
| Employee | Dealer employees (technicians, service advisors) |

### Connection Routing
```
DALHelper(SQLConnectionType.SqlOnlineDMS)  → DMSConnection (onlineDMS)
DALHelper(SQLConnectionType.SqlOraclePortal) → OracleSQLPortal (EMS_APP)
```

---

## Key Algorithms / Business Rules

### GST Tax Calculation (GSTTaxProcessor)
- Determines tax group based on item type and dealer state
- Applies CGST + SGST (intra-state) or IGST (inter-state)
- Central Tax rules changed post `CentralTaxDate` (04/10/2021)
- Handles multiple tax categories (Parts, Labour, AMC)

### Token Generation (TokenManager)
- HMAC-SHA256 signed JWT tokens
- Claims: encrypted DealerID, BranchID, RoleID
- Token types: Digi (12h), Audit (12h), SuperDMS (5min), RF (custom), SJP (1 month), PickNDrop (custom)
- Encryption via `MicroDMS.Utilities.MiscUtils.EncryptDecryptPassword`

### SMS Dispatch (SMSTemplateBL + Controllers)
- Template resolution from DB based on trigger event
- Multi-provider routing: Airtel IQ (primary) → Infobip (fallback)
- DLT compliance (Template ID, PE ID, TM ID)
- Notification Service (centralized) for newer flows via APIM

### APIM Token Acquisition (ApimTokenAcquisition)
- OAuth2 Client Credentials flow against Azure AD
- Tenant/Client/Secret stored in DB (per service type: WIP, NOTIFICATION_SERVICE, etc.)
- Returns Bearer token + APIM subscription key for downstream calls

---

## Configuration Handling

All config in `Web.config`:
- **Connection strings**: Named connections, environment-specific (Dev/UAT/Prod blocks commented)
- **AppSettings**: 100+ keys covering feature flags, external URLs, API keys, business rules
- **Azure Key Vault**: Used for dynamic secrets (SuperDMS key, SendGrid API key, Digi secrets)
- **Environment switching**: Manually comment/uncomment credential blocks per environment

---

## Request/Response Lifecycle

```
1. HTTP Request → IIS Pipeline
2. → MessageHandler (APIKeyMessageHandler - currently disabled)
3. → Auth Filter ([Authentication], [BasicAuthentication], [JWTSuperDMSAuthentication], etc.)
   - Validate token → Set HttpContext.Current.Session["DealerValue"]
   - UMS path: Validate via external UMS service → Cache result
4. → Controller Action
   - TokenValidation.CheckDealerValidation() — verify dealer from token matches request
   - Call Business Layer (BL)
5. → BL processes logic, calls DAL
6. → DAL executes stored procedure via DALHelper
7. → Return Output { statusCode, statusMessage, OutputList }
```

---

## Validation Logic

- **Token validation**: Every authenticated endpoint calls `TokenValidation.CheckDealerValidation(dealerId)` to ensure the token's dealer matches the request
- **Input deserialization**: Many GET endpoints accept JSON-serialized objects via query string `Id` parameter, deserialized in controller
- **Business rules**: Validated in BL layer (e.g., app version check before login, mobile number existence check)
- **No model validation framework**: Manual validation in controllers/BL

---

## Error Handling

- **Controller level**: Try/catch wrapping all actions
- **Response format**: `Output { statusCode: int, statusMessage: string, OutputList: object }`
- **Logging**: `LogGeneration.WriteToFile(exception)` — writes to file system
- **Auth failures**: Return `TokenOutput { Message: string }` with 401 status
- **No global exception handler**: Each controller handles its own errors

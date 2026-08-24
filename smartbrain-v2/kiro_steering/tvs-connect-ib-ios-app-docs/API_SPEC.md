# TVS Connect iOS — API Specification

> **Scope:** This document captures the API contract as *consumed by the
> TVS Connect iOS app*. It covers REST, GraphQL, MQTT, and BLE protocol
> interfaces.
>
> **Important:** Endpoint paths, payloads, and schemas in this document are
> reconstructed from the app's consumption patterns and conventions. All
> paths marked `[VERIFY WITH BACKEND TEAM]` must be confirmed against the
> authoritative backend API documentation before use.

---

## 1. API Overview

### 1.1 API Architecture

TVS Connect consumes four distinct interface types:

| Interface | Technology | Use Case |
|-----------|-----------|----------|
| REST | Alamofire over HTTPS | CRUD, auth, profile (500+ endpoints) |
| GraphQL | Apollo (HTTPS + WSS) | P360 vehicle mgmt, geofencing, live tracking |
| MQTT | CocoaMQTT over TLS | Real-time telemetry streaming |
| EventHub | HTTPS (Azure) | Telemetry upload per vehicle |

### 1.2 Base URL Structure (per Environment)

Resolved at runtime by `NetworkConfiguration.shared` using `country` +
`buildEnvironment`. Exact hosts are environment-specific.

| Environment | Pattern | Notes |
|-------------|---------|-------|
| Development | `https://dev-<service>.<domain>/` | `[VERIFY WITH BACKEND TEAM]` |
| QA | `https://qa-<service>.<domain>/` | `[VERIFY WITH BACKEND TEAM]` |
| Staging | `https://staging-<service>.<domain>/` | `[VERIFY WITH BACKEND TEAM]` |
| Production | `https://<service>.tvsmotor.com/` | `[VERIFY WITH BACKEND TEAM]` |

> Hosts are managed via the `NetworkConfiguration` singleton (e.g.,
> `hostURL`, `hostURLMob`, `serverURL`, `tvsServerURL`, `vinHostURL`,
> `tvsSiteCoreURL`). Per-country variants apply.

### 1.3 Authentication Mechanism

| Aspect | Detail |
|--------|--------|
| Primary | Bearer token (issued after OTP validation) |
| Secure calls | RSA-signed token for sensitive endpoints |
| Storage | Keychain + Realm |
| Refresh | Token refresh endpoint; force logout on failure |
| Push token | FCM token registered post-login |

### 1.4 Common Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | `Bearer <token>` | Yes (authenticated endpoints) |
| `Content-Type` | `application/json` | Yes (POST/PUT) |
| `Accept` | `application/json` | Yes |
| `User-Agent` | Constructed by `TvsUserAgent` (app version, OS, device) | Yes |
| `country` / locale | Region indicator | `[VERIFY WITH BACKEND TEAM]` |
| `x-api-key` | Service key (where applicable) | `[VERIFY WITH BACKEND TEAM]` |

### 1.5 API Versioning Approach

- REST: path-based or header-based versioning `[VERIFY WITH BACKEND TEAM]`
- GraphQL: schema-evolution (no URL versioning); managed via `schema.graphqls`
- App-side compatibility gated by app version check (`AppUpdateService`)

---

## 1A. Endpoint Inventory & Module Map

> Source of truth: `SourceCode/TVS/SupportingFiles/WebService/APIList.swift`.
> Each module below corresponds to a Swift `struct` inside `APIList`.
> Counts reflect endpoint URL constants defined in that file.

### 1A.1 Totals at a Glance

| Metric | Count |
|--------|-------|
| REST endpoint constants (in `APIList.swift`) | **~303** |
| Module groups (structs) in `APIList.swift` | **41** |
| GraphQL operations (P360 — `CODPSchema/`) | See §8 (separate) |
| MQTT topics | See §9 (separate) |
| EventHub endpoints (per vehicle) | 6 (see §10) |

> ⚠️ Some relative paths repeat across vehicle-specific modules (e.g.,
> `/ride` appears in `U399C_API`, `U400_API`, `N597_API`, `U368_API`),
> so unique backend paths are fewer than the constant count.

### 1A.2 Module Summary (Module → Use Case → Endpoint Count)

| # | Module (struct) | Primary Use Case | Endpoints |
|---|-----------------|------------------|-----------|
| 1 | `Main` | Auth & onboarding: register, login, OTP, tokens, consent, app version, 3rd-party keys | 31 |
| 2 | `Dashboard` | Home dashboard, mobile settings, parked location, mileage, badges, CSI/NPS feedback | 25 |
| 3 | `IOT` | Ride/travel data CRUD for connected vehicles (multi-model), speed analysis, to-do | 27 |
| 4 | `P360Apis` | EV/P360 platform: telemetry, charging, geofence, timefence, locations, emergency contacts | 50 |
| 5 | `AddBike` | Vehicle onboarding via VIN/frame, emergency contact, owner OTP | 13 |
| 6 | `Profile` | Profile edit, cumulative data, delete profile, marketing consent | 9 |
| 7 | `TVSWeb` | Static web content (domestic): about, contact, T&C, privacy | 9 |
| 8 | `IBTVSWeb` | Static web content (international, localized) | 9 |
| 9 | `GeoFence` | Geofence CRUD + alert history | 6 |
| 10 | `Help` | FAQ, feedback (v1/v2), user guide, feedback type | 5 |
| 11 | `Navigation` | Recent & favourite locations | 4 |
| 12 | `U399C_API` | RR310 ride, widget, TPMS history | 4 |
| 13 | `U400_API` | U400 ride, widget, TPMS history | 4 |
| 14 | `N597_API` | N597 ride, widget, TPMS history | 4 |
| 15 | `Notification` | In-app notifications (domestic) | 4 |
| 16 | `U368_API` | U368 ride, widget | 3 |
| 17 | `News` | News feed (all/cricket/football) | 3 |
| 18 | `NotificationIB` | In-app notifications (international) | 3 |
| 19 | `ManageProfile` | Delete profile flow (reason, delete, verify OTP) | 3 |
| 20 | `Common` | Crash-alert features, device details | 2 |
| 21 | `DeleteAndRenameBike` | Remove / rename vehicle | 2 |
| 22 | `Breakdown` | Roadside assistance type list + request | 2 |
| 23 | `CrashDetect` | Crash alert config (SMS / IB email) | 2 |
| 24 | `UserSetting` | User settings list / save | 2 |
| 25 | `UserAddress` | User address list / manage | 2 |
| 26 | `Weather` | Weather + air quality index | 2 |
| 27 | `OTA` | Over-the-air firmware (app + TNT URL) | 2 |
| 28 | `AppleSign` | Apple sign-in token / revoke | 2 |
| 29 | `BluArmor` | Smart helmet accessory add / delete | 2 |
| 30 | `PushNotification` | FCM token register / deregister | 2 |
| 31 | `BrandFeed` | Admin/brand notification feed | 1 |
| 32 | `VoiceAssist` | Voice command logging | 1 |
| 33 | `VINSample` | VIN sample image reference | 1 |
| 34 | `Kogo` | KogoAuto JWT token | 1 |
| 35 | `ShareExtension` | Resolve lat/long from shared map URL | 1 |
| 36 | `VehicleConfigurationList` | Vehicle feature config | 1 |
| 37 | `Favorite` | (Placeholder — no endpoints defined) | 0 |
| 38 | *(top-level paths)* | EventHub & 3rd-party base paths (non-struct constants) | — |
| | **TOTAL** | | **~303** |

### 1A.3 Detailed Endpoint Inventory (by Module)

> Relative paths are appended to the runtime base URL resolved by
> `NetworkConfiguration.shared` (`serverPath`, `hostUrl`, etc.).

**`Main` — Authentication & Onboarding**

| Constant | Relative Path |
|----------|---------------|
| register | `/RegisterUser/CreateUser` |
| login | `/UserLogin/Login` |
| loginV1 | `/UserLogin/Loginv1` |
| newLoginV3 | `/v3/UserLogin/Loginv3` |
| replaceICEUserWithEV | `/v3/userlogin/replaceICEnumber` |
| verifyMobileUpdateOTP | `/manageprofile/verifymobileupdateotp` |
| getUpdateMobileOTP | `/manageprofile/GetOTPForUpdateMobileNumber` |
| logout | `/UserLogin/Logout?` |
| verifySignUpOTP | `/RegisterUser/VerifyOTP` |
| verifySignInOTP | `/UserLogin/VerifyLoginOtp` |
| verifyNewSignInOTP | `/v3/userlogin/verifyloginotp` |
| generateOrResendOTP | `/RegisterUser/GenerateOTP` |
| generateNewOrResendOTP | `/RegisterUser/GenerateOTP` |
| cityList | `/CityMaster/GetCityMaster` |
| manageAssets | `/AppAsset/AssetByUser` |
| appVersion | `/UserLogin/getAppVersion` |
| countryList | `/RegisterUser/GetCountryList` |
| countriesMaster | `/CityMaster/GetCountryMaster` |
| getAllThirdParyKeys | `/secret?platform=ios` |
| refreshToken | `/RegisterUser/RefreshJWTToken` |
| upgradeToken | `/UpgradeToken` |
| inAppUserFeedback | `/InAppFeedback` |
| getUserConsent | `/userconsent?mobileNumber=` |
| setUserConsent | `/v3/userconsent` |
| getNewAllThirdParyKeys | `/v3/secret?platform=ios` |
| addVehicleByFrameOrInvoice | `/v3/vehicle/vehiclelistbyframeinvoice` |
| addVehicleByFrameAndEngineNo | `/v3/vehicle/vehiclelistbyframeengineno` |
| vehicleMakeModelList | `/vehicle/makemodelmaster` |
| cityAndStateList | `/citystatemaster` |
| getBannerLinks | `/GetAmBannerImagelink` |
| getframenoandp360token | `/home/getframenoandp360token?` |

**`Dashboard` — Home & Settings**

| Constant | Relative Path |
|----------|---------------|
| profileImage | `/Image/ProfileImage` |
| dashboard | `/v3/UserDashboard/GetDashboardDetail?userId=` |
| onboarding | `/v3/Vehicle/GetOnBoarding?mobileNumber=` |
| crashAlertTime | `/UserLogin/CrashAlertDate` |
| bannerImage | `/AppBanner/GetAppbanner` |
| saveLastParkedLocation | `/LastLocationParkedController/SaveLastLocationParked` |
| getLastParkedLocation | `/LastLocationParkedController/GetLastLocationParked` |
| insertMileageForVehicle | `/MileageForVehicleController/InsertMileageForVehicle` |
| getAllMileage | `/MileageForVehicleController/GetAllMileage` |
| clearAllMileage | `/MileageForVehicleController/ClearAllMileage` |
| getBadgesList | `/Vehicle/GetUserBadgesList?` |
| getMobileSettings | `/mobilesetting?Platform=iOS&Brand=` |
| getU279AppExperienceSettings | `/v2/mobilesetting?Platform=iOS&Brand=` |
| getSettingsInfoList | `/mobilesettinginfo?Platform=` |
| getFaq | `/v2/Faq/GetFaq` |
| getCSIFdbk | `/CSIFeedbackAvailable?FrameNo=` |
| rescheduleCSIFdbk | `/CSIFeedbackReschedule` |
| postCSIFdbk | `/CSIFeedback` |
| getNPSFdbk | `/NPSFeedbackAvailable?FrameNo=` |
| postNPSFdbk | `/NPSFeedback` |
| rescheduleNPSFdbk | `/NPSFeedbackReschedule` |
| activateMacID | `/Vehicle/ActivateMMIMacId?macid=` |
| nonconnectedvehicledeatils | `/vehicle/nonconnecteddashboard` |
| ncVehicleDetails | `/vehicle/vehicledetails` |
| updateNCVehicleName | `/vehicle/vehiclenickname` |

**`IOT` — Connected Vehicle Ride/Travel Data**

| Constant | Relative Path |
|----------|---------------|
| insertNonIOTTravel | `/ApacheNonIOT/inserttraveldataForNonIOTApache` |
| insertTravelN112 | `/Travel/inserttraveldataForApache` |
| insertTravelN251 | `/N251/inserttraveldataForN251BLE` |
| getTravelList | `/Travel/GetTravelList?` |
| getTravelListV2 | `/v2/Travel/GetTravelList?` |
| getTravelListV3 | `/v3/Travel/GetTravelList?` |
| updateTravelName | `/Travel/UpdateTravelName` |
| deleteTravel | `/Travel/DeleteTravel` |
| deleteTravelU408 | `/ride` |
| deleteRideU279 | `/v2/ride` |
| updateTravelNameU408 | `/ride` |
| insertTravelN109 | `/N109/inserttraveldataForN109` |
| insertTravelU347 | `/U347/inserttraveldataForU347` |
| getTravelListU408 | `/ride?` |
| getTravelListU408V2 | `/v2/ride?` |
| insertTravelU408 | `/ride` |
| setFavoriteRide | `/ride/favourite` |
| insertTravelN360 | `/ride` |
| getTravelListN360V2 | `/v2/ride?` |
| favoriteRideU279 | `/v2/ride/favourite` |
| setFavouriteRides | `/N251/setFavouriteRides` |
| deleteMultipleRides | `/N251/deleteMultipleRides` |
| getAllTravelList | `/Travel/GetAllTravelList?` |
| getSpeedAnalysisData | `/Travel/GetSpeedAnalysis` |
| getTodoList | `/TodoList/GetTodoList` |
| addOrUpdateToDoList | `/TodoList/AddOrUpdateToDoList` |
| manageToDoList | `/TodoList/ManageToDoList` |

**`P360Apis` — EV / P360 Connected Platform**

| Constant | Relative Path |
|----------|---------------|
| getLatestDeviceData | `/home/getlatestdevicedata?` |
| registerPushNotification | `/notification/pushnotificationfcmtokenregistration` |
| deRegisterPushNotification | `/notification/pushnotificationfcmtokenderegistration` |
| getCumulativeRideData | `/vehicle/getcumulativeridedata?` |
| getChargingHistorySessionSummaryData | `/charging/charginghistory?` |
| vehicleStatsChargingSummary | `/charging/vehiclestatschargingsummary?` |
| getTripPoints | `/charging/charginggraph?` |
| getAllSharedDestinations | `/home/getallshareddestinations?` |
| getAllRecentLocations | `/home/getallrecentlocations?` |
| getAllFavoriteLocations | `/home/getallfavoritelocations?` |
| getAllSharedLiveLocation | `/home/getallsharedlivelocation?` |
| getCurrentWeatherData | `/home/getcurrentweatherdata?` |
| getRideStatsList | `/ride/rideStats?` |
| getGeofenceList | `/geofence/getgeofencelist?` |
| updateGeofence | `/geofence/updategeofence` |
| addGeofence | `/geofence/addgeofence` |
| removeGeofence | `/geofence/deletegeofence` |
| getGeofenceAlertHistoryData | `/geofence/getallgeofencealerts?` |
| getgeofencedetails | `/geofence/getgeofencedetails?` |
| getOverspeedThreshold | `/vehicle/getoverspeedalert?` |
| getTrackingPoints | `/socanalysis/trackingpoints?` |
| addFavouriteLocation | `/location/addfavoritelocation` |
| addRecentLocation | `/location/addrecentlocation` |
| shareDestination | `/location/sharedestination` |
| deleteFavouriteLocation | `/location/deletefavoritelocation` |
| editFavouriteLocation | `/location/editfavoritelocation` |
| updateNickName | `/vehicle/updatenickname` |
| getEmergencyContact | `/emergencycontact/getemergencycontacts?` |
| updateEmergencyContact | `/emergencycontact/editemergencycontact` |
| deleteEmergencyContact | `/emergencycontact/deleteemergencycontacts` |
| saveEmergencyContact | `/emergencycontact/saveemergencycontacts` |
| vehicleStatsRideCharingCumulativeData | `/vehicle/getcumulativeridechargingsummary?` |
| shareLiveLocation | `/location/sharelivelocation` |
| stopShareLiveLocation | `/location/stoplivelocation` |
| getHomeChargerLatestData | `/homecharging/gethomechargerlatestdata?` |
| getHomeChargerCommandStatus | `/homecharging/gethomechargercommandstatus?` |
| getHomeChargerChargingCumulativeData | `/homecharging/gethomechargerchargingcummulativedata?` |
| getPortableChargerChargingCumulativeData | `/homecharging/getportablechargerchargingcummulativedata?` |
| setOverSpeedThreshold | `/vehicle/setoverspeedalert` |
| getHomeChargingHistoryData | `/homecharging/homechargercharginghistory?` |
| getPortableChargerChargingHistoryData | `/homecharging/getportablechargercharginghistory?` |
| getBatteriesLatestData | `/homecharging/getbatterieslatestdata?` |
| setHomeChargerSetting | `/homecharging/sethomechargersettings` |
| getTimefenceAlertConfigData | `/timefence/gettimefencealertconfig?` |
| setTimefenceAlertData | `/timefence/settimefence` |
| updateTimefenceAlertData | `/timefence/updatetimefence` |
| deleteTimefence | `/timefence/deletetimefence` |
| getHomeChargingPoints | `/homecharging/getChargingPoints?` |
| getPortableChargerLatestData | `/portablecharger/getportablechargerlatestdata?` |
| getPortableChargerCommandStatus | `/portablecharger/getportablechargercommandstatus?` |


**`AddBike` — Vehicle Onboarding**

| Constant | Relative Path |
|----------|---------------|
| vinBikeCount | `/getCustomerBikeCountAPI?MobileNo=` (vinServerPath) |
| vinAuthCheck | `/Multipleframenocheck.jsp?frameno=` (vinServerPath) |
| getVinDetail | `/getCustomerBikeDetailsAPI?FrameNumber=` (vinServerPath) |
| addVehicle | `/Vehicle/AddVehicle` |
| addContact | `/v3/EmergencyContact/AddEmergencyContact` |
| verifyOTPforBikeOwner | `/Vehicle/VerifyOTPforBikeOwner` |
| sendOTPtoBikeOwner | `/Vehicle/SendOTPtoBikeOwner` |
| getHelpSupport | `/UserSupport/AddSupport` |
| withoutVINDetail | `/Vehicle/AddVehicleAddVehicleWithoutVINDetails` |
| getCountrySpecificVehicleList | `/vehicle/countryvehicle` |
| addVehicleNew | `/v3/Vehicle/AddVehicle` |
| createNewUser | `/v3/userlogin/getnewevuserdetails` |
| updateActiveVehilce | `/v3/Vehicle/markactivevehicle?userVehicleId=` |

**`GeoFence` — Geofencing**

| Constant | Relative Path |
|----------|---------------|
| getGeofenceList | `/geofence/getgeofencelist?` |
| updateGeofence | `/geofence/updategeofence` |
| addGeofence | `/geofence/addgeofence` |
| removeGeofence | `/geofence/deletegeofence` |
| getGeofenceAlertHistoryData | `/geofence/getallgeofencealerts?` |
| getgeofencedetails | `/geofence/getgeofencedetails?` |

**`Navigation` — Locations**

| Constant | Relative Path |
|----------|---------------|
| createRecent | `/location/recent` |
| getRecentLocation | `/location/recent?vin=` |
| addFavouriteLocation | `/location/favourite` |
| getFavouriteLocation | `/location/favourite?vin=` |

**Vehicle-Specific Ride APIs** (`U399C_API`, `U400_API`, `N597_API`, `U368_API`)

| Constant | Path | Present In |
|----------|------|-----------|
| saveRide | `/ride` | U399C, U400, N597, U368 |
| widgetOpration | `/widget` | U399C, U400, N597, U368 |
| fetchRide | `/v2/ride` | U399C, U400, N597, U368 |
| fetchTpmsHistory | `/tpms/history?` | U399C, U400, N597 |

**Smaller Modules**

| Module | Constants → Paths |
|--------|-------------------|
| `Profile` | editProfile `/v3/ManageProfile/EditProfile`; vehicleCumulativeData `/Travel/GetVehicleCumulativeData?`; u408VehicleCumulativeData `/vehicle/overview?`; verifyDeleteProfileOtp `/ManageProfile/verifydeleteprofileotp`; getDeleteProfileOtp `/ManageProfile/getdeleteprofileotp`; deleteProfileReason `/ManageProfile/deleteprofilereason`; getUserConsent `/userconsent/marketing?email=`; saveUserConsent `/userconsent/marketing`; updateProfileImage `/Image/ProfileImage` |
| `Notification` | getNotificationList `/Notification/NotificationList`; notificationRead `/Notification/Read`; notificationReadMQTT `/notification/readmqttnotification`; notificationUnread `/Notification/Unread` |
| `NotificationIB` | getNotification `/Notification/GetNotificationByUser?userId=`; clearNotification `/Notification/ClearNotification`; notificationSeen `/Notification/MakeSeen` |
| `Help` | getFaq `/FAQ/getfaq`; addFeedback `/Feedback/AddFeedback`; addFeedbackV2 `/V2/Feedback/AddFeedback`; userGuide `/UserGuide/GetUserGuide?userid=`; getFeedbackType `/Feedback/Feedbacktype` |
| `ManageProfile` | deleteProfileReason `/deleteprofilereason`; deleteProfile `/DeleteProfile`; verifyDeleteProfileOTP `/verifydeleteprofileotp` |
| `Breakdown` | getAssistanceTypeList `/Assistance/GetAssistanceTypeList?VehicleTypeId=`; requestAssistance `/Assistance/RequestAssistance` |
| `CrashDetect` | crashDetectSMS `/UserSetting/GetSMSonCrashDetection?`; crashDetectIBEmail `/crashalert?` |
| `UserSetting` | settingList `/UserSetting/GetSettingList?`; saveSetting `/UserSetting/SaveSettingForUser` |
| `UserAddress` | userAddressList `/useraddress?`; userAddress `/useraddress` |
| `Weather` | weather `/weather`; airQuality `/airqualityindex` |
| `News` | allNews `/news`; cricketNews `/cricket`; footballNews `/football` |
| `OTA` | ota `/ota`; otaTNTURL `https://ft8.trakntell.com/tnt/servlet/tntDevAPI` |
| `Common` | features `/Support/getCrashAlertFeatures`; deviceDetails `/AddDeviceDetails` |
| `DeleteAndRenameBike` | deleteVehicle `/Vehicle/RemoveVehicle`; renameVehicle `/Vehicle/UpdatevehicleNickname` |
| `PushNotification` | register `/notification/pushnotificationfcmtokenregistration`; deRegister `/notification/pushnotificationfcmtokenderegistration` |
| `BluArmor` | accessories `/accessory`; deleteAccessories `/accessory?` |
| `AppleSign` | appleGenerateAndRefreshToken `https://appleid.apple.com/auth/token`; appleRevokeToken `https://appleid.apple.com/auth/revoke` |
| `BrandFeed` | getBrandFeed `/Notification/Getadminnotificationbyuser?` |
| `VoiceAssist` | userVoiceCommand `/UserVoiceCommand` |
| `VINSample` | vinSample `/VinSampleImage/GetVimSampleImage` |
| `Kogo` | getJWTToken `/api/UserLogin/getkogojwt` |
| `ShareExtension` | getLatLongFromURL `/maps/getmapdata` |
| `VehicleConfigurationList` | vehicleConfigurationList `/api/getvehiclefeatureconfig` |
| `TVSWeb` / `IBTVSWeb` | Static web pages: support, aboutus, contactus, termsconditions, privacypolicy (domestic + localized international variants) |

> **Note on methods:** `APIList.swift` stores only URL strings; HTTP methods
> (GET/POST/PUT/DELETE) are set at call sites in the service/ViewModel layer.
> Methods shown in §2–§7 are representative — confirm at the call site or with
> the backend team.

---

## 2. Authentication APIs

> Base path placeholder: `/api/Login` `[VERIFY WITH BACKEND TEAM]`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/Login` | POST | None | Request OTP for mobile number |
| `/api/Login/ValidateOTP` | POST | None | Validate OTP, issue token |
| `/api/Login/RefreshToken` | POST | Refresh token | Refresh access token |
| `/api/Login/Logout` | POST | Bearer | Terminate session |

### 2.1 POST /api/Login — Request OTP

**Auth:** None  
**Headers:** `Content-Type: application/json`, `User-Agent`

**Request Body:**
```json
{
  "mobileNumber": "string",
  "countryCode": "string",
  "deviceId": "string"
}
```

**Success (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "otpReferenceId": "string",
    "otpExpirySeconds": 120,
    "resendAfterSeconds": 30
  }
}
```

**Error responses:**
| Status | Meaning |
|--------|---------|
| 400 | Invalid mobile number / country code |
| 429 | Too many OTP requests (throttled) |
| 500 | Server error |

**Validation rules:**
- `mobileNumber`: numeric, valid length per country code
- `countryCode`: ISO/dial-code format

### 2.2 POST /api/Login/ValidateOTP — Validate OTP

**Auth:** None  
**Request Body:**
```json
{
  "mobileNumber": "string",
  "otp": "string",
  "otpReferenceId": "string",
  "deviceId": "string",
  "fcmToken": "string"
}
```

**Success (200):**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "tokenExpiry": "ISO-8601 datetime",
    "userId": "string",
    "isNewUser": false,
    "profile": {
      "name": "string",
      "email": "string",
      "mobileNumber": "string"
    }
  }
}
```

**Error responses:**
| Status | Meaning |
|--------|---------|
| 400 | Invalid/expired OTP |
| 401 | OTP mismatch |
| 410 | OTP reference expired |

**Validation rules:**
- `otp`: numeric, fixed length (e.g., 4–6 digits) `[VERIFY WITH BACKEND TEAM]`

### 2.3 POST /api/Login/RefreshToken — Refresh Token

**Auth:** Refresh token  
**Request Body:**
```json
{ "refreshToken": "string", "deviceId": "string" }
```

**Success (200):**
```json
{
  "status": "success",
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "tokenExpiry": "ISO-8601 datetime"
  }
}
```

**Error:** 401 → triggers forced logout (`LogoutViewModel.clearLoggedinUserData`)

### 2.4 POST /api/Login/Logout — Logout

**Auth:** Bearer  
**Request Body:**
```json
{ "deviceId": "string", "logoutAllDevices": false }
```

**Success (200):** `{ "status": "success", "code": 200 }`

---

## 3. Vehicle Management APIs

> Base path placeholder: `/api/Vehicle` `[VERIFY WITH BACKEND TEAM]`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/Vehicle/List` | GET | Bearer | User's vehicles |
| `/api/Vehicle/Register` | POST | Bearer | Register vehicle (VIN) |
| `/api/Vehicle/Details/{vehicleId}` | GET | Bearer | Vehicle details |
| `/api/Vehicle/Update` | PUT | Bearer | Update vehicle |
| `/api/Vehicle/Remove` | DELETE | Bearer | Remove vehicle |

### 3.1 GET /api/Vehicle/List

**Success (200):**
```json
{
  "status": "success",
  "data": {
    "vehicles": [
      {
        "vehicleId": "string",
        "vin": "string",
        "vehicleTypeId": 23,
        "series": "string",
        "modelName": "string",
        "registrationNumber": "string",
        "theme": 1,
        "isPrimaryUser": true,
        "isIotEnabled": true
      }
    ]
  }
}
```
> `vehicleTypeId` maps to `BLEType` (e.g., 23 = U399C, 9 = N251, 22 = U408).

### 3.2 POST /api/Vehicle/Register (VIN-based)

**Request Body:**
```json
{
  "vin": "string",
  "registrationNumber": "string",
  "modelCode": "string"
}
```

**Success (201):**
```json
{ "status": "success", "data": { "vehicleId": "string", "isIotEnabled": true } }
```

**Error responses:**
| Status | Meaning |
|--------|---------|
| 400 | Invalid VIN format |
| 409 | Vehicle already registered |
| 422 | VIN not recognized |

**Validation rules:**
- `vin`: format + checksum validation `[VEHICLE-SPECIFIC]` `[VERIFY WITH BACKEND TEAM]`

### 3.3 GET /api/Vehicle/Details/{vehicleId}
Returns full vehicle profile; schema superset of list item.

### 3.4 PUT /api/Vehicle/Update
```json
{ "vehicleId": "string", "registrationNumber": "string", "nickname": "string" }
```

### 3.5 DELETE /api/Vehicle/Remove
```json
{ "vehicleId": "string" }
```

---

## 4. Dashboard & Telemetry APIs

> Base path placeholders `[VERIFY WITH BACKEND TEAM]`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/Dashboard/Summary` | GET | Bearer | Dashboard summary |
| `/api/Dashboard/RideStats` | GET | Bearer | Ride statistics |
| `/api/Telemetry/Upload` | POST | SAS (EventHub) | Telemetry upload |
| `/api/Fuel/Status` | GET | Bearer | Fuel status |
| `/api/Battery/Status` | GET | Bearer | EV battery status |

### 4.1 GET /api/Dashboard/Summary
```json
{
  "status": "success",
  "data": {
    "vehicleId": "string",
    "odometer": 12345,
    "fuelLevel": 75,
    "lastRideDate": "ISO-8601",
    "healthStatus": "string",
    "alerts": []
  }
}
```

### 4.2 GET /api/Dashboard/RideStats
```json
{
  "status": "success",
  "data": {
    "totalRides": 120,
    "totalDistanceKm": 4520.5,
    "avgEcoScore": 82,
    "rides": [
      { "rideId": "string", "date": "ISO-8601", "distanceKm": 12.3, "ecoScore": 88 }
    ]
  }
}
```

### 4.3 POST /api/Telemetry/Upload (EventHub)
See Section 10 for EventHub specifics. Payload is per-vehicle telemetry,
JSON or Protobuf-derived.

### 4.4 GET /api/Fuel/Status
```json
{ "status": "success", "data": { "fuelLevelPercent": 75, "rangeKm": 210, "isLow": false } }
```

### 4.5 GET /api/Battery/Status (EV)
```json
{
  "status": "success",
  "data": {
    "socPercent": 64,
    "rangeKm": 90,
    "chargingState": "idle | charging | full",
    "timeToFullMinutes": 0
  }
}
```

---

## 5. Navigation APIs

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/Navigation/Route` | GET | Bearer | Compute route |
| `/api/Navigation/SaveRoute` | POST | Bearer | Save route/favorite |
| `/api/Dealers/NearMe` | GET | Bearer | Nearby dealers (LatLong) |

### 5.1 GET /api/Navigation/Route
**Query params:** `originLat`, `originLng`, `destLat`, `destLng`, `provider`
```json
{
  "status": "success",
  "data": {
    "distanceMeters": 5400,
    "durationSeconds": 900,
    "polyline": "encoded-string",
    "steps": [ { "instruction": "string", "distanceMeters": 120 } ]
  }
}
```
> Provider chosen by region (Mappls India / Google / HERE). See HLD §4.4.

### 5.2 POST /api/Navigation/SaveRoute
```json
{ "name": "string", "origin": {"lat":0,"lng":0}, "destination": {"lat":0,"lng":0} }
```

### 5.3 GET /api/Dealers/NearMe
**Query params:** `lat`, `lng`, `radiusKm`, `vehicleType`
```json
{
  "status": "success",
  "data": {
    "dealers": [
      { "dealerId": "string", "name": "string", "lat": 0, "lng": 0, "distanceKm": 2.1, "phone": "string" }
    ]
  }
}
```
> Uses LatLong dealer endpoints (`latLongAllDealersURL`,
> `latLongNtorqDealersURL`, `latLongU399CDealersURL`). `[VEHICLE-SPECIFIC]`

---

## 7. OTA APIs

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/OTA/CheckUpdate` | GET | Bearer | Check firmware version |
| `/api/OTA/Download` | GET | Bearer | Download firmware package |
| `/api/OTA/Status` | POST | Bearer | Report update result |

### 7.1 GET /api/OTA/CheckUpdate
**Query params:** `vehicleId`, `currentFirmwareVersion`, `vehicleType`
```json
{
  "status": "success",
  "data": {
    "updateAvailable": true,
    "latestVersion": "2.4.1",
    "packageUrl": "string",
    "packageSizeBytes": 524288,
    "checksum": "string",
    "mandatory": false,
    "releaseNotes": "string"
  }
}
```

### 7.2 GET /api/OTA/Download
Returns binary firmware package (Zip). Client verifies `checksum` before flashing.

### 7.3 POST /api/OTA/Status
```json
{
  "vehicleId": "string",
  "fromVersion": "string",
  "toVersion": "string",
  "status": "started | success | failed",
  "failureReason": "string|null"
}
```

---

## 8. GraphQL API (P360 Platform)

| Aspect | Detail |
|--------|--------|
| Endpoint | `/gapi` `[VERIFY WITH BACKEND TEAM]` |
| Transport | HTTPS (queries/mutations), WSS (subscriptions) |
| Client | Apollo (`CODPSchema/` generated) |
| Auth | Bearer token |
| Schema | `TVS/schema.graphqls`, EV: `iQubeQueries.graphql` |

### 8.1 Key Queries

```graphql
query getVehicleTrackingData($vehicleId: ID!) {
  vehicleTracking(vehicleId: $vehicleId) {
    lat lng speed heading timestamp ignitionState
  }
}
```

```graphql
query getChargingHistory($vehicleId: ID!, $from: DateTime, $to: DateTime) {
  chargingHistory(vehicleId: $vehicleId, from: $from, to: $to) {
    sessionId startTime endTime energyKwh socStart socEnd
  }
}

query getGeofenceList($vehicleId: ID!) {
  geofences(vehicleId: $vehicleId) { id name type radius center { lat lng } }
}

query getWeatherData($lat: Float!, $lng: Float!) {
  weather(lat: $lat, lng: $lng) { tempC condition icon }
}
```

### 8.2 Key Mutations

```graphql
mutation createGeofence($input: GeofenceInput!) {
  createGeofence(input: $input) { id status }
}

mutation updateEmergencyContacts($vehicleId: ID!, $contacts: [ContactInput!]!) {
  updateEmergencyContacts(vehicleId: $vehicleId, contacts: $contacts) { success }
}

mutation activateDevice($vehicleId: ID!, $deviceId: String!) {
  activateDevice(vehicleId: $vehicleId, deviceId: $deviceId) { status }
}
```

### 8.3 Subscriptions (WebSocket)

```graphql
subscription liveVehicleTracking($vehicleId: ID!) {
  liveTracking(vehicleId: $vehicleId) {
    lat lng speed timestamp
  }
}
```

> 📍 Field names above are representative. Confirm exact operations and
> field selections in `CODPSchema/Operations/` and `schema.graphqls`.
> `[VERIFY WITH BACKEND TEAM]`

---

## 9. MQTT Topics

| Aspect | Detail |
|--------|--------|
| Library | CocoaMQTT over TLS |
| Topic convention | `{telematicsOrganizationId}/{telematicsVehicleId}` |
| Message format | JSON / Protobuf-derived `[VERIFY WITH BACKEND TEAM]` |
| QoS | `[VERIFY WITH BACKEND TEAM]` (commonly QoS 1) |
| Connection | Broker host/port + TLS; credentials via secure config |

**Lifecycle (from app):**
```
connect → subscribe("{orgId}/{vehicleId}") → onMessage(parse) → ViewModel → UI
On terminate: unsubscribe + disconnectToServer()
```

**Example message (representative):**
```json
{
  "vehicleId": "string",
  "timestamp": 1719100000000,
  "lat": 0.0, "lng": 0.0,
  "speed": 42, "soc": 64, "ignition": true
}
```

---

## 10. EventHub Integration

| Aspect | Detail |
|--------|--------|
| Provider | Azure EventHub |
| Auth | SAS token `[VERIFY WITH BACKEND TEAM]` |
| Format | JSON message payload |
| Mode | Single event per upload (batch `[VERIFY WITH BACKEND TEAM]`) |

### 10.1 Endpoints per Vehicle Type

Endpoints are vehicle-specific topics on the Azure EventHub namespace.
`[VEHICLE-SPECIFIC]`

| Vehicle | Config Variable (in `NetworkConfiguration`) |
|---------|---------------------------------------------|
| U399C (RR310) | `eventHubEndpointU399C` |
| N251 (NTorq) | `eventHubEndpointN251` |
| U324 | `eventHubEndpointU324` |
| U408 | `eventHubEndpointU408` |
| U368 | `eventHubEndpointU368` |
| U532 | `eventHubEndpointU532` |

> ⚠️ Production/dev EventHub URLs are currently hardcoded in
> `NetworkConfiguration.swift`. Recommend moving to secure config.
> Endpoint values are intentionally omitted here.

### 10.2 Message Format (Representative)
```json
{
  "vehicleId": "string",
  "vehicleType": "U399C",
  "timestamp": 1719100000000,
  "telemetry": {
    "speed": 42, "rpm": 5200, "odometer": 12345,
    "fuelLevel": 75, "lat": 0.0, "lng": 0.0
  }
}
```

---

## 11. External API Dependencies

| Provider | Purpose | Auth Method |
|----------|---------|-------------|
| Mappls | Maps, Navigation, Geocoding (India) | API Key + Client ID/Secret (Atlas) |
| Google Maps | International maps/nav/places | API Key |
| HERE Maps | Alternative navigation | API Key |
| what3words | Location addressing | API Key |
| Firebase | Push (FCM), Crashlytics | Service config (`GoogleService-Info.plist`) |
| AppDynamics | APM | App Key (EUM) |
| KogoAuto | Partner features | SDK Token |
| LatLong.in | Dealer locator | OAuth/token `[VERIFY WITH BACKEND TEAM]` |

> All keys are resolved at runtime via `AppKeys` and are NOT included here.

---

## 12. Error Response Standard

### 12.1 Standard Error Body
```json
{
  "status": "error",
  "code": 400,
  "message": "Human readable message",
  "errors": [
    { "field": "phone", "message": "Invalid phone number" }
  ]
}
```

### 12.2 Standard HTTP Status Codes

| Code | Meaning | Typical Use |
|------|---------|-------------|
| 200 | OK | Successful GET/POST |
| 201 | Created | Resource created (register, book) |
| 400 | Bad Request | Validation failure |
| 401 | Unauthorized | Missing/expired token → refresh/logout |
| 403 | Forbidden | Insufficient permission |
| 404 | Not Found | Unknown resource |
| 409 | Conflict | Duplicate (vehicle/slot) |
| 410 | Gone | Expired OTP reference |
| 422 | Unprocessable | Semantic validation (VIN unknown) |
| 429 | Too Many Requests | Throttled (OTP) |
| 500 | Server Error | Backend failure |
| 503 | Service Unavailable | Maintenance/failover |

### 12.3 Retry Policy
- 401 → attempt token refresh once, then retry; on failure → logout
- 5xx / network → client retry with backoff (Alamofire) `[VERIFY WITH BACKEND TEAM]`
- 429 → respect `resendAfterSeconds` / `Retry-After`

---

## 13. Rate Limits

| Endpoint Category | Limit | Source |
|-------------------|-------|--------|
| OTP request | Throttled; `resendAfterSeconds` enforced | App behavior |
| Telemetry upload | Periodic interval `[VERIFY WITH BACKEND TEAM]` | EventHub |
| GraphQL live tracking | Subscription-based, continuous | P360 |
| General REST | `[VERIFY WITH BACKEND TEAM]` | Backend |

**Client-side retry logic:**
- Reachability monitored (`ReachabilitySwift`)
- Failed telemetry persisted locally and re-uploaded when online
- Exponential backoff for BLE/network `[VERIFY WITH BACKEND TEAM]`

---

## 14. Sample Requests / Responses

### 14.1 Login Flow (OTP → Validate → Token)

```bash
# Step 1: Request OTP
curl -X POST "https://<host>/api/Login" \
  -H "Content-Type: application/json" \
  -H "User-Agent: TVSConnect/8.7.0 (iOS 17.0; iPhone15)" \
  -d '{ "mobileNumber": "9999999999", "countryCode": "+91", "deviceId": "<device-id>" }'

# Step 2: Validate OTP
curl -X POST "https://<host>/api/Login/ValidateOTP" \
  -H "Content-Type: application/json" \
  -d '{ "mobileNumber": "9999999999", "otp": "1234", "otpReferenceId": "<ref>", "deviceId": "<device-id>", "fcmToken": "<fcm>" }'
# → returns accessToken, refreshToken
```

### 14.2 Fetch Dashboard Data
```bash
curl -X GET "https://<host>/api/Dashboard/Summary?vehicleId=<id>" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Accept: application/json"
```

### 14.3 Upload Telemetry (EventHub)
```bash
curl -X POST "<eventhub-endpoint-for-vehicle-type>" \
  -H "Authorization: SharedAccessSignature <sas-token>" \
  -H "Content-Type: application/json" \
  -d '{ "vehicleId": "<id>", "vehicleType": "U399C", "timestamp": 1719100000000, "telemetry": { "speed": 42 } }'
```

### 14.4 GraphQL Query Example
```bash
curl -X POST "https://<p360-host>/gapi" \
  -H "Authorization: Bearer <accessToken>" \
  -H "Content-Type: application/json" \
  -d '{ "query": "query($id:ID!){ vehicleTracking(vehicleId:$id){ lat lng speed timestamp } }", "variables": { "id": "<vehicleId>" } }'
```

### 14.5 MQTT Subscribe Example (conceptual)
```
CONNECT  host=<broker> port=<port> tls=true
SUBSCRIBE topic="<orgId>/<vehicleId>" qos=1
# On message → parse JSON/Protobuf → update UI
```

---

## 15. Known Gaps / Undocumented Areas

| Area | Gap | Action |
|------|-----|--------|
| Exact REST paths | Reconstructed from conventions, not verified | Cross-check `APIList.swift` + backend docs |
| Request/response schemas | Representative, not authoritative | Confirm with backend OpenAPI/Swagger |
| API versioning scheme | Unknown (path vs header) | `[VERIFY WITH BACKEND TEAM]` |
| GraphQL field selections | Representative | Confirm in `CODPSchema/Operations/` |
| MQTT message format & QoS | Partially known | `[VERIFY WITH BACKEND TEAM]` |
| EventHub auth & batching | SAS assumed | `[VERIFY WITH BACKEND TEAM]` |
| Rate limits | Mostly unknown | `[VERIFY WITH BACKEND TEAM]` |
| Region-specific endpoint variations | Per-country hosts | Map via `NetworkConfiguration` |
| 500+ REST endpoints | Only key ones documented | Generate full list from `APIList.swift` |
| Error code catalog | Custom codes not enumerated | `[VERIFY WITH BACKEND TEAM]` |

### Recommended Next Steps
1. Extract the authoritative endpoint list from
   `SupportingFiles/WebService/APIList.swift`.
2. Cross-reference with backend OpenAPI/Swagger specs.
3. Confirm GraphQL operations against `CODPSchema/`.
4. Validate MQTT/EventHub contracts with the telemetry team.

---

> **Security Notice:** This specification contains no API keys, tokens,
> SAS signatures, or credentials. Hosts and secrets are resolved at
> runtime via `NetworkConfiguration` / `AppKeys` and protected by SSL
> certificate pinning.

*End of API Specification Document.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |

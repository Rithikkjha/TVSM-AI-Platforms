# TVS Connect iOS — API Summary Table

> **Source:** Extracted directly from `SourceCode/TVS/SupportingFiles/WebService/APIList.swift`
> (authoritative endpoint definitions as consumed by the app).
>
> Endpoints are grouped by the `APIList` struct (module). Paths are shown
> relative to their resolved base host. Base hosts are resolved at runtime
> by `NetworkConfiguration` and vary by environment/region.

## Base Host Legend

| Token | NetworkConfiguration source | Used for |
|-------|------------------------------|----------|
| `{server}` | `serverURL` | Core app REST APIs |
| `{host}` | `hostURL` | Kogo JWT, vehicle config |
| `{vin}` | `vinHostURL` | VIN / bike lookup |
| `{tvsServer}` | `tvsServerURL` | Service history/reminder |
| `{tvsWeb}` / `{tvsWebDomestic}` | `hostURLWeb` / `hostURLWebDomestic` | Web content pages |
| `{eventHub*}` | `eventHubEndpoint*` | Azure EventHub telemetry |
| `{latLong*}` | `latLong*DealersURL` | Dealer locator |
| `{external}` | hardcoded | Third-party (Apple, TNT) |

---

## Module → API Endpoint Summary

### Authentication & User (`Main`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/RegisterUser/CreateUser` | Register user |
| POST | `{server}/UserLogin/Login` | Login |
| POST | `{server}/UserLogin/Loginv1` | Login v1 |
| POST | `{server}/v3/UserLogin/Loginv3` | Login v3 |
| POST | `{server}/v3/userlogin/replaceICEnumber` | Replace ICE user with EV |
| POST | `{server}/manageprofile/verifymobileupdateotp` | Verify mobile update OTP |
| GET | `{server}/manageprofile/GetOTPForUpdateMobileNumber` | Get mobile update OTP |
| POST | `{server}/UserLogin/Logout` | Logout |
| POST | `{server}/RegisterUser/VerifyOTP` | Verify signup OTP |
| POST | `{server}/UserLogin/VerifyLoginOtp` | Verify signin OTP |
| POST | `{server}/v3/userlogin/verifyloginotp` | Verify signin OTP (v3) |
| POST | `{server}/RegisterUser/GenerateOTP` | Generate/resend OTP |
| GET | `{server}/CityMaster/GetCityMaster` | City list |
| GET | `{server}/AppAsset/AssetByUser` | Manage assets |
| GET | `{server}/UserLogin/getAppVersion` | App version check |
| GET | `{server}/RegisterUser/GetCountryList` | Country list |
| GET | `{server}/CityMaster/GetCountryMaster` | Countries master |
| GET | `{server}/secret?platform=ios` | Third-party keys |
| GET | `{server}/v3/secret?platform=ios` | Third-party keys (v3) |
| POST | `{server}/RegisterUser/RefreshJWTToken` | Refresh token |
| POST | `{server}/UpgradeToken` | Upgrade token |
| POST | `{server}/InAppFeedback` | In-app feedback |
| GET | `{server}/userconsent?mobileNumber=` | Get user consent |
| POST | `{server}/v3/userconsent` | Set user consent |
| POST | `{server}/v3/vehicle/vehiclelistbyframeinvoice` | Add vehicle by frame/invoice |
| POST | `{server}/v3/vehicle/vehiclelistbyframeengineno` | Add vehicle by frame/engine |
| GET | `{server}/vehicle/makemodelmaster` | Make/model master |
| GET | `{server}/citystatemaster` | City/state list |
| GET | `{server}/GetAmBannerImagelink` | Banner links |
| GET | `{server}/home/getframenoandp360token` | Frame no + P360 token |

### Dashboard (`Dashboard`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/Image/ProfileImage` | Profile image |
| GET | `{server}/v3/UserDashboard/GetDashboardDetail?userId=` | Dashboard detail |
| GET | `{server}/v3/Vehicle/GetOnBoarding?mobileNumber=` | Onboarding |
| GET | `{server}/UserLogin/CrashAlertDate` | Crash alert time |
| GET | `{server}/AppBanner/GetAppbanner` | Banner image |
| POST | `{server}/LastLocationParkedController/SaveLastLocationParked` | Save parked location |
| GET | `{server}/LastLocationParkedController/GetLastLocationParked` | Get parked location |
| POST | `{server}/MileageForVehicleController/InsertMileageForVehicle` | Insert mileage |
| GET | `{server}/MileageForVehicleController/GetAllMileage` | Get all mileage |
| POST | `{server}/MileageForVehicleController/ClearAllMileage` | Clear mileage |
| GET | `{server}/Vehicle/GetUserBadgesList` | Badges list |
| GET | `{server}/mobilesetting?Platform=iOS&Brand=` | Mobile settings |
| GET | `{server}/v2/mobilesetting?Platform=iOS&Brand=` | U279 app experience settings |
| GET | `{server}/mobilesettinginfo?Platform=` | Settings info list |
| GET | `{server}/v2/Faq/GetFaq` | FAQ |
| GET | `{server}/CSIFeedbackAvailable?FrameNo=` | CSI feedback availability |
| POST | `{server}/CSIFeedbackReschedule` | Reschedule CSI feedback |
| POST | `{server}/CSIFeedback` | Post CSI feedback |
| GET | `{server}/NPSFeedbackAvailable?FrameNo=` | NPS feedback availability |
| POST | `{server}/NPSFeedback` | Post NPS feedback |
| POST | `{server}/NPSFeedbackReschedule` | Reschedule NPS feedback |
| GET | `{server}/Vehicle/ActivateMMIMacId?macid=` | Activate MAC ID |
| GET | `{server}/vehicle/nonconnecteddashboard` | Non-connected dashboard |
| GET | `{server}/vehicle/vehicledetails` | NC vehicle details |
| PUT | `{server}/vehicle/vehiclenickname` | Update NC vehicle name |

### Profile (`Profile`, `ManageProfile`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/v3/ManageProfile/EditProfile` | Edit profile |
| GET | `{server}/Travel/GetVehicleCumulativeData` | Vehicle cumulative data |
| GET | `{server}/vehicle/overview` | U408 cumulative data |
| POST | `{server}/ManageProfile/verifydeleteprofileotp` | Verify delete profile OTP |
| GET | `{server}/ManageProfile/getdeleteprofileotp` | Get delete profile OTP |
| POST | `{server}/ManageProfile/deleteprofilereason` | Delete profile reason |
| GET | `{server}/userconsent/marketing?email=` | Get marketing consent |
| POST | `{server}/userconsent/marketing` | Save marketing consent |
| POST | `{server}/Image/ProfileImage` | Update profile image |
| POST | `{server}/DeleteProfile` | Delete profile |

### Vehicle Management (`AddBike`, `DeleteAndRenameBike`, `VINSample`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{vin}/getCustomerBikeCountAPI?MobileNo=` | VIN bike count |
| GET | `{vin}/Multipleframenocheck.jsp?frameno=` | VIN auth check |
| GET | `{vin}/getCustomerBikeDetailsAPI?FrameNumber=` | VIN detail |
| POST | `{server}/Vehicle/AddVehicle` | Add vehicle |
| POST | `{server}/v3/Vehicle/AddVehicle` | Add vehicle (v3) |
| POST | `{server}/v3/EmergencyContact/AddEmergencyContact` | Add emergency contact |
| POST | `{server}/Vehicle/VerifyOTPforBikeOwner` | Verify bike owner OTP |
| POST | `{server}/Vehicle/SendOTPtoBikeOwner` | Send bike owner OTP |
| POST | `{server}/UserSupport/AddSupport` | Help support |
| POST | `{server}/Vehicle/AddVehicleAddVehicleWithoutVINDetails` | Add vehicle w/o VIN |
| GET | `{server}/vehicle/countryvehicle` | Country-specific vehicle list |
| POST | `{server}/v3/userlogin/getnewevuserdetails` | Create new EV user |
| GET | `{server}/v3/Vehicle/markactivevehicle?userVehicleId=` | Mark active vehicle |
| GET | `{server}/VinSampleImage/GetVimSampleImage` | VIN sample image |
| DELETE | `{server}/Vehicle/RemoveVehicle` | Delete vehicle |
| PUT | `{server}/Vehicle/UpdatevehicleNickname` | Rename vehicle |

### IOT / Ride & Travel (`IOT`) [VEHICLE-SPECIFIC]

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/ApacheNonIOT/inserttraveldataForNonIOTApache` | Insert NonIOT travel |
| POST | `{server}/Travel/inserttraveldataForApache` | Insert N112 travel |
| POST | `{server}/N251/inserttraveldataForN251BLE` | Insert N251 travel |
| GET | `{server}/Travel/GetTravelList` | Travel list |
| GET | `{server}/v2/Travel/GetTravelList` | Travel list v2 |
| GET | `{server}/v3/Travel/GetTravelList` | Travel list v3 |
| POST | `{server}/Travel/UpdateTravelName` | Update travel name |
| DELETE | `{server}/Travel/DeleteTravel` | Delete travel |
| DELETE | `{server}/ride` | Delete travel (U408) |
| DELETE | `{server}/v2/ride` | Delete ride (U279) |
| POST | `{server}/N109/inserttraveldataForN109` | Insert N109 travel |
| POST | `{server}/U347/inserttraveldataForU347` | Insert U347 travel |
| GET | `{server}/ride?` | Travel list (U408) |
| GET | `{server}/v2/ride?` | Travel list (U532/N360) |
| POST | `{server}/ride` | Insert travel (U408/N360) |
| POST | `{server}/ride/favourite` | Set favorite ride |
| POST | `{server}/v2/ride/favourite` | Favorite ride (U279) |
| POST | `{server}/N251/setFavouriteRides` | Set favorite rides (NTorq) |
| POST | `{server}/N251/deleteMultipleRides` | Delete multiple rides |
| GET | `{server}/Travel/GetAllTravelList` | All travel list |
| GET | `{server}/Travel/GetSpeedAnalysis` | Speed analysis |
| GET | `{server}/TodoList/GetTodoList` | Get to-do list (HUD) |
| POST | `{server}/TodoList/AddOrUpdateToDoList` | Add/update to-do (HUD) |
| POST | `{server}/TodoList/ManageToDoList` | Manage to-do (HUD) |

### Vehicle-Specific Ride APIs (`U399C_API`, `U400_API`, `N597_API`, `U368_API`) [VEHICLE-SPECIFIC]

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/ride` | Save ride |
| GET | `{server}/v2/ride` | Fetch ride |
| POST/GET | `{server}/widget` | Widget operation |
| GET | `{server}/tpms/history?` | TPMS history (U399C/U400/N597) |

### Navigation (`Navigation`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/location/recent` | Create recent location |
| GET | `{server}/location/recent?vin=` | Get recent locations |
| POST | `{server}/location/favourite` | Add favourite location |
| GET | `{server}/location/favourite?vin=` | Get favourite locations |

### Geofence (`GeoFence`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/geofence/getgeofencelist?` | Geofence list |
| POST | `{server}/geofence/updategeofence` | Update geofence |
| POST | `{server}/geofence/addgeofence` | Add geofence |
| DELETE | `{server}/geofence/deletegeofence` | Remove geofence |
| GET | `{server}/geofence/getallgeofencealerts?` | Geofence alert history |
| GET | `{server}/geofence/getgeofencedetails?` | Geofence details |

### P360 Platform / EV & Connected (`P360Apis`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/home/getlatestdevicedata?` | Latest device data |
| POST | `{server}/notification/pushnotificationfcmtokenregistration` | Register push |
| POST | `{server}/notification/pushnotificationfcmtokenderegistration` | Deregister push |
| GET | `{server}/vehicle/getcumulativeridedata?` | Cumulative ride data |
| GET | `{server}/charging/charginghistory?` | Charging history |
| GET | `{server}/charging/vehiclestatschargingsummary?` | Charging summary |
| GET | `{server}/charging/charginggraph?` | Trip points / charging graph |
| GET | `{server}/home/getallshareddestinations?` | Shared destinations |
| GET | `{server}/home/getallrecentlocations?` | Recent locations |
| GET | `{server}/home/getallfavoritelocations?` | Favorite locations |
| GET | `{server}/home/getallsharedlivelocation?` | Shared live location |
| GET | `{server}/home/getcurrentweatherdata?` | Current weather |
| GET | `{server}/ride/rideStats?` | Ride stats |
| GET | `{server}/vehicle/getoverspeedalert?` | Overspeed threshold |
| POST | `{server}/vehicle/setoverspeedalert` | Set overspeed threshold |
| GET | `{server}/socanalysis/trackingpoints?` | SOC tracking points |
| POST | `{server}/location/addfavoritelocation` | Add favourite location |
| POST | `{server}/location/addrecentlocation` | Add recent location |
| POST | `{server}/location/sharedestination` | Share destination |
| POST | `{server}/location/deletefavoritelocation` | Delete favourite location |
| POST | `{server}/location/editfavoritelocation` | Edit favourite location |
| POST | `{server}/location/sharelivelocation` | Share live location |
| POST | `{server}/location/stoplivelocation` | Stop live location |
| PUT | `{server}/vehicle/updatenickname` | Update nickname |
| GET | `{server}/emergencycontact/getemergencycontacts?` | Get emergency contacts |
| POST | `{server}/emergencycontact/editemergencycontact` | Edit emergency contact |
| POST | `{server}/emergencycontact/deleteemergencycontacts` | Delete emergency contact |
| POST | `{server}/emergencycontact/saveemergencycontacts` | Save emergency contact |
| GET | `{server}/vehicle/getcumulativeridechargingsummary?` | Ride+charging summary |

### EV Home / Portable Charging (`P360Apis` cont.)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/homecharging/gethomechargerlatestdata?` | Home charger latest data |
| GET | `{server}/homecharging/gethomechargercommandstatus?` | Home charger command status |
| GET | `{server}/homecharging/gethomechargerchargingcummulativedata?` | Home charger cumulative |
| GET | `{server}/homecharging/getportablechargerchargingcummulativedata?` | Portable charger cumulative |
| GET | `{server}/homecharging/homechargercharginghistory?` | Home charging history |
| GET | `{server}/homecharging/getportablechargercharginghistory?` | Portable charging history |
| GET | `{server}/homecharging/getbatterieslatestdata?` | Batteries latest data |
| POST | `{server}/homecharging/sethomechargersettings` | Set home charger settings |
| GET | `{server}/homecharging/getChargingPoints?` | Home charging points |
| GET | `{server}/portablecharger/getportablechargerlatestdata?` | Portable charger latest data |
| GET | `{server}/portablecharger/getportablechargercommandstatus?` | Portable charger command status |

### Timefence (`P360Apis` cont.)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/timefence/gettimefencealertconfig?` | Timefence config |
| POST | `{server}/timefence/settimefence` | Set timefence |
| POST | `{server}/timefence/updatetimefence` | Update timefence |
| DELETE | `{server}/timefence/deletetimefence` | Delete timefence |

### Notifications (`Notification`, `NotificationIB`, `PushNotification`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/Notification/NotificationList` | Notification list |
| POST | `{server}/Notification/Read` | Mark read |
| POST | `{server}/notification/readmqttnotification` | Mark MQTT notification read |
| POST | `{server}/Notification/Unread` | Mark unread |
| GET | `{server}/Notification/GetNotificationByUser?userId=` | Notifications (IB) |
| POST | `{server}/Notification/ClearNotification` | Clear notifications (IB) |
| POST | `{server}/Notification/MakeSeen` | Mark seen (IB) |
| POST | `{server}/notification/pushnotificationfcmtokenregistration` | Register FCM token |
| POST | `{server}/notification/pushnotificationfcmtokenderegistration` | Deregister FCM token |


### Help & Feedback (`Help`, `Common`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/FAQ/getfaq` | FAQ |
| POST | `{server}/Feedback/AddFeedback` | Add feedback |
| POST | `{server}/V2/Feedback/AddFeedback` | Add feedback (v2) |
| GET | `{server}/UserGuide/GetUserGuide?userid=` | User guide |
| GET | `{server}/Feedback/Feedbacktype` | Feedback type |
| GET | `{server}/Support/getCrashAlertFeatures` | Crash alert features |
| POST | `{server}/AddDeviceDetails` | Device details |

### OTA (`OTA`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `{server}/ota` | OTA check/status |
| POST | `{external}` TNT (`ft8.trakntell.com/.../tntDevAPI`) | OTA TNT (TrakNTell) |

### Voice Assist (`VoiceAssist`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `{server}/UserVoiceCommand` | User voice command |

### Weather & News (`Weather`, `News`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/weather` | Weather |
| GET | `{server}/airqualityindex` | Air quality |
| GET | `{server}/news` | All news |
| GET | `{server}/cricket` | Cricket news |
| GET | `{server}/football` | Football news |

### Settings & Consent (`UserSetting`, `UserAddress`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/UserSetting/GetSettingList?` | Settings list |
| POST | `{server}/UserSetting/SaveSettingForUser` | Save settings |
| GET | `{server}/useraddress?` | User address list |
| POST | `{server}/useraddress` | User address |

### Crash Detection (`CrashDetect`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{server}/UserSetting/GetSMSonCrashDetection?` | Crash SMS (India) |
| GET | `{server}/crashalert?` | Crash detect email (IB) |

### BluArmor / Accessories (`BluArmor`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `{server}/accessory` | Accessories |
| DELETE | `{server}/accessory?` | Delete accessory |

### Partner & Misc (`Kogo`, `ShareExtension`, `VehicleConfigurationList`, `BrandFeed`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `{host}/api/UserLogin/getkogojwt` | Kogo JWT token |
| POST | `{server}/maps/getmapdata` | Lat/long from URL (share ext) |
| GET | `{host}/api/getvehiclefeatureconfig` | Vehicle feature config |
| GET | `{server}/Notification/Getadminnotificationbyuser?` | Brand feed |

### Apple Sign-In (`AppleSign`) — External

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `https://appleid.apple.com/auth/token` | Apple token generate/refresh |
| POST | `https://appleid.apple.com/auth/revoke` | Apple token revoke |

### Dealer Locator (LatLong) & EventHub (Telemetry)

| Type | Resource | Purpose |
|------|----------|---------|
| GET | `{latLong}` (`latLongAllDealersURL`) | All dealers |
| GET | `{latLong}` (`latLongNtorqDealersURL`) | NTorq dealers |
| GET | `{latLong}` (`latLongU399CDealersURL`) | U399C dealers |
| POST | `{eventHubU399C}` | U399C telemetry upload |
| POST | `{eventHubN251}` | N251 telemetry upload |
| POST | `{eventHubU324}` | U324 telemetry upload |
| POST | `{eventHubU408}` | U408 telemetry upload |
| POST | `{eventHubU368}` | U368 telemetry upload |
| POST | `{eventHubU532}` | U532 telemetry upload |

### Web Content Pages (`TVSWeb`, `IBTVSWeb`) — WebView URLs

| Resource | Purpose |
|----------|---------|
| `{tvsWeb*}/support` | Crash alert / support |
| `{tvsWeb*}/aboutus` | About us |
| `{tvsWeb*}/contactus` | Contact us |
| `{tvsWeb*}/termsconditions` | Terms & conditions |
| `{tvsWeb*}/privacypolicy` | Privacy policy |
| `https://what3words.com/about` | what3words about |

---

## Module Coverage Summary

| Module (APIList struct) | Endpoint Count (approx.) | Primary Base Host |
|-------------------------|--------------------------|-------------------|
| Main (Auth/User) | 28 | `{server}` |
| Dashboard | 24 | `{server}` |
| Profile + ManageProfile | 13 | `{server}` |
| AddBike + Delete/Rename + VINSample | 16 | `{server}` / `{vin}` |
| IOT (Ride/Travel) | 23 | `{server}` |
| Vehicle-specific Ride APIs | ~14 | `{server}` |
| Navigation | 4 | `{server}` |
| GeoFence | 6 | `{server}` |
| P360Apis (connected/EV/charging) | 45+ | `{server}` |
| Notifications (3 structs) | 9 | `{server}` |
| Help + Common | 7 | `{server}` |
| OTA | 2 | `{server}` / external |
| Weather + News | 5 | `{server}` |
| Settings + Address | 4 | `{server}` |
| Others (Kogo, BluArmor, etc.) | ~12 | `{server}` / `{host}` |
| EventHub (telemetry) | 6 | Azure EventHub |
| LatLong (dealers) | 3 | LatLong |
| Apple Sign-In | 2 | External |
| Web content pages | ~12 | `{tvsWeb}` |

> **Note:** Counts are approximate and reflect distinct entries in
> `APIList.swift`. Some endpoints are reused across vehicle variants
> (e.g., `/ride`, `/widget`, `/v2/ride`) — actual behavior differs by
> selected vehicle (`[VEHICLE-SPECIFIC]`).

---

## Notes & Observations

1. **Versioning:** Multiple API versions coexist (`/v2/`, `/v3/`).
   Newer flows (login, vehicle add, dashboard) use `v3`.
2. **Shared ride endpoints:** `/ride`, `/v2/ride`, `/widget` are reused by
   several vehicle modules (U399C, U400, N597, U368, U408, N360).
4. **GraphQL not in this file:** P360 GraphQL operations live in
   `CODPSchema/` and `schema.graphqls`, not `APIList.swift`. The
   `P360Apis` struct here is the REST surface of P360.
5. **Region-aware:** Web content URLs branch on `country == .INDIA`
   (domestic vs international hosts).
6. **Security:** No keys/tokens are stored in `APIList.swift`; hosts are
   injected via `NetworkConfiguration`.

---

*Generated from `APIList.swift`. For exact query parameters and request
bodies, refer to the corresponding service/ViewModel call sites.*

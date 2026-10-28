"""java.spring over trimmed reproductions of TVS-CS files (source cited per fixture).
All URLs, hosts and secret values are fake; tests assert secrets never reach the output."""
from __future__ import annotations

import json

from phase2_helpers import make_ledgered_repo
from repo_docs import paths, phase2_extract as p2
from repo_docs.extractors import syntax as sx
from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.java_spring import JavaSpring
from repo_docs.state import StateStore

FAKE_SAS = "fakeSharedAccessKeyJava0123456789="
FAKE_PW = "fakeJavaDbPassw0rd"


def _run(files, stacks=(("java", "."),)):
    ctx = RepoContext.for_test(files, list(stacks))
    res = p2.run(ctx)
    assert p2.validate(ctx, res["items"]) == []
    return ctx, res


def _items(res, kind=None):
    return {i.id: i for i in res["items"] if kind is None or i.kind == kind}


def _touch(res, path):
    return next(t for x, _v, t, _n in res["touches"][path] if x == "java.spring")


def _line(text, needle):
    return next(i for i, ln in enumerate(text.split("\n"), 1) if needle in ln)


# ---- TVS-CPS-BACKEND appointment-service -------------------------------------------------
# appointment-service/src/main/java/com/tvsm/appointment/constants/AppointmentServiceEndpoints.java
ENDPOINTS = """package com.tvsm.appointment.constants;
public class AppointmentServiceEndpoints {
    private AppointmentServiceEndpoints() {}
    public static final String BASE_PATH = "/api/v1/appointments";
    public static final String CREATE_APPOINTMENT = "/create";
    public static final String GET_APPOINTMENT_DETAIL = "/{appointmentId}";
    public static final String APPOINTMENT_MASTER_DATA = "/master";
    public static final String APPOINTMENT_AUTOCLOSE =  "/appointments/auto-close";
    public static final String APPOINTMENT_JOB_API_PREFIX = "/system";
    public static final String APPOINTMENT_JOB_BASE_PATH = APPOINTMENT_JOB_API_PREFIX + "/api/v2";
}
"""
# appointment-service/.../controller/AppointmentController.java (trimmed)
APPT_CONTROLLER = """package com.tvsm.appointment.controller;
import com.tvsm.appointment.constants.AppointmentConstants;
import com.tvsm.appointment.constants.AppointmentServiceEndpoints;
import com.tvsm.appointment.dto.*;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping(AppointmentServiceEndpoints.BASE_PATH)
public class AppointmentController {
    @PostMapping(AppointmentServiceEndpoints.CREATE_APPOINTMENT)
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Appointment created successfully"),
            @ApiResponse(responseCode = "400", description = "Invalid input data"),
    })
    public ResponseEntity<APIResponse<AppointmentResponseDTO>> createAppointment(
            @RequestBody @Valid AppointmentCreateRequestDTO requestDTO
    ) {
        return null;
    }
    @GetMapping(AppointmentServiceEndpoints.GET_APPOINTMENT_DETAIL)
    public ResponseEntity<AppointmentResponseDTO> getAppointmentDetail(
            @PathVariable("appointmentId") String appointmentId) {
        return null;
    }
    @GetMapping(AppointmentServiceEndpoints.APPOINTMENT_MASTER_DATA)
    public ResponseEntity<String> getMaster(
            @RequestParam(name = "locale", defaultValue = AppointmentConstants.DEFAULT_LOCALE) String locale,
            @RequestHeader("X-Tenant") String tenant) {
        return null;
    }
}
"""
APPT_CONSTANTS = """package com.tvsm.appointment.constants;
public final class AppointmentConstants {
    public static final String DEFAULT_LOCALE = "en";
}
"""
# appointment-service/.../controller/AppointmentJobController.java (trimmed)
APPT_JOB = """package com.tvsm.appointment.controller;
import com.tvsm.appointment.constants.AppointmentServiceEndpoints;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping(AppointmentServiceEndpoints.APPOINTMENT_JOB_BASE_PATH)
public class AppointmentJobController {
    @PostMapping(AppointmentServiceEndpoints.APPOINTMENT_AUTOCLOSE)
    public void autoClose() {}
}
"""
# a DTO in the style of appointment-service dto/*RequestDTO.java (Lombok + jakarta validation)
APPT_DTO = """package com.tvsm.appointment.dto;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.*;
import lombok.Data;
import java.time.LocalDate;
import java.util.List;
@Data
public class AppointmentCreateRequestDTO {
    @NotBlank
    @Size(min = 1, max = 10 * 2)
    @JsonProperty("vin_number")
    private String vin;
    @NotNull
    private LocalDate appointmentDate;
    private AppointmentStatus status;
    private List<AppointmentNoteDTO> notes;
    @JsonIgnore
    private String internal;
    private static final long serialVersionUID = 1L;
}
"""
APPT_ENUM = """package com.tvsm.appointment.dto;
public enum AppointmentStatus { OPEN, CLOSED }
"""
APPT_NOTE = """package com.tvsm.appointment.dto;
public record AppointmentNoteDTO(@NotBlank String text, Integer order) {}
"""
APPT_RESP = """package com.tvsm.appointment.dto;
import lombok.Getter;
@Getter
public class AppointmentResponseDTO { private String appointmentId; }
"""
APPT_BASE = "appointment-service/src/main/java/com/tvsm/appointment/"
APPT = {
    "pom.xml": "<project><artifactId>tvs-cps</artifactId><packaging>pom</packaging></project>\n",
    "appointment-service/pom.xml": "<project><artifactId>appointment-service</artifactId>"
                                   "</project>\n",
    APPT_BASE + "constants/AppointmentServiceEndpoints.java": ENDPOINTS,
    APPT_BASE + "constants/AppointmentConstants.java": APPT_CONSTANTS,
    APPT_BASE + "controller/AppointmentController.java": APPT_CONTROLLER,
    APPT_BASE + "controller/AppointmentJobController.java": APPT_JOB,
    APPT_BASE + "dto/AppointmentCreateRequestDTO.java": APPT_DTO,
    APPT_BASE + "dto/AppointmentStatus.java": APPT_ENUM,
    APPT_BASE + "dto/AppointmentNoteDTO.java": APPT_NOTE,
    APPT_BASE + "dto/AppointmentResponseDTO.java": APPT_RESP,
}


def test_constant_routes_params_responses_and_schemas():
    ctx, res = _run(APPT, [("java", "."), ("java", "appointment-service")])
    ib = _items(res, "inbound_http")
    create = ib["inbound_http:appointment-service:POST:/api/v1/appointments/create"]
    a = create.attributes
    assert a["path"] == "/api/v1/appointments/create" and a["framework"] == "spring-mvc"
    assert a["handler"] == "AppointmentController.createAppointment"
    assert a["request"] == "AppointmentCreateRequestDTO"
    assert a["params"] == [{"name": "requestDTO", "in": "body",
                            "type": "AppointmentCreateRequestDTO", "required": True}]
    assert [(r["status"], r["schema"], r["from"]) for r in a["responses"]] == [
        (200, "APIResponse<AppointmentResponseDTO>", "annotation"), (400, None, "annotation")]
    assert a["responses"][1]["when"] == "Invalid input data"
    lines = {e.line for e in create.evidence}
    assert lines == {_line(APPT_CONTROLLER, "@PostMapping"), _line(APPT_CONTROLLER,
                                                                   "@RequestMapping")}
    detail = ib["inbound_http:appointment-service:GET:/api/v1/appointments/{}"].attributes
    assert detail["path"] == "/api/v1/appointments/{appointmentId}"
    assert detail["params"] == [{"name": "appointmentId", "in": "path", "type": "string",
                                 "required": True}]
    assert detail["responses"] == [{"status": 200, "schema": "AppointmentResponseDTO",
                                    "when": None, "from": "return-type"}]
    master = ib["inbound_http:appointment-service:GET:/api/v1/appointments/master"].attributes
    assert master["params"] == [
        {"name": "locale", "in": "query", "type": "string", "required": False},
        {"name": "X-Tenant", "in": "header", "type": "string", "required": True}]
    # APPOINTMENT_JOB_BASE_PATH = APPOINTMENT_JOB_API_PREFIX + "/api/v2"
    job = ib["inbound_http:appointment-service:POST:/system/api/v2/appointments/auto-close"]
    assert job.attributes["responses"] == [{"status": 200, "schema": None, "when": None,
                                            "from": "default"}]
    sch = _items(res, "schema")
    dto = sch["schema:appointment-service:AppointmentCreateRequestDTO"].attributes
    fields = {f["name"]: f for f in dto["fields"]}
    assert set(fields) == {"vin", "appointmentDate", "status", "notes"}
    assert fields["vin"] == {"name": "vin", "json_name": "vin_number", "type": "string",
                             "required": True, "nullable": None,
                             "validation": "minLength=1;maxLength=10 * 2", "default": None}
    assert fields["appointmentDate"]["type"] == "date" and fields["appointmentDate"]["required"]
    assert fields["status"]["type"] == "enum[OPEN,CLOSED]"
    assert fields["notes"]["type"] == "AppointmentNoteDTO[]"
    assert dto["defined_in"] == APPT_BASE + "dto/AppointmentCreateRequestDTO.java:8"
    note = sch["schema:appointment-service:AppointmentNoteDTO"].attributes
    assert note["schema_kind"] == "record" and note["fields"][0]["required"] is True
    assert sch["schema:appointment-service:AppointmentStatus"].attributes["enum_values"] == [
        "OPEN", "CLOSED"]
    out = sch["schema:appointment-service:APIResponse<AppointmentResponseDTO>"].attributes
    assert out["resolved"] is False
    assert sch["schema:appointment-service:AppointmentResponseDTO"].attributes["fields"][0][
        "name"] == "appointmentId"
    assert _touch(res, APPT_BASE + "controller/AppointmentController.java").parse == "full"


# ---- tvsm-auth -----------------------------------------------------------------------------
# tvsm-auth src/main/java/com/tvsmotor/tvsmauth/support/AppConstants.java (nested static class)
AUTH_CONST = """package com.tvsmotor.tvsmauth.support;
import java.util.Set;
public final class AppConstants {
    public static class BaseUrlMappings {
        public static final String LOCATION_URI = "/api/v1/location";
        public static final Set<String> OPEN_URLS = Set.of("/api/v1/public/**");
    }
}
"""
# tvsm-auth .../user/location/api/LocationController.java (static import + concatenation)
AUTH_LOC = """package com.tvsmotor.tvsmauth.user.location.api;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import static com.tvsmotor.tvsmauth.support.AppConstants.BaseUrlMappings.LOCATION_URI;
@RestController
@RequestMapping(value = LOCATION_URI + "/state")
public class LocationController {
    @GetMapping("/list")
    public ResponseEntity<String> getStateList(@RequestParam String countryCode) {
        return null;
    }
    @PreAuthorize("hasAnyRole('HO', 'Support')")
    @DeleteMapping("/{id}")
    public void remove(@PathVariable Long id) {}
}
"""
# tvsm-auth .../config/SecurityConfig.java (trimmed; OPEN_URLS.toArray is not a literal)
AUTH_SEC = """package com.tvsmotor.tvsmauth.config;
import org.springframework.security.web.SecurityFilterChain;
import static com.tvsmotor.tvsmauth.support.AppConstants.BaseUrlMappings.OPEN_URLS;
public class SecurityConfig {
  private final JwtTokenFilter jwtTokenFilter;
  public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth ->
                    auth.requestMatchers(OPEN_URLS.toArray(new String[0]))
                            .permitAll()
                            .requestMatchers("/api/v1/location/**")
                            .authenticated())
        .addFilterBefore(jwtTokenFilter, UsernamePasswordAuthenticationFilter.class);
    return http.build();
  }
}
"""
AUTH = {"src/main/java/com/tvsmotor/tvsmauth/support/AppConstants.java": AUTH_CONST,
        "src/main/java/com/tvsmotor/tvsmauth/user/location/api/LocationController.java": AUTH_LOC,
        "src/main/java/com/tvsmotor/tvsmauth/config/SecurityConfig.java": AUTH_SEC}


def test_nested_constant_static_import_and_security():
    _ctx, res = _run(AUTH)
    ib = _items(res, "inbound_http")
    lst = ib["inbound_http:.:GET:/api/v1/location/state/list"]
    assert lst.attributes["params"] == [{"name": "countryCode", "in": "query", "type": "string",
                                         "required": True}]
    # SecurityFilterChain requestMatchers + JWT filter -> bearer-jwt, path-matched -> medium
    assert lst.attributes["auth"] == "bearer-jwt" and lst.confidence == "medium"
    rm = ib["inbound_http:.:DELETE:/api/v1/location/state/{}"].attributes
    assert rm["auth"] == "roles:HO,Support" and "hasAnyRole" in rm["auth_raw"]
    assert rm["params"][0] == {"name": "id", "in": "path", "type": "integer", "required": True}
    assert _touch(res, "src/main/java/com/tvsmotor/tvsmauth/config/SecurityConfig.java").parse \
        == "partial"


# ---- TVS-CPS-JOB-CARD-SERVICE ----------------------------------------------------------------
# src/main/java/com/tvsm/jobcard/controller/JobcardController.java (trimmed)
JOBCARD = """package com.tvsm.jobcard.controller;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("${api.jobcards.base-path:/api/v1/jobcards}")
public class JobcardController {
    @PostMapping("/list")
    public String list(@RequestParam(defaultValue = "false") boolean isServiceHistory) { return ""; }
}
"""


def test_placeholder_route_with_and_without_property():
    files = {"src/main/java/com/tvsm/jobcard/controller/JobcardController.java": JOBCARD}
    _c, res = _run(files)
    it = _items(res, "inbound_http")["inbound_http:.:POST:/api/v1/jobcards/list"]
    assert it.attributes["params"][0] == {"name": "isServiceHistory", "in": "query",
                                          "type": "boolean", "required": False}
    files["src/main/resources/application.yml"] = "api:\n  jobcards:\n    base-path: /api/v2/jc\n"
    _c, res = _run(files)
    assert "inbound_http:.:POST:/api/v2/jc/list" in _items(res, "inbound_http")


# ---- master-data-platform ------------------------------------------------------------------
# src/main/resources/application.properties (trimmed) + .env (fake values)
MDP_PROPS = (
    "spring.application.name=mdp\n"
    "server.servlet.context-path=/${spring.application.name}\n"
    "spring.datasource.url=jdbc:postgresql://${DATABASE_HOST_URL}/${DATABASE_NAME}\n"
    "spring.datasource.password=${DATABASE_PASSWORD}\n"
    "spring.jms.servicebus.topic.dealerData.subscription=mdp\n"
    "spring.jms.servicebus.topic.dealerData.name=${SERVICE_BUS_DEALER_DATA_TOPIC_NAME}\n"
    "spring.jms.servicebus.topic.dealerData.connection-string="
    "${SERVICE_BUS_DEALER_DATA_CONNECTION_STRING}\n"
    "jobs.cleanup.cron=0 0 2 * * *\n")
MDP_ENV = ("DATABASE_HOST_URL=db.example.test:5432\nDATABASE_NAME=mdpdb\n"
           f"DATABASE_PASSWORD={FAKE_PW}\n"
           "SERVICE_BUS_DEALER_DATA_CONNECTION_STRING=Endpoint=sb://mdp-ns.servicebus.windows.net/;"
           f"SharedAccessKeyName=root;SharedAccessKey={FAKE_SAS}\n"
           "SERVICE_BUS_DEALER_DATA_TOPIC_NAME=local.mdp.dealer_data\n")
# src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java (trimmed)
MDP_SB = """package com.tvsmotor.mdp.config;
import com.azure.messaging.servicebus.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
@Configuration
public class DealerMasterServiceBusConfig {
    @Bean(name = "DealerServiceBusSenderClient")
    public ServiceBusSenderClient createServiceBusSenderClient(
            @Value("${spring.jms.servicebus.topic.dealerData.connection-string}") final String azureServiceBusConnectionString,
            @Value("${spring.jms.servicebus.topic.dealerData.name}") final String dealerDataTopicName) {
        return new ServiceBusClientBuilder()
                .connectionString(azureServiceBusConnectionString)
                .sender()
                .topicName(dealerDataTopicName)
                .buildClient();
    }
    @Bean(name = "Dealer_ServiceBusProcessorClient")
    public ServiceBusProcessorClient createServiceBusProcessorClient(
            @Value("${spring.jms.servicebus.topic.dealerData.connection-string}") final String azureServiceBusConnectionString,
            @Value("${spring.jms.servicebus.topic.dealerData.name}") final String dealerDataTopicName,
            @Value("${spring.jms.servicebus.topic.dealerData.subscription}") final String dealerDataTopicSubscriptionName) {
        final Consumer<ServiceBusReceivedMessageContext> onMessage = context -> {
            context.complete();
        };
        return new ServiceBusClientBuilder()
                .connectionString(azureServiceBusConnectionString)
                .sessionProcessor()
                .topicName(dealerDataTopicName)
                .subscriptionName(dealerDataTopicSubscriptionName)
                .disableAutoComplete()
                .maxConcurrentSessions(1)
                .processMessage(onMessage)
                .processError(onError)
                .buildProcessorClient();
    }
}
"""
# src/main/java/com/tvsmotor/mdp/service/service_bus/DealerDataSenderService.java (trimmed)
MDP_SENDER = """package com.tvsmotor.mdp.service.service_bus;
import com.azure.messaging.servicebus.ServiceBusMessage;
import com.azure.messaging.servicebus.ServiceBusSenderClient;
import org.springframework.beans.factory.annotation.Qualifier;
@Service
public class DealerDataSenderService {
    private final ServiceBusSenderClient serviceBusSenderClient;
    public DealerDataSenderService(@Qualifier("DealerServiceBusSenderClient") ServiceBusSenderClient senderClient) {
        this.serviceBusSenderClient = senderClient;
    }
    public void pushDealerData(final long id) {
        final ServiceBusMessage message = new ServiceBusMessage("{}");
        message.setSessionId("s-" + id);
        final Map<String, Object> messageProperties = message.getApplicationProperties();
        messageProperties.put("eventType", "DEALER_UPDATED");
        messageProperties.put("dealerId", id);
        serviceBusSenderClient.sendMessage(message); // this is SYNCHRONOUS
    }
}
"""
MDP_CTRL = """package com.tvsmotor.mdp.controller;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/v1/dealer")
public class DealerController {
    @GetMapping("/{dealerId}")
    public DealerDto getDealerData(@PathVariable Long dealerId) { return null; }
}
"""
MDP_DATA = """package com.tvsmotor.mdp.dealer;
import jakarta.persistence.*;
import org.springframework.data.jpa.repository.*;
import org.springframework.scheduling.annotation.Scheduled;
@Entity
@Table(name = "dealer", schema = "mdp")
public class Dealer { @Id private Long id; }
interface DealerRepository extends JpaRepository<Dealer, Long> {
    @Query(value = "SELECT * FROM mdp.dealer_flag f JOIN mdp.dealer d ON d.id = f.dealer_id", nativeQuery = true)
    List<Object> flags();
}
@Service
class DealerJob {
    private final DealerRepository dealerRepository;
    @Scheduled(cron = "${jobs.cleanup.cron}", zone = "Asia/Kolkata")
    public void cleanup() {
        dealerRepository.findById(1L);
        dealerRepository.save(null);
    }
}
"""
MDP_JB = "src/main/java/com/tvsmotor/mdp/"
MDP = {"pom.xml": "<project><artifactId>mdp</artifactId></project>\n",
       "src/main/resources/application.properties": MDP_PROPS,
       "src/main/resources/application-uat.properties": "server.port=9090\n",
       ".env": MDP_ENV,
       MDP_JB + "config/DealerMasterServiceBusConfig.java": MDP_SB,
       MDP_JB + "service/service_bus/DealerDataSenderService.java": MDP_SENDER,
       MDP_JB + "controller/DealerController.java": MDP_CTRL,
       MDP_JB + "dealer/Dealer.java": MDP_DATA}


def test_master_data_platform_context_path_service_bus_data_and_jobs():
    _ctx, res = _run(MDP)
    ib = _items(res, "inbound_http")["inbound_http:.:GET:/mdp/v1/dealer/{}"].attributes
    assert ib["path"] == "/mdp/v1/dealer/{dealerId}"
    assert ib["context_path_by_env"] == {"default": "/mdp"}
    msgs = _items(res, "messaging")
    key = "config:spring.jms.servicebus.topic.dealerData.name"
    pub = msgs[f"messaging:.:publish:azure-service-bus:{key}"].attributes
    assert pub["entity"] == "local.mdp.dealer_data" and pub["entity_type"] == "topic"
    assert pub["name_from"] == key and pub["name_key"] == key[len("config:"):]
    assert pub["resolved_values"] == {"default": "local.mdp.dealer_data"}
    assert pub["namespace"] == "mdp-ns"
    sender = MDP_JB + "service/service_bus/DealerDataSenderService.java"
    assert pub["published_by"] == f"{sender}:{_line(MDP_SENDER, 'sendMessage(')}"
    assert pub["message_types"] == ["DEALER_UPDATED"]
    assert pub["properties"] == {"session_id": True, "app_properties": ["dealerId"]}
    sub = msgs[f"messaging:.:subscribe:azure-service-bus:{key}"].attributes
    assert sub["subscription"] == "mdp" and sub["trigger"] == "processor"
    assert sub["properties"] == {"session_id": True, "auto_complete": False,
                                 "max_concurrent_sessions": 1}
    assert sub["error_handling"] == {"error_handler": True}
    cfg = MDP_JB + "config/DealerMasterServiceBusConfig.java"
    assert sub["handler"] == f"{cfg}:{_line(MDP_SB, 'onMessage = context')}"
    da = _items(res, "data_access")["data_access:.:postgres:config:spring.datasource.url"]
    a = da.attributes
    assert (a["host"], a["database"], a["orm"]) == ("db.example.test", "mdpdb", "spring-data")
    rows = {r["name"]: r for r in a["entities"]}
    assert rows["Dealer"]["table"] == "dealer" and rows["Dealer"]["schema"] == "mdp"
    assert rows["Dealer"]["operation"] == "both" and rows["dealer_flag"]["operation"] == "read"
    assert da.confidence == "medium"   # native SQL tables
    job = next(i for i in res["items"] if i.kind == "scheduled_job").attributes
    assert job["trigger_type"] == "cron" and job["expression"] == "0 0 2 * * *"
    assert job["expression_from"] == "config:jobs.cleanup.cron"
    assert job["timezone"] == "Asia/Kolkata" and job["name"] == "DealerJob.cleanup"
    reads = _items(res, "config_key")["config_key:.:spring.jms.servicebus.topic.dealerdata.name"]
    assert any(r["api"] == "@Value" and r["file"] == cfg for r in reads.attributes["reads"])
    blob = json.dumps([i.to_dict() for i in res["items"]])
    assert FAKE_SAS not in blob and FAKE_PW not in blob and "SharedAccessKey=" not in blob


def test_master_data_platform_end_to_end_no_secret(root, org_cfg):
    store = StateStore()
    make_ledgered_repo(root, org_cfg, store, "mdp", MDP)
    assert p2.extract_one(org_cfg, store, "mdp") == "done"
    out = paths.runs_dir("TEST-ORG", "mdp")
    for name in ("inventory.json", "ledger.json", "meta.json"):
        data = (out / name).read_text()
        assert FAKE_SAS not in data and FAKE_PW not in data, name
    inv = json.loads((out / "inventory.json").read_text())
    assert inv["extractor_versions"]["java.spring"] == sx.versioned("0.2.0", "java")
    led = {f["path"]: f for f in json.loads((out / "ledger.json").read_text())["files"]}
    assert led[MDP_JB + "controller/DealerController.java"]["status"] == "extracted"
    assert FAKE_SAS not in paths.state_path().read_text()


# ---- notification-service --------------------------------------------------------------------
# src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java (trimmed)
NOTIF = """package com.tvsmotor.notification.config;
import com.azure.messaging.servicebus.*;
import org.springframework.beans.factory.annotation.Value;
@Configuration
public class ServiceBusConfig {
    @Value("${spring.jms.servicebus.connection-string}")
    private String azureServiceBusTopicConnectionString;
    @Value("${spring.jms.servicebus.topic.notifications}")
    private String notificationDataTopicName;
    private LoadingCache<String, ServiceBusSenderClient> queueSenders;
    @Bean(name = "notificationServiceBusSenderClient")
    public ServiceBusSenderClient topicSenderClient() {
        return new ServiceBusClientBuilder()
                .connectionString(azureServiceBusTopicConnectionString)
                .sender()
                .topicName(notificationDataTopicName)
                .buildClient();
    }
    @PostConstruct
    public void init() {
        queueSenders = Caffeine.newBuilder()
                .build(queueName -> new ServiceBusClientBuilder()
                        .connectionString(azureServiceBusTopicConnectionString)
                        .sender()
                        .queueName(queueName)
                        .buildClient()
                );
    }
}
"""


def test_notification_service_field_value_and_dynamic_queue():
    path = "src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java"
    files = {path: NOTIF, "src/main/resources/application.yml":
             "spring:\n  jms:\n    servicebus:\n      topic:\n        notifications: local.notifications\n"}
    _c, res = _run(files)
    msgs = _items(res, "messaging")
    topic = msgs["messaging:.:publish:azure-service-bus:config:spring.jms.servicebus.topic."
                 "notifications"].attributes
    assert topic["entity"] == "local.notifications" and topic["entity_type"] == "topic"
    dyn = msgs["messaging:.:publish:azure-service-bus:unknown"]
    assert dyn.attributes["entity"] is None and dyn.attributes["name_from"] == "unknown"
    assert dyn.attributes["entity_type"] == "queue" and dyn.confidence == "medium"
    assert _touch(res, path).parse == "partial"


# ---- TVS-CPS-BACKEND bff-service Kafka listener ----------------------------------------------
# bff-service .../messaging/BookingMessagingConstants.java + consumer/BookingServiceConsumer.java
# (trimmed): the placeholder only exists after folding "${" + KAFKA_PREFIX + ".topics.booking}".
KAFKA_CONST = """package com.tvsm.bff.messaging;
public final class BookingMessagingConstants {
    public static final String KAFKA_PREFIX = "bff.booking.messaging.kafka";
    public static final String PROP_TOPIC_BOOKING = "${" + KAFKA_PREFIX + ".topics.booking}";
}
"""
KAFKA_CONSUMER = """package com.tvsm.bff.messaging.consumer;
import static com.tvsm.bff.messaging.BookingMessagingConstants.*;
import org.springframework.kafka.annotation.KafkaListener;
public class BookingServiceConsumer {
    @KafkaListener(id = "booking-order-allocation-consumer", topics = PROP_TOPIC_BOOKING)
    public void consume(String payload) {}
}
"""


def test_kafka_topic_placeholder_built_by_concatenation():
    base = "bff-service/src/main/java/com/tvsm/bff/messaging/"
    files = {base + "BookingMessagingConstants.java": KAFKA_CONST,
             base + "consumer/BookingServiceConsumer.java": KAFKA_CONSUMER}
    _c, res = _run(files)
    (m,) = _items(res, "messaging").values()
    a = m.attributes
    assert a["direction"] == "subscribe" and a["broker"] == "kafka"
    assert a["entity"] is None, "an unresolved ${...} placeholder is not a topic name"
    assert a["name_from"] == "config:bff.booking.messaging.kafka.topics.booking"
    # with the property present the topic resolves
    files["bff-service/src/main/resources/application.yml"] = (
        "bff:\n  booking:\n    messaging:\n      kafka:\n        topics:\n"
        "          booking: dev.cp-booking-events\n")
    _c, res = _run(files, stacks=(("java", "bff-service"),))
    (m,) = _items(res, "messaging").values()
    assert m.attributes["entity"] == "dev.cp-booking-events"


# bff-service .../producer/ServiceLeadEventProducer.java (trimmed): publish through the tvsm-be-core
# KafkaProducerUtil wrapper (TVS-CPS-BE-BASE-FRAMEWORK).
KAFKA_UTIL_PRODUCER = """package com.tvsm.bff.producer;
import com.tvsm.core.messaging.kafka.producer.KafkaProducerUtil;
import org.springframework.beans.factory.annotation.Value;
public class ServiceLeadEventProducer {
    private final KafkaProducerUtil producer;
    @Value("${bff.servicelead.messaging.kafka.topics.service-lead:dev.cp.service_lead}")
    private String topicName;
    public ServiceLeadEventProducer(KafkaProducerUtil kafkaProducerUtil) {
        this.producer = kafkaProducerUtil.forPublisher("service-lead");
    }
    public void publish(String eventId, Object payload) {
        producer
                .sendJson(topicName, eventId, payload)
                .join();
    }
}
"""


def test_kafka_producer_util_wrapper_publish():
    path = "bff-service/src/main/java/com/tvsm/bff/producer/ServiceLeadEventProducer.java"
    _c, res = _run({path: KAFKA_UTIL_PRODUCER})
    (m,) = _items(res, "messaging").values()
    a = m.attributes
    assert (a["direction"], a["broker"], a["library"]) == ("publish", "kafka", "tvsm-be-core")
    assert a["name_from"] == "config:bff.servicelead.messaging.kafka.topics.service-lead"
    assert a["entity"] == "dev.cp.service_lead"  # @Value default
    assert m.evidence[0].line == _line(KAFKA_UTIL_PRODUCER, ".sendJson(")


# order-service .../service/OrderProducerService.java + messaging/OrderMessagingConstants.java
# (trimmed): @Value takes a constant whose text is a concatenated placeholder.
ORDER_CONST = """package com.tvsm.order.messaging;
public final class OrderMessagingConstants {
    public static final String KAFKA_PREFIX = "order.messaging.kafka";
    public static final String PROP_TOPIC_ORDER = "${" + KAFKA_PREFIX + ".topics.order}";
}
"""
ORDER_PRODUCER = """package com.tvsm.order.service;
import com.tvsm.core.messaging.kafka.producer.KafkaProducerUtil;
import com.tvsm.order.messaging.OrderMessagingConstants;
import org.springframework.beans.factory.annotation.Value;
public class OrderProducerService {
    private final KafkaProducerUtil kafkaProducerUtil;
    @Value(OrderMessagingConstants.PROP_TOPIC_ORDER)
    private String topic;
    public OrderProducerService(KafkaProducerUtil kafkaProducerUtil) {
        this.kafkaProducerUtil = kafkaProducerUtil;
    }
    public void publishOrderEvent(Object event, String key) {
        kafkaProducerUtil.sendJsonAsync(topic, key, event, () -> {}, ex -> {});
    }
}
"""


def test_value_annotation_with_constant_argument():
    files = {"order-service/src/main/java/com/tvsm/order/messaging/OrderMessagingConstants.java":
             ORDER_CONST,
             "order-service/src/main/java/com/tvsm/order/service/OrderProducerService.java":
             ORDER_PRODUCER,
             "order-service/src/main/resources/application.yml":
             "order:\n  messaging:\n    kafka:\n      topics:\n        order: dev.cp.order\n"}
    _c, res = _run(files, stacks=(("java", "order-service"),))
    (m,) = _items(res, "messaging").values()
    assert m.attributes["name_from"] == "config:order.messaging.kafka.topics.order"
    assert m.attributes["entity"] == "dev.cp.order"


# ---- TVS-CPS-BACKEND bff-service outbound ------------------------------------------------------
# bff-service .../client/ClaimClient.java + constants/ClaimBFFEndpoints.java (trimmed)
CLAIM_EP = """package com.tvsm.bff.constants;
public class ClaimBFFEndpoints {
    public static final String BASE_PATH = "/cps/api/v1/claims";
}
"""
CLAIM_CLIENT = """package com.tvsm.bff.client;
import com.tvsm.bff.constants.*;
import com.tvsm.bff.dto.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
@Component
public class ClaimClient {
    @Value("${bff.claim-service.base-url}")
    private String baseUrl;
    private final RestTemplate restTemplate;
    private void callCreateClaimApi(ClaimCreateRequestDTO claimCreateRequestDTO, String token) {
            HttpHeaders headers = new HttpHeaders();
            HttpEntity<ClaimCreateRequestDTO> requestEntity = new HttpEntity<>(claimCreateRequestDTO, headers);
            String url = baseUrl + ClaimBFFEndpoints.BASE_PATH;
            ResponseEntity<String> responseEntity = restTemplate.exchange(
                    url, HttpMethod.POST, requestEntity, String.class);
    }
}
"""
CLAIM_DTO = """package com.tvsm.bff.dto;
@lombok.Data
public class ClaimCreateRequestDTO { private String channel; }
"""
# lead-allocation .../constants/ApiConstants.java (another Maven module) +
# bff-service .../client/LeadAllocationServiceClient.java (trimmed)
LEAD_CONST = """package com.tvsm.leadallocation.constants;
public final class ApiConstants {
    public static final String LEAD_ALLOCATION_API_BASE_PATH = "/api/v1/lead-allocation";
    public static final String LIST_ENDPOINT = "/list";
}
"""
LEAD_CLIENT = """package com.tvsm.bff.client;
import com.tvsm.leadallocation.constants.ApiConstants;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.reactive.function.client.WebClient;
public class LeadAllocationServiceClient {
    @Value("${bff.lead-allocation.base-url}")
    private String leadAllocationServiceBaseUrl;
    private WebClient buildClient() {
        return WebClient.builder()
                .baseUrl(leadAllocationServiceBaseUrl + ApiConstants.LEAD_ALLOCATION_API_BASE_PATH)
                .build();
    }
    public String getLeadAllocationList(LeadAllocationListRequestDTO request) {
        return buildClient().post()
                .uri(ApiConstants.LIST_ENDPOINT)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(String.class).block();
    }
}
"""
BFF = "TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/"
BFF_FILES = {
    "bff-service/src/main/resources/application.yml":
        "bff:\n  claim-service:\n    base-url: https://claims.example.test\n"
        "  lead-allocation:\n    base-url: https://leads.example.test\n",
    "bff-service/src/main/java/com/tvsm/bff/constants/ClaimBFFEndpoints.java": CLAIM_EP,
    "bff-service/src/main/java/com/tvsm/bff/client/ClaimClient.java": CLAIM_CLIENT,
    "bff-service/src/main/java/com/tvsm/bff/dto/ClaimCreateRequestDTO.java": CLAIM_DTO,
    "bff-service/src/main/java/com/tvsm/bff/client/LeadAllocationServiceClient.java": LEAD_CLIENT,
    "lead-allocation/src/main/java/com/tvsm/leadallocation/constants/ApiConstants.java": LEAD_CONST,
}


def test_bff_resttemplate_and_webclient_outbound():
    _c, res = _run(BFF_FILES, [("java", "bff-service"), ("java", "lead-allocation")])
    out = _items(res, "outbound_http")
    claim = out["outbound_http:bff-service:POST:config:bff.claim-service.base-url:"
                "/cps/api/v1/claims"]
    a = claim.attributes
    assert (a["client"], a["role"], a["request"], a["response"]) == (
        "resttemplate", "runtime", "ClaimCreateRequestDTO", "string")
    assert a["base_url_values"] == {"default": "https://claims.example.test"}
    assert a["path_raw"] == "url" and claim.confidence == "high"
    lead = out["outbound_http:bff-service:POST:config:bff.lead-allocation.base-url:"
               "/api/v1/lead-allocation/list"].attributes
    assert lead["client"] == "webclient" and lead["request"] == "LeadAllocationListRequestDTO"
    assert lead["response"] == "string"
    assert lead["base_url_values"] == {"default": "https://leads.example.test"}
    assert "schema:bff-service:ClaimCreateRequestDTO" in _items(res, "schema")


# ---- TVS-CPS-BILLING ApiPassthroughUtil (one-level wrapper) ----------------------------------
# src/main/java/com/tvsm/billing/util/ApiPassthroughUtil.java (verbatim shape) + a caller
PASS_UTIL = """package com.tvsm.billing.util;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
@Component
public class ApiPassthroughUtil {
    public <T> ResponseEntity<T> post(RestTemplate restTemplate, String url, Object request, HttpHeaders headers, Class<T> responseType) {
        HttpEntity<Object> entity = new HttpEntity<>(request, headers);
        return restTemplate.exchange(url, HttpMethod.POST, entity, responseType);
    }
}
"""
PASS_CALLER = """package com.tvsm.billing.service;
import com.tvsm.billing.util.ApiPassthroughUtil;
public class StockService {
    private final ApiPassthroughUtil apiPassthroughUtil;
    private final RestTemplate restTemplate;
    @Value("${inventory.base-url}")
    private String inventoryUrl;
    public StockDto reserve(Object req, HttpHeaders headers) {
        return apiPassthroughUtil.post(restTemplate, inventoryUrl + "/api/v1/stock/reserve", req, headers, StockDto.class).getBody();
    }
}
"""


def test_one_level_wrapper_following():
    util = "src/main/java/com/tvsm/billing/util/ApiPassthroughUtil.java"
    files = {util: PASS_UTIL, "src/main/java/com/tvsm/billing/service/StockService.java":
             PASS_CALLER}
    _c, res = _run(files)
    out = list(_items(res, "outbound_http").values())
    assert [o.id for o in out] == [
        "outbound_http:.:POST:config:inventory.base-url:/api/v1/stock/reserve"]
    a = out[0].attributes
    assert a["via_wrapper"] == f"{util}:{_line(PASS_UTIL, 'restTemplate.exchange')}"
    assert a["response"] == "StockDto" and out[0].confidence == "medium"
    assert _touch(res, util).parse == "full"


# ---- Feign (synthetic: no Feign client exists in the TVS-CS clones) ---------------------------
FEIGN = """package x.client;
@FeignClient(name = "pricing", url = "${pricing.url}", path = "/api")
public interface PricingClient {
    @GetMapping("/prices/{id}")
    PriceDto price(@PathVariable("id") String id);
}
"""


def test_feign_client():
    _c, res = _run({"src/main/java/x/client/PricingClient.java": FEIGN})
    a = _items(res, "outbound_http")["outbound_http:.:GET:config:pricing.url:/api/prices/{}"]
    assert a.attributes["client"] == "feign" and a.attributes["client_name"] == "pricing"
    assert a.attributes["response"] == "PriceDto"


# ---- Core-Commerce-Platform-API-Service-Testng-like test suite --------------------------------
TESTNG_POM = """<project><artifactId>cc-api-tests</artifactId><dependencies>
<dependency><groupId>org.testng</groupId><artifactId>testng</artifactId><version>7.10.2</version></dependency>
</dependencies></project>
"""
TESTNG_TEST = """package tests;
public class CatalogApiTest {
    private final RestTemplate restTemplate = new RestTemplate();
    @Test
    public void listCatalog() {
        restTemplate.getForObject("https://catalog.example.test/api/v1/catalog?page=1", String.class);
    }
}
"""


def test_test_suite_outbound_is_tests_target():
    files = {"pom.xml": TESTNG_POM, "testng.xml": "<suite name='s'/>\n",
             "src/test/java/tests/CatalogApiTest.java": TESTNG_TEST}
    _c, res = _run(files)
    assert res["repo_type"]["value"] == "test-suite"
    out = list(_items(res, "outbound_http").values())
    assert len(out) == 1 and out[0].attributes["role"] == "tests_target"
    assert out[0].attributes["query_params"] == ["page"]
    assert out[0].attributes["base_url_source"] == "literal"
    assert out[0].id == "outbound_http:.:GET:catalog.example.test:/api/v1/catalog"
    assert not [i for i in res["items"] if i.kind in ("inbound_http", "messaging")]


# ---- parse errors + determinism ----------------------------------------------------------------
def test_error_tree_is_partial_and_still_extracted():
    broken = JOBCARD.replace("public class JobcardController {",
                             "public class JobcardController { int x = ;")
    path = "src/main/java/com/tvsm/jobcard/controller/JobcardController.java"
    _c, res = _run({path: broken})
    t = _touch(res, path)
    assert t.parse == "partial" and t.error.startswith("tree-sitter:")
    assert any(e["file"] == path for e in res["errors"])
    assert "inbound_http:.:POST:/api/v1/jobcards/list" in _items(res, "inbound_http")


def test_deterministic_twice():
    files = {**APPT, **MDP, **AUTH}
    stacks = [("java", "."), ("java", "appointment-service")]
    a = [i.to_dict() for i in _run(files, stacks)[1]["items"]]
    b = [i.to_dict() for i in _run(files, stacks)[1]["items"]]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert JavaSpring.extractor_version == sx.versioned("0.2.0", "java")


# ---- review fixes: payload, unsupported clients, Mockito stubs, datasource fallback ----------
PAYLOAD_SENDER = MDP_SENDER.replace(
    'final ServiceBusMessage message = new ServiceBusMessage("{}");',
    'final DealerData dealerData = new DealerData();\n'
    '        final ServiceBusMessage message = new ServiceBusMessage('
    'jsonHelperService.toJson(dealerData));')
DEALER_DATA = """package com.tvsmotor.mdp.service.service_bus;
public class DealerData { private Long dealerId; private String name; }
"""
JMS_LISTENER = """package com.tvsmotor.mdp.listener;
import org.springframework.jms.annotation.JmsListener;
@Component
public class OrderListener {
    @JmsListener(destination = "orders", subscription = "mdp")
    public void onOrder(String body) {
        OrderEvent e = objectMapper.readValue(body, OrderEvent.class);
    }
}
class OrderEvent { private String id; }
"""


def test_messaging_payload_from_serialized_typed_local_and_listener():
    files = {**MDP, MDP_JB + "service/service_bus/DealerDataSenderService.java": PAYLOAD_SENDER,
             MDP_JB + "service/service_bus/DealerData.java": DEALER_DATA,
             MDP_JB + "listener/OrderListener.java": JMS_LISTENER}
    _c, res = _run(files)
    msgs = _items(res, "messaging")
    key = "config:spring.jms.servicebus.topic.dealerData.name"
    pub = msgs[f"messaging:.:publish:azure-service-bus:{key}"].attributes
    assert pub["payload"] == "DealerData"
    assert "schema:.:DealerData" in _items(res, "schema")
    sub = next(m.attributes for m in msgs.values() if m.attributes["entity"] == "orders")
    assert sub["direction"] == "subscribe" and sub["payload"] == "OrderEvent"


UNSUPPORTED_CLIENTS = """package com.tvsm.parts.search;
import org.elasticsearch.client.RestHighLevelClient;
import com.azure.cosmos.CosmosClient;
public class SearchRepository {
    private final RestHighLevelClient client;
    public SearchRepository(RestHighLevelClient c) { this.client = c; }
}
"""
# an OpenSearch client holder without calls: supported since java.spring 0.2.0 -> full, no item
OPENSEARCH = """package com.tvsm.parts.search;
import org.opensearch.client.opensearch.OpenSearchClient;
public class OpenSearchHolder {
    private final OpenSearchClient client;
    public OpenSearchHolder(OpenSearchClient c) { this.client = c; }
}
"""
PLAIN = """package com.tvsm.parts.util;
public class Strings { public static String trim(String s) { return s.trim(); } }
"""


def test_unsupported_client_imports_leave_file_partial():
    a, b = "src/main/java/com/tvsm/parts/search/SearchRepository.java", \
        "src/main/java/com/tvsm/parts/util/Strings.java"
    o = "src/main/java/com/tvsm/parts/search/OpenSearchHolder.java"
    _c, res = _run({a: UNSUPPORTED_CLIENTS, b: PLAIN, o: OPENSEARCH})
    assert _touch(res, a).parse == "partial" and _touch(res, a).error is None
    assert _touch(res, b).parse == "full"
    assert _touch(res, o).parse == "full"
    assert not [i for i in res["items"] if i.kind == "data_access"]


MOCK_TEST = """package com.tvsm.parts;
import org.springframework.web.client.RestClient;
import static org.mockito.Mockito.when;
class MdpEnrichmentServiceTest {
    private RestClient mdpRestClient;
    void setUp() {
        when(mdpRestClient.get()).thenReturn(null);
        verify(mdpRestClient).get();
    }
}
"""


def test_mockito_stubs_are_not_outbound_calls():
    _c, res = _run({"src/test/java/com/tvsm/parts/MdpEnrichmentServiceTest.java": MOCK_TEST})
    assert not _items(res, "outbound_http")


MT_APP_YML = """tvsm:
  core:
    multitenant:
      datasource:
        default-data-source:
          url: jdbc:postgresql://cps-db.example.test:5432/cpsdb?currentSchema=cps
"""
MT_ENTITY = """package com.tvsm.billing;
import jakarta.persistence.*;
@Entity
@Table(name = "invoice")
public class Invoice { @Id private Long id; }
"""


def test_module_without_datasource_key_uses_repo_wide_custom_datasource():
    files = {"app/src/main/resources/config/application.yml": MT_APP_YML,
             "billing/src/main/java/com/tvsm/billing/Invoice.java": MT_ENTITY}
    _c, res = _run(files, [("java", "app"), ("java", "billing")])
    da = [i for i in res["items"] if i.kind == "data_access"]
    assert len(da) == 1 and da[0].subproject == "billing"
    a = da[0].attributes
    assert a["store_type"] == "postgres" and a["host"] == "cps-db.example.test"
    assert a["database"] == "cpsdb"
    assert a["name_from"] == \
        "config:tvsm.core.multitenant.datasource.default-data-source.url"

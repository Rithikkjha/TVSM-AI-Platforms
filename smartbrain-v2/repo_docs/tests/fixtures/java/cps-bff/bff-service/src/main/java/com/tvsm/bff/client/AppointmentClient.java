// source: TVS-CS/TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/client/AppointmentClient.java (trimmed)
package com.tvsm.bff.client;
import com.tvsm.bff.constants.AppointmentServiceEndpoints;
import com.tvsm.bff.util.ApiPassthroughUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import java.util.HashMap;
import java.util.Map;
@Component
@RequiredArgsConstructor
public class AppointmentClient {
    private final RestTemplate restTemplate;
    private final ApiPassthroughUtil apiPassthroughUtil;
    @Value("${bff.appointment-service.base-url}")
    private String appointmentServiceBaseUrl;
    public ResponseEntity<Map<String, Object>> createAppointment(Map<String, Object> request, HttpHeaders headers) {
        request.put("customerVehicleDetails", new HashMap<>());
        return apiPassthroughUtil.post(
                restTemplate,
                appointmentServiceBaseUrl,
                AppointmentServiceEndpoints.APPOINTMENT_CREATE_ENDPOINTS,
                request,
                headers,
                "create appointment");
    }
    public ResponseEntity<Map<String, Object>> listAppointments(Map<String, Object> queryParams, HttpHeaders headers) {
        return apiPassthroughUtil.getWithQueryParams(restTemplate, appointmentServiceBaseUrl,
                AppointmentServiceEndpoints.APPOINTMENT_LIST_ENDPOINTS, queryParams, headers, "list appointments");
    }
}

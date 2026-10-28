// source: TVS-CS/TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/client/LeadServiceClient.java (trimmed)
package com.tvsm.bff.client;
import com.tvsm.bff.constants.EnquiryEndpoints;
import com.tvsm.bff.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.reactive.function.client.WebClient;
import java.util.HashMap;
import java.util.Map;
@RequiredArgsConstructor
@Component
public class LeadServiceClient {
    private final RestTemplate restTemplate;
    private static final String PARAM_PAGE_NUMBER = "?PageNumber=";
    private static final String PARAM_PAGE_SIZE = "&PageSize=";
    private static final int MAX_IN_MEMORY_SIZE = 10 * 1024 * 1024;
    @Value("${lead.api.url}")
    private String leadApiUrl;
    private WebClient buildClient(String accessToken, Map<String, String> additionalHeaders) {
        WebClient.Builder builder =  WebClient.builder()
                .baseUrl(leadApiUrl+EnquiryEndpoints.LEAD_BASE_URL)
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
        if (additionalHeaders != null) {
            additionalHeaders.forEach(builder::defaultHeader);
        }
        return builder.build();
    }
    public String createLead(EnquiryRequestDto enquiryRequestDto, String accessToken) {
        return buildClient(accessToken, null).post()
                .uri(EnquiryEndpoints.CREATE_LEAD)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(enquiryRequestDto)
                .retrieve()
                .bodyToMono(String.class)
                .block();
    }
    public String filterLeads(LeadFilterRequestDto filterRequestDto, int currentPage, int size, String accessToken) {
        String url = EnquiryEndpoints.LEAD_FILTER + PARAM_PAGE_NUMBER + currentPage + PARAM_PAGE_SIZE + size;
        Map<String, String> additionalHeaders = new HashMap<>();
        WebClient largeBufferClient = buildClient(accessToken, additionalHeaders)
                .mutate()
                .codecs(c -> c.defaultCodecs().maxInMemorySize(MAX_IN_MEMORY_SIZE))
                .build();
        return largeBufferClient.post()
                        .uri(url)
                        .contentType(MediaType.APPLICATION_JSON)
                        .bodyValue(filterRequestDto)
                .retrieve()
                .bodyToMono(String.class)
                .block();
    }
    public String fetchLeadsByDseId(String dseId, int pageNumber, int pageSize, HttpHeaders headers) {
        String url = leadApiUrl + EnquiryEndpoints.LEAD_BASE_URL + EnquiryEndpoints.LEAD_FILTER
                + PARAM_PAGE_NUMBER + pageNumber + PARAM_PAGE_SIZE + pageSize;
        Map<String, Object> body = new HashMap<>();
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<String> response =
                restTemplate.postForEntity(url, entity, String.class);
        return response.getBody();
    }
}

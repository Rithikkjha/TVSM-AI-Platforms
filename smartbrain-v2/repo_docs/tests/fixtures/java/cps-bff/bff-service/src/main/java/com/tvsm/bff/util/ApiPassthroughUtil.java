// source: TVS-CS/TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/util/ApiPassthroughUtil.java (trimmed)
package com.tvsm.bff.util;

import com.tvsm.bff.config.HeaderForwardingConfig;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.util.MultiValueMap;
import java.util.*;
import java.net.MalformedURLException;
import java.net.URL;

@Slf4j
@Component
public class ApiPassthroughUtil {

    private static final String LOG_REQUEST = "Making {} request to: {} for operation: {}";

    private final HeaderForwardingConfig headerForwardingConfig;

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_TYPE_REF = new ParameterizedTypeReference<Map<String, Object>>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_MAP_TYPE_REF = new ParameterizedTypeReference<List<Map<String, Object>>>() {};

    public ApiPassthroughUtil(HeaderForwardingConfig headerForwardingConfig) {
        this.headerForwardingConfig = headerForwardingConfig;
    }

    private void validateEndpoint(String baseUrl, String endpoint) {
        if (endpoint == null || endpoint.isEmpty()) {
            throw new IllegalArgumentException("Endpoint cannot be null or empty");
        }
        if (endpoint.contains("://") || endpoint.startsWith("//")) {
            throw new IllegalArgumentException("Endpoint must be a relative path");
        }
        try {
            new URL(baseUrl);
        } catch (MalformedURLException e) {
            throw new IllegalArgumentException("Invalid base URL: " + baseUrl, e);
        }
    }

    private String buildSafeUrl(String baseUrl, String endpoint) {
        validateEndpoint(baseUrl, endpoint);
        return UriComponentsBuilder.fromUriString(baseUrl)
                .path(endpoint)
                .build()
                .toUriString();
    }

    public ResponseEntity<Map<String, Object>> get(RestTemplate restTemplate, String baseUrl, String endpoint, HttpHeaders requestHeaders, String operation) {
        return getMethodCall(restTemplate, baseUrl, endpoint, null, requestHeaders, operation);
    }

    public ResponseEntity<Map<String, Object>> getWithQueryParams(RestTemplate restTemplate, String baseUrl, String basePath, Map<String, Object> queryParams, HttpHeaders requestHeaders, String operation) {
        return getMethodCall(restTemplate, baseUrl, basePath, queryParams, requestHeaders, operation);
    }

    private ResponseEntity<Map<String, Object>> getMethodCall(RestTemplate restTemplate, String baseUrl, String basePath, Map<String, Object> queryParams, HttpHeaders requestHeaders, String operation) {
        try {
            UriComponentsBuilder builder = getUriComponentsBuilder(baseUrl, basePath, queryParams);

            String fullUrl = builder.build().toUriString();
            log.debug(LOG_REQUEST, "GET", fullUrl, operation);

            HttpHeaders headers = createForwardedHeaders(requestHeaders);
            HttpEntity<Void> entity = new HttpEntity<>(headers);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(fullUrl, HttpMethod.GET, entity, MAP_TYPE_REF);
            return response;
        } catch (RestClientException error) {
            throw error;
        }
    }

    private UriComponentsBuilder getUriComponentsBuilder(String baseUrl, String basePath, Map<String, Object> queryParams) {
        validateEndpoint(baseUrl, basePath);

        UriComponentsBuilder builder = UriComponentsBuilder.fromUriString(baseUrl)
                .path(basePath);

        if (queryParams != null) {
            queryParams.forEach((key, value) -> {
                if (value != null) {
                    builder.queryParam(key, value);
                }
            });
        }
        return builder;
    }

    public ResponseEntity<Map<String, Object>> post(RestTemplate restTemplate, String baseUrl, String endpoint, Map<String, Object> request, HttpHeaders requestHeaders, String operation) {
          return postMethodCall(restTemplate, baseUrl, endpoint, null, request, requestHeaders, operation);
    }

    public <T> ResponseEntity<Map<String, Object>> post(RestTemplate restTemplate, String baseUrl, String endpoint, T request, HttpHeaders requestHeaders, String operation) {
        return postMethodCall(restTemplate, baseUrl, endpoint, null, request, requestHeaders, operation);
    }

    private ResponseEntity<Map<String, Object>> postMethodCall(RestTemplate restTemplate, String baseUrl, String basePath, Map<String, Object> queryParams, Map<String, Object> request, HttpHeaders requestHeaders, String operation) {
        try {
            UriComponentsBuilder builder = getUriComponentsBuilder(baseUrl, basePath, queryParams);

            String fullUrl = builder.build().toUriString();
            log.debug(LOG_REQUEST, "POST", fullUrl, operation);

            HttpHeaders headers = createForwardedHeaders(requestHeaders);
            if (request != null) {
                headers.setContentType(MediaType.APPLICATION_JSON);
            }
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(fullUrl, HttpMethod.POST, entity, MAP_TYPE_REF);
            return response;
        } catch (RestClientException error) {
            throw error;
        }
    }

    private <T> ResponseEntity<Map<String, Object>> postMethodCall(RestTemplate restTemplate, String baseUrl, String basePath, Map<String, Object> queryParams, T request, HttpHeaders requestHeaders, String operation) {
        try {
            UriComponentsBuilder builder = getUriComponentsBuilder(baseUrl, basePath, queryParams);
            String fullUrl = builder.build().toUriString();
            HttpHeaders headers = createForwardedHeaders(requestHeaders);
            HttpEntity<T> entity = new HttpEntity<>(request, headers);
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(fullUrl, HttpMethod.POST, entity, MAP_TYPE_REF);
            return response;
        } catch (RestClientException error) {
            throw error;
        }
    }

    public ResponseEntity<Map<String, Object>> put(RestTemplate restTemplate, String baseUrl, String endpoint, HttpHeaders requestHeaders, String operation) {
        String fullUrl = buildSafeUrl(baseUrl, endpoint);
        log.debug(LOG_REQUEST, "PUT", fullUrl, operation);
        HttpHeaders headers = createForwardedHeaders(requestHeaders);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        return restTemplate.exchange(fullUrl, HttpMethod.PUT, entity, MAP_TYPE_REF);
    }

    public ResponseEntity<Map<String, Object>> putWithBody(RestTemplate restTemplate, String baseUrl, String endpoint, Map<String, Object> request, HttpHeaders requestHeaders, String operation) {
        String fullUrl = buildSafeUrl(baseUrl, endpoint);
        HttpHeaders headers = createForwardedHeaders(requestHeaders);
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(request, headers);
        return restTemplate.exchange(fullUrl, HttpMethod.PUT, entity, MAP_TYPE_REF);
    }

    public ResponseEntity<Map<String, Object>> delete(RestTemplate restTemplate, String baseUrl, String endpoint, HttpHeaders requestHeaders, String operation) {
        String fullUrl = buildSafeUrl(baseUrl, endpoint);
        HttpHeaders headers = createForwardedHeaders(requestHeaders);
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        return restTemplate.exchange(fullUrl, HttpMethod.DELETE, entity, MAP_TYPE_REF);
    }

    public ResponseEntity<Map<String, Object>> postMultipart(RestTemplate restTemplate, String baseUrl, String endpoint, MultiValueMap<String, Object> formData, HttpHeaders requestHeaders, String operation) {
        String fullUrl = buildSafeUrl(baseUrl, endpoint);
        HttpHeaders headers = createForwardedHeaders(requestHeaders);
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(formData, headers);
        return restTemplate.exchange(fullUrl, HttpMethod.POST, entity, MAP_TYPE_REF);
    }

    private HttpHeaders createForwardedHeaders(HttpHeaders requestHeaders) {
        HttpHeaders headers = new HttpHeaders();
        if (requestHeaders != null && headerForwardingConfig != null) {
            requestHeaders.forEach((key, values) -> {
                if (headerForwardingConfig.isHeaderAllowed(key)) {
                    headers.put(key, values);
                }
            });
        }
        return headers;
    }

    public <T> ResponseEntity<T> post(RestTemplate restTemplate, String baseUrl, String endpoint, Object request, HttpHeaders requestHeaders, String operation, Class<T> responseType) {
        String fullUrl = buildSafeUrl(baseUrl, endpoint);
        HttpHeaders headers = createForwardedHeaders(requestHeaders);
        HttpEntity<Object> entity = new HttpEntity<>(request, headers);
        ResponseEntity<T> response = restTemplate.exchange(fullUrl, HttpMethod.POST, entity, responseType);
        return response;
    }

    public HttpHeaders createHeaders(String clientId, String scope, String tenantId) {
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Client-Id", clientId);
        return headers;
    }

    public <T> ResponseEntity<T> post(RestTemplate restTemplate, String url, Object request, HttpHeaders headers, Class<T> responseType) {
        HttpEntity<Object> entity = new HttpEntity<>(request, headers);
        return restTemplate.exchange(url, HttpMethod.POST, entity, responseType);
    }
}

// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/service/IngestionApiClientService.java (trimmed)
package org.com.graph.service;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.retry.Retry;
import lombok.RequiredArgsConstructor;
import org.com.graph.config.CatalogueApiProperties;
import org.springframework.web.client.RestClient;
@RequiredArgsConstructor
public class IngestionApiClientService {
    private final CircuitBreaker circuitBreaker;
    private final Retry retry;
    private final CatalogueApiProperties properties;
    private final RestClient client;
    public boolean isApiHealthy() {
        try {
            client.get()
                    .uri(properties.getBaseUrl())
                    .retrieve()
                    .toBodilessEntity();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}

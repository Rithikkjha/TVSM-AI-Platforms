// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/service/MdpEnrichmentService.java (trimmed)
package org.com.graph.service;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import org.com.graph.config.MdpApiProperties;
import org.com.graph.dto.MdpResponseDto;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
@Service
public class MdpEnrichmentService {
    private final MdpApiProperties mdpProperties;
    private final RestClient mdpRestClient;
    private final CircuitBreaker circuitBreaker;
    public MdpEnrichmentService(
            MdpApiProperties mdpProperties,
            @Qualifier("mdpRestClient") RestClient mdpRestClient,
            @Qualifier("mdpApiCircuitBreaker") CircuitBreaker circuitBreaker) {
        this.mdpProperties = mdpProperties;
        this.mdpRestClient = mdpRestClient;
        this.circuitBreaker = circuitBreaker;
    }
    private MdpResponseDto callMdpApi() {
        return mdpRestClient.get()
                .uri(mdpProperties.getEndpoint())
                .accept(MediaType.APPLICATION_JSON)
                .header("x-tenant-id", mdpProperties.getTenantId())
                .retrieve()
                .body(MdpResponseDto.class);
    }
}

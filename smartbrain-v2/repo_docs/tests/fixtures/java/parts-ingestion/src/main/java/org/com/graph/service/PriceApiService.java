// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/service/PriceApiService.java (trimmed)
package org.com.graph.service;
import org.com.graph.config.PriceApiProperties;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
@Service
public class PriceApiService {
    private final PriceApiProperties priceApiProperties;
    private final RestClient priceRestClient;
    public PriceApiService(PriceApiProperties priceApiProperties,
            RestClient priceRestClient) {
        this.priceApiProperties = priceApiProperties;
        this.priceRestClient = priceRestClient;
    }
    public boolean isApiHealthy() {
        try {
            priceRestClient.get()
                    .uri(priceApiProperties.getBaseUrl())
                    .retrieve()
                    .toBodilessEntity();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}

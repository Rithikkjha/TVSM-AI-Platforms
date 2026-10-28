// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/service/strategy/NortonClientStrategy.java
package org.com.graph.service.strategy;
import lombok.Getter;
import org.com.graph.config.NortonCatalogueApiProperties;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
@Component
@Getter
public class NortonClientStrategy implements IClientStrategy {
    private final NortonCatalogueApiProperties properties;
    private final RestClient client;
    public NortonClientStrategy(NortonCatalogueApiProperties properties, @Qualifier("nortonRestClient") RestClient client) {
        this.properties = properties;
        this.client = client;
    }
}

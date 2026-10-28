// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/service/strategy/IClientStrategy.java
package org.com.graph.service.strategy;
import org.com.graph.config.CatalogueApiProperties;
import org.springframework.web.client.RestClient;
public interface IClientStrategy {
    CatalogueApiProperties getProperties();
    RestClient getClient();
}

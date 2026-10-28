// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/config/PriceApiProperties.java (trimmed)
package org.com.graph.config;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
@EqualsAndHashCode(callSuper = true)
@Data
@Configuration
@ConfigurationProperties(prefix = "catalogue.api.price")
public class PriceApiProperties extends CatalogueApiProperties {
    private static final int DEFAULT_BATCH_SIZE = 100;
    private int batchSize = DEFAULT_BATCH_SIZE;
    @Override
    public String getBaseUrl() {
        return super.getBaseUrl();
    }
    public String getUrl() {
        return baseUrl + endpoint;
    }
}

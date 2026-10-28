// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/config/CatalogueApiProperties.java (trimmed)
package org.com.graph.config;
import lombok.Data;
@Data
public abstract class CatalogueApiProperties {
    protected String baseUrl;
    protected String endpoint;
    protected String apiKey;
    protected int timeoutSeconds = 30;
    public abstract String getUrl();
}

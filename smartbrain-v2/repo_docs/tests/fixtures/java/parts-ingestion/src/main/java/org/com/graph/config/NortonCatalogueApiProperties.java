// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/config/NortonCatalogueApiProperties.java (trimmed)
package org.com.graph.config;
import lombok.Data;
import lombok.EqualsAndHashCode;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
@EqualsAndHashCode(callSuper = true)
@Data
@Configuration
@ConfigurationProperties(prefix = "catalogue.api.norton")
public class NortonCatalogueApiProperties extends CatalogueApiProperties{
    @Override
    public String getBaseUrl(){
        return super.getBaseUrl();
    }
    public String getUrl() {
        return baseUrl + endpoint;
    }
}

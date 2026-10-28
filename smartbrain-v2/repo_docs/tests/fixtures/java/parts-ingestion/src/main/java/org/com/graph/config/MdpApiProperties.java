// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/config/MdpApiProperties.java (trimmed)
package org.com.graph.config;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
@Data
@Configuration
@ConfigurationProperties(prefix = "catalogue.api.mdp")
public class MdpApiProperties {
    private String baseUrl;
    private String endpoint;
    private String tenantId;
    private String tokenUrl;
    private String clientId;
    private String clientSecret;
    private String scope;
    private String grantType = "client_credentials";
    private int timeoutSeconds = 30;
    public String getUrl() {
        return baseUrl + endpoint;
    }
}

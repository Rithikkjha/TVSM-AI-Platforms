// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/config/OpenSearchProperties.java (trimmed, fake password default)
package org.com.graph.config;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
@Data
@Configuration
@ConfigurationProperties(prefix = "opensearch")
public class OpenSearchProperties {
    private String host = "localhost";
    private int port = 9200;
    private String username;
    private String password = "fakeOsPw0rd";
    private String partsIndex = "parts_catalogue";
    private String hierarchiesIndex = "parts_hierarchies";
    private String brandCataloguesIndex;
}

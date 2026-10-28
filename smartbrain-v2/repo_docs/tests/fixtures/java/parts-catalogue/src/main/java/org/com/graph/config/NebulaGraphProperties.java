// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/config/NebulaGraphProperties.java (trimmed, fake password default)
package org.com.graph.config;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
@Data
@Configuration
@ConfigurationProperties(prefix = "nebula")
public class NebulaGraphProperties {
    private String hosts = "127.0.0.1";
    private int port = 9669;
    private String space = "parts_catalogue_graph";
    private String username = "root";
    private String password = "fakeNebulaPw0rd";
    private boolean reconnect = true;
}

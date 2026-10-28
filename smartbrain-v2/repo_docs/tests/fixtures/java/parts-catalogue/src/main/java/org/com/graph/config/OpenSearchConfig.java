// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/config/OpenSearchConfig.java (trimmed)
package org.com.graph.config;
import lombok.RequiredArgsConstructor;
import org.apache.hc.core5.http.HttpHost;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.transport.httpclient5.ApacheHttpClient5TransportBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
@Configuration
@RequiredArgsConstructor
public class OpenSearchConfig {
    private final OpenSearchProperties properties;
    @Bean
    public OpenSearchClient openSearchClient() {
        HttpHost host = new HttpHost("http", properties.getHost(), properties.getPort());
        return new OpenSearchClient(ApacheHttpClient5TransportBuilder.builder(host).build());
    }
}

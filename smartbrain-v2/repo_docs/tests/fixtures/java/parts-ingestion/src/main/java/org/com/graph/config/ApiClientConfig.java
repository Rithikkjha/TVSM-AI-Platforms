// source: TVS-CS/Parts-Catalogue-Ingestion-Service/src/main/java/org/com/graph/config/ApiClientConfig.java (trimmed)
package org.com.graph.config;
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.retry.Retry;
import lombok.RequiredArgsConstructor;
import org.com.graph.service.IngestionApiClientService;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;
import java.util.Map;
@Configuration
@RequiredArgsConstructor
public class ApiClientConfig {
    private final NortonCatalogueApiProperties nortonCatalogueApiProperties;
    private final PriceApiProperties priceApiProperties;
    private final MdpApiProperties mdpApiProperties;
    private static final String ACCEPT = "Accept";
    @Bean
    public RestClient nortonRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        RestClient.Builder builder = RestClient.builder()
                .baseUrl(nortonCatalogueApiProperties.getBaseUrl())
                .requestFactory(requestFactory)
                .defaultHeader(ACCEPT, "application/vnd.ptc.sc+json;version=2");
        String apiKey = nortonCatalogueApiProperties.getApiKey();
        if (apiKey != null && !apiKey.isBlank()) {
            builder.defaultHeader("Authorization", "Basic " + apiKey);
        }
        return builder.build();
    }
    @Bean
    public IngestionApiClientService nortonApiClientService(
            NortonCatalogueApiProperties nortonProperties,
            @Qualifier("nortonRestClient") RestClient nortonRestClient,
            @Qualifier("catalogueApiRetry") Retry retry,
            @Qualifier("catalogueApiCircuitBreaker") CircuitBreaker circuitBreaker) {
        return new IngestionApiClientService(circuitBreaker, retry, nortonProperties, nortonRestClient);
    }
    @Bean
    public RestClient priceRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        return RestClient.builder()
                .baseUrl(priceApiProperties.getBaseUrl())
                .requestFactory(requestFactory)
                .defaultHeader(ACCEPT, "application/json")
                .build();
    }
    @Bean
    public RestClient mdpRestClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        return RestClient.builder()
                .baseUrl(mdpApiProperties.getBaseUrl())
                .requestFactory(requestFactory)
                .defaultHeader(ACCEPT, "application/json")
                .requestInitializer(request ->
                    request.getHeaders().setBearerAuth(fetchOAuth2Token()))
                .build();
    }
    private String fetchOAuth2Token() {
        SimpleClientHttpRequestFactory tokenFactory = new SimpleClientHttpRequestFactory();
        RestClient tokenClient = RestClient.builder()
                .requestFactory(tokenFactory)
                .build();
        @SuppressWarnings("unchecked")
        Map<String, Object> tokenResponse = tokenClient.post()
                .uri(mdpApiProperties.getTokenUrl())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .body(String.format("grant_type=%s&client_id=%s&client_secret=%s&scope=%s",
                        mdpApiProperties.getGrantType(),
                        mdpApiProperties.getClientId(),
                        mdpApiProperties.getClientSecret(),
                        mdpApiProperties.getScope()))
                .retrieve()
                .body(Map.class);
        return (String) tokenResponse.get("access_token");
    }
}

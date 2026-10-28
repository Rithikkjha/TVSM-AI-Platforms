// source: TVS-CS/TVS-CPS-BACKEND/order-service/src/main/java/com/tvsm/order/config/Config.java (trimmed, moved to bff-service)
package com.tvsm.bff.config;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;
@Configuration
public class Config {
	@Value("${app.rest.timeout.connect:5000}")
	private int connectTimeout;
	@Bean
	@Primary
	public RestTemplate restTemplate() {
		SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
		factory.setConnectTimeout(Duration.ofMillis(connectTimeout));
		return new RestTemplate(factory);
	}
}

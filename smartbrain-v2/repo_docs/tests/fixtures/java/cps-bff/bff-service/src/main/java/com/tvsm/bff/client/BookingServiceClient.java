// source: TVS-CS/TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/client/BookingServiceClient.java (trimmed)
package com.tvsm.bff.client;
import com.tvsm.bff.constants.BookingServiceEndpoints;
import com.tvsm.bff.dto.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import java.util.Map;
@Component
public class BookingServiceClient {
    @Value("${bff.booking-service.base-url}")
    private String bookingBaseUrl;
    private WebClient buildClient(String accessToken, Map<String, String> additionalHeaders) {
        WebClient.Builder builder = WebClient.builder()
                .baseUrl(bookingBaseUrl+ BookingServiceEndpoints.BOOKING_SERVICE_BASE_PATH)
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken);
        return builder.build();
    }
    public String search(BookingSearchRequestDto request, String accessToken) {
        return buildClient(accessToken, null).post()
                .uri(BookingServiceEndpoints.BOOKING + BookingServiceEndpoints.BOOKING_SEARCH)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(String.class)
                .block();
    }
}

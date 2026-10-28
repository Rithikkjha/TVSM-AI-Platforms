// source: TVS-CS/TVS-CPS-BACKEND/bff-service/src/main/java/com/tvsm/bff/controller/InventoryAnalyticsBFFController.java (trimmed annotations)
package com.tvsm.bff.controller;
import com.tvsm.bff.constants.InventoryEndpoints;
import com.tvsm.bff.util.ApiPassthroughUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import java.util.Map;
@RestController
@RequestMapping("/system")
@RequiredArgsConstructor
public class InventoryAnalyticsBFFController {
    private final RestTemplate restTemplate;
    private final ApiPassthroughUtil apiPassthroughUtil;
    @Value("${bff.inventory-service.base-url}")
    private String inventoryServiceBaseUrl;
    @PostMapping(path = InventoryEndpoints.PRODUCT_CATALOG_COUNT_LIST)
    public ResponseEntity<Map<String, Object>> productCatalogCount(
            @RequestBody Map<String, Object> request,
            HttpServletRequest httpRequest) {
        HttpHeaders headers = new HttpHeaders();
        return apiPassthroughUtil.post(restTemplate, inventoryServiceBaseUrl, InventoryEndpoints.PRODUCT_CATALOG_COUNT_LIST, request, headers, "Fetches product catalog ID-based inventory counts");
    }
}

// source: TVS-CS/tvsmbe-qrcode/src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java (trimmed)
package com.tvsmotor.qrcode.controller;
import com.tvsmotor.qrcode.model.QrCode;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.Map;
@RestController
@RequestMapping("/api/analytics")
public class AnalyticsController {
    private final MongoTemplate mongoTemplate;
    public AnalyticsController(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }
    @GetMapping("/summary")
    public Map<String, Object> summary() {
        Query qrQuery = new Query();
        long totalQr = mongoTemplate.count(qrQuery, QrCode.class);
        long totalScans = mongoTemplate.count(new Query(), "qr_redirect_events");
        return Map.of("totalQr", totalQr, "totalScans", totalScans);
    }
}

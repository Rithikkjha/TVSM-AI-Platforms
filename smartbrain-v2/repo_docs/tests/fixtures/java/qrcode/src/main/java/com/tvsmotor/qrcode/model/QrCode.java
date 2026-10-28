// source: TVS-CS/tvsmbe-qrcode/src/main/java/com/tvsmotor/qrcode/model/QrCode.java (trimmed)
package com.tvsmotor.qrcode.model;
import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
@Data
@Document(collection = "qr_codes")
public class QrCode {
    @Id
    private String id;
    private String shortCode;
}

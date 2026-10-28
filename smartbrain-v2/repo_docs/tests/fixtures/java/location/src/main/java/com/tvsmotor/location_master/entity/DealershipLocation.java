// source: TVS-CS/tvsmbe-location/src/main/java/com/tvsmotor/location_master/entity/DealershipLocation.java (trimmed)
package com.tvsmotor.location_master.entity;
import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
@Data
@Document(collection = "dealership_location")
public class DealershipLocation {
    @Id
    private String id;
    private String dealerCode;
}

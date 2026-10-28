// source: TVS-CS/tvsmbe-location/src/main/java/com/tvsmotor/location_master/service/DealershipLocationService.java (trimmed)
package com.tvsmotor.location_master.service;
import com.tvsmotor.location_master.entity.DealershipLocation;
import lombok.RequiredArgsConstructor;
import org.springframework.data.mongodb.core.BulkOperations;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Service;
import java.util.List;
@Service
@RequiredArgsConstructor
public class DealershipLocationService {
    private final MongoTemplate mongoTemplate;
    public void bulkUpload(List<DealershipLocation> validDealershipLocations) {
        BulkOperations bulkOps = mongoTemplate.bulkOps(
                BulkOperations.BulkMode.UNORDERED,
                DealershipLocation.class);
        for (DealershipLocation dealershipLocation : validDealershipLocations) {
            Query query = Query.query(
                    Criteria.where("dealerCode").is(dealershipLocation.getDealerCode()));
            bulkOps.upsert(query, new org.springframework.data.mongodb.core.query.Update());
        }
        bulkOps.execute();
    }
    public List<DealershipLocation> byDealer(String dealerCode) {
        Query query = Query.query(Criteria.where("dealerCode").is(dealerCode));
        return mongoTemplate.find(query, DealershipLocation.class);
    }
}

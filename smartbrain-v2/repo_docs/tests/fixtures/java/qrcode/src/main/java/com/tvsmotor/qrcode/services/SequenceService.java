// source: TVS-CS/tvsmbe-qrcode/src/main/java/com/tvsmotor/qrcode/services/SequenceService.java (trimmed)
package com.tvsmotor.qrcode.services;
import org.bson.Document;
import org.springframework.data.mongodb.core.FindAndModifyOptions;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Service;
@Service
public class SequenceService {
    private final MongoTemplate mongoTemplate;
    public SequenceService(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }
    public long getNextSequence(String sequenceName) {
        Query query = new Query(Criteria.where("_id").is(sequenceName));
        Update update = new Update().inc("seq", 1);
        FindAndModifyOptions options = FindAndModifyOptions.options().returnNew(true).upsert(true);
        Document result = mongoTemplate.findAndModify(query, update, options, Document.class, "sequences");
        return result != null ? ((Number) result.get("seq")).longValue() : 1L;
    }
}

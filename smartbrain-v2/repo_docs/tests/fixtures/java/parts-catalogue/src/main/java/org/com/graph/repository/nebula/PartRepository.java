// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/repository/nebula/PartRepository.java (trimmed)
package org.com.graph.repository.nebula;
import com.vesoft.nebula.client.graph.data.ResultSet;
import com.vesoft.nebula.client.graph.net.NebulaPool;
import org.com.graph.config.NebulaGraphProperties;
import org.com.graph.model.Part;
import org.springframework.stereotype.Repository;
import java.util.List;
import static org.com.graph.constants.NebulaGraphConstants.*;
@Repository
public class PartRepository extends NebulaGraphRepository {
    public PartRepository(NebulaGraphProperties properties, NebulaPool nebulaPool) {
        super(properties, nebulaPool);
    }
    public List<Part> findByPartNumber(String partNumber) {
        String query = String.format(
                "MATCH (p:`%s`)" +
                " WHERE p.`%s`.part_number == \"%s\"" +
                " RETURN p",
                TAG_PART, TAG_PART, partNumber);
        return executeQuery(query, this::mapToPart);
    }
    private Part mapToPart(ResultSet.Record row, List<String> columnNames) {
        return new Part();
    }
}

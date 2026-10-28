// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/repository/opensearch/HierarchyDataRepository.java (trimmed)
package org.com.graph.repository.opensearch;
import org.com.graph.config.OpenSearchProperties;
import org.com.graph.model.HierarchyData;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.opensearch._types.FieldValue;
import org.opensearch.client.opensearch.core.SearchResponse;
import org.springframework.stereotype.Repository;
import java.io.IOException;
import java.util.List;
@Repository
public class HierarchyDataRepository extends OpenSearchRepository {
    public HierarchyDataRepository(OpenSearchClient client, OpenSearchProperties properties) {
        super(client, properties);
    }
    public List<HierarchyData> getHierarchiesByPartNumber(String partNumber) {
        try {
            SearchResponse<HierarchyData> hlResp = client.search(s -> s
                            .index(properties.getHierarchiesIndex())
                            .query(q -> q.bool(b -> b
                                    .must(m -> m.term(t -> t
                                            .field("part_number")
                                            .value(FieldValue.of(partNumber))
                                    ))
                            ))
                            .size(10_000)
                            .scroll(sc -> sc.time("1m")),
                    HierarchyData.class
            );
            return hlResp.hits().hits().stream().map(h -> h.source()).toList();
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
    }
}

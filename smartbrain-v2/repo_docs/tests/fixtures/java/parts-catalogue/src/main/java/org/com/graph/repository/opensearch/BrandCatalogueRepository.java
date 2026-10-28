// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/repository/opensearch/BrandCatalogueRepository.java (trimmed)
package org.com.graph.repository.opensearch;
import org.com.graph.config.OpenSearchProperties;
import org.com.graph.model.BrandCatalogue;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.opensearch.core.SearchResponse;
import org.springframework.stereotype.Repository;
import java.io.IOException;
@Repository
public class BrandCatalogueRepository extends OpenSearchRepository {
    public BrandCatalogueRepository(OpenSearchClient client, OpenSearchProperties properties) {
        super(client, properties);
    }
    public SearchResponse<BrandCatalogue> all() throws IOException {
        return execute(properties.getBrandCataloguesIndex(), 100, BrandCatalogue.class);
    }
}

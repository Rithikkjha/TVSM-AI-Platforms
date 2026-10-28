// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/repository/opensearch/OpenSearchRepository.java (trimmed)
package org.com.graph.repository.opensearch;
import lombok.RequiredArgsConstructor;
import org.com.graph.config.OpenSearchProperties;
import org.com.graph.dto.SearchResponseDto;
import org.com.graph.model.BaseModel;
import org.opensearch.client.opensearch.OpenSearchClient;
import org.opensearch.client.opensearch.core.SearchRequest;
import org.opensearch.client.opensearch.core.SearchResponse;
import org.opensearch.client.opensearch.core.search.Hit;
import java.io.IOException;
@RequiredArgsConstructor
public abstract class OpenSearchRepository {
    protected final OpenSearchClient client;
    protected final OpenSearchProperties properties;
    public SearchResponse<BaseModel> search(int size) {
        try {
            SearchRequest.Builder searchBuilder = new SearchRequest.Builder();
            searchBuilder.index(properties.getPartsIndex());
            searchBuilder.size(size);
            SearchResponse<BaseModel> response =
                    client.search(searchBuilder.build(), BaseModel.class);
            return response;
        } catch (IOException e) {
            throw new IllegalStateException("Search failed", e);
        }
    }
    public void deleteDocument(String id) {
        try {
            client.delete(d -> d
                    .index(properties.getPartsIndex())
                    .id(id)
            );
        } catch (IOException e) {
            throw new IllegalStateException("Failed to delete document: " + id, e);
        }
    }
    public <T extends BaseModel> SearchResponse<T> execute(String indexName, int size, Class<T> documentClass)
            throws IOException {
        SearchRequest searchRequest = SearchRequest.of(s -> {
            s.index(indexName).size(size);
            return s;
        });
        return client.search(searchRequest, documentClass);
    }
    private SearchResponseDto.SearchHit mapHit(Hit<BaseModel> hit) {
        return SearchResponseDto.SearchHit.builder()
                .id(hit.id())
                .index(hit.index())
                .build();
    }
}

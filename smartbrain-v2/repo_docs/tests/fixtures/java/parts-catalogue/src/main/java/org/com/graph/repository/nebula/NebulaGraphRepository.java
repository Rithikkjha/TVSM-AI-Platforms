// source: TVS-CS/Parts-Catalogue-Service/src/main/java/org/com/graph/repository/nebula/NebulaGraphRepository.java (trimmed)
package org.com.graph.repository.nebula;
import com.vesoft.nebula.client.graph.data.ResultSet;
import com.vesoft.nebula.client.graph.net.NebulaPool;
import com.vesoft.nebula.client.graph.net.Session;
import lombok.RequiredArgsConstructor;
import org.com.graph.config.NebulaGraphProperties;
import java.util.ArrayList;
import java.util.List;
@RequiredArgsConstructor
public abstract class NebulaGraphRepository {
    private final NebulaGraphProperties properties;
    private final NebulaPool nebulaPool;
    public boolean isConnected() {
        ResultSet result = execute("YIELD 1");
        return result.isSucceeded();
    }
    protected <T> List<T> executeQuery(String query, RowMapper<T> mapper) {
        ResultSet result = execute(query);
        List<T> results = new ArrayList<>();
        for (int i = 0; i < result.rowsSize(); i++) {
            results.add(mapper.map(result.rowValues(i), result.getColumnNames()));
        }
        return results;
    }
    protected ResultSet execute(String query) {
        Session session = null;
        try {
            session = nebulaPool.getSession(
                    properties.getUsername(),
                    properties.getPassword(),
                    properties.isReconnect()
            );
            String useSpaceQuery = "USE " + properties.getSpace() + ";";
            ResultSet useResult = session.execute(useSpaceQuery);
            ResultSet result = session.execute(query);
            return result;
        } catch (Exception e) {
            throw new IllegalStateException("Failed to execute query: " + e.getMessage(), e);
        } finally {
            if (session != null) {
                session.release();
            }
        }
    }
    @FunctionalInterface
    protected interface RowMapper<T> {
        T map(ResultSet.Record row, List<String> columnNames);
    }
}

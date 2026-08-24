#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Import seed data into local Neo4j and Qdrant instances.
# Run this after `docker compose up -d` to populate the graph without
# running the full ingestion pipeline.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEO4J_URI="bolt://localhost:7687"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="neo4jpassword"
QDRANT_URL="http://localhost:6333"
COLLECTION="memory_graph_entities"

echo "=== Engineering Memory Graph — Seed Import ==="
echo ""

# ---------------------------------------------------------------------------
# 1. Wait for services
# ---------------------------------------------------------------------------
echo "[1/4] Waiting for Neo4j to be ready..."
for i in $(seq 1 30); do
    if docker exec emg-neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null 2>&1; then
        echo "  ✓ Neo4j is ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  ✗ Neo4j did not become ready in time. Is 'docker compose up -d' running?"
        exit 1
    fi
    sleep 2
done

echo "[2/4] Waiting for Qdrant to be ready..."
for i in $(seq 1 20); do
    if curl -s "$QDRANT_URL/collections" >/dev/null 2>&1; then
        echo "  ✓ Qdrant is ready"
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "  ✗ Qdrant did not become ready in time."
        exit 1
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# 2. Import Neo4j data
# ---------------------------------------------------------------------------
echo "[3/4] Importing Neo4j graph data..."

CYPHER_FILE="$SCRIPT_DIR/neo4j-seed.cypher"
CYPHER_GZ="$SCRIPT_DIR/neo4j-seed.cypher.gz"

if [ ! -f "$CYPHER_FILE" ] && [ -f "$CYPHER_GZ" ]; then
    echo "  Decompressing neo4j-seed.cypher.gz..."
    gunzip -k "$CYPHER_GZ"
fi

if [ ! -f "$CYPHER_FILE" ]; then
    echo "  ✗ neo4j-seed.cypher not found in $SCRIPT_DIR"
    exit 1
fi

# The seed file may be in APOC streamed format (has a "cypherStatements"
# header, outer quotes, and escaped \" inside). Normalize it to plain
# cypher that cypher-shell can execute.
CLEAN_FILE="$SCRIPT_DIR/.neo4j-seed-clean.cypher"
if head -1 "$CYPHER_FILE" | grep -q '^cypherStatements'; then
    echo "  Detected APOC streamed format, normalizing..."
    tail -n +2 "$CYPHER_FILE" | sed 's/^"//; s/"$//' | sed 's/\\"/"/g' > "$CLEAN_FILE"
else
    cp "$CYPHER_FILE" "$CLEAN_FILE"
fi

# Copy into container and run via cypher-shell
docker cp "$CLEAN_FILE" emg-neo4j:/var/lib/neo4j/import/seed.cypher
rm -f "$CLEAN_FILE"

# Run the import
docker exec emg-neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" \
    --file /var/lib/neo4j/import/seed.cypher \
    --format plain 2>&1 | tail -3

echo "  ✓ Neo4j import complete"

# ---------------------------------------------------------------------------
# 3. Import Qdrant data
# ---------------------------------------------------------------------------
echo "[4/4] Importing Qdrant vector data..."

SNAPSHOT_FILE="$SCRIPT_DIR/qdrant-snapshot.snapshot"
SNAPSHOT_GZ="$SCRIPT_DIR/qdrant-snapshot.snapshot.gz"

if [ ! -f "$SNAPSHOT_FILE" ] && [ -f "$SNAPSHOT_GZ" ]; then
    echo "  Decompressing qdrant-snapshot.snapshot.gz..."
    gunzip -k "$SNAPSHOT_GZ"
fi

if [ ! -f "$SNAPSHOT_FILE" ]; then
    echo "  ✗ qdrant-snapshot.snapshot not found in $SCRIPT_DIR"
    exit 1
fi

# Delete existing collection if present (snapshot restore requires it)
echo "  Dropping existing collection (if any)..."
curl -s -X DELETE "$QDRANT_URL/collections/$COLLECTION" >/dev/null 2>&1 || true

# Upload snapshot to restore
echo "  Uploading snapshot (this may take a minute)..."
RESTORE_RESULT=$(curl -s -X POST "$QDRANT_URL/collections/$COLLECTION/snapshots/upload" \
    -H "Content-Type: multipart/form-data" \
    -F "snapshot=@$SNAPSHOT_FILE")

if echo "$RESTORE_RESULT" | grep -q '"status":"ok"'; then
    echo "  ✓ Qdrant import complete"
else
    echo "  ✗ Qdrant import failed:"
    echo "$RESTORE_RESULT"
    exit 1
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=== Import complete! ==="
echo ""
echo "Services:"
echo "  API:           http://localhost:8000"
echo "  Chatbot UI:    http://localhost:8000/ui/"
echo "  Neo4j Browser: http://localhost:7474"
echo "  Qdrant:        http://localhost:6333/dashboard"
echo ""
echo "API Key: dev-api-key"

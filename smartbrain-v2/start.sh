#!/bin/bash
# SmartBrain V2 — Unified Startup Script
# Usage:
#   ./start.sh              → Start everything (infra + services)
#   ./start.sh infra        → Only Neo4j + Qdrant
#   ./start.sh mcp          → Only MCP server
#   ./start.sh api          → Only REST API
#   ./start.sh ingest       → Run ingestion pipeline
#   ./start.sh chatbot      → Start chatbot UI
#   ./start.sh bench        → Run benchmark suite
#   ./start.sh webhook      → Start Steering Webhook server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_NC='\033[0m'

log() { echo -e "${COLOR_GREEN}[SmartBrain]${COLOR_NC} $1"; }
info() { echo -e "${COLOR_BLUE}[Info]${COLOR_NC} $1"; }

start_infra() {
    log "Starting infrastructure (Neo4j + Qdrant)..."
    docker compose up -d neo4j qdrant
    log "Waiting for Neo4j to be ready..."
    until docker compose exec neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-neo4jpassword}" "RETURN 1" > /dev/null 2>&1; do
        sleep 2
    done
    log "Infrastructure ready ✓"
}

start_mcp() {
    log "Starting MCP Server..."
    python -m mcp_server.server
}

start_api() {
    log "Starting REST API..."
    uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
}

run_ingest() {
    log "Running ingestion pipeline..."
    python -m ingestion.run_sync
}

start_chatbot() {
    log "Starting Chatbot UI..."
    cd ui && python -m http.server 3000
}

run_bench() {
    log "Running benchmark suite..."
    cd steering-lite && python -m bench.run_bench
}

start_webhook() {
    log "Starting Steering Webhook Server..."
    uvicorn webhook_pipeline.app:app --host 0.0.0.0 --port 8002 --reload
}

case "${1:-all}" in
    infra)
        start_infra
        ;;
    mcp)
        start_mcp
        ;;
    api)
        start_api
        ;;
    ingest)
        run_ingest
        ;;
    chatbot)
        start_chatbot
        ;;
    bench)
        run_bench
        ;;
    webhook)
        start_webhook
        ;;
    all)
        start_infra
        log "Starting all services..."
        start_api &
        start_mcp &
        info "API running on http://localhost:8000"
        info "MCP server running on stdio"
        wait
        ;;
    *)
        echo "Usage: ./start.sh [infra|mcp|api|ingest|chatbot|bench|webhook|all]"
        exit 1
        ;;
esac

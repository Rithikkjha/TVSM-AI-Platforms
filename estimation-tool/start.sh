#!/bin/bash
set -e

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    sleep 2
done

# Pull the model if not already available
echo "Ensuring gemma3:4b model is available..."
if ! ollama list | grep -q "gemma3:4b"; then
    echo "Pulling gemma3:4b model (this may take a while on first run)..."
    ollama pull gemma3:4b
fi

echo "Model ready. Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

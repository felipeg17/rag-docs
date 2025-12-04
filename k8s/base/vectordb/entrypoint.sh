#!/bin/sh

# Start ChromaDB in background using its default command
chroma run --path /chroma/chroma --host 0.0.0.0 --port 8000 &
CHROMA_PID=$!

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB..."
until curl -s http://localhost:8000/api/v2/heartbeat > /dev/null; do
  sleep 1
done
echo "ChromaDB ready!"

# Initialize tenant and database
# Create tenant
curl -X POST http://localhost:8000/api/v2/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "dev"}'

# Create database
curl -X POST http://localhost:8000/api/v2/tenants/dev/databases \
  -H "Content-Type: application/json" \
  -d '{"name": "rag-database"}'

echo "ChromaDB initialized!"

# Keep ChromaDB running in foreground
wait $CHROMA_PID

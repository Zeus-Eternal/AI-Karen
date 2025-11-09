#!/bin/bash

echo "🔄 Restarting AI-Karen API with resource limits..."

# Stop the API service
echo "🛑 Stopping ai-karen-api service..."
docker compose stop api

# Remove the container to ensure clean restart
echo "🗑️ Removing old container..."
docker compose rm -f api

# Start the API service with new configuration
echo "🚀 Starting ai-karen-api with resource limits..."
docker compose up -d api

# Wait a moment for startup
sleep 5

# Check the new resource usage
echo "📊 New resource usage:"
docker stats --no-stream ai-karen-api

echo "✅ API service restarted with resource limits!"
echo "💡 Monitor with: docker stats ai-karen-api"
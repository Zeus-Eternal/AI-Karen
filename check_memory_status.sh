#!/bin/bash

echo "🔍 Checking AI-Karen API memory status..."

# Check if API is responding
echo "📡 Testing API health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding"
    exit 1
fi

# Check current Docker stats
echo ""
echo "📊 Current resource usage:"
docker stats --no-stream ai-karen-api

# Check if there are any resource warnings in logs
echo ""
echo "🚨 Recent resource warnings (last 50 lines):"
docker logs ai-karen-api --tail 50 | grep -i "resource\|memory\|cpu" | tail -10

echo ""
echo "✅ Memory status check complete!"
echo "💡 The API is now limited to 2GB RAM and 1 CPU core"
echo "💡 Monitor continuously with: docker stats ai-karen-api"
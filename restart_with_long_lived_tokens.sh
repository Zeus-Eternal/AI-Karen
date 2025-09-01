#!/bin/bash

echo "🔄 Restarting AI Karen Backend with Long-Lived Token Support"
echo "============================================================"

# Set environment variables for long-lived tokens
export LONG_LIVED_TOKEN_EXPIRE_HOURS=24
export ENABLE_LONG_LIVED_TOKENS=true

echo "✅ Environment variables set:"
echo "   LONG_LIVED_TOKEN_EXPIRE_HOURS=$LONG_LIVED_TOKEN_EXPIRE_HOURS"
echo "   ENABLE_LONG_LIVED_TOKENS=$ENABLE_LONG_LIVED_TOKENS"

# Kill existing server if running
echo ""
echo "🛑 Stopping existing server..."
pkill -f "python.*main.py" || echo "   No existing server found"

# Wait a moment for cleanup
sleep 2

# Start the server
echo ""
echo "🚀 Starting server with long-lived token support..."
python main.py &

# Get the PID
SERVER_PID=$!
echo "   Server started with PID: $SERVER_PID"

# Wait a moment for server to start
sleep 3

# Test if server is running
echo ""
echo "🧪 Testing server health..."
if curl -s http://127.0.0.1:8000/api/health > /dev/null; then
    echo "✅ Server is running and healthy!"
    echo ""
    echo "🎯 You can now test long-lived tokens:"
    echo "   1. Run: python test_long_lived_token.py"
    echo "   2. Or use the frontend TokenStatus component"
    echo ""
    echo "📝 Server logs will appear below:"
    echo "============================================================"
    
    # Follow the logs
    wait $SERVER_PID
else
    echo "❌ Server health check failed"
    echo "   Please check the server logs for errors"
fi
#!/bin/bash

echo "🔄 Restarting AI Karen server with updated rate limiting configuration..."

# Kill any existing server processes
echo "Stopping existing server processes..."
pkill -f "python.*main.py" || true
pkill -f "uvicorn.*main:app" || true

# Wait a moment for processes to stop
sleep 2

echo "Starting server with new configuration..."

# Start the server
python main.py &

echo "✅ Server restarted with updated rate limiting configuration"
echo "📊 New rate limits:"
echo "  - General rate limit: 300 requests/minute"
echo "  - Auth rate limit: 200 requests/minute"
echo "  - Max failed attempts: 50"
echo "  - Lockout duration: 2 minutes"
echo "  - Exponential backoff: 50 attempts/minute"
echo ""
echo "🌐 Server should be available at http://127.0.0.1:8000"
echo "🔍 Check logs for any issues"
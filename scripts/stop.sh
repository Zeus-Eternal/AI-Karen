#!/bin/bash

# AI Karen Backend Stop Script
# This script stops any running backend servers

echo "🛑 Stopping AI Karen Backend Server..."

# Find and kill uvicorn processes
PIDS=$(ps aux | grep "uvicorn main:create_app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "ℹ️  No backend server processes found running"
else
    echo "🔍 Found backend server processes: $PIDS"
    for PID in $PIDS; do
        echo "🛑 Stopping process $PID..."
        kill $PID
        sleep 1
        
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo "⚡ Force stopping process $PID..."
            kill -9 $PID
        fi
    done
    echo "✅ Backend server stopped"
fi

# Check if port 8000 is still in use
if lsof -i :8000 >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is still in use by another process"
    echo "🔍 Processes using port 8000:"
    lsof -i :8000
else
    echo "✅ Port 8000 is now free"
fi
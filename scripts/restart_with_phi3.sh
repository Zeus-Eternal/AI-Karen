#!/bin/bash

echo "🔧 Restarting AI-Karen with Phi-3 model..."
echo "This should fix the degraded mode issue."
echo

# Kill any existing backend processes
echo "Stopping existing backend processes..."
pkill -f "python.*start" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 3

# Clear any cached model states
echo "Clearing model cache..."
rm -rf __pycache__ 2>/dev/null || true
rm -rf src/**/__pycache__ 2>/dev/null || true

# Start the backend with the new configuration
echo "Starting backend with Phi-3 configuration..."
echo "This may take a moment to load the model..."
echo

# Check if start.py exists
if [ -f "start.py" ]; then
    python3 start.py
elif [ -f "src/start.py" ]; then
    python3 src/start.py
else
    echo "❌ Could not find start.py"
    echo "Please run manually: python3 start.py"
    exit 1
fi
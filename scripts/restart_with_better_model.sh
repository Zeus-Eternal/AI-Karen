#!/bin/bash
"""
Restart Backend with Better Model Configuration

This script restarts the backend to use Phi-3 instead of TinyLlama
for much more intelligent responses.
"""

echo "🔄 Restarting backend with upgraded model configuration..."
echo

# Find and kill existing backend processes
echo "1. Stopping existing backend processes..."
pkill -f "start.py" 2>/dev/null || true
pkill -f "start_optimized.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 2

# Check if processes are stopped
if pgrep -f "start.py\|start_optimized.py\|uvicorn" > /dev/null; then
    echo "⚠️  Some processes still running, force killing..."
    pkill -9 -f "start.py" 2>/dev/null || true
    pkill -9 -f "start_optimized.py" 2>/dev/null || true
    pkill -9 -f "uvicorn" 2>/dev/null || true
    sleep 2
fi

echo "✅ Backend processes stopped"
echo

# Start backend with new configuration
echo "2. Starting backend with Phi-3 model..."
echo "   Model: Phi-3-mini-4k-instruct-q4.gguf (2.3GB)"
echo "   This model is ~40x larger than TinyLlama and much more capable"
echo

# Use the optimized start script if available
if [ -f "start_optimized.py" ]; then
    echo "🚀 Starting optimized backend..."
    python3 start_optimized.py &
elif [ -f "start.py" ]; then
    echo "🚀 Starting standard backend..."
    python3 start.py &
else
    echo "❌ No start script found"
    exit 1
fi

# Wait a moment for startup
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully with Phi-3 model!"
    echo
    echo "🧪 Test the improvement:"
    echo "1. Open your chat interface"
    echo "2. Try: 'Explain the difference between Python lists and tuples'"
    echo "3. You should get a detailed, intelligent response"
    echo
    echo "📊 Model Comparison:"
    echo "   TinyLlama: 1.1B parameters (poor responses)"
    echo "   Phi-3-mini: 3.8B parameters (intelligent responses)"
    echo
    echo "🎉 Your AI should now give much better responses!"
else
    echo "❌ Backend failed to start. Check logs for errors."
    echo "Try running manually: python3 start_optimized.py"
fi
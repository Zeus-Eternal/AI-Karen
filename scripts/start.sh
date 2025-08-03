#!/bin/bash

# AI Karen Backend Startup Script
# This script starts the FastAPI backend server properly

set -e  # Exit on any error

echo "🚀 AI Karen Backend Startup"
echo "=========================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found! Please run this script from the project root."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".env_ai" ]; then
    echo "❌ Virtual environment .env_ai not found!"
    echo "Create it with: python -m venv .env_ai"
    echo "Then activate and install dependencies:"
    echo "source .env_ai/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .env_ai/bin/activate

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ Uvicorn not found! Installing..."
    pip install uvicorn
fi

# Start the server
echo "🚀 Starting FastAPI server..."
echo "📍 Backend will be available at:"
echo "   - http://localhost:8000"
echo "   - http://127.0.0.1:8000"
echo "   - http://0.0.0.0:8000"
echo ""
echo "🌐 CORS configured for:"
echo "   - http://localhost:9002 (Web UI)"
echo "   - http://127.0.0.1:9002 (Web UI)"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo "=================================="

# Start uvicorn with proper configuration
exec uvicorn main:create_app \
    --factory \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log

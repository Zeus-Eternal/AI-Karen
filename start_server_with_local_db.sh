#!/bin/bash

# AI Karen Server Startup Script with Local Database Configuration
# This script starts the AI Karen backend with proper environment variables for local development

echo "🚀 Starting AI Karen Backend Server with Local Database"
echo "=" * 60

# Set database environment variables for local development
export POSTGRES_URL="postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"
export DATABASE_URL="postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"

# Set Redis URL for local development
export REDIS_URL="redis://:redis_secure_pass_change_me@localhost:6379/0"

# Set other environment variables for local development
export KAREN_BACKEND_URL="http://localhost:8000"
export KAREN_WEB_UI_URL="http://localhost:8010"
export KAREN_EXTERNAL_HOST="localhost"
export KAREN_EXTERNAL_BACKEND_PORT="8000"
export KAREN_CORS_ORIGINS="http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000"

# Development settings
export ENVIRONMENT="development"
export DEBUG_LOGGING="true"
export DEV_MODE="true"

echo "🔗 Database URL: $POSTGRES_URL"
echo "🌐 Backend URL: $KAREN_BACKEND_URL"
echo "🎯 CORS Origins: $KAREN_CORS_ORIGINS"
echo ""

# Start the server
echo "🏃 Starting server on 0.0.0.0:8000..."
python main.py --host 0.0.0.0 --port 8000
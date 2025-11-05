#!/bin/bash

echo "🔧 AI Karen Development Environment Fix"
echo "======================================"

# Stop all existing processes
echo "🛑 Stopping existing development servers..."
sudo pkill -f "next dev" 2>/dev/null || true
sudo pkill -f "node.*next" 2>/dev/null || true
sleep 3

# Clean up problematic files
echo "🧹 Cleaning up build artifacts..."
rm -rf .next/static/chunks/app/chat/page.js 2>/dev/null || true
rm -rf .next/cache 2>/dev/null || true
rm -rf .next/server 2>/dev/null || true
rm -rf node_modules/.cache 2>/dev/null || true

# Set environment variables
echo "🔧 Setting up environment variables..."
export NODE_ENV=development
export NEXT_PUBLIC_NODE_ENV=development

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "⚠️  .env.local not found, creating one..."
    cat > .env.local << 'EOF'
NODE_ENV=development
NEXT_PUBLIC_NODE_ENV=development
KAREN_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_KAREN_BACKEND_URL=http://localhost:8000
DEBUG_AUTH=true
NEXT_PUBLIC_DEBUG_AUTH=true
SIMPLE_AUTH_ENABLED=true
NEXT_PUBLIC_SIMPLE_AUTH_ENABLED=true
NEXT_TELEMETRY_DISABLED=1
EOF
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check for common issues
echo "🔍 Checking for common issues..."

# Check if port 8010 is available
if lsof -Pi :8010 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8010 is in use. Attempting to free it..."
    sudo lsof -ti:8010 | xargs sudo kill -9 2>/dev/null || true
    sleep 2
fi

# Check if port 8000 (backend) is available
if ! nc -z localhost 8000 2>/dev/null; then
    echo "⚠️  Backend not running on port 8000. Starting development mode without backend..."
    echo "   You can start the backend separately or use dev-login for testing."
fi

echo "✅ Environment setup complete!"
echo ""
echo "🚀 Starting development server..."
echo "   Frontend: http://localhost:8010"
echo "   Dev Status: http://localhost:8010/api/dev-status"
echo "   Dev Login: http://localhost:8010/api/auth/dev-login"
echo ""

# Start the development server
npm run dev:8010
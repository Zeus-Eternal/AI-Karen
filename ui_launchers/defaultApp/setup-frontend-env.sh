#!/bin/bash
# Frontend Environment Setup Script
# This script creates the .env.local file for the frontend

cd "$(dirname "$0")"

echo "🔧 Setting up frontend environment configuration..."
echo ""

# Create .env.local file
cat > .env.local << 'ENVEOF'
# Backend API Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Optional: Enable debug mode for development
# NEXT_PUBLIC_DEBUG=true

# Optional: API Key if your backend requires authentication
# You'll need to obtain this from the backend after logging in
# NEXT_PUBLIC_API_KEY=your_api_key_here
ENVEOF

echo "✅ Created .env.local file"
echo ""
echo "📄 Configuration:"
cat .env.local
echo ""
echo "🔄 Next steps:"
echo "1. Rebuild the frontend: npm run build"
echo "2. Restart the frontend server"
echo "3. Test the integration"
echo ""
echo "⚠️  Note: The backend requires authentication. You may need to:"
echo "   - Log into the backend first to get an API key"
echo "   - Update NEXT_PUBLIC_API_KEY in .env.local"
echo "   - Or implement OAuth/login flow in the frontend"

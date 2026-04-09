#!/bin/bash

# Restart Karen AI services after configuration update
echo "🔄 Restarting Karen AI services..."

# Stop current services
echo "Stopping existing services..."
docker-compose down 2>/dev/null || true

# Clean up any orphaned containers
echo "Cleaning up..."
docker system prune -f 2>/dev/null || true

# Start services again
echo "Starting services..."
docker-compose up -d

echo "✅ Services restarted. Frontend should now connect to backend correctly."
echo ""
echo "🧪 Test the profile update again:"
echo "   1. Open the frontend at http://localhost:3000"
echo "   2. Login with admin@karen.ai / admin123"
echo "   3. Try updating your profile in Account settings"
echo ""
echo "💡 If issues persist, check that both containers are running:"
echo "   docker ps | grep karen"
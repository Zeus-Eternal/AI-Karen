#!/bin/bash

echo "📊 AI-Karen System Status Check"
echo "==============================="

echo "🐳 Docker Status:"
docker --version
docker compose --version
echo ""

echo "📦 Container Status:"
docker compose ps
echo ""

echo "🔌 Port Status:"
echo "Checking critical ports..."
ss -ltn | grep -E ':(5433|6380|8000|8020|3000)' || echo "No services listening on expected ports"
echo ""

echo "🌐 Network Connectivity:"
echo "Testing localhost connectivity..."
curl -s -I http://localhost:8000/health || echo "❌ Backend not accessible"
curl -s -I http://localhost:8020 || echo "❌ Frontend not accessible"
echo ""

echo "📁 File Status:"
echo ".env file: $([ -f .env ] && echo "✅ Exists" || echo "❌ Missing")"
echo "docker-compose.yml: $([ -f docker-compose.yml ] && echo "✅ Exists" || echo "❌ Missing")"
echo ""

echo "🔧 Environment Variables:"
if [ -f .env ]; then
    echo "Key variables from .env:"
    grep -E "(POSTGRES_|REDIS_|KAREN_)" .env | head -10
else
    echo "❌ No .env file found"
fi
echo ""

echo "📋 Recent Logs:"
echo "API logs (last 5 lines):"
docker compose logs api --tail=5 2>/dev/null || echo "No API logs"
echo ""

echo "🎯 Quick Fix Commands:"
echo "1. Emergency fix: ./emergency-backend-fix.sh"
echo "2. Full diagnosis: ./diagnose-and-fix-backend.sh"
echo "3. Manual restart: docker compose down && docker compose up -d"
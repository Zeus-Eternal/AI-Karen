#!/bin/bash

echo "🛑 Stopping any existing development servers..."
sudo pkill -f "next dev" || true
sudo pkill -f "node.*next" || true
sleep 2

echo "🔧 Cleaning up build artifacts..."
rm -rf .next/static/chunks/app/chat/page.js 2>/dev/null || true
rm -rf .next/cache 2>/dev/null || true
rm -rf node_modules/.cache 2>/dev/null || true

echo "📦 Installing dependencies..."
npm install

echo "🔧 Setting up environment..."
export NODE_ENV=development
export NEXT_PUBLIC_NODE_ENV=development

echo "🚀 Starting development server on port 8010..."
npm run dev:8010
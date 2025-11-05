#!/bin/bash

echo "🚨 Emergency Fix for Next.js Chunk Loading Error"
echo "================================================"

# Step 1: Kill all Next.js processes
echo "🛑 Stopping all Next.js processes..."
sudo pkill -f "next dev" 2>/dev/null || true
sudo pkill -f "node.*next" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true

# Wait for processes to stop
sleep 3

# Step 2: Force remove .next directory
echo "🗑️  Force removing .next directory..."
sudo rm -rf .next 2>/dev/null || true
rm -rf .next 2>/dev/null || true

# Step 3: Clear node_modules cache
echo "🧹 Clearing node_modules cache..."
rm -rf node_modules/.cache 2>/dev/null || true

# Step 4: Clear npm cache
echo "🧹 Clearing npm cache..."
npm cache clean --force 2>/dev/null || true

# Step 5: Reinstall dependencies
echo "📦 Reinstalling dependencies..."
npm install

# Step 6: Build the application first
echo "🔨 Building application..."
npm run build

# Step 7: Start development server
echo "🚀 Starting development server..."
npm run dev:8010
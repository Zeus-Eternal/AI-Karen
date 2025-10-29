#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔧 Fixing chunk loading issues...');

// Clear Next.js cache
const nextDir = path.join(__dirname, '.next');
if (fs.existsSync(nextDir)) {
  console.log('📁 Clearing .next directory...');
  try {
    fs.rmSync(nextDir, { recursive: true, force: true });
  } catch (error) {
    console.log('⚠️  Could not remove .next directory, trying alternative method...');
    try {
      const { execSync } = require('child_process');
      execSync(`rm -rf "${nextDir}"`, { stdio: 'inherit' });
    } catch (e) {
      console.log('⚠️  Please manually delete the .next directory and restart');
    }
  }
}

// Clear node_modules/.cache if it exists
const cacheDir = path.join(__dirname, 'node_modules', '.cache');
if (fs.existsSync(cacheDir)) {
  console.log('📁 Clearing node_modules/.cache...');
  fs.rmSync(cacheDir, { recursive: true, force: true });
}

console.log('✅ Cache cleared successfully!');
console.log('🚀 Please restart your development server with: npm run dev:8010');
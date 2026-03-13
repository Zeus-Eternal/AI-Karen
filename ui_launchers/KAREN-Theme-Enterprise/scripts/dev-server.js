#!/usr/bin/env node

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Starting Karen AI Development Server');
console.log('=====================================');

// Ensure clean state
const nextDir = path.join(__dirname, '.next');
if (fs.existsSync(nextDir)) {
  console.log('🧹 Cleaning previous build...');
  fs.rmSync(nextDir, { recursive: true, force: true });
}

// Start Next.js development server with proper configuration
const nextProcess = spawn('npx', ['next', 'dev', '-p', '8000'], {
  stdio: 'inherit',
  cwd: __dirname,
  env: {
    ...process.env,
    NODE_ENV: 'development',
    NEXT_TELEMETRY_DISABLED: '1',
    // Disable webpack cache to prevent chunk issues
    NEXT_WEBPACK_USEFILEYSTEMCACHE: 'false',
  }
});

nextProcess.on('error', (error) => {
  console.error('❌ Failed to start development server:', error);
  process.exit(1);
});

nextProcess.on('exit', (code) => {
  console.log(`🛑 Development server exited with code ${code}`);
  process.exit(code);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down development server...');
  nextProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down development server...');
  nextProcess.kill('SIGTERM');
});
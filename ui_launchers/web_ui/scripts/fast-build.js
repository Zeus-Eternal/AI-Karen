#!/usr/bin/env node

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Starting fast build process...');

// Set environment variables for faster build
process.env.NODE_ENV = 'production';
process.env.NEXT_TELEMETRY_DISABLED = '1';
process.env.DISABLE_ESLINT_PLUGIN = 'true';

// Clear .next directory for clean build
const nextDir = path.join(__dirname, '..', '.next');
if (fs.existsSync(nextDir)) {
  console.log('🧹 Cleaning .next directory...');
  try {
    fs.rmSync(nextDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
  } catch (error) {
    console.log('⚠️  Could not clean .next directory, continuing anyway...');
  }
}

// Run Next.js build with optimizations
const buildProcess = spawn('npx', ['next', 'build'], {
  stdio: 'inherit',
  env: {
    ...process.env,
    // Disable source maps
    GENERATE_SOURCEMAP: 'false',
    // Use SWC minifier (faster)
    NEXT_PRIVATE_STANDALONE: 'true',
    // Disable telemetry
    NEXT_TELEMETRY_DISABLED: '1',
    // Skip type checking (we disabled it in config)
    SKIP_TYPE_CHECK: 'true',
    // Skip ESLint (we disabled it in config)
    SKIP_LINT: 'true'
  }
});

buildProcess.on('close', (code) => {
  if (code === 0) {
    console.log('✅ Fast build completed successfully!');
  } else {
    console.error('❌ Build failed with code:', code);
    process.exit(code);
  }
});

buildProcess.on('error', (error) => {
  console.error('❌ Build process error:', error);
  process.exit(1);
});
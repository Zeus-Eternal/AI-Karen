#!/usr/bin/env node

const http = require('http');

async function checkBackendHealth() {
  // Prioritize NEXT_PUBLIC_KAREN_BACKEND_URL for client-side compatibility
  const BACKEND_URL = process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
  const HEALTH_ENDPOINT = `${BACKEND_URL}/health`;
  
  console.log(`🔍 Checking backend health at: ${HEALTH_ENDPOINT}`);
  
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error('Timeout waiting for backend'));
    }, 10000); // 10 second timeout
    
    const url = new URL(HEALTH_ENDPOINT);
    const options = {
      hostname: url.hostname,
      port: url.port || 8000,
      path: url.pathname,
      method: 'GET',
      timeout: 5000
    };
    
    const req = http.request(options, (res) => {
      clearTimeout(timeout);
      
      if (res.statusCode === 200) {
        console.log('✅ Backend is ready!');
        resolve(true);
      } else {
        reject(new Error(`Backend returned status ${res.statusCode}`));
      }
    });
    
    req.on('error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });
    
    req.on('timeout', () => {
      clearTimeout(timeout);
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    req.end();
  });
}

async function main() {
  try {
    await checkBackendHealth();
    console.log('🚀 Starting Next.js development server...');
    process.exit(0);
  } catch (error) {
    console.error('❌ Backend preflight check failed:', error.message);
    console.error('');
    console.error('The backend API is not reachable. Please ensure:');
    console.error('1. The backend service is running');
    console.error('2. The backend is healthy at http://api:8000/api/health');
    console.error('3. Docker services are started with: docker compose up -d');
    console.error('');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

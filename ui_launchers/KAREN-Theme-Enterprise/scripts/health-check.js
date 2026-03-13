#!/usr/bin/env node

const http = require('http');
const fs = require('fs');
const path = require('path');

console.log('🏥 Karen AI Health Check');
console.log('========================');

// Check if development server is running
function checkServer(port) {
  return new Promise((resolve) => {
    const req = http.get(`http://localhost:${port}/`, (res) => {
      resolve({ status: res.statusCode, running: true });
    });
    
    req.on('error', () => {
      resolve({ running: false });
    });
    
    req.setTimeout(5000, () => {
      req.destroy();
      resolve({ running: false, timeout: true });
    });
  });
}

// Check if chunk files exist
function checkChunks() {
  const chunkDir = path.join(__dirname, '.next', 'static', 'chunks', 'app', 'chat');
  const requiredChunks = ['page.js', 'loading.js', 'error.js'];
  
  const results = {};
  for (const chunk of requiredChunks) {
    const chunkPath = path.join(chunkDir, chunk);
    results[chunk] = fs.existsSync(chunkPath);
  }
  
  return results;
}

async function runHealthCheck() {
  console.log('🔍 Checking development server...');
  const serverStatus = await checkServer(8010);
  
  if (serverStatus.running) {
    console.log(`✅ Development server is running (HTTP ${serverStatus.status})`);
  } else if (serverStatus.timeout) {
    console.log('⚠️  Development server timeout');
  } else {
    console.log('❌ Development server is not running');
  }
  
  console.log('\n🔍 Checking chunk files...');
  const chunks = checkChunks();
  
  for (const [chunk, exists] of Object.entries(chunks)) {
    if (exists) {
      console.log(`✅ ${chunk} exists`);
    } else {
      console.log(`❌ ${chunk} missing`);
    }
  }
  
  console.log('\n📊 Health Check Summary:');
  const allChunksExist = Object.values(chunks).every(exists => exists);
  
  if (serverStatus.running && allChunksExist) {
    console.log('🎉 All systems operational!');
    console.log('🌐 Visit: http://localhost:8010/chat');
  } else {
    console.log('⚠️  Some issues detected. Try running the emergency fix script.');
  }
}

runHealthCheck().catch(console.error);
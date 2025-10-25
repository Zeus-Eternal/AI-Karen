#!/usr/bin/env node

const http = require('http');
const https = require('https');

async function testWebContainer() {
  console.log('🔍 SIMPLE WEB CONTAINER AUDIT');
  console.log('=============================\n');

  const results = [];
  
  // Test server availability
  console.log('📡 Testing server availability...');
  try {
    const response = await makeRequest('http://localhost:8000');
    console.log(`✅ Server responding: ${response.status}`);
    results.push({ test: 'Server Availability', status: 'PASS', message: `HTTP ${response.status}` });
    
    // Test basic security headers
    console.log('\n🔒 Checking security headers...');
    const headers = response.headers;
    
    const securityHeaders = [
      'x-frame-options',
      'x-content-type-options', 
      'content-security-policy'
    ];
    
    securityHeaders.forEach(header => {
      if (headers[header]) {
        console.log(`✅ ${header}: ${headers[header]}`);
        results.push({ test: `Security Header: ${header}`, status: 'PASS', message: headers[header] });
      } else {
        console.log(`⚠️  Missing: ${header}`);
        results.push({ test: `Security Header: ${header}`, status: 'WARNING', message: 'Missing' });
      }
    });
    
    // Test content
    console.log('\n📄 Checking page content...');
    if (response.data.includes('AI Karen') || response.data.includes('Karen')) {
      console.log('✅ Page contains expected content');
      results.push({ test: 'Page Content', status: 'PASS', message: 'Contains expected content' });
    } else {
      console.log('⚠️  Page content may be incomplete');
      results.push({ test: 'Page Content', status: 'WARNING', message: 'Content check failed' });
    }
    
  } catch (error) {
    console.log(`❌ Server not accessible: ${error.message}`);
    results.push({ test: 'Server Availability', status: 'FAIL', message: error.message });
  }

  // Test API endpoints with timeout
  console.log('\n🔌 Testing API endpoints...');
  const apiEndpoints = [
    '/api/health',
    '/login'
  ];

  for (const endpoint of apiEndpoints) {
    try {
      const response = await makeRequest(`http://localhost:8000${endpoint}`, 5000);
      if (response.status < 500) {
        console.log(`✅ ${endpoint}: ${response.status}`);
        results.push({ test: `API: ${endpoint}`, status: 'PASS', message: `HTTP ${response.status}` });
      } else {
        console.log(`⚠️  ${endpoint}: ${response.status}`);
        results.push({ test: `API: ${endpoint}`, status: 'WARNING', message: `HTTP ${response.status}` });
      }
    } catch (error) {
      console.log(`❌ ${endpoint}: ${error.message}`);
      results.push({ test: `API: ${endpoint}`, status: 'FAIL', message: error.message });
    }
  }

  // Summary
  console.log('\n📊 AUDIT SUMMARY');
  console.log('================');
  const passed = results.filter(r => r.status === 'PASS').length;
  const warnings = results.filter(r => r.status === 'WARNING').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  
  console.log(`✅ Passed: ${passed}`);
  console.log(`⚠️  Warnings: ${warnings}`);
  console.log(`❌ Failed: ${failed}`);
  
  if (failed === 0) {
    console.log('\n🎉 Web container is operational!');
    return 0;
  } else {
    console.log('\n🚨 Issues detected - check failed tests');
    return 1;
  }
}

function makeRequest(url, timeout = 10000) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const req = client.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ 
        status: res.statusCode, 
        headers: res.headers, 
        data 
      }));
    });
    
    req.on('error', reject);
    req.setTimeout(timeout, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

if (require.main === module) {
  testWebContainer().then(process.exit).catch(err => {
    console.error('Audit failed:', err);
    process.exit(1);
  });
}
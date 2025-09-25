#!/usr/bin/env node

/**
 * Test script to verify frontend authentication flow
 */

const fetch = require('node-fetch');

const BACKEND_URL = 'http://127.0.0.1:8000';

// Test token from our earlier successful login
const TEST_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YTMyZmQzZC05NGYwLTRmZjgtODE0Yi1lZWYzOTQyYTI3ZDkiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZnVsbF9uYW1lIjoiQWRtaW4gVXNlciIsInJvbGVzIjpbXSwidGVuYW50X2lkIjoiZmMwY2ExOTQtYTkxYS00NjA1LWE4OWUtMDkzNDQ3ODEyMTM1IiwiaXNfdmVyaWZpZWQiOnRydWUsImlzX2FjdGl2ZSI6dHJ1ZSwiZXhwIjoxNzU2NzQyNDE5LCJpYXQiOjE3NTY3NDE1MTksIm5iZiI6MTc1Njc0MTUxOSwianRpIjoiZTUzNTBkNGE0YzEyYTUyZTQ4ZjY2MzkzOTUxMWVkNDgiLCJ0eXAiOiJhY2Nlc3MifQ.lIeHeeaYxHJtks4-0iL_cNEvf3iUFOUyivc8YaH8lB0';

async function testEndpoint(endpoint, description) {
  console.log(`\n🔍 Testing ${description}...`);
  
  try {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${TEST_TOKEN}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
    
    console.log(`   Status: ${response.status} ${response.statusText}`);
    
    if (response.ok) {
      const data = await response.json();
      console.log(`   ✅ Success: ${JSON.stringify(data).substring(0, 100)}...`);
      return true;
    } else {
      const errorText = await response.text();
      console.log(`   ❌ Failed: ${errorText}`);
      return false;
    }
  } catch (error) {
    console.log(`   ❌ Error: ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('🚀 Testing Frontend Authentication Flow');
  console.log(`Backend URL: ${BACKEND_URL}`);
  
  const tests = [
    ['/api/auth/me', 'User Profile'],
    ['/api/plugins/', 'Plugins List'],
    ['/api/health', 'Health Check'],
  ];
  
  let passed = 0;
  let total = tests.length;
  
  for (const [endpoint, description] of tests) {
    const success = await testEndpoint(endpoint, description);
    if (success) passed++;
  }
  
  console.log(`\n📊 Results: ${passed}/${total} tests passed`);
  
  if (passed === total) {
    console.log('✅ All authentication tests passed!');
    console.log('\n💡 The backend authentication is working correctly.');
    console.log('   The issue is likely in the frontend session management.');
    console.log('   Check that the frontend is properly storing and sending tokens.');
  } else {
    console.log('❌ Some authentication tests failed.');
    console.log('   This indicates an issue with the backend authentication system.');
  }
}

main().catch(console.error);
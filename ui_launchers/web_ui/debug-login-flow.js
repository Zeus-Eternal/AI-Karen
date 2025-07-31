/**
 * Debug script to identify login redirect issues
 * This will help us understand what's happening during the authentication process
 */

console.log('🔍 Debugging Login Flow Issues...\n');

// Test 1: Check if the backend is accessible
console.log('Test 1: Backend Connectivity Check');
async function testBackendConnectivity() {
  const backendUrl = 'http://localhost:8000';
  const endpoints = [
    '/health',
    '/api/auth/login',
    '/api/auth/me'
  ];

  for (const endpoint of endpoints) {
    try {
      const url = `${backendUrl}${endpoint}`;
      console.log(`Testing: ${url}`);
      
      // For login endpoint, we expect a 405 (Method Not Allowed) or 422 (Validation Error) for GET
      // For health endpoint, we expect 200
      // For /me endpoint, we expect 401 (Unauthorized) without credentials
      
      const response = await fetch(url, {
        method: endpoint === '/health' ? 'GET' : 'GET', // Just test connectivity
        headers: { 'Accept': 'application/json' }
      });
      
      console.log(`  ✓ ${endpoint}: ${response.status} ${response.statusText}`);
      
      if (endpoint === '/health' && response.ok) {
        const data = await response.text();
        console.log(`    Response: ${data.substring(0, 100)}...`);
      }
      
    } catch (error) {
      console.log(`  ❌ ${endpoint}: ${error.message}`);
    }
  }
}

// Test 2: Simulate login request
console.log('\nTest 2: Simulate Login Request');
async function testLoginRequest() {
  const backendUrl = 'http://localhost:8000';
  const loginUrl = `${backendUrl}/api/auth/login`;
  
  // Test with dummy credentials to see the response structure
  const testCredentials = {
    email: 'test@example.com',
    password: 'testpassword'
  };
  
  try {
    console.log(`Sending POST to: ${loginUrl}`);
    console.log(`Credentials: ${JSON.stringify(testCredentials)}`);
    
    const response = await fetch(loginUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testCredentials),
      credentials: 'include',
    });
    
    console.log(`Response Status: ${response.status} ${response.statusText}`);
    console.log(`Response Headers:`, Object.fromEntries(response.headers.entries()));
    
    const responseText = await response.text();
    console.log(`Response Body: ${responseText}`);
    
    if (!response.ok) {
      console.log('  ℹ️ This is expected for dummy credentials');
    }
    
  } catch (error) {
    console.log(`  ❌ Login request failed: ${error.message}`);
  }
}

// Test 3: Check CORS configuration
console.log('\nTest 3: CORS Configuration Check');
function testCorsConfiguration() {
  const frontendUrl = 'http://localhost:9002';
  const backendUrl = 'http://localhost:8000';
  
  console.log(`Frontend URL: ${frontendUrl}`);
  console.log(`Backend URL: ${backendUrl}`);
  
  // Check if URLs match CORS configuration
  const corsOrigins = ['http://localhost:9002', 'http://127.0.0.1:9002'];
  const isConfigured = corsOrigins.includes(frontendUrl);
  
  console.log(`CORS Origins: ${corsOrigins.join(', ')}`);
  console.log(`Frontend URL in CORS: ${isConfigured ? '✓' : '❌'}`);
  
  if (!isConfigured) {
    console.log('  ⚠️ Frontend URL might not be in CORS configuration');
  }
}

// Test 4: Check authentication state flow
console.log('\nTest 4: Authentication State Flow Analysis');
function analyzeAuthFlow() {
  console.log('Expected Authentication Flow:');
  console.log('1. User submits login form');
  console.log('2. AuthContext.login() is called');
  console.log('3. authService.login() makes API request');
  console.log('4. Backend responds with LoginResponse');
  console.log('5. AuthContext creates User object');
  console.log('6. AuthContext sets isAuthenticated = true');
  console.log('7. ProtectedRoute detects authentication change');
  console.log('8. ProtectedRoute renders main UI instead of LoginForm');
  
  console.log('\nPotential Issues:');
  console.log('❓ Backend not responding correctly');
  console.log('❓ CORS blocking the request');
  console.log('❓ LoginResponse structure mismatch');
  console.log('❓ AuthContext not updating state');
  console.log('❓ ProtectedRoute not detecting state change');
  console.log('❓ React state update not triggering re-render');
}

// Test 5: Check environment configuration
console.log('\nTest 5: Environment Configuration Check');
function checkEnvironmentConfig() {
  const envVars = [
    'KAREN_BACKEND_URL',
    'NEXT_PUBLIC_API_URL',
    'KAREN_ENVIRONMENT',
    'KAREN_NETWORK_MODE',
    'KAREN_CORS_ORIGINS',
    'PORT'
  ];
  
  console.log('Environment Variables:');
  envVars.forEach(varName => {
    const value = process.env[varName] || 'NOT SET';
    console.log(`  ${varName}: ${value}`);
  });
  
  // Check for potential mismatches
  const backendUrl = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
  const port = process.env.PORT || '9002';
  
  console.log('\nConfiguration Analysis:');
  console.log(`Backend URL: ${backendUrl}`);
  console.log(`Frontend Port: ${port}`);
  
  if (backendUrl && !backendUrl.includes('8000')) {
    console.log('  ⚠️ Backend URL might not be pointing to port 8000');
  }
  
  if (port !== '9002') {
    console.log('  ⚠️ Frontend port might not be 9002');
  }
}

// Test 6: Check for common authentication issues
console.log('\nTest 6: Common Authentication Issues');
function checkCommonIssues() {
  console.log('Common Login Redirect Issues:');
  console.log('1. ❓ Backend authentication endpoint not working');
  console.log('2. ❓ CORS policy blocking requests');
  console.log('3. ❓ Cookie/session not being set properly');
  console.log('4. ❓ AuthContext state not updating after login');
  console.log('5. ❓ ProtectedRoute not re-rendering after state change');
  console.log('6. ❓ React strict mode causing double renders');
  console.log('7. ❓ Network request failing silently');
  console.log('8. ❓ LoginResponse structure not matching expected format');
  
  console.log('\nDebugging Steps:');
  console.log('1. Open browser dev tools');
  console.log('2. Go to Network tab');
  console.log('3. Try to login');
  console.log('4. Check if login request is made');
  console.log('5. Check response status and body');
  console.log('6. Check if cookies are set');
  console.log('7. Check console for errors');
  console.log('8. Check React dev tools for state changes');
}

// Run all tests
async function runAllTests() {
  try {
    checkEnvironmentConfig();
    testCorsConfiguration();
    analyzeAuthFlow();
    checkCommonIssues();
    
    console.log('\n🌐 Testing Backend Connectivity...');
    await testBackendConnectivity();
    
    console.log('\n🔐 Testing Login Endpoint...');
    await testLoginRequest();
    
  } catch (error) {
    console.error('Debug script error:', error);
  }
}

// Execute the debug script
runAllTests().then(() => {
  console.log('\n🎯 Debug Analysis Complete!');
  console.log('\n📋 Next Steps:');
  console.log('1. Check if FastAPI backend is running on http://localhost:8000');
  console.log('2. Test backend health endpoint: curl http://localhost:8000/health');
  console.log('3. Start frontend: npm run dev (should run on http://localhost:9002)');
  console.log('4. Open browser dev tools and try to login');
  console.log('5. Check Network tab for failed requests');
  console.log('6. Check Console tab for JavaScript errors');
  console.log('7. Check Application tab for cookies/session storage');
  
  console.log('\n🔧 If backend is not running:');
  console.log('1. Navigate to the backend directory');
  console.log('2. Activate virtual environment: source .env_ai/bin/activate');
  console.log('3. Start FastAPI: python main.py or uvicorn main:app --reload --port 8000');
  
  console.log('\n🔍 If requests are failing:');
  console.log('1. Check CORS configuration in backend');
  console.log('2. Verify authentication endpoints exist');
  console.log('3. Check if credentials are valid');
  console.log('4. Test with curl or Postman first');
});
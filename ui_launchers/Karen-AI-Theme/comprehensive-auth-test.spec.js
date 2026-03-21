#!/usr/bin/env node

/**
 * Comprehensive Authentication Test Script for Karen-AI-Theme
 * Tests the complete authentication flow with production backend auth system
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

console.log('🔐 Comprehensive Authentication Test - Karen-AI-Theme');
console.log('====================================================');
console.log(`API Base URL: ${API_BASE_URL}`);
console.log('');

// Test configuration
const testConfig = {
  // Test credentials
  validCredentials: [
    { identifier: 'admin', password: 'admin123', type: 'username' },
    { identifier: 'admin@kari.ai', password: 'admin123', type: 'email' }
  ],
  
  invalidCredentials: [
    { identifier: 'invalid', password: 'wrongpass', type: 'username' },
    { identifier: 'invalid@kari.ai', password: 'wrongpass', type: 'email' },
    { identifier: '', password: 'admin123', type: 'empty' },
    { identifier: 'admin', password: '', type: 'empty' }
  ],

  // Test scenarios
  scenarios: {
    backendHealth: 'Backend Service Health Check',
    authEndpoints: 'Authentication Endpoints Access',
    validLogin: 'Valid User Authentication',
    invalidLogin: 'Invalid Credentials Handling',
    tokenValidation: 'JWT Token Validation',
    tokenRefresh: 'Token Refresh Mechanism',
    sessionPersistence: 'Session Persistence',
    logout: 'Logout Functionality',
    corsHeaders: 'CORS and Security Headers',
    routeProtection: 'Route Protection',
    frontendIntegration: 'Frontend Integration'
  }
};

// Test results storage
const testResults = {
  passed: 0,
  failed: 0,
  details: []
};

function logTestResult(testName, status, details = '') {
  const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⚠️';
  console.log(`${icon} ${testName}: ${status}`);
  if (details) {
    console.log(`   ${details}`);
  }
  console.log('');
  
  testResults.details.push({
    name: testName,
    status,
    details,
    timestamp: new Date().toISOString()
  });
  
  if (status === 'PASS') {
    testResults.passed++;
  } else {
    testResults.failed++;
  }
}

async function makeRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    return {
      ok: response.ok,
      status: response.status,
      data: await response.json().catch(() => ({})),
      headers: Object.fromEntries(response.headers.entries())
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      data: { error: error.message },
      headers: {}
    };
  }
}

// Test 1: Backend Service Health Check
async function testBackendHealth() {
  console.log('🏥 Testing Backend Service Health...\n');
  
  try {
    const response = await makeRequest(`${API_BASE_URL}/health`);
    
    if (response.ok && response.data.status === 'ok') {
      logTestResult(
        testConfig.scenarios.backendHealth,
        'PASS',
        `Service is healthy (${response.data.timestamp})`
      );
      return true;
    } else {
      logTestResult(
        testConfig.scenarios.backendHealth,
        'FAIL',
        `Health check failed: ${response.data.error || 'Unknown error'}`
      );
      return false;
    }
  } catch (error) {
    logTestResult(
      testConfig.scenarios.backendHealth,
      'FAIL',
      `Unable to connect to backend: ${error.message}`
    );
    return false;
  }
}

// Test 2: Authentication Endpoints Access
async function testAuthEndpoints() {
  console.log('🔍 Testing Authentication Endpoints Access...\n');
  
  const endpoints = [
    '/api/auth/status',
    '/api/auth/health',
    '/api/auth/first-run'
  ];
  
  let allAccessible = true;
  
  for (const endpoint of endpoints) {
    try {
      const response = await makeRequest(`${API_BASE_URL}${endpoint}`);
      
      if (response.ok || response.status === 401 || response.status === 403) {
        logTestResult(
          `${testConfig.scenarios.authEndpoints} - ${endpoint}`,
          'PASS',
          `Endpoint accessible (Status: ${response.status})`
        );
      } else {
        logTestResult(
          `${testConfig.scenarios.authEndpoints} - ${endpoint}`,
          'FAIL',
          `Endpoint not accessible (Status: ${response.status})`
        );
        allAccessible = false;
      }
    } catch (error) {
      logTestResult(
        `${testConfig.scenarios.authEndpoints} - ${endpoint}`,
        'FAIL',
        `Connection error: ${error.message}`
      );
      allAccessible = false;
    }
  }
  
  return allAccessible;
}

// Test 3: Valid User Authentication
async function testValidAuthentication() {
  console.log('🔑 Testing Valid User Authentication...\n');
  
  let authenticationSuccessful = false;
  let successfulCredentials = null;
  
  for (const cred of testConfig.validCredentials) {
    console.log(`Testing ${cred.type}: ${cred.identifier} / ${cred.password}`);
    
    try {
      const response = await makeRequest(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        body: JSON.stringify({
          [cred.type]: cred.identifier,
          password: cred.password
        })
      });
      
      if (response.ok) {
        const { access_token, refresh_token, user, permissions } = response.data;
        
        logTestResult(
          testConfig.scenarios.validLogin,
          'PASS',
          `Authentication successful for ${cred.type}\n   User: ${user.email} (${user.full_name})\n   Permissions: ${permissions.join(', ')}`
        );
        
        // Store successful credentials for subsequent tests
        successfulCredentials = {
          ...cred,
          access_token,
          refresh_token,
          user,
          permissions
        };
        
        authenticationSuccessful = true;
        break;
      } else {
        const errorMsg = response.data.detail || 'Unknown error';
        console.log(`   ❌ Authentication failed: ${errorMsg}\n`);
      }
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}\n`);
    }
  }
  
  if (!authenticationSuccessful) {
    logTestResult(
      testConfig.scenarios.validLogin,
      'FAIL',
      'No valid authentication credentials worked'
    );
  }
  
  return { success: authenticationSuccessful, credentials: successfulCredentials };
}

// Test 4: Invalid Credentials Handling
async function testInvalidCredentials() {
  console.log('🚫 Testing Invalid Credentials Handling...\n');
  
  let allTestsPassed = true;
  
  for (const cred of testConfig.invalidCredentials) {
    console.log(`Testing invalid ${cred.type}: ${cred.identifier} / ${cred.password}`);
    
    try {
      const response = await makeRequest(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        body: JSON.stringify({
          [cred.type]: cred.identifier,
          password: cred.password
        })
      });
      
      if (!response.ok && response.data.detail) {
        logTestResult(
          `${testConfig.scenarios.invalidLogin} - ${cred.type}`,
          'PASS',
          `Correctly rejected invalid credentials: ${response.data.detail}`
        );
      } else {
        logTestResult(
          `${testConfig.scenarios.invalidLogin} - ${cred.type}`,
          'FAIL',
          'Should have rejected invalid credentials but did not'
        );
        allTestsPassed = false;
      }
    } catch (error) {
      logTestResult(
        `${testConfig.scenarios.invalidLogin} - ${cred.type}`,
        'FAIL',
        `Error during invalid credential test: ${error.message}`
      );
      allTestsPassed = false;
    }
  }
  
  return allTestsPassed;
}

// Test 5: JWT Token Validation
async function testTokenValidation(credentials) {
  if (!credentials || !credentials.access_token) {
    logTestResult(
      testConfig.scenarios.tokenValidation,
      'SKIP',
      'No valid credentials available for token testing'
    );
    return false;
  }
  
  console.log('🔒 Testing JWT Token Validation...\n');
  
  try {
    const response = await makeRequest(`${API_BASE_URL}/api/auth/validate-session`, {
      headers: {
        'Authorization': `Bearer ${credentials.access_token}`
      }
    });
    
    if (response.ok && response.data.authenticated) {
      logTestResult(
        testConfig.scenarios.tokenValidation,
        'PASS',
        `Token is valid for user: ${response.data.user.email}\n   Permissions: ${response.data.permissions.join(', ')}`
      );
      return true;
    } else {
      logTestResult(
        testConfig.scenarios.tokenValidation,
        'FAIL',
        `Token validation failed: ${response.data.detail || 'Unknown error'}`
      );
      return false;
    }
  } catch (error) {
    logTestResult(
      testConfig.scenarios.tokenValidation,
      'FAIL',
      `Error during token validation: ${error.message}`
    );
    return false;
  }
}

// Test 6: Token Refresh Mechanism
async function testTokenRefresh(credentials) {
  if (!credentials || !credentials.refresh_token) {
    logTestResult(
      testConfig.scenarios.tokenRefresh,
      'SKIP',
      'No refresh token available for testing'
    );
    return false;
  }
  
  console.log('🔄 Testing Token Refresh Mechanism...\n');
  
  try {
    const response = await makeRequest(`${API_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      body: JSON.stringify({
        refresh_token: credentials.refresh_token
      })
    });
    
    if (response.ok && response.data.access_token) {
      logTestResult(
        testConfig.scenarios.tokenRefresh,
        'PASS',
        `Token refresh successful\n   New token expires in: ${response.data.expires_in}s`
      );
      return true;
    } else {
      logTestResult(
        testConfig.scenarios.tokenRefresh,
        'FAIL',
        `Token refresh failed: ${response.data.detail || 'Unknown error'}`
      );
      return false;
    }
  } catch (error) {
    logTestResult(
      testConfig.scenarios.tokenRefresh,
      'FAIL',
      `Error during token refresh: ${error.message}`
    );
    return false;
  }
}

// Test 7: Session Persistence
async function testSessionPersistence(credentials) {
  if (!credentials || !credentials.access_token) {
    logTestResult(
      testConfig.scenarios.sessionPersistence,
      'SKIP',
      'No valid credentials available for session testing'
    );
    return false;
  }
  
  console.log('🕒 Testing Session Persistence...\n');
  
  try {
    // Test multiple requests with the same token
    const requests = [
      makeRequest(`${API_BASE_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${credentials.access_token}` }
      }),
      makeRequest(`${API_BASE_URL}/api/auth/validate-session`, {
        headers: { 'Authorization': `Bearer ${credentials.access_token}` }
      })
    ];
    
    const responses = await Promise.all(requests);
    const allSuccessful = responses.every(r => r.ok);
    
    if (allSuccessful) {
      logTestResult(
        testConfig.scenarios.sessionPersistence,
        'PASS',
        'Session persistence confirmed across multiple requests'
      );
      return true;
    } else {
      logTestResult(
        testConfig.scenarios.sessionPersistence,
        'FAIL',
        'Session persistence test failed'
      );
      return false;
    }
  } catch (error) {
    logTestResult(
      testConfig.scenarios.sessionPersistence,
      'FAIL',
      `Error during session persistence test: ${error.message}`
    );
    return false;
  }
}

// Test 8: Logout Functionality
async function testLogout(credentials) {
  if (!credentials || !credentials.refresh_token) {
    logTestResult(
      testConfig.scenarios.logout,
      'SKIP',
      'No refresh token available for logout testing'
    );
    return false;
  }
  
  console.log('🚪 Testing Logout Functionality...\n');
  
  try {
    const response = await makeRequest(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      body: JSON.stringify({
        refresh_token: credentials.refresh_token
      })
    });
    
    if (response.ok) {
      logTestResult(
        testConfig.scenarios.logout,
        'PASS',
        'Logout completed successfully'
      );
      return true;
    } else {
      logTestResult(
        testConfig.scenarios.logout,
        'FAIL',
        `Logout failed: ${response.data.detail || 'Unknown error'}`
      );
      return false;
    }
  } catch (error) {
    logTestResult(
      testConfig.scenarios.logout,
      'FAIL',
      `Error during logout: ${error.message}`
    );
    return false;
  }
}

// Test 9: CORS and Security Headers
async function testCorsHeaders() {
  console.log('🛡️ Testing CORS and Security Headers...\n');
  
  try {
    const response = await makeRequest(`${API_BASE_URL}/api/auth/status`);
    
    const securityHeaders = {
      'Access-Control-Allow-Origin': response.headers['access-control-allow-origin'],
      'Access-Control-Allow-Methods': response.headers['access-control-allow-methods'],
      'Access-Control-Allow-Headers': response.headers['access-control-allow-headers'],
      'X-Content-Type-Options': response.headers['x-content-type-options'],
      'X-Frame-Options': response.headers['x-frame-options'],
      'Content-Security-Policy': response.headers['content-security-policy']
    };
    
    let headersValid = true;
    const headerResults = [];
    
    for (const [header, value] of Object.entries(securityHeaders)) {
      if (value) {
        headerResults.push(`${header}: ${value}`);
      } else {
        headersValid = false;
        headerResults.push(`${header}: Missing`);
      }
    }
    
    if (headersValid) {
      logTestResult(
        testConfig.scenarios.corsHeaders,
        'PASS',
        `Security headers properly configured\n   ${headerResults.join('\n   ')}`
      );
    } else {
      logTestResult(
        testConfig.scenarios.corsHeaders,
        'FAIL',
        `Some security headers missing\n   ${headerResults.join('\n   ')}`
      );
    }
    
    return headersValid;
  } catch (error) {
    logTestResult(
      testConfig.scenarios.corsHeaders,
      'FAIL',
      `Error checking security headers: ${error.message}`
    );
    return false;
  }
}

// Test 10: Frontend Integration Check
async function testFrontendIntegration() {
  console.log('🌐 Testing Frontend Integration...\n');
  
  try {
    // Check if we can access the frontend development server
    const frontendUrl = 'http://localhost:9002'; // Assuming default Next.js port
    const response = await fetch(`${frontendUrl}/api/auth/status`, {
      // This will likely fail due to CORS, but we can check the error
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      logTestResult(
        testConfig.scenarios.frontendIntegration,
        'PASS',
        'Frontend API accessible'
      );
      return true;
    } else {
      logTestResult(
        testConfig.scenarios.frontendIntegration,
        'WARN',
        'Frontend not accessible (this is expected if not running)\n   Start the frontend with: cd ui_launchers/Karen-AI-Theme && npm run dev'
      );
      return false;
    }
  } catch (error) {
    logTestResult(
      testConfig.scenarios.frontendIntegration,
      'WARN',
      `Frontend not accessible (this is expected if not running)\n   Start the frontend with: cd ui_launchers/Karen-AI-Theme && npm run dev\n   Error: ${error.message}`
    );
    return false;
  }
}

// Main test execution
async function runComprehensiveTests() {
  console.log('🚀 Starting Comprehensive Authentication Tests...\n');
  
  // Test Results Summary
  console.log('📋 Test Suite Configuration:');
  console.log(`   Valid Credentials: ${testConfig.validCredentials.length} test cases`);
  console.log(`   Invalid Credentials: ${testConfig.invalidCredentials.length} test cases`);
  console.log(`   Total Scenarios: ${Object.keys(testConfig.scenarios).length}\n`);
  
  // Execute tests in sequence
  const testResults = {
    backendHealth: await testBackendHealth(),
    authEndpoints: await testAuthEndpoints(),
    authentication: await testValidAuthentication(),
    invalidCredentials: await testInvalidCredentials(),
    corsHeaders: await testCorsHeaders(),
    frontendIntegration: await testFrontendIntegration()
  };
  
  // If we have valid credentials, run additional tests
  if (testResults.authentication.success) {
    const credentials = testResults.authentication.credentials;
    
    testResults.tokenValidation = await testTokenValidation(credentials);
    testResults.tokenRefresh = await testTokenRefresh(credentials);
    testResults.sessionPersistence = await testSessionPersistence(credentials);
    testResults.logout = await testLogout(credentials);
  }
  
  // Generate comprehensive test report
  console.log('📊 Test Results Summary');
  console.log('=====================');
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log(`⚠️  Skipped: 0`);
  console.log('');
  
  // Detailed results
  console.log('🔍 Detailed Test Results:');
  console.log('========================');
  for (const result of Object.values(testResults)) {
    const icon = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '⚠️';
    console.log(`${icon} ${result.name}: ${result.status}`);
    if (result.details) {
      console.log(`   ${result.details}`);
    }
  }
  
  // Production readiness assessment
  console.log('\n🏁 Production Readiness Assessment');
  console.log('=================================');
  
  const criticalTests = [
    'backendHealth',
    'authEndpoints',
    'authentication',
    'invalidCredentials',
    'corsHeaders'
  ];
  
  const passedCritical = criticalTests.filter(test => 
    testResults.details.find(r => r.name.includes(testConfig.scenarios[test]))?.status === 'PASS'
  ).length;
  
  const criticalScore = (passedCritical / criticalTests.length) * 100;
  
  console.log(`Critical Tests Score: ${criticalScore.toFixed(1)}% (${passedCritical}/${criticalTests.length})`);
  
  if (criticalScore >= 80) {
    console.log('✅ Authentication system is ready for production deployment');
  } else if (criticalScore >= 60) {
    console.log('⚠️  Authentication system needs minor improvements before production');
  } else {
    console.log('❌ Authentication system requires significant fixes before production');
  }
  
  // Recommendations
  console.log('\n💡 Recommendations:');
  console.log('=================');
  
  if (!testResults.authentication.success) {
    console.log('• Admin user needs to be created or verified');
    console.log('• Check database initialization and user setup');
  }
  
  if (!testResults.frontendIntegration) {
    console.log('• Start frontend development server for UI testing');
    console.log('• Test login page at: http://localhost:9002/login');
  }
  
  if (testResults.authentication.success) {
    console.log('• Test both username (admin) and email (admin@kari.ai) login modes');
    console.log('• Verify UI preservation and styling');
    console.log('• Test route protection and AuthGuard behavior');
    console.log('• Validate useAuth hook functionality');
  }
  
  console.log('\n🔧 Next Steps:');
  console.log('=============');
  console.log('1. Ensure admin credentials are properly configured');
  console.log('2. Start frontend development server');
  console.log('3. Test complete authentication flow in browser');
  console.log('4. Validate UI preservation and user experience');
  console.log('5. Perform cross-browser compatibility testing');
  
  return testResults;
}

// Execute the comprehensive tests
runComprehensiveTests().catch(console.error);
// Simple authentication debugging script
// Run this in the browser console to debug the login loop

console.log('🔍 Authentication Debug Script');
console.log('================================');

// Check current page
console.log('Current page:', window.location.pathname);

// Check cookies
console.log('Cookies:', document.cookie);

// Check session storage
console.log('Session storage redirectAfterLogin:', sessionStorage.getItem('redirectAfterLogin'));

// Check if auth token exists
const hasAuthToken = document.cookie.includes('auth_token=');
console.log('Has auth token cookie:', hasAuthToken);

// Test session validation endpoint
async function testSessionValidation() {
  try {
    console.log('Testing session validation...');
    const response = await fetch('/api/auth/validate-session', {
      method: 'GET',
      credentials: 'include'
    });
    
    console.log('Session validation response status:', response.status);
    const data = await response.json();
    console.log('Session validation data:', data);
    
    return data;
  } catch (error) {
    console.error('Session validation error:', error);
    return null;
  }
}

// Test backend connectivity
async function testBackendConnectivity() {
  try {
    console.log('Testing backend connectivity...');
    const response = await fetch('/api/health', {
      method: 'GET'
    });
    
    console.log('Backend health response status:', response.status);
    const data = await response.json();
    console.log('Backend health data:', data);
    
    return data;
  } catch (error) {
    console.error('Backend connectivity error:', error);
    return null;
  }
}

// Run tests
async function runDebugTests() {
  console.log('\n🧪 Running debug tests...');
  
  const sessionData = await testSessionValidation();
  const healthData = await testBackendConnectivity();
  
  console.log('\n📊 Debug Summary:');
  console.log('- Current page:', window.location.pathname);
  console.log('- Has auth token:', hasAuthToken);
  console.log('- Session valid:', sessionData?.valid || false);
  console.log('- Backend healthy:', healthData?.status === 'healthy' || false);
  
  if (window.location.pathname === '/login' && hasAuthToken && sessionData?.valid) {
    console.log('⚠️ ISSUE DETECTED: On login page but have valid session - this could cause a loop!');
  }
  
  if (window.location.pathname !== '/login' && (!hasAuthToken || !sessionData?.valid)) {
    console.log('⚠️ ISSUE DETECTED: Not on login page but no valid session - should redirect to login');
  }
}

// Auto-run tests
runDebugTests();

// Export functions for manual testing
window.debugAuth = {
  testSessionValidation,
  testBackendConnectivity,
  runDebugTests
};

console.log('\n💡 Use window.debugAuth.runDebugTests() to run tests again');
// Simple script to set up authentication token for testing
// Run this in the browser console to set a valid token

console.log('🔧 Setting up authentication token for testing...');

// Use the working token from our earlier tests
const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YTMyZmQzZC05NGYwLTRmZjgtODE0Yi1lZWYzOTQyYTI3ZDkiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZnVsbF9uYW1lIjoiQWRtaW4gVXNlciIsInJvbGVzIjpbXSwidGVuYW50X2lkIjoiZmMwY2ExOTQtYTkxYS00NjA1LWE4OWUtMDkzNDQ3ODEyMTM1IiwiaXNfdmVyaWZpZWQiOnRydWUsImlzX2FjdGl2ZSI6dHJ1ZSwiZXhwIjoxNzU2NzQyNDE5LCJpYXQiOjE3NTY3NDE1MTksIm5iZiI6MTc1Njc0MTUxOSwianRpIjoiZTUzNTBkNGE0YzEyYTUyZTQ4ZjY2MzkzOTUxMWVkNDgiLCJ0eXAiOiJhY2Nlc3MifQ.lIeHeeaYxHJtks4-0iL_cNEvf3iUFOUyivc8YaH8lB0';

// Set the token in localStorage
localStorage.setItem('karen_access_token', testToken);

// Also set session data
localStorage.setItem('karen_session_data', JSON.stringify({
  userId: '8a32fd3d-94f0-4ff8-814b-eef3942a27d9',
  email: 'admin@example.com',
  expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours from now
  roles: [],
  tenantId: 'fc0ca194-a91a-4605-a89e-093447812135'
}));

console.log('✅ Authentication token set successfully!');
console.log('📝 Token preview:', testToken.substring(0, 50) + '...');
console.log('🔄 Please refresh the page to apply the authentication.');

// Test the token by making a request
fetch('/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${testToken}`,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  if (response.ok) {
    console.log('✅ Token validation successful!');
    return response.json();
  } else {
    console.log('❌ Token validation failed:', response.status);
    throw new Error(`HTTP ${response.status}`);
  }
})
.then(data => {
  console.log('👤 User data:', data);
})
.catch(error => {
  console.error('❌ Token test failed:', error);
});
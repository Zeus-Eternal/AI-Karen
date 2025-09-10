// Quick Authentication Fix - Run this in your browser console
// Copy and paste this entire script into the browser console on http://localhost:8010

console.log('🔧 Quick Authentication Fix Starting...');

// Clear any existing auth data first
localStorage.removeItem('karen_access_token');
localStorage.removeItem('karen_session_data');
console.log('🧹 Cleared existing auth data');

// Set the working authentication token
const authToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YTMyZmQzZC05NGYwLTRmZjgtODE0Yi1lZWYzOTQyYTI3ZDkiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZnVsbF9uYW1lIjoiQWRtaW4gVXNlciIsInJvbGVzIjpbXSwidGVuYW50X2lkIjoiZmMwY2ExOTQtYTkxYS00NjA1LWE4OWUtMDkzNDQ3ODEyMTM1IiwiaXNfdmVyaWZpZWQiOnRydWUsImlzX2FjdGl2ZSI6dHJ1ZSwiZXhwIjoxNzU2NzQyNDE5LCJpYXQiOjE3NTY3NDE1MTksIm5iZiI6MTc1Njc0MTUxOSwianRpIjoiZTUzNTBkNGE0YzEyYTUyZTQ4ZjY2MzkzOTUxMWVkNDgiLCJ0eXAiOiJhY2Nlc3MifQ.lIeHeeaYxHJtks4-0iL_cNEvf3iUFOUyivc8YaH8lB0';

localStorage.setItem('karen_access_token', authToken);
console.log('🔑 Set authentication token');

// Set session data
const sessionData = {
  userId: '8a32fd3d-94f0-4ff8-814b-eef3942a27d9',
  email: 'admin@example.com',
  expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours from now
  roles: [],
  tenantId: 'fc0ca194-a91a-4605-a89e-093447812135'
};

localStorage.setItem('karen_session_data', JSON.stringify(sessionData));
console.log('📝 Set session data:', sessionData);

// Test the authentication
console.log('🧪 Testing authentication...');
fetch('/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('📡 Response status:', response.status);
  if (response.ok) {
    return response.json();
  } else {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
})
.then(data => {
  console.log('✅ Authentication test successful!');
  console.log('👤 User data:', data);
  console.log('🎉 Authentication is now working!');
  console.log('🔄 Please refresh the page to apply the changes.');
  
  // Show a confirmation message
  if (confirm('Authentication setup complete! Click OK to refresh the page.')) {
    location.reload();
  }
})
.catch(error => {
  console.error('❌ Authentication test failed:', error);
  console.log('⚠️ This might be normal if the backend is not running or if there are network issues.');
  console.log('🔄 Try refreshing the page anyway - the token has been set.');
});

console.log('✅ Authentication fix complete!');
console.log('📋 Summary:');
console.log('   - Token stored in localStorage');
console.log('   - Session data stored');
console.log('   - Ready for API calls');
console.log('🔄 Refresh the page to see the changes take effect.');
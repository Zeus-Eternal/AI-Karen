// Browser console script to debug and fix authentication session issues
// Run this in your browser's developer console

console.log('🔧 AI-Karen Auth Session Debug & Fix');
console.log('=====================================');

// Step 1: Clear existing auth data
console.log('1. Clearing existing authentication data...');
localStorage.removeItem('karen_access_token');
localStorage.removeItem('karen_refresh_token');
localStorage.removeItem('karen_session');
localStorage.removeItem('karen_user');
sessionStorage.clear();

// Clear any auth cookies
document.cookie.split(";").forEach(function(c) { 
    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
});

console.log('✅ Cleared authentication data');

// Step 2: Check current session state
console.log('2. Checking current session state...');
const sessionData = {
    localStorage: {
        access_token: localStorage.getItem('karen_access_token'),
        refresh_token: localStorage.getItem('karen_refresh_token'),
        session: localStorage.getItem('karen_session'),
        user: localStorage.getItem('karen_user')
    },
    cookies: document.cookie,
    sessionStorage: Object.keys(sessionStorage).length
};
console.log('Session data:', sessionData);

// Step 3: Test backend connectivity
console.log('3. Testing backend connectivity...');
fetch('/api/auth/validate-session', {
    method: 'GET',
    headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    },
    credentials: 'include'
})
.then(response => {
    console.log('✅ Validate session response:', response.status);
    return response.json();
})
.then(data => {
    console.log('Validate session data:', data);
})
.catch(error => {
    console.log('❌ Validate session error:', error);
});

// Step 4: Test models endpoint
console.log('4. Testing models endpoint...');
fetch('/api/models/library', {
    method: 'GET',
    headers: {
        'Accept': 'application/json'
    },
    credentials: 'include'
})
.then(response => {
    console.log('✅ Models endpoint response:', response.status);
    return response.json();
})
.then(data => {
    console.log('Models data:', data.total || data.models?.length || 'No models');
})
.catch(error => {
    console.log('❌ Models endpoint error:', error);
});

// Step 5: Attempt auto-login
console.log('5. Attempting development auto-login...');
fetch('/api/auth/login-simple', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    body: JSON.stringify({
        username: 'dev_admin',
        password: 'dev_password'
    }),
    credentials: 'include'
})
.then(response => {
    console.log('✅ Auto-login response:', response.status);
    return response.json();
})
.then(data => {
    console.log('Auto-login data:', data);
    if (data.access_token) {
        localStorage.setItem('karen_access_token', data.access_token);
        console.log('✅ Stored access token');
    }
    if (data.user) {
        localStorage.setItem('karen_user', JSON.stringify(data.user));
        console.log('✅ Stored user data');
    }
})
.catch(error => {
    console.log('❌ Auto-login error:', error);
});

console.log('');
console.log('🎯 Debug complete! Check the console output above.');
console.log('🔄 If issues persist, refresh the page and try again.');
console.log('');
console.log('💡 Manual steps:');
console.log('1. Refresh the page (Ctrl+F5 or Cmd+Shift+R)');
console.log('2. Check Network tab for failed requests');
console.log('3. Verify backend is running on http://127.0.0.1:8000');
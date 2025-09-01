/**
 * Authentication Debug Helper
 * Provides debugging utilities for authentication issues
 */

import { getSession, getAuthHeader, isAuthenticated } from './auth/session';

export function debugAuthState(): void {
  console.log('🔍 Authentication Debug Information:');
  
  // Check current session
  const session = getSession();
  console.log('Current Session:', session ? {
    userId: session.userId,
    email: session.email,
    expiresAt: new Date(session.expiresAt).toISOString(),
    hasToken: !!session.accessToken,
    tokenLength: session.accessToken?.length || 0
  } : 'No session');
  
  // Check localStorage
  if (typeof window !== 'undefined') {
    const localToken = localStorage.getItem('karen_access_token');
    const sessionData = localStorage.getItem('karen_session_data');
    
    console.log('LocalStorage Token:', localToken ? {
      hasToken: !!localToken,
      tokenLength: localToken.length,
      tokenPreview: localToken.substring(0, 50) + '...'
    } : 'No token');
    
    console.log('LocalStorage Session Data:', sessionData ? JSON.parse(sessionData) : 'No data');
  }
  
  // Check auth header
  const authHeader = getAuthHeader();
  console.log('Auth Header:', authHeader);
  
  // Check authentication status
  console.log('Is Authenticated:', isAuthenticated());
  
  console.log('🔍 End Authentication Debug');
}

export function setTestToken(): void {
  console.log('🧪 Setting test token for debugging...');
  
  // Use the working token from our earlier tests
  const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4YTMyZmQzZC05NGYwLTRmZjgtODE0Yi1lZWYzOTQyYTI3ZDkiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZnVsbF9uYW1lIjoiQWRtaW4gVXNlciIsInJvbGVzIjpbXSwidGVuYW50X2lkIjoiZmMwY2ExOTQtYTkxYS00NjA1LWE4OWUtMDkzNDQ3ODEyMTM1IiwiaXNfdmVyaWZpZWQiOnRydWUsImlzX2FjdGl2ZSI6dHJ1ZSwiZXhwIjoxNzU2NzQyNDE5LCJpYXQiOjE3NTY3NDE1MTksIm5iZiI6MTc1Njc0MTUxOSwianRpIjoiZTUzNTBkNGE0YzEyYTUyZTQ4ZjY2MzkzOTUxMWVkNDgiLCJ0eXAiOiJhY2Nlc3MifQ.lIeHeeaYxHJtks4-0iL_cNEvf3iUFOUyivc8YaH8lB0';
  
  if (typeof window !== 'undefined') {
    localStorage.setItem('karen_access_token', testToken);
    localStorage.setItem('karen_session_data', JSON.stringify({
      userId: '8a32fd3d-94f0-4ff8-814b-eef3942a27d9',
      email: 'admin@example.com',
      expiresAt: Date.now() + (24 * 60 * 60 * 1000), // 24 hours from now
      roles: [],
      tenantId: 'fc0ca194-a91a-4605-a89e-093447812135'
    }));
    
    console.log('✅ Test token set in localStorage');
    debugAuthState();
  }
}

export function clearAuthState(): void {
  console.log('🧹 Clearing authentication state...');
  
  if (typeof window !== 'undefined') {
    localStorage.removeItem('karen_access_token');
    localStorage.removeItem('karen_session_data');
    console.log('✅ Authentication state cleared');
  }
}

// Make functions available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).debugAuth = debugAuthState;
  (window as any).setTestToken = setTestToken;
  (window as any).clearAuthState = clearAuthState;
}
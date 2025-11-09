/**
 * Authentication Debug Helper
 * Provides debugging utilities for authentication issues
 */
import { getSession, isAuthenticated, hasSessionCookie, getCurrentUser } from './auth/session';
export function debugAuthState(): void {
  // Check current session (in-memory)
  const session = getSession();
  console.log('Current Session (in-memory):', session ? {
    userId: session.userId,
    email: session.email,
    roles: session.roles,
    tenantId: session.tenantId
  } : 'No session');
  // Check current user
  const currentUser = getCurrentUser();
  // Check session cookie
  const hasCookie = hasSessionCookie();
  // Check document.cookie if available
  if (typeof document !== 'undefined') {
    const cookies = document.cookie;
    const sessionCookie = cookies.split(';').find(cookie => cookie.trim().startsWith('session_id='));
  }
  // Check authentication status
  console.log('Is Authenticated:', isAuthenticated());
}
export function setTestSession(): void {
  // Set a test session cookie (this would normally be set by the server)
  if (typeof document !== 'undefined') {
    document.cookie = 'session_id=test_session_123; path=/';
    debugAuthState();
  }
}
export function clearAuthState(): void {
  // Clear session cookie
  if (typeof document !== 'undefined') {
    document.cookie = 'session_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  }
  // Clear in-memory session
  const { clearSession } = require('./auth/session');
  clearSession();
}
// Make functions available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).debugAuth = debugAuthState;
  (window as any).setTestSession = setTestSession;
  (window as any).clearAuthState = clearAuthState;
}

/**
 * Authentication Debug Helper
 * Provides debugging utilities for authentication issues
 */
import {
  getSession,
  isAuthenticated,
  hasSessionCookie,
  getCurrentUser,
  clearSession
} from './auth/session';

interface DebugWindow extends Window {
  debugAuth?: () => void;
  setTestSession?: () => void;
  clearAuthState?: () => void;
}

const getDebugWindow = (): DebugWindow | undefined => {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return window as DebugWindow;
};
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
  console.log('Current User data:', currentUser ?? 'No user loaded');
  // Check session cookie
  const hasCookie = hasSessionCookie();
  console.log('Session cookie flag:', hasCookie);
  // Check document.cookie if available
  if (typeof document !== 'undefined') {
    const cookies = document.cookie;
    const sessionCookie = cookies.split(';').find(cookie => cookie.trim().startsWith('session_id='));
    console.log('Session cookie value:', sessionCookie ?? 'Not found');
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
  clearSession();
}
// Make functions available globally for debugging
const debugWindow = getDebugWindow();
if (debugWindow) {
  debugWindow.debugAuth = debugAuthState;
  debugWindow.setTestSession = setTestSession;
  debugWindow.clearAuthState = clearAuthState;
}

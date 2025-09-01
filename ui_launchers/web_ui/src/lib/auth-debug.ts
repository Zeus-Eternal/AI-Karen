/**
 * Authentication Debug Utilities
 * Helps diagnose 401 authentication errors
 */

import { getSession, isAuthenticated, getCurrentUser } from './auth/session';

export interface AuthDebugInfo {
  hasSession: boolean;
  isValid: boolean;
  sessionExpiry: string | null;
  timeUntilExpiry: number | null;
  user: any;
  tokens: {
    localStorage: boolean;
    sessionStorage: boolean;
  };
  cookies: string[];
}

export function getAuthDebugInfo(): AuthDebugInfo {
  const session = getSession();
  const user = getCurrentUser();
  
  // Check token storage
  const hasLocalStorageToken = typeof window !== 'undefined' && 
    !!localStorage.getItem('karen_access_token');
  const hasSessionStorageToken = typeof window !== 'undefined' && 
    !!sessionStorage.getItem('kari_session_token');
  
  // Get cookies
  const cookies = typeof document !== 'undefined' 
    ? document.cookie.split(';').map(c => c.trim().split('=')[0])
    : [];
  
  return {
    hasSession: !!session,
    isValid: isAuthenticated(),
    sessionExpiry: session ? new Date(session.expiresAt).toISOString() : null,
    timeUntilExpiry: session ? session.expiresAt - Date.now() : null,
    user,
    tokens: {
      localStorage: hasLocalStorageToken,
      sessionStorage: hasSessionStorageToken,
    },
    cookies,
  };
}

export function logAuthStatus(): void {
  const info = getAuthDebugInfo();
  console.group('🔐 Authentication Status');
  console.log('Has Session:', info.hasSession);
  console.log('Is Valid:', info.isValid);
  console.log('Session Expiry:', info.sessionExpiry);
  console.log('Time Until Expiry:', info.timeUntilExpiry ? `${Math.round(info.timeUntilExpiry / 1000)}s` : 'N/A');
  console.log('User:', info.user);
  console.log('Tokens:', info.tokens);
  console.log('Cookies:', info.cookies);
  console.groupEnd();
}

export function checkAuthBeforeRequest(endpoint: string): boolean {
  const info = getAuthDebugInfo();
  
  // Skip auth check for public endpoints
  const publicEndpoints = ['/api/health', '/api/auth/login', '/api/auth/refresh'];
  if (publicEndpoints.some(ep => endpoint.includes(ep))) {
    return true;
  }
  
  if (!info.isValid) {
    console.warn(`🚫 Making request to ${endpoint} without valid authentication`);
    logAuthStatus();
    return false;
  }
  
  // Warn if token expires soon (within 2 minutes)
  if (info.timeUntilExpiry && info.timeUntilExpiry < 120000) {
    console.warn(`⏰ Token expires soon for ${endpoint} (${Math.round(info.timeUntilExpiry / 1000)}s remaining)`);
  }
  
  return true;
}
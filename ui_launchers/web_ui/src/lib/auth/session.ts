/**
 * Frontend Session Management System
 * 
 * Implements in-memory access token storage with automatic expiry tracking,
 * silent session rehydration, token refresh utilities, and auth header injection.
 * 
 * Requirements: 1.1, 1.2, 1.3, 5.1
 */

import { getApiClient } from '@/lib/api-client';
import { isDevLoginEnabled, isProductionEnvironment, isSimpleAuthEnabled } from '@/lib/auth/env';

const SIMPLE_AUTH_ENABLED = isSimpleAuthEnabled();
const DEV_LOGIN_ENABLED = isDevLoginEnabled();
const IS_PRODUCTION = isProductionEnvironment();

// Types for session management
export interface SessionData {
  accessToken: string;
  expiresAt: number;
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
}

export interface TokenRefreshResponse {
  access_token: string;
  expires_in: number;
  user_data: {
    user_id: string;
    email: string;
    roles: string[];
    tenant_id: string;
  };
}

// In-memory session storage (cleared on page refresh)
let currentSession: SessionData | null = null;
let refreshPromise: Promise<void> | null = null;
let bootPromise: Promise<void> | null = null;

/**
 * Store session data in memory with automatic expiry tracking
 */
export function setSession(sessionData: SessionData): void {
  currentSession = sessionData;
  
  // Also store the access token in localStorage for API calls
  if (typeof window !== 'undefined' && sessionData.accessToken) {
    try {
      localStorage.setItem('karen_access_token', sessionData.accessToken);
      // Also store session data for debugging
      localStorage.setItem('karen_session_data', JSON.stringify({
        userId: sessionData.userId,
        email: sessionData.email,
        expiresAt: sessionData.expiresAt,
        roles: sessionData.roles,
        tenantId: sessionData.tenantId
      }));
      console.log('Session stored successfully:', {
        userId: sessionData.userId,
        email: sessionData.email,
        expiresAt: new Date(sessionData.expiresAt).toISOString(),
        hasToken: !!sessionData.accessToken
      });
    } catch (error) {
      console.warn('Failed to store access token in localStorage:', error);
    }
  }
}

/**
 * Get current session data from memory
 */
export function getSession(): SessionData | null {
  return currentSession;
}

/**
 * Clear current session from memory
 */
export function clearSession(): void {
  currentSession = null;
  refreshPromise = null;
  bootPromise = null;
  
  // Also clear the access token from localStorage
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem('karen_access_token');
      localStorage.removeItem('karen_session_data');
      console.log('Session cleared successfully');
    } catch (error) {
      console.warn('Failed to clear access token from localStorage:', error);
    }
  }
}

/**
 * Check if current session is valid (not expired)
 */
export function isSessionValid(): boolean {
  if (!currentSession) {
    return false;
  }
  
  // Check if token expires within the next 30 seconds (buffer for network latency)
  const bufferTime = 30 * 1000; // 30 seconds in milliseconds
  return Date.now() + bufferTime < currentSession.expiresAt;
}

/**
 * Get auth header for API calls
 * Returns Authorization header with Bearer token if session is valid
 */
export function getAuthHeader(): Record<string, string> {
  // First try to get from current session
  if (currentSession) {
    if (currentSession.accessToken !== 'validated' && isSessionValid()) {
      console.log('Using current session token for auth header');
      return {
        'Authorization': `Bearer ${currentSession.accessToken}`
      };
    }
    // Even if accessToken is 'validated', session might be valid via HttpOnly cookie
    // In this case, we should let the backend handle session validation
    if (isSessionValid()) {
      console.log('Session validated via cookie, proceeding without Authorization header');
      return {};
    }
  }
  
  // Fallback to localStorage if current session is not available or invalid
  if (typeof window !== 'undefined') {
    try {
      const accessToken = localStorage.getItem('karen_access_token');
      if (accessToken && accessToken !== 'null' && accessToken !== 'undefined') {
        console.log('Using localStorage token for auth header');
        return {
          'Authorization': `Bearer ${accessToken}`
        };
      }
    } catch (error) {
      console.warn('Failed to get access token from localStorage:', error);
    }
  }
  
  console.log('No valid auth token available for header');
  return {};
}

/**
 * Silent session rehydration function that calls refresh on app boot
 * Attempts to restore session using HttpOnly refresh token cookie
 */
export async function bootSession(): Promise<void> {
  // Prevent multiple simultaneous boot attempts
  if (bootPromise) {
    console.log('Boot session already in progress, waiting for existing attempt');
    return bootPromise;
  }
  
  bootPromise = (async () => {
    try {
      const apiClient = getApiClient();
      
      // First, try to validate existing session with a timeout
      try {
        const validateResponse = await apiClient.get('/api/auth/validate-session');
        
        if (validateResponse.data.valid && validateResponse.data.user) {
          // We have a valid session, create session data
          const sessionData: SessionData = {
            accessToken: 'validated', // Placeholder - actual token is in HttpOnly cookie
            expiresAt: Date.now() + (15 * 60 * 1000), // 15 minutes default
            userId: validateResponse.data.user.user_id,
            email: validateResponse.data.user.email,
            roles: validateResponse.data.user.roles || [],
            tenantId: validateResponse.data.user.tenant_id,
          };
          
          setSession(sessionData);
          console.log('Session validated successfully');
          return;
        }
      } catch (validateError: any) {
        // Validation failed, try refresh
        console.log('Session validation failed, attempting refresh:', validateError.message);
      }
      
      // Attempt to refresh token using HttpOnly cookie
      const response = await apiClient.post<TokenRefreshResponse>('/api/auth/refresh', {});
      
      // Calculate expiry time (expires_in is in seconds)
      const expiresAt = Date.now() + (response.data.expires_in * 1000);
      
      // Store session data in memory
      const sessionData: SessionData = {
        accessToken: response.data.access_token,
        expiresAt,
        userId: response.data.user_data.user_id,
        email: response.data.user_data.email,
        roles: response.data.user_data.roles || [],
        tenantId: response.data.user_data.tenant_id,
      };
      
      setSession(sessionData);
      
      console.log('Session rehydrated successfully');
    } catch (error: any) {
      // Silent failure - no session to restore
      console.log('No session to restore:', error.message);
      clearSession();
    } finally {
      bootPromise = null;
    }
  })();
  
  return bootPromise;
}

/**
 * Token refresh utility that handles automatic token renewal
 * Prevents multiple simultaneous refresh attempts
 */
export async function refreshToken(): Promise<void> {
  // Prevent multiple simultaneous refresh attempts
  if (refreshPromise) {
    console.log('Refresh already in progress, waiting for existing attempt');
    return refreshPromise;
  }
  
  refreshPromise = (async () => {
    try {
      const apiClient = getApiClient();
      
      // Call refresh endpoint with HttpOnly cookie
      const response = await apiClient.post<TokenRefreshResponse>('/api/auth/refresh');
      
      // Calculate expiry time
      const expiresAt = Date.now() + (response.data.expires_in * 1000);
      
      // Update session data in memory
      const sessionData: SessionData = {
        accessToken: response.data.access_token,
        expiresAt,
        userId: response.data.user_data.user_id,
        email: response.data.user_data.email,
        roles: response.data.user_data.roles,
        tenantId: response.data.user_data.tenant_id,
      };
      
      setSession(sessionData);
      
      console.log('Token refreshed successfully');
    } catch (error: any) {
      console.error('Token refresh failed:', error.message);
      clearSession();
      throw error;
    } finally {
      refreshPromise = null;
    }
  })();
  
  return refreshPromise;
}

/**
 * Ensure valid token before making API calls
 * Automatically refreshes token if expired or about to expire
 */
export async function ensureToken(): Promise<void> {
  // If no session, try to boot from cookie
  if (!currentSession) {
    try {
      await bootSession();
    } catch (error) {
      console.log('Boot session failed during ensureToken:', error);
      // Don't throw - let the API call proceed and handle auth errors
    }
    return;
  }
  
  // If session is still valid, no action needed
  if (isSessionValid()) {
    return;
  }
  
  // Token is expired or about to expire, refresh it
  try {
    await refreshToken();
  } catch (error) {
    console.log('Token refresh failed during ensureToken:', error);
    // Clear invalid session
    clearSession();
    // Don't throw - let the API call proceed and handle auth errors
  }
}

/**
 * Get current user data from session
 */
export function getCurrentUser(): {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
} | null {
  if (!currentSession) {
    return null;
  }
  
  return {
    userId: currentSession.userId,
    email: currentSession.email,
    roles: currentSession.roles,
    tenantId: currentSession.tenantId,
  };
}

/**
 * Check if user has specific role
 */
export function hasRole(role: string): boolean {
  const user = getCurrentUser();
  return user?.roles.includes(role) ?? false;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return currentSession !== null && isSessionValid();
}

/**
 * Check if current token is long-lived (expires in more than 2 hours)
 */
export function isLongLivedToken(): boolean {
  if (!currentSession) {
    return false;
  }
  
  const timeUntilExpiry = currentSession.expiresAt - Date.now();
  const twoHours = 2 * 60 * 60 * 1000; // 2 hours in milliseconds
  
  return timeUntilExpiry > twoHours;
}

/**
 * Get time until token expiry in human readable format
 */
export function getTokenExpiryInfo(): { expiresIn: string; isLongLived: boolean } | null {
  if (!currentSession) {
    return null;
  }
  
  const timeUntilExpiry = currentSession.expiresAt - Date.now();
  const hours = Math.floor(timeUntilExpiry / (60 * 60 * 1000));
  const minutes = Math.floor((timeUntilExpiry % (60 * 60 * 1000)) / (60 * 1000));
  
  let expiresIn: string;
  if (hours > 0) {
    expiresIn = `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    expiresIn = `${minutes}m`;
  } else {
    expiresIn = 'less than 1m';
  }
  
  return {
    expiresIn,
    isLongLived: isLongLivedToken(),
  };
}

/**
 * Login with credentials and establish session
 */
export async function login(email: string, password: string, totpCode?: string): Promise<void> {
  try {
    console.log('🔐 Auth Session: Starting login process', { email, hasTotp: !!totpCode });
    
    const credentials: any = { email, password };
    if (totpCode) {
      credentials.totp_code = totpCode;
    }

    // Debounce rapid attempts to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 500));

    const DIRECT_FIRST = (process.env.NEXT_PUBLIC_AUTH_DIRECT_FIRST || 'false').toLowerCase() === 'true';
    const DIRECT_BACKEND = (process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/+$/, '');
    const SHORT_TIMEOUT = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || 15000);

    console.log('🔐 Auth Session: Configuration', {
      DIRECT_FIRST,
      DIRECT_BACKEND,
      SHORT_TIMEOUT,
      NODE_ENV: process.env.NODE_ENV,
      NEXT_PUBLIC_AUTH_DIRECT_FIRST: process.env.NEXT_PUBLIC_AUTH_DIRECT_FIRST,
      NEXT_PUBLIC_KAREN_BACKEND_URL: process.env.NEXT_PUBLIC_KAREN_BACKEND_URL,
      NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
      SIMPLE_AUTH_ENABLED,
      DEV_LOGIN_ENABLED,
      IS_PRODUCTION,
    });

    const fetchWithTimeout = async (url: string, init: RequestInit, timeoutMs: number): Promise<Response> => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        console.log('🔐 Auth Session: Attempting fetch to', url);
        const result = await fetch(url, { ...init, signal: controller.signal });
        console.log('🔐 Auth Session: Fetch result', { url, status: result.status, statusText: result.statusText, ok: result.ok });
        return result;
      } catch (err) {
        console.error('🔐 Auth Session: Fetch error', { url, error: (err as Error)?.message || err });
        throw err;
      } finally {
        clearTimeout(timer);
      }
    };

    let response: Response | null = null;

    const attemptLogin = async (url: string): Promise<Response | null> => {
      try {
        console.log('🔐 Auth Session: Attempting login to', url);
        const result = await fetchWithTimeout(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(credentials),
          credentials: 'include',
        }, SHORT_TIMEOUT);
        console.log('🔐 Auth Session: Login attempt result', { url, status: result?.status, ok: result?.ok });
        return result;
      } catch (err) {
        console.error('🔐 Auth Session: Login attempt failed', { url, error: (err as Error)?.message || err });
        return null;
      }
    };

    if (DIRECT_FIRST) {
      console.log('Attempting login via backend API', { DIRECT_BACKEND });
      response = await attemptLogin(`${DIRECT_BACKEND}/api/auth/login`);
    } else {
      console.log('Attempting login via Next proxy');
      response = await attemptLogin('/api/auth/login');
    }

    // Fallbacks if missing/failed or non-OK
    if (!response || !response.ok) {
      const status = response?.status;
      let errorText = '';
      if (response) {
        try { const j = await response.json(); errorText = j?.error || ''; } catch {}
      }
      
      console.log('🔐 Auth Session: Primary login attempt failed', {
        status,
        errorText,
        DIRECT_FIRST,
        responseUrl: response?.url
      });
      
      if (status === 429) {
        throw new Error('Too many login attempts. Please wait a moment and try again.');
      }

      if (DIRECT_FIRST) {
        // Try backend simple-auth mount (/auth/login) for 404/405, otherwise try proxy
        if (response && (status === 404 || status === 405)) {
          if (SIMPLE_AUTH_ENABLED) {
            console.warn(`🔐 Auth Session: Backend /api/auth/login returned ${status}. Trying /auth/login on backend...`);
            response = await attemptLogin(`${DIRECT_BACKEND}/auth/login`);
          } else {
            console.warn('🔐 Auth Session: Backend fallback to /auth/login disabled. Skipping simple auth endpoint.');
          }
        }
        if (!response || !response.ok) {
          console.warn(`🔐 Auth Session: Backend login failed (${status ?? 'no-response'}). Trying Next.js API route...`);
          response = await attemptLogin('/api/auth/login');
        }
      } else {
        // Proxy-first: if 404/405, retry with proxy fallback header (same path)
        if (response && (status === 404 || status === 405)) {
          console.warn(`🔐 Auth Session: Proxy login returned ${status}. Retrying proxy with fallback header...`);
          response = await fetchWithTimeout('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'X-Karen-Auth-Fallback': 'true',
            },
            body: JSON.stringify(credentials),
            credentials: 'include',
          }, SHORT_TIMEOUT);
        }
      }

      // Try simplified login route in all cases if not OK yet
      if (!response || !response.ok) {
        if (SIMPLE_AUTH_ENABLED) {
          console.warn(`🔐 Auth Session: Primary login failed (${status ?? 'no-response'} ${errorText || ''}). Trying /api/auth/login-simple ...`);
          response = await attemptLogin('/api/auth/login-simple');
        } else {
          console.warn('🔐 Auth Session: Simple auth fallback disabled. Skipping /api/auth/login-simple retry.');
        }
      }

      // Dev-only final fallback
      if ((!response || !response.ok) && DEV_LOGIN_ENABLED) {
        console.warn(`🔐 Auth Session: Simplified login failed (${response ? response.status : 'no-response'}). Trying /api/dev-login ...`);
        response = await attemptLogin('/api/dev-login');
      } else if (!response || !response.ok) {
        console.warn('🔐 Auth Session: Dev login fallback disabled. Skipping /api/dev-login retry.');
      }

      if (!response || !response.ok) {
        const statusText = response ? `${response.status}: ${response.statusText}` : 'network error';
        console.error('🔐 Auth Session: All login attempts failed', { statusText });
        throw new Error(`Login failed (${statusText})`);
      }
    }

    console.log('🔐 Auth Session: Login request successful, parsing response', {
      status: response.status,
      statusText: response.statusText,
      url: response.url
    });
    
    const data = await response.json();
    console.log('🔐 Auth Session: Response data received', {
      hasAccessToken: !!data.access_token,
      hasUserData: !!data.user,
      expiresIn: data.expires_in,
      userData: data.user ? { user_id: data.user.user_id, email: data.user.email } : null
    });
    
    const expiresIn = data.expires_in || 86400; // Default 24h
    const expiresAt = Date.now() + (expiresIn * 1000);
    const sessionData: SessionData = {
      accessToken: data.access_token || 'validated',
      expiresAt,
      userId: data.user.user_id,
      email: data.user.email,
      roles: data.user.roles || [],
      tenantId: data.user.tenant_id,
    };
    setSession(sessionData);
    console.log('🔐 Auth Session: Login successful, session established', {
      userId: data.user.user_id,
      email: data.user.email,
      expiresAt: new Date(expiresAt).toISOString(),
      responseUrl: response.url,
      sessionData: {
        hasToken: !!sessionData.accessToken,
        expiresIn: expiresIn,
        rolesCount: sessionData.roles.length
      }
    });

  } catch (error: any) {
    console.error('🔐 Auth Session: Login failed with error:', {
      message: error.message,
      name: error.name,
      stack: error.stack,
      isNetworkError: error.message?.includes('network') || error.message?.includes('fetch'),
      isTimeout: error.name === 'AbortError'
    });
    clearSession();
    throw error;
  }
}

/**
 * Create a long-lived token after successful authentication for API stability
 */
export async function createLongLivedToken(): Promise<void> {
  try {
    const response = await fetch('/api/auth/create-long-lived-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...getAuthHeader(),
      },
      credentials: 'include',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Update session with long-lived token
    if (currentSession) {
      const longLivedExpiresAt = Date.now() + (data.expires_in * 1000);
      
      const updatedSession: SessionData = {
        ...currentSession,
        accessToken: data.access_token,
        expiresAt: longLivedExpiresAt,
      };
      
      setSession(updatedSession);
      
      console.log('Long-lived token created successfully, expires in 24 hours');
    }
    
  } catch (error: any) {
    console.error('Failed to create long-lived token:', error.message);
    throw error;
  }
}

/**
 * Logout and clear session
 */
export async function logout(): Promise<void> {
  try {
    const apiClient = getApiClient();
    
    // Call logout endpoint to invalidate server-side session
    await apiClient.post('/api/auth/logout');
  } catch (error) {
    // Logout should not throw errors, just log them
    console.warn('Logout request failed:', error);
  } finally {
    // Always clear local session
    clearSession();
  }
}

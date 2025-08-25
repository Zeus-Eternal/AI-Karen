/**
 * Frontend Session Management System
 * 
 * Implements in-memory access token storage with automatic expiry tracking,
 * silent session rehydration, token refresh utilities, and auth header injection.
 * 
 * Requirements: 1.1, 1.2, 1.3, 5.1
 */

import { getApiClient } from '@/lib/api-client';

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

/**
 * Store session data in memory with automatic expiry tracking
 */
export function setSession(sessionData: SessionData): void {
  currentSession = sessionData;
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
  if (!currentSession || !isSessionValid()) {
    return {};
  }
  
  return {
    'Authorization': `Bearer ${currentSession.accessToken}`
  };
}

/**
 * Silent session rehydration function that calls refresh on app boot
 * Attempts to restore session using HttpOnly refresh token cookie
 */
export async function bootSession(): Promise<void> {
  try {
    const apiClient = getApiClient();
    
    // First, try to validate existing session
    try {
      const validateResponse = await apiClient.get('/api/auth/validate-session');
      
      if (validateResponse.data.valid && validateResponse.data.user) {
        // We have a valid session, create session data
        const sessionData: SessionData = {
          accessToken: 'validated', // Placeholder - actual token is in HttpOnly cookie
          expiresAt: Date.now() + (15 * 60 * 1000), // 15 minutes default
          userId: validateResponse.data.user.user_id,
          email: validateResponse.data.user.email,
          roles: validateResponse.data.user.roles,
          tenantId: validateResponse.data.user.tenant_id,
        };
        
        setSession(sessionData);
        console.log('Session validated successfully');
        return;
      }
    } catch (validateError) {
      // Validation failed, try refresh
      console.log('Session validation failed, attempting refresh');
    }
    
    // Attempt to refresh token using HttpOnly cookie
    const response = await apiClient.post<TokenRefreshResponse>('/api/auth/refresh');
    
    // Calculate expiry time (expires_in is in seconds)
    const expiresAt = Date.now() + (response.data.expires_in * 1000);
    
    // Store session data in memory
    const sessionData: SessionData = {
      accessToken: response.data.access_token,
      expiresAt,
      userId: response.data.user_data.user_id,
      email: response.data.user_data.email,
      roles: response.data.user_data.roles,
      tenantId: response.data.user_data.tenant_id,
    };
    
    setSession(sessionData);
    
    console.log('Session rehydrated successfully');
  } catch (error: any) {
    // Silent failure - no session to restore
    console.log('No session to restore:', error.message);
    clearSession();
  }
}

/**
 * Token refresh utility that handles automatic token renewal
 * Prevents multiple simultaneous refresh attempts
 */
export async function refreshToken(): Promise<void> {
  // Prevent multiple simultaneous refresh attempts
  if (refreshPromise) {
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
    await bootSession();
    return;
  }
  
  // If session is still valid, no action needed
  if (isSessionValid()) {
    return;
  }
  
  // Token is expired or about to expire, refresh it
  await refreshToken();
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
 * Login with credentials and establish session
 */
export async function login(email: string, password: string, totpCode?: string): Promise<void> {
  try {
    const apiClient = getApiClient();
    
    const credentials: any = { email, password };
    if (totpCode) {
      credentials.totp_code = totpCode;
    }
    
    const response = await apiClient.post<TokenRefreshResponse>('/api/auth/login', credentials);
    
    // Calculate expiry time
    const expiresAt = Date.now() + (response.data.expires_in * 1000);
    
    // Store session data in memory
    const sessionData: SessionData = {
      accessToken: response.data.access_token,
      expiresAt,
      userId: response.data.user_data.user_id,
      email: response.data.user_data.email,
      roles: response.data.user_data.roles,
      tenantId: response.data.user_data.tenant_id,
    };
    
    setSession(sessionData);
    
    console.log('Login successful');
  } catch (error: any) {
    console.error('Login failed:', error.message);
    clearSession();
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
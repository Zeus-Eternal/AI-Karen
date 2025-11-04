/**
 * Simplified Session Management System
 *
 * Implements lightweight cookie-based session detection with single API call validation.
 * Removes complex token management, retry logic, and error handling abstractions.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */
// Simplified types for session management
export interface SessionData {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
  role?: 'super_admin' | 'admin' | 'user';
  permissions?: string[];
}
// Simple in-memory session storage
let currentSession: SessionData | null = null;
/**
 * Store session data in memory (no localStorage or token management)
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
}
/**
 * Check if current session exists (simple boolean check)
 */
export function isSessionValid(): boolean {
  return currentSession !== null;
}
/**
 * Check if session cookie exists in browser
 */
export function hasSessionCookie(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  // Check for auth token cookie (backend sets 'auth_token' cookie)
  return document.cookie.includes('auth_token=');
}
/**
 * Simple session validation that makes single API call
 * No retry logic or complex error handling - uses cookie-based authentication
 */
export async function validateSession(): Promise<boolean> {
  try {
    // Use direct fetch with cookie credentials for simple validation
    const response = await fetch("/api/auth/validate-session", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      credentials: "include", // Include cookies for authentication
    });

    if (response.ok) {
      const data = await response.json();
      if (data.valid && (data.user || data.user_data)) {
        // Store session data - handle both user and user_data response formats
        const userData = data.user || data.user_data;
        const sessionData: SessionData = {
          userId: userData.user_id,
          email: userData.email,
          roles: userData.roles || [],
          tenantId: userData.tenant_id,
          role: userData.role || determineUserRole(userData.roles || []),
          permissions: userData.permissions,
        };
        setSession(sessionData);
        return true;
      }
    }
    // Invalid session or error response
    clearSession();
    return false;
  } catch (error: any) {
    // Any error means invalid session
    clearSession();
    return false;
  }
}
/**
 * Get current user data from session
 */
export function getCurrentUser(): SessionData | null {
  return currentSession;
}
/**
 * Check if user has specific role
 */
export function hasRole(role: string): boolean {
  if (!currentSession) return false;
  // Check the new role field first, then fall back to roles array
  if (currentSession.role) {
    return currentSession.role === role;
  }
  return currentSession.roles.includes(role);
}
/**
 * Check if user has specific permission
 */
export function hasPermission(permission: string): boolean {
  if (!currentSession) return false;
  // Check permissions array if available
  if (currentSession.permissions) {
    return currentSession.permissions.includes(permission);
  }
  // Default permissions based on role
  const rolePermissions = getRolePermissions(currentSession.role || (currentSession.roles[0] as 'super_admin' | 'admin' | 'user'));
  return rolePermissions.includes(permission);
}
/**
 * Check if user is admin (admin or super_admin)
 */
export function isAdmin(): boolean {
  return hasRole('admin') || hasRole('super_admin');
}
/**
 * Check if user is super admin
 */
export function isSuperAdmin(): boolean {
  return hasRole('super_admin');
}
/**
 * Helper function to determine primary role from roles array
 */
function determineUserRole(roles: string[]): 'super_admin' | 'admin' | 'user' {
  if (roles.includes('super_admin')) return 'super_admin';
  if (roles.includes('admin')) return 'admin';
  return 'user';
}
/**
 * Helper function to get default permissions for a role
 */
function getRolePermissions(role: 'super_admin' | 'admin' | 'user'): string[] {
  switch (role) {
    case 'super_admin':
      return [
        'user_management',
        'admin_management', 
        'system_config',
        'audit_logs',
        'security_settings',
        'user_create',
        'user_edit',
        'user_delete',
        'admin_create',
        'admin_edit',
        'admin_delete'
      ];
    case 'admin':
      return [
        'user_management',
        'user_create',
        'user_edit',
        'user_delete'
      ];
    case 'user':
    default:
      return [];
  }
}
/**
 * Check if user is authenticated (simple boolean check)
 */
export function isAuthenticated(): boolean {
  return currentSession !== null;
}
/**
 * Simple login with credentials - single API call, no complex retry logic
 */
export async function login(
  email: string,
  password: string,
  totpCode?: string
): Promise<void> {
  try {
    const credentials: any = { email, password };
    if (totpCode) {
      credentials.totp_code = totpCode;
    }
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(credentials),
      credentials: "include", // Include cookies for session management
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error || errorData.detail || errorData.message || `Login failed: ${response.status}`;
      throw new Error(errorMessage);
    }
    const data = await response.json();
    // Store simple session data - handle both user and user_data response formats
    const userData = data.user || data.user_data;
    if (!userData) {
      throw new Error('No user data in login response');
    }
    const sessionData: SessionData = {
      userId: userData.user_id,
      email: userData.email,
      roles: userData.roles || [],
      tenantId: userData.tenant_id,
      role: userData.role || determineUserRole(userData.roles || []),
      permissions: userData.permissions,
    };
    setSession(sessionData);
  } catch (error: any) {
    clearSession();
    throw error;
  }
}
/**
 * Simple logout that clears session cookie
 * No complex error handling - just clear session and cookie
 */
export async function logout(): Promise<void> {
  // Always clear local session first
  clearSession();
  try {
    // Call logout endpoint to clear server-side session cookie
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
  } catch (error) {
    // Logout should not throw errors, just log them
  }
}

/**
 * Simplified Session Management System
 *
 * Implements lightweight cookie-based session detection with single API call validation.
 * Removes complex token management, retry logic, and error handling abstractions.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */
import {
  getHighestRole,
  normalizePermission,
  normalizePermissionList,
  ROLE_PERMISSIONS,
  type UserRole,
} from "@/components/security/rbac-shared";

const ACCESS_TOKEN_STORAGE_KEY = "karen_access_token";

const tokenStorageAvailable = (): boolean =>
  typeof window !== "undefined" && typeof window.localStorage !== "undefined";

function getStoredAccessToken(): string | null {
  if (!tokenStorageAvailable()) {
    return null;
  }
  try {
    return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

function setStoredAccessToken(token: string): void {
  if (!tokenStorageAvailable()) {
    return;
  }
  try {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
  } catch {
    // ignore storage failures
  }
}

export function persistAccessToken(token: string): void {
  setStoredAccessToken(token);
}

export function clearPersistedAccessToken(): void {
  clearStoredAccessToken();
}

function clearStoredAccessToken(): void {
  if (!tokenStorageAvailable()) {
    return;
  }
  try {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  } catch {
    // ignore storage failures
  }
}

// Simplified types for session management
export interface SessionData {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
  role?: UserRole;
  permissions?: string[];
}
// Simple in-memory session storage
let currentSession: SessionData | null = null;
/**
 * Store session data in memory (no localStorage or token management)
 */
export function setSession(sessionData: SessionData): void {
  currentSession = {
    ...sessionData,
    permissions: normalizePermissionList(sessionData.permissions ?? []),
  };
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
  clearStoredAccessToken();
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
  const cookieString = document.cookie || "";
  const cookieNames = ["auth_token", "kari_session", "session_token"];
  if (cookieNames.some((name) => cookieString.includes(`${name}=`))) {
    return true;
  }

  return Boolean(getStoredAccessToken());
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
          role: userData.role || getHighestRole(userData.roles || []),
          permissions: normalizePermissionList(userData.permissions),
        };
        setSession(sessionData);
        return true;
      }
    }
    // Invalid session or error response
    clearSession();
    return false;
  } catch {
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
  const canonical = normalizePermission(permission);
  if (!canonical) return false;
  // Check permissions array if available
  if (currentSession.permissions) {
    return normalizePermissionList(currentSession.permissions).includes(canonical);
  }
  // Default permissions based on role (use unified rbac-shared)
  const role = currentSession.role || getHighestRole(currentSession.roles);
  const rolePermissions = ROLE_PERMISSIONS[role] || [];
  return rolePermissions.includes(canonical);
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
    const credentials: Record<string, string> = { email, password };
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
    if (data.access_token) {
      setStoredAccessToken(data.access_token);
    }
    const sessionData: SessionData = {
      userId: userData.user_id,
      email: userData.email,
      roles: userData.roles || [],
      tenantId: userData.tenant_id,
      role: userData.role || getHighestRole(userData.roles || []),
      permissions: userData.permissions,
    };
    setSession(sessionData);
  } catch (error: unknown) {
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
  } catch {
    // Logout should not throw errors, just log them
  }
}

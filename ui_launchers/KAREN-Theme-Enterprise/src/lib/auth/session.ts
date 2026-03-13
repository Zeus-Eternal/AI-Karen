/**
 * Session Compatibility Layer
 * 
 * This file provides backward compatibility with the old session interface
 * while using the new unified authentication system underneath.
 */

import { authService } from "./core/AuthService";
import { tokenService } from "./core/TokenService";
import { sessionService } from "./core/SessionService";
import type { RoleName } from "@/lib/security/rbac/types";

// Re-export types for compatibility
export interface SessionData {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
  role?: RoleName;
  permissions?: string[];
}

/**
 * Store session data (delegates to AuthService)
 */
export function setSession(sessionData: SessionData): void {
  const user = authService.getCurrentUser();
  if (!user) {
    // If no user in auth service, create one from session data
    authService.setCurrentUser({
      userId: sessionData.userId,
      email: sessionData.email,
      roles: sessionData.roles as RoleName[],
      tenantId: sessionData.tenantId,
      role: sessionData.role,
      permissions: sessionData.permissions,
    });
  }
}

/**
 * Get current session data (delegates to AuthService)
 */
export function getSession(): SessionData | null {
  const user = authService.getCurrentUser();
  if (!user) {
    return null;
  }

  return {
    userId: user.userId,
    email: user.email,
    roles: user.roles,
    tenantId: user.tenantId || "default",
    role: user.role,
    permissions: user.permissions,
  };
}

/**
 * Clear current session (delegates to AuthService)
 */
export function clearSession(): void {
  authService.clearAuthState();
}

/**
 * Check if current session exists (delegates to AuthService)
 */
export function isSessionValid(): boolean {
  return authService.getCurrentUser() !== null;
}

/**
 * Check if session cookie exists (delegates to SessionService)
 */
export function hasSessionCookie(): boolean {
  return sessionService.hasSessionCookie();
}

/**
 * Validate session (delegates to AuthService)
 */
export async function validateSession(): Promise<boolean> {
  return await authService.checkAuth();
}

/**
 * Get current user data (delegates to AuthService)
 */
export function getCurrentUser(): SessionData | null {
  const user = authService.getCurrentUser();
  if (!user) {
    return null;
  }

  return {
    userId: user.userId,
    email: user.email,
    roles: user.roles,
    tenantId: user.tenantId || "default",
    role: user.role,
    permissions: user.permissions,
  };
}

/**
 * Check if user has specific role (delegates to AuthService)
 */
export function hasRole(role: string): boolean {
  return authService.hasRole(role as RoleName);
}

/**
 * Check if user has specific permission (delegates to AuthService)
 */
export function hasPermission(permission: string): boolean {
  return authService.hasPermission(permission);
}

/**
 * Check if user is admin (delegates to AuthService)
 */
export function isAdmin(): boolean {
  return authService.isAdmin();
}

/**
 * Check if user is super admin (delegates to AuthService)
 */
export function isSuperAdmin(): boolean {
  return authService.isSuperAdmin();
}

/**
 * Check if user is authenticated (delegates to AuthService)
 */
export function isAuthenticated(): boolean {
  return authService.getCurrentUser() !== null;
}

/**
 * Login with credentials (delegates to AuthService)
 */
export async function login(
  email: string,
  password: string,
  totpCode?: string
): Promise<void> {
  await authService.login({
    email,
    password,
    totp_code: totpCode,
  });
}

/**
 * Logout (delegates to AuthService)
 */
export async function logout(): Promise<void> {
  await authService.logout();
}

/**
 * Persist access token (delegates to TokenService)
 */
export function persistAccessToken(token: string): void {
  tokenService.setToken(token);
}

/**
 * Clear persisted access token (delegates to TokenService)
 */
export function clearPersistedAccessToken(): void {
  tokenService.clearToken();
}

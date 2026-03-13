/**
 * Authentication Utilities
 * 
 * Common authentication patterns, helper functions, and type definitions
 * for use throughout the application.
 */

import type { RoleName } from "@/lib/security/rbac/types";
import { authService } from "@/lib/auth/core/AuthService";
import { tokenService } from "@/lib/auth/core/TokenService";
import { sessionService } from "@/lib/auth/core/SessionService";

// Types
export interface LoginFormData {
  email: string;
  password: string;
  totp_code?: string;
  remember_me?: boolean;
}

export interface RegisterFormData {
  email: string;
  password: string;
  confirm_password: string;
  first_name?: string;
  last_name?: string;
  totp_code?: string;
}

export interface ResetPasswordFormData {
  email: string;
}

export interface NewPasswordFormData {
  token: string;
  password: string;
  confirm_password: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: {
    user_id: string;
    email: string;
    roles: RoleName[];
    role?: RoleName;
    permissions?: string[];
  };
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
}

export interface AuthError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// Error codes
export const AUTH_ERROR_CODES = {
  INVALID_CREDENTIALS: "invalid_credentials",
  USER_NOT_FOUND: "user_not_found",
  INVALID_TOKEN: "invalid_token",
  TOKEN_EXPIRED: "token_expired",
  SESSION_EXPIRED: "session_expired",
  PERMISSION_DENIED: "permission_denied",
  ACCOUNT_LOCKED: "account_locked",
  ACCOUNT_DISABLED: "account_disabled",
  EMAIL_NOT_VERIFIED: "email_not_verified",
  INVALID_TOTP: "invalid_totp",
  NETWORK_ERROR: "network_error",
  UNKNOWN_ERROR: "unknown_error",
} as const;

// Auth status types
export type AuthStatus = 
  | "loading" 
  | "authenticated" 
  | "unauthenticated" 
  | "error";

// Helper functions

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return authService.getCurrentUser() !== null;
}

/**
 * Check if user has a specific role
 */
export function hasRole(role: RoleName): boolean {
  return authService.hasRole(role);
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(permission: string): boolean {
  return authService.hasPermission(permission);
}

/**
 * Check if user is admin
 */
export function isAdmin(): boolean {
  return authService.isAdmin();
}

/**
 * Check if user is super admin
 */
export function isSuperAdmin(): boolean {
  return authService.isSuperAdmin();
}

/**
 * Get current user
 */
export function getCurrentUser() {
  return authService.getCurrentUser();
}

/**
 * Get authentication status
 */
export function getAuthStatus(): AuthStatus {
  const authState = authService.getAuthState();
  
  if (authState.isLoading) {
    return "loading";
  }
  
  if (authState.error) {
    return "error";
  }
  
  return isAuthenticated() ? "authenticated" : "unauthenticated";
}

/**
 * Get authentication error
 */
export function getAuthError(): string | null {
  const authState = authService.getAuthState();
  return authState.error;
}

/**
 * Clear authentication error
 */
export function clearAuthError(): void {
  authService.clearError();
}

/**
 * Login with credentials
 */
export async function login(credentials: LoginFormData): Promise<AuthResponse> {
  try {
    await authService.login({
      email: credentials.email,
      password: credentials.password,
      totp_code: credentials.totp_code,
    });

    const user = authService.getCurrentUser();
    
    return {
      success: true,
      message: "Login successful",
      user: user ? {
        user_id: user.userId,
        email: user.email,
        roles: user.roles,
        role: user.role,
        permissions: user.permissions,
      } : undefined,
    };
  } catch (error) {
    const authError = parseAuthError(error);
    return {
      success: false,
      message: authError.message,
    };
  }
}

/**
 * Logout
 */
export async function logout(): Promise<void> {
  await authService.logout();
}

/**
 * Check authentication status
 */
export async function checkAuth(): Promise<boolean> {
  return await authService.checkAuth();
}

/**
 * Parse authentication error
 */
export function parseAuthError(error: unknown): AuthError {
  if (error instanceof Error) {
    const message = error.message.toLowerCase();
    
    if (message.includes("invalid") && message.includes("credential")) {
      return {
        code: AUTH_ERROR_CODES.INVALID_CREDENTIALS,
        message: "Invalid email or password",
      };
    }
    
    if (message.includes("user") && (message.includes("not found") || message.includes("does not exist"))) {
      return {
        code: AUTH_ERROR_CODES.USER_NOT_FOUND,
        message: "User not found",
      };
    }
    
    if (message.includes("token") && message.includes("invalid")) {
      return {
        code: AUTH_ERROR_CODES.INVALID_TOKEN,
        message: "Invalid authentication token",
      };
    }
    
    if (message.includes("token") && message.includes("expired")) {
      return {
        code: AUTH_ERROR_CODES.TOKEN_EXPIRED,
        message: "Authentication token expired",
      };
    }
    
    if (message.includes("session") && message.includes("expired")) {
      return {
        code: AUTH_ERROR_CODES.SESSION_EXPIRED,
        message: "Session expired",
      };
    }
    
    if (message.includes("permission") && (message.includes("denied") || message.includes("not allowed"))) {
      return {
        code: AUTH_ERROR_CODES.PERMISSION_DENIED,
        message: "Permission denied",
      };
    }
    
    if (message.includes("account") && message.includes("locked")) {
      return {
        code: AUTH_ERROR_CODES.ACCOUNT_LOCKED,
        message: "Account is locked",
      };
    }
    
    if (message.includes("account") && message.includes("disabled")) {
      return {
        code: AUTH_ERROR_CODES.ACCOUNT_DISABLED,
        message: "Account is disabled",
      };
    }
    
    if (message.includes("email") && message.includes("verified")) {
      return {
        code: AUTH_ERROR_CODES.EMAIL_NOT_VERIFIED,
        message: "Email not verified",
      };
    }
    
    if (message.includes("totp") || message.includes("2fa")) {
      return {
        code: AUTH_ERROR_CODES.INVALID_TOTP,
        message: "Invalid verification code",
      };
    }
    
    if (message.includes("network") || message.includes("fetch")) {
      return {
        code: AUTH_ERROR_CODES.NETWORK_ERROR,
        message: "Network error, please try again",
      };
    }
    
    return {
      code: AUTH_ERROR_CODES.UNKNOWN_ERROR,
      message: error.message,
    };
  }
  
  return {
    code: AUTH_ERROR_CODES.UNKNOWN_ERROR,
    message: "An unknown error occurred",
  };
}

/**
 * Get authorization header for API requests
 */
export function getAuthHeader(): Record<string, string> {
  return tokenService.getAuthHeader();
}

/**
 * Create authenticated fetch wrapper
 */
export function createAuthenticatedFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const headers = {
    ...init?.headers,
    ...getAuthHeader(),
  };

  return fetch(input, {
    ...init,
    headers,
    credentials: "include",
  });
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 */
export function isStrongPassword(password: string): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long");
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  }
  
  if (!/[0-9]/.test(password)) {
    errors.push("Password must contain at least one number");
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push("Password must contain at least one special character");
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Format role name for display
 */
export function formatRoleName(role: RoleName): string {
  return role
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Get user initials for avatar
 */
export function getUserInitials(email: string): string {
  if (!email) return "";
  
  const [namePart] = email.split("@");
  const parts = namePart.split(".");
  
  if (parts.length > 1) {
    return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
  }
  
  return namePart.substring(0, 2).toUpperCase();
}

/**
 * Check if session is active
 */
export async function isSessionActive(): Promise<boolean> {
  return await sessionService.isSessionActive();
}

/**
 * Refresh session if needed
 */
export async function refreshSessionIfNeeded(): Promise<boolean> {
  return await authService.refreshSession();
}
/**
 * Core Authentication Service
 * 
 * Single source of truth for authentication in the application.
 * Handles login, logout, session management, and authentication state.
 */

import { RBACService } from "@/lib/security/rbac/RBACService";
import type { RoleName } from "@/lib/security/rbac/types";
import { TokenService } from "./TokenService";

// Types
export interface User {
  userId: string;
  email: string;
  roles: RoleName[];
  tenantId?: string;
  role?: RoleName;
  permissions?: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

export interface AuthState {
  isLoading: boolean;
  error: string | null;
  isRefreshing: boolean;
  lastActivity: Date | null;
}

// Auth Service Implementation
export class AuthService {
  private static instance: AuthService | null = null;
  private currentUser: User | null = null;
  private isAuthenticated = false;
  private authState: AuthState = {
    isLoading: false,
    error: null,
    isRefreshing: false,
    lastActivity: null,
  };
  private sessionRefreshTimer: ReturnType<typeof setInterval> | null = null;
  private sessionRefreshInterval = 15 * 60 * 1000; // 15 minutes

  /**
   * Get the singleton instance of the AuthService
   */
  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor() {}

  /**
   * Login with credentials
   */
  public async login(credentials: LoginCredentials): Promise<void> {
    try {
      this.setAuthState({ isLoading: true, error: null });

      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(credentials),
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error || errorData.detail || errorData.message || `Login failed: ${response.status}`;
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const userData = data.user || data.user_data;

      if (!userData) {
        throw new Error("No user data in login response");
      }

      // Store access token if provided
      if (data.access_token) {
        TokenService.getInstance().setToken(data.access_token);
      }

      // Create user object with highest role from RBAC service
      const roles = (userData.roles || []) as RoleName[];
      const highestRole = roles.length > 0 ? RBACService.getInstance().getHighestRole(roles) : undefined;

      const user: User = {
        userId: userData.user_id,
        email: userData.email,
        roles,
        tenantId: userData.tenant_id,
        role: userData.role || highestRole,
        permissions: userData.permissions,
      };

      this.setCurrentUser(user);
      this.setAuthenticated(true);
      this.setAuthState({ isLoading: false, lastActivity: new Date() });

      // Start session refresh timer
      this.startSessionRefreshTimer();

      // Set user in RBAC service
      RBACService.getInstance().setCurrentUser({
        id: user.userId,
        username: user.email,
        email: user.email,
        roles: user.roles,
        is_active: true,
      });
    } catch (error) {
      this.clearAuthState();
      this.setAuthState({ 
        isLoading: false, 
        error: error instanceof Error ? error.message : "Login failed" 
      });
      throw error;
    }
  }

  /**
   * Logout and clear session
   */
  public async logout(): Promise<void> {
    try {
      // Call logout endpoint to clear server-side session
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      this.clearAuthState();
      this.stopSessionRefreshTimer();
      
      // Clear RBAC service user
      RBACService.getInstance().setCurrentUser(null);
      
      // Redirect to login page
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  }

  /**
   * Check if user is authenticated
   */
  public async checkAuth(): Promise<boolean> {
    try {
      // First check if we have a current user
      if (this.currentUser && this.isAuthenticated) {
        this.setAuthState({ lastActivity: new Date() });
        return true;
      }

      // Check for session cookie
      if (!this.hasSessionCookie()) {
        this.clearAuthState();
        return false;
      }

      // Validate session with backend
      const response = await fetch("/api/auth/validate-session", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        const userData = data.user || data.user_data;

        if (data.valid && userData) {
          // Create user object with highest role from RBAC service
          const roles = (userData.roles || []) as RoleName[];
          const highestRole = roles.length > 0 ? RBACService.getInstance().getHighestRole(roles) : undefined;

          const user: User = {
            userId: userData.user_id,
            email: userData.email,
            roles,
            tenantId: userData.tenant_id,
            role: userData.role || highestRole,
            permissions: userData.permissions,
          };

          this.setCurrentUser(user);
          this.setAuthenticated(true);
          this.setAuthState({ error: null, lastActivity: new Date() });

          // Start session refresh timer if not already running
          if (!this.sessionRefreshTimer) {
            this.startSessionRefreshTimer();
          }

          // Set user in RBAC service
          RBACService.getInstance().setCurrentUser({
            id: user.userId,
            username: user.email,
            email: user.email,
            roles: user.roles,
            is_active: true,
          });

          return true;
        }
      }

      this.clearAuthState();
      return false;
    } catch (error) {
      console.error("Session validation failed:", error);
      this.clearAuthState();
      return false;
    }
  }

  /**
   * Refresh session
   */
  public async refreshSession(): Promise<boolean> {
    if (this.authState.isRefreshing) {
      return false;
    }

    this.setAuthState({ isRefreshing: true });

    try {
      const success = await this.checkAuth();
      this.setAuthState({ isRefreshing: false });
      return success;
    } catch (error) {
      console.error("Session refresh failed:", error);
      this.setAuthState({ isRefreshing: false });
      return false;
    }
  }

  /**
   * Check if user has a specific role
   */
  public hasRole(role: RoleName): boolean {
    if (!this.currentUser) {
      return false;
    }

    // Use RBAC service to check role
    const result = RBACService.getInstance().hasRole(role);
    return result.hasRole;
  }

  /**
   * Check if user has a specific permission
   */
  public hasPermission(permission: string): boolean {
    if (!this.currentUser) {
      return false;
    }

    // Use RBAC service to check permission
    const result = RBACService.getInstance().hasPermission(permission);
    return result.hasPermission ?? false;
  }

  /**
   * Check if user is admin
   */
  public isAdmin(): boolean {
    return this.hasRole("admin") || this.hasRole("super_admin");
  }

  /**
   * Check if user is super admin
   */
  public isSuperAdmin(): boolean {
    return this.hasRole("super_admin");
  }

  /**
   * Get current user
   */
  public getCurrentUser(): User | null {
    return this.currentUser;
  }

  /**
   * Get authentication state
   */
  public getAuthState(): AuthState {
    return { ...this.authState };
  }

  /**
   * Clear authentication error
   */
  public clearError(): void {
    this.setAuthState({ error: null });
  }

  /**
   * Set current user
   */
  public setCurrentUser(user: User | null): void {
    this.currentUser = user;
  }

  /**
   * Set authentication status
   */
  private setAuthenticated(authenticated: boolean): void {
    this.isAuthenticated = authenticated;
  }

  /**
   * Set authentication state
   */
  private setAuthState(state: Partial<AuthState>): void {
    this.authState = { ...this.authState, ...state };
  }

  /**
   * Clear authentication state
   */
  public clearAuthState(): void {
    this.setCurrentUser(null);
    this.setAuthenticated(false);
    this.setAuthState({
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: null
    });
    TokenService.getInstance().clearToken();
  }

  /**
   * Check if session cookie exists
   */
  private hasSessionCookie(): boolean {
    if (typeof window === "undefined") {
      return false;
    }

    const cookieString = document.cookie || "";
    const cookieNames = ["auth_token", "kari_session", "session_token"];
    
    return cookieNames.some((name) => cookieString.includes(`${name}=`)) ||
           !!TokenService.getInstance().getToken();
  }

  /**
   * Start session refresh timer
   */
  private startSessionRefreshTimer(): void {
    if (this.sessionRefreshTimer) {
      clearInterval(this.sessionRefreshTimer);
    }

    this.sessionRefreshTimer = setInterval(async () => {
      const success = await this.refreshSession();
      if (!success) {
        console.warn("Automatic session refresh failed, logging out");
        this.logout().catch(console.error);
      }
    }, this.sessionRefreshInterval);
  }

  /**
   * Stop session refresh timer
   */
  private stopSessionRefreshTimer(): void {
    if (this.sessionRefreshTimer) {
      clearInterval(this.sessionRefreshTimer);
      this.sessionRefreshTimer = null;
    }
  }
}

// Export singleton instance
export const authService = AuthService.getInstance();
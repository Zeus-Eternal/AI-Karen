"use client";

import { useCallback, useEffect, useState } from "react";
import type { FC, ReactNode } from "react";
import { AuthContext } from "./auth-context-instance";
import { authService } from "@/lib/auth/core/AuthService";
import type { RoleName } from "@/lib/security/rbac/types";

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

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  authState: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  refreshSession: () => Promise<boolean>;
  clearError: () => void;
  hasRole: (role: RoleName) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
  isLoggingIn: boolean;
}

export interface AuthProviderProps {
  children: ReactNode;
}

// Session refresh timer
const SESSION_REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes

export const AuthProvider: FC<AuthProviderProps> = ({ children }) => {
  // Authentication state - initialize with consistent values to avoid hydration mismatch
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [authState, setAuthState] = useState<AuthState>({
    isLoading: true, // Start with loading true to prevent flash of unauthenticated content
    error: null,
    isRefreshing: false,
    lastActivity: null,
  });

  // Session refresh timer
  const [sessionRefreshTimer, setSessionRefreshTimer] = useState<NodeJS.Timeout | null>(null);

  // Flag to track login in progress - prevents redirect loops
  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);

  // Start session refresh timer
  const startSessionRefreshTimer = useCallback(() => {
    if (sessionRefreshTimer) {
      clearInterval(sessionRefreshTimer);
    }

    const timer = setInterval(async () => {
      const success = await authService.refreshSession();
      if (!success) {
        console.warn("Automatic session refresh failed, logging out");
        authService.logout().catch(console.error);
      }
    }, SESSION_REFRESH_INTERVAL);

    setSessionRefreshTimer(timer);
  }, [sessionRefreshTimer]);

  // Stop session refresh timer
  const stopSessionRefreshTimer = useCallback(() => {
    if (sessionRefreshTimer) {
      clearInterval(sessionRefreshTimer);
      setSessionRefreshTimer(null);
    }
  }, [sessionRefreshTimer]);

  // Login method
  const login = useCallback(async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoggingIn(true);
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

      await authService.login(credentials);
      
      // Get the current user from the auth service
      const currentUser = authService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
        setIsAuthenticated(true);
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          lastActivity: new Date(),
        }));

        // Start session refresh timer
        startSessionRefreshTimer();
        
        // Mark auth success to prevent 401 redirects during grace period
        const { markAuthSuccess } = await import('@/lib/auth-interceptor');
        markAuthSuccess();
      }
    } catch (error) {
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "Login failed",
      }));
      throw error;
    } finally {
      setIsLoggingIn(false);
    }
  }, [startSessionRefreshTimer]);

  // Logout method
  const logout = useCallback(() => {
    authService.logout().catch(console.error);
    
    // Clear local state
    setUser(null);
    setIsAuthenticated(false);
    setAuthState({
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: null,
    });

    // Stop session refresh timer
    stopSessionRefreshTimer();
  }, [stopSessionRefreshTimer]);

  // Check authentication
  const checkAuth = useCallback(async (): Promise<boolean> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

      const isValid = await authService.checkAuth();
      
      if (isValid) {
        const currentUser = authService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          setIsAuthenticated(true);
          setAuthState(prev => ({
            ...prev,
            isLoading: false,
            lastActivity: new Date(),
          }));

          // Start session refresh timer if not already running
          if (!sessionRefreshTimer) {
            startSessionRefreshTimer();
          }

          return true;
        }
      }

      setUser(null);
      setIsAuthenticated(false);
      setAuthState(prev => ({ ...prev, isLoading: false }));
      return false;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : "Authentication check failed",
      }));
      return false;
    }
  }, [sessionRefreshTimer, startSessionRefreshTimer]);

  // Refresh session
  const refreshSession = useCallback(async (): Promise<boolean> => {
    if (authState.isRefreshing) {
      return false;
    }

    setAuthState(prev => ({ ...prev, isRefreshing: true }));

    try {
      const success = await authService.refreshSession();
      
      if (success) {
        const currentUser = authService.getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          setIsAuthenticated(true);
          setAuthState(prev => ({
            ...prev,
            isRefreshing: false,
            lastActivity: new Date(),
          }));
          return true;
        }
      }

      setUser(null);
      setIsAuthenticated(false);
      setAuthState(prev => ({ ...prev, isRefreshing: false }));
      return false;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      setAuthState(prev => ({
        ...prev,
        isRefreshing: false,
        error: error instanceof Error ? error.message : "Session refresh failed",
      }));
      return false;
    }
  }, [authState.isRefreshing]);

  // Clear error
  const clearError = useCallback(() => {
    setAuthState(prev => ({ ...prev, error: null }));
  }, []);

  // Role and permission checking functions
  const hasRole = useCallback((role: RoleName): boolean => {
    return authService.hasRole(role);
  }, []);

  const hasPermission = useCallback((permission: string): boolean => {
    return authService.hasPermission(permission);
  }, []);

  const isAdmin = useCallback((): boolean => {
    return authService.isAdmin();
  }, []);

  const isSuperAdmin = useCallback((): boolean => {
    return authService.isSuperAdmin();
  }, []);

  // Initialize authentication state on mount and cleanup on unmount
  useEffect(() => {
    // Only run on client side
    if (typeof window === "undefined") {
      return;
    }
    
    // Don't check auth if we're on the login page to prevent loops
    if (window.location?.pathname === "/login") {
      setAuthState(prev => ({ ...prev, isLoading: false }));
      return;
    }

    // Only check auth if we're not already authenticated
    if (!isAuthenticated) {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      checkAuth().finally(() => {
        setAuthState(prev => ({ ...prev, isLoading: false }));
      });
    } else {
      setAuthState(prev => (prev.isLoading ? { ...prev, isLoading: false } : prev));
    }

    // Cleanup timer on unmount
    return () => {
      stopSessionRefreshTimer();
    };
  }, [isAuthenticated, checkAuth, stopSessionRefreshTimer]);

  // Memoize the updateActivity function to prevent recreation on each render
  const updateActivity = useCallback(() => {
    if (isAuthenticated) {
      setAuthState(prev => ({ ...prev, lastActivity: new Date() }));
    }
  }, [isAuthenticated]);

  // Update activity timestamp on user interaction
  useEffect(() => {
    // Listen for user activity
    const events = [
      "mousedown",
      "mousemove",
      "keypress",
      "scroll",
      "touchstart",
    ];
    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
    };
  }, [updateActivity]);

  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    authState,
    login,
    logout,
    checkAuth,
    refreshSession,
    clearError,
    hasRole,
    hasPermission,
    isAdmin,
    isSuperAdmin,
    isLoggingIn,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

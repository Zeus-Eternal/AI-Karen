"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import {
  logout as sessionLogout,
  getCurrentUser,
  hasSessionCookie,
} from "@/lib/auth/session";
import {
  getConnectionManager,
  ConnectionError,
  ErrorCategory,
} from "@/lib/connection/connection-manager";
import {
  getTimeoutManager,
  OperationType,
} from "@/lib/connection/timeout-manager";
import { connectivityLogger } from "@/lib/logging";

export interface User {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
  role?: "super_admin" | "admin" | "user";
  permissions?: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

export interface AuthError {
  message: string;
  category: ErrorCategory;
  retryable: boolean;
  statusCode?: number;
  timestamp: Date;
}

export interface AuthState {
  isLoading: boolean;
  error: AuthError | null;
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
  hasRole: (role: "super_admin" | "admin" | "user") => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
}

export interface AuthProviderProps {
  children: ReactNode;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Export the context for testing purposes
export { AuthContext };

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // Enhanced authentication state with error handling and loading states
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [authState, setAuthState] = useState<AuthState>({
    isLoading: false,
    error: null,
    isRefreshing: false,
    lastActivity: null,
  });

  // Connection manager and timeout configuration
  const connectionManager = getConnectionManager();
  const timeoutManager = getTimeoutManager();

  // Session refresh timer
  const sessionRefreshTimer = useRef<NodeJS.Timeout | null>(null);
  const sessionRefreshInterval = 15 * 60 * 1000; // 15 minutes

  // Flag to prevent multiple simultaneous auth checks
  const isCheckingAuth = useRef<boolean>(false);

  // Helper functions - declare these first
  const determineUserRole = (
    roles: string[]
  ): "super_admin" | "admin" | "user" => {
    if (roles.includes("super_admin")) return "super_admin";
    if (roles.includes("admin")) return "admin";
    return "user";
  };

  // Convert technical errors to user-friendly messages
  const getUserFriendlyErrorMessage = (error: ConnectionError): string => {
    switch (error.category) {
      case ErrorCategory.NETWORK_ERROR:
        return "Unable to connect to server. Please check your internet connection and try again.";
      case ErrorCategory.TIMEOUT_ERROR:
        return "Login is taking longer than expected. Please wait or try again.";
      case ErrorCategory.HTTP_ERROR:
        if (error.statusCode === 401) {
          return "Invalid email or password. Please try again.";
        }
        if (error.statusCode === 429) {
          return "Too many login attempts. Please wait a moment and try again.";
        }
        if (error.statusCode && error.statusCode >= 500) {
          return "Authentication service temporarily unavailable. Please try again.";
        }
        return error.message;
      case ErrorCategory.CIRCUIT_BREAKER_ERROR:
        return "Authentication service is temporarily unavailable. Please try again in a few moments.";
      case ErrorCategory.CONFIGURATION_ERROR:
        return "System configuration error. Please contact support.";
      default:
        return error.message;
    }
  };

  // Create standardized auth error from various error types
  const createAuthError = (error: any): AuthError => {
    if (error instanceof ConnectionError) {
      return {
        message: getUserFriendlyErrorMessage(error),
        category: error.category,
        retryable: error.retryable,
        statusCode: error.statusCode,
        timestamp: new Date(),
      };
    }

    if (error instanceof Error) {
      return {
        message: error.message,
        category: ErrorCategory.UNKNOWN_ERROR,
        retryable: true,
        timestamp: new Date(),
      };
    }

    return {
      message: "An unexpected error occurred",
      category: ErrorCategory.UNKNOWN_ERROR,
      retryable: true,
      timestamp: new Date(),
    };
  };

  // Helper function to get default permissions for a role
  const getRolePermissions = (
    role: "super_admin" | "admin" | "user"
  ): string[] => {
    switch (role) {
      case "super_admin":
        return [
          "user_management",
          "admin_management",
          "system_config",
          "audit_logs",
          "security_settings",
          "user_create",
          "user_edit",
          "user_delete",
          "admin_create",
          "admin_edit",
          "admin_delete",
        ];
      case "admin":
        return ["user_management", "user_create", "user_edit", "user_delete"];
      case "user":
      default:
        return [];
    }
  };

  const stopSessionRefreshTimer = useCallback((): void => {
    if (sessionRefreshTimer.current) {
      clearInterval(sessionRefreshTimer.current);
      sessionRefreshTimer.current = null;
    }
  }, []);

  // Enhanced logout with proper cleanup
  const logout = useCallback((): void => {
    const currentUserEmail = user?.email;

    // Stop session refresh timer
    stopSessionRefreshTimer();

    // Clear all authentication state
    setUser(null);
    setIsAuthenticated(false);
    setAuthState({
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: null,
    });

    // Call session logout to clear server-side session cookie
    sessionLogout().catch((error) => {
      const errorObject =
        error instanceof Error ? error : new Error(String(error));
      connectivityLogger.logAuthentication(
        "warn",
        "Logout request failed",
        {
          email: currentUserEmail || undefined,
          success: false,
          failureReason: errorObject.message,
        },
        "logout",
        errorObject
      );
    });

    connectivityLogger.logAuthentication(
      "info",
      "User session terminated",
      {
        email: currentUserEmail || undefined,
        success: true,
      },
      "logout"
    );

    // Immediate redirect to login after logout
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }, [stopSessionRefreshTimer, user]);

  // Session refresh functionality - will be defined after checkAuth
  const refreshSession = useCallback(async (): Promise<boolean> => {
    if (authState.isRefreshing) {
      return false; // Prevent concurrent refresh attempts
    }

    setAuthState((prev) => ({ ...prev, isRefreshing: true }));

    try {
      // Inline session validation to avoid circular dependency
      const currentUser = getCurrentUser();
      if (currentUser && isAuthenticated) {
        setAuthState((prev) => ({
          ...prev,
          lastActivity: new Date(),
          isRefreshing: false,
        }));
        return true;
      }

      if (!hasSessionCookie()) {
        setUser(null);
        setIsAuthenticated(false);
        setAuthState((prev) => ({ ...prev, error: null, isRefreshing: false }));
        return false;
      }

      const validateUrl = "/api/auth/validate-session";
      const timeout = timeoutManager.getTimeout(
        OperationType.SESSION_VALIDATION
      );

      const result = await connectionManager.makeRequest(
        validateUrl,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          credentials: "include",
        },
        {
          timeout,
          retryAttempts: 1,
          exponentialBackoff: false,
        }
      );

      if (result.data.valid && (result.data.user || result.data.user_data)) {
        const userData = result.data.user || result.data.user_data;
        const user: User = {
          userId: userData.user_id,
          email: userData.email,
          roles: userData.roles || [],
          tenantId: userData.tenant_id,
          role: determineUserRole(userData.roles || []),
          permissions: userData.permissions,
        };

        setUser(user);
        setIsAuthenticated(true);
        setAuthState((prev) => ({
          ...prev,
          error: null,
          lastActivity: new Date(),
          isRefreshing: false,
        }));

        return true;
      }

      setUser(null);
      setIsAuthenticated(false);
      setAuthState((prev) => ({ ...prev, error: null, isRefreshing: false }));
      return false;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      setAuthState((prev) => ({ ...prev, isRefreshing: false }));
      return false;
    }
  }, [
    authState.isRefreshing,
    isAuthenticated,
    connectionManager,
    timeoutManager,
  ]);

  // Session refresh timer management
  const startSessionRefreshTimer = useCallback((): void => {
    if (sessionRefreshTimer.current) {
      clearInterval(sessionRefreshTimer.current);
    }

    sessionRefreshTimer.current = setInterval(async () => {
      const success = await refreshSession();
      if (!success) {
        connectivityLogger.logAuthentication(
          "warn",
          "Automatic session refresh failed",
          {
            success: false,
            failureReason: "session_refresh_failed",
          },
          "token_refresh"
        );
        logout();
      }
    }, sessionRefreshInterval);
  }, [refreshSession, logout]);

  // Enhanced login method with improved error handling and ConnectionManager integration
  const login = async (credentials: LoginCredentials): Promise<void> => {
    const authenticationStartTime =
      typeof performance !== "undefined" ? performance.now() : Date.now();

    connectivityLogger.logAuthentication(
      "info",
      "Authentication attempt started",
      {
        email: credentials.email,
        success: false,
        attemptNumber: 1,
      },
      "login"
    );

    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      // Use ConnectionManager for reliable authentication request against the production login endpoint
      const loginUrl = "/api/auth/login";
      const timeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);

      const requestBody = {
        email: credentials.email,
        password: credentials.password,
        ...(credentials.totp_code && { totp_code: credentials.totp_code }),
      };

      const result = await connectionManager.makeRequest(
        "/api/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(requestBody),
          credentials: "include",
        },
        {
          timeout,
          retryAttempts: 2, // Limited retries for authentication
          exponentialBackoff: true,
        }
      );

      // Handle successful login response
      const userData = result.data.user || result.data.user_data;
      if (!userData) {
        throw new ConnectionError(
          "No user data in login response",
          ErrorCategory.CONFIGURATION_ERROR,
          false,
          0
        );
      }

      // Create user object
      const user: User = {
        userId: userData.user_id,
        email: userData.email,
        roles: userData.roles || [],
        tenantId: userData.tenant_id,
        role: determineUserRole(userData.roles || []),
        permissions: userData.permissions,
      };

      // Update authentication state
      setUser(user);
      setIsAuthenticated(true);
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: null,
        lastActivity: new Date(),
      }));

      // Start session refresh timer
      startSessionRefreshTimer();

      connectivityLogger.logAuthentication(
        "info",
        "Authentication successful",
        {
          email: user.email,
          success: true,
        },
        "login",
        undefined,
        {
          startTime: authenticationStartTime,
          duration:
            result.duration ??
            ((typeof performance !== "undefined"
              ? performance.now()
              : Date.now()) - authenticationStartTime),
          retryCount: result.retryCount,
          metadata: {
            statusCode: result.status,
          },
        }
      );

      // Small delay to ensure state is fully updated before callback
      await new Promise((resolve) => setTimeout(resolve, 10));
    } catch (error) {
      // Enhanced error handling with categorization
      const authError = createAuthError(error);

      // Clear authentication state
      setUser(null);
      setIsAuthenticated(false);
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: authError,
      }));

      // Stop any existing session refresh timer
      stopSessionRefreshTimer();

      const errorObject =
        error instanceof Error ? error : new Error(String(error));
      const retryCount =
        error instanceof ConnectionError &&
        typeof error.retryCount === "number"
          ? error.retryCount
          : undefined;

      connectivityLogger.logAuthentication(
        "error",
        "Authentication attempt failed",
        {
          email: credentials.email,
          success: false,
          failureReason: authError.message,
        },
        "login",
        errorObject,
        {
          startTime: authenticationStartTime,
          duration:
            (typeof performance !== "undefined"
              ? performance.now()
              : Date.now()) - authenticationStartTime,
          retryCount,
          metadata: {
            statusCode:
              error instanceof ConnectionError ? error.statusCode : undefined,
          },
        }
      );

      throw error;
    }
  };

  // Role and permission checking functions
  const hasRole = useCallback(
    (role: "super_admin" | "admin" | "user"): boolean => {
      if (!user) return false;

      // Check the new role field first, then fall back to roles array
      if (user.role) {
        return user.role === role;
      }

      // Legacy support: check roles array
      return user.roles.includes(role);
    },
    [user]
  );

  const hasPermission = useCallback(
    (permission: string): boolean => {
      if (!user) return false;

      // Check permissions array if available
      if (user.permissions) {
        return user.permissions.includes(permission);
      }

      // Default permissions based on role
      const rolePermissions = getRolePermissions(
        user.role || (user.roles[0] as "super_admin" | "admin" | "user")
      );
      return rolePermissions.includes(permission);
    },
    [user]
  );

  const isAdmin = useCallback((): boolean => {
    return hasRole("admin") || hasRole("super_admin");
  }, [hasRole]);

  const isSuperAdmin = useCallback((): boolean => {
    return hasRole("super_admin");
  }, [hasRole]);

  // Enhanced authentication check with improved error handling
  const checkAuth = async (): Promise<boolean> => {
    // Prevent multiple simultaneous auth checks
    if (isCheckingAuth.current) {
      connectivityLogger.logAuthentication(
        "debug",
        "Skipped redundant authentication check",
        {
          success: true,
          failureReason: "in_progress",
        },
        "session_validation"
      );
      return isAuthenticated;
    }

    isCheckingAuth.current = true;
    const validationStartTime =
      typeof performance !== "undefined" ? performance.now() : Date.now();

    connectivityLogger.logAuthentication(
      "debug",
      "Starting authentication check",
      {
        success: false,
      },
      "session_validation"
    );

    try {
      // First check if we already have a valid session in memory
      const currentUser = getCurrentUser();
      if (currentUser && isAuthenticated) {
        connectivityLogger.logAuthentication(
          "debug",
          "Using cached authentication state",
          {
            email: currentUser.email,
            success: true,
          },
          "session_validation"
        );
        setAuthState((prev) => ({ ...prev, lastActivity: new Date() }));
        return true;
      }

      // Check for session cookie first
      if (!hasSessionCookie()) {
        connectivityLogger.logAuthentication(
          "info",
          "No session cookie found",
          {
            success: false,
            failureReason: "missing_session_cookie",
          },
          "session_validation"
        );
        setUser(null);
        setIsAuthenticated(false);
        setAuthState((prev) => ({ ...prev, error: null }));
        return false;
      }

      connectivityLogger.logAuthentication(
        "debug",
        "Session cookie detected, validating",
        {
          success: false,
        },
        "session_validation"
      );

      // Use ConnectionManager for session validation
      const validateUrl = "/api/auth/validate-session";
      const timeout = timeoutManager.getTimeout(
        OperationType.SESSION_VALIDATION
      );

      const result = await connectionManager.makeRequest(
        validateUrl,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          credentials: "include",
        },
        {
          timeout,
          retryAttempts: 1, // Single retry for validation
          exponentialBackoff: false,
        }
      );

      if (result.data.valid && (result.data.user || result.data.user_data)) {
        const userData = result.data.user || result.data.user_data;
        const user: User = {
          userId: userData.user_id,
          email: userData.email,
          roles: userData.roles || [],
          tenantId: userData.tenant_id,
          role: determineUserRole(userData.roles || []),
          permissions: userData.permissions,
        };

        setUser(user);
        setIsAuthenticated(true);
        setAuthState((prev) => ({
          ...prev,
          error: null,
          lastActivity: new Date(),
        }));

        // Start session refresh timer if not already running
        if (!sessionRefreshTimer.current) {
          startSessionRefreshTimer();
        }

        connectivityLogger.logAuthentication(
          "info",
          "Session validation succeeded",
          {
            email: user.email,
            success: true,
          },
          "session_validation",
          undefined,
          {
            startTime: validationStartTime,
            duration:
              result.duration ??
              ((typeof performance !== "undefined"
                ? performance.now()
                : Date.now()) - validationStartTime),
            retryCount: result.retryCount,
            metadata: {
              statusCode: result.status,
            },
          }
        );
        return true;
      }

      // Invalid session
      connectivityLogger.logAuthentication(
        "warn",
        "Session validation failed - invalid session data",
        {
          success: false,
          failureReason: "invalid_session",
        },
        "session_validation"
      );
      setUser(null);
      setIsAuthenticated(false);
      setAuthState((prev) => ({ ...prev, error: null }));
      stopSessionRefreshTimer();
      return false;
    } catch (error) {
      // Enhanced error handling
      const authError = createAuthError(error);

      setUser(null);
      setIsAuthenticated(false);
      setAuthState((prev) => ({
        ...prev,
        error: authError.retryable ? authError : null, // Only show retryable errors
      }));
      stopSessionRefreshTimer();

      const errorObject =
        error instanceof Error ? error : new Error(String(error));
      const retryCount =
        error instanceof ConnectionError &&
        typeof error.retryCount === "number"
          ? error.retryCount
          : undefined;

      connectivityLogger.logAuthentication(
        "error",
        "Authentication check failed",
        {
          success: false,
          failureReason: authError.message,
        },
        "session_validation",
        errorObject,
        {
          startTime: validationStartTime,
          duration:
            (typeof performance !== "undefined"
              ? performance.now()
              : Date.now()) - validationStartTime,
          retryCount,
          metadata: {
            category: authError.category,
          },
        }
      );

      return false;
    } finally {
      isCheckingAuth.current = false;
    }
  };

  // Clear authentication error
  const clearError = useCallback((): void => {
    setAuthState((prev) => ({ ...prev, error: null }));
  }, []);

  // Initialize authentication state on mount and cleanup on unmount
  useEffect(() => {
    // Don't check auth if we're on the login page to prevent loops
    if (
      typeof window !== "undefined" &&
      window.location.pathname === "/login"
    ) {
      setAuthState((prev) => ({ ...prev, isLoading: false }));
      return;
    }

    // Set initial loading state to prevent premature redirects
    setAuthState((prev) => ({ ...prev, isLoading: true }));

    // Only check auth if we're not already authenticated
    // This prevents unnecessary API calls and potential race conditions
    if (!isAuthenticated) {
      checkAuth().finally(() => {
        // Ensure loading state is cleared even if checkAuth fails
        setAuthState((prev) => ({ ...prev, isLoading: false }));
      });
    } else {
      // If already authenticated, clear loading state
      setAuthState((prev) => ({ ...prev, isLoading: false }));
    }

    // Cleanup timer on unmount
    return () => {
      stopSessionRefreshTimer();
    };
  }, []);

  // Update activity timestamp on user interaction
  useEffect(() => {
    const updateActivity = () => {
      if (isAuthenticated) {
        setAuthState((prev) => ({ ...prev, lastActivity: new Date() }));
      }
    };

    // Listen for user activity
    const events = [
      "mousedown",
      "mousemove",
      "keypress",
      "scroll",
      "touchstart",
    ];
    events.forEach((event) => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, updateActivity);
      });
    };
  }, [isAuthenticated]);

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
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

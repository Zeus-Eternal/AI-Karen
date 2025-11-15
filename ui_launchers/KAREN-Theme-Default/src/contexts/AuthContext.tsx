
"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FC, ReactNode } from "react";
import { connectivityLogger } from "@/lib/logging";
import { logout as sessionLogout, getCurrentUser, hasSessionCookie, persistAccessToken, setSession } from "@/lib/auth/session";
import {
  getConnectionManager,
  ConnectionError,
  ErrorCategory,
} from "@/lib/connection/connection-manager";
import { getTimeoutManager, OperationType } from "@/lib/connection/timeout-manager";
import { markAuthSuccess as markAuthSuccessInterceptor } from "@/lib/auth-interceptor";
import { markAuthSuccess as markAuthSuccessApiClient } from "@/lib/api-client-integrated";
import { AuthContext } from "./auth-context-instance";
import { getHighestRole, type UserRole } from "@/components/security/rbac-shared";


export interface User {
  userId: string;
  email: string;
  roles: string[];
  tenantId?: string;
  role?: UserRole;
  permissions?: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

interface AuthResponseUserData {
  user_id: string;
  email: string;
  roles?: string[];
  tenant_id: string;
  role?: UserRole;
  permissions?: string[];
}

interface AuthApiResponse {
  valid?: boolean;
  success?: boolean;
  user?: AuthResponseUserData;
  user_data?: AuthResponseUserData;
  access_token?: string;
  [key: string]: unknown;
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
  hasRole: (role: UserRole) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
  isLoggingIn: boolean;
}

export interface AuthProviderProps {
  children: ReactNode;
}

interface ApiUserData {
  user_id: string;
  email: string;
  roles?: string[];
  tenant_id?: string;
  permissions?: string[];
}

interface AuthApiResponseRaw {
  valid?: unknown;
  user?: unknown;
  user_data?: unknown;
}

function isApiUserData(value: unknown): value is ApiUserData {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.user_id === "string" &&
    typeof record.email === "string"
  );
}

function extractUserData(
  response: AuthApiResponse | AuthApiResponseRaw | null | undefined
): ApiUserData | null {
  if (!response) {
    return null;
  }

  if (response.user && isApiUserData(response.user)) {
    return response.user;
  }

  if (response.user_data && isApiUserData(response.user_data)) {
    return response.user_data;
  }

  return null;
}

// Hook moved to separate file for React Fast Refresh compatibility

export const AuthProvider: FC<AuthProviderProps> = ({ children }) => {
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
  const connectionManager = useMemo(() => getConnectionManager(), []);
  const timeoutManager = useMemo(() => getTimeoutManager(), []);

  // Session refresh timer
  const sessionRefreshTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionRefreshInterval = 15 * 60 * 1000; // 15 minutes

  // Flag to prevent multiple simultaneous auth checks
  const isCheckingAuth = useRef<boolean>(false);

  // Flag to track login in progress - prevents redirect loops
  const isLoggingInRef = useRef<boolean>(false);

  // Helper functions - use unified rbac-shared for role logic
  const createUserFromApiData = useCallback(
    (apiUser: ApiUserData): User => ({
      userId: apiUser.user_id,
      email: apiUser.email,
      roles: apiUser.roles ?? [],
      tenantId: apiUser.tenant_id ?? "default",
      role: getHighestRole(apiUser.roles ?? []),
      permissions: apiUser.permissions,
    }),
    []
  );

  // Convert technical errors to user-friendly messages
  const getUserFriendlyErrorMessage = useCallback((error: ConnectionError): string => {
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
  }, []);

  // Create standardized auth error from various error types
  const createAuthError = useCallback((error: unknown): AuthError => {
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
  }, [getUserFriendlyErrorMessage]);

  // Helper function to get default permissions for a role
  const getRolePermissions = (
    role: UserRole
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

      const result = await connectionManager.makeRequest<AuthApiResponse>(
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
          retryAttempts: 0, // No retries - keep refresh fast and simple
          exponentialBackoff: false,
        }
      );

      const data = result.data;
      const userData = extractUserData(data);

      if (data?.valid && userData) {
        const user = createUserFromApiData(userData);

        setUser(user);
        setIsAuthenticated(true);
        setAuthState((prev) => ({
          ...prev,
          error: null,
          lastActivity: new Date(),
          isRefreshing: false,
        }));
        setSession({
          userId: user.userId,
          email: user.email,
          roles: user.roles,
          tenantId: user.tenantId ?? "default",
          role: user.role,
          permissions: user.permissions,
        });

        return true;
      }

      setUser(null);
      setIsAuthenticated(false);
      setAuthState((prev) => ({ ...prev, error: null, isRefreshing: false }));
      return false;
    } catch (error) {
      console.error("Session validation request failed", error);
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
    createUserFromApiData,
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
  }, [refreshSession, logout, sessionRefreshInterval]);

  // Enhanced login method with improved error handling and ConnectionManager integration
  const login = async (credentials: LoginCredentials): Promise<void> => {
    const authenticationStartTime =
      typeof performance !== "undefined" ? performance.now() : Date.now();

    // Mark login as in progress to prevent redirect loops
    isLoggingInRef.current = true;

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

      const result = await connectionManager.makeRequest<AuthApiResponse>(
        loginUrl,
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
          retryAttempts: 0, // No retries - API route handles retries
          exponentialBackoff: false,
        }
      );

      // Handle successful login response
      const data = result.data;
      if (data?.access_token) {
        persistAccessToken(data.access_token);
      }
      const userData = extractUserData(data);
      if (!userData) {
        throw new ConnectionError(
          "No user data in login response",
          ErrorCategory.CONFIGURATION_ERROR,
          false,
          0
        );
      }

      // Create user object
      const user = createUserFromApiData(userData);
      const sessionData = {
        userId: user.userId,
        email: user.email,
        roles: user.roles,
        tenantId: user.tenantId ?? "default",
        role: user.role,
        permissions: user.permissions,
      };
      setSession(sessionData);

      // Update all authentication state together for consistent updates
      // React 18 will batch these automatically, but we keep them together for clarity
      setUser(user);
      setIsAuthenticated(true);
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: null,
        lastActivity: new Date(),
      }));

      // Start session refresh timer after state updates
      startSessionRefreshTimer();

      // Mark auth success in both auth interceptor and API client to prevent 401 redirects during grace period
      markAuthSuccessInterceptor();
      markAuthSuccessApiClient();

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

      // Clear login flag after all state updates are complete
      // Small delay to ensure React state has propagated
      setTimeout(() => {
        isLoggingInRef.current = false;
      }, 0);

    } catch (err) {
      // Enhanced error handling with categorization
      const authError = createAuthError(err);

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

      // Clear login flag on error
      isLoggingInRef.current = false;

      const errorObject =
        err instanceof Error ? err : new Error(String(err));
      const retryCount =
        err instanceof ConnectionError &&
        typeof err.retryCount === "number"
          ? err.retryCount
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
              err instanceof ConnectionError ? err.statusCode : undefined,
          },
        }
      );

      throw err;
    }
  };

  // Role and permission checking functions
  const hasRole = useCallback(
    (role: UserRole): boolean => {
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
        user.role || (user.roles[0] as UserRole)
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
  const checkAuth = useCallback(async (): Promise<boolean> => {
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
        // Only clear auth if we weren't already authenticated
        // This prevents clearing auth on transient cookie issues
        if (isAuthenticated) {
          connectivityLogger.logAuthentication(
            "warn",
            "Session cookie missing but user was authenticated - keeping session",
            {
              success: true,
              failureReason: "missing_cookie_but_authenticated",
            },
            "session_validation"
          );
          return true;
        }

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

      const result = await connectionManager.makeRequest<AuthApiResponse>(
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
          retryAttempts: 0, // No retries - keep session validation fast and simple
          exponentialBackoff: false,
        }
      );

      const data = result.data;
      const userData = extractUserData(data);

      if (data?.valid && userData) {
        const user = createUserFromApiData(userData);

        setUser(user);
        setIsAuthenticated(true);
        setAuthState((prev) => ({
          ...prev,
          error: null,
          lastActivity: new Date(),
        }));
        setSession({
          userId: user.userId,
          email: user.email,
          roles: user.roles,
          tenantId: user.tenantId ?? "default",
          role: user.role,
          permissions: user.permissions,
        });

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

      // Only clear authentication on actual auth failures (401, 403), not on transient errors
      const isAuthFailure = authError.statusCode === 401 || authError.statusCode === 403;
      const isTransientError =
        authError.category === ErrorCategory.NETWORK_ERROR ||
        authError.category === ErrorCategory.TIMEOUT_ERROR ||
        authError.retryable;

      if (isAuthFailure) {
        // Actual authentication failure - clear auth state
        setUser(null);
        setIsAuthenticated(false);
        setAuthState((prev) => ({
          ...prev,
          error: authError,
        }));
        stopSessionRefreshTimer();
      } else if (isTransientError && isAuthenticated) {
        // Transient error but user was authenticated - keep session
        connectivityLogger.logAuthentication(
          "warn",
          "Session validation failed with transient error - keeping authenticated state",
          {
            success: true,
            failureReason: authError.message,
          },
          "session_validation"
        );
        setAuthState((prev) => ({
          ...prev,
          error: authError,
        }));
        return true; // Keep authenticated
      } else {
        // Error on initial auth check - clear state
        setUser(null);
        setIsAuthenticated(false);
        setAuthState((prev) => ({
          ...prev,
          error: authError.retryable ? authError : null,
        }));
        stopSessionRefreshTimer();
      }

      const errorObject =
        error instanceof Error ? error : new Error(String(error));
      const retryCount =
        error instanceof ConnectionError &&
        typeof error.retryCount === "number"
          ? error.retryCount
          : undefined;

      connectivityLogger.logAuthentication(
        isAuthFailure ? "error" : "warn",
        isAuthFailure ? "Authentication check failed" : "Session validation error (non-fatal)",
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
            isAuthFailure,
            isTransientError,
          },
        }
      );

      return !isAuthFailure && isAuthenticated;
    } finally {
      isCheckingAuth.current = false;
    }
  }, [
    connectionManager,
    createAuthError,
    createUserFromApiData,
    isAuthenticated,
    startSessionRefreshTimer,
    stopSessionRefreshTimer,
    timeoutManager,
  ]);

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

    // Only check auth if we're not already authenticated
    // This prevents unnecessary API calls and potential race conditions
    if (!isAuthenticated) {
      // Set loading state only when we're actually checking auth
      setAuthState((prev) => ({ ...prev, isLoading: true }));
      checkAuth().finally(() => {
        // Ensure loading state is cleared even if checkAuth fails
        setAuthState((prev) => ({ ...prev, isLoading: false }));
      });
    } else {
      // If already authenticated, ensure loading state is cleared without triggering unnecessary state updates
      setAuthState((prev) => (prev.isLoading ? { ...prev, isLoading: false } : prev));
    }

    // Cleanup timer on unmount
    return () => {
      stopSessionRefreshTimer();
    };
    // Only re-run when authentication status changes, not when checkAuth function changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

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
    isLoggingIn: isLoggingInRef.current,
  };

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

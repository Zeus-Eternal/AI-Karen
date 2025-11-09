import { useState, useEffect, useCallback } from 'react';
import { isAuthenticated, getCurrentUser, hasRole, login as sessionLogin, logout as sessionLogout } from '@/lib/auth/session';

export interface UseSessionReturn {
  isAuthenticated: boolean;
  user: {
    userId: string;
    email: string;
    roles: string[];
    tenantId: string;
  } | null;
  isLoading: boolean;
  login: (email: string, password: string, totpCode?: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
  refreshSession: () => void;
}

/**
 * Hook for managing user session state
 */
export function useSession(): UseSessionReturn {
  const [isLoading, setIsLoading] = useState(true);
  const [sessionState, setSessionState] = useState({
    isAuthenticated: false,
    user: null as ReturnType<typeof getCurrentUser> | null,
  });

  // Update session state from memory
  const updateSessionState = useCallback(() => {
    setSessionState({
      isAuthenticated: isAuthenticated(),
      user: getCurrentUser(),
    });
  }, []);

  // Initialize session on mount
  useEffect(() => {
    updateSessionState();
    setIsLoading(false);
  }, [updateSessionState]);

  const login = useCallback(async (email: string, password: string, totpCode?: string) => {
    setIsLoading(true);
    try {
      await sessionLogin(email, password, totpCode);
      updateSessionState();
    } catch (error) {
      console.error('Login failed', error);
      setIsLoading(false);  // Ensure loading state is reset
    }
  }, [updateSessionState]);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await sessionLogout();
      updateSessionState();
    } catch (error) {
      console.error('Logout failed', error);
    } finally {
      setIsLoading(false);
    }
  }, [updateSessionState]);

  const hasRoleWrapper = useCallback((role: string) => {
    return hasRole(role);
  }, []);

  const refreshSession = useCallback(() => {
    updateSessionState();
  }, [updateSessionState]);

  return {
    isAuthenticated: sessionState.isAuthenticated,
    user: sessionState.user,
    isLoading,
    login,
    logout,
    hasRole: hasRoleWrapper,
    refreshSession,
  };
}

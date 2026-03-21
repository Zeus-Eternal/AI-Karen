"use client";

import { useState, useEffect, useCallback } from 'react';
import { authService, AuthUser, LoginCredentials } from './auth';

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Initialize auth state
  const initializeAuth = useCallback(async () => {
    try {
      setState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      const isValid = await authService.validateSession();
      const currentUser = isValid ? authService.getCurrentUser() : null;

      if (!isValid || !currentUser) {
        authService.clearAuth();
      }
      
      setState({
        user: isValid ? currentUser : null,
        isAuthenticated: isValid && !!currentUser,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Auth initialization error:', error);
      authService.clearAuth();
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Authentication failed',
      });
    }
  }, []);

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      setState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      const response = await authService.login(credentials);
      
      setState((prev: AuthState) => ({
        ...prev,
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      }));
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setState((prev: AuthState) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      setState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      await authService.logout();
      
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Logout error:', error);
      // Still update state even if API call fails
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Logout failed',
      });
    }
  }, []);

  // Refresh session
  const refreshSession = useCallback(async () => {
    try {
      setState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));
      
      const isValid = await authService.validateSession();
      const currentUser = isValid ? authService.getCurrentUser() : null;

      if (!isValid || !currentUser) {
        authService.clearAuth();
      }
      
      setState((prev: AuthState) => ({
        ...prev,
        user: isValid ? currentUser : null,
        isAuthenticated: isValid && !!currentUser,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Session refresh failed';
      setState((prev: AuthState) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  // Check permissions
  const hasPermission = useCallback((permission: string) => {
    return authService.hasPermission(permission);
  }, []);

  // Check if admin
  const isAdmin = useCallback(() => {
    return authService.isAdmin();
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setState((prev: AuthState) => ({ ...prev, error: null }));
  }, []);

  // Initialize on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Listen for storage changes (for multi-tab support)
  useEffect(() => {
    const handleStorageChange = () => {
      initializeAuth();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [initializeAuth]);

  return {
    // State
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    
    // Actions
    login,
    logout,
    refreshSession,
    initializeAuth,
    clearError,
    
    // Helpers
    hasPermission,
    isAdmin,
  };
}

// Export convenience hook for components
export default useAuth;

/**
 * Authentication Hook
 * Provides authentication state and methods for React components
 */

import { useState, useEffect, useCallback } from 'react';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: string;
  permissions: string[];
  preferences?: Record<string, unknown>;
  createdAt: string;
  lastLogin?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  lastActivity?: Date | null;
}

export interface UseAuthReturn extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  register: (userData: {
    email: string;
    password: string;
    name: string;
  }) => Promise<boolean>;
  updateProfile: (updates: Partial<User>) => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
  clearError: () => void;
}

export function useAuth(): UseAuthReturn {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null,
    isLoading: false,
    error: null,
    lastActivity: null
  });

  const updateAuthState = useCallback((updates: Partial<AuthState>) => {
    setAuthState(prev => ({ ...prev, ...updates }));
  }, []);

  const clearError = useCallback(() => {
    updateAuthState({ error: null });
  }, [updateAuthState]);

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    try {
      updateAuthState({ isLoading: true, error: null });

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Login failed');
      }

      const data = await response.json();
      
      if (data.success && data.token) {
        // Store token
        localStorage.setItem('karen-auth-token', data.token);
        
        // Update state
        updateAuthState({
          isAuthenticated: true,
          user: data.user,
          token: data.token,
          isLoading: false,
          lastActivity: new Date()
        });

        return true;
      } else {
        throw new Error(data.message || 'Login failed');
      }
    } catch (error) {
      updateAuthState({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed'
      });
      return false;
    }
  }, [updateAuthState]);

  const logout = useCallback(async (): Promise<void> => {
    try {
      updateAuthState({ isLoading: true });

      const token = authState.token;
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        });
      }

      // Clear stored data
      localStorage.removeItem('karen-auth-token');
      localStorage.removeItem('karen-user-preferences');
      
      // Reset state
      updateAuthState({
        isAuthenticated: false,
        user: null,
        token: null,
        isLoading: false,
        error: null,
        lastActivity: null
      });
    } catch (error) {
      updateAuthState({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Logout failed'
      });
    }
  }, [authState.token, updateAuthState]);

  const register = useCallback(async (userData: {
    email: string;
    password: string;
    name: string;
  }): Promise<boolean> => {
    try {
      updateAuthState({ isLoading: true, error: null });

      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Registration failed');
      }

      const data = await response.json();
      
      if (data.success) {
        updateAuthState({ isLoading: false });
        return true;
      } else {
        throw new Error(data.message || 'Registration failed');
      }
    } catch (error) {
      updateAuthState({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Registration failed'
      });
      return false;
    }
  }, [updateAuthState]);

  const updateProfile = useCallback(async (updates: Partial<User>): Promise<boolean> => {
    try {
      updateAuthState({ isLoading: true, error: null });

      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authState.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Profile update failed');
      }

      const data = await response.json();
      
      if (data.success) {
        updateAuthState({
          user: authState.user ? { ...authState.user, ...data.user } : null,
          isLoading: false
        });
        return true;
      } else {
        throw new Error(data.message || 'Profile update failed');
      }
    } catch (error) {
      updateAuthState({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Profile update failed'
      });
      return false;
    }
  }, [authState.token, authState.user, updateAuthState]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const token = authState.token;
      if (!token) {
        return false;
      }

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        // Token is invalid, clear auth state
        localStorage.removeItem('karen-auth-token');
        updateAuthState({
          isAuthenticated: false,
          user: null,
          token: null
        });
        return false;
      }

      const data = await response.json();
      
      if (data.success && data.token) {
        localStorage.setItem('karen-auth-token', data.token);
        updateAuthState({ token: data.token });
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }, [authState.token, updateAuthState]);

  // Check authentication status on mount and token changes
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = localStorage.getItem('karen-auth-token');
      
      if (token) {
        try {
          const response = await fetch('/api/auth/check', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
            }
          });

          if (response.ok) {
            const data = await response.json();
            if (data.valid && data.user) {
              updateAuthState({
                isAuthenticated: true,
                user: data.user,
                token
              });
            } else {
              // Token is invalid, clear it
              localStorage.removeItem('karen-auth-token');
              updateAuthState({
                isAuthenticated: false,
                user: null,
                token: null
              });
            }
          } else {
            // Token is invalid, clear it
            localStorage.removeItem('karen-auth-token');
            updateAuthState({
              isAuthenticated: false,
              user: null,
              token: null
            });
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('karen-auth-token');
          updateAuthState({
            isAuthenticated: false,
            user: null,
            token: null
          });
        }
      }
    };

    checkAuthStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    ...authState,
    login,
    logout,
    register,
    updateProfile,
    refreshToken,
    clearError
  };
}

export default useAuth;

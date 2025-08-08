'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthState, LoginCredentials, AuthContextType } from '@/types/auth';
import { authService } from '@/services/authService';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Initialize auth state using JWT tokens or session
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if we have a stored JWT token
        const accessToken = localStorage.getItem('karen_access_token');
        
        if (accessToken) {
          // We have a token, try to get current user
          const currentUser = await authService.getCurrentUser();
          setAuthState({
            user: currentUser,
            isAuthenticated: true,
            isLoading: false,
          });
        } else {
          // No token, user is not authenticated
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } catch (error) {
        // Token might be expired or invalid, clear it and set unauthenticated
        localStorage.removeItem('karen_access_token');
        localStorage.removeItem('karen_refresh_token');
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      
      const loginResponse = await authService.login(credentials);
      
      // Store JWT tokens in localStorage
      if (loginResponse.access_token) {
        localStorage.setItem('karen_access_token', loginResponse.access_token);
      }
      if (loginResponse.refresh_token) {
        localStorage.setItem('karen_refresh_token', loginResponse.refresh_token);
      }
      
      // Create user object from login response
      const user: User = {
        user_id: loginResponse.user_id,
        email: loginResponse.email,
        roles: loginResponse.roles,
        tenant_id: loginResponse.tenant_id,
        two_factor_enabled: loginResponse.two_factor_enabled,
        preferences: loginResponse.preferences || {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'ollama',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: {
            email: true,
            push: false,
          },
          ui: {
            theme: 'light',
            language: 'en',
            avatarUrl: '',
          },
        },
      };

      setAuthState({
        user,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const register = async (credentials: LoginCredentials): Promise<void> => {
    await authService.register(credentials);
  };

  const requestPasswordReset = async (email: string): Promise<void> => {
    await authService.requestPasswordReset(email);
  };

  const resetPassword = async (
    token: string,
    newPassword: string,
  ): Promise<void> => {
    await authService.resetPassword(token, newPassword);
  };

  const logout = (): void => {
    authService.logout();
    
    // Clear JWT tokens from localStorage
    localStorage.removeItem('karen_access_token');
    localStorage.removeItem('karen_refresh_token');
    
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
    
    // Redirect to login page after logout
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const user = await authService.getCurrentUser();
      setAuthState(prev => ({ ...prev, user }));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
      throw error;
    }
  };

  const updateUserPreferences = async (preferences: Partial<User['preferences']>): Promise<void> => {
    if (!authState.user) {
      throw new Error('User not authenticated');
    }

    try {
      await authService.updateUserPreferences('', preferences);
      
      // Update local user state
      const updatedUser: User = {
        ...authState.user,
        preferences: {
          ...authState.user.preferences,
          ...preferences,
          ui: {
            ...authState.user.preferences.ui,
            ...(preferences as any).ui,
          },
        },
      };
      
      setAuthState(prev => ({ ...prev, user: updatedUser }));
    } catch (error) {
      console.error('Failed to update user preferences:', error);
      throw error;
    }
  };

  const contextValue: AuthContextType = {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
    register,
    requestPasswordReset,
    resetPassword,
    logout,
    refreshUser,
    updateUserPreferences,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
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
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = authService.getToken();
        const savedUser = authService.getUser();

        if (token && savedUser) {
          // Verify token is still valid by fetching current user
          try {
            const currentUser = await authService.getCurrentUser(token);
            setAuthState({
              user: currentUser,
              token,
              isAuthenticated: true,
              isLoading: false,
            });
            // Update saved user data
            authService.saveUser(currentUser);
          } catch (error) {
            console.error('Token validation failed:', error);
            // Token is invalid, clear auth data
            authService.removeToken();
            authService.removeUser();
            setAuthState({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
            });
          }
        } else {
          setAuthState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        setAuthState({
          user: null,
          token: null,
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
      
      // Create user object from login response
      const user: User = {
        user_id: loginResponse.user_id,
        email: loginResponse.email,
        roles: loginResponse.roles,
        tenant_id: loginResponse.tenant_id,
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
          },
        },
      };

      // Save to localStorage
      authService.saveToken(loginResponse.token);
      authService.saveUser(user);

      setAuthState({
        user,
        token: loginResponse.token,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const logout = (): void => {
    authService.removeToken();
    authService.removeUser();
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  const refreshUser = async (): Promise<void> => {
    const token = authState.token;
    if (!token) {
      throw new Error('No token available');
    }

    try {
      const user = await authService.getCurrentUser(token);
      authService.saveUser(user);
      setAuthState(prev => ({ ...prev, user }));
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails, logout user
      logout();
      throw error;
    }
  };

  const updateUserPreferences = async (preferences: Partial<User['preferences']>): Promise<void> => {
    const token = authState.token;
    if (!token || !authState.user) {
      throw new Error('User not authenticated');
    }

    try {
      await authService.updateUserPreferences(token, preferences);
      
      // Update local user state
      const updatedUser: User = {
        ...authState.user,
        preferences: {
          ...authState.user.preferences,
          ...preferences,
        },
      };
      
      authService.saveUser(updatedUser);
      setAuthState(prev => ({ ...prev, user: updatedUser }));
    } catch (error) {
      console.error('Failed to update user preferences:', error);
      throw error;
    }
  };

  const contextValue: AuthContextType = {
    user: authState.user,
    token: authState.token,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
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
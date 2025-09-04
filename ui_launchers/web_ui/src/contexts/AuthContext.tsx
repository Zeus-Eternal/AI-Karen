'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { safeError, safeWarn } from '@/lib/safe-console';
import { User, AuthState, LoginCredentials, AuthContextType, DeepPartial } from '@/types/auth';
import { authStateManager } from './AuthStateManager';
import { authService } from '@/services/authService';
import { login as sessionLogin, logout as sessionLogout, getCurrentUser } from '@/lib/auth/session';

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

  // Derive from authStateManager/session only (no separate initial fetch)
  useEffect(() => {
    // Seed from current snapshot
    const snapshot = authStateManager.getState();
    const initialUser = snapshot.user && snapshot.user.userId ? {
      user_id: snapshot.user.userId,
      email: snapshot.user.email || '',
      roles: snapshot.user.roles || [],
      tenant_id: snapshot.user.tenantId || '',
      two_factor_enabled: false,
      preferences: {
        personalityTone: 'professional',
        personalityVerbosity: 'balanced',
        memoryDepth: 'medium',
        customPersonaInstructions: '',
        preferredLLMProvider: 'openai',
        preferredModel: 'gpt-4',
        temperature: 0.7,
        maxTokens: 2048,
        notifications: { email: true, push: false },
        ui: { theme: 'system', language: 'en' },
      },
    } as User : null;
    setAuthState({ user: initialUser, isAuthenticated: snapshot.isAuthenticated, isLoading: false });

    // Auto-login in development mode if not authenticated
    if (process.env.NODE_ENV === 'development' && !snapshot.isAuthenticated) {
      const autoLogin = async () => {
        try {
          console.log('Development mode: attempting auto-login...');
          setAuthState(prev => ({ ...prev, isLoading: true }));
          await sessionLogin('test@example.com', 'test123');
          console.log('Development auto-login successful');
          
          // Force a state update after successful login
          const currentUser = getCurrentUser();
          if (currentUser) {
            const user: User = {
              user_id: currentUser.userId,
              email: currentUser.email,
              roles: currentUser.roles,
              tenant_id: currentUser.tenantId,
              two_factor_enabled: false,
              preferences: {
                personalityTone: 'friendly',
                personalityVerbosity: 'balanced',
                memoryDepth: 'medium',
                customPersonaInstructions: '',
                preferredLLMProvider: 'llama-cpp',
                preferredModel: 'llama3.2:latest',
                temperature: 0.7,
                maxTokens: 1000,
                notifications: { email: true, push: false },
                ui: { theme: 'light', language: 'en', avatarUrl: '' },
              },
            };
            setAuthState({ user, isAuthenticated: true, isLoading: false });
          }
        } catch (error) {
          console.log('Development auto-login failed:', error);
          setAuthState(prev => ({ ...prev, isLoading: false }));
          // Don't throw - just continue without auth
        }
      };
      
      // Delay auto-login slightly to avoid race conditions
      setTimeout(autoLogin, 500);
    }

    const unsubscribe = authStateManager.subscribe(state => {
      // Convert SessionUser back to User format if needed
      const user = state.user && state.user.userId ? {
        user_id: state.user.userId,
        email: state.user.email || '',
        roles: state.user.roles || [],
        tenant_id: state.user.tenantId || '',
        two_factor_enabled: false, // Default value
        preferences: {
          personalityTone: 'professional',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'openai',
          preferredModel: 'gpt-4',
          temperature: 0.7,
          maxTokens: 2048,
          notifications: {
            email: true,
            push: false,
          },
          ui: {
            theme: 'system',
            language: 'en',
          },
        },
      } : null;
      
      setAuthState({ isAuthenticated: state.isAuthenticated, user, isLoading: false });
    });

    return () => unsubscribe();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      
      // Use the session login method to ensure proper session management
      await sessionLogin(credentials.email, credentials.password, credentials.totp_code);
      
      // Get the current user from session
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Failed to get user data after login');
      }
      
      // Create user object from session data
      const user: User = {
        user_id: currentUser.userId,
        email: currentUser.email,
        roles: currentUser.roles,
        tenant_id: currentUser.tenantId,
        two_factor_enabled: false, // Default value
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'llama-cpp',
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

      const newState = {
        user,
        isAuthenticated: true,
        isLoading: false,
      };
      setAuthState(newState);
      
      // Convert User to SessionUser format for authStateManager
      const sessionUser = {
        userId: user.user_id,
        email: user.email || '',
        roles: user.roles,
        tenantId: user.tenant_id
      };
      
      authStateManager.updateState({ isAuthenticated: true, user: sessionUser });
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

  const logout = async (): Promise<void> => {
    try {
      await sessionLogout();
    } catch (error) {
      safeWarn('Logout request failed:', error);
    }
    
    const newState = {
      user: null,
      isAuthenticated: false,
      isLoading: false,
    };
    setAuthState(newState);
    authStateManager.updateState({ isAuthenticated: false, user: null });
    
    // Redirect to login page after logout
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const user = await authService.getCurrentUser();
      setAuthState(prev => ({ ...prev, user }));
      
      // Convert User to SessionUser format for authStateManager
      const sessionUser = {
        userId: user.user_id,
        email: user.email || '',
        roles: user.roles,
        tenantId: user.tenant_id
      };
      
      authStateManager.updateState({ isAuthenticated: true, user: sessionUser });
    } catch (error) {
      safeError('Failed to refresh user:', error);
      logout();
      throw error;
    }
  };

  const updateUserPreferences = async (preferences: DeepPartial<User['preferences']>): Promise<void> => {
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
          notifications: {
            ...authState.user.preferences.notifications,
            ...preferences.notifications,
          },
          ui: {
            ...authState.user.preferences.ui,
            ...preferences.ui,
          },
        } as User['preferences'],
      };
      
      setAuthState(prev => ({ ...prev, user: updatedUser }));
    } catch (error) {
      safeError('Failed to update user preferences:', error);
      throw error;
    }
  };

  const updateCredentials = async (newUsername?: string, newPassword?: string): Promise<void> => {
    try {
      const resp = await authService.updateCredentials(newUsername, newPassword);
      // If username changed, reflect it in local state. The backend may also return updated fields.
      setAuthState(prev => {
        if (!prev.user) return prev;
        const updatedUser: User = {
          ...prev.user,
          user_id: newUsername && newUsername.length > 0 ? newUsername : prev.user.user_id,
          email: resp?.email || prev.user.email,
        } as User;
        return { ...prev, user: updatedUser };
      });
    } catch (error) {
      safeError('Failed to update credentials:', error);
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
    updateCredentials,
    updateUserPreferences,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

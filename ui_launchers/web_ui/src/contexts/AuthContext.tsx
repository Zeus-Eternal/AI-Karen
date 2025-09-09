'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { login as sessionLogin, logout as sessionLogout, getCurrentUser } from '@/lib/auth/session';
import { authStateManager, type AuthSnapshot } from './AuthStateManager';

export interface User {
  user_id: string;
  email: string;
  full_name?: string | null;
  roles: string[];
  tenant_id: string;
  preferences: {
    memoryDepth: string;
    personalityTone: string;
    personalityVerbosity: string;
    customPersonaInstructions: string;
    preferredLLMProvider: string;
    preferredModel: string;
    temperature: number;
    maxTokens: number;
    notifications: { email: boolean; push: boolean };
    ui: { theme: string; language: string; avatarUrl?: string };
  };
  two_factor_enabled: boolean;
  is_verified?: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export interface AuthProviderProps {
  children: ReactNode;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      await sessionLogin(credentials.email, credentials.password, credentials.totp_code);
      const currentUser = getCurrentUser();
      if (!currentUser) {
        throw new Error('Failed to get user data after login');
      }
      const user: User = {
        user_id: currentUser.userId,
        email: currentUser.email,
        roles: currentUser.roles,
        tenant_id: currentUser.tenantId,
        full_name: null,
        two_factor_enabled: false,
        is_verified: true,
        preferences: {
          memoryDepth: 'high',
          personalityTone: 'professional',
          personalityVerbosity: 'balanced',
          customPersonaInstructions: '',
          preferredLLMProvider: 'openai',
          preferredModel: 'gpt-4',
          temperature: 0.7,
          maxTokens: 2048,
          notifications: { email: true, push: false },
          ui: { theme: 'system', language: 'en' },
        },
      };
      setAuthState({ user, isAuthenticated: true, isLoading: false });
      
      // Update auth state manager
      authStateManager.updateState({ isAuthenticated: true, user: currentUser });
    } catch (error) {
      setAuthState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await sessionLogout();
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      setAuthState({ user: null, isAuthenticated: false, isLoading: false });
      authStateManager.updateState({ isAuthenticated: false, user: null });
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const currentUser = getCurrentUser();
      if (currentUser) {
        const user: User = {
          user_id: currentUser.userId,
          email: currentUser.email,
          roles: currentUser.roles,
          tenant_id: currentUser.tenantId,
          full_name: null,
          two_factor_enabled: false,
          is_verified: true,
          preferences: {
            memoryDepth: 'high',
            personalityTone: 'professional',
            personalityVerbosity: 'balanced',
            customPersonaInstructions: '',
            preferredLLMProvider: 'openai',
            preferredModel: 'gpt-4',
            temperature: 0.7,
            maxTokens: 2048,
            notifications: { email: true, push: false },
            ui: { theme: 'system', language: 'en' },
          },
        };
        setAuthState({ user, isAuthenticated: true, isLoading: false });
      } else {
        setAuthState({ user: null, isAuthenticated: false, isLoading: false });
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
      setAuthState({ user: null, isAuthenticated: false, isLoading: false });
    }
  };

  useEffect(() => {
    const snapshot = authStateManager.getState();
    
    // Convert SessionUser to User format if needed
    const initialUser = snapshot.user && snapshot.user.userId ? {
      user_id: snapshot.user.userId,
      email: snapshot.user.email || '',
      full_name: null,
      roles: snapshot.user.roles || [],
      tenant_id: snapshot.user.tenantId || '',
      preferences: {
        memoryDepth: 'high',
        personalityTone: 'professional',
        personalityVerbosity: 'balanced',
        customPersonaInstructions: '',
        preferredLLMProvider: 'openai',
        preferredModel: 'gpt-4',
        temperature: 0.7,
        maxTokens: 2048,
        notifications: { email: true, push: false },
        ui: { theme: 'system', language: 'en' },
      },
      two_factor_enabled: false,
      is_verified: true,
    } as User : null;
    setAuthState({ user: initialUser, isAuthenticated: snapshot.isAuthenticated, isLoading: false });

    // Auto-login in development mode
    const autoLogin = async () => {
      if (process.env.NODE_ENV === 'development' && !snapshot.isAuthenticated && !authState.isLoading) {
        try {
          console.log('Development mode: attempting auto-login');
          await login({
            email: 'admin@kari.ai',
            password: 'Password123!',
          });
          console.log('Auto-login successful');
        } catch (error) {
          console.log('Auto-login failed:', error);
          // Don't throw error for auto-login failures
        }
      }
    };

    // Subscribe to auth state manager updates
    const unsubscribe = authStateManager.subscribe((state) => {
      const user = state.user && state.user.userId ? {
        user_id: state.user.userId,
        email: state.user.email || '',
        full_name: null,
        roles: state.user.roles || [],
        tenant_id: state.user.tenantId || '',
        preferences: {
          memoryDepth: 'high',
          personalityTone: 'professional',
          personalityVerbosity: 'balanced',
          customPersonaInstructions: '',
          preferredLLMProvider: 'openai',
          preferredModel: 'gpt-4',
          temperature: 0.7,
          maxTokens: 2048,
          notifications: { email: true, push: false },
          ui: { theme: 'system', language: 'en' },
        },
        two_factor_enabled: false,
        is_verified: true,
      } as User : null;
      setAuthState({ user, isAuthenticated: state.isAuthenticated, isLoading: false });
    });

    // Only attempt auto-login after a short delay to allow session provider to initialize
    const timer = setTimeout(autoLogin, 2000);
    
    return () => {
      clearTimeout(timer);
      unsubscribe();
    };
  }, [authState.isLoading]);

  const contextValue: AuthContextType = {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

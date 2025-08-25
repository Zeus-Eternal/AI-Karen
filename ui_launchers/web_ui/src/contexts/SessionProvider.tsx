/**
 * Session Provider for Enhanced Session Management
 * 
 * Provides React context for session management with automatic rehydration,
 * token refresh, and session recovery capabilities.
 * 
 * Requirements: 1.1, 1.3, 5.1, 5.4, 5.5
 */

'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import {
  bootSession, 
  ensureToken, 
  isAuthenticated, 
  getCurrentUser, 
  hasRole, 
  login as sessionLogin, 
  logout as sessionLogout,
  getSession,
  clearSession,
  type SessionData
} from '@/lib/auth/session';
import { attemptSessionRecovery, type SessionRecoveryResult } from '@/lib/auth/session-recovery';
import { authStateManager, type AuthSnapshot } from './AuthStateManager';

export interface SessionUser {
  userId: string;
  email: string;
  roles: string[];
  tenantId: string;
}

export interface SessionContextType {
  // Session state
  isAuthenticated: boolean;
  user: SessionUser | null;
  isLoading: boolean;
  isInitialized: boolean;
  
  // Session actions
  login: (email: string, password: string, totpCode?: string) => Promise<void>;
  logout: () => Promise<void>;
  ensureToken: () => Promise<void>;
  refreshSession: () => void;
  
  // Session utilities
  hasRole: (role: string) => boolean;
  
  // Session recovery
  isRecovering: boolean;
  lastRecoveryResult: SessionRecoveryResult | null;
  attemptRecovery: () => Promise<SessionRecoveryResult>;
  
  // Session data
  sessionData: SessionData | null;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const useSession = () => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

interface SessionProviderProps {
  children: ReactNode;
  onSessionChange?: (isAuthenticated: boolean, user: SessionUser | null) => void;
  onSessionError?: (error: Error) => void;
  onRecoveryAttempt?: (result: SessionRecoveryResult) => void;
  autoRehydrate?: boolean;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({
  children,
  onSessionChange,
  onSessionError,
  onRecoveryAttempt,
  autoRehydrate = true,
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [lastRecoveryResult, setLastRecoveryResult] = useState<SessionRecoveryResult | null>(null);
  const [sessionState, setSessionState] = useState({
    isAuthenticated: false,
    user: null as SessionUser | null,
    sessionData: null as SessionData | null,
  });

  // Update session state from memory
  const updateSessionState = useCallback(() => {
    const authenticated = isAuthenticated();
    const currentUser = getCurrentUser();
    const sessionData = getSession();
    
    const newState = {
      isAuthenticated: authenticated,
      user: currentUser,
      sessionData,
    };

    setSessionState(newState);

    const snapshot: AuthSnapshot = {
      isAuthenticated: authenticated,
      user: currentUser,
    };
    authStateManager.updateState(snapshot);

    // Notify parent component of session changes
    onSessionChange?.(authenticated, currentUser);
    
    return newState;
  }, [onSessionChange]);

  // Initialize session on mount
  useEffect(() => {
    const initializeSession = async () => {
      if (!autoRehydrate) {
        setIsLoading(false);
        setIsInitialized(true);
        updateSessionState();
        return;
      }

      try {
        setIsLoading(true);
        await bootSession();
        console.log('Session initialized successfully');
      } catch (error: any) {
        console.log('No session to restore:', error.message);
        onSessionError?.(error);
      } finally {
        updateSessionState();
        setIsLoading(false);
        setIsInitialized(true);
      }
    };

    initializeSession();
  }, [autoRehydrate, updateSessionState, onSessionError]);

  // Login function
  const login = useCallback(async (email: string, password: string, totpCode?: string) => {
    setIsLoading(true);
    try {
      await sessionLogin(email, password, totpCode);
      updateSessionState();
      console.log('Login successful');
    } catch (error: any) {
      console.error('Login failed:', error);
      onSessionError?.(error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [updateSessionState, onSessionError]);

  // Logout function
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await sessionLogout();
      console.log('Logout successful');
    } catch (error: any) {
      console.warn('Logout request failed:', error);
      onSessionError?.(error);
    } finally {
      updateSessionState();
      setIsLoading(false);
    }
  }, [updateSessionState, onSessionError]);

  // Ensure token function
  const ensureTokenWrapper = useCallback(async () => {
    try {
      await ensureToken();
      updateSessionState();
    } catch (error: any) {
      console.error('Token refresh failed:', error);
      onSessionError?.(error);
      throw error;
    }
  }, [updateSessionState, onSessionError]);

  // Session recovery function
  const attemptRecovery = useCallback(async (): Promise<SessionRecoveryResult> => {
    if (isRecovering) {
      return lastRecoveryResult || {
        success: false,
        reason: 'recovery_in_progress',
        shouldShowLogin: false,
        message: 'Recovery already in progress',
      };
    }

    setIsRecovering(true);
    
    try {
      const result = await attemptSessionRecovery();
      setLastRecoveryResult(result);
      onRecoveryAttempt?.(result);
      
      if (result.success) {
        updateSessionState();
        console.log('Session recovery successful');
      } else {
        console.log('Session recovery failed:', result.reason);
      }
      
      return result;
    } catch (error: any) {
      console.error('Session recovery error:', error);
      const failureResult: SessionRecoveryResult = {
        success: false,
        reason: 'recovery_error',
        shouldShowLogin: true,
        message: 'Session recovery failed. Please log in again.',
      };
      setLastRecoveryResult(failureResult);
      onRecoveryAttempt?.(failureResult);
      onSessionError?.(error);
      return failureResult;
    } finally {
      setIsRecovering(false);
    }
  }, [isRecovering, lastRecoveryResult, updateSessionState, onRecoveryAttempt, onSessionError]);

  // Has role function
  const hasRoleWrapper = useCallback((role: string) => {
    return hasRole(role);
  }, []);

  // Refresh session function
  const refreshSession = useCallback(() => {
    updateSessionState();
  }, [updateSessionState]);

  // Context value
  const contextValue: SessionContextType = {
    // Session state
    isAuthenticated: sessionState.isAuthenticated,
    user: sessionState.user,
    isLoading,
    isInitialized,
    
    // Session actions
    login,
    logout,
    ensureToken: ensureTokenWrapper,
    refreshSession,
    
    // Session utilities
    hasRole: hasRoleWrapper,
    
    // Session recovery
    isRecovering,
    lastRecoveryResult,
    attemptRecovery,
    
    // Session data
    sessionData: sessionState.sessionData,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

/**
 * Higher-order component to wrap components with session provider
 */
export function withSessionProvider<P extends object>(
  Component: React.ComponentType<P>,
  providerProps?: Omit<SessionProviderProps, 'children'>
) {
  return function WrappedComponent(props: P) {
    return (
      <SessionProvider {...providerProps}>
        <Component {...props} />
      </SessionProvider>
    );
  };
}

export default SessionProvider;
/**
 * Simplified Session Provider
 * 
 * Provides a minimal session context for backward compatibility.
 * Removes complex rehydration, token refresh, and session recovery.
 * 
 * Requirements: 1.1, 1.3, 5.1, 5.4, 5.5
 */

"use client";

import React, { createContext, useContext, ReactNode } from 'react';
import {
  isAuthenticated,
  getCurrentUser,
  hasRole,
  login as sessionLogin,
  logout as sessionLogout,
  getSession,
  clearSession,
  type SessionData
} from '@/lib/auth/session';

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
  refreshSession: () => void;
  
  // Session utilities
  hasRole: (role: string) => boolean;
  
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
  autoRehydrate?: boolean;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({
  children,
}) => {
  // Simplified session provider - just provides basic state
  const refreshSession = async () => {
    try {
      const currentUser = getCurrentUser();
      if (currentUser && isAuthenticated()) {
        // Validate session with backend
        const response = await fetch('/api/auth/validate-session', {
          method: 'GET',
          credentials: 'include',
        });

        if (!response.ok) {
          // Session invalid, clear state
          await sessionLogout();
        }
        return response.ok;
      }
      return false;
    } catch (error) {
      console.error('Session refresh failed:', error);
      return false;
    }
  };

  const contextValue: SessionContextType = {
    // Session state
    isAuthenticated: isAuthenticated(),
    user: getCurrentUser(),
    isLoading: false,
    isInitialized: true,

    // Session actions
    login: sessionLogin,
    logout: sessionLogout,
    refreshSession,

    // Session utilities
    hasRole,

    // Session data
    sessionData: getSession(),
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
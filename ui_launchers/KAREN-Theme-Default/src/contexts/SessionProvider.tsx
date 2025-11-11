/**
 * Simplified Session Provider
 * 
 * Provides a minimal session context for backward compatibility.
 * Removes complex rehydration, token refresh, and session recovery.
 * 
 * Requirements: 1.1, 1.3, 5.1, 5.4, 5.5
 */

"use client";

import type { ComponentType, FC, ReactNode } from 'react';
import {
  isAuthenticated,
  getCurrentUser,
  hasRole,
  login as sessionLogin,
  logout as sessionLogout,
  getSession,
} from '@/lib/auth/session';
import { SessionContext, type SessionContextType, type SessionUser } from './session-context';

export interface SessionProviderProps {
  children: ReactNode;
  onSessionChange?: (isAuthenticated: boolean, user: SessionUser | null) => void;
  onSessionError?: (error: Error) => void;
  autoRehydrate?: boolean;
}

export const SessionProvider: FC<SessionProviderProps> = ({
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
/* eslint-disable-next-line react-refresh/only-export-components -- HOC export is retained for legacy usage. */
export function withSessionProvider<P extends object>(
  Component: ComponentType<P>,
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

export { SessionContext };
export type { SessionContextType, SessionUser };

export default SessionProvider;

/**
 * Extension Integration Initializer
 * 
 * Ensures the extension integration service is properly initialized
 */

 "use client";

import { ReactNode, useContext, useMemo } from 'react';
import { AuthContext } from '@/contexts/auth-context-instance';
import {
  ExtensionIntegrationContext,
  useExtensionInitialization,
} from './use-extension-initialization';
import { safeError } from '../safe-console';

/**
 * Extension Integration Provider Component
 * 
 * Wraps children with extension integration initialization
 */
export function ExtensionIntegrationProvider({ children }: { children: ReactNode }) {
  const authContext = useContext(AuthContext);
  const shouldInitializeExtensions = authContext
    ? authContext.authState.isLoading
      ? false
      : authContext.isAuthenticated
    : true;

  const { initialized, error } = useExtensionInitialization(
    shouldInitializeExtensions
  );

  const contextValue = useMemo(
    () => ({
      initialized,
      error,
    }),
    [initialized, error]
  );

  if (error) {
    safeError(
      'ExtensionIntegrationProvider: Extension integration failed to initialize:',
      error
    );
  }

  return (
    <ExtensionIntegrationContext.Provider value={contextValue}>
      {children}
    </ExtensionIntegrationContext.Provider>
  );
}

/**
 * Extension Integration Initializer
 * 
 * Ensures the extension integration service is properly initialized
 */

 "use client";

import { ReactNode, useMemo } from 'react';
import { useIsReadyForApiCalls } from '@/hooks/use-auth-grace-period';
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
  // Only initialize extensions after the auth grace period has passed
  // This prevents 401 errors when backend session hasn't fully propagated yet
  const isReadyForApiCalls = useIsReadyForApiCalls();
  const shouldInitializeExtensions = isReadyForApiCalls;

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

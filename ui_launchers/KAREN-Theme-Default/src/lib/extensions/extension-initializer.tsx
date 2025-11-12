/**
 * Extension Integration Initializer
 * 
 * Ensures the extension integration service is properly initialized
 */

"use client";

import * as React from 'react';
import { safeError } from '../safe-console';
import {
  useExtensionInitialization,
  useExtensionsAvailable as useExtensionsAvailableHook,
} from './hooks';

/**
 * Extension Integration Provider Component
 * 
 * Wraps children with extension integration initialization
 */
export function ExtensionIntegrationProvider({ children }: { children: React.ReactNode }) {
  const { initialized, error } = useExtensionInitialization();

  if (error) {
    safeError('ExtensionIntegrationProvider: Extension integration failed to initialize:', error);
    // Still render children even if extension integration fails
    return <>{children}</>;
  }

  if (!initialized) {
    // Extension integration is loading, but don't block the UI
    return <>{children}</>;
  }

  return <>{children}</>;
}

/**
 * Hook to check if extensions are available
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useExtensionsAvailable() {
  return useExtensionsAvailableHook();
}

// Re-export for convenience
export { useExtensionInitialization } from './hooks';
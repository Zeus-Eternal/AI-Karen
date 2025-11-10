/**
 * Extension Integration Initializer
 * 
 * Ensures the extension integration service is properly initialized
 */

"use client";

import * as React from 'react';
import { useEffect, useState } from 'react';
import { extensionIntegration } from './extension-integration';
import { safeLog, safeError } from '../safe-console';

/**
 * Hook to initialize extension integration service
 */
export function useExtensionInitialization() {
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const initializeExtensions = async () => {
      try {
        safeLog('ExtensionInitializer: Starting extension integration initialization...');
        
        await extensionIntegration.initialize();
        
        if (mounted) {
          setInitialized(true);
          setError(null);
          safeLog('ExtensionInitializer: Extension integration initialized successfully');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        safeError('ExtensionInitializer: Failed to initialize extension integration:', err);
        
        if (mounted) {
          setError(errorMessage);
          setInitialized(false);
        }
      }
    };

    initializeExtensions();

    return () => {
      mounted = false;
    };
  }, []);

  return { initialized, error };
}

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
export function useExtensionsAvailable() {
  const { initialized, error } = useExtensionInitialization();
  return initialized && !error;
}
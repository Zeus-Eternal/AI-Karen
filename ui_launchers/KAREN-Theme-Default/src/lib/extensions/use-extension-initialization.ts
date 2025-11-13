"use client";

import { useEffect, useState } from 'react';
import { extensionIntegration } from './extension-integration';
import { safeLog, safeError } from '../safe-console';

export const EXTENSION_INIT_TIMEOUT = 5000;
export const EXTENSION_RETRY_DELAY = 1000;

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

export function useExtensionsAvailable() {
  const { initialized, error } = useExtensionInitialization();
  return initialized && !error;
}


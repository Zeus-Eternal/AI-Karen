"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { extensionIntegration } from "./extension-integration";
import { safeError, safeLog } from "../safe-console";

export const EXTENSION_INIT_TIMEOUT = 5000;
export const EXTENSION_RETRY_DELAY = 1000;

export interface ExtensionIntegrationState {
  initialized: boolean;
  error: string | null;
}

export const ExtensionIntegrationContext =
  createContext<ExtensionIntegrationState>({
    initialized: false,
    error: null,
  });

export function useExtensionInitialization(shouldInitialize = true) {
  const [state, setState] = useState<ExtensionIntegrationState>({
    initialized: false,
    error: null,
  });
  const initializationRef = useRef<Promise<void> | null>(null);

  useEffect(() => {
    let mounted = true;

    if (!shouldInitialize) {
      if (initializationRef.current) {
        initializationRef.current = null;
      }
      extensionIntegration.shutdown();
      if (mounted) {
        setState({ initialized: false, error: null });
      }
      return () => {
        mounted = false;
      };
    }

    const initializeExtensions = async () => {
      try {
        safeLog("ExtensionInitializer: Starting extension integration initialization...");

        await extensionIntegration.initialize();

        if (mounted) {
          setState({ initialized: true, error: null });
          safeLog("ExtensionInitializer: Extension integration initialized successfully");
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error";
        safeError("ExtensionInitializer: Failed to initialize extension integration:", err);

        if (mounted) {
          setState({ initialized: false, error: errorMessage });
        }
      } finally {
        initializationRef.current = null;
      }
    };

    if (!initializationRef.current) {
      initializationRef.current = initializeExtensions();
    }

    return () => {
      mounted = false;
    };
  }, [shouldInitialize]);

  return state;
}

export function useExtensionsAvailable() {
  const context = useContext(ExtensionIntegrationContext);
  return context.initialized && !context.error;
}

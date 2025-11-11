/**
 * Hook for detecting and managing first-run setup state
 * Checks if super admin exists and manages setup flow
 */
import { useState, useEffect, useCallback } from 'react';
/**
 * First-run setup hook state
 */
export interface UseFirstRunSetupState {
  isLoading: boolean;
  isFirstRun: boolean;
  setupCompleted: boolean;
  setupToken?: string;
  error: string | null;
  lastChecked?: Date;
}
/**
 * First-run setup hook return type
 */
export interface UseFirstRunSetupReturn extends UseFirstRunSetupState {
  checkFirstRun: () => Promise<void>;
  markSetupCompleted: () => void;
  clearError: () => void;
  refresh: () => Promise<void>;
}
/**
 * Hook for managing first-run setup detection
 */
export function useFirstRunSetup(): UseFirstRunSetupReturn {
  const [state, setState] = useState<UseFirstRunSetupState>({
    isLoading: true,
    isFirstRun: false,
    setupCompleted: false,
    error: null
  });

  /**
   * Check if this is the first run by calling the API
   */
  const checkFirstRun = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      // Call production auth endpoint via API proxy
      const response = await fetch('/api/auth/first-run', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        cache: 'no-cache'
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // Production endpoint returns { first_run_required: boolean, message: string }
      const isFirstRun = result.first_run_required === true;

      setState(prev => ({
        ...prev,
        isLoading: false,
        isFirstRun: isFirstRun,
        setupCompleted: !isFirstRun,
        lastChecked: new Date(),
        error: null
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }));
    }
  }, []);
  /**
   * Mark setup as completed (called after successful super admin creation)
   */
  const markSetupCompleted = useCallback(() => {
    setState(prev => ({
      ...prev,
      isFirstRun: false,
      setupCompleted: true,
      setupToken: undefined
    }));
  }, []);
  /**
   * Clear any error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);
  /**
   * Refresh the first-run status
   */
  const refresh = useCallback(async () => {
    await checkFirstRun();
  }, [checkFirstRun]);
  /**
   * Check first-run status on mount
   */
  useEffect(() => {
    checkFirstRun();
  }, [checkFirstRun]);
  return {
    ...state,
    checkFirstRun,
    markSetupCompleted,
    clearError,
    refresh
  };
}
/**
 * Hook for managing first-run setup with automatic redirect
 */
export function useFirstRunSetupWithRedirect(
  redirectPath: string = '/setup'
): UseFirstRunSetupReturn & {
  shouldRedirect: boolean;
} {
  const setupState = useFirstRunSetup();
  const shouldRedirect = !setupState.isLoading && 
                        setupState.isFirstRun && 
                        !setupState.setupCompleted &&
                        typeof window !== 'undefined' &&
                        window.location.pathname !== redirectPath;
  // Perform redirect if needed
  useEffect(() => {
    if (shouldRedirect) {
      window.location.href = redirectPath;
    }
  }, [shouldRedirect, redirectPath]);
  return {
    ...setupState,
    shouldRedirect
  };
}
/**
 * Context provider hook for first-run setup
 * Provides setup state to child components
 */
export function useFirstRunSetupProvider() {
  const setupState = useFirstRunSetup();
  // Additional provider-specific logic can go here
  const isSetupRequired = !setupState.isLoading && 
                         setupState.isFirstRun && 
                         !setupState.setupCompleted;
  const canProceedWithApp = setupState.setupCompleted || 
                           (!setupState.isFirstRun && !setupState.isLoading);
  return {
    ...setupState,
    isSetupRequired,
    canProceedWithApp
  };
}
/**
 * Hook for setup completion tracking
 */
export function useSetupCompletion() {
  const [completionState, setCompletionState] = useState({
    isCompleting: false,
    completionError: null as string | null
  });

  const completeSetup = useCallback(async (_userData: unknown) => {
    setCompletionState({ isCompleting: true, completionError: null });
    try {
      // Setup completion logic would go here
      // This could include additional setup steps after super admin creation
      setCompletionState({ isCompleting: false, completionError: null });
      return true;
    } catch (error) {
      setCompletionState({ 
        isCompleting: false, 
        completionError: error instanceof Error ? error.message : 'Setup completion failed'
      });
      return false;
    }
  }, []);
  return {
    ...completionState,
    completeSetup
  };
}
/**
 * Utility function to check if current route should bypass first-run check
 */
export function shouldBypassFirstRunCheck(pathname: string): boolean {
  const bypassRoutes = [
    '/setup',
    '/api/',
    '/health',
    '/_next/',
    '/favicon.ico'
  ];
  return bypassRoutes.some(route => pathname.startsWith(route));
}
/**
 * Storage utilities for first-run setup state
 */
export const firstRunSetupStorage = {
  /**
   * Get cached first-run status from localStorage
   */
  getCachedStatus(): Partial<UseFirstRunSetupState> | null {
    if (typeof window === 'undefined') return null;
    try {
      const cached = localStorage.getItem('first_run_setup_status');
      if (!cached) return null;
      const parsed = JSON.parse(cached);
      // Check if cache is expired (5 minutes)
      if (parsed.timestamp && Date.now() - parsed.timestamp > 5 * 60 * 1000) {
        localStorage.removeItem('first_run_setup_status');
        return null;
      }
      return parsed.state;
    } catch {
      return null;
    }
  },
  /**
   * Cache first-run status in localStorage
   */
  setCachedStatus(state: Partial<UseFirstRunSetupState>): void {
    if (typeof window === 'undefined') return;
    try {
      const cacheData = {
        state,
        timestamp: Date.now()
      };
      localStorage.setItem('first_run_setup_status', JSON.stringify(cacheData));
    } catch {
      // Ignore localStorage errors
    }
  },
  /**
   * Clear cached first-run status
   */
  clearCachedStatus(): void {
    if (typeof window === 'undefined') return;
    try {
      localStorage.removeItem('first_run_setup_status');
    } catch {
      // Ignore localStorage errors
    }
  }
};

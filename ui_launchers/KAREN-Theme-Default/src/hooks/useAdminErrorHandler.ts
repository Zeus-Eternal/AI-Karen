/**
 * Admin Error Handler Hook
 * 
 * React hook for managing admin operation errors with retry logic,
 * user notifications, and accessibility announcements.
 * 
 * Requirements: 7.2, 7.4
 */

import { useState, useCallback, useRef } from 'react';
import AdminErrorHandler, { type AdminError, type ErrorContext } from '@/lib/errors/admin-error-handler';
import { useAriaLiveRegion } from '@/lib/accessibility/aria-helpers';

export interface UseAdminErrorHandlerOptions {
  maxRetries?: number;
  retryDelay?: number;
  announceErrors?: boolean;
  logErrors?: boolean;
  context?: Partial<ErrorContext>;
}

export interface ErrorState {
  error: AdminError | null;
  isRetrying: boolean;
  retryCount: number;
  lastRetryAt: Date | null;
}

export interface UseAdminErrorHandlerReturn {
  error: AdminError | null;
  isRetrying: boolean;
  retryCount: number;
  setError: (error: AdminError | null) => void;
  handleError: (error: unknown, context?: Partial<ErrorContext>) => void;
  handleAsyncOperation: <T>(
    operation: () => Promise<T>,
    context?: Partial<ErrorContext>
  ) => Promise<T | null>;
  retry: () => Promise<unknown>;
  clearError: () => void;
  canRetry: boolean;
}

export function useAdminErrorHandler(
  options: UseAdminErrorHandlerOptions = {}
): UseAdminErrorHandlerReturn {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    announceErrors = true,
    logErrors = true,
    context: defaultContext = {}
  } = options;
  const normalizedMaxRetries = Math.max(0, maxRetries);
  const normalizedRetryDelay = Math.max(0, retryDelay);

  const [errorState, setErrorState] = useState<ErrorState>({
    error: null,
    isRetrying: false,
    retryCount: 0,
    lastRetryAt: null,
  });

  const lastOperationRef = useRef<{
    operation: () => Promise<unknown>;
    context?: Partial<ErrorContext>;
  } | null>(null);

  const { announce } = useAriaLiveRegion();

  const shouldAttemptRetry = useCallback(
    (adminError: AdminError, attemptNumber: number) => {
      if (attemptNumber > normalizedMaxRetries) {
        return false;
      }
      return AdminErrorHandler.shouldRetry(adminError, attemptNumber);
    },
    [normalizedMaxRetries]
  );

  const setError = useCallback((error: AdminError | null) => {
    setErrorState(prev => ({
      ...prev,
      error,
      isRetrying: false,
      retryCount: error ? prev.retryCount : 0
    }));
  }, []);

  const handleError = useCallback((
    error: unknown,
    context: Partial<ErrorContext> = {}
  ) => {
    let adminError: AdminError;

    if (error instanceof Response) {
      // Handle HTTP Response errors
      adminError = AdminErrorHandler.fromHttpError(error.status, null, {
        operation: 'unknown',
        ...defaultContext,
        ...context,
        timestamp: new Date()
      });
    } else if (error instanceof Error) {
      // Handle JavaScript errors
      adminError = AdminErrorHandler.fromNetworkError(error, {
        operation: 'unknown',
        ...defaultContext,
        ...context,
        timestamp: new Date()
      });
    } else if (typeof error === 'object' && error !== null && 'code' in error) {
      // Handle AdminError objects
      adminError = error as AdminError;
    } else {
      // Handle unknown errors
      adminError = AdminErrorHandler.createError(
        'UNKNOWN_ERROR',
        typeof error === 'string' ? error : 'An unknown error occurred',
        {
          operation: 'unknown',
          ...defaultContext,
          ...context,
          timestamp: new Date()
        }
      );
    }

    // Log error if enabled
    if (logErrors) {
      AdminErrorHandler.logError(adminError, {
        operation: 'unknown',
        ...defaultContext,
        ...context,
        timestamp: new Date()
      });
    }

    // Announce error to screen readers if enabled
    if (announceErrors) {
      const priority = adminError.severity === 'critical' || adminError.severity === 'high'
        ? 'assertive'
        : 'polite';
      announce(`Error: ${adminError.message}`, priority);
    }

    setErrorState(prev => ({
      ...prev,
      error: adminError,
      isRetrying: false
    }));
  }, [defaultContext, logErrors, announceErrors, announce]);

  const handleAsyncOperation = useCallback(async <T>(
    operation: () => Promise<T>,
    context: Partial<ErrorContext> = {}
  ): Promise<T | null> => {
    try {
      // Store operation for potential retry
      lastOperationRef.current = { operation, context };

      // Clear previous error
      setError(null);

      const result = await operation();

      // Reset retry count on success
      setErrorState(prev => ({
        ...prev,
        retryCount: 0,
        lastRetryAt: null
      }));

      return result;
    } catch (error) {
      handleError(error, context);
      return null;
    }
  }, [handleError, setError]);

  const retry = useCallback(async () => {
    const { error } = errorState;
    const lastOperation = lastOperationRef.current;

    const attemptNumber = errorState.retryCount + 1;
    if (!error || !lastOperation || !shouldAttemptRetry(error, attemptNumber)) {
      return;
    }

    try {
      setErrorState(prev => ({
        ...prev,
        isRetrying: true,
        retryCount: prev.retryCount + 1,
        lastRetryAt: new Date()
      }));

      // Announce retry attempt
      if (announceErrors) {
        announce(`Retrying operation, attempt ${errorState.retryCount + 1}`, 'polite');
      }

      // Calculate delay with exponential backoff
      const serverDelay = AdminErrorHandler.getRetryDelay(error, attemptNumber);
      const computedDelay = Math.max(normalizedRetryDelay, serverDelay);
      if (computedDelay > 0) {
        await new Promise(resolve => setTimeout(resolve, computedDelay));
      }

      // Retry the operation
      const result = await lastOperation.operation();

      // Success - clear error and reset retry count
      setErrorState({
        error: null,
        isRetrying: false,
        retryCount: 0,
        lastRetryAt: null,
      });

      if (announceErrors) {
        announce('Operation completed successfully after retry', 'polite');
      }

      return result;
    } catch (retryError) {
      // Retry failed - update error state
      const newAdminError = retryError instanceof Error
        ? AdminErrorHandler.fromNetworkError(retryError)
        : retryError as AdminError;

      setErrorState(prev => ({
        ...prev,
        error: newAdminError,
        isRetrying: false
      }));

      if (logErrors) {
        AdminErrorHandler.logError(newAdminError, {
          operation: 'unknown',
          ...defaultContext,
          ...lastOperation.context,
          timestamp: new Date()
        });
      }

      if (announceErrors) {
        announce(`Retry failed: ${newAdminError.message}`, 'assertive');
      }
    }
  }, [
    announce,
    announceErrors,
    defaultContext,
    errorState,
    logErrors,
    normalizedRetryDelay,
    normalizedMaxRetries,
    shouldAttemptRetry,
  ]);

  const clearError = useCallback(() => {
    setErrorState({
      error: null,
      isRetrying: false,
      retryCount: 0,
      lastRetryAt: null,
    });
    lastOperationRef.current = null;
  }, []);

  const canRetry = errorState.error
    ? shouldAttemptRetry(errorState.error, errorState.retryCount + 1)
    : false;

  return {
    error: errorState.error,
    isRetrying: errorState.isRetrying,
    retryCount: errorState.retryCount,
    setError,
    handleError,
    handleAsyncOperation,
    retry,
    clearError,
    canRetry,
  };
}

// Specialized hooks for common admin operations
export function useUserManagementErrors() {
  return useAdminErrorHandler({
    maxRetries: 2,
    announceErrors: true,
    context: {
      operation: 'user_management',
    },
  });
}

export function useBulkOperationErrors() {
  return useAdminErrorHandler({
    maxRetries: 1, // Bulk operations typically shouldn't auto-retry
    announceErrors: true,
    context: {
      operation: 'bulk_operation',
    },
  });
}

export function useSystemConfigErrors() {
  return useAdminErrorHandler({
    maxRetries: 3,
    announceErrors: true,
    context: {
      operation: 'system_config',
    },
  });
}

export function useAuditLogErrors() {
  return useAdminErrorHandler({
    maxRetries: 2,
    announceErrors: false, // Audit log errors are less critical for UX
    context: {
      operation: 'audit_log',
    },
  });
}

export default useAdminErrorHandler;

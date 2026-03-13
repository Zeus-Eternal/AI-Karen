'use client';

import { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import {
  ErrorCategory,
  ErrorHandlingConfig,
  ErrorInfo,
  ErrorReport,
  ErrorSeverity,
  ErrorType,
  RecoveryAction,
  RecoveryAttempt,
  RecoveryResult,
  UseErrorHandlerReturn,
} from '../types';

type ErrorContextData = Record<string, unknown>;
type TimeoutHandle = ReturnType<typeof setTimeout>;

type ErrorNotifier = {
  notify: (notification: {
    type: 'error' | 'warning';
    title: string;
    message: string;
    timestamp: string;
    metadata?: Record<string, unknown>;
  }) => void;
};

type BrowserWindow = Window & {
  authContext?: {
    userId?: string;
  };
  errorNotificationSystem?: ErrorNotifier;
};

const generateErrorId = (): string =>
  `error_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;

const generateReportId = (): string =>
  `report_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;

const createFallbackRecoveryAction = (): RecoveryAction => ({
  id: 'auto_recovery',
  strategy: 'auto_recovery',
  description: 'Automatic recovery completed',
  priority: 50,
  maxAttempts: 1,
  timeout: 0,
  requiresUserInput: false,
});

const getBrowserWindow = (): BrowserWindow | undefined => {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return window as BrowserWindow;
};

const getContextComponent = (context?: Record<string, unknown>): string => {
  const component = context?.component;
  return typeof component === 'string' ? component : 'unknown';
};

/**
 * Error Handler Hook for CoPilot Frontend
 * 
 * This hook provides comprehensive error handling functionality with:
 * - Error state management
 * - Retry logic with exponential backoff
 * - Recovery strategies
 * - Error reporting
 * - Circuit breaker integration
 * - Context preservation
 */
export const useErrorHandler = (config: Partial<ErrorHandlingConfig> = {}): UseErrorHandlerReturn => {
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [recoveryAttempts, setRecoveryAttempts] = useState<RecoveryAttempt[]>([]);
  const [, setCircuitBreakerState] = useState<'closed' | 'open' | 'half_open'>('closed');

  // Merge config with defaults
  const finalConfig = useMemo<ErrorHandlingConfig>(() => ({
    enableRetry: true,
    enableCircuitBreaker: true,
    enableRecovery: true,
    enableMonitoring: true,
    enableContext: true,
    enableNotifications: true,
    enableReporting: true,
    defaultMaxRetries: 3,
    defaultTimeout: 30000,
    logLevel: 'error',
    ...config,
  }), [config]);

  const errorHistoryRef = useRef<ErrorInfo[]>([]);
  const retryTimeoutsRef = useRef<Map<string, TimeoutHandle>>(new Map());
  const circuitBreakerFailureCountRef = useRef<Map<string, number>>(new Map());

  const clearError = useCallback(() => {
    setError(null);
    setRetryCount(0);
    setIsRecovering(false);
    setRecoveryAttempts([]);
  }, []);

  const logError = useCallback((errorInfo: ErrorInfo) => {
    const logLevel = finalConfig.logLevel;

    if (logLevel === 'debug') {
      console.group(`Error Handler: ${errorInfo.title}`);
      console.error('Error Info:', errorInfo);
      console.error('Context:', errorInfo.context);
      console.error('Metadata:', errorInfo.metadata);
      console.groupEnd();
      return;
    }

    if (logLevel === 'warn') {
      console.warn(`Error Handler: ${errorInfo.title}`, errorInfo);
      return;
    }

    console.error(`Error Handler: ${errorInfo.title}`, errorInfo);
  }, [finalConfig.logLevel]);

  const sendToMonitoring = useCallback((errorInfo: ErrorInfo) => {
    if (!finalConfig.apiEndpoint) {
      return;
    }

    fetch(`${finalConfig.apiEndpoint}/api/errors`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(errorInfo),
    }).catch((monitoringError) => {
      console.warn('Failed to send error to monitoring:', monitoringError);
    });
  }, [finalConfig.apiEndpoint]);

  const sendNotification = useCallback((errorInfo: ErrorInfo) => {
    const browserWindow = getBrowserWindow();

    browserWindow?.errorNotificationSystem?.notify({
      type:
        errorInfo.severity === ErrorSeverity.CRITICAL || errorInfo.severity === ErrorSeverity.FATAL
          ? 'error'
          : 'warning',
      title: errorInfo.title,
      message: errorInfo.message,
      timestamp: errorInfo.timestamp,
      metadata: errorInfo.metadata,
    });
  }, []);

  const updateCircuitBreaker = useCallback((errorInfo: ErrorInfo) => {
    const component = getContextComponent(errorInfo.context);
    const failureCount = circuitBreakerFailureCountRef.current.get(component) ?? 0;
    const nextFailureCount = failureCount + 1;

    circuitBreakerFailureCountRef.current.set(component, nextFailureCount);

    const threshold = finalConfig.circuitBreakerConfig?.failureThreshold ?? 5;
    if (nextFailureCount < threshold) {
      return;
    }

    setCircuitBreakerState('open');

    const timeout = finalConfig.circuitBreakerConfig?.timeout ?? 60000;
    setTimeout(() => {
      setCircuitBreakerState('half_open');
      circuitBreakerFailureCountRef.current.set(component, 0);
    }, timeout);
  }, [finalConfig.circuitBreakerConfig?.failureThreshold, finalConfig.circuitBreakerConfig?.timeout]);

  const handleError = useCallback((input: Error | ErrorInfo, context?: ErrorContextData) => {
    const errorInfo =
      input instanceof Error
        ? {
            id: generateErrorId(),
            type: ErrorType.LOGIC_ERROR,
            category: ErrorCategory.UNKNOWN,
            severity: ErrorSeverity.MEDIUM,
            title: 'Error Occurred',
            message: input.message || 'An unknown error occurred',
            technicalDetails: input.stack || '',
            resolutionSteps: [
              'Try the operation again',
              'Check your input data',
              'Contact support if the problem persists',
            ],
            retryPossible: true,
            userActionRequired: false,
            timestamp: new Date().toISOString(),
            context: context ?? {},
            metadata: {
              originalError: input.name,
              stackTrace: input.stack,
            },
          }
        : input;

    errorHistoryRef.current = [...errorHistoryRef.current.slice(-9), errorInfo];

    setError(errorInfo);
    setIsLoading(false);
    setIsRecovering(false);

    logError(errorInfo);

    if (finalConfig.enableMonitoring) {
      sendToMonitoring(errorInfo);
    }

    if (finalConfig.enableNotifications) {
      sendNotification(errorInfo);
    }

    if (finalConfig.enableCircuitBreaker) {
      updateCircuitBreaker(errorInfo);
    }
  }, [
    finalConfig.enableCircuitBreaker,
    finalConfig.enableMonitoring,
    finalConfig.enableNotifications,
    logError,
    sendNotification,
    sendToMonitoring,
    updateCircuitBreaker,
  ]);

  const retry = useCallback(async (): Promise<void> => {
    if (!error || !finalConfig.enableRetry || isRecovering || isLoading) {
      return;
    }

    const component = getContextComponent(error.context);
    const currentRetryCount = retryCount + 1;
    const maxRetries = finalConfig.retryConfig?.maxRetries ?? finalConfig.defaultMaxRetries;

    if (currentRetryCount > maxRetries) {
      console.warn('Max retries reached');
      return;
    }

    setIsRecovering(true);
    setRetryCount(currentRetryCount);

    try {
      const baseDelay = finalConfig.retryConfig?.baseDelay ?? 1000;
      const backoffMultiplier = finalConfig.retryConfig?.backoffMultiplier ?? 2;
      const delay = baseDelay * Math.pow(backoffMultiplier, currentRetryCount - 1);

      const existingTimeout = retryTimeoutsRef.current.get(component);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      const timeoutId = setTimeout(async () => {
        try {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          clearError();

          finalConfig.retryConfig?.onSuccess?.(currentRetryCount);
        } catch (retryError) {
          console.error('Retry failed:', retryError);
          const errorObj = retryError instanceof Error ? retryError : new Error(String(retryError));

          const retryErrorInfo: ErrorInfo = {
            ...error,
            id: generateErrorId(),
            timestamp: new Date().toISOString(),
            metadata: {
              ...error.metadata,
              retryAttempt: currentRetryCount,
              retryError: errorObj.message
            }
          };

          handleError(retryErrorInfo);

          finalConfig.retryConfig?.onRetry?.(errorObj, currentRetryCount);

          if (currentRetryCount >= maxRetries) {
            finalConfig.retryConfig?.onMaxRetriesReached?.(errorObj);
          }
        }
      }, delay);

      retryTimeoutsRef.current.set(component, timeoutId);
    } catch (retrySetupError) {
      console.error('Error setting up retry:', retrySetupError);
      setIsRecovering(false);
    }
  }, [clearError, error, finalConfig, handleError, isLoading, isRecovering, retryCount]);

  const getUserId = useCallback((): string | undefined => {
    const browserWindow = getBrowserWindow();
    return browserWindow?.authContext?.userId ?? localStorage.getItem('userId') ?? undefined;
  }, []);

  const getSessionId = useCallback((): string | undefined => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    return sessionStorage.getItem('sessionId') ?? undefined;
  }, []);

  const submitErrorReport = useCallback(async (report: ErrorReport): Promise<void> => {
    if (!finalConfig.apiEndpoint) {
      return;
    }

    await fetch(`${finalConfig.apiEndpoint}/api/error-reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(report),
    });
  }, [finalConfig.apiEndpoint]);

  const attemptRecovery = useCallback(async (errorInfo: ErrorInfo): Promise<RecoveryResult> => {
    if (finalConfig.apiEndpoint) {
      const response = await fetch(`${finalConfig.apiEndpoint}/api/error-recovery`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          errorId: errorInfo.id,
          category: errorInfo.category,
          type: errorInfo.type,
          context: errorInfo.context,
        }),
      });

      if (!response.ok) {
        throw new Error('Recovery request failed');
      }

      return response.json();
    }

    return {
      finalStatus: 'success',
      successfulAction: createFallbackRecoveryAction(),
      failedActions: [],
      successfulActions: [],
      totalDuration: 0,
    };
  }, [finalConfig.apiEndpoint]);

  const recover = useCallback(async (): Promise<void> => {
    if (!error || !finalConfig.enableRecovery || isRecovering) {
      return;
    }

    setIsRecovering(true);

    try {
      const recoveryResult = await attemptRecovery(error);

      const attempt: RecoveryAttempt = {
        action: recoveryResult.successfulAction ?? createFallbackRecoveryAction(),
        attemptNumber: recoveryAttempts.length + 1,
        startTime: new Date().toISOString(),
        status: 'success',
        result: recoveryResult.finalResult,
      };

      setRecoveryAttempts((previousAttempts) => [...previousAttempts, attempt]);

      if (recoveryResult.finalStatus === 'success') {
        clearError();
      } else {
        setIsRecovering(false);
      }
    } catch (recoveryError) {
      console.error('Recovery failed:', recoveryError);
      setIsRecovering(false);
      const errorObj = recoveryError instanceof Error ? recoveryError : new Error(String(recoveryError));

      const recoveryErrorInfo: ErrorInfo = {
        ...error,
        id: generateErrorId(),
        timestamp: new Date().toISOString(),
        metadata: {
          ...error.metadata,
          recoveryError: errorObj.message,
          recoveryAttempts: recoveryAttempts.length + 1
        }
      };

      handleError(recoveryErrorInfo);
    }
  }, [attemptRecovery, clearError, error, finalConfig.enableRecovery, handleError, isRecovering, recoveryAttempts.length]);

  const report = useCallback(async (feedback?: string): Promise<void> => {
    if (!error || !finalConfig.enableReporting) {
      return;
    }

    try {
      const browserWindow = getBrowserWindow();
      const errorReport: ErrorReport = {
        id: generateReportId(),
        errorId: error.id,
        userId: getUserId(),
        sessionId: getSessionId(),
        component: error.component,
        operation: error.operation,
        errorInfo: error,
        userFeedback: feedback,
        timestamp: new Date().toISOString(),
        status: 'pending',
        metadata: {
          userAgent: browserWindow?.navigator.userAgent ?? 'Unknown',
          url: browserWindow?.location.href ?? 'Unknown',
        }
      };

      await submitErrorReport(errorReport);

      const updatedError: ErrorInfo = {
        ...error,
        metadata: {
          ...error.metadata,
          reportId: errorReport.id,
          reportStatus: 'submitted',
          userFeedback: feedback
        }
      };

      setError(updatedError);
    } catch (reportError) {
      console.error('Failed to submit error report:', reportError);
    }
  }, [error, finalConfig.enableReporting, getSessionId, getUserId, submitErrorReport]);

  // Cleanup on unmount
  useEffect(() => {
    const retryTimeouts = retryTimeoutsRef.current;

    return () => {
      retryTimeouts.forEach((timeout) => clearTimeout(timeout));
      retryTimeouts.clear();
    };
  }, []);

  return {
    error,
    setError,
    clearError,
    retry,
    recover,
    report,
    isLoading,
    isRecovering,
    retryCount,
    recoveryAttempts
  };
};

export default useErrorHandler;

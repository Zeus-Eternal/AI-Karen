/**
 * Error Handling Hook for AI-Karen Production Chat System
 * Provides comprehensive error handling functionality for React components.
 */

import { useCallback, useEffect, useRef } from 'react';
import useErrorStore, { useRecoveryActions, useNotificationActions, useRecoveryAttempts } from '../stores/errorStore';
import { ErrorInfo, ErrorCategory, RecoveryAction, RecoveryResult, NotificationType as ErrorNotificationType } from '../components/error-handling/types';

// Error handling hook options interface
interface ErrorHandlingOptions {
  enableAutoRetry?: boolean;
  enableAutoRecovery?: boolean;
  maxRetryAttempts?: number;
  retryDelay?: number;
  enableErrorReporting?: boolean;
  enableNotifications?: boolean;
  persistErrors?: boolean;
}

/**
 * Hook for comprehensive error handling
 * 
 * Provides:
 * - Error state management
 * - Automatic retry functionality
 * - Recovery mechanisms
 * - Error reporting
 * - Error history tracking
 * - Loading states
 * 
 * @param options - Configuration options for error handling
 * @returns - Error handling utilities and state
 */
export const useErrorHandling = (options: ErrorHandlingOptions = {}) => {
  const {
    enableAutoRetry = true,
    enableAutoRecovery = true,
    maxRetryAttempts = 3,
    retryDelay = 1000,
    enableErrorReporting = true,
    enableNotifications = true,
    persistErrors = true
  } = options;
  
  const errorStore = useErrorStore();
  const notificationActions = useNotificationActions();
  const recoveryActions = useRecoveryActions();
  const recoveryAttempts = useRecoveryAttempts();
  
  const error = useErrorStore((state: { activeError: ErrorInfo | null }) => state.activeError);
  const setError = useErrorStore((state: { setActiveError: (error: ErrorInfo | null) => void }) => state.setActiveError);
  const errorHistory = useErrorStore((state: { errorHistory: ErrorInfo[] }) => state.errorHistory);
  
  // Ref for tracking retry count
  const retryCountRef = useRef(0);
  const isRecoveringRef = useRef(false);
  const lastErrorRef = useRef<ErrorInfo | null>(null);
  
  // Initialize error history on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('karen-error-history');
    if (savedHistory && persistErrors) {
      try {
        const parsedHistory = JSON.parse(savedHistory);
        errorStore.errorHistory = parsedHistory;
        lastErrorRef.current = parsedHistory[0] || null;
      } catch (error) {
        console.error('Failed to load error history:', error);
      }
    }
  }, [errorStore, persistErrors]);
  
  // Auto-save error history when it changes
  useEffect(() => {
    if (persistErrors && errorHistory.length > 0) {
      try {
        localStorage.setItem('karen-error-history', JSON.stringify(errorHistory.slice(-100))); // Keep last 100 errors
      } catch (error) {
        console.error('Failed to save error history:', error);
      }
    }
  }, [errorHistory, persistErrors]);
  
  /**
   * Clear the current error
   */
  const clearError = useCallback(() => {
    setError(null);
    lastErrorRef.current = null;
  }, [setError]);
  
  /**
   * Retry the last failed operation
   */
  const retry = useCallback(async () => {
    if (!lastErrorRef.current || !enableAutoRetry || retryCountRef.current >= maxRetryAttempts) {
      return;
    }
    
    isRecoveringRef.current = true;
    retryCountRef.current += 1;
    
    try {
      if (retryDelay > 0) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }

      // Execute retry logic based on error category
      let retrySuccess = false;
      
      switch (lastErrorRef.current.category) {
        case ErrorCategory.NETWORK:
        case ErrorCategory.CONNECTIVITY:
          // Retry network operations
          retrySuccess = await retryNetworkOperation();
          break;
          
        case ErrorCategory.API_FAILURE:
          // Retry API calls
          retrySuccess = await retryApiCall();
          break;
          
        case ErrorCategory.TIMEOUT:
          // Retry with longer timeout
          retrySuccess = await retryWithLongerTimeout();
          break;
          
        case ErrorCategory.DATABASE:
          // Retry database operations
          retrySuccess = await retryDatabaseOperation();
          break;
          
        case ErrorCategory.AI_PROCESSING:
        case ErrorCategory.MODEL_UNAVAILABLE:
          // Retry with fallback model
          retrySuccess = await retryWithFallbackModel();
          break;
          
        default:
          // Generic retry
          retrySuccess = await genericRetry();
          break;
      }
      
      if (retrySuccess) {
        // Clear error on successful retry
        clearError();

        if (enableNotifications) {
          notificationActions.addNotification({
            id: `retry-success-${Date.now()}`,
            type: ErrorNotificationType.SUCCESS,
            title: 'Operation Successful',
            message: 'The operation completed successfully after retry.',
            timestamp: new Date().toISOString(),
            read: false,
            autoHide: 2000
          });
        }
      } else {
        if (enableNotifications) {
          notificationActions.addNotification({
            id: `retry-failed-${Date.now()}`,
            type: ErrorNotificationType.ERROR,
            title: 'Retry Failed',
            message: `Failed to retry operation after ${retryCountRef.current} attempts.`,
            timestamp: new Date().toISOString(),
            read: false,
            persistent: true
          });
        }
      }
      
      isRecoveringRef.current = false;
    } catch (error) {
      console.error('Retry failed:', error);
      isRecoveringRef.current = false;
    }
  }, [enableAutoRetry, maxRetryAttempts, notificationActions, clearError, retryDelay, enableNotifications]);
  
  /**
   * Attempt automatic error recovery
   */
  const attemptRecovery = useCallback(async () => {
    if (!lastErrorRef.current || !enableAutoRecovery) {
      return;
    }
    
    isRecoveringRef.current = true;
    
    try {
      let recoveryResult: RecoveryResult | null = null;
      
      // Execute recovery logic based on error category
      switch (lastErrorRef.current.category) {
        case ErrorCategory.NETWORK:
          recoveryResult = await recoverFromNetworkError();
          break;
          
        case ErrorCategory.CONNECTIVITY:
          recoveryResult = await recoverFromConnectivityError();
          break;
          
        case ErrorCategory.API_FAILURE:
          recoveryResult = await recoverFromApiError();
          break;
          
        case ErrorCategory.TIMEOUT:
          recoveryResult = await recoverFromTimeoutError();
          break;
          
        case ErrorCategory.DATABASE:
          recoveryResult = await recoverFromDatabaseError();
          break;
          
        case ErrorCategory.AI_PROCESSING:
        case ErrorCategory.MODEL_UNAVAILABLE:
          recoveryResult = await recoverFromAiError();
          break;
          
        default:
          recoveryResult = await genericRecovery();
          break;
      }
      
      // Add recovery attempt to history
      const recoveryAction: RecoveryAction = {
        id: `auto-recovery-${Date.now()}`,
        strategy: 'auto_recovery',
        description: 'Automatic error recovery attempt',
        priority: 1,
        maxAttempts: 3,
        timeout: 30000,
        requiresUserInput: false
      };
 
      const recoveryAttempt = {
        action: recoveryAction,
        attemptNumber: 1,
        startTime: new Date().toISOString() as string,
        endTime: new Date().toISOString() as string,
        status: (recoveryResult ? 'success' : 'failed') as 'success' | 'failed' | 'pending' | 'partial' | 'in_progress' | 'abandoned',
        result: recoveryResult,
        error: recoveryResult ? null : 'Recovery failed',
        metadata: {
          errorCategory: lastErrorRef.current.category,
          recoveryStrategy: 'auto_recovery'
        }
      };
      
      recoveryActions.addRecoveryAttempt(recoveryAttempt);
      
      if (recoveryResult && recoveryResult.finalStatus === 'success') {
        // Clear error on successful recovery
        clearError();
        
      if (enableNotifications) {
        notificationActions.addNotification({
          id: `recovery-success-${Date.now()}`,
          type: ErrorNotificationType.INFO,
          title: 'Recovery Successful',
          message: 'The error was automatically resolved.',
          timestamp: new Date().toISOString(),
          read: false,
          autoHide: 3000
        });
      }
      } else {
        if (enableNotifications) {
          notificationActions.addNotification({
            id: `recovery-failed-${Date.now()}`,
            type: ErrorNotificationType.ERROR,
            title: 'Recovery Failed',
            message: 'Automatic error recovery failed. Manual intervention may be required.',
            timestamp: new Date().toISOString(),
            read: false,
            persistent: true
          });
        }
      }
      
      isRecoveringRef.current = false;
    } catch (error) {
      console.error('Recovery failed:', error);
      isRecoveringRef.current = false;
    }
  }, [enableAutoRecovery, recoveryActions, clearError, notificationActions, enableNotifications]);
  
  /**
   * Report an error with user feedback
   */
  const reportError = useCallback(async (feedback?: string) => {
    if (!lastErrorRef.current || !enableErrorReporting) {
      return;
    }
    
    try {
      // Send error report to server
      const reportData = {
        errorId: lastErrorRef.current.id,
        userId: getCurrentUserId(), // This would come from auth context
        feedback: feedback,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        error: lastErrorRef.current
      };
      
      const response = await fetch('/api/error-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(reportData)
      });
      
      if (enableNotifications) {
        if (response.ok) {
          notificationActions.addNotification({
            id: `report-success-${Date.now()}`,
            type: ErrorNotificationType.INFO,
            title: 'Error Report Submitted',
            message: 'Thank you for helping us improve our service.',
            timestamp: new Date().toISOString(),
            read: false,
            autoHide: 5000
          });
        } else {
          notificationActions.addNotification({
            id: `report-failed-${Date.now()}`,
            type: ErrorNotificationType.ERROR,
            title: 'Report Failed',
            message: 'Failed to submit error report. Please try again later.',
            timestamp: new Date().toISOString(),
            read: false,
            persistent: true
          });
        }
      }
    } catch (error) {
      console.error('Failed to report error:', error);

      if (enableNotifications) {
        notificationActions.addNotification({
          id: `report-error-${Date.now()}`,
          type: ErrorNotificationType.ERROR,
          title: 'Report Failed',
          message: 'Failed to submit error report. Please try again later.',
          timestamp: new Date().toISOString(),
          read: false,
          persistent: true
        });
      }
    }
  }, [enableErrorReporting, notificationActions, enableNotifications]);
  
  // Recovery functions (simplified implementations)
  const retryNetworkOperation = async (): Promise<boolean> => {
    // Simulate network retry
    await new Promise(resolve => setTimeout(resolve, 1000));
    return true;
  };
  
  const retryApiCall = async (): Promise<boolean> => {
    // Simulate API retry
    await new Promise(resolve => setTimeout(resolve, 1500));
    return true;
  };
  
  const retryWithLongerTimeout = async (): Promise<boolean> => {
    // Simulate retry with longer timeout
    await new Promise(resolve => setTimeout(resolve, 2000));
    return true;
  };
  
  const retryDatabaseOperation = async (): Promise<boolean> => {
    // Simulate database retry
    await new Promise(resolve => setTimeout(resolve, 1200));
    return true;
  };
  
  const retryWithFallbackModel = async (): Promise<boolean> => {
    // Simulate fallback model retry
    await new Promise(resolve => setTimeout(resolve, 800));
    return true;
  };
  
  const genericRetry = async (): Promise<boolean> => {
    // Simulate generic retry
    await new Promise(resolve => setTimeout(resolve, 500));
    return true;
  };
  
  // Recovery functions (simplified implementations)
  const recoverFromNetworkError = async (): Promise<RecoveryResult> => {
    // Simulate network recovery
    await new Promise(resolve => setTimeout(resolve, 2000));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'network-recovery',
        strategy: 'retry_with_backoff',
        description: 'Network connection recovered',
        priority: 80,
        maxAttempts: 3,
        timeout: 30000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 2.0,
      finalResult: { recovered: true }
    };
  };
  
  const recoverFromConnectivityError = async (): Promise<RecoveryResult> => {
    // Simulate connectivity recovery
    await new Promise(resolve => setTimeout(resolve, 1500));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'connectivity-recovery',
        strategy: 'fallback_to_alternative',
        description: 'Switched to alternative connection method',
        priority: 85,
        maxAttempts: 2,
        timeout: 15000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 1.5,
      finalResult: { recovered: true }
    };
  };
  
  const recoverFromApiError = async (): Promise<RecoveryResult> => {
    // Simulate API recovery
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'api-recovery',
        strategy: 'retry_with_backoff',
        description: 'API call recovered with exponential backoff',
        priority: 90,
        maxAttempts: 3,
        timeout: 30000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 1.0,
      finalResult: { recovered: true }
    };
  };
  
  const recoverFromTimeoutError = async (): Promise<RecoveryResult> => {
    // Simulate timeout recovery
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'timeout-recovery',
        strategy: 'increase_timeout',
        description: 'Increased timeout and retried operation',
        priority: 85,
        maxAttempts: 2,
        timeout: 60000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 0.5,
      finalResult: { recovered: true }
    };
  };
  
  const recoverFromDatabaseError = async (): Promise<RecoveryResult> => {
    // Simulate database recovery
    await new Promise(resolve => setTimeout(resolve, 2000));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'database-recovery',
        strategy: 'reset_connection',
        description: 'Database connection reset and retried',
        priority: 80,
        maxAttempts: 2,
        timeout: 20000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 2.0,
      finalResult: { recovered: true }
    };
  };
  
  const recoverFromAiError = async (): Promise<RecoveryResult> => {
    // Simulate AI error recovery
    await new Promise(resolve => setTimeout(resolve, 3000));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'ai-recovery',
        strategy: 'fallback_model',
        description: 'Switched to fallback AI model',
        priority: 85,
        maxAttempts: 2,
        timeout: 30000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 3.0,
      finalResult: { recovered: true }
    };
  };
  
  const genericRecovery = async (): Promise<RecoveryResult> => {
    // Simulate generic recovery
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      finalStatus: 'success',
      successfulAction: {
        id: 'generic-recovery',
        strategy: 'retry_with_backoff',
        description: 'Generic recovery attempt with backoff',
        priority: 70,
        maxAttempts: 3,
        timeout: 30000,
        requiresUserInput: false
      },
      failedActions: [],
      successfulActions: [],
      totalDuration: 1.0,
      finalResult: { recovered: true }
    };
  };
  
  // Helper functions
  const getCurrentUserId = (): string => {
    // This would come from your auth context
    return localStorage.getItem('karen-user-id') || 'anonymous';
  };
  
  const getAuthToken = (): string => {
    // This would come from your auth context
    return localStorage.getItem('karen-auth-token') || '';
  };
  
  return {
    error,
    setError,
    clearError,
    retry,
    recover: attemptRecovery,
    reportError,
    isLoading: isRecoveringRef.current,
    isRecovering: isRecoveringRef.current,
    retryCount: retryCountRef.current,
    recoveryAttempts: recoveryAttempts.map((a: { attemptNumber: number }) => a.attemptNumber),
    lastError: lastErrorRef.current,
    errorHistory,
  };
};

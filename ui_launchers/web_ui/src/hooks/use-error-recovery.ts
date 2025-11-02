import { useState, useCallback, useRef, useEffect } from 'react';
import { useUIStore, selectErrorState } from '../store';

export interface ErrorRecoveryOptions {
  // Maximum number of automatic retries
  maxAutoRetries?: number;
  
  // Delay between retries (in milliseconds)
  retryDelay?: number;
  
  // Exponential backoff multiplier
  backoffMultiplier?: number;
  
  // Whether to retry automatically
  autoRetry?: boolean;
  
  // Custom error filter - return true to retry, false to stop
  shouldRetry?: (error: Error, retryCount: number) => boolean;
  
  // Callback when all retries are exhausted
  onMaxRetriesReached?: (error: Error) => void;
  
  // Callback on successful recovery
  onRecovery?: () => void;
}

export interface ErrorRecoveryState {
  error: Error | null;
  retryCount: number;
  isRetrying: boolean;
  canRetry: boolean;
  lastRetryAt: Date | null;
}

export function useErrorRecovery(
  key: string,
  operation: () => Promise<any>,
  options: ErrorRecoveryOptions = {}
) {
  const {
    maxAutoRetries = 3,
    retryDelay = 1000,
    backoffMultiplier = 2,
    autoRetry = true,
    shouldRetry,
    onMaxRetriesReached,
    onRecovery,
  } = options;
  
  const [state, setState] = useState<ErrorRecoveryState>({
    error: null,
    retryCount: 0,
    isRetrying: false,
    canRetry: true,
    lastRetryAt: null,

  const timeoutRef = useRef<NodeJS.Timeout>();
  const { setError, clearError } = useUIStore(selectErrorState(key));
  
  const calculateDelay = useCallback((retryCount: number) => {
    return retryDelay * Math.pow(backoffMultiplier, retryCount);
  }, [retryDelay, backoffMultiplier]);
  
  const executeOperation = useCallback(async (isRetry = false) => {
    try {
      setState(prev => ({
        ...prev,
        isRetrying: isRetry,
        error: null,
      }));
      
      clearError();
      
      const result = await operation();
      
      // Success - reset state
      setState({
        error: null,
        retryCount: 0,
        isRetrying: false,
        canRetry: true,
        lastRetryAt: null,

      if (isRetry && onRecovery) {
        onRecovery();
      }
      
      return result;
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      
      setState(prev => {
        const newRetryCount = isRetry ? prev.retryCount + 1 : 1;
        const canStillRetry = newRetryCount < maxAutoRetries;
        const shouldRetryError = shouldRetry ? shouldRetry(errorObj, newRetryCount) : true;
        
        return {
          error: errorObj,
          retryCount: newRetryCount,
          isRetrying: false,
          canRetry: canStillRetry && shouldRetryError,
          lastRetryAt: isRetry ? new Date() : prev.lastRetryAt,
        };

      setError(errorObj.message);
      
      // Check if we should auto-retry
      const newRetryCount = isRetry ? state.retryCount + 1 : 1;
      const canStillRetry = newRetryCount < maxAutoRetries;
      const shouldRetryError = shouldRetry ? shouldRetry(errorObj, newRetryCount) : true;
      
      if (autoRetry && canStillRetry && shouldRetryError) {
        const delay = calculateDelay(newRetryCount - 1);
        
        timeoutRef.current = setTimeout(() => {
          executeOperation(true);
        }, delay);
      } else if (newRetryCount >= maxAutoRetries && onMaxRetriesReached) {
        onMaxRetriesReached(errorObj);
      }
      
      throw errorObj;
    }
  }, [
    operation,
    maxAutoRetries,
    autoRetry,
    shouldRetry,
    onMaxRetriesReached,
    onRecovery,
    calculateDelay,
    clearError,
    setError,
    state.retryCount,
  ]);
  
  const manualRetry = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    return executeOperation(true);
  }, [executeOperation]);
  
  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    setState({
      error: null,
      retryCount: 0,
      isRetrying: false,
      canRetry: true,
      lastRetryAt: null,

    clearError();
  }, [clearError]);
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);
  
  return {
    ...state,
    execute: executeOperation,
    retry: manualRetry,
    reset,
  };
}

// Hook for handling network errors specifically
export function useNetworkErrorRecovery(
  key: string,
  operation: () => Promise<any>,
  options: ErrorRecoveryOptions = {}
) {
  const networkAwareOptions: ErrorRecoveryOptions = {
    ...options,
    shouldRetry: (error, retryCount) => {
      // Retry network errors, but not client errors (4xx)
      if (error.message.includes('fetch') || error.message.includes('network')) {
        return true;
      }
      
      // Check for specific HTTP status codes
      if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
        return true;
      }
      
      // Don't retry client errors
      if (error.message.includes('400') || error.message.includes('401') || error.message.includes('403')) {
        return false;
      }
      
      // Use custom shouldRetry if provided
      return options.shouldRetry ? options.shouldRetry(error, retryCount) : true;
    },
  };
  
  return useErrorRecovery(key, operation, networkAwareOptions);
}

// Hook for handling form submission errors
export function useFormErrorRecovery(
  key: string,
  submitFn: (data: any) => Promise<any>,
  options: ErrorRecoveryOptions = {}
) {
  const [formData, setFormData] = useState<any>(null);
  
  const formAwareOptions: ErrorRecoveryOptions = {
    ...options,
    maxAutoRetries: 1, // Usually don't auto-retry form submissions
    autoRetry: false,
    shouldRetry: (error, retryCount) => {
      // Only retry on network errors, not validation errors
      if (error.message.includes('validation') || error.message.includes('invalid')) {
        return false;
      }
      
      return options.shouldRetry ? options.shouldRetry(error, retryCount) : true;
    },
  };
  
  const operation = useCallback(() => {
    if (!formData) {
      throw new Error('No form data to submit');
    }
    return submitFn(formData);
  }, [submitFn, formData]);
  
  const recovery = useErrorRecovery(key, operation, formAwareOptions);
  
  const submitForm = useCallback(async (data: any) => {
    setFormData(data);
    return recovery.execute();
  }, [recovery]);
  
  const retrySubmission = useCallback(() => {
    return recovery.retry();
  }, [recovery]);
  
  return {
    ...recovery,
    submitForm,
    retrySubmission,
    formData,
  };
}
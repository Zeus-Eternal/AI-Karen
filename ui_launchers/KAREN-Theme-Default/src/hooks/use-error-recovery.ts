import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useUIStore, selectErrorState } from '../store';

export interface ErrorRecoveryOptions {
  maxAutoRetries?: number;
  retryDelay?: number;
  backoffMultiplier?: number;
  autoRetry?: boolean;
  shouldRetry?: (error: Error, retryCount: number) => boolean;
  onMaxRetriesReached?: (error: Error) => void;
  onRecovery?: () => void;
}

export interface ErrorRecoveryState {
  error: Error | null;
  retryCount: number;
  isRetrying: boolean;
  canRetry: boolean;
  lastRetryAt: Date | null;
}

const createDefaultErrorRecoveryState = (): ErrorRecoveryState => ({
  error: null,
  retryCount: 0,
  isRetrying: false,
  canRetry: true,
  lastRetryAt: null,
});

export function useErrorRecovery(
  key: string,
  operation: () => Promise<unknown>,
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
  
  const initialState = useMemo(() => createDefaultErrorRecoveryState(), []);
  const [state, setState] = useState<ErrorRecoveryState>(initialState);
  const stateRef = useRef<ErrorRecoveryState>(initialState);

  const syncState = useCallback((updater: (prev: ErrorRecoveryState) => ErrorRecoveryState) => {
    setState(prev => {
      const next = updater(prev);
      stateRef.current = next;
      return next;
    });
  }, []);
  
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { setError, clearError } = useUIStore(selectErrorState(key));
  
  const calculateDelay = useCallback((retryCount: number) => {
    return retryDelay * Math.pow(backoffMultiplier, retryCount);
  }, [retryDelay, backoffMultiplier]);
  
  const executeOperation = useCallback(async function executeOperationImpl(isRetry = false) {
    try {
      syncState(prev => ({
        ...prev,
        isRetrying: isRetry,
        error: null,
      }));

      clearError();

      const result = await operation();

      syncState(() => createDefaultErrorRecoveryState());

      if (isRetry && onRecovery) {
        onRecovery();
      }

      return result;
    } catch (error) {
      const errorObj = error instanceof Error ? error : new Error(String(error));
      const currentState = stateRef.current;
      const nextRetryCount = currentState.retryCount + 1;
      const canStillRetry = nextRetryCount < maxAutoRetries;
      const shouldRetryError = shouldRetry ? shouldRetry(errorObj, nextRetryCount) : true;
      const nextState: ErrorRecoveryState = {
        error: errorObj,
        retryCount: nextRetryCount,
        isRetrying: false,
        canRetry: canStillRetry && shouldRetryError,
        lastRetryAt: isRetry ? new Date() : currentState.lastRetryAt,
      };

      syncState(() => nextState);

      setError(errorObj.message);

      if (autoRetry && nextState.canRetry) {
        const delay = calculateDelay(currentState.retryCount);

        timeoutRef.current = setTimeout(() => {
          executeOperationImpl(true);
        }, delay);
      } else if (nextRetryCount >= maxAutoRetries && onMaxRetriesReached) {
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
    syncState,
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
    
    syncState(() => createDefaultErrorRecoveryState());
    
    clearError();
  }, [clearError, syncState]);
  
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

export function useNetworkErrorRecovery(
  key: string,
  operation: () => Promise<unknown>,
  options: ErrorRecoveryOptions = {}
) {
  const networkAwareOptions: ErrorRecoveryOptions = {
    ...options,
    shouldRetry: (error, retryCount) => {
      if (error.message.includes('fetch') || error.message.includes('network')) {
        return true;
      }
      
      if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
        return true;
      }
      
      if (error.message.includes('400') || error.message.includes('401') || error.message.includes('403')) {
        return false;
      }
      
      return options.shouldRetry ? options.shouldRetry(error, retryCount) : true;
    },
  };
  
  return useErrorRecovery(key, operation, networkAwareOptions);
}

export function useFormErrorRecovery(
  key: string,
  submitFn: (data: unknown) => Promise<unknown>,
  options: ErrorRecoveryOptions = {}
) {
  const [formData, setFormData] = useState<unknown>(null);
  
  const formAwareOptions: ErrorRecoveryOptions = {
    ...options,
    maxAutoRetries: 1,
    autoRetry: false,
    shouldRetry: (error, retryCount) => {
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
  
  const submitForm = useCallback(async (data: unknown) => {
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

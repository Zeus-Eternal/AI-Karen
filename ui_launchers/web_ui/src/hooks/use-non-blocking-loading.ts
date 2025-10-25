import { useState, useCallback, useRef, useEffect } from 'react';
import { useUIStore, selectLoadingState } from '../store';

export interface NonBlockingLoadingOptions {
  // Minimum time to show loading state (prevents flashing)
  minLoadingTime?: number;
  
  // Maximum time to show loading state before timing out
  maxLoadingTime?: number;
  
  // Whether to show loading state immediately or after a delay
  showLoadingDelay?: number;
  
  // Whether to allow interactions during loading
  allowInteractions?: boolean;
  
  // Callback when loading times out
  onTimeout?: () => void;
  
  // Callback when loading starts
  onLoadingStart?: () => void;
  
  // Callback when loading ends
  onLoadingEnd?: () => void;
}

export interface NonBlockingLoadingState {
  isLoading: boolean;
  isVisible: boolean;
  progress: number;
  startTime: Date | null;
  duration: number;
  hasTimedOut: boolean;
}

export function useNonBlockingLoading(
  key: string,
  options: NonBlockingLoadingOptions = {}
) {
  const {
    minLoadingTime = 300,
    maxLoadingTime = 30000,
    showLoadingDelay = 200,
    allowInteractions = true,
    onTimeout,
    onLoadingStart,
    onLoadingEnd,
  } = options;
  
  const [state, setState] = useState<NonBlockingLoadingState>({
    isLoading: false,
    isVisible: false,
    progress: 0,
    startTime: null,
    duration: 0,
    hasTimedOut: false,
  });
  
  const timeoutRef = useRef<NodeJS.Timeout>();
  const minTimeRef = useRef<NodeJS.Timeout>();
  const showDelayRef = useRef<NodeJS.Timeout>();
  const progressRef = useRef<NodeJS.Timeout>();
  const { setLoading } = useUIStore(selectLoadingState(key));
  
  // Update duration periodically
  useEffect(() => {
    if (state.isLoading && state.startTime) {
      const interval = setInterval(() => {
        setState(prev => ({
          ...prev,
          duration: Date.now() - (prev.startTime?.getTime() || 0),
        }));
      }, 100);
      
      return () => clearInterval(interval);
    }
  }, [state.isLoading, state.startTime]);
  
  const startLoading = useCallback(() => {
    const startTime = new Date();
    
    setState({
      isLoading: true,
      isVisible: false,
      progress: 0,
      startTime,
      duration: 0,
      hasTimedOut: false,
    });
    
    // Set loading in store if interactions should be blocked
    if (!allowInteractions) {
      setLoading(true);
    }
    
    // Show loading after delay
    showDelayRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, isVisible: true }));
    }, showLoadingDelay);
    
    // Set timeout
    timeoutRef.current = setTimeout(() => {
      setState(prev => ({ ...prev, hasTimedOut: true }));
      if (onTimeout) {
        onTimeout();
      }
    }, maxLoadingTime);
    
    // Start progress simulation
    let progress = 0;
    const updateProgress = () => {
      progress += Math.random() * 10;
      if (progress > 90) progress = 90; // Never reach 100% until actually done
      
      setState(prev => ({ ...prev, progress }));
      
      if (progress < 90) {
        progressRef.current = setTimeout(updateProgress, 200 + Math.random() * 300);
      }
    };
    
    progressRef.current = setTimeout(updateProgress, 100);
    
    if (onLoadingStart) {
      onLoadingStart();
    }
  }, [
    allowInteractions,
    setLoading,
    showLoadingDelay,
    maxLoadingTime,
    onTimeout,
    onLoadingStart,
  ]);
  
  const stopLoading = useCallback(() => {
    const endLoading = () => {
      setState(prev => ({
        ...prev,
        isLoading: false,
        isVisible: false,
        progress: 100,
      }));
      
      setLoading(false);
      
      if (onLoadingEnd) {
        onLoadingEnd();
      }
    };
    
    // Clear all timeouts
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (showDelayRef.current) clearTimeout(showDelayRef.current);
    if (progressRef.current) clearTimeout(progressRef.current);
    
    // Ensure minimum loading time
    if (state.startTime) {
      const elapsed = Date.now() - state.startTime.getTime();
      if (elapsed < minLoadingTime) {
        minTimeRef.current = setTimeout(endLoading, minLoadingTime - elapsed);
        return;
      }
    }
    
    endLoading();
  }, [state.startTime, minLoadingTime, setLoading, onLoadingEnd]);
  
  const resetLoading = useCallback(() => {
    // Clear all timeouts
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (minTimeRef.current) clearTimeout(minTimeRef.current);
    if (showDelayRef.current) clearTimeout(showDelayRef.current);
    if (progressRef.current) clearTimeout(progressRef.current);
    
    setState({
      isLoading: false,
      isVisible: false,
      progress: 0,
      startTime: null,
      duration: 0,
      hasTimedOut: false,
    });
    
    setLoading(false);
  }, [setLoading]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (minTimeRef.current) clearTimeout(minTimeRef.current);
      if (showDelayRef.current) clearTimeout(showDelayRef.current);
      if (progressRef.current) clearTimeout(progressRef.current);
    };
  }, []);
  
  return {
    ...state,
    startLoading,
    stopLoading,
    resetLoading,
    allowInteractions,
  };
}

// Hook for wrapping async operations with non-blocking loading
export function useNonBlockingOperation<T = any>(
  key: string,
  operation: () => Promise<T>,
  options: NonBlockingLoadingOptions = {}
) {
  const loading = useNonBlockingLoading(key, options);
  const [result, setResult] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  const execute = useCallback(async () => {
    try {
      setError(null);
      setResult(null);
      loading.startLoading();
      
      const result = await operation();
      setResult(result);
      
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      loading.stopLoading();
    }
  }, [operation, loading]);
  
  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    loading.resetLoading();
  }, [loading]);
  
  return {
    ...loading,
    execute,
    reset,
    result,
    error,
  };
}

// Hook for managing multiple non-blocking operations
export function useMultipleNonBlockingOperations() {
  const [operations, setOperations] = useState<Record<string, NonBlockingLoadingState>>({});
  
  const createOperation = useCallback((key: string, options: NonBlockingLoadingOptions = {}) => {
    const loading = useNonBlockingLoading(key, options);
    
    // Update operations state when loading state changes
    useEffect(() => {
      setOperations(prev => ({
        ...prev,
        [key]: loading,
      }));
    }, [loading]);
    
    return loading;
  }, []);
  
  const getOperation = useCallback((key: string) => {
    return operations[key];
  }, [operations]);
  
  const isAnyLoading = useCallback(() => {
    return Object.values(operations).some(op => op.isLoading);
  }, [operations]);
  
  const getLoadingOperations = useCallback(() => {
    return Object.entries(operations)
      .filter(([, op]) => op.isLoading)
      .map(([key]) => key);
  }, [operations]);
  
  return {
    operations,
    createOperation,
    getOperation,
    isAnyLoading,
    getLoadingOperations,
  };
}
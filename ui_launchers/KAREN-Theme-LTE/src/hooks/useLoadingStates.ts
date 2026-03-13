/**
 * Loading States Hook for AI-Karen Production Chat System
 * Provides comprehensive loading state management for React components.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// Loading state interface
export interface LoadingState {
  isLoading: boolean;
  isPending: boolean;
  isDelayed: boolean;
  isTimedOut: boolean;
  progress: number;
  message?: string;
  startTime?: number;
  endTime?: number;
  duration?: number;
  timeout?: number;
  delay?: number;
  operation?: string;
  component?: string;
  metadata?: Record<string, unknown>;
}

// Loading operation interface
export interface LoadingOperation {
  id: string;
  name: string;
  type: 'fetch' | 'upload' | 'process' | 'compute' | 'render' | 'network' | 'database' | 'ai_processing' | 'custom';
  status: 'pending' | 'in_progress' | 'success' | 'failed' | 'cancelled' | 'timeout';
  progress: number;
  startTime: number;
  endTime?: number;
  duration?: number;
  timeout?: number;
  delay?: number;
  message?: string;
  error?: string;
  metadata?: Record<string, unknown>;
  onCancel?: () => void;
}

// Loading context interface
export interface LoadingContext {
  operations: Record<string, LoadingOperation>;
  globalLoading: boolean;
  activeOperations: string[];
  completedOperations: string[];
  failedOperations: string[];
}

// Loading hook options interface
export interface LoadingOptions {
  timeout?: number;
  delay?: number;
  showProgress?: boolean;
  showDelay?: boolean;
  showTimeout?: boolean;
  onCancel?: () => void;
  metadata?: Record<string, unknown>;
  message?: string;
}

// Loading hook return interface
export interface UseLoadingReturn {
  isLoading: boolean;
  isPending: boolean;
  isDelayed: boolean;
  isTimedOut: boolean;
  progress: number;
  message?: string;
  start: (operation?: string, options?: LoadingOptions) => void;
  stop: (success?: boolean, result?: unknown, error?: string) => void;
  update: (progress: number, message?: string) => void;
  cancel: () => void;
  reset: () => void;
  operation: LoadingOperation | null;
}

/**
 * Hook for managing loading states
 * 
 * Provides:
 * - Loading state management
 * - Progress tracking
 * - Timeout handling
 * - Delay detection
 * - Operation cancellation
 * - Loading history
 * 
 * @param initialOptions - Initial configuration options
 * @returns - Loading state utilities and controls
 */
export const useLoading = (initialOptions: LoadingOptions = {}) => {
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: false,
    isPending: false,
    isDelayed: false,
    isTimedOut: false,
    progress: 0,
    message: undefined,
    startTime: undefined,
    endTime: undefined,
    duration: undefined,
    timeout: initialOptions.timeout,
    delay: initialOptions.delay,
    operation: undefined,
    component: undefined,
    metadata: initialOptions.metadata
  });

  const [operation, setOperation] = useState<LoadingOperation | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const delayRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // Start loading operation
  const start = useCallback((
    operationName?: string,
    options: LoadingOptions = {}
  ) => {
    const mergedOptions = { ...initialOptions, ...options };
    const now = Date.now();
    startTimeRef.current = now;

    const newOperation: LoadingOperation = {
      id: `loading-${Date.now()}`,
      name: operationName || 'unknown',
      type: 'custom',
      status: 'pending',
      progress: 0,
      startTime: now,
      timeout: mergedOptions.timeout,
      delay: mergedOptions.delay,
      message: mergedOptions.message as string | undefined,
      metadata: mergedOptions.metadata,
      onCancel: mergedOptions.onCancel
    };

    setOperation(newOperation);
    setLoadingState(prev => ({
      ...prev,
      isLoading: true,
      isPending: true,
      isDelayed: false,
      isTimedOut: false,
      progress: 0,
      message: mergedOptions.message as string | undefined,
      startTime: now,
      endTime: undefined,
      duration: undefined,
      operation: operationName,
      timeout: mergedOptions.timeout,
      delay: mergedOptions.delay,
      component: prev.component,
      metadata: mergedOptions.metadata
    }));

    // Set delay timer if specified
    if (mergedOptions.delay && mergedOptions.delay > 0) {
      delayRef.current = setTimeout(() => {
        setLoadingState(prev => ({
          ...prev,
          isDelayed: true
        }));
        
        if (newOperation.status === 'pending') {
          newOperation.status = 'in_progress';
          setOperation({ ...newOperation });
        }
      }, mergedOptions.delay);
    } else {
      // Start immediately if no delay
      newOperation.status = 'in_progress';
      setOperation({ ...newOperation });
    }

    // Set timeout timer if specified
    if (mergedOptions.timeout && mergedOptions.timeout > 0) {
      timeoutRef.current = setTimeout(() => {
        setLoadingState(prev => ({
          ...prev,
          isTimedOut: true,
          isLoading: false,
          isPending: false,
          endTime: Date.now(),
          duration: prev.startTime ? Date.now() - prev.startTime : undefined
        }));
        
        if (newOperation.status === 'in_progress' || newOperation.status === 'pending') {
          newOperation.status = 'timeout';
          newOperation.endTime = Date.now();
          newOperation.duration = Date.now() - newOperation.startTime;
          newOperation.error = 'Operation timed out';
          setOperation({ ...newOperation });
        }
      }, mergedOptions.timeout);
    }
  }, [initialOptions]);

  // Update loading progress
  const update = useCallback((
    progress: number,
    message?: string
  ) => {
    if (!operation) return;

    const updatedOperation = {
      ...operation,
      progress: Math.max(0, Math.min(100, progress)),
      message: message || operation.message
    };

    setOperation(updatedOperation);
    setLoadingState(prev => ({
      ...prev,
      progress: Math.max(0, Math.min(100, progress)),
      message: message || prev.message
    }));
  }, [operation]);

  // Stop loading operation
  const stop = useCallback((
    success?: boolean,
    result?: unknown,
    error?: string
  ) => {
    if (!operation) return;

    const now = Date.now();
    const duration = startTimeRef.current ? now - startTimeRef.current : undefined;

    // Clear timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (delayRef.current) {
      clearTimeout(delayRef.current);
      delayRef.current = null;
    }

    const finalStatus: LoadingOperation['status'] = success ? 'success' : (error ? 'failed' : 'cancelled');
    const finalOperation = {
      ...operation,
      status: finalStatus,
      progress: success ? 100 : operation.progress,
      endTime: now,
      duration,
      error: error || undefined
    };

    setOperation(finalOperation);
    setLoadingState(prev => ({
      ...prev,
      isLoading: false,
      isPending: false,
      isDelayed: false,
      isTimedOut: operation.status === 'timeout',
      progress: finalOperation.progress,
      endTime: now,
      duration,
      message: finalOperation.message
    }));

    startTimeRef.current = null;
  }, [operation]);

  // Cancel loading operation
  const cancel = useCallback(() => {
    if (!operation) return;

    // Clear timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (delayRef.current) {
      clearTimeout(delayRef.current);
      delayRef.current = null;
    }

    // Call cancel callback if provided
    if (operation.onCancel) {
      operation.onCancel();
    }

    const cancelledOperation: LoadingOperation = {
      ...operation,
      status: 'cancelled' as const,
      endTime: Date.now(),
      duration: startTimeRef.current ? Date.now() - startTimeRef.current : undefined
    };

    setOperation(cancelledOperation);
    setLoadingState(prev => ({
      ...prev,
      isLoading: false,
      isPending: false,
      isDelayed: false,
      isTimedOut: false,
      progress: operation.progress,
      endTime: Date.now(),
      duration: cancelledOperation.duration,
      message: 'Operation cancelled'
    }));

    startTimeRef.current = null;
  }, [operation]);

  // Reset loading state
  const reset = useCallback(() => {
    // Clear timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (delayRef.current) {
      clearTimeout(delayRef.current);
      delayRef.current = null;
    }

    setOperation(null);
    setLoadingState({
      isLoading: false,
      isPending: false,
      isDelayed: false,
      isTimedOut: false,
      progress: 0,
      message: undefined,
      startTime: undefined,
      endTime: undefined,
      duration: undefined,
      timeout: initialOptions.timeout,
      delay: initialOptions.delay,
      operation: undefined,
      component: undefined,
      metadata: initialOptions.metadata
    });

    startTimeRef.current = null;
  }, [initialOptions]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (delayRef.current) {
        clearTimeout(delayRef.current);
      }
    };
  }, []);

  return {
    ...loadingState,
    start,
    stop,
    update,
    cancel,
    reset,
    operation
  };
};

/**
 * Hook for managing multiple loading operations
 * 
 * Provides:
 * - Multi-operation management
 * - Global loading state
 * - Operation history
 * - Concurrent operation control
 * - Operation prioritization
 * 
 * @returns - Loading context utilities and state
 */
export const useLoadingContext = () => {
  const [loadingContext, setLoadingContext] = useState<LoadingContext>({
    operations: {},
    globalLoading: false,
    activeOperations: [],
    completedOperations: [],
    failedOperations: []
  });

  // Add loading operation
  const addOperation = useCallback((operation: LoadingOperation) => {
    setLoadingContext(prev => {
      const newOperations = { ...prev.operations, [operation.id]: operation };
      const isActive = operation.status === 'in_progress' || operation.status === 'pending';
      const activeOperations = isActive 
        ? [...prev.activeOperations, operation.id]
        : prev.activeOperations.filter(id => id !== operation.id);
      
      const isCompleted = operation.status === 'success';
      const completedOperations = isCompleted 
        ? [...prev.completedOperations, operation.id]
        : prev.completedOperations.filter(id => id !== operation.id);
      
      const isFailed = operation.status === 'failed' || operation.status === 'timeout' || operation.status === 'cancelled';
      const failedOperations = isFailed 
        ? [...prev.failedOperations, operation.id]
        : prev.failedOperations.filter(id => id !== operation.id);

      return {
        ...prev,
        operations: newOperations,
        globalLoading: activeOperations.length > 0,
        activeOperations,
        completedOperations,
        failedOperations
      };
    });
  }, []);

  // Update loading operation
  const updateOperation = useCallback((
    operationId: string,
    updates: Partial<LoadingOperation>
  ) => {
    setLoadingContext(prev => {
      const currentOperation = prev.operations[operationId];
      if (!currentOperation) return prev;

      const updatedOperation = { ...currentOperation, ...updates };
      const newOperations = { ...prev.operations, [operationId]: updatedOperation };

      const isActive = updatedOperation.status === 'in_progress' || updatedOperation.status === 'pending';
      const activeOperations = isActive 
        ? [...prev.activeOperations.filter(id => id !== operationId), operationId]
        : prev.activeOperations.filter(id => id !== operationId);
      
      const isCompleted = updatedOperation.status === 'success';
      const completedOperations = isCompleted 
        ? [...prev.completedOperations.filter(id => id !== operationId), operationId]
        : prev.completedOperations.filter(id => id !== operationId);
      
      const isFailed = updatedOperation.status === 'failed' || updatedOperation.status === 'timeout' || updatedOperation.status === 'cancelled';
      const failedOperations = isFailed 
        ? [...prev.failedOperations.filter(id => id !== operationId), operationId]
        : prev.failedOperations.filter(id => id !== operationId);

      return {
        ...prev,
        operations: newOperations,
        globalLoading: activeOperations.length > 0,
        activeOperations,
        completedOperations,
        failedOperations
      };
    });
  }, []);

  // Remove loading operation
  // Remove loading operation
  const removeOperation = useCallback((operationId: string) => {
    setLoadingContext(prev => {
      const remainingOperations = { ...prev.operations };
      delete remainingOperations[operationId];
      
      const activeOperations = prev.activeOperations.filter(id => id !== operationId);
      
      const completedOperations = prev.completedOperations.filter(id => id !== operationId);
      
      const failedOperations = prev.failedOperations.filter(id => id !== operationId);
      return {
        ...prev,
        operations: remainingOperations,
        globalLoading: activeOperations.length > 0,
        activeOperations,
        completedOperations,
        failedOperations
      };
    });
  }, []);

  // Clear all operations
  const clearOperations = useCallback(() => {
    setLoadingContext({
      operations: {},
      globalLoading: false,
      activeOperations: [],
      completedOperations: [],
      failedOperations: []
    });
  }, []);

  // Get operation by ID
  const getOperation = useCallback((operationId: string) => {
    return loadingContext.operations[operationId] || null;
  }, [loadingContext.operations]);

  // Get active operations
  const getActiveOperations = useCallback(() => {
    return loadingContext.activeOperations.map(id => loadingContext.operations[id]).filter(Boolean);
  }, [loadingContext.activeOperations, loadingContext.operations]);

  // Get completed operations
  const getCompletedOperations = useCallback(() => {
    return loadingContext.completedOperations.map(id => loadingContext.operations[id]).filter(Boolean);
  }, [loadingContext.completedOperations, loadingContext.operations]);

  // Get failed operations
  const getFailedOperations = useCallback(() => {
    return loadingContext.failedOperations.map(id => loadingContext.operations[id]).filter(Boolean);
  }, [loadingContext.failedOperations, loadingContext.operations]);

  // Check if any operation is active
  const hasActiveOperation = useCallback(() => {
    return loadingContext.globalLoading;
  }, [loadingContext.globalLoading]);

  return {
    ...loadingContext,
    addOperation,
    updateOperation,
    removeOperation,
    clearOperations,
    getOperation,
    getActiveOperations,
    getCompletedOperations,
    getFailedOperations,
    hasActiveOperation
  };
};

/**
 * Hook for managing upload progress
 * 
 * Provides:
 * - Upload progress tracking
 * - File upload state
 * - Upload speed calculation
 * - Estimated time remaining
 * - Error handling
 * 
 * @param options - Upload configuration options
 * @returns - Upload state and utilities
 */
export const useUploadProgress = (options: {
  onProgress?: (progress: number, loaded: number, total: number, speed: number) => void;
  onComplete?: (result: unknown) => void;
  onError?: (error: string) => void;
  showSpeed?: boolean;
  showTimeRemaining?: boolean;
} = {}) => {
  const { onProgress, onComplete, onError, showSpeed, showTimeRemaining } = options;
  const [uploadState, setUploadState] = useState<{
    isUploading: boolean;
    progress: number;
    loaded: number;
    total: number;
    speed: number;
    timeRemaining: number;
    startTime: number;
    fileName: string;
    fileSize: number;
    error: string | null;
  }>({
    isUploading: false,
    progress: 0,
    loaded: 0,
    total: 0,
    speed: 0,
    timeRemaining: 0,
    startTime: 0,
    fileName: '',
    fileSize: 0,
    error: null
  });

  const progressRef = useRef<number>(0);
  const lastProgressRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(Date.now());

  // Start upload
  const startUpload = useCallback((
    fileName: string,
    fileSize: number
  ) => {
    const now = Date.now();
    progressRef.current = 0;
    lastProgressRef.current = 0;
    lastTimeRef.current = now;

    setUploadState({
      isUploading: true,
      progress: 0,
      loaded: 0,
      total: fileSize,
      speed: 0,
      timeRemaining: 0,
      startTime: now,
      fileName,
      fileSize,
      error: null
    });
  }, []);

  // Update upload progress
  const updateProgress = useCallback((
    loaded: number,
    total: number
  ) => {
    const now = Date.now();
    const progress = total > 0 ? (loaded / total) * 100 : 0;
    
    // Calculate speed (bytes per second)
    const timeDiff = (now - lastTimeRef.current) / 1000;
    const progressDiff = loaded - lastProgressRef.current;
    const speed = timeDiff > 0 ? progressDiff / timeDiff : 0;
    
    // Calculate estimated time remaining
    const remainingBytes = total - loaded;
    const timeRemaining = speed > 0 ? remainingBytes / speed : 0;

    setUploadState(prev => ({
      ...prev,
      progress,
      loaded,
      total,
      speed: showSpeed ? speed : prev.speed,
      timeRemaining: showTimeRemaining ? timeRemaining : prev.timeRemaining
    }));

    if (onProgress) {
      onProgress(progress, loaded, total, speed);
    }

    progressRef.current = loaded;
    lastProgressRef.current = loaded;
    lastTimeRef.current = now;
  }, [onProgress, showSpeed, showTimeRemaining]);

  // Complete upload
  const completeUpload = useCallback((result?: unknown) => {
    setUploadState(prev => ({
      ...prev,
      isUploading: false,
      progress: 100,
      error: null
    }));

    if (onComplete) {
      onComplete(result);
    }
  }, [onComplete]);

  // Fail upload
  const failUpload = useCallback((error: string) => {
    setUploadState(prev => ({
      ...prev,
      isUploading: false,
      error
    }));

    if (onError) {
      onError(error);
    }
  }, [onError]);

  // Reset upload state
  const resetUpload = useCallback(() => {
    setUploadState({
      isUploading: false,
      progress: 0,
      loaded: 0,
      total: 0,
      speed: 0,
      timeRemaining: 0,
      startTime: 0,
      fileName: '',
      fileSize: 0,
      error: null
    });

    progressRef.current = 0;
    lastProgressRef.current = 0;
    lastTimeRef.current = Date.now();
  }, []);

  return {
    ...uploadState,
    startUpload,
    updateProgress,
    completeUpload,
    failUpload,
    resetUpload
  };
};

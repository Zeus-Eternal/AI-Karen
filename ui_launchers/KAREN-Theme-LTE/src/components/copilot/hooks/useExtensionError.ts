import { useState, useEffect, useCallback, useRef } from 'react';
import { ExtensionErrorCode, ExtensionError } from '../types/extension';
import ExtensionErrorService, {
  ExtensionErrorInfo,
  ExtensionErrorSeverity
} from '../services/ExtensionErrorService';

interface UseExtensionErrorOptions {
  /** Auto-initialize error service */
  autoInitialize?: boolean;
  
  /** Extension ID to filter errors by */
  extensionId?: string;
  
  /** Whether to include resolved errors */
  includeResolved?: boolean;
}

interface UseExtensionErrorResult {
  /** Error service instance */
  errorService: ExtensionErrorService;
  
  /** Errors */
  errors: ExtensionErrorInfo[];
  
  /** Loading state */
  isLoading: boolean;
  
  /** Error state */
  error: string | null;
  
  /** Report an error */
  reportError: (
    extensionId: string, 
    errorCode: ExtensionErrorCode, 
    message: string, 
    details?: any,
    context?: Record<string, any>
  ) => void;
  
  /** Get errors for an extension */
  getErrors: (extensionId: string, includeResolved?: boolean) => ExtensionErrorInfo[];
  
  /** Get all errors */
  getAllErrors: (includeResolved?: boolean) => ExtensionErrorInfo[];
  
  /** Get errors by severity */
  getErrorsBySeverity: (severity: ExtensionErrorSeverity, includeResolved?: boolean) => ExtensionErrorInfo[];
  
  /** Get unresolved errors */
  getUnresolvedErrors: (extensionId: string) => ExtensionErrorInfo[];
  
  /** Resolve an error */
  resolveError: (extensionId: string, errorIndex: number) => boolean;
  
  /** Resolve all errors */
  resolveAllErrors: (extensionId: string) => number;
  
  /** Clear errors */
  clearErrors: (extensionId: string) => boolean;
  
  /** Get error statistics */
  getErrorStats: (extensionId: string) => {
    total: number;
    resolved: number;
    unresolved: number;
    bySeverity: Record<ExtensionErrorSeverity, number>;
    byCode: Record<ExtensionErrorCode, number>;
  };
  
  /** Add error event listener */
  addErrorEventListener: (eventType: string, listener: (event: any) => void) => void;
  
  /** Remove error event listener */
  removeErrorEventListener: (eventType: string, listener: (event: any) => void) => void;
}

/**
 * React hook for managing CoPilot extension errors
 */
export const useExtensionError = (options: UseExtensionErrorOptions = {}): UseExtensionErrorResult => {
  const {
    autoInitialize = true,
    extensionId,
    includeResolved = false
  } = options;
  
  // State
  const [errorService] = useState(() => ExtensionErrorService.getInstance());
  const [errors, setErrors] = useState<ExtensionErrorInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const isMountedRef = useRef(true);
  const eventListenersRef = useRef<Map<string, Function[]>>(new Map());
  
  // Update errors based on filters
  const updateErrors = useCallback(() => {
    try {
      let filteredErrors: ExtensionErrorInfo[] = [];
      
      if (extensionId) {
        // Get errors for specific extension
        filteredErrors = errorService.getErrors(extensionId, includeResolved);
      } else {
        // Get all errors
        filteredErrors = errorService.getAllErrors(includeResolved);
      }
      
      if (isMountedRef.current) {
        setErrors(filteredErrors);
      }
    } catch (err) {
      console.error('Failed to update errors:', err);
      if (isMountedRef.current) {
        setError('Failed to update errors');
      }
    }
  }, [errorService, extensionId, includeResolved]);
  
  // Initialize on mount
  useEffect(() => {
    if (autoInitialize) {
      setIsLoading(false);
      updateErrors();
    }
    
    // Set up event listeners to update state
    const handleErrorEvent = () => {
      if (isMountedRef.current) {
        updateErrors();
      }
    };
    
    errorService.addErrorEventListener('error_reported', handleErrorEvent);
    errorService.addErrorEventListener('error_resolved', handleErrorEvent);
    errorService.addErrorEventListener('errors_cleared', handleErrorEvent);
    
    return () => {
      isMountedRef.current = false;
      
      // Clean up event listeners
      errorService.removeErrorEventListener('error_reported', handleErrorEvent);
      errorService.removeErrorEventListener('error_resolved', handleErrorEvent);
      errorService.removeErrorEventListener('errors_cleared', handleErrorEvent);
      
      // Clean up tracked listeners
      for (const [eventType, listeners] of eventListenersRef.current) {
        for (const listener of listeners) {
          errorService.removeErrorEventListener(eventType, listener as any);
        }
      }
    };
  }, [autoInitialize, updateErrors, errorService]);
  
  // Report an error
  const reportError = useCallback((
    extensionId: string, 
    errorCode: ExtensionErrorCode, 
    message: string, 
    details?: any,
    context?: Record<string, any>
  ): void => {
    try {
      errorService.reportError(extensionId, errorCode, message, details, context);
      
      // Update state if this error is for the filtered extension
      if (!extensionId || extensionId === extensionId) {
        if (isMountedRef.current) {
          updateErrors();
        }
      }
    } catch (err) {
      console.error(`Failed to report error for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to report error for extension ${extensionId}`);
      }
    }
  }, [errorService, updateErrors, extensionId]);
  
  // Get errors for an extension
  const getErrors = useCallback((extensionId: string, includeResolved?: boolean): ExtensionErrorInfo[] => {
    return errorService.getErrors(extensionId, includeResolved);
  }, [errorService]);
  
  // Get all errors
  const getAllErrors = useCallback((includeResolved?: boolean): ExtensionErrorInfo[] => {
    return errorService.getAllErrors(includeResolved);
  }, [errorService]);
  
  // Get errors by severity
  const getErrorsBySeverity = useCallback((
    severity: ExtensionErrorSeverity, 
    includeResolved?: boolean
  ): ExtensionErrorInfo[] => {
    return errorService.getErrorsBySeverity(severity, includeResolved);
  }, [errorService]);
  
  // Get unresolved errors
  const getUnresolvedErrors = useCallback((extensionId: string): ExtensionErrorInfo[] => {
    return errorService.getUnresolvedErrors(extensionId);
  }, [errorService]);
  
  // Resolve an error
  const resolveError = useCallback((
    extensionId: string, 
    errorIndex: number
  ): boolean => {
    try {
      const success = errorService.resolveError(extensionId, errorIndex);
      
      // Update state if this error is for the filtered extension
      if (!extensionId || extensionId === extensionId) {
        if (isMountedRef.current) {
          updateErrors();
        }
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to resolve error ${errorIndex} for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to resolve error ${errorIndex} for extension ${extensionId}`);
      }
      return false;
    }
  }, [errorService, updateErrors, extensionId]);
  
  // Resolve all errors
  const resolveAllErrors = useCallback((extensionId: string): number => {
    try {
      const count = errorService.resolveAllErrors(extensionId);
      
      // Update state if this error is for the filtered extension
      if (!extensionId || extensionId === extensionId) {
        if (isMountedRef.current) {
          updateErrors();
        }
      }
      
      return count;
    } catch (err) {
      console.error(`Failed to resolve all errors for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to resolve all errors for extension ${extensionId}`);
      }
      return 0;
    }
  }, [errorService, updateErrors, extensionId]);
  
  // Clear errors
  const clearErrors = useCallback((extensionId: string): boolean => {
    try {
      const success = errorService.clearErrors(extensionId);
      
      // Update state if this error is for the filtered extension
      if (!extensionId || extensionId === extensionId) {
        if (isMountedRef.current) {
          updateErrors();
        }
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to clear errors for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to clear errors for extension ${extensionId}`);
      }
      return false;
    }
  }, [errorService, updateErrors, extensionId]);
  
  // Get error statistics
  const getErrorStats = useCallback((extensionId: string) => {
    return errorService.getErrorStats(extensionId);
  }, [errorService]);
  
  // Add error event listener
  const addErrorEventListener = useCallback((
    eventType: string, 
    listener: (event: any) => void
  ): void => {
    errorService.addErrorEventListener(eventType, listener);
    
    // Track for cleanup
    if (!eventListenersRef.current.has(eventType)) {
      eventListenersRef.current.set(eventType, []);
    }
    eventListenersRef.current.get(eventType)?.push(listener);
  }, [errorService]);
  
  // Remove error event listener
  const removeErrorEventListener = useCallback((
    eventType: string, 
    listener: (event: any) => void
  ): void => {
    errorService.removeErrorEventListener(eventType, listener);
    
    // Remove from tracking
    const listeners = eventListenersRef.current.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }, [errorService]);
  
  return {
    errorService,
    errors,
    isLoading,
    error,
    reportError,
    getErrors,
    getAllErrors,
    getErrorsBySeverity,
    getUnresolvedErrors,
    resolveError,
    resolveAllErrors,
    clearErrors,
    getErrorStats,
    addErrorEventListener,
    removeErrorEventListener
  };
};

export default useExtensionError;
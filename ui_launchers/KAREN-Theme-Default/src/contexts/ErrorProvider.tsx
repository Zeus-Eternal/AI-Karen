/**
 * Error Provider for Intelligent Error Handling
 * 
 * Provides React context for intelligent error detection, analysis,
 * and response generation across the application.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */

"use client";

import { createContext, useCallback, useState } from 'react';
import type { ErrorInfo, FC, ReactNode } from 'react';
import { safeError } from '@/lib/safe-console';
import { useIntelligentError, useIntelligentErrorBoundary, useIntelligentApiError, type ErrorAnalysisResponse, type ErrorAnalysisRequest, type UseIntelligentErrorOptions } from '@/hooks/use-intelligent-error';

interface ExtendedApiError extends Error {
  status?: number;
  isNetworkError?: boolean;
  isCorsError?: boolean;
  isTimeoutError?: boolean;
  responseTime?: number;
}

export interface ErrorContextType {
  // Current error analysis
  currentAnalysis: ErrorAnalysisResponse | null;
  isAnalyzing: boolean;
  analysisError: string | null;
  
  // Error handling functions
  analyzeError: (error: Error | string, context?: Partial<ErrorAnalysisRequest>) => Promise<void>;
  handleApiError: (error: ExtendedApiError, requestContext?: {
    endpoint?: string;
    method?: string;
    provider?: string;
  }) => void;
  handleBoundaryError: (error: Error, errorInfo?: ErrorInfo) => void;
  
  // Error management
  clearError: () => void;
  retryAnalysis: () => Promise<void>;
  retryCount: number;
  
  // Global error state
  globalErrors: Array<{
    id: string;
    error: Error | string;
    analysis: ErrorAnalysisResponse | null;
    timestamp: Date;
    context?: Partial<ErrorAnalysisRequest>;
  }>;
  addGlobalError: (error: Error | string, context?: Partial<ErrorAnalysisRequest>) => string;
  removeGlobalError: (id: string) => void;
  clearAllErrors: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export { ErrorContext };

// Hook moved to separate file for React Fast Refresh compatibility

interface ApiErrorLike extends Error {
  status?: number;
  isNetworkError?: boolean;
  isCorsError?: boolean;
  isTimeoutError?: boolean;
  responseTime?: number;
}

export interface ErrorProviderProps {
  children: ReactNode;
  options?: UseIntelligentErrorOptions;
  onErrorAnalyzed?: (analysis: ErrorAnalysisResponse) => void;
  onAnalysisError?: (error: Error) => void;
  maxGlobalErrors?: number;
}

type ApiErrorLike = Error & {
  status?: number;
  isNetworkError?: boolean;
  isCorsError?: boolean;
  isTimeoutError?: boolean;
  responseTime?: number;
};

export const ErrorProvider: FC<ErrorProviderProps> = ({
  children,
  options = {},
  onErrorAnalyzed,
  onAnalysisError,
  maxGlobalErrors = 10,
}) => {
  const [globalErrors, setGlobalErrors] = useState<Array<{
    id: string;
    error: Error | string;
    analysis: ErrorAnalysisResponse | null;
    timestamp: Date;
    context?: Partial<ErrorAnalysisRequest>;
  }>>([]);

  // Main intelligent error hook
  const {
    onAnalysisComplete: optionsOnAnalysisComplete,
    onAnalysisError: optionsOnAnalysisError,
    ...intelligentOptions
  } = options;

  const handleAnalysisComplete = useCallback((analysis: ErrorAnalysisResponse) => {
    onErrorAnalyzed?.(analysis);
    optionsOnAnalysisComplete?.(analysis);
    setGlobalErrors(prev => {
      const updated = [...prev];
      const errorIndex = updated.findIndex(e => e.analysis === null);
      if (errorIndex !== -1) {
        updated[errorIndex] = {
          ...updated[errorIndex],
          analysis,
        };
      }
      return updated;
    });
  }, [onErrorAnalyzed, optionsOnAnalysisComplete]);

  const handleAnalysisError = useCallback((error: Error) => {
    onAnalysisError?.(error);
    optionsOnAnalysisError?.(error);
  }, [onAnalysisError, optionsOnAnalysisError]);

  const intelligentError = useIntelligentError({
    ...intelligentOptions,
    onAnalysisComplete: handleAnalysisComplete,
    onAnalysisError: handleAnalysisError,
  });

  // Error boundary hook
  const boundaryError = useIntelligentErrorBoundary({
    ...options,
    autoAnalyze: false, // We'll handle this manually
  });

  // API error hook
  const apiError = useIntelligentApiError({
    ...options,
    autoAnalyze: false, // We'll handle this manually
  });

  // Generate unique error ID
  const generateErrorId = useCallback(() => {
    return `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Add global error
  const addGlobalError = useCallback((
    error: Error | string,
    context?: Partial<ErrorAnalysisRequest>
  ): string => {
    const id = generateErrorId();
    const newError = {
      id,
      error,
      analysis: null,
      timestamp: new Date(),
      context,
    };

    setGlobalErrors(prev => {
      const updated = [newError, ...prev];
      // Limit the number of global errors
      return updated.slice(0, maxGlobalErrors);
    });

    // Analyze the error after state update
    intelligentError.analyzeError(error, context);

    return id;
  }, [generateErrorId, maxGlobalErrors, intelligentError]);

  // Remove global error
  const removeGlobalError = useCallback((id: string) => {
    setGlobalErrors(prev => prev.filter(error => error.id !== id));
  }, []);

  // Clear all errors
  const clearAllErrors = useCallback(() => {
    setGlobalErrors([]);
    intelligentError.clearAnalysis();
    boundaryError.clearAnalysis();
    apiError.clearAnalysis();
  }, [intelligentError, boundaryError, apiError]);

  // Handle boundary errors
  const handleBoundaryError = useCallback((error: Error, errorInfo?: ErrorInfo) => {
    safeError('Error boundary caught error:', error, { useStructuredLogging: true });
    if (errorInfo) {
      safeError('Error info:', errorInfo, { useStructuredLogging: true });
    }

    const boundaryInfo = errorInfo as { componentStack?: string } | undefined;

    const context: Partial<ErrorAnalysisRequest> = {
      error_type: error.name,
      user_context: {
        component_stack: boundaryInfo?.componentStack,
        error_boundary: true,
        timestamp: new Date().toISOString(),
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined,
      },
    };

    // Add to global errors
    addGlobalError(error, context);

    // Use boundary error hook for analysis
    boundaryError.handleError(error, boundaryInfo);
  }, [addGlobalError, boundaryError]);

  // Handle API errors
  const handleApiError = useCallback((error: ExtendedApiError, requestContext?: {
    endpoint?: string;
    method?: string;
    provider?: string;
  }) => {
    safeError('API error occurred:', error, { useStructuredLogging: true });
    if (requestContext) {
      safeError('Request context:', requestContext, { useStructuredLogging: true });
    }
    
    const apiErrorDetails = error as ApiErrorLike;

    const context: Partial<ErrorAnalysisRequest> = {
      status_code: apiErrorDetails.status,
      error_type: error.name || 'ApiError',
      request_path: requestContext?.endpoint,
      provider_name: requestContext?.provider,
      user_context: {
        method: requestContext?.method,
        is_network_error: apiErrorDetails.isNetworkError,
        is_cors_error: apiErrorDetails.isCorsError,
        is_timeout_error: apiErrorDetails.isTimeoutError,
        response_time: apiErrorDetails.responseTime,
        timestamp: new Date().toISOString(),
      },
    };

    // Add to global errors
    addGlobalError(error, context);
    
    // Use API error hook for analysis
    apiError.handleApiError(error, requestContext);
  }, [addGlobalError, apiError]);

  // Context value
  const contextValue: ErrorContextType = {
    // Current error analysis (from main hook)
    currentAnalysis: intelligentError.analysis,
    isAnalyzing: intelligentError.isAnalyzing,
    analysisError: intelligentError.analysisError,
    
    // Error handling functions
    analyzeError: intelligentError.analyzeError,
    handleApiError,
    handleBoundaryError,
    
    // Error management
    clearError: intelligentError.clearAnalysis,
    retryAnalysis: intelligentError.retryAnalysis,
    retryCount: intelligentError.retryCount,
    
    // Global error state
    globalErrors,
    addGlobalError,
    removeGlobalError,
    clearAllErrors,
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  );
};

export default ErrorProvider;

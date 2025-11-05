/**
 * Error Provider for Intelligent Error Handling
 * 
 * Provides React context for intelligent error detection, analysis,
 * and response generation across the application.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */

"use client";

import React, { createContext, useContext, useCallback, useState, ReactNode } from 'react';
import { safeError } from '@/lib/safe-console';
import { useIntelligentError, useIntelligentErrorBoundary, useIntelligentApiError, type ErrorAnalysisResponse, type ErrorAnalysisRequest, type UseIntelligentErrorOptions } from '@/hooks/use-intelligent-error';

export interface ErrorContextType {
  // Current error analysis
  currentAnalysis: ErrorAnalysisResponse | null;
  isAnalyzing: boolean;
  analysisError: string | null;
  
  // Error handling functions
  analyzeError: (error: Error | string, context?: Partial<ErrorAnalysisRequest>) => Promise<void>;
  handleApiError: (error: any, requestContext?: {
    endpoint?: string;
    method?: string;
    provider?: string;
  }) => void;
  handleBoundaryError: (error: Error, errorInfo?: any) => void;
  
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

export const useError = () => {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

interface ErrorProviderProps {
  children: ReactNode;
  options?: UseIntelligentErrorOptions;
  onErrorAnalyzed?: (analysis: ErrorAnalysisResponse) => void;
  onAnalysisError?: (error: Error) => void;
  maxGlobalErrors?: number;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({
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
  const intelligentError = useIntelligentError({
    ...options,
    onAnalysisComplete: (analysis) => {
      onErrorAnalyzed?.(analysis);
      options.onAnalysisComplete?.(analysis);
    },
    onAnalysisError: (error) => {
      onAnalysisError?.(error);
      options.onAnalysisError?.(error);
    },
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

    // Analyze the error
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
  const handleBoundaryError = useCallback((error: Error, errorInfo?: any) => {
    safeError('Error boundary caught error:', error, { useStructuredLogging: true });
    if (errorInfo) {
      safeError('Error info:', errorInfo, { useStructuredLogging: true });
    }
    
    const context: Partial<ErrorAnalysisRequest> = {
      error_type: error.name,
      user_context: {
        component_stack: errorInfo?.componentStack,
        error_boundary: true,
        timestamp: new Date().toISOString(),
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined,
      },
    };

    // Add to global errors
    addGlobalError(error, context);
    
    // Use boundary error hook for analysis
    boundaryError.handleError(error, errorInfo);
  }, [addGlobalError, boundaryError]);

  // Handle API errors
  const handleApiError = useCallback((error: any, requestContext?: {
    endpoint?: string;
    method?: string;
    provider?: string;
  }) => {
    safeError('API error occurred:', error, { useStructuredLogging: true });
    if (requestContext) {
      safeError('Request context:', requestContext, { useStructuredLogging: true });
    }
    
    const context: Partial<ErrorAnalysisRequest> = {
      status_code: error.status,
      error_type: error.name || 'ApiError',
      request_path: requestContext?.endpoint,
      provider_name: requestContext?.provider,
      user_context: {
        method: requestContext?.method,
        is_network_error: error.isNetworkError,
        is_cors_error: error.isCorsError,
        is_timeout_error: error.isTimeoutError,
        response_time: error.responseTime,
        timestamp: new Date().toISOString(),
      },
    };

    // Add to global errors
    addGlobalError(error, context);
    
    // Use API error hook for analysis
    apiError.handleApiError(error, requestContext);
  }, [addGlobalError, apiError]);

  // Update global errors with analysis results
  React.useEffect(() => {
    if (intelligentError.analysis) {
      setGlobalErrors(prev => {
        const updated = [...prev];
        // Find the most recent error without analysis and update it
        const errorIndex = updated.findIndex(e => e.analysis === null);
        if (errorIndex !== -1) {
          updated[errorIndex] = {
            ...updated[errorIndex],
            analysis: intelligentError.analysis,
          };
        }
        return updated;
      });
    }
  }, [intelligentError.analysis]);

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

/**
 * Higher-order component to wrap components with error provider
 */
export function withErrorProvider<P extends object>(
  Component: React.ComponentType<P>,
  providerProps?: Omit<ErrorProviderProps, 'children'>
) {
  return function WrappedComponent(props: P) {
    return (
      <ErrorProvider {...providerProps}>
        <Component {...props} />
      </ErrorProvider>
    );
  };
}

export default ErrorProvider;
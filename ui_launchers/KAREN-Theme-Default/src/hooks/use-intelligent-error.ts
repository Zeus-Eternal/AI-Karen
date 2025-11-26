/**
 * Hook for Intelligent Error Detection and Response
 * 
 * Provides automatic error detection, intelligent response fetching,
 * and error state management for components.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { safeError } from '@/lib/safe-console';
import { useApiClient } from '@/hooks/use-api-client';

export interface ErrorAnalysisRequest {
  error_message: string;
  error_type?: string;
  status_code?: number;
  provider_name?: string;
  request_path?: string;
  user_context?: Record<string, unknown>;
  use_ai_analysis?: boolean;
}

export interface ErrorAnalysisResponse {
  title: string;
  summary: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  next_steps: string[];
  provider_health?: {
    name: string;
    status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
    success_rate: number;
    response_time: number;
    error_message?: string;
    last_check?: string;
  };
  contact_admin: boolean;
  retry_after?: number;
  help_url?: string;
  technical_details?: string;
  cached: boolean;
  response_time_ms: number;
}

export interface UseIntelligentErrorOptions {
  autoAnalyze?: boolean;
  useAiAnalysis?: boolean;
  debounceMs?: number;
  maxRetries?: number;
  onAnalysisComplete?: (analysis: ErrorAnalysisResponse) => void;
  onAnalysisError?: (error: Error) => void;
}

export interface UseIntelligentErrorReturn {
  analysis: ErrorAnalysisResponse | null;
  isAnalyzing: boolean;
  analysisError: string | null;
  analyzeError: (error: Error | string, context?: Partial<ErrorAnalysisRequest>) => Promise<void>;
  retryAnalysis: () => Promise<void>;
  clearAnalysis: () => void;
  retryCount: number;
}

/**
 * Hook for intelligent error analysis and response generation
 */
export function useIntelligentError(options: UseIntelligentErrorOptions = {}): UseIntelligentErrorReturn {
  const {
    autoAnalyze = true,
    useAiAnalysis = true,
    debounceMs = 500,
    maxRetries = 3,
    onAnalysisComplete,
    onAnalysisError,
  } = options;

  const [analysis, setAnalysis] = useState<ErrorAnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<{ error: Error | string; context?: Partial<ErrorAnalysisRequest> } | null>(null);

  const apiClient = useApiClient();
  const client = typeof window !== 'undefined' ? apiClient : null;
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Perform error analysis
   */
  const performAnalysis = useCallback(async (
    error: Error | string,
    context: Partial<ErrorAnalysisRequest> = {}
  ) => {
    // Cancel any pending analysis
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const errorMessage = typeof error === 'string' ? error : error.message;
      const errorType = typeof error === 'object' && error.constructor ? error.constructor.name : undefined;

      const request: ErrorAnalysisRequest = {
        error_message: errorMessage,
        error_type: errorType,
        use_ai_analysis: useAiAnalysis,
        ...context,
      };

      if (!client) {
        // Skip API call during server-side rendering
        const fallbackAnalysis: ErrorAnalysisResponse = {
          title: 'Error Analysis Unavailable',
          summary: 'Error analysis is not available during server-side rendering.',
          category: 'system_error',
          severity: 'low',
          next_steps: [
            'Try refreshing the page',
            'Contact admin if the problem persists'
          ],
          contact_admin: false,
          cached: false,
          response_time_ms: 0,
          technical_details: `Original error: ${typeof error === 'string' ? error : error.message}`,
        };
        setAnalysis(fallbackAnalysis);
        setIsAnalyzing(false);
        return;
      }

      const response = await client.post<ErrorAnalysisResponse>(
        '/api/error-response/analyze',
        request,
        {
          headers: {
            'X-Request-ID': `error-analysis-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          }
        }
      );

      // Check if request was aborted
      if (abortController.signal.aborted) {
        return;
      }

      setAnalysis(response.data);
      setRetryCount(0);
      onAnalysisComplete?.(response.data);

    } catch (err: unknown) {
      // Check if request was aborted
      if (abortController.signal.aborted) {
        return;
      }

      safeError('Error analysis failed:', err);
      const errorMessage = (err as Error).message || 'Failed to analyze error';
      setAnalysisError(errorMessage);
      onAnalysisError?.(err as Error);

      // Create fallback analysis for critical errors
      if (retryCount >= maxRetries) {
        const fallbackAnalysis: ErrorAnalysisResponse = {
          title: 'Error Analysis Unavailable',
          summary: 'Unable to generate intelligent error response. The error analysis service may be temporarily unavailable.',
          category: 'system_error',
          severity: 'medium',
          next_steps: [
            'Try refreshing the page',
            'Check your internet connection',
            'Contact admin if the problem persists'
          ],
          contact_admin: true,
          cached: false,
          response_time_ms: 0,
          technical_details: `Original error: ${typeof error === 'string' ? error : error.message}\nAnalysis error: ${errorMessage}`,
        };
        setAnalysis(fallbackAnalysis);
      }
    } finally {
      setIsAnalyzing(false);
      abortControllerRef.current = null;
    }
  }, [client, useAiAnalysis, retryCount, maxRetries, onAnalysisComplete, onAnalysisError]);

  /**
   * Debounced error analysis
   */
  const analyzeError = useCallback(async (
    error: Error | string,
    context: Partial<ErrorAnalysisRequest> = {}
  ) => {
    // Store the error for potential retry
    setLastError({ error, context });

    // Clear existing debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Debounce the analysis to avoid rapid-fire requests
    debounceTimeoutRef.current = setTimeout(() => {
      if (autoAnalyze) {
        performAnalysis(error, context);
      }
    }, debounceMs);
  }, [autoAnalyze, debounceMs, performAnalysis]);

  /**
   * Retry the last analysis
   */
  const retryAnalysis = useCallback(async () => {
    if (!lastError || retryCount >= maxRetries) {
      return;
    }

    setRetryCount(prev => prev + 1);
    await performAnalysis(lastError.error, lastError.context);
  }, [lastError, retryCount, maxRetries, performAnalysis]);

  /**
   * Clear analysis state
   */
  const clearAnalysis = useCallback(() => {
    // Cancel any pending analysis
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    setAnalysis(null);
    setAnalysisError(null);
    setIsAnalyzing(false);
    setRetryCount(0);
    setLastError(null);
  }, []);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Cancel any pending analysis
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Clear debounce timeout
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  return {
    analysis,
    isAnalyzing,
    analysisError,
    analyzeError,
    retryAnalysis,
    clearAnalysis,
    retryCount,
  };
}

/**
 * Hook for automatic error boundary integration
 */
export function useIntelligentErrorBoundary(options: UseIntelligentErrorOptions = {}) {
  const intelligentError = useIntelligentError(options);

  /**
   * Error boundary handler that automatically analyzes errors
   */
  const handleError = useCallback((error: Error, errorInfo?: unknown) => {
    const context: Partial<ErrorAnalysisRequest> = {
      error_type: error.name,
      user_context: {
        component_stack: (errorInfo as { componentStack?: string })?.componentStack,
        error_boundary: true,
        timestamp: new Date().toISOString(),
        user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined,
      },
    };

    intelligentError.analyzeError(error, context);
  }, [intelligentError]);

  return {
    ...intelligentError,
    handleError,
  };
}

/**
 * Hook for API error detection and analysis
 */
export function useIntelligentApiError(options: UseIntelligentErrorOptions = {}) {
  const intelligentError = useIntelligentError(options);

  /**
   * API error handler that extracts relevant context
   */
  const handleApiError = useCallback((error: Error, requestContext?: {
    endpoint?: string;
    method?: string;
    provider?: string;
  }) => {
    const context: Partial<ErrorAnalysisRequest> = {
      status_code: (error as { status?: number }).status,
      error_type: error.name || 'ApiError',
      request_path: requestContext?.endpoint,
      provider_name: requestContext?.provider,
      user_context: {
        method: requestContext?.method,
        is_network_error: (error as { isNetworkError?: boolean }).isNetworkError,
        is_cors_error: (error as { isCorsError?: boolean }).isCorsError,
        is_timeout_error: (error as { isTimeoutError?: boolean }).isTimeoutError,
        response_time: (error as { responseTime?: number }).responseTime,
        timestamp: new Date().toISOString(),
      },
    };

    intelligentError.analyzeError(error, context);
  }, [intelligentError]);

  return {
    ...intelligentError,
    handleApiError,
  };
}

export default useIntelligentError;
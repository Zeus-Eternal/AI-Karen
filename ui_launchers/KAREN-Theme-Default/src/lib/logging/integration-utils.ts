/**
 * Integration utilities for connecting logging system with existing components
 */

import { connectivityLogger } from './connectivity-logger';
import { correlationTracker } from './correlation-tracker';
import { performanceTracker } from './performance-tracker';

/**
 * Enhanced fetch wrapper with logging
 */
export async function loggedFetch(
  url: string,
  options: RequestInit = {},
  operationName?: string
): Promise<Response> {
  const correlationId = correlationTracker.getCurrentCorrelationId();
  const method = options.method || 'GET';
  const opName = operationName || `${method} ${url}`;
  
  // Start performance tracking
  const networkTracker = performanceTracker.trackNetworkRequest(url, method);
  networkTracker.start();
  
  // Add correlation ID to headers
  const headers = new Headers(options.headers);
  headers.set('X-Correlation-ID', correlationId);
  
  try {
    connectivityLogger.logConnectivity(
      'debug',
      `Starting ${method} request to ${url}`,
      {
        url,
        method,
        backendUrl: url
      },
      undefined,
      undefined,
      { correlationId }
    );
    
    const response = await fetch(url, {
      ...options,
      headers
    });
    const metrics = networkTracker.end(response.status);
    
    connectivityLogger.logConnectivity(
      response.ok ? 'info' : 'warn',
      `${method} request to ${url} completed with status ${response.status}`,
      {
        url,
        method,
        statusCode: response.status,
        backendUrl: url
      },
      undefined,
      metrics,
      { correlationId }
    );
    
    // Log performance if slow
    if (metrics.duration && metrics.duration > 5000) {
      connectivityLogger.logPerformance(
        'warn',
        `Slow network request detected: ${opName}`,
        {
          operation: opName,
          duration: metrics.duration,
          threshold: 5000,
          exceeded: true
        }
      );
    }
    
    return response;
  } catch (error) {
    const metrics = networkTracker.end(undefined, error as Error);
    
    connectivityLogger.logConnectivity(
      'error',
      `${method} request to ${url} failed`,
      {
        url,
        method,
        backendUrl: url
      },
      error as Error,
      metrics,
      { correlationId }
    );
    
    throw error;
  }
}

/**
 * Enhanced fetch with retry and logging
 */
export async function loggedFetchWithRetry(
  url: string,
  options: RequestInit = {},
  maxRetries: number = 3,
  operationName?: string
): Promise<Response> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        connectivityLogger.logConnectivity(
          'info',
          `Retrying request to ${url} (attempt ${attempt + 1}/${maxRetries + 1})`,
          {
            url,
            method: options.method || 'GET',
            retryAttempt: attempt,
            backendUrl: url
          }
        );
        
        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      
      return await loggedFetch(url, options, operationName);
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxRetries) {
        connectivityLogger.logConnectivity(
          'error',
          `All retry attempts failed for ${url}`,
          {
            url,
            method: options.method || 'GET',
            retryAttempt: attempt,
            backendUrl: url
          },
          lastError
        );
        break;
      }
    }
  }
  
  throw lastError;
}

/**
 * Authentication logging wrapper
 */
export function logAuthenticationAttempt<T>(
  operation: () => Promise<T>,
  email?: string,
  operationType: 'login' | 'logout' | 'session_validation' | 'token_refresh' = 'login'
): Promise<T> {
  return correlationTracker.withCorrelationAsync(
    correlationTracker.generateCorrelationId(),
    async () => {
      const startTime = Date.now();
      
      try {
        connectivityLogger.logAuthentication(
          'info',
          `Starting ${operationType} attempt`,
          {
            email,
            success: false // Will be updated on success
          },
          operationType
        );
        
        const result = await operation();
        const duration = Date.now() - startTime;
        
        connectivityLogger.logAuthentication(
          'info',
          `${operationType} attempt succeeded`,
          {
            email,
            success: true
          },
          operationType,
          undefined,
          {
            startTime: Date.now() - duration,
            endTime: Date.now(),
            duration,
            responseTime: duration
          }
        );
        
        return result;
      } catch (error) {
        const duration = Date.now() - startTime;
        
        connectivityLogger.logAuthentication(
          'error',
          `${operationType} attempt failed`,
          {
            email,
            success: false,
            failureReason: (error as Error).message
          },
          operationType,
          error as Error,
          {
            startTime: Date.now() - duration,
            endTime: Date.now(),
            duration,
            responseTime: duration
          }
        );
        
        throw error;
      }
    }
  );
}

/**
 * Performance monitoring wrapper for React components
 */
export function withPerformanceLogging<T extends (...args: unknown[]) => unknown>(
  fn: T,
  operationName: string
): T {
  return ((...args: unknown[]) => {
    const { result, metrics } = performanceTracker.trackSyncOperation(
      operationName,
      () => fn(...args)
    );
    
    if (metrics.duration && metrics.duration > 100) {
      connectivityLogger.logPerformance(
        metrics.duration > 1000 ? 'warn' : 'info',
        `Component operation: ${operationName}`,
        {
          operation: operationName,
          duration: metrics.duration,
          threshold: 100,
          exceeded: metrics.duration > 100
        }
      );
    }
    
    return result;
  }) as T;
}

/**
 * Async performance monitoring wrapper
 */
export function withAsyncPerformanceLogging<T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  operationName: string
): T {
  return (async (...args: unknown[]) => {
    const { result, metrics } = await performanceTracker.trackOperation(
      operationName,
      () => fn(...args)
    );
    
    if (metrics.duration && metrics.duration > 1000) {
      connectivityLogger.logPerformance(
        metrics.duration > 5000 ? 'warn' : 'info',
        `Async operation: ${operationName}`,
        {
          operation: operationName,
          duration: metrics.duration,
          threshold: 1000,
          exceeded: metrics.duration > 1000
        }
      );
    }
    
    return result;
  }) as T;
}

/**
 * Error boundary logging
 */
export function logComponentError(
  error: Error,
  errorInfo: { componentStack: string },
  componentName: string
): void {
  connectivityLogger.logError(
    `React component error in ${componentName}`,
    error,
    'error',
    {
      correlationId: correlationTracker.getCurrentCorrelationId()
    }
  );
}

/**
 * Session management logging
 */
export function logSessionEvent(
  event: 'created' | 'validated' | 'expired' | 'refreshed',
  sessionId?: string,
  userId?: string
): void {
  connectivityLogger.logAuthentication(
    'info',
    `Session ${event}`,
    {
      success: event !== 'expired',
      failureReason: event === 'expired' ? 'Session expired' : undefined
    },
    'session_validation',
    undefined,
    undefined,
    {
      sessionId,
      userId
    }
  );
}
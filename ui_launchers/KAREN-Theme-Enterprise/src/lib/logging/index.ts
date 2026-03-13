/**
 * Structured logging system for connectivity and authentication monitoring
 */

import { connectivityLogger } from './connectivity-logger';
import type { PerformanceMetrics } from './types';

export * from './types';
export * from './correlation-tracker';
export * from './performance-tracker';
export * from './connectivity-logger';

// Re-export main instances for convenience
export { correlationTracker } from './correlation-tracker';
export { performanceTracker } from './performance-tracker';
export { connectivityLogger } from './connectivity-logger';

// Utility functions for common logging scenarios
export const logAuthAttempt = (
  email: string,
  success: boolean,
  failureReason?: string,
  metrics?: PerformanceMetrics
) => {
  connectivityLogger.logAuthentication(
    success ? 'info' : 'warn',
    `Authentication attempt ${success ? 'succeeded' : 'failed'}`,
    {
      email,
      success,
      failureReason,
      attemptNumber: 1
    },
    'login',
    undefined,
    metrics
  );
};

export const logConnectivityIssue = (
  url: string,
  method: string,
  error: Error,
  retryAttempt?: number,
  metrics?: PerformanceMetrics
) => {
  connectivityLogger.logConnectivity(
    'error',
    `Connectivity issue with ${method} ${url}`,
    {
      url,
      method,
      retryAttempt
    },
    error,
    metrics
  );
};

export const logPerformanceIssue = (
  operation: string,
  duration: number,
  threshold: number
) => {
  connectivityLogger.logPerformance(
    duration > threshold ? 'warn' : 'info',
    `Performance ${duration > threshold ? 'issue' : 'metric'} for ${operation}`,
    {
      operation,
      duration,
      threshold,
      exceeded: duration > threshold
    }
  );
};

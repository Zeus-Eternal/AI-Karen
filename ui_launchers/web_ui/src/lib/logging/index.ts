/**
 * Structured logging system for connectivity and authentication monitoring
 */

export * from './types';
export * from './correlation-tracker';
export * from './performance-tracker';
export * from './connectivity-logger';

// Re-export main instances for convenience
import { export { correlationTracker } from './correlation-tracker';
import { export { performanceTracker } from './performance-tracker';
import { export { connectivityLogger } from './connectivity-logger';

// Utility functions for common logging scenarios
export const logAuthAttempt = (
  email: string,
  success: boolean,
  failureReason?: string,
  metrics?: any
) => {
  const { connectivityLogger } = require('./connectivity-logger');
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
  metrics?: any
) => {
  const { connectivityLogger } = require('./connectivity-logger');
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
  const { connectivityLogger } = require('./connectivity-logger');
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
/**
 * Retry Mechanisms System
 * 
 * Provides comprehensive retry functionality with exponential backoff,
 * circuit breaker patterns, and intelligent failure detection.
 */

import React from 'react';

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
  jitter: boolean;
  retryCondition?: (error: any, attempt: number) => boolean;
  onRetry?: (error: any, attempt: number) => void;
  onSuccess?: (result: any, attempt: number) => void;
  onFailure?: (error: any, attempts: number) => void;
}

export interface RetryState {
  attempt: number;
  isRetrying: boolean;
  lastError: Error | null;
  nextRetryIn: number;
  totalAttempts: number;
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  monitoringPeriod: number;
}

export interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half-open';
  failures: number;
  lastFailureTime: number;
  nextAttemptTime: number;
}

class RetryMechanismService {
  private circuitBreakers = new Map<string, CircuitBreakerState>();
  private activeRetries = new Map<string, RetryState>();

  // Default retry configuration
  private defaultConfig: RetryConfig = {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffFactor: 2,
    jitter: true,
    retryCondition: this.defaultRetryCondition,
  };

  // Default circuit breaker configuration
  private defaultCircuitBreakerConfig: CircuitBreakerConfig = {
    failureThreshold: 5,
    resetTimeout: 60000,
    monitoringPeriod: 300000, // 5 minutes
  };

  private defaultRetryCondition(error: any, attempt: number): boolean {
    // Retry on network errors, 5xx errors, and timeouts
    if (error.name === 'NetworkError' || error.name === 'TimeoutError') {
      return true;
    }

    if (error.status >= 500 && error.status < 600) {
      return true;
    }

    // Retry on specific error codes
    if (error.status === 408 || error.status === 429) {
      return true;
    }

    // Don't retry on client errors (4xx except 408, 429)
    if (error.status >= 400 && error.status < 500) {
      return false;
    }

    return true;
  }

  public async withRetry<T>(
    operation: () => Promise<T>,
    config: Partial<RetryConfig> = {},
    operationId?: string
  ): Promise<T> {
    const finalConfig = { ...this.defaultConfig, ...config };
    const id = operationId || this.generateOperationId();

    // Initialize retry state
    this.activeRetries.set(id, {
      attempt: 0,
      isRetrying: false,
      lastError: null,
      nextRetryIn: 0,
      totalAttempts: 0,

    try {
      return await this.executeWithRetry(operation, finalConfig, id);
    } finally {
      this.activeRetries.delete(id);
    }
  }

  private async executeWithRetry<T>(
    operation: () => Promise<T>,
    config: RetryConfig,
    operationId: string
  ): Promise<T> {
    const state = this.activeRetries.get(operationId)!;
    let lastError: any;

    for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
      state.attempt = attempt;
      state.totalAttempts = attempt;

      try {
        // Check circuit breaker
        if (operationId && !this.canExecute(operationId)) {
          throw new Error('Circuit breaker is open');
        }

        const result = await operation();
        
        // Success - reset circuit breaker and call success callback
        if (operationId) {
          this.recordSuccess(operationId);
        }
        
        config.onSuccess?.(result, attempt);
        return result;

      } catch (error) {
        lastError = error;
        state.lastError = error instanceof Error ? error : new Error(String(error));

        // Record failure for circuit breaker
        if (operationId) {
          this.recordFailure(operationId);
        }

        // Check if we should retry
        const shouldRetry = attempt < config.maxAttempts && 
                           (config.retryCondition?.(error, attempt) ?? true);

        if (!shouldRetry) {
          break;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = this.calculateDelay(attempt, config);
        state.nextRetryIn = delay;
        state.isRetrying = true;

        config.onRetry?.(error, attempt);

        // Wait before retrying
        await this.delay(delay);
        state.isRetrying = false;
      }
    }

    // All retries exhausted
    config.onFailure?.(lastError, config.maxAttempts);
    throw lastError;
  }

  private calculateDelay(attempt: number, config: RetryConfig): number {
    let delay = config.baseDelay * Math.pow(config.backoffFactor, attempt - 1);
    
    // Apply maximum delay limit
    delay = Math.min(delay, config.maxDelay);
    
    // Add jitter to prevent thundering herd
    if (config.jitter) {
      delay = delay * (0.5 + Math.random() * 0.5);
    }
    
    return Math.floor(delay);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private generateOperationId(): string {
    return `retry-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Circuit Breaker Implementation
  public canExecute(operationId: string): boolean {
    const state = this.getCircuitBreakerState(operationId);
    const now = Date.now();

    switch (state.state) {
      case 'closed':
        return true;

      case 'open':
        if (now >= state.nextAttemptTime) {
          // Transition to half-open
          state.state = 'half-open';
          return true;
        }
        return false;

      case 'half-open':
        return true;

      default:
        return true;
    }
  }

  public recordSuccess(operationId: string): void {
    const state = this.getCircuitBreakerState(operationId);
    
    if (state.state === 'half-open') {
      // Reset to closed state
      state.state = 'closed';
      state.failures = 0;
    }
  }

  public recordFailure(operationId: string): void {
    const state = this.getCircuitBreakerState(operationId);
    const config = this.defaultCircuitBreakerConfig;
    const now = Date.now();

    state.failures++;
    state.lastFailureTime = now;

    if (state.failures >= config.failureThreshold) {
      state.state = 'open';
      state.nextAttemptTime = now + config.resetTimeout;
    }
  }

  private getCircuitBreakerState(operationId: string): CircuitBreakerState {
    if (!this.circuitBreakers.has(operationId)) {
      this.circuitBreakers.set(operationId, {
        state: 'closed',
        failures: 0,
        lastFailureTime: 0,
        nextAttemptTime: 0,

    }
    return this.circuitBreakers.get(operationId)!;
  }

  // Public API for getting retry state
  public getRetryState(operationId: string): RetryState | null {
    return this.activeRetries.get(operationId) || null;
  }

  public getCircuitBreakerStatus(operationId: string): CircuitBreakerState {
    return this.getCircuitBreakerState(operationId);
  }

  public resetCircuitBreaker(operationId: string): void {
    this.circuitBreakers.set(operationId, {
      state: 'closed',
      failures: 0,
      lastFailureTime: 0,
      nextAttemptTime: 0,

  }

  // Specialized retry methods
  public async retryFetch(
    url: string,
    options: RequestInit = {},
    config: Partial<RetryConfig> = {}
  ): Promise<Response> {
    const operationId = `fetch-${url}`;
    
    return this.withRetry(
      async () => {
        const response = await fetch(url, options);
        
        if (!response.ok) {
          const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
          (error as any).status = response.status;
          (error as any).response = response;
          throw error;
        }
        
        return response;
      },
      {
        ...config,
        retryCondition: (error, attempt) => {
          // Custom retry logic for HTTP requests
          if (error.status === 429) {
            // Rate limited - always retry with longer delay
            return true;
          }
          return this.defaultRetryCondition(error, attempt);
        },
      },
      operationId
    );
  }

  public async retryAsync<T>(
    asyncFn: () => Promise<T>,
    config: Partial<RetryConfig> = {}
  ): Promise<T> {
    return this.withRetry(asyncFn, config);
  }

  // Batch retry operations
  public async retryBatch<T>(
    operations: Array<() => Promise<T>>,
    config: Partial<RetryConfig> = {}
  ): Promise<Array<T | Error>> {
    const results = await Promise.allSettled(
      operations.map(op => this.withRetry(op, config))
    );

    return results.map(result => 
      result.status === 'fulfilled' ? result.value : result.reason
    );
  }

  // Cleanup old circuit breaker states
  public cleanup(): void {
    const now = Date.now();
    const maxAge = this.defaultCircuitBreakerConfig.monitoringPeriod;

    for (const [operationId, state] of this.circuitBreakers.entries()) {
      if (now - state.lastFailureTime > maxAge && state.failures === 0) {
        this.circuitBreakers.delete(operationId);
      }
    }
  }
}

// Create singleton instance
export const retryMechanism = new RetryMechanismService();

// React hook for retry functionality
export function useRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {},
  dependencies: any[] = []
) {
  const [state, setState] = React.useState<{
    data: T | null;
    error: Error | null;
    isLoading: boolean;
    isRetrying: boolean;
    attempt: number;
    canRetry: boolean;
  }>({
    data: null,
    error: null,
    isLoading: false,
    isRetrying: false,
    attempt: 0,
    canRetry: true,

  const operationId = React.useRef<string>();

  const execute = React.useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    operationId.current = retryMechanism['generateOperationId']();

    try {
      const result = await retryMechanism.withRetry(
        operation,
        {
          ...config,
          onRetry: (error, attempt) => {
            setState(prev => ({ 
              ...prev, 
              isRetrying: true, 
              attempt,
              error: error instanceof Error ? error : new Error(String(error))
            }));
            config.onRetry?.(error, attempt);
          },
        },
        operationId.current
      );

      setState(prev => ({ 
        ...prev, 
        data: result, 
        isLoading: false, 
        isRetrying: false,
        error: null,
        canRetry: true,
      }));

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setState(prev => ({ 
        ...prev, 
        error: err, 
        isLoading: false, 
        isRetrying: false,
        canRetry: prev.attempt < (config.maxAttempts || 3),
      }));
    }
  }, [operation, config, ...dependencies]);

  const retry = React.useCallback(() => {
    if (state.canRetry) {
      execute();
    }
  }, [execute, state.canRetry]);

  const reset = React.useCallback(() => {
    setState({
      data: null,
      error: null,
      isLoading: false,
      isRetrying: false,
      attempt: 0,
      canRetry: true,

    if (operationId.current) {
      retryMechanism.resetCircuitBreaker(operationId.current);
    }
  }, []);

  return {
    ...state,
    execute,
    retry,
    reset,
  };
}

// Hook for fetch with retry
export function useRetryFetch(
  url: string,
  options: RequestInit = {},
  config: Partial<RetryConfig> = {}
) {
  return useRetry(
    () => retryMechanism.retryFetch(url, options, config),
    config,
    [url, JSON.stringify(options)]
  );
}

export default retryMechanism;
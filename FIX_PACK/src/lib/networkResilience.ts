import { telemetryService } from './telemetry';

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
  jitterMax?: number;
  retryCondition?: (error: Error) => boolean;
  onRetry?: (attempt: number, error: Error) => void;
  correlationId?: string;
}

export interface CircuitBreakerOptions {
  failureThreshold?: number;
  recoveryTimeout?: number;
  monitoringPeriod?: number;
  correlationId?: string;
}

export interface NetworkRequest {
  url: string;
  options?: RequestInit;
  timeout?: number;
}

export enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

export class CircuitBreaker {
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failureCount = 0;
  private lastFailureTime = 0;
  private successCount = 0;
  private readonly failureThreshold: number;
  private readonly recoveryTimeout: number;
  private readonly monitoringPeriod: number;
  private readonly correlationId?: string;

  constructor(options: CircuitBreakerOptions = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.recoveryTimeout = options.recoveryTimeout || 60000; // 1 minute
    this.monitoringPeriod = options.monitoringPeriod || 10000; // 10 seconds
    this.correlationId = options.correlationId;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitBreakerState.OPEN) {
      if (Date.now() - this.lastFailureTime < this.recoveryTimeout) {
        const error = new Error('Circuit breaker is OPEN');
        telemetryService.track('circuit_breaker.request_blocked', {
          state: this.state,
          failureCount: this.failureCount,
          correlationId: this.correlationId,
        }, this.correlationId);
        throw error;
      } else {
        this.state = CircuitBreakerState.HALF_OPEN;
        this.successCount = 0;
        telemetryService.track('circuit_breaker.state_changed', {
          from: CircuitBreakerState.OPEN,
          to: CircuitBreakerState.HALF_OPEN,
          correlationId: this.correlationId,
        }, this.correlationId);
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= 3) { // Require 3 successes to close
        this.state = CircuitBreakerState.CLOSED;
        telemetryService.track('circuit_breaker.state_changed', {
          from: CircuitBreakerState.HALF_OPEN,
          to: CircuitBreakerState.CLOSED,
          successCount: this.successCount,
          correlationId: this.correlationId,
        }, this.correlationId);
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.OPEN;
      telemetryService.track('circuit_breaker.state_changed', {
        from: CircuitBreakerState.HALF_OPEN,
        to: CircuitBreakerState.OPEN,
        failureCount: this.failureCount,
        correlationId: this.correlationId,
      }, this.correlationId);
    } else if (this.failureCount >= this.failureThreshold) {
      this.state = CircuitBreakerState.OPEN;
      telemetryService.track('circuit_breaker.state_changed', {
        from: CircuitBreakerState.CLOSED,
        to: CircuitBreakerState.OPEN,
        failureCount: this.failureCount,
        correlationId: this.correlationId,
      }, this.correlationId);
    }
  }

  getState(): CircuitBreakerState {
    return this.state;
  }

  getMetrics() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
    };
  }

  reset(): void {
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.lastFailureTime = 0;
    
    telemetryService.track('circuit_breaker.reset', {
      correlationId: this.correlationId,
    }, this.correlationId);
  }
}

export class NetworkResilience {
  private circuitBreaker: CircuitBreaker;
  private isOnline = navigator.onLine;
  private onlineListeners: Array<(online: boolean) => void> = [];

  constructor(circuitBreakerOptions?: CircuitBreakerOptions) {
    this.circuitBreaker = new CircuitBreaker(circuitBreakerOptions);
    this.setupOnlineDetection();
  }

  private setupOnlineDetection(): void {
    const handleOnline = () => {
      this.isOnline = true;
      telemetryService.track('network.online_detected', {});
      this.notifyOnlineListeners(true);
    };

    const handleOffline = () => {
      this.isOnline = false;
      telemetryService.track('network.offline_detected', {});
      this.notifyOnlineListeners(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
  }

  private notifyOnlineListeners(online: boolean): void {
    this.onlineListeners.forEach(listener => {
      try {
        listener(online);
      } catch (error) {
        console.warn('Error in online status listener:', error);
      }
    });
  }

  onOnlineStatusChange(listener: (online: boolean) => void): () => void {
    this.onlineListeners.push(listener);
    return () => {
      const index = this.onlineListeners.indexOf(listener);
      if (index > -1) {
        this.onlineListeners.splice(index, 1);
      }
    };
  }

  async fetchWithResilience(
    request: NetworkRequest,
    retryOptions: RetryOptions = {}
  ): Promise<Response> {
    const {
      maxRetries = 3,
      baseDelay = 1000,
      maxDelay = 30000,
      backoffFactor = 2,
      jitterMax = 1000,
      retryCondition = this.defaultRetryCondition,
      onRetry,
      correlationId,
    } = retryOptions;

    if (!this.isOnline) {
      const error = new Error('Network is offline');
      telemetryService.track('network.request_blocked_offline', {
        url: request.url,
        correlationId,
      }, correlationId);
      throw error;
    }

    return this.circuitBreaker.execute(async () => {
      return this.retryWithBackoff(
        () => this.makeRequest(request),
        {
          maxRetries,
          baseDelay,
          maxDelay,
          backoffFactor,
          jitterMax,
          retryCondition,
          onRetry,
          correlationId,
        }
      );
    });
  }

  private async makeRequest(request: NetworkRequest): Promise<Response> {
    const { url, options = {}, timeout = 30000 } = request;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  private async retryWithBackoff<T>(
    fn: () => Promise<T>,
    options: RetryOptions
  ): Promise<T> {
    const {
      maxRetries = 3,
      baseDelay = 1000,
      maxDelay = 30000,
      backoffFactor = 2,
      jitterMax = 1000,
      retryCondition = this.defaultRetryCondition,
      onRetry,
      correlationId,
    } = options;

    let lastError: Error;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await fn();
        
        if (attempt > 0) {
          telemetryService.track('network.retry_succeeded', {
            attempt,
            correlationId,
          }, correlationId);
        }
        
        return result;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        if (attempt === maxRetries || !retryCondition(lastError)) {
          telemetryService.track('network.retry_exhausted', {
            attempt,
            maxRetries,
            error: lastError.message,
            correlationId,
          }, correlationId);
          throw lastError;
        }

        // Calculate delay with exponential backoff and jitter
        const exponentialDelay = Math.min(
          baseDelay * Math.pow(backoffFactor, attempt),
          maxDelay
        );
        const jitter = Math.random() * jitterMax;
        const delay = exponentialDelay + jitter;

        telemetryService.track('network.retry_scheduled', {
          attempt: attempt + 1,
          delay,
          exponentialDelay,
          jitter,
          error: lastError.message,
          correlationId,
        }, correlationId);

        if (onRetry) {
          try {
            onRetry(attempt + 1, lastError);
          } catch (retryCallbackError) {
            console.warn('Error in retry callback:', retryCallbackError);
          }
        }

        await this.delay(delay);
      }
    }

    throw lastError!;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private defaultRetryCondition(error: Error): boolean {
    // Retry on network errors, timeouts, and 5xx server errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return true; // Network error
    }
    
    if (error.name === 'AbortError') {
      return true; // Timeout
    }

    if (error.message.includes('HTTP 5')) {
      return true; // 5xx server error
    }

    if (error.message.includes('HTTP 429')) {
      return true; // Rate limited
    }

    return false;
  }

  // Health check functionality
  async healthCheck(url: string, timeout = 5000): Promise<boolean> {
    try {
      const response = await this.makeRequest({
        url,
        options: { method: 'HEAD' },
        timeout,
      });
      
      const isHealthy = response.ok;
      
      telemetryService.track('network.health_check', {
        url,
        healthy: isHealthy,
        status: response.status,
      });
      
      return isHealthy;
    } catch (error) {
      telemetryService.track('network.health_check', {
        url,
        healthy: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      
      return false;
    }
  }

  // Get network status and metrics
  getNetworkStatus() {
    return {
      isOnline: this.isOnline,
      circuitBreaker: this.circuitBreaker.getMetrics(),
      connection: this.getConnectionInfo(),
    };
  }

  private getConnectionInfo() {
    // @ts-ignore - navigator.connection is experimental
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    
    if (!connection) {
      return null;
    }

    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
      saveData: connection.saveData,
    };
  }

  // Reset circuit breaker
  resetCircuitBreaker(): void {
    this.circuitBreaker.reset();
  }

  // Cleanup
  destroy(): void {
    window.removeEventListener('online', () => {});
    window.removeEventListener('offline', () => {});
    this.onlineListeners.length = 0;
  }
}

// Global instance for convenience
export const networkResilience = new NetworkResilience();

// Utility functions
export async function resilientFetch(
  url: string,
  options?: RequestInit,
  retryOptions?: RetryOptions
): Promise<Response> {
  return networkResilience.fetchWithResilience(
    { url, options },
    retryOptions
  );
}

export function createResilientFetcher(
  baseOptions: RetryOptions = {}
) {
  return (url: string, options?: RequestInit, overrideOptions?: RetryOptions) =>
    resilientFetch(url, options, { ...baseOptions, ...overrideOptions });
}

export default NetworkResilience;
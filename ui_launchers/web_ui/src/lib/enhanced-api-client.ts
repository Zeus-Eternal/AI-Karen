/**
 * Enhanced API Client with Advanced Error Handling and Recovery
 * Provides robust error handling, retry logic, and graceful degradation
 */

import { getApiClient, ApiClient, ApiError, ApiResponse, ApiRequest } from './api-client';

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableStatuses: number[];
  retryableErrors: string[];
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  monitoringPeriod: number;
}

export interface EnhancedApiClientConfig {
  retry: RetryConfig;
  circuitBreaker: CircuitBreakerConfig;
  enableOfflineMode: boolean;
  enableRequestDeduplication: boolean;
  enableResponseCaching: boolean;
  cacheTTL: number;
}

export interface RequestMetrics {
  endpoint: string;
  method: string;
  attempts: number;
  totalTime: number;
  success: boolean;
  error?: string;
  timestamp: number;
}

export interface CircuitBreakerState {
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failures: number;
  lastFailureTime: number;
  nextAttemptTime: number;
}

/**
 * Enhanced API Client with advanced error handling and recovery mechanisms
 */
export class EnhancedApiClient {
  private baseClient: ApiClient;
  private config: EnhancedApiClientConfig;
  private circuitBreakers = new Map<string, CircuitBreakerState>();
  private requestCache = new Map<string, { data: any; timestamp: number }>();
  private pendingRequests = new Map<string, Promise<any>>();
  private metrics: RequestMetrics[] = [];
  private isOnline = true;

  constructor(config?: Partial<EnhancedApiClientConfig>) {
    this.baseClient = getApiClient();
    this.config = {
      retry: {
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 10000,
        backoffMultiplier: 2,
        retryableStatuses: [408, 429, 500, 502, 503, 504],
        retryableErrors: ['NetworkError', 'TimeoutError', 'AbortError'],
      },
      circuitBreaker: {
        failureThreshold: 5,
        resetTimeout: 60000,
        monitoringPeriod: 300000,
      },
      enableOfflineMode: true,
      enableRequestDeduplication: true,
      enableResponseCaching: false,
      cacheTTL: 300000, // 5 minutes
      ...config,
    };

    this.initializeNetworkMonitoring();
  }

  /**
   * Initialize network monitoring for offline detection
   */
  private initializeNetworkMonitoring(): void {
    if (typeof window !== 'undefined' && this.config.enableOfflineMode) {
      window.addEventListener('online', () => {
        this.isOnline = true;
        console.log('EnhancedApiClient: Network connection restored');
      });

      window.addEventListener('offline', () => {
        this.isOnline = false;
        console.log('EnhancedApiClient: Network connection lost');
      });

      this.isOnline = navigator.onLine;
    }
  }

  /**
   * Make an enhanced API request with retry logic and circuit breaker
   */
  public async request<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    const requestKey = this.getRequestKey(request);
    const startTime = Date.now();

    // Check if we're offline and this isn't a critical request
    if (!this.isOnline && !this.isCriticalRequest(request)) {
      throw this.createEnhancedError(
        'Network unavailable - operating in offline mode',
        0,
        'Offline',
        request.endpoint,
        0,
        true,
        false,
        false
      );
    }

    // Check circuit breaker
    if (this.isCircuitBreakerOpen(requestKey)) {
      throw this.createEnhancedError(
        'Circuit breaker is open - service temporarily unavailable',
        503,
        'Service Unavailable',
        request.endpoint,
        0,
        false,
        false,
        false
      );
    }

    // Check cache if enabled
    if (this.config.enableResponseCaching && request.method === 'GET') {
      const cached = this.getCachedResponse<T>(requestKey);
      if (cached) {
        return cached;
      }
    }

    // Check for duplicate requests
    if (this.config.enableRequestDeduplication) {
      const pending = this.pendingRequests.get(requestKey);
      if (pending) {
        return pending;
      }
    }

    // Create the request promise
    const requestPromise = this.executeWithRetry<T>(request, requestKey, startTime);

    // Store pending request for deduplication
    if (this.config.enableRequestDeduplication) {
      this.pendingRequests.set(requestKey, requestPromise);
    }

    try {
      const result = await requestPromise;
      
      // Cache successful GET responses
      if (this.config.enableResponseCaching && request.method === 'GET' && result.status < 400) {
        this.cacheResponse(requestKey, result);
      }

      // Record success metrics
      this.recordMetrics({
        endpoint: request.endpoint,
        method: request.method || 'GET',
        attempts: 1,
        totalTime: Date.now() - startTime,
        success: true,
        timestamp: startTime,
      });

      // Reset circuit breaker on success
      this.recordCircuitBreakerSuccess(requestKey);

      return result;
    } catch (error) {
      // Record failure metrics
      this.recordMetrics({
        endpoint: request.endpoint,
        method: request.method || 'GET',
        attempts: this.config.retry.maxRetries + 1,
        totalTime: Date.now() - startTime,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: startTime,
      });

      // Record circuit breaker failure
      this.recordCircuitBreakerFailure(requestKey);

      throw error;
    } finally {
      // Clean up pending request
      if (this.config.enableRequestDeduplication) {
        this.pendingRequests.delete(requestKey);
      }
    }
  }

  /**
   * Execute request with retry logic
   */
  private async executeWithRetry<T>(
    request: ApiRequest,
    requestKey: string,
    startTime: number
  ): Promise<ApiResponse<T>> {
    let lastError: Error | null = null;
    let attempt = 0;

    while (attempt <= this.config.retry.maxRetries) {
      try {
        const result = await this.baseClient.request<T>(request);
        return result;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        attempt++;

        // Check if we should retry
        if (attempt > this.config.retry.maxRetries || !this.shouldRetry(error, attempt)) {
          break;
        }

        // Calculate delay with exponential backoff and jitter
        const delay = this.calculateRetryDelay(attempt);
        console.log(`EnhancedApiClient: Retrying request ${requestKey} in ${delay}ms (attempt ${attempt}/${this.config.retry.maxRetries})`);
        
        await this.sleep(delay);
      }
    }

    // All retries exhausted, throw the last error
    throw this.enhanceError(lastError!, request.endpoint, Date.now() - startTime);
  }

  /**
   * Determine if an error should trigger a retry
   */
  private shouldRetry(error: any, attempt: number): boolean {
    // Don't retry if we've exceeded max attempts
    if (attempt > this.config.retry.maxRetries) {
      return false;
    }

    // Check if it's an ApiError with retryable status
    if (error && typeof error.status === 'number') {
      return this.config.retry.retryableStatuses.includes(error.status);
    }

    // Check if it's a retryable error type
    if (error && error.name) {
      return this.config.retry.retryableErrors.includes(error.name);
    }

    // Check error message for network-related issues
    if (error && error.message) {
      const message = error.message.toLowerCase();
      return (
        message.includes('network') ||
        message.includes('timeout') ||
        message.includes('connection') ||
        message.includes('fetch')
      );
    }

    return false;
  }

  /**
   * Calculate retry delay with exponential backoff and jitter
   */
  private calculateRetryDelay(attempt: number): number {
    const exponentialDelay = this.config.retry.baseDelay * Math.pow(this.config.retry.backoffMultiplier, attempt - 1);
    const jitter = Math.random() * 0.1 * exponentialDelay; // 10% jitter
    const delay = Math.min(exponentialDelay + jitter, this.config.retry.maxDelay);
    return Math.floor(delay);
  }

  /**
   * Circuit breaker management
   */
  private isCircuitBreakerOpen(requestKey: string): boolean {
    const breaker = this.circuitBreakers.get(requestKey);
    if (!breaker) return false;

    const now = Date.now();

    switch (breaker.state) {
      case 'OPEN':
        if (now >= breaker.nextAttemptTime) {
          breaker.state = 'HALF_OPEN';
          return false;
        }
        return true;
      case 'HALF_OPEN':
        return false;
      case 'CLOSED':
      default:
        return false;
    }
  }

  private recordCircuitBreakerFailure(requestKey: string): void {
    const now = Date.now();
    let breaker = this.circuitBreakers.get(requestKey);

    if (!breaker) {
      breaker = {
        state: 'CLOSED',
        failures: 0,
        lastFailureTime: now,
        nextAttemptTime: 0,
      };
      this.circuitBreakers.set(requestKey, breaker);
    }

    breaker.failures++;
    breaker.lastFailureTime = now;

    if (breaker.failures >= this.config.circuitBreaker.failureThreshold) {
      breaker.state = 'OPEN';
      breaker.nextAttemptTime = now + this.config.circuitBreaker.resetTimeout;
      console.warn(`EnhancedApiClient: Circuit breaker opened for ${requestKey}`);
    }
  }

  private recordCircuitBreakerSuccess(requestKey: string): void {
    const breaker = this.circuitBreakers.get(requestKey);
    if (breaker) {
      breaker.failures = 0;
      breaker.state = 'CLOSED';
    }
  }

  /**
   * Response caching
   */
  private getCachedResponse<T>(requestKey: string): ApiResponse<T> | null {
    const cached = this.requestCache.get(requestKey);
    if (cached && Date.now() - cached.timestamp < this.config.cacheTTL) {
      return cached.data;
    }
    return null;
  }

  private cacheResponse<T>(requestKey: string, response: ApiResponse<T>): void {
    this.requestCache.set(requestKey, {
      data: response,
      timestamp: Date.now(),
    });
  }

  /**
   * Utility methods
   */
  private getRequestKey(request: ApiRequest): string {
    const method = request.method || 'GET';
    const body = request.body ? JSON.stringify(request.body) : '';
    return `${method}:${request.endpoint}:${body}`;
  }

  private isCriticalRequest(request: ApiRequest): boolean {
    // Define critical endpoints that should work even offline
    const criticalEndpoints = ['/api/auth/refresh', '/health'];
    return criticalEndpoints.some(endpoint => request.endpoint.includes(endpoint));
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private createEnhancedError(
    message: string,
    status?: number,
    statusText?: string,
    endpoint?: string,
    responseTime?: number,
    isNetworkError: boolean = false,
    isCorsError: boolean = false,
    isTimeoutError: boolean = false
  ): ApiError {
    const error = new Error(message) as ApiError;
    error.name = 'EnhancedApiError';
    error.status = status;
    error.statusText = statusText;
    error.endpoint = endpoint;
    error.responseTime = responseTime;
    error.isNetworkError = isNetworkError;
    error.isCorsError = isCorsError;
    error.isTimeoutError = isTimeoutError;
    return error;
  }

  private enhanceError(error: Error, endpoint?: string, responseTime?: number): ApiError {
    if (error.name === 'ApiError') {
      return error as ApiError;
    }

    return this.createEnhancedError(
      error.message,
      undefined,
      undefined,
      endpoint,
      responseTime,
      error.name === 'NetworkError',
      error.message.includes('CORS'),
      error.name === 'TimeoutError'
    );
  }

  private recordMetrics(metrics: RequestMetrics): void {
    this.metrics.push(metrics);
    
    // Keep only recent metrics (last 1000 requests)
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }
  }

  /**
   * Public API methods
   */
  public async get<T = any>(endpoint: string, options?: Omit<ApiRequest, 'endpoint' | 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>({ endpoint, method: 'GET', ...options });
  }

  public async post<T = any>(endpoint: string, body?: any, options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>({ endpoint, method: 'POST', body, ...options });
  }

  public async put<T = any>(endpoint: string, body?: any, options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>({ endpoint, method: 'PUT', body, ...options });
  }

  public async delete<T = any>(endpoint: string, options?: Omit<ApiRequest, 'endpoint' | 'method'>): Promise<ApiResponse<T>> {
    return this.request<T>({ endpoint, method: 'DELETE', ...options });
  }

  public async patch<T = any>(endpoint: string, body?: any, options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>): Promise<ApiResponse<T>> {
    return this.request<T>({ endpoint, method: 'PATCH', body, ...options });
  }

  /**
   * Health and monitoring methods
   */
  public getMetrics(): RequestMetrics[] {
    return [...this.metrics];
  }

  public getCircuitBreakerStates(): Map<string, CircuitBreakerState> {
    return new Map(this.circuitBreakers);
  }

  public clearCache(): void {
    this.requestCache.clear();
    this.pendingRequests.clear();
  }

  public clearMetrics(): void {
    this.metrics = [];
  }

  public resetCircuitBreakers(): void {
    this.circuitBreakers.clear();
  }

  public isOnlineMode(): boolean {
    return this.isOnline;
  }

  public getConfig(): EnhancedApiClientConfig {
    return { ...this.config };
  }

  public updateConfig(config: Partial<EnhancedApiClientConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// Singleton instance
let enhancedApiClient: EnhancedApiClient | null = null;

/**
 * Get the global enhanced API client instance
 */
export function getEnhancedApiClient(): EnhancedApiClient {
  if (!enhancedApiClient) {
    enhancedApiClient = new EnhancedApiClient();
  }
  return enhancedApiClient;
}

/**
 * Initialize enhanced API client with custom configuration
 */
export function initializeEnhancedApiClient(config?: Partial<EnhancedApiClientConfig>): EnhancedApiClient {
  enhancedApiClient = new EnhancedApiClient(config);
  return enhancedApiClient;
}

export type {
  RetryConfig,
  CircuitBreakerConfig,
  EnhancedApiClientConfig,
  RequestMetrics,
  CircuitBreakerState,
};
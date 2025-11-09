/**
 * Connection Manager for Extension Authentication
 * 
 * Handles HTTP connections with retry logic, timeout management,
 * and comprehensive error handling for extension API calls.
 */

import { logger } from '@/lib/logger';

// Error categories for connection issues
export enum ErrorCategory {
  NETWORK_ERROR = 'network_error',
  TIMEOUT_ERROR = 'timeout_error',
  HTTP_ERROR = 'http_error',
  CONFIGURATION_ERROR = 'configuration_error',
  CIRCUIT_BREAKER_ERROR = 'circuit_breaker_error',
  UNKNOWN_ERROR = 'unknown_error',
}

// Connection error class
export class ConnectionError extends Error {
  public category: ErrorCategory;
  public retryable: boolean;
  public statusCode?: number;
  public originalError?: any;
  public retryCount?: number;

  constructor(
    message: string,
    category: ErrorCategory,
    retryable: boolean = false,
    statusCode?: number,
    originalError?: any,
    retryCount?: number
  ) {
    super(message);
    this.name = 'ConnectionError';
    this.category = category;
    this.retryable = retryable;
    this.statusCode = statusCode;
    this.originalError = originalError;
    this.retryCount = retryCount;
  }
}

// Request configuration interface
export interface RequestConfig {
  timeout?: number;
  retryAttempts?: number;
  exponentialBackoff?: boolean;
  circuitBreakerEnabled?: boolean;
}

// Connection options interface
export interface ConnectionOptions extends RequestConfig {
  baseUrl?: string;
  defaultHeaders?: Record<string, string>;
}

// Response interface
export interface ConnectionResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  duration?: number;
  retryCount?: number;
}

// Request result interface (alias for compatibility)
export interface RequestResult<T = any> extends ConnectionResponse<T> {}

// Connection status interface
export interface ConnectionStatus {
  healthy: boolean;
  latency?: number;
  error?: string;
  lastCheck?: Date;
  circuitBreakerState?: CircuitBreakerState;
}

// Circuit breaker state
export enum CircuitBreakerState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

// Type aliases for compatibility
export type ConnectionOptionsType = ConnectionOptions;
export type RequestResultType<T = any> = RequestResult<T>;
export type ConnectionStatusType = ConnectionStatus;
export type ConnectionErrorType = ConnectionError;

/**
 * Connection Manager for handling HTTP requests with retry logic
 */
export class ConnectionManager {
  private readonly defaultTimeout = 30000; // 30 seconds
  private readonly maxRetries = 3;
  private readonly baseRetryDelay = 1000; // 1 second

  /**
   * Make an HTTP request with retry logic and error handling
   */
  async makeRequest<T = any>(
    url: string,
    options: RequestInit = {},
    config: RequestConfig = {}
  ): Promise<ConnectionResponse<T>> {
    const {
      timeout = this.defaultTimeout,
      retryAttempts = this.maxRetries,
      exponentialBackoff = true,
    } = config;

    const startTime = Date.now();
    let lastError: ConnectionError | null = null;

    for (let attempt = 1; attempt <= retryAttempts + 1; attempt++) {
      try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        // Make the request
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Convert response headers to record
        const headers: Record<string, string> = {};
        response.headers.forEach((value, key) => {
          headers[key] = value;
        });

        // Parse response data
        let data: T;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
          data = await response.json();
        } else {
          data = (await response.text()) as unknown as T;
        }

        // Check if response is successful
        if (!response.ok) {
          const isRetryable = this.isRetryableStatus(response.status);
          throw new ConnectionError(
            `HTTP ${response.status}: ${response.statusText}`,
            ErrorCategory.HTTP_ERROR,
            isRetryable,
            response.status,
            { data, headers }
          );
        }

        const duration = Date.now() - startTime;
        logger.debug(`Request successful: ${url}`, {
          status: response.status,
          duration,
          attempt,
        });

        return {
          data,
          status: response.status,
          statusText: response.statusText,
          headers,
          duration,
          retryCount: attempt - 1,
        };
      } catch (error) {
        lastError = this.handleRequestError(error, url, attempt);

        // Don't retry non-retryable errors
        if (!lastError.retryable || attempt > retryAttempts) {
          break;
        }

        // Calculate delay for next attempt
        const delay = exponentialBackoff
          ? this.baseRetryDelay * Math.pow(2, attempt - 1)
          : this.baseRetryDelay;

        logger.warn(
          `Request failed for ${url} (attempt ${attempt}):`,
          lastError.message,
          `Retrying in ${delay}ms...`
        );

        await this.delay(delay);
      }
    }

    // All retries exhausted
    const duration = Date.now() - startTime;
    logger.error(
      `Request failed for ${url} after ${retryAttempts + 1} attempts:`,
      lastError?.message || 'Unknown error'
    );

    throw lastError || new ConnectionError(
      'Request failed for unknown reason',
      ErrorCategory.UNKNOWN_ERROR,
      false
    );
  }

  /**
   * Handle request errors and convert to ConnectionError
   */
  private handleRequestError(
    error: any,
    url: string,
    attempt: number
  ): ConnectionError {
    if (error instanceof ConnectionError) {
      return error;
    }

    // Handle abort/timeout errors
    if (error.name === 'AbortError') {
      return new ConnectionError(
        'Request timeout',
        ErrorCategory.TIMEOUT_ERROR,
        true,
        408,
        error
      );
    }

    // Handle network errors
    if (error instanceof TypeError) {
      return new ConnectionError(
        'Network error: Unable to connect to service',
        ErrorCategory.NETWORK_ERROR,
        true,
        0,
        error
      );
    }

    // Handle fetch errors
    if (error.message && error.message.includes('fetch')) {
      return new ConnectionError(
        'Network error: Fetch failed',
        ErrorCategory.NETWORK_ERROR,
        true,
        0,
        error
      );
    }

    // Generic error
    return new ConnectionError(
      error.message || 'Unknown connection error',
      ErrorCategory.UNKNOWN_ERROR,
      true,
      0,
      error
    );
  }

  /**
   * Check if HTTP status code is retryable
   */
  private isRetryableStatus(status: number): boolean {
    return [408, 429, 500, 502, 503, 504].includes(status);
  }

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get connection health status
   */
  async getHealthStatus(baseUrl: string): Promise<ConnectionStatus> {
    const startTime = Date.now();
    
    try {
      await this.makeRequest(`${baseUrl}/health`, {
        method: 'GET',
      }, {
        timeout: 5000,
        retryAttempts: 1,
      });

      return {
        healthy: true,
        latency: Date.now() - startTime,
        lastCheck: new Date(),
        circuitBreakerState: CircuitBreakerState.CLOSED,
      };
    } catch (error) {
      return {
        healthy: false,
        latency: Date.now() - startTime,
        error: error instanceof ConnectionError ? error.message : 'Unknown error',
        lastCheck: new Date(),
        circuitBreakerState: CircuitBreakerState.OPEN,
      };
    }
  }

  /**
   * Health check method (alias for compatibility)
   */
  async healthCheck(): Promise<ConnectionStatus> {
    return this.getHealthStatus(window.location.origin);
  }

  /**
   * Get connection status (alias for compatibility)
   */
  async getConnectionStatus(): Promise<ConnectionStatus> {
    return this.getHealthStatus(window.location.origin);
  }
}

// Global instance
let connectionManager: ConnectionManager | null = null;

/**
 * Get the global connection manager instance
 */
export function getConnectionManager(): ConnectionManager {
  if (!connectionManager) {
    connectionManager = new ConnectionManager();
  }
  return connectionManager;
}

/**
 * Initialize a new connection manager instance
 */
export function initializeConnectionManager(): ConnectionManager {
  connectionManager = new ConnectionManager();
  return connectionManager;
}
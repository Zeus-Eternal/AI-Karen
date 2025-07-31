/**
 * Centralized API Client
 * Provides consistent API communication with automatic endpoint fallback and error handling
 */

import { getConfigManager } from './endpoint-config';
import { getEndpointFallbackService } from './endpoint-fallback';
import { getNetworkDetectionService } from './network-detector';
import { shouldAutoRetry, getRetryDelay, formatErrorForLogging } from './error-handler';

export interface ApiClientConfig {
  timeout: number;
  retries: number;
  retryDelay: number;
  enableFallback: boolean;
  enableNetworkDetection: boolean;
  defaultHeaders: Record<string, string>;
}

export interface ApiRequest {
  endpoint: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';
  body?: any;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
  skipFallback?: boolean;
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Headers;
  endpoint: string;
  responseTime: number;
  wasFailover: boolean;
}

export interface ApiError extends Error {
  status?: number;
  statusText?: string;
  endpoint?: string;
  responseTime?: number;
  isNetworkError: boolean;
  isCorsError: boolean;
  isTimeoutError: boolean;
  originalError?: Error;
}

/**
 * Centralized API client with automatic endpoint management
 */
export class ApiClient {
  private config: ApiClientConfig;
  private configManager = getConfigManager();
  private fallbackService = getEndpointFallbackService();
  private networkDetector = getNetworkDetectionService();

  constructor(config?: Partial<ApiClientConfig>) {
    this.config = {
      timeout: 30000,
      retries: 3,
      retryDelay: 1000,
      enableFallback: true,
      enableNetworkDetection: true,
      defaultHeaders: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
      },
      ...config,
    };

    // Initialize network detection if enabled
    if (this.config.enableNetworkDetection) {
      this.initializeNetworkDetection();
    }
  }

  /**
   * Initialize network detection and apply configuration
   */
  private async initializeNetworkDetection(): Promise<void> {
    try {
      await this.networkDetector.applyDetectedConfiguration();
    } catch (error) {
      console.warn('ApiClient: Failed to apply network detection:', error);
    }
  }

  /**
   * Make an API request with automatic fallback
   */
  public async request<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    const startTime = performance.now();

    // Prepare request function
    const makeRequest = async (baseUrl: string): Promise<ApiResponse<T>> => {
      const url = `${baseUrl}${request.endpoint}`;
      const timeout = request.timeout || this.config.timeout;
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      try {
        const response = await fetch(url, {
          method: request.method || 'GET',
          headers: {
            ...this.config.defaultHeaders,
            ...request.headers,
          },
          body: request.body ? JSON.stringify(request.body) : undefined,
          signal: controller.signal,
          credentials: 'include', // Include cookies for authentication
        });

        clearTimeout(timeoutId);
        const responseTime = performance.now() - startTime;

        // Parse response body
        let data: T;
        const contentType = response.headers.get('content-type');
        
        if (contentType?.includes('application/json')) {
          data = await response.json();
        } else {
          data = (await response.text()) as unknown as T;
        }

        if (!response.ok) {
          throw this.createApiError(
            `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            response.statusText,
            url,
            responseTime,
            false,
            false,
            false
          );
        }

        return {
          data,
          status: response.status,
          statusText: response.statusText,
          headers: response.headers,
          endpoint: url,
          responseTime,
          wasFailover: false,
        };

      } catch (error) {
        clearTimeout(timeoutId);
        const responseTime = performance.now() - startTime;

        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            throw this.createApiError(
              'Request timeout',
              0,
              'Timeout',
              url,
              responseTime,
              false,
              false,
              true,
              error
            );
          } else if (error.message.includes('CORS')) {
            throw this.createApiError(
              'CORS error - cross-origin requests blocked',
              0,
              'CORS Error',
              url,
              responseTime,
              false,
              true,
              false,
              error
            );
          } else if (error.message.includes('fetch')) {
            throw this.createApiError(
              'Network error - unable to connect',
              0,
              'Network Error',
              url,
              responseTime,
              true,
              false,
              false,
              error
            );
          }
        }

        // Re-throw ApiError instances
        if (this.isApiError(error)) {
          throw error;
        }

        // Wrap unknown errors
        throw this.createApiError(
          error instanceof Error ? error.message : 'Unknown error',
          0,
          'Unknown Error',
          url,
          responseTime,
          true,
          false,
          false,
          error instanceof Error ? error : undefined
        );
      }
    };

    // Use fallback service if enabled and not explicitly skipped
    if (this.config.enableFallback && !request.skipFallback) {
      try {
        const result = await this.fallbackService.requestWithFallback(
          makeRequest,
          this.getRequestType(request.endpoint)
        );

        return {
          ...result.data,
          wasFailover: result.fallbackResult.wasFailover,
        };
      } catch (error) {
        throw error;
      }
    } else {
      // Direct request without fallback
      const baseUrl = this.configManager.getBackendUrl();
      return makeRequest(baseUrl);
    }
  }

  /**
   * GET request helper
   */
  public async get<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.request<T>({
      endpoint,
      method: 'GET',
      ...options,
    });
  }

  /**
   * POST request helper
   */
  public async post<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.request<T>({
      endpoint,
      method: 'POST',
      body,
      ...options,
    });
  }

  /**
   * PUT request helper
   */
  public async put<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.request<T>({
      endpoint,
      method: 'PUT',
      body,
      ...options,
    });
  }

  /**
   * DELETE request helper
   */
  public async delete<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.request<T>({
      endpoint,
      method: 'DELETE',
      ...options,
    });
  }

  /**
   * PATCH request helper
   */
  public async patch<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.request<T>({
      endpoint,
      method: 'PATCH',
      body,
      ...options,
    });
  }

  /**
   * Upload file helper
   */
  public async uploadFile<T = any>(
    endpoint: string,
    file: File,
    fieldName: string = 'file',
    additionalFields?: Record<string, string>,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body' | 'headers'>
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append(fieldName, file);
    
    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    // Remove Content-Type header to let browser set it with boundary
    const headers = { ...options?.headers };
    delete headers['Content-Type'];

    return this.request<T>({
      endpoint,
      method: 'POST',
      body: formData,
      headers,
      ...options,
    });
  }

  /**
   * Health check helper
   */
  public async healthCheck(): Promise<ApiResponse<any>> {
    return this.get('/health', { skipFallback: false });
  }

  /**
   * Get current backend URL
   */
  public getBackendUrl(): string {
    return this.configManager.getBackendUrl();
  }

  /**
   * Get endpoint URLs for different services
   */
  public getEndpoints() {
    return {
      auth: this.configManager.getAuthEndpoint(),
      chat: this.configManager.getChatEndpoint(),
      memory: this.configManager.getMemoryEndpoint(),
      plugins: this.configManager.getPluginsEndpoint(),
      health: this.configManager.getHealthEndpoint(),
    };
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<ApiClientConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration
   */
  public getConfig(): ApiClientConfig {
    return { ...this.config };
  }

  /**
   * Determine request type based on endpoint
   */
  private getRequestType(endpoint: string): 'api' | 'auth' | 'chat' | 'health' {
    if (endpoint.startsWith('/api/auth')) return 'auth';
    if (endpoint.startsWith('/api/chat')) return 'chat';
    if (endpoint.startsWith('/health')) return 'health';
    return 'api';
  }

  /**
   * Create standardized API error
   */
  private createApiError(
    message: string,
    status?: number,
    statusText?: string,
    endpoint?: string,
    responseTime?: number,
    isNetworkError: boolean = false,
    isCorsError: boolean = false,
    isTimeoutError: boolean = false,
    originalError?: Error
  ): ApiError {
    const error = new Error(message) as ApiError;
    error.name = 'ApiError';
    error.status = status;
    error.statusText = statusText;
    error.endpoint = endpoint;
    error.responseTime = responseTime;
    error.isNetworkError = isNetworkError;
    error.isCorsError = isCorsError;
    error.isTimeoutError = isTimeoutError;
    error.originalError = originalError;
    return error;
  }

  /**
   * Check if error is an ApiError
   */
  private isApiError(error: any): error is ApiError {
    return error && error.name === 'ApiError';
  }

  /**
   * Get endpoint statistics from fallback service
   */
  public getEndpointStats() {
    return this.fallbackService.getEndpointStatsArray();
  }

  /**
   * Reset endpoint statistics
   */
  public resetEndpointStats(endpoint?: string): void {
    this.fallbackService.resetEndpointStats(endpoint);
  }

  /**
   * Clear all caches
   */
  public clearCaches(): void {
    this.fallbackService.clearCache();
    this.networkDetector.clearCache();
  }
}

// Singleton instance
let apiClient: ApiClient | null = null;

/**
 * Get the global API client instance
 */
export function getApiClient(): ApiClient {
  if (!apiClient) {
    apiClient = new ApiClient();
  }
  return apiClient;
}

/**
 * Initialize API client with custom configuration
 */
export function initializeApiClient(config?: Partial<ApiClientConfig>): ApiClient {
  apiClient = new ApiClient(config);
  return apiClient;
}

// Export types
export type {
  ApiClientConfig as ApiClientConfigType,
  ApiRequest as ApiRequestType,
  ApiResponse as ApiResponseType,
  ApiError as ApiErrorType,
};
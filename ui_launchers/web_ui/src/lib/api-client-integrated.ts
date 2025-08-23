/**
 * Integrated API Client with Enhanced Session Management
 * 
 * Wraps the existing API client with the new session management system,
 * providing automatic token refresh, session recovery, and intelligent error handling.
 * 
 * Requirements: 5.2, 5.3, 1.1, 1.2
 */

import { getApiClient, type ApiClient, type ApiRequest, type ApiResponse, type ApiError } from './api-client';
import { getEnhancedApiClient, type EnhancedApiClient } from './auth/api-client-enhanced';
import { ensureToken, getAuthHeader, isAuthenticated } from './auth/session';

export interface IntegratedApiClientOptions {
  useEnhancedAuth?: boolean;
  autoRetryOn401?: boolean;
  includeCredentials?: boolean;
}

/**
 * Integrated API Client that combines the existing API client with enhanced session management
 */
export class IntegratedApiClient {
  private apiClient: ApiClient;
  private enhancedApiClient: EnhancedApiClient;
  private options: IntegratedApiClientOptions;

  constructor(options: IntegratedApiClientOptions = {}) {
    this.apiClient = getApiClient();
    this.enhancedApiClient = getEnhancedApiClient();
    this.options = {
      useEnhancedAuth: true,
      autoRetryOn401: true,
      includeCredentials: true,
      ...options,
    };
  }

  /**
   * Make an authenticated request using the enhanced API client
   */
  private async makeAuthenticatedRequest<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    if (this.options.useEnhancedAuth && this.isProtectedEndpoint(request.endpoint)) {
      // Use enhanced API client for protected endpoints
      return this.enhancedApiClient.request(request);
    } else {
      // Use regular API client for public endpoints or when enhanced auth is disabled
      return this.makeRegularRequest<T>(request);
    }
  }

  /**
   * Make a request using the regular API client with manual auth header injection
   */
  private async makeRegularRequest<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    // Add auth headers if user is authenticated
    if (isAuthenticated()) {
      try {
        await ensureToken();
        const authHeaders = getAuthHeader();
        request.headers = {
          ...request.headers,
          ...authHeaders,
        };
      } catch (error) {
        console.warn('Failed to ensure token for regular request:', error);
      }
    }

    return this.apiClient.request<T>(request);
  }

  /**
   * Determine if an endpoint requires authentication
   */
  private isProtectedEndpoint(endpoint: string): boolean {
    // Public endpoints that don't require authentication
    const publicEndpoints = [
      '/api/auth/login',
      '/api/auth/register',
      '/api/auth/forgot-password',
      '/api/auth/reset-password',
      '/health',
      '/api/health',
      '/api/public/',
    ];

    return !publicEndpoints.some(publicEndpoint => endpoint.startsWith(publicEndpoint));
  }

  /**
   * GET request
   */
  async get<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'GET',
      ...options,
    });
  }

  /**
   * POST request
   */
  async post<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'POST',
      body,
      ...options,
    });
  }

  /**
   * PUT request
   */
  async put<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'PUT',
      body,
      ...options,
    });
  }

  /**
   * DELETE request
   */
  async delete<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'DELETE',
      ...options,
    });
  }

  /**
   * PATCH request
   */
  async patch<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'PATCH',
      body,
      ...options,
    });
  }

  /**
   * Upload file
   */
  async uploadFile<T = any>(
    endpoint: string,
    file: File,
    fieldName: string = 'file',
    additionalFields?: Record<string, string>,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body' | 'headers'>
  ): Promise<ApiResponse<T>> {
    if (this.options.useEnhancedAuth && this.isProtectedEndpoint(endpoint)) {
      return this.enhancedApiClient.uploadFile<T>(endpoint, file, fieldName, additionalFields, options);
    } else {
      return this.apiClient.uploadFile<T>(endpoint, file, fieldName, additionalFields, options);
    }
  }

  /**
   * Make a public request (no authentication)
   */
  async requestPublic<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    return this.apiClient.request<T>(request);
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.apiClient.healthCheck();
  }

  /**
   * Get backend URL
   */
  getBackendUrl(): string {
    return this.apiClient.getBackendUrl();
  }

  /**
   * Get endpoints
   */
  getEndpoints() {
    return this.apiClient.getEndpoints();
  }

  /**
   * Get endpoint statistics
   */
  getEndpointStats() {
    return this.apiClient.getEndpointStats();
  }

  /**
   * Reset endpoint statistics
   */
  resetEndpointStats(endpoint?: string): void {
    this.apiClient.resetEndpointStats(endpoint);
  }

  /**
   * Clear caches
   */
  clearCaches(): void {
    this.apiClient.clearCaches();
  }

  /**
   * Get the underlying API clients
   */
  getClients() {
    return {
      regular: this.apiClient,
      enhanced: this.enhancedApiClient,
    };
  }

  /**
   * Update options
   */
  updateOptions(options: Partial<IntegratedApiClientOptions>): void {
    this.options = { ...this.options, ...options };
  }

  /**
   * Get current options
   */
  getOptions(): IntegratedApiClientOptions {
    return { ...this.options };
  }
}

// Singleton instance
let integratedApiClient: IntegratedApiClient | null = null;

/**
 * Get the integrated API client instance
 */
export function getIntegratedApiClient(options?: IntegratedApiClientOptions): IntegratedApiClient {
  if (!integratedApiClient) {
    integratedApiClient = new IntegratedApiClient(options);
  } else if (options) {
    integratedApiClient.updateOptions(options);
  }
  return integratedApiClient;
}

/**
 * Initialize integrated API client with custom options
 */
export function initializeIntegratedApiClient(options?: IntegratedApiClientOptions): IntegratedApiClient {
  integratedApiClient = new IntegratedApiClient(options);
  return integratedApiClient;
}

/**
 * Hook for using the integrated API client in React components
 */
export function useIntegratedApiClient(options?: IntegratedApiClientOptions) {
  // Note: This should be used in a React component context
  // React.useMemo will be available when imported in a React component
  return getIntegratedApiClient(options);
}

// Re-export types for convenience
export type {
  ApiRequest,
  ApiResponse,
  ApiError,
  IntegratedApiClientOptions as IntegratedApiClientOptionsType,
};

// Default export
export default IntegratedApiClient;
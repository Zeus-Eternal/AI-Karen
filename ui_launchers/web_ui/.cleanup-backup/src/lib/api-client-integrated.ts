/**
 * Integrated API Client with Enhanced Session Management
 * 
 * Wraps the existing API client with the new session management system,
 * providing automatic token refresh, session recovery, and intelligent error handling.
 * 
 * Requirements: 5.2, 5.3, 1.1, 1.2
 */

import { getApiClient, type ApiClient, type RequestConfig, type ApiResponse, type ApiError } from './api-client';
import { isAuthenticated, clearSession } from './auth/session';

export interface ApiRequest extends RequestConfig {
  endpoint: string;
}

export interface IntegratedApiClientOptions {
  autoRetryOn401?: boolean;
  includeCredentials?: boolean;
}

/**
 * Integrated API Client that combines the existing API client with simplified session management
 */
export class IntegratedApiClient {
  private apiClient: ApiClient;
  private options: IntegratedApiClientOptions;

  constructor(options: IntegratedApiClientOptions = {}) {
    this.apiClient = getApiClient();
    this.options = {
      autoRetryOn401: true,
      includeCredentials: true,
      ...options,
    };
  }

  /**
   * Make an authenticated request with simple 401 handling
   */
  private async makeAuthenticatedRequest<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    try {
      // Use regular API client with automatic cookie handling
      const { endpoint, ...config } = request;
      return await this.apiClient.request<T>(endpoint, config);
    } catch (error: any) {
      // Simple 401 error handling - clear session and redirect to login
      if (error.status === 401) {
        console.log('Integrated API Client: 401 error detected, clearing session and redirecting');
        clearSession();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
      
      // For all other errors, throw immediately (no complex retry logic)
      throw error;
    }
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
    // Create form data
    const formData = new FormData();
    formData.append(fieldName, file);
    
    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'POST',
      body: formData,
      ...options,
    });
  }

  /**
   * Make a public request (no authentication)
   */
  async requestPublic<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    const { endpoint, ...config } = request;
    return this.apiClient.request<T>(endpoint, config);
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.apiClient.get('/api/health');
  }

  /**
   * Get backend URL
   */
  getBackendUrl(): string {
    // Access the private baseURL through a simple method
    if (typeof window !== 'undefined') {
      return `${window.location.protocol}//${window.location.host}/api`;
    }
    return process.env.NEXT_PUBLIC_API_URL || '/api';
  }

  /**
   * Get the underlying API client
   */
  getClient() {
    return this.apiClient;
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
  ApiResponse,
  ApiError,
  IntegratedApiClientOptions as IntegratedApiClientOptionsType,
};

// Default export
export default IntegratedApiClient;
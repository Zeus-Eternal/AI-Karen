/**
 * Enhanced API Client with Automatic Token Refresh and Session Recovery
 * 
 * Extends the existing API client to automatically handle token refresh
 * for 401 errors, inject auth headers, and implement intelligent session recovery.
 * 
 * Requirements: 5.2, 5.3
 */

import { getApiClient, ApiClient, ApiRequest, ApiResponse } from '@/lib/api-client';
import { ensureToken, getAuthHeader, clearSession } from './session';
import { recoverFrom401Error, type SessionRecoveryResult } from './session-recovery';

export class EnhancedApiClient {
  private apiClient: ApiClient;
  private isRefreshing = false;
  private retryQueue: Array<{
    request: ApiRequest;
    resolve: (value: any) => void;
    reject: (error: any) => void;
  }> = [];

  constructor() {
    this.apiClient = getApiClient();
  }

  /**
   * Process queued requests after successful token refresh
   */
  private async processRetryQueue(): Promise<void> {
    const queue = [...this.retryQueue];
    this.retryQueue = [];

    for (const { request, resolve, reject } of queue) {
      try {
        const result = await this.makeAuthenticatedRequest(request);
        resolve(result);
      } catch (error) {
        reject(error);
      }
    }
  }

  /**
   * Make an authenticated request without retry logic
   */
  private async makeAuthenticatedRequest<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    const authHeaders = getAuthHeader();
    const enhancedRequest: ApiRequest = {
      ...request,
      headers: {
        ...request.headers,
        ...authHeaders,
      },
    };

    return await this.apiClient.request<T>(enhancedRequest);
  }

  /**
   * Make an API request with intelligent session recovery and automatic retry
   */
  private async requestWithAuth<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    // Ensure we have a valid token before making the request
    try {
      await ensureToken();
    } catch (error) {
      // If token refresh fails, clear session and let the request proceed
      // The request will likely fail with 401, which is expected
      clearSession();
    }

    try {
      // Make the initial request
      return await this.makeAuthenticatedRequest<T>(request);
    } catch (error: any) {
      // Handle 401 errors with intelligent session recovery
      if (error.status === 401) {
        return await this.handleAuthenticationError<T>(request, error);
      }
      
      // For non-401 errors, throw immediately
      throw error;
    }
  }

  /**
   * Handle 401 authentication errors with session recovery and retry logic
   */
  private async handleAuthenticationError<T = any>(
    request: ApiRequest, 
    originalError: any
  ): Promise<ApiResponse<T>> {
    // If already refreshing, queue this request
    if (this.isRefreshing) {
      return new Promise<ApiResponse<T>>((resolve, reject) => {
        this.retryQueue.push({ request, resolve, reject });
      });
    }

    this.isRefreshing = true;

    try {
      // Attempt session recovery
      const recoveryResult: SessionRecoveryResult = await recoverFrom401Error();

      if (recoveryResult.success) {
        // Recovery successful, retry the original request
        const result = await this.makeAuthenticatedRequest<T>(request);
        
        // Process any queued requests
        await this.processRetryQueue();
        
        return result;
      } else {
        // Recovery failed, process queue with errors and throw original error
        const queue = [...this.retryQueue];
        this.retryQueue = [];
        
        for (const { reject } of queue) {
          reject(originalError);
        }
        
        throw originalError;
      }
    } catch (recoveryError) {
      // Recovery attempt failed, clear session and throw original error
      clearSession();
      
      // Process queue with errors
      const queue = [...this.retryQueue];
      this.retryQueue = [];
      
      for (const { reject } of queue) {
        reject(originalError);
      }
      
      throw originalError;
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * GET request with automatic auth handling
   */
  async get<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.requestWithAuth<T>({
      endpoint,
      method: 'GET',
      ...options,
    });
  }

  /**
   * POST request with automatic auth handling
   */
  async post<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.requestWithAuth<T>({
      endpoint,
      method: 'POST',
      body,
      ...options,
    });
  }

  /**
   * PUT request with automatic auth handling
   */
  async put<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.requestWithAuth<T>({
      endpoint,
      method: 'PUT',
      body,
      ...options,
    });
  }

  /**
   * DELETE request with automatic auth handling
   */
  async delete<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.requestWithAuth<T>({
      endpoint,
      method: 'DELETE',
      ...options,
    });
  }

  /**
   * PATCH request with automatic auth handling
   */
  async patch<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.requestWithAuth<T>({
      endpoint,
      method: 'PATCH',
      body,
      ...options,
    });
  }

  /**
   * Upload file with automatic auth handling
   */
  async uploadFile<T = any>(
    endpoint: string,
    file: File,
    fieldName: string = 'file',
    additionalFields?: Record<string, string>,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body' | 'headers'>
  ): Promise<ApiResponse<T>> {
    // Ensure we have a valid token
    await ensureToken();
    
    // Get auth headers
    const authHeaders = getAuthHeader();
    
    // Use the original API client's uploadFile method with auth headers
    const formData = new FormData();
    formData.append(fieldName, file);
    
    if (additionalFields) {
      Object.entries(additionalFields).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const headers = { ...options?.headers, ...authHeaders };
    delete headers['Content-Type']; // Let browser set it with boundary

    return this.requestWithAuth<T>({
      endpoint,
      method: 'POST',
      body: formData,
      headers,
      ...options,
    });
  }

  /**
   * Make a request without auth (for public endpoints)
   */
  async requestPublic<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    return this.apiClient.request<T>(request);
  }

  /**
   * Get the underlying API client for direct access
   */
  getApiClient(): ApiClient {
    return this.apiClient;
  }
}

// Singleton instance
let enhancedApiClient: EnhancedApiClient | null = null;

/**
 * Get the enhanced API client instance
 */
export function getEnhancedApiClient(): EnhancedApiClient {
  if (!enhancedApiClient) {
    enhancedApiClient = new EnhancedApiClient();
  }
  return enhancedApiClient;
}
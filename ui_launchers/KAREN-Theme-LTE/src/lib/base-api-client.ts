import { ApiResponse, RequestOptions } from '@/lib/types';

/**
 * Base API Client for KAREN Theme Default
 * Provides a unified interface for all API communications
 */
export class BaseApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;
  private timeout: number;

  constructor(options: {
    baseUrl?: string;
    timeout?: number;
    defaultHeaders?: Record<string, string>;
  } = {}) {
    this.baseUrl = options.baseUrl || process.env.NEXT_PUBLIC_API_BASE_URL || '/api';
    this.timeout = options.timeout || 10000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.defaultHeaders,
    };
  }

  /**
   * Generic request method that handles all HTTP verbs
   */
  protected async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      params,
      timeout = this.timeout,
      signal,
    } = options;

    const url = new URL(endpoint, this.baseUrl);
    
    // Add query parameters
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    // Prepare request headers
    const requestHeaders = new Headers({
      ...this.defaultHeaders,
      ...headers,
    });

    // Prepare request body
    let requestBody: BodyInit | undefined;
    if (body) {
      if (body instanceof FormData) {
        // Let browser set Content-Type for FormData
        requestHeaders.delete('Content-Type');
        requestBody = body;
      } else if (typeof body === 'object') {
        requestBody = JSON.stringify(body);
      } else {
        requestBody = body;
      }
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    // Use provided signal if available
    const finalSignal = signal || controller.signal;

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: requestHeaders,
        body: requestBody,
        signal: finalSignal,
        credentials: 'include',
      });

      clearTimeout(timeoutId);

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await this.parseErrorBody(response);
        throw new BaseApiError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData.code,
          errorData.details
        );
      }

      // Parse successful response
      const data = await this.parseResponse(response) as T;
      
      return {
        data,
        status: response.status,
        headers: response.headers,
        ok: true,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof BaseApiError) {
        throw error;
      }
      
      // Handle network errors, timeouts, etc.
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new BaseApiError('Request timeout', 408, 'TIMEOUT');
        }
        throw new BaseApiError(error.message, 0, 'NETWORK_ERROR');
      }
      
      throw new BaseApiError('Unknown error occurred', 0, 'UNKNOWN_ERROR');
    }
  }

  /**
   * Parse response body based on Content-Type
   */
  private async parseResponse(response: Response): Promise<unknown> {
    const contentType = response.headers.get('Content-Type');
    
    if (contentType?.includes('application/json')) {
      return await response.json();
    } else if (contentType?.includes('text/')) {
      return await response.text();
    } else {
      return await response.blob();
    }
  }

  /**
   * Parse error body for detailed error information
   */
  private async parseErrorBody(response: Response): Promise<{ message?: string; code?: string; details?: unknown }> {
    try {
      const contentType = response.headers.get('Content-Type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }
      return { message: await response.text() };
    } catch {
      return { message: response.statusText };
    }
  }

  // HTTP method helpers
  async get<T>(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: BodyInit | Record<string, unknown>, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body: data });
  }


  async put<T>(endpoint: string, data?: BodyInit | Record<string, unknown>, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body: data });
  }

  async patch<T>(endpoint: string, data?: BodyInit | Record<string, unknown>, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PATCH', body: data });
  }

  async delete<T>(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * Upload file with progress tracking
   */
  async uploadFile<T>(
    endpoint: string,
    file: File,
    options: {
      onProgress?: (progress: number) => void;
      field?: string;
      metadata?: Record<string, string | number | boolean>;
    } & Omit<RequestOptions, 'method' | 'body'> = {}
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append(options.field || 'file', file);
    
    if (options.metadata) {
      Object.entries(options.metadata).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Progress tracking
      if (options.onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            options.onProgress!(progress);
          }
        });
      }

      // Load handler
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve({
              data,
              status: xhr.status,
              headers: new Headers(),
              ok: true,
            });
          } catch (error) {
            reject(new BaseApiError('Invalid response format', xhr.status, 'PARSE_ERROR'));
          }
        } else {
          reject(new BaseApiError(xhr.statusText, xhr.status, 'HTTP_ERROR'));
        }
      });

      // Error handler
      xhr.addEventListener('error', () => {
        reject(new BaseApiError('Network error', 0, 'NETWORK_ERROR'));
      });

      // Abort handler
      xhr.addEventListener('abort', () => {
        reject(new BaseApiError('Request aborted', 0, 'ABORTED'));
      });

      // Configure and send request
      xhr.timeout = options.timeout || this.timeout;
      xhr.open('POST', new URL(endpoint, this.baseUrl).toString());
      
      // Set headers
      Object.entries(this.defaultHeaders).forEach(([key, value]) => {
        if (key !== 'Content-Type') { // Let browser set for FormData
          xhr.setRequestHeader(key, value);
        }
      });
      
      Object.entries(options.headers || {}).forEach(([key, value]) => {
        xhr.setRequestHeader(key, String(value));
      });

      xhr.send(formData);
    });
  }

  /**
   * Create a new instance with different configuration
   */
  withConfig(config: {
    baseUrl?: string;
    timeout?: number;
    headers?: Record<string, string>;
  }): BaseApiClient {
    return new BaseApiClient({
      baseUrl: config.baseUrl || this.baseUrl,
      timeout: config.timeout || this.timeout,
      defaultHeaders: {
        ...this.defaultHeaders,
        ...config.headers,
      },
    });
  }
}

// Enhanced API Client with store integration
export class EnhancedApiClient {
  private static storeCallbacks: {
    setLoading?: (loading: { isLoading: boolean; message?: string }) => void;
    setGlobalLoading?: (loading: { isLoading: boolean; message?: string }) => void;
    clearLoading?: () => void;
    logout?: () => void;
    addNotification?: (notification: { title: string; message?: string; type: 'error' | 'success' | 'warning' | 'info' }) => void;
    setConnectionQuality?: (quality: { quality: 'offline' | 'excellent' | 'good' | 'fair' | 'poor'; speed?: number; latency?: number }) => void;
  } = {};

  private static queryClientCallback: () => unknown = () => null;

  private baseUrl: string;
  private defaultHeaders: Record<string, string>;
  private timeout: number;

  constructor(options: {
    baseUrl?: string;
    timeout?: number;
    defaultHeaders?: Record<string, string>;
  } = {}) {
    this.baseUrl = options.baseUrl || process.env.NEXT_PUBLIC_API_BASE_URL || '/api';
    this.timeout = options.timeout || 10000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.defaultHeaders,
    };
  }

  static setStoreCallbacks(callbacks: typeof EnhancedApiClient.storeCallbacks) {
    EnhancedApiClient.storeCallbacks = { ...EnhancedApiClient.storeCallbacks, ...callbacks };
  }

  static setQueryClientCallback(callback: () => unknown) {
    EnhancedApiClient.queryClientCallback = callback;
  }

  async request(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<unknown>> {
    // Set loading state
    if (EnhancedApiClient.storeCallbacks.setLoading) {
      EnhancedApiClient.storeCallbacks.setLoading({ isLoading: true });
    }

    try {
      const {
        method = 'GET',
        headers = {},
        body,
        params,
        signal,
      } = options;

      const url = new URL(endpoint, this.baseUrl);
      
      // Add query parameters
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            url.searchParams.append(key, String(value));
          }
        });
      }

      // Prepare request headers
      const requestHeaders = new Headers({
        ...this.defaultHeaders,
        ...headers,
      });

      // Prepare request body
      let requestBody: BodyInit | undefined;
      if (body) {
        if (body instanceof FormData) {
          // Let browser set Content-Type for FormData
          requestHeaders.delete('Content-Type');
          requestBody = body;
        } else if (typeof body === 'object') {
          requestBody = JSON.stringify(body);
        } else {
          requestBody = body;
        }
      }

      // Create abort controller for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);
      
      // Use provided signal if available
      const finalSignal = signal || controller.signal;

      const response = await fetch(url.toString(), {
        method,
        headers: requestHeaders,
        body: requestBody,
        signal: finalSignal,
        credentials: 'include',
      });

      clearTimeout(timeoutId);

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await this.parseErrorBody(response);
        throw new BaseApiError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData.code,
          errorData.details
        );
      }

      // Parse successful response
      const data = await this.parseResponse(response);
      
      // Clear loading state
      if (EnhancedApiClient.storeCallbacks.clearLoading) {
        EnhancedApiClient.storeCallbacks.clearLoading();
      }

      return {
        data,
        status: response.status,
        headers: response.headers,
        ok: true,
      };
    } catch (error) {
      // Clear loading state
      if (EnhancedApiClient.storeCallbacks.clearLoading) {
        EnhancedApiClient.storeCallbacks.clearLoading();
      }

      // Handle auth errors
      if (error instanceof BaseApiError && error.status === 401) {
        if (EnhancedApiClient.storeCallbacks.logout) {
          EnhancedApiClient.storeCallbacks.logout();
        }
      }

      // Show error notification
      if (EnhancedApiClient.storeCallbacks.addNotification) {
        EnhancedApiClient.storeCallbacks.addNotification({
          title: 'API Error',
          message: error instanceof Error ? error.message : 'Unknown error',
          type: 'error'
        });
      }

      throw error;
    }
  }

  private async parseResponse(response: Response): Promise<unknown> {
    const contentType = response.headers.get('Content-Type');
    
    if (contentType?.includes('application/json')) {
      return await response.json();
    } else if (contentType?.includes('text/')) {
      return await response.text();
    } else {
      return await response.blob();
    }
  }

  private async parseErrorBody(response: Response): Promise<{ message?: string; code?: string; details?: unknown }> {
    try {
      const contentType = response.headers.get('Content-Type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }
      return { message: await response.text() };
    } catch {
      return { message: response.statusText };
    }
  }

  // Query client integration
  getQueryClient() {
    return EnhancedApiClient.queryClientCallback();
  }

  // Post method for making POST requests
  async post(endpoint: string, data?: BodyInit | Record<string, unknown>, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<unknown>> {
    return this.request(endpoint, { ...options, method: 'POST', body: data });
  }

  // Other HTTP methods
  async get(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<unknown>> {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  async put(endpoint: string, data?: BodyInit | Record<string, unknown>, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<unknown>> {
    return this.request(endpoint, { ...options, method: 'PUT', body: data });
  }

  async patch(endpoint: string, data?: BodyInit | Record<string, unknown>, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<unknown>> {
    return this.request(endpoint, { ...options, method: 'PATCH', body: data });
  }

  async delete(endpoint: string, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<unknown>> {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Default instance
export const apiClient = new BaseApiClient();

// Error class for API errors
export class BaseApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'BaseApiError';
  }
}

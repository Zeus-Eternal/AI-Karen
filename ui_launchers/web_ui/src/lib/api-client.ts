/**
 * Enhanced API Client
 * 
 * HTTP client with error handling, retries, and request/response interceptors.
 * Based on requirements: 12.2, 12.3
 */

import { useAppStore } from '@/store/app-store';

// API Response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error' | 'warning';
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
    hasMore?: boolean;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

// Request configuration
export interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  skipAuth?: boolean;
  skipErrorHandling?: boolean;
}

// Interceptor types
export type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
export type ResponseInterceptor = (response: Response) => Response | Promise<Response>;
export type ErrorInterceptor = (error: ApiError) => ApiError | Promise<ApiError>;

// API Client class
export class ApiClient {
  private baseURL: string;
  private defaultTimeout = 30000;
  private defaultRetries = 3;
  private defaultRetryDelay = 1000;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];

  constructor(baseURL?: string) {
    this.baseURL = baseURL || this.getBaseURL();
    this.setupDefaultInterceptors();
  }

  // Get base URL from environment or current location
  private getBaseURL(): string {
    if (typeof window !== 'undefined') {
      return `${window.location.protocol}//${window.location.host}/api`;
    }
    return process.env.NEXT_PUBLIC_API_URL || '/api';
  }

  // Setup default interceptors
  private setupDefaultInterceptors(): void {
    // Request interceptor for authentication
    this.addRequestInterceptor(async (config) => {
      if (!config.skipAuth) {
        const token = this.getAuthToken();
        if (token) {
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${token}`,
          };
        }
      }

      // Add default headers
      config.headers = {
        'Content-Type': 'application/json',
        ...config.headers,
      };

      return config;
    });

    // Response interceptor for error handling
    this.addResponseInterceptor(async (response) => {
      // Handle 401 unauthorized
      if (response.status === 401) {
        const { logout, addNotification } = useAppStore.getState();
        logout();
        addNotification({
          type: 'warning',
          title: 'Session Expired',
          message: 'Please log in again to continue.',
        });
      }

      return response;
    });

    // Error interceptor for global error handling
    this.addErrorInterceptor(async (error) => {
      if (!error.code) {
        const { addNotification } = useAppStore.getState();
        
        // Handle network errors
        if (error.message.includes('fetch')) {
          addNotification({
            type: 'error',
            title: 'Network Error',
            message: 'Please check your internet connection and try again.',
          });
        }
      }

      return error;
    });
  }

  // Add request interceptor
  public addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }

  // Add response interceptor
  public addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }

  // Add error interceptor
  public addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor);
  }

  // Make HTTP request
  public async request<T = any>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const {
      timeout = this.defaultTimeout,
      retries = this.defaultRetries,
      retryDelay = this.defaultRetryDelay,
      skipErrorHandling = false,
      ...fetchConfig
    } = config;

    // Apply request interceptors
    let finalConfig = { ...fetchConfig };
    for (const interceptor of this.requestInterceptors) {
      finalConfig = await interceptor(finalConfig);
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    let lastError: ApiError | null = null;

    // Retry logic
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...finalConfig,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Apply response interceptors
        let finalResponse = response;
        for (const interceptor of this.responseInterceptors) {
          finalResponse = await interceptor(finalResponse);
        }

        // Handle HTTP errors
        if (!finalResponse.ok) {
          const errorData = await this.parseErrorResponse(finalResponse);
          const apiError: ApiError = {
            message: errorData.message || `HTTP ${finalResponse.status}`,
            code: errorData.code,
            status: finalResponse.status,
            details: errorData.details,
          };

          // Don't retry on client errors (4xx)
          if (finalResponse.status >= 400 && finalResponse.status < 500) {
            throw apiError;
          }

          lastError = apiError;
          
          // Wait before retry
          if (attempt < retries) {
            await this.delay(retryDelay * Math.pow(2, attempt));
            continue;
          }
          
          throw apiError;
        }

        // Parse successful response
        const data = await this.parseResponse<T>(finalResponse);
        return data;

      } catch (error: any) {
        clearTimeout(timeoutId);

        // Handle abort error (timeout)
        if (error.name === 'AbortError') {
          lastError = {
            message: 'Request timeout',
            code: 'TIMEOUT',
            status: 408,
          };
        } else if (error instanceof TypeError && error.message.includes('fetch')) {
          // Network error
          lastError = {
            message: 'Network error',
            code: 'NETWORK_ERROR',
            status: 0,
          };
        } else if (error.message || error.code) {
          // API error
          lastError = error;
        } else {
          // Unknown error
          lastError = {
            message: 'An unexpected error occurred',
            code: 'UNKNOWN_ERROR',
          };
        }

        // Don't retry on certain errors
        if (error.code === 'TIMEOUT' || (error.status && error.status >= 400 && error.status < 500)) {
          break;
        }

        // Wait before retry
        if (attempt < retries) {
          await this.delay(retryDelay * Math.pow(2, attempt));
          continue;
        }
      }
    }

    // Apply error interceptors
    if (lastError && !skipErrorHandling) {
      for (const interceptor of this.errorInterceptors) {
        lastError = await interceptor(lastError);
      }
    }

    throw lastError;
  }

  // HTTP method helpers
  public async get<T = any>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  public async post<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async put<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async patch<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async delete<T = any>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  // Upload file
  public async upload<T = any>(
    endpoint: string,
    file: File,
    config?: Omit<RequestConfig, 'body'>
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData, let browser set it
        ...config?.headers,
        'Content-Type': undefined,
      },
    });
  }

  // Parse response
  private async parseResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json();
      
      // Handle different response formats
      if (json.data !== undefined) {
        return json as ApiResponse<T>;
      } else {
        return {
          data: json as T,
          status: 'success',
        };
      }
    } else {
      const text = await response.text();
      return {
        data: text as T,
        status: 'success',
      };
    }
  }

  // Parse error response
  private async parseErrorResponse(response: Response): Promise<any> {
    try {
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        const text = await response.text();
        return { message: text || response.statusText };
      }
    } catch {
      return { message: response.statusText || 'Unknown error' };
    }
  }

  // Get authentication token
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth-token');
    }
    return null;
  }

  // Delay helper
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// React hook for API client
export function useApiClient() {
  return apiClient;
}

// Backwards compatibility helper for modules expecting getApiClient()
export function getApiClient() {
  return apiClient;
}

// Utility functions for common API patterns
export const api = {
  // Authentication
  auth: {
    login: (credentials: { email: string; password: string }) =>
      apiClient.post('/auth/login', credentials),
    logout: () => apiClient.post('/auth/logout'),
    refresh: () => apiClient.post('/auth/refresh'),
    me: () => apiClient.get('/auth/me'),
  },

  // Dashboard
  dashboard: {
    getMetrics: () => apiClient.get('/dashboard/metrics'),
    getHealth: () => apiClient.get('/system/health'),
  },

  // Chat
  chat: {
    getConversations: () => apiClient.get('/chat/conversations'),
    getConversation: (id: string) => apiClient.get(`/chat/conversations/${id}`),
    sendMessage: (conversationId: string, message: string) =>
      apiClient.post(`/chat/conversations/${conversationId}/messages`, { message }),
  },

  // Memory
  memory: {
    getAnalytics: () => apiClient.get('/memory/analytics'),
    search: (query: string) => apiClient.post('/memory/search', { query }),
    getNetwork: () => apiClient.get('/memory/network'),
  },

  // Plugins
  plugins: {
    getInstalled: () => apiClient.get('/plugins'),
    getMarketplace: () => apiClient.get('/plugins/marketplace'),
    install: (pluginId: string) => apiClient.post(`/plugins/${pluginId}/install`),
    uninstall: (pluginId: string) => apiClient.delete(`/plugins/${pluginId}`),
  },

  // Providers
  providers: {
    getList: () => apiClient.get('/providers'),
    getProvider: (id: string) => apiClient.get(`/providers/${id}`),
    updateProvider: (id: string, config: any) => apiClient.put(`/providers/${id}`, config),
  },

  // Users
  users: {
    getList: () => apiClient.get('/users'),
    getUser: (id: string) => apiClient.get(`/users/${id}`),
    updateUser: (id: string, data: any) => apiClient.put(`/users/${id}`, data),
  },

  // System
  system: {
    getHealth: () => apiClient.get('/system/health'),
    getMetrics: () => apiClient.get('/system/metrics'),
    getLogs: () => apiClient.get('/system/logs'),
  },
};

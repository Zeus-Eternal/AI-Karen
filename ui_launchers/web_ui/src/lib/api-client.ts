/**
 * API Client
 * 
 * A simple HTTP client for making API requests to the Kari backend.
 */

export interface ApiRequest {
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
  params?: Record<string, any>;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export interface ApiError extends Error {
  message: string;
  status?: number;
  code?: string;
  details?: any;
  statusText?: string;
  endpoint?: string;
  responseTime?: number;
  isNetworkError?: boolean;
  isCorsError?: boolean;
  isTimeoutError?: boolean;
}

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = '', defaultHeaders: Record<string, string> = {}) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...defaultHeaders
    };
  }

  private async makeRequest<T = any>(
    method: string,
    url: string,
    data?: any,
    headers?: Record<string, string>
  ): Promise<T> {
    const fullUrl = `${this.baseUrl}${url}`;
    const requestHeaders = { ...this.defaultHeaders, ...headers };

    const config: RequestInit = {
      method,
      headers: requestHeaders,
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(fullUrl, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        
        // Handle rate limiting with exponential backoff
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After');
          const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : 5000;
          
          console.warn(`Rate limited. Retrying after ${waitTime}ms`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          
          // Retry the request once
          const retryResponse = await fetch(fullUrl, config);
          if (retryResponse.ok) {
            const contentType = retryResponse.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
              return await retryResponse.json();
            } else {
              return await retryResponse.text() as any;
            }
          }
        }
        
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text() as any;
      }
    } catch (error) {
      console.error(`API request failed: ${method} ${fullUrl}`, error);
      throw error;
    }
  }

  async get<T = any>(url: string, headers?: Record<string, string>): Promise<T> {
    return this.makeRequest<T>('GET', url, undefined, headers);
  }

  async post<T = any>(url: string, data?: any, headers?: Record<string, string>): Promise<T> {
    return this.makeRequest<T>('POST', url, data, headers);
  }

  async put<T = any>(url: string, data?: any, headers?: Record<string, string>): Promise<T> {
    return this.makeRequest<T>('PUT', url, data, headers);
  }

  async patch<T = any>(url: string, data?: any, headers?: Record<string, string>): Promise<T> {
    return this.makeRequest<T>('PATCH', url, data, headers);
  }

  async delete<T = any>(url: string, headers?: Record<string, string>): Promise<T> {
    return this.makeRequest<T>('DELETE', url, undefined, headers);
  }

  // Generic request method that matches ApiRequest interface
  async request<T = any>(apiRequest: ApiRequest): Promise<ApiResponse<T>> {
    const { endpoint, method, body, headers, params } = apiRequest;
    
    // Build URL with query parameters if provided
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
      }
    }

    try {
      const data = await this.makeRequest<T>(method, url, body, headers);
      return {
        data,
        status: 200 // We don't have access to the actual status in this simplified version
      };
    } catch (error: any) {
      throw {
        message: error.message || 'Request failed',
        status: error.status || 500,
        code: error.code,
        details: error
      } as ApiError;
    }
  }

  // Health check method
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const data = await this.get('/health');
      return {
        data,
        status: 200
      };
    } catch (error: any) {
      throw {
        message: error.message || 'Health check failed',
        status: error.status || 500,
        code: error.code,
        details: error
      } as ApiError;
    }
  }

  // Get backend URL
  getBackendUrl(): string {
    return this.baseUrl;
  }

  // Get endpoints (placeholder)
  getEndpoints() {
    return {};
  }

  // Get endpoint statistics (placeholder)
  getEndpointStats() {
    return {};
  }

  // Reset endpoint statistics (placeholder)
  resetEndpointStats(endpoint?: string): void {
    // Implementation would go here
  }

  // Clear caches (placeholder)
  clearCaches(): void {
    // Implementation would go here
  }

  // Upload file method
  async uploadFile<T = any>(url: string, file: File, fieldName: string = 'file'): Promise<T> {
    const formData = new FormData();
    formData.append(fieldName, file);
    
    const headers = { ...this.defaultHeaders };
    // Remove Content-Type header to let browser set it with boundary
    delete headers['Content-Type'];
    
    const fullUrl = `${this.baseUrl}${url}`;
    
    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers,
        body: formData,
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text() as any;
      }
    } catch (error) {
      console.error(`File upload failed: POST ${fullUrl}`, error);
      throw error;
    }
  }

  setAuthToken(token: string) {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  removeAuthToken() {
    delete this.defaultHeaders['Authorization'];
  }

  setBaseUrl(baseUrl: string) {
    this.baseUrl = baseUrl;
  }
}

// Default API client instance
const defaultApiClient = new ApiClient(
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  {
    'Content-Type': 'application/json',
  }
);

/**
 * Get the default API client instance
 */
export function getApiClient(): ApiClient {
  return defaultApiClient;
}

// Export the default instance as well
export default defaultApiClient;
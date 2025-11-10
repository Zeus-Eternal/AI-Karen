/**
 * Integrated API Client with Enhanced Session Management
 *
 * Wraps the existing API client with the new session management system,
 * providing automatic token refresh, session recovery, and intelligent error handling.
 *
 * Requirements: 5.2, 5.3, 1.1, 1.2
 */
import {
  getApiClient,
  type ApiClient,
  type RequestConfig,
  type ApiResponse,
} from './api-client';
import { isAuthenticated, clearSession } from './auth/session';

export interface ApiRequest extends RequestConfig {
  endpoint: string;
}

export interface IntegratedApiClientOptions {
  autoRetryOn401?: boolean;     // reserved for future token-refresh
  includeCredentials?: boolean; // include cookies by default
  redirectOn401?: boolean;      // redirect to /login on 401
  loginPath?: string;           // default '/login'
  treatNetworkErrorsAs401?: boolean; // optional: treat 0/undefined status as auth-loss (off)
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

function isFormLike(body: unknown): body is FormData | Blob | ArrayBuffer | ReadableStream {
  return (
    typeof FormData !== 'undefined' && body instanceof FormData
  ) || (typeof Blob !== 'undefined' && body instanceof Blob)
    || (typeof ArrayBuffer !== 'undefined' && body instanceof ArrayBuffer)
    || (typeof ReadableStream !== 'undefined' && body instanceof ReadableStream);
}

function isPlainObject(v: unknown): v is Record<string, any> {
  return Object.prototype.toString.call(v) === '[object Object]';
}

function extractStatus(err: any): number | undefined {
  // Support multiple error shapes: fetch, axios-like, custom
  return (
    err?.status ??
    err?.response?.status ??
    err?.data?.status ??
    (typeof err?.code === 'number' ? err.code : undefined)
  );
}

function withCredentials(config?: RequestConfig, include = true): RequestConfig {
  if (!include) return config ?? {};
  return { credentials: 'include', ...config };
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
      redirectOn401: true,
      loginPath: '/login',
      treatNetworkErrorsAs401: false,
      ...options,
    };
  }

  /**
   * Make an authenticated request with simple 401 handling
   */
  private async makeAuthenticatedRequest<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    const { endpoint, ...rest } = request;

    // If endpoint is protected and user is not authenticated, short-circuit
    if (this.isProtectedEndpoint(endpoint) && typeof window !== 'undefined') {
      try {
        if (!isAuthenticated()) {
          if (this.options.redirectOn401 && this.options.loginPath) {
            window.location.href = this.options.loginPath;
          }
          throw Object.assign(new Error('Unauthenticated'), { status: 401 });
        }
      } catch {
        // if session layer throws, fall through to request anyway
      }
    }

    // Prepare config: credentials + headers + JSON encoding if needed
    const config = this.prepareConfig(rest);

    try {
      return await this.apiClient.request<T>(endpoint, config);
    } catch (error: any) {
      const status = extractStatus(error);

      const isNetworkLike401 =
        this.options.treatNetworkErrorsAs401 && (status === undefined || status === 0);

      if (status === 401 || isNetworkLike401) {
        // Clear session and optionally redirect
        try { clearSession(); } catch { /* no-op */ }

        if (typeof window !== 'undefined' && this.options.redirectOn401 && this.options.loginPath) {
          window.location.href = this.options.loginPath;
        }
      }
      throw error;
    }
  }

  /**
   * Build RequestConfig with credentials and content normalization
   */
  private prepareConfig(config?: RequestConfig): RequestConfig {
    const merged: RequestConfig = withCredentials(config, this.options.includeCredentials !== false);

    // Normalize JSON bodies unless already FormData/Blob/etc.
    const method = (merged.method || 'GET').toUpperCase() as HttpMethod;
    const hasBody = method === 'POST' || method === 'PUT' || method === 'PATCH';

    if (hasBody && merged.body != null && !isFormLike(merged.body)) {
      if (isPlainObject(merged.body) || Array.isArray(merged.body)) {
        const headers = new Headers(merged.headers as any);
        if (!headers.has('Content-Type')) {
          headers.set('Content-Type', 'application/json');
        }
        merged.headers = headers as any;
        merged.body = JSON.stringify(merged.body);
      }
      // else: let strings pass-through as-is
    }

    return merged;
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
    return !publicEndpoints.some((pub) => endpoint.startsWith(pub));
  }

  // ------------- HTTP Convenience Methods -------------

  async get<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'GET',
      ...(options || {}),
    });
  }

  async post<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'POST',
      body,
      ...(options || {}),
    });
  }

  async put<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'PUT',
      body,
      ...(options || {}),
    });
  }

  async delete<T = any>(
    endpoint: string,
    options?: Omit<ApiRequest, 'endpoint' | 'method'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'DELETE',
      ...(options || {}),
    });
  }

  async patch<T = any>(
    endpoint: string,
    body?: any,
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'PATCH',
      body,
      ...(options || {}),
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
    options?: Omit<ApiRequest, 'endpoint' | 'method' | 'body'>
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append(fieldName, file);
    if (additionalFields) {
      for (const [k, v] of Object.entries(additionalFields)) {
        formData.append(k, v);
      }
    }

    return this.makeAuthenticatedRequest<T>({
      endpoint,
      method: 'POST',
      body: formData,
      ...(options || {}),
      // Ensure no JSON headers override; browser sets multipart boundary
      headers: options?.headers, 
    });
  }

  /**
   * Make a public request (no authentication enforcement)
   */
  async requestPublic<T = any>(request: ApiRequest): Promise<ApiResponse<T>> {
    const { endpoint, ...config } = request;
    const prepared = this.prepareConfig(config);
    return this.apiClient.request<T>(endpoint, prepared);
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
export function getIntegratedApiClient(
  options?: IntegratedApiClientOptions
): IntegratedApiClient {
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
export function initializeIntegratedApiClient(
  options?: IntegratedApiClientOptions
): IntegratedApiClient {
  integratedApiClient = new IntegratedApiClient(options);
  return integratedApiClient;
}

/**
 * Hook for using the integrated API client in React components
 * (kept minimal to avoid react import; caller can wrap with useMemo)
 */
export function useIntegratedApiClient(options?: IntegratedApiClientOptions) {
  return getIntegratedApiClient(options);
}

export default IntegratedApiClient;

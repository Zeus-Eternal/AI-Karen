"use client";

// API service for HTTP requests
const SAME_ORIGIN_API_BASE_URL = '';
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

class ApiClient {
  private readonly SESSION_MARKER_KEY = 'kari_session_expected';

  private async sleep(ms: number): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, ms));
  }

  private getPreferredBaseUrl(): string {
    const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';
    if (isBrowser) {
      const origin = window.location.origin;
      console.log('[ApiClient] Browser environment. Using origin as baseUrl:', origin);
      return origin;
    }

    // Server-side only
    const env = (process as any).env || {};
    return (env.KAREN_BACKEND_URL || env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/$/, '');
  }

  private getFallbackBaseUrl(preferredBaseUrl: string): string | null {
    const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';
    if (isBrowser) {
      return null;
    }

    const env = (process as any).env || {};
    const configuredBackendUrl = (env.KAREN_BACKEND_URL || env.NEXT_PUBLIC_API_BASE_URL || '').replace(/\/$/, '');
    
    // Server-side: if we preferred same-origin (unlikely on server), fallback to direct backend URL
    if (preferredBaseUrl === SAME_ORIGIN_API_BASE_URL) {
      return configuredBackendUrl || null;
    }
    
    // Otherwise, we were already trying direct backend, fallback to proxy origin if applicable
    return SAME_ORIGIN_API_BASE_URL || null;
  }

  private buildUrl(baseUrl: string | null, endpoint: string): string {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    if (typeof window !== 'undefined' && typeof document !== 'undefined') {
      // Browser: Prevent Docker internal hostnames or subnets from leaking
      if (baseUrl && (
        baseUrl.includes('api') || 
        baseUrl.includes('172.') || 
        baseUrl.includes('10.') || 
        baseUrl.includes('192.168.') ||
        baseUrl.includes('localhost:8000') ||
        baseUrl === 'api'
      )) {
        console.warn('[ApiClient] Blocking internal/Docker baseUrl in browser:', baseUrl, 'Rewriting to:', normalizedEndpoint);
        return normalizedEndpoint;
      }
      const result = baseUrl ? `${baseUrl}${normalizedEndpoint}` : normalizedEndpoint;
      console.log('[ApiClient] Browser BuildUrl result:', result, '(baseUrl:', baseUrl, 'endpoint:', endpoint, ')');
      return result;
    }

    if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
      return endpoint;
    }

    return `${baseUrl || ''}${normalizedEndpoint}`;
  }

  private shouldRetryWithSameOrigin(error: unknown): boolean {
    return typeof window !== 'undefined' && error instanceof TypeError;
  }

  private hasFallbackBaseUrl(baseUrl: string | null): baseUrl is string {
    return baseUrl !== null && baseUrl !== '';
  }

  private shouldRetryWithDirectBackend(response: Response, fallbackBaseUrl: string | null): boolean {
    return (
      typeof window !== 'undefined' &&
      this.hasFallbackBaseUrl(fallbackBaseUrl) &&
      response.status >= 500
    );
  }

  private shouldRetryMissingApiRoute(endpoint: string, response: Response, fallbackBaseUrl: string | null): boolean {
    return (
      typeof window !== 'undefined' &&
      this.hasFallbackBaseUrl(fallbackBaseUrl) &&
      endpoint.startsWith('/api/') &&
      response.status === 404
    );
  }

  private shouldRetryAssistServerError(endpoint: string, response: Response): boolean {
    return (
      typeof window !== 'undefined' &&
      endpoint === '/api/copilot/assist' &&
      response.status >= 500
    );
  }

  private hasSessionMarker(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }

    try {
      return localStorage.getItem(this.SESSION_MARKER_KEY) === 'true';
    } catch {
      return false;
    }
  }

  private shouldPreferCookieSession(): boolean {
    return typeof window !== 'undefined' && this.hasSessionMarker();
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      if (this.shouldPreferCookieSession()) {
        return {
          'Content-Type': 'application/json'
        };
      }

      // Try to get a valid access token
      const accessToken = localStorage.getItem('access_token');
      
      if (!accessToken) {
        return {
          'Content-Type': 'application/json'
        };
      }

      // Check if token is expired and refresh if needed
      if (this.isTokenExpired(accessToken)) {
        try {
          await this.refreshAccessToken();
        } catch (error) {
          // If refresh fails, clear auth data and continue without auth
          console.warn('Failed to refresh access token, proceeding without auth');
          return {
            'Content-Type': 'application/json'
          };
        }
      }

      return {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      };
    } catch (error) {
      return {
        'Content-Type': 'application/json'
      };
    }
  }

  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp < Date.now() / 1000;
    } catch {
      return true;
    }
  }

  private async refreshAccessToken(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const sendRefresh = async (baseUrl: string | null): Promise<Response> =>
        fetch(this.buildUrl(baseUrl, '/api/auth/refresh'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

      const preferredBaseUrl = this.getPreferredBaseUrl();
      const fallbackBaseUrl = this.getFallbackBaseUrl(preferredBaseUrl);

      let response: Response;
      try {
        response = await sendRefresh(preferredBaseUrl);
      } catch (error) {
        if (!this.shouldRetryWithSameOrigin(error) || !fallbackBaseUrl) {
          throw error;
        }
        response = await sendRefresh(fallbackBaseUrl);
      }

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
    } catch (error) {
      // If refresh fails, clear all auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
      
      if (typeof document !== 'undefined') {
        document.cookie = 'kari_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
        document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        document.cookie = 'refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      }
      
      throw error;
    }
  }

  private async request<T>(endpoint: string, init: RequestInit = {}): Promise<T> {
    const send = async (baseUrl: string | null): Promise<Response> => {
      const authHeaders = await this.getAuthHeaders();
      const requestHeaders = {
        ...authHeaders,
        ...((init.headers as Record<string, string> | undefined) || {}),
      };

      let url = this.buildUrl(baseUrl, endpoint);
      // Final fallback: Ensure no Docker hostnames leak if logic above somehow missed it or was bypassed
      if (typeof window !== 'undefined') {
        url = url.replace(/http:\/\/api:8000/g, '');
        console.log('[ApiClient] Executing browser fetch to URL:', url);
      }
      return fetch(url, {
        ...init,
        headers: requestHeaders,
        credentials: 'include',
      });
    };

    const preferredBaseUrl = this.getPreferredBaseUrl();
    const fallbackBaseUrl: string | null = this.getFallbackBaseUrl(preferredBaseUrl) || null;

    let response: Response;
    try {
      response = await send(preferredBaseUrl);
    } catch (error) {
      if (!this.shouldRetryWithSameOrigin(error) || !this.hasFallbackBaseUrl(fallbackBaseUrl)) {
        throw error;
      }
      response = await send(fallbackBaseUrl);
    }

    if (
      this.shouldRetryWithDirectBackend(response, fallbackBaseUrl) ||
      this.shouldRetryMissingApiRoute(endpoint, response, fallbackBaseUrl)
    ) {
      response = await send(fallbackBaseUrl);
    }

    if (response.status === 401 && !this.shouldPreferCookieSession()) {
      try {
        await this.refreshAccessToken();
        try {
          response = await send(preferredBaseUrl);
        } catch (error) {
          if (!this.shouldRetryWithSameOrigin(error) || !fallbackBaseUrl) {
            throw error;
          }
          response = await send(fallbackBaseUrl);
        }
        if (
          this.shouldRetryWithDirectBackend(response, fallbackBaseUrl) ||
          this.shouldRetryMissingApiRoute(endpoint, response, fallbackBaseUrl)
        ) {
          response = await send(fallbackBaseUrl);
        }
      } catch (refreshError) {
        // Fall through to the error handling below with the original/second response.
      }
    }

    if (!response.ok && this.shouldRetryAssistServerError(endpoint, response)) {
      await this.sleep(250);
      try {
        response = await send(preferredBaseUrl);
      } catch (error) {
        if (!this.shouldRetryWithSameOrigin(error) || !this.hasFallbackBaseUrl(fallbackBaseUrl)) {
          throw error;
        }
        response = await send(fallbackBaseUrl);
      }

      if (
        this.shouldRetryWithDirectBackend(response, fallbackBaseUrl) ||
        this.shouldRetryMissingApiRoute(endpoint, response, fallbackBaseUrl)
      ) {
        response = await send(fallbackBaseUrl);
      }
    }

    if (!response.ok) {
      const rawText = await response.text().catch(() => '');
      let errorData: Record<string, any> = {};
      if (rawText) {
        try {
          errorData = JSON.parse(rawText);
        } catch {
          errorData = { detail: rawText.trim() };
        }
      }
      throw new ApiError(
        response.status,
        errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const text = await response.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async post<T>(endpoint: string, data?: any, init: RequestInit = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async put<T>(endpoint: string, data?: any, init: RequestInit = {}): Promise<T> {
    return this.request<T>(endpoint, {
      ...init,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;

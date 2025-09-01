/**
 * Authentication Interceptor
 * Handles 401 errors and automatic token refresh
 */

import { bootSession, clearSession, refreshToken, isAuthenticated } from './auth/session';

export interface RequestInterceptor {
  onRequest?: (config: RequestInit) => Promise<RequestInit>;
  onResponse?: (response: Response) => Promise<Response>;
  onError?: (error: any) => Promise<any>;
}

class AuthInterceptor implements RequestInterceptor {
  private refreshInProgress = false;
  private refreshPromise: Promise<void> | null = null;

  async onRequest(config: RequestInit): Promise<RequestInit> {
    // Don't add auth headers to login/refresh endpoints
    const url = (config as any).url || '';
    if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
      return config;
    }

    // Ensure we have a valid session before making the request
    try {
      if (!isAuthenticated()) {
        await bootSession();
      }
    } catch (error) {
      console.log('Failed to ensure authentication before request:', error);
      // Don't block the request - let it proceed and handle 401 in response
    }

    return config;
  }

  async onResponse(response: Response): Promise<Response> {
    // Handle 401 responses
    if (response.status === 401) {
      const url = response.url;
      
      // Don't retry auth endpoints
      if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
        return response;
      }

      console.log('Received 401 response, attempting token refresh');
      
      try {
        await this.handleTokenRefresh();
        
        // Clone the original request and retry
        const originalRequest = (response as any).originalRequest;
        if (originalRequest) {
          console.log('Retrying request after token refresh');
          const retryResponse = await fetch(originalRequest.url, originalRequest);
          return retryResponse;
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        clearSession();
        
        // Redirect to login if we're in a browser environment
        if (typeof window !== 'undefined' && !url.includes('/api/auth/')) {
          window.location.href = '/login';
        }
      }
    }

    return response;
  }

  async onError(error: any): Promise<any> {
    // Handle network errors that might be auth-related
    if (error.status === 401 || error.message?.includes('401')) {
      console.log('Handling 401 error in interceptor');
      
      try {
        await this.handleTokenRefresh();
      } catch (refreshError) {
        console.error('Token refresh failed in error handler:', refreshError);
        clearSession();
        
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }

    throw error;
  }

  private async handleTokenRefresh(): Promise<void> {
    // Prevent multiple simultaneous refresh attempts
    if (this.refreshInProgress) {
      if (this.refreshPromise) {
        return this.refreshPromise;
      }
      return;
    }

    this.refreshInProgress = true;
    this.refreshPromise = (async () => {
      try {
        await refreshToken();
        console.log('Token refresh successful');
      } catch (error) {
        console.error('Token refresh failed:', error);
        throw error;
      } finally {
        this.refreshInProgress = false;
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }
}

export const authInterceptor = new AuthInterceptor();

/**
 * Wrap fetch with authentication interceptor
 */
export async function authenticatedFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  try {
    // Apply request interceptor
    const config = await authInterceptor.onRequest(init || {});
    
    // Store original request for potential retry
    const originalRequest = {
      url: input.toString(),
      ...config
    };

    // Make the request
    const response = await fetch(input, config);
    
    // Store original request on response for retry capability
    (response as any).originalRequest = originalRequest;
    
    // Apply response interceptor
    return await authInterceptor.onResponse(response);
    
  } catch (error) {
    // Apply error interceptor
    return await authInterceptor.onError(error);
  }
}

/**
 * Check if a URL requires authentication
 */
export function requiresAuth(url: string): boolean {
  const publicEndpoints = [
    '/api/health',
    '/api/auth/login',
    '/api/auth/refresh',
    '/api/auth/logout',
    '/login',
    '/register',
    '/forgot-password'
  ];
  
  return !publicEndpoints.some(endpoint => url.includes(endpoint));
}

/**
 * Add authentication headers to a request
 */
export function addAuthHeaders(headers: Record<string, string> = {}): Record<string, string> {
  // This will be handled by the session management
  // Just return the headers as-is since session.ts handles auth headers
  return headers;
}
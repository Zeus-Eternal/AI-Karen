/**
 * Authentication Interceptor
 * Handles 401 errors and automatic token refresh
 */
import { clearSession, isAuthenticated, validateSession } from './auth/session';
export interface RequestInterceptor {
  onRequest?: (config: RequestInit) => Promise<RequestInit>;
  onResponse?: (response: Response) => Promise<Response>;
  onError?: (error: Error) => Promise<unknown>;
}
class AuthInterceptor implements RequestInterceptor {
  private refreshInProgress = false;
  private refreshPromise: Promise<void> | null = null;
  async onRequest(config: RequestInit): Promise<RequestInit> {
    // Don't add auth headers to login/logout endpoints
    const url = (config as any).url || '';
    if (url.includes('/auth/login') || url.includes('/auth/logout')) {
      return config;
    }
    // Ensure cookies are included for authentication
    return {
      ...config,
      credentials: 'include'
    };
  }
  async onResponse(response: Response): Promise<Response> {
    // Handle 401 responses
    if (response.status === 401) {
      const url = response.url;
      // Don't redirect for auth endpoints
      if (url.includes('/auth/login') || url.includes('/auth/logout')) {
        return response;
      }
      // Clear session state
      clearSession();
      // Redirect to login if we're in a browser environment
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return response;
  }
  async onError(error: Error): Promise<Response> {
    // Handle network errors that might be auth-related
    const errorWithStatus = error as Error & { status?: number };
    if (errorWithStatus.status === 401 || error.message?.includes('401')) {
      // Clear session and redirect to login
      clearSession();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    throw error;
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
    return await authInterceptor.onError(error as Error);
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
 * In cookie-based auth, this just ensures credentials are included
 */
export function addAuthHeaders(headers: Record<string, string> = {}): Record<string, string> {
  // Cookie-based authentication doesn't need manual headers
  // The credentials: 'include' option handles cookie authentication
  return headers;
}

/**
 * Authentication Interceptor
 * Handles 401 errors and automatic token refresh
 */
import { clearSession } from './auth/session';

type RequestInitWithUrl = RequestInit & { url?: string };

interface ResponseWithOriginalRequest extends Response {
  originalRequest?: {
    url: string;
    init: RequestInit;
  };
}
export interface RequestInterceptor {
  onRequest?: (config: RequestInit) => Promise<RequestInit>;
  onResponse?: (response: Response) => Promise<Response>;
  onError?: (error: Error) => Promise<unknown>;
}

// Track last successful auth to prevent redirect loops during login
let lastAuthSuccessTime: number | null = null;
const AUTH_GRACE_PERIOD_MS = 3000; // 3 second grace period after login

/**
 * Call this when authentication succeeds to prevent 401 redirects during state propagation
 */
export function markAuthSuccess(): void {
  lastAuthSuccessTime = Date.now();
}

/**
 * Check if we're within the grace period after a successful login
 */
function isWithinAuthGracePeriod(): boolean {
  if (lastAuthSuccessTime === null) return false;
  return (Date.now() - lastAuthSuccessTime) < AUTH_GRACE_PERIOD_MS;
}

class AuthInterceptor implements RequestInterceptor {
  private refreshInProgress = false;
  private refreshPromise: Promise<void> | null = null;
  async onRequest(config: RequestInit): Promise<RequestInit> {
    // Don't add auth headers to login/logout endpoints
    const requestConfig = config as RequestInitWithUrl;
    const url = typeof requestConfig.url === 'string' ? requestConfig.url : '';
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

      // Don't redirect during grace period after successful login
      // This prevents race conditions where API calls made immediately after login
      // might fail before auth state has fully propagated
      if (isWithinAuthGracePeriod()) {
        console.warn('[AuthInterceptor] Suppressing 401 redirect during auth grace period', url);
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
      // Don't redirect during grace period after successful login
      if (!isWithinAuthGracePeriod()) {
        // Clear session and redirect to login
        clearSession();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      } else {
        console.warn('[AuthInterceptor] Suppressing 401 error redirect during auth grace period');
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
    // Make the request
    const response = await fetch(input, config);
    // Store original request on response for retry capability
    const responseWithOriginalRequest = response as ResponseWithOriginalRequest;
    responseWithOriginalRequest.originalRequest = {
      url: input.toString(),
      init: config,
    };
    // Apply response interceptor
    return await authInterceptor.onResponse(response);
  } catch (error: unknown) {
    // Apply error interceptor
    if (error instanceof Error) {
      return await authInterceptor.onError(error);
    }

    return await authInterceptor.onError(new Error(String(error)));
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

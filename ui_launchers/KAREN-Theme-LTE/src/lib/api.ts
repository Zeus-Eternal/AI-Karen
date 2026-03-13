/**
 * API Utility Functions
 * Helper functions for making API calls to backend
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000';

/**
 * Get the backend URL for API calls
 */
export function getBackendUrl(): string {
  return BACKEND_URL;
}

/**
 * Make an authenticated API call to backend
 */
export async function apiCall<T>(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    headers?: Record<string, string>;
    body?: Record<string, unknown>;
  } = {}
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;
  const token = typeof window !== 'undefined' ? localStorage.getItem('karen-auth-token') : null;

  const response = await fetch(url, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
    ...(options.body && { body: JSON.stringify(options.body) }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || error.message || 'API call failed');
  }

  return response.json();
}

/**
 * Make a public API call (no authentication)
 */
export async function publicApiCall<T>(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    headers?: Record<string, string>;
    body?: Record<string, unknown>;
  } = {}
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;

  const response = await fetch(url, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...(options.body && { body: JSON.stringify(options.body) }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || error.message || 'API call failed');
  }

  return response.json();
}

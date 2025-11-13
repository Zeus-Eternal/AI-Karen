/**
 * Backend endpoint resolution utilities for Next.js API routes.
 *
 * Enhanced with Environment Configuration Manager and ConnectionManager for improved reliability,
 * automatic environment detection, comprehensive validation, and retry logic.
 * 
 * Requirements: 1.1, 3.1, 3.2
 */
import { getEnvironmentConfigManager } from '../../../lib/config/index';
import { getConnectionManager, ConnectionOptions, RequestResult, ConnectionError } from '../../../lib/connection/connection-manager';

// Legacy implementation for backward compatibility
const DEFAULT_PORT = process.env.KAREN_BACKEND_PORT || process.env.BACKEND_PORT || '8000';
// Standardized environment variables with legacy fallbacks
const KAREN_BACKEND_URL = process.env.KAREN_BACKEND_URL;
const NEXT_PUBLIC_KAREN_BACKEND_URL = process.env.NEXT_PUBLIC_KAREN_BACKEND_URL;

// Log the final resolved URL for debugging purposes
if (KAREN_BACKEND_URL) {
  console.log(`[API Proxy] Backend URL (server-side): ${KAREN_BACKEND_URL}`);
}
if (NEXT_PUBLIC_KAREN_BACKEND_URL) {
  console.log(`[API Proxy] Backend URL (client-side): ${NEXT_PUBLIC_KAREN_BACKEND_URL}`);
}

export const backendUrl = KAREN_BACKEND_URL || NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000';
const DEFAULT_HOST_CANDIDATES = [
  `http://localhost:${DEFAULT_PORT}`,
  `http://127.0.0.1:${DEFAULT_PORT}`,
  `http://0.0.0.0:${DEFAULT_PORT}`,
  `http://ai-karen-api:${DEFAULT_PORT}`,
  `http://api:${DEFAULT_PORT}`,
];
function normalizeUrl(url: string): string {
  return url.replace(/\/+$/, '');
}
function buildCandidateList(extra: (string | undefined)[] = []): string[] {
  const ordered = [...extra, ...ENV_CANDIDATES, ...DEFAULT_HOST_CANDIDATES]
    .filter((value): value is string => Boolean(value && value.trim()))
    .map((value) => normalizeUrl(value.trim()));
  return Array.from(new Set(ordered));
}
/**
 * Return the preferred backend base URL using the Environment Configuration Manager.
 * Falls back to legacy implementation if the manager is not available.
 */
export function getBackendBaseUrl(): string {
  try {
    const configManager = getEnvironmentConfigManager();
    const config = configManager.getBackendConfig();
    return config.primaryUrl;
  } catch {
    // Fallback to legacy implementation
    const candidates = buildCandidateList();
    return candidates[0] ?? 'http://localhost:8000';
  }
}
/**
 * Return every backend candidate URL in priority order using the Environment Configuration Manager.
 * Includes primary URL and all fallback URLs for comprehensive connectivity options.
 */
export function getBackendCandidates(additional: (string | undefined)[] = []): string[] {
  try {
    const configManager = getEnvironmentConfigManager();
    const candidates = configManager.getAllCandidateUrls();
    // Add any additional URLs provided
    const additionalUrls = additional
      .filter((value): value is string => Boolean(value && value.trim()))
      .map((value) => normalizeUrl(value.trim()));
    return Array.from(new Set([...candidates, ...additionalUrls]));
  } catch {
    // Fallback to legacy implementation
    return buildCandidateList(additional);
  }
}
/**
 * Helper that joins a path onto the resolved backend base URL.
 */
export function withBackendPath(path: string, baseUrl = getBackendBaseUrl()): string {
  const normalizedBase = normalizeUrl(baseUrl);
  if (!path.startsWith('/')) {
    return `${normalizedBase}/${path}`;
  }
  return `${normalizedBase}${path}`;
}
/**
 * Get timeout configuration from Environment Configuration Manager
 */
export function getTimeoutConfig() {
  try {
    const configManager = getEnvironmentConfigManager();
    return configManager.getTimeoutConfig();
  } catch {
    return {
      connection: 30000,
      authentication: 45000,
      sessionValidation: 30000,
      healthCheck: 10000,
    };
  }
}
/**
 * Get retry policy from Environment Configuration Manager
 */
export function getRetryPolicy() {
  try {
    const configManager = getEnvironmentConfigManager();
    return configManager.getRetryPolicy();
  } catch {
    return {
      maxAttempts: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      exponentialBase: 2,
      jitterEnabled: true,
    };
  }
}
/**
 * Get environment information from Environment Configuration Manager
 */
export function getEnvironmentInfo() {
  try {
    const configManager = getEnvironmentConfigManager();
    return configManager.getEnvironmentInfo();
  } catch {
    return {
      type: 'local' as const,
      networkMode: 'localhost' as const,
      isDocker: false,
      isProduction: false,
    };
  }
}
/**
 * Validate backend configuration
 */
export function validateBackendConfiguration() {
  try {
    const configManager = getEnvironmentConfigManager();
    return configManager.validateConfiguration();
  } catch (error) {
    return {
      isValid: false,
      warnings: ['Environment Configuration Manager not available'],
      errors: [String(error)],
      environment: getEnvironmentInfo(),
      config: {
        primaryUrl: getBackendBaseUrl(),
        fallbackUrls: [],
        timeout: 30000,
        retryAttempts: 3,
        healthCheckInterval: 30000,
      },
    };
  }
}
/**
 * Enhanced API request function with retry logic, connection management, and performance optimization
 * 
 * @param path - API endpoint path (e.g., '/api/auth/login')
 * @param options - Fetch options (method, body, headers, etc.)
 * @param connectionOptions - Connection-specific options (timeout, retry, etc.)
 * @returns Promise with request result including retry information
 */
export async function makeBackendRequest<T = unknown>(
  path: string,
  options: RequestInit = {},
  connectionOptions: ConnectionOptions = {}
): Promise<RequestResult<T>> {
  const url = withBackendPath(path);
  try {
    // Temporarily bypass performance optimizer and use connection manager directly
    const connectionManager = getConnectionManager();
    return await connectionManager.makeRequest<T>(url, options, connectionOptions);
  } catch (error) {
    // Enhanced error handling with fallback URLs
    if (error instanceof ConnectionError && error.retryable) {
      const connectionManager = getConnectionManager();
      const candidates = getBackendCandidates();
      // Try fallback URLs if primary failed
      for (let i = 1; i < candidates.length; i++) {
        try {
          const fallbackUrl = withBackendPath(path, candidates[i]);
          return await connectionManager.makeRequest<T>(fallbackUrl, options, {
            ...connectionOptions,
            retryAttempts: 1, // Reduce retries for fallback attempts
          });

        } catch {
          continue;
        }
      }
    }
    // Re-throw the original error if all fallbacks failed
    throw error;
  }
}

/**
 * Simplified API request function for common use cases
 * 
 * @param path - API endpoint path
 * @param method - HTTP method (default: 'GET')
 * @param body - Request body (will be JSON stringified if object)
 * @param headers - Additional headers
 * @returns Promise with response data
 */
export async function apiRequest<T = unknown>(
  path: string,
  method: string = 'GET',
  body?: unknown,
  headers: Record<string, string> = {}
): Promise<T> {
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };
  if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    options.body = typeof body === 'string' ? body : JSON.stringify(body);
  }
  const result = await makeBackendRequest<T>(path, options);
  return result.data;
}
/**
 * GET request with retry logic
 */
export async function apiGet<T = unknown>(
  path: string,
  headers: Record<string, string> = {}
): Promise<T> {
  return apiRequest<T>(path, 'GET', undefined, headers);
}
/**
 * POST request with retry logic
 */
export async function apiPost<T = unknown>(
  path: string,
  body?: unknown,
  headers: Record<string, string> = {}
): Promise<T> {
  return apiRequest<T>(path, 'POST', body, headers);
}
/**
 * PUT request with retry logic
 */
export async function apiPut<T = unknown>(
  path: string,
  body?: unknown,
  headers: Record<string, string> = {}
): Promise<T> {
  return apiRequest<T>(path, 'PUT', body, headers);
}
/**
 * DELETE request with retry logic
 */
export async function apiDelete<T = unknown>(
  path: string,
  headers: Record<string, string> = {}
): Promise<T> {
  return apiRequest<T>(path, 'DELETE', undefined, headers);
}
/**
 * Health check function using ConnectionManager
 */
export async function checkBackendHealth(): Promise<boolean> {
  const connectionManager = getConnectionManager();
  const status = await connectionManager.healthCheck();
  return status.healthy;
}
/**
 * Get connection status from ConnectionManager
 */
export function getConnectionStatus() {
  const connectionManager = getConnectionManager();
  return connectionManager.getConnectionStatus();
}

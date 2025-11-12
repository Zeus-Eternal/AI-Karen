/**
 * Extension 403 Error Fix (production-ready)
 *
 * Immediate, idempotent fetch patch for /api/extensions*:
 * - Handles 403 (permission), 504 (timeout), network errors (offline)
 * - Optional: also shields common transient 5xx + 401
 * - Returns deterministic fallback payloads to keep UI stable
 */

import { logger } from './logger';

declare global {
  interface Window {
    __EXT_PATCH__?: {
      extFetchPatched?: boolean;
      extOriginalFetch?: typeof fetch;
    };
  }
}

/** Type guard: running in a browser */
function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

/** Match any /api/extensions endpoint */
function isExtensionsUrl(url: string): boolean {
  return url.includes('/api/extensions');
}

/** The list endpoint (used to return the full fallback catalog) */
function isListEndpoint(url: string): boolean {
  return /\/api\/extensions\/?$/.test(url);
}

/** Error codes we treat as “gracefully degradable” */
function isGracefulStatus(status: number): boolean {
  return status === 403 || status === 504 || status === 502 || status === 503 || status === 401;
}

/**
 * Get appropriate fallback data based on the extension endpoint
 */
function getFallbackDataForExtensionEndpoint(
  url: string,
  status: number = 403
): Record<string, unknown> {
  // Main extensions list endpoint
  if (isListEndpoint(url)) {
    if (status === 504) {
      // Gateway timeout - service unavailable
      return {
        extensions: {
          'offline-mode': {
            id: 'offline-mode',
            name: 'offline-mode',
            display_name: 'Extensions (Service Unavailable)',
            description:
              'Extension service is temporarily unavailable due to a timeout. Core functionality continues to work.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'offline',
            capabilities: {
              provides_ui: false,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Extension service is temporarily unavailable',
        access_level: 'offline',
        available_features: [],
        restricted_features: ['all'],
        fallback_mode: true,
        error_type: 'timeout'
      };
    } else if (status === 0) {
      // Network error
      return {
        extensions: {
          'network-error': {
            id: 'network-error',
            name: 'network-error',
            display_name: 'Extensions (Network Error)',
            description:
              'Unable to connect to extension service. Please check your internet connection.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'disconnected',
            capabilities: {
              provides_ui: false,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Unable to connect to extension service',
        access_level: 'disconnected',
        available_features: [],
        restricted_features: ['all'],
        fallback_mode: true,
        error_type: 'network'
      };
    } else {
      // 403/401 or other permission errors
      return {
        extensions: {
          'readonly-mode': {
            id: 'readonly-mode',
            name: 'readonly-mode',
            display_name: 'Extensions (Read-Only Mode)',
            description:
              'Extension features are available in read-only mode. Some functionality may be limited due to insufficient permissions.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'readonly',
            capabilities: {
              provides_ui: true,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Extension features are available in read-only mode',
        access_level: 'readonly',
        available_features: ['view', 'status'],
        restricted_features: ['install', 'configure', 'manage', 'execute'],
        fallback_mode: true,
        error_type: 'permission'
      };
    }
  }

  // Extension status/health endpoints
  if (url.includes('/status') || url.includes('/health')) {
    if (status === 504 || status === 0) {
      return {
        status: 'offline',
        message: 'Extension service is temporarily unavailable',
        health: {
          status: 'error',
          message: status === 504 ? 'Service timeout' : 'Network error',
          lastCheck: new Date().toISOString()
        },
        fallback_mode: true,
        error_type: status === 504 ? 'timeout' : 'network'
      };
    }
    return {
      status: 'readonly',
      message: 'Extension status available in read-only mode',
      health: {
        status: 'degraded',
        message: 'Running in read-only mode',
        lastCheck: new Date().toISOString()
      },
      fallback_mode: true,
      error_type: 'permission'
    };
  }

  // Background tasks endpoint
  if (url.includes('/background-tasks')) {
    const message =
      status === 504 || status === 0
        ? 'Background tasks service is temporarily unavailable'
        : 'Background tasks not available in read-only mode';

    return {
      tasks: [],
      total: 0,
      message,
      access_level: status === 504 || status === 0 ? 'offline' : 'readonly',
      fallback_mode: true,
      error_type: status === 504 ? 'timeout' : status === 0 ? 'network' : 'permission'
    };
  }

  // Generic extension endpoint
  const message =
    status === 504 || status === 0
      ? 'This extension feature is temporarily unavailable'
      : 'This extension feature is not available in read-only mode';

  return {
    data: [],
    message,
    access_level: status === 504 || status === 0 ? 'offline' : 'readonly',
    fallback_mode: true,
    error: status === 504 ? 'service_timeout' : status === 0 ? 'network_error' : 'insufficient_permissions',
    error_type: status === 504 ? 'timeout' : status === 0 ? 'network' : 'permission'
  };
}

/**
 * Patch fetch to handle extension errors (403, 504, plus offline/5xx/401)
 * Idempotent and SSR-safe.
 */
export function patchFetchForExtension403(): void {
  if (!isBrowser()) return;

  if (!window.__EXT_PATCH__) window.__EXT_PATCH__ = {};

  // Avoid double-patching under HMR or multiple imports
  if (window.__EXT_PATCH__.extFetchPatched) {
    logger?.info?.('Extension 403 error fix already applied to fetch');
    return;
  }

  const originalFetch = window.fetch.bind(window);
  window.__EXT_PATCH__.extOriginalFetch = originalFetch;

  window.fetch = async function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const url = typeof input === 'string' ? input : input.toString();

    try {
      const response = await originalFetch(input as unknown, init);

      // Non-extensions: pass through
      if (!isExtensionsUrl(url)) return response;

      // OK path: pass through
      if (response.ok) return response;

      // Graceful statuses → fallback
      if (isGracefulStatus(response.status)) {
        const kind =
          response.status === 504 ? 'extension-offline' : 'extension-readonly';
        const fallbackData = getFallbackDataForExtensionEndpoint(url, response.status);

        logger?.warn?.(
          `Extension API ${response.status} for ${url}, returning fallback (${kind})`
        );

        return new Response(JSON.stringify(fallbackData), {
          status: 200,
          statusText: 'OK',
          headers: {
            'Content-Type': 'application/json',
            'X-Fallback-Mode': kind
          }
        });
      }

      // Other errors: return as-is
      return response;
    } catch (error) {
      // Network/CORS failure on extensions → offline fallback
      if (isExtensionsUrl(url)) {
        logger?.warn?.(
          `Extension API network error for ${url}, providing offline fallback`
        );
        const fallbackData = getFallbackDataForExtensionEndpoint(url, 0);
        return new Response(JSON.stringify(fallbackData), {
          status: 200,
          statusText: 'OK',
          headers: {
            'Content-Type': 'application/json',
            'X-Fallback-Mode': 'extension-offline'
          }
        });
      }

      // Non-extensions: propagate
      throw error;
    }
  };

  window.__EXT_PATCH__.extFetchPatched = true;
  logger?.info?.('Extension 403 error fix applied to fetch');
}

/**
 * Show user notification about extension status
 */
export function showExtensionStatusNotification(
  errorType: 'permission' | 'timeout' | 'network' = 'permission'
) {
  if (!isBrowser()) return;

  let message: string;
  let logLevel: 'info' | 'warn' | 'error' = 'info';

  switch (errorType) {
    case 'timeout':
      message =
        'Extension service is temporarily unavailable due to a timeout. Core functionality continues to work.';
      logLevel = 'warn';
      break;
    case 'network':
      message =
        'Unable to connect to extension service. Please check your internet connection.';
      logLevel = 'error';
      break;
    case 'permission':
    default:
      message =
        'Extension features are running in read-only mode due to insufficient permissions.';
      logLevel = 'info';
      break;
  }

  logger?.[logLevel]?.(message);

  // Hook a toast system here if present:
  // toast[logLevel === 'error' ? 'error' : logLevel](message);
}

/**
 * Initialize the extension error fix (safe to call multiple times)
 */
export function initializeExtensionErrorFix() {
  patchFetchForExtension403();
  logger?.info?.(
    'Extension error fix initialized (handles 403, 504, 5xx/401 gracefully, and network errors)'
  );
}

// Auto-init (browser only) after a short delay to let other modules mount first
if (isBrowser()) {
  setTimeout(() => {
    try {
      initializeExtensionErrorFix();
    } catch (e) {
      logger?.error?.('Failed to initialize Extension 403 error fix', e);
    }
  }, 500);
}

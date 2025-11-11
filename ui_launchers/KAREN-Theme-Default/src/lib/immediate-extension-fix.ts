/**
 * immediate-extension-fix.ts
 *
 * Ultra-early, idempotent fetch patch for /api/extensions* calls.
 * - Handles 401/403/502/503/504 and network failures
 * - Returns deterministic read-only fallback payloads
 * - Safe in SSR, safe under HMR, reversible via window.__KAREN_BACKEND_PATCH__
 */

import type { KarenBackendPatchState } from './karen-backend-direct-patch';

declare global {
  interface Window {
    __KAREN_BACKEND_PATCH__?: KarenBackendPatchState;
  }
}

export type FallbackList = {
  extensions: Record<string, unknown>;
  total: number;
  message: string;
  access_level: 'readonly';
  available_features: string[];
  restricted_features: string[];
  fallback_mode: true;
};

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

function isExtensionsUrl(url: string): boolean {
  return url.includes('/api/extensions');
}

function isListEndpoint(url: string): boolean {
  return /\/api\/extensions\/?$/.test(url);
}

function shouldFallbackStatus(status: number): boolean {
  return status === 401 || status === 403 || status === 502 || status === 503 || status === 504;
}

const READONLY_LIST_FALLBACK: FallbackList = {
  extensions: {
    'readonly-mode': {
      id: 'readonly-mode',
      name: 'readonly-mode',
      display_name: 'Extensions (Read-Only Mode)',
      description:
        'Extension features are available in read-only mode due to insufficient permissions or service unavailability.',
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
  fallback_mode: true
} as const;

function jsonResponse(data: unknown, status = 200, headers?: Record<string, string>): Response {
  return new Response(JSON.stringify(data), {
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: { 'Content-Type': 'application/json', ...(headers ?? {}) }
  });
}

function fallbackResponseForUrl(url: string, modeHeader: string): Response {
  if (isListEndpoint(url)) {
    return jsonResponse(READONLY_LIST_FALLBACK, 200, { 'X-Fallback-Mode': modeHeader });
  }
  return jsonResponse(
    {
      data: [],
      message: 'Extension feature not available in read-only/offline mode',
      fallback_mode: true
    },
    200,
    { 'X-Fallback-Mode': modeHeader }
  );
}

// ---- Ultra-early, idempotent patch ----
if (isBrowser()) {
  if (!window.__KAREN_BACKEND_PATCH__) window.__KAREN_BACKEND_PATCH__ = {};

  if (!window.__KAREN_BACKEND_PATCH__.earlyFetchPatched) {
    const originalFetch = window.fetch.bind(window);
    window.__KAREN_BACKEND_PATCH__.earlyOriginalFetch = originalFetch;

    window.fetch = async function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
      const url = typeof input === 'string' ? input : input.toString();

      try {
        const res = await originalFetch(input as unknown, init);

        if (!isExtensionsUrl(url)) return res; // not our concern
        if (res.ok) return res; // happy path

        if (shouldFallbackStatus(res.status)) {
          // Immediate graceful degradation
          return fallbackResponseForUrl(url, 'extension-readonly');
        }

        return res; // other errors pass through
      } catch (_err) {
        // Network/CORS failure for extensions → offline fallback
        if (isExtensionsUrl(url)) {
          return jsonResponse(
            {
              ...READONLY_LIST_FALLBACK,
              message: 'Extension service is temporarily unavailable',
              fallback_mode: true
            },
            200,
            { 'X-Fallback-Mode': 'extension-offline' }
          );
        }
        // Non-extensions network errors bubble up
        throw _err;
      }
    };

    window.__KAREN_BACKEND_PATCH__.earlyFetchPatched = true;
    // (Optional) minimal console breadcrumb; keep silent if you prefer
    // console.info('[ImmediateExtensionFix] Early fetch patched for /api/extensions');
  }
}

export {}; // Keep this file a module

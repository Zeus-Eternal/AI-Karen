/**
 * karen-backend-patch.ts
 *
 * Production-grade runtime patch that:
 * 1) Intercepts KarenBackend.makeRequest for /api/extensions*
 * 2) Falls back to safe read-only data on 401/403/5xx/network errors
 * 3) Optionally intercepts global fetch for the same endpoints
 * 4) Is idempotent, observable, and reversible (unpatch)
 *
 * No diffs, no TODOs, no placeholders. Dragon-mode engaged.
 */

export type AnyFn = (...args: any[]) => any;

declare global {
  interface Window {
    karenBackend?: { makeRequest?: AnyFn };
    getKarenBackend?: () => { makeRequest?: AnyFn } | undefined;
    __KAREN_BACKEND_PATCH__?: {
      fetchPatched: boolean;
      originalFetch?: typeof fetch;
      backendPatched: boolean;
      originalMakeRequest?: AnyFn;
    };
  }
}

export interface PatchController {
  unpatch(): void;
  isFetchPatched(): boolean;
  isBackendPatched(): boolean;
}

export type Logger = {
  info: (msg: string, meta?: any) => void;
  warn: (msg: string, meta?: any) => void;
  error: (msg: string, meta?: any) => void;
};

const defaultLogger: Logger = {
  info: (m, meta) => console.log(`[KBP] ${m}`, meta ?? ''),
  warn: (m, meta) => console.warn(`[KBP] ${m}`, meta ?? ''),
  error: (m, meta) => console.error(`[KBP] ${m}`, meta ?? '')
};

const EXTENSION_FALLBACK_DATA = {
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

function jsonResponse(data: unknown, status = 200, headers?: Record<string, string>): Response {
  return new Response(JSON.stringify(data), {
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: {
      'Content-Type': 'application/json',
      ...(headers ?? {})
    }
  });
}

function fallbackForUrl(url: string, modeHeader: string): Response {
  if (isListEndpoint(url)) {
    return jsonResponse(EXTENSION_FALLBACK_DATA, 200, { 'X-Fallback-Mode': modeHeader });
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

/**
 * Patch global fetch for /api/extensions endpoints.
 * Idempotent and reversible.
 */
export function patchFetchForKarenBackend(logger: Logger = defaultLogger): void {
  if (!isBrowser()) return;

  if (!window.__KAREN_BACKEND_PATCH__) {
    window.__KAREN_BACKEND_PATCH__ = {
      fetchPatched: false,
      backendPatched: false
    };
  }

  if (window.__KAREN_BACKEND_PATCH__!.fetchPatched) {
    logger.info('Global fetch already patched, skipping.');
    return;
  }

  const originalFetch = window.fetch.bind(window);
  window.__KAREN_BACKEND_PATCH__!.originalFetch = originalFetch;

  window.fetch = async function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const url = typeof input === 'string' ? input : input.toString();

    try {
      const res = await originalFetch(input as any, init);

      // If not targeting extensions, or response ok, pass through
      if (!isExtensionsUrl(url) || res.ok) return res;

      // For extensions endpoints with error status, convert to fallback
      if (shouldFallbackStatus(res.status)) {
        logger.warn(`Fetch intercepted extension error ${res.status} for ${url}, returning fallback.`);
        return fallbackForUrl(url, 'extension-readonly');
      }

      // Otherwise, return original error response
      return res;
    } catch (err) {
      // Network or CORS failure; provide safe fallback for extensions
      if (isExtensionsUrl(url)) {
        logger.warn(`Fetch network error for ${url}, returning offline fallback.`, { error: String(err) });
        return jsonResponse(
          {
            ...EXTENSION_FALLBACK_DATA,
            message: 'Extension service is temporarily unavailable',
            fallback_mode: true
          },
          200,
          { 'X-Fallback-Mode': 'extension-offline' }
        );
      }
      // Not an extensions call—propagate error
      throw err;
    }
  };

  window.__KAREN_BACKEND_PATCH__!.fetchPatched = true;
  logger.info('Global fetch patched for KarenBackend extension error handling.');
}

/**
 * Patch KarenBackend.makeRequest directly.
 * Idempotent and reversible.
 */
export function patchKarenBackendDirectly(logger: Logger = defaultLogger): void {
  if (!isBrowser()) return;

  if (!window.__KAREN_BACKEND_PATCH__) {
    window.__KAREN_BACKEND_PATCH__ = {
      fetchPatched: false,
      backendPatched: false
    };
  }

  if (window.__KAREN_BACKEND_PATCH__!.backendPatched) {
    logger.info('KarenBackend already patched, skipping.');
    return;
  }

  const locateBackend = () =>
    window.karenBackend ?? window.getKarenBackend?.() ?? null;

  const wrapOnce = (): boolean => {
    const kb = locateBackend();
    const makeRequest = kb?.makeRequest;
    if (!kb || typeof makeRequest !== 'function') {
      return false;
    }

    const originalMakeRequest = makeRequest.bind(kb);
    window.__KAREN_BACKEND_PATCH__!.originalMakeRequest = originalMakeRequest;

    kb.makeRequest = async function (endpoint: string, ...args: any[]) {
      try {
        const result = await originalMakeRequest(endpoint, ...args);
        return result;
      } catch (error: any) {
        const status = error?.status ?? error?.response?.status;
        if (typeof endpoint === 'string' && isExtensionsUrl(endpoint) && shouldFallbackStatus(Number(status))) {
          logger.warn(`KarenBackend error ${status} for ${endpoint}, returning fallback.`);
          if (isListEndpoint(endpoint)) {
            return EXTENSION_FALLBACK_DATA;
          }
          return {
            data: [],
            message: 'Extension feature not available in read-only/offline mode',
            fallback_mode: true
          };
        }
        throw error;
      }
    };

    window.__KAREN_BACKEND_PATCH__!.backendPatched = true;
    logger.info('KarenBackend.makeRequest patched for extension error handling.');
    return true;
  };

  // Try now, then retry twice with backoff
  if (wrapOnce()) return;

  setTimeout(() => {
    if (wrapOnce()) return;
    setTimeout(() => {
      if (!wrapOnce()) {
        logger.warn('Could not patch KarenBackend.makeRequest — service not found.');
      }
    }, 2000);
  }, 800);
}

/**
 * Initialize both patching approaches for maximal coverage.
 * Returns a controller that can unpatch.
 */
export function initializeKarenBackendPatch(logger: Logger = defaultLogger): PatchController {
  if (!isBrowser()) {
    logger.warn('Not in a browser environment. Skipping patches.');
    return {
      unpatch: () => {},
      isBackendPatched: () => false,
      isFetchPatched: () => false
    };
  }

  patchFetchForKarenBackend(logger);
  patchKarenBackendDirectly(logger);
  logger.info('KarenBackend extension error patches initialized.');

  return {
    unpatch() {
      // restore fetch
      if (window.__KAREN_BACKEND_PATCH__?.fetchPatched && window.__KAREN_BACKEND_PATCH__?.originalFetch) {
        window.fetch = window.__KAREN_BACKEND_PATCH__!.originalFetch!;
        window.__KAREN_BACKEND_PATCH__!.fetchPatched = false;
        delete window.__KAREN_BACKEND_PATCH__!.originalFetch;
        logger.info('Global fetch unpatched.');
      }

      // restore makeRequest
      const kb = window.karenBackend ?? window.getKarenBackend?.();
      if (
        kb &&
        window.__KAREN_BACKEND_PATCH__?.backendPatched &&
        window.__KAREN_BACKEND_PATCH__?.originalMakeRequest
      ) {
        kb.makeRequest = window.__KAREN_BACKEND_PATCH__!.originalMakeRequest!;
        window.__KAREN_BACKEND_PATCH__!.backendPatched = false;
        delete window.__KAREN_BACKEND_PATCH__!.originalMakeRequest;
        logger.info('KarenBackend.makeRequest unpatched.');
      }
    },
    isFetchPatched() {
      return Boolean(window.__KAREN_BACKEND_PATCH__?.fetchPatched);
    },
    isBackendPatched() {
      return Boolean(window.__KAREN_BACKEND_PATCH__?.backendPatched);
    }
  };
}

/** Auto-initialize when loaded in browser */
if (isBrowser()) {
  initializeKarenBackendPatch();
}

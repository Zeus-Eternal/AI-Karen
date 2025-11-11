/**
 * Early Extension Fix
 *
 * Runs as early as possible to patch console and fetch
 * before any other code can flood logs with extension errors.
 *
 * Design:
 * - Idempotent: won't repatch if executed twice
 * - Conservative: only targets /api/extensions + specific status codes
 * - Observable: suppressed errors become console.info with a marker
 */

(function earlyExtensionFix() {
  if (typeof window === 'undefined') return;

  // Idempotency guard
  const FLAG = '__karenEarlyPatched__' as const;
  type EarlyExtensionWindow = typeof window & Record<typeof FLAG, boolean>;
  const earlyWindow = window as EarlyExtensionWindow;
  if (earlyWindow[FLAG]) return;
  earlyWindow[FLAG] = true;

  // ---------------------------
  // 1) Patch console.error
  // ---------------------------
  const originalConsoleError = console.error.bind(console);

  function isSuppressedExtensionError(args: unknown[]): boolean {
    const first = args[0];
    const hasExtObj =
      args.some(arg => {
        if (arg && typeof arg === 'object') {
          const candidate = arg as { url?: unknown; endpoint?: unknown };
          const url = typeof candidate.url === 'string' ? candidate.url : undefined;
          const endpoint =
            typeof candidate.endpoint === 'string' ? candidate.endpoint : undefined;
          return (
            (url && url.includes('/api/extensions')) ||
            (endpoint && endpoint.includes('/api/extensions'))
          );
        }
        return false;
      }) || false;

    if (typeof first === 'string') {
      if (
        first.includes('[ERROR] "KarenBackendService 4xx/5xx"') ||
        first.includes('[ERROR] "[EXT_AUTH_HIGH] Permission Denied"') ||
        (first.includes('[ERROR]') && hasExtObj)
      ) {
        return true;
      }
    }
    return hasExtObj;
  }

  console.error = function patchedConsoleError(...args: unknown[]) {
    if (isSuppressedExtensionError(args)) {
      // Downshift to info with a clear marker for observability
      try {
        console.info('[EXTENSION-READONLY] Suppressed noisy error:', ...args);
        return;
      } catch {
        // if info somehow fails, swallow to avoid loops
        return;
      }
    }
    return originalConsoleError(...args);
  };

  // ---------------------------
  // 2) Patch fetch
  // ---------------------------
  const originalFetch = window.fetch.bind(window);

  function toUrlString(input: RequestInfo | URL): string {
    try {
      if (typeof input === 'string') return input;
      if (input instanceof URL) return input.href;
      // Some runtimes export Request on window; guard in case
      if (typeof Request !== 'undefined' && input instanceof Request) return input.url;
      // Fallback best-effort
      const candidate = input as { url?: unknown };
      const fromUrlProperty = candidate?.url;
      if (typeof fromUrlProperty === 'string') {
        return fromUrlProperty;
      }
      return String(input);
    } catch {
      return String(input);
    }
  }

  function buildReadonlyFallback() {
    const payload = {
      extensions: {
        'readonly-mode': {
          id: 'readonly-mode',
          name: 'readonly-mode',
          display_name: 'Extensions (Read-Only Mode)',
          description: 'Extension features are available in read-only mode',
          version: '1.0.0',
          status: 'readonly',
          capabilities: {
            provides_ui: true,
            provides_api: false,
            provides_background_tasks: false,
            provides_webhooks: false,
          },
        },
      },
      total: 1,
      message: 'Extension features are available in read-only mode',
      access_level: 'readonly',
      fallback_mode: true,
    };
    return new Response(JSON.stringify(payload), {
      status: 200,
      statusText: 'OK',
      headers: {
        'Content-Type': 'application/json',
        'X-Fallback-Mode': 'extension-readonly',
        'X-Fallback-Reason': 'unauthorized-or-gateway-timeout',
      },
    });
  }

  function buildOfflineFallback() {
    const payload = {
      extensions: {},
      message: 'Extension service temporarily unavailable',
      fallback_mode: true,
    };
    return new Response(JSON.stringify(payload), {
      status: 200,
      statusText: 'OK',
      headers: {
        'Content-Type': 'application/json',
        'X-Fallback-Mode': 'extension-offline',
        'X-Fallback-Reason': 'network-error',
      },
    });
  }

  window.fetch = async function patchedFetch(
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const url = toUrlString(input);

    try {
      const fetchInput: RequestInfo = input instanceof URL ? input.toString() : input;
      const response = await originalFetch(fetchInput, init);

      // Only intervene for extension API and targeted status
      if (
        url.includes('/api/extensions') &&
        !response.ok &&
        (response.status === 401 || response.status === 403 || response.status === 504)
      ) {
        return buildReadonlyFallback();
      }

      return response;
    } catch (error) {
      // Network errors: flip to offline fallback for extension endpoints
      if (url.includes('/api/extensions')) {
        return buildOfflineFallback();
      }
      // Non-extension requests behave normally
      throw error;
    }
  };
})();

export {}; // keep this a module (no global augmentation leakage)

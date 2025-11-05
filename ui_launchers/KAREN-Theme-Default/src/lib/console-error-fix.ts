/**
 * Console Error Fix - Prevents Next.js console interceptor issues
 * - Idempotent (safe to import multiple times)
 * - Preserves original console bindings
 * - Filters known interceptor stacks/messages
 * - Adds global handlers for error & unhandledrejection
 */

let isInitialized = false;

function isInterceptorSignature(msgOrStack: unknown): boolean {
  if (!msgOrStack) return false;
  const s = typeof msgOrStack === 'string' ? msgOrStack : String((msgOrStack as any) ?? '');
  return (
    s.includes('console-error.js') ||
    s.includes('use-error-handler.js') ||
    s.includes('intercept-console-error.js')
  );
}

export function initializeConsoleErrorFix(): void {
  if (isInitialized || typeof window === 'undefined') return;
  isInitialized = true;

  // Store original console methods with bound context
  const originalConsoleError = console.error.bind(console);
  const originalConsoleWarn = console.warn.bind(console);

  // ---------------------------
  // Override console.error
  // ---------------------------
  console.error = function patchedConsoleError(...args: any[]) {
    try {
      const first = args[0];
      const msg = typeof first === 'string' ? first : first?.toString?.() ?? '';

      // Known noisy paths or specific component signatures
      if (
        isInterceptorSignature(msg) ||
        (typeof msg === 'string' && msg.includes('ChatInterface') && msg.includes('sendMessage')) ||
        // also check nested error objects for stack signatures
        args.some((a) => isInterceptorSignature((a as any)?.stack))
      ) {
        // Downshift with a safety marker, but do not rethrow
        originalConsoleError('[SAFE]', ...args);
        return;
      }

      // Default path
      originalConsoleError(...args);
    } catch {
      // Final fallback
      originalConsoleError(...args);
    }
  };

  // ---------------------------
  // Override console.warn
  // ---------------------------
  console.warn = function patchedConsoleWarn(...args: any[]) {
    try {
      const first = args[0];
      const msg = typeof first === 'string' ? first : first?.toString?.() ?? '';

      if (isInterceptorSignature(msg) || args.some((a) => isInterceptorSignature((a as any)?.stack))) {
        originalConsoleWarn('[SAFE]', ...args);
        return;
      }

      originalConsoleWarn(...args);
    } catch {
      originalConsoleWarn(...args);
    }
  };

  // ---------------------------
  // Global error handler
  // ---------------------------
  window.addEventListener(
    'error',
    (event: ErrorEvent) => {
      try {
        const stk = (event?.error as any)?.stack || '';
        if (isInterceptorSignature(stk)) {
          event.preventDefault();
          event.stopPropagation?.();
          (event as any).stopImmediatePropagation?.();

          originalConsoleError('[SAFE] Prevented console interceptor error:', {
            message: event?.error?.message ?? event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: (event?.error as any)?.stack,
          });
        }
      } catch (e) {
        originalConsoleError('[SAFE] Error in window.onerror filter:', e);
      }
    },
    true // capture early
  );

  // ---------------------------
  // Global unhandled promise rejection handler
  // ---------------------------
  window.addEventListener(
    'unhandledrejection',
    (event: PromiseRejectionEvent) => {
      try {
        const reason: any = event.reason;
        const msg = reason?.message ?? String(reason ?? '');
        const stk = reason?.stack ?? '';

        if (isInterceptorSignature(stk) || isInterceptorSignature(msg)) {
          event.preventDefault?.();

          originalConsoleError('[SAFE] Prevented console interceptor promise rejection:', {
            reason: msg,
            stack: stk,
          });
        }
      } catch (e) {
        originalConsoleError('[SAFE] Error in unhandledrejection filter:', e);
      }
    },
    true
  );
}

// Auto-initialize in browser environment (after DOM ready)
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initializeConsoleErrorFix());
  } else {
    initializeConsoleErrorFix();
  }
}

export default initializeConsoleErrorFix;

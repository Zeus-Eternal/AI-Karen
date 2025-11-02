/**
 * Console Error Fix - Prevents Next.js console interceptor issues
 */
let isInitialized = false;
export function initializeConsoleErrorFix() {
  if (isInitialized || typeof window === 'undefined') {
    return;
  }
  isInitialized = true;
  // Store original console methods
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;
  // Override console.error to prevent interceptor issues
  console.error = function(...args: any[]) {
    try {
      // Check if this is a Next.js console interceptor error
      const errorMessage = args[0]?.toString() || '';
      // Skip problematic console errors that cause interceptor issues
      if (
        errorMessage.includes('console-error.js') ||
        errorMessage.includes('use-error-handler.js') ||
        errorMessage.includes('intercept-console-error.js') ||
        (errorMessage.includes('ChatInterface') && errorMessage.includes('sendMessage'))
      ) {
        // Log to original console instead
        originalConsoleError.apply(console, ['[SAFE]', ...args]);
        return;
      }
      // For all other errors, use original console.error
      originalConsoleError.apply(console, args);
    } catch (e) {
      // Fallback to original console if anything goes wrong
      originalConsoleError.apply(console, args);
    }
  };
  // Override console.warn for similar issues
  console.warn = function(...args: any[]) {
    try {
      const warnMessage = args[0]?.toString() || '';
      // Skip problematic console warnings
      if (
        warnMessage.includes('console-error.js') ||
        warnMessage.includes('use-error-handler.js') ||
        warnMessage.includes('intercept-console-error.js')
      ) {
        originalConsoleWarn.apply(console, ['[SAFE]', ...args]);
        return;
      }
      originalConsoleWarn.apply(console, args);
    } catch (e) {
      originalConsoleWarn.apply(console, args);
    }
  };
  // Add global error handler to catch unhandled errors
  window.addEventListener('error', (event) => {
    // Prevent Next.js console interceptor errors from propagating
    if (
      event.error?.stack?.includes('console-error.js') ||
      event.error?.stack?.includes('use-error-handler.js') ||
      event.error?.stack?.includes('intercept-console-error.js')
    ) {
      event.preventDefault();
      event.stopPropagation();
      // Log safely instead
      originalConsoleError('[SAFE] Prevented console interceptor error:', {
        message: event.error?.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,

      return false;
    }

  // Add unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason;
    // Check if this is related to console interceptor
    if (
      reason?.stack?.includes('console-error.js') ||
      reason?.stack?.includes('use-error-handler.js') ||
      reason?.stack?.includes('intercept-console-error.js')
    ) {
      event.preventDefault();
      // Log safely instead
      originalConsoleError('[SAFE] Prevented console interceptor promise rejection:', {
        reason: reason?.message || reason,
        stack: reason?.stack,

    }

}
// Auto-initialize in browser environment
if (typeof window !== 'undefined') {
  // Initialize after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeConsoleErrorFix);
  } else {
    initializeConsoleErrorFix();
  }
}

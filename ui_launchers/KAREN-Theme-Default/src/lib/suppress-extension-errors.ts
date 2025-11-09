/**
 * Suppress Extension Error Logs
 * 
 * This patches the logger to suppress extension-related error logs
 * that are expected and handled gracefully.
 */
import { logger } from './logger';
/**
 * Patch the logger to suppress extension error logs
 */
export function suppressExtensionErrorLogs() {
  if (typeof window === 'undefined') return;
  // Store original logger methods
  const originalError = logger.error;
  const originalWarn = logger.warn;
  // Patch logger.error to suppress extension-related errors
  logger.error = function(message: string, meta?: any, options?: any) {
    // Check if this is an extension-related error that should be suppressed
    if (typeof message === 'string') {
      const isExtensionError = 
        message.includes('KarenBackendService 4xx/5xx') ||
        message.includes('[EXT_AUTH_HIGH]') ||
        message.includes('Permission Denied') ||
        message.includes('extension') ||
        message.includes('Extension');
      // Check if the meta contains extension-related URLs
      const isExtensionUrl = meta && 
        (meta.url?.includes('/api/extensions') || 
         meta.endpoint?.includes('/api/extensions'));
      // Suppress if it's an extension error with 403 or 401 status
      if ((isExtensionError || isExtensionUrl) && meta && 
          (meta.status === 403 || meta.status === 401)) {
        // Convert to info log instead of error
        logger.info(`[EXTENSION-HANDLED] ${message}`, meta);
        return;
      }
    }
    // Call original error method for non-extension errors
    originalError.call(this, message, meta, options);
  };
  // Patch logger.warn for extension warnings
  logger.warn = function(message: string, meta?: any, options?: any) {
    // Check if this is an extension-related warning
    if (typeof message === 'string') {
      const isExtensionWarning = 
        message.includes('extension') ||
        message.includes('Extension') ||
        message.includes('auth recovery') ||
        message.includes('fallback');
      // Check if the meta contains extension-related URLs
      const isExtensionUrl = meta && 
        (meta.url?.includes('/api/extensions') || 
         meta.endpoint?.includes('/api/extensions'));
      // Convert extension warnings to debug logs
      if (isExtensionWarning || isExtensionUrl) {
        logger.debug(`[EXTENSION-DEBUG] ${message}`, meta);
        return;
      }
    }
    // Call original warn method for non-extension warnings
    originalWarn.call(this, message, meta, options);
  };
}
/**
 * Patch console.error to suppress specific extension errors
 */
export function suppressConsoleExtensionErrors() {
  if (typeof window === 'undefined') return;
  const originalConsoleError = console.error;
  console.error = function(...args: any[]) {
    // Check if this is an extension-related error
    const message = args[0];
    if (typeof message === 'string') {
      const isExtensionError = 
        message.includes('[ERROR] "KarenBackendService 4xx/5xx"') ||
        message.includes('[ERROR] "[EXT_AUTH_HIGH] Permission Denied"') ||
        message.includes('api/extensions');
      // Check if any of the arguments contain extension URLs
      const hasExtensionUrl = args.some(arg => 
        typeof arg === 'object' && arg && 
        (arg.url?.includes('/api/extensions') || 
         arg.endpoint?.includes('/api/extensions'))
      );
      // Suppress extension errors with 403/401 status
      if (isExtensionError || hasExtensionUrl) {
        const statusArg = args.find(arg => 
          typeof arg === 'object' && arg && 
          (arg.status === 403 || arg.status === 401)
        );
        if (statusArg) {
          // Convert to info log
          return;
        }
      }
    }
    // Call original console.error for other errors
    originalConsoleError.apply(console, args);
  };
}
/**
 * Initialize all error suppression
 */
export function initializeExtensionErrorSuppression() {
  suppressExtensionErrorLogs();
  suppressConsoleExtensionErrors();
}
// Auto-initialize immediately
if (typeof window !== 'undefined') {
  initializeExtensionErrorSuppression();
}

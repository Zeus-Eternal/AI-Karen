/**
 * Suppress Extension Error Logs
 * 
 * This patches the logger to suppress extension-related error logs
 * that are expected and handled gracefully.
 */
import { logger } from './logger';

type ExtensionMeta = {
  url?: string;
  endpoint?: string;
  status?: number;
};

const isExtensionMetaObject = (value: unknown): value is ExtensionMeta =>
  Boolean(value && typeof value === 'object' && ('url' in (value as Record<string, unknown>) || 'endpoint' in (value as Record<string, unknown>) || 'status' in (value as Record<string, unknown>)));

const containsExtensionUrl = (meta?: ExtensionMeta): boolean =>
  Boolean(
    meta &&
      ((typeof meta.url === 'string' && meta.url.includes('/api/extensions')) ||
        (typeof meta.endpoint === 'string' && meta.endpoint.includes('/api/extensions')))
  );

const isExtensionMessage = (message: string) =>
  ['KarenBackendService 4xx/5xx', '[EXT_AUTH_HIGH]', 'Permission Denied', 'extension', 'Extension', 'auth recovery', 'fallback'].some((indicator) =>
    message.includes(indicator)
  );

/**
 * Patch the logger to suppress extension error logs
 */
export function suppressExtensionErrorLogs() {
  if (typeof window === 'undefined') return;
  const originalError = logger.error;
  const originalWarn = logger.warn;

  logger.error = function (message: string, meta?: ExtensionMeta, options?: unknown) {
    if (typeof message === 'string') {
      const isExtensionError = isExtensionMessage(message);
      const isExtensionUrl = containsExtensionUrl(meta);
      if ((isExtensionError || isExtensionUrl) && meta && (meta.status === 403 || meta.status === 401)) {
        logger.info(`[EXTENSION-HANDLED] ${message}`, meta);
        return;
      }
    }
    originalError.call(this, message, meta, options);
  };

  logger.warn = function (message: string, meta?: ExtensionMeta, options?: unknown) {
    if (typeof message === 'string') {
      const isExtensionWarning = isExtensionMessage(message);
      const isExtensionUrl = containsExtensionUrl(meta);
      if (isExtensionWarning || isExtensionUrl) {
        logger.debug(`[EXTENSION-DEBUG] ${message}`, meta);
        return;
      }
    }
    originalWarn.call(this, message, meta, options);
  };
}

/**
 * Patch console.error to suppress specific extension errors
 */
export function suppressConsoleExtensionErrors() {
  if (typeof window === 'undefined') return;
  const originalConsoleError = console.error;

  console.error = function (...args: unknown[]) {
    const message = args[0];
    if (typeof message === 'string') {
      const isExtensionError =
        message.includes('[ERROR] "KarenBackendService 4xx/5xx"') ||
        message.includes('[ERROR] "[EXT_AUTH_HIGH] Permission Denied"') ||
        message.includes('api/extensions');

      const hasExtensionUrlArg = args.some((arg) => isExtensionMetaObject(arg) && containsExtensionUrl(arg));
      if (isExtensionError || hasExtensionUrlArg) {
        const statusArg = args.find(
          (arg) => isExtensionMetaObject(arg) && (arg.status === 403 || arg.status === 401)
        );
        if (statusArg) {
          return;
        }
      }
    }
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

if (typeof window !== 'undefined') {
  initializeExtensionErrorSuppression();
}

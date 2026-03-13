import { webUIConfig } from './config';

// Simple gated logger that respects webUIConfig flags and provides
// optional rate-limiting for highly repetitive errors (e.g., 504 spikes).

const lastLogged: Map<string, number> = new Map();

function now() {
  return Date.now();
}

function shouldRateLimit(key: string, windowMs: number): boolean {
  if (!key) return false;
  const last = lastLogged.get(key) ?? 0;
  if (now() - last < windowMs) return true;
  lastLogged.set(key, now());
  return false;
}

export const logger = {
  debug: (...args: unknown[]) => {
    if (webUIConfig.debugLogging && process.env.NODE_ENV === 'development') {
      // prefer console.debug when available
      // eslint-disable-next-line no-console
      console.debug('[DEBUG]', ...args);
    }
  },
  info: (...args: unknown[]) => {
    if ((webUIConfig.requestLogging || webUIConfig.logLevel === 'info') && process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.info('[INFO]', ...args);
    }
  },
  warn: (...args: unknown[]) => {
    if (process.env.NODE_ENV === 'development') {
      // always show warnings in development, but keep them concise
      // eslint-disable-next-line no-console
      console.warn('[WARN]', ...args);
    }
  },
  error: (message: string, meta?: unknown, opts?: { rateLimitKey?: string; rateLimitMs?: number }) => {
    const key = opts?.rateLimitKey;
    const windowMs = opts?.rateLimitMs ?? 10000; // default 10s
    
    // Always log to error monitoring in production
    if (process.env.NODE_ENV === 'production' && typeof window !== 'undefined') {
      try {
        // Send to error monitoring service (implementation depends on your service)
        // Example: errorMonitoringService.captureError(message, meta);
      } catch (e) {
        // Fail silently to avoid infinite loops
      }
    }
    
    if (process.env.NODE_ENV === 'development') {
      if (key && shouldRateLimit(key, windowMs)) {
        // If rate-limited, drop full error noise and issue a concise notice
        // eslint-disable-next-line no-console
        console.warn('[RATE-LIMITED ERROR]', message, '(suppressed repetitive logs)');
        return;
      }
      const isMetaObject = meta && typeof meta === 'object' && Object.keys(meta).length === 0;
      if (meta !== undefined && !isMetaObject) {
        // eslint-disable-next-line no-console
        console.error('[ERROR]', message, meta);
      } else {
        // eslint-disable-next-line no-console
        console.error('[ERROR]', message);
      }
    }
  },
};

// Logger export
const Logger = logger;

export default Logger;

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
  debug: (...args: any[]) => {
    if (webUIConfig.debugLogging) {
      // prefer console.debug when available
      // eslint-disable-next-line no-console
      console.debug('[DEBUG]', ...args);
    }
  },
  info: (...args: any[]) => {
    if (webUIConfig.requestLogging || webUIConfig.logLevel === 'info') {
      // eslint-disable-next-line no-console
      console.info('[INFO]', ...args);
    }
  },
  warn: (...args: any[]) => {
    // always show warnings, but keep them concise
    // eslint-disable-next-line no-console
    console.warn('[WARN]', ...args);
  },
  error: (message: string, meta?: any, opts?: { rateLimitKey?: string; rateLimitMs?: number }) => {
    const key = opts?.rateLimitKey;
    const windowMs = opts?.rateLimitMs ?? 10000; // default 10s
    if (key && shouldRateLimit(key, windowMs)) {
      // If rate-limited, drop full error noise and issue a concise notice
      // eslint-disable-next-line no-console
      console.warn('[RATE-LIMITED ERROR]', message, '(suppressed repetitive logs)');
      return;
    }
    if (meta !== undefined) {
      // eslint-disable-next-line no-console
      console.error('[ERROR]', message, meta);
    } else {
      // eslint-disable-next-line no-console
      console.error('[ERROR]', message);
    }
  },
};

export default logger;

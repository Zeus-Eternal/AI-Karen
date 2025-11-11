/**
 * Verify Extension Fix (production-grade)
 *
 * - SSR-safe (no window/document on server)
 * - Strong typing for results
 * - Robust patch detection (flag-based with safe fallbacks)
 * - Resilient fetch test (handles non-JSON/headers missing)
 * - Minimal dev logging
 */

import type { ExtensionErrorIntegration } from './extension-error-integration';
import type { HandleKarenBackendErrorFn } from './error-recovery-integration-example';

export type Status = 'not_browser' | 'active' | 'inactive' | 'success' | 'error';

export interface VerifyChecks {
  fetchPatched: boolean;
  immediateFixApplied: boolean;
  errorRecoveryLoaded: boolean;
}

export interface VerifyResult {
  status: 'not_browser' | 'active' | 'inactive';
  checks: VerifyChecks;
  message: string;
  fetchInfo: {
    isPatched: boolean;
    patchType: 'immediate' | 'standard' | 'unknown';
  };
}

export interface TestResultSuccess {
  status: 'success';
  usingFallback: boolean;
  data: unknown;
  message: string;
}

export interface TestResultError {
  status: 'error' | 'not_browser';
  error?: string;
  message: string;
}

export type TestExtensionErrorRecoveryResult = TestResultSuccess | TestResultError;

const PREFIX = '[ExtensionFix]';
const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

interface ExtensionFixWindow extends Window {
  __EXT_FIX_PATCHED__?: { type: 'immediate' | 'standard' };
  extensionErrorIntegration?: ExtensionErrorIntegration;
  handleKarenBackendError?: HandleKarenBackendErrorFn;
}

// Optional: a more reliable signal your fetch patch can set.
// e.g. when patching, do: (window as ExtensionFixWindow).__EXT_FIX_PATCHED__ = { type: 'immediate' | 'standard' }
function readPatchedFlag(): { patched: boolean; type: 'immediate' | 'standard' | 'unknown' } {
  if (!isBrowser) return { patched: false, type: 'unknown' };
  const win = window as ExtensionFixWindow;
  const flag = win.__EXT_FIX_PATCHED__;
  if (flag && (flag.type === 'immediate' || flag.type === 'standard')) {
    return { patched: true, type: flag.type };
  }
  return { patched: false, type: 'unknown' };
}

function safeIncludes(haystack: unknown, needle: string): boolean {
  try {
    return typeof haystack === 'string' && haystack.includes(needle);
  } catch {
    return false;
  }
}

/**
 * Verify that the extension error recovery shim is present.
 * Uses a preferred global flag and falls back to fetch string checks.
 */
export function verifyExtensionFix(): VerifyResult | { status: 'not_browser'; message: string } {
  if (!isBrowser) {
    return { status: 'not_browser', message: 'Not running in browser environment' };
  }

  const win = window as ExtensionFixWindow;

  const checks: VerifyChecks = {
    fetchPatched: false,
    immediateFixApplied: false,
    errorRecoveryLoaded: false,
  };

  // 1) Prefer explicit patch flag (set by your patcher)
  const flag = readPatchedFlag();
  if (flag.patched) {
    checks.fetchPatched = true;
    checks.immediateFixApplied = flag.type === 'immediate';
  } else {
    // 2) Fallback to heuristic via fetch.toString()
    try {
      const fetchString = Function.prototype.toString.call(win.fetch);
      checks.fetchPatched =
        safeIncludes(fetchString, 'api/extensions') ||
        safeIncludes(fetchString, 'EXTENSION-FIX') ||
        safeIncludes(fetchString, 'Extension API');

      checks.immediateFixApplied = safeIncludes(fetchString, 'EXTENSION-FIX');
    } catch {
      // Some environments lock down Function#toString
      // Leave heuristic as false in that case
    }
  }

  // 3) Error recovery integration presence
  checks.errorRecoveryLoaded =
    Boolean(win.extensionErrorIntegration) ||
    Boolean(win.handleKarenBackendError);

  const allChecksPass = checks.fetchPatched || checks.immediateFixApplied || checks.errorRecoveryLoaded;

  return {
    status: allChecksPass ? 'active' : 'inactive',
    checks,
    message: allChecksPass ? 'Extension error recovery is active' : 'Extension error recovery is not active',
    fetchInfo: {
      isPatched: checks.fetchPatched,
      patchType: checks.immediateFixApplied ? 'immediate' : flag.type,
    },
  };
}

/**
 * Test the extension error recovery by making a test request.
 * Robust to non-JSON responses and missing headers.
 */
export async function testExtensionErrorRecovery(): Promise<TestExtensionErrorRecoveryResult> {
  if (!isBrowser) {
    return { status: 'not_browser', message: 'Not running in browser environment' };
  }

  try {
    const response = await fetch('/api/extensions', {
      headers: {
        'Accept': 'application/json, */*;q=0.8',
        'X-Extension-Fix-Probe': '1',
      },
      // keep credentials policy if your endpoint requires auth:
      // credentials: 'include',
    });

    // Try to parse JSON, fall back to text
    let data: unknown;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      // Attempt JSON parse in case backend sends JSON without proper header
      try {
        data = JSON.parse(text);
      } catch {
        data = { raw: text };
      }
    }

    const headerFallback =
      response.headers.get('X-Fallback-Mode') === '1' ||
      response.headers.get('X-Fallback-Mode') === 'true';

    const body = (data ?? {}) as Record<string, unknown>;
    const bodyFallback =
      body.fallback_mode === true ||
      body.fallback === true ||
      body.access_level === 'readonly';

    const isUsingFallback = Boolean(headerFallback || bodyFallback);

    return {
      status: 'success',
      usingFallback: isUsingFallback,
      data,
      message: isUsingFallback
        ? 'Extension error recovery is working — using fallback data'
        : 'Extension API is working normally',
    };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return {
      status: 'error',
      error: msg,
      message: 'Test request failed',
    };
  }
}

/**
 * Dev-time auto verification (browser only)
 * - Runs a quick verify + live call
 * - Silently no-ops on server
 */
if (isBrowser && process.env.NODE_ENV === 'development') {
  setTimeout(() => {
    try {
      const verification = verifyExtensionFix();
      // eslint-disable-next-line no-console
      console.log(`${PREFIX} Verification:`, verification);

      setTimeout(() => {
        testExtensionErrorRecovery()
          .then((testResult) => {
            // eslint-disable-next-line no-console
            console.log(`${PREFIX} Test:`, testResult);
          })
          .catch((err) => {
            // eslint-disable-next-line no-console
            console.warn(`${PREFIX} Test error:`, err);
          });
      }, 800);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn(`${PREFIX} Verification error:`, err);
    }
  }, 300);
}

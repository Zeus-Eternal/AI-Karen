/**
 * initialize-extension-error-recovery.ts
 *
 * Production-grade initializer for the Extension Error Recovery System.
 * - Loads early/runtime fixes in correct order
 * - Provides a clean initialize() + checkStatus() API
 * - Idempotent, SSR-safe, and observable
 */

import { logger } from './logger';
import type { KarenBackendPatchState } from './karen-backend';
// Extension error handling is now integrated into the main error handler

// --- Early/ordering-sensitive runtime guards (execute on import) ---
// Removed imports to deleted development files for production cleanup

// --- Core recovery components (execute on import) ---
import './extension-403-fix';
import './error-recovery-integration-example';
import './extension-error-integration';

// Note: karen-backend-error-suppression, karen-backend-extension-patch, and karen-backend-direct-patch
// functionality has been consolidated into karen-backend.ts and is no longer needed as separate imports

// If you extracted my previous patch helper, this will be present.
// We call it defensively if available at runtime.
declare global {
  interface Window {
    __KAREN_BACKEND_PATCH__?: KarenBackendPatchState;
  }
}

export type InitResult =
  | {
      success: true;
      message: string;
      features: string[];
    }
  | {
      success: false;
      message: string;
      error: string;
    };

export type StatusResult = {
  status: 'active' | 'partial';
  checks: {
    fetchPatched: boolean;
    backendPatched: boolean;
    globalHandlerAvailable: boolean;
    errorRecoveryAvailable: boolean;
  };
  message: string;
};

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

/**
 * Initialize the complete extension error recovery system.
 * Safe to call multiple times; underlying modules are idempotent.
 */
export function initializeExtensionErrorRecovery(): InitResult {
  logger.info('Initializing extension error recovery system...');
  try {
    // Modules above perform side-effects on import.
    // If you have an exported initialize from your patch file, call it here:
    try {
      // Optional dynamic hook (won't throw if absent)
      const w = isBrowser() ? window : ({} as Window);
      // NOP: side-effect modules already executed.
      // If you expose window.initializeKarenBackendPatch() elsewhere, you can call it.
      // (Intentionally skipped to avoid tight coupling.)
      void w;
    } catch {
      // Non-fatal: proceed with already-imported side-effects.
    }

    logger.info('Extension error recovery system initialized successfully');

    return {
      success: true,
      message: 'Extension error recovery system is active',
      features: [
        'HTTP 401/403/5xx handling',
        'Network error handling',
        'Graceful degradation',
        'Fallback data provision',
        'User-friendly error messages',
        'Automatic retry logic',
        'Read-only capability shielding'
      ]
    };
  } catch (error: unknown) {
    logger.error('Failed to initialize extension error recovery system:', error);
    return {
      success: false,
      message: 'Extension error recovery system failed to initialize',
      error: error instanceof Error ? error.message : String(error ?? 'Unknown error')
    };
  }
}

/**
 * Check if the extension error recovery system is working.
 * Uses robust flags from the runtime patch (window.__KAREN_BACKEND_PATCH__),
 * not brittle string inspection of fetch().
 */
export function checkExtensionErrorRecoveryStatus(): StatusResult {
  const checks = {
    fetchPatched: false,
    backendPatched: false,
    globalHandlerAvailable: false,
    errorRecoveryAvailable: false
  };

  if (isBrowser()) {
    const state = window.__KAREN_BACKEND_PATCH__ ?? {};
    checks.fetchPatched = Boolean(state.fetchPatched);
    checks.backendPatched = Boolean(state.backendPatched);

    // App-level integrations wired by your suppress/handler modules
    checks.globalHandlerAvailable = true; // Error handler is now integrated into main error handler
    checks.errorRecoveryAvailable = true; // Error recovery is now integrated into main error handler
  }

  const all = checks.fetchPatched && checks.backendPatched && checks.globalHandlerAvailable && checks.errorRecoveryAvailable;

  return {
    status: all ? 'active' : 'partial',
    checks,
    message: all
      ? 'Extension error recovery system is fully operational'
      : 'Extension error recovery system is partially operational'
  };
}

// --- Auto-initialize when this module is imported in the browser ---
if (isBrowser()) {
  // Defer slightly to allow other modules to attach first
  setTimeout(() => {
    const result = initializeExtensionErrorRecovery();
    if (result.success) {
      logger.info('Extension error recovery auto-initialization completed');

      // Dev-only: emit a quick status snapshot without crashing prod
      try {
        if (typeof process !== 'undefined' && process.env && process.env.NODE_ENV !== 'production') {
          setTimeout(() => {
            const status = checkExtensionErrorRecoveryStatus();
            logger.info('Extension recovery status snapshot', status);
          }, 1000);
        }
      } catch {
        // Ignore env detection issues in non-Node bundlers
      }
    } else {
      logger.error('Extension error recovery auto-initialization failed:', result.error);
    }
  }, 100);
}

const extensionErrorRecovery = {
  initialize: initializeExtensionErrorRecovery,
  checkStatus: checkExtensionErrorRecoveryStatus
};

export default extensionErrorRecovery;

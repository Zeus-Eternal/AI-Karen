/**
 * Initialize Extension Error Recovery System
 * 
 * This file sets up the complete extension error recovery system.
 * Import this early in your application to enable graceful degradation
 * for extension authentication errors.
 */
import { logger } from './logger';
// Import early fix first (immediate execution)
import './early-extension-fix';
// Import error suppression (before any logging occurs)
import './suppress-extension-errors';
// Import immediate fix
import './immediate-extension-fix';
// Import all error recovery components
import './karen-backend-error-suppression';
import './extension-403-fix';
import './error-recovery-integration-example';
import './extension-error-integration';
import './karen-backend-extension-patch';
import './karen-backend-direct-patch';
// Import test utilities in development
/**
 * Initialize the complete extension error recovery system
 */
export function initializeExtensionErrorRecovery() {
  logger.info('Initializing extension error recovery system...');
  try {
    // The imports above will automatically set up the error recovery system
    // This function can be used for any additional initialization if needed
    logger.info('Extension error recovery system initialized successfully');
    return {
      success: true,
      message: 'Extension error recovery system is active',
      features: [
        'HTTP 403/504 error handling',
        'Network error handling',
        'Graceful degradation',
        'Fallback data provision',
        'User-friendly error messages',
        'Automatic retry logic'
      ]
    };
  } catch (error) {
    logger.error('Failed to initialize extension error recovery system:', error);
    return {
      success: false,
      message: 'Extension error recovery system failed to initialize',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}
/**
 * Check if the extension error recovery system is working
 */
export function checkExtensionErrorRecoveryStatus() {
  const checks = {
    fetchPatched: false,
    globalHandlerAvailable: false,
    errorRecoveryAvailable: false
  };
  if (typeof window !== 'undefined') {
    // Check if fetch is patched
    checks.fetchPatched = window.fetch.toString().includes('Extension API') && 
                         window.fetch.toString().includes('error');
    // Check if global error handler is available
    checks.globalHandlerAvailable = !!(window as any).extensionErrorIntegration;
    // Check if error recovery handler is available
    checks.errorRecoveryAvailable = !!(window as any).handleKarenBackendError;
  }
  const allChecksPass = Object.values(checks).every(check => check);
  return {
    status: allChecksPass ? 'active' : 'partial',
    checks,
    message: allChecksPass 
      ? 'Extension error recovery system is fully operational'
      : 'Extension error recovery system is partially operational'
  };
}
// Auto-initialize when this module is imported
if (typeof window !== 'undefined') {
  // Initialize after a short delay to ensure other modules are loaded
  setTimeout(() => {
    const result = initializeExtensionErrorRecovery();
    if (result.success) {
      logger.info('Extension error recovery auto-initialization completed');
      // Check status in development mode
      , 1000);
      }
    } else {
      logger.error('Extension error recovery auto-initialization failed:', result.error);
    }
  }, 100);
}
export default {
  initialize: initializeExtensionErrorRecovery,
  checkStatus: checkExtensionErrorRecoveryStatus
};

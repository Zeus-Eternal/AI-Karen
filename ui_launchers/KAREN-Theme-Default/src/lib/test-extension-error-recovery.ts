/**
 * Test Extension Error Recovery
 * 
 * Simple test to verify that extension error recovery is working properly
 */

import { logger } from './logger';
import {
  handleExtensionError,
  type ExtensionErrorIntegration,
  type ExtensionErrorResponse,
} from './extension-error-integration';
import { getExtensionFallbackData } from './auth/extension-auth-degradation';

declare global {
  interface Window {
    extensionErrorIntegration?: ExtensionErrorIntegration;
  }
}

/**
 * Test extension error recovery functionality
 */
export function testExtensionErrorRecovery() {
  logger.info('Testing extension error recovery...');

  // Test 403 error handling
  const result403 = handleExtensionError(403, '/api/extensions', 'extension_list');
  logger.info('403 error result:', result403);

  // Test 504 error handling
  const result504 = handleExtensionError(504, '/api/extensions', 'extension_list');
  logger.info('504 error result:', result504);

  // Test fallback data
  const fallbackData = getExtensionFallbackData('extension_list');
  logger.info('Fallback data:', fallbackData);

  // Test if the integration is available globally
  if (typeof window !== 'undefined') {
    const globalHandler = window.extensionErrorIntegration;
    if (globalHandler) {
      logger.info('Global extension error integration is available');
      const globalResult = globalHandler.handleExtensionError(403, '/api/extensions');
      logger.info('Global handler result:', globalResult);
    } else {
      logger.warn('Global extension error integration is not available');
    }
  }

  return {
    result403,
    result504,
    fallbackData,
    globalAvailable: typeof window !== 'undefined' && !!window.extensionErrorIntegration
  };
}

// Auto-run test in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  setTimeout(() => {
    testExtensionErrorRecovery();
  }, 1000);
}

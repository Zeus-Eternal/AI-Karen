/**
 * KarenBackend Extension Error Handling Patch
 * 
 * This patch can be applied to the KarenBackend service to handle
 * extension authentication errors gracefully.
 */

import { logger } from './logger';
import { handleExtensionError, shouldUseExtensionFallback, getExtensionErrorMessage } from './extension-error-integration';

/**
 * Patch the KarenBackend service to handle extension errors
 * This should be called after the KarenBackend service is loaded
 */
export function patchKarenBackendForExtensions() {
  // Check if window.handleKarenBackendError exists (from error-recovery-integration)
  if (typeof window !== 'undefined' && (window as any).handleKarenBackendError) {
    logger.info('KarenBackend extension error handling already integrated');
    return;
  }

  // Add extension error handling to window for KarenBackend to use
  if (typeof window !== 'undefined') {
    (window as any).handleExtensionError = (status: number, url: string, operation?: string) => {
      if (shouldUseExtensionFallback(status, url)) {
        const result = handleExtensionError(status, url, operation);
        
        // Show user-friendly message for certain errors
        if (status === 403 && url.includes('/api/extensions')) {
          const message = getExtensionErrorMessage(status, url);
          // You could show a toast notification here
          logger.info(`Extension Error: ${message}`);
        }
        
        return result;
      }
      
      return null; // Let KarenBackend handle other errors normally
    };

    logger.info('KarenBackend extension error handling patched');
  }
}

/**
 * Example of how to integrate this with the KarenBackend makeRequest method
 * This is pseudocode showing where the patch would be applied
 */
export const karenBackendIntegrationExample = `
// In KarenBackend.makeRequest method, after getting a response:

if (!response.ok) {
  // Check if this is an extension error that should be handled specially
  if (typeof window !== 'undefined' && (window as any).handleExtensionError) {
    const extensionErrorResult = (window as any).handleExtensionError(
      response.status, 
      response.url, 
      operation
    );
    
    if (extensionErrorResult) {
      // Handle extension error with fallback data
      if (extensionErrorResult.fallback_data) {
        // Return fallback data as if it was a successful response
        return extensionErrorResult.fallback_data;
      }
      
      if (extensionErrorResult.retry && attempt < maxRetries) {
        // Retry the request after delay
        if (extensionErrorResult.delay > 0) {
          await new Promise(resolve => setTimeout(resolve, extensionErrorResult.delay * 1000));
        }
        // Continue with retry logic
      }
      
      if (extensionErrorResult.requires_login) {
        // Handle authentication required
        throw new Error('Authentication required');
      }
    }
  }
  
  // Continue with normal error handling...
}
`;

// Auto-apply the patch when this module is loaded
if (typeof window !== 'undefined') {
  // Wait a bit for other modules to load
  setTimeout(() => {
    patchKarenBackendForExtensions();
  }, 100);
}
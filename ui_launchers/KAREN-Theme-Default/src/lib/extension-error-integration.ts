/**
 * Extension Error Integration
 * 
 * Simple integration layer for handling extension authentication errors
 * in the KarenBackend service with graceful degradation.
 */

import { logger } from './logger';

export interface ExtensionErrorResponse {
  fallback_data?: any;
  retry?: boolean;
  delay?: number;
  requires_login?: boolean;
  message?: string;
}

/**
 * Handle extension API errors with graceful degradation
 */
export function handleExtensionError(
  status: number,
  url: string,
  operation: string = 'extension_api'
): ExtensionErrorResponse {
  logger.info(`Handling extension error: ${status} for ${url}`);

  // Handle 403 Forbidden errors for extensions
  if (status === 403 && url.includes('/api/extensions')) {
    logger.warn('Extension API access denied, providing fallback data');
    
    // Return appropriate fallback data based on the endpoint
    if (url.endsWith('/api/extensions') || url.endsWith('/api/extensions/')) {
      return {
        fallback_data: {
          extensions: {
            'sample-extension': {
              id: 'sample-extension',
              name: 'Sample Extension',
              display_name: 'Sample Extension (Read-Only)',
              description: 'Extension features are available in read-only mode',
              version: '1.0.0',
              status: 'readonly',
              capabilities: {
                provides_ui: true,
                provides_api: false,
                provides_background_tasks: false,
                provides_webhooks: false
              }
            }
          },
          message: 'Extension features are available in read-only mode',
          access_level: 'readonly',
          available_features: ['view', 'status'],
          restricted_features: ['install', 'configure', 'manage', 'execute']
        },
        message: 'Extensions loaded in read-only mode due to insufficient permissions'
      };
    }
    
    // For other extension endpoints
    return {
      fallback_data: {
        data: [],
        message: 'This extension feature requires additional permissions',
        access_level: 'readonly',
        error: 'insufficient_permissions'
      },
      message: 'Extension feature not available - insufficient permissions'
    };
  }

  // Handle 401 Unauthorized errors
  if (status === 401) {
    logger.warn('Extension API authentication required');
    return {
      requires_login: true,
      message: 'Authentication required to access extension features'
    };
  }

  // Handle 404 Not Found errors
  if (status === 404 && url.includes('/api/extensions')) {
    logger.warn('Extension API endpoint not found');
    return {
      fallback_data: {
        extensions: {},
        message: 'Extension service is not available',
        access_level: 'unavailable'
      },
      message: 'Extension service is temporarily unavailable'
    };
  }

  // Handle 429 Rate Limited errors
  if (status === 429) {
    logger.warn('Extension API rate limited');
    return {
      retry: true,
      delay: 60, // Wait 1 minute before retry
      message: 'Too many requests - please wait before trying again'
    };
  }

  // Handle 504 Gateway Timeout specifically
  if (status === 504) {
    logger.warn('Extension API gateway timeout');
    return {
      retry: true,
      delay: 15, // Wait 15 seconds before retry for timeouts
      fallback_data: {
        extensions: {
          'offline-mode': {
            id: 'offline-mode',
            name: 'offline-mode',
            display_name: 'Extensions (Offline Mode)',
            description: 'Extension service is temporarily unavailable. Core functionality continues to work.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'offline',
            capabilities: {
              provides_ui: false,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Extension service is temporarily unavailable due to timeout',
        access_level: 'offline',
        available_features: [],
        restricted_features: ['all'],
        fallback_mode: true
      },
      message: 'Extension service timed out - using offline mode'
    };
  }

  // Handle 5xx Server errors
  if (status >= 500) {
    logger.error(`Extension API server error: ${status}`);
    return {
      retry: true,
      delay: 30, // Wait 30 seconds before retry
      fallback_data: {
        extensions: {
          'maintenance-mode': {
            id: 'maintenance-mode',
            name: 'maintenance-mode',
            display_name: 'Extensions (Maintenance Mode)',
            description: 'Extension service is under maintenance. Please try again later.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'maintenance',
            capabilities: {
              provides_ui: false,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Extension service is temporarily unavailable for maintenance',
        access_level: 'maintenance',
        available_features: [],
        restricted_features: ['all'],
        fallback_mode: true
      },
      message: 'Extension service is experiencing issues - using cached data'
    };
  }

  // Default fallback for other errors
  logger.warn(`Unhandled extension error: ${status}`);
  return {
    fallback_data: {
      extensions: {},
      message: 'Extension service encountered an error',
      access_level: 'limited'
    },
    message: 'Extension service is temporarily limited'
  };
}

/**
 * Check if an error should trigger extension fallback mode
 */
export function shouldUseExtensionFallback(status: number, url: string): boolean {
  return (
    url.includes('/api/extensions') &&
    (status === 403 || status === 404 || status === 504 || status >= 500)
  );
}

/**
 * Get user-friendly message for extension errors
 */
export function getExtensionErrorMessage(status: number, url: string): string {
  if (status === 403) {
    return 'Extension features are running in read-only mode. Some functionality may be limited.';
  }
  
  if (status === 401) {
    return 'Please log in to access full extension features.';
  }
  
  if (status === 404) {
    return 'Extension service is not available. Core features will continue to work.';
  }
  
  if (status === 504) {
    return 'Extension service timed out. Core features will continue to work while we retry the connection.';
  }
  
  if (status >= 500) {
    return 'Extension service is temporarily unavailable. Please try again later.';
  }
  
  return 'Extension service encountered an issue. Some features may be limited.';
}

export interface ExtensionErrorIntegration {
  handleExtensionError: typeof handleExtensionError;
  shouldUseExtensionFallback: typeof shouldUseExtensionFallback;
  getExtensionErrorMessage: (status: number, url: string) => string;
}

declare global {
  interface Window {
    extensionErrorIntegration?: ExtensionErrorIntegration;
    handleExtensionError?: typeof handleExtensionError;
  }
}

// Make functions available globally for KarenBackend integration
if (typeof window !== 'undefined') {
  const integration: ExtensionErrorIntegration = {
    handleExtensionError,
    shouldUseExtensionFallback,
    getExtensionErrorMessage,
  };
  window.extensionErrorIntegration = integration;
  logger.info('Extension error integration initialized');
}

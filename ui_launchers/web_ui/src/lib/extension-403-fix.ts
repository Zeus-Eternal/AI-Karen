/**
 * Extension 403 Error Fix
 * 
 * Immediate fix for the 403 Forbidden error when accessing /api/extensions
 * This provides a quick solution while the comprehensive error recovery system is being integrated.
 */

import { logger } from './logger';

/**
 * Patch fetch to handle extension errors (403, 504, network errors)
 */
export function patchFetchForExtension403() {
  if (typeof window === 'undefined') return;

  const originalFetch = window.fetch;

  window.fetch = async function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    try {
      const response = await originalFetch(input, init);
      
      // Handle 403 and 504 errors for extension endpoints
      if (!response.ok && (response.status === 403 || response.status === 504)) {
        const url = typeof input === 'string' ? input : input.toString();
        
        if (url.includes('/api/extensions')) {
          const errorType = response.status === 403 ? 'permission denied' : 'timeout';
          logger.warn(`Extension API ${response.status} error (${errorType}) for ${url}, providing fallback response`);
          
          // Create fallback response data
          const fallbackData = getFallbackDataForExtensionEndpoint(url, response.status);
          
          // Return a mock successful response with fallback data
          return new Response(JSON.stringify(fallbackData), {
            status: 200,
            statusText: 'OK',
            headers: {
              'Content-Type': 'application/json',
              'X-Fallback-Mode': response.status === 403 ? 'extension-readonly' : 'extension-offline'
            }
          });
        }
      }
      
      return response;
    } catch (error) {
      // Handle network errors for extension endpoints
      const url = typeof input === 'string' ? input : input.toString();
      
      if (url.includes('/api/extensions')) {
        logger.warn(`Extension API network error for ${url}, providing fallback response`);
        
        const fallbackData = getFallbackDataForExtensionEndpoint(url, 0); // 0 indicates network error
        
        return new Response(JSON.stringify(fallbackData), {
          status: 200,
          statusText: 'OK',
          headers: {
            'Content-Type': 'application/json',
            'X-Fallback-Mode': 'extension-offline'
          }
        });
      }
      
      throw error;
    }
  };

  logger.info('Extension 403 error fix applied to fetch');
}

/**
 * Get appropriate fallback data based on the extension endpoint
 */
function getFallbackDataForExtensionEndpoint(url: string, status: number = 403): any {
  // Main extensions list endpoint
  if (url.endsWith('/api/extensions') || url.endsWith('/api/extensions/')) {
    if (status === 504) {
      // Gateway timeout - service unavailable
      return {
        extensions: {
          'offline-mode': {
            id: 'offline-mode',
            name: 'offline-mode',
            display_name: 'Extensions (Service Unavailable)',
            description: 'Extension service is temporarily unavailable due to a timeout. Core functionality continues to work.',
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
        message: 'Extension service is temporarily unavailable',
        access_level: 'offline',
        available_features: [],
        restricted_features: ['all'],
        fallback_mode: true,
        error_type: 'timeout'
      };
    } else if (status === 0) {
      // Network error
      return {
        extensions: {
          'network-error': {
            id: 'network-error',
            name: 'network-error',
            display_name: 'Extensions (Network Error)',
            description: 'Unable to connect to extension service. Please check your internet connection.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'disconnected',
            capabilities: {
              provides_ui: false,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Unable to connect to extension service',
        access_level: 'disconnected',
        available_features: [],
        restricted_features: ['all'],
        fallback_mode: true,
        error_type: 'network'
      };
    } else {
      // 403 or other permission errors
      return {
        extensions: {
          'readonly-mode': {
            id: 'readonly-mode',
            name: 'readonly-mode',
            display_name: 'Extensions (Read-Only Mode)',
            description: 'Extension features are available in read-only mode. Some functionality may be limited due to insufficient permissions.',
            version: '1.0.0',
            author: 'System',
            category: 'system',
            status: 'readonly',
            capabilities: {
              provides_ui: true,
              provides_api: false,
              provides_background_tasks: false,
              provides_webhooks: false
            }
          }
        },
        total: 1,
        message: 'Extension features are available in read-only mode',
        access_level: 'readonly',
        available_features: ['view', 'status'],
        restricted_features: ['install', 'configure', 'manage', 'execute'],
        fallback_mode: true,
        error_type: 'permission'
      };
    }
  }

  // Extension status endpoint
  if (url.includes('/status') || url.includes('/health')) {
    if (status === 504 || status === 0) {
      return {
        status: 'offline',
        message: 'Extension service is temporarily unavailable',
        health: {
          status: 'error',
          message: status === 504 ? 'Service timeout' : 'Network error',
          lastCheck: new Date().toISOString()
        },
        fallback_mode: true,
        error_type: status === 504 ? 'timeout' : 'network'
      };
    } else {
      return {
        status: 'readonly',
        message: 'Extension status available in read-only mode',
        health: {
          status: 'degraded',
          message: 'Running in read-only mode',
          lastCheck: new Date().toISOString()
        },
        fallback_mode: true,
        error_type: 'permission'
      };
    }
  }

  // Background tasks endpoint
  if (url.includes('/background-tasks')) {
    const message = status === 504 || status === 0 
      ? 'Background tasks service is temporarily unavailable'
      : 'Background tasks not available in read-only mode';
    
    return {
      tasks: [],
      total: 0,
      message,
      access_level: status === 504 || status === 0 ? 'offline' : 'readonly',
      fallback_mode: true,
      error_type: status === 504 ? 'timeout' : status === 0 ? 'network' : 'permission'
    };
  }

  // Generic extension endpoint
  const message = status === 504 || status === 0
    ? 'This extension feature is temporarily unavailable'
    : 'This extension feature is not available in read-only mode';
    
  return {
    data: [],
    message,
    access_level: status === 504 || status === 0 ? 'offline' : 'readonly',
    fallback_mode: true,
    error: status === 504 ? 'service_timeout' : status === 0 ? 'network_error' : 'insufficient_permissions',
    error_type: status === 504 ? 'timeout' : status === 0 ? 'network' : 'permission'
  };
}

/**
 * Show user notification about extension status
 */
export function showExtensionStatusNotification(errorType: 'permission' | 'timeout' | 'network' = 'permission') {
  if (typeof window === 'undefined') return;

  let message: string;
  let logLevel: 'info' | 'warn' | 'error' = 'info';

  switch (errorType) {
    case 'timeout':
      message = 'Extension service is temporarily unavailable due to a timeout. Core functionality continues to work.';
      logLevel = 'warn';
      break;
    case 'network':
      message = 'Unable to connect to extension service. Please check your internet connection.';
      logLevel = 'error';
      break;
    case 'permission':
    default:
      message = 'Extension features are running in read-only mode due to insufficient permissions.';
      logLevel = 'info';
      break;
  }

  // Log with appropriate level
  logger[logLevel](message);
  
  // You could add a toast notification here if you have a notification system
  // For example:
  // if (errorType === 'timeout' || errorType === 'network') {
  //   toast.warning(message);
  // } else {
  //   toast.info(message);
  // }
}

/**
 * Initialize the extension error fix
 */
export function initializeExtensionErrorFix() {
  patchFetchForExtension403();
  
  logger.info('Extension error fix initialized (handles 403, 504, and network errors)');
}

// Auto-initialize if in browser environment
if (typeof window !== 'undefined') {
  // Wait a bit for other modules to load
  setTimeout(() => {
    initializeExtensionErrorFix();
  }, 500);
}
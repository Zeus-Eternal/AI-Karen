/**
 * Direct KarenBackend Patch for Extension Errors
 * 
 * This directly patches the KarenBackend service to handle extension errors
 * by intercepting the makeRequest method and providing fallback data.
 */

import { logger } from './logger';

/**
 * Fallback data for extension endpoints
 */
const EXTENSION_FALLBACK_DATA = {
  extensions: {
    'readonly-mode': {
      id: 'readonly-mode',
      name: 'readonly-mode',
      display_name: 'Extensions (Read-Only Mode)',
      description: 'Extension features are available in read-only mode due to insufficient permissions',
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
  fallback_mode: true
};

/**
 * Patch the KarenBackend service to handle extension errors
 */
export function patchKarenBackendDirectly() {
  if (typeof window === 'undefined') return;

  // Wait for KarenBackend to be available
  const checkAndPatch = () => {
    // Try to find the KarenBackend instance
    const karenBackend = (window as any).karenBackend || 
                        (window as any).getKarenBackend?.() ||
                        null;

    if (karenBackend && karenBackend.makeRequest) {
      const originalMakeRequest = karenBackend.makeRequest.bind(karenBackend);

      karenBackend.makeRequest = async function(endpoint: string, ...args: any[]) {
        try {
          return await originalMakeRequest(endpoint, ...args);
        } catch (error: any) {
          // Handle extension endpoint errors
          if (endpoint.includes('/api/extensions') && 
              (error.status === 403 || error.status === 401 || error.status === 504)) {
            
            logger.warn(`KarenBackend extension error ${error.status} for ${endpoint}, providing fallback data`);
            
            // Return appropriate fallback data based on endpoint
            if (endpoint.endsWith('/api/extensions') || endpoint.endsWith('/api/extensions/')) {
              return EXTENSION_FALLBACK_DATA;
            }
            
            // For other extension endpoints, return empty data
            return {
              data: [],
              message: 'Extension feature not available in read-only mode',
              fallback_mode: true
            };
          }
          
          // Re-throw other errors
          throw error;
        }
      };

      logger.info('KarenBackend directly patched for extension error handling');
      return true;
    }

    return false;
  };

  // Try to patch immediately
  if (checkAndPatch()) {
    return;
  }

  // If not available, try again after a delay
  setTimeout(() => {
    if (checkAndPatch()) {
      return;
    }

    // Try one more time after a longer delay
    setTimeout(() => {
      if (!checkAndPatch()) {
        logger.warn('Could not patch KarenBackend - service not found');
      }
    }, 2000);
  }, 1000);
}

/**
 * Alternative approach: Patch the global fetch for KarenBackend requests
 */
export function patchFetchForKarenBackend() {
  if (typeof window === 'undefined') return;

  const originalFetch = window.fetch;

  window.fetch = async function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const url = typeof input === 'string' ? input : input.toString();
    
    try {
      const response = await originalFetch(input, init);
      
      // Handle extension API errors
      if (!response.ok && url.includes('/api/extensions')) {
        if (response.status === 403 || response.status === 401 || response.status === 504) {
          logger.warn(`Fetch intercepted extension error ${response.status} for ${url}, providing fallback response`);
          
          let fallbackData;
          if (url.endsWith('/api/extensions') || url.endsWith('/api/extensions/')) {
            fallbackData = EXTENSION_FALLBACK_DATA;
          } else {
            fallbackData = {
              data: [],
              message: 'Extension feature not available',
              fallback_mode: true
            };
          }
          
          return new Response(JSON.stringify(fallbackData), {
            status: 200,
            statusText: 'OK',
            headers: {
              'Content-Type': 'application/json',
              'X-Fallback-Mode': 'extension-readonly'
            }

        }
      }
      
      return response;
    } catch (error) {
      // Handle network errors for extension endpoints
      if (url.includes('/api/extensions')) {
        logger.warn(`Fetch intercepted network error for ${url}, providing fallback response`);
        
        return new Response(JSON.stringify({
          extensions: {},
          message: 'Extension service is temporarily unavailable',
          fallback_mode: true
        }), {
          status: 200,
          statusText: 'OK',
          headers: {
            'Content-Type': 'application/json',
            'X-Fallback-Mode': 'extension-offline'
          }

      }
      
      throw error;
    }
  };

  logger.info('Global fetch patched for KarenBackend extension error handling');
}

/**
 * Initialize both patching approaches
 */
export function initializeKarenBackendPatch() {
  // Apply both patches for maximum coverage
  patchFetchForKarenBackend();
  patchKarenBackendDirectly();
  
  logger.info('KarenBackend extension error patches initialized');
}

// Auto-initialize
if (typeof window !== 'undefined') {
  // Apply immediately
  initializeKarenBackendPatch();
}
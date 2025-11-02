/**
 * KarenBackend Error Suppression
 * 
 * Specifically targets the KarenBackend service to suppress extension-related
 * error logging while preserving the error handling functionality.
 */

/**
 * Patch KarenBackend to suppress extension error logging
 */
export function suppressKarenBackendExtensionErrors() {
  if (typeof window === 'undefined') return;

  // Wait for the KarenBackend service to be available
  const patchKarenBackend = () => {
    // Try to find KarenBackend instances
    const possibleInstances = [
      (window as any).karenBackend,
      (window as any).getKarenBackend?.(),
      // Look for instances in common locations
      ...(Object.values(window as any).filter((val: any) => 
        val && typeof val === 'object' && 
        typeof val.makeRequest === 'function' &&
        typeof val.isExtensionEndpoint === 'function'
      ))
    ].filter(Boolean);

    let patchedCount = 0;

    possibleInstances.forEach(instance => {
      if (instance && instance.makeRequest && !instance._extensionErrorPatched) {
        const originalMakeRequest = instance.makeRequest.bind(instance);

        instance.makeRequest = async function(endpoint: string, ...args: any[]) {
          try {
            return await originalMakeRequest(endpoint, ...args);
          } catch (error: any) {
            // If this is an extension endpoint error, handle it silently
            if (endpoint.includes('/api/extensions') && 
                (error.status === 403 || error.status === 401)) {
              
              // Log as info instead of error
              console.info(`[EXTENSION-HANDLED] KarenBackend handled ${error.status} for ${endpoint}`);
              
              // Try to get fallback data
              if (typeof instance.handleExtensionError === 'function') {
                try {
                  const fallbackData = await instance.handleExtensionError(endpoint, error, error.details);
                  if (fallbackData !== null) {
                    return fallbackData;
                  }
                } catch (fallbackError) {
                  console.debug('[EXTENSION-FALLBACK] Fallback error:', fallbackError);
                }
              }

              // Return default fallback data
              if (endpoint.endsWith('/api/extensions') || endpoint.endsWith('/api/extensions/')) {
                return {
                  extensions: {
                    'readonly-mode': {
                      id: 'readonly-mode',
                      name: 'readonly-mode',
                      display_name: 'Extensions (Read-Only Mode)',
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
                  total: 1,
                  message: 'Extension features are available in read-only mode',
                  access_level: 'readonly',
                  fallback_mode: true
                };
              }

              // Return empty data for other extension endpoints
              return {
                data: [],
                message: 'Extension feature not available',
                fallback_mode: true
              };
            }

            // Re-throw non-extension errors
            throw error;
          }
        };

        // Mark as patched to avoid double-patching
        instance._extensionErrorPatched = true;
        patchedCount++;
      }
    });

    return patchedCount;
  };

  // Try to patch immediately
  let patchedCount = patchKarenBackend();
  
  if (patchedCount > 0) {
    console.info(`[KAREN-BACKEND-PATCH] Patched ${patchedCount} KarenBackend instance(s)`);
    return;
  }

  // If no instances found, try again after delays
  setTimeout(() => {
    patchedCount = patchKarenBackend();
    if (patchedCount > 0) {
      console.info(`[KAREN-BACKEND-PATCH] Patched ${patchedCount} KarenBackend instance(s) (delayed)`);
      return;
    }

    // Try one more time after a longer delay
    setTimeout(() => {
      patchedCount = patchKarenBackend();
      if (patchedCount > 0) {
        console.info(`[KAREN-BACKEND-PATCH] Patched ${patchedCount} KarenBackend instance(s) (final attempt)`);
      } else {
        console.debug('[KAREN-BACKEND-PATCH] No KarenBackend instances found to patch');
      }
    }, 3000);
  }, 1000);
}

// Auto-initialize
if (typeof window !== 'undefined') {
  suppressKarenBackendExtensionErrors();
}
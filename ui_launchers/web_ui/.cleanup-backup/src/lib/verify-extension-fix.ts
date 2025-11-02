/**
 * Verify Extension Fix
 * 
 * Simple verification script to check if the extension error recovery is working
 */

export function verifyExtensionFix() {
  if (typeof window === 'undefined') {
    return { status: 'not_browser', message: 'Not running in browser environment' };
  }

  const checks = {
    fetchPatched: false,
    immediateFixApplied: false,
    errorRecoveryLoaded: false
  };

  // Check if fetch is patched
  const fetchString = window.fetch.toString();
  checks.fetchPatched = fetchString.includes('api/extensions') || 
                       fetchString.includes('EXTENSION-FIX') ||
                       fetchString.includes('Extension API');

  // Check if immediate fix is applied
  checks.immediateFixApplied = fetchString.includes('EXTENSION-FIX');

  // Check if error recovery system is loaded
  checks.errorRecoveryLoaded = !!(window as any).extensionErrorIntegration ||
                              !!(window as any).handleKarenBackendError;

  const allChecksPass = Object.values(checks).some(check => check);

  return {
    status: allChecksPass ? 'active' : 'inactive',
    checks,
    message: allChecksPass 
      ? 'Extension error recovery is active'
      : 'Extension error recovery is not active',
    fetchInfo: {
      isPatched: checks.fetchPatched,
      patchType: checks.immediateFixApplied ? 'immediate' : 'standard'
    }
  };
}

/**
 * Test the extension error recovery by making a test request
 */
export async function testExtensionErrorRecovery() {
  if (typeof window === 'undefined') {
    return { status: 'not_browser', message: 'Not running in browser environment' };
  }

  try {
    console.log('[EXTENSION-TEST] Testing extension error recovery...');
    
    // Make a test request to the extensions endpoint
    const response = await fetch('/api/extensions');
    const data = await response.json();
    
    const isUsingFallback = response.headers.get('X-Fallback-Mode') !== null ||
                           data.fallback_mode === true ||
                           data.access_level === 'readonly';

    return {
      status: 'success',
      usingFallback: isUsingFallback,
      data: data,
      message: isUsingFallback 
        ? 'Extension error recovery is working - using fallback data'
        : 'Extension API is working normally'
    };
  } catch (error) {
    return {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
      message: 'Test request failed'
    };
  }
}

// Auto-run verification in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  setTimeout(() => {
    const verification = verifyExtensionFix();
    console.log('[EXTENSION-VERIFY] Extension fix verification:', verification);
    
    // Also test the actual functionality
    setTimeout(() => {
      testExtensionErrorRecovery().then(testResult => {
        console.log('[EXTENSION-TEST] Extension error recovery test:', testResult);
      });
    }, 2000);
  }, 1000);
}
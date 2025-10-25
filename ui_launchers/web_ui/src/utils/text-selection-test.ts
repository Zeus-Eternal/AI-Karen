/**
 * Text Selection Test Utilities
 * 
 * Utilities to test and verify text selection functionality.
 */

export interface TextSelectionTestResult {
  isSupported: boolean;
  canSelect: boolean;
  canCopy: boolean;
  canPaste: boolean;
  browserInfo: {
    userAgent: string;
    isSecureContext: boolean;
    hasClipboardAPI: boolean;
  };
  errors: string[];
}

/**
 * Comprehensive test of text selection functionality
 */
export async function testTextSelection(): Promise<TextSelectionTestResult> {
  const result: TextSelectionTestResult = {
    isSupported: false,
    canSelect: false,
    canCopy: false,
    canPaste: false,
    browserInfo: {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
      isSecureContext: typeof window !== 'undefined' ? window.isSecureContext : false,
      hasClipboardAPI: typeof navigator !== 'undefined' && 'clipboard' in navigator,
    },
    errors: [],
  };

  try {
    // Test 1: Basic selection support
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      result.errors.push('Not running in browser environment');
      return result;
    }

    if (typeof window.getSelection !== 'function') {
      result.errors.push('window.getSelection not supported');
      return result;
    }

    if (typeof document.createRange !== 'function') {
      result.errors.push('document.createRange not supported');
      return result;
    }

    result.isSupported = true;

    // Test 2: Create a test element and try to select text
    const testElement = document.createElement('div');
    testElement.textContent = 'Test selection text';
    testElement.style.position = 'absolute';
    testElement.style.left = '-9999px';
    testElement.style.userSelect = 'auto';
    document.body.appendChild(testElement);

    try {
      const range = document.createRange();
      range.selectNodeContents(testElement);
      const selection = window.getSelection();
      
      if (selection) {
        selection.removeAllRanges();
        selection.addRange(range);
        
        if (selection.toString() === 'Test selection text') {
          result.canSelect = true;
        } else {
          result.errors.push('Text selection failed - selected text does not match');
        }
        
        selection.removeAllRanges();
      } else {
        result.errors.push('Could not get selection object');
      }
    } catch (error) {
      result.errors.push(`Selection test failed: ${error}`);
    } finally {
      document.body.removeChild(testElement);
    }

    // Test 3: Copy functionality
    try {
      if (navigator.clipboard && window.isSecureContext) {
        // Test modern clipboard API
        await navigator.clipboard.writeText('test copy');
        const clipboardText = await navigator.clipboard.readText();
        if (clipboardText === 'test copy') {
          result.canCopy = true;
        } else {
          result.errors.push('Clipboard write/read test failed');
        }
      } else {
        // Test legacy copy method
        const testInput = document.createElement('textarea');
        testInput.value = 'test copy legacy';
        testInput.style.position = 'absolute';
        testInput.style.left = '-9999px';
        document.body.appendChild(testInput);
        
        testInput.select();
        const copySuccess = document.execCommand('copy');
        
        if (copySuccess) {
          result.canCopy = true;
        } else {
          result.errors.push('Legacy copy method failed');
        }
        
        document.body.removeChild(testInput);
      }
    } catch (error) {
      result.errors.push(`Copy test failed: ${error}`);
    }

    // Test 4: Paste functionality (if supported)
    try {
      if (navigator.clipboard && window.isSecureContext) {
        // We can't reliably test paste without user interaction
        // but we can check if the API is available
        result.canPaste = typeof navigator.clipboard.readText === 'function';
      } else {
        // Legacy paste is not reliably testable
        result.canPaste = false;
      }
    } catch (error) {
      result.errors.push(`Paste test failed: ${error}`);
    }

  } catch (error) {
    result.errors.push(`General test failure: ${error}`);
  }

  return result;
}

/**
 * Test if a specific element supports text selection
 */
export function testElementSelection(element: HTMLElement): boolean {
  try {
    const computedStyle = window.getComputedStyle(element);
    const userSelect = computedStyle.userSelect || computedStyle.webkitUserSelect;
    
    // Check if user-select is not 'none'
    if (userSelect === 'none') {
      return false;
    }

    // Try to select text in the element
    const range = document.createRange();
    range.selectNodeContents(element);
    const selection = window.getSelection();
    
    if (selection) {
      const originalRangeCount = selection.rangeCount;
      selection.removeAllRanges();
      selection.addRange(range);
      
      const hasSelection = selection.rangeCount > 0 && !selection.isCollapsed;
      
      // Restore original selection
      selection.removeAllRanges();
      for (let i = 0; i < originalRangeCount; i++) {
        // Note: We can't restore the exact original ranges without storing them
        // This is a simplified restoration
      }
      
      return hasSelection;
    }
    
    return false;
  } catch (error) {
    console.error('Element selection test failed:', error);
    return false;
  }
}

/**
 * Get detailed information about text selection support
 */
export function getTextSelectionInfo() {
  const info = {
    apis: {
      getSelection: typeof window !== 'undefined' && typeof window.getSelection === 'function',
      createRange: typeof document !== 'undefined' && typeof document.createRange === 'function',
      execCommand: typeof document !== 'undefined' && typeof document.execCommand === 'function',
      clipboardAPI: typeof navigator !== 'undefined' && 'clipboard' in navigator,
    },
    browser: {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
      isSecureContext: typeof window !== 'undefined' ? window.isSecureContext : false,
      language: typeof navigator !== 'undefined' ? navigator.language : 'Unknown',
    },
    features: {
      touchSupport: typeof window !== 'undefined' && 'ontouchstart' in window,
      pointerEvents: typeof window !== 'undefined' && 'PointerEvent' in window,
      selectionAPI: typeof window !== 'undefined' && 'Selection' in window,
    },
  };

  return info;
}

/**
 * Log text selection test results to console
 */
export async function logTextSelectionTest() {
  console.group('🔍 Text Selection Test Results');
  
  const testResult = await testTextSelection();
  const info = getTextSelectionInfo();
  
  console.log('✅ Test Results:', testResult);
  console.log('ℹ️ Browser Info:', info);
  
  if (testResult.errors.length > 0) {
    console.group('❌ Errors:');
    testResult.errors.forEach(error => console.error(error));
    console.groupEnd();
  }
  
  if (testResult.isSupported && testResult.canSelect && testResult.canCopy) {
    console.log('🎉 Text selection is working properly!');
  } else {
    console.warn('⚠️ Text selection may have issues');
  }
  
  console.groupEnd();
}

// Auto-run test in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  // Run test after a short delay to ensure DOM is ready
  setTimeout(() => {
    logTextSelectionTest();
  }, 1000);
}